#!/usr/bin/env python3
"""
Enhanced reporting system with user-friendly format and explanations.
"""

import pandas as pd
from datetime import datetime
from pathlib import Path
import logging
from typing import List, Dict, Any
import json

logger = logging.getLogger(__name__)

class EnhancedReportGenerator:
    """Generate user-friendly reports with explanations and recommendations."""
    
    def __init__(self):
        self.reports_dir = Path(__file__).parent.parent.parent / 'reports'
        self.reports_dir.mkdir(exist_ok=True)
        
        # Define criteria explanations
        self.criteria_explanations = {
            'overall_score': 'Overall Investment Score (0-1, higher is better)',
            'pe_ratio': 'Price-to-Earnings Ratio (lower is generally better for value)',
            'price_to_book': 'Price-to-Book Ratio (measures if stock is undervalued)',
            'gross_margin': 'Gross Profit Margin % (higher indicates efficiency)',
            'roe': 'Return on Equity % (measures profitability)',
            'debt_coverage': 'Debt Coverage (ability to service debt)',
            'fcf_growth': 'Free Cash Flow Growth (sustainability)',
            'sales_growth': 'Revenue Growth % (business expansion)',
            'market_cap': 'Market Capitalization (company size)',
            'competitive_moat': 'Competitive Advantages (barriers to entry)',
            'margin_of_safety': 'Margin of Safety (downside protection)',
            'management_trust': 'Management Quality (leadership assessment)'
        }
        
        # Investment recommendation thresholds
        self.recommendation_thresholds = {
            'strong_buy': 0.80,
            'buy': 0.70,
            'hold': 0.60,
            'weak_hold': 0.50,
            'avoid': 0.0
        }
    
    def get_investment_recommendation(self, score: float) -> Dict[str, str]:
        """Get investment recommendation based on score."""
        if score >= self.recommendation_thresholds['strong_buy']:
            return {
                'rating': 'STRONG BUY ⭐⭐⭐⭐⭐',
                'color': 'green',
                'explanation': 'Excellent value investment opportunity with strong fundamentals'
            }
        elif score >= self.recommendation_thresholds['buy']:
            return {
                'rating': 'BUY ⭐⭐⭐⭐',
                'color': 'lightgreen', 
                'explanation': 'Good value investment with solid metrics'
            }
        elif score >= self.recommendation_thresholds['hold']:
            return {
                'rating': 'HOLD ⭐⭐⭐',
                'color': 'yellow',
                'explanation': 'Decent investment but monitor closely'
            }
        elif score >= self.recommendation_thresholds['weak_hold']:
            return {
                'rating': 'WEAK HOLD ⭐⭐',
                'color': 'orange',
                'explanation': 'Below average metrics, consider other options'
            }
        else:
            return {
                'rating': 'AVOID ⭐',
                'color': 'red',
                'explanation': 'Poor value investment characteristics'
            }
    
    def get_key_strengths(self, analysis: Dict[str, Any]) -> List[str]:
        """Identify key strengths of the investment."""
        strengths = []
        
        # High overall score
        if analysis.get('overall_score', 0) >= 0.75:
            strengths.append("🏆 High overall investment score")
            
        # Good valuation metrics
        if analysis.get('pe_ratio', 100) <= 15:
            strengths.append("💰 Attractive P/E ratio (undervalued)")
            
        if analysis.get('price_to_book', 10) <= 1.5:
            strengths.append("📈 Low price-to-book ratio (good value)")
            
        # Strong profitability
        if analysis.get('gross_margin', 0) >= 40:
            strengths.append("💼 Strong profit margins")
            
        if analysis.get('roe', 0) >= 15:
            strengths.append("🎯 High return on equity")
            
        # Financial health
        if analysis.get('debt_coverage', 0) >= 0.8:
            strengths.append("🛡️ Strong debt coverage")
            
        # Growth potential
        if analysis.get('sales_growth', 0) >= 10:
            strengths.append("🚀 Strong revenue growth")
            
        # Competitive advantages
        if analysis.get('competitive_moat', 0) >= 0.7:
            strengths.append("🏰 Strong competitive moat")
            
        # Safety margin
        if analysis.get('margin_of_safety', 0) >= 0.8:
            strengths.append("🛡️ Good margin of safety")
            
        return strengths[:5]  # Top 5 strengths
    
    def get_key_concerns(self, analysis: Dict[str, Any]) -> List[str]:
        """Identify key concerns about the investment."""
        concerns = []
        
        # Poor overall score
        if analysis.get('overall_score', 1) <= 0.5:
            concerns.append("⚠️ Low overall investment score")
            
        # Valuation concerns
        if analysis.get('pe_ratio', 0) >= 30:
            concerns.append("💸 High P/E ratio (potentially overvalued)")
            
        if analysis.get('price_to_book', 0) >= 3:
            concerns.append("📉 High price-to-book ratio")
            
        # Profitability issues
        if analysis.get('gross_margin', 100) <= 20:
            concerns.append("🔻 Low profit margins")
            
        if analysis.get('roe', 100) <= 10:
            concerns.append("📊 Low return on equity")
            
        # Financial health
        if analysis.get('debt_coverage', 1) <= 0.5:
            concerns.append("⚠️ Poor debt coverage")
            
        # Growth issues
        if analysis.get('sales_growth', 100) <= 5:
            concerns.append("📉 Slow revenue growth")
            
        # Competitive position
        if analysis.get('competitive_moat', 1) <= 0.4:
            concerns.append("🏚️ Weak competitive position")
            
        return concerns[:5]  # Top 5 concerns
    
    def generate_readable_report(self, results: List[Dict[str, Any]], filename_suffix: str = None) -> str:
        """Generate a user-friendly, readable report."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"investment_analysis_{timestamp}"
        if filename_suffix:
            filename += f"_{filename_suffix}"
        filename += ".html"
        
        filepath = self.reports_dir / filename
        
        # Sort by overall score (best first)
        sorted_results = sorted(results, key=lambda x: x.get('overall_score', 0), reverse=True)
        
        # Generate HTML report
        html_content = self._generate_html_report(sorted_results, timestamp)
        
        # Save HTML report
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        logger.info(f"Beautiful HTML investment report generated: {filepath}")
        return str(filepath)
    
    def _generate_html_report(self, results: List[Dict[str, Any]], timestamp: str) -> str:
        """Generate beautiful HTML report."""
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Investment Analysis Report - {timestamp}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .investment-card {{ border-left: 5px solid #007bff; margin-bottom: 20px; }}
        .strong-buy {{ border-left-color: #28a745 !important; }}
        .buy {{ border-left-color: #6f42c1 !important; }}
        .hold {{ border-left-color: #ffc107 !important; }}
        .weak-hold {{ border-left-color: #fd7e14 !important; }}
        .avoid {{ border-left-color: #dc3545 !important; }}
        .score-badge {{ font-size: 1.2em; font-weight: bold; }}
        .strength {{ color: #28a745; }}
        .concern {{ color: #dc3545; }}
        .metric-good {{ background-color: #d4edda; }}
        .metric-average {{ background-color: #fff3cd; }}
        .metric-poor {{ background-color: #f8d7da; }}
    </style>
</head>
<body class="bg-light">
    <div class="container my-5">
        <div class="row">
            <div class="col-12">
                <h1 class="text-center mb-4">
                    <i class="fas fa-chart-line text-primary me-2"></i>
                    Investment Analysis Report
                </h1>
                <p class="text-center text-muted">Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
                <hr>
            </div>
        </div>
        
        <div class="row mb-4">
            <div class="col-md-8 mx-auto">
                <div class="alert alert-info">
                    <h5><i class="fas fa-info-circle me-2"></i>How to Read This Report</h5>
                    <ul class="mb-0">
                        <li><strong>Overall Score:</strong> 0-1 scale where 1.0 is perfect (0.80+ = Strong Buy, 0.70+ = Buy, 0.60+ = Hold)</li>
                        <li><strong>Strengths:</strong> Key positive factors that make this a good investment</li>
                        <li><strong>Concerns:</strong> Areas of weakness or risk to monitor</li>
                        <li><strong>Financial Metrics:</strong> Color-coded performance indicators</li>
                    </ul>
                </div>
            </div>
        </div>
"""
        
        # Add summary statistics
        if results:
            avg_score = sum(r.get('overall_score', 0) for r in results) / len(results)
            strong_buys = len([r for r in results if r.get('overall_score', 0) >= 0.80])
            buys = len([r for r in results if 0.70 <= r.get('overall_score', 0) < 0.80])
            
            html += f"""
        <div class="row mb-4">
            <div class="col-md-12">
                <div class="card">
                    <div class="card-header bg-primary text-white">
                        <h5><i class="fas fa-chart-bar me-2"></i>Analysis Summary</h5>
                    </div>
                    <div class="card-body">
                        <div class="row text-center">
                            <div class="col-md-3">
                                <h4 class="text-primary">{len(results)}</h4>
                                <p class="text-muted">Companies Analyzed</p>
                            </div>
                            <div class="col-md-3">
                                <h4 class="text-success">{strong_buys}</h4>
                                <p class="text-muted">Strong Buy Recommendations</p>
                            </div>
                            <div class="col-md-3">
                                <h4 class="text-info">{buys}</h4>
                                <p class="text-muted">Buy Recommendations</p>
                            </div>
                            <div class="col-md-3">
                                <h4 class="text-warning">{avg_score:.2f}</h4>
                                <p class="text-muted">Average Score</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
"""
        
        # Add individual company analysis
        html += '<div class="row">'
        
        for i, company in enumerate(results[:20]):  # Limit to top 20
            recommendation = self.get_investment_recommendation(company.get('overall_score', 0))
            strengths = self.get_key_strengths(company)
            concerns = self.get_key_concerns(company)
            
            rating_class = recommendation['rating'].split()[0].lower().replace(' ', '_')
            
            html += f"""
            <div class="col-lg-6 mb-4">
                <div class="card investment-card {rating_class}">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <div>
                            <h5 class="mb-0">{company.get('symbol', 'N/A')} - {company.get('company_name', 'Unknown Company')}</h5>
                            <small class="text-muted">{company.get('sector', 'Unknown Sector')}</small>
                        </div>
                        <span class="score-badge badge bg-primary">{company.get('overall_score', 0):.2f}</span>
                    </div>
                    <div class="card-body">
                        <div class="mb-3">
                            <h6 class="fw-bold">{recommendation['rating']}</h6>
                            <p class="text-muted small mb-0">{recommendation['explanation']}</p>
                        </div>
                        
                        <div class="row mb-3">
                            <div class="col-6">
                                <small class="text-muted">Market Cap</small>
                                <div class="fw-bold">${company.get('market_cap', 0):,.0f}</div>
                            </div>
                            <div class="col-6">
                                <small class="text-muted">P/E Ratio</small>
                                <div class="fw-bold">{company.get('pe_ratio', 'N/A')}</div>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <h6 class="text-success"><i class="fas fa-thumbs-up me-1"></i>Key Strengths</h6>
                            <ul class="list-unstyled">
                                {"".join(f"<li class='strength small'>{strength}</li>" for strength in strengths[:3])}
                            </ul>
                        </div>
                        
                        {"<div class='mb-3'><h6 class='text-danger'><i class='fas fa-exclamation-triangle me-1'></i>Key Concerns</h6><ul class='list-unstyled'>" + "".join(f"<li class='concern small'>{concern}</li>" for concern in concerns[:3]) + "</ul></div>" if concerns else ""}
                        
                        <div class="mt-3">
                            <button class="btn btn-outline-primary btn-sm" onclick="toggleDetails('{company.get('symbol', i)}')">
                                <i class="fas fa-chart-line me-1"></i>View Detailed Metrics
                            </button>
                        </div>
                        
                        <div id="details-{company.get('symbol', i)}" class="mt-3" style="display: none;">
                            <div class="table-responsive">
                                <table class="table table-sm">
                                    <tr><td>Gross Margin</td><td>{company.get('gross_margin', 'N/A')}%</td></tr>
                                    <tr><td>Return on Equity</td><td>{company.get('roe', 'N/A')}%</td></tr>
                                    <tr><td>Debt Coverage</td><td>{company.get('debt_coverage', 'N/A')}</td></tr>
                                    <tr><td>Sales Growth</td><td>{company.get('sales_growth', 'N/A')}%</td></tr>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
"""
        
        html += """
        </div>
        
        <div class="row mt-5">
            <div class="col-12">
                <div class="alert alert-secondary">
                    <h6><i class="fas fa-lightbulb me-2"></i>Investment Tips</h6>
                    <ul class="mb-0">
                        <li><strong>Diversify:</strong> Don't put all your money in one stock, even highly rated ones</li>
                        <li><strong>Research Further:</strong> This analysis is a starting point - do additional research</li>
                        <li><strong>Monitor:</strong> Keep tracking these companies as conditions change</li>
                        <li><strong>Risk Tolerance:</strong> Consider your personal risk tolerance and investment timeline</li>
                    </ul>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        function toggleDetails(symbol) {
            const details = document.getElementById('details-' + symbol);
            if (details.style.display === 'none') {
                details.style.display = 'block';
            } else {
                details.style.display = 'none';
            }
        }
    </script>
</body>
</html>
"""
        return html
    
    def _generate_simplified_csv(self, results: List[Dict[str, Any]], timestamp: str, suffix: str = None) -> str:
        """Generate a simplified, readable CSV."""
        filename = f"investment_summary_{timestamp}"
        if suffix:
            filename += f"_{suffix}"
        filename += ".csv"
        
        filepath = self.reports_dir / filename
        
        # Create simplified data structure
        simplified_data = []
        for company in results:
            recommendation = self.get_investment_recommendation(company.get('overall_score', 0))
            strengths = self.get_key_strengths(company)
            concerns = self.get_key_concerns(company)
            
            simplified_data.append({
                'Rank': len(simplified_data) + 1,
                'Symbol': company.get('symbol', 'N/A'),
                'Company Name': company.get('company_name', 'Unknown'),
                'Sector': company.get('sector', 'Unknown'),
                'Overall Score': f"{company.get('overall_score', 0):.2f}",
                'Investment Rating': recommendation['rating'],
                'Explanation': recommendation['explanation'],
                'Market Cap ($)': f"{company.get('market_cap', 0):,.0f}",
                'P/E Ratio': company.get('pe_ratio', 'N/A'),
                'Gross Margin (%)': f"{company.get('gross_margin', 0):.1f}",
                'ROE (%)': f"{company.get('roe', 0):.1f}",
                'Sales Growth (%)': f"{company.get('sales_growth', 0):.1f}",
                'Key Strengths': ' | '.join(strengths[:3]),
                'Key Concerns': ' | '.join(concerns[:3]),
                'Analysis Date': company.get('analysis_date', timestamp)
            })
        
        # Save to CSV
        df = pd.DataFrame(simplified_data)
        df.to_csv(filepath, index=False)
        
        return str(filepath)

# Global instance
enhanced_reporter = EnhancedReportGenerator()

def generate_enhanced_report(results: List[Dict[str, Any]], suffix: str = None) -> str:
    """Generate enhanced report with explanations."""
    return enhanced_reporter.generate_readable_report(results, suffix)
