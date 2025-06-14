from typing import Dict, List, Any, Optional
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from jinja2 import Template

logger = logging.getLogger(__name__)

class NotificationService:
    """Notification service for ESG reporting workflows"""
    
    def __init__(self):
        self.email_templates = self._load_email_templates()
        # In production, these would come from configuration
        self.smtp_config = {
            "host": "smtp.gmail.com",
            "port": 587,
            "username": "esg-reports@company.com",
            "password": "app_password",
            "use_tls": True
        }
    
    def _load_email_templates(self) -> Dict[str, str]:
        """Load email templates"""
        return {
            "approval_request": """
            <h2>ESG Report Approval Request</h2>
            <p>Dear {{ approver_name }},</p>
            <p>A new ESG report requires your approval:</p>
            <ul>
                <li><strong>Report:</strong> {{ report_name }}</li>
                <li><strong>Framework:</strong> {{ framework }}</li>
                <li><strong>Approval Level:</strong> {{ approval_level }}</li>
                <li><strong>Submitted:</strong> {{ submitted_date }}</li>
            </ul>
            <p>Please review and approve the report in the ESG platform.</p>
            <p><a href="{{ approval_link }}">Review Report</a></p>
            """,
            
            "approval_complete": """
            <h2>ESG Report Approved</h2>
            <p>Great news! Your ESG report has been fully approved:</p>
            <ul>
                <li><strong>Report:</strong> {{ report_name }}</li>
                <li><strong>Framework:</strong> {{ framework }}</li>
                <li><strong>Approved:</strong> {{ approved_date }}</li>
            </ul>
            <p>The report is now ready for publication.</p>
            """,
            
            "rejection": """
            <h2>ESG Report Rejected</h2>
            <p>Your ESG report has been rejected:</p>
            <ul>
                <li><strong>Report:</strong> {{ report_name }}</li>
                <li><strong>Rejected by:</strong> {{ rejector_name }}</li>
                <li><strong>Reason:</strong> {{ rejection_reason }}</li>
            </ul>
            <p>Please address the feedback and resubmit.</p>
            """,
            
            "change_request": """
            <h2>Changes Requested for ESG Report</h2>
            <p>Changes have been requested for your ESG report:</p>
            <ul>
                <li><strong>Report:</strong> {{ report_name }}</li>
                <li><strong>Requested by:</strong> {{ requester_name }}</li>
                <li><strong>Comments:</strong> {{ comments }}</li>
            </ul>
            <p>Please make the requested changes and resubmit.</p>
            """
        }
    
    def send_approval_request_notification(
        self,
        report_id: int,
        approval_level: int,
        required_role: str
    ):
        """Send approval request notification"""
        try:
            # In production, query actual user data
            template = Template(self.email_templates["approval_request"])
            
            email_content = template.render(
                approver_name="Approver",
                report_name=f"ESG Report {report_id}",
                framework="CDP",
                approval_level=approval_level,
                submitted_date=datetime.now().strftime("%Y-%m-%d"),
                approval_link=f"https://esg-platform.com/reports/{report_id}/approve"
            )
            
            # Send email (mock implementation)
            self._send_email(
                to_emails=["approver@company.com"],
                subject=f"ESG Report Approval Required - Level {approval_level}",
                content=email_content
            )
            
            logger.info(f"Approval request notification sent for report {report_id}")
            
        except Exception as e:
            logger.error(f"Failed to send approval request notification: {str(e)}")
    
    def send_approval_complete_notification(self, report_id: int):
        """Send notification when report is fully approved"""
        try:
            template = Template(self.email_templates["approval_complete"])
            
            email_content = template.render(
                report_name=f"ESG Report {report_id}",
                framework="CDP",
                approved_date=datetime.now().strftime("%Y-%m-%d")
            )
            
            self._send_email(
                to_emails=["report-author@company.com"],
                subject="ESG Report Approved",
                content=email_content
            )
            
            logger.info(f"Approval complete notification sent for report {report_id}")
            
        except Exception as e:
            logger.error(f"Failed to send approval complete notification: {str(e)}")
    
    def send_rejection_notification(self, report_id: int, comments: str):
        """Send rejection notification"""
        try:
            template = Template(self.email_templates["rejection"])
            
            email_content = template.render(
                report_name=f"ESG Report {report_id}",
                rejector_name="Approver",
                rejection_reason=comments
            )
            
            self._send_email(
                to_emails=["report-author@company.com"],
                subject="ESG Report Rejected",
                content=email_content
            )
            
            logger.info(f"Rejection notification sent for report {report_id}")
            
        except Exception as e:
            logger.error(f"Failed to send rejection notification: {str(e)}")
    
    def send_change_request_notification(self, report_id: int, comments: str):
        """Send change request notification"""
        try:
            template = Template(self.email_templates["change_request"])
            
            email_content = template.render(
                report_name=f"ESG Report {report_id}",
                requester_name="Approver",
                comments=comments
            )
            
            self._send_email(
                to_emails=["report-author@company.com"],
                subject="Changes Requested for ESG Report",
                content=email_content
            )
            
            logger.info(f"Change request notification sent for report {report_id}")
            
        except Exception as e:
            logger.error(f"Failed to send change request notification: {str(e)}")
    
    def _send_email(self, to_emails: List[str], subject: str, content: str):
        """Send email notification"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.smtp_config["username"]
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject
            
            # Add body
            msg.attach(MIMEText(content, 'html'))
            
            # Send email
            server = smtplib.SMTP(self.smtp_config["host"], self.smtp_config["port"])
            if self.smtp_config["use_tls"]:
                server.starttls()
            
            server.login(self.smtp_config["username"], self.smtp_config["password"])
            server.sendmail(self.smtp_config["username"], to_emails, msg.as_string())
            server.quit()
            
            logger.info(f"Email sent to {to_emails}")
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            # In production, you might want to queue failed emails for retry
