"""
Unit tests for the market data collection module.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import pandas as pd

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from data_collection.market_data import MarketDataCollector

class TestMarketDataCollector(unittest.TestCase):
    """Test cases for MarketDataCollector class."""
    
    def setUp(self):
        """Set up test fixtures."""
        with patch.dict('os.environ', {'FINNHUB_API_KEY': 'test_key', 'SEC_API_KEY': 'test_key'}):
            self.collector = MarketDataCollector()
            
    @patch('pandas.read_html')
    def test_get_stock_universe(self, mock_read_html):
        """Test getting stock universe from S&P 500."""
        # Mock the pandas read_html response
        mock_df = pd.DataFrame({
            'Symbol': ['AAPL', 'MSFT', 'GOOGL'],
            'Security': ['Apple Inc', 'Microsoft Corp', 'Alphabet Inc']
        })
        mock_read_html.return_value = [mock_df]
        
        result = self.collector.get_stock_universe()
        
        self.assertIsInstance(result, list)
        self.assertEqual(result, ['AAPL', 'MSFT', 'GOOGL'])
        
    @patch('yfinance.Ticker')
    def test_get_complete_stock_data_success(self, mock_ticker):
        """Test successful data collection for a stock."""
        # Mock yfinance Ticker
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
            'Total Stockholder Equity': [10000000000]
        }, index=['Total Stockholder Equity'])
        
        mock_cash_flow = pd.DataFrame({
            'Operating Cash Flow': [2000000000],
            'Capital Expenditure': [-500000000]
        }, index=['Operating Cash Flow', 'Capital Expenditure'])
        
        mock_stock.financials = mock_financials
        mock_stock.balance_sheet = mock_balance_sheet
        mock_stock.cashflow = mock_cash_flow
        
        mock_ticker.return_value = mock_stock
        
        # Mock Finnhub client
        self.collector.finnhub_client = Mock()
        self.collector.finnhub_client.company_profile2.return_value = {
            'employeeTotal': 150000,
            'country': 'US'
        }
        self.collector.finnhub_client.company_news.return_value = [
            {'headline': 'Test news 1'},
            {'headline': 'Test news 2'}
        ]
        
        # Mock SEC client
        self.collector.sec_client = Mock()
        self.collector.sec_client.get_filings.return_value = {
            'filings': [
                {'filedAt': '2023-01-01', 'formType': '10-K'}
            ]
        }
        
        result = self.collector.get_complete_stock_data('AAPL')
        
        self.assertIsNotNone(result)
        self.assertEqual(result['symbol'], 'AAPL')
        self.assertEqual(result['company_name'], 'Apple Inc')
        self.assertEqual(result['sector'], 'Technology')
        self.assertEqual(result['market_cap'], 2000000000000)
        
    @patch('yfinance.Ticker')
    def test_get_complete_stock_data_failure(self, mock_ticker):
        """Test data collection failure handling."""
        mock_ticker.side_effect = Exception("API Error")
        
        result = self.collector.get_complete_stock_data('INVALID')
        
        self.assertIsNone(result)
        
    def test_calculate_roe(self):
        """Test ROE calculation."""
        financials = pd.DataFrame({
            'Net Income': [1000000000]
        }, index=['Net Income'])
        
        balance_sheet = pd.DataFrame({
            'Total Stockholder Equity': [10000000000]
        }, index=['Total Stockholder Equity'])
        
        result = self.collector._calculate_roe(financials, balance_sheet)
        
        # Expected: (1000000000 / 10000000000) * 100 = 10%
        self.assertEqual(result, 10.0)
        
    def test_calculate_gross_margin(self):
        """Test gross margin calculation."""
        financials = pd.DataFrame({
            'Total Revenue': [5000000000],
            'Gross Profit': [2500000000]
        }, index=['Total Revenue', 'Gross Profit'])
        
        result = self.collector._calculate_gross_margin(financials)
        
        # Expected: (2500000000 / 5000000000) * 100 = 50%
        self.assertEqual(result, 50.0)
        
    def test_calculate_sales_growth(self):
        """Test sales growth calculation."""
        financials = pd.DataFrame({
            'Total Revenue': [1100000000, 1000000000]  # 10% growth
        }, index=['Total Revenue'])
        
        result = self.collector._calculate_sales_growth(financials)
        
        # Expected: ((1100000000 - 1000000000) / 1000000000) * 100 = 10%
        self.assertEqual(result, 10.0)
        
    def test_calculate_fcf_3year_sum(self):
        """Test FCF 3-year sum calculation."""
        cash_flow = pd.DataFrame({
            'Operating Cash Flow': [2000000000, 1800000000, 1600000000],
            'Capital Expenditure': [-500000000, -450000000, -400000000]
        }, index=['Operating Cash Flow', 'Capital Expenditure'])
        
        result = self.collector._calculate_fcf_3year_sum(cash_flow)
        
        # Expected: (2000000000-500000000) + (1800000000-450000000) + (1600000000-400000000)
        # = 1500000000 + 1350000000 + 1200000000 = 4050000000
        self.assertEqual(result, 4050000000)

if __name__ == '__main__':
    unittest.main()
