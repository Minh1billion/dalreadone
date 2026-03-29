from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, field_validator

from app.db.session import get_db
from app.core.security import get_current_user
from app.models import User
from app.services import settings_service

router = APIRouter(prefix="/settings", tags=["settings"])


class SettingsResponse(BaseModel):
    use_own_key:      bool
    groq_api_key:     str | None  # masked, e.g. "gsk_****...****Ab"


class UpdateSettingsRequest(BaseModel):
    use_own_key:  bool
    groq_api_key: str | None = None

    @field_validator("groq_api_key")
    @classmethod
    def validate_key_format(cls, v, info):
        if v is not None:
            v = v.strip()
            if not v.startswith("gsk_"):
                raise ValueError("Groq API key must start with 'gsk_'")
            if len(v) < 20:
                raise ValueError("Groq API key is too short")
        return v


@router.get("", response_model=SettingsResponse)
def get_settings(
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    settings = settings_service.get_or_create(db, current_user.id)

    masked_key = None
    if settings.groq_api_key_encrypted:
        from app.core.encryption import decrypt
        masked_key = settings_service.mask_api_key(decrypt(settings.groq_api_key_encrypted))

    return SettingsResponse(
        use_own_key=settings.use_own_key,
        groq_api_key=masked_key,
    )


@router.put("", response_model=SettingsResponse)
def update_settings(
    body:         UpdateSettingsRequest,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    # Bật use_own_key nhưng không truyền key và chưa có key cũ → lỗi
    if body.use_own_key and body.groq_api_key is None:
        existing = settings_service.get_or_create(db, current_user.id)
        if not existing.groq_api_key_encrypted:
            raise HTTPException(
                status_code=400,
                detail="Please provide a Groq API key before enabling this option.",
            )

    settings = settings_service.update_settings(
        db,
        user_id=current_user.id,
        use_own_key=body.use_own_key,
        groq_api_key=body.groq_api_key,
    )

    masked_key = None
    if settings.groq_api_key_encrypted:
        from app.core.encryption import decrypt
        masked_key = settings_service.mask_api_key(decrypt(settings.groq_api_key_encrypted))

    return SettingsResponse(
        use_own_key=settings.use_own_key,
        groq_api_key=masked_key,
    )


@router.delete("/groq-key", response_model=SettingsResponse)
def delete_api_key(
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    settings = settings_service.delete_api_key(db, current_user.id)
    return SettingsResponse(
        use_own_key=settings.use_own_key,
        groq_api_key=None,
    )