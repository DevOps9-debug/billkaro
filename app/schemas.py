from pydantic import BaseModel, field_validator, EmailStr
from typing import Optional, List, Dict
from datetime import date


# ---------- Auth ----------
class UserCreate(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_min_len(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- Customer ----------
class CustomerBase(BaseModel):
    name: str
    gstin: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    vendor_code: Optional[str] = None

    @field_validator("gstin")
    @classmethod
    def gstin_upper(cls, v):
        v = v.strip().upper()
        if len(v) != 15:
            raise ValueError("GSTIN must be 15 characters")
        return v


class CustomerOut(CustomerBase):
    id: int
    state: str

    class Config:
        from_attributes = True


# ---------- Item ----------
class ItemBase(BaseModel):
    name: str
    code: Optional[str] = None
    hsn: Optional[str] = None
    price: float
    unit: str = "Nos"
    custom_values: Optional[List[str]] = []


class ItemOut(ItemBase):
    id: int

    class Config:
        from_attributes = True


# ---------- Custom Column ----------
class CustomColumnCreate(BaseModel):
    name: str


class CustomColumnOut(BaseModel):
    id: int
    name: str
    sort_order: int

    class Config:
        from_attributes = True


class ReorderRequest(BaseModel):
    ids: List[int]


# ---------- Settings ----------
class SettingsUpdate(BaseModel):
    biz_name: Optional[str] = ""
    gstin: Optional[str] = ""
    address: Optional[str] = ""
    phone: Optional[str] = ""
    email: Optional[str] = ""
    about: Optional[str] = ""
    bank_name: Optional[str] = ""
    bank_account: Optional[str] = ""
    bank_ifsc: Optional[str] = ""
    gst_rate: Optional[str] = "18"
    invoice_prefix: Optional[str] = "INV"
    terms_conditions: Optional[str] = ""


# ---------- Invoice ----------
class InvoiceLineIn(BaseModel):
    item_id: Optional[int] = None
    item_name: str
    hsn: Optional[str] = ""
    quantity: float
    rate: float
    custom_values: Optional[List[str]] = []


class InvoiceCreate(BaseModel):
    customer_id: int
    date: date
    lines: List[InvoiceLineIn]
    po_number: str | None = None
    invoice_number: str | None = None


class InvoiceLineOut(BaseModel):
    id: int
    item_id: Optional[int]
    item_name: str
    hsn: Optional[str]
    quantity: float
    rate: float
    amount: float
    custom_values: Optional[List[str]] = []

    class Config:
        from_attributes = True


class InvoiceOut(BaseModel):
    id: int
    number: str
    date: date
    customer_name: str
    customer_gstin: str
    customer_state: str
    customer_address: Optional[str]
    customer_vendor_code: Optional[str] = None
    subtotal: float
    gst_rate: float
    cgst: float
    sgst: float
    igst: float
    gst_total: float
    grand_total: float
    is_intra_state: bool
    col_snapshot: Optional[List[str]] = []
    lines: List[InvoiceLineOut] = []
    status: str = "active"
    po_number: str | None = None

    class Config:
        from_attributes = True


class DashboardOut(BaseModel):
    period_label: str
    summary: Dict
    all_time: Dict
    recent: List[Dict]
