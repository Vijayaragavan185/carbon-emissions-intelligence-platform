import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """Thread-safe rate limiter for API calls"""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = []
        self.lock = threading.Lock()
    
    def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        with self.lock:
            now = datetime.now()
            minute_ago = now - timedelta(minutes=1)
            
            # Remove requests older than 1 minute
            self.requests = [req_time for req_time in self.requests if req_time > minute_ago]
            
            # Check if we're at the limit
            if len(self.requests) >= self.requests_per_minute:
                oldest_request = min(self.requests)
                wait_until = oldest_request + timedelta(minutes=1)
                wait_seconds = (wait_until - now).total_seconds()
                
                if wait_seconds > 0:
                    logger.info(f"Rate limit reached, waiting {wait_seconds:.2f} seconds")
                    time.sleep(wait_seconds)
            
            # Record this request
            self.requests.append(now)

class APIKeyRotator:
    """Rotate API keys to increase rate limits"""
    
    def __init__(self, api_keys: List[str]):
        self.api_keys = api_keys if api_keys else [""]
        self.current_index = 0
        self.usage_counts = {key: 0 for key in self.api_keys}
        self.lock = threading.Lock()
    
    def get_next_key(self) -> str:
        """Get the next API key in rotation"""
        with self.lock:
            key = self.api_keys[self.current_index]
            self.usage_counts[key] += 1
            self.current_index = (self.current_index + 1) % len(self.api_keys)
            return key
