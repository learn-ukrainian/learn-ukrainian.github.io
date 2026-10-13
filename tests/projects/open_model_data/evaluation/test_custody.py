import json
import os
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest
import yaml

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
    if case.startswith("manifest-") or case in {"genesis", "issuer-prefix"}:
        sealed.history.manifest(sealed.manifest)
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
    original = custody.run_git

    def git(args, **kwargs):
        calls.append((args, kwargs))
        return original(args, **kwargs)

    monkeypatch.setattr(custody, "run_git", git)
    assert read(sealed, "custody_verify") is True
    assert calls[0][0] == ["rev-parse", "--verify", "refs/remotes/origin/main^{commit}"]
    sha = sealed.history.git("rev-parse", "HEAD").stdout.decode().strip()
    assert calls[1][0] == ["cat-file", "blob", sha + ":" + custody.MANIFEST_PATH]
    assert calls[0][1]["cwd"] == custody.REPOSITORY


def test_actual_git_blob_ignores_worktree_and_unmerged_manifest(sealed, tmp_path, monkeypatch):
    repo = sealed.history.repo
    git = sealed.history.git
    manifest = repo / custody.MANIFEST_PATH
    git("update-ref", "-d", "refs/remotes/origin/main")
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


def bind_synthetic_chain(sealed, chain):
    """Tamper only disposable evidence, including its committed event pin."""
    for index, entry in enumerate(chain):
        entry["seq"] = index
        entry["prev_sha256"] = custody.digest(custody.canonical(chain[index - 1])) if index else "0" * 64
    (sealed.root / custody.LOG).write_bytes(b"".join(custody.canonical(e) + b"\n" for e in chain))
    sealed.entry["sealed_event_sha256"] = custody.digest(custody.canonical(chain[1]))
    sealed.history.manifest(sealed.manifest)


def assert_preopen_refusal(sealed, monkeypatch, code):
    original = custody.OutputGuard.read

    def spy(out, name):
        assert not name.endswith(".sealed"), "prohibited artifact open"
        return original(out, name)

    monkeypatch.setattr(custody.OutputGuard, "read", spy)
    with pytest.raises(custody.CustodyRefused, match=f"^{code}$"):
        read(sealed)
    if code != "access_log_corrupt":
        assert [(e["event"], e.get("code")) for e in events(sealed)[-2:]] == [("attempt", None), ("refused", code)]


@pytest.mark.parametrize("lifecycle", ["active", "hold", "retired", "removed"])
@pytest.mark.parametrize("purpose", ["custody_verify", "final_evaluation"])
def test_historical_issuer_survives_rotation_and_retirement(sealed, lifecycle, purpose):
    before = events(sealed)[:2]
    artifact = sealed.root / custody._artifact_name(sealed.ref)
    data = yaml.safe_load(sealed.history.catalog_path.read_bytes())
    data["seats"]["openai_frontier"]["model_id"] = "SYNTHETIC-model-b"
    if lifecycle == "removed":
        del data["models"]["SYNTHETIC-model-a"]
    else:
        data["models"]["SYNTHETIC-model-a"]["lifecycle"] = lifecycle
        if lifecycle == "retired":
            data["models"]["SYNTHETIC-model-a"]["transports"] = []
            data["models"]["SYNTHETIC-model-a"].pop("routing_wire_ids")
    sealed.history.catalog(data)
    assert (
        yaml.safe_load(sealed.history.catalog_path.read_bytes())["seats"]["openai_frontier"]["model_id"]
        == "SYNTHETIC-model-b"
    )
    assert (
        yaml.safe_load(sealed.history.catalog_path.read_text())["seats"]["openai_frontier"]["model_id"]
        == "SYNTHETIC-model-b"
    )
    assert custody.load_model_catalog()["seats"]["openai_frontier"]["model_id"] == "SYNTHETIC-model-b"
    sealed.dispatched.record["model"] = "SYNTHETIC-model-b"
    sealed.dispatched.save()
    result = read(sealed, purpose)
    assert result is True if purpose == "custody_verify" else result.data() == sealed.payload
    assert artifact.read_bytes() == sealed.payload
    assert events(sealed)[:2] == before
    assert events(sealed)[-1]["event"] == "completed"
    assert custody.load_model_catalog()["seats"]["openai_frontier"]["model_id"] == "SYNTHETIC-model-b"


