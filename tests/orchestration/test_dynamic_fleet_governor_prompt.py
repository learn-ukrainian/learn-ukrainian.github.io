from __future__ import annotations

from pathlib import Path

from scripts.api.route_contracts import contract_for_route


REPO_ROOT = Path(__file__).resolve().parents[2]
PROMPT = (
    REPO_ROOT
    / "agents_extensions/shared/prompts/dynamic-area-epic-fleet-governor.md"
)


def _prompt() -> str:
    return PROMPT.read_text(encoding="utf-8")


def _normalized_prompt() -> str:
    return " ".join(_prompt().split())


def test_governor_prompt_is_api_first_with_bounded_fallbacks() -> None:
    prompt = _normalized_prompt()

    assert "/api/state/manifest?session=<current-session-id>" in prompt
    assert "/api/orient?lean=true&session=<current-session-id>" in prompt
    assert "only when the manifest rules hash is new" in prompt
    assert "Give each read a two-second deadline" in prompt
    assert "null field is missing evidence" in prompt
    assert "Retry the API on the next material cycle" in prompt
    for endpoint in (
        "/api/issues/streams",
        "/api/worktrees",
        "/api/runtime/agents",
        "/api/runtime/auth",
        "/api/state/routing-budget",
        "/api/delegate/active",
    ):
        assert endpoint in prompt
        assert contract_for_route(endpoint, "http") is not None


def test_governor_prompt_binds_one_area_epic_and_github_lifecycle() -> None:
    prompt = _normalized_prompt()

    assert "An area is the projection of its registered epics" in prompt
    assert "Select exactly one focus epic" in prompt
    assert "Never infer ownership from an author/branch prefix" in prompt
    assert "out-of-stream membership is fail-closed" in prompt
    assert "area → exactly one epic → GitHub child issue" in prompt
    assert "task-lifecycle.v1" in prompt


def test_governor_prompt_keeps_sol_bounded_and_v2_accountable() -> None:
    prompt = _normalized_prompt()

    assert "Run as `gpt-5.6-sol` at `high`" in prompt
    assert "summoned supervisor, not a resident polling loop" in prompt
    assert "Escalate Sol to `xhigh` only for one concrete" in prompt
    assert prompt.count("list_agents") >= 3
    assert 'fork_turns="none"' in prompt
    assert "no more than three non-root native agents" in prompt
    assert "same three-agent whole-tree cap" in prompt
    assert "never satisfy the independent cross-family review gate" in prompt
    for field in (
        "functional role",
        "task family",
        "exact owned paths",
        "read/write authority",
        "verification",
        "return contract",
    ):
        assert field in prompt


def test_governor_prompt_routes_live_capacity_without_fixed_width() -> None:
    prompt = _normalized_prompt()

    assert "/Applications/CodexBar.app/Contents/Helpers/CodexBarCLI usage" in prompt
    assert "<codex|claude|cursor|gemini|antigravity|grok|kimi|zai>" in prompt
    assert "Never persist live percentages or fixed fleet width" in prompt
    assert "Disk is a hard gate and wins every conflict" in prompt
    assert "Never manufacture work to burn quota" in prompt
    assert "Do not automatically consume a Codex reset credit" in prompt


def test_governor_prompt_preserves_language_glm_and_trail_boundaries() -> None:
    prompt = _normalized_prompt()

    assert "Ukrainian pedagogy" in prompt
    assert "uses only `agy`, `codex`, `claude`, or `grok-4.5`" in prompt
    assert "`gemini-3.6-flash-high` first" in prompt
    assert "Require `sources`/VESUM evidence" in prompt
    assert "GLM-5.2/z.ai" in prompt
    assert "sends prompt data to China" in prompt
    assert "never runs in CI or automated pipelines" in prompt
    assert "No receipt-emitting trail runner exists yet" in prompt
    assert "RB-1 through RB-6" in prompt
