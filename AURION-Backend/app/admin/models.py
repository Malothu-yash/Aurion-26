# app/admin/models.py
# Pydantic models for admin endpoints

from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class AdminRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    API_MANAGER = "api_manager"
    MEMORY_AUDITOR = "memory_auditor"
    LIMITED_ADMIN = "limited_admin"

class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str

class AdminLoginResponse(BaseModel):
    success: bool
    token: Optional[str] = None
    admin_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    message: Optional[str] = None

class UserStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    INACTIVE = "inactive"

class UserUpdateRequest(BaseModel):
    status: Optional[UserStatus] = None
    role: Optional[str] = None
    display_name: Optional[str] = None

class CreateAdminRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: str
    role: AdminRole

class APIKeyUpdateRequest(BaseModel):
    provider: str  # groq, gemini, openai, etc.
    api_key: str
    enabled: bool = True

class ServerActionRequest(BaseModel):
    action: str  # start, stop, restart

class AuditLog(BaseModel):
    admin_id: str
    action: str
    target: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime
    ip_address: Optional[str] = None

class APIUsageStats(BaseModel):
    provider: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_latency: float
    last_used: Optional[datetime] = None

class SystemStats(BaseModel):
    total_users: int
    active_users: int
    inactive_users: int
    suspended_users: int
    total_memory_usage: float  # in MB
    server_uptime: float  # in seconds
    cpu_usage: float
    memory_usage: float
    api_usage: List[APIUsageStats]
