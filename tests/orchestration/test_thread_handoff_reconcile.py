"""Tie and newer-bundle containment with real redirects and writer mutations (#9891)."""

from __future__ import annotations

import ast
import errno
import inspect
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path
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


# Deliberately explicit: a new call needs inspection, not another forbidden-name
# heuristic. Pure/read-only helpers are named; arbitrary helper calls fail closed.
_BUNDLE_CALLS = {
    "_bundle_archive_local_lineage": {
        "BundleReconcileRefused", "_bundle_json", "archived_state.get", "isinstance", "json.loads",
        "remote_manifest.get", "replacement.get", "tree.exists", "tree.ledger.drop_prefix", "tree.move",
        "tree.read_path", "tree.write_path", "utc_now", "utc_now().strftime",
    },
    "_bundle_stage_install": {
        "ValueError", "_BundleImportLedger", "_BundleReconcileTree", "_bundle_member_path", "_bundle_rewrite",
        "_bundle_text_member", "_bundle_typed_failure", "any", "files.items", "isinstance", "members.items",
        "name.removeprefix", "name.startswith", "normalize_agent_name", "normalize_lineage_id", "str",
        "tree.new_directory", "tree.remove_path", "tree.write_path", "uuid.uuid4",
    },
    "_bundle_preserved_path": {
        "preserved.as_posix", "target.with_name", "tree.exists", "utc_now", "utc_now().strftime",
    },
    "_bundle_commit_install": {
        "'; '.join",
        "(repo_root / superseded).as_posix", "Path", "_BundleReconcileTree", "BundleReconcileRefused",
        "_bundle_archive_local_lineage", "_bundle_handoff_candidates_for_agent", "_bundle_json",
        "_BundleImportLedger", "_bundle_leftover_detail", "_bundle_present_leftovers", "_bundle_preserved_path",
        "_bundle_preserved_path(Path(name), repo).as_posix", "_bundle_typed_failure",
        "archived.relative_to", "archived.relative_to(state_root).as_posix", "created_preserved.append",
        "int", "isinstance", "manifest.get", "normalize_agent_name", "normalize_lineage_id", "preserved.append",
        "repo.ledger.drop", "repo.read_path", "repo.remove_path", "repo.write_path", "repo_backups.items",
        "rollback_errors.append", "set", "sorted", "tree.ledger.drop", "tree.ledger.drop_prefix",
        "source.relative_to", "source.relative_to(state_root).as_posix", "stage_root.relative_to",
        "stage_root.relative_to(state_root).as_posix", "staged_lineage.relative_to",
        "staged_lineage.relative_to(state_root).as_posix", "staged_repo.items", "str", "tree.copy_tree",
        "tree.exists", "tree.move", "tree.read_path", "tree.remove_path", "tree.write_path",
    },
    "_bundle_preserve_tie": {
        "(Path(*tree.parts) / '_bundle-reconcile' / upload / 'remote.bundle.tgz').as_posix",
        "BundleReconcileRefused", "Path", "ValueError", "_BundleReconcileTree", "_bundle_json",
        "_bundle_member_path", "dict", "files.items", "int", "len", "members.items",
        "_BundleImportLedger", "_bundle_typed_failure", "isinstance", "normalize_agent_name",
        "normalize_lineage_id", "path.split", "re.fullmatch",
        "sorted", "str", "tree.directory", "tree.release", "tree.write",
    },
    "_bundle_import_candidate": {
        "_BundleReconcileTree", "_bundle_commit_install", "_bundle_handoff_candidates_for_agent",
        "_BundleImportLedger", "_bundle_capture_baseline", "_bundle_local_lineage_snapshot", "_bundle_order",
        "_bundle_preserve_tie", "_bundle_stage_install", "_bundle_typed_failure",
        "_bundle_validate_lease_member", "archived.relative_to", "isoformat_z", "local_manifest.get",
        "local_members.items", "manifest.get", "members.items", "normalize_agent_name",
        "normalize_lineage_id", "set", "str",
    },
}
# Explicit call sets for the recursively admitted local helpers. Imported
# library helpers remain outside this module-level regression guard.
_BUNDLE_HELPER_CALLS = {
    '_bundle_member_path': {
        'Path', 'ValueError', 'isinstance', 'path.as_posix', 'path.is_absolute',
    },
    'BundleReconcileRefused': {
        'super', 'super().__init__',
    },
    'normalize_lineage_id': {
        'LINEAGE_ID_RE.fullmatch', 'ValueError', 'value.strip', 'value.strip().lower',
    },
    'normalize_agent_name': {
        '(value or DEFAULT_AGENT).strip', '(value or DEFAULT_AGENT).strip().lower', 'AGENT_NAME_RE.fullmatch',
        'ValueError',
    },
    'isoformat_z': {
        'value.astimezone', 'value.astimezone(UTC).isoformat', 'value.astimezone(UTC).isoformat().replace',
    },
    '_bundle_validate_lease_member': {
        'ValueError', 'int', 'isinstance', 'json.loads', 'manifest.get', 'members.get', 'payload.decode',
        'replacement.get', 'state.get', 'str', 'validate_live_lease',
    },
    'validate_live_lease': {
        'LINEAGE_ID_RE.fullmatch', 'active.get', "active['thread_id'].strip", 'display.get',
        'expected_paths.items', 'isinstance', 'lineage_id.startswith', 'native.get',
        'normalize_identity_state', 'normalize_rollover_id', 'normalized_state.get', 're.fullmatch',
        'replacement.get', "replacement['resumed_thread_id'].strip", 'replacement_packet_paths',
        'source_checkout_binding_error', 'state.get', 'str', 'task_family_rollover.transition_identity',
        'task_identity.validate_identity', 'task_identity.validate_title_transition', 'utc_now',
    },
    'utc_now': {
        'datetime.now', 'datetime.now(UTC).replace',
    },
    'source_checkout_binding_error': {
        'binding.get', 'full_head.strip', 'head_advanced.strip', 'isinstance', 'replacement.get', 'set',
    },
    'replacement_packet_paths': {
        "(packet_dir / 'bootstrap.md').as_posix", "(packet_dir / 'canary-pass.json').as_posix",
        "(packet_dir / 'handoff.md').as_posix", "(packet_dir / 'identity-receipt.json').as_posix",
        "(packet_dir / 'semantic-snapshot.json').as_posix", "(packet_dir / 'strict-answers.json').as_posix",
        "(packet_dir / 'strict-probe.json').as_posix", "(packet_dir / 'strict-questions.json').as_posix",
        "(packet_dir / 'strict-verdict.json').as_posix", 'packet_dir.as_posix', 'runtime_dir',
    },
    'runtime_dir': {
        'Path',
    },
    'normalize_rollover_id': {
        'ROLLOVER_ID_RE.fullmatch', 'ValueError', 'value.strip', 'value.strip().lower',
    },
    'normalize_identity_state': {
        'ValueError', '_retire_unsatisfiable_native_plan', 'dict', 'int', 'isoformat_z', 'normalized.get',
        'replacement.setdefault', 'replacement_packet_paths', 'str', 'task_identity.backfill_legacy_identity',
    },
    '_retire_unsatisfiable_native_plan': {
        'dict', 'isinstance', 'isoformat_z', 'native.get', 'replacement.get', 'state.get', 'transition.get',
        'updated_replacement.pop',
    },
    '_bundle_text_member': {
        'Path', 'Path(name).suffix.lower',
    },
    '_bundle_rewrite': {
        'ROLLOVER_BUNDLE_REPO_TOKEN.encode', 'data.replace', 'repo_root.resolve', 'str',
        'str(repo_root.resolve()).encode',
    },
    '_bundle_json': {
        'json.dumps', "json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode",
    },
    '_bundle_order': {
        'ValueError', '_bundle_replacement_status', 'int', 'manifest.get', 'normalize_rollover_id',
        'parse_iso_datetime', 'str',
    },
    'parse_iso_datetime': {
        'datetime.fromisoformat', 'parsed.astimezone', 'parsed.replace', 'str', 'str(value).replace',
    },
    '_bundle_replacement_status': {
        'ValueError', 'replacement.get', 'str',
    },
    '_bundle_local_lineage_snapshot': {
        'ValueError', '_bundle_local_members', '_bundle_state_manifest', 'int', 'lineage_root.exists',
        'lineage_root.is_dir', 'lineage_root.is_symlink', 'load_state', 'receipt.get', 'receipt_path.is_file',
        'validate_live_lease',
    },
    'load_state': {
        'data.get', 'isinstance', 'json.loads', 'path.exists', 'path.read_text', 'type',
    },
    '_bundle_state_manifest': {
        'ValueError', '_bundle_replacement_status', 'int', 'isinstance', 'isoformat_z', 'normalize_agent_name',
        'normalize_lineage_id', 'normalize_rollover_id', 'parse_iso_datetime', 'replacement.get', 'state.get',
        'str', 'utc_now',
    },
    '_bundle_local_members': {
        '_bundle_source_members', 'load_state',
    },
    '_bundle_source_members': {
        "(Path('.agent') / 'thread-rollovers' / agent / lineage_id / path.relative_to(lineage_root)).as_posix",
        'Path', 'ValueError', '_bundle_handoff_candidates_for_agent', '_bundle_member_path',
        '_bundle_text_member', '_bundle_tokenize', 'lineage_root.is_dir', 'lineage_root.rglob',
        'normalize_lineage_id', 'path.is_file', 'path.is_symlink', 'path.name.endswith', 'path.read_bytes',
        'path.relative_to', 'sorted', 'state.get', 'str',
    },
    '_bundle_tokenize': {
        'data.decode', 'repo_root.resolve', 'state_root.resolve', 'str', 'text.encode', 'text.replace',
    },
    '_bundle_handoff_candidates_for_agent': {
        '_bundle_handoff_candidates', 'agent.removeprefix', 'agent.startswith', 'candidates.append',
        'dict.fromkeys', 'list', 'tuple',
    },
    '_bundle_handoff_candidates': {
        'epic_handoff_map', 'epic_handoff_map(repo_root).get', 'tuple',
    },
    '_BundleImportLedger': {
        'list', 'relative.startswith', 'self.entries.get', 'self.entries.items', 'self.entries.pop',
        'self.entries.setdefault', 'sorted', 'tuple',
    },
    '_bundle_leftover_detail': {
        "', '.join", "'; '.join", 'any', 'parts.append', 'path.startswith',
    },
    '_bundle_present_leftovers': {
        'ledger.baseline.get', 'ledger.dirty_paths', 'present.append', 'tree.signature',
    },
    '_bundle_typed_failure': {
        'BundleReconcileRefused', '_bundle_leftover_detail', '_bundle_present_leftovers',
    },
    '_bundle_capture_baseline': {
        '_BundleReconcileTree', '_bundle_handoff_candidates_for_agent', 'repo.signature', 'state.snapshot_prefix',
    },
}

