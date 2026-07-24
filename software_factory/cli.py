"""
Command Line Interface for Software Factory (`factory-loop`).
"""

import sys
import argparse
import yaml
from .controller import FactoryController
from .spec_parser import parse_ticket_spec


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
"""
    with open("factory.yaml", "w", encoding="utf-8") as f:
        f.write(sample_yaml)
    print("Initialized new 'factory.yaml' configuration file.")


def main():
    parser = argparse.ArgumentParser(description="Software Factory Loop Controller (`factory-loop`)")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # `start` command
    start_parser = subparsers.add_parser("start", help="Start the factory execution loop")
    start_parser.add_argument("--single-cycle", action="store_true", help="Run a single cycle then exit")
    start_parser.add_argument("--config", default="factory.yaml", help="Path to config file")

    # `init` command
    subparsers.add_parser("init", help="Scaffold factory.yaml in current directory")

    # `validate-spec` command
    val_parser = subparsers.add_parser("validate-spec", help="Validate a 5-Part Ticket Spec Markdown file")
    val_parser.add_argument("file", help="Path to Markdown ticket file")

    args = parser.parse_args()

    if args.command == "init":
        init_config()
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
            print(f"Engine: {res.engine_name} ({res.model_used}) | Duration: {res.duration_seconds}s")
            if res.stderr:
                print(f"Stderr output:\n{res.stderr}")
        except Exception as e:
            print(f"Error executing factory loop: {e}")
            sys.exit(1)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
