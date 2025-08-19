#!/usr/bin/env python3
"""
Fixed admin panel database with proper session management.
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Text, Boolean, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
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
    api_provider = Column(String(50))
    endpoint = Column(String(200))
    symbol = Column(String(20))
    status_code = Column(Integer)
    response_time = Column(Float)
    user_ip = Column(String(45))
    user_agent = Column(Text)
    request_data = Column(Text)
    success = Column(Boolean)

class UserActivity(Base):
    """Track user activity and searches."""
    __tablename__ = 'user_activity'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now)
    user_ip = Column(String(45))
    user_agent = Column(Text)
    session_id = Column(String(100))
    action = Column(String(100))
    page_url = Column(String(500))
    search_terms = Column(String(200))
    company_analyzed = Column(String(20))
    document_type = Column(String(50))
    duration_seconds = Column(Float, default=0.0)
    extra_data = Column(Text)

class CachedFinancialData(Base):
    """Cache financial data to reduce API calls."""
    __tablename__ = 'cached_financial_data'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(10), unique=True, index=True)
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
    roe = Column(Float)
    roa = Column(Float)
    roic = Column(Float)
    
    # Financial Health
    current_ratio = Column(Float)
    debt_to_equity = Column(Float)
    debt_to_assets = Column(Float)
    interest_coverage = Column(Float)
    
    # Growth Metrics
    revenue_growth = Column(Float)
    earnings_growth = Column(Float)
    fcf_growth = Column(Float)
    
    # Additional Financial Data
    additional_metrics = Column(Text)
    
    # Metadata
    data_source = Column(String(50), default='FMP')
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    is_active = Column(Boolean, default=True)
    api_calls_saved = Column(Integer, default=0)

# Database connection with proper SQLite settings
engine = create_engine(f'sqlite:///{DB_PATH}', echo=False, 
                      connect_args={
                          'check_same_thread': False, 
                          'timeout': 30,
                          'isolation_level': None  # Use autocommit mode
                      })
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

class AdminTrackerFixed:
    """Fixed admin tracker with proper session management."""
    
    def cache_financial_data(self, symbol: str, financial_data: Dict[str, Any]) -> bool:
        """Cache financial data with proper session handling."""
        session = SessionLocal()
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
    
    def get_all_cached_companies(self) -> List[Dict[str, Any]]:
        """Get all cached financial data for admin panel."""
        session = SessionLocal()
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
    
    def get_cached_financial_data(self, symbol: str, max_age_days: int = 7) -> Optional[Dict[str, Any]]:
        """Retrieve cached financial data if it's not too old."""
        session = SessionLocal()
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
    
    def track_api_usage(self, api_provider: str, endpoint: str, symbol: str = None, 
                       status_code: int = 200, response_time: float = 0.0,
                       user_ip: str = None, user_agent: str = None, 
                       request_data: Dict = None, success: bool = True):
        """Track an API call with proper session handling."""
        session = SessionLocal()
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

    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get admin dashboard summary statistics."""
        session = SessionLocal()
        try:
            total_companies = session.query(CachedFinancialData).filter_by(is_active=True).count()
            total_api_calls = session.query(APIUsage).count()
            total_api_calls_saved = session.query(func.sum(CachedFinancialData.api_calls_saved)).scalar() or 0
            
            # Recent activity (last 7 days)
            week_ago = datetime.now() - timedelta(days=7)
            recent_companies = session.query(CachedFinancialData).filter(
                CachedFinancialData.created_at >= week_ago,
                CachedFinancialData.is_active == True
            ).count()
            
            recent_api_calls = session.query(APIUsage).filter(
                APIUsage.timestamp >= week_ago
            ).count()
            
            return {
                'total_companies': total_companies,
                'total_api_calls': total_api_calls,
                'total_api_calls_saved': total_api_calls_saved,
                'recent_companies': recent_companies,
                'recent_api_calls': recent_api_calls,
                'cache_hit_rate': round((total_api_calls_saved / max(total_api_calls, 1)) * 100, 2),
                'last_updated': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get dashboard summary: {e}")
            return {
                'total_companies': 0,
                'total_api_calls': 0,
                'total_api_calls_saved': 0,
                'recent_companies': 0,
                'recent_api_calls': 0,
                'cache_hit_rate': 0,
                'last_updated': datetime.now().isoformat()
            }
        finally:
            session.close()
    
    def get_api_usage_stats(self) -> Dict[str, Any]:
        """Get API usage statistics."""
        session = SessionLocal()
        try:
            total_calls = session.query(APIUsage).count()
            successful_calls = session.query(APIUsage).filter_by(success=True).count()
            
            # Recent activity (last 24 hours)
            day_ago = datetime.now() - timedelta(days=1)
            recent_calls = session.query(APIUsage).filter(
                APIUsage.timestamp >= day_ago
            ).count()
            
            # Popular endpoints
            popular_endpoints = session.query(
                APIUsage.endpoint, 
                func.count(APIUsage.id).label('count')
            ).group_by(APIUsage.endpoint).order_by(
                func.count(APIUsage.id).desc()
            ).limit(5).all()
            
            return {
                'total_calls': total_calls,
                'successful_calls': successful_calls,
                'success_rate': round((successful_calls / max(total_calls, 1)) * 100, 2),
                'recent_calls': recent_calls,
                'popular_endpoints': [
                    {'endpoint': ep, 'count': count} 
                    for ep, count in popular_endpoints
                ]
            }
        except Exception as e:
            logger.error(f"Failed to get API usage stats: {e}")
            return {
                'total_calls': 0,
                'successful_calls': 0,
                'success_rate': 0,
                'recent_calls': 0,
                'popular_endpoints': []
            }
        finally:
            session.close()
    
    def get_user_activity_stats(self) -> Dict[str, Any]:
        """Get user activity statistics."""
        session = SessionLocal()
        try:
            total_activities = session.query(UserActivity).count()
            
            # Recent activity (last 24 hours)
            day_ago = datetime.now() - timedelta(days=1)
            recent_activities = session.query(UserActivity).filter(
                UserActivity.timestamp >= day_ago
            ).count()
            
            # Popular actions
            popular_actions = session.query(
                UserActivity.action,
                func.count(UserActivity.id).label('count')
            ).group_by(UserActivity.action).order_by(
                func.count(UserActivity.id).desc()
            ).limit(5).all()
            
            return {
                'total_activities': total_activities,
                'recent_activities': recent_activities,
                'popular_actions': [
                    {'action': action, 'count': count}
                    for action, count in popular_actions
                ]
            }
        except Exception as e:
            logger.error(f"Failed to get user activity stats: {e}")
            return {
                'total_activities': 0,
                'recent_activities': 0,
                'popular_actions': []
            }
        finally:
            session.close()
    
    def track_user_activity(self, user_ip: str, action: str, user_agent: str = None,
                          session_id: str = None, page_url: str = None,
                          search_terms: str = None, company_analyzed: str = None,
                          document_type: str = None, duration_seconds: float = 0.0,
                          extra_data: Dict = None):
        """Track user activity with proper session handling."""
        session = SessionLocal()
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
            session.add(activity)
            session.commit()
            logger.info(f"Tracked user activity: {action} from {user_ip}")
        except Exception as e:
            logger.error(f"Failed to track user activity: {e}")
            session.rollback()
        finally:
            session.close()
    
    def clear_all_cached_data(self) -> bool:
        """Clear all cached financial data."""
        session = SessionLocal()
        try:
            # Get total before deletion for logging
            total_before = session.query(CachedFinancialData).filter_by(is_active=True).count()
            
            # Mark all as inactive instead of deleting for audit trail
            session.query(CachedFinancialData).filter_by(is_active=True).update({'is_active': False})
            session.commit()
            
            logger.info(f"Cleared {total_before} cached company records")
            return True
        except Exception as e:
            logger.error(f"Failed to clear cached data: {e}")
            session.rollback()
            return False
        finally:
            session.close()

# Create fixed admin tracker instance
admin_tracker_fixed = AdminTrackerFixed()

def track_api_call(api_provider: str, endpoint: str, symbol: str = None, **kwargs):
    """Helper function for tracking API calls."""
    admin_tracker_fixed.track_api_usage(api_provider, endpoint, symbol, **kwargs)

def track_user_action(user_ip: str, action: str, **kwargs):
    """Helper function for tracking user actions."""
    admin_tracker_fixed.track_user_activity(user_ip, action, **kwargs)
