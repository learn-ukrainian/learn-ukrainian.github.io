"""Contract tests for fleet taxonomy alias resolution and entry point wiring."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from agents_extensions.shared.session_streams.inventory import (
    _handoff_candidates_for,
)
from scripts.orchestration.fleet_taxonomy import (
    EpicInfo,
    ResolvedArea,
    UnknownAreaError,
    list_valid_names,
    load_fleet_taxonomy,
    resolve_area,
    resolve_area_by_epic,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_HANDOFF_IDENTITY_SH = _REPO_ROOT / "scripts" / "lib" / "handoff_identity.sh"


# ---------------------------------------------------------------------------
# 1. Helper Unit Tests (scripts/orchestration/fleet_taxonomy.py)
# ---------------------------------------------------------------------------


def test_load_fleet_taxonomy_structure() -> None:
    registry = load_fleet_taxonomy()
    assert "infra" in registry.areas
    assert "harness" in registry.areas
    assert "devops" in registry.areas
    assert "atlas" in registry.areas
    assert "core" in registry.areas
    assert "seminars" in registry.areas
    assert "hramatka" in registry.areas


def test_resolve_area_canonical_ids() -> None:
    infra = resolve_area("infra")
    assert isinstance(infra, ResolvedArea)
    assert infra.id == "infra"
    assert "infra-harness" in infra.aliases
    assert EpicInfo(number=4707, name="Infra & fleet reliability (hooks, dispatch, routing)") in infra.epics

    harness = resolve_area("harness")
    assert harness.id == "harness"
    assert "eval-harness" in harness.aliases

    devops = resolve_area("devops")
    assert devops.id == "devops"


def test_resolve_area_aliases() -> None:
    # infra-harness -> infra
    area1 = resolve_area("infra-harness")
    assert area1.id == "infra"

    # eval-harness -> harness
    area2 = resolve_area("eval-harness")
    assert area2.id == "harness"

    # atlas-practice -> atlas
    area3 = resolve_area("atlas-practice")
    assert area3.id == "atlas"

    # seminars-folk -> seminars
    area4 = resolve_area("seminars-folk")
    assert area4.id == "seminars"

    # hramatka -> hramatka
    area5 = resolve_area("hramatka")
    assert area5.id == "hramatka"


def test_resolve_area_by_epic_number() -> None:
    # int epic lookup
    infra = resolve_area(4707)
    assert infra.id == "infra"

    devops = resolve_area(5703)
    assert devops.id == "devops"

    harness = resolve_area(4913)
    assert harness.id == "harness"

    # string epic lookup
    assert resolve_area("4707").id == "infra"
    assert resolve_area("epic:4707").id == "infra"
    assert resolve_area_by_epic(4707).id == "infra"
    assert resolve_area_by_epic("epic:5703").id == "devops"


def test_resolve_area_unknown_raises_typed_error() -> None:
    with pytest.raises(UnknownAreaError) as exc_info:
        resolve_area("invalid_area_xyz")

    err_msg = str(exc_info.value)
    assert "Unknown area name, alias, or epic 'invalid_area_xyz'" in err_msg
    assert "infra" in err_msg
    assert "harness" in err_msg


def test_resolve_area_unknown_epic_raises_typed_error() -> None:
    with pytest.raises(UnknownAreaError) as exc_info:
        resolve_area(999999)

    err_msg = str(exc_info.value)
    assert "Unknown epic number 999999" in err_msg


def test_list_valid_names() -> None:
    names = list_valid_names()
    assert "infra" in names
    assert "infra-harness" in names
    assert "harness" in names
    assert "eval-harness" in names
    assert "devops" in names
    assert names == tuple(sorted(names))


# ---------------------------------------------------------------------------
# 2. Per-Python-Entry-Point Wiring Tests
# ---------------------------------------------------------------------------


def test_inventory_session_streams_wiring() -> None:
    """Verify session_streams inventory uses fleet_taxonomy resolution."""
    # epic:4707 is in HANDOFF_PATH_OVERRIDES
    cands_infra = _handoff_candidates_for("infra-harness", 4707)
    assert any("harness-epic" in path for path in cands_infra)

    # A non-overridden stream name should use resolve_area to determine directory slug
    cands_core = _handoff_candidates_for("core-quality", 4274)
    assert any("core-epic" in path for path in cands_core)


# ---------------------------------------------------------------------------
# 3. Per-Launcher Spelling-Acceptance & Resolver Contract Tests
# ---------------------------------------------------------------------------


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")
@pytest.mark.parametrize(
    ("selector", "expected_lane", "expected_stream"),
    [
        ("infra", "infra", "epic:4707"),
        ("harness", "infra", "epic:4707"),
        ("infra.fleet-comms", "infra", "epic:4707"),
        ("devops", "devops", "epic:5703"),
        ("infra.devops", "devops", "epic:5703"),
        ("atlas", "atlas", "epic:4387"),
        ("practice", "atlas", "epic:4387"),
        ("practice-hub", "atlas", "epic:4387"),
        ("atlas.practice", "atlas", "epic:4387"),
        ("hramatka", "hramatka", "epic:4542"),
        ("hramatka.lessons", "hramatka", "epic:4542"),
        ("folk", "folk", "epic:2836"),
        ("seminars-folk", "folk", "epic:2836"),
        ("bio", "bio", "epic:4431"),
        ("seminars-bio", "bio", "epic:4431"),
        ("corpus", "corpus", "epic:4706"),
        ("corpus-channels", "corpus", "epic:4706"),
    ],
)
def test_handoff_identity_shell_selector_contract(
    selector: str,
    expected_lane: str,
    expected_stream: str,
) -> None:
    """Pin the current shell selector table in scripts/lib/handoff_identity.sh."""
    result = subprocess.run(
        [
            "bash",
            "-c",
            'source "$1"; launcher_selector_resolve "$2"',
            "bash",
            str(_HANDOFF_IDENTITY_SH),
            selector,
        ],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, f"Failed for selector '{selector}': {result.stderr}"
    assert result.stdout.strip() == f"{expected_lane}\t{expected_stream}"


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")
@pytest.mark.parametrize(
    "unknown_selector",
    [
        "invalid_selector_xyz",
        "unknown_lane_abc",
        "epic:999999",
    ],
)
def test_handoff_identity_shell_resolver_unknown_selector_fails_closed(
    unknown_selector: str,
) -> None:
    """Hermetic resolver contract test: verify launcher_selector_resolve in handoff_identity.sh fails closed (rc=1) for unknown selectors."""
    result = subprocess.run(
        [
            "bash",
            "-c",
            'source "$1"; launcher_selector_resolve "$2"',
            "bash",
            str(_HANDOFF_IDENTITY_SH),
            unknown_selector,
        ],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode != 0, f"Expected non-zero returncode for unknown selector '{unknown_selector}'"
    assert result.stdout.strip() == ""


@pytest.mark.parametrize(
    "launcher",
    [
        "start-claude.sh",
        "start-codex.sh",
        "start-gemini.sh",
        "start-grok.sh",
        "start-kimi.sh",
        "start-codex-drive.sh",
        "start-gemini-drive.sh",
        "start-grok-drive.sh",
        "start-opus-drive.sh",
        "start-sonnet-drive.sh",
    ],
)
def test_launcher_static_selector_wiring(launcher: str) -> None:
    """Verify statically (text inspection) that each launcher script sources handoff_identity.sh and invokes selector resolution functions."""
    script_path = _REPO_ROOT / launcher
    assert script_path.is_file(), f"Launcher missing: {launcher}"
    content = script_path.read_text(encoding="utf-8")
    assert "scripts/lib/handoff_identity.sh" in content, f"{launcher} does not source scripts/lib/handoff_identity.sh"
    assert any(
        fn in content
        for fn in (
            "launcher_selector_resolve",
            "launcher_selector_lane",
            "handoff_identity_for_",
        )
    ), f"{launcher} does not call selector resolution functions"


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")
@pytest.mark.parametrize(
    ("launcher", "unknown_arg", "expected_rc"),
    [
        # CI-safe: start-claude.sh parses and validates --epic early before preflight checks or external CLI lookups.
        ("start-claude.sh", "--epic=invalid_selector_xyz", 1),
        # CI-safe: start-codex-drive.sh validates $1 via launcher_selector_resolve at top of script before exec start-codex.sh.
        ("start-codex-drive.sh", "invalid_selector_xyz", 2),
        # CI-safe: start-gemini-drive.sh validates $1 via launcher_selector_resolve at top of script before exec start-gemini.sh.
        ("start-gemini-drive.sh", "invalid_selector_xyz", 2),
        # CI-safe: start-grok-drive.sh validates $1 via launcher_selector_resolve at top of script before exec start-grok.sh.
        ("start-grok-drive.sh", "invalid_selector_xyz", 2),
        # CI-safe: start-opus-drive.sh validates $1 via launcher_selector_resolve at top of script before exec start-opus.sh.
        ("start-opus-drive.sh", "invalid_selector_xyz", 2),
        # CI-safe: start-sonnet-drive.sh validates $1 via launcher_selector_resolve at top of script before exec start-sonnet.sh.
        ("start-sonnet-drive.sh", "invalid_selector_xyz", 2),
    ],
)
def test_hermetic_launcher_unknown_selector_fails_closed_contract(
    launcher: str,
    unknown_arg: str,
    expected_rc: int,
) -> None:
    """Verify hermetic launchers (which validate selectors early without external CLI/checkout requirements) fail closed on unknown selectors."""
    script_path = _REPO_ROOT / launcher
    assert script_path.is_file(), f"Launcher missing: {launcher}"

    clean_env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}

    result = subprocess.run(
        ["bash", str(script_path), unknown_arg],
        cwd=_REPO_ROOT,
        env=clean_env,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == expected_rc, (
        f"Launcher {launcher} with arg {unknown_arg} returned rc={result.returncode}, expected {expected_rc}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert "unknown lane selector" in result.stderr.lower() or "invalid" in result.stderr.lower()


def test_inventory_handoff_candidates_survive_missing_resolver(monkeypatch):
    """#5857 r3: deployed/sandbox copies lack the repo-root ``scripts`` package.

    The thread-restart e2e sandbox materializes ``inventory.py`` without
    ``scripts/orchestration`` — a module-level resolver import crashed the whole
    session supervisor there (ModuleNotFoundError). The resolver import must be
    lazy and degrade to the legacy map. Mutation check: with the import hoisted
    back to module level, the blocked-module fallback below is unreachable and
    the resolved slug ('infra') breaks this assertion.
    """
    import sys

    from agents_extensions.shared.session_streams import inventory

    monkeypatch.setitem(sys.modules, "scripts.orchestration.fleet_taxonomy", None)
    candidates = inventory._handoff_candidates_for("infra-harness", 99999)
    # Legacy-map answer ('harness'); the resolver would give 'infra' — so a hoisted
    # module-level import makes this assertion fail, keeping the mutation detectable.
    assert candidates[0] == ".claude/harness-epic/CLAUDE-DRIVER-HANDOFF.md"
