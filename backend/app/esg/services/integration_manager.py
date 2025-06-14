from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from sqlalchemy.orm import Session
from ..integrations.cdp_integration import CDPIntegration
from ..integrations.edci_integration import EDCIIntegration
from ..integrations.lseg_data_integration import LSEGDataIntegration
from ..integrations.webhook_service import WebhookService
from ..models.reports import ESGReport
from .audit_service import ESGAuditService

logger = logging.getLogger(__name__)

class IntegrationManager:
    """Central manager for all ESG platform integrations"""
    
    def __init__(self, db: Session, integration_configs: Dict[str, Dict]):
        self.db = db
        self.configs = integration_configs
        self.audit_service = ESGAuditService(db)
        self.webhook_service = WebhookService(db)
        
        # Initialize integrations
        self.integrations = {}
        self._initialize_integrations()
    
    def _initialize_integrations(self):
        """Initialize all configured integrations"""
        try:
            if "cdp" in self.configs:
                self.integrations["cdp"] = CDPIntegration(self.configs["cdp"])
                logger.info("CDP integration initialized")
            
            if "edci" in self.configs:
                self.integrations["edci"] = EDCIIntegration(self.configs["edci"])
                logger.info("EDCI integration initialized")
            
            if "lseg" in self.configs:
                self.integrations["lseg"] = LSEGDataIntegration(self.configs["lseg"])
                logger.info("LSEG data integration initialized")
            
            # Setup default webhooks
            self._setup_default_webhooks()
            
        except Exception as e:
            logger.error(f"Integration initialization failed: {str(e)}")
    
    def _setup_default_webhooks(self):
        """Setup default webhook endpoints"""
        default_webhooks = self.configs.get("webhooks", {})
        
        for name, webhook_config in default_webhooks.items():
            self.webhook_service.register_webhook(
                name=name,
                url=webhook_config["url"],
                events=webhook_config["events"],
                secret=webhook_config.get("secret"),
                headers=webhook_config.get("headers")
            )
    
    def submit_to_platform(
        self,
        platform: str,
        report_id: int,
        user_id: int,
        additional_data: Dict = None
    ) -> Dict:
        """Submit report to external platform"""
        try:
            if platform not in self.integrations:
                return {
                    "success": False,
                    "error": f"Platform {platform} not configured"
                }
            
            # Get report data
            report = self.db.query(ESGReport).filter(ESGReport.id == report_id).first()
            if not report:
                return {
                    "success": False,
                    "error": "Report not found"
                }
            
            # Prepare submission data
            submission_data = {
                "report_data": report.report_data,
                "metadata": {
                    "report_id": report_id,
                    "report_name": report.report_name,
                    "framework": report.framework.value,
                    "reporting_period": {
                        "start": report.reporting_period_start.isoformat(),
                        "end": report.reporting_period_end.isoformat()
                    }
                }
            }
            
            if additional_data:
                submission_data.update(additional_data)
            
            # Submit to platform
            integration = self.integrations[platform]
            result = integration.submit_report(submission_data)
            
            # Log audit trail
            self.audit_service.log_external_submission(
                report_id=report_id,
                user_id=user_id,
                platform=platform,
                submission_id=result.get("submission_id"),
                status="submitted" if result.get("success") else "failed"
            )
            
            # Trigger webhook
            self.webhook_service.on_external_submission(report_id, platform, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Platform submission failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_submission_status(self, platform: str, submission_id: str) -> Dict:
        """Get submission status from external platform"""
        try:
            if platform not in self.integrations:
                return {"error": f"Platform {platform} not configured"}
            
            integration = self.integrations[platform]
            return integration.get_submission_status(submission_id)
            
        except Exception as e:
            logger.error(f"Status check failed: {str(e)}")
            return {"error": str(e)}
    
    def get_benchmark_data(self, platform: str, criteria: Dict) -> Dict:
        """Get benchmark data from external platforms"""
        try:
            if platform not in self.integrations:
                return {"error": f"Platform {platform} not configured"}
            
            integration = self.integrations[platform]
            
            if platform == "lseg":
                instruments = criteria.get("instruments", [])
                return integration.get_esg_data(instruments, "scores")
            elif platform == "cdp":
                industry = criteria.get("industry_sector")
                return integration.get_benchmark_data(industry)
            elif platform == "edci":
                return integration.get_benchmark_data()
            
            return {"error": "Benchmark data not available for this platform"}
            
        except Exception as e:
            logger.error(f"Benchmark data retrieval failed: {str(e)}")
            return {"error": str(e)}
    
    def sync_external_data(self, sources: List[str] = None) -> Dict:
        """Sync data from external ESG data providers"""
        try:
            if sources is None:
                sources = ["lseg"]  # Default data sources
            
            sync_results = {}
            
            for source in sources:
                if source == "lseg" and "lseg" in self.integrations:
                    # Sync LSEG ESG data for tracked companies
                    companies = self.db.query(ESGReport).distinct(ESGReport.company_id).all()
                    company_symbols = [f"COMP{c.company_id}.O" for c in companies]  # Mock instrument format
                    
                    lseg_data = self.integrations["lseg"].get_esg_data(company_symbols, "scores")
                    sync_results[source] = lseg_data
            
            return {
                "success": True,
                "sync_timestamp": datetime.utcnow().isoformat(),
                "sources_synced": list(sync_results.keys()),
                "results": sync_results
            }
            
        except Exception as e:
            logger.error(f"External data sync failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def validate_integration_health(self) -> Dict:
        """Check health of all integrations"""
        health_status = {
            "overall_healthy": True,
            "timestamp": datetime.utcnow().isoformat(),
            "integrations": {}
        }
        
        for platform, integration in self.integrations.items():
            try:
                # Test basic connectivity
                if platform == "lseg":
                    test_result = integration.get_esg_data(["MSFT.O"], "basic")
                    healthy = not test_result.get("error")
                elif platform in ["cdp", "edci"]:
                    # For submission platforms, check auth
                    test_result = integration.validate_data({"test": "data"})
                    healthy = not test_result.get("error")
                else:
                    healthy = True
                
                health_status["integrations"][platform] = {
                    "healthy": healthy,
                    "last_check": datetime.utcnow().isoformat(),
                    "config_valid": bool(integration.api_key)
                }
                
                if not healthy:
                    health_status["overall_healthy"] = False
                    
            except Exception as e:
                health_status["integrations"][platform] = {
                    "healthy": False,
                    "error": str(e),
                    "last_check": datetime.utcnow().isoformat()
                }
                health_status["overall_healthy"] = False
        
        # Check webhook health
        webhook_stats = self.webhook_service.get_webhook_stats()
        health_status["webhooks"] = {
            "total_registered": webhook_stats["total_webhooks"],
            "success_rate": (
                webhook_stats["total_successes"] / 
                (webhook_stats["total_successes"] + webhook_stats["total_failures"]) * 100
                if (webhook_stats["total_successes"] + webhook_stats["total_failures"]) > 0 else 100
            )
        }
        
        return health_status
    
    def get_available_platforms(self) -> List[Dict]:
        """Get list of available integration platforms"""
        platforms = []
        
        for platform_name, integration in self.integrations.items():
            platform_info = {
                "name": platform_name,
                "type": "submission" if platform_name in ["cdp", "edci"] else "data_provider",
                "status": "active",
                "capabilities": []
            }
            
            if platform_name == "cdp":
                platform_info["capabilities"] = ["report_submission", "benchmarking", "validation"]
            elif platform_name == "edci":
                platform_info["capabilities"] = ["data_submission", "benchmarking"]
            elif platform_name == "lseg":
                platform_info["capabilities"] = ["esg_data", "industry_benchmarks", "scoring"]
            
            platforms.append(platform_info)
        
        return platforms
