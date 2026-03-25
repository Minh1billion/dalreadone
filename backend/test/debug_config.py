from app.core.config import Config


def debug_config():
    fields = {
        "MODEL_ID": Config.MODEL_ID,
        "AWS_REGION": Config.AWS_REGION,
        "S3_BUCKET_NAME": Config.S3_BUCKET_NAME,
        "POSTGRES_HOST": Config.POSTGRES_HOST,
        "POSTGRES_PORT": Config.POSTGRES_PORT,
        "POSTGRES_DB": Config.POSTGRES_DB,
    }

    print("=== CONFIG DEBUG ===")
    for key, val in fields.items():
        status = val if val else "MISSING"
        print(f"{key}: {status}")


if __name__ == "__main__":
    debug_config()