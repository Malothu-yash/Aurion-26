# app/email_service.py
# Email service for sending OTPs using Gmail SMTP or other providers

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
from app.core.config import settings
import logging
from typing import List

# Set up logging
logger = logging.getLogger(__name__)

# Check if email is configured
EMAIL_ENABLED = (
    bool(settings.MAIL_USERNAME) and 
    bool(settings.MAIL_PASSWORD)
)

if EMAIL_ENABLED:
    # Email configuration
    conf = ConnectionConfig(
        MAIL_USERNAME=settings.MAIL_USERNAME,
        MAIL_PASSWORD=settings.MAIL_PASSWORD,  # Already SecretStr from config
        MAIL_FROM=settings.MAIL_FROM,
        MAIL_PORT=settings.MAIL_PORT,
        MAIL_SERVER=settings.MAIL_SERVER,
        MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
        MAIL_STARTTLS=settings.MAIL_STARTTLS,
        MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True
    )

    # Initialize FastMail
    fm = FastMail(conf)
    logger.info("✅ Email service configured successfully")
else:
    fm = None
    logger.warning("⚠️ Email not configured - OTPs will be printed to console")

async def send_otp_email(email: EmailStr, otp: str, purpose: str = "signup"):
    """
    Send OTP email to user
    
    Args:
        email: Recipient email address
        otp: 4-digit OTP code
        purpose: 'signup' or 'forgot_password'
    """
    
    # Customize subject and message based on purpose
    if purpose == "signup":
        subject = "🔐 Your AURION Verification Code"
        greeting = "Welcome to AURION!"
        message_text = "Thank you for signing up. Please use the following code to verify your email:"
    else:
        subject = "🔐 Reset Your AURION Password"
        greeting = "Password Reset Request"
        message_text = "You requested to reset your password. Please use the following code:"
    
    # HTML email template
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
            .header h1 {{
                margin: 0;
                font-size: 32px;
                font-weight: 700;
            }}
            .content {{
                padding: 40px;
                text-align: center;
            }}
            .greeting {{
                font-size: 24px;
                font-weight: 600;
                color: #1f2937;
                margin-bottom: 20px;
            }}
            .message {{
                font-size: 16px;
                color: #4b5563;
                margin-bottom: 30px;
                line-height: 1.6;
            }}
            .otp-box {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 12px;
                padding: 30px;
                margin: 30px 0;
                display: inline-block;
            }}
            .otp-code {{
                font-size: 48px;
                font-weight: 700;
                color: white;
                letter-spacing: 12px;
                margin: 0;
                font-family: 'Courier New', monospace;
            }}
            .expiry {{
                font-size: 14px;
                color: #6b7280;
                margin-top: 20px;
            }}
            .warning {{
                background: #fef3c7;
                border-left: 4px solid #f59e0b;
                padding: 15px;
                margin: 20px 0;
                border-radius: 8px;
                text-align: left;
            }}
            .warning-text {{
                font-size: 14px;
                color: #92400e;
                margin: 0;
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
            .logo {{
                font-size: 40px;
                margin-bottom: 10px;
            }}
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
                
                <p class="message">
                    If you didn't request this code, please ignore this email or contact support.
                </p>
            </div>
            
            <div class="footer">
                <p>
                    This is an automated message from <strong>AURION AI</strong><br>
                    Your Intelligent AI Assistant<br>
                    <a href="{settings.FRONTEND_URL}">Visit AURION</a>
                </p>
                <p style="margin-top: 20px; font-size: 12px; color: #9ca3af;">
                    © 2025 AURION AI. All rights reserved.
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    # Plain text fallback
    text = f"""
    {greeting}
    
    {message_text}
    
    Your verification code is: {otp}
    
    This code will expire in 60 seconds.
    
    If you didn't request this code, please ignore this email.
    
    ---
    AURION AI - Your Intelligent Assistant
    """

    # If email is not configured, print to console (DEV MODE)
    if not EMAIL_ENABLED or fm is None:
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

    try:
        message = MessageSchema(
            subject=subject,
            recipients=[email],
            body=text,
            html=html,
            subtype=MessageType.html
        )

        await fm.send_message(message)
        logger.info(f"✅ OTP email sent successfully to {email}")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to send OTP email to {email}: {e}")
        # Fallback to console
        logger.info(f"🔐 FALLBACK - OTP for {email}: {otp}")
        return False

async def send_welcome_email(email: EmailStr, display_name: str):
    """Send welcome email after successful signup"""

    # Skip if email not configured
    if not EMAIL_ENABLED or fm is None:
        logger.info(f"🎉 Welcome {display_name}! (Email skipped - dev mode)")
        return True

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

    try:
        message = MessageSchema(
            subject="🎉 Welcome to AURION AI!",
            recipients=[email],
            body=f"Welcome {display_name}! Start your AI journey with AURION.",
            html=html,
            subtype=MessageType.html
        )

        await fm.send_message(message)
        logger.info(f"✅ Welcome email sent to {email}")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to send welcome email: {e}")
        return False