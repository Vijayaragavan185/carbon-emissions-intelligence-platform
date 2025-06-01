import pytest
from unittest.mock import Mock, patch
from requests.exceptions import HTTPError, Timeout, ConnectionError
from app.utils.error_handler import handle_api_error

class TestErrorHandling:
    
    def test_successful_function(self):
        """Test successful function execution"""
        @handle_api_error(max_retries=3)
        def successful_function():
            return "success"
        
        result = successful_function()
        assert result == "success"
    
    def test_timeout_retry_exhausted(self):
        """Test timeout error retry exhaustion"""
        @handle_api_error(max_retries=2)
        def failing_function():
            raise Timeout("Request timed out")
        
        with patch('time.sleep'):  # Don't actually sleep in tests
            with pytest.raises(Timeout):
                failing_function()
    
    def test_rate_limit_handling(self):
        """Test rate limit error handling"""
        @handle_api_error(max_retries=2)
        def rate_limited_function():
            error = HTTPError()
            error.response = Mock()
            error.response.status_code = 429
            error.response.headers = {'Retry-After': '1'}
            raise error
        
        with patch('time.sleep') as mock_sleep:
            with pytest.raises(HTTPError):
                rate_limited_function()
            mock_sleep.assert_called()
    
    def test_server_error_retry(self):
        """Test server error retry logic"""
        @handle_api_error(max_retries=2)
        def server_error_function():
            error = HTTPError()
            error.response = Mock()
            error.response.status_code = 500
            raise error
        
        with patch('time.sleep'):
            with pytest.raises(HTTPError):
                server_error_function()
