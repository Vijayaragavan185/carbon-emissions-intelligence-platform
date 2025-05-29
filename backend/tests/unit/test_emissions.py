from app.api.endpoints.emissions import create_emission, read_emission
from app.schemas.emissions import EmissionCreate
from sqlalchemy.orm import Session

def test_create_emission(db: Session):
    emission_data = EmissionCreate(source="power", value=100.0, unit="kg")
    result = create_emission(emission_data, db)
    assert result.source == "power"
