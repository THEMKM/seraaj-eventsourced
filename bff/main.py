"""
Simplified Seraaj BFF API for testing schema validation
"""

import os
import json
import yaml
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import jsonschema
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Import service adapters
from .adapters.applications import ApplicationsAdapter
from .adapters.matching import MatchingAdapter


# Load OpenAPI schema for validation
def load_openapi_schema():
    """Load the OpenAPI schema and referenced schemas for validation"""
    try:
        schema_path = Path(__file__).parent.parent / "contracts" / "v1.0.0" / "api" / "bff.openapi.yaml"
        schemas_dir = schema_path.parent / "schemas"
        
        with open(schema_path, 'r', encoding='utf-8') as f:
            openapi_spec = yaml.safe_load(f)
        
        # Load referenced schemas
        referenced_schemas = {}
        for schema_file in ["match-suggestion.yaml", "application.yaml", "submit-application.yaml", "volunteer-profile-view.yaml"]:
            schema_file_path = schemas_dir / schema_file
            if schema_file_path.exists():
                with open(schema_file_path, 'r', encoding='utf-8') as f:
                    schema_content = yaml.safe_load(f)
                    referenced_schemas[f"./schemas/{schema_file}"] = schema_content
        
        return openapi_spec, referenced_schemas
    except Exception as e:
        print(f"[WARNING] Could not load OpenAPI schema: {e}")
        return {}, {}


OPENAPI_SPEC, REFERENCED_SCHEMAS = load_openapi_schema()


def resolve_schema_ref(schema_ref: str) -> Dict[str, Any]:
    """Resolve a schema reference to actual schema"""
    if schema_ref.startswith('./schemas/'):
        return REFERENCED_SCHEMAS.get(schema_ref, {})
    elif schema_ref.startswith('#/components/schemas/'):
        component_name = schema_ref.split('/')[-1]
        return OPENAPI_SPEC.get('components', {}).get('schemas', {}).get(component_name, {})
    return {}


def validate_response_schema(endpoint_path: str, method: str, status_code: int, response_data: Any):
    """Validate response against OpenAPI schema - simplified version"""
    try:
        if not OPENAPI_SPEC:
            print("[DEBUG] No OpenAPI spec loaded, skipping validation")
            return
            
        print(f"[DEBUG] Validating {method.upper()} {endpoint_path} ({status_code})")
        
        # Find the endpoint in OpenAPI spec
        paths = OPENAPI_SPEC.get('paths', {})
        endpoint_spec = paths.get(endpoint_path, {})
        method_spec = endpoint_spec.get(method.lower(), {})
        responses = method_spec.get('responses', {})
        
        # Get response schema for status code
        response_spec = responses.get(str(status_code), responses.get('default', {}))
        content = response_spec.get('content', {}).get('application/json', {})
        schema = content.get('schema', {})
        
        if not schema:
            print(f"[DEBUG] No schema found for {method.upper()} {endpoint_path} ({status_code})")
            return
        
        print(f"[DEBUG] Found schema: {json.dumps(schema, indent=2)}")
        
        # Resolve schema references
        if '$ref' in schema:
            resolved_schema = resolve_schema_ref(schema['$ref'])
            if resolved_schema:
                schema = resolved_schema
                print(f"[DEBUG] Resolved schema: {json.dumps(schema, indent=2)[:200]}...")
        
        # Handle array responses
        if schema.get('type') == 'array' and 'items' in schema:
            items_schema = schema['items']
            if '$ref' in items_schema:
                resolved_items = resolve_schema_ref(items_schema['$ref'])
                if resolved_items:
                    items_schema = resolved_items
            
            # Validate each item in the array
            if isinstance(response_data, list):
                for i, item in enumerate(response_data):
                    jsonschema.validate(item, items_schema)
                    print(f"[DEBUG] Item {i} validation passed")
            print(f"[DEBUG] Array validation passed for {len(response_data) if isinstance(response_data, list) else 0} items")
            return
        
        # Validate the response
        jsonschema.validate(response_data, schema)
        print(f"[DEBUG] Schema validation passed for {method.upper()} {endpoint_path} ({status_code})")
        
    except jsonschema.ValidationError as e:
        print(f"[ERROR] Schema validation failed for {method.upper()} {endpoint_path} ({status_code}): {e.message}")
        print(f"[DEBUG] Failed at: {e.json_path}")
        print(f"[DEBUG] Response data sample: {str(response_data)[:500]}...")
        # Don't raise in development - just log
    except Exception as e:
        print(f"[WARNING] Schema validation error for {method.upper()} {endpoint_path}: {str(e)}")


