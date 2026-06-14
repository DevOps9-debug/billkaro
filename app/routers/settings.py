from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database import get_db
from app.auth import get_current_user
from app import models, schemas

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("")
def get_settings(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    rows = db.execute(select(models.Setting).where(models.Setting.user_id == user.id)).scalars().all()
    s = {row.key: row.value for row in rows}
    for k, v in models.DEFAULT_SETTINGS.items():
        s.setdefault(k, v)
    return s


@router.put("")
def update_settings(payload: schemas.SettingsUpdate, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    data = payload.model_dump()
    for key, value in data.items():
        setting = db.execute(
            select(models.Setting).where(models.Setting.user_id == user.id, models.Setting.key == key)
        ).scalar_one_or_none()
        if setting:
            setting.value = value or ""
        else:
            db.add(models.Setting(user_id=user.id, key=key, value=value or ""))
    db.commit()
    return {"message": "Settings saved"}
