from pathlib import Path

from scripts.audit.find_dead_code import (
    _is_excluded,
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

    hits = category_b(tmp_path)
    assert len(hits) == 1
    assert "foo.py:1: unused import 'os'" in hits[0]


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
