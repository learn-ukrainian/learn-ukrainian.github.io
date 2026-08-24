"""Unit tests for subprocess timeout bounds in scripts/lexicon/ (#7213 slice 8)."""

from __future__ import annotations

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


def test_anchor_curation_evidence_audit_entries_timeout() -> None:
    from scripts.lexicon import anchor_curation_evidence as ace

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="lemma\tcefr\tslug\tbucket\n")

    with patch("subprocess.run", side_effect=fake_run):
        with pytest.raises(RuntimeError, match="unexpected search_no_visible_gloss count"):
            ace.audit_entries()

    assert len(calls) == 1
    assert calls[0]["timeout"] == ace.DEFAULT_AUDIT_COMMAND_TIMEOUT_SECONDS

    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(list(ace.AUDIT_COMMAND), ace.DEFAULT_AUDIT_COMMAND_TIMEOUT_SECONDS),
    ):
        with pytest.raises(RuntimeError, match="Atlas richness audit timed out"):
            ace.audit_entries()


def test_check_manifest_vocabulary_coverage_changed_vocab_modules_timeout(tmp_path: Path) -> None:
    from scripts.lexicon import check_manifest_vocabulary_coverage as cmvc

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="")

    with patch("subprocess.run", side_effect=fake_run):
        assert cmvc.changed_vocab_modules(tmp_path, "origin/main") == set()

    assert len(calls) == 1
    assert calls[0]["timeout"] == cmvc.DEFAULT_GIT_TIMEOUT_SECONDS

    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(["git", "diff"], cmvc.DEFAULT_GIT_TIMEOUT_SECONDS),
    ):
        assert cmvc.changed_vocab_modules(tmp_path, "origin/main") is None


def test_content_lexicon_reconciler_get_local_changed_files_timeout() -> None:
    from scripts.lexicon import content_lexicon_reconciler as clr

    calls: list[dict] = []

    def fake_check_output(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return "site/src/content/docs/foo.md\n"

    with patch("subprocess.check_output", side_effect=fake_check_output):
        paths = clr._get_local_changed_files(cached=False)

    assert len(paths) == 1
    assert len(calls) == 1
    assert calls[0]["timeout"] == clr.DEFAULT_GIT_TIMEOUT_SECONDS

    with patch(
        "subprocess.check_output",
        side_effect=subprocess.TimeoutExpired(["git", "diff"], clr.DEFAULT_GIT_TIMEOUT_SECONDS),
    ):
        assert clr._get_local_changed_files(cached=False) == []


def test_extract_book_headword_inventory_run_timeout() -> None:
    from scripts.lexicon import extract_book_headword_inventory as ebhi

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="Pages: 1\n")

    with patch("subprocess.run", side_effect=fake_run):
        ebhi._run(["pdfinfo", "book.pdf"])

    assert len(calls) == 1
    assert calls[0]["timeout"] == ebhi.DEFAULT_PDFTOTEXT_TIMEOUT_SECONDS

    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(["pdfinfo"], ebhi.DEFAULT_PDFTOTEXT_TIMEOUT_SECONDS),
    ):
        with pytest.raises(ebhi.ExtractionError, match="command timed out"):
            ebhi._run(["pdfinfo", "book.pdf"])


def test_publish_manifest_gh_subprocess_timeouts() -> None:
    from scripts.lexicon import publish_manifest as pm

    upload_calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        upload_calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout=b'{"assets":[]}' if b"view" in str(cmd).encode() else b"")

    with patch("subprocess.run", side_effect=fake_run):
        pm._release_asset_names()
        pm._download_release_asset("lexicon-manifest.json.gz")
        pm.upload_release_asset(Path("lexicon-manifest.json.gz"))

    assert len(upload_calls) == 3
    assert all(call["timeout"] == pm.DEFAULT_GH_TIMEOUT_SECONDS for call in upload_calls)

    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(["gh", "release", "view"], pm.DEFAULT_GH_TIMEOUT_SECONDS),
    ):
        with pytest.raises(subprocess.TimeoutExpired):
            pm._release_asset_names()

    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(["gh", "release", "download"], pm.DEFAULT_GH_TIMEOUT_SECONDS),
    ):
        with pytest.raises(pm.ManifestPublishError, match="could not read the canonical published Atlas manifest"):
            pm.download_published_manifest()


