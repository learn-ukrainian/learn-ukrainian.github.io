"""DeepSeek admission preserves the public-monorepo input boundary."""

from __future__ import annotations

import pytest

from scripts.agent_runtime.deepseek_admission import (
    DeepSeekAdmissionRefused,
    refuse_deepseek_if_disallowed,
)
from scripts.agent_runtime.kimi_admission import refuse_kimi_if_disallowed
from scripts.agent_runtime.target_admission import resolve_and_admit


@pytest.mark.parametrize("repo", ["synthetic-private-role", "synthetic-other-role"])
def test_private_repository_role_is_refused(repo):
    with pytest.raises(DeepSeekAdmissionRefused, match="repository role must be public-monorepo"):
        refuse_deepseek_if_disallowed(("deepseek",), repo=repo)


@pytest.mark.parametrize("component", [".claude", ".agent", ".codex"])
@pytest.mark.parametrize("prefix", ["", "briefs/"])
def test_private_state_prompt_file_is_refused(component, prefix):
    with pytest.raises(DeepSeekAdmissionRefused, match="prompt file lives in agent-private state"):
        refuse_deepseek_if_disallowed(
            ("deepseek",), repo="public-monorepo", prompt_file=f"{prefix}{component}/brief.md",
        )


def test_public_monorepo_coding_is_admitted():
    assert refuse_deepseek_if_disallowed(
        ("deepseek",), ("deepseek-v4.1-flash",), repo="public-monorepo", prompt_file="briefs/coding.md",
    ) is None
    assert refuse_kimi_if_disallowed(
        ("deepseek",), mode="workspace-write", repo="public-monorepo", prompt_file="briefs/coding.md",
    ) is None


@pytest.mark.parametrize("seat", ["deepseek", "hermes", "hermes-deepseek", "acpx-deepseek-shadow"])
def test_prelaunch_function_calls_deepseek_helper_before_kimi_return(seat):
    with pytest.raises(DeepSeekAdmissionRefused, match="repository role must be public-monorepo"):
        refuse_kimi_if_disallowed(
            iter((seat,)), iter(()), mode="workspace-write", repo="synthetic-private-role",
        )


@pytest.mark.parametrize("model", ["deepseek-v4.1-flash", "deepseek/deepseek-flash", "openrouter/deepseek/deepseek-v4.1-flash"])
def test_deepseek_model_override_is_gated(model):
    with pytest.raises(DeepSeekAdmissionRefused, match="repository role must be public-monorepo"):
        refuse_deepseek_if_disallowed(("synthetic-seat",), (model,), repo="synthetic-private-role")


def test_resolve_and_admit_refuses_before_launch():
    with pytest.raises(DeepSeekAdmissionRefused, match="repository role must be public-monorepo"):
        resolve_and_admit(("deepseek",), mode="workspace-write", repo="synthetic-private-role")


def test_other_seats_are_unaffected():
    assert refuse_deepseek_if_disallowed(("codex",), repo="synthetic-private-role", prompt_file=".codex/brief.md") is None


def test_non_language_consult_without_repository_role_remains_admitted():
    (target,) = resolve_and_admit(("deepseek",), mode="acp", compat=True)
    assert target.recipient == "deepseek"
