import hashlib
import os
import stat
from copy import deepcopy
from pathlib import Path

import pytest

from scripts.curriculum.evidence import codes, lock, registry


def allocate(rows, entry_id=1):
    return registry.allocate(
        rows,
        lemma="synthetic",
        pos="noun",
        entry={"source": "vesum", "entry_id": entry_id},
        allocated_at_build="synthetic-build-fingerprint",
    )


def test_lock_determinism_modes_and_corruption(tmp_path):
    path = tmp_path / "synthetic-level" / "nested" / "synthetic-words.yaml"
    content = lock.yaml_bytes({"z": 1, "a": [{"id": "W-002"}, {"id": "W-010"}]})
    old_umask = os.umask(0o077)
    try:
        first = lock.write(path, content)
    finally:
        os.umask(old_umask)
    expected_lock = hashlib.sha256(content).hexdigest().encode() + b"\n"
    sidecar = Path(f"{path}.lock")
    assert sidecar.read_bytes() == expected_lock
    assert lock.write(path, content) == first
    assert lock.check(path)
    assert sidecar.read_bytes() == expected_lock
    assert all(stat.S_IMODE(p.stat().st_mode) == 0o644 for p in (path, sidecar))
    assert all(stat.S_IMODE(p.stat().st_mode) == 0o755 for p in (path.parent, path.parent.parent))
    path.write_bytes(b"synthetic corruption")
    assert not lock.check(path)
    with pytest.raises(ValueError, match=codes.LOCK_MISMATCH):
        lock.require(path)


@pytest.mark.parametrize("suffix", [b" comment\n", b"\nextra\n", b"", b"\r\n"])
def test_lock_rejects_noncanonical_format(tmp_path, suffix):
    path = tmp_path / "synthetic.yaml"
    digest = lock.write(path, b"synthetic")
    Path(f"{path}.lock").write_bytes(digest.encode() + suffix)
    assert not lock.check(path)


def test_atomic_failure_keeps_previous_bytes(monkeypatch, tmp_path):
    path = tmp_path / "synthetic.yaml"
    lock.write(path, b"synthetic old")

    def fail(source, target):
        assert Path(source).parent == Path(target).parent
        raise OSError("synthetic replace failure")

    monkeypatch.setattr(lock.os, "replace", fail)
    with pytest.raises(OSError, match="synthetic replace failure"):
        lock.write(path, b"synthetic new")
    assert path.read_bytes() == b"synthetic old"
    assert lock.check(path)
    assert sorted(p.name for p in tmp_path.iterdir()) == ["synthetic.yaml", "synthetic.yaml.lock"]


def test_atomic_write_mode_default_and_custom(tmp_path: Path) -> None:
    target_default = tmp_path / "default.txt"
    lock.atomic_write(target_default, b"public")
    assert stat.S_IMODE(target_default.stat().st_mode) == 0o644

    target_private = tmp_path / "private.txt"
    lock.atomic_write(target_private, b"secret", mode=0o600)
    assert stat.S_IMODE(target_private.stat().st_mode) == 0o600


def test_tombstone_never_reused_and_append_only(tmp_path):
    path = tmp_path / "synthetic-registry.yaml"
    rows = registry.load(path)
    assert allocate(rows) == "W-001"
    registry.write(path, rows)
    registry.retire(rows, "W-001")
    registry.write(path, rows)
    assert allocate(rows) == "W-002"
    registry.write(path, rows)
    assert registry.load(path) == rows
    assert rows[0]["retired"] is True
    assert lock.check(path)
    for changed in [rows[1:], list(reversed(rows)), [{**rows[0], "lemma": "synthetic-other"}, rows[1]]]:
        with pytest.raises(ValueError, match=codes.REGISTRY_MISMATCH):
            registry.write(path, changed)
    resurrected = deepcopy(rows)
    resurrected[0].pop("retired")
    with pytest.raises(ValueError, match=codes.REGISTRY_MISMATCH):
        registry.write(path, resurrected)


def test_duplicate_ids_and_id_aliases_rejected():
    rows = []
    allocate(rows)
    with pytest.raises(ValueError, match=codes.REGISTRY_MISMATCH):
        registry.validate([*rows, {**rows[0], "id": "W-1"}])
    with pytest.raises(ValueError, match=codes.REGISTRY_MISMATCH):
        allocate(rows)
    assert len(rows) == 1


def test_store_disagreement_and_resolved_allocation():
    rows = []
    word_id = registry.allocate(rows, lemma="synthetic", pos="noun", entry="unresolved", allocated_at_build="synthetic")
    words = [{"id": word_id, "lemma": "synthetic", "pos": "noun", "entry": {"source": "vesum", "entry_id": 1}}]
    registry.check_store(rows, words)
    for bad_words in [[], words * 2, [{**words[0], "id": "W-999"}], [{**words[0], "lemma": "synthetic-other"}]]:
        with pytest.raises(ValueError, match=codes.REGISTRY_MISMATCH):
            registry.check_store(rows, bad_words)
    registry.retire(rows, word_id)
    with pytest.raises(ValueError, match=codes.REGISTRY_MISMATCH):
        registry.check_store(rows, words)


def test_registry_entry_cannot_change(tmp_path):
    rows = []
    allocate(rows)
    path = tmp_path / "synthetic-registry.yaml"
    registry.write(path, rows)
    rows[0]["entry"]["entry_id"] = 2
    with pytest.raises(ValueError, match=codes.REGISTRY_MISMATCH):
        registry.write(path, rows)


def test_code_registry_is_complete_and_help_lists_every_code():
    constants = {name: value for name, value in vars(codes).items() if name.isupper() and isinstance(value, str)}
    assert set(constants.values()) == set(codes.DESCRIPTIONS)
    assert len(constants) == len(codes.DESCRIPTIONS)
    assert set(line.split(":", 1)[0] for line in codes.help_text().splitlines()) == set(codes.DESCRIPTIONS)
