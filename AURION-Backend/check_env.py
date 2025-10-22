"""
Quick diagnostics for AURION backend environment variables.
Runs config loading and prints a summarized status of all important keys.
"""
from app.core.config import settings


def mask(val: str | None) -> str:
    return (val[:4] + "***") if val else "<missing>"

print("\nAURION environment diagnostics:\n")
print(f"PROJECT_NAME: {settings.PROJECT_NAME}")
print("\n-- AI Providers --")
print(f"GROQ_API_KEY: {mask(settings.GROQ_API_KEY)}")
print(f"GEMINI_API_KEY: {mask(settings.GEMINI_API_KEY)}")
print(f"OPENAI_API_KEY: {mask(settings.OPENAI_API_KEY)}")

print("\n-- Web/Search --")
print(f"GOOGLE_API_KEY: {mask(settings.GOOGLE_API_KEY)}")
print(f"GOOGLE_SEARCH_CX_ID: {settings.GOOGLE_SEARCH_CX_ID or '<missing>'}")
print(f"SERPAPI_KEY: {mask(settings.SERPAPI_KEY)}")
print(f"YOUTUBE_API_KEY: {mask(settings.YOUTUBE_API_KEY)}")

print("\n-- Weather --")
print(f"WEATHER_API_KEY: {mask(settings.WEATHER_API_KEY)}")

print("\n-- Vector DB (Pinecone) --")
print(f"PINECONE_API_KEY: {mask(settings.PINECONE_API_KEY)}  (index: {settings.PINECONE_INDEX_NAME})")

print("\n-- Redis --")
print(f"REDIS_URL: {bool(settings.REDIS_URL)}  (host: {settings.REDIS_HOST}, port: {settings.REDIS_PORT})")

print("\n-- Email --")
print(f"SENDGRID_API_KEY: {mask(settings.SENDGRID_API_KEY)}  (from: {settings.SENDER_EMAIL or settings.MAIL_FROM})")
print(f"SMTP MAIL_FROM: {settings.MAIL_FROM}")

print("\n-- Neo4j --")
print(f"NEO4J_URI: {'set' if settings.NEO4J_URI else '<missing>'}")
print(f"NEO4J_USER: {'set' if settings.NEO4J_USER else '<missing>'}")
print(f"NEO4J_PASSWORD: {'set' if settings.NEO4J_PASSWORD else '<missing>'}")

# High-level checks
problems = []
if not (settings.GEMINI_API_KEY or settings.FRIEND_GEMINI_KEY):
    problems.append("Gemini: missing GEMINI_API_KEY/GOOGLE_GEMINI_API_KEY")
if not (settings.GROQ_API_KEY or settings.FRIEND_GROQ_KEY):
    problems.append("Groq: missing GROQ_API_KEY")
if not (settings.GOOGLE_API_KEY and settings.GOOGLE_SEARCH_CX_ID) and not settings.SERPAPI_KEY:
    problems.append("Web search: need GOOGLE_API_KEY+GOOGLE_SEARCH_CX_ID or SERPAPI_KEY")
if not settings.SENDER_EMAIL and not settings.MAIL_FROM:
    problems.append("Email: set SENDER_EMAIL (SendGrid) or MAIL_FROM (SMTP)")

print("\nSummary:")
if problems:
    for p in problems:
        print(f" - {p}")
else:
    print(" All required keys appear configured.")
