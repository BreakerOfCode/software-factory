"""
Metrics & Cost Calculation Utilities for Software Factory.
Provides token telemetry parsing, pricing lookup, and metric aggregation.
"""

import re
import json
from typing import Dict, Any, Tuple, Optional, List

# Pricing per 1,000,000 tokens (USD)
MODEL_PRICING: Dict[str, Dict[str, float]] = {
    "sonnet": {"input": 3.00, "output": 15.00},
    "claude-3-5-sonnet": {"input": 3.00, "output": 15.00},
    "claude-3-7-sonnet": {"input": 3.00, "output": 15.00},
    "opus": {"input": 15.00, "output": 75.00},
    "claude-3-opus": {"input": 15.00, "output": 75.00},
    "haiku": {"input": 0.80, "output": 4.00},
    "claude-3-5-haiku": {"input": 0.80, "output": 4.00},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "codex": {"input": 2.50, "output": 10.00},
    "default": {"input": 3.00, "output": 15.00},
}


def get_model_pricing(model: str) -> Dict[str, float]:
    """Retrieves input and output cost per 1M tokens for a given model string."""
    m_lower = (model or "").lower().strip()
    for key, rates in MODEL_PRICING.items():
        if key in m_lower or m_lower in key:
            return rates
    return MODEL_PRICING["default"]


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculates total cost in USD based on model pricing rates."""
    pricing = get_model_pricing(model)
    cost_in = (input_tokens / 1_000_000.0) * pricing["input"]
    cost_out = (output_tokens / 1_000_000.0) * pricing["output"]
    return round(cost_in + cost_out, 6)


def parse_token_telemetry(
    stdout: str = "",
    stderr: str = "",
    prompt: str = "",
    completion: str = ""
) -> Tuple[int, int, int]:
    """
    Parses explicit token metrics from stdout/stderr (JSON or text regex).
    Falls back to length estimation (~4 characters/token) if no explicit metrics are present.
    Returns (input_tokens, output_tokens, total_tokens).
    """
    combined_output = f"{stdout}\n{stderr}"
    
    # 1. Attempt to parse JSON telemetry in output
    for line in combined_output.splitlines():
        line_str = line.strip()
        if line_str.startswith("{") and line_str.endswith("}"):
            try:
                data = json.loads(line_str)
                if isinstance(data, dict):
                    # Check common JSON token fields
                    usage = data.get("usage", data)
                    in_tok = usage.get("input_tokens") or usage.get("prompt_tokens")
                    out_tok = usage.get("output_tokens") or usage.get("completion_tokens")
                    if in_tok is not None and out_tok is not None:
                        in_val = int(in_tok)
                        out_val = int(out_tok)
                        return in_val, out_val, in_val + out_val
            except (json.JSONDecodeError, ValueError, TypeError):
                pass

    # 2. Attempt regex extraction from output text
    # Pattern A: "Tokens: 450 in, 150 out" or "450 input tokens, 150 output tokens"
    in_out_match = re.search(
        r'([\d,]+)\s*(?:in|input|prompt)(?:[_\s]*tokens?)?,\s*([\d,]+)\s*(?:out|output|completion)(?:[_\s]*tokens?)?',
        combined_output,
        re.IGNORECASE
    )
    if in_out_match:
        try:
            in_val = int(in_out_match.group(1).replace(',', ''))
            out_val = int(in_out_match.group(2).replace(',', ''))
            return in_val, out_val, in_val + out_val
        except ValueError:
            pass

    # Pattern B: "input_tokens: 450" or "prompt_tokens: 450"
    tok_in_match = re.search(r'(?:input[_\s]*tokens?|prompt[_\s]*tokens?):\s*([\d,]+)', combined_output, re.IGNORECASE)
    tok_out_match = re.search(r'(?:output[_\s]*tokens?|completion[_\s]*tokens?):\s*([\d,]+)', combined_output, re.IGNORECASE)

    if tok_in_match and tok_out_match:
        try:
            in_val = int(tok_in_match.group(1).replace(',', ''))
            out_val = int(tok_out_match.group(1).replace(',', ''))
            return in_val, out_val, in_val + out_val
        except ValueError:
            pass

    # 3. Fallback: Estimate tokens based on prompt and completion character length (~4 chars/token)
    in_val = max(0, len(prompt) // 4)
    out_val = max(0, len(completion) // 4)
    
    # Ensure non-zero fallback if text exists
    if len(prompt) > 0 and in_val == 0:
        in_val = 1
    if len(completion) > 0 and out_val == 0:
        out_val = 1

    return in_val, out_val, in_val + out_val
