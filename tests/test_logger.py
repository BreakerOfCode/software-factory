"""
Unit tests for AgentInvocationLogger functionality.
"""

import os
import tempfile
import pytest
from software_factory.logger import AgentInvocationLogger


def test_agent_invocation_logging():
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = AgentInvocationLogger(tmpdir)
        
        entry = logger.log_invocation(
            cycle_id="cycle-001",
            ticket_id="ENG-123",
            agent_role="software-engineer",
            model="sonnet",
            engine="claude",
            status="SUCCESS",
            duration_seconds=12.5,
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            cost_usd=0.04
        )

        assert entry.cycle_id == "cycle-001"
        assert entry.ticket_id == "ENG-123"
        assert entry.agent_role == "software-engineer"
        assert entry.status == "SUCCESS"
        assert entry.input_tokens == 100
        assert entry.output_tokens == 50
        assert entry.total_tokens == 150

        logs = logger.read_recent_logs(limit=10)
        assert len(logs) == 1
        assert logs[0]["cycle_id"] == "cycle-001"
        assert logs[0]["ticket_id"] == "ENG-123"
        assert logs[0]["model"] == "sonnet"
        assert logs[0]["duration_seconds"] == 12.5
        assert logs[0]["input_tokens"] == 100
        assert logs[0]["output_tokens"] == 50
        assert logs[0]["total_tokens"] == 150
