"""
Configuration management for the Value Investing Stock Finder application.
"""

import os
from typing import Dict, Any
from dataclasses import dataclass
from pathlib import Path

@dataclass
class APIConfig:
    """API configuration settings."""
    fmp_api_key: str           # Financial Modeling Prep - Primary API
    finnhub_api_key: str       # Finnhub - Backup API
    sec_api_key: str           # SEC API - Optional
    
@dataclass
class ScreeningConfig:
    """Screening parameters configuration."""
    min_market_cap: float
    max_pe_ratio: float
    min_roe: float
    min_gross_margin: float
    min_sales_growth: float
    max_price_to_book: float
    
@dataclass
class CacheConfig:
    """Cache configuration settings."""
    cache_duration: int
    cache_dir: Path
    max_concurrent_requests: int

class Config:
    """Main configuration class."""
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        self.api = APIConfig(
            fmp_api_key=os.getenv('FMP_API_KEY', '7a3e0f062a0c0ac69223d7d7570ac5c1'),
            finnhub_api_key=os.getenv('FINNHUB_API_KEY', 'demo'),
            sec_api_key=os.getenv('SEC_API_KEY', '')
        )
        
        self.screening = ScreeningConfig(
            min_market_cap=float(os.getenv('MIN_MARKET_CAP', 100000000)),  # $100M
            max_pe_ratio=float(os.getenv('MAX_PE_RATIO', 30)),
            min_roe=float(os.getenv('MIN_ROE', 30)),
            min_gross_margin=float(os.getenv('MIN_GROSS_MARGIN', 40)),
            min_sales_growth=float(os.getenv('MIN_SALES_GROWTH', 15)),
            max_price_to_book=float(os.getenv('MAX_PRICE_TO_BOOK', 3))
        )
        
        self.cache = CacheConfig(
            cache_duration=int(os.getenv('CACHE_DURATION', 3600)),  # 1 hour
            cache_dir=Path(os.getenv('DATA_CACHE_DIR', './cache')),
            max_concurrent_requests=int(os.getenv('MAX_CONCURRENT_REQUESTS', 5))
        )
        
        # Create cache directory if it doesn't exist
        self.cache.cache_dir.mkdir(exist_ok=True)
        
    def validate(self) -> bool:
        """Validate configuration settings."""
        errors = []
        
        if not self.api.fmp_api_key:
            errors.append("FMP_API_KEY is required for comprehensive financial data")
            
        # Finnhub API key is optional for now - can use demo key
        # if not self.api.finnhub_api_key:
        #     errors.append("FINNHUB_API_KEY is required as backup")
            
        # SEC API key is optional now
        # if not self.api.sec_api_key:
        #     errors.append("SEC_API_KEY is required")
            
        if self.screening.min_market_cap <= 0:
            errors.append("MIN_MARKET_CAP must be positive")
            
        if self.screening.max_pe_ratio <= 0:
            errors.append("MAX_PE_RATIO must be positive")
            
        if self.cache.cache_duration <= 0:
            errors.append("CACHE_DURATION must be positive")
            
        if errors:
            print("Configuration errors:")
            for error in errors:
                print(f"  - {error}")
            return False
            
        return True
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'api': {
                'fmp_api_key': self.api.fmp_api_key[:10] + '...' if self.api.fmp_api_key else '',
                'finnhub_api_key': self.api.finnhub_api_key[:10] + '...' if self.api.finnhub_api_key else '',
                'sec_api_key': self.api.sec_api_key[:10] + '...' if self.api.sec_api_key else ''
            },
            'screening': {
                'min_market_cap': self.screening.min_market_cap,
                'max_pe_ratio': self.screening.max_pe_ratio,
                'min_roe': self.screening.min_roe,
                'min_gross_margin': self.screening.min_gross_margin,
                'min_sales_growth': self.screening.min_sales_growth,
                'max_price_to_book': self.screening.max_price_to_book
            },
            'cache': {
                'cache_duration': self.cache.cache_duration,
                'cache_dir': str(self.cache.cache_dir),
                'max_concurrent_requests': self.cache.max_concurrent_requests
            }
        }
