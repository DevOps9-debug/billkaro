from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Date, DateTime,
    ForeignKey, JSON, Text, func, UniqueConstraint, Numeric
)
from sqlalchemy.orm import relationship
from app.database import Base

STATE_CODES = {
    "01": "Jammu & Kashmir", "02": "Himachal Pradesh", "03": "Punjab",
    "04": "Chandigarh", "05": "Uttarakhand", "06": "Haryana", "07": "Delhi",
    "08": "Rajasthan", "09": "Uttar Pradesh", "10": "Bihar", "11": "Sikkim",
    "12": "Arunachal Pradesh", "13": "Nagaland", "14": "Manipur", "15": "Mizoram",
    "16": "Tripura", "17": "Meghalaya", "18": "Assam", "19": "West Bengal",
    "20": "Jharkhand", "21": "Odisha", "22": "Chhattisgarh", "23": "Madhya Pradesh",
    "24": "Gujarat", "27": "Maharashtra", "29": "Karnataka", "30": "Goa",
    "32": "Kerala", "33": "Tamil Nadu", "34": "Puducherry", "36": "Telangana",
    "37": "Andhra Pradesh",
}


def state_from_gstin(gstin: str) -> str:
    if not gstin or len(gstin) < 2:
        return ""
    return STATE_CODES.get(gstin[:2], "")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    gstin = Column(String(15), nullable=False)
    state = Column(String(100), default="")
    address = Column(String(500), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    vendor_code = Column(String(50), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    invoices = relationship("Invoice", back_populates="customer")


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(100), nullable=True)
    hsn = Column(String(20), nullable=True)
    price = Column(Float, nullable=False, default=0)
    unit = Column(String(20), default="Nos")
    custom_values = Column(JSON, nullable=True, default=list)
    created_at = Column(DateTime, server_default=func.now())


class CustomColumn(Base):
    __tablename__ = "custom_columns"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_user_column_name"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    sort_order = Column(Integer, default=0)


class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (UniqueConstraint("user_id", "number", name="uq_user_invoice_number"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    number = Column(String(50), nullable=False)
    date = Column(Date, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    customer_name = Column(String(255))
    customer_gstin = Column(String(15))
    customer_state = Column(String(100), default="")
    customer_address = Column(String(500), nullable=True)
    customer_vendor_code = Column(String(50), nullable=True)
    po_number = Column(String(100), nullable=True)

    subtotal = Column(Numeric(12,2), default=0)
    gst_rate = Column(Numeric(5,2), default=18)
    gst_total = Column(Numeric(12,2), default=0)
    grand_total = Column(Numeric(12,2), default=0)
    cgst = Column(Numeric(12,2), default=0)
    sgst = Column(Numeric(12,2), default=0)
    igst = Column(Numeric(12,2), default=0)
    is_intra_state = Column(Boolean, default=True)
    col_snapshot = Column(JSON, nullable=True, default=list)
    tax_breakdown = Column(JSON, nullable=True, default=list)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, server_default=func.now())

    customer = relationship("Customer", back_populates="invoices")
    lines = relationship("InvoiceLine", back_populates="invoice", cascade="all, delete-orphan")


class InvoiceLine(Base):
    __tablename__ = "invoice_lines"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    item_id = Column(Integer, ForeignKey("items.id", ondelete="SET NULL"), nullable=True)
    item_name = Column(String(255))
    hsn = Column(String(20), nullable=True)
    quantity = Column(Float, nullable=False)
    rate = Column(Float, nullable=False)
    unit = Column(String(20), default="")
    amount = Column(Float, nullable=False)
    custom_values = Column(JSON, nullable=True, default=list)

    invoice = relationship("Invoice", back_populates="lines")


class Setting(Base):
    __tablename__ = "settings"
    __table_args__ = (UniqueConstraint("user_id", "key", name="uq_user_setting_key"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    key = Column(String(100), nullable=False)
    value = Column(Text, nullable=True, default="")


DEFAULT_SETTINGS = {
    "biz_name": "",
    "gstin": "03",
    "address": "",
    "phone": "",
    "email": "",
    "about": "",
    "bank_name": "",
    "bank_account": "",
    "bank_ifsc": "",
    "gst_rate": "18",
    "invoice_prefix": "INV",
    "terms_conditions": "1. Interest @ 24% P.A. will be charged on delayed payments.\n2. All disputes are subject to Mohali Jurisdiction only.\n3. E. & O.E.",
}
