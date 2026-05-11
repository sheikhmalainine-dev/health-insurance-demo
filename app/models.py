from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Patient(Base):
    __tablename__ = "patients"
    id          = Column(Integer, primary_key=True, index=True)
    nom         = Column(String, nullable=False)
    prenom      = Column(String, nullable=False)
    email       = Column(String, unique=True, nullable=False)
    telephone   = Column(String)
    policies    = relationship("Policy", back_populates="patient")

class Policy(Base):
    __tablename__ = "policies"
    id           = Column(Integer, primary_key=True, index=True)
    numero       = Column(String, unique=True, nullable=False)
    type_police  = Column(String, nullable=False)
    montant      = Column(Float, nullable=False)
    patient_id   = Column(Integer, ForeignKey("patients.id"))
    patient      = relationship("Patient", back_populates="policies")
    claims       = relationship("Claim", back_populates="policy")

class Claim(Base):
    __tablename__ = "claims"
    id          = Column(Integer, primary_key=True, index=True)
    description = Column(String, nullable=False)
    montant     = Column(Float, nullable=False)
    statut      = Column(String, default="en_attente")
    policy_id   = Column(Integer, ForeignKey("policies.id"))
    policy      = relationship("Policy", back_populates="claims")
