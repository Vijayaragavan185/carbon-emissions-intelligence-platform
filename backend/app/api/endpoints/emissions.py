from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.models.emissions import EmissionRecord
from app.db.session import get_db
from app.schemas.emissions import EmissionCreate, EmissionRead

router = APIRouter()

@router.post("/emissions/", response_model=EmissionRead)
def create_emission(emission: EmissionCreate, db: Session = Depends(get_db)):
    db_emission = EmissionRecord(**emission.model_dump())
    db.add(db_emission)
    db.commit()
    db.refresh(db_emission)
    return db_emission

@router.get("/emissions/", response_model=List[EmissionRead])
def get_emissions(db: Session = Depends(get_db)):
    return db.query(EmissionRecord).all()

@router.get("/emissions/{emission_id}", response_model=EmissionRead)
def read_emission(emission_id: int, db: Session = Depends(get_db)):
    emission = db.query(EmissionRecord).filter(EmissionRecord.id == emission_id).first()
    if emission is None:
        raise HTTPException(status_code=404, detail="Emission not found")
    return emission

@router.get("/dashboard")
def get_dashboard_data(db: Session = Depends(get_db)):
    # Mock dashboard data for now
    return {
        "totalEmissions": 1250.5,
        "scopeBreakdown": {
            "scope1": 450.2,
            "scope2": 500.3,
            "scope3": 300.0
        },
        "monthlyTrends": [
            {"month": "2023-01-01", "emissions": 100},
            {"month": "2023-02-01", "emissions": 120},
            {"month": "2023-03-01", "emissions": 110},
        ]
    }
