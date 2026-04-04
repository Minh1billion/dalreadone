import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # LLM
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
    GROQ_MODEL_ID = os.environ.get("GROQ_MODEL_ID")
    
    DA_TEMPERATURE = float(os.environ.get("DA_TEMPERATURE", 0.2))
    DA_MAX_TOKENS = int(os.environ.get("DA_MAX_TOKENS", 8192))
    DA_CHAIN_RETRY_MAX = int(os.environ.get("DA_CHAIN_RETRY_MAX", 2))
    DA_TASK_TTL = int(os.environ.get("DA_TASK_TTL", 3600))
    DA_CODE_EXEC_TIMEOUT = int(os.environ.get("DA_CODE_EXEC_TIMEOUT", 30))

    # S3 Bucket
    AWS_REGION = os.environ.get("AWS_REGION")
    S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME")
    S3_ACCESS_KEY = os.environ.get("S3_ACCESS_KEY")
    S3_SECRET_KEY = os.environ.get("S3_SECRET_KEY")
    
    # Local Storage (storage for dev)
    LOCAL_STORAGE_PATH = os.environ.get("LOCAL_STORAGE_PATH", "./local_storage")

    # Database
    POSTGRES_USER = os.environ.get("POSTGRES_USER")
    POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD")
    POSTGRES_DB = os.environ.get("POSTGRES_DB")
    POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.environ.get("POSTGRES_PORT", "5432")

    SQL_CONNECTION_STRING = (
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
        f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )

    # Redis
    REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
    REDIS_URL  = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"
    EDA_TASK_TTL = int(os.environ.get("EDA_TASK_TTL", 3600))
    PREPROCESS_TASK_TTL = int(os.environ.get("PREPROCESS_TASK_TTL", 3600))

    # JWT
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
    JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", 15))
    REFRESH_TOKEN_EXPIRE_DAYS = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", 7))

    # OAuth - Google
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI")

    # OAuth - Github
    GITHUB_CLIENT_ID = os.environ.get("GITHUB_CLIENT_ID")
    GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET")
    GITHUB_REDIRECT_URI = os.environ.get("GITHUB_REDIRECT_URI")

    # App
    ENV = os.environ.get("ENV", "development")
    FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")

    # Encryption
    ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY")