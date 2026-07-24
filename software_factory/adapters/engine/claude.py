"""
Claude Code CLI Engine Adapter.
Invokes Anthropic's `claude` CLI with permission modes, model configuration, and execution timing.
"""

import os
import shutil
import subprocess
import time
from typing import Dict, Any, Optional
from .base import BaseEngineAdapter, EngineExecutionResult


class ClaudeEngine(BaseEngineAdapter):
    """Adapter for Anthropic Claude Code CLI executable."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        engine_cfg = config.get("engine", {})
        self.permission_mode = engine_cfg.get("permission_mode", "bypassPermissions")
        self.default_model = engine_cfg.get("primary_model", "sonnet")
        self.claude_bin = engine_cfg.get("claude_bin", "") or shutil.which("claude") or "claude"

    def execute_cycle(
        self,
        prompt: str,
        project_dir: str,
        model: Optional[str] = None,
        timeout_seconds: int = 1800
    ) -> EngineExecutionResult:
        selected_model = model or self.default_model
        
        # Build command invocation
        cmd = [self.claude_bin, "-p", prompt]
        
        if self.permission_mode:
            cmd.extend(["--permission-mode", self.permission_mode])
            
        if selected_model:
            cmd.extend(["--model", selected_model])

        env = os.environ.copy()
        # Enable experimental agent teams / subagents if roster enabled
        env["CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS"] = "1"

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
            
            return EngineExecutionResult(
                success=success,
                exit_code=process.returncode,
                stdout=process.stdout,
                stderr=process.stderr,
                duration_seconds=round(duration, 2),
                cost_usd=0.0,  # Telemetry parsed from stdout/JSON if present
                engine_name="claude",
                model_used=selected_model,
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
