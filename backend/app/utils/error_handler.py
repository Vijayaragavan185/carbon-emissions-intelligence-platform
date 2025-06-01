import logging
import time
import functools
from typing import Any, Callable
import requests
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

def handle_api_error(max_retries: int = 3):
    """Decorator for handling API errors with retry logic"""
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            base_delay = 1
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                
                except requests.exceptions.Timeout as e:
                    logger.warning(f"Timeout on attempt {attempt + 1}: {e}")
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(base_delay * (2 ** attempt))
                
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 429:  # Rate limited
                        retry_after = int(e.response.headers.get('Retry-After', 60))
                        logger.warning(f"Rate limited, waiting {retry_after} seconds")
                        time.sleep(retry_after)
                        continue
                    elif e.response.status_code >= 500:  # Server error
                        logger.warning(f"Server error on attempt {attempt + 1}: {e}")
                        if attempt == max_retries - 1:
                            raise
                        time.sleep(base_delay * (2 ** attempt))
                    else:
                        # Client error, don't retry
                        raise
                
                except requests.exceptions.ConnectionError as e:
                    logger.warning(f"Connection error on attempt {attempt + 1}: {e}")
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(base_delay * (2 ** attempt))
                
                except Exception as e:
                    logger.error(f"Unexpected error in {func.__name__}: {e}")
                    raise
        
        return wrapper
    return decorator

def handle_database_error(func: Callable) -> Callable:
    """Decorator for handling database errors"""
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except SQLAlchemyError as e:
            logger.error(f"Database error in {func.__name__}: {e}")
            # Rollback transaction if session is available
            if hasattr(args[0], 'db') and hasattr(args[0].db, 'rollback'):
                args[0].db.rollback()
            raise
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}")
            raise
    
    return wrapper
