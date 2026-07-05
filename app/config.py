from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OLLAMA_BASE_URL: str = "http://localhost:11434/v1"
    OLLAMA_API_KEY: str = ""
    OLLAMA_MODEL: str = "llama3"
    DATABASE_URL: str = "postgresql+asyncpg://bisdom:bisdom_secret@localhost:5432/bisdom_intelligence"
    REDIS_URL: str = "redis://localhost:6379"
    RESEND_API_KEY: str = ""
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    WHATSAPP_TOKEN: str = ""
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    INSTAGRAM_USERNAME: str = ""
    INSTAGRAM_PASSWORD: str = ""
    REDDIT_CLIENT_ID: str = ""
    REDDIT_CLIENT_SECRET: str = ""

    TARGET_EMAILS: list[str] = ["mathan@bisdom.com"]
    TARGET_PHONES: list[str] = []

    model_config = {"env_file": ".env", "case_sensitive": True}


settings = Settings()

if settings.DATABASE_URL and settings.DATABASE_URL.startswith("postgres://"):
    settings.DATABASE_URL = settings.DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif settings.DATABASE_URL and settings.DATABASE_URL.startswith("postgresql://"):
    settings.DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

if "?" in settings.DATABASE_URL:
    settings.DATABASE_URL = settings.DATABASE_URL.split("?")[0]

# Enforce SSL for remote Postgres hosts (Neon, Supabase, Railway, etc.)
if settings.DATABASE_URL and "localhost" not in settings.DATABASE_URL:
    settings.DATABASE_URL += "?ssl=require"
