from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import json
import requests
import hmac
import hashlib
import logging
from sqlalchemy.orm import Session
from ..models.reports import ESGReport
from ..services.audit_service import ESGAuditService

logger = logging.getLogger(__name__)

class WebhookService:
    """Service for managing webhooks and real-time notifications"""
    
    def __init__(self, db: Session):
        self.db = db
        self.audit_service = ESGAuditService(db)
        self.registered_webhooks = {}
        
    def register_webhook(
        self,
        name: str,
        url: str,
        events: List[str],
        secret: str = None,
        headers: Dict[str, str] = None
    ):
        """Register a webhook endpoint"""
        self.registered_webhooks[name] = {
            "url": url,
            "events": events,
            "secret": secret,
            "headers": headers or {},
            "created_at": datetime.utcnow().isoformat(),
            "last_triggered": None,
            "success_count": 0,
            "failure_count": 0
        }
        
        logger.info(f"Webhook registered: {name} for events: {events}")
    
    def trigger_webhook(self, event: str, data: Dict):
        """Trigger webhooks for specific events"""
        for name, webhook_config in self.registered_webhooks.items():
            if event in webhook_config["events"]:
                try:
                    self._send_webhook(name, webhook_config, event, data)
                except Exception as e:
                    logger.error(f"Webhook {name} failed: {str(e)}")
    
    def _send_webhook(self, name: str, config: Dict, event: str, data: Dict):
        """Send webhook notification"""
        try:
            payload = {
                "event": event,
                "timestamp": datetime.utcnow().isoformat(),
                "data": data
            }
            
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Carbon-ESG-Platform/1.0",
                **config.get("headers", {})
            }
            
            # Add signature if secret is provided
            if config.get("secret"):
                signature = self._generate_signature(
                    json.dumps(payload, sort_keys=True),
                    config["secret"]
                )
                headers["X-ESG-Signature"] = signature
            
            response = requests.post(
                config["url"],
                json=payload,
                headers=headers,
                timeout=30
            )
            
            response.raise_for_status()
            
            # Update webhook stats
            config["last_triggered"] = datetime.utcnow().isoformat()
            config["success_count"] += 1
            
            logger.info(f"Webhook {name} triggered successfully for event: {event}")
            
        except Exception as e:
            config["failure_count"] += 1
            logger.error(f"Webhook {name} failed: {str(e)}")
            raise
    
    def _generate_signature(self, payload: str, secret: str) -> str:
        """Generate HMAC signature for webhook security"""
        signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"
    
    def on_report_submitted(self, report_id: int, user_id: int):
        """Trigger webhook when report is submitted for approval"""
        report = self.db.query(ESGReport).filter(ESGReport.id == report_id).first()
        if report:
            data = {
                "report_id": report_id,
                "report_name": report.report_name,
                "framework": report.framework.value,
                "submitted_by": user_id,
                "status": report.status.value
            }
            self.trigger_webhook("report.submitted", data)
    
    def on_report_approved(self, report_id: int, approver_id: int):
        """Trigger webhook when report is approved"""
        report = self.db.query(ESGReport).filter(ESGReport.id == report_id).first()
        if report:
            data = {
                "report_id": report_id,
                "report_name": report.report_name,
                "framework": report.framework.value,
                "approved_by": approver_id,
                "approved_at": report.approved_at.isoformat() if report.approved_at else None
            }
            self.trigger_webhook("report.approved", data)
    
    def on_report_published(self, report_id: int, publication_details: Dict):
        """Trigger webhook when report is published to external platforms"""
        report = self.db.query(ESGReport).filter(ESGReport.id == report_id).first()
        if report:
            data = {
                "report_id": report_id,
                "report_name": report.report_name,
                "framework": report.framework.value,
                "publication_details": publication_details,
                "published_at": datetime.utcnow().isoformat()
            }
            self.trigger_webhook("report.published", data)
    
    def on_external_submission(self, report_id: int, platform: str, submission_result: Dict):
        """Trigger webhook when report is submitted to external platform"""
        data = {
            "report_id": report_id,
            "platform": platform,
            "submission_id": submission_result.get("submission_id"),
            "success": submission_result.get("success", False),
            "submitted_at": datetime.utcnow().isoformat()
        }
        self.trigger_webhook("external.submission", data)
    
    def get_webhook_stats(self) -> Dict:
        """Get webhook statistics"""
        stats = {
            "total_webhooks": len(self.registered_webhooks),
            "active_webhooks": len([w for w in self.registered_webhooks.values() if w["last_triggered"]]),
            "total_successes": sum(w["success_count"] for w in self.registered_webhooks.values()),
            "total_failures": sum(w["failure_count"] for w in self.registered_webhooks.values()),
            "webhooks": {}
        }
        
        for name, config in self.registered_webhooks.items():
            stats["webhooks"][name] = {
                "events": config["events"],
                "last_triggered": config["last_triggered"],
                "success_count": config["success_count"],
                "failure_count": config["failure_count"],
                "success_rate": (
                    config["success_count"] / (config["success_count"] + config["failure_count"]) * 100
                    if (config["success_count"] + config["failure_count"]) > 0 else 0
                )
            }
        
        return stats