_PRIMITIVE_CALLS = {
    "BundleReconcileRefused", "_BundleImportLedger", "_bundle_member_path", "_bundle_member_path(path).split",
    "any", "found.append", "found.extend", "handle.fileno", "handle.flush", "handle.read", "handle.write", "len",
    "os.close", "os.fdopen", "os.fstat", "os.fsync", "os.link", "os.listdir", "os.mkdir", "os.open",
    "os.replace", "os.rmdir", "os.stat", "os.unlink", "relative.split", "reversed", "self.__exit__",
    "self._child_relative", "self._descendant_rels", "self._error_with_cleanup", "self._leaf_exists",
    "self._snapshot_children",
    "self._walk_parent", "self.copy_contents", "self.directory", "self.existing", "self.exists",
    "self.fd_paths.pop", "self.fds.append", "self.fds.clear", "self.ledger.drop", "self.ledger.intend_existing",
    "self.ledger.intend_new", "self.ledger.mark_published", "self.lstat_nofollow", "self.parent", "self.release",
    "self.remove", "self.signature", "self.write", "stat.S_ISDIR", "stat.S_ISFIFO", "stat.S_ISLNK", "stat.S_ISREG",
    "suppress", "uuid.uuid4",
}


def _assert_bundle_containment(source):
    """Allowlist every call reachable from the bundle import writers.

    Limits: the lint cannot trace a path built in a variable, an allowed
    method called with an outside path, or an imported library helper.
    Behavioural real-symlink tests are the containment proof.
    """
    module = ast.parse(source)
    definitions = {node.name: node for node in module.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
    parents = {child: parent for parent in ast.walk(module) for child in ast.iter_child_nodes(parent)}
    pending = [*_BUNDLE_CALLS, "_BundleReconcileTree"]
    checked = set()
    while pending:
        name = pending.pop()
        if name in checked:
            continue
        checked.add(name)
        definition = definitions[name]
        primitive = name == "_BundleReconcileTree"
        if primitive:
            permitted = _PRIMITIVE_CALLS
        else:
            assert name in _BUNDLE_CALLS or name in _BUNDLE_HELPER_CALLS, f"missing helper allowlist: {name}"
            permitted = _BUNDLE_CALLS.get(name, _BUNDLE_HELPER_CALLS.get(name))
        # Follow every admitted module-level helper, including helpers of helpers.
        pending.extend(permitted & definitions.keys())
        for node in ast.walk(definition):
            # Write-capable flags outside the only audited writer are forbidden,
            # even if they are assigned to a variable before os.open is called.
            if not primitive and isinstance(node, ast.Attribute):
                assert node.attr not in {"O_WRONLY", "O_RDWR", "O_TRUNC", "O_CREAT"}, "write flags outside primitive"
            if (
                isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Name)
                and node.value.id in {"os", "shutil"}
                and not (node.value.id == "os" and node.attr.startswith("O_"))
            ):
                parent = parents.get(node)
                assert isinstance(parent, ast.Call) and parent.func is node, (
                    f"unchecked non-call function reference in {name}: {ast.unparse(node)}"
                )
            if not isinstance(node, ast.Call):
                continue
            call = ast.unparse(node.func)
            assert call in permitted, f"unchecked call in {name}: {call}"
            keywords = {kw.arg: ast.unparse(kw.value) for kw in node.keywords}
            if call in {"os.mkdir", "os.stat", "os.unlink", "os.rmdir"}:
                assert "dir_fd" in keywords, f"unanchored {call}"
            if call in {"os.stat", "os.link"}:
                assert keywords.get("follow_symlinks") == "False"
            if call in {"os.link", "os.replace"}:
                assert "src_dir_fd" in keywords and "dst_dir_fd" in keywords
                assert (
                    ast.unparse(node.args[0]), ast.unparse(node.args[1]),
                    keywords["src_dir_fd"], keywords["dst_dir_fd"],
                ) in {
                    ("temporary", "name", "parent", "parent"),
                    ("src_name", "dst_name", "src", "dst"),
                }, "unchecked publication paths"
            if call == "os.open":
                flags = {part.attr for part in ast.walk(node.args[1]) if isinstance(part, ast.Attribute)}
                assert flags in (
                    {"O_RDONLY", "O_NOFOLLOW", "O_DIRECTORY"},
                    {"O_RDONLY", "O_NOFOLLOW", "O_NONBLOCK"},
                    {"O_WRONLY", "O_CREAT", "O_EXCL", "O_NOFOLLOW"},
                ), f"unsafe open flags: {flags}"
                assert all(isinstance(part, (ast.BinOp, ast.BitOr, ast.Attribute, ast.Name, ast.Load))
                           for part in ast.walk(node.args[1])), "indirect open flags"
                assert all(part.id == "os" for part in ast.walk(node.args[1]) if isinstance(part, ast.Name))
                assert ast.unparse(node.args[0]) in {"self.state_root", "name", "temporary"}, "unchecked open path"
                assert "dir_fd" in keywords or ast.unparse(node.args[0]) == "self.state_root"
                if "dir_fd" not in keywords:
                    assert flags == {"O_RDONLY", "O_NOFOLLOW", "O_DIRECTORY"}
            if call == "os.fdopen":
                assert ast.unparse(node.args[0]) == "fd"
                assert ast.literal_eval(node.args[1]) in {"rb", "wb"}


