# Universal Software Factory Framework 🚀

> An autonomous, session-boundary-spanning software development factory for individual engineers. Decouples software architecture & micro-speccing from code execution by using **Jira / Linear** as a durable contract bus and **Claude Code / Codex** as async software factory engines.

---

## Key Features

- 🎯 **Multi-Tracker Support**: Native adapters for **Jira Cloud** (JQL queries, Markdown/ADF parsing), **Linear** (GraphQL API), and **Local Markdown** files.
- 🤖 **Multi-Engine CLI Runners**: **Claude Code CLI** as primary execution engine, with **OpenAI Codex CLI** as an automatic failover runner.
- 👥 **Agent Council Roster**: Per-cycle agent council creation with configurable models per role (`sonnet`, `opus`, `haiku`). Pre-loaded with generic, repo-agnostic default roles (`software-engineer`, `qa-test-engineer`, `scope-gate`, `project-architect`).
- 📊 **Structured Invocation Telemetry**: Every agent invocation step is logged to `.factory/logs/invocations.jsonl` carrying timestamp, role, model, duration, and status.
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
                  │  (Engine, Gates, Agent Council Roster)   │
                  └────────────────────┬─────────────────────┘
                                       │
                                       ▼
                  ┌──────────────────────────────────────────┐
                  │      factory-loop Controller CLI         │
                  │   (Cycle Runner, Council Sync, Logger)   │
                  └──────┬───────────────────┬───────────────┘
                         │                   │
      ┌──────────────────┴──┐             ┌──┴──────────────────┐
      │  Issue Tracker      │             │  Multi-Engine &     │
      │  Adapter Layer      │             │  Agent Council      │
      └──────────┬──────────┘             └──────────┬──────────┘
                 │                                   │
      ┌──────────┴──────────┐             ┌──────────┴──────────┐
      │ - JiraAdapter       │             │ - ClaudeEngine      │
      │   (Markdown/YAML)   │             │   (Subagent Sync)   │
      │ - LinearAdapter     │             │ - CodexEngine       │
      │ - LocalMdAdapter    │             │ - InvocationLogger  │
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

This creates a `factory.yaml` in your project root with the Agent Council roster settings:

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
  project-architect:
    model: "opus"
    description: "Architect — module layout & interface structure"
```

---

## Agent Council & Telemetry

### Generic Repository Roles
The factory automatically provisions subagent definitions (`.claude/agents/*.md`) for generic repo roles:
1. `software-engineer` (`sonnet`): Core code executor operating inside the target files fence.
2. `qa-test-engineer` (`sonnet` / `haiku` - **Mandatory**): Evaluates test runner and linter output to assert Definition of Done.
3. `scope-gate` (`opus` - **Mandatory**): Scope-acceptance gate auditing `git diff` boundaries before PR creation.
4. `project-architect` (`opus`): Structural and module design reviewer.

### Agent Invocation Logging & Commands
- **Sync Council Manifests**: `factory-loop sync-roster` (syncs `.claude/agents/*.md` definitions).
- **View Invocation Logs**: `factory-loop logs` (displays recent agent executions with input/output/total tokens and cost from `.factory/logs/invocations.jsonl`).
- **View Cost & Token Metrics**: `factory-loop metrics` (displays aggregated summary and per-cycle breakdown of token usage and USD costs).

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

# Sync agent roster manifests manually
factory-loop sync-roster

# View recent agent invocation logs with token/cost details
factory-loop logs

# View aggregate cost and token usage metrics across cycles
factory-loop metrics

# Validate a ticket spec file
factory-loop validate-spec path/to/ticket.md
```

---

## License

[MIT License](LICENSE)
