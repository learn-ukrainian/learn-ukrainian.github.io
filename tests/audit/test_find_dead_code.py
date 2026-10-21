import sys
from pathlib import Path

import pytest

from scripts.audit.find_dead_code import (
    EXCLUDE_DIR_NAMES,
    _is_excluded,
    _vulture_exclude_glob,
    category_a,
    category_b,
    category_c,
    category_d,
    category_f,
    category_g,
    main,
)


def test_category_a(tmp_path):
    p = tmp_path / "obs.py"
    p.write_text("OBSOLETE\ndef foo(): pass", encoding="utf-8")
    hits = category_a(tmp_path)
    assert len(hits) == 1
    assert "obs.py (no live callers found)" in hits[0]


def test_category_b(tmp_path, monkeypatch):
    def mock_run(cmd, *args, **kwargs):
        class FakeRes:
            stdout = "foo.py:1: unused import 'os'\n"
            returncode = 1

        return FakeRes()

    monkeypatch.setattr("scripts.audit.find_dead_code.run_cmd", mock_run)

    vulture_bin = tmp_path / ".venv" / "bin" / "vulture"
    vulture_bin.parent.mkdir(parents=True, exist_ok=True)
    vulture_bin.touch()
    vulture_bin.chmod(0o755)

    hits = category_b(tmp_path)
    assert len(hits) == 1
    assert "foo.py:1: unused import 'os'" in hits[0]


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


def test_category_b_prefers_root_local_vulture(tmp_path, monkeypatch):
    root = tmp_path / "scan"
    root.mkdir()
    path_bin = tmp_path / "bin"
    monkeypatch.setenv("PATH", str(path_bin))
    _write_vulture_stub(
        root / ".venv" / "bin" / "vulture", root, "local.py:2: unused variable 'local' (100% confidence)"
    )
    _write_vulture_stub(path_bin / "vulture", root, "path.py:3: unused variable 'other' (100% confidence)")

    assert category_b(root) == ["local.py:2: unused variable 'local' (100% confidence)"]


@pytest.mark.parametrize("local_kind", ["non-executable", "directory"])
def test_category_b_skips_unusable_local_vulture(tmp_path, monkeypatch, local_kind):
    root = tmp_path / "scan"
    local = root / ".venv" / "bin" / "vulture"
    local.parent.mkdir(parents=True)
    if local_kind == "directory":
        local.mkdir()
    else:
        local.write_text("not executable", encoding="utf-8")
        local.chmod(0o644)
    path_bin = tmp_path / "bin"
    monkeypatch.setenv("PATH", str(path_bin))
    _write_vulture_stub(path_bin / "vulture", root, "path.py:3: unused variable 'other' (100% confidence)")

    assert category_b(root) == ["path.py:3: unused variable 'other' (100% confidence)"]


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


def test_category_c(tmp_path, monkeypatch):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "foo.md").write_text("referencing v6_build", encoding="utf-8")

    def mock_run(cmd, *args, **kwargs):
        class FakeRes:
            stdout = "docs/foo.md:1:referencing v6_build\n"
            returncode = 0

        return FakeRes()

    monkeypatch.setattr("scripts.audit.find_dead_code.run_cmd", mock_run)

    hits = category_c(tmp_path)
    assert len(hits) == 1
    assert "docs/foo.md:1:referencing v6_build" in hits[0]


def test_category_d(tmp_path, monkeypatch):
    def mock_run(cmd, *args, **kwargs):
        if "-i" in cmd:

            class FakeRes:
                stdout = "ignored.log\n"
                returncode = 0

            return FakeRes()
        else:

            class FakeRes:
                stdout = "foo.bak\nbar.coverage\n"
                returncode = 0

            return FakeRes()

    monkeypatch.setattr("scripts.audit.find_dead_code.run_cmd", mock_run)

    hits = category_d(tmp_path)
    assert len(hits) == 3
    assert "foo.bak" in hits
    assert "bar.coverage" in hits
    assert "ignored.log (tracked but matches .gitignore)" in hits


