import json
import os
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest

from scripts.projects.open_model_data.evaluation import custody
from scripts.projects.open_model_data.review_build.errors import BuildError


def events(fixture):
    return [json.loads(line) for line in (fixture.root / custody.LOG).read_bytes().split(b"\n") if line]


def read(fixture, purpose="final_evaluation", ref=None):
    return custody.read_sealed(ref or fixture.ref, purpose, custody_root=fixture.root)


def test_valid_control_and_privacy(sealed):
    payload = read(sealed)
    assert payload.data() == sealed.payload
    assert repr(payload) == str(payload) == "<SealedPayload redacted>"
    assert read(sealed, "custody_verify") is True
    assert [e["event"] for e in events(sealed)] == ["genesis", "sealed", "attempt", "completed", "attempt", "completed"]
    log = (sealed.root / custody.LOG).read_bytes()
    assert log.isascii() and sealed.payload not in log
    assert str(sealed.root).encode() not in log
    assert b"membership" not in log
    for path in sealed.root.iterdir():
        assert path.stat().st_mode & 0o777 == 0o600


@pytest.mark.parametrize(
    "case,code",
    [
        ("purpose", "purpose_invalid"),
        ("purpose-list", "purpose_invalid"),
        ("ref", "artifact_ref"),
        ("ref-type", "artifact_ref"),
        ("ref-invalid", "artifact_ref"),
        ("unmerged", "manifest_unmerged"),
        ("manifest-json", "manifest_unmerged"),
        ("manifest-schema", "manifest_invalid"),
        ("manifest-entries", "manifest_invalid"),
        ("manifest-duplicate", "artifact_ref"),
        ("manifest-fields", "manifest_invalid"),
        ("genesis", "custody_genesis"),
        ("issuer-prefix", "manifest_invalid"),
        ("issuer-running", "issuer_invalid"),
        ("issuer-missing", "record_unavailable"),
        ("issuer-task", "issuer_invalid"),
        ("issuer-model", "model_not_admitted"),
        ("issuer-nonce", "issuer_invalid"),
        ("sealed-missing", "issuer_invalid"),
        ("not-steward", "not_steward_family"),
        ("stale-before", "not_running"),
    ],
)
def test_refusals_logged_without_open(sealed, monkeypatch, case, code):
    purpose = "final_evaluation"
    ref = sealed.ref
    if case == "purpose":
        purpose = "SYNTHETIC /private/ АБВ membership"
    elif case == "purpose-list":
        purpose = []
    elif case == "ref":
        ref = custody.ArtifactRef("C2", "final", "synthetic-v1")
    elif case == "ref-type":
        ref = object()
    elif case == "ref-invalid":
        ref = custody.ArtifactRef("АБВ", "final", "/private/")
    elif case in {"unmerged", "manifest-json"}:
        monkeypatch.setattr(
            custody, "run_git", lambda *a, **kw: SimpleNamespace(returncode=1 if case == "unmerged" else 0, stdout=b"{")
        )
    elif case == "manifest-schema":
        sealed.manifest["schema"] = "wrong"
    elif case == "manifest-entries":
        sealed.manifest["entries"] = [None]
    elif case == "manifest-duplicate":
        sealed.manifest["entries"].append(dict(sealed.entry))
    elif case == "manifest-fields":
        sealed.entry["bytes"] = True
    elif case == "genesis":
        sealed.entry["custody_genesis_sha256"] = "0" * 64
    elif case == "issuer-prefix":
        sealed.entry["sealed_by_task_id"] = "ordinary-task"
    elif case == "issuer-running":
        sealed.issuer["status"] = "running"
        sealed.issuer_path.write_text(json.dumps(sealed.issuer))
    elif case == "issuer-missing":
        sealed.issuer_path.unlink()
    elif case.startswith("issuer-"):
        sealed.issuer[{"issuer-task": "task_id", "issuer-model": "model", "issuer-nonce": "run_nonce"}[case]] = (
            "wrong" if case != "issuer-nonce" else ""
        )
        sealed.issuer_path.write_text(json.dumps(sealed.issuer))
    elif case == "sealed-missing":
        (sealed.root / custody.LOG).write_bytes(custody.canonical(events(sealed)[0]) + b"\n")
    elif case == "not-steward":
        monkeypatch.setenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", "ordinary-reader")
    else:
        sealed.dispatched.record["status"] = "done"
        sealed.dispatched.save()
    original = custody.OutputGuard.read
    opened = []

    def spy(out, name):
        if name.endswith(".sealed"):
            opened.append(name)
        return original(out, name)

    monkeypatch.setattr(custody.OutputGuard, "read", spy)
    with pytest.raises(custody.CustodyRefused, match=f"^{code}$"):
        custody.read_sealed(ref, purpose, custody_root=sealed.root)
    assert opened == []
    assert [(e["event"], e.get("code")) for e in events(sealed)[-2:]] == [("attempt", None), ("refused", code)]
    assert (sealed.root / custody.LOG).read_bytes().isascii()


