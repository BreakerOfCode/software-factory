"""
Roster Manager for Software Factory Agent Council.
Manages generic default roles, per-agent model configurations,
and subagent manifest generation (.claude/agents/*.md).
"""

import os
from dataclasses import dataclass
from typing import Dict, Any, List, Optional


@dataclass
class AgentRoleSpec:
    name: str
    model: str
    description: str
    mandatory: bool = False
    system_instructions: str = ""


# Generic repository roles default schema
DEFAULT_GENERIC_ROLES: List[AgentRoleSpec] = [
    AgentRoleSpec(
        name="software-engineer",
        model="sonnet",
        description="Executor — writes code inside the Target-Files fence",
        mandatory=False,
        system_instructions="You are the software engineer executor. Implement feature logic strictly within the Target Files scope fence."
    ),
    AgentRoleSpec(
        name="qa-test-engineer",
        model="sonnet",
        description="QA Gate — runs test runner & linter suites to assert Definition of Done",
        mandatory=True,
        system_instructions="You are the QA test engineer. Run the project's test command and linters. Quoting exact summary output, assert PASS/FAIL."
    ),
    AgentRoleSpec(
        name="scope-gate",
        model="opus",
        description="Scope Acceptance Gate — verifies git diff against Goal and Target Files fence",
        mandatory=True,
        system_instructions="You are the scope gate auditor. Examine modified files and git diff against Goal and Target Files. Return VERDICT: PASS or REJECT."
    ),
    AgentRoleSpec(
        name="project-architect",
        model="opus",
        description="Architect — verifies structural layout, dependencies, and module contracts",
        mandatory=False,
        system_instructions="You are the project architect. Review high-level package boundaries, class contracts, and system design."
    )
]


class RosterManager:
    """Manages Agent Council roles, models, and subagent manifest generation."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.roles: Dict[str, AgentRoleSpec] = self._parse_roster_config()

    def _parse_roster_config(self) -> Dict[str, AgentRoleSpec]:
        roles_map: Dict[str, AgentRoleSpec] = {}

        # Load default generic roles first
        for spec in DEFAULT_GENERIC_ROLES:
            roles_map[spec.name] = AgentRoleSpec(
                name=spec.name,
                model=spec.model,
                description=spec.description,
                mandatory=spec.mandatory,
                system_instructions=spec.system_instructions
            )

        roster_cfg = self.config.get("roster", {})
        if not roster_cfg:
            return roles_map

        for role_key, role_val in roster_cfg.items():
            if isinstance(role_val, str):
                # Simple string mapping: e.g. executor_role: "software-engineer"
                # or custom-role: "sonnet"
                if role_val in roles_map:
                    continue  # standard role name mapping
                roles_map[role_key] = AgentRoleSpec(
                    name=role_key,
                    model=role_val,
                    description=f"Custom agent role '{role_key}'",
                    mandatory=False,
                    system_instructions=f"You are the {role_key} agent."
                )
            elif isinstance(role_val, dict):
                model = role_val.get("model", "sonnet")
                desc = role_val.get("description", f"Agent role '{role_key}'")
                mandatory = role_val.get("mandatory", False)
                instructions = role_val.get("system_instructions", f"You are the {role_key} agent.")

                roles_map[role_key] = AgentRoleSpec(
                    name=role_key,
                    model=model,
                    description=desc,
                    mandatory=bool(mandatory),
                    system_instructions=instructions
                )

        return roles_map

    def get_role(self, name: str) -> Optional[AgentRoleSpec]:
        return self.roles.get(name)

    def sync_claude_agents(self, project_dir: str) -> List[str]:
        """Generates/syncs .claude/agents/*.md files for all configured council roles."""
        claude_agents_dir = os.path.join(project_dir, ".claude", "agents")
        os.makedirs(claude_agents_dir, exist_ok=True)

        created_files = []
        for role_name, spec in self.roles.items():
            file_path = os.path.join(claude_agents_dir, f"{role_name}.md")
            content = f"""---
name: {spec.name}
description: {spec.description}
model: {spec.model}
---

# {spec.name.replace('-', ' ').title()}

{spec.system_instructions}
"""
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            created_files.append(file_path)

        return created_files

    def render_council_table(self) -> str:
        """Renders a Markdown table of the Agent Council for cycle prompts."""
        lines = [
            "## Agent Council Roster",
            "The following specialized agent roles are available for this project cycle.",
            "",
            "| Role | Model | Type | Description |",
            "| :--- | :--- | :--- | :--- |"
        ]

        for name, spec in self.roles.items():
            gate_type = "**MANDATORY GATE**" if spec.mandatory else "Optional / Work"
            lines.append(f"| **{spec.name}** | `{spec.model}` | {gate_type} | {spec.description} |")

        lines.append("")
        lines.append("### Execution Rules for Council:")
        lines.append("1. **`software-engineer`** writes code strictly within `Target Files` fence.")
        lines.append("2. **`qa-test-engineer`** (MANDATORY) must run test and lint commands and report exact summary lines before cycle report.")
        lines.append("3. **`scope-gate`** (MANDATORY) must evaluate git diff against target files and return `VERDICT: PASS` before opening any PR.")
        lines.append("4. **`project-architect`** evaluates system structural changes.")
        lines.append("")

        return "\n".join(lines)
