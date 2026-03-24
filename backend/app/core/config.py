import os

from dotenv import load_dotenv

load_dotenv()

class Config:
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
    MODEL_ID = os.environ.get("MODEL_ID")
    
    AWS_REGION = os.environ.get("AWS_REGION")
    S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME")
    S3_ACCESS_KEY = os.environ.get("S3_ACCESS_KEY")
    S3_SECRET_KEY = os.environ.get("S3_SECRET_KEY")
    
if __name__ == "__main__":
    pass