@pytest.mark.parametrize("kind", ["symlink", "hardlink", "mode", "missing", "directory"])
def test_unsafe_artifact_open_logged(sealed, kind, tmp_path):
    artifact = sealed.root / custody._artifact_name(sealed.ref)
    if kind == "symlink":
        target = tmp_path / "SYNTHETIC-target"
        target.write_bytes(sealed.payload)
        artifact.unlink()
        artifact.symlink_to(target)
    elif kind == "hardlink":
        os.link(artifact, tmp_path / "SYNTHETIC-link")
    elif kind == "mode":
        artifact.chmod(0o640)
    elif kind == "missing":
        artifact.unlink()
    else:
        artifact.unlink()
        artifact.mkdir(mode=0o700)
    with pytest.raises(custody.CustodyRefused, match="artifact_open"):
        read(sealed)
    assert events(sealed)[-1]["event"] == "open_failed"


def test_equal_count_swapped_bytes_discarded(sealed):
    artifact = sealed.root / custody._artifact_name(sealed.ref)
    artifact.write_bytes(sealed.payload[::-1])
    with pytest.raises(custody.CustodyRefused, match="artifact_digest"):
        read(sealed)
    assert events(sealed)[-1]["code"] == "artifact_digest"


def test_stale_after_read_withholds_bytes(sealed, monkeypatch):
    original = custody.OutputGuard.read

    def stale(out, name):
        data = original(out, name)
        if name.endswith(".sealed"):
            sealed.dispatched.record["status"] = "done"
            sealed.dispatched.save()
        return data

    monkeypatch.setattr(custody.OutputGuard, "read", stale)
    with pytest.raises(custody.CustodyRefused, match="designation_stale"):
        read(sealed)
    assert events(sealed)[-1]["code"] == "designation_stale"


@pytest.mark.parametrize("failure", ["attempt", "completed"])
def test_log_failure_never_releases_bytes_and_reconciles(sealed, monkeypatch, failure):
    original = custody.OutputGuard.append
    original_read = custody.OutputGuard.read
    opened = []

    def fail(out, name, line):
        if name == custody.LOG and json.loads(line)["event"] in {failure, "interrupted"}:
            raise BuildError("output_io")
        return original(out, name, line)

    def spy(out, name):
        if name.endswith(".sealed"):
            opened.append(name)
        return original_read(out, name)

    with monkeypatch.context() as m:
        m.setattr(custody.OutputGuard, "append", fail)
        m.setattr(custody.OutputGuard, "read", spy)
        with pytest.raises(custody.CustodyRefused, match="access_log_unavailable"):
            read(sealed)
    assert len(opened) == (0 if failure == "attempt" else 1)
    assert read(sealed, "custody_verify") is True
    assert [e["event"] for e in events(sealed)] == (
        ["genesis", "sealed", "attempt", "completed"]
        if failure == "attempt"
        else ["genesis", "sealed", "attempt", "interrupted", "attempt", "completed"]
    )


def test_interruption_records_terminal_and_propagates(sealed, monkeypatch):
    original = custody.OutputGuard.read

    def interrupt(out, name):
        if name.endswith(".sealed"):
            raise KeyboardInterrupt
        return original(out, name)

    monkeypatch.setattr(custody.OutputGuard, "read", interrupt)
    with pytest.raises(KeyboardInterrupt):
        read(sealed)
    assert events(sealed)[-1]["event"] == "interrupted"


