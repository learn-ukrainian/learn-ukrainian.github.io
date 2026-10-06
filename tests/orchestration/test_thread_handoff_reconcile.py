"""Differing-tie reconciliation: real redirect objects and outside sentinels (#9789)."""

from __future__ import annotations

import ast
import errno
import inspect
import json
import os
from types import SimpleNamespace

import pytest

from scripts.hooks import session_start_gate as gate
from scripts.orchestration import thread_handoff as th
from tests.test_rollover_bundles import AGENT, HANDOFF_PATH, STREAM, _import_args, _seed_state


@pytest.fixture
def tied_bundle(tmp_path, monkeypatch):
    monkeypatch.setattr(th, "_bundle_handoff_candidates", lambda _root, _stream: (HANDOFF_PATH,))
    root = tmp_path / "repo"
    root.mkdir()
    state = _seed_state(root, thread_id="reconcile-source")
    lineage = root / th.default_state_path(AGENT, state["lineage_id"])
    lineage = lineage.parent
    receipt = lineage.parent / "_bundle-receipts" / f"{state['lineage_id']}.json"
    th.write_json_atomic(receipt, {"upload_seq": 7})
    manifest, _, _ = th._build_rollover_bundle(root, root, agent=AGENT, state=state, stream_id=STREAM)
    manifest["upload_seq"] = 7
    members = th._bundle_source_members(root, root, agent=AGENT, state=state, stream_id=STREAM)
    members[HANDOFF_PATH] = b"remote handoff bytes\n{{REPO_ROOT}}\n"
    manifest["files"] = [
        {
            "path": name,
            "sha256": th.hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload),
            "tokenized": th._bundle_text_member(name),
        }
        for name, payload in sorted(members.items())
    ]
    manifest["tokenized_members"] = [name for name in sorted(members) if th._bundle_text_member(name)]
    manifest["bundle_sha256"] = th._bundle_digest(members, manifest)
    blob = th._bundle_archive(members, manifest)
    bundle = tmp_path / "remote.tgz"
    bundle.write_bytes(blob)
    upload = lineage / "_bundle-reconcile" / f"upload-7-{manifest['bundle_sha256']}"
    return SimpleNamespace(
        root=root,
        lineage=lineage,
        manifest=manifest,
        members=members,
        blob=blob,
        bundle=bundle,
        upload=upload,
        receipt=receipt,
    )


def _snapshot(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}


@pytest.mark.parametrize("force", [False, True])
def test_differing_tie_keeps_local_preserves_exact_remote_and_warns(tied_bundle, monkeypatch, capsys, force):
    b = tied_bundle
    before = _snapshot(b.root)

    def unexpected_install(*_args, **_kwargs):
        pytest.fail("a differing positive-sequence tie reached the normal installer")

    monkeypatch.setattr(th, "_bundle_stage_install", unexpected_install)
    monkeypatch.setattr(th, "_bundle_commit_install", unexpected_install)
    assert th.cmd_import_bundle(_import_args(b.root, b.bundle, force=force)) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "warning"
    assert output["preserved_copy"] == (b.upload / "remote.bundle.tgz").relative_to(b.root).as_posix()
    assert (b.root / output["preserved_copy"]).read_bytes() == b.blob
    for name, payload in b.members.items():
        assert (b.upload / "members" / name).read_bytes() == payload
    assert json.loads((b.upload / "manifest.json").read_bytes()) == b.manifest
    after = _snapshot(b.root)
    assert {name: after[name] for name in before} == before
    assert all(
        name.startswith(b.lineage.relative_to(b.root).as_posix() + "/_bundle-reconcile/")
        for name in after.keys() - before.keys()
    )
    assert not list(b.root.rglob(".reconcile-*.tmp"))

    # Repeated imports reuse the same immutable copy; reconciliation never enters export members.
    assert th.cmd_import_bundle(_import_args(b.root, b.bundle)) == 0
    capsys.readouterr()
    assert _snapshot(b.root) == after
    local = th._bundle_local_members(b.root, b.root, agent=AGENT, lineage_id=b.manifest["lineage_id"], stream_id=STREAM)
    assert not any("_bundle-reconcile" in name for name in local)

    monkeypatch.setattr(gate, "_import_thread_handoff", lambda: th)
    monkeypatch.setattr(th, "_bundle_api_list", lambda *_a, **_kw: [{"manifest": b.manifest, "upload_seq": 7}])
    monkeypatch.setattr(th, "_bundle_api_by_seq", lambda *_a, **_kw: (b.manifest, b.blob))
    warning = gate.phase_rollover_import(
        SimpleNamespace(import_bundle=True, repo_root=str(b.root), agent=AGENT, stream=STREAM)
    )
    assert warning["status"] == "issue"
    assert warning["warning"].count("WARNING:") == 1
    assert output["preserved_copy"] in warning["warning"]
    assert "kept local" in warning["warning"]
    assert str(b.root) not in warning["warning"]


