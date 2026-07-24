# Universal Software Factory Framework 🚀

> An autonomous, session-boundary-spanning software development factory for individual engineers. Decouples software architecture & micro-speccing from code execution by using **Jira / Linear** as a durable contract bus and **Claude Code / Codex** as async software factory engines.

---

## Key Features

- 🎯 **Multi-Tracker Support**: Native adapters for **Jira Cloud** (JQL queries, Markdown/ADF parsing), **Linear** (GraphQL API), and **Local Markdown** files.
- 🤖 **Multi-Engine CLI Runners**: **Claude Code CLI** as primary execution engine, with **OpenAI Codex CLI** as an automatic failover runner.
- 🛡️ **Scope Fence Enforcement**: Strict file-level fences (`Target Files`). Cycles fail if changes drift outside declared boundaries.
- 📋 **5-Part Ticket Spec Rules**: Standardized spec structure (Goal, Target Files, Interface Contract, Requirements, Definition of Done).
- 🌿 **Clean Branching Strategy**: Pristine `main` branch, long-running `staging` integration branch, and isolated `jira-KEY-<slug>` feature branches.
- 🧠 **Auto-Discovery Skill (`/factory-init`)**: Agent skill that inspects any codebase to auto-detect language, test runners (`pytest`, `npm test`, `cargo test`), linters, and branch strategy to generate `factory.yaml`.

---

## Architecture

```
                  ┌──────────────────────────────────────────┐
                  │    /factory-init Agent Skill             │
                  │   (Auto-detects repo test/lint/branches) │
                  └────────────────────┬─────────────────────┘
                                       │
                                       ▼
                  ┌──────────────────────────────────────────┐
                  │      per-repo factory.yaml Config        │
                  └────────────────────┬─────────────────────┘
                                       │
                                       ▼
                  ┌──────────────────────────────────────────┐
                  │      factory-loop Controller CLI         │
                  │   (Cycle Runner, Locks, Circuit-Breaker) │
                  └──────┬───────────────────┬───────────────┘
                         │                   │
      ┌──────────────────┴──┐             ┌──┴──────────────────┐
      │  Issue Tracker      │             │  Multi-Engine       │
      │  Adapter Layer      │             │  CLI Runner Layer   │
      └──────────┬──────────┘             └──────────┬──────────┘
                 │                                   │
      ┌──────────┴──────────┐             ┌──────────┴──────────┐
      │ - JiraAdapter       │             │ - ClaudeEngine      │
      │   (Markdown/YAML)   │             │   (Primary)         │
      │ - LinearAdapter     │             │ - CodexEngine       │
      │ - LocalMdAdapter    │             │   (Fallback)        │
      └─────────────────────┘             └─────────────────────┘
```

---

## Quickstart

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/your-username/software-factory.git
cd software-factory

# Install in editable mode
pip install -e .
```

### 2. Configure a Project

Navigate to any codebase repository where you want to run the factory, and run:

```bash
factory-loop init
```

This creates a `factory.yaml` in your project root:

```yaml
project:
  name: "my-service"
  base_branch: "main"
  integration_branch: "staging"
  ticket_branch_prefix: "jira-"

issue_tracker:
  type: "jira"
  project_key: "ENG"
  auth_email_env: "JIRA_EMAIL"
  auth_token_env: "JIRA_API_TOKEN"
  domain_env: "JIRA_DOMAIN"

engine:
  primary: "claude"
  fallback: "codex"
  permission_mode: "bypassPermissions"
  primary_model: "sonnet"

gates:
  test_command: "python3 -m pytest"
  lint_command: "python3 -m ruff check ."
```

Alternatively, invoke the `/factory-init` skill in Claude Code or your agent environment to auto-detect your project's configuration!

---

## Authoring 5-Part Ticket Specs

In Jira or Linear, format issue descriptions using standard Markdown or YAML FrontMatter:

```markdown
## Goal
Implement JWT authentication middleware for internal API routes.

## Target Files
- `src/middleware/auth.py`
- `tests/test_auth_middleware.py`

## Interface Contract
```python
def authenticate_request(headers: Dict[str, str]) -> AuthContext:
    ...
```

## Requirements
1. Extract Bearer token from `Authorization` header.
2. Validate signature against `JWT_SECRET`.
3. Return 401 Unauthorized on invalid or expired token.

## Definition of Done
- [ ] Logic implemented in `src/middleware/auth.py`
- [ ] `pytest tests/test_auth_middleware.py` passes cleanly
- [ ] Zero linting errors via `ruff`
```

---

## Running the Factory

```bash
# Run a single cycle (great for testing)
factory-loop start --single-cycle

# Validate a ticket spec file
factory-loop validate-spec path/to/ticket.md
```

---

## License

[MIT License](LICENSE)
