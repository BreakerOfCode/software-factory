"""
Command Line Interface for Software Factory (`factory-loop`).
"""

import sys
import argparse
import yaml
import json
from .controller import FactoryController
from .spec_parser import parse_ticket_spec
from .roster import RosterManager
from .logger import AgentInvocationLogger


def init_config():
    sample_yaml = """project:
  name: "my-app"
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
  project-architect:
    model: "opus"
    description: "Architect — module layout & interface structure"
"""
    with open("factory.yaml", "w", encoding="utf-8") as f:
        f.write(sample_yaml)
    print("Initialized new 'factory.yaml' configuration file with Agent Council roster settings.")


def main():
    parser = argparse.ArgumentParser(description="Software Factory Loop Controller (`factory-loop`)")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # `start` command
    start_parser = subparsers.add_parser("start", help="Start the factory execution loop")
    start_parser.add_argument("--single-cycle", action="store_true", help="Run a single cycle then exit")
    start_parser.add_argument("--config", default="factory.yaml", help="Path to config file")

    # `init` command
    subparsers.add_parser("init", help="Scaffold factory.yaml in current directory")

    # `sync-roster` command
    sync_parser = subparsers.add_parser("sync-roster", help="Sync .claude/agents/*.md subagent manifests")
    sync_parser.add_argument("--config", default="factory.yaml", help="Path to config file")

    # `logs` command
    logs_parser = subparsers.add_parser("logs", help="View recent agent invocation logs")
    logs_parser.add_argument("--limit", type=int, default=20, help="Number of log entries to display")

    # `metrics` command
    metrics_parser = subparsers.add_parser("metrics", help="View aggregated cost and token telemetry metrics")
    metrics_parser.add_argument("--limit", type=int, default=50, help="Number of cycle logs to include in breakdown")

    # `validate-spec` command
    val_parser = subparsers.add_parser("validate-spec", help="Validate a 5-Part Ticket Spec Markdown file")
    val_parser.add_argument("file", help="Path to Markdown ticket file")

    args = parser.parse_args()

    if args.command == "init":
        init_config()
        return

    if args.command == "sync-roster":
        try:
            with open(args.config, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
            rm = RosterManager(config)
            created = rm.sync_claude_agents(".")
            print(f"✅ Synced {len(created)} Agent Council manifest(s) in .claude/agents/:")
            for path in created:
                print(f"  - {path}")
        except Exception as e:
            print(f"❌ Failed to sync roster: {e}")
            sys.exit(1)
        return

    if args.command == "logs":
        logger = AgentInvocationLogger(".")
        logs = logger.read_recent_logs(limit=args.limit)
        if not logs:
            print("No invocation logs found in .factory/logs/invocations.jsonl.")
            return
        print(f"📋 Recent Agent Invocations (Last {len(logs)}):")
        for entry in logs:
            status_icon = "✅" if entry.get("status") == "SUCCESS" else "❌"
            in_tok = entry.get("input_tokens", 0)
            out_tok = entry.get("output_tokens", 0)
            tot_tok = entry.get("total_tokens", 0) or (in_tok + out_tok)
            cost = entry.get("cost_usd", 0.0)
            print(
                f"{status_icon} [{entry.get('timestamp')}] Cycle: {entry.get('cycle_id')} | Ticket: {entry.get('ticket_id')} | "
                f"Role: {entry.get('agent_role')} ({entry.get('model')}) | Engine: {entry.get('engine')} | "
                f"Duration: {entry.get('duration_seconds')}s | Tokens: {in_tok} in / {out_tok} out ({tot_tok} total) | Cost: ${cost:.6f}"
            )
        return

    if args.command == "metrics":
        logger = AgentInvocationLogger(".")
        summary = logger.get_metrics_summary()
        logs = logger.read_recent_logs(limit=args.limit)

        print("📊 Software Factory Cost & Token Metrics Summary")
        print("=" * 55)
        print(f"Total Cycles Recorded:    {summary['total_cycles']}")
        print(f"Total Execution Time:     {summary['total_duration_seconds']:.2f}s")
        print(f"Total Input Tokens:       {summary['total_input_tokens']:,}")
        print(f"Total Output Tokens:      {summary['total_output_tokens']:,}")
        print(f"Grand Total Tokens:       {summary['total_tokens']:,}")
        print(f"Total Estimated Cost:     ${summary['total_cost_usd']:.6f}")
        print(f"Average Cost / Cycle:     ${summary['avg_cost_per_cycle']:.6f}")
        print(f"Average Tokens / Cycle:   {summary['avg_tokens_per_cycle']:,.1f}")
        print("=" * 55)

        if logs:
            print(f"\nCycle-by-Cycle Telemetry Breakdown (Last {len(logs)}):")
            for entry in logs:
                in_t = entry.get("input_tokens", 0)
                out_t = entry.get("output_tokens", 0)
                tot_t = entry.get("total_tokens", 0) or (in_t + out_t)
                c_usd = entry.get("cost_usd", 0.0)
                print(
                    f" - Cycle: {entry.get('cycle_id')} | Ticket: {entry.get('ticket_id')} | "
                    f"Model: {entry.get('model')} ({entry.get('engine')}) | "
                    f"Tokens: {tot_t:,} ({in_t:,} in / {out_t:,} out) | Cost: ${c_usd:.6f}"
                )
        return

    if args.command == "validate-spec":
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                content = f.read()
            spec = parse_ticket_spec("VALIDATE", "Ticket Validation", content)
            print("✅ Ticket Spec is VALID:")
            print(f"  Goal: {spec.goal}")
            print(f"  Target Files: {spec.target_files}")
            print(f"  Requirements: {len(spec.requirements)} item(s)")
            print(f"  Definition of Done: {len(spec.definition_of_done)} item(s)")
        except Exception as e:
            print(f"❌ Spec Validation Failed: {e}")
            sys.exit(1)
        return

    if args.command == "start":
        try:
            controller = FactoryController(config_path=args.config)
            print(f"🚀 Starting Software Factory for '{controller.config.get('project', {}).get('name')}'")
            res = controller.run_single_cycle()
            print(f"Cycle finished with status: {'SUCCESS' if res.success else 'FAILED'}")
            print(
                f"Engine: {res.engine_name} ({res.model_used}) | Duration: {res.duration_seconds}s | "
                f"Tokens: {res.input_tokens} in / {res.output_tokens} out ({res.total_tokens} total) | Cost: ${res.cost_usd:.6f}"
            )
            if res.stderr:
                print(f"Stderr output:\n{res.stderr}")
        except Exception as e:
            print(f"Error executing factory loop: {e}")
            sys.exit(1)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
