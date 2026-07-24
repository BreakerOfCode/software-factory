---
name: software-factory-setup
description: Auto-discovers codebase language, test framework, linters, and git branch configuration to auto-generate a tailored factory.yaml file.
---

# Software Factory Setup Skill (`/factory-init`)

This skill allows an AI agent to inspect any repository workspace, detect its environment, and automatically generate a verified `factory.yaml` configuration for running the Software Factory loop.

## Workflow

### 1. Workspace Inspection

The agent inspects the root workspace directory for project manifests:

| File Pattern | Environment Detected | Default Test Command | Default Lint Command |
| :--- | :--- | :--- | :--- |
| `pyproject.toml`, `requirements.txt` | Python | `python3 -m pytest` | `python3 -m ruff check .` |
| `package.json` | Node.js / TypeScript | `npm test` | `npm run lint` |
| `Cargo.toml` | Rust | `cargo test` | `cargo clippy` |
| `go.mod` | Go | `go test ./...` | `golangci-lint run` |
| `pom.xml`, `build.gradle` | Java / Kotlin | `./mvnw test` / `./gradlew test` | `./mvnw spotbugs:check` |

### 2. Git Branch Discovery

Run `git branch -a` or inspect `.git/config` to check default branch names:
- Base branch: `main` or `master`
- Integration branch: `staging` or `dev` (if absent, recommends creating `staging`)

### 3. Issue Tracker Setup

Inspect git commit history or environment variables for issue prefixes (e.g. `JIRA-`, `ENG-`, `PROD-`). Prompt the user for:
- Tracker Type: `jira` (default) | `linear` | `local_md`
- Project Key (e.g., `ENG`, `PROD`)

### 4. Config Emission

Generate `factory.yaml` in the repo root using the discovered parameters:

```yaml
project:
  name: "<detected-repo-name>"
  base_branch: "<detected-main-branch>"
  integration_branch: "staging"
  ticket_branch_prefix: "jira-"

issue_tracker:
  type: "jira"
  project_key: "<PROJECT_KEY>"
  auth_email_env: "JIRA_EMAIL"
  auth_token_env: "JIRA_API_TOKEN"
  domain_env: "JIRA_DOMAIN"

engine:
  primary: "claude"
  fallback: "codex"
  permission_mode: "bypassPermissions"
  primary_model: "sonnet"

gates:
  test_command: "<detected-test-command>"
  lint_command: "<detected-lint-command>"
```
