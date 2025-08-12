"""
Tests for structured logging functionality
"""
import json
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime

from services.shared.logging_config import (
    setup_json_logging, 
    log_structured,
    log_business_metric,
    log_performance_metric,
    StructuredLoggingMiddleware
)


def test_setup_json_logging():
    """Test that structured logging setup creates a logger"""
    logger = setup_json_logging("test_service")
    assert logger.name == "test_service"


def test_log_structured_format():
    """Test that structured logs are properly formatted as JSON"""
    logger = setup_json_logging("test_service")
    
    with patch('builtins.print') as mock_print:
        log_structured(
            logger, "INFO", "Test message",
            trace_id="test-trace-123",
            operation="test_operation",
            userId="user-456"
        )
        
        # Verify print was called with JSON
        mock_print.assert_called_once()
        printed_text = mock_print.call_args[0][0]
        
        # Should be valid JSON
        log_data = json.loads(printed_text)
        
        # Verify required fields
        assert log_data["level"] == "INFO"
        assert log_data["service"] == "test_service"
        assert log_data["message"] == "Test message"
        assert log_data["traceId"] == "test-trace-123"
        assert log_data["operation"] == "test_operation"
        assert log_data["userId"] == "user-456"
        assert "timestamp" in log_data


def test_log_business_metric():
    """Test business metric logging"""
    logger = setup_json_logging("test_service")
    
    with patch('builtins.print') as mock_print:
        log_business_metric(
            logger, "user_registration", 1,
            trace_id="test-trace-123",
            email="test@example.com"
        )
        
        # Verify log structure
        mock_print.assert_called_once()
        printed_text = mock_print.call_args[0][0]
        log_data = json.loads(printed_text)
        
        assert log_data["operation"] == "business_metric"
        assert log_data["metricName"] == "user_registration"
        assert log_data["metricValue"] == 1
        assert log_data["email"] == "test@example.com"


def test_log_performance_metric():
    """Test performance metric logging"""
    logger = setup_json_logging("test_service")
    
    with patch('builtins.print') as mock_print:
        log_performance_metric(
            logger, "database_query", 150,
            trace_id="test-trace-123",
            query="SELECT * FROM users"
        )
        
        # Verify log structure
        mock_print.assert_called_once()
        printed_text = mock_print.call_args[0][0]
        log_data = json.loads(printed_text)
        
        assert log_data["operation"] == "performance_metric"
        assert log_data["operationName"] == "database_query"
        assert log_data["durationMs"] == 150
        assert log_data["query"] == "SELECT * FROM users"
        
        # Performance logs should be WARN for slow operations
        assert log_data["level"] == "INFO"  # 150ms is fast


def test_structured_logging_middleware():
    """Test that middleware adds trace IDs and logs requests"""
    from fastapi import FastAPI, Request
    
    app = FastAPI()
    
    @app.get("/test")
    async def test_endpoint(request: Request):
        # Middleware should add trace_id to request.state
        return {"trace_id": getattr(request.state, 'trace_id', None)}
    
    # Add middleware
    app.add_middleware(StructuredLoggingMiddleware, service_name="test_service")
    
    client = TestClient(app)
    
    with patch('builtins.print') as mock_print:
        response = client.get("/test")
        
        # Verify response includes trace ID
        assert response.status_code == 200
        data = response.json()
        assert data["trace_id"] is not None
        
        # Verify X-Trace-Id header is present
        assert "X-Trace-Id" in response.headers
        assert response.headers["X-Trace-Id"] == data["trace_id"]
        
        # Verify middleware logged the request
        mock_print.assert_called()
        printed_text = mock_print.call_args[0][0]
        log_data = json.loads(printed_text)
        
        assert log_data["service"] == "test_service"
        assert log_data["method"] == "GET"
        assert log_data["path"] == "/test"
        assert log_data["status"] == 200
        assert "durationMs" in log_data
        assert log_data["traceId"] == data["trace_id"]


def test_error_logging_levels():
    """Test that different HTTP status codes get appropriate log levels"""
    from fastapi import FastAPI, HTTPException
    
    app = FastAPI()
    
    @app.get("/test-error")
    async def test_error():
        raise HTTPException(status_code=500, detail="Server error")
    
    @app.get("/test-not-found")
    async def test_not_found():
        raise HTTPException(status_code=404, detail="Not found")
    
    @app.get("/test-success")
    async def test_success():
        return {"status": "ok"}
    
    app.add_middleware(StructuredLoggingMiddleware, service_name="test_service")
    
    client = TestClient(app)
    
    with patch('builtins.print') as mock_print:
        # Test 500 error - should be ERROR level
        response = client.get("/test-error")
        assert response.status_code == 500
        
        printed_text = mock_print.call_args[0][0]
        log_data = json.loads(printed_text)
        assert log_data["level"] == "ERROR"
        assert log_data["status"] == 500
        
        mock_print.reset_mock()
        
        # Test 404 error - should be WARN level
        response = client.get("/test-not-found")
        assert response.status_code == 404
        
        printed_text = mock_print.call_args[0][0]
        log_data = json.loads(printed_text)
        assert log_data["level"] == "WARN"
        assert log_data["status"] == 404
        
        mock_print.reset_mock()
        
        # Test 200 success - should be INFO level
        response = client.get("/test-success")
        assert response.status_code == 200
        
        printed_text = mock_print.call_args[0][0]
        log_data = json.loads(printed_text)
        assert log_data["level"] == "INFO"
        assert log_data["status"] == 200


def test_json_log_format_consistency():
    """Test that all logs follow consistent JSON format"""
    logger = setup_json_logging("test_service")
    
    with patch('builtins.print') as mock_print:
        # Test various log scenarios
        log_structured(logger, "INFO", "Simple message")
        log_structured(logger, "ERROR", "Error message", error="Something went wrong")
        log_business_metric(logger, "test_metric", 42, userId="user-123")
        log_performance_metric(logger, "test_operation", 250, database="postgres")
        
        # Verify all calls produced valid JSON
        assert mock_print.call_count == 4
        
        for call in mock_print.call_args_list:
            printed_text = call[0][0]
            log_data = json.loads(printed_text)  # Should not raise exception
            
            # Verify consistent required fields
            assert "timestamp" in log_data
            assert "level" in log_data
            assert "service" in log_data
            assert "message" in log_data
            
            # Verify timestamp format (ISO 8601 with Z suffix)
            assert log_data["timestamp"].endswith("Z")
            datetime.fromisoformat(log_data["timestamp"][:-1])  # Should parse correctly


if __name__ == "__main__":
    pytest.main([__file__])