"""Prove pytest exposes ``scripts/`` as an import root from startup."""

from importlib import import_module


def test_scripts_is_a_pytest_import_root() -> None:
    ai_llm = import_module("ai_llm")
    agent_runtime = import_module("agent_runtime")

    assert agent_runtime.__file__
    assert ai_llm.__file__
