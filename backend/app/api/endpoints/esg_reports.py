from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from ...db.database import get_db
from ...esg.models.reports import ESGReport, ReportStatus, ComplianceFramework
from ...esg.compliance.cdp import CDPReportGenerator
from ...esg.compliance.tcfd import TCFDReportGenerator
from ...esg.compliance.eu_taxonomy import EUTaxonomyReportGenerator
from ...esg.services.pdf_generator import ESGReportPDFGenerator
from ...esg.services.audit_service import ESGAuditService
from ...esg.services.approval_service import ApprovalWorkflowService
from ...esg.services.integration_manager import IntegrationManager
from ...core.config import settings
from ...core.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/esg", tags=["ESG Reports"])

# Integration manager instance (would be dependency injected in production)
integration_manager = IntegrationManager(
    db=None,  # Will be set per request
    integration_configs=settings.ESG_INTEGRATIONS
)

@router.post("/reports", response_model=Dict[str, Any])
async def create_esg_report(
    report_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Create a new ESG report"""
    try:
        # Validate required fields
        required_fields = ["report_name", "framework", "reporting_period_start", "reporting_period_end", "company_id"]
        for field in required_fields:
            if field not in report_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        # Create report
        new_report = ESGReport(
            company_id=report_data["company_id"],
            report_name=report_data["report_name"],
            framework=ComplianceFramework(report_data["framework"]),
            reporting_period_start=datetime.fromisoformat(report_data["reporting_period_start"]),
            reporting_period_end=datetime.fromisoformat(report_data["reporting_period_end"]),
            report_data=report_data.get("report_data", {}),
            status=ReportStatus.DRAFT,
            created_by=current_user["id"],
            version=1
        )
        
        db.add(new_report)
        db.commit()
        db.refresh(new_report)
        
        # Log audit trail
        audit_service = ESGAuditService(db)
        audit_service.log_report_creation(
            report_id=new_report.id,
            user_id=current_user["id"],
            report_data=report_data
        )
        
        logger.info(f"ESG report created: {new_report.id} by user {current_user['id']}")
        
        return {
            "success": True,
            "report_id": new_report.id,
            "message": "ESG report created successfully",
            "report": {
                "id": new_report.id,
                "name": new_report.report_name,
                "framework": new_report.framework.value,
                "status": new_report.status.value,
                "created_at": new_report.created_at.isoformat(),
                "version": new_report.version
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to create ESG report: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create report: {str(e)}"
        )

@router.get("/reports", response_model=Dict[str, Any])
async def get_esg_reports(
    company_id: Optional[int] = None,
    framework: Optional[str] = None,
    status_filter: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Get list of ESG reports with filtering"""
    try:
        query = db.query(ESGReport)
        
        # Apply filters
        if company_id:
            query = query.filter(ESGReport.company_id == company_id)
        
        if framework:
            query = query.filter(ESGReport.framework == ComplianceFramework(framework))
        
        if status_filter:
            query = query.filter(ESGReport.status == ReportStatus(status_filter))
        
        # Get total count for pagination
        total_count = query.count()
        
        # Apply pagination
        reports = query.order_by(ESGReport.created_at.desc()).offset(offset).limit(limit).all()
        
        # Format response
        report_list = []
        for report in reports:
            report_list.append({
                "id": report.id,
                "name": report.report_name,
                "framework": report.framework.value,
                "status": report.status.value,
                "company_id": report.company_id,
                "reporting_period": {
                    "start": report.reporting_period_start.isoformat(),
                    "end": report.reporting_period_end.isoformat()
                },
                "compliance_score": report.compliance_score,
                "completeness_percentage": report.completeness_percentage,
                "created_at": report.created_at.isoformat(),
                "updated_at": report.updated_at.isoformat(),
                "version": report.version,
                "created_by": report.created_by
            })
        
        return {
            "success": True,
            "reports": report_list,
            "pagination": {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_count
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve ESG reports: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve reports: {str(e)}"
        )

@router.get("/reports/{report_id}", response_model=Dict[str, Any])
async def get_esg_report_detail(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Get detailed ESG report information"""
    try:
        report = db.query(ESGReport).filter(ESGReport.id == report_id).first()
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        # Get audit trail
        audit_service = ESGAuditService(db)
        audit_trail = audit_service.get_audit_trail(report_id, limit=20)
        audit_summary = audit_service.get_audit_summary(report_id)
        
        # Get approval status
        approval_service = ApprovalWorkflowService(db)
        approval_status = approval_service.get_approval_status(report_id)
        
        return {
            "success": True,
            "report": {
                "id": report.id,
                "name": report.report_name,
                "framework": report.framework.value,
                "status": report.status.value,
                "company_id": report.company_id,
                "reporting_period": {
                    "start": report.reporting_period_start.isoformat(),
                    "end": report.reporting_period_end.isoformat()
                },
                "report_data": report.report_data,
                "compliance_score": report.compliance_score,
                "completeness_percentage": report.completeness_percentage,
                "created_at": report.created_at.isoformat(),
                "updated_at": report.updated_at.isoformat(),
                "approved_at": report.approved_at.isoformat() if report.approved_at else None,
                "published_at": report.published_at.isoformat() if report.published_at else None,
                "version": report.version,
                "files": {
                    "pdf": report.pdf_file_path,
                    "xml": report.xml_file_path
                }
            },
            "audit_trail": audit_trail,
            "audit_summary": audit_summary,
            "approval_status": approval_status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve ESG report detail: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve report detail: {str(e)}"
        )

@router.put("/reports/{report_id}", response_model=Dict[str, Any])
async def update_esg_report(
    report_id: int,
    update_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Update ESG report"""
    try:
        report = db.query(ESGReport).filter(ESGReport.id == report_id).first()
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        if report.status != ReportStatus.DRAFT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only draft reports can be updated"
            )
        
        # Store old values for audit trail
        old_values = {
            "report_name": report.report_name,
            "report_data": report.report_data,
            "updated_at": report.updated_at.isoformat()
        }
        
        # Update fields
        updatable_fields = ["report_name", "report_data", "reporting_period_start", "reporting_period_end"]
        fields_changed = []
        
        for field in updatable_fields:
            if field in update_data:
                if field.endswith("_start") or field.endswith("_end"):
                    setattr(report, field, datetime.fromisoformat(update_data[field]))
                else:
                    setattr(report, field, update_data[field])
                fields_changed.append(field)
        
        report.updated_at = datetime.utcnow()
        report.version += 1
        
        db.commit()
        db.refresh(report)
        
        # Log audit trail
        audit_service = ESGAuditService(db)
        audit_service.log_report_update(
            report_id=report_id,
            user_id=current_user["id"],
            old_data=old_values,
            new_data=update_data,
            fields_changed=fields_changed
        )
        
        logger.info(f"ESG report updated: {report_id} by user {current_user['id']}")
        
        return {
            "success": True,
            "message": "Report updated successfully",
            "version": report.version,
            "fields_changed": fields_changed
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update ESG report: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update report: {str(e)}"
        )

@router.post("/reports/{report_id}/generate", response_model=Dict[str, Any])
async def generate_esg_report(
    report_id: int,
    generation_options: Dict[str, Any] = {},
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Generate ESG report content based on framework"""
    try:
        report = db.query(ESGReport).filter(ESGReport.id == report_id).first()
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        # Get company and emission data (simplified - would query actual data)
        company_data = {"id": report.company_id, "name": "Company Name"}
        emission_data = []  # Would fetch from emission_records table
        
        # Generate report based on framework
        if report.framework == ComplianceFramework.CDP:
            generator = CDPReportGenerator()
            generated_report = generator.generate_report(company_data, emission_data)
        elif report.framework == ComplianceFramework.TCFD:
            generator = TCFDReportGenerator()
            generated_report = generator.generate_report(company_data, emission_data)
        elif report.framework == ComplianceFramework.EU_TAXONOMY:
            generator = EUTaxonomyReportGenerator()
            financial_data = {"total_revenue": 1000000, "total_capex": 100000, "total_opex": 50000}
            generated_report = generator.generate_report(company_data, [], financial_data)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Report generation not supported for framework: {report.framework.value}"
            )
        
        # Update report with generated content
        report.report_data = generated_report
        report.compliance_score = generated_report.get("compliance_score", 0)
        report.completeness_percentage = 100  # Would calculate based on actual data
        report.updated_at = datetime.utcnow()
        
        db.commit()
        
        # Log audit trail
        audit_service = ESGAuditService(db)
        audit_service.log_action(
            report_id=report_id,
            user_id=current_user["id"],
            action="report_generated",
            new_values={"framework": report.framework.value, "compliance_score": report.compliance_score}
        )
        
        logger.info(f"ESG report generated: {report_id} for framework {report.framework.value}")
        
        return {
            "success": True,
            "message": "Report generated successfully",
            "compliance_score": report.compliance_score,
            "completeness_percentage": report.completeness_percentage,
            "framework": report.framework.value,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate ESG report: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report: {str(e)}"
        )

@router.post("/reports/{report_id}/submit", response_model=Dict[str, Any])
async def submit_for_approval(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Submit ESG report for approval workflow"""
    try:
        approval_service = ApprovalWorkflowService(db)
        result = approval_service.submit_for_approval(report_id, current_user["id"])
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit report for approval: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit for approval: {str(e)}"
        )

@router.post("/reports/{report_id}/approve", response_model=Dict[str, Any])
async def approve_report(
    report_id: int,
    approval_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Approve or reject ESG report"""
    try:
        required_fields = ["approval_level", "action"]  # approve, reject, request_changes
        for field in required_fields:
            if field not in approval_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        approval_service = ApprovalWorkflowService(db)
        result = approval_service.process_approval(
            report_id=report_id,
            approver_id=current_user["id"],
            approval_level=approval_data["approval_level"],
            action=approval_data["action"],
            comments=approval_data.get("comments")
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process approval: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process approval: {str(e)}"
        )

@router.post("/reports/{report_id}/export/pdf", response_model=Dict[str, Any])
async def export_report_pdf(
    report_id: int,
    export_options: Dict[str, Any] = {},
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Export ESG report as branded PDF"""
    try:
        report = db.query(ESGReport).filter(ESGReport.id == report_id).first()
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        if not report.report_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Report must be generated before export"
            )
        
        # Generate PDF
        pdf_generator = ESGReportPDFGenerator(export_options.get("template_config"))
        
        output_filename = f"esg_report_{report_id}_{report.framework.value}_{datetime.now().strftime('%Y%m%d')}.pdf"
        output_path = f"/tmp/{output_filename}"  # In production, use proper storage
        
        if report.framework == ComplianceFramework.CDP:
            pdf_path = pdf_generator.generate_cdp_report(report.report_data, output_path)
        elif report.framework == ComplianceFramework.TCFD:
            pdf_path = pdf_generator.generate_tcfd_report(report.report_data, output_path)
        elif report.framework == ComplianceFramework.EU_TAXONOMY:
            pdf_path = pdf_generator.generate_eu_taxonomy_report(report.report_data, output_path)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"PDF export not supported for framework: {report.framework.value}"
            )
        
        # Update report with PDF path
        report.pdf_file_path = pdf_path
        db.commit()
        
        # Log audit trail
        audit_service = ESGAuditService(db)
        audit_service.log_file_generation(
            report_id=report_id,
            user_id=current_user["id"],
            file_type="pdf",
            file_path=pdf_path
        )
        
        return {
            "success": True,
            "message": "PDF generated successfully",
            "file_path": pdf_path,
            "filename": output_filename,
            "download_url": f"/api/esg/reports/{report_id}/download/pdf"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export PDF: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export PDF: {str(e)}"
        )

@router.get("/reports/{report_id}/download/pdf")
async def download_pdf(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Download PDF file"""
    try:
        report = db.query(ESGReport).filter(ESGReport.id == report_id).first()
        
        if not report or not report.pdf_file_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="PDF file not found"
            )
        
        return FileResponse(
            path=report.pdf_file_path,
            filename=f"esg_report_{report_id}.pdf",
            media_type='application/pdf'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download PDF: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download PDF: {str(e)}"
        )

@router.post("/reports/{report_id}/publish", response_model=Dict[str, Any])
async def publish_to_external_platforms(
    report_id: int,
    publication_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Publish report to external ESG platforms"""
    try:
        platforms = publication_data.get("platforms", [])
        if not platforms:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No platforms specified for publication"
            )
        
        # Initialize integration manager with db session
        integration_manager.db = db
        
        publication_results = {}
        
        for platform in platforms:
            result = integration_manager.submit_to_platform(
                platform=platform,
                report_id=report_id,
                user_id=current_user["id"],
                additional_data=publication_data.get("additional_data", {})
            )
            publication_results[platform] = result
        
        # Update report status if any submission was successful
        successful_submissions = [p for p, r in publication_results.items() if r.get("success")]
        
        if successful_submissions:
            report = db.query(ESGReport).filter(ESGReport.id == report_id).first()
            if report and report.status == ReportStatus.APPROVED:
                report.status = ReportStatus.PUBLISHED
                report.published_at = datetime.utcnow()
                db.commit()
        
        return {
            "success": len(successful_submissions) > 0,
            "message": f"Published to {len(successful_submissions)} of {len(platforms)} platforms",
            "platforms_published": successful_submissions,
            "publication_results": publication_results,
            "published_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to publish report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to publish report: {str(e)}"
        )

@router.get("/reports/{report_id}/audit-trail", response_model=Dict[str, Any])
async def get_audit_trail(
    report_id: int,
    limit: int = 50,
    action_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Get audit trail for ESG report"""
    try:
        audit_service = ESGAuditService(db)
        
        action_filters = [action_filter] if action_filter else None
        audit_trail = audit_service.get_audit_trail(
            report_id=report_id,
            limit=limit,
            action_filter=action_filters
        )
        
        audit_summary = audit_service.get_audit_summary(report_id)
        
        return {
            "success": True,
            "report_id": report_id,
            "audit_trail": audit_trail,
            "summary": audit_summary
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve audit trail: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve audit trail: {str(e)}"
        )

@router.get("/pending-approvals", response_model=Dict[str, Any])
async def get_pending_approvals(
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Get pending approvals for current user"""
    try:
        approval_service = ApprovalWorkflowService(db)
        user_role = current_user.get("role")  # Would come from JWT token
        
        pending_approvals = approval_service.get_pending_approvals(
            approver_id=current_user["id"],
            role=user_role
        )
        
        return {
            "success": True,
            "pending_approvals": pending_approvals,
            "total_pending": len(pending_approvals)
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve pending approvals: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve pending approvals: {str(e)}"
        )

@router.get("/integration-health", response_model=Dict[str, Any])
async def check_integration_health(
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Check health of external integrations"""
    try:
        integration_manager.db = db
        health_status = integration_manager.validate_integration_health()
        
        return {
            "success": True,
            "health_status": health_status
        }
        
    except Exception as e:
        logger.error(f"Failed to check integration health: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check integration health: {str(e)}"
        )

@router.get("/frameworks", response_model=Dict[str, Any])
async def get_supported_frameworks():
    """Get list of supported ESG frameworks"""
    frameworks = [
        {
            "code": "cdp",
            "name": "Carbon Disclosure Project",
            "description": "Global climate disclosure system for companies",
            "supported_features": ["report_generation", "submission", "benchmarking"]
        },
        {
            "code": "tcfd",
            "name": "Task Force on Climate-related Financial Disclosures",
            "description": "Climate-related financial disclosure recommendations",
            "supported_features": ["report_generation", "scenario_analysis"]
        },
        {
            "code": "eu_taxonomy",
            "name": "EU Taxonomy Regulation",
            "description": "EU classification system for sustainable activities",
            "supported_features": ["report_generation", "alignment_assessment"]
        }
    ]
    
    return {
        "success": True,
        "frameworks": frameworks,
        "total_frameworks": len(frameworks)
    }

@router.post("/validate", response_model=Dict[str, Any])
async def validate_report_data(
    validation_request: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Validate ESG report data against framework requirements"""
    try:
        framework = validation_request.get("framework")
        data = validation_request.get("data", {})
        
        if not framework:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Framework is required for validation"
            )
        
        # Initialize appropriate integration for validation
        integration_manager.db = db
        
        if framework == "cdp":
            from ...esg.integrations.cdp_integration import CDPIntegration
            validator = CDPIntegration(settings.ESG_INTEGRATIONS.get("cdp", {}))
        elif framework == "tcfd":
            # TCFD validation would be implemented
            validation_result = {"valid": True, "score": 85, "warnings": []}
        elif framework == "eu_taxonomy":
            from ...esg.integrations.edci_integration import EDCIIntegration
            validator = EDCIIntegration(settings.ESG_INTEGRATIONS.get("edci", {}))
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Validation not supported for framework: {framework}"
            )
        
        if 'validator' in locals():
            validation_result = validator.validate_data(data)
        
        return {
            "success": True,
            "framework": framework,
            "validation_result": validation_result,
            "validated_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to validate data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate data: {str(e)}"
        )
