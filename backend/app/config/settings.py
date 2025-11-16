from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Configuration
    PROJECT_NAME: str = "Fraud Detection AI System"
    API_V1_STR: str = "/api/v1"
    
    # Database Configuration
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "Tushar16#"
    DB_NAME: str = "fraud_detection"
    
    # OpenAI Configuration
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4.1-mini"  # or gpt-4o-mini
    
    # Security
    SECRET_KEY: str = "7F9K2-PQ5R8-XY3W6-LM1N4-BV7C9-D2Z4A"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    ALLOWED_ORIGINS: list = ["http://localhost:8501", "https://your-domain.com"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
