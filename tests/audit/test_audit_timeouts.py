"""Unit tests for subprocess timeouts in scripts/audit/ modules (#7213 slice 6)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest


def _completed(
    args: list[str] | None = None,
    returncode: int = 0,
    stdout: str = "",
    stderr: str = "",
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=args or [],
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


# ---------------------------------------------------------------------------
# 1. _judge_eval_lib.py
# ---------------------------------------------------------------------------
def test_judge_eval_lib_pull_calibration_cases_timeout(tmp_path: Path) -> None:
    from scripts.audit import _judge_eval_lib as jel

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout='{"id": "c1"}\n')

    with patch("subprocess.run", side_effect=fake_run):
        res = jel.pull_calibration_cases(ref="HEAD", blob="calibration.json", project_root=tmp_path)
        assert res == [{"id": "c1"}]

    assert len(calls) == 1
    assert calls[0]["timeout"] == jel.DEFAULT_GIT_TIMEOUT_SECONDS

    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(["git", "show"], jel.DEFAULT_GIT_TIMEOUT_SECONDS),
    ):
        with pytest.raises(SystemExit):
            jel.pull_calibration_cases(ref="HEAD", blob="calibration.json", project_root=tmp_path)


# ---------------------------------------------------------------------------
# 2. atlas_source_census.py
# ---------------------------------------------------------------------------
def test_atlas_source_census_scan_textbook_pdf_root_timeout(tmp_path: Path) -> None:
    from scripts.audit import atlas_source_census as asc

    # create a dummy pdf file
    pdf_dir = tmp_path / "textbooks"
    pdf_dir.mkdir()
    pdf_file = pdf_dir / "test.pdf"
    pdf_file.write_bytes(b"%PDF-dummy")

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        Path(cmd[3]).write_text("Sample text with page count", encoding="utf-8")
        return _completed(cmd, returncode=0, stdout="Sample text with page count")

    atlas_state = asc.AtlasState(None, False, None, 0, frozenset(), {}, 0)
    census = asc.AtlasSourceCensus(generated_at="now", atlas=atlas_state)
    with patch("subprocess.run", side_effect=fake_run), patch("scripts.audit.atlas_source_census._pdftotext_path", return_value="/usr/bin/pdftotext"):
        asc.scan_textbook_pdf_root(tmp_path, census, pdf_dir)

    assert len(calls) == 1
    assert calls[0]["timeout"] == asc.DEFAULT_PDFTOTEXT_TIMEOUT_SECONDS

    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(["pdftotext"], asc.DEFAULT_PDFTOTEXT_TIMEOUT_SECONDS),
    ), patch("scripts.audit.atlas_source_census._pdftotext_path", return_value="/usr/bin/pdftotext"):
        census_timeout = asc.AtlasSourceCensus(generated_at="now", atlas=atlas_state)
        asc.scan_textbook_pdf_root(tmp_path, census_timeout, pdf_dir)


# ---------------------------------------------------------------------------
# 3. audit_level.py
# ---------------------------------------------------------------------------
def test_audit_level_run_audit_timeout(tmp_path: Path) -> None:
    from scripts.audit import audit_level as al

    dummy_module = tmp_path / "module.md"
    dummy_module.write_text("# Test Module\n", encoding="utf-8")

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="All checks passed")

    with patch("subprocess.run", side_effect=fake_run):
        passed, failed, _failed_mods, _slug_res = al.run_audit([dummy_module], verbose=False)
        assert passed == 1
        assert failed == 0

    assert len(calls) == 1
    assert calls[0]["timeout"] == al.DEFAULT_AUDIT_MODULE_TIMEOUT_SECONDS

    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(["python", "audit_module.py"], al.DEFAULT_AUDIT_MODULE_TIMEOUT_SECONDS),
    ):
        passed, failed, _failed_mods, _slug_res = al.run_audit([dummy_module], verbose=False)
        assert passed == 0
        assert failed == 1


# ---------------------------------------------------------------------------
# 4. bakeoff_run.py
# ---------------------------------------------------------------------------
def test_bakeoff_run_run_command_timeout() -> None:
    from scripts.audit import bakeoff_run as br

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="ok")

    with patch("subprocess.run", side_effect=fake_run):
        proc = br.run_command(["echo", "hi"])
        assert proc.returncode == 0

    assert len(calls) == 1
    assert calls[0]["timeout"] == br.DEFAULT_COMMAND_TIMEOUT_SECONDS

    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(["sleep", "10"], br.DEFAULT_COMMAND_TIMEOUT_SECONDS),
    ):
        proc = br.run_command(["sleep", "10"])
        assert proc.returncode == 124
        assert "timed out after 300.0s" in proc.stderr


# ---------------------------------------------------------------------------
# 5. certify_module.py
# ---------------------------------------------------------------------------
def test_certify_module_timeouts() -> None:
    from scripts.audit import certify_module as cm

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="file1\nfile2\n")

    with patch("subprocess.run", side_effect=fake_run):
        files = cm.tracked_paths(Path("."), [Path("file1"), Path("file2")])
        assert files == {Path("file1"), Path("file2")}
        lines = cm._git_lines(("ls-files",))
        assert lines == ["file1", "file2"]

    assert len(calls) == 2
    assert calls[0]["timeout"] == cm.DEFAULT_GIT_TIMEOUT_SECONDS
    assert calls[1]["timeout"] == cm.DEFAULT_GIT_TIMEOUT_SECONDS

    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(["git", "ls-files"], cm.DEFAULT_GIT_TIMEOUT_SECONDS),
    ):
        assert cm.tracked_paths(Path("."), [Path("file1")]) == set()
        with pytest.raises(RuntimeError) as exc:
            cm._git_lines(("ls-files",))
        assert "timed out after 30.0s" in str(exc.value)

    # test run_check timeout
    check_calls: list[dict] = []

    def fake_check_run(cmd, **kwargs):
        check_calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="build ok")

    check = cm.CommandCheck("build", ("npm", "run", "build"), cwd=Path("."))
    with patch("subprocess.run", side_effect=fake_check_run):
        rc = cm.run_check(check)
        assert rc == 0

    assert len(check_calls) == 1
    assert check_calls[0]["timeout"] == cm.DEFAULT_CHECK_TIMEOUT_SECONDS

    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(["npm", "run", "build"], cm.DEFAULT_CHECK_TIMEOUT_SECONDS),
    ):
        rc = cm.run_check(check)
        assert rc == 124


# ---------------------------------------------------------------------------
# 6. check_core_bare.py
# ---------------------------------------------------------------------------
def test_check_core_bare_timeouts(tmp_path: Path) -> None:
    from scripts.audit import check_core_bare as ccb

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="false\n")

    with patch("subprocess.run", side_effect=fake_run):
        assert ccb._git_config_get(tmp_path, "core.bare") == "false"
        ccb._git_config_set(tmp_path, "core.bare", "false")
        assert ccb._is_bare_broken(tmp_path) is False

    assert len(calls) == 4
    for c in calls:
        assert c["timeout"] == ccb.DEFAULT_GIT_TIMEOUT_SECONDS

    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(["git"], ccb.DEFAULT_GIT_TIMEOUT_SECONDS),
    ):
        assert ccb._git_config_get(tmp_path, "core.bare") is None
        with pytest.raises(subprocess.TimeoutExpired):
            ccb._git_config_set(tmp_path, "core.bare", "false")
        assert ccb._is_bare_broken(tmp_path) is False


# ---------------------------------------------------------------------------
# 7. check_dossier_wordcount.py
# ---------------------------------------------------------------------------
def test_check_dossier_wordcount_timeout() -> None:
    from scripts.audit import check_dossier_wordcount as cdw

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="doc1.md\n")

    with patch("subprocess.run", side_effect=fake_run):
        paths = cdw.changed_paths()
        assert len(paths) == 1

    assert len(calls) == 1
    assert calls[0]["timeout"] == cdw.DEFAULT_GIT_TIMEOUT_SECONDS

    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(["git", "diff"], cdw.DEFAULT_GIT_TIMEOUT_SECONDS),
    ):
        with pytest.raises(SystemExit) as exc:
            cdw.changed_paths()
        assert exc.value.code == 124


# ---------------------------------------------------------------------------
# 8. check_framing_compliance_changed.py
# ---------------------------------------------------------------------------
def test_check_framing_compliance_changed_timeout(tmp_path: Path) -> None:
    from scripts.audit import check_framing_compliance_changed as cfcc

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="curriculum/l2-uk-en/plans/folk/test.yaml\n")

    with patch("subprocess.run", side_effect=fake_run):
        paths = cfcc.changed_paths_from_git(tmp_path, "origin/main")
        assert len(paths) == 1

    assert len(calls) == 1
    assert calls[0]["timeout"] == cfcc.DEFAULT_GIT_TIMEOUT_SECONDS

    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(["git", "diff"], cfcc.DEFAULT_GIT_TIMEOUT_SECONDS),
    ):
        with pytest.raises(SystemExit) as exc:
            cfcc.changed_paths_from_git(tmp_path, "origin/main")
        assert exc.value.code == 124


# ---------------------------------------------------------------------------
# 9. check_locked_module_not_published.py
# ---------------------------------------------------------------------------
def test_check_locked_module_not_published_timeout() -> None:
    from scripts.audit import check_locked_module_not_published as clm

    calls: list[dict] = []

    def fake_check_output(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return "main\n"

    with patch("subprocess.check_output", side_effect=fake_check_output):
        out = clm._git_output(["rev-parse", "--abbrev-ref", "HEAD"])
        assert out == "main\n"

    assert len(calls) == 1
    assert calls[0]["timeout"] == clm.DEFAULT_GIT_TIMEOUT_SECONDS


# ---------------------------------------------------------------------------
# 10. check_mdx_forward_parity.py
# ---------------------------------------------------------------------------
def test_check_mdx_forward_parity_timeout() -> None:
    from scripts.audit import check_mdx_forward_parity as cmfp

    calls: list[dict] = []

    def fake_check_output(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return "site/src/content/docs/a1/test.mdx\n"

    with patch("subprocess.check_output", side_effect=fake_check_output):
        files = cmfp._get_local_changed_files()
        assert len(files) == 1

    assert len(calls) == 1
    assert calls[0]["timeout"] == cmfp.DEFAULT_GIT_TIMEOUT_SECONDS

    with patch(
        "subprocess.check_output",
        side_effect=subprocess.TimeoutExpired(["git", "diff"], cmfp.DEFAULT_GIT_TIMEOUT_SECONDS),
    ):
        assert cmfp._get_local_changed_files() == []


# ---------------------------------------------------------------------------
# 11. check_mdx_generation_drift.py
# ---------------------------------------------------------------------------
def test_check_mdx_generation_drift_timeouts() -> None:
    from scripts.audit import check_mdx_generation_drift as cmgd

    calls: list[dict] = []

    def fake_check_output(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return "file.txt\n"

    with patch("subprocess.check_output", side_effect=fake_check_output):
        files = cmgd._git_changed_files("origin/main")
        assert len(files) == 1

    assert len(calls) == 2
    assert calls[0]["timeout"] == cmgd.DEFAULT_GIT_TIMEOUT_SECONDS
    assert calls[1]["timeout"] == cmgd.DEFAULT_GIT_TIMEOUT_SECONDS

    with patch(
        "subprocess.check_output",
        side_effect=subprocess.TimeoutExpired(["git"], cmgd.DEFAULT_GIT_TIMEOUT_SECONDS),
    ):
        with pytest.raises(RuntimeError) as exc:
            cmgd._git_changed_files("origin/main")
        assert "timed out after 30.0s" in str(exc.value)

    run_calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        run_calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0)

    target = cmgd.ModuleTarget(level="a1", slug="test", local_num=1)
    with patch("subprocess.run", side_effect=fake_run), patch.object(Path, "exists", return_value=True):
        cmgd._run_generator(target)

    assert len(run_calls) == 1
    assert run_calls[0]["timeout"] == cmgd.DEFAULT_GENERATE_TIMEOUT_SECONDS


# ---------------------------------------------------------------------------
# 12. check_mdx_source_parity.py
# ---------------------------------------------------------------------------
def test_check_mdx_source_parity_timeouts() -> None:
    from scripts.audit import check_mdx_source_parity as cmsp

    calls: list[dict] = []

    def fake_check_output(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return "D\tdeleted.txt\n"

    with patch("subprocess.check_output", side_effect=fake_check_output):
        assert len(cmsp.get_changed_files(base="origin/main")) == 1
        assert len(cmsp.get_deleted_files(base="origin/main")) == 1
        assert cmsp.is_whitespace_only(Path("test.txt"), base="origin/main") is False
        assert cmsp.is_nav_only_mdx_change(Path("test.mdx"), base="origin/main") is False

    for c in calls:
        assert c["timeout"] == cmsp.DEFAULT_GIT_TIMEOUT_SECONDS

    with patch(
        "subprocess.check_output",
        side_effect=subprocess.TimeoutExpired(["git"], cmsp.DEFAULT_GIT_TIMEOUT_SECONDS),
    ):
        assert cmsp.get_changed_files(base="origin/main") == []
        assert cmsp.get_deleted_files(base="origin/main") == set()
        assert cmsp.is_whitespace_only(Path("test.txt"), base="origin/main") is False
        assert cmsp.is_nav_only_mdx_change(Path("test.mdx"), base="origin/main") is False


# ---------------------------------------------------------------------------
# 13. check_no_internal_ids.py
# ---------------------------------------------------------------------------
def test_check_no_internal_ids_timeout() -> None:
    from scripts.audit import check_no_internal_ids as cnii

    calls: list[dict] = []

    def fake_check_output(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return "output\n"

    with patch("subprocess.check_output", side_effect=fake_check_output):
        res = cnii._git_output(["status"])
        assert res == "output\n"

    assert len(calls) == 1
    assert calls[0]["timeout"] == cnii.DEFAULT_GIT_TIMEOUT_SECONDS


# ---------------------------------------------------------------------------
# 14. check_no_private_source_review_exports.py
# ---------------------------------------------------------------------------
def test_check_no_private_source_review_exports_timeout() -> None:
    from scripts.audit import check_no_private_source_review_exports as cnp

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="staged.json\n")

    with patch("subprocess.run", side_effect=fake_run):
        paths = cnp.staged_paths()
        assert len(paths) == 1

    assert len(calls) == 1
    assert calls[0]["timeout"] == cnp.DEFAULT_GIT_TIMEOUT_SECONDS


# ---------------------------------------------------------------------------
# 15. check_promote_quality_changed.py
# ---------------------------------------------------------------------------
def test_check_promote_quality_changed_timeout(tmp_path: Path) -> None:
    from scripts.audit import check_promote_quality_changed as cpqc

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="curriculum/l2-uk-en/a1/m1/module.md\n")

    with patch("subprocess.run", side_effect=fake_run):
        paths = cpqc.changed_paths_from_git(tmp_path, "origin/main")
        assert len(paths) == 1

    assert len(calls) == 1
    assert calls[0]["timeout"] == cpqc.DEFAULT_GIT_TIMEOUT_SECONDS

    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(["git", "diff"], cpqc.DEFAULT_GIT_TIMEOUT_SECONDS),
    ):
        with pytest.raises(SystemExit) as exc:
            cpqc.changed_paths_from_git(tmp_path, "origin/main")
        assert exc.value.code == 124


# ---------------------------------------------------------------------------
# 16. check_review_issues.py
# ---------------------------------------------------------------------------
def test_check_review_issues_timeouts(tmp_path: Path) -> None:
    from scripts.audit import check_review_issues as cri

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="PASS\n")

    with patch("subprocess.run", side_effect=fake_run):
        out = cri._run_gh(["issue", "list"])
        assert out == "PASS"
        passed, text = cri._run_audit(tmp_path / "module.md")
        assert passed is True

    assert len(calls) == 2
    assert calls[0]["timeout"] == cri.DEFAULT_GH_TIMEOUT_SECONDS
    assert calls[1]["timeout"] == cri.DEFAULT_AUDIT_MODULE_TIMEOUT_SECONDS

    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(["audit_module.py"], cri.DEFAULT_AUDIT_MODULE_TIMEOUT_SECONDS),
    ):
        passed, text = cri._run_audit(tmp_path / "module.md")
        assert passed is False
        assert "timed out after 60.0s" in text


# ---------------------------------------------------------------------------
# 17. find_dead_code.py
# ---------------------------------------------------------------------------
def test_find_dead_code_timeout() -> None:
    from scripts.audit import find_dead_code as fdc

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="dead code")

    with patch("subprocess.run", side_effect=fake_run):
        res = fdc.run_cmd(["echo", "test"])
        assert res is not None

    assert len(calls) == 1
    assert calls[0]["timeout"] == fdc.DEFAULT_COMMAND_TIMEOUT_SECONDS

    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(["echo"], fdc.DEFAULT_COMMAND_TIMEOUT_SECONDS),
    ):
        assert fdc.run_cmd(["echo", "test"]) is None


# ---------------------------------------------------------------------------
# 18. freeze_benchmark.py
# ---------------------------------------------------------------------------
def test_freeze_benchmark_timeout() -> None:
    from scripts.audit import freeze_benchmark as fb

    calls: list[dict] = []

    def fake_check_output(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return "a" * 40 + "\n"

    with patch("subprocess.check_output", side_effect=fake_check_output):
        head = fb._git_head()
        assert head == "a" * 40

    assert len(calls) == 1
    assert calls[0]["timeout"] == fb.DEFAULT_GIT_TIMEOUT_SECONDS

    with patch(
        "subprocess.check_output",
        side_effect=subprocess.TimeoutExpired(["git"], fb.DEFAULT_GIT_TIMEOUT_SECONDS),
    ):
        with pytest.raises(fb.ManifestConfigError):
            fb._git_head()


# ---------------------------------------------------------------------------
# 19. hermes_nightly_audit.py
# ---------------------------------------------------------------------------
def test_hermes_nightly_audit_timeouts() -> None:
    from scripts.audit import hermes_nightly_audit as hna

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        if "track_deterministic_audit.py" in cmd[1]:
            return _completed(cmd, returncode=0, stdout=json.dumps({"track": "a1", "summary": {}}))
        return _completed(cmd, returncode=0, stdout="insights ok")

    with patch("subprocess.run", side_effect=fake_run):
        res = hna.run_track_audit("a1")
        assert res["track"] == "a1"
        insights = hna.get_hermes_insights()
        assert insights == "insights ok"

    assert len(calls) == 2
    assert calls[0]["timeout"] == hna.DEFAULT_TRACK_AUDIT_TIMEOUT_SECONDS
    assert calls[1]["timeout"] == hna.DEFAULT_HERMES_TIMEOUT_SECONDS

    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(["track_deterministic_audit.py"], hna.DEFAULT_TRACK_AUDIT_TIMEOUT_SECONDS),
    ):
        res = hna.run_track_audit("a1")
        assert res["summary"]["findings_total"] == 1
        assert "timed out after 300.0s" in res["findings"][0]["message"]

    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(["hermes"], hna.DEFAULT_HERMES_TIMEOUT_SECONDS),
    ):
        assert hna.get_hermes_insights() == "insights unavailable"


# ---------------------------------------------------------------------------
# 20. ingest_ua_gec_gold.py
# ---------------------------------------------------------------------------
def test_ingest_ua_gec_gold_timeout(tmp_path: Path) -> None:
    from scripts.audit import ingest_ua_gec_gold as iug

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="b" * 40 + "\n")

    with patch("subprocess.run", side_effect=fake_run):
        assert iug.source_commit(tmp_path) == "b" * 40

    assert len(calls) == 1
    assert calls[0]["timeout"] == iug.DEFAULT_GIT_TIMEOUT_SECONDS

    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(["git"], iug.DEFAULT_GIT_TIMEOUT_SECONDS),
    ):
        assert iug.source_commit(tmp_path) == "unknown"


# ---------------------------------------------------------------------------
# 21. layerb_differential_replay.py
# ---------------------------------------------------------------------------
def test_layerb_differential_replay_timeouts() -> None:
    from scripts.audit import layerb_differential_replay as ldr

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return subprocess.CompletedProcess(cmd, returncode=0, stdout=b"# mock source\n")

    with patch("subprocess.run", side_effect=fake_run):
        hashes = ldr._helper_hashes("main")
        assert "grounding_gate_v2.py" in hashes

    assert len(calls) == 1
    assert calls[0]["timeout"] == ldr.DEFAULT_GIT_TIMEOUT_SECONDS


# ---------------------------------------------------------------------------
# 22. lint_agent_trailer.py
# ---------------------------------------------------------------------------
def test_lint_agent_trailer_timeout() -> None:
    from scripts.audit import lint_agent_trailer as lat

    calls: list[dict] = []

    def fake_check_output(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return "c" * 40 + "\n"

    with patch("subprocess.check_output", side_effect=fake_check_output):
        commits = lat._commits_in_range("main..HEAD")
        assert len(commits) == 1

    assert len(calls) == 1
    assert calls[0]["timeout"] == lat.DEFAULT_GIT_TIMEOUT_SECONDS


# ---------------------------------------------------------------------------
# 23. lint_opsec_leaks.py
# ---------------------------------------------------------------------------
def test_lint_opsec_leaks_timeouts() -> None:
    from scripts.audit import lint_opsec_leaks as lol

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        if cmd[1] == "show":
            return subprocess.CompletedProcess(cmd, returncode=0, stdout=b"content")
        if "-z" in cmd:
            return subprocess.CompletedProcess(cmd, returncode=0, stdout=b"file1\x00file2\x00")
        return _completed(cmd, returncode=0, stdout="line1\nline2\n")

    with patch("subprocess.run", side_effect=fake_run):
        assert lol.get_git_content("file.txt") == "content"
        assert lol.run_git_nul_separated(["git", "diff", "-z"]) == ["file1", "file2"]
        assert lol.run_git_lines(["git", "status"]) == ["line1", "line2"]

    assert len(calls) == 3
    for c in calls:
        assert c["timeout"] == lol.DEFAULT_GIT_TIMEOUT_SECONDS

    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(["git"], lol.DEFAULT_GIT_TIMEOUT_SECONDS),
    ):
        assert lol.get_git_content("file.txt") is None


# ---------------------------------------------------------------------------
# 24. lint_word_atlas.py
# ---------------------------------------------------------------------------
def test_lint_word_atlas_timeout() -> None:
    from scripts.audit import lint_word_atlas as lwa

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return subprocess.CompletedProcess(cmd, returncode=0, stdout=b'{"key": "value"}')

    with patch("subprocess.run", side_effect=fake_run):
        res = lwa._git_show_json("HEAD", "atlas.json")
        assert res == {"key": "value"}

    assert len(calls) == 1
    assert calls[0]["timeout"] == lwa.DEFAULT_GIT_TIMEOUT_SECONDS

    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(["git"], lwa.DEFAULT_GIT_TIMEOUT_SECONDS),
    ):
        assert lwa._git_show_json("HEAD", "atlas.json") is None


# ---------------------------------------------------------------------------
# 25. post_build_review.py
# ---------------------------------------------------------------------------
def test_post_build_review_timeout(tmp_path: Path) -> None:
    from scripts.audit import post_build_review as pbr

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout=str(tmp_path / ".git") + "\n")

    with patch("subprocess.run", side_effect=fake_run):
        venv_py = tmp_path / ".venv" / "bin" / "python"
        venv_py.parent.mkdir(parents=True)
        venv_py.touch()
        py_path = pbr.resolve_venv_python(tmp_path / "worktree")
        assert py_path == venv_py

    assert len(calls) == 1
    assert calls[0]["timeout"] == pbr.DEFAULT_GIT_TIMEOUT_SECONDS

    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(["git"], pbr.DEFAULT_GIT_TIMEOUT_SECONDS),
    ):
        with pytest.raises(pbr.ReviewProtocolError) as exc:
            pbr.resolve_venv_python(tmp_path / "worktree_missing")
        assert "timed out after 30.0s" in str(exc.value)


# ---------------------------------------------------------------------------
# 26. run_gemini_1x17_sweep.py
# ---------------------------------------------------------------------------
def test_run_gemini_1x17_sweep_timeouts() -> None:
    from scripts.audit import run_gemini_1x17_sweep as rgs

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        if "codexbar" in cmd[0]:
            return _completed(
                cmd,
                returncode=0,
                stdout=json.dumps({
                    "id": "antigravity-quota-summary-gemini-5h",
                    "window": {"usedPercent": 50.0, "resetsAt": "2026-08-24T18:00:00Z"},
                }),
            )
        return _completed(cmd, returncode=0)

    with patch("subprocess.run", side_effect=fake_run):
        used, _mins = rgs._throttle_quota()
        assert used == 50.0

    assert len(calls) == 1
    assert calls[0]["timeout"] == rgs.DEFAULT_CODEXBAR_TIMEOUT_SECONDS

    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(["codexbar"], rgs.DEFAULT_CODEXBAR_TIMEOUT_SECONDS),
    ):
        with pytest.raises(RuntimeError) as exc:
            rgs._throttle_quota()
        assert "codexbar timed out after 30.0s" in str(exc.value)


# ---------------------------------------------------------------------------
# 27. run_subscription_1x17_sweep.py
# ---------------------------------------------------------------------------
def test_run_subscription_1x17_sweep_timeout(tmp_path: Path) -> None:
    from scripts.audit import run_subscription_1x17_sweep as rss

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0)

    with patch("subprocess.run", side_effect=fake_run), patch.object(rss, "time"):
        rc = rss._run_cell(tmp_path, "claude-opus-4-8", "vesnianky", "raw")
        assert rc == 0

    assert len(calls) == 1
    assert calls[0]["timeout"] == rss.DEFAULT_BAKEOFF_CELL_TIMEOUT_SECONDS

    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(["python"], rss.DEFAULT_BAKEOFF_CELL_TIMEOUT_SECONDS),
    ), patch.object(rss, "time"):
        rc = rss._run_cell(tmp_path, "claude-opus-4-8", "vesnianky", "raw")
        assert rc == 124


# ---------------------------------------------------------------------------
# 28. russianism_eval.py
# ---------------------------------------------------------------------------
def test_russianism_eval_timeout() -> None:
    from scripts.audit import russianism_eval as re_eval

    caller = re_eval.BridgeCaller("run-123")
    prompt = re_eval.PromptCase(
        id="test-1",
        category="calque",
        prompt_text="translate this",
        expected_calque_categories=["test"],
        notes="",
    )

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="model translation")

    with patch("subprocess.run", side_effect=fake_run):
        _call, resp = caller(prompt, "gemini-3.1-pro-high")
        assert resp == "model translation"

    assert len(calls) == 1
    assert calls[0]["timeout"] == re_eval.DEFAULT_BRIDGE_TIMEOUT_SECONDS

    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(["python"], re_eval.DEFAULT_BRIDGE_TIMEOUT_SECONDS),
    ):
        with pytest.raises(RuntimeError) as exc:
            caller(prompt, "gemini-3.1-pro-high")
        assert "timed out after 300.0s" in str(exc.value)


# ---------------------------------------------------------------------------
# 29. track_deterministic_audit.py
# ---------------------------------------------------------------------------
def test_track_deterministic_audit_timeouts() -> None:
    from scripts.audit import track_deterministic_audit as tda

    calls: list[dict] = []

    def fake_check_output(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return "file.txt\n"

    with patch("subprocess.check_output", side_effect=fake_check_output):
        res = tda.git_output(["status"])
        assert res == "file.txt\n"

    assert len(calls) == 1
    assert calls[0]["timeout"] == tda.DEFAULT_GIT_TIMEOUT_SECONDS

    run_calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        run_calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0)

    with patch("subprocess.run", side_effect=fake_run):
        assert tda.protected_config_changed() == []

    assert len(run_calls) > 0
    assert run_calls[0]["timeout"] == tda.DEFAULT_GIT_TIMEOUT_SECONDS

    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(["git"], tda.DEFAULT_GIT_TIMEOUT_SECONDS),
    ):
        # TimeoutExpired maps to non-zero rc (124) -> flagged as modified
        assert len(tda.protected_config_changed()) > 0
