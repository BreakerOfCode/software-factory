"""
Tests for Jira Adapter & Local Markdown Adapter.
"""

import os
from software_factory.adapters.tracker.jira import JiraAdapter
from software_factory.adapters.tracker.local_md import LocalMdAdapter


def test_jira_adapter_unconfigured_fallback():
    config = {
        "issue_tracker": {
            "type": "jira",
            "project_key": "TEST",
            "domain_env": "NONEXISTENT_JIRA_DOMAIN"
        }
    }
    adapter = JiraAdapter(config)
    assert adapter.get_active_ticket() is None
    assert adapter.get_next_todo_ticket() is None


def test_local_md_adapter(tmp_path):
    backlog_dir = tmp_path / ".factory" / "backlog"
    todo_dir = backlog_dir / "todo"
    todo_dir.mkdir(parents=True)

    sample_ticket = todo_dir / "test-1.md"
    sample_ticket.write_text("""
## Goal
Local test goal

## Target Files
- `src/sample.py`
""")

    config = {
        "issue_tracker": {
            "type": "local_md",
            "backlog_dir": str(backlog_dir)
        }
    }
    adapter = LocalMdAdapter(config)
    ticket = adapter.get_next_todo_ticket()
    assert ticket is not None
    assert ticket.ticket_id == "TEST-1"
    assert ticket.target_files == ["src/sample.py"]
