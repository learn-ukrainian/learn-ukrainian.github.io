"""Content-verified lookup acceleration and the pre-#9757 replay oracle."""

import json
import sys
from pathlib import Path
from typing import Any

import pytest

from scripts.fleet import ignored_task_output as output


def legacy_record_matches_worktree(record, worktree, *, repo_root):
    """Keep the replay oracle independent of the optimized matcher."""
    from scripts.orchestration.worktree_claims import resolve_claim_path

    locations = [record.get("worktree_path") or record.get("cwd")]
    runtime_paths = record.get("acp_runtime_paths")
    if isinstance(runtime_paths, list):
        locations.extend(runtime_paths)
    for location in locations:
        if not isinstance(location, str) or not location:
            continue
        try:
            if resolve_claim_path(location, repo_root=repo_root) == worktree.resolve(strict=True):
                return True
        except (OSError, ValueError, RuntimeError):
            continue
    return False


def legacy_resolve_worktree_record(
    worktree: Path, tasks_dir: Path, *, repo_root: Path
) -> tuple[Path | None, dict[str, Any]]:
    """Resolve identity from canonical records, never from a caller's hint.

    Inspect hot and archived records: a different filename, renamed tree, or
    optional task argument cannot hide a retention claim. Ambiguity fails closed.
    """
    from scripts.orchestration.worktree_claims import record_may_claim_worktree, worktree_claim_needles

    matches = []
    needles = worktree_claim_needles(worktree, worktree.resolve())
    for path in sorted(tasks_dir.glob("*.json")) + sorted((tasks_dir / "archive").glob("*.json")):
        try:
            raw = path.read_bytes()
        except OSError:
            raise ValueError("task identity inventory unreadable") from None
        try:
            record = json.loads(raw)
        except ValueError:
            # Reuse the claim owner's existing released-record proof only for
            # corrupt records with no possible retention key. Valid records,
            # including released symlink aliases, are always resolved below.
            if record_may_claim_worktree(raw, needles) or b'"keep_worktree"' in raw:
                raise ValueError("task identity inventory unreadable") from None
            continue
        if isinstance(record, dict):
            if legacy_record_matches_worktree(record, worktree, repo_root=repo_root):
                matches.append((path, record))
            elif record.get("keep_worktree") and legacy_record_matches_worktree(
                {"cwd": record.get("cwd")}, worktree, repo_root=repo_root
            ):
                raise ValueError("ambiguous retention task binding")
    if len(matches) > 1:
        kept = [match for match in matches if match[1].get("keep_worktree")]
        if len(kept) == 1:
            return kept[0]
        if kept:
            raise ValueError("ambiguous worktree task attribution with retention intent")
        # Finished references alone are not ownership. Without one creator,
        # output retains unknown attribution; empty trees remain removable.
        creators = [match for match in matches if match[1].get("worktree_reused") is False]
        return creators[0] if len(creators) == 1 else (None, {})
    return matches[0] if matches else (None, {})


def result(resolve, tree, tasks, root):
    try:
        return resolve(tree, tasks, repo_root=root)
    except ValueError as exc:
        return ("ValueError", str(exc))


def replay(tasks, root, trees):
    """Run both implementations, comparing the full record or exact error text."""
    for tree in trees:
        expected = result(legacy_resolve_worktree_record, tree, tasks, root)
        assert result(output.resolve_worktree_record, tree, tasks, root) == expected


