"""
Centralized structured logging configuration for Seraaj services
"""
import os
import json
import time
import uuid
import logging
from datetime import datetime
from typing import Any, Dict, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to add structured JSON logging with trace IDs"""
    
    def __init__(self, app, service_name: str):
        super().__init__(app)
        self.service_name = service_name
    
    async def dispatch(self, request: Request, call_next):
        # Generate trace ID for request correlation
        trace_id = str(uuid.uuid4())
        request.state.trace_id = trace_id
        
        # Start timing
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Structure log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": "ERROR" if response.status_code >= 500 else "WARN" if response.status_code >= 400 else "INFO",
            "traceId": trace_id,
            "service": self.service_name,
            "operation": "http_request",
            "method": request.method,
            "path": str(request.url.path),
            "query": str(request.url.query) if request.url.query else None,
            "status": response.status_code,
            "durationMs": duration_ms,
            "userAgent": request.headers.get("user-agent"),
            "remoteAddr": request.client.host if request.client else None
        }
        
        # Add error details for 4xx/5xx
        if response.status_code >= 400:
            log_entry["message"] = f"HTTP {response.status_code} - {request.method} {request.url.path}"
        else:
            log_entry["message"] = f"HTTP {response.status_code} - {request.method} {request.url.path}"
        
        # Output structured log
        print(json.dumps(log_entry, separators=(',', ':')))
        
        # Add trace ID to response headers for debugging
        response.headers["X-Trace-Id"] = trace_id
        
        return response


def setup_json_logging(service_name: str, log_level: str = None) -> logging.Logger:
    """Setup structured JSON logging for a service"""
    if log_level is None:
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format='%(message)s',  # We'll structure the JSON ourselves
        handlers=[logging.StreamHandler()]
    )
    
    # Create service-specific logger
    logger = logging.getLogger(service_name)
    return logger


def log_structured(
    logger: logging.Logger, 
    level: str, 
    message: str, 
    trace_id: Optional[str] = None,
    operation: Optional[str] = None,
    **kwargs
):
    """Log a structured JSON message"""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "level": level.upper(),
        "service": logger.name,
        "message": message
    }
    
    # Add trace ID if provided
    if trace_id:
        log_entry["traceId"] = trace_id
    
    # Add operation if provided
    if operation:
        log_entry["operation"] = operation
    
    # Add any additional structured data
    for key, value in kwargs.items():
        if value is not None:
            log_entry[key] = value
    
    # Output as JSON
    print(json.dumps(log_entry, separators=(',', ':')))


def get_trace_id(request: Request) -> str:
    """Extract trace ID from request, or generate a new one"""
    return getattr(request.state, 'trace_id', str(uuid.uuid4()))


# Optional OpenTelemetry integration
def setup_telemetry(app, service_name: str):
    """Setup OpenTelemetry if OTEL endpoint is configured"""
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not otlp_endpoint:
        return  # Skip telemetry setup
    
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        
        # Configure trace provider
        trace.set_tracer_provider(TracerProvider())
        tracer = trace.get_tracer(service_name)
        
        # Configure OTLP exporter
        otlp_exporter = OTLPSpanExporter(endpoint=f"{otlp_endpoint}/v1/traces")
        span_processor = BatchSpanProcessor(otlp_exporter)
        trace.get_tracer_provider().add_span_processor(span_processor)
        
        # Auto-instrument FastAPI
        FastAPIInstrumentor.instrument_app(app)
        
        print(f"OpenTelemetry enabled for {service_name}, endpoint: {otlp_endpoint}")
        
    except ImportError:
        print(f"OpenTelemetry dependencies not available for {service_name}")
    except Exception as e:
        print(f"Failed to setup OpenTelemetry for {service_name}: {e}")
        # Continue without telemetry - don't fail the service


# Business metrics logging helpers
def log_business_metric(
    logger: logging.Logger,
    metric_name: str,
    metric_value: Any,
    trace_id: Optional[str] = None,
    **context
):
    """Log business metrics in structured format"""
    log_structured(
        logger,
        "INFO",
        f"Business metric: {metric_name}",
        trace_id=trace_id,
        operation="business_metric",
        metricName=metric_name,
        metricValue=metric_value,
        **context
    )


def log_performance_metric(
    logger: logging.Logger,
    operation: str,
    duration_ms: int,
    trace_id: Optional[str] = None,
    **context
):
    """Log performance metrics in structured format"""
    log_structured(
        logger,
        "INFO" if duration_ms < 1000 else "WARN",
        f"Performance: {operation} took {duration_ms}ms",
        trace_id=trace_id,
        operation="performance_metric",
        operationName=operation,
        durationMs=duration_ms,
        **context
    )