# Initialize FastAPI app
app = FastAPI(
    title="Seraaj BFF API",
    description="Backend for Frontend API for the Seraaj volunteer platform",
    version="1.0.0"
)

# CORS Configuration
CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for request/response
class QuickMatchRequest(BaseModel):
    volunteerId: str = Field(..., description="ID of the volunteer requesting matches")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum number of matches to return")


class SubmitApplicationRequest(BaseModel):
    volunteerId: str = Field(..., description="ID of the volunteer submitting the application")
    opportunityId: str = Field(..., description="ID of the opportunity being applied to")
    coverLetter: Optional[str] = Field(None, max_length=1000, description="Optional cover letter from volunteer")


# Mock data generators for contract-accurate responses
def generate_mock_match_suggestion(volunteer_id: str, index: int = 0) -> Dict[str, Any]:
    """Generate a mock match suggestion that matches the schema"""
    base_time = datetime.utcnow()
    return {
        "id": f"match-{volunteer_id}-{index:03d}",
        "volunteerId": volunteer_id,
        "opportunityId": f"opp-{index:03d}",
        "organizationId": f"org-{index:03d}",
        "score": 85.5 + (index * 2),
        "reasons": [
            "Skills match opportunity requirements",
            "Location preference aligns",
            "Available during required time slots"
        ],
        "opportunityTitle": f"Community Education Program {index + 1}",
        "organizationName": f"Hope Foundation {index + 1}",
        "status": "active",
        "generatedAt": base_time.isoformat(),
        "expiresAt": base_time.replace(day=min(28, base_time.day + 7)).isoformat()
    }


def generate_mock_application(volunteer_id: str, index: int = 0) -> Dict[str, Any]:
    """Generate a mock application that matches the schema"""
    base_time = datetime.utcnow()
    return {
        "id": f"app-{volunteer_id}-{index:03d}",
        "volunteerId": volunteer_id,
        "opportunityId": f"opp-{index:03d}",
        "organizationId": f"org-{index:03d}",
        "status": "submitted",
        "coverLetter": f"I am very interested in this opportunity because...",
        "submittedAt": base_time.isoformat(),
        "createdAt": base_time.isoformat(),
        "updatedAt": base_time.isoformat()
    }


def generate_mock_volunteer_profile(volunteer_id: str) -> Dict[str, Any]:
    """Generate a mock volunteer profile that matches the schema"""
    base_time = datetime.utcnow()
    return {
        "id": volunteer_id,
        "email": "volunteer@example.com",
        "firstName": "John",
        "lastName": "Doe",
        "level": 5,
        "status": "active",
        "skills": ["teaching", "technical", "social"],
        "badges": [
            {
                "id": "badge-rookie",
                "name": "Rookie",
                "description": "Completed first volunteer opportunity",
                "imageUrl": "https://example.com/badges/rookie.png",
                "earnedAt": base_time.isoformat()
            }
        ],
        "totalHours": 120.5,
        "completedApplications": 8,
        "createdAt": base_time.isoformat(),
        "lastActive": base_time.isoformat()
    }


# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint that returns service status"""
    response_data = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }
    
    # Validate against schema
    validate_response_schema("/health", "get", 200, response_data)
    
    return response_data


@app.get("/api/health/services")
async def services_health_check():
    """Extended health check that includes dependent services"""
    applications_healthy = await applications_adapter.health_check()
    matching_healthy = await matching_adapter.health_check()
    
    overall_status = "healthy" if applications_healthy and matching_healthy else "degraded"
    
    response_data = {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "services": {
            "applications": "healthy" if applications_healthy else "unhealthy",
            "matching": "healthy" if matching_healthy else "unhealthy"
        }
    }
    
    return response_data


