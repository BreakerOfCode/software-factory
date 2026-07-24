"""
Software Factory Loop Controller.
Manages cycle iteration, tracker state synchronization, primary/fallback engine failover,
DOD test verification, Agent Council roster sync, and structured invocation logging.
"""

import os
import sys
import time
import json
import yaml
from typing import Dict, Any, Optional
from .spec_parser import TicketSpec
from .adapters.tracker import BaseTrackerAdapter, JiraAdapter, LinearAdapter, LocalMdAdapter
from .adapters.engine import BaseEngineAdapter, ClaudeEngine, CodexEngine, EngineExecutionResult
from .roster import RosterManager
from .logger import AgentInvocationLogger


class FactoryController:
    """Core orchestrator for Software Factory execution cycles."""

    def __init__(self, config_path: str = "factory.yaml", project_dir: str = "."):
        self.project_dir = os.path.abspath(project_dir)
        self.config_path = os.path.join(self.project_dir, config_path)
        self.config = self._load_config()
        self.tracker = self._init_tracker()
        self.roster_manager = RosterManager(self.config)
        self.logger = AgentInvocationLogger(self.project_dir)
        self.primary_engine = self._init_engine(self.config.get("engine", {}).get("primary", "claude"))
        self.fallback_engine = self._init_engine(self.config.get("engine", {}).get("fallback", "codex"))

    def _load_config(self) -> Dict[str, Any]:
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(
                f"Configuration file not found at '{self.config_path}'. "
                "Run 'factory-loop init' or run the /factory-init skill to generate one."
            )
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def _init_tracker(self) -> BaseTrackerAdapter:
        t_type = self.config.get("issue_tracker", {}).get("type", "jira").lower()
        if t_type == "jira":
            return JiraAdapter(self.config)
        elif t_type == "linear":
            return LinearAdapter(self.config)
        elif t_type == "local_md":
            return LocalMdAdapter(self.config)
        else:
            raise ValueError(f"Unsupported issue tracker type: '{t_type}'")

    def _init_engine(self, engine_name: str) -> Optional[BaseEngineAdapter]:
        name = (engine_name or "").lower()
        if name == "claude":
            return ClaudeEngine(self.config)
        elif name == "codex":
            return CodexEngine(self.config)
        return None

    def render_prompt(self, ticket: TicketSpec) -> str:
        """Generates cycle execution prompt for the engine, including Agent Council roster."""
        prj_cfg = self.config.get("project", {})
        gates_cfg = self.config.get("gates", {})
        
        prompt = f"# Mandate for {prj_cfg.get('name', 'Project')}\n\n"
        prompt += f"## Active Ticket: [{ticket.ticket_id}] {ticket.title}\n"
        prompt += f"**Goal**: {ticket.goal}\n\n"
        prompt += "## Target Files (STRICT SCOPE FENCE)\n"
        for tf in ticket.target_files:
            prompt += f"- `{tf}`\n"
        prompt += "\n"

        if ticket.interface_contract:
            prompt += f"## Interface Contract\n```python\n{ticket.interface_contract}\n```\n\n"

        if ticket.requirements:
            prompt += "## Requirements\n"
            for req in ticket.requirements:
                prompt += f"1. {req}\n"
            prompt += "\n"

        if ticket.definition_of_done:
            prompt += "## Definition of Done\n"
            for dod in ticket.definition_of_done:
                prompt += f"- [ ] {dod}\n"
            prompt += "\n"

        prompt += "## Execution Constraints\n"
        prompt += f"- Test Command: `{gates_cfg.get('test_command', 'pytest')}`\n"
        prompt += f"- Lint Command: `{gates_cfg.get('lint_command', 'ruff check .')}`\n"
        prompt += f"- Integration Branch: `{prj_cfg.get('integration_branch', 'staging')}`\n"
        prompt += f"- Feature Branch: `{prj_cfg.get('ticket_branch_prefix', 'jira-')}{ticket.ticket_id.lower()}`\n\n"

        # Append Agent Council Roster table
        prompt += self.roster_manager.render_council_table()

        return prompt

    def run_single_cycle(self) -> EngineExecutionResult:
        """Runs a single development cycle with automatic engine failover and invocation logging."""
        # Ensure subagent manifests under .claude/agents/*.md are synced for council roles
        self.roster_manager.sync_claude_agents(self.project_dir)

        ticket = self.tracker.get_active_ticket() or self.tracker.get_next_todo_ticket()
        if not ticket:
            return EngineExecutionResult(
                success=True,
                exit_code=0,
                stdout="No ready tickets found in tracker.",
                stderr="",
                duration_seconds=0.0,
                engine_name="none",
                model_used="none"
            )

        prompt = self.render_prompt(ticket)
        timeout = self.config.get("engine", {}).get("cycle_timeout_seconds", 1800)
        cycle_id = f"cycle-{int(time.time())}"

        # Attempt primary engine
        if self.primary_engine:
            res = self.primary_engine.execute_cycle(prompt, self.project_dir, timeout_seconds=timeout)
            
            # Log invocation
            executor_role = self.roster_manager.get_role("software-engineer")
            model_used = res.model_used if res.model_used != "none" else (executor_role.model if executor_role else "sonnet")
            
            self.logger.log_invocation(
                cycle_id=cycle_id,
                ticket_id=ticket.ticket_id,
                agent_role="software-engineer",
                model=model_used,
                engine=res.engine_name,
                status="SUCCESS" if res.success else "FAILED",
                duration_seconds=res.duration_seconds,
                input_tokens=res.input_tokens,
                output_tokens=res.output_tokens,
                total_tokens=res.total_tokens,
                cost_usd=res.cost_usd,
                error_message=res.error_message
            )

            if res.success:
                return res

        # Failover to secondary engine if primary failed
        if self.fallback_engine:
            res_fallback = self.fallback_engine.execute_cycle(prompt, self.project_dir, timeout_seconds=timeout)
            
            self.logger.log_invocation(
                cycle_id=cycle_id,
                ticket_id=ticket.ticket_id,
                agent_role="software-engineer",
                model=res_fallback.model_used,
                engine=res_fallback.engine_name,
                status="SUCCESS" if res_fallback.success else "FAILED",
                duration_seconds=res_fallback.duration_seconds,
                input_tokens=res_fallback.input_tokens,
                output_tokens=res_fallback.output_tokens,
                total_tokens=res_fallback.total_tokens,
                cost_usd=res_fallback.cost_usd,
                error_message=res_fallback.error_message
            )

            return res_fallback

        return EngineExecutionResult(
            success=False,
            exit_code=1,
            stdout="",
            stderr="Primary and fallback engines both failed.",
            duration_seconds=0.0,
            engine_name="failed",
            model_used="none"
        )
