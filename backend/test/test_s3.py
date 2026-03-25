import io
import boto3

from app.core.config import Config
from app.storage.s3_client import upload_file, delete_file


def test_s3():
    s3 = boto3.client(
        "s3",
        aws_access_key_id=Config.S3_ACCESS_KEY,
        aws_secret_access_key=Config.S3_SECRET_KEY,
        region_name=Config.AWS_REGION,
    )

    buckets = s3.list_buckets()
    assert buckets["Buckets"], "No buckets found"
    print("Buckets:", [b["Name"] for b in buckets["Buckets"]])

    file = io.BytesIO(b"hello world")
    key = "test/test.txt"

    upload_file(file, key)
    print("Upload success:", key)

    delete_file(key)
    print("Cleanup done")

if __name__ == "__main__":
    test_s3()