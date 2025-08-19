"""
Helper utilities for the stock finder application.
"""

import logging
import os
from pathlib import Path
from typing import Dict, Any
import json
from datetime import datetime

def setup_logging() -> logging.Logger:
    """Set up logging configuration."""
    # Create logs directory if it doesn't exist
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    # Create log file with timestamp
    log_file = log_dir / f"stock_finder_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

def initialize_config() -> Dict[str, Any]:
    """Initialize configuration from environment variables."""
    config = {
        'max_concurrent_requests': int(os.getenv('MAX_CONCURRENT_REQUESTS', 5)),
        'cache_duration': int(os.getenv('CACHE_DURATION', 3600)),
        'data_cache_dir': os.getenv('DATA_CACHE_DIR', './cache'),
        'screening_params': {
            'min_market_cap': float(os.getenv('MIN_MARKET_CAP', 100000000)),
            'max_pe_ratio': float(os.getenv('MAX_PE_RATIO', 30)),
            'min_roe': float(os.getenv('MIN_ROE', 30)),
            'min_gross_margin': float(os.getenv('MIN_GROSS_MARGIN', 40)),
            'min_sales_growth': float(os.getenv('MIN_SALES_GROWTH', 15))
        }
    }
    
    # Create cache directory if it doesn't exist
    cache_dir = Path(config['data_cache_dir'])
    cache_dir.mkdir(exist_ok=True)
    
    return config

def cache_data(key: str, data: Any, cache_dir: str = './cache') -> None:
    """Cache data to file system."""
    cache_path = Path(cache_dir) / f"{key}.json"
    with open(cache_path, 'w') as f:
        json.dump({
            'timestamp': datetime.now().timestamp(),
            'data': data
        }, f)

def get_cached_data(key: str, cache_duration: int, cache_dir: str = './cache') -> Any:
    """Retrieve cached data if not expired."""
    cache_path = Path(cache_dir) / f"{key}.json"
    
    if not cache_path.exists():
        return None
        
    try:
        with open(cache_path, 'r') as f:
            cached = json.load(f)
            
        # Check if cache is expired
        if datetime.now().timestamp() - cached['timestamp'] > cache_duration:
            return None
            
        return cached['data']
        
    except Exception:
        return None

def format_currency(value: float) -> str:
    """Format number as currency string."""
    if value >= 1_000_000_000:
        return f"${value/1_000_000_000:.1f}B"
    elif value >= 1_000_000:
        return f"${value/1_000_000:.1f}M"
    elif value >= 1_000:
        return f"${value/1_000:.1f}K"
    else:
        return f"${value:.2f}"

def format_percentage(value: float) -> str:
    """Format number as percentage string."""
    return f"{value:.1f}%"