def test_reconcile_writes_have_one_descriptor_primitive():
    """The allowlist lint accepts this module; its limits are on the helper."""
    _assert_bundle_containment(inspect.getsource(th))


_WRITER_MUTATIONS = [
    "shutil.copyfile('source', 'target')",
    "writer = os.replace\nwriter('source', 'target')",
    "os.open('target', os.O_RDWR | os.O_CREAT | os.O_TRUNC)",
    "os.symlink('source', 'target')",
    "os.write(123, b'bytes')",
    "_unchecked_bundle_writer()",
]


@pytest.mark.parametrize("mutation", _WRITER_MUTATIONS, ids=["copyfile", "replace-alias", "rdwr-create-trunc", "symlink", "write", "unchecked-helper"])
@pytest.mark.parametrize("location", ["primitive", "installer", "tie"])
def test_containment_rejects_all_six_writer_mutations(mutation, location):
    source = inspect.getsource(th)
    _assert_bundle_containment(source)
    if location == "primitive":
        marker = "    def __enter__(self) -> _BundleReconcileTree:\n"
        indent = "        "
    else:
        function = th._bundle_stage_install if location == "installer" else th._bundle_preserve_tie
        marker = inspect.getsource(function).split('    agent =', 1)[0]
        indent = "    "
    injected = "\n".join(indent + line for line in mutation.splitlines()) + "\n"
    source = source.replace(marker, marker + injected, 1)
    source += "\ndef _unchecked_bundle_writer():\n    shutil.copyfile('source', 'target')\n"
    expected = "unchecked call"
    if mutation.startswith("writer ="):
        expected = "unchecked non-call function reference"
    elif location == "primitive" and mutation.startswith("os.open"):
        expected = "unsafe open flags"
    with pytest.raises(AssertionError, match=expected):
        _assert_bundle_containment(source)


@pytest.mark.parametrize("flag", ["O_RDWR", "O_TRUNC", "O_CREAT"])
def test_containment_rejects_write_flags_outside_primitive(flag):
    source = inspect.getsource(th)
    marker = "    agent = normalize_agent_name(str(manifest[\"agent\"]))"
    start = source.index("def _bundle_stage_install(")
    source = source[:start] + source[start:].replace(marker, f"    flags = os.{flag}\n" + marker, 1)
    with pytest.raises(AssertionError, match="write flags outside primitive"):
        _assert_bundle_containment(source)


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


@pytest.fixture
def newer_bundle(tied_bundle):
    b = tied_bundle
    b.manifest['upload_seq'] = 8
    b.manifest['bundle_sha256'] = th._bundle_digest(b.members, b.manifest)
    b.blob = th._bundle_archive(b.members, b.manifest)
    b.bundle.write_bytes(b.blob)
    return b


@pytest.mark.parametrize('component', [
    'receipts', 'archive', 'archive-entry', 'handoff-root', 'handoff-parent',
    'handoff-leaf', 'receipt-leaf', 'packet', 'lineage-sibling',
])
def test_newer_install_refuses_real_redirects_without_outside_write(newer_bundle, tmp_path, capsys, monkeypatch, component):
    b = newer_bundle
    outside = tmp_path / 'outside'
    outside.mkdir()
    (outside / 'sentinel').write_bytes(b'outside untouched')
    now = th.utc_now()
    monkeypatch.setattr(th, 'utc_now', lambda: now)
    archive_entry = b.lineage.parent / '_archive' / f"{b.manifest['lineage_id']}-{now.strftime('%Y%m%dT%H%M%SZ')}"
    paths = {
        'receipts': b.receipt.parent,
        'archive': b.lineage.parent / '_archive',
        'archive-entry': archive_entry,
        'handoff-root': b.root / '.claude',
        'handoff-parent': (b.root / HANDOFF_PATH).parent,
        'handoff-leaf': b.root / HANDOFF_PATH,
        'receipt-leaf': b.receipt,
        'packet': next(b.lineage.glob('generation-*')),
        'lineage-sibling': b.lineage / '_bundle-reconcile',
    }
    target = paths[component]
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        target.rename(outside / 'original')
        target.symlink_to(outside / 'original', target_is_directory=(outside / 'original').is_dir())
    else:
        target.symlink_to(outside, target_is_directory=True)
    before = _snapshot(outside)
    assert th.cmd_import_bundle(_import_args(b.root, b.bundle)) == 2
    assert json.loads(capsys.readouterr().out)['status'] == 'refused'
    assert _snapshot(outside) == before
    assert not list(b.lineage.parent.glob('.*.import-*'))
    assert not list(b.root.rglob('.reconcile-*.tmp'))


