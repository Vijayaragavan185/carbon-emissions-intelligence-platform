from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..models.reports import ESGReport, ESGApproval, ReportStatus
from .audit_service import ESGAuditService
from .notification_service import NotificationService
import logging

logger = logging.getLogger(__name__)

class ApprovalWorkflowService:
    """Multi-level approval workflow service for ESG reports"""
    
    def __init__(self, db: Session):
        self.db = db
        self.audit_service = ESGAuditService(db)
        self.notification_service = NotificationService()
        
        # Define approval workflows by framework
        self.approval_workflows = {
            "cdp": {
                "levels": [
                    {"level": 1, "title": "Data Manager Review", "required_role": "data_manager"},
                    {"level": 2, "title": "Sustainability Manager Approval", "required_role": "sustainability_manager"},
                    {"level": 3, "title": "Executive Approval", "required_role": "executive"}
                ],
                "auto_advance": True,
                "parallel_approval": False
            },
            "tcfd": {
                "levels": [
                    {"level": 1, "title": "Risk Manager Review", "required_role": "risk_manager"},
                    {"level": 2, "title": "CFO Approval", "required_role": "cfo"},
                    {"level": 3, "title": "CEO Final Approval", "required_role": "ceo"}
                ],
                "auto_advance": False,
                "parallel_approval": False
            },
            "eu_taxonomy": {
                "levels": [
                    {"level": 1, "title": "Legal Review", "required_role": "legal"},
                    {"level": 2, "title": "Finance Review", "required_role": "finance"},
                    {"level": 3, "title": "Board Approval", "required_role": "board_member"}
                ],
                "auto_advance": True,
                "parallel_approval": True  # Level 1 and 2 can run in parallel
            }
        }
    
    def submit_for_approval(self, report_id: int, submitted_by: int) -> Dict:
        """Submit report for approval workflow"""
        try:
            report = self.db.query(ESGReport).filter(ESGReport.id == report_id).first()
            if not report:
                return {"success": False, "message": "Report not found"}
            
            if report.status != ReportStatus.DRAFT:
                return {"success": False, "message": "Only draft reports can be submitted for approval"}
            
            # Get workflow configuration
            framework = report.framework.value
            workflow = self.approval_workflows.get(framework)
            if not workflow:
                return {"success": False, "message": f"No approval workflow defined for {framework}"}
            
            # Update report status
            report.status = ReportStatus.UNDER_REVIEW
            self.db.commit()
            
            # Create approval records
            approval_records = []
            for level_config in workflow["levels"]:
                approval = ESGApproval(
                    report_id=report_id,
                    approver_id=None,  # Will be assigned when approver takes action
                    approval_level=level_config["level"],
                    status="pending"
                )
                self.db.add(approval)
                approval_records.append(approval)
            
            self.db.commit()
            
            # Log audit trail
            self.audit_service.log_status_change(
                report_id=report_id,
                user_id=submitted_by,
                old_status="draft",
                new_status="under_review",
                comments="Submitted for approval workflow"
            )
            
            # Start workflow
            self._start_approval_workflow(report_id, workflow)
            
            return {
                "success": True,
                "message": "Report submitted for approval",
                "workflow_started": True,
                "approval_levels": len(workflow["levels"])
            }
            
        except Exception as e:
            logger.error(f"Failed to submit report for approval: {str(e)}")
            self.db.rollback()
            return {"success": False, "message": str(e)}
    
    def process_approval(
        self,
        report_id: int,
        approver_id: int,
        approval_level: int,
        action: str,  # approve, reject, request_changes
        comments: str = None
    ) -> Dict:
        """Process an approval action"""
        try:
            # Validate inputs
            if action not in ["approve", "reject", "request_changes"]:
                return {"success": False, "message": "Invalid approval action"}
            
            report = self.db.query(ESGReport).filter(ESGReport.id == report_id).first()
            if not report:
                return {"success": False, "message": "Report not found"}
            
            if report.status != ReportStatus.UNDER_REVIEW:
                return {"success": False, "message": "Report is not under review"}
            
            # Get approval record
            approval = self.db.query(ESGApproval).filter(
                ESGApproval.report_id == report_id,
                ESGApproval.approval_level == approval_level,
                ESGApproval.status == "pending"
            ).first()
            
            if not approval:
                return {"success": False, "message": "No pending approval found for this level"}
            
            # Update approval record
            approval.approver_id = approver_id
            approval.status = action + "d"  # approved, rejected, request_changesd
            approval.comments = comments
            approval.approved_at = datetime.utcnow()
            
            # Log audit trail
            self.audit_service.log_approval_action(
                report_id=report_id,
                approver_id=approver_id,
                action=action,
                approval_level=approval_level,
                comments=comments
            )
            
            # Process workflow based on action
            if action == "reject":
                return self._handle_rejection(report, approver_id, comments)
            elif action == "request_changes":
                return self._handle_change_request(report, approver_id, comments)
            elif action == "approve":
                return self._handle_approval(report, approval_level, approver_id)
            
        except Exception as e:
            logger.error(f"Failed to process approval: {str(e)}")
            self.db.rollback()
            return {"success": False, "message": str(e)}
    
    def _handle_rejection(self, report: ESGReport, approver_id: int, comments: str) -> Dict:
        """Handle report rejection"""
        # Update report status
        old_status = report.status.value
        report.status = ReportStatus.REJECTED
        
        # Log status change
        self.audit_service.log_status_change(
            report_id=report.id,
            user_id=approver_id,
            old_status=old_status,
            new_status="rejected",
            comments=comments
        )
        
        # Cancel pending approvals
        pending_approvals = self.db.query(ESGApproval).filter(
            ESGApproval.report_id == report.id,
            ESGApproval.status == "pending"
        ).all()
        
        for approval in pending_approvals:
            approval.status = "cancelled"
        
        self.db.commit()
        
        # Send notifications
        self.notification_service.send_rejection_notification(report.id, comments)
        
        return {
            "success": True,
            "message": "Report rejected",
            "final_status": "rejected"
        }
    
    def _handle_change_request(self, report: ESGReport, approver_id: int, comments: str) -> Dict:
        """Handle change request"""
        # Update report status back to draft
        old_status = report.status.value
        report.status = ReportStatus.DRAFT
        
        # Reset all approvals
        approvals = self.db.query(ESGApproval).filter(
            ESGApproval.report_id == report.id
        ).all()
        
        for approval in approvals:
            approval.status = "reset"
        
        # Log status change
        self.audit_service.log_status_change(
            report_id=report.id,
            user_id=approver_id,
            old_status=old_status,
            new_status="draft",
            comments=f"Changes requested: {comments}"
        )
        
        self.db.commit()
        
        # Send notifications
        self.notification_service.send_change_request_notification(report.id, comments)
        
        return {
            "success": True,
            "message": "Changes requested - report returned to draft",
            "final_status": "draft"
        }
    
    def _handle_approval(self, report: ESGReport, approval_level: int, approver_id: int) -> Dict:
        """Handle approval and check if workflow is complete"""
        framework = report.framework.value
        workflow = self.approval_workflows.get(framework, {})
        max_level = len(workflow.get("levels", []))
        
        # Check if this was the final approval
        if approval_level >= max_level:
            # All approvals complete
            old_status = report.status.value
            report.status = ReportStatus.APPROVED
            report.approved_by = approver_id
            report.approved_at = datetime.utcnow()
            
            # Log status change
            self.audit_service.log_status_change(
                report_id=report.id,
                user_id=approver_id,
                old_status=old_status,
                new_status="approved",
                comments="All approvals completed"
            )
            
            self.db.commit()
            
            # Send notifications
            self.notification_service.send_approval_complete_notification(report.id)
            
            return {
                "success": True,
                "message": "Report fully approved",
                "final_status": "approved",
                "workflow_complete": True
            }
        else:
            # Continue to next approval level
            self._advance_workflow(report.id, approval_level + 1, workflow)
            
            self.db.commit()
            
            return {
                "success": True,
                "message": f"Level {approval_level} approved - proceeding to level {approval_level + 1}",
                "next_level": approval_level + 1,
                "workflow_complete": False
            }
    
    def _start_approval_workflow(self, report_id: int, workflow: Dict):
        """Start the approval workflow"""
        if workflow.get("parallel_approval", False):
            # Start all levels that can run in parallel
            for level_config in workflow["levels"][:2]:  # Example: first 2 levels in parallel
                self._notify_approvers(report_id, level_config["level"], level_config["required_role"])
        else:
            # Start with level 1
            self._notify_approvers(report_id, 1, workflow["levels"][0]["required_role"])
    
    def _advance_workflow(self, report_id: int, next_level: int, workflow: Dict):
        """Advance workflow to next level"""
        if next_level <= len(workflow["levels"]):
            level_config = workflow["levels"][next_level - 1]
            self._notify_approvers(report_id, next_level, level_config["required_role"])
    
    def _notify_approvers(self, report_id: int, level: int, required_role: str):
        """Notify appropriate approvers for the level"""
        # In a real implementation, this would:
        # 1. Query users with the required role
        # 2. Send notifications (email, in-app, etc.)
        # 3. Log notification events
        
        self.notification_service.send_approval_request_notification(
            report_id=report_id,
            approval_level=level,
            required_role=required_role
        )
    
    def get_approval_status(self, report_id: int) -> Dict:
        """Get current approval status for a report"""
        try:
            report = self.db.query(ESGReport).filter(ESGReport.id == report_id).first()
            if not report:
                return {"error": "Report not found"}
            
            approvals = self.db.query(ESGApproval).filter(
                ESGApproval.report_id == report_id
            ).order_by(ESGApproval.approval_level).all()
            
            framework = report.framework.value
            workflow = self.approval_workflows.get(framework, {})
            
            approval_status = []
            for approval in approvals:
                level_config = None
                if workflow and "levels" in workflow:
                    level_configs = [l for l in workflow["levels"] if l["level"] == approval.approval_level]
                    level_config = level_configs[0] if level_configs else None
                
                approval_status.append({
                    "level": approval.approval_level,
                    "title": level_config["title"] if level_config else f"Level {approval.approval_level}",
                    "required_role": level_config["required_role"] if level_config else "unknown",
                    "status": approval.status,
                    "approver_id": approval.approver_id,
                    "approved_at": approval.approved_at.isoformat() if approval.approved_at else None,
                    "comments": approval.comments
                })
            
            # Calculate overall progress
            total_levels = len(workflow.get("levels", []))
            completed_levels = len([a for a in approvals if a.status == "approved"])
            progress_percentage = (completed_levels / total_levels * 100) if total_levels > 0 else 0
            
            return {
                "report_id": report_id,
                "current_status": report.status.value,
                "framework": framework,
                "approval_levels": approval_status,
                "progress_percentage": progress_percentage,
                "total_levels": total_levels,
                "completed_levels": completed_levels,
                "workflow_complete": report.status == ReportStatus.APPROVED
            }
            
        except Exception as e:
            logger.error(f"Failed to get approval status: {str(e)}")
            return {"error": str(e)}
    
    def get_pending_approvals(self, approver_id: int, role: str = None) -> List[Dict]:
        """Get pending approvals for a user"""
        try:
            # Get reports that need approval at levels matching the user's role
            pending_reports = []
            
            # Query all pending approvals
            pending_approvals = self.db.query(ESGApproval).filter(
                ESGApproval.status == "pending"
            ).all()
            
            for approval in pending_approvals:
                report = self.db.query(ESGReport).filter(
                    ESGReport.id == approval.report_id
                ).first()
                
                if not report:
                    continue
                
                # Check if user can approve this level
                framework = report.framework.value
                workflow = self.approval_workflows.get(framework, {})
                
                if workflow and "levels" in workflow:
                    level_config = next(
                        (l for l in workflow["levels"] if l["level"] == approval.approval_level),
                        None
                    )
                    
                    if level_config and (not role or level_config["required_role"] == role):
                        pending_reports.append({
                            "report_id": report.id,
                            "report_name": report.report_name,
                            "framework": framework,
                            "approval_level": approval.approval_level,
                            "level_title": level_config["title"],
                            "required_role": level_config["required_role"],
                            "submitted_date": report.created_at.isoformat(),
                            "reporting_period": {
                                "start": report.reporting_period_start.isoformat(),
                                "end": report.reporting_period_end.isoformat()
                            }
                        })
            
            return pending_reports
            
        except Exception as e:
            logger.error(f"Failed to get pending approvals: {str(e)}")
            return []
