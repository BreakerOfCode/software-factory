"""
Tests for 5-Part Ticket Spec Parser (Markdown and FrontMatter).
"""

import pytest
from software_factory.spec_parser import parse_ticket_spec, TicketSpec


def test_parse_markdown_headings():
    raw_desc = """
## Goal
Implement secure authentication tokens for user sessions.

## Target Files
- `src/auth.py`
- `tests/test_auth.py`

## Interface Contract
```python
def generate_token(user_id: str) -> str:
    ...
```

## Requirements
1. Use HMAC-SHA256 signing.
2. Expire tokens after 3600 seconds.

## Definition of Done
- [ ] Code implemented in src/auth.py
- [ ] Unit tests passing in tests/test_auth.py
"""
    spec = parse_ticket_spec("JIRA-101", "Auth Tokens", raw_desc)
    assert spec.ticket_id == "JIRA-101"
    assert spec.goal == "Implement secure authentication tokens for user sessions."
    assert "src/auth.py" in spec.target_files
    assert "tests/test_auth.py" in spec.target_files
    assert len(spec.requirements) == 2
    assert len(spec.definition_of_done) == 2


def test_parse_frontmatter_spec():
    raw_desc = """---
goal: Build user avatar component
target_files:
  - src/components/Avatar.tsx
requirements:
  - Support size prop (sm, md, lg)
definition_of_done:
  - Component rendered cleanly
---

Additional Markdown documentation text here...
"""
    spec = parse_ticket_spec("JIRA-102", "Avatar Component", raw_desc)
    assert spec.ticket_id == "JIRA-102"
    assert spec.goal == "Build user avatar component"
    assert spec.target_files == ["src/components/Avatar.tsx"]
    assert len(spec.requirements) == 1


def test_empty_target_files_raises_validation_error():
    invalid_desc = """
## Goal
Refactor entire project

## Target Files

## Requirements
1. Do stuff
"""
    with pytest.raises(ValueError, match="Target Files list cannot be empty or missing"):
        parse_ticket_spec("JIRA-999", "Invalid Ticket", invalid_desc)


def test_to_handoff_markdown():
    spec = TicketSpec(
        ticket_id="EMB-50",
        title="Refactor Pipeline",
        goal="Extract pipeline logic",
        target_files=["software_factory/pipeline.py"],
        requirements=["Must be modular"],
        definition_of_done=["Tests pass"]
    )
    handoff_md = spec.to_handoff_markdown(test_baseline="PASS (10 passed)", lint_baseline="PASS (clean)")
    assert "# Active Spec Handoff: [EMB-50] Refactor Pipeline" in handoff_md
    assert "software_factory/pipeline.py" in handoff_md
    assert "PASS (10 passed)" in handoff_md
    assert "PASS (clean)" in handoff_md

