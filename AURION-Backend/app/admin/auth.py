# app/admin/auth.py
# Admin authentication and JWT handling

import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import bcrypt
import app.auth_db as auth_db_module

# JWT Configuration
SECRET_KEY = "your-super-secret-admin-key-change-in-production-2024"  # CHANGE THIS!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours

security = HTTPBearer()

# Hardcoded admin credentials (for initial setup)
ADMIN_EMAIL = "rathodvamshi369@gmail.com"
ADMIN_PASSWORD = "Rathod@369"

def hash_admin_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_admin_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[Dict]:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_admin(credentials: HTTPAuthorizationCredentials = Security(security)) -> Dict:
    """Get current admin from JWT token"""
    token = credentials.credentials
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    # Check if admin exists in database
    admin = await auth_db_module.db.admins.find_one({"email": email})
    if not admin:
        raise HTTPException(status_code=401, detail="Admin not found")
    
    return {
        "admin_id": str(admin["_id"]),
        "email": admin["email"],
        "role": admin["role"],
        "display_name": admin.get("display_name", "Admin")
    }

async def authenticate_admin(email: str, password: str) -> Dict:
    """Authenticate admin and return user info"""
    
    # First check hardcoded admin
    if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
        # Initialize this admin in database if not exists
        admin = await auth_db_module.db.admins.find_one({"email": ADMIN_EMAIL})
        if not admin:
            # Create the super admin
            admin_data = {
                "email": ADMIN_EMAIL,
                "password": hash_admin_password(ADMIN_PASSWORD),
                "display_name": "Super Admin",
                "role": "super_admin",
                "created_at": datetime.utcnow(),
                "last_login": datetime.utcnow()
            }
            result = await auth_db_module.db.admins.insert_one(admin_data)
            admin_id = str(result.inserted_id)
        else:
            admin_id = str(admin["_id"])
            # Update last login
            await auth_db_module.db.admins.update_one(
                {"_id": admin["_id"]},
                {"$set": {"last_login": datetime.utcnow()}}
            )
        
        return {
            "success": True,
            "admin_id": admin_id,
            "email": ADMIN_EMAIL,
            "role": "super_admin",
            "display_name": "Super Admin"
        }
    
    # Check database admins
    admin = await auth_db_module.db.admins.find_one({"email": email})
    
    if not admin:
        return {"success": False, "error": "Unauthorized Access"}
    
    if not verify_admin_password(password, admin["password"]):
        return {"success": False, "error": "Unauthorized Access"}
    
    # Update last login
    await auth_db_module.db.admins.update_one(
        {"_id": admin["_id"]},
        {"$set": {"last_login": datetime.utcnow()}}
    )
    
    return {
        "success": True,
        "admin_id": str(admin["_id"]),
        "email": admin["email"],
        "role": admin.get("role", "limited_admin"),
        "display_name": admin.get("display_name", "Admin")
    }

async def create_admin(email: str, password: str, display_name: str, role: str) -> Dict:
    """Create a new admin"""
    existing = await auth_db_module.db.admins.find_one({"email": email})
    if existing:
        return {"success": False, "error": "Admin already exists"}
    
    admin_data = {
        "email": email,
        "password": hash_admin_password(password),
        "display_name": display_name,
        "role": role,
        "created_at": datetime.utcnow(),
        "last_login": None
    }
    
    result = await auth_db_module.db.admins.insert_one(admin_data)
    return {
        "success": True,
        "admin_id": str(result.inserted_id),
        "email": email,
        "role": role
    }

async def log_admin_action(admin_id: str, action: str, target: Optional[str] = None, 
                          details: Optional[Dict] = None, ip_address: Optional[str] = None):
    """Log admin action to audit trail"""
    log_entry = {
        "admin_id": admin_id,
        "action": action,
        "target": target,
        "details": details or {},
        "timestamp": datetime.utcnow(),
        "ip_address": ip_address
    }
    
    await auth_db_module.db.audit_logs.insert_one(log_entry)
