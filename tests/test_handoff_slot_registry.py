"""The launcher refuses unregistered handoff slots and every mintable one is registered (#8303).

``scripts/config/area_assignments.yaml`` is the roster of addressable slots.  Its header says
"do not add rows without a mintable selector"; these tests enforce that rule in both
directions and prove the launcher fails closed instead of minting ``<provider>-<lane>``.
"""

from __future__ import annotations

import csv
import functools
import os
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
import yaml

from scripts.ai_agent_bridge import _channels
from scripts.orchestration import handoff_slot_registry as registry

REPO = Path(__file__).resolve().parents[1]
HANDOFF_IDENTITY = REPO / "scripts" / "lib" / "handoff_identity.sh"
ALIASES = REPO / "scripts" / "config" / "launcher_stream_aliases.tsv"
ISSUE_STREAMS = REPO / "scripts" / "config" / "issue_streams.yaml"

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


def _driver_providers() -> tuple[str, ...]:
    """Providers whose driver launcher runs the slot gate, read from the entry points themselves.

    ``--epic`` (and so ``launcher_require_registered_slot``) is accepted only by
    ``start-<provider>-driver.sh``; each one hands its provider to ``launcher_main``.
    """
    providers = sorted(
        {
            match.group(1)
            for script in REPO.glob("start-*-driver.sh")
            for match in re.finditer(r"^launcher_main (\w+) driver\b", script.read_text(encoding="utf-8"), re.M)
        }
    )
    assert providers, "no driver launcher found: start-*-driver.sh"
    return tuple(providers)


PROVIDERS = _driver_providers()


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
        timeout=300,
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


@functools.cache
def _gate_matrix() -> tuple[dict[str, str], dict[str, dict[str, int]]]:
    """(selector -> lane, provider -> lane -> the real launcher gate's exit code) for every candidate selector.

    The gate's verdict depends only on ``<provider>-<lane>``, so it runs once per provider and lane
    (through one representative selector), two providers at a time; every launcher provider is covered.
    """
    lanes = _minted_lanes(_candidate_selectors())
    representative = {lane: selector for selector, lane in sorted(lanes.items(), reverse=True)}
    script = (
        'source "$1"; shift; p="$1"; shift; '
        'for s in "$@"; do launcher_require_registered_slot "$p" "$s" >/dev/null 2>&1; printf "%s\\t%s\\t%s\\n" "$p" "$s" "$?"; done'
    )
    selectors = list(representative.values())
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda provider: _bash(script, str(HANDOFF_IDENTITY), provider, *selectors), PROVIDERS))
    gate: dict[str, dict[str, int]] = {provider: {} for provider in PROVIDERS}
    for result in results:
        assert result.returncode == 0, result.stderr
        for line in result.stdout.splitlines():
            provider, selector, code = line.split("\t")
            gate[provider][lanes[selector]] = int(code)
    return lanes, gate


def test_launcher_providers_are_read_from_the_driver_entry_points() -> None:
    assert {"claude", "codex"} <= set(PROVIDERS)


def test_every_alias_selector_mints_a_registered_slot_for_every_provider() -> None:
    """Forward direction: nothing the compatibility map can mint is missing from the roster."""
    lanes, gate = _gate_matrix()
    aliases = _alias_selectors()
    assert set(aliases) <= set(lanes), "an alias selector no longer resolves"
    refused = [
        f"{provider}-{lanes[selector]} (selector {selector}, gate exit {gate[provider][lanes[selector]]})"
        for selector in aliases
        for provider in PROVIDERS
        if gate[provider][lanes[selector]] != 0
    ]
    assert not refused, f"aliases mint slots the launcher gate refuses: {refused}"


def test_every_registered_slot_is_reachable_from_a_selector_for_its_provider() -> None:
    """Converse direction, judged by the real gate per provider, not assumed from one provider.

    Every lane the roster has for any provider must be accepted by every launcher provider:
    a stream with slots for five providers but none for ``codex`` is refused by the Codex
    launcher, so the roster row set must be uniform across the launcher providers.
    """
    roster = _channels._load_registry_slots()
    assert roster, "area_assignments.yaml roster must load"
    _, gate = _gate_matrix()
    accepted = {provider: {lane for lane, code in gate[provider].items() if code == 0} for provider in PROVIDERS}
    roster_lanes = {slot.split("-", 1)[1] for slot in roster}
    unreachable = [f"{provider}-{lane}" for provider in PROVIDERS for lane in sorted(roster_lanes - accepted[provider])]
    assert not unreachable, f"launcher providers cannot reach these roster lanes: {unreachable}"
    # Roster providers without a driver launcher (kimi) still need a selector that mints their lane.
    minted = set().union(*accepted.values())
    unminted = [
        slot for slot in roster if slot.split("-", 1)[0] not in PROVIDERS and slot.split("-", 1)[1] not in minted
    ]
    assert not unminted, f"roster slots no launcher selector can mint: {unminted}"


def test_generic_registry_keys_are_registered_or_refused_for_every_provider() -> None:
    """A registry key the alias map does not cover is backed by a slot for every provider or refused for all."""
    keys = _registry_stream_keys()
    lanes, gate = _gate_matrix()
    for selector in [*keys, *(f"infra.{key}" for key in keys)]:
        if selector not in lanes:
            continue
        lane = lanes[selector]
        accepting = [provider for provider in PROVIDERS if gate[provider][lane] == 0]
        refusing = [provider for provider in PROVIDERS if provider not in accepting]
        for provider in accepting:
            assert registry.is_registered_slot(f"{provider}-{lane}"), (
                f"{selector}: gate accepted unregistered {provider}-{lane}"
            )
        assert not (accepting and refusing), (
            f"{selector}: lane '{lane}' is registered for {accepting} but the launcher refuses {refusing}"
        )
        for provider in refusing:
            result = _gate(provider, selector)
            assert result.returncode == 1, f"{selector} must be refused for {provider}: {result.stderr}"
            assert f"{provider}-{lane}" in result.stderr


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


@pytest.mark.parametrize(
    "selector", ["infra", "devops", "monitor", "open-model-data", "atlas", "folk", "bio", "corpus", "hramatka"]
)
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
