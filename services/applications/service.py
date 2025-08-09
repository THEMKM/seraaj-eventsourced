"""
Application domain service implementing business logic
"""
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from services.shared.models import Application
from .repository import ApplicationRepository
from .state_machine import ApplicationStateMachine, ApplicationState
from .events import EventPublisher


class SubmitApplicationCommand:
    """Command for submitting an application"""
    def __init__(self, volunteer_id: str, opportunity_id: str, cover_letter: Optional[str] = None):
        self.volunteerId = volunteer_id
        self.opportunityId = opportunity_id
        self.coverLetter = cover_letter


class ApplicationService:
    """Application domain service"""
    
    def __init__(self, data_dir: str = "data"):
        self.repository = ApplicationRepository(data_dir)
        self.event_publisher = EventPublisher(data_dir)
    
    async def submit_application(self, command: SubmitApplicationCommand) -> Application:
        """Submit a new application"""
        
        # Validate volunteer exists (stub - in production would call volunteer service)
        if not command.volunteerId:
            raise ValueError("Volunteer ID is required")
        
        # Validate opportunity exists (stub - in production would call opportunity service)
        if not command.opportunityId:
            raise ValueError("Opportunity ID is required")
        
        # Check for existing application
        existing_apps = await self.repository.find_by_volunteer(command.volunteerId)
        for app in existing_apps:
            if (app.opportunityId == command.opportunityId and 
                app.status not in ['rejected', 'cancelled', 'completed']):
                raise ValueError(f"Application already exists for this opportunity")
        
        # Create application
        now = datetime.utcnow()
        application = Application(
            id=str(uuid4()),
            volunteerId=command.volunteerId,
            opportunityId=command.opportunityId,
            status=ApplicationState.SUBMITTED,  # Skip draft for quick-match flow
            coverLetter=command.coverLetter,
            submittedAt=now,
            createdAt=now,
            updatedAt=now
        )
        
        # Save application
        application = await self.repository.create(application)
        
        # Publish submitted event
        await self.event_publisher.publish(
            "application.submitted",
            {
                "applicationId": application.id,
                "volunteerId": application.volunteerId,
                "opportunityId": application.opportunityId,
                "submittedAt": application.submittedAt.isoformat()
            }
        )
        
        return application
    
    async def update_application_state(
        self,
        application_id: str,
        action: str,
        reason: Optional[str] = None
    ) -> Application:
        """Update application state using state machine"""
        
        # Get current application
        application = await self.repository.get(application_id)
        if not application:
            raise ValueError(f"Application {application_id} not found")
        
        # Create state machine with current state
        state_machine = ApplicationStateMachine(application.status)
        
        # Validate and execute transition
        if not state_machine.can_transition(action):
            available = state_machine.get_available_actions()
            raise ValueError(
                f"Cannot {action} application in {application.status} state. "
                f"Available actions: {available}"
            )
        
        # Execute transition
        state_machine.transition(action)
        
        # Update application
        application.status = state_machine.state
        application.updatedAt = datetime.utcnow()
        
        # Set specific timestamps
        if state_machine.state == ApplicationState.REVIEWING:
            application.reviewedAt = application.updatedAt
        elif state_machine.state == ApplicationState.SUBMITTED and not application.submittedAt:
            application.submittedAt = application.updatedAt
        
        # Save changes
        application = await self.repository.update(application)
        
        # Handle completed state
        if state_machine.state == ApplicationState.COMPLETED:
            await self._handle_completion(application)
        
        return application
    
    async def _handle_completion(self, application: Application):
        """Handle application completion side effects"""
        # Award points to volunteer (event for recognition service)
        await self.event_publisher.publish(
            "points.award",
            {
                "volunteerId": application.volunteerId,
                "points": 100,
                "reason": f"Completed opportunity application {application.id}",
                "applicationId": application.id
            }
        )
        
        # Publish completion event
        await self.event_publisher.publish(
            "application.completed",
            {
                "applicationId": application.id,
                "volunteerId": application.volunteerId,
                "opportunityId": application.opportunityId,
                "completedAt": application.updatedAt.isoformat()
            }
        )
    
    async def get_application(self, application_id: str) -> Optional[Application]:
        """Get application by ID"""
        return await self.repository.get(application_id)
    
    async def get_volunteer_applications(self, volunteer_id: str) -> List[Application]:
        """Get all applications for a volunteer"""
        return await self.repository.find_by_volunteer(volunteer_id)
    
    async def get_opportunity_applications(self, opportunity_id: str) -> List[Application]:
        """Get all applications for an opportunity"""
        return await self.repository.find_by_opportunity(opportunity_id)