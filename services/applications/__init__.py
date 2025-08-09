"""
Applications Service

Manages the complete application lifecycle from submission to completion.
Implements event sourcing and state machine patterns.
"""
from .api import app
from .service import ApplicationService, SubmitApplicationCommand

__all__ = ["app", "ApplicationService", "SubmitApplicationCommand"]