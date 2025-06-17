from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from ...db.database import get_db
from ...esg.models.reports import ESGReport, ReportStatus, ComplianceFramework
from ...core.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/esg/dashboard", tags=["ESG Dashboard"])

@router.get("/overview", response_model=Dict[str, Any])
async def get_dashboard_overview(
    company_id: Optional[int] = None,
    time_period: str = Query("12m", description="Time period: 1m, 3m, 6m, 12m, all"),
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Get ESG dashboard overview metrics"""
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        if time_period == "1m":
            start_date = end_date - timedelta(days=30)
        elif time_period == "3m":
            start_date = end_date - timedelta(days=90)
        elif time_period == "6m":
            start_date = end_date - timedelta(days=180)
        elif time_period == "12m":
            start_date = end_date - timedelta(days=365)
        else:
            start_date = datetime(2020, 1, 1)  # All time
        
        # Base query
        query = db.query(ESGReport).filter(ESGReport.created_at >= start_date)
        
        if company_id:
            query = query.filter(ESGReport.company_id == company_id)
        
        # Total reports
        total_reports = query.count()
        
        # Reports by status
        status_counts = {}
        for status in ReportStatus:
            count = query.filter(ESGReport.status == status).count()
            status_counts[status.value] = count
        
        # Reports by framework
        framework_counts = {}
        for framework in ComplianceFramework:
            count = query.filter(ESGReport.framework == framework).count()
            framework_counts[framework.value] = count
        
        # Average compliance score
        avg_compliance_score = db.query(func.avg(ESGReport.compliance_score)).filter(
            ESGReport.compliance_score.isnot(None),
            ESGReport.created_at >= start_date
        ).scalar() or 0
        
        # Recent activity (last 30 days)
        recent_cutoff = end_date - timedelta(days=30)
        recent_reports = query.filter(ESGReport.created_at >= recent_cutoff).count()
        
        # Monthly trend data
        monthly_trend = []
        for i in range(12):
            month_start = end_date - timedelta(days=30 * (i + 1))
            month_end = end_date - timedelta(days=30 * i)
            
            monthly_count = query.filter(
                ESGReport.created_at >= month_start,
                ESGReport.created_at < month_end
            ).count()
            
            monthly_trend.append({
                "month": month_start.strftime("%Y-%m"),
                "reports": monthly_count
            })
        
        monthly_trend.reverse()  # Chronological order
        
        # Compliance score trend
        compliance_trend = []
        reports_with_scores = query.filter(
            ESGReport.compliance_score.isnot(None)
        ).order_by(ESGReport.created_at.desc()).limit(50).all()
        
        for report in reversed(reports_with_scores):
            compliance_trend.append({
                "date": report.created_at.strftime("%Y-%m-%d"),
                "score": report.compliance_score,
                "framework": report.framework.value
            })
        
        return {
            "success": True,
            "overview": {
                "total_reports": total_reports,
                "recent_reports": recent_reports,
                "average_compliance_score": round(avg_compliance_score, 1),
                "time_period": time_period
            },
            "status_breakdown": status_counts,
            "framework_breakdown": framework_counts,
            "trends": {
                "monthly_reports": monthly_trend,
                "compliance_scores": compliance_trend
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get dashboard overview: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve dashboard data: {str(e)}"
        )

@router.get("/compliance-metrics", response_model=Dict[str, Any])
async def get_compliance_metrics(
    framework: Optional[str] = None,
    company_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Get detailed compliance metrics"""
    try:
        query = db.query(ESGReport).filter(ESGReport.compliance_score.isnot(None))
        
        if framework:
            query = query.filter(ESGReport.framework == ComplianceFramework(framework))
        
        if company_id:
            query = query.filter(ESGReport.company_id == company_id)
        
        reports = query.order_by(ESGReport.created_at.desc()).all()
        
        if not reports:
            return {
                "success": True,
                "metrics": {
                    "total_reports": 0,
                    "average_score": 0,
                    "score_distribution": [],
                    "framework_performance": []
                }
            }
        
        # Calculate metrics
        scores = [r.compliance_score for r in reports if r.compliance_score is not None]
        
        # Score distribution
        score_ranges = [
            {"range": "90-100", "count": len([s for s in scores if 90 <= s <= 100])},
            {"range": "80-89", "count": len([s for s in scores if 80 <= s < 90])},
            {"range": "70-79", "count": len([s for s in scores if 70 <= s < 80])},
            {"range": "60-69", "count": len([s for s in scores if 60 <= s < 70])},
            {"range": "0-59", "count": len([s for s in scores if s < 60])}
        ]
        
        # Framework performance
        framework_performance = []
        for fw in ComplianceFramework:
            fw_reports = [r for r in reports if r.framework == fw]
            if fw_reports:
                fw_scores = [r.compliance_score for r in fw_reports if r.compliance_score is not None]
                framework_performance.append({
                    "framework": fw.value,
                    "reports_count": len(fw_reports),
                    "average_score": round(sum(fw_scores) / len(fw_scores), 1) if fw_scores else 0,
                    "highest_score": max(fw_scores) if fw_scores else 0,
                    "latest_score": fw_reports[0].compliance_score if fw_reports else 0
                })
        
        return {
            "success": True,
            "metrics": {
                "total_reports": len(reports),
                "average_score": round(sum(scores) / len(scores), 1) if scores else 0,
                "highest_score": max(scores) if scores else 0,
                "lowest_score": min(scores) if scores else 0,
                "score_distribution": score_ranges,
                "framework_performance": framework_performance
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get compliance metrics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve compliance metrics: {str(e)}"
        )

@router.get("/recent-activity", response_model=Dict[str, Any])
async def get_recent_activity(
    limit: int = Query(20, description="Number of recent activities to return"),
    activity_types: Optional[str] = Query(None, description="Comma-separated activity types"),
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Get recent ESG reporting activity"""
    try:
        # Get recent reports with their activities
        recent_reports = db.query(ESGReport).order_by(
            ESGReport.updated_at.desc()
        ).limit(limit).all()
        
        activities = []
        for report in recent_reports:
            # Report creation
            activities.append({
                "id": f"report_created_{report.id}",
                "type": "report_created",
                "description": f"ESG report '{report.report_name}' created",
                "report_id": report.id,
                "report_name": report.report_name,
                "framework": report.framework.value,
                "timestamp": report.created_at.isoformat(),
                "user_id": report.created_by,
                "status": report.status.value
            })
            
            # Status changes
            if report.status != ReportStatus.DRAFT:
                activities.append({
                    "id": f"status_change_{report.id}",
                    "type": "status_changed",
                    "description": f"Report status changed to {report.status.value}",
                    "report_id": report.id,
                    "report_name": report.report_name,
                    "framework": report.framework.value,
                    "timestamp": report.updated_at.isoformat(),
                    "status": report.status.value
                })
            
            # Approvals
            if report.approved_at:
                activities.append({
                    "id": f"approval_{report.id}",
                    "type": "report_approved",
                    "description": f"Report '{report.report_name}' approved",
                    "report_id": report.id,
                    "report_name": report.report_name,
                    "framework": report.framework.value,
                    "timestamp": report.approved_at.isoformat(),
                    "status": report.status.value
                })
            
            # Publications
            if report.published_at:
                activities.append({
                    "id": f"publication_{report.id}",
                    "type": "report_published",
                    "description": f"Report '{report.report_name}' published",
                    "report_id": report.id,
                    "report_name": report.report_name,
                    "framework": report.framework.value,
                    "timestamp": report.published_at.isoformat(),
                    "status": report.status.value
                })
        
        # Sort by timestamp and limit
        activities.sort(key=lambda x: x["timestamp"], reverse=True)
        activities = activities[:limit]
        
        # Filter by activity types if specified
        if activity_types:
            filter_types = [t.strip() for t in activity_types.split(",")]
            activities = [a for a in activities if a["type"] in filter_types]
        
        return {
            "success": True,
            "activities": activities,
            "total_activities": len(activities),
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get recent activity: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve recent activity: {str(e)}"
        )

@router.get("/performance-analytics", response_model=Dict[str, Any])
async def get_performance_analytics(
    framework: Optional[str] = None,
    time_range: str = Query("12m", description="Time range: 3m, 6m, 12m, 24m"),
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Get ESG performance analytics and trends"""
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        months = {"3m": 3, "6m": 6, "12m": 12, "24m": 24}.get(time_range, 12)
        start_date = end_date - timedelta(days=30 * months)
        
        query = db.query(ESGReport).filter(
            ESGReport.created_at >= start_date,
            ESGReport.compliance_score.isnot(None)
        )
        
        if framework:
            query = query.filter(ESGReport.framework == ComplianceFramework(framework))
        
        reports = query.order_by(ESGReport.created_at.asc()).all()
        
        # Performance trends
        monthly_performance = {}
        for report in reports:
            month_key = report.created_at.strftime("%Y-%m")
            if month_key not in monthly_performance:
                monthly_performance[month_key] = {
                    "month": month_key,
                    "reports": [],
                    "average_score": 0,
                    "report_count": 0
                }
            monthly_performance[month_key]["reports"].append(report.compliance_score)
        
        # Calculate averages
        trend_data = []
        for month_data in monthly_performance.values():
            scores = month_data["reports"]
            month_data["average_score"] = round(sum(scores) / len(scores), 1) if scores else 0
            month_data["report_count"] = len(scores)
            trend_data.append({
                "month": month_data["month"],
                "average_score": month_data["average_score"],
                "report_count": month_data["report_count"]
            })
        
        # Sort by month
        trend_data.sort(key=lambda x: x["month"])
        
        # Benchmark analysis
        all_scores = [r.compliance_score for r in reports]
        
        benchmark_analysis = {
            "current_average": round(sum(all_scores) / len(all_scores), 1) if all_scores else 0,
            "industry_benchmark": 75.0,  # Mock industry benchmark
            "best_in_class": 92.0,  # Mock best-in-class benchmark
            "performance_rating": "Above Average"  # Would be calculated based on actual benchmarks
        }
        
        # Improvement opportunities
        framework_scores = {}
        for report in reports:
            fw = report.framework.value
            if fw not in framework_scores:
                framework_scores[fw] = []
            framework_scores[fw].append(report.compliance_score)
        
        improvement_opportunities = []
        for fw, scores in framework_scores.items():
            avg_score = sum(scores) / len(scores)
            if avg_score < 80:  # Threshold for improvement
                improvement_opportunities.append({
                    "framework": fw,
                    "current_score": round(avg_score, 1),
                    "potential_improvement": round(85 - avg_score, 1),
                    "priority": "High" if avg_score < 70 else "Medium"
                })
        
        return {
            "success": True,
            "performance_analytics": {
                "time_range": time_range,
                "trend_data": trend_data,
                "benchmark_analysis": benchmark_analysis,
                "improvement_opportunities": improvement_opportunities,
                "total_reports_analyzed": len(reports)
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance analytics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve performance analytics: {str(e)}"
        )
