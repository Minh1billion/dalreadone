import logging

from sqlalchemy.orm import Session

from app.core.encryption import encrypt, decrypt
from app.models.user_settings import UserSettings

logger = logging.getLogger(__name__)


def get_or_create(db: Session, user_id: int) -> UserSettings:
    settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
    if not settings:
        logger.debug("get_or_create: no settings found for user_id=%s — creating", user_id)
        settings = UserSettings(user_id=user_id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


def get_api_key(db: Session, user_id: int) -> str | None:
    """Return decrypted key, or None if not set."""
    settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()

    logger.debug(
        "get_api_key user_id=%s  settings_found=%s  use_own_key=%s  has_encrypted_key=%s",
        user_id,
        settings is not None,
        getattr(settings, "use_own_key", None),
        bool(getattr(settings, "groq_api_key_encrypted", None)),
    )

    if settings and settings.use_own_key and settings.groq_api_key_encrypted:
        try:
            key = decrypt(settings.groq_api_key_encrypted)
            logger.debug(
                "get_api_key user_id=%s  decrypted OK  key_prefix=%s",
                user_id,
                key[:8] if key else "(empty)",
            )
            return key
        except Exception as exc:
            logger.error(
                "get_api_key user_id=%s  decrypt FAILED: %s — falling back to system key",
                user_id, exc,
            )
            return None

    logger.debug(
        "get_api_key user_id=%s  → using system key (use_own_key=%s)",
        user_id,
        getattr(settings, "use_own_key", False),
    )
    return None


def update_settings(
    db: Session,
    user_id: int,
    use_own_key: bool,
    groq_api_key: str | None = None,
) -> UserSettings:
    settings = get_or_create(db, user_id)

    logger.debug(
        "update_settings user_id=%s  use_own_key=%s  providing_new_key=%s",
        user_id, use_own_key, groq_api_key is not None,
    )

    settings.use_own_key = use_own_key

    if groq_api_key is not None:
        try:
            settings.groq_api_key_encrypted = encrypt(groq_api_key)
            logger.debug("update_settings user_id=%s  key encrypted OK", user_id)
        except Exception as exc:
            logger.error("update_settings user_id=%s  encrypt FAILED: %s", user_id, exc)
            raise

    db.commit()
    db.refresh(settings)
    return settings


def delete_api_key(db: Session, user_id: int) -> UserSettings:
    settings = get_or_create(db, user_id)
    logger.debug("delete_api_key user_id=%s", user_id)
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