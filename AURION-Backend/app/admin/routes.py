# app/admin/routes.py
# Admin API routes

from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Optional
from datetime import timedelta

from app.admin.models import (
    AdminLoginRequest, AdminLoginResponse, CreateAdminRequest,
    UserUpdateRequest, APIKeyUpdateRequest, ServerActionRequest
)
from app.admin.auth import (
    authenticate_admin, create_access_token, get_current_admin,
    create_admin, log_admin_action
)
from app.admin.services import admin_services

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])

# ===========================
# AUTHENTICATION
# ===========================

@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(request: AdminLoginRequest):
    """Admin login endpoint"""
    result = await authenticate_admin(request.email, request.password)
    
    if not result["success"]:
        raise HTTPException(status_code=401, detail="Unauthorized Access")
    
    # Create JWT token
    token = create_access_token(
        data={"sub": result["email"], "role": result["role"]},
        expires_delta=timedelta(hours=8)
    )
    
    # Log the login
    await log_admin_action(
        result["admin_id"],
        "admin_login",
        details={"email": result["email"]}
    )
    
    return AdminLoginResponse(
        success=True,
        token=token,
        admin_id=result["admin_id"],
        email=result["email"],
        role=result["role"]
    )

@router.post("/logout")
async def admin_logout(admin: dict = Depends(get_current_admin)):
    """Admin logout (client should delete token)"""
    await log_admin_action(admin["admin_id"], "admin_logout")
    return {"success": True, "message": "Logged out successfully"}

@router.get("/me")
async def get_current_admin_info(admin: dict = Depends(get_current_admin)):
    """Get current admin info"""
    return admin

# ===========================
# DASHBOARD & STATISTICS
# ===========================

@router.get("/dashboard/stats")
async def get_dashboard_stats(admin: dict = Depends(get_current_admin)):
    """Get dashboard statistics"""
    stats = await admin_services.get_system_stats()
    api_stats = await admin_services.get_api_usage_stats()
    
    return {
        "system": stats,
        "api_usage": api_stats
    }

# ===========================
# USER MANAGEMENT
# ===========================

@router.get("/users")
async def get_users(
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = None,
    status: Optional[str] = None,
    admin: dict = Depends(get_current_admin)
):
    """Get all users with pagination and filters"""
    result = await admin_services.get_all_users(skip, limit, search, status)
    
    await log_admin_action(
        admin["admin_id"],
        "view_users",
        details={"skip": skip, "limit": limit, "search": search}
    )
    
    return result

@router.get("/users/{user_id}")
async def get_user_details(
    user_id: str,
    admin: dict = Depends(get_current_admin)
):
    """Get detailed user information"""
    user = await admin_services.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user's memory stats
    memory_stats = await admin_services.get_user_memory_stats(user_id)
    
    await log_admin_action(
        admin["admin_id"],
        "view_user_details",
        target=user_id
    )
    
    return {
        "user": user,
        "memory_stats": memory_stats
    }

