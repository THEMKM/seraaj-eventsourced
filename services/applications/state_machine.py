"""
Application state machine using transitions library
Implements: draft → submitted → reviewing → accepted → completed|rejected|cancelled
"""
from enum import Enum
from typing import List, Optional


class ApplicationState(str, Enum):
    """Application states"""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    REVIEWING = "reviewing"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

    def to_external_status(self) -> str:
        """Map internal state to external contract value"""
        mapping = {
            ApplicationState.DRAFT: "pending",
            ApplicationState.SUBMITTED: "pending",
            ApplicationState.REVIEWING: "pending",
            ApplicationState.ACCEPTED: "approved",
            ApplicationState.REJECTED: "rejected",
            ApplicationState.COMPLETED: "approved",
            ApplicationState.CANCELLED: "withdrawn",
        }
        return mapping[self]

    @classmethod
    def from_external_status(cls, external_status: str) -> 'ApplicationState':
        """Map external contract value to internal state"""
        mapping = {
            "pending": cls.SUBMITTED,
            "approved": cls.ACCEPTED,
            "rejected": cls.REJECTED,
            "withdrawn": cls.CANCELLED,
        }
        return mapping.get(str(external_status).lower(), cls.SUBMITTED)


class ApplicationStateMachine:
    """State machine for application lifecycle"""
    
    def __init__(self, initial_state: str = ApplicationState.DRAFT):
        self.state = ApplicationState(initial_state)
        
        # Define valid transitions
        self._transitions = {
            ApplicationState.DRAFT: [ApplicationState.SUBMITTED, ApplicationState.CANCELLED],
            ApplicationState.SUBMITTED: [ApplicationState.REVIEWING, ApplicationState.CANCELLED],
            ApplicationState.REVIEWING: [ApplicationState.ACCEPTED, ApplicationState.REJECTED],
            ApplicationState.ACCEPTED: [ApplicationState.COMPLETED, ApplicationState.CANCELLED],
            ApplicationState.REJECTED: [],  # Terminal state
            ApplicationState.COMPLETED: [],  # Terminal state
            ApplicationState.CANCELLED: []  # Terminal state
        }
    
    def can_transition(self, action: str) -> bool:
        """Check if a transition is valid from current state"""
        target_state = self._action_to_state(action)
        if not target_state:
            return False
        
        return target_state in self._transitions.get(self.state, [])
    
    def transition(self, action: str) -> bool:
        """Execute a state transition"""
        target_state = self._action_to_state(action)
        
        if not target_state:
            raise ValueError(f"Unknown action: {action}")
        
        if not self.can_transition(action):
            valid_actions = self.get_available_actions()
            raise ValueError(
                f"Cannot {action} application in {self.state} state. "
                f"Valid actions: {valid_actions}"
            )
        
        old_state = self.state
        self.state = target_state
        print(f"[STATE] State transition: {old_state} -> {self.state} (action: {action})")
        return True
    
    def get_available_actions(self) -> List[str]:
        """Get list of actions available from current state"""
        available_states = self._transitions.get(self.state, [])
        return [self._state_to_action(state) for state in available_states if state]
    
    def _action_to_state(self, action: str) -> Optional[ApplicationState]:
        """Map action to target state"""
        action_mapping = {
            "submit": ApplicationState.SUBMITTED,
            "review": ApplicationState.REVIEWING,
            "accept": ApplicationState.ACCEPTED,
            "reject": ApplicationState.REJECTED,
            "complete": ApplicationState.COMPLETED,
            "cancel": ApplicationState.CANCELLED
        }
        return action_mapping.get(action)
    
    def _state_to_action(self, state: ApplicationState) -> str:
        """Map state to action that leads to it"""
        state_mapping = {
            ApplicationState.SUBMITTED: "submit",
            ApplicationState.REVIEWING: "review",
            ApplicationState.ACCEPTED: "accept",
            ApplicationState.REJECTED: "reject",
            ApplicationState.COMPLETED: "complete",
            ApplicationState.CANCELLED: "cancel"
        }
        return state_mapping.get(state, "unknown")
    
    def is_terminal(self) -> bool:
        """Check if current state is terminal"""
        terminal_states = [
            ApplicationState.REJECTED,
            ApplicationState.COMPLETED,
            ApplicationState.CANCELLED
        ]
        return self.state in terminal_states
