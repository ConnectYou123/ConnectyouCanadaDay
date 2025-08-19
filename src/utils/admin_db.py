#!/usr/bin/env python3
"""
Admin panel database for tracking API usage and user activity.
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timedelta
from pathlib import Path
import logging
import json
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Database setup
BASE_DIR = Path(__file__).parent.parent.parent
DB_PATH = BASE_DIR / 'admin.db'
Base = declarative_base()

class APIUsage(Base):
    """Track API usage statistics."""
    __tablename__ = 'api_usage'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now)
    api_provider = Column(String(50))  # 'FMP', 'Finnhub', 'Alpha Vantage'
    endpoint = Column(String(200))     # Which endpoint was called
    symbol = Column(String(20))        # Stock symbol if applicable
    status_code = Column(Integer)      # HTTP status code
    response_time = Column(Float)      # Response time in seconds
    user_ip = Column(String(45))       # User IP address
    user_agent = Column(Text)          # User agent string
    request_data = Column(Text)        # JSON of request parameters
    success = Column(Boolean)          # Whether request was successful

class UserActivity(Base):
    """Track user activity and searches."""
    __tablename__ = 'user_activity'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now)
    user_ip = Column(String(45))
    user_agent = Column(Text)
    session_id = Column(String(100))   # Browser session ID
    action = Column(String(50))        # 'search', 'analysis', 'document_upload', 'page_view'
    page_url = Column(String(500))     # Which page/endpoint
    search_terms = Column(Text)        # What they searched for
    company_analyzed = Column(String(50))  # Which company was analyzed
    document_type = Column(String(20)) # PDF, DOCX, TXT for uploads
    duration_seconds = Column(Float)   # Time spent on action
    extra_data = Column(Text)           # Additional JSON metadata

class SystemStats(Base):
    """Track system-wide statistics."""
    __tablename__ = 'system_stats'
    
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, default=datetime.now)
    total_api_calls = Column(Integer, default=0)
    successful_calls = Column(Integer, default=0)
    failed_calls = Column(Integer, default=0)
    unique_visitors = Column(Integer, default=0)
    total_searches = Column(Integer, default=0)
    total_analyses = Column(Integer, default=0)
    total_document_uploads = Column(Integer, default=0)
    avg_response_time = Column(Float, default=0.0)
    top_searched_stocks = Column(Text)  # JSON of top 10 searched stocks

class CachedFinancialData(Base):
    """Cache financial data to reduce API calls."""
    __tablename__ = 'cached_financial_data'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(10), unique=True, index=True)  # Stock symbol (AAPL, MSFT, etc.)
    company_name = Column(String(200))
    sector = Column(String(100))
    industry = Column(String(100))
    market_cap = Column(Float)
    
    # Valuation Metrics
    pe_ratio = Column(Float)
    price_to_book = Column(Float) 
    price_to_sales = Column(Float)
    ev_to_ebitda = Column(Float)
    
    # Profitability Metrics
    gross_margin = Column(Float)
    operating_margin = Column(Float)
    net_margin = Column(Float)
    roe = Column(Float)  # Return on Equity
    roa = Column(Float)  # Return on Assets
    roic = Column(Float) # Return on Invested Capital
    
    # Financial Health
    current_ratio = Column(Float)
    debt_to_equity = Column(Float)
    debt_to_assets = Column(Float)
    interest_coverage = Column(Float)
    
    # Growth Metrics
    revenue_growth = Column(Float)
    earnings_growth = Column(Float)
    fcf_growth = Column(Float)
    
    # Additional Financial Data (stored as JSON for flexibility)
    additional_metrics = Column(Text)  # JSON string for other metrics
    
    # Metadata
    data_source = Column(String(50), default='FMP')  # FMP, Yahoo, Manual, etc.
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    is_active = Column(Boolean, default=True)
    api_calls_saved = Column(Integer, default=0)  # Track how many API calls this cache entry saved

# Database connection and session management
engine = create_engine(f'sqlite:///{DB_PATH}', echo=False, 
                      connect_args={'check_same_thread': False, 'timeout': 20})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_admin_db():
    """Initialize the admin database."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info(f"Admin database initialized at {DB_PATH}")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize admin database: {e}")
        return False

