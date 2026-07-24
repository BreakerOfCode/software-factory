"""
Tests for FactoryController.
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
