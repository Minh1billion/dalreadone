from sqlalchemy.orm import Session

from app.core.encryption import encrypt, decrypt
from app.models.user_settings import UserSettings


def get_or_create(db: Session, user_id: int) -> UserSettings:
    settings = db.query(UserSettings).filter(UserSettings.user_id==user_id).first()
    if not settings:
        settings = UserSettings(user_id=user_id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
        
    return settings

def get_api_key(db: Session, user_id: int) -> str | None:
    """Return decrypted key, or None if not set."""
    settings = db.query(UserSettings).filter(UserSettings.user_id==user_id).first()
    if settings and settings.use_own_key and settings.groq_api_key_encrypted:
        return decrypt(settings.groq_api_key_encrypted)
    
    return None

def update_settings(
    db: Session,
    user_id: int,
    use_own_key: bool,
    groq_api_key: str | None = None,
) -> UserSettings:
    settings = get_or_create(db, user_id)
    
    settings.use_own_key = use_own_key
    
    if groq_api_key is not None:
        settings.groq_api_key_encrypted = encrypt(groq_api_key)
        
    db.commit()
    db.refresh(settings)
    
    return settings

def delete_api_key(db: Session, user_id: int) -> UserSettings:
    settings = get_or_create(db, user_id)
    settings.use_own_key = False
    settings.groq_api_key_encrypted = None
    
    db.commit()
    db.refresh(settings)
    
    return settings

def mask_api_key(key: str) -> str:
    """gsk_****...****Gh"""
    if len(key) <= 8:
        return "****"
    
    return key[:6] + "****" + key[-4:]