import boto3
from app.core.config import Config

def test_s3():
    s3 = boto3.client(
        "s3",
        aws_access_key_id=Config.S3_ACCESS_KEY,
        aws_secret_access_key=Config.S3_SECRET_KEY,
        region_name=Config.AWS_REGION,
    )

    buckets = s3.list_buckets()
    print("Buckets:", [b["Name"] for b in buckets["Buckets"]])

if __name__ == "__main__":
    test_s3()