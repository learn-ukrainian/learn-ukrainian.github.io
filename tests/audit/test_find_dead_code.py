import sys

import pytest

from scripts.audit.find_dead_code import (
    category_a,
    category_b,
    category_f,
)


def _write_vulture_stub(path, root, finding):
    expected_args = [
        str(root),
        "--min-confidence",
        "80",
        "--exclude",
        "*/.venv/*,*/embed-venv/*,*/node_modules/*,*/site-packages/*,*/.git/*,*/.worktrees/*,*/archive/*",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"#!{sys.executable}\n"
        "import sys\n"
        f"if sys.argv[1:] != {expected_args!r}:\n"
        "    print('unexpected scanner arguments')\n"
        "    sys.exit(2)\n"
        f"print({finding!r})\n"
        "sys.exit(3)\n",
        encoding="utf-8",
    )
    path.chmod(0o755)


@pytest.mark.parametrize("location", ["root-local", "PATH-only"])
def test_category_b_executes_vulture(tmp_path, monkeypatch, location):
    root = tmp_path / "scan root"
    root.mkdir()
    path_bin = tmp_path / "path bin"
    path_bin.mkdir()
    monkeypatch.setenv("PATH", str(path_bin))
    executable = root / ".venv" / "bin" / "vulture" if location == "root-local" else path_bin / "vulture"
    _write_vulture_stub(executable, root, "sample.py:1: unused import 'os' (90% confidence)")

    assert category_b(root) == ["sample.py:1: unused import 'os' (90% confidence)"]


@pytest.mark.parametrize("unusable_files", [False, True])
def test_category_b_vulture_unavailable(tmp_path, monkeypatch, unusable_files):
    root = tmp_path / "scan"
    root.mkdir()
    path_bin = tmp_path / "bin"
    path_bin.mkdir()
    monkeypatch.setenv("PATH", str(path_bin))
    if unusable_files:
        local = root / ".venv" / "bin" / "vulture"
        local.parent.mkdir(parents=True)
        for executable in (local, path_bin / "vulture"):
            executable.write_text("not executable", encoding="utf-8")
            executable.chmod(0o644)

    assert category_b(root) == ["NEEDS-MANUAL-REVIEW: vulture-unavailable"]


def test_category_b_invocation_failure(tmp_path, monkeypatch):
    root = tmp_path / "scan"
    executable = root / ".venv" / "bin" / "vulture"
    executable.parent.mkdir(parents=True)
    executable.write_text(f"#!{tmp_path / 'missing-interpreter'}\n", encoding="utf-8")
    executable.chmod(0o755)
    path_bin = tmp_path / "bin"
    monkeypatch.setenv("PATH", str(path_bin))
    _write_vulture_stub(path_bin / "vulture", root, "path.py:3: unused variable 'other' (100% confidence)")

    assert category_b(root) == ["NEEDS-MANUAL-REVIEW: vulture failed to run"]


def test_category_a_excludes_worktrees(tmp_path):
    # An OBSOLETE module in the live tree is flagged; an identical one inside
    # .worktrees/ (a full repo copy) must NOT be — else every hit is counted
    # once per active worktree (the 2026-06-06 77%-pollution bug).
    (tmp_path / "live.py").write_text("OBSOLETE\ndef foo(): pass", encoding="utf-8")
    wt = tmp_path / ".worktrees" / "dispatch" / "x"
    wt.mkdir(parents=True)
    (wt / "copy.py").write_text("OBSOLETE\ndef foo(): pass", encoding="utf-8")

    hits = category_a(tmp_path)

    assert any("live.py" in h for h in hits)
    assert not any(".worktrees" in h for h in hits)


def test_category_f_excludes_worktrees(tmp_path):
    # An orphaned orchestration dir in the live tree is a candidate; one inside
    # .worktrees/ must NOT be (484 of the polluted F hits were worktree copies).
    (tmp_path / "mod" / "orchestration").mkdir(parents=True)
    wt_orch = tmp_path / ".worktrees" / "dispatch" / "x" / "mod" / "orchestration"
    wt_orch.mkdir(parents=True)

    hits = category_f(tmp_path)

    assert any("mod/orchestration" in h and ".worktrees" not in h for h in hits)
    assert not any(".worktrees" in h for h in hits)