def test_atlas_job_collect_host_load_systemctl_timeout(tmp_path: Path) -> None:
    from scripts.lexicon.runner import atlas_job

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="")

    with patch("subprocess.run", side_effect=fake_run):
        atlas_job.collect_host_load(run_root=tmp_path)

    assert len(calls) == 1
    assert calls[0]["timeout"] == atlas_job.DEFAULT_SYSTEMCTL_TIMEOUT_SECONDS

    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(["systemctl"], atlas_job.DEFAULT_SYSTEMCTL_TIMEOUT_SECONDS),
    ):
        payload = atlas_job.collect_host_load(run_root=tmp_path)
        assert payload["job_unit"]["active_count"] == 0


def test_atlas_job_ssh_timeout() -> None:
    from scripts.lexicon.runner import atlas_job

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="")

    with patch("subprocess.run", side_effect=fake_run):
        atlas_job._ssh("atlas-runner", "true")

    assert len(calls) == 1
    assert calls[0]["timeout"] == atlas_job.DEFAULT_SSH_TIMEOUT_SECONDS

    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(["ssh"], atlas_job.DEFAULT_SSH_TIMEOUT_SECONDS),
    ):
        with pytest.raises(ConnectionError, match="ssh timed out"):
            atlas_job._ssh("atlas-runner", "true")