@pytest.mark.parametrize(
    "case,code",
    [
        ("legacy", "issuer_admission_missing"),
        ("legacy-event", "issuer_admission_invalid"),
        ("legacy-manifest", "issuer_admission_invalid"),
        ("event-pin", "issuer_admission_invalid"),
        ("witness-missing", "issuer_admission_unavailable"),
        ("witness-digest", "issuer_admission_invalid"),
        ("witness-model", "model_not_admitted"),
        ("event-task", "issuer_invalid"),
        ("event-run", "issuer_invalid"),
        ("event-artifact", "issuer_invalid"),
        ("event-length", "issuer_invalid"),
        ("duplicate-seal", "issuer_invalid"),
        ("manifest-pin-type", "manifest_invalid"),
        ("manifest-extra", "manifest_invalid"),
    ],
)
def test_immutable_admission_and_event_controls(sealed, monkeypatch, case, code):
    chain = events(sealed)
    event = chain[1]
    if case in {"legacy", "legacy-event"}:
        del event["issuer_admission"]
    if case in {"legacy", "legacy-manifest"}:
        sealed.entry.pop("sealed_event_sha256")
    elif case == "witness-missing":
        event["issuer_admission"]["catalog_commit"] = "e" * 40
    elif case == "witness-digest":
        event["issuer_admission"]["catalog_sha256"] = "0" * 64
    elif case == "witness-model":
        event["issuer_admission"]["model"] = "SYNTHETIC-model-b"
    elif case.startswith("event-") and case != "event-pin":
        key = {
            "event-task": "task_id",
            "event-run": "run_nonce_sha256",
            "event-artifact": "sha256",
            "event-length": "bytes",
        }[case]
        event[key] = 1 if key == "bytes" else "eval-steward-6321-wrong" if key == "task_id" else "0" * 64
    elif case == "duplicate-seal":
        chain.append(dict(event))
    bind_synthetic_chain(sealed, chain)
    if case in {"legacy", "legacy-manifest"}:
        del sealed.entry["sealed_event_sha256"]
    elif case == "event-pin":
        sealed.entry["sealed_event_sha256"] = "0" * 64
    elif case == "manifest-pin-type":
        sealed.entry["sealed_event_sha256"] = True
    elif case == "manifest-extra":
        sealed.entry["extra"] = "SYNTHETIC"
    sealed.history.manifest(sealed.manifest)
    assert_preopen_refusal(sealed, monkeypatch, code)


@pytest.mark.parametrize(
    "case,code",
    [
        ("non-frontier", "model_not_admitted"),
        ("retired", "model_not_admitted"),
        ("off-main", "issuer_admission_invalid"),
        ("substitution", "issuer_admission_invalid"),
        ("schema", "issuer_admission_invalid"),
        ("aliases", "issuer_admission_invalid"),
        ("yaml", "issuer_admission_invalid"),
        ("projection-only", None),
    ],
)
def test_historical_catalog_ancestry_and_projection(sealed, monkeypatch, case, code):
    current_raw = sealed.history.catalog_path.read_bytes()
    data = yaml.safe_load(current_raw)
    original_main = sealed.history.git("rev-parse", "HEAD").stdout.decode().strip()
    if case == "non-frontier":
        data["seats"]["openai_frontier"]["model_id"] = "SYNTHETIC-model-b"
    elif case == "retired":
        data["models"]["SYNTHETIC-model-a"]["lifecycle"] = "retired"
    elif case == "schema":
        data["schema_version"] = "unknown"
    elif case == "aliases":
        data["models"]["SYNTHETIC-model-a"]["aliases"] = [None]
    elif case == "projection-only":
        data = {k: data[k] for k in ("schema_version", "seats", "models")}
    if case == "yaml":
        sealed.history.catalog_path.write_bytes(b"[invalid YAML")
        witness = sealed.history.commit()
    else:
        witness = sealed.history.catalog(data)
    raw = sealed.history.catalog_path.read_bytes()
    if case == "off-main":
        sealed.history.git("checkout", "--detach", original_main)
    sealed.history.catalog_path.write_bytes(current_raw)
    chain = events(sealed)
    chain[1]["issuer_admission"].update(catalog_commit=witness, catalog_sha256=custody.digest(raw))
    if case == "substitution":
        chain[1]["issuer_admission"]["catalog_sha256"] = custody.digest(b"SYNTHETIC substitute")
    bind_synthetic_chain(sealed, chain)
    if code:
        assert_preopen_refusal(sealed, monkeypatch, code)
    else:
        assert read(sealed).data() == sealed.payload


