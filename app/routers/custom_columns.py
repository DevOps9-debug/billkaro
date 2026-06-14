from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.database import get_db
from app.auth import get_current_user
from app import models, schemas

router = APIRouter(prefix="/custom-columns", tags=["custom-columns"])


@router.get("", response_model=list[schemas.CustomColumnOut])
def list_columns(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return db.execute(
        select(models.CustomColumn).where(models.CustomColumn.user_id == user.id).order_by(models.CustomColumn.sort_order)
    ).scalars().all()


@router.post("", response_model=schemas.CustomColumnOut, status_code=201)
def create_column(payload: schemas.CustomColumnCreate, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    existing = db.execute(
        select(models.CustomColumn).where(
            models.CustomColumn.user_id == user.id,
            models.CustomColumn.name == payload.name,
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(400, "Column already exists")

    max_order = db.execute(
        select(func.max(models.CustomColumn.sort_order)).where(models.CustomColumn.user_id == user.id)
    ).scalar() or 0
    col = models.CustomColumn(user_id=user.id, name=payload.name, sort_order=max_order + 1)
    db.add(col)
    db.commit()
    db.refresh(col)
    return col


@router.delete("/{col_id}")
def delete_column(col_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    col = db.get(models.CustomColumn, col_id)
    if not col or col.user_id != user.id:
        raise HTTPException(404, "Column not found")
    db.delete(col)
    db.commit()
    return {"message": "Deleted"}


@router.post("/reorder")
def reorder_columns(payload: schemas.ReorderRequest, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    for order, col_id in enumerate(payload.ids, start=1):
        col = db.get(models.CustomColumn, col_id)
        if col and col.user_id == user.id:
            col.sort_order = order
    db.commit()
    return {"message": "Reordered"}
