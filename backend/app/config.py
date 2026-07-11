"""
CareVoice AI Hospital Platform - Application Configuration.

Centralizes all environment-based configuration using Pydantic Settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ---
    APP_NAME: str = "CareVoice AI Hospital"
    DEBUG: bool = False
    BASE_URL: str = "http://localhost:8000"

    # --- Database ---
    DATABASE_URL: str

    # --- Redis ---
    REDIS_URL: str

    # --- JWT Auth ---
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # --- OpenAI ---
    OPENAI_API_KEY: str = ""

    # --- Gemini ---
    GEMINI_API_KEY: str = ""



    # --- Razorpay ---
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""

    # --- Email / SMTP ---
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = "noreply@carevoice.ai"

    # --- Business Config ---
    GST_RATE: float = 18.0
    SLOT_LOCK_TTL_SECONDS: int = 300

    # --- Admin Seeding ---
    ADMIN_EMAIL: str = "admin@carevoice.ai"
    ADMIN_PASSWORD: str = "changeme_in_production"
    ADMIN_FULL_NAME: str = "System Administrator"

    # --- Testing / Demo ---
    # Set to e.g. 99 to reduce Razorpay charges by 99% for testing (₹1500 → ₹15)
    TEST_FEE_DISCOUNT_PERCENT: float = 0.0

    # --- CORS ---
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://anya-carevoice.vercel.app"
    ]


settings = Settings()
