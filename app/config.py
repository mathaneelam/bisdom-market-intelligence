from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ANTHROPIC_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    DATABASE_URL: str = "postgresql+asyncpg://bisdom:bisdom_secret@localhost:5432/bisdom_intelligence"
    REDIS_URL: str = "redis://localhost:6379"
    RESEND_API_KEY: str = ""
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    WHATSAPP_TOKEN: str = ""
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    INSTAGRAM_USERNAME: str = ""
    INSTAGRAM_PASSWORD: str = ""
    
    # Delivery Targets
    TARGET_EMAILS: list[str] = ["mathan@bisdom.com"]
    TARGET_PHONES: list[str] = []

    model_config = {"env_file": ".env", "case_sensitive": True}


settings = Settings()
