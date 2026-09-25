"""The launcher refuses unregistered handoff slots and every mintable one is registered (#8303).

``scripts/config/area_assignments.yaml`` is the roster of addressable slots.  Its header says
"do not add rows without a mintable selector"; these tests enforce that rule in both
directions and prove the launcher fails closed instead of minting ``<provider>-<lane>``.
"""

from __future__ import annotations

import csv
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from scripts.ai_agent_bridge import _channels
from scripts.orchestration import handoff_slot_registry as registry

REPO = Path(__file__).resolve().parents[1]
HANDOFF_IDENTITY = REPO / "scripts" / "lib" / "handoff_identity.sh"
ALIASES = REPO / "scripts" / "config" / "launcher_stream_aliases.tsv"
ISSUE_STREAMS = REPO / "scripts" / "config" / "issue_streams.yaml"
PROVIDERS = ("claude", "codex", "gemini", "grok", "kimi", "cursor")

# Registry stream keys that no compatibility alias covers and no roster row backs.
# Each must be refused, never minted (#8303).  Widening the roster or adding an alias
# removes a key from this list; it must never be silently accepted while unregistered.
UNREGISTERED_SELECTORS = (
    "atlas-practice",
    "core-quality",
    "curriculum-upgrade",
    "docs-knowledge",
    "infra-harness",
    "seminars-cross",
    "infra.atlas-practice",
)

pytestmark = pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")


def _helper_root() -> Path:
    """Root holding the shared interpreter (dispatch worktrees carry no ``.venv``)."""
    if (REPO / ".venv" / "bin" / "python").exists():
        return REPO
    return Path(sys.prefix).parent


