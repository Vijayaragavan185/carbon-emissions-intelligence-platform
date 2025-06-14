from typing import Dict, List, Any
from datetime import datetime
import json
from ..models.reports import ComplianceFramework

class EUTaxonomyReportGenerator:
    """EU Taxonomy Regulation Report Generator"""
    
    def __init__(self):
        self.framework = ComplianceFramework.EU_TAXONOMY
        self.environmental_objectives = [
            "climate_change_mitigation",
            "climate_change_adaptation", 
            "sustainable_water_marine",
            "circular_economy",
            "pollution_prevention",
            "biodiversity_ecosystems"
        ]
        
    def generate_report(self, company_data: Dict, activity_data: List[Dict], financial_data: Dict) -> Dict:
        """Generate EU Taxonomy compliance report"""
        try:
            report = {
                "metadata": {
                    "framework": "EU_Taxonomy",
                    "version": "2024",
                    "generated_at": datetime.utcnow().isoformat(),
                    "company_id": company_data.get("id"),
                    "reporting_year": datetime.now().year,
                    "applicable_objectives": self.environmental_objectives
                },
                "article_8_disclosures": {}
            }
            
            # Article 8 Disclosures for each environmental objective
            for objective in self.environmental_objectives:
                report["article_8_disclosures"][objective] = self._generate_article_8_disclosure(
                    objective, activity_data, financial_data
                )
            
            # Summary KPIs
            report["summary_kpis"] = self._generate_summary_kpis(report["article_8_disclosures"], financial_data)
            
            # Calculate compliance score
            report["compliance_score"] = self._calculate_taxonomy_score(report)
            
            return report
            
        except Exception as e:
            raise Exception(f"EU Taxonomy report generation failed: {str(e)}")
    
    def _generate_article_8_disclosure(self, objective: str, activity_data: List[Dict], financial_data: Dict) -> Dict:
        """Generate Article 8 disclosure for specific environmental objective"""
        
        # Mock taxonomy-eligible activities (in practice, this would be based on real business activities)
        eligible_activities = self._identify_eligible_activities(objective, activity_data)
        aligned_activities = self._assess_alignment(eligible_activities)
        
        total_revenue = financial_data.get("total_revenue", 1000000)
        total_capex = financial_data.get("total_capex", 100000)
        total_opex = financial_data.get("total_opex", 50000)
        
        return {
            "environmental_objective": objective,
            "eligible_activities": eligible_activities,
            "aligned_activities": aligned_activities,
            "kpis": {
                "revenue": {
                    "eligible_percentage": self._calculate_eligible_percentage(eligible_activities, "revenue", total_revenue),
                    "aligned_percentage": self._calculate_aligned_percentage(aligned_activities, "revenue", total_revenue),
                    "absolute_eligible": sum(act.get("revenue", 0) for act in eligible_activities),
                    "absolute_aligned": sum(act.get("revenue", 0) for act in aligned_activities)
                },
                "capex": {
                    "eligible_percentage": self._calculate_eligible_percentage(eligible_activities, "capex", total_capex),
                    "aligned_percentage": self._calculate_aligned_percentage(aligned_activities, "capex", total_capex),
                    "absolute_eligible": sum(act.get("capex", 0) for act in eligible_activities),
                    "absolute_aligned": sum(act.get("capex", 0) for act in aligned_activities)
                },
                "opex": {
                    "eligible_percentage": self._calculate_eligible_percentage(eligible_activities, "opex", total_opex),
                    "aligned_percentage": self._calculate_aligned_percentage(aligned_activities, "opex", total_opex),
                    "absolute_eligible": sum(act.get("opex", 0) for act in eligible_activities),
                    "absolute_aligned": sum(act.get("opex", 0) for act in aligned_activities)
                }
            }
        }
    
    def _identify_eligible_activities(self, objective: str, activity_data: List[Dict]) -> List[Dict]:
        """Identify taxonomy-eligible activities for the environmental objective"""
        eligible_activities = []
        
        # Mock eligible activities based on objective
        if objective == "climate_change_mitigation":
            eligible_activities = [
                {
                    "activity_code": "4.1",
                    "activity_name": "Electricity generation using solar photovoltaic technology",
                    "revenue": 250000,
                    "capex": 15000,
                    "opex": 5000,
                    "description": "Solar PV installations"
                },
                {
                    "activity_code": "7.4",
                    "activity_name": "Operation of personal mobility devices, cycle logistics",
                    "revenue": 150000,
                    "capex": 8000,
                    "opex": 3000,
                    "description": "Electric vehicle fleet operations"
                }
            ]
        elif objective == "climate_change_adaptation":
            eligible_activities = [
                {
                    "activity_code": "13.1",
                    "activity_name": "Manufacture of renewable energy technologies",
                    "revenue": 180000,
                    "capex": 12000,
                    "opex": 4000,
                    "description": "Manufacturing climate adaptation equipment"
                }
            ]
        
        return eligible_activities
    
    def _assess_alignment(self, eligible_activities: List[Dict]) -> List[Dict]:
        """Assess which eligible activities are also aligned (meet technical criteria and safeguards)"""
        aligned_activities = []
        
        for activity in eligible_activities:
            # Mock alignment assessment
            alignment_score = self._calculate_alignment_score(activity)
            
            if alignment_score >= 80:  # Threshold for alignment
                activity["alignment_score"] = alignment_score
                activity["alignment_status"] = "Aligned"
                activity["technical_criteria_met"] = True
                activity["dnsh_criteria_met"] = True
                activity["minimum_safeguards_met"] = True
                aligned_activities.append(activity)
            else:
                activity["alignment_score"] = alignment_score
                activity["alignment_status"] = "Not aligned"
                activity["barriers_to_alignment"] = self._identify_alignment_barriers(activity)
        
        return aligned_activities
    
    def _calculate_alignment_score(self, activity: Dict) -> int:
        """Calculate alignment score for an activity (mock implementation)"""
        # In practice, this would assess against technical screening criteria,
        # DNSH criteria, and minimum safeguards
        base_score = 70
        
        # Bonus points for various criteria
        if activity.get("activity_code", "").startswith("4."):  # Renewable energy
            base_score += 20
        if activity.get("revenue", 0) > 200000:  # Significant scale
            base_score += 10
        
        return min(base_score, 100)
    
    def _identify_alignment_barriers(self, activity: Dict) -> List[str]:
        """Identify barriers preventing an activity from being taxonomy-aligned"""
        barriers = []
        
        if activity.get("alignment_score", 0) < 60:
            barriers.append("Technical screening criteria not fully met")
        if activity.get("alignment_score", 0) < 70:
            barriers.append("DNSH criteria concerns")
        if activity.get("alignment_score", 0) < 80:
            barriers.append("Minimum safeguards assessment incomplete")
        
        return barriers
    
    def _calculate_eligible_percentage(self, activities: List[Dict], metric: str, total: float) -> float:
        """Calculate percentage of eligible activities for a KPI"""
        if total == 0:
            return 0.0
        
        eligible_total = sum(act.get(metric, 0) for act in activities)
        return (eligible_total / total) * 100
    
    def _calculate_aligned_percentage(self, activities: List[Dict], metric: str, total: float) -> float:
        """Calculate percentage of aligned activities for a KPI"""
        if total == 0:
            return 0.0
        
        aligned_total = sum(act.get(metric, 0) for act in activities)
        return (aligned_total / total) * 100
    
    def _generate_summary_kpis(self, disclosures: Dict, financial_data: Dict) -> Dict:
        """Generate summary KPIs across all environmental objectives"""
        total_revenue = financial_data.get("total_revenue", 1000000)
        total_capex = financial_data.get("total_capex", 100000)
        total_opex = financial_data.get("total_opex", 50000)
        
        # Aggregate across all objectives (avoiding double counting)
        total_eligible_revenue = 0
        total_aligned_revenue = 0
        total_eligible_capex = 0
        total_aligned_capex = 0
        total_eligible_opex = 0
        total_aligned_opex = 0
        
        # Use climate change mitigation as primary (to avoid double counting)
        primary_objective = disclosures.get("climate_change_mitigation", {})
        
        if primary_objective:
            total_eligible_revenue = primary_objective["kpis"]["revenue"]["absolute_eligible"]
            total_aligned_revenue = primary_objective["kpis"]["revenue"]["absolute_aligned"]
            total_eligible_capex = primary_objective["kpis"]["capex"]["absolute_eligible"]
            total_aligned_capex = primary_objective["kpis"]["capex"]["absolute_aligned"]
            total_eligible_opex = primary_objective["kpis"]["opex"]["absolute_eligible"]
            total_aligned_opex = primary_objective["kpis"]["opex"]["absolute_aligned"]
        
        return {
            "turnover": {
                "eligible_percentage": (total_eligible_revenue / total_revenue) * 100 if total_revenue > 0 else 0,
                "aligned_percentage": (total_aligned_revenue / total_revenue) * 100 if total_revenue > 0 else 0,
                "absolute_eligible": total_eligible_revenue,
                "absolute_aligned": total_aligned_revenue,
                "total": total_revenue
            },
            "capex": {
                "eligible_percentage": (total_eligible_capex / total_capex) * 100 if total_capex > 0 else 0,
                "aligned_percentage": (total_aligned_capex / total_capex) * 100 if total_capex > 0 else 0,
                "absolute_eligible": total_eligible_capex,
                "absolute_aligned": total_aligned_capex,
                "total": total_capex
            },
            "opex": {
                "eligible_percentage": (total_eligible_opex / total_opex) * 100 if total_opex > 0 else 0,
                "aligned_percentage": (total_aligned_opex / total_opex) * 100 if total_opex > 0 else 0,
                "absolute_eligible": total_eligible_opex,
                "absolute_aligned": total_aligned_opex,
                "total": total_opex
            }
        }
    
    def _calculate_taxonomy_score(self, report: Dict) -> int:
        """Calculate EU Taxonomy compliance score"""
        summary = report.get("summary_kpis", {})
        
        # Weight different KPIs
        revenue_weight = 0.5
        capex_weight = 0.3
        opex_weight = 0.2
        
        revenue_score = summary.get("turnover", {}).get("aligned_percentage", 0)
        capex_score = summary.get("capex", {}).get("aligned_percentage", 0)
        opex_score = summary.get("opex", {}).get("aligned_percentage", 0)
        
        weighted_score = (
            revenue_score * revenue_weight +
            capex_score * capex_weight +
            opex_score * opex_weight
        )
        
        return int(min(weighted_score, 100))
