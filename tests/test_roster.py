"""
Unit tests for RosterManager and Agent Council functionality.
"""

import os
import tempfile
import pytest
from software_factory.roster import RosterManager, AgentRoleSpec


def test_default_generic_roles():
    rm = RosterManager({})
    assert "software-engineer" in rm.roles
    assert "qa-test-engineer" in rm.roles
    assert "scope-gate" in rm.roles
    assert "project-architect" in rm.roles

    qa_role = rm.get_role("qa-test-engineer")
    assert qa_role is not None
    assert qa_role.mandatory is True

    scope_role = rm.get_role("scope-gate")
    assert scope_role is not None
    assert scope_role.model == "opus"
    assert scope_role.mandatory is True


def test_custom_roster_config():
    config = {
        "roster": {
            "qa-test-engineer": {
                "model": "haiku",
                "description": "Fast QA runner",
                "mandatory": True
            },
            "security-auditor": {
                "model": "opus",
                "description": "Security audit gate",
                "mandatory": False
            }
        }
    }
    rm = RosterManager(config)

    qa_role = rm.get_role("qa-test-engineer")
    assert qa_role.model == "haiku"
    assert qa_role.description == "Fast QA runner"

    sec_role = rm.get_role("security-auditor")
    assert sec_role is not None
    assert sec_role.model == "opus"
    assert sec_role.description == "Security audit gate"


def test_sync_claude_agents():
    with tempfile.TemporaryDirectory() as tmpdir:
        rm = RosterManager({})
        created_files = rm.sync_claude_agents(tmpdir)
        assert len(created_files) >= 4

        se_path = os.path.join(tmpdir, ".claude", "agents", "software-engineer.md")
        assert os.path.exists(se_path)

        with open(se_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "name: software-engineer" in content
        assert "model: sonnet" in content


def test_render_council_table():
    rm = RosterManager({})
    table_md = rm.render_council_table()
    assert "## Agent Council Roster" in table_md
    assert "| **software-engineer** | `sonnet` |" in table_md
    assert "| **scope-gate** | `opus` | **MANDATORY GATE** |" in table_md
