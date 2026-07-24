# 5-Part Ticket Spec Template for Jira / Linear / Markdown

Copy and paste this standard Markdown / FrontMatter structure into your Jira issue description or Linear issue.

```markdown
## Goal
[One line summary of what this component or feature does]

## Target Files
- `path/to/component.py`
- `tests/test_component.py`

## Interface Contract
```python
# Expected function signatures, Pydantic models, or API endpoints
def process_data(input_payload: Dict[str, Any]) -> ComponentOutput:
    ...
```

## Requirements
1. Requirement 1: [Behavioral constraint or logic requirement]
2. Requirement 2: [Fallback handling or validation rule]

## Definition of Done
- [ ] Code implemented in Target Files following codebase style
- [ ] Automated tests written and passing cleanly via `pytest` / `npm test`
- [ ] Zero linting or type check errors
```
