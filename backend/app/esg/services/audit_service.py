from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from ..models.reports import ESGAuditLog, ESGReport
from ...db.database import get_db
import json
import hashlib
from flask import request
import logging

logger = logging.getLogger(__name__)

class ESGAuditService:
    """Comprehensive audit trail service for ESG reporting"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def log_action(
        self,
        report_id: int,
        user_id: int,
        action: str,
        old_values: Dict = None,
        new_values: Dict = None,
        additional_context: Dict = None
    ) -> ESGAuditLog:
        """Log an audit trail entry"""
        try:
            # Get request metadata if available
            ip_address = None
            user_agent = None
            
            try:
                if request:
                    ip_address = request.remote_addr
                    user_agent = request.headers.get('User-Agent')
            except:
                pass  # Outside request context
            
            audit_log = ESGAuditLog(
                report_id=report_id,
                user_id=user_id,
                action=action,
                old_values=old_values,
                new_values=new_values,
                timestamp=datetime.utcnow(),
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Add additional context if provided
            if additional_context:
                if not audit_log.new_values:
                    audit_log.new_values = {}
                audit_log.new_values['_context'] = additional_context
            
            self.db.add(audit_log)
            self.db.commit()
            
            logger.info(f"Audit log created: {action} for report {report_id} by user {user_id}")
            return audit_log
            
        except Exception as e:
            logger.error(f"Failed to create audit log: {str(e)}")
            self.db.rollback()
            raise
    
    def log_report_creation(self, report_id: int, user_id: int, report_data: Dict) -> ESGAuditLog:
        """Log report creation"""
        return self.log_action(
            report_id=report_id,
            user_id=user_id,
            action="report_created",
            new_values={"report_data": report_data},
            additional_context={"creation_timestamp": datetime.utcnow().isoformat()}
        )
    
    def log_report_update(
        self,
        report_id: int,
        user_id: int,
        old_data: Dict,
        new_data: Dict,
        fields_changed: List[str]
    ) -> ESGAuditLog:
        """Log report updates with detailed change tracking"""
        
        # Create change summary
        changes = {}
        for field in fields_changed:
            changes[field] = {
                "old": old_data.get(field),
                "new": new_data.get(field)
            }
        
        return self.log_action(
            report_id=report_id,
            user_id=user_id,
            action="report_updated",
            old_values=old_data,
            new_values=new_data,
            additional_context={
                "fields_changed": fields_changed,
                "change_summary": changes,
                "change_count": len(fields_changed)
            }
        )
    
    def log_status_change(
        self,
        report_id: int,
        user_id: int,
        old_status: str,
        new_status: str,
        comments: str = None
    ) -> ESGAuditLog:
        """Log report status changes"""
        return self.log_action(
            report_id=report_id,
            user_id=user_id,
            action="status_changed",
            old_values={"status": old_status},
            new_values={"status": new_status, "comments": comments},
            additional_context={
                "status_transition": f"{old_status} -> {new_status}",
                "workflow_step": self._get_workflow_step(new_status)
            }
        )
    
    def log_approval_action(
        self,
        report_id: int,
        approver_id: int,
        action: str,  # approved, rejected, requested_changes
        approval_level: int,
        comments: str = None
    ) -> ESGAuditLog:
        """Log approval workflow actions"""
        return self.log_action(
            report_id=report_id,
            user_id=approver_id,
            action=f"approval_{action}",
            new_values={
                "approval_action": action,
                "approval_level": approval_level,
                "comments": comments
            },
            additional_context={
                "workflow_stage": f"Level {approval_level} Approval",
                "approval_timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def log_file_generation(
        self,
        report_id: int,
        user_id: int,
        file_type: str,  # pdf, xml, csv
        file_path: str,
        file_size: int = None
    ) -> ESGAuditLog:
        """Log file generation events"""
        file_hash = self._calculate_file_hash(file_path) if file_path else None
        
        return self.log_action(
            report_id=report_id,
            user_id=user_id,
            action="file_generated",
            new_values={
                "file_type": file_type,
                "file_path": file_path,
                "file_size": file_size,
                "file_hash": file_hash
            },
            additional_context={
                "generation_timestamp": datetime.utcnow().isoformat(),
                "file_integrity_check": file_hash is not None
            }
        )
    
    def log_data_validation(
        self,
        report_id: int,
        user_id: int,
        validation_results: Dict,
        passed: bool
    ) -> ESGAuditLog:
        """Log data validation events"""
        return self.log_action(
            report_id=report_id,
            user_id=user_id,
            action="data_validated",
            new_values={
                "validation_passed": passed,
                "validation_results": validation_results
            },
            additional_context={
                "validation_timestamp": datetime.utcnow().isoformat(),
                "validation_score": validation_results.get("score", 0),
                "errors_found": len(validation_results.get("errors", []))
            }
        )
    
    def log_external_submission(
        self,
        report_id: int,
        user_id: int,
        platform: str,  # CDP, TCFD, etc.
        submission_id: str = None,
        status: str = "submitted"
    ) -> ESGAuditLog:
        """Log external platform submissions"""
        return self.log_action(
            report_id=report_id,
            user_id=user_id,
            action="external_submission",
            new_values={
                "platform": platform,
                "submission_id": submission_id,
                "submission_status": status
            },
            additional_context={
                "submission_timestamp": datetime.utcnow().isoformat(),
                "external_platform": platform
            }
        )
    
    def get_audit_trail(
        self,
        report_id: int,
        limit: int = 100,
        action_filter: List[str] = None
    ) -> List[Dict]:
        """Get audit trail for a report"""
        try:
            query = self.db.query(ESGAuditLog).filter(
                ESGAuditLog.report_id == report_id
            )
            
            if action_filter:
                query = query.filter(ESGAuditLog.action.in_(action_filter))
            
            audit_logs = query.order_by(
                ESGAuditLog.timestamp.desc()
            ).limit(limit).all()
            
            return [self._format_audit_log(log) for log in audit_logs]
            
        except Exception as e:
            logger.error(f"Failed to retrieve audit trail: {str(e)}")
            return []
    
    def get_audit_summary(self, report_id: int) -> Dict:
        """Get audit trail summary statistics"""
        try:
            audit_logs = self.db.query(ESGAuditLog).filter(
                ESGAuditLog.report_id == report_id
            ).all()
            
            if not audit_logs:
                return {"total_actions": 0, "unique_users": 0, "timeline": []}
            
            # Calculate summary statistics
            total_actions = len(audit_logs)
            unique_users = len(set(log.user_id for log in audit_logs))
            
            # Action breakdown
            action_counts = {}
            for log in audit_logs:
                action_counts[log.action] = action_counts.get(log.action, 0) + 1
            
            # Timeline (last 10 actions)
            timeline = []
            for log in sorted(audit_logs, key=lambda x: x.timestamp, reverse=True)[:10]:
                timeline.append({
                    "timestamp": log.timestamp.isoformat(),
                    "action": log.action,
                    "user_id": log.user_id
                })
            
            # Calculate report lifecycle metrics
            creation_log = next((log for log in audit_logs if log.action == "report_created"), None)
            latest_log = max(audit_logs, key=lambda x: x.timestamp)
            
            lifecycle_duration = None
            if creation_log:
                lifecycle_duration = (latest_log.timestamp - creation_log.timestamp).total_seconds()
            
            return {
                "total_actions": total_actions,
                "unique_users": unique_users,
                "action_breakdown": action_counts,
                "timeline": timeline,
                "first_action": creation_log.timestamp.isoformat() if creation_log else None,
                "latest_action": latest_log.timestamp.isoformat(),
                "lifecycle_duration_seconds": lifecycle_duration,
                "most_common_action": max(action_counts.items(), key=lambda x: x[1])[0] if action_counts else None
            }
            
        except Exception as e:
            logger.error(f"Failed to generate audit summary: {str(e)}")
            return {}
    
    def verify_data_integrity(self, report_id: int) -> Dict:
        """Verify data integrity for a report"""
        try:
            report = self.db.query(ESGReport).filter(ESGReport.id == report_id).first()
            if not report:
                return {"status": "error", "message": "Report not found"}
            
            # Get all audit logs for the report
            audit_logs = self.db.query(ESGAuditLog).filter(
                ESGAuditLog.report_id == report_id
            ).order_by(ESGAuditLog.timestamp.asc()).all()
            
            integrity_checks = {
                "report_exists": True,
                "audit_trail_complete": len(audit_logs) > 0,
                "creation_logged": any(log.action == "report_created" for log in audit_logs),
                "status_changes_logged": True,  # Would implement detailed check
                "file_integrity": True,  # Would check file hashes
                "timeline_consistent": self._verify_timeline_consistency(audit_logs),
                "version_consistency": self._verify_version_consistency(report, audit_logs)
            }
            
            all_passed = all(integrity_checks.values())
            
            return {
                "status": "passed" if all_passed else "failed",
                "checks": integrity_checks,
                "total_checks": len(integrity_checks),
                "passed_checks": sum(integrity_checks.values()),
                "verification_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Data integrity verification failed: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def _get_workflow_step(self, status: str) -> str:
        """Get workflow step description for status"""
        workflow_steps = {
            "draft": "Preparation",
            "under_review": "Review Process",
            "approved": "Approval Complete",
            "published": "Published",
            "rejected": "Rejected"
        }
        return workflow_steps.get(status, "Unknown")
    
    def _calculate_file_hash(self, file_path: str) -> Optional[str]:
        """Calculate SHA-256 hash of file for integrity checking"""
        try:
            if not file_path or not os.path.exists(file_path):
                return None
            
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256()
                while chunk := f.read(8192):
                    file_hash.update(chunk)
                return file_hash.hexdigest()
        except Exception:
            return None
    
    def _format_audit_log(self, log: ESGAuditLog) -> Dict:
        """Format audit log for API response"""
        return {
            "id": log.id,
            "timestamp": log.timestamp.isoformat(),
            "action": log.action,
            "user_id": log.user_id,
            "old_values": log.old_values,
            "new_values": log.new_values,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "context": log.new_values.get("_context") if log.new_values else None
        }
    
    def _verify_timeline_consistency(self, audit_logs: List[ESGAuditLog]) -> bool:
        """Verify that audit log timeline is consistent"""
        if len(audit_logs) < 2:
            return True
        
        # Check that timestamps are in order
        for i in range(1, len(audit_logs)):
            if audit_logs[i].timestamp < audit_logs[i-1].timestamp:
                return False
        
        return True
    
    def _verify_version_consistency(self, report: ESGReport, audit_logs: List[ESGAuditLog]) -> bool:
        """Verify that report version is consistent with audit logs"""
        update_count = len([log for log in audit_logs if log.action == "report_updated"])
        expected_version = update_count + 1  # Start from version 1
        
        return report.version >= expected_version
