"""
Unit tests for metrics and cost calculation module.
"""

import pytest
from software_factory.metrics import (
    calculate_cost,
    parse_token_telemetry,
    get_model_pricing,
)
from software_factory.logger import AgentInvocationLogger


def test_calculate_cost():
    # Sonnet: $3.00/1M in, $15.00/1M out
    # 1,000,000 in, 1,000,000 out => $18.00
    cost = calculate_cost("sonnet", 1_000_000, 1_000_000)
    assert pytest.approx(cost, 0.0001) == 18.00

    # 10,000 in, 2,000 out => 0.03 + 0.03 = 0.06
    cost = calculate_cost("sonnet", 10_000, 2_000)
    assert pytest.approx(cost, 0.0001) == 0.06


def test_fmt_usd():
    from software_factory.metrics import fmt_usd
    assert fmt_usd(4.5114) == 4.51
    assert fmt_usd(0.0699) == 0.07
    assert fmt_usd(0.0) == 0.0



def test_parse_token_telemetry_explicit_json():
    json_stdout = '{"usage": {"input_tokens": 1200, "output_tokens": 300}}'
    in_t, out_t, tot_t = parse_token_telemetry(stdout=json_stdout)
    assert in_t == 1200
    assert out_t == 300
    assert tot_t == 1500


def test_parse_token_telemetry_regex():
    regex_stdout = "Execution complete. Tokens: 450 in, 150 out."
    in_t, out_t, tot_t = parse_token_telemetry(stdout=regex_stdout)
    assert in_t == 450
    assert out_t == 150
    assert tot_t == 600


def test_parse_token_telemetry_fallback_length():
    prompt = "A" * 400   # ~100 tokens
    completion = "B" * 200 # ~50 tokens
    in_t, out_t, tot_t = parse_token_telemetry(prompt=prompt, completion=completion)
    assert in_t == 100
    assert out_t == 50
    assert tot_t == 150


def test_logger_metrics_summary(tmp_path):
    logger = AgentInvocationLogger(str(tmp_path))
    
    logger.log_invocation(
        cycle_id="c-1",
        ticket_id="ENG-1",
        agent_role="software-engineer",
        model="sonnet",
        engine="claude",
        status="SUCCESS",
        duration_seconds=10.0,
        input_tokens=1000,
        output_tokens=500,
        total_tokens=1500,
        cost_usd=0.0105
    )

    logger.log_invocation(
        cycle_id="c-2",
        ticket_id="ENG-2",
        agent_role="software-engineer",
        model="opus",
        engine="claude",
        status="SUCCESS",
        duration_seconds=20.0,
        input_tokens=2000,
        output_tokens=1000,
        total_tokens=3000,
        cost_usd=0.105
    )

    summary = logger.get_metrics_summary()
    assert summary["total_cycles"] == 2
    assert summary["total_input_tokens"] == 3000
    assert summary["total_output_tokens"] == 1500
    assert summary["total_tokens"] == 4500
    assert summary["total_cost_usd"] == pytest.approx(0.1155, 0.0001)
    assert summary["avg_tokens_per_cycle"] == 2250.0