def test_category_g(tmp_path):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "a.py").write_text("pass", encoding="utf-8")
    sub = scripts / "sub"
    sub.mkdir()
    (sub / "a.py").write_text("pass", encoding="utf-8")

    hits = category_g(tmp_path)
    assert len(hits) == 1
    assert "Collision:" in hits[0]
    assert "a.py" in hits[0]


def test_smoke_main(tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", "")
    report_file = tmp_path / "report.md"
    monkeypatch.setattr("sys.argv", ["find_dead_code.py", "--root", str(tmp_path), "--output", str(report_file)])
    main()
    assert report_file.exists()
    content = report_file.read_text(encoding="utf-8")
    categories = [
        "A Marked-obsolete code",
        "B Dead Python",
        "C Stale docs",
        "D Generated artifacts that escaped",
        "E Old session-state",
        "F Orphaned orchestration artifacts",
        "G Basename collisions across scripts/",
        "H Stale experiments",
        "I Old audit JSONs",
        "J Test fixtures inventory",
    ]
    for c in categories:
        assert c in content


def test_is_excluded():
    # .worktrees (live dispatch worktrees = full repo copies) and archive
    # (Phase-4 holding pen) must be excluded; normal source paths must not.
    assert _is_excluded(Path("/repo/.worktrees/dispatch/x/scripts/foo.py"))
    assert _is_excluded(Path("/repo/archive/2026-06-06-cleanup-1/old.py"))
    assert _is_excluded(Path("/repo/.venv/lib/python/site-packages/x.py"))
    assert _is_excluded(Path("/repo/node_modules/pkg/index.js"))
    assert not _is_excluded(Path("/repo/scripts/build/v7_build.py"))


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


def test_category_a_run_cmd_error(tmp_path, monkeypatch):
    p = tmp_path / "obs.py"
    p.write_text("OBSOLETE\ndef foo(): pass", encoding="utf-8")

    def mock_run_cmd(*args, **kwargs):
        raise RuntimeError("Subprocess crash")

    monkeypatch.setattr("scripts.audit.find_dead_code.run_cmd", mock_run_cmd)

    hits = category_a(tmp_path)
    assert len(hits) == 1
    assert "NEEDS-MANUAL-REVIEW: category A scan error: Subprocess crash" in hits[0]


def test_category_f_scan_error(tmp_path, monkeypatch):
    def mock_rglob(*args, **kwargs):
        raise OSError("Read error")

    monkeypatch.setattr(Path, "rglob", mock_rglob)
    hits = category_f(tmp_path)
    assert len(hits) == 2
    assert "NEEDS-MANUAL-REVIEW: category F scan error: Read error" in hits[1]


def test_vulture_exclude_glob():
    glob_str = _vulture_exclude_glob()
    assert isinstance(glob_str, str)
    assert glob_str != ""
    for name in EXCLUDE_DIR_NAMES:
        assert f"*/{name}/*" in glob_str


def test_category_b_subprocess_argv_types(tmp_path, monkeypatch):
    recorded_argv: list[list[str]] = []

    def fake_subprocess_run(cmd, *args, **kwargs):
        # Emulate real subprocess.run argument validation
        for arg in cmd:
            if not isinstance(arg, (str, bytes, Path)):
                raise TypeError(
                    f"expected str, bytes or os.PathLike object, not {type(arg).__name__}"
                )
        recorded_argv.append(list(cmd))

        class FakeRes:
            stdout = "foo.py:1: unused import 'os'\n"
            returncode = 1

        return FakeRes()

    monkeypatch.setattr("subprocess.run", fake_subprocess_run)

    vulture_bin = tmp_path / ".venv" / "bin" / "vulture"
    vulture_bin.parent.mkdir(parents=True, exist_ok=True)
    vulture_bin.touch()
    vulture_bin.chmod(0o755)

    hits = category_b(tmp_path)
    assert len(hits) == 1
    assert "foo.py:1: unused import 'os'" in hits[0]
    assert len(recorded_argv) == 1
    exclude_idx = recorded_argv[0].index("--exclude")
    exclude_val = recorded_argv[0][exclude_idx + 1]
    assert isinstance(exclude_val, str)
    assert len(exclude_val) > 0
