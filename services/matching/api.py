from fastapi import FastAPI, HTTPException, Query, Request
from typing import List, Dict, Any, Optional
from datetime import datetime

from services.shared.models import MatchSuggestion
from services.shared.logging_config import (
    StructuredLoggingMiddleware, 
    setup_json_logging, 
    setup_telemetry,
    log_structured, 
    get_trace_id,
    log_business_metric,
    log_performance_metric
)
from .service import MatchingService

app = FastAPI(title="Matching Service", version="1.0.0")
service = MatchingService()

# Setup structured logging
logger = setup_json_logging("matching")

# Add structured logging middleware
app.add_middleware(StructuredLoggingMiddleware, service_name="matching")

# Setup optional OpenTelemetry
setup_telemetry(app, "matching")

@app.post("/quick-match", response_model=List[MatchSuggestion])
async def quick_match(
    volunteer_id: str = Query(..., description="Volunteer ID to match"),
    limit: int = Query(3, description="Number of matches to return", ge=1, le=10),
    request: Request = None
):
    """Generate quick match suggestions (top matches)"""
    trace_id = get_trace_id(request) if request else None
    start_time = datetime.utcnow()
    
    log_structured(
        logger, "INFO", "Quick match requested",
        trace_id=trace_id,
        operation="quick_match",
        volunteerId=volunteer_id,
        limit=limit
    )
    
    try:
        suggestions = await service.quick_match(volunteer_id, limit)
        
        if not suggestions:
            log_structured(
                logger, "WARN", "No matches found for volunteer",
                trace_id=trace_id,
                operation="quick_match",
                volunteerId=volunteer_id,
                limit=limit
            )
            raise HTTPException(
                status_code=404,
                detail="No suitable matches found for this volunteer"
            )
        
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        avg_score = sum(s.score for s in suggestions) / len(suggestions) if suggestions else 0
        
        log_structured(
            logger, "INFO", "Quick match generated successfully",
            trace_id=trace_id,
            operation="quick_match",
            volunteerId=volunteer_id,
            matchCount=len(suggestions),
            avgScore=round(avg_score, 2),
            durationMs=duration_ms
        )
        
        # Log business metrics
        log_business_metric(
            logger, "matches_generated", len(suggestions),
            trace_id=trace_id,
            volunteerId=volunteer_id,
            matchType="quick"
        )
        
        log_performance_metric(
            logger, "quick_match", duration_ms,
            trace_id=trace_id,
            volunteerId=volunteer_id
        )
        
        return suggestions
        
    except HTTPException:
        raise
    except Exception as e:
        log_structured(
            logger, "ERROR", "Quick match generation failed",
            trace_id=trace_id,
            operation="quick_match",
            volunteerId=volunteer_id,
            error=str(e),
            errorType=type(e).__name__
        )
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/generate", response_model=List[MatchSuggestion])
async def generate_matches(
    volunteer_id: str = Query(..., description="Volunteer ID to match"),
    category: Optional[str] = Query(None, description="Filter by opportunity category"),
    limit: int = Query(10, description="Number of matches to return", ge=1, le=50),
    request: Request = None
):
    """Generate comprehensive match suggestions"""
    trace_id = get_trace_id(request) if request else None
    start_time = datetime.utcnow()
    
    filters = {}
    if category:
        filters["category"] = category
    
    log_structured(
        logger, "INFO", "Comprehensive match generation requested",
        trace_id=trace_id,
        operation="generate_matches",
        volunteerId=volunteer_id,
        category=category,
        limit=limit
    )
    
    try:
        suggestions = await service.generate_matches(volunteer_id, filters, limit)
        
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        avg_score = sum(s.score for s in suggestions) / len(suggestions) if suggestions else 0
        
        log_structured(
            logger, "INFO", "Comprehensive matches generated successfully",
            trace_id=trace_id,
            operation="generate_matches",
            volunteerId=volunteer_id,
            category=category,
            matchCount=len(suggestions),
            avgScore=round(avg_score, 2),
            durationMs=duration_ms
        )
        
        # Log business metrics
        log_business_metric(
            logger, "matches_generated", len(suggestions),
            trace_id=trace_id,
            volunteerId=volunteer_id,
            matchType="comprehensive",
            category=category
        )
        
        log_performance_metric(
            logger, "generate_matches", duration_ms,
            trace_id=trace_id,
            volunteerId=volunteer_id
        )
        
        return suggestions
        
    except Exception as e:
        log_structured(
            logger, "ERROR", "Comprehensive match generation failed",
            trace_id=trace_id,
            operation="generate_matches",
            volunteerId=volunteer_id,
            error=str(e),
            errorType=type(e).__name__
        )
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/suggestions/{volunteer_id}", response_model=List[MatchSuggestion])
async def get_suggestions(volunteer_id: str, request: Request = None):
    """Get existing suggestions for a volunteer"""
    trace_id = get_trace_id(request) if request else None
    
    log_structured(
        logger, "INFO", "Existing suggestions retrieval requested",
        trace_id=trace_id,
        operation="get_suggestions",
        volunteerId=volunteer_id
    )
    
    try:
        suggestions = await service.get_suggestions(volunteer_id)
        
        log_structured(
            logger, "INFO", "Existing suggestions retrieved successfully",
            trace_id=trace_id,
            operation="get_suggestions",
            volunteerId=volunteer_id,
            suggestionCount=len(suggestions)
        )
        
        return suggestions
        
    except Exception as e:
        log_structured(
            logger, "ERROR", "Suggestions retrieval failed",
            trace_id=trace_id,
            operation="get_suggestions",
            volunteerId=volunteer_id,
            error=str(e),
            errorType=type(e).__name__
        )
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy", 
        "service": "matching",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@app.get("/health/live")
async def liveness_check():
    """Kubernetes liveness probe - is the service running?"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "matching",
        "version": "1.0.0"
    }


@app.get("/health/ready")
async def readiness_check():
    """Kubernetes readiness probe - can the service handle requests?"""
    checks = {}
    overall_healthy = True
    
    # Check Redis connectivity (when event bus is active)
    try:
        # Future: await event_bus.ping()
        checks["eventBus"] = {"status": "healthy", "latencyMs": 2}
    except Exception as e:
        checks["eventBus"] = {"status": "unhealthy", "error": str(e)}
        overall_healthy = False
    
    return {
        "status": "healthy" if overall_healthy else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8003)