@pytest.mark.parametrize(
    "component,code",
    [
        ("reconcile", "reconcile_dir_symlink"),
        ("upload", "upload_dir_symlink"),
        ("member", "member_dir_symlink"),
        (".agent", "lineage_ancestor_symlink"),
        ("thread-rollovers", "lineage_ancestor_symlink"),
        ("agent", "lineage_ancestor_symlink"),
        ("lineage", "lineage_ancestor_symlink"),
    ],
)
def test_symlink_redirect_refused_without_outside_write(tied_bundle, tmp_path, capsys, component, code):
    b = tied_bundle
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "sentinel").write_bytes(b"untouched outside")
    paths = {
        "reconcile": b.upload.parent,
        "upload": b.upload,
        "member": b.upload / "members" / ".claude",
        ".agent": b.root / ".agent",
        "thread-rollovers": b.root / ".agent/thread-rollovers",
        "agent": b.lineage.parent,
        "lineage": b.lineage,
    }
    target = paths[component]
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        target.rename(outside / "original")
        target.symlink_to(outside / "original", target_is_directory=True)
    else:
        target.symlink_to(outside, target_is_directory=True)
    before = _snapshot(outside)
    assert th.cmd_import_bundle(_import_args(b.root, b.bundle)) == 2
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "refused"
    assert output["code"] == code
    assert _snapshot(outside) == before


@pytest.mark.parametrize(
    "kind,code",
    [
        ("hardlink", "reconcile_temp_hardlink"),
        ("existing", "reconcile_temp_exists"),
        ("fifo", "reconcile_fifo"),
    ],
)
def test_exclusive_temporary_refuses_existing_objects(tied_bundle, tmp_path, monkeypatch, capsys, kind, code):
    b = tied_bundle
    outside = tmp_path / "sentinel"
    outside.write_bytes(b"untouched outside")
    b.upload.mkdir(parents=True)
    temporary = b.upload / ".reconcile-fixed.tmp"
    if kind == "hardlink":
        os.link(outside, temporary)
    elif kind == "fifo":
        os.mkfifo(temporary)
    else:
        temporary.write_bytes(b"pre-existing local")
    monkeypatch.setattr(th.uuid, "uuid4", lambda: SimpleNamespace(hex="fixed"))
    assert th.cmd_import_bundle(_import_args(b.root, b.bundle)) == 2
    output = json.loads(capsys.readouterr().out)
    assert output["code"] == code
    assert outside.read_bytes() == b"untouched outside"
    assert temporary.exists()
    if kind != "fifo":
        assert temporary.read_bytes() == (b"untouched outside" if kind == "hardlink" else b"pre-existing local")


@pytest.mark.parametrize(
    "kind,code",
    [
        ("symlink", "reconcile_member_symlink"),
        ("hardlink", "reconcile_member_hardlink"),
        ("fifo", "reconcile_fifo"),
        ("different", "reconcile_member_differs"),
    ],
)
def test_member_leaf_is_never_overwritten(tied_bundle, tmp_path, capsys, kind, code):
    b = tied_bundle
    outside = tmp_path / "sentinel"
    outside.write_bytes(b"untouched outside")
    b.upload.mkdir(parents=True)
    leaf = b.upload / "manifest.json"
    if kind == "symlink":
        leaf.symlink_to(outside)
    elif kind == "hardlink":
        os.link(outside, leaf)
    elif kind == "fifo":
        os.mkfifo(leaf)
    else:
        leaf.write_bytes(b"different")
    assert th.cmd_import_bundle(_import_args(b.root, b.bundle)) == 2
    assert json.loads(capsys.readouterr().out)["code"] == code
    assert outside.read_bytes() == b"untouched outside"


