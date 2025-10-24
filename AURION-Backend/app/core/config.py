# app/core/config.py
# This file reads all our secrets from the .env file
# and makes them available to our application.

import pydantic_settings
import pydantic
import os
from pathlib import Path
import logging  # Added for debugging email settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Settings(pydantic_settings.BaseSettings):
    """
    Settings class to hold all environment variables.
    pydantic will automatically read from the .env file.
    """
    # --- AI APIs ---
    GROQ_API_KEY: str | None = None
    GEMINI_API_KEY: str | None = None
    GOOGLE_GEMINI_API_KEY: str | None = None  # Back-compat alias
    OPENAI_API_KEY: str | None = None
    OPENROUTER_API_KEY: str | None = None
    COHERE_API_KEY: str | None = None
    MISTRAL_API_KEY: str | None = None
    EDENAI_API_KEY: str | None = None
    NLP_CLOUD_API_KEY: str | None = None

    # --- GOOGLE TOOL APIs ---
    GOOGLE_API_KEY: str | None = None
    GOOGLE_SEARCH_CX_ID: str | None = None
    SERPAPI_KEY: str | None = None
    ZENSERP_API_KEY: str | None = None
    YOUTUBE_API_KEY: str | None = None
    FRIEND_GROQ_KEY: str | None = None
    FRIEND_GEMINI_KEY: str | None = None
    FRIEND_YOUTUBE_KEY: str | None = None
    FRIEND_GMAIL_KEY: str | None = None
    
    # --- WEATHER API ---
    WEATHER_API_KEY: str | None = None

    # --- DATABASE APIs ---
    PINECONE_API_KEY: str | None = None
    PINECONE_INDEX_NAME: str | None = None
    REDIS_HOST: str | None = None
    REDIS_PORT: int | None = None
    REDIS_PASSWORD: str | None = None
    REDIS_URL: str | None = None

    # --- EMAIL TOOL API (SendGrid) ---
    SENDGRID_API_KEY: str | None = os.getenv("SENDGRID_API_KEY")
    SENDER_EMAIL: pydantic.EmailStr | None = os.getenv("SENDER_EMAIL")  # Ensures it's a valid email format
    # Set these in your environment or .env file for SendGrid

    # --- SMTP EMAIL CONFIGURATION (for OTP emails) ---
    MAIL_USERNAME: str | None = None  # Gmail address
    MAIL_PASSWORD: pydantic.SecretStr | None = None  # Use SecretStr for security
    MAIL_FROM: str | None = None
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_FROM_NAME: str = "AURION AI"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False

    # --- NEO4J GRAPH DATABASE (Semantic Memory) ---
    NEO4J_URI: str | None = None
    NEO4J_USER: str | None = None
    NEO4J_PASSWORD: str | None = None
    NEO4J_DATABASE: str = "neo4j"
    NEO4J_STARTUP_TIMEOUT_SECS: int = 12

    # --- MongoDB (User Authentication) ---
    MONGODB_URL: str | None = None
    MONGODB_DB_NAME: str = "aurion_auth"
    # Aliases for .env compatibility
    mongo_uri: str | None = pydantic.Field(default=None, alias="mongo_uri")
    mongo_db_name: str | None = pydantic.Field(default=None, alias="mongo_db_name")

    # --- Project Settings ---
    PROJECT_NAME: str = "AURION AI"
    BASE_URL: str = "http://127.0.0.1:8000"  # Server base URL for email links
    FRONTEND_URL: str = "http://localhost:5173"  # Frontend URL for local development
    # CORS origins for frontend
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,https://aurion-2w2m89dqc-rathods-projects-2f0dc844.vercel.app"
    
    # --- JWT Settings (for Admin Authentication) ---
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # This tells pydantic to load variables from the backend .env with an absolute path
    # Resolve to the AURION-Backend/.env regardless of working directory
    _env_file = str(Path(__file__).resolve().parents[2] / ".env")
    model_config = pydantic_settings.SettingsConfigDict(
        env_file=_env_file,
        env_file_encoding='utf-8'
    )

