"""Parity of the process-parallel scan with the in-process scan (#11096).

The lint's verdicts must not depend on how files are distributed over workers:
every case here runs once serially and once through a real process pool.
"""

from __future__ import annotations

import ast
import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pytest

from scripts.hygiene import lint_source_db_writable_connects as lint

DB_TARGET = "data/sources@@db".replace("@@", ".")

WRITER = lint.AllowedReference(
    path="scripts/writer.py", reference_count=1, kind="writer", target_db=DB_TARGET,
    reason="fixture", calls=("sqlite3.connect(PATH)",))
BAD_WRITER = lint.AllowedReference(
    path="scripts/writer_bad.py", reference_count=1, kind="writer", target_db=DB_TARGET,
    reason="fixture", calls=("sqlite3.connect(PATH)",))
STALE_WRITER = lint.AllowedReference(
    path="scripts/gone.py", reference_count=1, kind="writer", target_db=DB_TARGET,
    reason="fixture", calls=("sqlite3.connect(PATH)",))
FACTORY = lint.AllowedReference(
    path="tests/factory.py", reference_count=1, kind="fixture_factory", target_db=None,
    reason="fixture", calls=("sqlite3.connect(tmp)",))
ALLOWLIST = (WRITER, BAD_WRITER, STALE_WRITER, FACTORY)

# Store filenames are spelled with a placeholder so this file is not itself a census site.
STORE_SOURCE = "DB = REPO_ROOT / 'data' / 'sources@@db'\n".replace("@@", ".")
PINNED_SOURCE = "def test_x(): return ROOT / 'data' / 'vesum@@db'\n".replace("@@", ".")


def _planted_repo(root: Path, monkeypatch) -> None:
    """Planted violations, a renamed file with a stale baseline pin, unreadable inputs."""
    (root / "scripts").mkdir()
    (root / "tests").mkdir()
    files = {
        "scripts/writer.py": "import sqlite3\nc = sqlite3.connect(PATH)\n",
        "scripts/writer_bad.py": "import sqlite3\nc = sqlite3.connect(OTHER)\n",
        "scripts/planted_connect.py": "import sqlite3\nsqlite3.connect('x.db')\n",
        "scripts/planted_path.py": STORE_SOURCE,
        "scripts/renamed_new.py": STORE_SOURCE + "# renamed from renamed_old.py\n",
        "scripts/broken.py": "def (:\n",
        "tests/factory.py": "import sqlite3\ndef make(tmp):\n    return sqlite3.connect(tmp)\n",
        "tests/pinned.py": PINNED_SOURCE,
        "tests/broken_test.py": "x = (\n",
    }
    files.update({f"scripts/clean_{i}.py": f"VALUE = {i}\n" for i in range(12)})
    for rel, source in files.items():
        (root / rel).write_text(source)
    (root / "scripts" / "dangling.py").symlink_to(root / "missing-target")
    pinned = lint.classify_store_source(files["tests/pinned.py"], "tests/pinned.py")
    stale = lint.classify_store_source(STORE_SOURCE, "scripts/renamed_old.py")
    assert pinned and stale
    baseline = root / "baseline.json"
    baseline.write_text(json.dumps({"entries": [f.__dict__ for f in (*pinned, *stale)]}))
    monkeypatch.setattr(lint, "REPO_ROOT", root)
    monkeypatch.setattr(lint, "BASELINE", baseline)


class _SpyPool(ProcessPoolExecutor):
    started = 0

    def __init__(self, *args, **kwargs):
        type(self).started += 1
        super().__init__(*args, **kwargs)


def _run(root: Path, monkeypatch, *, parallel: bool):
    monkeypatch.setattr(lint, "PARALLEL_MIN_FILES", 1 if parallel else 10**9)
    monkeypatch.setattr(lint, "MAX_WORKERS", 3)
    monkeypatch.setattr(lint, "ProcessPoolExecutor", _SpyPool)
    _SpyPool.started = 0
    result = lint.find_violations(root, ALLOWLIST)
    assert _SpyPool.started == (1 if parallel else 0)
    return result


def test_parallel_scan_matches_serial_scan_on_planted_repo(tmp_path, monkeypatch):
    _planted_repo(tmp_path, monkeypatch)
    serial = _run(tmp_path, monkeypatch, parallel=False)
    parallel = _run(tmp_path, monkeypatch, parallel=True)
    assert parallel == serial
    violations, unreadable = parallel
    joined = "\n".join(violations)
    assert "scripts/planted_connect.py:2: constructor reference" in joined
    assert "scripts/planted_path.py: store_path" in joined
    assert "scripts/renamed_new.py: store_path" in joined
    assert "scripts/renamed_old.py: stale baseline store_path" in joined
    assert "scripts/writer_bad.py: opens differ from declared target sites" in joined
    assert "scripts/gone.py: stale reference allowlist entry" in joined
    assert "tests/pinned.py" not in joined
    # Disk errors and syntax errors keep their file order in both modes.
    assert unreadable == ["scripts/broken.py", "scripts/dangling.py", "tests/broken_test.py"]


def test_small_batches_stay_in_process(tmp_path, monkeypatch):
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "a.py").write_text("X = 1\n")
    monkeypatch.setattr(lint, "ProcessPoolExecutor", _SpyPool)
    _SpyPool.started = 0
    assert lint.find_violations(tmp_path, ()) == ([], [])
    assert _SpyPool.started == 0


def test_single_cpu_host_scans_in_process(tmp_path, monkeypatch):
    _planted_repo(tmp_path, monkeypatch)
    expected = _run(tmp_path, monkeypatch, parallel=False)
    monkeypatch.setattr(lint, "PARALLEL_MIN_FILES", 1)
    monkeypatch.setattr(lint.os, "cpu_count", lambda: 1)
    _SpyPool.started = 0
    assert lint.find_violations(tmp_path, ALLOWLIST) == expected
    assert _SpyPool.started == 0


@pytest.mark.parametrize("path", [Path(lint.__file__), Path(__file__)])
def test_structural_children_match_iter_child_nodes(path):
    markers = (ast.expr_context, ast.operator, ast.unaryop, ast.boolop, ast.cmpop)
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        expected = tuple(child for child in ast.iter_child_nodes(node) if not isinstance(child, markers))
        assert lint._structural_children(node) == expected
