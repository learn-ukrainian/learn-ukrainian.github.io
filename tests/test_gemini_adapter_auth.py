"""Tests for Gemini auth-mode resolution + API cooldown (#1384 Phase 1).

``auto`` default is API-first (faster); cooldown-driven fallback to
subscription on 429. No probe calls — cooldown is set ONLY by real
rate-limit responses, because the Gemini API has a small daily call
budget (~150) that we refuse to burn on liveness checks.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

# Repo-root shim (same pattern as other tests in this directory).
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from agent_runtime.adapters.gemini import (
    _normalize_gemini_auth_mode,
    resolve_gemini_auth_mode,
)
from ai_llm.cooldown import (
    clear_api_cooldown,
    cooldown_remaining_s,
    is_api_cooldown_active,
    set_api_cooldown,
)
from ai_llm.fallback import (
    build_gemini_ladder,
    resolve_allowed_auth_modes,
)

# ── _normalize_gemini_auth_mode ───────────────────────────────────────


class TestNormalizeAuthMode:
    def test_none_defaults_to_auto(self) -> None:
        assert _normalize_gemini_auth_mode(None) == "auto"

    def test_empty_string_defaults_to_auto(self) -> None:
        assert _normalize_gemini_auth_mode("") == "auto"

    def test_explicit_subscription(self) -> None:
        assert _normalize_gemini_auth_mode("subscription") == "subscription"

    def test_explicit_api(self) -> None:
        assert _normalize_gemini_auth_mode("api") == "api"

    def test_oauth_alias_normalizes_to_subscription(self) -> None:
        assert _normalize_gemini_auth_mode("oauth") == "subscription"

    def test_api_key_alias_normalizes_to_api(self) -> None:
        assert _normalize_gemini_auth_mode("api-key") == "api"

    def test_case_insensitive(self) -> None:
        assert _normalize_gemini_auth_mode("SUBSCRIPTION") == "subscription"
        assert _normalize_gemini_auth_mode("Api") == "api"

    def test_whitespace_stripped(self) -> None:
        assert _normalize_gemini_auth_mode("  subscription  ") == "subscription"

    def test_invalid_value_falls_back_to_auto(self) -> None:
        assert _normalize_gemini_auth_mode("garbage") == "auto"
        assert _normalize_gemini_auth_mode("🐙") == "auto"


# ── resolve_gemini_auth_mode — cooldown-aware auto ────────────────────


class TestResolveAuthMode:
    """#1384: ``auto`` is API-first (faster), flips to subscription only
    when cooldown is active (set by a prior 429). Zero probe calls — the
    Gemini API has a tiny daily quota that we must not burn on liveness.
    """

    def test_auto_unset_cooldown_inactive_resolves_to_api(self) -> None:
        """Default case: no env var, no cooldown → API (faster)."""
        env: dict[str, str] = {}
        assert resolve_gemini_auth_mode(env, cooldown_active=False) == "api"

    def test_auto_unset_cooldown_active_resolves_to_subscription(self) -> None:
        """After a recent 429: auto flips to subscription for the cooldown window."""
        env: dict[str, str] = {}
        assert resolve_gemini_auth_mode(env, cooldown_active=True) == "subscription"

    def test_explicit_auto_respects_cooldown(self) -> None:
        env = {"GEMINI_AUTH_MODE": "auto"}
        assert resolve_gemini_auth_mode(env, cooldown_active=False) == "api"
        assert resolve_gemini_auth_mode(env, cooldown_active=True) == "subscription"

    def test_explicit_subscription_wins_regardless_of_cooldown(self) -> None:
        """User can force subscription even with no active cooldown."""
        env = {"GEMINI_AUTH_MODE": "subscription"}
        assert resolve_gemini_auth_mode(env, cooldown_active=False) == "subscription"
        assert resolve_gemini_auth_mode(env, cooldown_active=True) == "subscription"

    def test_explicit_api_wins_regardless_of_cooldown(self) -> None:
        """User can force API mode even when cooldown says 'stay off'."""
        env = {"GEMINI_AUTH_MODE": "api"}
        assert resolve_gemini_auth_mode(env, cooldown_active=False) == "api"
        assert resolve_gemini_auth_mode(env, cooldown_active=True) == "api"

    def test_invalid_value_degrades_to_auto_cooldown_logic(self) -> None:
        """Invalid → normalize to auto → cooldown-aware."""
        env = {"GEMINI_AUTH_MODE": "garbage"}
        assert resolve_gemini_auth_mode(env, cooldown_active=False) == "api"
        assert resolve_gemini_auth_mode(env, cooldown_active=True) == "subscription"

    def test_oauth_alias_forces_subscription(self) -> None:
        env = {"GEMINI_AUTH_MODE": "oauth"}
        assert resolve_gemini_auth_mode(env, cooldown_active=False) == "subscription"

    def test_reads_real_cooldown_state_when_not_injected(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """End-to-end: with cooldown_active=None, resolver reads disk state."""
        monkeypatch.setenv("LU_GEMINI_COOLDOWN_PATH", str(tmp_path / "cd.json"))
        # No cooldown written → auto → api
        env: dict[str, str] = {}
        assert resolve_gemini_auth_mode(env) == "api"
        # Trip the cooldown → auto flips to subscription
        set_api_cooldown(3600)
        assert resolve_gemini_auth_mode(env) == "subscription"


# ── cooldown module ───────────────────────────────────────────────────


class TestCooldownPrimitives:
    """Cover the on-disk state machine: set / read / clear / expire."""

    def test_inactive_by_default(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.setenv("LU_GEMINI_COOLDOWN_PATH", str(tmp_path / "cd.json"))
        assert is_api_cooldown_active() is False
        assert cooldown_remaining_s() == 0

    def test_set_then_active(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.setenv("LU_GEMINI_COOLDOWN_PATH", str(tmp_path / "cd.json"))
        set_api_cooldown(3600)
        assert is_api_cooldown_active() is True
        # remaining ≈ 3600, allow 2s slack for test timing
        assert 3598 <= cooldown_remaining_s() <= 3600

    def test_expired_cooldown_reads_inactive(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """Cooldown in the past = inactive, without requiring manual clear."""
        monkeypatch.setenv("LU_GEMINI_COOLDOWN_PATH", str(tmp_path / "cd.json"))
        set_api_cooldown(3600)
        # Project into the future
        future = time.time() + 7200
        assert is_api_cooldown_active(now=future) is False
        assert cooldown_remaining_s(now=future) == 0

    def test_clear(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.setenv("LU_GEMINI_COOLDOWN_PATH", str(tmp_path / "cd.json"))
        set_api_cooldown(3600)
        assert is_api_cooldown_active() is True
        clear_api_cooldown()
        assert is_api_cooldown_active() is False

    def test_clear_when_absent_is_noop(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        monkeypatch.setenv("LU_GEMINI_COOLDOWN_PATH", str(tmp_path / "cd.json"))
        clear_api_cooldown()  # should not raise
        assert is_api_cooldown_active() is False

    def test_set_twice_keeps_later_expiry(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """Extending a cooldown never shortens it — latest expiry wins."""
        monkeypatch.setenv("LU_GEMINI_COOLDOWN_PATH", str(tmp_path / "cd.json"))
        set_api_cooldown(3600)
        first_remaining = cooldown_remaining_s()
        # A shorter subsequent 429 must NOT shrink the window
        set_api_cooldown(60)
        second_remaining = cooldown_remaining_s()
        assert second_remaining >= first_remaining - 2  # slack for test timing

    def test_corrupt_state_file_treated_as_inactive(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        path = tmp_path / "cd.json"
        monkeypatch.setenv("LU_GEMINI_COOLDOWN_PATH", str(path))
        path.write_text("{not valid json", "utf-8")
        assert is_api_cooldown_active() is False

    def test_no_probe_calls_in_cooldown_module(self) -> None:
        """Guarantee: the cooldown module has NO network / subprocess imports.

        Daily API quota is tight; the cooldown logic must NEVER do a
        probe call to decide whether cooldown should end. Inspect the
        module source to confirm.
        """
        import ast

        import ai_llm.cooldown as mod
        tree = ast.parse(Path(mod.__file__).read_text("utf-8"))
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])

        forbidden = {
            "requests", "urllib", "urllib2", "urllib3", "httpx",
            "subprocess", "socket", "http",
        }
        overlap = imported & forbidden
        assert not overlap, (
            f"cooldown.py imports forbidden modules {overlap} — daily "
            f"API quota forbids probe calls (#1384)"
        )


# ── Adapter env-strip wiring ──────────────────────────────────────────


class TestEnvStripWiring:
    """Regression guard: when resolver returns subscription, the adapter
    MUST actually strip API-key env vars. Otherwise flipping the mode is
    decorative. Structural test — catches future refactors that
    disconnect the two.
    """

    def test_adapter_strips_api_keys_when_cooldown_active(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        from agent_runtime.adapters.gemini import GeminiAdapter

        # Arrange: cooldown on, API key in env, no explicit auth mode
        monkeypatch.setenv("LU_GEMINI_COOLDOWN_PATH", str(tmp_path / "cd.json"))
        set_api_cooldown(3600)
        monkeypatch.setenv("GEMINI_API_KEY", "should-be-stripped")
        monkeypatch.delenv("GEMINI_AUTH_MODE", raising=False)

        plan = GeminiAdapter().build_invocation(
            prompt="test", mode="read-only", cwd=tmp_path,
            model=None, task_id=None, session_id=None, tool_config=None,
        )
        assert "GEMINI_API_KEY" in plan.env_unsets, (
            "Auto mode under active cooldown must strip GEMINI_API_KEY — "
            "otherwise the CLI keeps billing API and cooldown is moot."
        )

    def test_adapter_keeps_api_keys_when_cooldown_inactive(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        from agent_runtime.adapters.gemini import GeminiAdapter

        monkeypatch.setenv("LU_GEMINI_COOLDOWN_PATH", str(tmp_path / "cd.json"))
        clear_api_cooldown()
        monkeypatch.setenv("GEMINI_API_KEY", "should-be-kept")
        monkeypatch.delenv("GEMINI_AUTH_MODE", raising=False)

        plan = GeminiAdapter().build_invocation(
            prompt="test", mode="read-only", cwd=tmp_path,
            model=None, task_id=None, session_id=None, tool_config=None,
        )
        assert plan.env_unsets == (), (
            "Auto mode without cooldown must NOT strip keys — API is "
            "the default (faster)."
        )

    def test_adapter_preserves_api_keys_when_explicit_api(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        from agent_runtime.adapters.gemini import GeminiAdapter

        monkeypatch.setenv("LU_GEMINI_COOLDOWN_PATH", str(tmp_path / "cd.json"))
        set_api_cooldown(3600)  # even with cooldown active ...
        monkeypatch.setenv("GEMINI_AUTH_MODE", "api")  # explicit wins

        plan = GeminiAdapter().build_invocation(
            prompt="test", mode="read-only", cwd=tmp_path,
            model=None, task_id=None, session_id=None, tool_config=None,
        )
        assert plan.env_unsets == (), (
            "Explicit GEMINI_AUTH_MODE=api must not strip keys even "
            "under active cooldown."
        )


# ── Parse-response trips cooldown on real 429 only ────────────────────


class TestParseResponseCooldownTrip:
    """On a 429 while in API mode, parse_response MUST set the cooldown.
    On a 429 while on subscription, it must NOT — otherwise we'd steer
    the next auto-mode call INTO the exhausted path.
    """

    @staticmethod
    def _make_plan(env_unsets: tuple) -> object:
        """Minimal InvocationPlan stub for parse_response()."""
        from agent_runtime.adapters.base import InvocationPlan
        return InvocationPlan(
            cmd=["gemini"],
            cwd=Path("."),
            stdin_payload="",
            output_file=None,
            env_overrides={},
            env_unsets=env_unsets,
            liveness_paths=(),
        )

    def test_api_mode_429_sets_cooldown(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        from agent_runtime.adapters.gemini import GeminiAdapter

        monkeypatch.setenv("LU_GEMINI_COOLDOWN_PATH", str(tmp_path / "cd.json"))
        clear_api_cooldown()
        assert is_api_cooldown_active() is False

        plan = self._make_plan(env_unsets=())  # API mode — keys NOT stripped
        result = GeminiAdapter().parse_response(
            stdout="",
            stderr="429 RESOURCE_EXHAUSTED: quota exceeded",
            returncode=1,
            output_file=None,
            plan=plan,  # type: ignore[arg-type]
        )
        assert result.rate_limited is True
        assert is_api_cooldown_active() is True, (
            "Real 429 on API mode must trip the cooldown so subsequent "
            "auto-mode callers flip to subscription."
        )

    def test_subscription_mode_429_does_not_set_cooldown(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        from agent_runtime.adapters.gemini import GeminiAdapter
        from ai_llm.fallback import GEMINI_AUTH_ENV_VARS

        monkeypatch.setenv("LU_GEMINI_COOLDOWN_PATH", str(tmp_path / "cd.json"))
        clear_api_cooldown()

        # Plan with env_unsets set = caller was on subscription mode
        plan = self._make_plan(env_unsets=GEMINI_AUTH_ENV_VARS)
        result = GeminiAdapter().parse_response(
            stdout="",
            stderr="429 quota exceeded",
            returncode=1,
            output_file=None,
            plan=plan,  # type: ignore[arg-type]
        )
        assert result.rate_limited is True
        assert is_api_cooldown_active() is False, (
            "A 429 while already on subscription means subscription is "
            "exhausted. Tripping the cooldown would wrongly steer the "
            "next auto-mode call INTO that exhausted path."
        )

    def test_clean_response_does_not_trip_cooldown(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        from agent_runtime.adapters.gemini import GeminiAdapter

        monkeypatch.setenv("LU_GEMINI_COOLDOWN_PATH", str(tmp_path / "cd.json"))
        clear_api_cooldown()

        plan = self._make_plan(env_unsets=())
        long_response = "x" * 500  # long enough to avoid short-response path
        result = GeminiAdapter().parse_response(
            stdout=long_response,
            stderr="",
            returncode=0,
            output_file=None,
            plan=plan,  # type: ignore[arg-type]
        )
        assert result.ok is True
        assert result.rate_limited is False
        assert is_api_cooldown_active() is False, (
            "Successful calls must not trip cooldown — it's driven by "
            "real 429s only, never by liveness probing."
        )


# ── Ladder rung filtering (#1384, the thing biting the 14:00 batch) ───


class TestLadderAuthModeFiltering:
    """When GEMINI_AUTH_MODE=subscription or cooldown is active, the
    ladder must NOT include API rungs. Otherwise a wiki compile run
    wastes 3 × per_rung_timeout on rung-1 API before advancing — exactly
    the ~15-min silent hang the user hit at 14:00.
    """

    def test_auto_no_cooldown_includes_both(self) -> None:
        assert resolve_allowed_auth_modes({}, cooldown_active=False) == ("api", "oauth")

    def test_auto_with_cooldown_skips_api(self) -> None:
        assert resolve_allowed_auth_modes({}, cooldown_active=True) == ("oauth",)

    def test_explicit_subscription_skips_api(self) -> None:
        env = {"GEMINI_AUTH_MODE": "subscription"}
        assert resolve_allowed_auth_modes(env, cooldown_active=False) == ("oauth",)

    def test_explicit_oauth_alias_skips_api(self) -> None:
        env = {"GEMINI_AUTH_MODE": "oauth"}
        assert resolve_allowed_auth_modes(env, cooldown_active=False) == ("oauth",)

    def test_explicit_api_skips_oauth_even_under_cooldown(self) -> None:
        """Explicit API wins even if cooldown says skip. Fail-loudly path
        for debugging — if a user forces API they want to see the 429."""
        env = {"GEMINI_AUTH_MODE": "api"}
        assert resolve_allowed_auth_modes(env, cooldown_active=True) == ("api",)

    def test_ladder_oauth_only_has_three_rungs(self) -> None:
        ladder = build_gemini_ladder(allowed_auth_modes=("oauth",))
        assert len(ladder) == 3
        assert all(r.auth_mode == "oauth" for r in ladder)
        # Rung indices renumber to filtered total so log "Rung 1/3" is honest
        assert [r.index for r in ladder] == [1, 2, 3]
        assert all(r.total == 3 for r in ladder)

    def test_ladder_api_only_has_three_rungs(self) -> None:
        ladder = build_gemini_ladder(allowed_auth_modes=("api",))
        assert len(ladder) == 3
        assert all(r.auth_mode == "api" for r in ladder)

    def test_ladder_both_has_six_rungs_with_api_first_per_model(self) -> None:
        ladder = build_gemini_ladder(allowed_auth_modes=("api", "oauth"))
        assert len(ladder) == 6
        # API-first ordering preserves the "fast-path first" intent
        assert ladder[0].auth_mode == "api"
        assert ladder[1].auth_mode == "oauth"
        assert ladder[0].model == ladder[1].model

    def test_empty_allowed_modes_rejected(self) -> None:
        import pytest
        with pytest.raises(ValueError, match="allowed_auth_modes"):
            build_gemini_ladder(allowed_auth_modes=())


# ── Rate-limit classification (the bug that burned 15 min at 14:30) ──


class TestRateLimitClassification:
    """``is_gemini_rate_limited`` must return True for EVERY stderr that
    means "this rung will not answer, advance." Missing patterns here
    cause the ladder to retry the same rung 3× instead of advancing,
    which is exactly how #1384 Phase 1 shipped broken on 2026-04-21.
    """

    def test_matches_429(self) -> None:
        from ai_llm.fallback import is_gemini_rate_limited
        assert is_gemini_rate_limited("429 Too Many Requests")

    def test_matches_quota(self) -> None:
        from ai_llm.fallback import is_gemini_rate_limited
        assert is_gemini_rate_limited("Error: quota exceeded for project")

    def test_matches_rate_limited_word(self) -> None:
        from ai_llm.fallback import is_gemini_rate_limited
        assert is_gemini_rate_limited("Response: rate_limited")

    def test_matches_resource_exhausted(self) -> None:
        """GRPC status name — Gemini prints this in place of 429."""
        from ai_llm.fallback import is_gemini_rate_limited
        assert is_gemini_rate_limited("RESOURCE_EXHAUSTED: ...")

    def test_matches_no_capacity_available(self) -> None:
        """The exact string Gemini emitted that burned 15 min on rung 1
        at 14:30 today before this regression guard existed. A backend
        queue-full signal — must classify as rate-limited so the ladder
        advances to OAuth / flash / 2.5-pro instead of retrying the
        same overloaded model-auth combo three times."""
        from ai_llm.fallback import is_gemini_rate_limited
        assert is_gemini_rate_limited(
            "No capacity available for model gemini-3.1-pro-preview"
        )

    def test_case_insensitive(self) -> None:
        """Gemini capitalizes inconsistently; matching must be robust."""
        from ai_llm.fallback import is_gemini_rate_limited
        assert is_gemini_rate_limited("No Capacity Available in region")
        assert is_gemini_rate_limited("NO CAPACITY AVAILABLE")

    def test_clean_success_is_not_rate_limited(self) -> None:
        """Regression guard against an over-broad pattern. A normal
        response must NOT flip to rate_limited just because it mentions
        'capacity' or similar words in article content."""
        from ai_llm.fallback import is_gemini_rate_limited
        assert not is_gemini_rate_limited(
            "The lesson explains Ukrainian phonetics clearly."
        )
        assert not is_gemini_rate_limited("")
        assert not is_gemini_rate_limited(None)

    def test_no_capacity_triggers_rung_advance_not_retry(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """End-to-end behavior: when an API-rung outcome reports
        'No capacity available', ``run_gemini_fallback_ladder`` MUST
        advance to the next rung on the first occurrence. Before the
        fix, it retried the same rung 3× (elapsed burned on transient
        errors instead of actual work).
        """
        from ai_llm.cooldown import clear_api_cooldown
        from ai_llm.fallback import (
            AttemptOutcome,
            run_gemini_fallback_ladder,
        )

        monkeypatch.setenv("LU_GEMINI_COOLDOWN_PATH", str(tmp_path / "cd.json"))
        clear_api_cooldown()

        # Simulate: rung 1 API returns "No capacity", rung 1 OAuth succeeds.
        attempts_seen: list[tuple[str, int]] = []

        def runner(rung, attempt_idx, timeout_s) -> AttemptOutcome:
            attempts_seen.append((rung.auth_mode, rung.index))
            if rung.auth_mode == "api":
                return AttemptOutcome(
                    status="rate_limited",
                    elapsed_s=0.1,
                    stderr_excerpt="No capacity available",
                )
            return AttemptOutcome(
                status="success",
                elapsed_s=0.1,
                response_text="x" * 200,
            )

        # With no env override and no cooldown, ladder includes both modes.
        result = run_gemini_fallback_ladder(
            task_name="test-no-capacity",
            preferred_model="gemini-3.1-pro-preview",
            max_retries=3,
            attempt_runner=runner,
            logger=lambda _msg: None,  # silence output in tests
            sleep_fn=lambda _s, _r: None,  # don't actually sleep
            allowed_auth_modes=("api", "oauth"),
        )
        # Must have advanced to OAuth on the VERY FIRST rung-1 API attempt
        # (not retried api 3×). Pattern observed: api once, then oauth.
        assert result.ok, f"expected success, got {result.error_message}"
        api_attempts = [a for a in attempts_seen if a[0] == "api"]
        assert len(api_attempts) == 1, (
            f"expected API rung attempted ONCE before advancing, got "
            f"{len(api_attempts)} attempts: {attempts_seen}"
        )
