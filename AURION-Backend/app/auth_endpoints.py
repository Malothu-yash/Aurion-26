# app/auth_endpoints.py
# FastAPI routes for authentication

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from app.auth_db import (
    create_user, authenticate_user, create_otp, verify_otp,
    reset_password, get_user_by_email
)
from app.email_service import send_otp_email, send_welcome_email

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

# Request Models
class SignupStep1Request(BaseModel):
    email: EmailStr
    password: str
    confirm_password: str

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str
    purpose: str = "signup"

class SignupStep2Request(BaseModel):
    email: EmailStr
    display_name: str
    role: str
    hobbies: List[str]
    password: str  # From step 1

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    new_password: str
    confirm_password: str

class ResendOTPRequest(BaseModel):
    email: EmailStr
    purpose: str = "signup"

# Endpoints
@router.post("/signup/step1")
async def signup_step1(data: SignupStep1Request, background_tasks: BackgroundTasks):
    """Step 1: Validate email/password and send OTP"""
    
    # Validate passwords match
    if data.password != data.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    
    # Check password strength
    if len(data.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    
    # Check if email already exists
    existing_user = await get_user_by_email(data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Generate and send OTP
    result = await create_otp(data.email, purpose="signup")
    
    if not result["success"]:
        raise HTTPException(status_code=429, detail=result["error"])
    
    # Send OTP via email in background
    background_tasks.add_task(send_otp_email, data.email, result["otp"], "signup")
    
    return {
        "success": True,
        "message": "OTP sent to your email",
        "expires_in": result["expires_in"],
        "otp": result["otp"]  # REMOVE IN PRODUCTION - for testing only
    }

@router.post("/verify-otp")
async def verify_otp_endpoint(data: VerifyOTPRequest):
    """Verify OTP"""
    result = await verify_otp(data.email, data.otp, data.purpose)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@router.post("/resend-otp")
async def resend_otp(data: ResendOTPRequest, background_tasks: BackgroundTasks):
    """Resend OTP"""
    result = await create_otp(data.email, purpose=data.purpose)
    
    if not result["success"]:
        raise HTTPException(status_code=429, detail=result["error"])
    
    background_tasks.add_task(send_otp_email, data.email, result["otp"], data.purpose)
    
    return {
        "success": True,
        "message": "OTP resent",
        "expires_in": result["expires_in"],
        "otp": result["otp"]  # REMOVE IN PRODUCTION
    }

@router.post("/signup/step2")
async def signup_step2(data: SignupStep2Request, background_tasks: BackgroundTasks):
    """Step 2: Complete signup with display name, role, hobbies"""
    
    # Verify OTP was completed (check if verified OTP exists)
    # This is a security measure to ensure step 1 was completed
    
    # Create user
    result = await create_user(
        email=data.email,
        password=data.password,
        display_name=data.display_name,
        role=data.role,
        hobbies=data.hobbies
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    # Send welcome email in background
    background_tasks.add_task(send_welcome_email, data.email, data.display_name)
    
    return {
        "success": True,
        "message": "Account created successfully",
        "user": {
            "email": result["email"],
            "display_name": result["display_name"]
        }
    }

@router.post("/login")
async def login(data: LoginRequest):
    """Login with email and password"""
    result = await authenticate_user(data.email, data.password)
    
    if not result["success"]:
        raise HTTPException(status_code=401, detail=result["error"])
    
    return {
        "success": True,
        "message": "Login successful",
        "user": {
            "user_id": result["user_id"],
            "email": result["email"],
            "display_name": result["display_name"],
            "role": result["role"],
            "hobbies": result["hobbies"]
        }
    }

@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordRequest, background_tasks: BackgroundTasks):
    """Request password reset OTP"""
    
    # Check if user exists
    user = await get_user_by_email(data.email)
    if not user:
        # Don't reveal if email exists - security measure
        return {
            "success": True,
            "message": "If the email exists, an OTP has been sent"
        }
    
    # Generate OTP
    result = await create_otp(data.email, purpose="forgot_password")
    
    if not result["success"]:
        raise HTTPException(status_code=429, detail=result["error"])
    
    # Send OTP
    background_tasks.add_task(send_otp_email, data.email, result["otp"], "forgot_password")
    
    return {
        "success": True,
        "message": "OTP sent to your email",
        "expires_in": result["expires_in"],
        "otp": result["otp"]  # REMOVE IN PRODUCTION
    }

@router.post("/reset-password")
async def reset_password_endpoint(data: ResetPasswordRequest):
    """Reset password after OTP verification"""
    
    # Validate passwords match
    if data.new_password != data.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    
    # Check password strength
    if len(data.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    
    # Reset password
    result = await reset_password(data.email, data.new_password)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {
        "success": True,
        "message": "Password reset successfully"
    }

@router.get("/me")
async def get_current_user(user_id: str):
    """Get current user info (mock endpoint - implement with JWT)"""
    # TODO: Implement proper JWT authentication
    return {
        "user_id": user_id,
        "message": "This endpoint needs JWT implementation"
    }