def test_newer_install_preserves_archive_receipt_and_handoff(newer_bundle, capsys):
    b = newer_bundle
    original_lease = json.loads((b.lineage / 'lease.json').read_bytes())
    original_handoff = (b.root / HANDOFF_PATH).read_bytes()
    assert th.cmd_import_bundle(_import_args(b.root, b.bundle)) == 0
    output = json.loads(capsys.readouterr().out)
    assert output['status'] == 'installed'
    assert 'cleanup_warning' not in output
    archive = b.root / output['archived']
    archived_lease = json.loads((archive / 'lease.json').read_bytes())
    assert archived_lease['replacement']['status'] == 'superseded'
    assert archived_lease['active'] == original_lease['active']
    assert json.loads(b.receipt.read_bytes())['upload_seq'] == 8
    assert output['preserved_handoffs']
    assert all(th.Path(path).read_bytes() == original_handoff for path in output['preserved_handoffs'])
    for name, payload in b.members.items():
        expected = th._bundle_rewrite(payload, repo_root=b.root) if th._bundle_text_member(name) else payload
        assert (b.root / name).read_bytes() == expected
    assert not list(b.lineage.parent.glob('.*.import-*'))
    assert not list(b.root.rglob('.reconcile-*.tmp'))


@pytest.mark.parametrize('failure', ['handoff', 'receipt', 'archive-lease', 'lineage-move'])
def test_newer_install_failure_restores_exact_original(newer_bundle, monkeypatch, capsys, failure):
    b = newer_bundle
    before = _snapshot(b.root)
    native_write = th._BundleReconcileTree.write_path
    native_move = th._BundleReconcileTree.move
    failed = False

    def write(tree, path, payload, **kwargs):
        nonlocal failed
        selected = (
            (failure == 'handoff' and path == HANDOFF_PATH)
            or (failure == 'receipt' and '/_bundle-receipts/' in path)
            or (failure == 'archive-lease' and '/_archive/' in path and path.endswith('/lease.json'))
        )
        if selected and not failed:
            failed = True
            raise OSError('injected install failure')
        return native_write(tree, path, payload, **kwargs)

    def move(tree, source, target):
        nonlocal failed
        if failure == 'lineage-move' and source.endswith('/lineage') and not failed:
            failed = True
            raise OSError('injected install failure')
        return native_move(tree, source, target)

    monkeypatch.setattr(th._BundleReconcileTree, 'write_path', write)
    monkeypatch.setattr(th._BundleReconcileTree, 'move', move)
    assert th.cmd_import_bundle(_import_args(b.root, b.bundle)) == 2
    assert 'injected install failure' in capsys.readouterr().out
    assert failed
    assert _snapshot(b.root) == before
    assert not list(b.lineage.parent.glob('.*.import-*'))
    assert not list(b.root.rglob('.reconcile-*.tmp'))


@pytest.mark.parametrize('kind', ['symlink', 'hardlink', 'fifo', 'existing'])
def test_newer_install_exclusive_temporary_refuses_existing_objects(newer_bundle, tmp_path, monkeypatch, capsys, kind):
    b = newer_bundle
    outside = tmp_path / 'sentinel'
    outside.write_bytes(b'outside untouched')
    temporary = (b.root / HANDOFF_PATH).parent / '.reconcile-fixed.tmp'
    if kind == 'symlink':
        temporary.symlink_to(outside)
    elif kind == 'hardlink':
        os.link(outside, temporary)
    elif kind == 'fifo':
        os.mkfifo(temporary)
    else:
        temporary.write_bytes(b'local untouched')
    monkeypatch.setattr(th.uuid, 'uuid4', lambda: SimpleNamespace(hex='fixed'))
    assert th.cmd_import_bundle(_import_args(b.root, b.bundle)) == 2
    output = json.loads(capsys.readouterr().out)
    assert output['status'] == 'refused'
    assert outside.read_bytes() == b'outside untouched'
    if kind != 'fifo':
        assert temporary.read_bytes() == (b'local untouched' if kind == 'existing' else b'outside untouched')
    assert not list(b.lineage.parent.glob('.*.import-*'))


def test_tie_invalid_member_creates_no_upload_directory(tied_bundle):
    b = tied_bundle
    with pytest.raises(ValueError, match='unsafe'):
        th._bundle_preserve_tie(b.root, manifest=b.manifest, members={'../escape': b'bad'}, blob=b.blob)
    assert not b.upload.parent.exists()


def test_newer_install_archives_large_local_member_without_truncation(newer_bundle, capsys):
    b = newer_bundle
    payload = b'x' * (th.ROLLOVER_BUNDLE_MAX_BYTES + 1)
    (b.lineage / 'large-local.bin').write_bytes(payload)
    assert th.cmd_import_bundle(_import_args(b.root, b.bundle)) == 0
    output = json.loads(capsys.readouterr().out)
    assert (b.root / output['archived'] / 'large-local.bin').read_bytes() == payload


def test_failed_rollback_retains_original_backup(newer_bundle, monkeypatch, capsys):
    b = newer_bundle
    original = _snapshot(b.lineage)
    original_handoff = (b.root / HANDOFF_PATH).read_bytes()
    original_receipt = b.receipt.read_bytes()
    native_move = th._BundleReconcileTree.move

    def move(tree, source, target):
        if source.endswith('/lineage') or source.endswith('/original-lineage'):
            raise OSError('injected commit and rollback failure')
        return native_move(tree, source, target)

    monkeypatch.setattr(th._BundleReconcileTree, 'move', move)
    assert th.cmd_import_bundle(_import_args(b.root, b.bundle)) == 2
    output = json.loads(capsys.readouterr().out)
    assert 'injected commit and rollback failure' in output['error']
    stages = list(b.lineage.parent.glob('.*.import-*'))
    assert len(stages) == 1
    assert _snapshot(stages[0] / 'original-lineage') == original
    assert stages[0].relative_to(b.root).as_posix() in output['error']
    assert (b.root / HANDOFF_PATH).read_bytes() == original_handoff
    assert b.receipt.read_bytes() == original_receipt


@pytest.mark.parametrize('rollback_failure', ['archive-removal', 'superseded-removal'])
def test_two_failures_continue_independent_rollback_steps(newer_bundle, monkeypatch, capsys, rollback_failure):
    b = newer_bundle
    original_lineage = _snapshot(b.lineage)
    original_handoff = (b.root / HANDOFF_PATH).read_bytes()
    original_receipt = b.receipt.read_bytes()
    native_move = th._BundleReconcileTree.move
    native_remove = th._BundleReconcileTree.remove_path
    failures = []

    def move(tree, source, target):
        if source.endswith('/lineage'):
            failures.append('commit')
            raise OSError('injected final lineage move failure')
        return native_move(tree, source, target)

    def remove(tree, path):
        if (
            (rollback_failure == 'archive-removal' and '/_archive/' in path)
            or (rollback_failure == 'superseded-removal' and '.superseded' in path)
        ):
            failures.append('rollback')
            raise OSError('injected ' + rollback_failure.replace('-', ' ') + ' failure')
        return native_remove(tree, path)

    monkeypatch.setattr(th._BundleReconcileTree, 'move', move)
    monkeypatch.setattr(th._BundleReconcileTree, 'remove_path', remove)
    assert th.cmd_import_bundle(_import_args(b.root, b.bundle)) == 2
    output = json.loads(capsys.readouterr().out)
    assert failures == ['commit', 'rollback']
    assert _snapshot(b.lineage) == original_lineage
    assert b.receipt.read_bytes() == original_receipt
    assert (b.root / HANDOFF_PATH).read_bytes() == original_handoff
    if rollback_failure == 'archive-removal':
        assert not list(b.root.rglob('*.superseded*'))
    else:
        assert all(p.read_bytes() == original_handoff for p in b.root.rglob('*.superseded*'))
    stages = list(b.lineage.parent.glob('.*.import-*'))
    assert len(stages) == 1
    assert output['status'] == 'refused'
    assert output['code'] == 'reconcile_rollback_failed'
    assert stages[0].relative_to(b.root).as_posix() in output['error']
    assert 'injected final lineage move failure' in output['error']
    assert 'injected ' + rollback_failure.replace('-', ' ') + ' failure' in output['error']


