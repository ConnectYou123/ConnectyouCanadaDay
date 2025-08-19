"""
Handles collection of market data from various sources.
"""

import os
import logging
from typing import Dict, List, Any, Optional
import yfinance as yf
import finnhub
from datetime import datetime, timedelta
import pandas as pd

logger = logging.getLogger(__name__)

class MarketDataCollector:
    def __init__(self, fmp_collector=None):
        """Initialize the data collector with necessary API clients."""
        # Initialize Finnhub client
        self.finnhub_client = finnhub.Client(api_key=os.getenv('FINNHUB_API_KEY'))
        
        # FMP API client for comprehensive financial data
        self.fmp_collector = fmp_collector
        
        # SEC API client (optional)
        self.sec_client = None
        
    def get_stock_universe(self) -> List[str]:
        """Get list of stocks to analyze."""
        try:
            # Get stock symbols from major exchanges
            stock_data = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]
            return stock_data['Symbol'].tolist()
        except Exception as e:
            print(f"Error getting stock universe: {str(e)}")
            return []
            
    def get_complete_stock_data(self, symbol: str, force_live_prices: bool = False) -> Optional[Dict[str, Any]]:
        """Collect all necessary data for a stock using FMP API with optional live price forcing."""
        try:
            # Use FMP API comprehensive data method that we know works perfectly
            if self.fmp_collector:
                print(f"Fetching comprehensive FMP data for {symbol} (live_prices: {force_live_prices})")
                
                # Use the comprehensive method that returns all 51 financial metrics
                data = self.fmp_collector.get_comprehensive_data(symbol)
                
                # If live prices are requested, force refresh the current price
                if force_live_prices and data:
                    print(f"🔄 Force refreshing live price for {symbol}")
                    live_quote = self.fmp_collector.get_current_stock_price(symbol, force_live=True)
                    if live_quote.get('current_price'):
                        data.update({
                            'current_price': live_quote.get('current_price'),
                            'price_change': live_quote.get('change', 0),
                            'price_change_percent': live_quote.get('change_percent', 0),
                            'volume': live_quote.get('volume', 0),
                            'fetch_timestamp': live_quote.get('fetch_timestamp'),
                            'live_data_fetched': True
                        })
                        print(f"✅ Updated {symbol} with live price: ${live_quote.get('current_price')}")
                
                print(f"Successfully got comprehensive FMP data for {symbol}: {len(data)} metrics")
                
                # The data is already comprehensive with all 51 financial metrics, properly formatted
                # Return the comprehensive data directly - no conversion needed as percentages are already correct
                return data
            else:
                # Fallback to yfinance if FMP not available
                stock = yf.Ticker(symbol)
                info = stock.info
                
                data = {
                    'symbol': symbol,
                    'company_name': info.get('longName', ''),
                    'sector': info.get('sector', ''),
                    'market_cap': info.get('marketCap', 0),
                    'pe_ratio': info.get('forwardPE', 0),
                    'price_to_book': info.get('priceToBook', 0),
                    'roe': info.get('returnOnEquity', 0),
                    'gross_margin': info.get('grossMargins', 0) * 100 if info.get('grossMargins') else 0,
                    'net_margin': info.get('profitMargins', 0) * 100 if info.get('profitMargins') else 0,
                    'current_ratio': info.get('currentRatio', 0),
                    'debt_to_equity': info.get('debtToEquity', 0),
                    'revenue': info.get('totalRevenue', 0),
                    'dividend_yield': info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0,
                    'earnings_per_share': info.get('trailingEps', 0),
                    'description': info.get('longBusinessSummary', ''),
                    'industry': info.get('industry', ''),
                    'website': info.get('website', ''),
                }
            
            # Enrich with additional data from Finnhub
            self._enrich_with_finnhub_data(data, symbol)
            
            # Add SEC filing analysis
            self._add_sec_filing_analysis(data, symbol)
            
            return data
            
        except Exception as e:
            print(f"Error collecting data for {symbol}: {str(e)}")
            return None
            
    def _calculate_roe(self, financials: pd.DataFrame, balance_sheet: pd.DataFrame) -> float:
        """Calculate Return on Equity."""
        try:
            net_income = financials.loc['Net Income'].iloc[0]
            equity = balance_sheet.loc["Total Stockholder Equity"].iloc[0]
            return (net_income / equity) * 100 if equity != 0 else 0
        except Exception:
            return 0
            
    def _calculate_gross_margin(self, financials: pd.DataFrame) -> float:
        """Calculate Gross Margin percentage."""
        try:
            revenue = financials.loc['Total Revenue'].iloc[0]
            gross_profit = financials.loc['Gross Profit'].iloc[0]
            return (gross_profit / revenue) * 100 if revenue != 0 else 0
        except Exception:
            return 0
            
    def _calculate_fcf_3year_sum(self, cash_flow: pd.DataFrame) -> float:
        """Calculate sum of Free Cash Flow for past 3 years."""
        try:
            operating_cash = cash_flow.loc['Operating Cash Flow']
            capital_expenditures = cash_flow.loc['Capital Expenditure']
            fcf = operating_cash + capital_expenditures  # Capital expenditures are negative
            return fcf.iloc[:3].sum()
        except Exception:
            return 0
            
    def _calculate_sales_growth(self, financials: pd.DataFrame) -> float:
        """Calculate year-over-year sales growth percentage."""
        try:
            revenue = financials.loc['Total Revenue']
            if len(revenue) >= 2:
                current = revenue.iloc[0]
                previous = revenue.iloc[1]
                return ((current - previous) / previous) * 100 if previous != 0 else 0
            return 0
        except Exception:
            return 0
            
    def _enrich_with_finnhub_data(self, data: Dict[str, Any], symbol: str) -> None:
        """Add additional data from Finnhub API."""
        try:
            # Get company profile
            profile = self.finnhub_client.company_profile2(symbol=symbol)
            if profile:
                data['employee_count'] = profile.get('employeeTotal', 0)
                data['country'] = profile.get('country', '')
                
            # Get company news
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            news = self.finnhub_client.company_news(
                symbol,
                _from=start_date.strftime('%Y-%m-%d'),
                to=end_date.strftime('%Y-%m-%d')
            )
            data['recent_news_count'] = len(news)
            
        except Exception as e:
            print(f"Error enriching data from Finnhub for {symbol}: {str(e)}")
            
    def _add_sec_filing_analysis(self, data: Dict[str, Any], symbol: str) -> None:
        """Add analysis of recent SEC filings."""
        # SEC API integration removed for now
        data['recent_10k_count'] = 0
        data['latest_10k_date'] = None
