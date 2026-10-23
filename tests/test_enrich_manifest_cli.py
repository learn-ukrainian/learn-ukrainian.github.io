"""CLI argv guard for lexicon enrich/build/export scripts (#5393).

``--help`` and bare invocation must exit without rewriting side-effect files.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
ENRICH_SCRIPT = ROOT / "scripts" / "lexicon" / "enrich_manifest.py"
BUILD_SCRIPT = ROOT / "scripts" / "lexicon" / "build_data_manifest.py"
EXPORT_SCRIPT = ROOT / "scripts" / "lexicon" / "export_open_dataset.py"
MANIFEST_PATH = ROOT / "site" / "src" / "data" / "lexicon-manifest.json"
DATASET_ROOT = ROOT / "data" / "lexicon-dataset"


def _path_snapshot(path: Path) -> tuple[bool, int | None, int | None, str | None]:
    """Return (exists, mtime_ns, size, sha256_hex) for a path."""
    if not path.exists():
        return (False, None, None, None)
    data = path.read_bytes()
    st = path.stat()
    return (True, st.st_mtime_ns, st.st_size, hashlib.sha256(data).hexdigest())


def _run_script(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, str(script), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )


# --- enrich_manifest.py -------------------------------------------------------


def test_enrich_help_exits_zero_and_leaves_manifest_untouched() -> None:
    before = _path_snapshot(MANIFEST_PATH)
    proc = _run_script(ENRICH_SCRIPT, "--help")
    after = _path_snapshot(MANIFEST_PATH)

    assert proc.returncode == 0, proc.stderr
    help_text = (proc.stdout + proc.stderr).lower()
    assert "usage:" in help_text
    assert "--write" in help_text
    assert "enrich" in help_text
    assert after == before


def test_enrich_no_flags_exits_nonzero_and_leaves_manifest_untouched() -> None:
    before = _path_snapshot(MANIFEST_PATH)
    proc = _run_script(ENRICH_SCRIPT)
    after = _path_snapshot(MANIFEST_PATH)

    assert proc.returncode != 0
    combined = proc.stdout + proc.stderr
    assert "usage:" in combined.lower() or "--write" in combined
    assert "refusing" in combined.lower() or "required" in combined.lower() or "--write" in combined
    assert after == before


# --- build_data_manifest.py (sibling #5393) ------------------------------------


def test_build_help_exits_zero_and_leaves_manifest_untouched() -> None:
    before = _path_snapshot(MANIFEST_PATH)
    proc = _run_script(BUILD_SCRIPT, "--help")
    after = _path_snapshot(MANIFEST_PATH)

    assert proc.returncode == 0, proc.stderr
    help_text = (proc.stdout + proc.stderr).lower()
    assert "usage:" in help_text
    assert "--write" in help_text
    assert after == before


def test_build_no_flags_exits_nonzero_and_leaves_manifest_untouched() -> None:
    before = _path_snapshot(MANIFEST_PATH)
    proc = _run_script(BUILD_SCRIPT)
    after = _path_snapshot(MANIFEST_PATH)

    assert proc.returncode != 0
    assert after == before


# --- export_open_dataset.py (sibling #5393) -----------------------------------


def test_export_help_exits_zero_and_leaves_dataset_untouched(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Subprocess path: assert default dataset root is not created/touched by --help.
    before_root_exists = DATASET_ROOT.exists()
    before_marker = _path_snapshot(DATASET_ROOT / "README.md") if before_root_exists else (False, None, None, None)
    proc = _run_script(EXPORT_SCRIPT, "--help")
    after_marker = _path_snapshot(DATASET_ROOT / "README.md") if DATASET_ROOT.exists() else (False, None, None, None)

    assert proc.returncode == 0, proc.stderr
    assert "usage:" in (proc.stdout + proc.stderr).lower()
    assert "--write" in (proc.stdout + proc.stderr)
    assert after_marker == before_marker
    if not before_root_exists:
        assert not DATASET_ROOT.exists()


def test_export_no_flags_exits_nonzero() -> None:
    before_root_exists = DATASET_ROOT.exists()
    before_marker = _path_snapshot(DATASET_ROOT / "README.md") if before_root_exists else (False, None, None, None)
    proc = _run_script(EXPORT_SCRIPT)
    after_marker = _path_snapshot(DATASET_ROOT / "README.md") if DATASET_ROOT.exists() else (False, None, None, None)

    assert proc.returncode != 0
    assert after_marker == before_marker
    if not before_root_exists:
        assert not DATASET_ROOT.exists()
