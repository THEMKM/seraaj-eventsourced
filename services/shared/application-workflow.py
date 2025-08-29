"""
Auto-generated state machine from application-workflow.json
Generated at: 2025-08-13T07:58:10.777370
"""
from transitions import Machine
from typing import Optional, Dict, Any

class ApplicationWorkflowStateMachine:
    def __init__(self):
        states = ['draft', 'submitted', 'reviewing', 'accepted', 'rejected', 'completed', 'cancelled']
        transitions = []
        
        # Define transitions from workflow
        workflow_states = {'draft': {'description': 'Application is being prepared', 'on': {'SUBMIT': {'target': 'submitted', 'guards': ['hasRequiredFields', 'volunteerIsActive', 'opportunityIsOpen'], 'actions': ['notifyOrganization', 'createSubmissionRecord']}}}, 'submitted': {'description': 'Application has been submitted and awaiting review', 'on': {'START_REVIEW': {'target': 'reviewing', 'actions': ['assignReviewer', 'notifyReviewer']}, 'AUTO_REJECT': {'target': 'rejected', 'guards': ['opportunityIsFull', 'volunteerNotEligible'], 'actions': ['notifyVolunteer', 'recordRejectionReason']}}}, 'reviewing': {'description': 'Application is under review by organization', 'on': {'ACCEPT': {'target': 'accepted', 'actions': ['notifyVolunteer', 'reserveSpot', 'createAcceptanceRecord']}, 'REJECT': {'target': 'rejected', 'actions': ['notifyVolunteer', 'recordRejectionReason']}}}, 'accepted': {'description': 'Application has been accepted', 'on': {'COMPLETE': {'target': 'completed', 'actions': ['awardPoints', 'generateCertificate', 'releaseSpot', 'recordCompletionHours']}, 'CANCEL': {'target': 'cancelled', 'actions': ['releaseSpot', 'notifyOrganization', 'recordCancellationReason']}}}, 'rejected': {'description': 'Application has been rejected', 'type': 'final', 'entry': ['recordFinalStatus']}, 'completed': {'description': 'Application has been completed successfully', 'type': 'final', 'entry': ['recordHours', 'checkBadgeEligibility', 'updateVolunteerStats']}, 'cancelled': {'description': 'Application has been cancelled', 'type': 'final', 'entry': ['recordCancellationStats']}}
        for state, config in workflow_states.items():
            for event, target in config.get("on", {}).items():
                if isinstance(target, str):
                    transitions.append({
                        "trigger": event.lower(),
                        "source": state,
                        "dest": target
                    })
                elif isinstance(target, dict):
                    transitions.append({
                        "trigger": event.lower(),
                        "source": state,
                        "dest": target.get("target"),
                        "conditions": target.get("guards", [])
                    })
        
        self.machine = Machine(
            model=self,
            states=states,
            transitions=transitions,
            initial="draft"
        )
