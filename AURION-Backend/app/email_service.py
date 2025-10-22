# TEST: Send a test email to any address and log full SendGrid response
import fastapi
router = fastapi.APIRouter()

@router.post("/test-email")
async def send_test_email(email: str):
    subject = "AURION Test Email"
    text = "This is a test email from your AURION backend. If you receive this, SendGrid is working."
    html = f"""
    <html><body><h1>AURION Test Email</h1><p>This is a test email from your backend. If you see this, SendGrid is working!</p></body></html>
    """
    payload = {
        "personalizations": [
            {"to": [{"email": email}], "subject": subject}
        ],
        "from": {"email": settings.SENDER_EMAIL},
        "content": [
            {"type": "text/plain", "value": text},
            {"type": "text/html", "value": html}
        ]
    }
    headers = {
        "Authorization": f"Bearer {settings.SENDGRID_API_KEY}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(SENDGRID_API_URL, json=payload, headers=headers, timeout=10)
        logger.info(f"[TEST EMAIL] SendGrid response: status={response.status_code}, body={response.text}")
        return {"status": response.status_code, "body": response.text}
    except Exception as e:
        logger.error(f"[TEST EMAIL] Exception: {e}")
        return {"error": str(e)}

import requests
from pydantic import EmailStr
from app.core.config import settings
import logging

SENDGRID_API_URL = "https://api.sendgrid.com/v3/mail/send"
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
EMAIL_ENABLED = bool(settings.SENDGRID_API_KEY) and bool(settings.SENDER_EMAIL)

async def send_otp_email(email: EmailStr, otp: str, purpose: str = "signup"):
    """
    Send OTP email to user using SendGrid HTTP API. Logs all errors and returns True/False for delivery acceptance.
    """
    if purpose == "signup":
        subject = "🔐 Your AURION Verification Code"
        greeting = "Welcome to AURION!"
        message_text = "Thank you for signing up. Please use the following code to verify your email:"
    else:
        subject = "🔐 Reset Your AURION Password"
        greeting = "Password Reset Request"
        message_text = "You requested to reset your password. Please use the following code:"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset='UTF-8'>
        <style>
            body {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); margin: 0; padding: 40px 20px; }}
            .otp-box {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; padding: 30px; margin: 30px 0; display: inline-block; }}
            .otp-code {{ font-size: 48px; font-weight: 700; color: white; letter-spacing: 12px; margin: 0; font-family: 'Courier New', monospace; }}
            .expiry {{ font-size: 14px; color: #6b7280; margin-top: 20px; }}
            .warning {{ background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0; border-radius: 8px; text-align: left; }}
            .warning-text {{ font-size: 14px; color: #92400e; margin: 0; }}
            .footer {{ background: #f9fafb; padding: 30px; text-align: center; font-size: 14px; color: #6b7280; }}
            .footer a {{ color: #667eea; text-decoration: none; }}
            .logo {{ font-size: 40px; margin-bottom: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">✨</div>
                <h1>AURION AI</h1>
            </div>
            <div class="content">
                <div class="greeting">{greeting}</div>
                <p class="message">{message_text}</p>
                <div class="otp-box">
                    <p class="otp-code">{otp}</p>
                </div>
                <p class="expiry">⏰ This code will expire in <strong>60 seconds</strong></p>
                <div class="warning">
                    <p class="warning-text">
                        <strong>⚠️ Security Notice:</strong><br>
                        Never share this code with anyone. AURION will never ask for your verification code.
                    </p>
                </div>
                <p class="message">If you didn't request this code, please ignore this email or contact support.</p>
            </div>
            <div class="footer">
                <p>This is an automated message from <strong>AURION AI</strong><br>Your Intelligent AI Assistant<br><a href="{settings.FRONTEND_URL}">Visit AURION</a></p>
                <p style="margin-top: 20px; font-size: 12px; color: #9ca3af;">© 2025 AURION AI. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """

    text = f"""
    {greeting}

    {message_text}

    Your verification code is: {otp}

    This code will expire in 60 seconds.

    If you didn't request this code, please ignore this email.

    ---
    AURION AI - Your Intelligent Assistant
    """

    if not EMAIL_ENABLED:
        logger.info(f"\n{'='*60}")
        logger.info(f"🔐 DEV MODE - OTP EMAIL")
        logger.info(f"{'='*60}")
        logger.info(f"To: {email}")
        logger.info(f"Subject: {subject}")
        logger.info(f"Purpose: {purpose}")
        logger.info(f"\n  YOUR OTP CODE: {otp}")
        logger.info(f"\n  ⏰ Expires in 60 seconds")
        logger.info(f"{'='*60}\n")
        return True

    payload = {
        "personalizations": [
            {"to": [{"email": str(email)}], "subject": subject}
        ],
        "from": {"email": settings.SENDER_EMAIL},
        "content": [
            {"type": "text/plain", "value": text},
            {"type": "text/html", "value": html}
        ]
    }
    headers = {
        "Authorization": f"Bearer {settings.SENDGRID_API_KEY}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(SENDGRID_API_URL, json=payload, headers=headers, timeout=10)
        logger.info(f"SendGrid response for OTP email to {email}: status={response.status_code}, body={response.text}")
        if response.status_code in (200, 202):
            logger.info(f"✅ OTP email sent successfully to {email}")
            return True
        else:
            logger.error(f"❌ SendGrid error sending OTP email to {email}: {response.status_code} {response.text}")
            # Log more details if available
            try:
                error_json = response.json()
                logger.error(f"SendGrid error details: {error_json}")
            except Exception:
                pass
            return False
    except Exception as e:
        logger.error(f"❌ Exception sending OTP email to {email}: {e}")
        return False
# -*- coding: utf-8 -*-

# app/email_service.py
"""
Robust email service for sending OTPs and welcome emails using SendGrid HTTP API only.
"""
import requests
from pydantic import EmailStr
from app.core.config import settings
import logging
import asyncio
import secrets
import string

# SendGrid API endpoint
SENDGRID_API_URL = "https://api.sendgrid.com/v3/mail/send"
from pydantic import EmailStr
from app.core.config import settings
import logging
import asyncio
import secrets
import string

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

EMAIL_ENABLED = bool(settings.SENDGRID_API_KEY) and bool(settings.SENDER_EMAIL)

async def test_smtp_connection() -> bool:
    """Test SMTP connection to diagnose issues with retries"""
    logger.info("SMTP connection test is not applicable when using SendGrid API.")
    return True


    # Plain text fallback
    text = f"""
    {greeting}
    
    {message_text}
    
    Your verification code is: {otp}
    
    This code will expire in 5 minutes.
    
    If you didn't request this code, please ignore this email.
    
    ---
    AURION AI - Your Intelligent Assistant
    """


    # If email is not configured, print to console (DEV MODE)
    if not EMAIL_ENABLED:
        logger.error("❌ Email sending is not enabled. Please set SENDGRID_API_KEY and SENDER_EMAIL.")
        return False



async def send_welcome_email(email: EmailStr, display_name: str):
    """Send welcome email after successful signup"""
    text = f"""
    Welcome {display_name}!
    
    Welcome to AURION AI - Your intelligent assistant powered by cutting-edge AI technology.
    
    We're excited to have you on board! Here's what you can do with AURION:
    - Have natural conversations with advanced AI
    - Manage your calendar and schedule
    - Let autonomous agents handle complex tasks
    - Get personalized insights and recommendations
    - Enjoy enterprise-grade security and privacy
    
    Start chatting now: {settings.FRONTEND_URL}/chat
    
    If you have any questions, feel free to reach out to our support team.
    
    Happy exploring!<br>
    <strong>The AURION Team</strong>
    </p>
    </div>
    <div class="footer">
        <p>© 2025 AURION AI. All rights reserved.</p>
    </div>
    </div>
    </body>
    </html>
    """

    subject = "🎉 Welcome to AURION AI!"
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: 0;
                padding: 40px 20px;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 40px;
                text-align: center;
                color: white;
            }}
            .content {{
                padding: 40px;
            }}
            h1 {{ color: #1f2937; margin-bottom: 20px; }}
            p {{ color: #4b5563; line-height: 1.6; margin-bottom: 15px; }}
            .cta-button {{
                display: inline-block;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px 40px;
                border-radius: 10px;
                text-decoration: none;
                font-weight: 600;
                margin: 20px 0;
            }}
            .footer {{
                background: #f9fafb;
                padding: 30px;
                text-align: center;
                font-size: 14px;
                color: #6b7280;
            }}
            .footer a {{
                color: #667eea;
                text-decoration: none;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="color: white; margin: 0;">✨ Welcome to AURION!</h1>
            </div>
            <div class="content">
                <h1>Hi {display_name}! 👋</h1>
                <p>
                    Welcome to AURION AI - Your intelligent assistant powered by cutting-edge AI technology.
                </p>
                <p>
                    We're excited to have you on board! Here's what you can do with AURION:
                </p>
                <ul style="color: #4b5563; line-height: 1.8;">
                    <li>💬 Have natural conversations with advanced AI</li>
                    <li>📅 Manage your calendar and schedule</li>
                    <li>🤖 Let autonomous agents handle complex tasks</li>
                    <li>📊 Get personalized insights and recommendations</li>
                    <li>🔒 Enjoy enterprise-grade security and privacy</li>
                </ul>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{settings.FRONTEND_URL}/chat" class="cta-button">Start Chatting Now</a>
                </div>
                <p>
                    If you have any questions, feel free to reach out to our support team.
                </p>
                <p>
                    Happy exploring!<br>
                    <strong>The AURION Team</strong>
                </p>
            </div>
            <div class="footer">
                <p>© 2025 AURION AI. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """

    text = f"""
    Welcome {display_name}!
    
    Welcome to AURION AI - Your intelligent assistant powered by cutting-edge AI technology.
    
    We're excited to have you on board! Here's what you can do with AURION:
    - Have natural conversations with advanced AI
    - Manage your calendar and schedule
    - Let autonomous agents handle complex tasks
    - Get personalized insights and recommendations
    - Enjoy enterprise-grade security and privacy
    
    Start chatting now: {settings.FRONTEND_URL}/chat
    
    If you have any questions, feel free to reach out to our support team.
    
    Happy exploring!
    The AURION Team
    """

    # If email is not configured, print to console (DEV MODE)
    if not EMAIL_ENABLED:
        logger.error("❌ Email sending is not enabled. Please set SENDGRID_API_KEY and SENDER_EMAIL.")
        return False

    payload = {
        "personalizations": [
            {
                "to": [{"email": str(email)}],
                "subject": subject
            }
        ],
        "from": {"email": settings.SENDER_EMAIL},
        "content": [
            {"type": "text/plain", "value": text},
            {"type": "text/html", "value": html}
        ]
    }
    headers = {
        "Authorization": f"Bearer {settings.SENDGRID_API_KEY}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(SENDGRID_API_URL, json=payload, headers=headers, timeout=10)
        if response.status_code in (200, 202):
            logger.info(f"✅ Welcome email sent to {email}")
            return True
        else:
            logger.error(f"❌ SendGrid error sending welcome email to {email}: {response.status_code} {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Exception sending welcome email to {email}: {e}")
        return False