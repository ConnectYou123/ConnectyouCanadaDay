"""
Stock screener that applies value investing criteria to find potential investments.
"""

from typing import Dict, List, Any
import pandas as pd
from datetime import datetime
from pathlib import Path
from .criteria import ValueInvestingCriteria

class StockScreener:
    def __init__(self, market_data_collector):
        """Initialize the stock screener with data collector and criteria."""
        self.market_data = market_data_collector
        self.criteria = ValueInvestingCriteria()
        
    def run_full_analysis(self) -> List[Dict[str, Any]]:
        """Run a full analysis on all available stocks."""
        # Get list of stocks to analyze
        stocks = self.market_data.get_stock_universe()
        results = []
        
        for stock in stocks:
            try:
                # Collect all necessary data for the stock
                stock_data = self.market_data.get_complete_stock_data(stock)
                
                # Skip if we couldn't get the necessary data
                if not stock_data:
                    continue
                
                # Evaluate against all criteria
                evaluation = self.criteria.evaluate_company(stock_data)
                
                # Add ALL financial data to results (preserve FMP API data)
                evaluation.update(stock_data)  # Include all the rich FMP financial data
                evaluation.update({
                    'analysis_date': datetime.now().isoformat()
                })
                
                results.append(evaluation)
                
            except Exception as e:
                print(f"Error analyzing {stock}: {str(e)}")
                continue
                
        return results
    
    def generate_report(self, results: List[Dict[str, Any]]) -> None:
        """Generate a detailed report from the analysis results."""
        if not results:
            print("No results to generate report from.")
            return
        
        # Create reports directory if it doesn't exist
        reports_dir = Path('reports')
        reports_dir.mkdir(exist_ok=True)
        
        # Generate ONLY beautiful HTML reports (absolutely no CSV files)
        from utils.enhanced_reports import generate_enhanced_report
        
        # Determine search suffix for filename
        search_suffix = None
        if hasattr(self, '_current_search_terms') and self._current_search_terms:
            search_suffix = "_".join(self._current_search_terms)
        
        # Generate enhanced HTML report with explanations
        enhanced_report_path = generate_enhanced_report(results, search_suffix)
        print(f"📊 Beautiful Investment Analysis Report: {enhanced_report_path}")
        print(f"🌐 Open this report in your browser to see the beautiful visual analysis!")
        
        # No CSV files generated - only beautiful HTML reports
