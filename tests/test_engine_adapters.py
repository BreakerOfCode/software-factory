"""
Tests for LLM CLI Engine Adapters (Claude and Codex).
"""

from software_factory.adapters.engine.claude import ClaudeEngine
from software_factory.adapters.engine.codex import CodexEngine


def test_claude_engine_missing_executable():
    config = {
        "engine": {
            "claude_bin": "nonexistent_claude_cli_binary_path"
        }
    }
    engine = ClaudeEngine(config)
    res = engine.execute_cycle("test prompt", ".")
    assert res.success is False
    assert res.exit_code == 127
    assert "not found" in res.stderr.lower()


def test_codex_engine_missing_executable():
    config = {
        "engine": {
            "codex_bin": "nonexistent_codex_cli_binary_path"
        }
    }
    engine = CodexEngine(config)
    res = engine.execute_cycle("test prompt", ".")
    assert res.success is False
    assert res.exit_code == 127
    assert "not found" in res.stderr.lower()
