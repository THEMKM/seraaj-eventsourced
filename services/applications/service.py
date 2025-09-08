"""
Application domain service implementing business logic
"""
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from services.shared.models import Application, ApplicationStatus
from .repository import ApplicationRepository
from .state_machine import ApplicationStateMachine, ApplicationState
from .events import EventPublisher


class SubmitApplicationCommand:
    """Command for submitting an application (supports camelCase and snake_case)"""
    def __init__(
        self,
        volunteerId: Optional[str] = None,
        opportunityId: Optional[str] = None,
        coverLetter: Optional[str] = None,
        # Backward-compatible snake_case parameters used in tests
        volunteer_id: Optional[str] = None,
        opportunity_id: Optional[str] = None,
        cover_letter: Optional[str] = None,
    ):
        self.volunteerId = volunteerId or volunteer_id  # type: ignore[assignment]
        self.opportunityId = opportunityId or opportunity_id  # type: ignore[assignment]
        self.coverLetter = coverLetter if coverLetter is not None else cover_letter


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
                app.status not in [ApplicationStatus.rejected, ApplicationStatus.cancelled, ApplicationStatus.completed]):
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
        old_state = state_machine.state
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

        # Publish state changed event
        try:
            await self.event_publisher.publish_application_state_changed(
                application_id=application.id,
                old_state=old_state.value if hasattr(old_state, 'value') else str(old_state),
                new_state=state_machine.state.value if hasattr(state_machine.state, 'value') else str(state_machine.state),
                details={"action": action, "reason": reason} if reason else {"action": action}
            )
        except Exception:
            # Non-fatal for business flow; log and continue
            print(f"[WARN] Failed to publish state changed event for {application.id}")
        
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
    
    async def get_organization_stats(self, organization_id: str) -> dict:
        """Get application statistics for an organization"""
        return await self.repository.get_organization_stats(organization_id)