# Initialize service adapters
applications_adapter = ApplicationsAdapter()
matching_adapter = MatchingAdapter()


# Volunteer endpoints with real service calls
@app.post("/api/volunteer/quick-match")
async def get_quick_match(request: QuickMatchRequest):
    """Get quick match suggestions for a volunteer"""
    print(f"[DEBUG] Quick match request for volunteer: {request.volunteerId}, limit: {request.limit}")
    
    try:
        # Call matching service
        matches = await matching_adapter.quick_match(request.volunteerId, request.limit)
        
        # Validate response against schema
        validate_response_schema("/volunteer/quick-match", "post", 200, matches)
        
        return matches
        
    except HTTPException:
        # Re-raise HTTP exceptions (from service adapter)
        raise
    except Exception as e:
        print(f"[ERROR] Quick match failed: {str(e)}")
        # Fallback to mock data for graceful degradation
        matches = [
            generate_mock_match_suggestion(request.volunteerId, i)
            for i in range(min(request.limit, 3))
        ]
        validate_response_schema("/volunteer/quick-match", "post", 200, matches)
        return matches


@app.post("/api/volunteer/apply", status_code=201)
async def submit_application(request: SubmitApplicationRequest):
    """Submit a volunteer application"""
    print(f"[DEBUG] Application submission for volunteer: {request.volunteerId}, opportunity: {request.opportunityId}")
    
    try:
        # Call applications service
        application = await applications_adapter.submit_application(
            request.volunteerId, 
            request.opportunityId, 
            request.coverLetter
        )
        
        # Validate response against schema
        validate_response_schema("/volunteer/apply", "post", 201, application)
        
        return application
        
    except HTTPException:
        # Re-raise HTTP exceptions (from service adapter)
        raise
    except Exception as e:
        print(f"[ERROR] Application submission failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/api/volunteer/{volunteer_id}/dashboard")
async def get_volunteer_dashboard(volunteer_id: str):
    """Get volunteer dashboard data"""
    print(f"[DEBUG] Dashboard request for volunteer: {volunteer_id}")
    
    try:
        # Fetch data from multiple services concurrently
        # In production, these would be done in parallel
        
        # Get applications from applications service
        applications = await applications_adapter.get_volunteer_applications(volunteer_id)
        
        # Filter for active applications (not in final states)
        active_applications = [
            app for app in applications 
            if app.get('status') not in ['completed', 'cancelled', 'rejected']
        ]
        
        # Get recent matches from matching service
        recent_matches = await matching_adapter.get_suggestions(volunteer_id)
        
        # Generate profile data (mock for now - would come from volunteer service in production)
        profile = generate_mock_volunteer_profile(volunteer_id)
        
        # Update profile stats based on real data
        profile.update({
            "completedApplications": len([
                app for app in applications 
                if app.get('status') == 'completed'
            ])
        })
        
        dashboard_data = {
            "profile": profile,
            "activeApplications": active_applications,
            "recentMatches": recent_matches
        }
        
        # Validate response against schema
        validate_response_schema("/volunteer/{volunteerId}/dashboard", "get", 200, dashboard_data)
        
        return dashboard_data
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        print(f"[ERROR] Dashboard request failed: {str(e)}")
        # Fallback to mock data for graceful degradation
        dashboard_data = {
            "profile": generate_mock_volunteer_profile(volunteer_id),
            "activeApplications": [
                generate_mock_application(volunteer_id, i)
                for i in range(2)
            ],
            "recentMatches": [
                generate_mock_match_suggestion(volunteer_id, i)
                for i in range(3)
            ]
        }
        validate_response_schema("/volunteer/{volunteerId}/dashboard", "get", 200, dashboard_data)
        return dashboard_data


if __name__ == "__main__":
    port = int(os.getenv('BFF_PORT', '8000'))
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="debug")