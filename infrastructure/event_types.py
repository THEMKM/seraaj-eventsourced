"""
Centralized event type definitions for Seraaj event bus
"""

class EventTypes:
    """Event type constants for cross-service communication"""
    
    # Application Events
    APPLICATION_CREATED = "application.created"
    APPLICATION_SUBMITTED = "application.submitted"
    APPLICATION_STATE_CHANGED = "application.state.changed"
    APPLICATION_COMPLETED = "application.completed"
    APPLICATION_WITHDRAWN = "application.withdrawn"
    
    # Matching Events
    MATCH_SUGGESTIONS_GENERATED = "match.suggestions.generated"
    MATCH_SUGGESTION_APPLIED = "match.suggestion.applied"
    MATCH_SUGGESTION_ACCEPTED = "match.suggestion.accepted"
    MATCH_SUGGESTION_REJECTED = "match.suggestion.rejected"
    MATCH_SUGGESTION_EXPIRED = "match.suggestion.expired"
    
    # Authentication Events
    USER_REGISTERED = "user.registered"
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout" 
    USER_PASSWORD_CHANGED = "user.password.changed"
    USER_PROFILE_UPDATED = "user.profile.updated"
    
    # System/Service Events
    SERVICE_STARTED = "service.started"
    SERVICE_STOPPED = "service.stopped"
    SERVICE_HEALTH_CHECK = "service.health.check"
    SERVICE_ERROR = "service.error"
    
    # Organization Events (future)
    ORGANIZATION_CREATED = "organization.created"
    ORGANIZATION_UPDATED = "organization.updated"
    OPPORTUNITY_CREATED = "opportunity.created"
    OPPORTUNITY_UPDATED = "opportunity.updated"

    @classmethod
    def get_all_types(cls) -> list:
        """Get all defined event types"""
        return [
            value for name, value in cls.__dict__.items() 
            if not name.startswith('_') and isinstance(value, str) and not callable(value)
        ]

    @classmethod
    def get_application_events(cls) -> list:
        """Get application-related event types"""
        return [
            cls.APPLICATION_CREATED,
            cls.APPLICATION_SUBMITTED,
            cls.APPLICATION_STATE_CHANGED,
            cls.APPLICATION_COMPLETED,
            cls.APPLICATION_WITHDRAWN
        ]
    
    @classmethod
    def get_matching_events(cls) -> list:
        """Get matching-related event types"""
        return [
            cls.MATCH_SUGGESTIONS_GENERATED,
            cls.MATCH_SUGGESTION_APPLIED,
            cls.MATCH_SUGGESTION_ACCEPTED,
            cls.MATCH_SUGGESTION_REJECTED,
            cls.MATCH_SUGGESTION_EXPIRED
        ]
    
    @classmethod
    def get_auth_events(cls) -> list:
        """Get authentication-related event types"""
        return [
            cls.USER_REGISTERED,
            cls.USER_LOGIN,
            cls.USER_LOGOUT,
            cls.USER_PASSWORD_CHANGED,
            cls.USER_PROFILE_UPDATED
        ]
    
    @classmethod
    def get_system_events(cls) -> list:
        """Get system/service-related event types"""
        return [
            cls.SERVICE_STARTED,
            cls.SERVICE_STOPPED,
            cls.SERVICE_HEALTH_CHECK,
            cls.SERVICE_ERROR
        ]


class EventSchemas:
    """Event payload schemas for validation (optional)"""
    
    APPLICATION_SUBMITTED = {
        "type": "object",
        "required": ["applicationId", "volunteerId", "organizationId"],
        "properties": {
            "applicationId": {"type": "string"},
            "volunteerId": {"type": "string"},
            "organizationId": {"type": "string"},
            "opportunityId": {"type": "string"},
            "submittedAt": {"type": "string", "format": "date-time"}
        }
    }
    
    MATCH_SUGGESTIONS_GENERATED = {
        "type": "object", 
        "required": ["volunteerId", "matchCount"],
        "properties": {
            "volunteerId": {"type": "string"},
            "matchCount": {"type": "integer", "minimum": 0},
            "matches": {"type": "array", "items": {"type": "object"}},
            "generatedAt": {"type": "string", "format": "date-time"}
        }
    }
    
    USER_REGISTERED = {
        "type": "object",
        "required": ["userId", "email", "role"],
        "properties": {
            "userId": {"type": "string"},
            "email": {"type": "string", "format": "email"},
            "name": {"type": "string"},
            "role": {"type": "string", "enum": ["volunteer", "organization", "admin"]},
            "registeredAt": {"type": "string", "format": "date-time"}
        }
    }