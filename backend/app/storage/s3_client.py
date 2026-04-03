from app.core.config import Config

if Config.ENV == "development":
    from app.storage.local_client import upload_file, delete_file, get_file_bytes
else:
    import boto3

    s3 = boto3.client(
        "s3",
        aws_access_key_id=Config.S3_ACCESS_KEY,
        aws_secret_access_key=Config.S3_SECRET_KEY,
        region_name=Config.AWS_REGION,
    )

    def upload_file(file, key: str) -> str:
        s3.upload_fileobj(file, Config.S3_BUCKET_NAME, key)
        return key

    def delete_file(key: str):
        s3.delete_object(Bucket=Config.S3_BUCKET_NAME, Key=key)

    def get_file_bytes(s3_key: str) -> bytes:
        response = s3.get_object(Bucket=Config.S3_BUCKET_NAME, Key=s3_key)
        return response["Body"].read()