import boto3
from app.core.config import Config

s3 = boto3.client(
    "s3",
    aws_access_key_id=Config.S3_ACCESS_KEY,
    aws_secret_access_key=Config.S3_SECRET_KEY,
    region_name=Config.AWS_REGION
)

def upload_file(file, key):
    s3.upload_fileobj(file, Config.S3_BUCKET_NAME, key)
    return key

def delete_file(key):
    s3.delete_object(Bucket=Config.S3_BUCKET_NAME, Key=key)