def _bash(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "LC_DURABLE_HELPER_ROOT": str(_helper_root())}
    return subprocess.run(
        ["bash", "-c", script, "bash", *args],
        cwd=REPO,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


def _launcher(*args: str, dry_run: bool = True, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    launch_env = {**os.environ, "LAUNCHER_DRY_RUN": "1" if dry_run else "0"}
    launch_env.update(env or {})
    return subprocess.run(
        [str(REPO / "start-claude-driver.sh"), *args],
        cwd=REPO,
        env=launch_env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


def _alias_selectors() -> list[str]:
    with ALIASES.open(encoding="utf-8", newline="") as handle:
        rows = [row for row in csv.reader(handle, delimiter="\t") if row and not row[0].startswith("#")]
    return [row[0] for row in rows]


def _registry_stream_keys() -> list[str]:
    return list(yaml.safe_load(ISSUE_STREAMS.read_text(encoding="utf-8"))["streams"])


def _candidate_selectors() -> list[str]:
    """Every selector shape the launcher can resolve: aliases, registry keys, ``infra.<key>``."""
    keys = _registry_stream_keys()
    return sorted({*_alias_selectors(), *keys, *(f"infra.{key}" for key in keys)})


def _minted_lanes(selectors: list[str]) -> dict[str, str]:
    """selector -> lane for those the launcher's selector table resolves (one bash call)."""
    script = 'source "$1"; shift; for s in "$@"; do l="$(launcher_selector_lane "$s" 2>/dev/null)" && printf "%s\\t%s\\n" "$s" "$l"; done'
    result = _bash(script, str(HANDOFF_IDENTITY), *selectors)
    assert result.returncode == 0, result.stderr
    return dict(line.split("\t") for line in result.stdout.splitlines())


def _gate(provider: str, selector: str) -> subprocess.CompletedProcess[str]:
    return _bash('source "$1"; launcher_require_registered_slot "$2" "$3"', str(HANDOFF_IDENTITY), provider, selector)


def test_every_alias_selector_mints_a_registered_slot_for_every_provider() -> None:
    """Forward direction: nothing the compatibility map can mint is missing from the roster."""
    lanes = _minted_lanes(_alias_selectors())
    assert set(lanes) == set(_alias_selectors()), "an alias selector no longer resolves"
    unregistered = [
        f"{provider}-{lane} (selector {selector})"
        for selector, lane in lanes.items()
        for provider in PROVIDERS
        if not registry.is_registered_slot(f"{provider}-{lane}")
    ]
    assert not unregistered, f"aliases mint unregistered slots: {unregistered}"


def test_every_registered_slot_is_reachable_from_a_selector() -> None:
    """Converse direction: no roster row without a selector that mints it."""
    accepted = {
        selector: lane
        for selector, lane in _minted_lanes(_candidate_selectors()).items()
        if _gate("claude", selector).returncode == 0
    }
    reachable = {f"{provider}-{lane}" for lane in accepted.values() for provider in PROVIDERS}
    roster = _channels._load_registry_slots()
    assert roster, "area_assignments.yaml roster must load"
    unreachable = [slot for slot in roster if slot not in reachable]
    assert not unreachable, f"roster slots no launcher selector can mint: {unreachable}"


def test_generic_registry_keys_are_registered_or_refused() -> None:
    """A registry key the alias map does not cover is either backed by a roster slot or refused."""
    keys = _registry_stream_keys()
    lanes = _minted_lanes([*keys, *(f"infra.{key}" for key in keys)])
    for selector, lane in lanes.items():
        result = _gate("claude", selector)
        if registry.is_registered_slot(f"claude-{lane}"):
            assert result.returncode == 0, f"{selector}: {result.stderr}"
        else:
            assert result.returncode == 1, f"{selector} must be refused: {result.stderr}"
            assert f"claude-{lane}" in result.stderr


@pytest.mark.parametrize("selector", UNREGISTERED_SELECTORS)
def test_launcher_refuses_unregistered_selector_before_starting(selector: str) -> None:
    result = _launcher("--epic", selector)
    slot = f"claude-{selector.removeprefix('infra.')}"
    assert result.returncode == 2, result.stdout + result.stderr
    assert f"selector '{selector}'" in result.stderr
    assert f"'{slot}'" in result.stderr
    assert "not registered" in result.stderr
    assert "Registered claude slots: claude-infra" in result.stderr
    assert "would claim lease" not in result.stdout
    assert "would exec" not in result.stdout


def test_real_launch_of_unregistered_selector_never_execs_the_provider(tmp_path: Path) -> None:
    """Outside dry-run the provider binary must never start for an unregistered slot."""
    marker = tmp_path / "started"
    stub = tmp_path / "claude"
    stub.write_text(f"#!/usr/bin/env bash\ntouch {marker}\n", encoding="utf-8")
    stub.chmod(0o755)
    result = _launcher(
        "--epic", "curriculum-upgrade", dry_run=False, env={"PATH": f"{tmp_path}{os.pathsep}{os.environ['PATH']}"}
    )
    assert result.returncode == 2, result.stdout + result.stderr
    assert "not registered" in result.stderr
    assert not marker.exists(), "the provider binary started for an unregistered slot"


@pytest.mark.parametrize("selector", ["infra", "devops", "monitor", "open-model-data", "atlas", "folk", "bio", "corpus", "hramatka"])
def test_registered_selectors_still_launch(selector: str) -> None:
    result = _launcher("--epic", selector)
    assert result.returncode == 0, result.stderr
    assert "not registered" not in result.stderr
    assert "would exec claude" in result.stdout


def test_gate_fails_closed_when_the_registry_cannot_be_read(tmp_path: Path) -> None:
    empty = tmp_path / "assignments.yaml"
    empty.write_text("assignments: {}\n", encoding="utf-8")
    assert registry.main(["--slot", "claude-infra", "--assignments", str(empty)]) == 2
    assert registry.main(["--slot", "claude-infra"]) == 0
    assert registry.main(["--slot", "claude-not-a-lane"]) == 3


def test_gate_refuses_when_no_interpreter_can_verify_the_slot(tmp_path: Path) -> None:
    """No durable interpreter means an unverifiable identity, which is refused, not waved through."""
    result = subprocess.run(
        ["bash", "-c", 'source "$1"; launcher_require_registered_slot claude infra', "bash", str(HANDOFF_IDENTITY)],
        cwd=REPO,
        env={**os.environ, "LC_DURABLE_HELPER_ROOT": str(tmp_path)},
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 2, result.stderr
    assert "cannot verify handoff slot 'claude-infra'" in result.stderr
