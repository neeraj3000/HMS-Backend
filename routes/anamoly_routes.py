from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import google.generativeai as genai
import json
from datetime import datetime

from models.medicine import Medicine
from models.prescription import Prescription
from models.student import Student
from models.lab_report import LabReport
from models.prescription_medicine import PrescriptionMedicine
from utils.db_utils import orm_to_dict
import os
from dotenv import load_dotenv
load_dotenv()

router = APIRouter(prefix="/anomalies", tags=["Admin"])


# ---------------------- GEMINI HELPER ---------------------- #

def call_gemini_ai(prompt: str, api_key: str):
    """ Calls Gemini AI safely and enforces JSON output. """

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash-lite")

        response = model.generate_content(prompt)
        raw = response.text.strip()

        # Remove markdown wrappers
        cleaned = raw.replace("```json", "").replace("```", "").strip()

        # Try direct JSON parse
        try:
            return json.loads(cleaned)

        except json.JSONDecodeError:
            # Ask Gemini again to FIX JSON
            fix_prompt = f"""
            Convert the following AI output into clean VALID JSON.
            Remove all markdown, commentary, or symbols.

            INPUT:
            {raw}

            OUTPUT (JSON only):
            """

            fix_resp = model.generate_content(fix_prompt)
            fixed = fix_resp.text.strip().replace("```json", "").replace("```", "").strip()

            return json.loads(fixed)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Error: {str(e)}")


# ---------------------- MAIN ROUTE ---------------------- #

@router.get("/")
def get_ai_generated_anomalies(db: Session = Depends(get_db)):
    """ 
    Collects full HMS dataset → sends to Gemini → returns detected anomalies.
    """

    GEMINI_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_KEY:
        raise HTTPException(status_code=500, detail="Gemini API key missing")

    # 1. Load FULL dataset
    medicines = [orm_to_dict(m) for m in db.query(Medicine).all()]
    prescriptions = [orm_to_dict(p) for p in db.query(Prescription).all()]
    students = [orm_to_dict(s) for s in db.query(Student).all()]
    lab_reports = [orm_to_dict(l) for l in db.query(LabReport).all()]
    pmeds = [orm_to_dict(pm) for pm in db.query(PrescriptionMedicine).all()]


    dataset = {
        "medicines": medicines,
        "prescriptions": prescriptions,
        "students": students,
        "lab_reports": lab_reports,
        "prescription_medicines": pmeds,
        "timestamp": datetime.utcnow().isoformat()
    }

    # 2. AI Prompt
    prompt = f"""
    You are an advanced anomaly detection engine for a Hospital Management System.

    Analyze the dataset below and identify ANY anomalies.
    Return STRICT JSON only.

    DATASET:
    {json.dumps(dataset, indent=2)}

    REQUIRED JSON STRUCTURE:
    {{
      "anomalies": [
        {{
          "type": "string",
          "severity": "low | medium | high",
          "message": "short human-friendly explanation",
          "details": "technical explanation"
        }}
      ]
    }}

    Detect anomalies in these areas:
    - Medicine Inventory (negative stock, expired, missing category, cost mismatch)
    - Prescriptions (invalid statuses, missing vitals, duplicate entries)
    - Medicines Used (issued > prescribed, missing stock)
    - Lab Reports (missing result, pending too long, no prescription)
    - Student Records (duplicate ID, missing fields)

    Return JSON only. No markdown.
    """

    # 3. Call Gemini AI
    anomalies = call_gemini_ai(prompt, GEMINI_KEY)

    # 4. Return to client
    return anomalies