@pytest.mark.parametrize("case", ["missing", "extra", "type", "schema", "model", "commit", "digest"])
def test_admission_shape_is_closed(sealed, monkeypatch, case):
    chain = events(sealed)
    admission = chain[1]["issuer_admission"]
    if case == "missing":
        del admission["catalog_commit"]
    elif case == "extra":
        admission["extra"] = "SYNTHETIC"
    elif case == "type":
        chain[1]["issuer_admission"] = []
    else:
        key = {"schema": "schema", "model": "model", "commit": "catalog_commit", "digest": "catalog_sha256"}[case]
        admission[key] = "SYNTHETIC/bad" if case == "model" else None
    bind_synthetic_chain(sealed, chain)
    assert_preopen_refusal(sealed, monkeypatch, "access_log_corrupt")


@pytest.mark.parametrize(
    "case", ["duplicate-private", "duplicate-ascii", "spacing", "order", "escaping", "crlf", "bom", "blank", "partial"]
)
def test_noncanonical_raw_bytes_refuse_before_append(sealed, monkeypatch, case):
    raw = (sealed.root / custody.LOG).read_bytes()
    first, rest = raw.split(b"\n", 1)
    if case.startswith("duplicate"):
        injected = (
            b'"custody_id":"'
            + ("АБВ /SYNTHETIC/private/".encode() if case == "duplicate-private" else b"discarded")
            + b'",'
        )
        first = b"{" + injected + first[1:]
    elif case == "spacing":
        first = first.replace(b":", b": ")
    elif case == "order":
        first = json.dumps(dict(reversed(list(json.loads(first).items()))), separators=(",", ":")).encode()
    elif case == "escaping":
        first = first.replace(b"genesis", b"gen\\u0065sis")
    elif case == "crlf":
        first += b"\r"
    elif case == "bom":
        first = b"\xef\xbb\xbf" + first
    elif case == "blank":
        first = b""
    corrupt = first + b"\n" + rest
    if case == "partial":
        corrupt = corrupt[:-1]
    (sealed.root / custody.LOG).write_bytes(corrupt)
    assert_preopen_refusal(sealed, monkeypatch, "access_log_corrupt")
    assert (sealed.root / custody.LOG).read_bytes() == corrupt


@pytest.mark.parametrize("when", ["initial", "before-write", "after-write"])
def test_catalog_drift_never_seals(dispatched, tmp_path, monkeypatch, when):
    from scripts.projects.open_model_data.review_build import output

    monkeypatch.setattr(output, "filesystem", lambda p: "ext4")
    root = tmp_path / "SYNTHETIC-drift"
    ref = custody.ArtifactRef("C1", "final", "synthetic-v1")
    path = dispatched.history.catalog_path

    def drift():
        path.write_bytes(path.read_bytes() + b"\n# SYNTHETIC drift\n")

    if when == "initial":
        drift()
    elif when == "before-write":
        original = custody.recheck

        def recheck(designation):
            original(designation)
            drift()

        monkeypatch.setattr(custody, "recheck", recheck)
    else:
        original = custody.OutputGuard.append

        def append(out, name, value):
            original(out, name, value)
            if name.endswith(".sealed"):
                drift()

        monkeypatch.setattr(custody.OutputGuard, "append", append)
    with pytest.raises(custody.CustodyRefused, match=r"^issuer_admission_invalid$"):
        custody.seal(ref, b"SYNTHETIC", custody_root=root)
    artifact = root / custody._artifact_name(ref)
    assert artifact.exists() == (when == "after-write")
    if root.exists():
        assert not any(e["event"] == "sealed" for e in events(SimpleNamespace(root=root)))
    if when == "after-write":
        path.write_bytes(dispatched.history.git("show", "HEAD:" + custody.CATALOG_BLOB).stdout)
        with pytest.raises(custody.CustodyRefused, match=r"^artifact_exists$"):
            custody.seal(ref, b"SYNTHETIC", custody_root=root)