@pytest.mark.parametrize('function,mutation', [
    ('_bundle_commit_install', "sorted(['/outside/victim'], key=os.unlink)"),
    ('_bundle_local_lineage_snapshot', "shutil.rmtree('/outside')"),
    ('load_state', "shutil.rmtree('/outside')"),
])
def test_containment_checks_callbacks_and_recursive_helpers(function, mutation):
    source = inspect.getsource(th)
    _assert_bundle_containment(source)
    definition = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == function)
    lines = source.splitlines(keepends=True)
    lines.insert(definition.body[0].lineno - 1, '    ' + mutation + '\n')
    with pytest.raises(AssertionError):
        _assert_bundle_containment(''.join(lines))


@pytest.mark.parametrize('missing,code', [
    ('local-lease', 'reconcile_local_lease_missing'),
    ('staged-member', 'reconcile_staged_member_missing'),
])
def test_missing_install_payload_is_a_typed_refusal(newer_bundle, monkeypatch, capsys, missing, code):
    b = newer_bundle
    before = _snapshot(b.root)
    native_read = th._BundleReconcileTree.read_path
    original_lease = b.lineage.relative_to(b.root).as_posix() + '/lease.json'

    def read(tree, path):
        if missing == 'local-lease' and path == original_lease:
            return None
        if missing == 'staged-member' and '/repo/' in path:
            return None
        return native_read(tree, path)

    monkeypatch.setattr(th._BundleReconcileTree, 'read_path', read)
    assert th.cmd_import_bundle(_import_args(b.root, b.bundle)) == 2
    output = json.loads(capsys.readouterr().out)
    assert output['status'] == 'refused'
    assert output['code'] == code
    assert _snapshot(b.root) == before
    assert not list(b.lineage.parent.glob('.*.import-*'))


def test_rollback_archive_link_refuses_and_still_restores_original(newer_bundle, tmp_path, monkeypatch, capsys):
    b = newer_bundle
    original_lineage = _snapshot(b.lineage)
    original_handoff = (b.root / HANDOFF_PATH).read_bytes()
    original_receipt = b.receipt.read_bytes()
    outside = tmp_path / 'outside'
    outside.mkdir()
    (outside / 'sentinel').write_bytes(b'untouched outside')
    before = _snapshot(outside)
    native_move = th._BundleReconcileTree.move

    def move(tree, source, target):
        if source.endswith('/lineage'):
            archive = next((b.lineage.parent / '_archive').iterdir())
            archive.rename(archive.with_name(archive.name + '-saved'))
            archive.symlink_to(outside, target_is_directory=True)
            raise OSError('injected final lineage move failure')
        return native_move(tree, source, target)

    monkeypatch.setattr(th._BundleReconcileTree, 'move', move)
    assert th.cmd_import_bundle(_import_args(b.root, b.bundle)) == 2
    output = json.loads(capsys.readouterr().out)
    assert output['code'] == 'reconcile_rollback_failed'
    assert 'reconcile_member_symlink' in output['error']
    assert _snapshot(outside) == before
    assert _snapshot(b.lineage) == original_lineage
    assert (b.root / HANDOFF_PATH).read_bytes() == original_handoff
    assert b.receipt.read_bytes() == original_receipt
    stage = next(b.lineage.parent.glob('.*.import-*'))
    assert stage.relative_to(b.root).as_posix() in output['error']


def test_stage_cleanup_failure_reports_installed_with_warning(newer_bundle, monkeypatch):
    b = newer_bundle
    native_remove = th._BundleReconcileTree.remove_path
    captured = {}
    real_candidate = th._bundle_import_candidate

    def remove(tree, path):
        if '.import-' in path:
            raise OSError('injected stage cleanup failure')
        return native_remove(tree, path)

    def spy(*args, **kwargs):
        result = real_candidate(*args, **kwargs)
        captured['result'] = result
        return result

    monkeypatch.setattr(th._BundleReconcileTree, 'remove_path', remove)
    monkeypatch.setattr(th, '_bundle_import_candidate', spy)
    monkeypatch.setattr(gate, '_import_thread_handoff', lambda: th)
    monkeypatch.setattr(th, '_bundle_api_list', lambda *_a, **_kw: [{'manifest': b.manifest, 'upload_seq': 8}])
    monkeypatch.setattr(th, '_bundle_api_by_seq', lambda *_a, **_kw: (b.manifest, b.blob))
    surfaced = gate.phase_rollover_import(
        SimpleNamespace(import_bundle=True, repo_root=str(b.root), agent=AGENT, stream=STREAM)
    )
    output = captured['result']
    assert output['status'] == 'installed'
    warning = output['cleanup_warning']
    stage = next(b.lineage.parent.glob('.*.import-*'))
    relative = stage.relative_to(b.root).as_posix()
    assert warning['code'] == 'reconcile_stage_cleanup_failed'
    assert warning['stage'] == relative
    assert relative in warning['error']
    assert 'injected stage cleanup failure' in warning['error']
    assert str(b.root) not in warning['error']
    assert json.loads(b.receipt.read_bytes())['upload_seq'] == 8
    assert surfaced['status'] == 'issue'
    assert surfaced['warning'].startswith('WARNING:')
    assert relative in surfaced['warning']
    assert 'reconcile_stage_cleanup_failed' in surfaced['warning']
    assert 'skipped' not in surfaced['warning']
    assert 'refused' not in surfaced['warning']
    assert str(b.root) not in surfaced['warning']


