from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.models.emissions import Emission
from app.db.session import get_db
from app.schemas.emissions import EmissionCreate, EmissionRead

router = APIRouter()

@router.post("/emissions/", response_model=EmissionRead)
def create_emission(emission: EmissionCreate, db: Session = Depends(get_db)):
    db_emission = Emission(**emission.model_dump())

    db.add(db_emission)
    db.commit()
    db.refresh(db_emission)
    return db_emission

@router.get("/emissions/{emission_id}", response_model=EmissionRead)
def read_emission(emission_id: int, db: Session = Depends(get_db)):
    emission = db.query(Emission).filter(Emission.id == emission_id).first()
    if emission is None:
        raise HTTPException(status_code=404, detail="Emission not found")
    return emission
