from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models import Patient

router = APIRouter(prefix="/patients", tags=["Patients"])

class PatientCreate(BaseModel):
    nom: str
    prenom: str
    email: str
    telephone: str = ""

@router.get("/")
def list_patients(db: Session = Depends(get_db)):
    return db.query(Patient).all()

@router.post("/")
def create_patient(p: PatientCreate, db: Session = Depends(get_db)):
    existing = db.query(Patient).filter(Patient.email == p.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email déjà utilisé")
    patient = Patient(**p.model_dump())
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient

@router.get("/{patient_id}")
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient introuvable")
    return patient