@pytest.mark.parametrize('restore_failure', ['lease-restore', 'move-back'])
def test_archive_restore_failure_names_leftover_copy(newer_bundle, monkeypatch, capsys, restore_failure):
    b = newer_bundle
    original_lineage = _snapshot(b.lineage)
    original_handoff = (b.root / HANDOFF_PATH).read_bytes()
    original_receipt = b.receipt.read_bytes()
    before = _snapshot(b.root)
    native_write = th._BundleReconcileTree.write_path
    native_move = th._BundleReconcileTree.move
    archive_writes = 0

    def write(tree, path, payload, **kwargs):
        nonlocal archive_writes
        if '/_archive/' in path and path.endswith('/lease.json'):
            archive_writes += 1
            if archive_writes == 1:
                raise OSError('injected archive lease rewrite failure')
            if restore_failure == 'lease-restore':
                raise OSError('injected archive lease restore failure')
        return native_write(tree, path, payload, **kwargs)

    def move(tree, source, target):
        if restore_failure == 'move-back' and '/_archive/' in source:
            raise OSError('injected archive move-back failure')
        return native_move(tree, source, target)

    monkeypatch.setattr(th._BundleReconcileTree, 'write_path', write)
    monkeypatch.setattr(th._BundleReconcileTree, 'move', move)
    assert th.cmd_import_bundle(_import_args(b.root, b.bundle)) == 2
    output = json.loads(capsys.readouterr().out)
    archives = [path for path in (b.lineage.parent / '_archive').iterdir() if path.is_dir()]
    assert len(archives) == 1
    leftover = archives[0].relative_to(b.root).as_posix()
    assert output['status'] == 'refused'
    assert output['code'] == 'reconcile_archive_restore_failed'
    assert leftover in output['error']
    assert not Path(leftover).is_absolute()
    assert str(b.root) not in output['error']
    assert 'injected archive lease rewrite failure' in output['error']
    if restore_failure == 'move-back':
        assert 'injected archive move-back failure' in output['error']
    else:
        assert 'injected archive lease restore failure' in output['error']
    assert (archives[0] / 'lease.json').read_bytes() == original_lineage['lease.json']
    assert _snapshot(b.lineage) == original_lineage
    assert (b.root / HANDOFF_PATH).read_bytes() == original_handoff
    assert b.receipt.read_bytes() == original_receipt
    assert not list(b.lineage.parent.glob('.*.import-*'))
    assert not list(b.root.rglob('.reconcile-*.tmp'))
    extra = set(_snapshot(b.root)) - set(before)
    assert extra
    assert all(name.startswith(leftover + '/') for name in extra)


def _disk_snapshot(root: Path) -> dict[str, tuple]:
    """No-follow signatures: file bytes, directory identity, or other inode."""
    snap: dict[str, tuple] = {}
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        current = Path(dirpath)
        relative_dir = current.relative_to(root).as_posix()
        if relative_dir != ".":
            info = os.lstat(current)
            snap[relative_dir] = ("dir", info.st_dev, info.st_ino)
        for name in dirnames:
            path = current / name
            info = os.lstat(path)
            if stat.S_ISLNK(info.st_mode):
                rel = path.relative_to(root).as_posix()
                snap[rel] = ("other", info.st_mode, info.st_dev, info.st_ino)
        dirnames[:] = [name for name in dirnames if not (current / name).is_symlink()]
        for name in filenames:
            path = current / name
            rel = path.relative_to(root).as_posix()
            info = os.lstat(path)
            if stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode):
                snap[rel] = ("file", path.read_bytes())
            else:
                snap[rel] = ("other", info.st_mode, info.st_dev, info.st_ino)
    return snap


def _disk_leftovers(before: dict[str, tuple], after: dict[str, tuple]) -> list[str]:
    """Paths still on disk whose no-follow signature is new or changed.

    A directory that already existed and is still a directory is not a leftover:
    restoring it by copy changes its inode without leaving a new path.
    """
    leftover: list[str] = []
    for path, signature in after.items():
        previous = before.get(path)
        if previous == signature:
            continue
        if previous is not None and previous[0] == "dir" and signature[0] == "dir":
            continue
        leftover.append(path)
    return sorted(leftover)


def _parse_leftovers(text: str) -> list[str]:
    matches = re.findall(r"leftovers: \[([^\]]*)\]", text)
    assert matches, text
    body = matches[-1].strip()
    if not body:
        return []
    return [part.strip() for part in body.split(", ")]


# One code site for each create, link, publish, move, and remove the import performs.
# The superseded-unlink probe is the reviewer's native write, not an eleventh site.
_IMPORT_MUTATION_SITES = (
    "directory-mkdir",
    "write-create",
    "write-link",
    "write-replace",
    "write-unlink",
    "new-directory-mkdir",
    "move-replace",
    "copy-mkdir",
    "remove-unlink",
    "remove-rmdir",
    "write-unlink-superseded",
)


def _fail_import_site(monkeypatch, site: str, *, cleanup_fails: bool) -> dict[str, bool]:
    """Fail the first trusted-descriptor call at one import mutation site."""
    hit = {"site": False, "cleanup": False}
    native_mkdir = os.mkdir
    native_open = os.open
    native_link = os.link
    native_replace = os.replace
    native_unlink = os.unlink
    native_rmdir = os.rmdir
    native_remove = th._BundleReconcileTree.remove_path

    def caller() -> str:
        return sys._getframe(2).f_code.co_name

    def mkdir(path, mode=0o777, *, dir_fd=None):
        identified = {
            "directory": "directory-mkdir",
            "new_directory": "new-directory-mkdir",
            "copy_tree": "copy-mkdir",
        }.get(caller())
        if dir_fd is not None and identified == site and not hit["site"]:
            hit["site"] = True
            raise OSError(f"injected {site} failure")
        if dir_fd is None:
            return native_mkdir(path, mode)
        return native_mkdir(path, mode, dir_fd=dir_fd)

    def open_(path, flags, *args, **kwargs):
        creating = bool(flags & os.O_CREAT) and caller() == "write"
        if site == "write-create" and creating and kwargs.get("dir_fd") is not None and not hit["site"]:
            hit["site"] = True
            raise OSError("injected write-create failure")
        return native_open(path, flags, *args, **kwargs)

    def link(src, dst, *, src_dir_fd=None, dst_dir_fd=None, follow_symlinks=True):
        if site == "write-link" and caller() == "write" and src_dir_fd is not None and not hit["site"]:
            hit["site"] = True
            raise OSError("injected write-link failure")
        return native_link(
            src, dst, src_dir_fd=src_dir_fd, dst_dir_fd=dst_dir_fd, follow_symlinks=follow_symlinks
        )

    def replace(src, dst, *, src_dir_fd=None, dst_dir_fd=None):
        identified = {"write": "write-replace", "move": "move-replace"}.get(caller())
        if identified == site and src_dir_fd is not None and not hit["site"]:
            hit["site"] = True
            raise OSError(f"injected {site} failure")
        if src_dir_fd is None:
            return native_replace(src, dst)
        return native_replace(src, dst, src_dir_fd=src_dir_fd, dst_dir_fd=dst_dir_fd)

    def unlink(path, *, dir_fd=None):
        name = caller()
        if site == "write-unlink" and name == "write" and dir_fd is not None and not hit["site"]:
            hit["site"] = True
            raise OSError("injected write-unlink failure")
        if site == "remove-unlink" and name == "remove" and dir_fd is not None and not hit["site"]:
            hit["site"] = True
            raise OSError("injected remove-unlink failure")
        if (
            site == "write-unlink-superseded"
            and name == "write"
            and dir_fd is not None
            and not hit["site"]
            and any(".superseded" in entry for entry in os.listdir(dir_fd))
        ):
            hit["site"] = True
            raise OSError("injected superseded temp unlink failure")
        if dir_fd is None:
            return native_unlink(path)
        return native_unlink(path, dir_fd=dir_fd)

    def rmdir(path, *, dir_fd=None):
        if site == "remove-rmdir" and caller() == "remove" and dir_fd is not None and not hit["site"]:
            hit["site"] = True
            raise OSError("injected remove-rmdir failure")
        if dir_fd is None:
            return native_rmdir(path)
        return native_rmdir(path, dir_fd=dir_fd)

    def remove_path(tree, path):
        separate_cleanup = cleanup_fails and site not in {"remove-unlink", "remove-rmdir"}
        if separate_cleanup and ".import-" in path and not hit["cleanup"]:
            hit["cleanup"] = True
            raise OSError("injected stage cleanup failure")
        return native_remove(tree, path)

    monkeypatch.setattr(os, "mkdir", mkdir)
    monkeypatch.setattr(os, "open", open_)
    monkeypatch.setattr(os, "link", link)
    monkeypatch.setattr(os, "replace", replace)
    monkeypatch.setattr(os, "unlink", unlink)
    monkeypatch.setattr(os, "rmdir", rmdir)
    monkeypatch.setattr(th._BundleReconcileTree, "remove_path", remove_path)
    return hit


