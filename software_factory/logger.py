"""
Invocation Logger for Software Factory.
Logs structured telemetry for each agent/engine invocation to .factory/logs/invocations.jsonl.
"""

import os
import json
import time
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional


@dataclass
class InvocationLogEntry:
    timestamp: str
    cycle_id: str
    ticket_id: str
    agent_role: str
    model: str
    engine: str
    status: str
    duration_seconds: float
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    error_message: Optional[str] = None


class AgentInvocationLogger:
    """Structured telemetry logger for agent invocations."""

    def __init__(self, project_dir: str):
        self.project_dir = os.path.abspath(project_dir)
        self.log_dir = os.path.join(self.project_dir, ".factory", "logs")
        self.log_file = os.path.join(self.log_dir, "invocations.jsonl")

    def _ensure_log_dir(self):
        os.makedirs(self.log_dir, exist_ok=True)

    def log_invocation(
        self,
        cycle_id: str,
        ticket_id: str,
        agent_role: str,
        model: str,
        engine: str,
        status: str,
        duration_seconds: float,
        input_tokens: int = 0,
        output_tokens: int = 0,
        total_tokens: int = 0,
        cost_usd: float = 0.0,
        error_message: Optional[str] = None
    ) -> InvocationLogEntry:
        self._ensure_log_dir()

        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        tot_tokens = total_tokens if total_tokens > 0 else (input_tokens + output_tokens)
        
        entry = InvocationLogEntry(
            timestamp=timestamp,
            cycle_id=cycle_id,
            ticket_id=ticket_id,
            agent_role=agent_role,
            model=model,
            engine=engine,
            status=status,
            duration_seconds=round(duration_seconds, 2),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=tot_tokens,
            cost_usd=round(cost_usd, 6),
            error_message=error_message
        )

        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(entry)) + "\n")

        return entry

    def read_recent_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        if not os.path.exists(self.log_file):
            return []

        entries = []
        with open(self.log_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

        return entries[-limit:]

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Calculates aggregated metrics across all recorded invocation cycles."""
        logs = self.read_recent_logs(limit=10000)
        if not logs:
            return {
                "total_cycles": 0,
                "total_duration_seconds": 0.0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_tokens": 0,
                "total_cost_usd": 0.0,
                "avg_cost_per_cycle": 0.0,
                "avg_tokens_per_cycle": 0.0
            }

        total_cycles = len(logs)
        total_duration = sum(entry.get("duration_seconds", 0.0) for entry in logs)
        total_in = sum(entry.get("input_tokens", 0) for entry in logs)
        total_out = sum(entry.get("output_tokens", 0) for entry in logs)
        total_tok = sum(entry.get("total_tokens", 0) or (entry.get("input_tokens", 0) + entry.get("output_tokens", 0)) for entry in logs)
        total_cost = sum(entry.get("cost_usd", 0.0) for entry in logs)

        return {
            "total_cycles": total_cycles,
            "total_duration_seconds": round(total_duration, 2),
            "total_input_tokens": total_in,
            "total_output_tokens": total_out,
            "total_tokens": total_tok,
            "total_cost_usd": round(total_cost, 6),
            "avg_cost_per_cycle": round(total_cost / total_cycles, 6) if total_cycles > 0 else 0.0,
            "avg_tokens_per_cycle": round(total_tok / total_cycles, 2) if total_cycles > 0 else 0.0
        }
