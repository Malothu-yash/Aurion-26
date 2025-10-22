# app/core/config.py
# This file reads all our secrets from the .env file
# and makes them available to our application.

import pydantic_settings
import pydantic
import os
from pathlib import Path

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

    # --- EMAIL TOOL API ---
    SENDGRID_API_KEY: str | None = None
    SENDER_EMAIL: pydantic.EmailStr | None = None # Ensures it's a valid email format

    # --- SMTP EMAIL CONFIGURATION (for OTP emails) ---
    MAIL_USERNAME: str | None = None  # Gmail address
    MAIL_PASSWORD: str | None = None  # Gmail App Password
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

    # --- Project Settings ---
    PROJECT_NAME: str = "AURION AI"
    BASE_URL: str = "http://127.0.0.1:8000"  # Server base URL for email links
    FRONTEND_URL: str = "http://localhost:5173"  # Frontend URL for local development
    # Updated to include production frontend URL for CORS
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,https://aurion-2w2m89dqc-rathods-projects-2f0dc844.vercel.app"
    
    # --- JWT Settings (for Admin Authentication) ---
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # This tells pydantic to load variables from the backend .env with an absolute path
    # Resolve to the AURION-Backend/.env regardless of working directory
    _env_path = str(Path(__file__).resolve().parents[2] / ".env")
    model_config = pydantic_settings.SettingsConfigDict(env_file=_env_path)

# Create a single instance of the settings that our whole app can import
# We will import `settings` from this file in other parts of our code
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

    print("Settings loaded successfully!")

    # Debug: Verify API keys are loaded (mask to 4 chars)
    def mask(val: str | None) -> str:
        return (val[:4] + "***") if val else "<missing>"

    print("-- API/Service Configuration --")
    print(f"  ✓ GROQ_API_KEY: {mask(settings.GROQ_API_KEY)}")
    print(f"  ✓ GEMINI_API_KEY: {mask(settings.GEMINI_API_KEY)}")
    print(f"  ✓ OPENAI_API_KEY: {mask(settings.OPENAI_API_KEY)}")
    print(f"  ✓ OPENROUTER_API_KEY: {mask(settings.OPENROUTER_API_KEY)}")
    print(f"  ✓ COHERE_API_KEY: {mask(settings.COHERE_API_KEY)}")
    print(f"  ✓ EDENAI_API_KEY: {mask(settings.EDENAI_API_KEY)}")
    print(f"  ✓ MISTRAL_API_KEY: {mask(settings.MISTRAL_API_KEY)}")
    print(f"  ✓ GOOGLE_API_KEY: {mask(settings.GOOGLE_API_KEY)}")
    print(f"  ✓ GOOGLE_SEARCH_CX_ID: {settings.GOOGLE_SEARCH_CX_ID or '<missing>'}")
    print(f"  ✓ SERPAPI_KEY: {mask(settings.SERPAPI_KEY)}")
    print(f"  ✓ ZENSERP_API_KEY: {mask(settings.ZENSERP_API_KEY)}")
    print(f"  ✓ YOUTUBE_API_KEY: {mask(settings.YOUTUBE_API_KEY)}")
    print(f"  ✓ WEATHER_API_KEY: {mask(settings.WEATHER_API_KEY)}")
    print(f"  ✓ PINECONE_API_KEY: {mask(settings.PINECONE_API_KEY)}  (index: {settings.PINECONE_INDEX_NAME})")
    print(f"  ✓ REDIS_URL: {bool(settings.REDIS_URL)}  (host: {settings.REDIS_HOST}, port: {settings.REDIS_PORT})")
    print(f"  ✓ SENDGRID_API_KEY: {mask(settings.SENDGRID_API_KEY)}  (from: {settings.SENDER_EMAIL})")
    print(f"  ✓ SMTP MAIL_FROM: {settings.MAIL_FROM}")
    print(f"  ✓ NEO4J_URI: {'set' if settings.NEO4J_URI else '<missing>'}")
    print(f"  ✓ ALLOWED_ORIGINS: {settings.ALLOWED_ORIGINS}")  # Added to debug CORS

    # Warnings for common misconfigurations
    if not (settings.GOOGLE_API_KEY and settings.GOOGLE_SEARCH_CX_ID):
        print("  ! Web search: Needs GOOGLE_API_KEY and GOOGLE_SEARCH_CX_ID (or SERPAPI_KEY as fallback)")
    if not (settings.GEMINI_API_KEY or settings.FRIEND_GEMINI_KEY):
        print("  ! Gemini: No API key found (GEMINI_API_KEY or GOOGLE_GEMINI_API_KEY)")
    if not (settings.GROQ_API_KEY or settings.FRIEND_GROQ_KEY):
        print("  ! Groq: No API key found (GROQ_API_KEY)")
    if not settings.SENDER_EMAIL and not settings.MAIL_FROM:
        print("  ! Email: Set SENDER_EMAIL (SendGrid) or MAIL_FROM (SMTP)")
    
except pydantic.ValidationError as e:
    print("--- FATAL ERROR: Could not load .env settings. ---")
    print(e)
    # Exit if settings are missing - the app can't run.
    exit(1)