from app.core.config import Config

def debug_config():
    print("=== CONFIG DEBUG ===")
    print("MODEL:", Config.MODEL_ID)
    print("REGION:", Config.AWS_REGION)
    print("BUCKET:", Config.S3_BUCKET_NAME)

if __name__ == "__main__":
    debug_config()