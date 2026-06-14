from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database import get_db
from app.auth import get_current_user
from app import models, schemas

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("", response_model=list[schemas.CustomerOut])
def list_customers(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return db.execute(
        select(models.Customer).where(models.Customer.user_id == user.id).order_by(models.Customer.name)
    ).scalars().all()


@router.post("", response_model=schemas.CustomerOut, status_code=201)
def create_customer(payload: schemas.CustomerBase, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    customer = models.Customer(
        user_id=user.id,
        name=payload.name,
        gstin=payload.gstin,
        state=models.state_from_gstin(payload.gstin),
        address=payload.address,
        phone=payload.phone,
        email=payload.email,
        vendor_code=payload.vendor_code,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("/{customer_id}", response_model=schemas.CustomerOut)
def get_customer(customer_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    customer = db.get(models.Customer, customer_id)
    if not customer or customer.user_id != user.id:
        raise HTTPException(404, "Customer not found")
    return customer


@router.put("/{customer_id}", response_model=schemas.CustomerOut)
def update_customer(customer_id: int, payload: schemas.CustomerBase, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    customer = db.get(models.Customer, customer_id)
    if not customer or customer.user_id != user.id:
        raise HTTPException(404, "Customer not found")
    customer.name = payload.name
    customer.gstin = payload.gstin
    customer.state = models.state_from_gstin(payload.gstin)
    customer.address = payload.address
    customer.phone = payload.phone
    customer.email = payload.email
    customer.vendor_code = payload.vendor_code
    db.commit()
    db.refresh(customer)
    return customer


@router.delete("/{customer_id}")
def delete_customer(customer_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    customer = db.get(models.Customer, customer_id)
    if not customer or customer.user_id != user.id:
        raise HTTPException(404, "Customer not found")
    db.delete(customer)
    db.commit()
    return {"message": "Deleted"}
