from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models import Claim

router = APIRouter(prefix="/claims", tags=["Claims"])

class ClaimCreate(BaseModel):
    description: str
    montant: float
    policy_id: int

@router.get("/")
def list_claims(db: Session = Depends(get_db)):
    return db.query(Claim).all()

@router.post("/")
def create_claim(c: ClaimCreate, db: Session = Depends(get_db)):
    claim = Claim(**c.model_dump())
    db.add(claim)
    db.commit()
    db.refresh(claim)
    return claim

@router.get("/{claim_id}")
def get_claim(claim_id: int, db: Session = Depends(get_db)):
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Sinistre introuvable")
    return claim

@router.patch("/{claim_id}/statut")
def update_statut(claim_id: int, statut: str, db: Session = Depends(get_db)):
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Sinistre introuvable")
    claim.statut = statut
    db.commit()
    return claim
