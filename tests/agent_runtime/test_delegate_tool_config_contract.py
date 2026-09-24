"""Every dispatch adapter must accept the tool_config keys delegate.py adds.

The key list is parsed from ``_run_worker`` so a new read-only or review
assignment fails this contract until the adapters accept it.
"""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

import pytest

from scripts.agent_runtime.registry import AGENTS

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DELEGATE = _REPO_ROOT / "scripts" / "delegate.py"
_GATE_NAMES = frozenset({"review_id", "attempt_id", "strict_mcp_config", "mcp_config_path"})


def delegate_read_only_and_review_tool_config_keys() -> frozenset[str]:
    """Return tool_config keys assigned under read-only or review gates."""
    tree = ast.parse(_DELEGATE.read_text(encoding="utf-8"))
    keys: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef) or node.name != "_run_worker":
            continue
        for child in ast.walk(node):
            if isinstance(child, ast.If) and _gates_read_only_or_review(child.test):
                keys.update(_assigned_tool_config_keys(child))
    if not keys:
        raise AssertionError("delegate.py _run_worker assigned no read-only or review tool_config keys")
    return frozenset(keys)


def _gates_read_only_or_review(test: ast.AST) -> bool:
    for node in ast.walk(test):
        if (
            isinstance(node, ast.Compare)
            and isinstance(node.left, ast.Name)
            and node.left.id == "mode"
            and any(isinstance(item, ast.Constant) and item.value == "read-only" for item in node.comparators)
        ):
            return True
        if isinstance(node, ast.Name) and node.id in _GATE_NAMES:
            return True
    return False


def _assigned_tool_config_keys(node: ast.AST) -> set[str]:
    keys: set[str] = set()
    for child in ast.walk(node):
        if not isinstance(child, ast.Assign):
            continue
        for target in child.targets:
            key = _tool_config_subscript(target)
            if key is not None:
                keys.add(key)
    return keys


def _tool_config_subscript(target: ast.AST) -> str | None:
    if not isinstance(target, ast.Subscript):
        return None
    if not isinstance(target.value, ast.Name) or target.value.id != "tool_config":
        return None
    if isinstance(target.slice, ast.Constant) and isinstance(target.slice.value, str):
        return target.slice.value
    return None


def _dispatch_adapter_classes() -> list[type]:
    seen: set[type] = set()
    classes: list[type] = []
    for entry in AGENTS.values():
        if entry.get("direct_only"):
            continue
        module_path, class_name = entry["adapter"].split(":", 1)
        cls = getattr(importlib.import_module(module_path), class_name)
        if cls in seen:
            continue
        seen.add(cls)
        classes.append(cls)
    return classes


def test_parsed_delegate_keys_cover_read_only_and_review_attempts() -> None:
    keys = delegate_read_only_and_review_tool_config_keys()
    assert "read_only_tmp_root" in keys
    assert {"mcp_server_names", "review_id", "attempt_id", "strict_mcp_config", "mcp_config_path"} <= keys


@pytest.mark.parametrize("adapter_cls", _dispatch_adapter_classes(), ids=lambda cls: cls.__name__)
def test_every_dispatch_adapter_accepts_delegate_tool_config_keys(adapter_cls, tmp_path, monkeypatch) -> None:
    lease = tmp_path / "learn-ukrainian" / "contract-lease"
    lease.mkdir(parents=True)
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    monkeypatch.setenv("LU_RUNTIME_TMP_BASE_ROOT", str(tmp_path))
    claude = tmp_path / "claude"
    claude.write_text("#!/bin/sh\n", encoding="utf-8")
    claude.chmod(0o755)
    monkeypatch.setattr("scripts.agent_runtime.adapters.kimicc._default_claude_bin", lambda: str(claude))
    monkeypatch.setattr("scripts.agent_runtime.adapters.kimicc._ensure_supported_claude_cli_version", lambda _: None)
    monkeypatch.setattr(
        "scripts.agent_runtime.adapters.claude._ensure_supported_claude_cli_version", lambda _: (2, 1, 120)
    )
    monkeypatch.setattr("scripts.agent_runtime.adapters.claude._default_claude_bin", lambda: str(claude))

    tool_config = {
        "read_only_tmp_root": str(lease),
        "mcp_config_path": str(tmp_path / "review.mcp.json"),
        "strict_mcp_config": True,
        "mcp_server_names": ["sources"],
        "review_id": "rev-contract",
        "attempt_id": "att-contract",
        "allowed_tools": "mcp__sources__verify_word",
        "codex_home_override": str(tmp_path / "codex-home"),
        "agy_home_override": str(tmp_path / "agy-home"),
    }
    # Drop keys the parser does not currently assign so the call stays
    # exactly the delegate set, plus harness for the Kimi seat.
    parsed = delegate_read_only_and_review_tool_config_keys()
    tool_config = {key: value for key, value in tool_config.items() if key in parsed}
    if adapter_cls.__name__ == "KimiAdapter":
        tool_config["harness"] = "kimicc"

    try:
        plan = adapter_cls().build_invocation(
            prompt="read-only contract",
            mode="read-only",
            cwd=checkout,
            model=None,
            task_id="tool-config-contract",
            session_id=None,
            tool_config=tool_config,
        )
    except Exception as exc:
        message = str(exc)
        assert "unsupported tool_config" not in message, f"{adapter_cls.__name__} rejected delegate keys: {message}"
        if adapter_cls.__name__ in {"KimiAdapter", "KimiccHarness"}:
            raise
        return

    joined = " ".join(plan.cmd)
    assert "read_only_tmp_root" not in joined
    assert "review_id" not in joined
    assert "attempt_id" not in joined
