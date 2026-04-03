import io
from pathlib import Path
from app.core.config import Config

LOCAL_STORAGE_DIR = Path(Config.LOCAL_STORAGE_PATH)


def _resolve(key: str) -> Path:
    path = LOCAL_STORAGE_DIR / key
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def upload_file(file, key: str) -> str:
    dest = _resolve(key)
    content = file.read() if hasattr(file, "read") else file
    dest.write_bytes(content if isinstance(content, bytes) else content.encode())
    return key


def delete_file(key: str):
    path = _resolve(key)
    if path.exists():
        path.unlink()


def get_file_bytes(key: str) -> bytes:
    path = _resolve(key)
    if not path.exists():
        raise FileNotFoundError(f"File not found in local storage: {key}")
    return path.read_bytes()