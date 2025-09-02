from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Información del proyecto
    PROJECT_NAME: str = "Mi API"
    VERSION: str = "1.0.0"

    # Base de datos
    DATABASE_URL: str

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Entorno
    ENV: str = "development"  

    # OAuth Google
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str

    # OAuth Github
    GITHUB_CLIENT_ID: str
    GITHUB_CLIENT_SECRET: str

    # Frontend
    FRONTEND_BASE_URL: str

    class Config:
        env_file = ".env"
        case_sensitive = True  

settings = Settings()
