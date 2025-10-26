# app/auth_db.py
# MongoDB-based authentication system for AURION


from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
import bcrypt
import random
import string
from typing import Optional, Dict
import pymongo
from fastapi import Depends, HTTPException, Header
from app.models.schemas import User
from app.core.config import settings

# MongoDB Connection
MONGO_URI = getattr(settings, 'mongo_uri', None)
MONGO_DB = getattr(settings, 'mongo_db_name', 'aurion')

mongo_client: Optional[AsyncIOMotorClient] = None
db = None

async def init_mongodb():
    """Initialize MongoDB connection with retry logic"""
    global mongo_client, db
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            mongo_client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            db = mongo_client[MONGO_DB]
            
            # Test connection
            await mongo_client.admin.command('ping')
            
            # Create indexes
            await db.users.create_index("email", unique=True)
            await db.otps.create_index("email")
            await db.otps.create_index("expires_at")
            
            # Create session collections if they don't exist
            await db.chat_sessions.create_index("session_id", unique=True)
            await db.chat_sessions.create_index("user_id")
            await db.chat_messages.create_index("session_id")
            await db.chat_messages.create_index("user_id")

            # Mini agent conversation indexes
            await db.mini_agent_conversations.create_index("messageId", unique=True)
            await db.mini_agent_conversations.create_index("sessionId")
            await db.mini_agent_conversations.create_index("updatedAt")

            # Message highlights indexes
            await db.message_highlights.create_index("messageId", unique=True)
            await db.message_highlights.create_index("sessionId")
            await db.message_highlights.create_index("updatedAt")
            
            
            print("✅ MongoDB connected successfully")
            return True
            
        except Exception as e:
            print(f"❌ MongoDB connection attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                import asyncio
                await asyncio.sleep(retry_delay)
                retry_delay *= 2
            else:
                print("❌ MongoDB connection failed after all retries")
                return False

async def close_mongodb():
    """Close MongoDB connection"""
    global mongo_client
    if mongo_client:
        mongo_client.close()
        print("MongoDB connection closed")

# Helper functions
def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def generate_otp() -> str:
    """Generate 4-digit OTP"""
    return ''.join(random.choices(string.digits, k=4))

# User Management
async def create_user(email: str, password: str, display_name: str, role: str, hobbies: list) -> Dict:
    """Create a new user"""
    existing = await db.users.find_one({"email": email})
    if existing:
        return {"success": False, "error": "Email already registered"}
    
    user_data = {
        "email": email,
        "password": hash_password(password),
        "display_name": display_name,
        "role": role,
        "hobbies": hobbies,
        "created_at": datetime.utcnow(),
        "verified": True,
        "oauth_provider": None
    }
    
    result = await db.users.insert_one(user_data)
    return {
        "success": True,
        "user_id": str(result.inserted_id),
        "email": email,
        "display_name": display_name
    }

async def authenticate_user(email: str, password: str) -> Dict:
    """Authenticate user with email and password"""
    user = await db.users.find_one({"email": email})
    
    if not user:
        return {"success": False, "error": "Invalid email or password"}
    
    if not verify_password(password, user["password"]):
        return {"success": False, "error": "Invalid email or password"}
    
    return {
        "success": True,
        "user_id": str(user["_id"]),
        "email": user["email"],
        "display_name": user["display_name"],
        "role": user.get("role"),
        "hobbies": user.get("hobbies", [])
    }

async def get_user_by_email(email: str) -> Optional[Dict]:
    """Get user by email"""
    try:
        user = await db.users.find_one({"email": email})
        if user:
            user["_id"] = str(user["_id"])
        return user
    except Exception as e:
        # Handle transient Mongo errors by attempting to re-initialize the client once
        # and retrying the operation. If recovery fails, raise a 503 so the API
        # returns a friendly status instead of crashing the request pipeline.
        err = e
        # Check for common connection-reset/autoreconnect errors
        is_transient = False
        try:
            is_transient = isinstance(e, pymongo.errors.AutoReconnect) or isinstance(e, ConnectionResetError)
        except Exception:
            is_transient = False

        if is_transient:
            print(f"Detected transient Mongo error in get_user_by_email: {e}; attempting re-init")
            init_ok = await init_mongodb()
            if init_ok and db is not None:
                try:
                    user = await db.users.find_one({"email": email})
                    if user:
                        user["_id"] = str(user["_id"])
                    return user
                except Exception as e2:
                    print(f"Retry after init failed: {e2}")
                    raise HTTPException(status_code=503, detail="MongoDB temporarily unavailable")
            else:
                raise HTTPException(status_code=503, detail="MongoDB not initialized")

        # Non-transient error; surface as 503
        print(f"Non-transient DB error in get_user_by_email: {e}")
        raise HTTPException(status_code=503, detail="MongoDB error")

# OTP Management
async def create_otp(email: str, purpose: str = "signup") -> Dict:
    """Create and store OTP"""
    # Check rate limiting (max 5 OTPs per hour)
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    recent_otps = await db.otps.count_documents({
        "email": email,
        "created_at": {"$gte": one_hour_ago}
    })
    
    if recent_otps >= 5:
        return {
            "success": False,
            "error": "Too many OTP requests. Please try again later."
        }
    
    otp = generate_otp()
    otp_data = {
        "email": email,
        "otp": otp,
        "purpose": purpose,  # 'signup' or 'forgot_password'
        "attempts": 0,
        "max_attempts": 3,
        "expires_at": datetime.utcnow() + timedelta(seconds=60),
        "created_at": datetime.utcnow(),
        "verified": False
    }
    
    await db.otps.insert_one(otp_data)
    
    return {
        "success": True,
        "otp": otp,  # In production, don't return OTP - send via email
        "expires_in": 60
    }

async def verify_otp(email: str, otp: str, purpose: str = "signup") -> Dict:
    """Verify OTP"""
    otp_doc = await db.otps.find_one({
        "email": email,
        "purpose": purpose,
        "verified": False,
        "expires_at": {"$gte": datetime.utcnow()}
    })
    
    if not otp_doc:
        return {
            "success": False,
            "error": "OTP expired or not found"
        }
    
    # Check attempts
    if otp_doc["attempts"] >= otp_doc["max_attempts"]:
        return {
            "success": False,
            "error": "Maximum attempts exceeded"
        }
    
    # Verify OTP
    if otp_doc["otp"] != otp:
        # Increment attempts
        await db.otps.update_one(
            {"_id": otp_doc["_id"]},
            {"$inc": {"attempts": 1}}
        )
        remaining = otp_doc["max_attempts"] - otp_doc["attempts"] - 1
        return {
            "success": False,
            "error": f"Invalid OTP. {remaining} attempts remaining."
        }
    
    # Mark as verified
    await db.otps.update_one(
        {"_id": otp_doc["_id"]},
        {"$set": {"verified": True}}
    )
    
    return {"success": True, "message": "OTP verified successfully"}

async def reset_password(email: str, new_password: str) -> Dict:
    """Reset user password"""
    # Check if OTP was verified for forgot_password
    verified_otp = await db.otps.find_one({
        "email": email,
        "purpose": "forgot_password",
        "verified": True,
        "created_at": {"$gte": datetime.utcnow() - timedelta(minutes=10)}
    })
    
    if not verified_otp:
        return {
            "success": False,
            "error": "OTP verification required"
        }
    
    # Update password
    result = await db.users.update_one(
        {"email": email},
        {"$set": {"password": hash_password(new_password)}}
    )
    
    if result.modified_count == 0:
        return {
            "success": False,
            "error": "User not found"
        }
    
    # Invalidate all OTPs for this email
    await db.otps.delete_many({"email": email})
    
    return {
        "success": True,
        "message": "Password reset successfully"
    }

# Cleanup expired OTPs (call periodically)
async def cleanup_expired_otps():
    """Remove expired OTPs"""
    result = await db.otps.delete_many({
        "expires_at": {"$lt": datetime.utcnow()}
    })
    print(f"Cleaned up {result.deleted_count} expired OTPs")


# Authentication Dependency for FastAPI
async def get_current_user(
    authorization: Optional[str] = Header(None),
    x_user_email: Optional[str] = Header(None)
) -> User:
    """
    Dependency to get current authenticated user.
    
    For now, this is a simplified version that accepts user email from headers.
    In production, implement proper JWT token validation.
    
    Usage in endpoints:
        async def my_endpoint(current_user: User = Depends(get_current_user)):
            # current_user.email, current_user.display_name, etc.
    """
    
    # TODO: Implement proper JWT token validation
    # For now, accept email from x-user-email header for development
    # Ensure MongoDB connection is available (try to initialize on-demand)
    global db
    if db is None:
        init_ok = await init_mongodb()
        if not init_ok or db is None:
            raise HTTPException(status_code=503, detail="MongoDB not initialized")

    if x_user_email:
        user_data = await get_user_by_email(x_user_email)
        if user_data:
            return User(
                email=user_data["email"],
                display_name=user_data.get("display_name"),
                role=user_data.get("role"),
                hobbies=user_data.get("hobbies", [])
            )
    
    # If no user found, raise authentication error
    raise HTTPException(
        status_code=401,
        detail="Not authenticated. Please provide x-user-email header."
    )