@pytest.fixture
def store(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    tasks = root / "tasks"
    tasks.mkdir()
    (tasks / "archive").mkdir()
    tree = root / "tree"
    tree.mkdir()
    return root, tasks, tree


def save(tasks, name, record):
    path = tasks / name
    path.write_text(json.dumps(record))
    return path


def test_ac01_full_and_cached_fixture_replay(store):
    root, tasks, tree = store
    alias = root / "different-name"
    alias.symlink_to(tree, target_is_directory=True)
    save(tasks, "hot.json", {"worktree_path": "tree", "worktree_reused": True, "extra": [1, 2]})
    save(tasks, "archive/creator.json", {"cwd": str(alias), "worktree_reused": False, "extra": {"a": 3}})
    save(tasks, "runtime.json", {"acp_runtime_paths": [None, 42, str(tree)], "worktree_reused": True})
    trees = [tree, alias, root / "absent", tree / ".." / "tree", tree / "."]
    replay(tasks, root, trees)
    replay(tasks, root, trees)
    actual = output.resolve_worktree_record(tree, tasks, repo_root=root)
    assert actual[0].name == "creator.json" and actual[1]["extra"] == {"a": 3}


@pytest.mark.parametrize(
    "spelling", ["relative", "home", "slash_escape", "unicode_escape", "quote_escape", "escaped_key"]
)
def test_path_spellings_and_json_escapes(store, monkeypatch, spelling):
    root, tasks, tree = store
    if spelling == "quote_escape":
        tree = root / 'quote"tree'
        tree.mkdir()
    value = str(tree)
    if spelling == "relative":
        value = tree.name
    elif spelling == "home":
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: root))
        # expanduser uses the OS home, so patch its resolver rather than env.
        monkeypatch.setattr(
            output.os.path, "expanduser", lambda text: str(root) + text[1:] if text.startswith("~") else text
        )
        value = "~/tree"
    raw = json.dumps({"worktree_path": value, "keep_worktree": True})
    if spelling == "slash_escape":
        raw = raw.replace("/", r"\/")
    elif spelling == "unicode_escape":
        raw = raw.replace("tree", r"tr\u0065e")
    elif spelling == "escaped_key":
        raw = raw.replace("worktree_path", r"worktree_\u0070ath")
    (tasks / "record.json").write_text(raw)
    replay(tasks, root, [tree])
    assert output.resolve_worktree_record(tree, tasks, repo_root=root)[0] == tasks / "record.json"


@pytest.mark.parametrize(
    "raw,blocked",
    [
        (b'{"status":"done", broken', False),
        (b'{"status":"running", broken', True),
        (b'{"status":"done", "worktree_path":"tree", broken', True),
        (b'{"status":"done", "keep_worktree":false, broken', True),
        (b'{"status":"done", "worktree_path":"tr\\u0065e", broken', True),
    ],
)
def test_corrupt_record_keeps_legacy_fail_closed_outcome(store, raw, blocked):
    root, tasks, tree = store
    (tasks / "corrupt.json").write_bytes(raw)
    replay(tasks, root, [tree, root / "absent"])
    actual = result(output.resolve_worktree_record, tree, tasks, root)
    assert actual == (("ValueError", "task identity inventory unreadable") if blocked else (None, {}))


def test_cached_source_is_still_read_and_unreadable_fails_closed(store, monkeypatch):
    root, tasks, tree = store
    path = save(tasks, "record.json", {"worktree_path": str(tree)})
    output.resolve_worktree_record(tree, tasks, repo_root=root)
    original = Path.read_bytes

    def read(candidate):
        if candidate == path:
            raise OSError("denied")
        return original(candidate)

    monkeypatch.setattr(Path, "read_bytes", read)
    replay(tasks, root, [tree])
    assert result(output.resolve_worktree_record, tree, tasks, root) == (
        "ValueError",
        "task identity inventory unreadable",
    )


def test_cached_symlink_is_resolved_again_after_retargeting(store):
    root, tasks, tree = store
    alias = root / "alias"
    alias.symlink_to(tree)
    save(tasks, "record.json", {"worktree_path": str(alias), "status": "done"})
    replay(tasks, root, [tree])
    other = root / "other"
    other.mkdir()
    alias.unlink()
    alias.symlink_to(other)
    replay(tasks, root, [tree, other, alias])
    assert output.resolve_worktree_record(tree, tasks, repo_root=root) == (None, {})
    assert output.resolve_worktree_record(other, tasks, repo_root=root)[0] == tasks / "record.json"


def test_hot_and_archived_same_name_keep_distinct_cache_entries(store):
    root, tasks, tree = store
    save(tasks, "record.json", {"cwd": str(root), "worktree_reused": True})
    archived = save(tasks, "archive/record.json", {"cwd": str(tree), "keep_worktree": True})
    replay(tasks, root, [tree, root])
    replay(tasks, root, [tree, root])
    cache = output._read_identity_cache(output._identity_cache_path(tasks))
    assert set(cache) == {"record.json", "archive/record.json"}
    assert output.resolve_worktree_record(tree, tasks, repo_root=root)[0] == archived


def test_target_is_strictly_resolved_once_per_lookup(store, monkeypatch):
    root, tasks, tree = store
    for i in range(4):
        save(tasks, f"record-{i}.json", {"cwd": str(root / "other"), "acp_runtime_paths": [str(tree)]})
    original = Path.resolve
    strict_targets = []

    def resolve(path, strict=False):
        if path == tree and strict:
            strict_targets.append(path)
        return original(path, strict=strict)

    monkeypatch.setattr(Path, "resolve", resolve)
    assert output.resolve_worktree_record(tree, tasks, repo_root=root) == (None, {})
    assert strict_targets == [tree]


