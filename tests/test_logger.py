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


def test_upsert_ticket_cost_ledger():
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = AgentInvocationLogger(tmpdir)
        
        # Initial cycle for ticket ENG-100 ($2.10)
        e1 = logger.upsert_ticket_cost_ledger("ENG-100", cost_usd=2.1034, branch="jira-eng-100")
        assert e1["ticket_id"] == "ENG-100"
        assert e1["total_cost_usd"] == 2.10
        assert e1["cycles_count"] == 1
        assert e1["branch"] == "jira-eng-100"
        assert e1["pr_number"] is None

        # Second cycle for ticket ENG-100 ($1.40 + PR #15)
        e2 = logger.upsert_ticket_cost_ledger("ENG-100", cost_usd=1.4012, branch="jira-eng-100", pr_number=15)
        assert e2["ticket_id"] == "ENG-100"
        assert e2["total_cost_usd"] == 3.50  # 2.10 + 1.40
        assert e2["cycles_count"] == 2
        assert e2["pr_number"] == 15

        # Check ledger file persistence
        assert os.path.exists(logger.ledger_file)

