"""
OpenAI Codex CLI Engine Adapter (Fallback Engine).
Invokes OpenAI's `codex` CLI as an automatic fallback when primary engine fails or hits limits.
"""

import os
import shutil
import subprocess
import time
from typing import Dict, Any, Optional
from .base import BaseEngineAdapter, EngineExecutionResult
from ...metrics import parse_token_telemetry, calculate_cost


class CodexEngine(BaseEngineAdapter):
    """Adapter for OpenAI Codex CLI executable."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        engine_cfg = config.get("engine", {})
        self.sandbox_mode = engine_cfg.get("sandbox_mode", "danger-full-access")
        self.default_model = engine_cfg.get("fallback_model", "gpt-4o")
        self.codex_bin = engine_cfg.get("codex_bin", "") or shutil.which("codex") or "codex"

    def execute_cycle(
        self,
        prompt: str,
        project_dir: str,
        model: Optional[str] = None,
        timeout_seconds: int = 1800
    ) -> EngineExecutionResult:
        selected_model = model or self.default_model
        
        cmd = [self.codex_bin, "exec", prompt]
        if self.sandbox_mode:
            cmd.extend(["--sandbox", self.sandbox_mode])
        if selected_model:
            cmd.extend(["--model", selected_model])

        start_time = time.time()
        try:
            process = subprocess.run(
                cmd,
                cwd=project_dir,
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
            cost = calculate_cost(selected_model, in_tok, out_tok)

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
                engine_name="codex",
                model_used=selected_model,
                error_message=None if success else process.stderr or "Non-zero exit code"
            )
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return EngineExecutionResult(
                success=False,
                exit_code=124,
                stdout="",
                stderr=f"Codex execution timed out after {timeout_seconds} seconds.",
                duration_seconds=round(duration, 2),
                cost_usd=0.0,
                engine_name="codex",
                model_used=selected_model,
                error_message=f"Timeout after {timeout_seconds}s"
            )
        except FileNotFoundError:
            return EngineExecutionResult(
                success=False,
                exit_code=127,
                stdout="",
                stderr=f"Codex CLI executable not found at '{self.codex_bin}'",
                duration_seconds=0.0,
                cost_usd=0.0,
                engine_name="codex",
                model_used=selected_model,
                error_message="Codex CLI executable not found"
            )