def get_admin_session() -> Session:
    """Get a database session."""
    return SessionLocal()

class AdminTracker:
    """Main class for tracking admin metrics."""
    
    def __init__(self):
        # Don't keep a persistent session - create new ones as needed
        pass
    
    def _get_session(self):
        """Get a fresh database session for each operation."""
        return get_admin_session()
    
    def track_api_usage(self, 
                       api_provider: str,
                       endpoint: str,
                       symbol: str = None,
                       status_code: int = 200,
                       response_time: float = 0.0,
                       user_ip: str = None,
                       user_agent: str = None,
                       request_data: Dict = None,
                       success: bool = True):
        """Track an API call."""
        session = self._get_session()
        try:
            usage = APIUsage(
                api_provider=api_provider,
                endpoint=endpoint,
                symbol=symbol,
                status_code=status_code,
                response_time=response_time,
                user_ip=user_ip,
                user_agent=user_agent,
                request_data=json.dumps(request_data) if request_data else None,
                success=success
            )
            session.add(usage)
            session.commit()
            logger.info(f"Tracked API usage: {api_provider} - {endpoint} - {symbol}")
        except Exception as e:
            logger.error(f"Failed to track API usage: {e}")
            session.rollback()
        finally:
            session.close()
    
    def track_user_activity(self,
                           user_ip: str,
                           action: str,
                           page_url: str = None,
                           search_terms: str = None,
                           company_analyzed: str = None,
                           document_type: str = None,
                           user_agent: str = None,
                           session_id: str = None,
                           duration_seconds: float = 0.0,
                           extra_data: Dict = None):
        """Track user activity."""
        try:
            activity = UserActivity(
                user_ip=user_ip,
                user_agent=user_agent,
                session_id=session_id,
                action=action,
                page_url=page_url,
                search_terms=search_terms,
                company_analyzed=company_analyzed,
                document_type=document_type,
                duration_seconds=duration_seconds,
                extra_data=json.dumps(extra_data) if extra_data else None
            )
            self.session.add(activity)
            self.session.commit()
            logger.info(f"Tracked user activity: {action} - {search_terms or company_analyzed}")
        except Exception as e:
            logger.error(f"Failed to track user activity: {e}")
            self.session.rollback()
    
    def get_api_usage_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get API usage statistics for the last N days."""
        try:
            from sqlalchemy import func
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Total calls by provider
            provider_stats = self.session.query(
                APIUsage.api_provider,
                func.count(APIUsage.id).label('total_calls'),
                func.count(func.nullif(APIUsage.success, False)).label('successful_calls'),
                func.avg(APIUsage.response_time).label('avg_response_time')
            ).filter(APIUsage.timestamp >= cutoff_date)\
             .group_by(APIUsage.api_provider)\
             .all()
            
            # Most searched symbols
            symbol_stats = self.session.query(
                APIUsage.symbol,
                func.count(APIUsage.id).label('search_count')
            ).filter(APIUsage.timestamp >= cutoff_date, APIUsage.symbol.isnot(None))\
             .group_by(APIUsage.symbol)\
             .order_by(func.count(APIUsage.id).desc())\
             .limit(10)\
             .all()
            
            return {
                'period_days': days,
                'provider_stats': [
                    {
                        'provider': stat.api_provider,
                        'total_calls': stat.total_calls,
                        'successful_calls': stat.successful_calls,
                        'success_rate': round((stat.successful_calls / stat.total_calls) * 100, 2),
                        'avg_response_time': round(stat.avg_response_time or 0, 3)
                    } for stat in provider_stats
                ],
                'top_symbols': [
                    {'symbol': stat.symbol, 'count': stat.search_count}
                    for stat in symbol_stats
                ]
            }
        except Exception as e:
            logger.error(f"Failed to get API usage stats: {e}")
            return {}
    
    def get_user_activity_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get user activity statistics."""
        try:
            from sqlalchemy import func
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Activity by type
            activity_stats = self.session.query(
                UserActivity.action,
                func.count(UserActivity.id).label('count')
            ).filter(UserActivity.timestamp >= cutoff_date)\
             .group_by(UserActivity.action)\
             .all()
            
            # Unique visitors
            unique_visitors = self.session.query(
                func.count(func.distinct(UserActivity.user_ip))
            ).filter(UserActivity.timestamp >= cutoff_date).scalar()
            
            # Top searches
            top_searches = self.session.query(
                UserActivity.search_terms,
                func.count(UserActivity.id).label('count')
            ).filter(
                UserActivity.timestamp >= cutoff_date,
                UserActivity.search_terms.isnot(None),
                UserActivity.search_terms != ''
            ).group_by(UserActivity.search_terms)\
             .order_by(func.count(UserActivity.id).desc())\
             .limit(10)\
             .all()
            
            # Top analyzed companies
            top_companies = self.session.query(
                UserActivity.company_analyzed,
                func.count(UserActivity.id).label('count')
            ).filter(
                UserActivity.timestamp >= cutoff_date,
                UserActivity.company_analyzed.isnot(None)
            ).group_by(UserActivity.company_analyzed)\
             .order_by(func.count(UserActivity.id).desc())\
             .limit(10)\
             .all()
            
            return {
                'period_days': days,
                'unique_visitors': unique_visitors,
                'activity_breakdown': [
                    {'action': stat.action, 'count': stat.count}
                    for stat in activity_stats
                ],
                'top_searches': [
                    {'search': stat.search_terms, 'count': stat.count}
                    for stat in top_searches
                ],
                'top_companies': [
                    {'company': stat.company_analyzed, 'count': stat.count}
                    for stat in top_companies
                ]
            }
        except Exception as e:
            logger.error(f"Failed to get user activity stats: {e}")
            return {}
    
    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get a summary for the admin dashboard."""
        try:
            from sqlalchemy import func
            from datetime import timedelta
            
            today = datetime.now().date()
            yesterday = today - timedelta(days=1)
            week_ago = today - timedelta(days=7)
            
            # Today's stats
            today_api_calls = self.session.query(func.count(APIUsage.id))\
                .filter(func.date(APIUsage.timestamp) == today).scalar() or 0
            
            today_visitors = self.session.query(func.count(func.distinct(UserActivity.user_ip)))\
                .filter(func.date(UserActivity.timestamp) == today).scalar() or 0
            
            # Week stats
            week_api_calls = self.session.query(func.count(APIUsage.id))\
                .filter(APIUsage.timestamp >= week_ago).scalar() or 0
            
            week_visitors = self.session.query(func.count(func.distinct(UserActivity.user_ip)))\
                .filter(UserActivity.timestamp >= week_ago).scalar() or 0
            
            # API call distribution
            api_distribution = self.session.query(
                APIUsage.api_provider,
                func.count(APIUsage.id).label('count')
            ).filter(APIUsage.timestamp >= week_ago)\
             .group_by(APIUsage.api_provider)\
             .all()
            
            return {
                'today': {
                    'api_calls': today_api_calls,
                    'unique_visitors': today_visitors
                },
                'week': {
                    'api_calls': week_api_calls,
                    'unique_visitors': week_visitors
                },
                'api_distribution': [
                    {'provider': stat.api_provider, 'calls': stat.count}
                    for stat in api_distribution
                ],
                'last_updated': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get dashboard summary: {e}")
            return {}
    
    def cache_financial_data(self, symbol: str, financial_data: Dict[str, Any]) -> bool:
        """Cache financial data to reduce future API calls."""
        session = self._get_session()
        try:
            # Check if data already exists
            existing = session.query(CachedFinancialData).filter_by(symbol=symbol).first()
            
            if existing:
                # Update existing record
                for key, value in financial_data.items():
                    if hasattr(existing, key) and value is not None:
                        setattr(existing, key, value)
                existing.updated_at = datetime.now()
                existing.api_calls_saved += 1
                logger.info(f"Updated cached financial data for {symbol}")
            else:
                # Create new record
                cache_entry = CachedFinancialData(
                    symbol=symbol,
                    company_name=financial_data.get('company_name', symbol),
                    sector=financial_data.get('sector'),
                    industry=financial_data.get('industry'),
                    market_cap=financial_data.get('market_cap'),
                    pe_ratio=financial_data.get('pe_ratio'),
                    price_to_book=financial_data.get('price_to_book'),
                    price_to_sales=financial_data.get('price_to_sales'),
                    ev_to_ebitda=financial_data.get('ev_to_ebitda'),
                    gross_margin=financial_data.get('gross_margin'),
                    operating_margin=financial_data.get('operating_margin'),
                    net_margin=financial_data.get('net_margin'),
                    roe=financial_data.get('roe'),
                    roa=financial_data.get('roa'),
                    roic=financial_data.get('roic'),
                    current_ratio=financial_data.get('current_ratio'),
                    debt_to_equity=financial_data.get('debt_to_equity'),
                    debt_to_assets=financial_data.get('debt_to_assets'),
                    interest_coverage=financial_data.get('interest_coverage'),
                    revenue_growth=financial_data.get('revenue_growth'),
                    earnings_growth=financial_data.get('earnings_growth'),
                    fcf_growth=financial_data.get('fcf_growth'),
                    additional_metrics=json.dumps({k: v for k, v in financial_data.items() 
                                                 if k not in ['symbol', 'company_name', 'sector', 'industry', 'market_cap',
                                                            'pe_ratio', 'price_to_book', 'price_to_sales', 'ev_to_ebitda',
                                                            'gross_margin', 'operating_margin', 'net_margin', 'roe', 'roa', 'roic',
                                                            'current_ratio', 'debt_to_equity', 'debt_to_assets', 'interest_coverage',
                                                            'revenue_growth', 'earnings_growth', 'fcf_growth']}),
                    data_source='FMP'
                )
                session.add(cache_entry)
                logger.info(f"Cached new financial data for {symbol}")
            
            session.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to cache financial data for {symbol}: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    def get_cached_financial_data(self, symbol: str, max_age_days: int = 7) -> Optional[Dict[str, Any]]:
        """Retrieve cached financial data if it's not too old."""
        session = self._get_session()
        try:
            cutoff_date = datetime.now() - timedelta(days=max_age_days)
            cached = session.query(CachedFinancialData).filter(
                CachedFinancialData.symbol == symbol,
                CachedFinancialData.updated_at >= cutoff_date,
                CachedFinancialData.is_active == True
            ).first()
            
            if cached:
                # Convert to dictionary
                data = {
                    'symbol': cached.symbol,
                    'company_name': cached.company_name,
                    'sector': cached.sector,
                    'industry': cached.industry,
                    'market_cap': cached.market_cap,
                    'pe_ratio': cached.pe_ratio,
                    'price_to_book': cached.price_to_book,
                    'price_to_sales': cached.price_to_sales,
                    'ev_to_ebitda': cached.ev_to_ebitda,
                    'gross_margin': cached.gross_margin,
                    'operating_margin': cached.operating_margin,
                    'net_margin': cached.net_margin,
                    'roe': cached.roe,
                    'roa': cached.roa,
                    'roic': cached.roic,
                    'current_ratio': cached.current_ratio,
                    'debt_to_equity': cached.debt_to_equity,
                    'debt_to_assets': cached.debt_to_assets,
                    'interest_coverage': cached.interest_coverage,
                    'revenue_growth': cached.revenue_growth,
                    'earnings_growth': cached.earnings_growth,
                    'fcf_growth': cached.fcf_growth,
                    'data_source': f"Cached ({cached.data_source})",
                    'last_updated': cached.updated_at.isoformat(),
                    'cache_hit': True
                }
                
                # Add additional metrics from JSON
                if cached.additional_metrics:
                    try:
                        additional = json.loads(cached.additional_metrics)
                        data.update(additional)
                    except:
                        pass
                
                # Increment cache hit counter
                cached.api_calls_saved += 1
                session.commit()
                
                logger.info(f"Retrieved cached financial data for {symbol}")
                return data
            
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve cached financial data for {symbol}: {e}")
            return None
        finally:
            session.close()
    
    def get_all_cached_companies(self) -> List[Dict[str, Any]]:
        """Get all cached financial data for admin panel."""
        session = self._get_session()
        try:
            cached_data = session.query(CachedFinancialData).filter_by(is_active=True).all()
            return [
                {
                    'id': data.id,
                    'symbol': data.symbol,
                    'company_name': data.company_name,
                    'sector': data.sector,
                    'market_cap': data.market_cap,
                    'pe_ratio': data.pe_ratio,
                    'roe': data.roe,
                    'gross_margin': data.gross_margin,
                    'data_source': data.data_source,
                    'created_at': data.created_at.isoformat(),
                    'updated_at': data.updated_at.isoformat(),
                    'api_calls_saved': data.api_calls_saved
                }
                for data in cached_data
            ]
        except Exception as e:
            logger.error(f"Failed to get cached companies: {e}")
            return []
        finally:
            session.close()
    
    def clear_all_cached_data(self) -> bool:
        """Clear all cached financial data."""
        try:
            # Get total before deletion for logging
            total_before = self.session.query(CachedFinancialData).filter_by(is_active=True).count()
            
            # Mark all as inactive instead of deleting for audit trail
            self.session.query(CachedFinancialData).filter_by(is_active=True).update({'is_active': False})
            self.session.commit()
            
            logger.info(f"Cleared {total_before} cached company records")
            return True
        except Exception as e:
            logger.error(f"Failed to clear cached data: {e}")
            self.session.rollback()
            return False
    
    def delete_cached_company(self, company_id: int) -> bool:
        """Delete a specific cached company by ID."""
        try:
            cached_data = self.session.query(CachedFinancialData).filter_by(id=company_id, is_active=True).first()
            if cached_data:
                # Mark as inactive instead of deleting for audit trail
                cached_data.is_active = False
                self.session.commit()
                logger.info(f"Deleted cached data for {cached_data.symbol} (ID: {company_id})")
                return True
            else:
                logger.warning(f"No active cached data found for ID: {company_id}")
                return False
        except Exception as e:
            logger.error(f"Failed to delete cached company {company_id}: {e}")
            self.session.rollback()
            return False
    
    def reset_api_calls_saved(self) -> bool:
        """Reset all API calls saved counters to 0."""
        try:
            updated_count = self.session.query(CachedFinancialData).filter_by(is_active=True).update({'api_calls_saved': 0})
            self.session.commit()
            logger.info(f"Reset API calls saved counter for {updated_count} companies")
            return True
        except Exception as e:
            logger.error(f"Failed to reset API calls saved: {e}")
            self.session.rollback()
            return False
    
    def close(self):
        """Close the database session - no longer needed with new session management."""
        pass

# Global tracker instance - use the fixed version
from utils.admin_db_fixed import admin_tracker_fixed
from utils.admin_db_fixed import track_user_action as fixed_track_user_action
admin_tracker = admin_tracker_fixed

def track_api_call(api_provider: str, endpoint: str, symbol: str = None, **kwargs):
    """Convenience function to track API calls."""
    try:
        admin_tracker.track_api_usage(api_provider, endpoint, symbol, **kwargs)
    except Exception:
        # Swallow errors to avoid breaking the app on logging issues
        pass

def track_user_action(user_ip: str, action: str, **kwargs):
    """Convenience function to track user actions (uses fixed tracker)."""
    try:
        # Use the fixed helper which is lightweight and non-blocking
        return fixed_track_user_action(user_ip, action, **kwargs)
    except Exception:
        return None
