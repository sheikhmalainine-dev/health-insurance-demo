from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models import Policy

router = APIRouter(prefix="/policies", tags=["Policies"])

class PolicyCreate(BaseModel):
    numero: str
    type_police: str
    montant: float
    patient_id: int

@router.get("/")
def list_policies(db: Session = Depends(get_db)):
    return db.query(Policy).all()

@router.post("/")
def create_policy(p: PolicyCreate, db: Session = Depends(get_db)):
    existing = db.query(Policy).filter(Policy.numero == p.numero).first()
    if existing:
        raise HTTPException(status_code=400, detail="Numéro de police déjà utilisé")
    policy = Policy(**p.model_dump())
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy

@router.get("/{policy_id}")
def get_policy(policy_id: int, db: Session = Depends(get_db)):
    policy = db.query(Policy).filter(Policy.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Police introuvable")
    return policy
