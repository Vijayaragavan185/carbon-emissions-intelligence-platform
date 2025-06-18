from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

# Import Base from your existing database setup
from ...db.database import Base

class ReportStatus(enum.Enum):
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    PUBLISHED = "published"
    REJECTED = "rejected"

class ComplianceFramework(enum.Enum):
    CDP = "cdp"
    TCFD = "tcfd"
    EU_TAXONOMY = "eu_taxonomy"
    GRI = "gri"
    SASB = "sasb"

class ESGReport(Base):
    __tablename__ = "esg_reports"
    
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    report_name = Column(String(255), nullable=False)
    framework = Column(Enum(ComplianceFramework), nullable=False)
    reporting_period_start = Column(DateTime, nullable=False)
    reporting_period_end = Column(DateTime, nullable=False)
    status = Column(Enum(ReportStatus), default=ReportStatus.DRAFT)
    version = Column(Integer, default=1)
    
    # Report content and metadata
    report_data = Column(JSON)
    compliance_score = Column(Integer)  # 0-100
    completeness_percentage = Column(Integer)  # 0-100
    
    # Audit trail
    created_by = Column(Integer)  # Would be ForeignKey to users table
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    approved_by = Column(Integer)  # Would be ForeignKey to users table
    approved_at = Column(DateTime)
    published_at = Column(DateTime)
    
    # File storage
    pdf_file_path = Column(String(500))
    xml_file_path = Column(String(500))
    
    # Relationships (using your existing Company model)
    # company = relationship("Company")
    audit_logs = relationship("ESGAuditLog", back_populates="report")
    approvals = relationship("ESGApproval", back_populates="report")

class ESGAuditLog(Base):
    __tablename__ = "esg_audit_logs"
    
    id = Column(Integer, primary_key=True)
    report_id = Column(Integer, ForeignKey("esg_reports.id"), nullable=False)
    user_id = Column(Integer, nullable=False)
    action = Column(String(100), nullable=False)
    old_values = Column(JSON)
    new_values = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    # Relationships
    report = relationship("ESGReport", back_populates="audit_logs")

class ESGApproval(Base):
    __tablename__ = "esg_approvals"
    
    id = Column(Integer, primary_key=True)
    report_id = Column(Integer, ForeignKey("esg_reports.id"), nullable=False)
    approver_id = Column(Integer, nullable=False)
    approval_level = Column(Integer, nullable=False)
    status = Column(String(20), default="pending")
    comments = Column(Text)
    approved_at = Column(DateTime)
    
    # Relationships
    report = relationship("ESGReport", back_populates="approvals")
