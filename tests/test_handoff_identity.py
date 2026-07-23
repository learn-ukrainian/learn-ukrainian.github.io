"""Run the launcher handoff-identity fixtures under the required pytest gate.

``scripts/audit/test_handoff_identity.sh`` exercises
``scripts/lib/handoff_identity.sh`` — the derivation that ``start-claude.sh``
uses to turn a Claude Code ``--agent`` selection into the right
``SESSION_HANDOFF_AGENT`` cold-start slot (e.g. ``infra-orchestrator`` →
``claude-infra``). This thin wrapper makes that mapping load-bearing in the
required ``Test (pytest)`` job, so the infra/folk cold-start collision cannot
silently regress.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_HOOK_TEST = _REPO_ROOT / "scripts" / "audit" / "test_handoff_identity.sh"
_HANDOFF_IDENTITY = _REPO_ROOT / "scripts" / "lib" / "handoff_identity.sh"


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")
def test_handoff_identity_fixtures() -> None:
    assert _HOOK_TEST.is_file(), f"missing identity test: {_HOOK_TEST}"
    result = subprocess.run(
        ["bash", str(_HOOK_TEST)],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, (
        f"identity fixtures failed (rc={result.returncode})\n"
        f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
    )
    assert "ok - handoff identity fixtures passed" in result.stdout


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")
@pytest.mark.parametrize(
    ("resolver", "expected"),
    [
        ("handoff_identity_for_epic", "claude-infra"),
        ("handoff_identity_for_gemini_epic", "gemini-infra"),
        ("handoff_identity_for_codex_epic", "codex-infra"),
    ],
)
def test_devops_alias_resolves_to_canonical_infra_slot(resolver: str, expected: str) -> None:
    result = subprocess.run(
        ["bash", "-c", 'source "$1"; "$2" devops', "bash", str(_HANDOFF_IDENTITY), resolver],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == expected


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")
@pytest.mark.parametrize(
    ("selector", "lane", "stream", "claude_slot", "gemini_slot", "grok_slot"),
    [
        ("infra.fleet-comms", "infra", "epic:4707", "claude-infra", "gemini-infra", "grok-infra"),
        ("infra.devops", "infra", "epic:4707", "claude-infra", "gemini-infra", "grok-infra"),
        ("devops", "infra", "epic:4707", "claude-infra", "gemini-infra", "grok-infra"),
        ("atlas.practice", "atlas", "epic:4387", "claude-atlas", "gemini-atlas", "grok-atlas"),
        ("practice-hub", "atlas", "epic:4387", "claude-atlas", "gemini-atlas", "grok-atlas"),
        ("hramatka.lessons", "hramatka", "epic:4542", "claude-hramatka", "gemini-hramatka", "grok-hramatka"),
        ("corpus", "corpus", "epic:4706", "claude-corpus", "gemini-corpus", "grok-corpus"),
        ("corpus-channels", "corpus", "epic:4706", "claude-corpus", "gemini-corpus", "grok-corpus"),
    ],
)
def test_dot_notation_selector_resolves_stream_and_provider_handoff(
    selector: str,
    lane: str,
    stream: str,
    claude_slot: str,
    gemini_slot: str,
    grok_slot: str,
) -> None:
    result = subprocess.run(
        [
            "bash",
            "-c",
            'source "$1"; printf "%s|%s|%s|%s|%s|%s" "$(launcher_selector_lane "$2")" "$(launcher_selector_stream "$2")" "$(handoff_identity_for_epic "$2")" "$(handoff_identity_for_gemini_epic "$2")" "$(handoff_identity_for_grok_epic "$2")" "$(handoff_identity_for_codex_epic "$2")"',
            "bash",
            str(_HANDOFF_IDENTITY),
            selector,
        ],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == f"{lane}|{stream}|{claude_slot}|{gemini_slot}|{grok_slot}|codex-{lane}"


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")
@pytest.mark.parametrize("arguments", [["--epic", "atlas.epic"], ["--epic=atlas.epic"]])
def test_legacy_epic_suffix_normalizes_before_selector_resolution(arguments: list[str]) -> None:
    result = subprocess.run(
        [
            "bash",
            "-c",
            'source "$1"; epic="$(handoff_epic_from_argv "${@:2}")"; printf "%s|%s" "$epic" "$(launcher_selector_lane "$epic")"',
            "bash",
            str(_HANDOFF_IDENTITY),
            *arguments,
        ],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "atlas|atlas"


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")
def test_unknown_selector_fails_closed() -> None:
    result = subprocess.run(
        ["bash", "-c", 'source "$1"; launcher_selector_resolve unknown', "bash", str(_HANDOFF_IDENTITY)],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 1
    assert result.stdout == ""


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")
@pytest.mark.parametrize(
    "launcher",
    [
        "start-gemini-drive.sh",
        "start-grok-drive.sh",
        "start-sonnet-drive.sh",
        "start-claude.sh",
    ],
)
def test_launcher_help_documents_allowlisted_dot_notation(launcher: str) -> None:
    result = subprocess.run(
        ["bash", str(_REPO_ROOT / launcher), "--help"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert "Valid lane selectors:" in result.stdout
    assert "infra.fleet-comms" in result.stdout
    assert "atlas.practice" in result.stdout


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")
@pytest.mark.parametrize(
    ("launcher", "arguments", "expected_code"),
    [
        ("start-gemini-drive.sh", ["unknown"], 2),
        ("start-grok-drive.sh", ["unknown"], 2),
        ("start-sonnet-drive.sh", ["unknown"], 2),
        ("start-claude.sh", ["--epic", "unknown"], 1),
    ],
)
def test_launcher_unknown_selector_fails_closed(launcher: str, arguments: list[str], expected_code: int) -> None:
    result = subprocess.run(
        ["bash", str(_REPO_ROOT / launcher), *arguments],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == expected_code
    assert "unknown lane selector 'unknown'" in result.stderr
    assert "Valid lane selectors:" in result.stderr
