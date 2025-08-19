"""
Integration tests for the Value Investing Stock Finder application.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import pandas as pd
from pathlib import Path

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from analysis.screener import StockScreener
from data_collection.market_data import MarketDataCollector
from analysis.criteria import ValueInvestingCriteria

class TestIntegration(unittest.TestCase):
    """Integration tests for the complete application workflow."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock environment variables
        with patch.dict('os.environ', {
            'FINNHUB_API_KEY': 'test_key',
            'SEC_API_KEY': 'test_key'
        }):
            self.market_data = MarketDataCollector()
            self.screener = StockScreener(self.market_data)
            
    @patch('pandas.read_html')
    def test_complete_workflow(self, mock_read_html):
        """Test the complete workflow from data collection to analysis."""
        # Mock stock universe
        mock_df = pd.DataFrame({
            'Symbol': ['AAPL', 'MSFT'],
            'Security': ['Apple Inc', 'Microsoft Corp']
        })
        mock_read_html.return_value = [mock_df]
        
        # Mock yfinance data for AAPL
        with patch('yfinance.Ticker') as mock_ticker:
            mock_stock = Mock()
            mock_stock.info = {
                'longName': 'Apple Inc',
                'sector': 'Technology',
                'marketCap': 2000000000000,
                'forwardPE': 25.5,
                'priceToBook': 2.5
            }
            
            # Mock financial statements
            mock_financials = pd.DataFrame({
                'Net Income': [1000000000],
                'Total Revenue': [5000000000],
                'Gross Profit': [2500000000]
            }, index=['Net Income', 'Total Revenue', 'Gross Profit'])
            
            mock_balance_sheet = pd.DataFrame({
                'Total Stockholder Equity': [10000000000],
                'Long Term Debt': [500000000]
            }, index=['Total Stockholder Equity', 'Long Term Debt'])
            
            mock_cash_flow = pd.DataFrame({
                'Operating Cash Flow': [2000000000],
                'Capital Expenditure': [-500000000]
            }, index=['Operating Cash Flow', 'Capital Expenditure'])
            
            mock_stock.financials = mock_financials
            mock_stock.balance_sheet = mock_balance_sheet
            mock_stock.cashflow = mock_cash_flow
            
            mock_ticker.return_value = mock_stock
            
            # Mock API clients
            self.market_data.finnhub_client = Mock()
            self.market_data.finnhub_client.company_profile2.return_value = {
                'employeeTotal': 150000,
                'country': 'US'
            }
            self.market_data.finnhub_client.company_news.return_value = []
            
            self.market_data.sec_client = Mock()
            self.market_data.sec_client.get_filings.return_value = {
                'filings': []
            }
            
            # Run the complete analysis
            results = self.screener.run_full_analysis()
            
            # Verify results
            self.assertIsInstance(results, list)
            self.assertGreater(len(results), 0)
            
            # Check that AAPL is in results
            aapl_result = next((r for r in results if r['symbol'] == 'AAPL'), None)
            self.assertIsNotNone(aapl_result)
            
            # Verify key fields
            self.assertEqual(aapl_result['company_name'], 'Apple Inc')
            self.assertEqual(aapl_result['sector'], 'Technology')
            self.assertIn('overall_score', aapl_result)
            self.assertIsInstance(aapl_result['overall_score'], float)
            
    def test_criteria_evaluation_integration(self):
        """Test that criteria evaluation works with real data structure."""
        # Create sample company data
        company_data = {
            'symbol': 'TEST',
            'company_name': 'Test Company',
            'sector': 'Technology',
            'market_cap': 1000000000,
            'pe_ratio': 20,
            'price_to_book': 2.0,
            'gross_margin': 45,
            'roe': 35,
            'fcf_3year_sum': 1000000,
            'long_term_debt': 800000,
            'sales_growth': 15,
            'fcf_growth': 10,
            'retained_earnings': 500000,
            'executive_compensation': 20000000,
            'brand_strength': 8,
            'switching_costs': 7,
            'market_share': 25
        }
        
        # Evaluate against criteria
        criteria = ValueInvestingCriteria()
        results = criteria.evaluate_company(company_data)
        
        # Verify evaluation results
        self.assertIn('overall_score', results)
        self.assertGreater(results['overall_score'], 0)
        
        # Check individual criteria scores
        expected_criteria = [
            'PE Ratio', 'Price-to-Book', 'Gross Margin', 'Return on Equity',
            'Debt Coverage', 'Sales Growth', 'FCF Growth', 'Market Cap',
            'Retained Earnings', 'Executive Compensation', 'Brand Strength',
            'Switching Costs', 'Industry Leadership'
        ]
        
        for criterion in expected_criteria:
            self.assertIn(criterion, results)
            self.assertIsInstance(results[criterion], (int, float))
            
    @patch('pathlib.Path.mkdir')
    def test_report_generation(self, mock_mkdir):
        """Test report generation functionality."""
        # Create sample results
        sample_results = [
            {
                'symbol': 'AAPL',
                'company_name': 'Apple Inc',
                'sector': 'Technology',
                'market_cap': 2000000000000,
                'overall_score': 0.85,
                'PE Ratio': 0.5,
                'Gross Margin': 1.0,
                'Return on Equity': 1.0
            },
            {
                'symbol': 'MSFT',
                'company_name': 'Microsoft Corp',
                'sector': 'Technology',
                'market_cap': 1800000000000,
                'overall_score': 0.75,
                'PE Ratio': 0.5,
                'Gross Margin': 0.5,
                'Return on Equity': 1.0
            }
        ]
        
        # Mock file operations
        with patch('builtins.open', create=True) as mock_open:
            mock_file = Mock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            # Generate report
            self.screener.generate_report(sample_results)
            
            # Verify file operations were called
            mock_open.assert_called()
            mock_file.write.assert_called()
            
    def test_error_handling_integration(self):
        """Test error handling in the complete workflow."""
        # Mock market data to return None for invalid symbols
        with patch.object(self.market_data, 'get_complete_stock_data') as mock_get_data:
            mock_get_data.return_value = None
            
            # Mock stock universe
            with patch.object(self.market_data, 'get_stock_universe') as mock_universe:
                mock_universe.return_value = ['INVALID']
                
                # Run analysis - should handle errors gracefully
                results = self.screener.run_full_analysis()
                
                # Should return empty list when no valid data
                self.assertEqual(results, [])
                
    def test_data_consistency(self):
        """Test that data structure remains consistent throughout the pipeline."""
        # Create test data
        test_data = {
            'symbol': 'TEST',
            'company_name': 'Test Company',
            'sector': 'Technology',
            'market_cap': 1000000000,
            'pe_ratio': 20,
            'gross_margin': 45,
            'roe': 35
        }
        
        # Evaluate with criteria
        criteria = ValueInvestingCriteria()
        evaluation = criteria.evaluate_company(test_data)
        
        # Verify data consistency
        self.assertIn('symbol', evaluation)
        self.assertEqual(evaluation['symbol'], 'TEST')
        
        # Verify all required fields are present
        required_fields = ['overall_score']
        for field in required_fields:
            self.assertIn(field, evaluation)

if __name__ == '__main__':
    unittest.main()
