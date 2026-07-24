"""
Tests for FactoryController with Agent Council and Telemetry Logger integration.
"""

import os
from software_factory.controller import FactoryController
from software_factory.spec_parser import TicketSpec


def test_controller_render_prompt(tmp_path):
    config_file = tmp_path / "factory.yaml"
    config_file.write_text("""
project:
  name: "test-app"
  base_branch: "main"
  integration_branch: "staging"
  ticket_branch_prefix: "jira-"

issue_tracker:
  type: "local_md"

engine:
  primary: "claude"
  fallback: "codex"

gates:
  test_command: "pytest"
  lint_command: "ruff check ."

roster:
  software-engineer:
    model: "sonnet"
    description: "Executor — writes code inside Target-Files fence"
  qa-test-engineer:
    model: "sonnet"
    description: "QA Gate — runs test & lint commands"
    mandatory: true
  scope-gate:
    model: "opus"
    description: "Scope Acceptance Gate — verifies diff vs Target-Files"
    mandatory: true
""")

    controller = FactoryController(config_path=str(config_file), project_dir=str(tmp_path))
    ticket = TicketSpec(
        ticket_id="ENG-1",
        title="Sample Ticket",
        goal="Test goal description",
        target_files=["src/main.py"],
        requirements=["Req 1"],
        definition_of_done=["Done 1"]
    )
    prompt = controller.render_prompt(ticket)
    assert "[ENG-1] Sample Ticket" in prompt
    assert "src/main.py" in prompt
    assert "pytest" in prompt
    assert "jira-eng-1" in prompt
    assert "## Agent Council Roster" in prompt
    assert "| **software-engineer** | `sonnet` |" in prompt
    assert "| **scope-gate** | `opus` | **MANDATORY GATE** |" in prompt


def test_controller_roster_sync_and_logging(tmp_path):
    config_file = tmp_path / "factory.yaml"
    config_file.write_text("""
project:
  name: "test-app"

issue_tracker:
  type: "local_md"

engine:
  primary: "none"
  fallback: "none"
""")

    controller = FactoryController(config_path=str(config_file), project_dir=str(tmp_path))
    res = controller.run_single_cycle()

    # Subagent manifests generated
    se_manifest = tmp_path / ".claude" / "agents" / "software-engineer.md"
    assert se_manifest.exists()
