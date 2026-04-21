"""Tests for Gemini auth-mode resolution (#1384 Phase 1, AC3).

Covers the new ``auto`` default that detects on-disk OAuth credentials
and flips to subscription mode instead of silently keeping API-mode
billing active for Ultra-authenticated users.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Repo-root shim (same pattern as other tests in this directory).
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from agent_runtime.adapters.gemini import (
    _normalize_gemini_auth_mode,
    _oauth_creds_present,
    resolve_gemini_auth_mode,
)

# ── _oauth_creds_present ──────────────────────────────────────────────


class TestOAuthCredsPresent:
    def test_returns_true_for_non_empty_file(self, tmp_path: Path) -> None:
        creds = tmp_path / "oauth_creds.json"
        creds.write_text('{"token": "abc"}', "utf-8")
        assert _oauth_creds_present(creds) is True

    def test_returns_false_for_missing_file(self, tmp_path: Path) -> None:
        missing = tmp_path / "does_not_exist.json"
        assert _oauth_creds_present(missing) is False

    def test_returns_false_for_zero_byte_file(self, tmp_path: Path) -> None:
        """Zero-byte file = CLI would reject; treat as absent so auto falls to api."""
        creds = tmp_path / "empty.json"
        creds.touch()
        assert _oauth_creds_present(creds) is False

    def test_returns_false_for_directory(self, tmp_path: Path) -> None:
        dir_path = tmp_path / "oauth_creds.json"
        dir_path.mkdir()
        assert _oauth_creds_present(dir_path) is False


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
        """Unknown strings degrade to auto for backward compatibility."""
        assert _normalize_gemini_auth_mode("garbage") == "auto"
        assert _normalize_gemini_auth_mode("🐙") == "auto"


# ── resolve_gemini_auth_mode (the behavior change for #1384) ──────────


class TestResolveAuthMode:
    """The headline behavior change: ``auto`` (default) now prefers
    subscription when OAuth creds are on disk, instead of silently
    leaving GEMINI_API_KEY in place and billing API mode.
    """

    def test_unset_with_oauth_creds_resolves_to_subscription(self, tmp_path: Path) -> None:
        """#1384: Ultra-authenticated user with key in shell → prefer subscription."""
        creds = tmp_path / "oauth_creds.json"
        creds.write_text('{"token": "x"}', "utf-8")
        env: dict[str, str] = {}  # GEMINI_AUTH_MODE unset
        assert resolve_gemini_auth_mode(env, creds_path=creds) == "subscription"

    def test_unset_without_oauth_creds_resolves_to_api(self, tmp_path: Path) -> None:
        """No subscription session on disk → fall through to API mode."""
        missing = tmp_path / "nope.json"
        env: dict[str, str] = {}
        assert resolve_gemini_auth_mode(env, creds_path=missing) == "api"

    def test_explicit_subscription_wins_over_missing_creds(self, tmp_path: Path) -> None:
        """User can force subscription even with no creds (CLI will error usefully)."""
        missing = tmp_path / "nope.json"
        env = {"GEMINI_AUTH_MODE": "subscription"}
        assert resolve_gemini_auth_mode(env, creds_path=missing) == "subscription"

    def test_explicit_api_wins_over_present_creds(self, tmp_path: Path) -> None:
        """User can force API mode even when subscription is available."""
        creds = tmp_path / "oauth_creds.json"
        creds.write_text('{"token": "x"}', "utf-8")
        env = {"GEMINI_AUTH_MODE": "api"}
        assert resolve_gemini_auth_mode(env, creds_path=creds) == "api"

    def test_explicit_auto_with_creds(self, tmp_path: Path) -> None:
        """Literal ``auto`` detects creds same as unset."""
        creds = tmp_path / "oauth_creds.json"
        creds.write_text('{"token": "x"}', "utf-8")
        env = {"GEMINI_AUTH_MODE": "auto"}
        assert resolve_gemini_auth_mode(env, creds_path=creds) == "subscription"

    def test_explicit_auto_without_creds(self, tmp_path: Path) -> None:
        missing = tmp_path / "nope.json"
        env = {"GEMINI_AUTH_MODE": "auto"}
        assert resolve_gemini_auth_mode(env, creds_path=missing) == "api"

    def test_invalid_value_degrades_to_auto_detection(self, tmp_path: Path) -> None:
        """Invalid → normalize to ``auto`` → then detect creds."""
        creds = tmp_path / "oauth_creds.json"
        creds.write_text('{"token": "x"}', "utf-8")
        env = {"GEMINI_AUTH_MODE": "garbage"}
        assert resolve_gemini_auth_mode(env, creds_path=creds) == "subscription"

    def test_oauth_alias_forces_subscription_without_creds(self, tmp_path: Path) -> None:
        """Normalizer maps `oauth` → `subscription`; explicit value wins."""
        missing = tmp_path / "nope.json"
        env = {"GEMINI_AUTH_MODE": "oauth"}
        assert resolve_gemini_auth_mode(env, creds_path=missing) == "subscription"


# ── Env-strip wiring guarantee ────────────────────────────────────────


class TestEnvStripWiring:
    """Regression guard: when resolver returns subscription, the adapter
    MUST actually strip API-key env vars. Otherwise flipping the default
    is decorative. Structural test so a future refactor can't silently
    disconnect the two.
    """

    def test_adapter_strips_api_keys_when_resolver_returns_subscription(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        from agent_runtime.adapters.gemini import GeminiAdapter

        # Plant creds so auto → subscription, and a key in env so we can
        # verify the adapter's env_unsets actually targets it.
        creds = tmp_path / "oauth_creds.json"
        creds.write_text('{"token": "x"}', "utf-8")
        monkeypatch.setattr(
            "agent_runtime.adapters.gemini._GEMINI_OAUTH_CREDS_PATH", creds
        )
        monkeypatch.setenv("GEMINI_API_KEY", "should-be-stripped")
        monkeypatch.delenv("GEMINI_AUTH_MODE", raising=False)

        adapter = GeminiAdapter()
        plan = adapter.build_invocation(
            prompt="test",
            mode="read-only",
            cwd=tmp_path,
            model=None,
            task_id=None,
            session_id=None,
            tool_config=None,
        )
        # env_unsets should include GEMINI_API_KEY (the whole
        # GEMINI_AUTH_ENV_VARS tuple, in fact).
        assert "GEMINI_API_KEY" in plan.env_unsets, (
            "Auto-detected subscription mode must strip GEMINI_API_KEY from "
            "the subprocess env — otherwise the Gemini CLI silently uses "
            "API mode and burns the quota."
        )

    def test_adapter_preserves_api_keys_when_explicit_api(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        from agent_runtime.adapters.gemini import GeminiAdapter

        creds = tmp_path / "oauth_creds.json"
        creds.write_text('{"token": "x"}', "utf-8")
        monkeypatch.setattr(
            "agent_runtime.adapters.gemini._GEMINI_OAUTH_CREDS_PATH", creds
        )
        monkeypatch.setenv("GEMINI_AUTH_MODE", "api")

        adapter = GeminiAdapter()
        plan = adapter.build_invocation(
            prompt="test",
            mode="read-only",
            cwd=tmp_path,
            model=None,
            task_id=None,
            session_id=None,
            tool_config=None,
        )
        assert plan.env_unsets == (), (
            "Explicit GEMINI_AUTH_MODE=api must not strip keys"
        )