def test_atlas_job_primary_checkout_root_git_timeout() -> None:
    from scripts.lexicon.runner import atlas_job

    calls: list[dict] = []

    def fake_check_output(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return "/tmp/project/.git\n"

    with patch("subprocess.check_output", side_effect=fake_check_output):
        root = atlas_job.primary_checkout_root()

    assert len(calls) == 1
    assert calls[0]["timeout"] == atlas_job.DEFAULT_GIT_TIMEOUT_SECONDS
    assert root == atlas_job.repo_root()

    with patch(
        "subprocess.check_output",
        side_effect=subprocess.TimeoutExpired(["git", "rev-parse"], atlas_job.DEFAULT_GIT_TIMEOUT_SECONDS),
    ):
        assert atlas_job.primary_checkout_root() == atlas_job.repo_root()


def test_atlas_job_submit_launcher_timeout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from scripts.lexicon.runner import atlas_job

    fake = atlas_job.FakeHostAdapter()
    atlas_job.set_host_adapter(fake)
    monkeypatch.setattr(atlas_job, "registry_dir", lambda: tmp_path)
    monkeypatch.setenv("ATLAS_RUN_ROOT", str(tmp_path / "run-root"))
    calls: list[dict] = []

    def fake_call(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return 0

    monkeypatch.setattr(atlas_job.subprocess, "call", fake_call)
    plan = {
        "schema": "atlas-job.v1",
        "id": "timeout-submit-job",
        "kind": "reenrich",
        "host": "atlas-runner",
        "args": ["--target", "missing-translation", "--no-poll"],
        "pointer_write": False,
        "result_sink": "restic",
        "denominator": 10,
        "issue": 6867,
        "success": {"circuit_breaker": False, "min_filled": 0},
    }
    rc = atlas_job.submit(plan, dry_run=False, host_adapter=fake)
    assert rc == 0
    assert len(calls) == 1
    assert calls[0]["timeout"] == atlas_job.DEFAULT_LAUNCHER_SUBPROCESS_TIMEOUT_SECONDS


def test_atlas_job_submit_launcher_timeout_rejects(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from scripts.lexicon.runner import atlas_job

    fake = atlas_job.FakeHostAdapter()
    atlas_job.set_host_adapter(fake)
    monkeypatch.setattr(atlas_job, "registry_dir", lambda: tmp_path)
    monkeypatch.setenv("ATLAS_RUN_ROOT", str(tmp_path / "run-root"))

    def timeout_call(cmd, **kwargs):
        raise subprocess.TimeoutExpired(cmd, atlas_job.DEFAULT_LAUNCHER_SUBPROCESS_TIMEOUT_SECONDS)

    monkeypatch.setattr(atlas_job.subprocess, "call", timeout_call)
    plan = {
        "schema": "atlas-job.v1",
        "id": "timeout-submit-reject",
        "kind": "reenrich",
        "host": "atlas-runner",
        "args": ["--target", "missing-translation", "--no-poll"],
        "pointer_write": False,
        "result_sink": "restic",
        "denominator": 10,
        "issue": 6867,
        "success": {"circuit_breaker": False, "min_filled": 0},
    }
    rc = atlas_job.submit(plan, dry_run=False, host_adapter=fake)
    assert rc == 124
    row = atlas_job.load_registry("timeout-submit-reject")
    assert row is not None
    assert row["state"] == "rejected"
    assert row["submit_exit"] == 124


def test_atlas_job_pull_launcher_timeout(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from scripts.lexicon.runner import atlas_job

    monkeypatch.setenv("ATLAS_RUN_ROOT", str(tmp_path / "run-root"))
    calls: list[dict] = []

    def fake_call(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return 0

    monkeypatch.setattr(atlas_job.subprocess, "call", fake_call)
    assert atlas_job.pull(host="test-runner-host") == 0
    assert len(calls) == 1
    assert calls[0]["timeout"] == atlas_job.DEFAULT_LAUNCHER_SUBPROCESS_TIMEOUT_SECONDS

    def timeout_call(cmd, **kwargs):
        raise subprocess.TimeoutExpired(cmd, atlas_job.DEFAULT_LAUNCHER_SUBPROCESS_TIMEOUT_SECONDS)

    monkeypatch.setattr(atlas_job.subprocess, "call", timeout_call)
    assert atlas_job.pull(host="test-runner-host") == 124


def test_durable_mirror_snapshot_ssh_probe_timeout() -> None:
    from scripts.lexicon.runner import durable_mirror as dm

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=255, stderr=b"ssh failed")

    with patch("subprocess.run", side_effect=fake_run), patch(
        "scripts.lexicon.runner.durable_mirror.sync_source_to_mirror"
    ):
        with pytest.raises(dm.DurableMirrorError, match="could not probe remote runner liveness"):
            dm.snapshot("host:/remote/work", Path("/tmp/mirror"), allow_live=False)

    assert len(calls) == 1
    assert calls[0]["timeout"] == dm.DEFAULT_SSH_PROBE_TIMEOUT_SECONDS


def test_durable_mirror_snapshot_ssh_probe_timeout_expired() -> None:
    from scripts.lexicon.runner import durable_mirror as dm

    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(["ssh"], dm.DEFAULT_SSH_PROBE_TIMEOUT_SECONDS),
    ), patch("scripts.lexicon.runner.durable_mirror.sync_source_to_mirror"):
        with pytest.raises(dm.DurableMirrorError, match="ssh timed out"):
            dm.snapshot("host:/remote/work", Path("/tmp/mirror"), allow_live=False)


def test_transport_zstd_subprocess_timeouts() -> None:
    from scripts.lexicon.runner import transport

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout=b"compressed")

    with patch("shutil.which", return_value="/usr/bin/zstd"), patch("subprocess.run", side_effect=fake_run):
        assert transport.zstd_compress(b"payload") == b"compressed"
        assert transport.zstd_decompress(b"payload") == b"compressed"

    assert len(calls) == 2
    assert all(call["timeout"] == transport.DEFAULT_ZSTD_TIMEOUT_SECONDS for call in calls)

    with patch("shutil.which", return_value="/usr/bin/zstd"), patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(["zstd"], transport.DEFAULT_ZSTD_TIMEOUT_SECONDS),
    ):
        with pytest.raises(transport.TransportError, match="zstd compress timed out"):
            transport.zstd_compress(b"payload")
        with pytest.raises(transport.TransportError, match="zstd decompress timed out"):
            transport.zstd_decompress(b"payload")
