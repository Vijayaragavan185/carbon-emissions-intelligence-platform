from typing import Dict, List, Any, Optional
import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
import matplotlib.pyplot as plt
import io
import base64
import tempfile

class ESGReportPDFGenerator:
    """Generate branded PDF reports for ESG compliance"""
    
    def __init__(self, template_config: Dict = None):
        self.template_config = template_config or self._get_default_template()
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _get_default_template(self) -> Dict:
        """Default branding template"""
        return {
            "company_name": "Carbon Emissions Intelligence Platform",
            "logo_path": None,  # Path to company logo
            "primary_color": colors.HexColor("#2E7D32"),  # Green
            "secondary_color": colors.HexColor("#1565C0"),  # Blue
            "accent_color": colors.HexColor("#FF6F00"),  # Orange
            "font_family": "Helvetica",
            "header_font_size": 16,
            "body_font_size": 10,
            "footer_text": "Generated by Carbon Emissions Intelligence Platform",
            "watermark": None
        }
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=self.template_config["primary_color"],
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceBefore=20,
            spaceAfter=12,
            textColor=self.template_config["primary_color"]
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=self.template_config["body_font_size"],
            spaceAfter=12
        ))
        
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER
        ))
    
    def generate_cdp_report(self, report_data: Dict, output_path: str) -> str:
        """Generate CDP-formatted PDF report"""
        try:
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            story = []
            
            # Title page
            story.extend(self._create_title_page("CDP Climate Change Report", report_data))
            story.append(PageBreak())
            
            # Executive summary
            story.extend(self._create_executive_summary(report_data))
            story.append(PageBreak())
            
            # CDP sections
            for section_key, section_data in report_data.get("sections", {}).items():
                story.extend(self._create_cdp_section(section_key, section_data))
                story.append(Spacer(1, 20))
            
            # Appendices
            story.extend(self._create_appendices(report_data))
            
            # Build PDF
            doc.build(story, onFirstPage=self._add_header_footer, onLaterPages=self._add_header_footer)
            
            return output_path
            
        except Exception as e:
            raise Exception(f"CDP PDF generation failed: {str(e)}")
    
    def generate_tcfd_report(self, report_data: Dict, output_path: str) -> str:
        """Generate TCFD-formatted PDF report"""
        try:
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            story = []
            
            # Title page
            story.extend(self._create_title_page("TCFD Climate-Related Financial Disclosures", report_data))
            story.append(PageBreak())
            
            # TCFD structure
            story.extend(self._create_tcfd_overview())
            story.append(PageBreak())
            
            # Four pillars
            for pillar_key, pillar_data in report_data.get("pillars", {}).items():
                story.extend(self._create_tcfd_pillar(pillar_key, pillar_data))
                story.append(PageBreak())
            
            # Build PDF
            doc.build(story, onFirstPage=self._add_header_footer, onLaterPages=self._add_header_footer)
            
            return output_path
            
        except Exception as e:
            raise Exception(f"TCFD PDF generation failed: {str(e)}")
    
    def generate_eu_taxonomy_report(self, report_data: Dict, output_path: str) -> str:
        """Generate EU Taxonomy-formatted PDF report"""
        try:
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            story = []
            
            # Title page
            story.extend(self._create_title_page("EU Taxonomy Compliance Report", report_data))
            story.append(PageBreak())
            
            # Summary KPIs
            story.extend(self._create_taxonomy_summary(report_data.get("summary_kpis", {})))
            story.append(PageBreak())
            
            # Environmental objectives
            for objective, disclosure in report_data.get("article_8_disclosures", {}).items():
                story.extend(self._create_taxonomy_objective(objective, disclosure))
                story.append(Spacer(1, 20))
            
            # Build PDF
            doc.build(story, onFirstPage=self._add_header_footer, onLaterPages=self._add_header_footer)
            
            return output_path
            
        except Exception as e:
            raise Exception(f"EU Taxonomy PDF generation failed: {str(e)}")
    
    def _create_title_page(self, title: str, report_data: Dict) -> List:
        """Create title page"""
        elements = []
        
        # Logo if available
        if self.template_config.get("logo_path") and os.path.exists(self.template_config["logo_path"]):
            logo = Image(self.template_config["logo_path"], width=2*inch, height=1*inch)
            elements.append(logo)
            elements.append(Spacer(1, 30))
        
        # Title
        elements.append(Paragraph(title, self.styles['CustomTitle']))
        elements.append(Spacer(1, 50))
        
        # Company info
        company_name = self.template_config.get("company_name", "Company Name")
        elements.append(Paragraph(f"<b>{company_name}</b>", self.styles['CustomHeading']))
        
        # Report period
        metadata = report_data.get("metadata", {})
        reporting_year = metadata.get("reporting_year", datetime.now().year)
        elements.append(Paragraph(f"Reporting Year: {reporting_year}", self.styles['CustomBody']))
        
        # Generation date
        generated_at = metadata.get("generated_at", datetime.utcnow().isoformat())
        elements.append(Paragraph(f"Generated: {generated_at[:10]}", self.styles['CustomBody']))
        
        elements.append(Spacer(1, 100))
        
        # Compliance score if available
        if "compliance_score" in report_data:
            score = report_data["compliance_score"]
            score_color = colors.green if score >= 80 else colors.orange if score >= 60 else colors.red
            elements.append(Paragraph(
                f'<font color="{score_color}"><b>Compliance Score: {score}%</b></font>',
                self.styles['CustomHeading']
            ))
        
        return elements
    
    def _create_executive_summary(self, report_data: Dict) -> List:
        """Create executive summary"""
        elements = []
        
        elements.append(Paragraph("Executive Summary", self.styles['CustomHeading']))
        
        # Key metrics
        if "compliance_score" in report_data:
            score = report_data["compliance_score"]
            elements.append(Paragraph(
                f"This report achieved a compliance score of {score}%, indicating "
                f"{'strong' if score >= 80 else 'moderate' if score >= 60 else 'limited'} "
                f"alignment with regulatory requirements.",
                self.styles['CustomBody']
            ))
        
        # Framework-specific summary
        framework = report_data.get("metadata", {}).get("framework", "")
        if framework == "CDP":
            elements.extend(self._create_cdp_summary(report_data))
        elif framework == "TCFD":
            elements.extend(self._create_tcfd_summary(report_data))
        elif framework == "EU_Taxonomy":
            elements.extend(self._create_taxonomy_exec_summary(report_data))
        
        return elements
    
    def _create_cdp_summary(self, report_data: Dict) -> List:
        """Create CDP-specific executive summary"""
        elements = []
        
        elements.append(Paragraph(
            "This Carbon Disclosure Project (CDP) report provides comprehensive disclosure "
            "of our climate-related governance, strategy, risk management, and performance metrics.",
            self.styles['CustomBody']
        ))
        
        # Extract key emissions data if available
        sections = report_data.get("sections", {})
        if "C6" in sections:
            c6_data = sections["C6"]
            if "C6.1" in c6_data:
                scope1 = c6_data["C6.1"].get("scope_1_emissions", 0)
                elements.append(Paragraph(
                    f"Scope 1 Emissions: {scope1:,.0f} metric tons CO2e",
                    self.styles['CustomBody']
                ))
        
        return elements
    
    def _create_tcfd_summary(self, report_data: Dict) -> List:
        """Create TCFD-specific executive summary"""
        elements = []
        
        elements.append(Paragraph(
            "This report follows the Task Force on Climate-related Financial Disclosures (TCFD) "
            "framework, covering governance, strategy, risk management, and metrics & targets.",
            self.styles['CustomBody']
        ))
        
        return elements
    
    def _create_taxonomy_exec_summary(self, report_data: Dict) -> List:
        """Create EU Taxonomy executive summary"""
        elements = []
        
        summary_kpis = report_data.get("summary_kpis", {})
        
        elements.append(Paragraph(
            "This EU Taxonomy report discloses the alignment of our economic activities "
            "with the EU's sustainable finance taxonomy.",
            self.styles['CustomBody']
        ))
        
        # Key KPIs
        if summary_kpis:
            turnover = summary_kpis.get("turnover", {})
            aligned_pct = turnover.get("aligned_percentage", 0)
            elements.append(Paragraph(
                f"Taxonomy-aligned turnover: {aligned_pct:.1f}%",
                self.styles['CustomBody']
            ))
        
        return elements
    
    def _create_cdp_section(self, section_key: str, section_data: Dict) -> List:
        """Create CDP section content"""
        elements = []
        
        section_titles = {
            "C1": "Governance",
            "C2": "Risks and Opportunities", 
            "C3": "Business Strategy",
            "C4": "Targets and Performance",
            "C5": "Emissions Methodology",
            "C6": "Emissions Data",
            "C7": "Emissions Breakdown"
        }
        
        title = section_titles.get(section_key, section_key)
        elements.append(Paragraph(f"{section_key}: {title}", self.styles['CustomHeading']))
        
        for question_key, question_data in section_data.items():
            elements.append(Paragraph(f"<b>{question_key}</b>", self.styles['CustomBody']))
            
            if isinstance(question_data, dict) and "question" in question_data:
                elements.append(Paragraph(question_data["question"], self.styles['CustomBody']))
                
                # Response
                response = question_data.get("response", "")
                if isinstance(response, str):
                    elements.append(Paragraph(f"Response: {response}", self.styles['CustomBody']))
                elif isinstance(response, dict):
                    # Format complex responses
                    for key, value in response.items():
                        if isinstance(value, (str, int, float)):
                            elements.append(Paragraph(f"{key}: {value}", self.styles['CustomBody']))
            
            elements.append(Spacer(1, 12))
        
        return elements
    
    def _create_tcfd_pillar(self, pillar_key: str, pillar_data: Dict) -> List:
        """Create TCFD pillar content"""
        elements = []
        
        pillar_titles = {
            "governance": "Governance",
            "strategy": "Strategy",
            "risk_management": "Risk Management",
            "metrics_targets": "Metrics and Targets"
        }
        
        title = pillar_titles.get(pillar_key, pillar_key.replace("_", " ").title())
        elements.append(Paragraph(title, self.styles['CustomHeading']))
        
        for recommendation_key, recommendation_data in pillar_data.items():
            elements.append(Paragraph(f"<b>{recommendation_key.replace('_', ' ').title()}</b>", self.styles['CustomBody']))
            
            if "recommendation" in recommendation_data:
                elements.append(Paragraph(
                    f"<i>{recommendation_data['recommendation']}</i>",
                    self.styles['CustomBody']
                ))
            
            if "disclosure" in recommendation_data:
                disclosure = recommendation_data["disclosure"]
                if isinstance(disclosure, dict):
                    for key, value in disclosure.items():
                        if isinstance(value, str):
                            elements.append(Paragraph(f"{key}: {value}", self.styles['CustomBody']))
                        elif isinstance(value, list):
                            elements.append(Paragraph(f"{key}:", self.styles['CustomBody']))
                            for item in value[:5]:  # Limit to first 5 items
                                elements.append(Paragraph(f"• {item}", self.styles['CustomBody']))
            
            # Implementation status
            status = recommendation_data.get("implementation_status", "Not specified")
            status_color = colors.green if status == "Implemented" else colors.orange if status == "Partially implemented" else colors.red
            elements.append(Paragraph(
                f'<font color="{status_color}">Status: {status}</font>',
                self.styles['CustomBody']
            ))
            
            elements.append(Spacer(1, 12))
        
        return elements
    
    def _create_taxonomy_summary(self, summary_kpis: Dict) -> List:
        """Create EU Taxonomy summary KPIs"""
        elements = []
        
        elements.append(Paragraph("EU Taxonomy KPI Summary", self.styles['CustomHeading']))
        
        if not summary_kpis:
            elements.append(Paragraph("No KPI data available", self.styles['CustomBody']))
            return elements
        
        # Create KPI table
        kpi_data = [
            ["KPI", "Eligible %", "Aligned %", "Absolute Eligible", "Absolute Aligned"]
        ]
        
        for kpi_name, kpi_data_item in summary_kpis.items():
            if isinstance(kpi_data_item, dict):
                kpi_data.append([
                    kpi_name.title(),
                    f"{kpi_data_item.get('eligible_percentage', 0):.1f}%",
                    f"{kpi_data_item.get('aligned_percentage', 0):.1f}%",
                    f"€{kpi_data_item.get('absolute_eligible', 0):,.0f}",
                    f"€{kpi_data_item.get('absolute_aligned', 0):,.0f}"
                ])
        
        kpi_table = Table(kpi_data)
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.template_config["primary_color"]),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(kpi_table)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_taxonomy_objective(self, objective: str, disclosure: Dict) -> List:
        """Create EU Taxonomy environmental objective section"""
        elements = []
        
        objective_title = objective.replace("_", " ").title()
        elements.append(Paragraph(f"Environmental Objective: {objective_title}", self.styles['CustomHeading']))
        
        # Eligible activities
        eligible_activities = disclosure.get("eligible_activities", [])
        if eligible_activities:
            elements.append(Paragraph("Eligible Activities:", self.styles['CustomBody']))
            for activity in eligible_activities:
                elements.append(Paragraph(
                    f"• {activity.get('activity_code', '')}: {activity.get('activity_name', '')}",
                    self.styles['CustomBody']
                ))
        
        # KPIs for this objective
        kpis = disclosure.get("kpis", {})
        if kpis:
            elements.append(Paragraph("KPIs for this objective:", self.styles['CustomBody']))
            for kpi_name, kpi_data in kpis.items():
                elements.append(Paragraph(
                    f"{kpi_name.title()}: {kpi_data.get('aligned_percentage', 0):.1f}% aligned",
                    self.styles['CustomBody']
                ))
        
        return elements
    
    def _create_appendices(self, report_data: Dict) -> List:
        """Create appendices"""
        elements = []
        
        elements.append(Paragraph("Appendices", self.styles['CustomHeading']))
        
        # Methodology
        elements.append(Paragraph("A. Methodology", self.styles['CustomBody']))
        elements.append(Paragraph(
            "This report was generated using the Carbon Emissions Intelligence Platform, "
            "which implements automated compliance assessment and reporting capabilities.",
            self.styles['CustomBody']
        ))
        
        # Data sources
        elements.append(Paragraph("B. Data Sources", self.styles['CustomBody']))
        elements.append(Paragraph(
            "• Internal emissions measurement systems\n"
            "• Third-party verification reports\n"
            "• Industry emission factors (EPA, IPCC, DEFRA)\n"
            "• Financial accounting systems",
            self.styles['CustomBody']
        ))
        
        return elements
    
    def _add_header_footer(self, canvas, doc):
        """Add header and footer to pages"""
        canvas.saveState()
        
        # Header
        canvas.setFont('Helvetica-Bold', 12)
        canvas.setFillColor(self.template_config["primary_color"])
        canvas.drawString(72, doc.height + 50, self.template_config["company_name"])
        
        # Footer
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.grey)
        footer_text = self.template_config["footer_text"]
        canvas.drawString(72, 30, footer_text)
        
        # Page number
        canvas.drawRightString(doc.width + 72, 30, f"Page {doc.page}")
        
        canvas.restoreState()
    
    def add_charts_to_report(self, report_data: Dict, chart_type: str = "emissions_breakdown") -> str:
        """Add charts to report (returns base64 encoded image)"""
        try:
            plt.figure(figsize=(10, 6))
            
            if chart_type == "emissions_breakdown":
                # Pie chart of emissions by scope
                sections = report_data.get("sections", {})
                if "C6" in sections:
                    scope_data = {}
                    for key, data in sections["C6"].items():
                        if "scope_1_emissions" in data:
                            scope_data["Scope 1"] = data["scope_1_emissions"]
                        elif "scope_2_emissions" in data:
                            scope_data["Scope 2"] = data["scope_2_emissions"]
                        elif "scope_3_emissions" in data:
                            scope_data["Scope 3"] = data["scope_3_emissions"]
                    
                    if scope_data:
                        plt.pie(scope_data.values(), labels=scope_data.keys(), autopct='%1.1f%%')
                        plt.title("Emissions by Scope")
            
            # Save to base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight', dpi=150)
            buffer.seek(0)
            
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return image_base64
            
        except Exception as e:
            print(f"Chart generation failed: {e}")
            return ""
