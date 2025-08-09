from fastapi import FastAPI, HTTPException, Query
from typing import List, Dict, Any, Optional

from services.shared.models import MatchSuggestion
from .service import MatchingService

app = FastAPI(title="Matching Service", version="1.0.0")
service = MatchingService()

@app.post("/quick-match", response_model=List[MatchSuggestion])
async def quick_match(
    volunteer_id: str = Query(..., description="Volunteer ID to match"),
    limit: int = Query(3, description="Number of matches to return", ge=1, le=10)
):
    """Generate quick match suggestions (top matches)"""
    try:
        suggestions = await service.quick_match(volunteer_id, limit)
        if not suggestions:
            raise HTTPException(
                status_code=404,
                detail="No suitable matches found for this volunteer"
            )
        return suggestions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/generate", response_model=List[MatchSuggestion])
async def generate_matches(
    volunteer_id: str = Query(..., description="Volunteer ID to match"),
    category: Optional[str] = Query(None, description="Filter by opportunity category"),
    limit: int = Query(10, description="Number of matches to return", ge=1, le=50)
):
    """Generate comprehensive match suggestions"""
    try:
        filters = {}
        if category:
            filters["category"] = category
            
        suggestions = await service.generate_matches(volunteer_id, filters, limit)
        return suggestions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/suggestions/{volunteer_id}", response_model=List[MatchSuggestion])
async def get_suggestions(volunteer_id: str):
    """Get existing suggestions for a volunteer"""
    try:
        suggestions = await service.get_suggestions(volunteer_id)
        return suggestions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "matching"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8002)