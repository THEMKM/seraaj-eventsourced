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

    # Recognition/Points Events
    POINTS_AWARD = "points.award"
    
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


from jsonschema import validate as _js_validate, ValidationError as _JSValidationError


class EventSchemas:
    """Event payload schemas for validation (optional)"""
    
    APPLICATION_SUBMITTED = {
        "type": "object",
        "required": ["applicationId", "volunteerId", "organizationId"],
        "properties": {
            "applicationId": {"type": "string"},
            "volunteerId": {"type": "string"},
            "organizationId": {"type": ["string", "null"]},
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
            "role": {"type": "string", "enum": ["VOLUNTEER", "ORG_ADMIN", "SUPERADMIN"]},
            "registeredAt": {"type": "string", "format": "date-time"}
        }
    }

    APPLICATION_CREATED = {
        "type": "object",
        "required": ["applicationId", "volunteerId", "opportunityId"],
        "properties": {
            "applicationId": {"type": "string"},
            "volunteerId": {"type": "string"},
            "opportunityId": {"type": "string"},
            "createdAt": {"type": "string", "format": "date-time"}
        }
    }

    APPLICATION_STATE_CHANGED = {
        "type": "object",
        "required": ["applicationId", "oldState", "newState"],
        "properties": {
            "applicationId": {"type": "string"},
            "oldState": {"type": "string"},
            "newState": {"type": "string"},
            "changedAt": {"type": "string", "format": "date-time"}
        }
    }

    APPLICATION_COMPLETED = {
        "type": "object",
        "required": ["applicationId", "volunteerId"],
        "properties": {
            "applicationId": {"type": "string"},
            "volunteerId": {"type": "string"},
            "completedAt": {"type": "string", "format": "date-time"}
        }
    }

    POINTS_AWARD = {
        "type": "object",
        "required": ["volunteerId", "points"],
        "properties": {
            "volunteerId": {"type": "string"},
            "points": {"type": "integer", "minimum": 1},
            "reason": {"type": ["string", "null"]},
            "applicationId": {"type": ["string", "null"]}
        }
    }

    USER_LOGIN = {
        "type": "object",
        "required": ["userId", "email", "loginAt"],
        "properties": {
            "userId": {"type": "string"},
            "email": {"type": "string", "format": "email"},
            "loginAt": {"type": "string", "format": "date-time"}
        }
    }

    USER_PASSWORD_CHANGED = {
        "type": "object",
        "required": ["userId", "changedAt"],
        "properties": {
            "userId": {"type": "string"},
            "changedAt": {"type": "string", "format": "date-time"}
        }
    }

    MATCH_SUGGESTION_APPLIED = {
        "type": "object",
        "required": ["suggestionId", "volunteerId", "opportunityId", "appliedAt"],
        "properties": {
            "suggestionId": {"type": "string"},
            "volunteerId": {"type": "string"},
            "opportunityId": {"type": "string"},
            "appliedAt": {"type": "string", "format": "date-time"}
        }
    }

    _SCHEMA_MAP = {
        EventTypes.APPLICATION_CREATED: APPLICATION_CREATED,
        EventTypes.APPLICATION_SUBMITTED: APPLICATION_SUBMITTED,
        EventTypes.APPLICATION_STATE_CHANGED: APPLICATION_STATE_CHANGED,
        EventTypes.APPLICATION_COMPLETED: APPLICATION_COMPLETED,
        EventTypes.POINTS_AWARD: POINTS_AWARD,
        EventTypes.MATCH_SUGGESTIONS_GENERATED: MATCH_SUGGESTIONS_GENERATED,
        EventTypes.MATCH_SUGGESTION_APPLIED: MATCH_SUGGESTION_APPLIED,
        EventTypes.USER_REGISTERED: USER_REGISTERED,
        EventTypes.USER_LOGIN: USER_LOGIN,
        EventTypes.USER_PASSWORD_CHANGED: USER_PASSWORD_CHANGED,
    }

    @classmethod
    def get_schema_for_type(cls, event_type: str) -> dict | None:
        return cls._SCHEMA_MAP.get(event_type)

    @classmethod
    def validate_payload(cls, event_type: str, payload: dict) -> None:
        schema = cls.get_schema_for_type(event_type)
        if not schema:
            # If no schema, consider it unknown; raise to enforce defined types only
            raise _JSValidationError(f"No schema defined for event type: {event_type}")
        _js_validate(payload, schema)