def test_orphan_attempt_reconciled_before_next_attempt(sealed):
    with custody.OutputGuard(sealed.root) as out:
        chain = custody._chain(out)
        custody._append(
            out,
            chain,
            "attempt",
            attempt_id="a" * 32,
            **custody._identity(),
            ref=custody.asdict(sealed.ref),
            purpose="final_evaluation",
        )
    assert read(sealed, "custody_verify") is True
    tail = events(sealed)[-3:]
    assert [e["event"] for e in tail] == ["interrupted", "attempt", "completed"]
    assert tail[0]["attempt_id"] == "a" * 32
    assert tail[0]["reconciled_by"] == tail[1]["attempt_id"]


@pytest.mark.parametrize("kind", ["tamper", "truncated", "json", "extra", "cyrillic", "ref", "seq", "terminal"])
def test_corrupt_chain_refuses_without_open(sealed, monkeypatch, kind):
    chain = events(sealed)
    if kind == "tamper":
        chain[1]["prev_sha256"] = "0" * 64
    elif kind == "extra":
        chain[0]["private_path"] = "/SYNTHETIC"
    elif kind == "cyrillic":
        chain[0]["custody_id"] = "АБВ"
    elif kind == "ref":
        chain[1]["ref"]["component"] = "bad"
    elif kind == "seq":
        chain[0]["seq"] = False
    elif kind == "terminal":
        chain[1] = {
            **chain[0],
            "seq": 1,
            "prev_sha256": custody.digest(custody.canonical(chain[0])),
            "event": "completed",
            "attempt_id": "b" * 32,
        }
        del chain[1]["custody_id"]
    raw = b"{" if kind == "json" else b"".join(custody.canonical(e) + b"\n" for e in chain)
    (sealed.root / custody.LOG).write_bytes(raw[:-1] if kind == "truncated" else raw)
    original = custody.OutputGuard.read
    monkeypatch.setattr(
        custody.OutputGuard,
        "read",
        lambda out, name: original(out, name) if name == custody.LOG else pytest.fail("artifact opened"),
    )
    with pytest.raises(custody.CustodyRefused, match="access_log_corrupt"):
        read(sealed)


def test_invalid_claim_does_not_leak_into_log(sealed, monkeypatch):
    monkeypatch.setenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", "АБВ /private/ membership")
    monkeypatch.setenv("LU_RUNTIME_RUN_NONCE", "АБВ /private/ membership")
    with pytest.raises(custody.CustodyRefused, match="not_steward_family"):
        read(sealed)
    assert events(sealed)[-2]["task_id"] == "unknown"
    assert (sealed.root / custody.LOG).read_bytes().isascii()
    assert b"/private/" not in (sealed.root / custody.LOG).read_bytes()


def test_concurrent_readers_serialize_attempt_and_terminal(sealed):
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert list(pool.map(lambda _: read(sealed, "custody_verify"), range(4))) == [True] * 4
    assert [e["event"] for e in events(sealed)[2:]] == ["attempt", "completed"] * 4


def test_missing_log_and_unsafe_root_fail_closed(sealed, tmp_path):
    (sealed.root / custody.LOG).unlink()
    with pytest.raises(custody.CustodyRefused, match="access_log_unavailable"):
        read(sealed)
    link = tmp_path / "SYNTHETIC-root-link"
    link.symlink_to(sealed.root, target_is_directory=True)
    with pytest.raises(custody.CustodyRefused, match="access_log_unavailable"):
        custody.read_sealed(sealed.ref, "final_evaluation", custody_root=link)


def test_lock_unavailable_and_busy(sealed, monkeypatch):
    original = custody.os.open
    with monkeypatch.context() as m:
        m.setattr(
            custody.os,
            "open",
            lambda name, *a, **kw: (
                (_ for _ in ()).throw(PermissionError()) if name == custody.LOCK else original(name, *a, **kw)
            ),
        )
        with pytest.raises(custody.CustodyRefused, match="access_log_unavailable"):
            read(sealed)
    with monkeypatch.context() as m:
        m.setattr(custody.fcntl, "flock", lambda *a: (_ for _ in ()).throw(BlockingIOError()))
        m.setattr(custody, "LOCK_TIMEOUT", 0)
        with pytest.raises(custody.CustodyRefused, match="custody_busy"):
            read(sealed)
    assert [e["event"] for e in events(sealed)] == ["genesis", "sealed"]


