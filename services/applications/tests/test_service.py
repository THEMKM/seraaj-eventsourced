"""
Tests for Application service
"""
import os
import tempfile
import shutil
import pytest
from datetime import datetime
from uuid import uuid4

from services.applications.service import ApplicationService, SubmitApplicationCommand
from services.applications.state_machine import ApplicationState


@pytest.fixture
def temp_data_dir():
    """Create a temporary data directory for tests"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def service(temp_data_dir):
    """Create ApplicationService with temporary data directory"""
    return ApplicationService(data_dir=temp_data_dir)


@pytest.mark.asyncio
async def test_submit_application(service):
    """Test application submission"""
    volunteer_id = str(uuid4())
    opportunity_id = str(uuid4())
    
    command = SubmitApplicationCommand(
        volunteer_id=volunteer_id,
        opportunity_id=opportunity_id,
        cover_letter="I'm excited to help with this opportunity!"
    )
    
    application = await service.submit_application(command)
    
    # Verify application properties
    assert application.id is not None
    assert application.volunteerId == volunteer_id
    assert application.opportunityId == opportunity_id
    assert application.status == ApplicationState.SUBMITTED
    assert application.coverLetter == "I'm excited to help with this opportunity!"
    assert application.createdAt is not None
    assert application.updatedAt is not None
    assert application.submittedAt is not None


@pytest.mark.asyncio
async def test_submit_application_validation(service):
    """Test application submission validation"""
    
    # Test missing volunteer ID
    with pytest.raises(ValueError, match="Volunteer ID is required"):
        command = SubmitApplicationCommand(
            volunteer_id="",
            opportunity_id=str(uuid4())
        )
        await service.submit_application(command)
    
    # Test missing opportunity ID
    with pytest.raises(ValueError, match="Opportunity ID is required"):
        command = SubmitApplicationCommand(
            volunteer_id=str(uuid4()),
            opportunity_id=""
        )
        await service.submit_application(command)


@pytest.mark.asyncio
async def test_duplicate_application_prevention(service):
    """Test that duplicate applications are prevented"""
    volunteer_id = str(uuid4())
    opportunity_id = str(uuid4())
    
    # Submit first application
    command = SubmitApplicationCommand(
        volunteer_id=volunteer_id,
        opportunity_id=opportunity_id
    )
    await service.submit_application(command)
    
    # Try to submit duplicate
    with pytest.raises(ValueError, match="Application already exists"):
        await service.submit_application(command)


@pytest.mark.asyncio
async def test_application_state_transitions(service):
    """Test state machine transitions"""
    volunteer_id = str(uuid4())
    opportunity_id = str(uuid4())
    
    # Submit application
    command = SubmitApplicationCommand(
        volunteer_id=volunteer_id,
        opportunity_id=opportunity_id
    )
    application = await service.submit_application(command)
    
    # Verify initial state
    assert application.status == ApplicationState.SUBMITTED
    
    # Transition to reviewing
    application = await service.update_application_state(application.id, "review")
    assert application.status == ApplicationState.REVIEWING
    assert application.reviewedAt is not None
    
    # Transition to accepted
    application = await service.update_application_state(application.id, "accept")
    assert application.status == ApplicationState.ACCEPTED
    
    # Transition to completed
    application = await service.update_application_state(application.id, "complete")
    assert application.status == ApplicationState.COMPLETED


@pytest.mark.asyncio
async def test_invalid_state_transition(service):
    """Test that invalid transitions are rejected"""
    volunteer_id = str(uuid4())
    opportunity_id = str(uuid4())
    
    # Submit application
    command = SubmitApplicationCommand(
        volunteer_id=volunteer_id,
        opportunity_id=opportunity_id
    )
    application = await service.submit_application(command)
    
    # Try invalid transition (submitted -> completed)
    with pytest.raises(ValueError, match="Cannot complete application in submitted state"):
        await service.update_application_state(application.id, "complete")


@pytest.mark.asyncio
async def test_get_application(service):
    """Test retrieving application by ID"""
    volunteer_id = str(uuid4())
    opportunity_id = str(uuid4())
    
    # Submit application
    command = SubmitApplicationCommand(
        volunteer_id=volunteer_id,
        opportunity_id=opportunity_id,
        cover_letter="Test cover letter"
    )
    original_app = await service.submit_application(command)
    
    # Retrieve application
    retrieved_app = await service.get_application(original_app.id)
    
    assert retrieved_app is not None
    assert retrieved_app.id == original_app.id
    assert retrieved_app.volunteerId == volunteer_id
    assert retrieved_app.opportunityId == opportunity_id
    assert retrieved_app.coverLetter == "Test cover letter"


@pytest.mark.asyncio
async def test_get_nonexistent_application(service):
    """Test retrieving non-existent application"""
    fake_id = str(uuid4())
    application = await service.get_application(fake_id)
    assert application is None


@pytest.mark.asyncio
async def test_get_volunteer_applications(service):
    """Test retrieving applications by volunteer"""
    volunteer_id = str(uuid4())
    
    # Submit multiple applications
    for i in range(3):
        command = SubmitApplicationCommand(
            volunteer_id=volunteer_id,
            opportunity_id=str(uuid4()),
            cover_letter=f"Application {i}"
        )
        await service.submit_application(command)
    
    # Retrieve volunteer applications
    applications = await service.get_volunteer_applications(volunteer_id)
    
    assert len(applications) == 3
    for app in applications:
        assert app.volunteerId == volunteer_id


@pytest.mark.asyncio
async def test_state_machine_rejection_path(service):
    """Test rejection path in state machine"""
    volunteer_id = str(uuid4())
    opportunity_id = str(uuid4())
    
    # Submit and move to reviewing
    command = SubmitApplicationCommand(volunteer_id=volunteer_id, opportunity_id=opportunity_id)
    application = await service.submit_application(command)
    application = await service.update_application_state(application.id, "review")
    
    # Reject application
    application = await service.update_application_state(application.id, "reject", "Not a good fit")
    assert application.status == ApplicationState.REJECTED
    
    # Verify no further transitions are possible (terminal state)
    with pytest.raises(ValueError):
        await service.update_application_state(application.id, "accept")


@pytest.mark.asyncio
async def test_state_machine_cancellation(service):
    """Test cancellation from various states"""
    volunteer_id = str(uuid4())
    opportunity_id = str(uuid4())
    
    # Test cancellation from submitted state
    command = SubmitApplicationCommand(volunteer_id=volunteer_id, opportunity_id=opportunity_id)
    application = await service.submit_application(command)
    
    application = await service.update_application_state(application.id, "cancel")
    assert application.status == ApplicationState.CANCELLED