@pytest.mark.parametrize(
    "case,code",
    [
        ("main-missing", "issuer_admission_unavailable"),
        ("blob-missing", "issuer_admission_unavailable"),
        ("git-io", "issuer_admission_unavailable"),
        ("catalog-invalid", "issuer_admission_invalid"),
        ("historical-other-seat", "model_not_admitted"),
        ("local-io", "issuer_admission_unavailable"),
    ],
)
def test_initial_witness_failure_precedes_artifact_access(dispatched, tmp_path, monkeypatch, case, code):
    from pathlib import Path

    original = custody.run_git
    catalog = yaml.safe_load(dispatched.history.catalog_path.read_bytes())
    catalog["seats"]["openai_frontier"]["model_id"] = "SYNTHETIC-model-b"

    def git(args, **kwargs):
        if case == "git-io":
            raise PermissionError("SYNTHETIC")
        if args[0] == "rev-parse" and case == "main-missing":
            return SimpleNamespace(returncode=1, stdout=b"")
        if args[0] == "cat-file":
            if case == "blob-missing":
                return SimpleNamespace(returncode=1, stdout=b"")
            if case == "catalog-invalid":
                return SimpleNamespace(returncode=0, stdout=b"[invalid YAML")
            if case == "historical-other-seat":
                return SimpleNamespace(returncode=0, stdout=yaml.safe_dump(catalog).encode())
        return original(args, **kwargs)

    monkeypatch.setattr(custody, "run_git", git)
    if case == "local-io":
        original_read = Path.read_bytes

        def read_bytes(path):
            if path == dispatched.history.catalog_path:
                raise PermissionError("SYNTHETIC")
            return original_read(path)

        monkeypatch.setattr(Path, "read_bytes", read_bytes)
    root = tmp_path / "SYNTHETIC-initial-refusal"
    with pytest.raises(custody.CustodyRefused, match=f"^{code}$"):
        custody.seal(custody.ArtifactRef("C1", "final", "synthetic-v1"), b"SYNTHETIC", custody_root=root)
    assert not root.exists()


@pytest.mark.parametrize("case", ["missing-blob", "git-io"])
def test_unavailable_historical_witness_refuses_without_open(sealed, monkeypatch, case):
    if case == "missing-blob":
        original_raw = sealed.history.catalog_path.read_bytes()
        sealed.history.catalog_path.unlink()
        witness = sealed.history.commit()
        sealed.history.catalog_path.write_bytes(original_raw)
        chain = events(sealed)
        chain[1]["issuer_admission"]["catalog_commit"] = witness
        bind_synthetic_chain(sealed, chain)
    else:
        original = custody.run_git

        def git(args, **kwargs):
            if args[0] == "merge-base":
                raise PermissionError("SYNTHETIC")
            return original(args, **kwargs)

        monkeypatch.setattr(custody, "run_git", git)
    assert_preopen_refusal(sealed, monkeypatch, "issuer_admission_unavailable")


def test_historical_record_alias_uses_historical_catalog(sealed):
    sealed.issuer["model"] = "codex:SYNTHETIC-model-a[synthetic]"
    sealed.issuer["progress"] = "SYNTHETIC permitted metadata change"
    sealed.issuer_path.write_text(json.dumps(sealed.issuer))
    assert read(sealed, "custody_verify") is True


def test_main_is_pinned_once_despite_ref_movement(sealed, monkeypatch):
    original = custody.run_git
    calls = []

    def git(args, **kwargs):
        result = original(args, **kwargs)
        calls.append(args)
        if args[0] == "rev-parse":
            sealed.history.git("update-ref", "refs/remotes/origin/main", sealed.history.initial)
        return result

    monkeypatch.setattr(custody, "run_git", git)
    assert read(sealed, "custody_verify") is True
    assert sum(args[0] == "rev-parse" for args in calls) == 1
