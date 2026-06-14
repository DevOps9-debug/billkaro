from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from datetime import date
from app.database import get_db
from app.auth import get_current_user
from app import models

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("")
def get_dashboard(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    today = date.today()

    # Default range = current month
    if not date_from or not date_to:
        date_from = today.replace(day=1)
        if today.month == 12:
            next_month = today.replace(year=today.year + 1, month=1, day=1)
        else:
            next_month = today.replace(month=today.month + 1, day=1)
        date_to = next_month.replace(day=1)
        from datetime import timedelta
        date_to = date_to - timedelta(days=1)

    invoices_in_range = db.execute(
        select(models.Invoice).where(
            models.Invoice.user_id == user.id,
            models.Invoice.date >= date_from,
            models.Invoice.date <= date_to,
        )
    ).scalars().all()

    invoices_in_range = [i for i in invoices_in_range if i.status != "cancelled"]
    subtotal = sum(i.subtotal for i in invoices_in_range)
    gst_total = sum(i.gst_total for i in invoices_in_range)
    grand_total = sum(i.grand_total for i in invoices_in_range)
    igst_count = sum(1 for i in invoices_in_range if not i.is_intra_state)
    cgst_count = sum(1 for i in invoices_in_range if i.is_intra_state)
   

    total_invoices = db.execute(
        select(func.count(models.Invoice.id)).where(models.Invoice.user_id == user.id)
    ).scalar() or 0
    total_billed = db.execute(
        select(func.sum(models.Invoice.grand_total)).where(models.Invoice.user_id == user.id)
    ).scalar() or 0

    recent = db.execute(
        select(models.Invoice)
        .where(models.Invoice.user_id == user.id)
        .order_by(models.Invoice.created_at.desc())
        .limit(5)
    ).scalars().all()

    recent_data = [
        {
            "id": inv.id,
            "number": inv.number,
            "date": inv.date.isoformat(),
            "cust_name": inv.customer_name,
            "tax_type": "IGST" if not inv.is_intra_state else "CGST+SGST",
            "grand_total": inv.grand_total,
        }
        for inv in recent
    ]

    if date_from.replace(day=1) == date_to.replace(day=1) or (
        date_from.day == 1 and (date_from.month != date_to.month or date_from.year != date_to.year) is False
    ):
        period_label = date_from.strftime("%B %Y")
    else:
        period_label = f"{date_from.strftime('%d %b %Y')} – {date_to.strftime('%d %b %Y')}"

    return {
        "period_label": period_label,
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
        "summary": {
            "count": len(invoices_in_range),
            "subtotal": round(subtotal, 2),
            "gst_total": round(gst_total, 2),
            "grand_total": round(grand_total, 2),
            "igst_count": igst_count,
            "cgst_count": cgst_count,
        },
        "all_time": {
            "total_invoices": total_invoices,
            "total_billed": round(total_billed, 2),
        },
        "recent": recent_data,
    }
