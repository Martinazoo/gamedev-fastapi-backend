from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Mi API"
    VERSION: str = "1.0.0"

    DATABASE_URL: str

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # OAuth Google
    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str


    #OAuth Github
    github_client_id: str
    github_client_secret: str
    FRONTEND_BASE_URL: str 

    class Config:
        env_file = ".env"

settings = Settings()