# Create a single instance of the settings that our whole app can import
try:
    settings = Settings()

    # --- Normalize aliases and fallbacks ---
    # Gemini
    if not settings.GEMINI_API_KEY and settings.GOOGLE_GEMINI_API_KEY:
        settings.GEMINI_API_KEY = settings.GOOGLE_GEMINI_API_KEY

    # Google Custom Search CX (common alias variants)
    if not settings.GOOGLE_SEARCH_CX_ID:
        settings.GOOGLE_SEARCH_CX_ID = (
            os.getenv("GOOGLE_CSE_ID")
            or os.getenv("CUSTOM_SEARCH_CX")
            or os.getenv("GOOGLE_SEARCH_ENGINE_ID")
            or os.getenv("SEARCH_ENGINE_ID")
        )

    # Google API Key alias (sometimes named GOOGLE_SEARCH_API_KEY)
    if not settings.GOOGLE_API_KEY:
        settings.GOOGLE_API_KEY = (
            os.getenv("GOOGLE_SEARCH_API_KEY")
            or os.getenv("GOOGLE_CLOUD_API_KEY")
        )

    # SerpAPI alias
    if not settings.SERPAPI_KEY:
        settings.SERPAPI_KEY = os.getenv("SERP_API_KEY")

    # YouTube Data API alias
    if not settings.YOUTUBE_API_KEY:
        settings.YOUTUBE_API_KEY = os.getenv("YOUTUBE_DATA_API_KEY")

    # Email from address fallback (for SendGrid-based mailer)
    if not settings.SENDER_EMAIL and settings.MAIL_FROM:
        settings.SENDER_EMAIL = settings.MAIL_FROM

    # Pinecone index default to avoid None issues
    if not settings.PINECONE_INDEX_NAME:
        settings.PINECONE_INDEX_NAME = "aurion_index"

    logger.info("Settings loaded successfully!")
    logger.info(f"ALLOWED_ORIGINS: {settings.ALLOWED_ORIGINS}")
    logger.info(f"SMTP Config: server={settings.MAIL_SERVER}, port={settings.MAIL_PORT}, "
                f"username={settings.MAIL_USERNAME}, from={settings.MAIL_FROM}")
    logger.info(f"SendGrid Config: from={settings.SENDER_EMAIL}, api_key={'set' if settings.SENDGRID_API_KEY else '<missing>'}")

    # Debug: Verify API keys are loaded (mask to 4 chars)
    def mask(val: str | None) -> str:
        return (val[:4] + "***") if val else "<missing>"

    logger.info("-- API/Service Configuration --")
    logger.info(f"  ✓ GROQ_API_KEY: {mask(settings.GROQ_API_KEY)}")
    logger.info(f"  ✓ GEMINI_API_KEY: {mask(settings.GEMINI_API_KEY)}")
    logger.info(f"  ✓ OPENAI_API_KEY: {mask(settings.OPENAI_API_KEY)}")
    logger.info(f"  ✓ OPENROUTER_API_KEY: {mask(settings.OPENROUTER_API_KEY)}")
    logger.info(f"  ✓ COHERE_API_KEY: {mask(settings.COHERE_API_KEY)}")
    logger.info(f"  ✓ EDENAI_API_KEY: {mask(settings.EDENAI_API_KEY)}")
    logger.info(f"  ✓ MISTRAL_API_KEY: {mask(settings.MISTRAL_API_KEY)}")
    logger.info(f"  ✓ GOOGLE_API_KEY: {mask(settings.GOOGLE_API_KEY)}")
    logger.info(f"  ✓ GOOGLE_SEARCH_CX_ID: {settings.GOOGLE_SEARCH_CX_ID or '<missing>'}")
    logger.info(f"  ✓ SERPAPI_KEY: {mask(settings.SERPAPI_KEY)}")
    logger.info(f"  ✓ ZENSERP_API_KEY: {mask(settings.ZENSERP_API_KEY)}")
    logger.info(f"  ✓ YOUTUBE_API_KEY: {mask(settings.YOUTUBE_API_KEY)}")
    logger.info(f"  ✓ WEATHER_API_KEY: {mask(settings.WEATHER_API_KEY)}")
    logger.info(f"  ✓ PINECONE_API_KEY: {mask(settings.PINECONE_API_KEY)}  (index: {settings.PINECONE_INDEX_NAME})")
    logger.info(f"  ✓ REDIS_URL: {bool(settings.REDIS_URL)}  (host: {settings.REDIS_HOST}, port: {settings.REDIS_PORT})")
    logger.info(f"  ✓ SENDGRID_API_KEY: {mask(settings.SENDGRID_API_KEY)}  (from: {settings.SENDER_EMAIL})")
    logger.info(f"  ✓ SMTP MAIL_FROM: {settings.MAIL_FROM}")
    logger.info(f"  ✓ NEO4J_URI: {'set' if settings.NEO4J_URI else '<missing>'}")

    # Warnings for common misconfigurations
    if not (settings.GOOGLE_API_KEY and settings.GOOGLE_SEARCH_CX_ID):
        logger.warning("Web search: Needs GOOGLE_API_KEY and GOOGLE_SEARCH_CX_ID (or SERPAPI_KEY as fallback)")
    if not (settings.GEMINI_API_KEY or settings.FRIEND_GEMINI_KEY):
        logger.warning("Gemini: No API key found (GEMINI_API_KEY or GOOGLE_GEMINI_API_KEY)")
    if not (settings.GROQ_API_KEY or settings.FRIEND_GROQ_KEY):
        logger.warning("Groq: No API key found (GROQ_API_KEY)")
    if not settings.SENDER_EMAIL and not settings.MAIL_FROM:
        logger.warning("Email: Set SENDER_EMAIL (SendGrid) or MAIL_FROM (SMTP)")
    if not settings.MAIL_USERNAME or not settings.MAIL_PASSWORD:
        logger.warning("SMTP Email: MAIL_USERNAME and MAIL_PASSWORD must be set for email functionality")
    
except pydantic.ValidationError as e:
    logger.error(f"FATAL ERROR: Could not load .env settings: {e}")
    exit(1)