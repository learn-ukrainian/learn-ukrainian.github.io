"""Tests for scripts/hygiene/root_entry_guard.py (#6863).

The guard must deterministically flag top-level repo-root entries that git
neither tracks nor ignores — crucially EMPTY DIRECTORIES, which git status
cannot see — and must never delete anything itself.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from scripts.hygiene.root_entry_guard import main, scan_unexpected_root_entries


def _git(root: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )


def _make_repo(root: Path) -> Path:
    """Minimal real git repo: one tracked file, one ignored dir."""
    root.mkdir(parents=True, exist_ok=True)
    _git(root, "init", "-q")
    (root / "tracked.py").write_text("# tracked\n", encoding="utf-8")
    (root / ".gitignore").write_text("node_modules/\n", encoding="utf-8")
    _git(root, "add", "tracked.py", ".gitignore")
    (root / "node_modules").mkdir()
    (root / "node_modules" / "dep.js").write_text("// ignored\n", encoding="utf-8")
    return root


def test_empty_garbage_dir_flagged_as_git_invisible(tmp_path: Path) -> None:
    root = _make_repo(tmp_path / "repo")
    # The Aug-13 leak class: a verbatim ACP event line as a directory name.
    (root / '{"type":"text","part":{"type":"text","text":"привіт"}}').mkdir()

    unexpected = scan_unexpected_root_entries(root)

    assert [e.name for e in unexpected] == [
        '{"type":"text","part":{"type":"text","text":"привіт"}}'
    ]
    assert unexpected[0].kind == "dir"
    assert unexpected[0].git_invisible is True


def test_literal_dash_rf_dir_flagged_without_arg_injection(tmp_path: Path) -> None:
    root = _make_repo(tmp_path / "repo")
    (root / "-rf").mkdir()

    unexpected = scan_unexpected_root_entries(root)

    assert [e.name for e in unexpected] == ["-rf"]
    assert unexpected[0].git_invisible is True
    # The flag-shaped name must not have been consumed as a git option:
    # the ignored node_modules dir is still correctly NOT flagged.
    assert all(e.name != "node_modules" for e in unexpected)


def test_guard_never_deletes(tmp_path: Path) -> None:
    root = _make_repo(tmp_path / "repo")
    garbage = root / "-rf"
    garbage.mkdir()

    scan_unexpected_root_entries(root)
    main(["--repo-root", str(root), "--strict"])

    assert garbage.is_dir()


def test_cli_json_report(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = _make_repo(tmp_path / "repo")
    (root / "-rf").mkdir()

    rc = main(["--repo-root", str(root), "--json"])

    assert rc == 0  # advisory by default, even with findings
    report = json.loads(capsys.readouterr().out)
    assert report["repo_root"] == str(root)
    assert report["unexpected_count"] == 1
    assert report["unexpected"][0]["name"] == "-rf"
    assert report["unexpected"][0]["git_invisible"] is True


def test_cli_strict_exit_codes(tmp_path: Path) -> None:
    dirty = _make_repo(tmp_path / "dirty")
    (dirty / "-rf").mkdir()
    clean = _make_repo(tmp_path / "clean")

    assert main(["--repo-root", str(dirty), "--strict"]) == 1
    assert main(["--repo-root", str(clean), "--strict"]) == 0
