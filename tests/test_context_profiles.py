from __future__ import annotations

import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from scripts.lib.context_profiles import (
    CONFIG_PATH,
    ContextProfileError,
    get_profile,
    load_registry,
    resolve_profile,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESOLVER = PROJECT_ROOT / "scripts" / "lib" / "context_profiles.py"
SHELL_RESOLVER = PROJECT_ROOT / "scripts" / "lib" / "profile_resolver.sh"
EXPECTED_ENV0_KEYS = {
    "PROFILE_ID",
    "TRANSPORT",
    "MAIN_MODEL_ID",
    "MAIN_CONTEXT_WINDOW_TOKENS",
    "AUTO_COMPACT_CAPACITY_TOKENS",
    "COLD_START_PROFILE",
    "COLD_START_BUDGET_TOKENS",
    "ROLLOVER_WARNING_PERCENTAGES",
    "ROLLOVER_MODE",
    "REQUESTED_PROFILE_ID",
    "REQUESTED_MODEL_ID",
    "RESOLUTION_REASON",
    "TRUSTED",
    "MODEL_MISMATCH",
    "EXPECTED_PROFILE_ID",
    "EXPECTED_MAIN_MODEL_ID",
    "EXPECTED_MAIN_CONTEXT_WINDOW_TOKENS",
}


def _write_registry(tmp_path: Path, profiles: dict[str, dict[str, object]]) -> Path:
    path = tmp_path / "profiles.yaml"
    path.write_text(
        yaml.safe_dump({"version": 1, "profiles": profiles}, sort_keys=False),
        encoding="utf-8",
    )
    return path


def test_production_registry_separates_sol_capacity_values() -> None:
    profiles = load_registry(CONFIG_PATH)["profiles"]

    assert profiles["native_codex"] == {
        "profile_id": "native_codex",
        "transport": "native_codex",
        "main_model_id": "gpt-6.1-sol",
        "model_id_patterns": [r"^(gpt-6\.1-sol|gpt-6-luna)$"],
        "main_context_window_tokens": 272_000,
        "auto_compact_capacity_tokens": None,
        "cold_start_profile": "compact",
        "cold_start_budget_tokens": 27_200,
        "rollover_warning_percentages": [75.0, 85.0, 92.0],
    }
    assert profiles["sol_lead"] == {
        "profile_id": "sol_lead",
        "transport": "claudex",
        "main_model_id": "gpt-6.1-sol",
        "model_id_patterns": [r"^gpt-6\.1-sol$"],
        "main_context_window_tokens": 272_000,
        "auto_compact_capacity_tokens": 258_400,
        "cold_start_profile": "compact",
        "cold_start_budget_tokens": 27_200,
        "rollover_warning_percentages": [75.0, 85.0, 92.0],
    }
    assert profiles["native_claude"]["auto_compact_capacity_tokens"] is None
    assert profiles["kimicc_k3"] == {
        "profile_id": "kimicc_k3",
        "transport": "kimicc",
        "main_model_id": "kimi-k3[1m]",
        "model_id_patterns": [r"^kimi-k3(\[1m\])?$", r"^k3$"],
        "main_context_window_tokens": 1_048_576,
        "auto_compact_capacity_tokens": 996_147,
        "cold_start_profile": "compact",
        "cold_start_budget_tokens": 104_857,
        "rollover_warning_percentages": [75.0, 85.0, 92.0],
    }
    assert profiles["kimicc_k3_256k"] == {
        "profile_id": "kimicc_k3_256k",
        "transport": "kimicc",
        "main_model_id": "kimi-k3-256k",
        "model_id_patterns": [r"^kimi-k3-256k$", r"^k3-256k$"],
        "main_context_window_tokens": 262_144,
        "auto_compact_capacity_tokens": 249_036,
        "cold_start_profile": "compact",
        "cold_start_budget_tokens": 26_214,
        "rollover_warning_percentages": [75.0, 85.0, 92.0],
    }
    assert profiles["kimicc_k27"]["main_context_window_tokens"] == 262_144
    assert profiles["kimicc_k27"]["auto_compact_capacity_tokens"] == 249_036
    assert profiles["kimicc_k27_highspeed"]["main_model_id"] == "kimi-k2.7-code-highspeed"
    assert profiles["glmcc_glm53"] == {
        "profile_id": "glmcc_glm53",
        "transport": "glmcc",
        "main_model_id": "glm-5.3",
        "model_id_patterns": [r"^glm-5\.3$", r"^glm53$", r"^glm$"],
        "main_context_window_tokens": 1_048_576,
        "auto_compact_capacity_tokens": 996_147,
        "cold_start_profile": "compact",
        "cold_start_budget_tokens": 104_857,
        "rollover_warning_percentages": [75.0, 85.0, 92.0],
    }


def test_native_claude_hands_off_at_750k_and_waits_for_operator_restart() -> None:
    """#8511: 650k heads-up, 700k finish the unit, 750k hand off and wait."""
    profile = load_registry(CONFIG_PATH)["profiles"]["native_claude"]
    resolved = resolve_profile("native_claude", "claude-opus-5-5")

    assert profile["rollover_warning_percentages"] == [65.0, 70.0, 75.0]
    assert profile["rollover_mode"] == "operator_restart"
    window = profile["main_context_window_tokens"]
    assert [int(window * pct / 100) for pct in profile["rollover_warning_percentages"]] == [
        650_000,
        700_000,
        750_000,
    ]
    assert resolved["trusted"]
    assert resolved["rollover_mode"] == "operator_restart"


def test_only_native_claude_declares_a_rollover_mode() -> None:
    """Every other profile keeps the default continuation behaviour unchanged."""
    raw = load_registry(CONFIG_PATH)["profiles"]

    assert [key for key, profile in raw.items() if "rollover_mode" in profile] == ["native_claude"]
    assert resolve_profile("sol_lead", "gpt-6.1-sol")["rollover_mode"] == "continuation"
    assert resolve_profile("kimicc_k3", "kimi-k3[1m]")["rollover_mode"] == "continuation"
    assert resolve_profile()["rollover_mode"] == "continuation"
    # A model mismatch falls back, so it can never inherit operator_restart.
    assert resolve_profile("native_claude", "gpt-6.1-sol")["rollover_mode"] == "continuation"


def test_registry_rejects_unknown_rollover_mode(tmp_path: Path) -> None:
    profiles = load_registry(CONFIG_PATH)["profiles"]
    profiles["native_claude"]["rollover_mode"] = "wait"
    path = _write_registry(tmp_path, profiles)

    with pytest.raises(ContextProfileError, match="rollover_mode must be one of"):
        load_registry(path)


def test_no_context_profile_routes_to_retired_gpt56() -> None:
    for profile in load_registry(CONFIG_PATH)["profiles"].values():
        assert not profile["main_model_id"].startswith("gpt-5.6-")
        for pattern in profile["model_id_patterns"]:
            for retired in ("gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna", "gpt-6-sol", "gpt-6-astra"):
                assert re.fullmatch(pattern, retired) is None


@pytest.mark.parametrize("model", ["gpt-6-luna", "gpt-6.1-sol"])
def test_native_codex_profile_accepts_gpt6_and_rejects_other_models(model: str) -> None:
    trusted = resolve_profile("native_codex", model)
    mismatch = resolve_profile("native_codex", "gpt-5.6-terra")

    assert trusted["profile_id"] == "native_codex"
    assert trusted["transport"] == "native_codex"
    assert trusted["trusted"]
    assert trusted["main_model_id"] == model
    assert trusted["expected_main_model_id"] == model
    assert trusted["main_context_window_tokens"] == 272_000
    assert mismatch["profile_id"] == "fallback"
    assert mismatch["resolution_reason"] == "model-mismatch"
    assert mismatch["expected_profile_id"] == "native_codex"


def test_kimicc_k3_256k_profile_is_distinct_from_the_1m_k3_profile() -> None:
    """k3-256k must never silently borrow the 1M kimicc_k3 window."""
    trusted = resolve_profile("kimicc_k3_256k", "kimi-k3-256k")
    alias = resolve_profile("kimicc_k3_256k", "k3-256k")
    mismatch = resolve_profile("kimicc_k3_256k", "kimi-k3[1m]")

    assert trusted["profile_id"] == "kimicc_k3_256k"
    assert trusted["trusted"]
    assert trusted["main_context_window_tokens"] == 262_144
    assert alias["trusted"]
    assert mismatch["profile_id"] == "fallback"
    assert mismatch["resolution_reason"] == "model-mismatch"
    assert mismatch["expected_profile_id"] == "kimicc_k3_256k"


def test_resolution_fails_closed_without_trusted_route_metadata() -> None:
    missing = resolve_profile()
    unknown = resolve_profile("not-a-route", "claude-opus-4-8")
    mismatch = resolve_profile("native_claude", "gpt-5.6-sol")

    assert (missing["profile_id"], missing["resolution_reason"]) == (
        "fallback",
        "missing-profile",
    )
    assert (unknown["profile_id"], unknown["resolution_reason"]) == (
        "fallback",
        "unknown-profile",
    )
    assert (mismatch["profile_id"], mismatch["resolution_reason"]) == (
        "fallback",
        "model-mismatch",
    )
    assert missing["main_context_window_tokens"] == 0
    assert missing["auto_compact_capacity_tokens"] is None
    assert not missing["trusted"]
    assert mismatch["model_mismatch"]
    assert mismatch["expected_main_context_window_tokens"] == 1_000_000


@pytest.mark.parametrize(
    ("model_id", "expected_profile"),
    [
        ("claude-opus-4-8", "native_claude"),
        ("claude-sonnet-5", "native_claude"),
        ("opus", "native_claude"),
    ],
)
def test_native_profile_matches_model_family(
    model_id: str, expected_profile: str
) -> None:
    resolved = resolve_profile("native_claude", model_id)

    assert resolved["profile_id"] == expected_profile
    assert resolved["trusted"]
    assert resolved["main_context_window_tokens"] == 1_000_000
    assert resolved["auto_compact_capacity_tokens"] is None


def test_get_profile_uses_validated_fallback_for_unknown_id() -> None:
    assert get_profile("does-not-exist")["profile_id"] == "fallback"


def test_registry_rejects_compact_budget_over_ten_percent(tmp_path: Path) -> None:
    profiles = load_registry(CONFIG_PATH)["profiles"]
    profiles["sol_lead"]["cold_start_budget_tokens"] = 27_201
    path = _write_registry(tmp_path, profiles)

    with pytest.raises(ContextProfileError, match="cannot exceed 10%"):
        load_registry(path)


def test_registry_rejects_emergency_warning_after_auto_compaction(
    tmp_path: Path,
) -> None:
    profiles = load_registry(CONFIG_PATH)["profiles"]
    profiles["sol_lead"]["rollover_warning_percentages"] = [75.0, 85.0, 95.0]
    path = _write_registry(tmp_path, profiles)

    with pytest.raises(ContextProfileError, match="must fire before"):
        load_registry(path)


def test_env0_output_is_exact_allow_list() -> None:
    result = subprocess.run(
        [
            sys.executable,
            os.fspath(RESOLVER),
            "--profile",
            "sol_lead",
            "--model",
            "gpt-6.1-sol",
            "--format",
            "env0",
        ],
        check=True,
        capture_output=True,
        timeout=30,
    )
    fields = result.stdout.split(b"\0")
    assert fields[-1] == b""
    pairs = dict(zip(fields[0:-1:2], fields[1:-1:2], strict=True))

    assert {key.decode() for key in pairs} == EXPECTED_ENV0_KEYS
    assert pairs[b"PROFILE_ID"] == b"sol_lead"
    assert pairs[b"MAIN_CONTEXT_WINDOW_TOKENS"] == b"272000"
    assert pairs[b"AUTO_COMPACT_CAPACITY_TOKENS"] == b"258400"
    assert pairs[b"TRUSTED"] == b"1"
    assert pairs[b"ROLLOVER_MODE"] == b"continuation"
    assert b"export " not in result.stdout


def test_shell_resolver_exports_only_project_private_fields() -> None:
    command = f"""
        set -euo pipefail
        PROJECT_DIR={shlex.quote(os.fspath(PROJECT_ROOT))}
        CLAUDE_PROFILE_RESOLVER_PYTHON={shlex.quote(sys.executable)}
        env | LC_ALL=C sort
        printf '%s\n' '__AFTER_PROFILE_RESOLUTION__'
        source {shlex.quote(os.fspath(SHELL_RESOLVER))}
        resolve_context_profile sol_lead gpt-6.1-sol
        env | LC_ALL=C sort
    """
    result = subprocess.run(
        ["bash", "-c", command],
        check=True,
        capture_output=True,
        text=True,
        env={
            "HOME": os.environ["HOME"],
            "PATH": os.environ["PATH"],
            "TMPDIR": os.environ.get("TMPDIR", "/tmp"),
        },
        timeout=30,
    )
    before_output, after_output = result.stdout.split(
        "__AFTER_PROFILE_RESOLUTION__\n", 1
    )
    before = dict(
        line.split("=", 1)
        for line in before_output.splitlines()
        if "=" in line
    )
    after = dict(
        line.split("=", 1)
        for line in after_output.splitlines()
        if "=" in line
    )
    exported = {
        key: value
        for key, value in after.items()
        if key.startswith("LEARN_UKRAINIAN_")
    }

    assert set(after) - set(before) == set(exported)
    assert set(exported) == {f"LEARN_UKRAINIAN_{key}" for key in EXPECTED_ENV0_KEYS}
    assert exported["LEARN_UKRAINIAN_PROFILE_ID"] == "sol_lead"
    assert exported["LEARN_UKRAINIAN_MAIN_CONTEXT_WINDOW_TOKENS"] == "272000"
    assert "eval " not in SHELL_RESOLVER.read_text(encoding="utf-8")


def _run_with_old_resolver(
    tmp_path: Path,
    *,
    omitted: str,
    profile_id: str = "native_claude",
    model_id: str = "claude-opus-5-5",
    project_dir: Path = PROJECT_ROOT,
) -> subprocess.CompletedProcess[str]:
    """Pair this parser with a resolver that predates a field, as a launcher
    pointing CLAUDE_PROFILE_RESOLVER_PY at another checkout can (#8511)."""
    old_resolver = tmp_path / "old_context_profiles.py"
    fields = {key: "x" for key in EXPECTED_ENV0_KEYS if key != omitted}
    fields["PROFILE_ID"] = profile_id
    old_resolver.write_text(
        "import sys\n"
        f"for key, value in {sorted(fields.items())!r}:\n"
        "    sys.stdout.write(key + '\\0' + value + '\\0')\n",
        encoding="utf-8",
    )
    command = f"""
        set -uo pipefail
        PROJECT_DIR={shlex.quote(os.fspath(project_dir))}
        CLAUDE_PROFILE_RESOLVER_PYTHON={shlex.quote(sys.executable)}
        CLAUDE_PROFILE_RESOLVER_PY={shlex.quote(os.fspath(old_resolver))}
        source {shlex.quote(os.fspath(SHELL_RESOLVER))}
        resolve_context_profile native_claude {shlex.quote(model_id)} || exit 7
        printf '%s|%s\\n' "$LEARN_UKRAINIAN_PROFILE_ID" "$LEARN_UKRAINIAN_ROLLOVER_MODE"
    """
    return subprocess.run(
        ["bash", "-c", command],
        capture_output=True,
        text=True,
        env={"HOME": os.environ["HOME"], "PATH": os.environ["PATH"], "TMPDIR": os.fspath(tmp_path)},
        timeout=30,
        check=False,
    )


def test_old_resolver_without_rollover_mode_takes_it_from_the_current_contract(tmp_path: Path) -> None:
    """A resolver that predates ROLLOVER_MODE must not silently downgrade native
    Claude to continuation; the mode comes from this checkout's profile YAML."""
    result = _run_with_old_resolver(tmp_path, omitted="ROLLOVER_MODE")

    assert result.returncode == 0, result.stderr
    assert result.stdout == "native_claude|operator_restart\n"


def test_old_resolver_without_rollover_mode_keeps_continuation_profiles(tmp_path: Path) -> None:
    result = _run_with_old_resolver(tmp_path, omitted="ROLLOVER_MODE", profile_id="fallback", model_id="gpt-6.1-sol")

    assert result.returncode == 0, result.stderr
    assert result.stdout == "fallback|continuation\n"


@pytest.mark.parametrize("case", ["profile_disagrees", "contract_missing"])
def test_old_resolver_without_rollover_mode_fails_loudly_when_contract_cannot_answer(
    tmp_path: Path, case: str
) -> None:
    if case == "profile_disagrees":
        result = _run_with_old_resolver(tmp_path, omitted="ROLLOVER_MODE", profile_id="sol_lead")
    else:
        result = _run_with_old_resolver(tmp_path, omitted="ROLLOVER_MODE", project_dir=tmp_path / "no-checkout")

    assert result.returncode == 7
    assert result.stdout == ""
    assert "omitted ROLLOVER_MODE and the current contract could not supply it" in result.stderr


def test_shell_resolver_rejects_any_other_missing_field(tmp_path: Path) -> None:
    result = _run_with_old_resolver(tmp_path, omitted="TRUSTED")

    assert result.returncode == 7
    assert "invalid field stream" in result.stderr