def test_cleanup_failure_on_archive_restore_names_archive_and_stage(newer_bundle, monkeypatch, capsys):
    """Lease rewrite, move-back, and stage cleanup all fail.

    The typed refusal must keep the archive-restore diagnostic and name both
    leftovers: the repository-relative archive copy and the retained stage.
    """
    b = newer_bundle
    original_lineage = _snapshot(b.lineage)
    original_handoff = (b.root / HANDOFF_PATH).read_bytes()
    original_receipt = b.receipt.read_bytes()
    before = _disk_snapshot(b.root)
    native_write = th._BundleReconcileTree.write_path
    native_move = th._BundleReconcileTree.move
    native_remove = th._BundleReconcileTree.remove_path
    archive_writes = 0

    def write(tree, path, payload, **kwargs):
        nonlocal archive_writes
        if '/_archive/' in path and path.endswith('/lease.json'):
            archive_writes += 1
            if archive_writes == 1:
                raise OSError('injected archive lease rewrite failure')
        return native_write(tree, path, payload, **kwargs)

    def move(tree, source, target):
        if '/_archive/' in source:
            raise OSError('injected archive move-back failure')
        return native_move(tree, source, target)

    def remove(tree, path):
        if '.import-' in path:
            raise OSError('injected stage cleanup failure')
        return native_remove(tree, path)

    monkeypatch.setattr(th._BundleReconcileTree, 'write_path', write)
    monkeypatch.setattr(th._BundleReconcileTree, 'move', move)
    monkeypatch.setattr(th._BundleReconcileTree, 'remove_path', remove)
    assert th.cmd_import_bundle(_import_args(b.root, b.bundle)) == 2
    output = json.loads(capsys.readouterr().out)
    archives = [path for path in (b.lineage.parent / '_archive').iterdir() if path.is_dir()]
    assert len(archives) == 1
    leftover = archives[0].relative_to(b.root).as_posix()
    stage = next(b.lineage.parent.glob('.*.import-*'))
    relative_stage = stage.relative_to(b.root).as_posix()
    diagnostic = (
        'archive lease rewrite failed: injected archive lease rewrite failure; '
        'archive restore failed: injected archive move-back failure; '
        f'leftover archive: {leftover}'
    )
    assert output['status'] == 'refused'
    assert output['code'] == 'reconcile_archive_restore_failed'
    assert diagnostic in output['error']
    assert 'stage cleanup failed: injected stage cleanup failure' in output['error']
    assert f'retained stage: {relative_stage}' in output['error']
    assert _parse_leftovers(output['error']) == _disk_leftovers(before, _disk_snapshot(b.root))
    assert not Path(leftover).is_absolute()
    assert not Path(relative_stage).is_absolute()
    assert str(b.root) not in output['error']
    assert (archives[0] / 'lease.json').read_bytes() == original_lineage['lease.json']
    assert _snapshot(b.lineage) == original_lineage
    assert (b.root / HANDOFF_PATH).read_bytes() == original_handoff
    assert b.receipt.read_bytes() == original_receipt
    assert stage.is_dir()
    assert not list(b.root.rglob('.reconcile-*.tmp'))
    extra = set(_snapshot(b.root)) - set(before)
    assert extra
    assert all(name.startswith((leftover + '/', relative_stage + '/')) for name in extra)


def test_session_start_warns_for_each_installed_bundle_cleanup(monkeypatch):
    stage = '.agent/thread-rollovers/claude-infra/.lineage-probe.import-abc'

    class FakeTH:
        @staticmethod
        def main(argv):
            del argv
            print(json.dumps({
                'status': 'installed',
                'bundles': [
                    {
                        'status': 'installed',
                        'cleanup_warning': {
                            'code': 'reconcile_stage_cleanup_failed',
                            'stage': stage,
                            'error': f'stage cleanup failed; retained stage: {stage}',
                        },
                    },
                    {'status': 'noop'},
                ],
            }))
            return 0

    monkeypatch.setattr(gate, '_import_thread_handoff', lambda: FakeTH)
    surfaced = gate.phase_rollover_import(
        SimpleNamespace(import_bundle=True, repo_root='.', agent=AGENT, stream=STREAM)
    )
    assert surfaced['status'] == 'issue'
    assert surfaced['warning'].startswith('WARNING:')
    assert stage in surfaced['warning']
    assert 'reconcile_stage_cleanup_failed' in surfaced['warning']
    assert 'skipped' not in surfaced['warning']
    assert 'refused' not in surfaced['warning']


def test_session_start_names_cleanup_leftovers():
    """An installed stage warning names the leftover paths SessionStart should show."""
    stage = ".agent/thread-rollovers/claude-infra/.lineage-probe.import-abc"
    leftover = f"{stage}/lineage/lease.json"
    lines = gate._installed_stage_cleanup_warnings(
        {
            "status": "installed",
            "cleanup_warning": {
                "code": "reconcile_stage_cleanup_failed",
                "stage": stage,
                "leftovers": [leftover, "", 3],
                "error": "stage cleanup failed",
            },
        }
    )
    assert lines == [
        "WARNING: rollover bundle installed; reconcile_stage_cleanup_failed; "
        f"retained stage: {stage}; leftovers: {leftover}"
    ]


