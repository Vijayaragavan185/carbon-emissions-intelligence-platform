from sqlalchemy import Column, Integer, String, Float, DateTime, func
from app.db.session import Base

class Emission(Base):
    __tablename__ = "emissions"
    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, index=True)
    value = Column(Float)
    unit = Column(String)
    timestamp = Column(DateTime, server_default=func.now())