@pytest.mark.parametrize("failure", [OSError, ValueError, RuntimeError])
def test_failed_strict_target_resolution_keeps_every_comparison_false(store, monkeypatch, failure):
    root, tasks, tree = store
    save(tasks, "record.json", {"cwd": str(tree), "keep_worktree": True})
    original = Path.resolve

    def resolve(path, strict=False):
        if path == tree and strict:
            raise failure("unresolvable target")
        return original(path, strict=strict)

    monkeypatch.setattr(Path, "resolve", resolve)
    replay(tasks, root, [tree])
    assert output.resolve_worktree_record(tree, tasks, repo_root=root) == (None, {})


def test_claim_paths_are_memoized_only_within_each_lookup(store, monkeypatch):
    from scripts.orchestration import worktree_claims

    root, tasks, tree = store
    for i in range(4):
        save(tasks, f"record-{i}.json", {"cwd": str(root / "other"), "acp_runtime_paths": [str(tree)]})
    original = worktree_claims.resolve_claim_path
    locations = []

    def resolve(location, *, repo_root):
        locations.append(location)
        return original(location, repo_root=repo_root)

    monkeypatch.setattr(worktree_claims, "resolve_claim_path", resolve)
    for _ in range(2):
        locations.clear()
        assert output.resolve_worktree_record(tree, tasks, repo_root=root) == (None, {})
        assert locations == [str(root / "other"), str(tree)]


def test_cached_keep_worktree_cwd_ambiguity(store):
    root, tasks, tree = store
    save(tasks, "record.json", {"worktree_path": str(root), "cwd": str(tree), "keep_worktree": True})
    output.resolve_worktree_record(root / "absent", tasks, repo_root=root)
    replay(tasks, root, [tree])
    assert result(output.resolve_worktree_record, tree, tasks, root) == (
        "ValueError",
        "ambiguous retention task binding",
    )


@pytest.mark.parametrize("kept,creators", [(0, 0), (0, 1), (0, 2), (1, 0), (2, 2)])
def test_multiple_creators_and_retention_attribution(store, kept, creators):
    root, tasks, tree = store
    for i in range(2):
        save(tasks, f"record-{i}.json", {"cwd": str(tree), "keep_worktree": i < kept, "worktree_reused": i >= creators})
    replay(tasks, root, [tree, root / "absent"])
    replay(tasks, root, [tree])


@pytest.mark.parametrize("damage", ["missing", "truncated", "deep", "projection", "schema", "entry_shape"])
def test_missing_or_damaged_cache_falls_back(store, damage):
    root, tasks, tree = store
    save(tasks, "record.json", {"cwd": str(tree), "keep_worktree": True, "extra": 9})
    output.resolve_worktree_record(tree, tasks, repo_root=root)
    path = output._identity_cache_path(tasks)
    if damage == "missing":
        path.unlink()
    elif damage == "truncated":
        path.write_bytes(b"{")
    elif damage == "deep":
        path.write_bytes(b"[" * 2000)
    else:
        cache = json.loads(path.read_bytes())
        if damage == "projection":
            cache["entries"]["record.json"]["identity"]["cwd"] = str(root)
        elif damage == "schema":
            cache["schema"] = "old"
        else:
            cache["entries"]["record.json"]["identity"] = {}
            cache["sha256"] = output.hashlib.sha256(json.dumps(cache["entries"], sort_keys=True).encode()).hexdigest()
        path.write_text(json.dumps(cache))
    replay(tasks, root, [tree])


def test_same_length_changed_bytes_invalidate_cached_identity(store):
    root, tasks, tree = store
    other = root / "else"
    other.mkdir()
    path = save(tasks, "record.json", {"cwd": str(tree)})
    output.resolve_worktree_record(tree, tasks, repo_root=root)
    raw = path.read_bytes()
    path.write_bytes(raw.replace(b"tree", b"else"))
    assert len(path.read_bytes()) == len(raw)
    replay(tasks, root, [tree, other])
    assert output.resolve_worktree_record(tree, tasks, repo_root=root) == (None, {})