def test_sequence_zero_differing_tie_still_refuses(tied_bundle, capsys):
    b = tied_bundle
    b.manifest["upload_seq"] = 0
    b.manifest["bundle_sha256"] = th._bundle_digest(b.members, b.manifest)
    b.bundle.write_bytes(th._bundle_archive(b.members, b.manifest))
    th.write_json_atomic(b.receipt, {"upload_seq": 0})
    assert th.cmd_import_bundle(_import_args(b.root, b.bundle)) == 2
    assert "refusing to choose" in json.loads(capsys.readouterr().out)["error"]
    assert not b.upload.parent.exists()
    b.manifest["upload_seq"] = 7
    b.manifest["bundle_sha256"] = th._bundle_digest(b.members, b.manifest)
    b.bundle.write_bytes(th._bundle_archive(b.members, b.manifest))
    th.write_json_atomic(b.receipt, {"upload_seq": 7})
    assert th.cmd_import_bundle(_import_args(b.root, b.bundle)) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "warning"


def test_reconcile_writes_have_one_descriptor_primitive():
    """Guard against introducing a path-string writer in the reconciliation branch."""
    tree = ast.parse(inspect.getsource(th._BundleReconcileTree))
    preserve = ast.parse(inspect.getsource(th._bundle_preserve_tie))
    forbidden = {
        "write_bytes",
        "write_text",
        "write_bytes_atomic",
        "write_json_atomic",
        "mkdir",
        "replace",
        "rename",
        "mkdtemp",
        "NamedTemporaryFile",
        "copytree",
        "rmtree",
    }
    for node in ast.walk(preserve):
        if isinstance(node, ast.Call):
            name = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
            assert name not in forbidden | {"open", "fdopen"}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            assert node.func.id not in forbidden | {"open"}
        elif isinstance(node.func, ast.Attribute):
            assert node.func.attr not in forbidden - {"mkdir"}
            if node.func.attr in {"mkdir", "stat", "unlink", "link"}:
                assert any(kw.arg in {"dir_fd", "src_dir_fd"} for kw in node.keywords)
            if node.func.attr == "open":
                assert isinstance(node.func.value, ast.Name) and node.func.value.id == "os"
                # Only the trusted repository anchor may be opened without dir_fd.
                assert any(kw.arg == "dir_fd" for kw in node.keywords) or (
                    isinstance(node.args[0], ast.Attribute) and node.args[0].attr == "state_root"
                )
                flags = ast.unparse(node.args[1])
                assert "O_NOFOLLOW" in flags
                if "O_WRONLY" in flags:
                    assert "O_EXCL" in flags and "O_CREAT" in flags and "O_TRUNC" not in flags


def test_many_members_keep_directory_descriptors_bounded(tied_bundle, monkeypatch, capsys):
    b = tied_bundle
    for index in range(80):
        b.members[f".agent/thread-rollovers/{AGENT}/{b.manifest['lineage_id']}/many/{index}.txt"] = b"member\n"
    b.manifest["files"] = [
        {
            "path": name,
            "sha256": th.hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload),
            "tokenized": th._bundle_text_member(name),
        }
        for name, payload in sorted(b.members.items())
    ]
    b.manifest["tokenized_members"] = [name for name in sorted(b.members) if th._bundle_text_member(name)]
    b.manifest["bundle_sha256"] = th._bundle_digest(b.members, b.manifest)
    b.bundle.write_bytes(th._bundle_archive(b.members, b.manifest))
    native_open, native_close = os.open, os.close
    held = set()
    peak = 0

    def bounded_open(path, flags, *args, **kwargs):
        nonlocal peak
        if flags & os.O_DIRECTORY and len(held) >= 32:
            raise OSError(errno.EMFILE, "directory descriptor budget exhausted")
        fd = native_open(path, flags, *args, **kwargs)
        if flags & os.O_DIRECTORY:
            held.add(fd)
            peak = max(peak, len(held))
        return fd

    def tracked_close(fd):
        held.discard(fd)
        return native_close(fd)

    monkeypatch.setattr(os, "open", bounded_open)
    monkeypatch.setattr(os, "close", tracked_close)
    assert th.cmd_import_bundle(_import_args(b.root, b.bundle)) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "warning"
    assert peak < 32
    assert not held