def test_seal_refuses_reseal_and_wrong_payload(sealed):
    with pytest.raises(custody.CustodyRefused, match="already_sealed"):
        custody.seal(sealed.ref, b"SYNTHETIC changed", custody_root=sealed.root)
    with pytest.raises(custody.CustodyRefused, match="payload_type"):
        custody.seal(sealed.ref, "SYNTHETIC", custody_root=sealed.root)


def test_seal_orphan_artifact_and_io_failure(sealed, monkeypatch):
    ref = custody.ArtifactRef("C2", "final", "synthetic-v1")
    artifact = sealed.root / custody._artifact_name(ref)
    artifact.write_bytes(b"SYNTHETIC orphan")
    artifact.chmod(0o600)
    with pytest.raises(custody.CustodyRefused, match="artifact_exists"):
        custody.seal(ref, b"SYNTHETIC", custody_root=sealed.root)
    with monkeypatch.context() as m:
        m.setattr(custody.OutputGuard, "append", lambda *a: (_ for _ in ()).throw(BuildError("output_io")))
        with pytest.raises(custody.CustodyRefused, match="access_log_unavailable"):
            custody.seal(ref, b"SYNTHETIC", custody_root=sealed.root)


def test_manifest_reads_only_remote_main_blob(sealed, monkeypatch):
    calls = []

    def git(args, **kwargs):
        calls.append((args, kwargs))
        return SimpleNamespace(returncode=0, stdout=custody.canonical(sealed.manifest))

    monkeypatch.setattr(custody, "run_git", git)
    assert read(sealed, "custody_verify") is True
    assert calls[0][0] == ["cat-file", "blob", "refs/remotes/origin/main:" + custody.MANIFEST_PATH]
    assert calls[0][1]["cwd"] == custody.REPOSITORY


def test_actual_git_blob_ignores_worktree_and_unmerged_manifest(sealed, tmp_path, monkeypatch):
    import subprocess

    from scripts.orchestration.execution_safe_git import run_git

    repo = tmp_path / "SYNTHETIC-repo"
    repo.mkdir()

    def git(*args):
        return subprocess.run(
            [
                "git",
                "-c",
                "core.hooksPath=/dev/null",
                "-c",
                "commit.gpgSign=false",
                "-c",
                "user.name=Synthetic",
                "-c",
                "user.email=synthetic@example.invalid",
                *args,
            ],
            cwd=repo,
            check=True,
            capture_output=True,
            timeout=30,
        )

    git("init", "-b", "synthetic")
    manifest = repo / custody.MANIFEST_PATH
    manifest.parent.mkdir(parents=True)
    manifest.write_bytes(custody.canonical(sealed.manifest))
    git("add", custody.MANIFEST_PATH)
    git("commit", "-m", "Synthetic manifest fixture")
    monkeypatch.setattr(custody, "REPOSITORY", repo)
    monkeypatch.setattr(custody, "run_git", run_git)
    with pytest.raises(custody.CustodyRefused, match="manifest_unmerged"):
        read(sealed)
    git("update-ref", "refs/remotes/origin/main", "HEAD")
    manifest.write_bytes(b"SYNTHETIC worktree edit is not a manifest")
    assert read(sealed, "custody_verify") is True
    assert [e["event"] for e in events(sealed)[-4:]] == ["attempt", "refused", "attempt", "completed"]


def test_seal_artifact_io_failure_is_closed(sealed, monkeypatch):
    ref = custody.ArtifactRef("C2", "final", "synthetic-v1")
    original = custody.OutputGuard.append

    def fail(out, name, line):
        if name.endswith(".sealed"):
            raise BuildError("output_io")
        return original(out, name, line)

    monkeypatch.setattr(custody.OutputGuard, "append", fail)
    with pytest.raises(custody.CustodyRefused, match="artifact_open"):
        custody.seal(ref, b"SYNTHETIC", custody_root=sealed.root)
