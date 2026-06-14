from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database import get_db
from app.auth import get_current_user
from app import models, schemas

router = APIRouter(prefix="/items", tags=["items"])


@router.get("", response_model=list[schemas.ItemOut])
def list_items(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return db.execute(
        select(models.Item).where(models.Item.user_id == user.id).order_by(models.Item.name)
    ).scalars().all()


@router.post("", response_model=schemas.ItemOut, status_code=201)
def create_item(payload: schemas.ItemBase, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    item = models.Item(user_id=user.id, **payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/{item_id}", response_model=schemas.ItemOut)
def get_item(item_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    item = db.get(models.Item, item_id)
    if not item or item.user_id != user.id:
        raise HTTPException(404, "Item not found")
    return item


@router.put("/{item_id}", response_model=schemas.ItemOut)
def update_item(item_id: int, payload: schemas.ItemBase, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    item = db.get(models.Item, item_id)
    if not item or item.user_id != user.id:
        raise HTTPException(404, "Item not found")
    for k, v in payload.model_dump().items():
        setattr(item, k, v)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    item = db.get(models.Item, item_id)
    if not item or item.user_id != user.id:
        raise HTTPException(404, "Item not found")
    db.delete(item)
    db.commit()
    return {"message": "Deleted"}
