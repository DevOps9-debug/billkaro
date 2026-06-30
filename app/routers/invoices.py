import csv
import io
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, func
from app.database import get_db
from app.auth import get_current_user
from app import models, schemas
from app.pdf import render_invoice_pdf, render_invoices_pdf

router = APIRouter(prefix="/invoices", tags=["invoices"])


def _user_settings(db: Session, user_id: int) -> dict:
    rows = db.execute(select(models.Setting).where(models.Setting.user_id == user_id)).scalars().all()
    s = {row.key: row.value for row in rows}
    for k, v in models.DEFAULT_SETTINGS.items():
        s.setdefault(k, v)
    return s


@router.get("/next-number")
def get_next_number(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    """Preview the next invoice number (does not increment). Never resets — continuous forever."""
    settings = _user_settings(db, user.id)
    prefix = settings.get("invoice_prefix", "INV") or "INV"

    seq_setting = db.execute(
        select(models.Setting).where(models.Setting.user_id == user.id, models.Setting.key == "invoice_seq")
    ).scalar_one_or_none()

    current_seq = int(seq_setting.value) if seq_setting and seq_setting.value else 0
    next_seq = current_seq + 1
    return {"number": f"{prefix}-{str(next_seq).zfill(4)}"}


@router.get("", response_model=list[schemas.InvoiceOut])
def list_invoices(
    month: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    query = (
        select(models.Invoice)
        .options(selectinload(models.Invoice.lines))
        .where(models.Invoice.user_id == user.id)
        .order_by(models.Invoice.date.desc(), models.Invoice.id.desc())
    )
    invoices = db.execute(query).scalars().all()

    if month:
        invoices = [i for i in invoices if i.date.strftime("%Y-%m") == month]
    if date_from:
        invoices = [i for i in invoices if i.date >= date_from]
    if date_to:
        invoices = [i for i in invoices if i.date <= date_to]

    return invoices


@router.post("", response_model=schemas.InvoiceOut, status_code=201)
def create_invoice(payload: schemas.InvoiceCreate, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    customer = db.get(models.Customer, payload.customer_id)
    if not customer or customer.user_id != user.id:
        raise HTTPException(404, "Customer not found")

    if not payload.lines:
        raise HTTPException(400, "Invoice must have at least one line item")

    settings = _user_settings(db, user.id)
    my_gstin = settings.get("gstin", "03") or "03"
    gst_rate = float(settings.get("gst_rate", "18") or 18)
    prefix = settings.get("invoice_prefix", "INV") or "INV"

    is_intra = customer.gstin[:2] == my_gstin[:2]

    subtotal = sum(line.quantity * line.rate for line in payload.lines)
    gst_amt = subtotal * gst_rate / 100
    cgst = gst_amt / 2 if is_intra else 0
    sgst = gst_amt / 2 if is_intra else 0
    igst = 0 if is_intra else gst_amt
    # Group by HSN for tax breakdown table
    hsn_groups = {}
    for line in payload.lines:
        hsn = line.hsn or "—"
        line_amount = line.quantity * line.rate
        if hsn not in hsn_groups:
            hsn_groups[hsn] = 0
        hsn_groups[hsn] += line_amount

    tax_breakdown = []
    for hsn, taxable in hsn_groups.items():
        hsn_gst = taxable * gst_rate / 100
        tax_breakdown.append({
            "hsn": hsn,
            "rate": gst_rate,
            "taxable": round(taxable, 2),
            "cgst": round(hsn_gst / 2, 2) if is_intra else 0,
            "sgst": round(hsn_gst / 2, 2) if is_intra else 0,
            "igst": round(hsn_gst, 2) if not is_intra else 0,
        })

    # ---- Invoice numbering — continuous, never resets, editable ----
    seq_setting = db.execute(
        select(models.Setting).where(models.Setting.user_id == user.id, models.Setting.key == "invoice_seq")
    ).scalar_one_or_none()

    current_seq = int(seq_setting.value) if seq_setting and seq_setting.value else 0

    if payload.invoice_number:
        # Father typed a custom number — use it and extract sequence from it
        number = payload.invoice_number.strip()
        # Try to extract the numeric part from the end (e.g. "INV-0026" -> 26)
        try:
            seq_val = int(number.split("-")[-1])
        except (ValueError, IndexError):
            seq_val = current_seq + 1
    else:
        # Auto-generate next number
        seq_val = current_seq + 1
        number = f"{prefix}-{str(seq_val).zfill(4)}"

    # Save the sequence so next invoice continues from here
    if seq_setting:
        seq_setting.value = str(seq_val)
    else:
        db.add(models.Setting(user_id=user.id, key="invoice_seq", value=str(seq_val)))
    # ----------------------------------------------------------------

    col_snapshot = [
        c.name for c in db.execute(
            select(models.CustomColumn)
            .where(models.CustomColumn.user_id == user.id)
            .order_by(models.CustomColumn.sort_order)
        ).scalars().all()
    ]

    invoice = models.Invoice(
        user_id=user.id,
        number=number,
        date=payload.date,
        customer_id=customer.id,
        customer_name=customer.name,
        customer_gstin=customer.gstin,
        customer_state=customer.state,
        customer_address=customer.address,
        customer_vendor_code=customer.vendor_code,
        po_number=payload.po_number,
        subtotal=round(subtotal, 2),
        gst_rate=gst_rate,
        cgst=round(cgst, 2),
        sgst=round(sgst, 2),
        igst=round(igst, 2),
        gst_total=round(gst_amt, 2),
        grand_total=round(subtotal + gst_amt, 2),
        is_intra_state=is_intra,
        col_snapshot=col_snapshot,
        tax_breakdown=tax_breakdown,
    )
    db.add(invoice)
    db.flush()

    for line in payload.lines:
        db.add(models.InvoiceLine(
            invoice_id=invoice.id,
            item_id=line.item_id,
            item_name=line.item_name,
            hsn=line.hsn or "",
            quantity=line.quantity,
            rate=line.rate,
            amount=round(line.quantity * line.rate, 2),
            custom_values=line.custom_values or [],
        ))

    db.commit()
    db.refresh(invoice)
    return invoice


@router.get("/export/csv")
def export_csv(
    month: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    invoices = db.execute(
        select(models.Invoice)
        .where(models.Invoice.user_id == user.id)
        .order_by(models.Invoice.date.desc())
    ).scalars().all()

    if month:
        invoices = [i for i in invoices if i.date.strftime("%Y-%m") == month]
    if date_from:
        invoices = [i for i in invoices if i.date >= date_from]
    if date_to:
        invoices = [i for i in invoices if i.date <= date_to]

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "Invoice No", "Date", "Customer", "Customer GSTIN", "State",
        "Tax Type", "Subtotal", "CGST", "SGST", "IGST", "GST Total", "Grand Total",
    ])
    for inv in invoices:
        writer.writerow([
            inv.number,
            inv.date.isoformat(),
            inv.customer_name,
            inv.customer_gstin,
            inv.customer_state,
            "CGST+SGST" if inv.is_intra_state else "IGST",
            f"{inv.subtotal:.2f}",
            f"{inv.cgst:.2f}",
            f"{inv.sgst:.2f}",
            f"{inv.igst:.2f}",
            f"{inv.gst_total:.2f}",
            f"{inv.grand_total:.2f}",
        ])

    buf.seek(0)
    filename = f"gst-invoices-{datetime.now().strftime('%Y-%m-%d')}.csv"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/export/pdf")
def export_pdf(
    month: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Bundle all invoices in a date range into a single PDF — for sending to CA."""
    invoices = db.execute(
        select(models.Invoice)
        .options(selectinload(models.Invoice.lines))
        .where(models.Invoice.user_id == user.id)
        .order_by(models.Invoice.date.asc(), models.Invoice.id.asc())
    ).scalars().all()

    if month:
        invoices = [i for i in invoices if i.date.strftime("%Y-%m") == month]
    if date_from:
        invoices = [i for i in invoices if i.date >= date_from]
    if date_to:
        invoices = [i for i in invoices if i.date <= date_to]

    if not invoices:
        raise HTTPException(404, "No invoices found in this range")

    settings = _user_settings(db, user.id)
    pdf_bytes = render_invoices_pdf(invoices, settings)

    if date_from and date_to:
        suffix = f"{date_from.isoformat()}_to_{date_to.isoformat()}"
    elif month:
        suffix = month
    else:
        suffix = datetime.now().strftime("%Y-%m-%d")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=gst-invoices-{suffix}.pdf"},
    )

@router.put("/{invoice_id}", response_model=schemas.InvoiceOut)
def update_invoice(invoice_id: int, payload: schemas.InvoiceUpdate, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    invoice = db.get(models.Invoice, invoice_id)
    if not invoice or invoice.user_id != user.id:
        raise HTTPException(404, "Invoice not found")

    customer = db.get(models.Customer, payload.customer_id)
    if not customer or customer.user_id != user.id:
        raise HTTPException(404, "Customer not found")

    settings = _user_settings(db, user.id)
    my_gstin = settings.get("gstin", "03") or "03"
    gst_rate = float(settings.get("gst_rate", "18") or 18)

    is_intra = customer.gstin[:2] == my_gstin[:2]

    subtotal = sum(line.quantity * line.rate for line in payload.lines)
    gst_amt = subtotal * gst_rate / 100
    cgst = gst_amt / 2 if is_intra else 0
    sgst = gst_amt / 2 if is_intra else 0
    igst = 0 if is_intra else gst_amt

    # Tax breakdown
    hsn_groups = {}
    for line in payload.lines:
        hsn = line.hsn or "—"
        line_amount = line.quantity * line.rate
        if hsn not in hsn_groups:
            hsn_groups[hsn] = 0
        hsn_groups[hsn] += line_amount

    tax_breakdown = []
    for hsn, taxable in hsn_groups.items():
        hsn_gst = taxable * gst_rate / 100
        tax_breakdown.append({
            "hsn": hsn,
            "rate": gst_rate,
            "taxable": round(taxable, 2),
            "cgst": round(hsn_gst / 2, 2) if is_intra else 0,
            "sgst": round(hsn_gst / 2, 2) if is_intra else 0,
            "igst": round(hsn_gst, 2) if not is_intra else 0,
        })

    # Update invoice fields - including customer
    invoice.customer_id = customer.id
    invoice.customer_name = customer.name
    invoice.customer_gstin = customer.gstin
    invoice.customer_state = customer.state
    invoice.customer_address = customer.address
    invoice.customer_vendor_code = customer.vendor_code
    invoice.date = payload.date
    invoice.po_number = payload.po_number
    if payload.invoice_number:
        invoice.number = payload.invoice_number.strip()
    invoice.subtotal = round(subtotal, 2)
    invoice.gst_rate = gst_rate
    invoice.cgst = round(cgst, 2)
    invoice.sgst = round(sgst, 2)
    invoice.igst = round(igst, 2)
    invoice.gst_total = round(gst_amt, 2)
    invoice.grand_total = round(subtotal + gst_amt, 2)
    invoice.is_intra_state = is_intra
    invoice.tax_breakdown = tax_breakdown

    # Delete old lines and recreate
    for old_line in invoice.lines:
        db.delete(old_line)
    db.flush()

    for line in payload.lines:
        db.add(models.InvoiceLine(
            invoice_id=invoice.id,
            item_id=line.item_id,
            item_name=line.item_name,
            hsn=line.hsn or "",
            quantity=line.quantity,
            rate=line.rate,
            unit=line.unit or "",
            amount=round(line.quantity * line.rate, 2),
            custom_values=line.custom_values or [],
        ))

    db.commit()
    db.refresh(invoice)
    return invoice

@router.patch("/{invoice_id}/cancel")
def cancel_invoice(invoice_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    invoice = db.get(models.Invoice, invoice_id)
    if not invoice or invoice.user_id != user.id:
        raise HTTPException(404, "Invoice not found")
    invoice.status = "cancelled" if invoice.status != "cancelled" else "active"
    db.commit()
    db.refresh(invoice)
    return invoice


@router.get("/{invoice_id}", response_model=schemas.InvoiceOut)
def get_invoice(invoice_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    invoice = db.execute(
        select(models.Invoice)
        .options(selectinload(models.Invoice.lines))
        .where(models.Invoice.id == invoice_id)
    ).scalar_one_or_none()
    if not invoice or invoice.user_id != user.id:
        raise HTTPException(404, "Invoice not found")
    return invoice


@router.delete("/{invoice_id}")
def delete_invoice(invoice_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    invoice = db.get(models.Invoice, invoice_id)
    if not invoice or invoice.user_id != user.id:
        raise HTTPException(404, "Invoice not found")
    db.delete(invoice)
    db.commit()
    return {"message": "Deleted"}


@router.get("/{invoice_id}/pdf")
def get_invoice_pdf(invoice_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    invoice = db.execute(
        select(models.Invoice)
        .options(selectinload(models.Invoice.lines))
        .where(models.Invoice.id == invoice_id)
    ).scalar_one_or_none()
    if not invoice or invoice.user_id != user.id:
        raise HTTPException(404, "Invoice not found")

    settings = _user_settings(db, user.id)
    pdf_bytes = render_invoice_pdf(invoice, settings)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=invoice-{invoice.number}.pdf"},
    )