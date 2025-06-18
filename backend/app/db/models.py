from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, func, Text, Enum, JSON
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime
import enum
from .database import Base

class ScopeEnum(enum.Enum):
    SCOPE_1 = "Scope 1"
    SCOPE_2 = "Scope 2"
    SCOPE_3 = "Scope 3"

class Company(Base):
    __tablename__ = 'companies'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    registration_number = Column(String(100), unique=True, nullable=True)
    industry_sector = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False)
    parent_id = Column(Integer, ForeignKey('companies.id'), nullable=True)
    reporting_year = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Fixed relationships
    parent = relationship('Company', remote_side=[id], back_populates='children')
    children = relationship('Company', back_populates='parent')
    emission_records = relationship('EmissionRecord', back_populates='company')
    
    @hybrid_property
    def total_emissions(self):
        return sum(record.calculated_emission for record in self.emission_records)

class EmissionFactor(Base):
    __tablename__ = 'emission_factors'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    scope = Column(Enum(ScopeEnum), nullable=False)
    category = Column(String(100), nullable=False)
    subcategory = Column(String(100), nullable=True)
    factor_value = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)
    source = Column(String(255), nullable=False)
    region = Column(String(100), nullable=True)
    year = Column(Integer, nullable=False)
    uncertainty = Column(Float, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    emission_records = relationship('EmissionRecord', back_populates='emission_factor')

class EmissionRecord(Base):
    __tablename__ = 'emission_records'
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    facility_name = Column(String(255), nullable=True)
    scope = Column(Enum(ScopeEnum), nullable=False)
    activity_type = Column(String(100), nullable=False)
    activity_amount = Column(Float, nullable=False)
    activity_unit = Column(String(50), nullable=False)
    emission_factor_id = Column(Integer, ForeignKey('emission_factors.id'), nullable=False)
    calculated_emission = Column(Float, nullable=False)
    emission_unit = Column(String(50), default="kg CO2e")
    reporting_period_start = Column(DateTime, nullable=False)
    reporting_period_end = Column(DateTime, nullable=False)
    data_quality_score = Column(Float, nullable=True)
    verification_status = Column(String(50), default="Unverified")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    company = relationship('Company', back_populates='emission_records')
    emission_factor = relationship('EmissionFactor', back_populates='emission_records')
    audit_trails = relationship('AuditTrail', back_populates='emission_record')
    validation_logs = relationship('DataValidationLog', back_populates='emission_record')

class AuditTrail(Base):
    __tablename__ = 'audit_trails'
    
    id = Column(Integer, primary_key=True, index=True)
    emission_record_id = Column(Integer, ForeignKey('emission_records.id'), nullable=False)
    action = Column(String(50), nullable=False)
    performed_by = Column(String(255), nullable=False)
    previous_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String(45), nullable=True)
    details = Column(Text, nullable=True)
    
    emission_record = relationship('EmissionRecord', back_populates='audit_trails')

class DataValidationLog(Base):
    __tablename__ = 'data_validation_logs'
    
    id = Column(Integer, primary_key=True, index=True)
    emission_record_id = Column(Integer, ForeignKey('emission_records.id'), nullable=False)
    validation_rule = Column(String(100), nullable=False)
    validation_status = Column(Boolean, nullable=False)
    validation_message = Column(Text, nullable=True)
    severity = Column(String(20), default="INFO")
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    emission_record = relationship('EmissionRecord', back_populates='validation_logs')

class CalculationMethod(Base):
    __tablename__ = 'calculation_methods'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    scope = Column(Enum(ScopeEnum), nullable=False)
    formula = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    ghg_protocol_reference = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Backward compatibility
class Emission(Base):
    __tablename__ = "emissions"
    
    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, index=True)
    value = Column(Float)
    unit = Column(String)
    timestamp = Column(DateTime, server_default=func.now())
