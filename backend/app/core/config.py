import os

from dotenv import load_dotenv

load_dotenv()

class Config:
    # LLM
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
    MODEL_ID = os.environ.get("MODEL_ID")
    
    # S3 Bucket
    AWS_REGION = os.environ.get("AWS_REGION")
    S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME")
    S3_ACCESS_KEY = os.environ.get("S3_ACCESS_KEY")
    S3_SECRET_KEY = os.environ.get("S3_SECRET_KEY")
    
    # Database
    POSTGRES_USER = os.environ.get("POSTGRES_USER")
    POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD")
    POSTGRES_DB = os.environ.get("POSTGRES_DB")
    POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.environ.get("PORT", "5432")
    
    SQL_CONNECTION_STRING = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )
    
if __name__ == "__main__":
    pass