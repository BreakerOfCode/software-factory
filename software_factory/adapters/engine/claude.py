"""
Claude Code CLI Engine Adapter.
Invokes Anthropic's `claude` CLI with permission modes, model configuration, and execution timing.
"""

import json
import os
import re
import shutil
import subprocess
import time
from typing import Dict, Any, Optional, List, Tuple
from .base import BaseEngineAdapter, EngineExecutionResult
from ...metrics import parse_token_telemetry, calculate_cost, fmt_usd


class ClaudeEngine(BaseEngineAdapter):
    """Adapter for Anthropic Claude Code CLI executable."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        engine_cfg = config.get("engine", {})
        self.permission_mode = engine_cfg.get("permission_mode", "bypassPermissions")
        self.default_model = engine_cfg.get("primary_model", "sonnet")
        self.claude_bin = engine_cfg.get("claude_bin", "") or shutil.which("claude") or "claude"

    def parse_subagent_invocations(self, stdout: str, stderr: str) -> List[str]:
        """Parses stream-json / text output for subagent roll-call invocations."""
        combined = f"{stdout}\n{stderr}"
        invocations: List[str] = []

        for line in combined.splitlines():
            line_str = line.strip()
            if line_str.startswith("{") and line_str.endswith("}"):
                try:
                    data = json.loads(line_str)
                    if isinstance(data, dict):
                        # 1. Direct subagent_type field in stream-json event
                        sub_type = data.get("subagent_type") or data.get("agent_type") or data.get("subagent")
                        if sub_type and isinstance(sub_type, str):
                            invocations.append(sub_type)

                        # 2. Tool invocation targeting Task / subagent
                        if data.get("type") == "tool_use":
                            t_name = data.get("name") or ""
                            t_input = data.get("input") or {}
                            if t_name in ("Task", "Agent", "subagent") or "subagent" in t_name.lower():
                                agent_name = t_input.get("subagent_type") or t_input.get("agent_name") or t_name
                                invocations.append(str(agent_name))
                except (json.JSONDecodeError, ValueError, TypeError):
                    pass

        # Fallback text regex search for roll-call patterns (e.g. "Running subagent: qa-test-engineer")
        if not invocations:
            matches = re.findall(r'(?:subagent|invoking agent|Agent|role)[:\s]+([\w-]+)', combined, re.IGNORECASE)
            for m in matches:
                if m.lower() not in ("claude", "system", "user", "none", "true", "false"):
                    invocations.append(m)

        return invocations

    def execute_cycle(
        self,
        prompt: str,
        project_dir: str,
        model: Optional[str] = None,
        timeout_seconds: int = 1800
    ) -> EngineExecutionResult:
        selected_model = model or self.default_model
        
        # Build command invocation with stream-json formatting
        cmd = [self.claude_bin, "-p", prompt, "--output-format", "stream-json", "--verbose"]
        
        if self.permission_mode:
            cmd.extend(["--permission-mode", self.permission_mode])
            
        if selected_model:
            cmd.extend(["--model", selected_model])

        env = os.environ.copy()
        # Enable experimental agent teams / subagents if roster enabled
        env["CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS"] = "1"
        # Ensure prompt caching is enabled (unset DISABLE_PROMPT_CACHING)
        env.pop("DISABLE_PROMPT_CACHING", None)

        start_time = time.time()
        try:
            process = subprocess.run(
                cmd,
                cwd=project_dir,
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout_seconds
            )
            duration = time.time() - start_time
            success = process.returncode == 0
            
            in_tok, out_tok, tot_tok = parse_token_telemetry(
                stdout=process.stdout,
                stderr=process.stderr,
                prompt=prompt,
                completion=process.stdout
            )
            cost = fmt_usd(calculate_cost(selected_model, in_tok, out_tok))
            invocations = self.parse_subagent_invocations(process.stdout, process.stderr)

            return EngineExecutionResult(
                success=success,
                exit_code=process.returncode,
                stdout=process.stdout,
                stderr=process.stderr,
                duration_seconds=round(duration, 2),
                input_tokens=in_tok,
                output_tokens=out_tok,
                total_tokens=tot_tok,
                cost_usd=cost,
                engine_name="claude",
                model_used=selected_model,
                subagent_invocations=invocations,
                subagent_count=len(invocations),
                error_message=None if success else process.stderr or "Non-zero exit code"
            )

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return EngineExecutionResult(
                success=False,
                exit_code=124,
                stdout="",
                stderr=f"Execution timed out after {timeout_seconds} seconds.",
                duration_seconds=round(duration, 2),
                cost_usd=0.0,
                engine_name="claude",
                model_used=selected_model,
                error_message=f"Timeout after {timeout_seconds}s"
            )
        except FileNotFoundError:
            return EngineExecutionResult(
                success=False,
                exit_code=127,
                stdout="",
                stderr=f"Claude CLI executable not found at '{self.claude_bin}'",
                duration_seconds=0.0,
                cost_usd=0.0,
                engine_name="claude",
                model_used=selected_model,
                error_message="Claude CLI executable not found"
            )
