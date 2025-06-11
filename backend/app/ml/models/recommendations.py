import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

logger = logging.getLogger(__name__)

class SustainabilityRecommendationEngine:
    """AI-powered recommendation engine for sustainability initiatives"""
    
    def __init__(self):
        self.company_profiles = {}
        self.initiative_embeddings = {}
        self.similarity_matrix = None
        self.clusters = {}
        self.is_trained = False
        
    def create_company_profile(self, company_data: Dict) -> Dict:
        """Create comprehensive company profile for recommendations"""
        try:
            profile = {
                'company_id': company_data.get('company_id'),
                'industry_sector': company_data.get('industry_sector', 'Unknown'),
                'company_size': company_data.get('company_size', 'Medium'),
                'annual_emissions': company_data.get('annual_emissions', 0),
                'budget_range': company_data.get('budget_range', 'Medium'),
                'current_initiatives': company_data.get('current_initiatives', []),
                'emission_breakdown': company_data.get('emission_breakdown', {}),
                'reduction_targets': company_data.get('reduction_targets', {}),
                'sustainability_maturity': self._assess_maturity(company_data),
                'risk_tolerance': company_data.get('risk_tolerance', 'Medium')
            }
            
            # Calculate profile features
            profile['features'] = self._extract_company_features(profile)
            
            return profile
            
        except Exception as e:
            logger.error(f"Error creating company profile: {e}")
            raise
    
    def _assess_maturity(self, company_data: Dict) -> str:
        """Assess company's sustainability maturity level"""
        try:
            score = 0
            
            # Existing initiatives
            initiatives = company_data.get('current_initiatives', [])
            score += min(len(initiatives) * 10, 40)
            
            # Emission tracking
            if company_data.get('has_emission_tracking', False):
                score += 20
            
            # Targets set
            targets = company_data.get('reduction_targets', {})
            if targets:
                score += 20
            
            # Reporting
            if company_data.get('sustainability_reporting', False):
                score += 20
            
            # Classify maturity
            if score >= 80:
                return 'Advanced'
            elif score >= 50:
                return 'Intermediate'
            elif score >= 20:
                return 'Beginner'
            else:
                return 'Starter'
                
        except Exception as e:
            logger.error(f"Error assessing maturity: {e}")
            return 'Unknown'
    
    def _extract_company_features(self, profile: Dict) -> np.ndarray:
        """Extract numerical features from company profile"""
        try:
            features = []
            
            # Industry encoding (simplified)
            industry_encoding = {
                'Technology': 1, 'Manufacturing': 2, 'Energy': 3,
                'Transportation': 4, 'Construction': 5, 'Other': 0
            }
            features.append(industry_encoding.get(profile['industry_sector'], 0))
            
            # Size encoding
            size_encoding = {'Small': 1, 'Medium': 2, 'Large': 3}
            features.append(size_encoding.get(profile['company_size'], 2))
            
            # Emissions (log scale)
            features.append(np.log1p(profile['annual_emissions']))
            
            # Budget encoding
            budget_encoding = {'Low': 1, 'Medium': 2, 'High': 3}
            features.append(budget_encoding.get(profile['budget_range'], 2))
            
            # Maturity encoding
            maturity_encoding = {'Starter': 1, 'Beginner': 2, 'Intermediate': 3, 'Advanced': 4}
            features.append(maturity_encoding.get(profile['sustainability_maturity'], 1))
            
            # Number of current initiatives
            features.append(len(profile['current_initiatives']))
            
            # Scope breakdown (if available)
            breakdown = profile.get('emission_breakdown', {})
            features.extend([
                breakdown.get('scope1', 0),
                breakdown.get('scope2', 0),
                breakdown.get('scope3', 0)
            ])
            
            return np.array(features)
            
        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return np.zeros(9)
    
    def load_initiative_database(self, initiatives: List[Dict]) -> Dict:
        """Load and process sustainability initiatives database"""
        try:
            processed_initiatives = []
            
            for init in initiatives:
                processed_init = {
                    'id': init.get('id'),
                    'name': init.get('name'),
                    'category': init.get('category', 'Other'),
                    'subcategory': init.get('subcategory', ''),
                    'description': init.get('description', ''),
                    'cost_range': init.get('cost_range', 'Medium'),
                    'implementation_time': init.get('implementation_time', 'Medium'),
                    'co2_reduction_potential': init.get('co2_reduction_potential', 0),
                    'complexity': init.get('complexity', 'Medium'),
                    'industry_applicability': init.get('industry_applicability', []),
                    'company_size_fit': init.get('company_size_fit', []),
                    'prerequisites': init.get('prerequisites', []),
                    'benefits': init.get('benefits', []),
                    'risks': init.get('risks', []),
                    'roi_timeframe': init.get('roi_timeframe', 'Medium'),
                    'sustainability_impact': init.get('sustainability_impact', 'Medium')
                }
                
                # Create feature vector for initiative
                processed_init['features'] = self._extract_initiative_features(processed_init)
                processed_initiatives.append(processed_init)
            
            self.initiatives_db = processed_initiatives
            self._build_similarity_matrix()
            
            return {
                'total_initiatives': len(processed_initiatives),
                'categories': list(set(init['category'] for init in processed_initiatives)),
                'cost_ranges': list(set(init['cost_range'] for init in processed_initiatives))
            }
            
        except Exception as e:
            logger.error(f"Error loading initiative database: {e}")
            raise
    
    def _extract_initiative_features(self, initiative: Dict) -> np.ndarray:
        """Extract numerical features from initiative"""
        try:
            features = []
            
            # Category encoding
            category_encoding = {
                'Energy Efficiency': 1, 'Renewable Energy': 2, 'Transportation': 3,
                'Waste Management': 4, 'Water Conservation': 5, 'Green Building': 6,
                'Supply Chain': 7, 'Other': 0
            }
            features.append(category_encoding.get(initiative['category'], 0))
            
            # Cost encoding
            cost_encoding = {'Low': 1, 'Medium': 2, 'High': 3}
            features.append(cost_encoding.get(initiative['cost_range'], 2))
            
            # Implementation time
            time_encoding = {'Short': 1, 'Medium': 2, 'Long': 3}
            features.append(time_encoding.get(initiative['implementation_time'], 2))
            
            # CO2 reduction potential (log scale)
            features.append(np.log1p(initiative['co2_reduction_potential']))
            
            # Complexity
            complexity_encoding = {'Low': 1, 'Medium': 2, 'High': 3}
            features.append(complexity_encoding.get(initiative['complexity'], 2))
            
            # ROI timeframe
            roi_encoding = {'Short': 1, 'Medium': 2, 'Long': 3}
            features.append(roi_encoding.get(initiative['roi_timeframe'], 2))
            
            # Impact
            impact_encoding = {'Low': 1, 'Medium': 2, 'High': 3}
            features.append(impact_encoding.get(initiative['sustainability_impact'], 2))
            
            # Industry applicability (binary features for top industries)
            top_industries = ['Technology', 'Manufacturing', 'Energy', 'Transportation']
            for industry in top_industries:
                features.append(1 if industry in initiative['industry_applicability'] else 0)
            
            return np.array(features)
            
        except Exception as e:
            logger.error(f"Error extracting initiative features: {e}")
            return np.zeros(11)
    
    def _build_similarity_matrix(self):
        """Build similarity matrix for initiatives"""
        try:
            if not self.initiatives_db:
                return
            
            # Extract all feature vectors
            features = np.array([init['features'] for init in self.initiatives_db])
            
            # Scale features
            scaler = StandardScaler()
            features_scaled = scaler.fit_transform(features)
            
            # Calculate cosine similarity
            self.similarity_matrix = cosine_similarity(features_scaled)
            self.feature_scaler = scaler
            
            logger.info(f"Built similarity matrix: {self.similarity_matrix.shape}")
            
        except Exception as e:
            logger.error(f"Error building similarity matrix: {e}")
            raise
    
    def recommend_initiatives(
        self,
        company_profile: Dict,
        num_recommendations: int = 10,
        filter_existing: bool = True
    ) -> Dict:
        """Generate personalized initiative recommendations"""
        try:
            if not self.initiatives_db:
                raise ValueError("Initiative database not loaded")
            
            company_features = company_profile['features']
            existing_initiatives = set(company_profile.get('current_initiatives', []))
            
            recommendations = []
            
            # Method 1: Content-based filtering
            content_scores = self._content_based_recommendations(company_profile)
            
            # Method 2: Collaborative filtering (simplified)
            collaborative_scores = self._collaborative_recommendations(company_profile)
            
            # Method 3: Rules-based recommendations
            rules_scores = self._rules_based_recommendations(company_profile)
            
            # Combine scores
            for i, initiative in enumerate(self.initiatives_db):
                if filter_existing and initiative['name'] in existing_initiatives:
                    continue
                
                # Weighted combination of methods
                combined_score = (
                    0.4 * content_scores.get(i, 0) +
                    0.3 * collaborative_scores.get(i, 0) +
                    0.3 * rules_scores.get(i, 0)
                )
                
                # Calculate confidence and rationale
                confidence = self._calculate_confidence(company_profile, initiative)
                rationale = self._generate_rationale(company_profile, initiative)
                
                recommendation = {
                    'initiative': initiative,
                    'score': float(combined_score),
                    'confidence': float(confidence),
                    'rationale': rationale,
                    'estimated_impact': self._estimate_impact(company_profile, initiative),
                    'implementation_roadmap': self._generate_roadmap(initiative)
                }
                
                recommendations.append(recommendation)
            
            # Sort by score and return top recommendations
            recommendations.sort(key=lambda x: x['score'], reverse=True)
            top_recommendations = recommendations[:num_recommendations]
            
            return {
                'recommendations': top_recommendations,
                'total_considered': len(recommendations),
                'company_profile_summary': self._summarize_profile(company_profile),
                'recommendation_metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'methods_used': ['content_based', 'collaborative', 'rules_based'],
                    'filters_applied': ['existing_initiatives'] if filter_existing else []
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            raise
    
    def _content_based_recommendations(self, company_profile: Dict) -> Dict:
        """Content-based recommendation using feature similarity"""
        try:
            scores = {}
            company_features = company_profile['features']
            
            if self.feature_scaler is None:
                return scores
            
            # Scale company features
            company_features_scaled = self.feature_scaler.transform(
                company_features.reshape(1, -1)
            )
            
            for i, initiative in enumerate(self.initiatives_db):
                init_features_scaled = self.feature_scaler.transform(
                    initiative['features'].reshape(1, -1)
                )
                
                # Calculate similarity
                similarity = cosine_similarity(
                    company_features_scaled, init_features_scaled
                )[0][0]
                
                scores[i] = similarity
            
            return scores
            
        except Exception as e:
            logger.error(f"Error in content-based recommendations: {e}")
            return {}
    
    def _collaborative_recommendations(self, company_profile: Dict) -> Dict:
        """Simplified collaborative filtering"""
        try:
            scores = {}
            
            # Find similar companies (simplified - in practice, use user-item matrix)
            similar_industry = company_profile['industry_sector']
            similar_size = company_profile['company_size']
            
            # Boost scores for initiatives popular in similar companies
            for i, initiative in enumerate(self.initiatives_db):
                score = 0.5  # Base score
                
                # Industry match bonus
                if similar_industry in initiative['industry_applicability']:
                    score += 0.3
                
                # Size match bonus
                if similar_size in initiative['company_size_fit']:
                    score += 0.2
                
                scores[i] = score
            
            return scores
            
        except Exception as e:
            logger.error(f"Error in collaborative recommendations: {e}")
            return {}
    
    def _rules_based_recommendations(self, company_profile: Dict) -> Dict:
        """Rules-based recommendations using business logic"""
        try:
            scores = {}
            
            annual_emissions = company_profile['annual_emissions']
            maturity = company_profile['sustainability_maturity']
            budget_range = company_profile['budget_range']
            
            for i, initiative in enumerate(self.initiatives_db):
                score = 0.5  # Base score
                
                # Maturity matching
                if maturity == 'Starter' and initiative['complexity'] == 'Low':
                    score += 0.3
                elif maturity == 'Advanced' and initiative['complexity'] == 'High':
                    score += 0.2
                
                # Budget matching
                budget_match = {
                    ('Low', 'Low'): 0.3,
                    ('Medium', 'Medium'): 0.2,
                    ('High', 'High'): 0.1,
                    ('High', 'Medium'): 0.15,
                    ('High', 'Low'): 0.2
                }
                score += budget_match.get((budget_range, initiative['cost_range']), 0)
                
                # High impact bonus for high emitters
                if annual_emissions > 10000 and initiative['sustainability_impact'] == 'High':
                    score += 0.2
                
                # Quick wins for beginners
                if (maturity in ['Starter', 'Beginner'] and 
                    initiative['implementation_time'] == 'Short'):
                    score += 0.2
                
                scores[i] = min(score, 1.0)  # Cap at 1.0
            
            return scores
            
        except Exception as e:
            logger.error(f"Error in rules-based recommendations: {e}")
            return {}
    
    def _calculate_confidence(self, company_profile: Dict, initiative: Dict) -> float:
        """Calculate confidence score for recommendation"""
        try:
            confidence = 0.5  # Base confidence
            
            # Industry match
            if company_profile['industry_sector'] in initiative['industry_applicability']:
                confidence += 0.2
            
            # Size match
            if company_profile['company_size'] in initiative['company_size_fit']:
                confidence += 0.15
            
            # Prerequisites check
            current_initiatives = set(company_profile.get('current_initiatives', []))
            prerequisites = set(initiative.get('prerequisites', []))
            
            if prerequisites.issubset(current_initiatives):
                confidence += 0.15
            elif prerequisites and not prerequisites.intersection(current_initiatives):
                confidence -= 0.2
            
            # Budget feasibility
            budget_map = {'Low': 1, 'Medium': 2, 'High': 3}
            company_budget = budget_map.get(company_profile['budget_range'], 2)
            init_cost = budget_map.get(initiative['cost_range'], 2)
            
            if company_budget >= init_cost:
                confidence += 0.1
            else:
                confidence -= 0.15
            
            return max(0.0, min(1.0, confidence))
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return 0.5
    
    def _generate_rationale(self, company_profile: Dict, initiative: Dict) -> List[str]:
        """Generate human-readable rationale for recommendation"""
        try:
            rationale = []
            
            # Industry match
            if company_profile['industry_sector'] in initiative['industry_applicability']:
                rationale.append(
                    f"Well-suited for {company_profile['industry_sector']} companies"
                )
            
            # Maturity match
            maturity = company_profile['sustainability_maturity']
            complexity = initiative['complexity']
            
            if maturity == 'Starter' and complexity == 'Low':
                rationale.append("Perfect starting point for sustainability journey")
            elif maturity == 'Advanced' and complexity == 'High':
                rationale.append("Advanced initiative matching your sustainability maturity")
            
            # Impact potential
            if initiative['co2_reduction_potential'] > 1000:
                rationale.append("High carbon reduction potential")
            
            # Cost effectiveness
            if (initiative['cost_range'] == 'Low' and 
                initiative['sustainability_impact'] in ['Medium', 'High']):
                rationale.append("Cost-effective solution with good impact")
            
            # Quick implementation
            if initiative['implementation_time'] == 'Short':
                rationale.append("Can be implemented quickly for immediate impact")
            
            # ROI
            if initiative['roi_timeframe'] == 'Short':
                rationale.append("Quick return on investment expected")
            
            return rationale[:3]  # Limit to top 3 reasons
            
        except Exception as e:
            logger.error(f"Error generating rationale: {e}")
            return ["Recommended based on company profile analysis"]
    
    def _estimate_impact(self, company_profile: Dict, initiative: Dict) -> Dict:
        """Estimate implementation impact for the company"""
        try:
            annual_emissions = company_profile['annual_emissions']
            
            # Base reduction from initiative specs
            base_reduction = initiative['co2_reduction_potential']
            
            # Scale based on company size
            size_multipliers = {'Small': 0.5, 'Medium': 1.0, 'Large': 2.0}
            size_multiplier = size_multipliers.get(company_profile['company_size'], 1.0)
            
            estimated_reduction = base_reduction * size_multiplier
            
            # Calculate percentage of total emissions
            reduction_percentage = (estimated_reduction / annual_emissions * 100) if annual_emissions > 0 else 0
            
            # Estimate costs (simplified)
            cost_ranges = {
                'Low': (10000, 50000),
                'Medium': (50000, 200000),
                'High': (200000, 1000000)
            }
            cost_range = cost_ranges.get(initiative['cost_range'], (50000, 200000))
            estimated_cost = cost_range[0] * size_multiplier
            
            return {
                'estimated_co2_reduction': float(estimated_reduction),
                'reduction_percentage': float(reduction_percentage),
                'estimated_cost': float(estimated_cost),
                'cost_per_tonne_co2': float(estimated_cost / estimated_reduction) if estimated_reduction > 0 else 0,
                'payback_period_years': self._estimate_payback(estimated_cost, estimated_reduction)
            }
            
        except Exception as e:
            logger.error(f"Error estimating impact: {e}")
            return {}
    
    def _estimate_payback(self, cost: float, co2_reduction: float) -> float:
        """Estimate payback period in years"""
        try:
            # Assume $50 per tonne CO2 cost savings (simplified)
            carbon_price = 50
            annual_savings = co2_reduction * carbon_price
            
            if annual_savings > 0:
                return cost / annual_savings
            else:
                return float('inf')
                
        except Exception as e:
            return float('inf')
    
    def _generate_roadmap(self, initiative: Dict) -> Dict:
        """Generate implementation roadmap"""
        try:
            phases = []
            
            # Phase 1: Planning
            phases.append({
                'phase': 'Planning & Assessment',
                'duration': '2-4 weeks',
                'activities': [
                    'Conduct detailed feasibility study',
                    'Stakeholder alignment',
                    'Budget approval',
                    'Resource allocation'
                ]
            })
            
            # Phase 2: Implementation
            impl_time = initiative['implementation_time']
            impl_duration = {
                'Short': '1-3 months',
                'Medium': '3-9 months',
                'Long': '9-18 months'
            }.get(impl_time, '3-6 months')
            
            phases.append({
                'phase': 'Implementation',
                'duration': impl_duration,
                'activities': [
                    'Project kickoff',
                    'System deployment/changes',
                    'Staff training',
                    'Initial testing'
                ]
            })
            
            # Phase 3: Monitoring
            phases.append({
                'phase': 'Monitoring & Optimization',
                'duration': 'Ongoing',
                'activities': [
                    'Performance tracking',
                    'Regular reporting',
                    'Continuous improvement',
                    'Impact measurement'
                ]
            })
            
            return {
                'phases': phases,
                'total_timeline': impl_duration,
                'key_milestones': [
                    'Feasibility study complete',
                    'Implementation 50% complete',
                    'Full deployment',
                    'First impact measurement'
                ]
            }
            
        except Exception as e:
            logger.error(f"Error generating roadmap: {e}")
            return {}
    
    def _summarize_profile(self, company_profile: Dict) -> Dict:
        """Summarize company profile for recommendations"""
        return {
            'industry': company_profile['industry_sector'],
            'size': company_profile['company_size'],
            'maturity': company_profile['sustainability_maturity'],
            'annual_emissions': company_profile['annual_emissions'],
            'budget_range': company_profile['budget_range'],
            'current_initiatives_count': len(company_profile.get('current_initiatives', []))
        }
