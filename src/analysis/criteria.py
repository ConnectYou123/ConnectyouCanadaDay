"""
Defines the value investing criteria and their evaluation logic.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import numpy as np

@dataclass
class Criterion:
    name: str
    description: str
    category: str
    evaluation_function: callable
    weight: float = 1.0
    
class ValueInvestingCriteria:
    """Collection of value investing criteria based on legendary investors."""
    
    @staticmethod
    def evaluate_pe_ratio(data: Dict[str, Any]) -> Optional[float]:
        """Evaluate P/E ratio criterion (Graham's principle)."""
        try:
            pe_ratio = data.get('pe_ratio')
            if pe_ratio is None or pe_ratio <= 0:
                return 0
            # Score based on PE ratio (higher score for lower PE)
            if pe_ratio <= 15:
                return 1.0
            elif pe_ratio <= 30:
                return 0.5
            return 0
        except Exception:
            return None
            
    @staticmethod
    def evaluate_gross_margin(data: Dict[str, Any]) -> Optional[float]:
        """Evaluate gross margin criterion (>40%)."""
        try:
            gross_margin = data.get('gross_margin', 0)
            if gross_margin >= 40:
                return 1.0
            elif gross_margin >= 30:
                return 0.5
            return 0
        except Exception:
            return None
    
    @staticmethod
    def evaluate_roe(data: Dict[str, Any]) -> Optional[float]:
        """Evaluate Return on Equity criterion (>30%)."""
        try:
            roe = data.get('roe', 0)
            if roe >= 30:
                return 1.0
            elif roe >= 20:
                return 0.5
            return 0
        except Exception:
            return None
    
    @staticmethod
    def evaluate_debt_coverage(data: Dict[str, Any]) -> Optional[float]:
        """Evaluate if 3 years FCF covers long-term debt."""
        try:
            fcf_3year = data.get('fcf_3year_sum', 0)
            long_term_debt = data.get('long_term_debt', 0)
            if long_term_debt == 0:
                return 1.0
            coverage_ratio = fcf_3year / long_term_debt if long_term_debt > 0 else float('inf')
            if coverage_ratio >= 1:
                return 1.0
            elif coverage_ratio >= 0.5:
                return 0.5
            return 0
        except Exception:
            return None

    @staticmethod
    def evaluate_price_to_book(data: Dict[str, Any]) -> Optional[float]:
        """Evaluate Price-to-Book ratio (Graham's principle: under 3)."""
        try:
            pb_ratio = data.get('price_to_book', float('inf'))
            if pb_ratio <= 1.5:
                return 1.0
            elif pb_ratio <= 3.0:
                return 0.5
            return 0
        except Exception:
            return None

    @staticmethod
    def evaluate_sales_growth(data: Dict[str, Any]) -> Optional[float]:
        """Evaluate sales growth (15%+ for 5 years)."""
        try:
            sales_growth = data.get('sales_growth', 0)
            if sales_growth >= 15:
                return 1.0
            elif sales_growth >= 10:
                return 0.5
            return 0
        except Exception:
            return None

    @staticmethod
    def evaluate_fcf_growth(data: Dict[str, Any]) -> Optional[float]:
        """Evaluate Free Cash Flow growth year-over-year."""
        try:
            fcf_growth = data.get('fcf_growth', 0)
            if fcf_growth > 0:
                return 1.0
            return 0
        except Exception:
            return None

    @staticmethod
    def evaluate_market_cap(data: Dict[str, Any]) -> Optional[float]:
        """Evaluate market capitalization (minimum $100M)."""
        try:
            market_cap = data.get('market_cap', 0)
            if market_cap >= 1000000000:  # $1B
                return 1.0
            elif market_cap >= 100000000:  # $100M
                return 0.5
            return 0
        except Exception:
            return None

    @staticmethod
    def evaluate_retained_earnings(data: Dict[str, Any]) -> Optional[float]:
        """Evaluate retained earnings (should be positive and accumulating)."""
        try:
            retained_earnings = data.get('retained_earnings', 0)
            if retained_earnings > 0:
                return 1.0
            return 0
        except Exception:
            return None

    @staticmethod
    def evaluate_executive_compensation(data: Dict[str, Any]) -> Optional[float]:
        """Evaluate executive compensation (under $30M or 5% of FCF)."""
        try:
            exec_comp = data.get('executive_compensation', 0)
            fcf = data.get('fcf_3year_sum', 0)
            if exec_comp <= 30000000 or (fcf > 0 and exec_comp <= fcf * 0.05):
                return 1.0
            return 0
        except Exception:
            return None

    @staticmethod
    def evaluate_brand_strength(data: Dict[str, Any]) -> Optional[float]:
        """Evaluate brand strength and recognition."""
        try:
            brand_score = data.get('brand_strength', 0)
            if brand_score >= 8:
                return 1.0
            elif brand_score >= 5:
                return 0.5
            return 0
        except Exception:
            return None

    @staticmethod
    def evaluate_switching_costs(data: Dict[str, Any]) -> Optional[float]:
        """Evaluate customer switching costs."""
        try:
            switching_costs = data.get('switching_costs', 0)
            if switching_costs >= 8:
                return 1.0
            elif switching_costs >= 5:
                return 0.5
            return 0
        except Exception:
            return None

    @staticmethod
    def evaluate_industry_leadership(data: Dict[str, Any]) -> Optional[float]:
        """Evaluate industry leadership position."""
        try:
            market_share = data.get('market_share', 0)
            if market_share >= 30:
                return 1.0
            elif market_share >= 15:
                return 0.5
            return 0
        except Exception:
            return None

    @staticmethod
    def evaluate_margin_of_safety(data: Dict[str, Any]) -> Optional[float]:
        """Evaluate margin of safety (Graham's principle)."""
        try:
            # Simple margin of safety calculation based on P/E and P/B
            pe_ratio = data.get('pe_ratio', float('inf'))
            pb_ratio = data.get('price_to_book', float('inf'))
            
            if pe_ratio <= 15 and pb_ratio <= 1.5:
                return 1.0
            elif pe_ratio <= 25 and pb_ratio <= 2.5:
                return 0.5
            return 0
        except Exception:
            return None

    @staticmethod
    def evaluate_business_durability(data: Dict[str, Any]) -> Optional[float]:
        """Evaluate if company will be successful 20 years from now."""
        try:
            # Based on brand strength, market position, and financial health
            brand_strength = data.get('brand_strength', 0)
            market_share = data.get('market_share', 0)
            debt_coverage = data.get('fcf_3year_sum', 0) / max(data.get('long_term_debt', 1), 1)
            
            score = 0
            if brand_strength >= 7: score += 0.4
            if market_share >= 20: score += 0.3
            if debt_coverage >= 1: score += 0.3
            
            return min(score, 1.0)
        except Exception:
            return None

    @staticmethod
    def evaluate_economic_necessity(data: Dict[str, Any]) -> Optional[float]:
        """Evaluate if the world would care if this company died tomorrow."""
        try:
            # Based on market position, brand strength, and sector importance
            market_share = data.get('market_share', 0)
            brand_strength = data.get('brand_strength', 0)
            sector = data.get('sector', '').lower()
            
            score = 0
            if market_share >= 25: score += 0.4
            if brand_strength >= 8: score += 0.3
            if any(essential in sector for essential in ['technology', 'healthcare', 'utilities', 'consumer']):
                score += 0.3
            
            return min(score, 1.0)
        except Exception:
            return None

    @staticmethod
    def evaluate_management_trust(data: Dict[str, Any]) -> Optional[float]:
        """Evaluate if you can trust the management."""
        try:
            # Based on executive compensation and financial transparency
            exec_comp = data.get('executive_compensation', 0)
            fcf = data.get('fcf_3year_sum', 0)
            
            if exec_comp <= 20000000 or (fcf > 0 and exec_comp <= fcf * 0.03):
                return 1.0
            elif exec_comp <= 50000000:
                return 0.5
            return 0
        except Exception:
            return None

    @staticmethod
    def evaluate_competitive_moat(data: Dict[str, Any]) -> Optional[float]:
        """Evaluate sustainable competitive advantage (moat)."""
        try:
            # Based on multiple moat indicators
            brand_strength = data.get('brand_strength', 0)
            switching_costs = data.get('switching_costs', 0)
            market_share = data.get('market_share', 0)
            gross_margin = data.get('gross_margin', 0)
            
            score = 0
            if brand_strength >= 8: score += 0.25
            if switching_costs >= 7: score += 0.25
            if market_share >= 20: score += 0.25
            if gross_margin >= 40: score += 0.25
            
            return min(score, 1.0)
        except Exception:
            return None

    @staticmethod
    def evaluate_capital_allocation(data: Dict[str, Any]) -> Optional[float]:
        """Evaluate management's capital allocation during adversity."""
        try:
            # Based on ROE, debt management, and retained earnings
            roe = data.get('roe', 0)
            debt_coverage = data.get('fcf_3year_sum', 0) / max(data.get('long_term_debt', 1), 1)
            retained_earnings = data.get('retained_earnings', 0)
            
            score = 0
            if roe >= 20: score += 0.4
            if debt_coverage >= 1: score += 0.3
            if retained_earnings > 0: score += 0.3
            
            return min(score, 1.0)
        except Exception:
            return None

    @staticmethod
    def evaluate_global_potential(data: Dict[str, Any]) -> Optional[float]:
        """Evaluate if company can go global."""
        try:
            # Based on brand strength, market position, and sector
            brand_strength = data.get('brand_strength', 0)
            market_share = data.get('market_share', 0)
            sector = data.get('sector', '').lower()
            
            score = 0
            if brand_strength >= 7: score += 0.4
            if market_share >= 15: score += 0.3
            if any(global_sector in sector for global_sector in ['technology', 'consumer', 'healthcare']):
                score += 0.3
            
            return min(score, 1.0)
        except Exception:
            return None

    @staticmethod
    def evaluate_10x_growth_potential(data: Dict[str, Any]) -> Optional[float]:
        """Evaluate if company can grow 10X."""
        try:
            # Based on market size, current position, and growth metrics
            market_share = data.get('market_share', 0)
            sales_growth = data.get('sales_growth', 0)
            sector = data.get('sector', '').lower()
            
            score = 0
            if market_share <= 10: score += 0.4  # Room to grow
            if sales_growth >= 20: score += 0.3
            if any(high_growth in sector for high_growth in ['technology', 'healthcare', 'renewable']):
                score += 0.3
            
            return min(score, 1.0)
        except Exception:
            return None

    @staticmethod
    def evaluate_relative_performance(data: Dict[str, Any]) -> Optional[float]:
        """Evaluate superior returns compared to competitors."""
        try:
            # Based on ROE, growth, and market position
            roe = data.get('roe', 0)
            sales_growth = data.get('sales_growth', 0)
            market_share = data.get('market_share', 0)
            
            score = 0
            if roe >= 25: score += 0.4
            if sales_growth >= 15: score += 0.3
            if market_share >= 20: score += 0.3
            
            return min(score, 1.0)
        except Exception:
            return None

    @staticmethod
    def evaluate_risk_assessment(data: Dict[str, Any]) -> Optional[float]:
        """Evaluate how we can lose our capital (Li Lu's approach)."""
        try:
            # Inverse risk assessment - lower risk = higher score
            debt_coverage = data.get('fcf_3year_sum', 0) / max(data.get('long_term_debt', 1), 1)
            market_cap = data.get('market_cap', 0)
            sector = data.get('sector', '').lower()
            
            score = 0
            if debt_coverage >= 2: score += 0.4  # Low debt risk
            if market_cap >= 10000000000: score += 0.3  # Large cap = lower risk
            if any(low_risk in sector for low_risk in ['utilities', 'consumer staples', 'healthcare']):
                score += 0.3
            
            return min(score, 1.0)
        except Exception:
            return None

    @staticmethod
    def evaluate_business_model_clarity(data: Dict[str, Any]) -> Optional[float]:
        """Evaluate how the company makes money (Li Lu's approach)."""
        try:
            # Based on gross margin, sector clarity, and market position
            gross_margin = data.get('gross_margin', 0)
            market_share = data.get('market_share', 0)
            sector = data.get('sector', '').lower()
            
            score = 0
            if gross_margin >= 30: score += 0.4  # Clear pricing power
            if market_share >= 15: score += 0.3  # Clear market position
            if any(simple_model in sector for simple_model in ['consumer', 'utilities', 'technology']):
                score += 0.3
            
            return min(score, 1.0)
        except Exception:
            return None

    @staticmethod
    def evaluate_competitive_analysis(data: Dict[str, Any]) -> Optional[float]:
        """Evaluate how it compares to competition (Li Lu's approach)."""
        try:
            # Based on market share, brand strength, and financial metrics
            market_share = data.get('market_share', 0)
            brand_strength = data.get('brand_strength', 0)
            roe = data.get('roe', 0)
            
            score = 0
            if market_share >= 25: score += 0.4  # Market leader
            if brand_strength >= 8: score += 0.3  # Strong brand
            if roe >= 20: score += 0.3  # Superior returns
            
            return min(score, 1.0)
        except Exception:
            return None

    @staticmethod
    def evaluate_earnings_quality(data: Dict[str, Any]) -> Optional[float]:
        """Evaluate if earnings are rising because book value is rising (not debt)."""
        try:
            # Based on ROE, debt levels, and retained earnings
            roe = data.get('roe', 0)
            debt_coverage = data.get('fcf_3year_sum', 0) / max(data.get('long_term_debt', 1), 1)
            retained_earnings = data.get('retained_earnings', 0)
            
            score = 0
            if roe >= 20: score += 0.4
            if debt_coverage >= 1.5: score += 0.3
            if retained_earnings > 0: score += 0.3
            
            return min(score, 1.0)
        except Exception:
            return None

    @staticmethod
    def evaluate_relative_growth(data: Dict[str, Any]) -> Optional[float]:
        """Evaluate if sales/users growing faster than industry or S&P 500."""
        try:
            # Based on sales growth and market position
            sales_growth = data.get('sales_growth', 0)
            market_share = data.get('market_share', 0)
            
            score = 0
            if sales_growth >= 20: score += 0.6  # Strong growth
            if market_share >= 15: score += 0.4  # Market position
            
            return min(score, 1.0)
        except Exception:
            return None

    @staticmethod
    def evaluate_customer_dependency(data: Dict[str, Any]) -> Optional[float]:
        """Evaluate if company is ingrained in customers' lives."""
        try:
            # Based on brand strength, switching costs, and sector
            brand_strength = data.get('brand_strength', 0)
            switching_costs = data.get('switching_costs', 0)
            sector = data.get('sector', '').lower()
            
            score = 0
            if brand_strength >= 8: score += 0.4
            if switching_costs >= 7: score += 0.3
            if any(essential in sector for essential in ['technology', 'consumer', 'healthcare']):
                score += 0.3
            
            return min(score, 1.0)
        except Exception:
            return None

    @staticmethod
    def evaluate_scenario_planning(data: Dict[str, Any]) -> Optional[float]:
        """Evaluate what can go wrong (Munger's inversion)."""
        try:
            # Inverse risk assessment - lower risk = higher score
            debt_coverage = data.get('fcf_3year_sum', 0) / max(data.get('long_term_debt', 1), 1)
            market_cap = data.get('market_cap', 0)
            sector = data.get('sector', '').lower()
            
            score = 0
            if debt_coverage >= 2: score += 0.4
            if market_cap >= 50000000000: score += 0.3  # Large cap = lower risk
            if any(stable in sector for stable in ['utilities', 'consumer staples', 'healthcare']):
                score += 0.3
            
            return min(score, 1.0)
        except Exception:
            return None

    def get_all_criteria(self) -> List[Criterion]:
        """Return all value investing criteria."""
        return [
            # Buffett & Munger Core Philosophy
            Criterion("Business Understanding", "Can you understand the business?", "Core Philosophy", self.evaluate_business_model_clarity, 1.0),
            Criterion("20-Year Success", "Will this company be successful 20 years from now?", "Core Philosophy", self.evaluate_business_durability, 1.0),
            Criterion("Economic Necessity", "If this company dies tomorrow, would anyone care?", "Core Philosophy", self.evaluate_economic_necessity, 1.0),
            Criterion("Competitive Moat", "Does this company have a competitive edge (moat)?", "Core Philosophy", self.evaluate_competitive_moat, 1.0),
            Criterion("Management Trust", "Can you trust the management?", "Core Philosophy", self.evaluate_management_trust, 1.0),
            
            # Graham Value Principles
            Criterion("Margin of Safety", "Is there a margin of safety?", "Graham Principles", self.evaluate_margin_of_safety, 1.0),
            Criterion("PE Ratio", "P/E ratio should be reasonable (under 15-30)", "Valuation", self.evaluate_pe_ratio, 1.0),
            Criterion("Price-to-Book", "P/B ratio should be under 3 (Graham's principle)", "Valuation", self.evaluate_price_to_book, 1.0),
            
            # Business Quality Assessment
            Criterion("Gross Margin", "Gross margin should be >40%", "Profitability", self.evaluate_gross_margin, 1.0),
            Criterion("Return on Equity", "ROE should be >30%", "Efficiency", self.evaluate_roe, 1.0),
            Criterion("Debt Coverage", "3 years FCF should cover long-term debt", "Financial Strength", self.evaluate_debt_coverage, 1.0),
            Criterion("FCF Growth", "Free Cash Flow should be positive and growing", "Cash Flow", self.evaluate_fcf_growth, 1.0),
            
            # Growth and Competitive Position
            Criterion("10X Growth Potential", "Can this company grow 10X?", "Growth", self.evaluate_10x_growth_potential, 1.0),
            Criterion("Global Potential", "Can this company go global?", "Growth", self.evaluate_global_potential, 1.0),
            Criterion("Sales Growth", "Sales should grow 15%+ year-over-year", "Growth", self.evaluate_sales_growth, 1.0),
            Criterion("Industry Leadership", "Company should be leader in their industry", "Competitive Position", self.evaluate_industry_leadership, 1.0),
            
            # Neff's Low P/E Strategy
            Criterion("Relative Performance", "Does it offer superior returns vs competitors?", "Performance", self.evaluate_relative_performance, 1.0),
            
            # Li Lu's Approach
            Criterion("Business Model Clarity", "How does the company make money?", "Business Model", self.evaluate_business_model_clarity, 1.0),
            Criterion("Competitive Analysis", "How does it compare to competition?", "Competition", self.evaluate_competitive_analysis, 1.0),
            Criterion("Risk Assessment", "How can we lose our capital?", "Risk", self.evaluate_risk_assessment, 1.0),
            
            # Mayer's 100 Baggers
            Criterion("Relative Growth", "Sales growing faster than industry/S&P 500?", "Growth", self.evaluate_relative_growth, 1.0),
            Criterion("Earnings Quality", "Earnings rising because book value rising?", "Quality", self.evaluate_earnings_quality, 1.0),
            
            # Management and Governance
            Criterion("Executive Compensation", "Executive compensation should be reasonable", "Governance", self.evaluate_executive_compensation, 0.5),
            Criterion("Capital Allocation", "Management knows how to allocate capital?", "Management", self.evaluate_capital_allocation, 1.0),
            Criterion("Retained Earnings", "Retained earnings should be positive", "Financial Strength", self.evaluate_retained_earnings, 1.0),
            
            # Moat Identification
            Criterion("Switching Costs", "High customer switching costs indicate moat", "Competitive Advantage", self.evaluate_switching_costs, 1.0),
            Criterion("Brand Strength", "Company should have strong brand recognition", "Competitive Advantage", self.evaluate_brand_strength, 1.0),
            Criterion("Customer Dependency", "Company ingrained in customers' lives?", "Competitive Advantage", self.evaluate_customer_dependency, 1.0),
            
            # Risk Management
            Criterion("Scenario Planning", "What can go wrong? (Munger's inversion)", "Risk Management", self.evaluate_scenario_planning, 1.0),
            
            # Additional Metrics
            Criterion("Market Cap", "Market capitalization should be >$100M", "Size", self.evaluate_market_cap, 0.5),
        ]
        
    def evaluate_company(self, company_data: Dict[str, Any]) -> Dict[str, float]:
        """Evaluate a company against all criteria."""
        results = {}
        criteria = self.get_all_criteria()
        
        for criterion in criteria:
            score = criterion.evaluation_function(company_data)
            if score is not None:
                results[criterion.name] = score * criterion.weight
                
        # Calculate overall score
        valid_scores = [score for score in results.values() if score is not None]
        results['overall_score'] = np.mean(valid_scores) if valid_scores else 0
        
        return results
    
    def get_criteria_evaluation(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed criteria evaluation with descriptions and thresholds for frontend display."""
        results = {}
        criteria = self.get_all_criteria()
        
        for criterion in criteria:
            try:
                score = criterion.evaluation_function(company_data)
                if score is not None:
                    # Determine rating based on score
                    if score >= 0.8:
                        rating = "Excellent"
                    elif score >= 0.6:
                        rating = "Good"
                    elif score >= 0.4:
                        rating = "Fair"
                    else:
                        rating = "Poor"
                    
                    # Create detailed result for frontend
                    results[criterion.name] = {
                        'score': score,
                        'rating': rating,
                        'description': criterion.description,
                        'category': criterion.category,
                        'weight': criterion.weight,
                        'source': self._get_criterion_source(criterion.name),
                        'threshold': self._get_criterion_threshold(criterion.name),
                        'current': self._get_current_value(criterion.name, company_data)
                    }
            except Exception as e:
                logger.error(f"Error evaluating criterion '{criterion.name}': {e}")
                results[criterion.name] = {
                    'score': 0,
                    'rating': "Error",
                    'description': criterion.description,
                    'category': criterion.category,
                    'weight': criterion.weight,
                    'source': "Error in calculation",
                    'threshold': "N/A",
                    'current': "N/A"
                }
        
        return results
    
    def _get_criterion_source(self, criterion_name: str) -> str:
        """Get the source/origin of each criterion."""
        sources = {
            'PE Ratio': 'Benjamin Graham',
            'Price-to-Book': 'Benjamin Graham', 
            'Gross Margin': 'Warren Buffett',
            'Return on Equity': 'Warren Buffett',
            'Competitive Moat': 'Warren Buffett',
            '20-Year Success': 'Warren Buffett',
            'Business Understanding': 'Charlie Munger',
            'Management Trust': 'Charlie Munger',
            'Scenario Planning': 'Charlie Munger',
            'Debt Coverage': "Phil Town's Rule #1",
            'FCF Growth': 'Warren Buffett',
            '10X Growth Potential': 'Growth Assessment',
            'Global Potential': 'Growth Assessment',
            'Sales Growth': 'Growth Analysis',
            'Industry Leadership': 'Market Analysis',
            'Relative Performance': 'John Neff',
            'Business Model Clarity': 'Li Lu',
            'Competitive Analysis': 'Li Lu',
            'Risk Assessment': 'Li Lu',
            'Relative Growth': 'Christopher Mayer',
            'Earnings Quality': 'Christopher Mayer',
            'Executive Compensation': 'Kenneth Jeffrey Marshall',
            'Capital Allocation': 'Management Assessment',
            'Retained Earnings': 'Financial Analysis',
            'Switching Costs': 'Moat Identification',
            'Brand Strength': 'Moat Identification',
            'Customer Dependency': 'Moat Identification',
            'Economic Necessity': 'Value Investing',
            'Market Cap': 'Size Analysis'
        }
        return sources.get(criterion_name, 'Value Investing Analysis')
    
    def _get_criterion_threshold(self, criterion_name: str) -> str:
        """Get the threshold description for each criterion."""
        thresholds = {
            'PE Ratio': '≤ 15 (excellent), ≤ 30 (good)',
            'Price-to-Book': '≤ 1.5 (excellent), ≤ 3.0 (good)',
            'Gross Margin': '≥ 40% (excellent), ≥ 30% (good)',
            'Return on Equity': '≥ 20% (excellent), ≥ 15% (good)',
            'Competitive Moat': 'Multiple moat indicators (excellent)',
            '20-Year Success': 'Strong moat + financial health (excellent)',
            'Business Understanding': 'Clear business model (excellent)',
            'Management Trust': 'Honest, capable leadership (excellent)',
            'Scenario Planning': 'Low risk scenarios (excellent)',
            'Debt Coverage': '≥ 1.0x coverage (excellent), ≥ 0.5x (good)',
            'FCF Growth': '> 0% (excellent)',
            '10X Growth Potential': 'Room to grow + high growth sector (excellent)',
            'Global Potential': 'International expansion opportunity (excellent)',
            'Sales Growth': '≥ 15% (excellent), ≥ 10% (good)',
            'Industry Leadership': 'Market leader position (excellent)',
            'Relative Performance': 'Superior vs competitors (excellent)',
            'Business Model Clarity': 'Clear pricing power + market position (excellent)',
            'Competitive Analysis': 'Market leader + strong brand (excellent)',
            'Risk Assessment': 'Low risk profile (excellent)',
            'Relative Growth': 'Faster than industry (excellent)',
            'Earnings Quality': 'ROE ≥ 20% + low debt + retained earnings (excellent)',
            'Executive Compensation': '≤ $30M or ≤ 5% of FCF (excellent)',
            'Capital Allocation': 'ROE ≥ 20% + good debt management (excellent)',
            'Retained Earnings': 'Positive retained earnings (excellent)',
            'Switching Costs': 'High switching costs (excellent)',
            'Brand Strength': '≥ 8/10 (excellent), ≥ 5/10 (good)',
            'Customer Dependency': 'Strong brand + high switching costs (excellent)',
            'Economic Necessity': 'Essential service + market position (excellent)',
            'Market Cap': '≥ $100M (excellent)'
        }
        return thresholds.get(criterion_name, 'Based on value investing principles')
    
    def _get_current_value(self, criterion_name: str, data: Dict[str, Any]) -> str:
        """Get the current value for display."""
        value_mappings = {
            'PE Ratio': lambda d: f"{d.get('pe_ratio', 0):.1f}" if d.get('pe_ratio') else 'N/A',
            'Price-to-Book': lambda d: f"{d.get('price_to_book', 0):.2f}" if d.get('price_to_book') else 'N/A',
            'Gross Margin': lambda d: f"{d.get('gross_margin', 0):.1f}%" if d.get('gross_margin') else 'N/A',
            'Return on Equity': lambda d: f"{d.get('roe', 0):.1f}%" if d.get('roe') else 'N/A',
            'Sales Growth': lambda d: f"{d.get('sales_growth', 0):.1f}%" if d.get('sales_growth') else 'N/A',
            'FCF Growth': lambda d: f"{d.get('free_cash_flow_growth', 0):.1f}%" if d.get('free_cash_flow_growth') else 'N/A',
            'Market Cap': lambda d: f"${d.get('market_cap', 0):,.0f}" if d.get('market_cap') else 'N/A',
        }
        
        try:
            if criterion_name in value_mappings:
                return value_mappings[criterion_name](data)
            else:
                # Generic mapping based on criterion type
                if 'growth' in criterion_name.lower():
                    return f"{data.get('sales_growth', 0):.1f}%" if data.get('sales_growth') else 'N/A'
                elif 'margin' in criterion_name.lower():
                    return f"{data.get('gross_margin', 0):.1f}%" if data.get('gross_margin') else 'N/A'
                else:
                    return "Based on multiple factors"
        except:
            return 'N/A'