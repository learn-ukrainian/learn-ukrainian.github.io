"""CLI argv guard for lexicon enrich/build/export scripts (#5393).

``--help`` and bare invocation must exit without rewriting side-effect files.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PYTHON = str(ROOT / ".venv" / "bin" / "python")
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


def test_enrich_main_write_runs_enrich_only(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from scripts.lexicon import enrich_manifest as mod

    called: list[str] = []

    def fake_enrich() -> tuple[int, int]:
        called.append("enrich")
        return (3, 10)

    manifest_path = tmp_path / "lexicon-manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "entries": [
                    {"lemma": "тест", "pronunciation": {"ipa": "/tɛst/"}},
                    {"lemma": "слово"},
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "enrich", fake_enrich)
    monkeypatch.setattr(mod, "MANIFEST", manifest_path)
    monkeypatch.setattr(mod, "_single_word_etymology_coverage", lambda _m: (1, 2))

    assert mod.main(["--write"]) == 0
    assert called == ["enrich"]


def test_enrich_main_no_flags_does_not_call_enrich(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.lexicon import enrich_manifest as mod

    def boom() -> tuple[int, int]:
        raise AssertionError("enrich() must not run without --write")

    monkeypatch.setattr(mod, "enrich", boom)
    with pytest.raises(SystemExit) as excinfo:
        mod.main([])
    assert excinfo.value.code not in (0, None)


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


def test_build_main_no_flags_does_not_call_build(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.lexicon import build_data_manifest as mod

    def boom() -> dict:
        raise AssertionError("build_manifest() must not run without --write")

    monkeypatch.setattr(mod, "build_manifest", boom)
    with pytest.raises(SystemExit) as excinfo:
        mod.main([])
    assert excinfo.value.code not in (0, None)


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


def test_export_main_no_flags_does_not_call_export(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.lexicon import export_open_dataset as mod

    def boom() -> tuple[int, int]:
        raise AssertionError("export_dataset() must not run without --write")

    monkeypatch.setattr(mod, "export_dataset", boom)
    with pytest.raises(SystemExit) as excinfo:
        mod.main([])
    assert excinfo.value.code not in (0, None)


def test_export_main_write_calls_export(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.lexicon import export_open_dataset as mod

    called: list[str] = []

    def fake_export() -> tuple[int, int]:
        called.append("export")
        return (5, 2)

    monkeypatch.setattr(mod, "export_dataset", fake_export)
    assert mod.main(["--write"]) == 0
    assert called == ["export"]
