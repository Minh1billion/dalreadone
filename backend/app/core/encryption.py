from cryptography.fernet import Fernet
from app.core.config import Config

_fernet = Fernet(Config.ENCRYPTION_KEY.encode())

def encrypt(text: str) -> str:
    return _fernet.encrypt(text.encode()).decode()

def decrypt(text: str) -> str:
    return _fernet.decrypt(text.encode()).decode()