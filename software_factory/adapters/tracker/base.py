"""
Base abstract class for issue tracker adapters.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from ...spec_parser import TicketSpec


class BaseTrackerAdapter(ABC):
    """Abstract interface that all issue tracker adapters must implement."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    @abstractmethod
    def get_active_ticket(self) -> Optional[TicketSpec]:
        """Returns the currently in-progress ticket spec, or None if idle."""
        pass

    @abstractmethod
    def get_next_todo_ticket(self) -> Optional[TicketSpec]:
        """Returns the top unblocked 'To Do' ticket spec from the tracker backlog."""
        pass

    @abstractmethod
    def update_ticket_status(self, ticket_id: str, status: str) -> bool:
        """Transitions ticket status (e.g. 'In Progress', 'In Review', 'Done')."""
        pass

    @abstractmethod
    def post_pr_link(self, ticket_id: str, pr_url: str, comment: Optional[str] = None) -> bool:
        """Attaches a pull request URL or progress comment to the ticket."""
        pass
