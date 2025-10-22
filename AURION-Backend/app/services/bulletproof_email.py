"""
Bulletproof Email Sender
Tries FastAPI-Mail first, falls back to SMTP, ensures delivery
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from app.core.config import settings

try:
    from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
    FASTAPI_MAIL_AVAILABLE = True
except Exception as e:
    print(f"⚠️ fastapi-mail not available: {e}")
    FASTAPI_MAIL_AVAILABLE = False

logger = logging.getLogger(__name__)


class BulletproofEmailSender:
    """
    Email sender with automatic fallback
    Strategy: FastAPI-Mail → SMTP → Log error
    """
    
    def __init__(self):
        self.fastapi_mail_enabled = False
        self.smtp_enabled = False
        
        # Try to set up FastAPI-Mail
        if FASTAPI_MAIL_AVAILABLE and settings.MAIL_USERNAME and settings.MAIL_PASSWORD:
            try:
                self.mail_conf = ConnectionConfig(
                    MAIL_USERNAME=settings.MAIL_USERNAME,
                    MAIL_PASSWORD=settings.MAIL_PASSWORD,
                    MAIL_FROM=settings.MAIL_FROM,
                    MAIL_PORT=settings.MAIL_PORT,
                    MAIL_SERVER=settings.MAIL_SERVER,
                    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
                    MAIL_STARTTLS=settings.MAIL_STARTTLS,
                    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
                    USE_CREDENTIALS=True,
                    VALIDATE_CERTS=True
                )
                self.fm = FastMail(self.mail_conf)
                self.fastapi_mail_enabled = True
                logger.info("✅ FastAPI-Mail configured")
            except Exception as e:
                logger.warning(f"⚠️ FastAPI-Mail setup failed: {e}")
        
        # Check if we have SMTP credentials as fallback
        if settings.MAIL_USERNAME and settings.MAIL_PASSWORD:
            self.smtp_enabled = True
            logger.info("✅ SMTP fallback available")
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        plain_body: Optional[str] = None
    ) -> bool:
        """
        Send email with automatic fallback
        Returns True if sent successfully, False otherwise
        """
        
        # Try Method 1: FastAPI-Mail (preferred)
        if self.fastapi_mail_enabled:
            try:
                message = MessageSchema(
                    subject=subject,
                    recipients=[to_email],
                    html=html_body,
                    subtype="html"
                )
                await self.fm.send_message(message)
                logger.info(f"✅ Email sent via FastAPI-Mail to {to_email}")
                return True
            except Exception as e:
                logger.warning(f"⚠️ FastAPI-Mail failed: {e}, trying SMTP fallback...")
        
        # Try Method 2: Direct SMTP (fallback)
        if self.smtp_enabled:
            try:
                return await self._send_via_smtp(to_email, subject, html_body, plain_body)
            except Exception as e:
                logger.error(f"❌ SMTP fallback also failed: {e}")
        
        # Both methods failed
        logger.error(f"❌ All email methods failed for {to_email}")
        return False
    
    async def _send_via_smtp(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        plain_body: Optional[str] = None
    ) -> bool:
        """
        Send email directly via SMTP
        Works with Gmail, Outlook, etc.
        """
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{settings.MAIL_FROM_NAME} <{settings.MAIL_FROM}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add plain text version (fallback)
            if plain_body:
                part1 = MIMEText(plain_body, 'plain')
                msg.attach(part1)
            
            # Add HTML version
            part2 = MIMEText(html_body, 'html')
            msg.attach(part2)
            
            # Determine SSL/TLS mode
            if settings.MAIL_SSL_TLS:
                # Use SSL (port 465)
                logger.info(f"Connecting to {settings.MAIL_SERVER}:{settings.MAIL_PORT} with SSL...")
                server = smtplib.SMTP_SSL(settings.MAIL_SERVER, settings.MAIL_PORT, timeout=30)
            else:
                # Use STARTTLS (port 587 or 25)
                logger.info(f"Connecting to {settings.MAIL_SERVER}:{settings.MAIL_PORT} with STARTTLS...")
                server = smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT, timeout=30)
                if settings.MAIL_STARTTLS:
                    server.starttls()
            
            # Login and send
            server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"✅ Email sent via SMTP to {to_email}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"❌ SMTP Authentication failed: {e}")
            logger.error("Check your MAIL_USERNAME and MAIL_PASSWORD in .env")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"❌ SMTP error: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected SMTP error: {e}")
            return False


# Global instance
email_sender = BulletproofEmailSender()


async def send_reminder_email_bulletproof(
    to_email: str,
    task_description: str,
    task_id: str,
    user_id: str = "user",
    scheduled_time: str = None
) -> bool:
    """
    Send reminder email with bulletproof delivery
    Uses multiple methods to ensure delivery
    
    Args:
        to_email: Recipient email
        task_description: User's original task message
        task_id: Unique task identifier
        user_id: User identifier
        scheduled_time: Human-readable time (e.g., "09:00 AM, October 22, 2025")
    """
    
    # Build email content
    base_url = settings.BASE_URL if hasattr(settings, 'BASE_URL') else "http://127.0.0.1:8000"
    complete_url = f"{base_url}/api/v1/task/action?task_id={task_id}&action=complete&user_id={user_id}"
    snooze_url = f"{base_url}/api/v1/task/action?task_id={task_id}&action=snooze&user_id={user_id}"
    
    # Create a proper title (capitalize first letter of each word)
    title = task_description.strip().capitalize()
    
    # Format time nicely if provided
    from datetime import datetime
    import pytz
    if not scheduled_time:
        now = datetime.now(pytz.timezone('Asia/Kolkata'))
        scheduled_time = now.strftime("%I:%M %p, %B %d, %Y")
    
    subject = f"⏰ AURION Reminder: {title[:50]}{'...' if len(title) > 50 else ''}"
    
    # HTML version - Beautiful, professional template
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                background-color: #f0f2f5;
                margin: 0;
                padding: 40px 20px;
                line-height: 1.6;
            }}
            .email-wrapper {{
                max-width: 600px;
                margin: 0 auto;
                background-color: #ffffff;
                border-radius: 12px;
                box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 40px 30px;
                text-align: center;
            }}
            .header-icon {{
                font-size: 48px;
                margin-bottom: 10px;
            }}
            .header h1 {{
                color: #ffffff;
                font-size: 26px;
                font-weight: 700;
                margin: 0;
                text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }}
            .content {{
                padding: 40px 30px;
            }}
            .greeting {{
                color: #333333;
                font-size: 18px;
                margin-bottom: 20px;
                font-weight: 500;
            }}
            .time-badge {{
                display: inline-block;
                background: #e3f2fd;
                color: #1976d2;
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 14px;
                font-weight: 600;
                margin-bottom: 20px;
            }}
            .task-card {{
                background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
                border-left: 5px solid #667eea;
                padding: 25px;
                border-radius: 10px;
                margin: 25px 0;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
            }}
            .task-label {{
                color: #6c757d;
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 1px;
                font-weight: 600;
                margin-bottom: 10px;
            }}
            .task-title {{
                color: #1a1a1a;
                font-size: 24px;
                font-weight: 700;
                margin-bottom: 12px;
                line-height: 1.3;
            }}
            .task-description {{
                color: #495057;
                font-size: 16px;
                line-height: 1.6;
                margin-top: 10px;
            }}
            .divider {{
                height: 1px;
                background: linear-gradient(to right, transparent, #dee2e6, transparent);
                margin: 30px 0;
            }}
            .action-section {{
                text-align: center;
                margin: 35px 0;
            }}
            .action-title {{
                color: #495057;
                font-size: 16px;
                margin-bottom: 20px;
                font-weight: 500;
            }}
            .button-group {{
                display: flex;
                justify-content: center;
                gap: 15px;
                flex-wrap: wrap;
            }}
            .btn {{
                display: inline-block;
                padding: 16px 32px;
                text-decoration: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: 15px;
                transition: all 0.3s ease;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                text-align: center;
                min-width: 180px;
            }}
            .btn-complete {{
                background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
                color: #ffffff;
            }}
            .btn-complete:hover {{
                box-shadow: 0 6px 16px rgba(76, 175, 80, 0.4);
                transform: translateY(-2px);
            }}
            .btn-snooze {{
                background: linear-gradient(135deg, #ffd54f 0%, #ffca28 100%);
                color: #1a1a1a;
            }}
            .btn-snooze:hover {{
                box-shadow: 0 6px 16px rgba(255, 202, 40, 0.4);
                transform: translateY(-2px);
            }}
            .footer {{
                background-color: #f8f9fa;
                padding: 30px;
                text-align: center;
                border-top: 1px solid #e9ecef;
            }}
            .footer-brand {{
                color: #667eea;
                font-weight: 700;
                font-size: 16px;
                margin-bottom: 10px;
            }}
            .footer-text {{
                color: #6c757d;
                font-size: 13px;
                line-height: 1.6;
            }}
            .footer-links {{
                margin-top: 15px;
                padding-top: 15px;
                border-top: 1px solid #dee2e6;
            }}
            .task-id {{
                color: #adb5bd;
                font-size: 11px;
                font-family: 'Courier New', monospace;
                margin-top: 8px;
            }}
            @media only screen and (max-width: 600px) {{
                .email-wrapper {{
                    border-radius: 0;
                }}
                .content {{
                    padding: 30px 20px;
                }}
                .button-group {{
                    flex-direction: column;
                    gap: 12px;
                }}
                .btn {{
                    width: 100%;
                    min-width: auto;
                }}
                .task-title {{
                    font-size: 20px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="email-wrapper">
            <div class="header">
                <div class="header-icon">⏰</div>
                <h1>AURION Reminder</h1>
            </div>
            
            <div class="content">
                <div class="greeting">
                    Hey there! 👋
                </div>
                
                <div class="time-badge">
                    🕐 {scheduled_time}
                </div>
                
                <p style="color: #495057; font-size: 15px; margin-bottom: 20px;">
                    Your scheduled reminder is here! Here's what you asked me to remind you about:
                </p>
                
                <div class="task-card">
                    <div class="task-label">📋 Your Task</div>
                    <div class="task-title">{title}</div>
                    <div class="task-description">
                        <strong>Original Message:</strong> "{task_description}"
                    </div>
                </div>
                
                <div class="divider"></div>
                
                <div class="action-section">
                    <div class="action-title">
                        ✨ Quick Actions
                    </div>
                    <div class="button-group">
                        <a href="{complete_url}" class="btn btn-complete">
                            ✅ Mark Complete
                        </a>
                        <a href="{snooze_url}" class="btn btn-snooze">
                            ⏰ Snooze 1 Hour
                        </a>
                    </div>
                </div>
            </div>
            
            <div class="footer">
                <div class="footer-brand">🤖 AURION AI</div>
                <div class="footer-text">
                    Your Intelligent Personal Assistant<br>
                    Making your life easier, one reminder at a time
                </div>
                <div class="footer-links">
                    <div class="task-id">Task ID: {task_id}</div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Plain text version (fallback)
    plain_body = f"""
═══════════════════════════════════════
⏰ AURION REMINDER
═══════════════════════════════════════

Hey there! 👋

📅 Scheduled Time: {scheduled_time}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 YOUR TASK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{title}

Original Message: "{task_description}"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✨ QUICK ACTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Mark Complete:
{complete_url}

⏰ Snooze 1 Hour:
{snooze_url}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Task ID: {task_id}

🤖 AURION AI - Your Intelligent Personal Assistant
Making your life easier, one reminder at a time
    """
    
    # Send with bulletproof method
    success = await email_sender.send_email(
        to_email=to_email,
        subject=subject,
        html_body=html_body,
        plain_body=plain_body
    )
    
    if success:
        logger.info(f"✅ Reminder email delivered to {to_email}")
    else:
        logger.error(f"❌ Failed to deliver reminder to {to_email}")
    
    return success
