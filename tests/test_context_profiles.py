from __future__ import annotations

import os
import shlex
import subprocess
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
        "main_model_id": "gpt-5.6-sol",
        "model_id_patterns": [r"^gpt-5\.6-sol$"],
        "main_context_window_tokens": 372_000,
        "auto_compact_capacity_tokens": 353_000,
        "cold_start_profile": "compact",
        "cold_start_budget_tokens": 37_200,
        "rollover_warning_percentages": [75.0, 85.0, 92.0],
    }
    assert profiles["sol_lead"] == {
        "profile_id": "sol_lead",
        "transport": "claudex",
        "main_model_id": "gpt-5.6-sol",
        "model_id_patterns": [r"^gpt-5\.6-sol$"],
        "main_context_window_tokens": 372_000,
        "auto_compact_capacity_tokens": 353_000,
        "cold_start_profile": "compact",
        "cold_start_budget_tokens": 37_200,
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
    assert profiles["kimicc_k27"]["main_context_window_tokens"] == 262_144
    assert profiles["kimicc_k27"]["auto_compact_capacity_tokens"] == 249_036
    assert profiles["kimicc_k27_highspeed"]["main_model_id"] == "kimi-k2.7-code-highspeed"


def test_native_codex_profile_accepts_sol_and_rejects_other_models() -> None:
    trusted = resolve_profile("native_codex", "gpt-5.6-sol")
    mismatch = resolve_profile("native_codex", "gpt-5.6-terra")

    assert trusted["profile_id"] == "native_codex"
    assert trusted["transport"] == "native_codex"
    assert trusted["trusted"]
    assert trusted["main_context_window_tokens"] == 372_000
    assert mismatch["profile_id"] == "fallback"
    assert mismatch["resolution_reason"] == "model-mismatch"
    assert mismatch["expected_profile_id"] == "native_codex"


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
    profiles["sol_lead"]["cold_start_budget_tokens"] = 37_201
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
            os.fspath(PROJECT_ROOT / ".venv" / "bin" / "python"),
            os.fspath(RESOLVER),
            "--profile",
            "sol_lead",
            "--model",
            "gpt-5.6-sol",
            "--format",
            "env0",
        ],
        check=True,
        capture_output=True,
    )
    fields = result.stdout.split(b"\0")
    assert fields[-1] == b""
    pairs = dict(zip(fields[0:-1:2], fields[1:-1:2], strict=True))

    assert {key.decode() for key in pairs} == EXPECTED_ENV0_KEYS
    assert pairs[b"PROFILE_ID"] == b"sol_lead"
    assert pairs[b"MAIN_CONTEXT_WINDOW_TOKENS"] == b"372000"
    assert pairs[b"AUTO_COMPACT_CAPACITY_TOKENS"] == b"353000"
    assert pairs[b"TRUSTED"] == b"1"
    assert b"export " not in result.stdout


def test_shell_resolver_exports_only_project_private_fields() -> None:
    command = f"""
        set -euo pipefail
        PROJECT_DIR={shlex.quote(os.fspath(PROJECT_ROOT))}
        env | LC_ALL=C sort
        printf '%s\n' '__AFTER_PROFILE_RESOLUTION__'
        source {shlex.quote(os.fspath(SHELL_RESOLVER))}
        resolve_context_profile sol_lead gpt-5.6-sol
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
    assert exported["LEARN_UKRAINIAN_MAIN_CONTEXT_WINDOW_TOKENS"] == "372000"
    assert "eval " not in SHELL_RESOLVER.read_text(encoding="utf-8")
