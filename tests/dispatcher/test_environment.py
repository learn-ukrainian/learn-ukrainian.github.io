"""The provider environment carries the sense-proof directory and nothing else that is ambient."""

import pytest

from scripts.dispatcher import environment
from scripts.dispatcher.types import TaskSpec

PROOF_DIR = "LU_SENSE_PROOF_DIR"
SENTINEL = "/fixture/sense-proofs"
LOGIN_NAMES = sorted({name for names in environment._AUTH.values() for name in names} | {"CODEX_ACCESS_TOKEN"})
PROVIDERS = [(agent, None) for agent in environment._AUTH] + [("opencode", "openrouter")]


@pytest.mark.parametrize(("agent", "provider"), PROVIDERS)
def test_child_env_carries_sense_proof_dir_and_strips_logins(tmp_path, monkeypatch, agent, provider):
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path / "tasks"))
    for name in (*LOGIN_NAMES, "GH_TOKEN"):
        monkeypatch.setenv(name, "fixture-credential")
    spec = TaskSpec("fixture", agent, "stub", None, "read-only", tmp_path, tmp_path / "prompt", tmp_path / "final",
                    provider=provider)

    monkeypatch.setenv(PROOF_DIR, SENTINEL)
    env = environment.child_env(spec)
    assert env[PROOF_DIR] == SENTINEL
    own = set(environment._AUTH[agent]) if provider is None else {"OPENROUTER_API_KEY"}
    assert set(LOGIN_NAMES) & env.keys() <= own
    assert "GH_TOKEN" not in env

    monkeypatch.delenv(PROOF_DIR)
    assert PROOF_DIR not in environment.child_env(spec)