@router.patch("/users/{user_id}")
async def update_user(
    user_id: str,
    updates: UserUpdateRequest,
    admin: dict = Depends(get_current_admin)
):
    """Update user details"""
    # Check permissions
    if admin["role"] not in ["super_admin", "api_manager"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    update_data = {}
    if updates.status:
        update_data["status"] = updates.status
    if updates.role:
        update_data["role"] = updates.role
    if updates.display_name:
        update_data["display_name"] = updates.display_name
    
    success = await admin_services.update_user(user_id, update_data)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update user")
    
    await log_admin_action(
        admin["admin_id"],
        "update_user",
        target=user_id,
        details=update_data
    )
    
    return {"success": True, "message": "User updated successfully"}

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    admin: dict = Depends(get_current_admin)
):
    """Delete user"""
    # Only super admin can delete users
    if admin["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Only super admin can delete users")
    
    success = await admin_services.delete_user(user_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to delete user")
    
    await log_admin_action(
        admin["admin_id"],
        "delete_user",
        target=user_id
    )
    
    return {"success": True, "message": "User deleted successfully"}

@router.post("/users/{user_id}/suspend")
async def suspend_user(
    user_id: str,
    admin: dict = Depends(get_current_admin)
):
    """Suspend user account"""
    success = await admin_services.update_user(user_id, {"status": "suspended"})
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to suspend user")
    
    await log_admin_action(
        admin["admin_id"],
        "suspend_user",
        target=user_id
    )
    
    return {"success": True, "message": "User suspended successfully"}

@router.post("/users/{user_id}/reactivate")
async def reactivate_user(
    user_id: str,
    admin: dict = Depends(get_current_admin)
):
    """Reactivate suspended user"""
    success = await admin_services.update_user(user_id, {"status": "active"})
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to reactivate user")
    
    await log_admin_action(
        admin["admin_id"],
        "reactivate_user",
        target=user_id
    )
    
    return {"success": True, "message": "User reactivated successfully"}

@router.post("/users/{user_id}/promote")
async def promote_user_to_admin(
    user_id: str,
    admin: dict = Depends(get_current_admin)
):
    """Promote user to admin"""
    if admin["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Only super admin can promote users")
    
    success = await admin_services.update_user(user_id, {"role": "admin"})
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to promote user")
    
    await log_admin_action(
        admin["admin_id"],
        "promote_user",
        target=user_id
    )
    
    return {"success": True, "message": "User promoted to admin"}

# ===========================
# API MANAGEMENT
# ===========================

@router.get("/api/usage")
async def get_api_usage(admin: dict = Depends(get_current_admin)):
    """Get API usage statistics"""
    stats = await admin_services.get_api_usage_stats()
    return {"api_usage": stats}

@router.post("/api/update-key")
async def update_api_key(
    request: APIKeyUpdateRequest,
    admin: dict = Depends(get_current_admin)
):
    """Update API key in .env file"""
    if admin["role"] not in ["super_admin", "api_manager"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Map provider to env key (only supported providers)
    provider_keys = {
        "groq": "GROQ_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "nlp_cloud": "NLP_CLOUD_API_KEY"
    }
    
    env_key = provider_keys.get(request.provider)
    if not env_key:
        raise HTTPException(status_code=400, detail="Unknown provider")
    
    success = admin_services.update_env_file(env_key, request.api_key)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update API key")
    
    await log_admin_action(
        admin["admin_id"],
        "update_api_key",
        target=request.provider,
        details={"key": "***" + request.api_key[-4:]}  # Log only last 4 chars
    )
    
    return {
        "success": True,
        "message": f"API key for {request.provider} updated. Server restart required."
    }

# ===========================
# MEMORY MANAGEMENT
# ===========================

@router.get("/memory/stats")
async def get_memory_stats(admin: dict = Depends(get_current_admin)):
    """Get overall memory usage statistics"""
    stats = await admin_services.get_system_stats()
    return {
        "total_memory_mb": stats["total_memory_usage"],
        "timestamp": stats["timestamp"]
    }

@router.get("/memory/user/{user_id}")
async def get_user_memory(
    user_id: str,
    admin: dict = Depends(get_current_admin)
):
    """Get specific user's memory data"""
    memory_stats = await admin_services.get_user_memory_stats(user_id)
    return memory_stats

# ===========================
# LOGS & AUDIT
# ===========================

@router.get("/logs/audit")
async def get_audit_logs(
    skip: int = 0,
    limit: int = 50,
    admin: dict = Depends(get_current_admin)
):
    """Get admin audit logs"""
    logs = await admin_services.get_audit_logs(skip, limit)
    return logs

@router.get("/logs/system")
async def get_system_logs(
    skip: int = 0,
    limit: int = 100,
    admin: dict = Depends(get_current_admin)
):
    """Get system logs"""
    logs = await admin_services.get_system_logs(skip, limit)
    return logs

# ===========================
# ADMIN MANAGEMENT
# ===========================

@router.post("/admins/create")
async def create_new_admin(
    request: CreateAdminRequest,
    admin: dict = Depends(get_current_admin)
):
    """Create a new admin (super admin only)"""
    if admin["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Only super admin can create admins")
    
    result = await create_admin(
        request.email,
        request.password,
        request.display_name,
        request.role
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    await log_admin_action(
        admin["admin_id"],
        "create_admin",
        target=result["admin_id"],
        details={"email": request.email, "role": request.role}
    )
    
    return result

# ===========================
# SERVER CONTROL
# ===========================

@router.get("/server/status")
async def get_server_status(admin: dict = Depends(get_current_admin)):
    """Get server status"""
    stats = await admin_services.get_system_stats()
    return {
        "status": "running",
        "cpu_usage": stats["cpu_usage"],
        "memory_usage": stats["memory_usage"],
        "uptime": stats["server_uptime"]
    }

@router.post("/server/action")
async def server_action(
    request: ServerActionRequest,
    admin: dict = Depends(get_current_admin)
):
    """Perform server action (start/stop/restart)"""
    if admin["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Only super admin can control server")
    
    await log_admin_action(
        admin["admin_id"],
        f"server_{request.action}",
        details={"action": request.action}
    )
    
    # Note: Actual implementation would use PM2 or subprocess
    return {
        "success": True,
        "message": f"Server {request.action} command queued. (Implementation required)"
    }