def test_typed_checks_hold_under_optimize():
    root = Path(__file__).resolve().parents[2]
    script = """
import sys
from pathlib import Path
from scripts.orchestration import thread_handoff as th

if sys.flags.optimize < 1:
    sys.exit("python -O did not set optimize")

th.validate_live_lease = lambda *_args, **_kwargs: (None, None)
try:
    th._bundle_validate_lease_member(
        Path("."),
        agent="claude-infra",
        lineage_id="lineage-probe",
        manifest={},
        members={
            ".agent/thread-rollovers/claude-infra/lineage-probe/lease.json": b"{}",
        },
    )
except ValueError as exc:
    if "bundle lease replacement is missing" not in str(exc):
        sys.exit("replacement check raised the wrong error: " + str(exc))
else:
    sys.exit("replacement check did not fire")

tree = th._BundleReconcileTree(Path("."), "claude-infra", "lineage-probe")
try:
    with tree.parent("lease.json"):
        sys.exit("closed tree parent yielded")
except th.BundleReconcileRefused as exc:
    if exc.code != "reconcile_tree_unopened":
        sys.exit("root check raised the wrong code: " + exc.code)
else:
    sys.exit("root check did not fire")
print("typed-checks-ok")
"""
    completed = subprocess.run(
        [sys.executable, "-O", "-c", script],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "typed-checks-ok"


def test_import_mutation_sites_are_enumerated():
    """Ten create/link/publish/move/remove sites, plus the reviewer's native-write probe."""
    sites = [site for site in _IMPORT_MUTATION_SITES if site != "write-unlink-superseded"]
    assert len(sites) == 10
    assert sites == [
        "directory-mkdir",
        "write-create",
        "write-link",
        "write-replace",
        "write-unlink",
        "new-directory-mkdir",
        "move-replace",
        "copy-mkdir",
        "remove-unlink",
        "remove-rmdir",
    ]


@pytest.mark.parametrize("site", _IMPORT_MUTATION_SITES)
@pytest.mark.parametrize("cleanup_fails", [False, True])
def test_import_mutation_failure_names_exact_leftovers(newer_bundle, monkeypatch, capsys, site, cleanup_fails):
    """Each mutation failure, also with stage-cleanup failure, names exactly the paths still changed."""
    bundle = newer_bundle
    before = _disk_snapshot(bundle.root)
    original_handoff = (bundle.root / HANDOFF_PATH).read_bytes()
    hit = _fail_import_site(monkeypatch, site, cleanup_fails=cleanup_fails)
    rc = th.cmd_import_bundle(_import_args(bundle.root, bundle.bundle))
    output = json.loads(capsys.readouterr().out)
    if output.get("status") == "installed":
        text = output["cleanup_warning"]["error"]
        assert output["cleanup_warning"]["code"] == "reconcile_stage_cleanup_failed"
        assert rc == 0
    else:
        text = output["error"]
        assert output["status"] == "refused"
        assert rc == 2
    marker = (
        "injected superseded temp unlink failure"
        if site == "write-unlink-superseded"
        else f"injected {site} failure"
    )
    assert marker in text
    if cleanup_fails and site not in {"remove-unlink", "remove-rmdir"}:
        assert "injected stage cleanup failure" in text
        assert text.index(marker) < text.index("injected stage cleanup failure")
    assert hit["site"] is True
    assert str(bundle.root) not in text
    assert _parse_leftovers(text) == _disk_leftovers(before, _disk_snapshot(bundle.root))
    if site == "write-unlink-superseded":
        named = _parse_leftovers(text)
        assert any(path.endswith(".tmp") and ".reconcile-" in path for path in named)
        assert any(".superseded" in path for path in named)
        assert (bundle.root / HANDOFF_PATH).read_bytes() == original_handoff


@pytest.mark.parametrize("cleanup_fails", [False, True])
def test_publication_failure_keeps_diagnostic_when_temp_unlink_fails(
    newer_bundle, monkeypatch, capsys, cleanup_fails
):
    """A failed publish plus a failed temporary unlink keeps both diagnostics.

    Real link and unlink errors carry errno, so the typed refusal has to copy
    ``str()`` of each. With or without a stage-cleanup failure, the named
    leftovers stay exactly the paths still changed on disk.
    """
    bundle = newer_bundle
    before = _disk_snapshot(bundle.root)
    native_link = os.link
    native_unlink = os.unlink
    native_remove = th._BundleReconcileTree.remove_path
    hit = {"link": False, "unlink": False, "cleanup": False}

    def caller() -> str:
        return sys._getframe(2).f_code.co_name

    def link(src, dst, *, src_dir_fd=None, dst_dir_fd=None, follow_symlinks=True):
        if caller() == "write" and src_dir_fd is not None and not hit["link"]:
            hit["link"] = True
            raise OSError(errno.EIO, "injected write publication failure")
        return native_link(
            src, dst, src_dir_fd=src_dir_fd, dst_dir_fd=dst_dir_fd, follow_symlinks=follow_symlinks
        )

    def unlink(path, *, dir_fd=None):
        if caller() == "write" and dir_fd is not None and not hit["unlink"]:
            hit["unlink"] = True
            raise OSError(errno.EBUSY, "injected temporary unlink failure")
        if dir_fd is None:
            return native_unlink(path)
        return native_unlink(path, dir_fd=dir_fd)

    def remove_path(tree, path):
        if cleanup_fails and ".import-" in path and not hit["cleanup"]:
            hit["cleanup"] = True
            raise OSError("injected stage cleanup failure")
        return native_remove(tree, path)

    monkeypatch.setattr(os, "link", link)
    monkeypatch.setattr(os, "unlink", unlink)
    monkeypatch.setattr(th._BundleReconcileTree, "remove_path", remove_path)
    rc = th.cmd_import_bundle(_import_args(bundle.root, bundle.bundle))
    output = json.loads(capsys.readouterr().out)
    text = output["error"]
    assert output["status"] == "refused"
    assert output["code"] == "reconcile_install_failed"
    assert rc == 2
    assert hit == {"link": True, "unlink": True, "cleanup": cleanup_fails}
    publication = str(OSError(errno.EIO, "injected write publication failure"))
    unlink_diagnostic = str(OSError(errno.EBUSY, "injected temporary unlink failure"))
    assert publication in text
    assert unlink_diagnostic in text
    assert text.index(publication) < text.index(unlink_diagnostic)
    if cleanup_fails:
        assert "injected stage cleanup failure" in text
        assert text.index(unlink_diagnostic) < text.index("injected stage cleanup failure")
    else:
        assert "stage cleanup failed" not in text
    assert str(bundle.root) not in text
    assert _parse_leftovers(text) == _disk_leftovers(before, _disk_snapshot(bundle.root))


@pytest.mark.parametrize('mutation', [
    "os.replace('source', 'target')",
    "os.replace('/source', '/target', src_dir_fd=parent, dst_dir_fd=parent)",
    "os.open('/target', os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, dir_fd=parent)",
])
def test_containment_rejects_unanchored_or_unchecked_primitive_paths(mutation):
    source = inspect.getsource(th)
    _assert_bundle_containment(source)
    marker = '    def __enter__(self) -> _BundleReconcileTree:\n'
    source = source.replace(marker, marker + '        ' + mutation + '\n', 1)
    with pytest.raises(AssertionError):
        _assert_bundle_containment(source)
