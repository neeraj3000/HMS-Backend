from sqlalchemy.orm import Session
from sqlalchemy import func, extract, and_, case
from datetime import datetime, timedelta, date

from models.medicine import Medicine
from models.prescription import Prescription
from models.prescription_medicine import PrescriptionMedicine


def get_inventory_analytics(db: Session, days: int):
    """
    Computes pharmacy inventory analytics, fully compatible with frontend.
    """

    # Time window for filtering prescribing activity
    now = datetime.now()
    start_date = now - timedelta(days=days)

    # -------------------------------------------------
    # 1) TOTAL MEDICINES IN INVENTORY
    # -------------------------------------------------
    total_medicines = (
        db.query(func.count(Medicine.id))
        .scalar()
        or 0
    )

    # -------------------------------------------------
    # 2) LOW STOCK COUNT (<= 10 units)
    # -------------------------------------------------
    low_stock_count = (
        db.query(func.count(Medicine.id))
        .filter(Medicine.quantity <= 10)
        .scalar()
        or 0
    )

    # -------------------------------------------------
    # 3) EXPIRING SOON (within next 90 days)
    # -------------------------------------------------
    expiring_soon = (
        db.query(func.count(Medicine.id))
        .filter(
            Medicine.expiry_date != None,
            Medicine.expiry_date <= (date.today() + timedelta(days=90))
        )
        .scalar()
        or 0
    )

    # -------------------------------------------------
    # 4) TOTAL VALUE OF INVENTORY (quantity × cost)
    # -------------------------------------------------
    total_value = (
        db.query(func.sum(Medicine.quantity * func.coalesce(Medicine.cost, 0)))
        .scalar()
        or 0
    )

    # -------------------------------------------------
    # 5) MOST PRESCRIBED MEDICINES (last X days)
    # -------------------------------------------------
    most_prescribed_raw = (
        db.query(
            Medicine.name,
            Medicine.category,
            func.sum(PrescriptionMedicine.quantity_prescribed).label("count")
        )
        .join(PrescriptionMedicine, PrescriptionMedicine.medicine_id == Medicine.id)
        .join(Prescription, Prescription.id == PrescriptionMedicine.prescription_id)
        .filter(Prescription.created_at >= start_date)
        .group_by(Medicine.id)
        .order_by(func.sum(PrescriptionMedicine.quantity_prescribed).desc())
        .limit(5)
        .all()
    )

    most_prescribed = [
        {
            "name": row[0],
            "category": row[1] or "Uncategorized",
            "count": int(row[2] or 0)
        }
        for row in most_prescribed_raw
    ]

    # -------------------------------------------------
    # 6) STOCK LEVELS BY CATEGORY
    # -------------------------------------------------
    stock_levels_raw = (
        db.query(
            Medicine.category,
            func.sum(Medicine.quantity).label("total"),
            func.sum(
                case(
                    (Medicine.quantity <= 10, 1),
                    else_=0
                )
            ).label("low")
        )
        .group_by(Medicine.category)
        .all()
    )

    stock_levels = [
        {
            "category": row[0] or "Uncategorized",
            "total": int(row[1] or 0),
            "low": int(row[2] or 0)
        }
        for row in stock_levels_raw
    ]

    # -------------------------------------------------
    # 7) MONTHLY USAGE (Issued last 5 months)
    # -------------------------------------------------
    monthly_usage = []
    today = date.today()

    for i in range(5):
        # Compute month & year
        month = (today.month - i - 1) % 12 + 1
        year = today.year - ((today.month - i - 1) // 12)

        # ISSUED count
        issued = (
            db.query(func.sum(PrescriptionMedicine.quantity_prescribed))
            .join(Prescription, Prescription.id == PrescriptionMedicine.prescription_id)
            .filter(
                extract("month", Prescription.created_at) == month,
                extract("year", Prescription.created_at) == year
            )
            .scalar()
            or 0
        )

        # No receiving tracking in DB → always 0
        received = 0

        monthly_usage.append({
            "month": date(year, month, 1).strftime("%b"),
            "issued": int(issued),
            "received": received
        })

    # Oldest → newest order
    monthly_usage.reverse()

    # -------------------------------------------------
    # FINAL RESPONSE
    # -------------------------------------------------
    return {
        "totalMedicines": total_medicines,
        "lowStockCount": low_stock_count,
        "expiringCount": expiring_soon,
        "totalValue": float(total_value),

        "mostPrescribed": most_prescribed,
        "stockLevels": stock_levels,
        "monthlyUsage": monthly_usage,
    }