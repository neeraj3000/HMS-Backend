from io import BytesIO
from sqlalchemy.orm import Session
from models.medicine import Medicine
from schemas.medicine_schema import MedicineCreate, MedicineUpdate
import openpyxl


# ========== CRUD ==========
def get_medicines(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Medicine).offset(skip).limit(limit).all()


def get_medicine(db: Session, medicine_id: int):
    return db.query(Medicine).filter(Medicine.id == medicine_id).first()


def create_medicine(db: Session, medicine: MedicineCreate):
    db_medicine = Medicine(**medicine.dict())
    db.add(db_medicine)
    db.commit()
    db.refresh(db_medicine)
    return db_medicine


def update_medicine(db: Session, medicine_id: int, medicine: MedicineUpdate):
    db_medicine = get_medicine(db, medicine_id)
    if not db_medicine:
        return None
    for field, value in medicine.dict(exclude_unset=True).items():
        setattr(db_medicine, field, value)
    db.commit()
    db.refresh(db_medicine)
    return db_medicine


def delete_medicine(db: Session, medicine_id: int):
    db_medicine = get_medicine(db, medicine_id)
    if not db_medicine:
        return None
    db.delete(db_medicine)
    db.commit()
    return db_medicine


# ========== DOWNLOAD INVENTORY ==========
def get_medicine_inventory_excel(db: Session) -> BytesIO:
    medicines = db.query(Medicine).all()
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Medicine Inventory"

    # Headers
    ws.append(["ID", "Name", "Brand", "Quantity", "Cost", "Tax", "Total Cost"])

    for med in medicines:
        ws.append([
            med.id,
            med.name,
            med.brand,
            med.quantity,
            med.cost,
            med.tax,
            med.total_cost
        ])

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer

def import_medicine_inventory_excel(file, db: Session):
    """
    Import medicine inventory data from an Excel file.
    Expected columns: Name | Brand | Quantity | Cost | Tax | Total Cost
    """
    try:
        workbook = openpyxl.load_workbook(BytesIO(file.file.read()))
        sheet = workbook.active

        inserted, updated = 0, 0
        for idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True)):
            if not any(row):
                continue

            name = str(row[0]).strip().upper() if row[0] else None
            brand = str(row[1]).strip() if row[1] else None
            quantity = int(row[2]) if row[2] else 0
            cost = float(row[3]) if row[3] else 0.0
            tax = float(row[4]) if row[4] else 0.0
            total_cost = float(row[5]) if row[5] else (cost + tax)

            if not name:
                continue

            existing = db.query(Medicine).filter(Medicine.name == name).first()

            if existing:
                existing.brand = brand or existing.brand
                existing.quantity = quantity
                existing.cost = cost
                existing.tax = tax
                existing.total_cost = total_cost
                updated += 1
            else:
                new_medicine = Medicine(
                    name=name,
                    brand=brand,
                    quantity=quantity,
                    cost=cost,
                    tax=tax,
                    total_cost=total_cost,
                )
                db.add(new_medicine)
                inserted += 1

        db.commit()
        return {"message": "Import completed successfully", "inserted": inserted, "updated": updated}

    except Exception as e:
        db.rollback()
        return {"error": f"Failed to import Excel file: {str(e)}"}

# ========== UPLOAD INDENT (ADMIN APPROVAL) ==========
def approve_indent_excel(file, db: Session):
    contents = file.file.read()
    workbook = openpyxl.load_workbook(BytesIO(contents))
    sheet = workbook.active

    # Expected columns: S.No | Drug/Item Name | Brand | Present Qty | Required Qty | Cost | Tax | Total Cost
    inserted = 0
    updated = 0

    for index, row in enumerate(sheet.iter_rows(min_row=2, values_only=True)):
        try:
            s_no, drug_name, brand, present_qty, required_qty, cost, tax, total_cost = row[:8]

            # Clean data
            name = str(drug_name).strip().upper() if drug_name else None
            brand = str(brand).strip() if brand else None

            if not name:
                continue

            # Check if medicine already exists
            existing = db.query(Medicine).filter(Medicine.name == name).first()

            if existing:
                # Update: add required qty to existing quantity
                existing.quantity = (existing.quantity or 0) + int(required_qty or 0)
                existing.brand = brand or existing.brand
                existing.cost = cost or existing.cost
                existing.tax = tax or existing.tax
                existing.total_cost = total_cost or existing.total_cost
                updated += 1
            else:
                # Insert: new medicine with total quantity
                new_medicine = Medicine(
                    name=name,
                    brand=brand,
                    quantity=int(present_qty or 0) + int(required_qty or 0),
                    cost=cost,
                    tax=tax,
                    total_cost=total_cost
                )
                db.add(new_medicine)
                inserted += 1
        except Exception:
            continue

    db.commit()
    return {"inserted": inserted, "updated": updated}
