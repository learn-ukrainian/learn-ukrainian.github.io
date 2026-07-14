"""Tests for the Atlas manifest enrichment-depth gate (#3658).

Guards the #3631 empty-atlas regression class: a thin/un-enriched manifest must
fail the gate, and the real committed manifest must always pass.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.audit.check_atlas_manifest_enrichment import (
    DEFAULT_MANIFEST,
    check_enrichment,
)


def _write(path: Path, *, enrichment_generated, n_total: int, n_enriched: int) -> Path:
    entries = []
    for i in range(n_total):
        entry = {"lemma": f"w{i}", "gloss": "g"}
        if i < n_enriched:
            entry["enrichment"] = {"definition": "d"}
        entries.append(entry)
    path.write_text(
        json.dumps({"enrichment_generated": enrichment_generated, "entries": entries}),
        encoding="utf-8",
    )
    return path


def test_healthy_manifest_passes(tmp_path: Path) -> None:
    m = _write(tmp_path / "m.json", enrichment_generated=True, n_total=100, n_enriched=85)
    assert check_enrichment(manifest_path=m) == 0


def test_thin_manifest_zero_enriched_fails(tmp_path: Path) -> None:
    # The exact #3631 shape: enrichment_generated False, 0 enriched entries.
    m = _write(tmp_path / "m.json", enrichment_generated=False, n_total=4148, n_enriched=0)
    assert check_enrichment(manifest_path=m) == 2


def test_below_ratio_floor_fails(tmp_path: Path) -> None:
    # enrichment_generated True but coverage collapsed below the floor.
    m = _write(tmp_path / "m.json", enrichment_generated=True, n_total=100, n_enriched=30)
    assert check_enrichment(manifest_path=m) == 2


def test_ratio_at_floor_passes(tmp_path: Path) -> None:
    m = _write(tmp_path / "m.json", enrichment_generated=True, n_total=100, n_enriched=40)
    assert check_enrichment(manifest_path=m, min_ratio=0.40) == 0


def test_enrichment_flag_false_fails_even_if_entries_enriched(tmp_path: Path) -> None:
    m = _write(tmp_path / "m.json", enrichment_generated=False, n_total=100, n_enriched=90)
    assert check_enrichment(manifest_path=m) == 2


def test_empty_entries_fails(tmp_path: Path) -> None:
    m = _write(tmp_path / "m.json", enrichment_generated=True, n_total=0, n_enriched=0)
    assert check_enrichment(manifest_path=m) == 2


def test_missing_manifest_fails(tmp_path: Path) -> None:
    assert check_enrichment(manifest_path=tmp_path / "nope.json") == 2


@pytest.mark.skipif(not DEFAULT_MANIFEST.exists(), reason="committed manifest not present")
def test_committed_manifest_is_enriched() -> None:
    # The real shipped manifest must always pass — this is the regression guard.
    assert check_enrichment() == 0


def test_gate_runs_in_minimal_env_without_third_party_deps(tmp_path: Path) -> None:
    """The freshness CI job installs no third-party deps (#5166 burn).

    The gate's FULL import chain — including the lazy in-function import of
    migrate_source_labels — must never pull `requests` (or transitively,
    enrich_manifest's other heavy deps). Reproduces the CI env by blocking
    `requests` at import time in a fresh interpreter, then running the gate
    end-to-end on a healthy fixture manifest.
    """
    import subprocess

    root = Path(__file__).resolve().parents[1]
    venv_python = root / ".venv" / "bin" / "python"
    manifest = _write(tmp_path / "m.json", enrichment_generated=True, n_total=4, n_enriched=4)
    code = (
        "import builtins, sys\n"
        "_real = builtins.__import__\n"
        "def _guard(name, *a, **k):\n"
        "    if name == 'requests' or name.startswith('requests.'):\n"
        "        raise ModuleNotFoundError(\"No module named 'requests' (blocked: minimal CI env)\")\n"
        "    return _real(name, *a, **k)\n"
        "builtins.__import__ = _guard\n"
        f"sys.path.insert(0, {str(root)!r})\n"
        "from scripts.audit.check_atlas_manifest_enrichment import check_enrichment\n"
        "from pathlib import Path\n"
        f"rc = check_enrichment(manifest_path=Path({str(manifest)!r}))\n"
        "raise SystemExit(rc)\n"
    )
    proc = subprocess.run(
        [str(venv_python), "-c", code], capture_output=True, text=True, cwd=root, timeout=120
    )
    assert proc.returncode == 0, (
        f"gate failed in minimal env (rc={proc.returncode})\n"
        f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
    )
