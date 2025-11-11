from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import auth_routes, staff_profile_router, stats_routes, student_routes, lab_report_routes, medicine_routes, prescription_medicine_routes, prescription_routes, inventory_routes, user_routes, admin_router, indent_router
from database import Base, engine

from models.student import Student
from models.user import User
from models.prescription import Prescription
from models.medicine import Medicine
from models.lab_report import LabReport
from models.prescription_medicine import PrescriptionMedicine
from models.inventory import InventoryItem


# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include auth routes FIRST
app.include_router(auth_routes.router, prefix="/api")
app.include_router(user_routes.router, prefix="/api", tags=["Users"])
app.include_router(student_routes.router)
app.include_router(medicine_routes.router)
app.include_router(lab_report_routes.router)
app.include_router(prescription_routes.router)
app.include_router(prescription_medicine_routes.router)
app.include_router(inventory_routes.router)
app.include_router(admin_router.router)
app.include_router(indent_router.router)
app.include_router(staff_profile_router.router)
app.include_router(stats_routes.router)


@app.get("/")
def root():
    return {"status" : "ok" , "message" : "Welcoime bro its working"}