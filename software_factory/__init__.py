"""
Software Factory Framework
Universal autonomous software development loop for Jira, Linear, and multi-LLM engines.
"""

from .roster import RosterManager, AgentRoleSpec
from .logger import AgentInvocationLogger, InvocationLogEntry

__version__ = "0.1.0"
__all__ = ["RosterManager", "AgentRoleSpec", "AgentInvocationLogger", "InvocationLogEntry"]
