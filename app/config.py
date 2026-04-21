import os

class Settings:
    SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
    SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    JWT_SECRET = os.environ.get("JWT_SECRET", "")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRE_MINUTES = 60 * 24
    DAILY_API_KEY = os.environ.get("DAILY_API_KEY", "")
    STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
    STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")
    STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
    APP_ENV = os.environ.get("APP_ENV", "development")
    CORS_ORIGINS = ["http://localhost:3000"]


settings = Settings()