def test_concurrent_stale_cache_publication_and_new_inventory_entries(store):
    root, tasks, tree = store
    path = save(tasks, "record.json", {"cwd": str(root / "other")})
    output.resolve_worktree_record(tree, tasks, repo_root=root)
    stale = output._read_identity_cache(output._identity_cache_path(tasks))
    path.write_text(json.dumps({"cwd": str(tree), "keep_worktree": True}))
    output.resolve_worktree_record(tree, tasks, repo_root=root)
    # Model a slower concurrent writer publishing its earlier complete snapshot.
    output._write_identity_cache(output._identity_cache_path(tasks), stale)
    save(tasks, "archive/new.json", {"cwd": str(tree), "keep_worktree": True})
    replay(tasks, root, [tree])
    assert result(output.resolve_worktree_record, tree, tasks, root) == (
        "ValueError",
        "ambiguous worktree task attribution with retention intent",
    )
    (tasks / "archive/new.json").unlink()
    replay(tasks, root, [tree])


def test_valid_cached_record_becoming_corrupt_is_not_hidden(store):
    root, tasks, tree = store
    path = save(tasks, "record.json", {"cwd": str(tree), "keep_worktree": True})
    output.resolve_worktree_record(tree, tasks, repo_root=root)
    path.write_bytes(path.read_bytes()[:-1])
    replay(tasks, root, [tree])


def test_cached_decoder_policy_change_reparses_unchanged_source_bytes(store):
    root, tasks, tree = store
    previous_limit = sys.get_int_max_str_digits()
    try:
        sys.set_int_max_str_digits(0)
        raw = '{"cwd":' + json.dumps(str(tree)) + ',"keep_worktree":true,"ignored":' + "1" * 700 + "}"
        (tasks / "record.json").write_text(raw)
        output.resolve_worktree_record(tree, tasks, repo_root=root)
        sys.set_int_max_str_digits(640)
        replay(tasks, root, [tree])
        assert result(output.resolve_worktree_record, tree, tasks, root) == (
            "ValueError",
            "task identity inventory unreadable",
        )
    finally:
        sys.set_int_max_str_digits(previous_limit)


@pytest.mark.parametrize(
    "record",
    [
        None,
        False,
        42,
        [],
        {"worktree_path": ["tree"], "cwd": "tree", "keep_worktree": False},
        {"worktree_path": "", "cwd": "tree", "acp_runtime_paths": {"path": "tree"}},
    ],
)
def test_nonstandard_valid_record_values(store, record):
    root, tasks, tree = store
    save(tasks, "record.json", record)
    replay(tasks, root, [tree, root / "absent"])
    replay(tasks, root, [tree])


@pytest.mark.parametrize("failure", ["read", "write", "replace", "serialize"])
def test_cache_io_failure_does_not_change_inventory_result(store, monkeypatch, failure):
    root, tasks, tree = store
    save(tasks, "record.json", {"cwd": str(tree)})
    if failure == "read":
        original = Path.read_bytes

        def read(path):
            if path == output._identity_cache_path(tasks):
                raise OSError("cache denied")
            return original(path)

        monkeypatch.setattr(Path, "read_bytes", read)
    elif failure == "write":
        monkeypatch.setattr(
            output.tempfile, "NamedTemporaryFile", lambda **kwargs: (_ for _ in ()).throw(OSError("denied"))
        )
    elif failure == "replace":
        monkeypatch.setattr(output.os, "replace", lambda *args: (_ for _ in ()).throw(OSError("denied")))
    else:
        original_dumps = json.dumps

        def dumps(value, *args, **kwargs):
            if isinstance(value, dict):
                raise RecursionError("deep")
            return original_dumps(value, *args, **kwargs)

        monkeypatch.setattr(output.json, "dumps", dumps)
    replay(tasks, root, [tree])
    assert not list(tasks.glob(".record-identities-*"))


def test_ac02_cache_hits_only_parse_the_matching_canonical_record(store, monkeypatch):
    root, tasks, tree = store
    paths = [
        save(tasks, f"unrelated-{i}.json", {"cwd": str(root / f"other-{i}"), "keep_worktree": False}) for i in range(8)
    ]
    paths.append(save(tasks, "match.json", {"cwd": str(tree), "extra": [1, 2, 3]}))
    output.resolve_worktree_record(tree, tasks, repo_root=root)
    source_bytes = {path.read_bytes() for path in paths}
    original = json.loads
    parsed = []

    def loads(raw, *args, **kwargs):
        if isinstance(raw, bytes) and raw in source_bytes:
            parsed.append(raw)
        return original(raw, *args, **kwargs)

    monkeypatch.setattr(output.json, "loads", loads)
    actual = output.resolve_worktree_record(tree, tasks, repo_root=root)
    assert actual[1]["extra"] == [1, 2, 3]
    assert parsed == [(tasks / "match.json").read_bytes()]
