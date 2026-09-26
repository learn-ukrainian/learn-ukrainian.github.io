"""The once-per-process arranged-tree cache in ``test_v4_real_slot_mechanism``
must refuse to serve a tree that is no longer exactly what its build produced,
and must never cache a failed build. Each case drives ``_arrange_base`` with a
tiny builder so the guard itself is proven without the ~9 s real build."""

from __future__ import annotations

import os
from pathlib import Path

import _v4_a7_real_slot_fixture as fx
import pytest
import test_v4_real_slot_mechanism as mechanism

ADMISSION_FILE = "data/projects/open_model_data/admission/receipt.json"  # stays writable
FROZEN_FILE = "data/projects/open_model_data/evidence/units.jsonl"  # frozen 0o444 and shared


@pytest.fixture(autouse=True)
def _guard_environment(monkeypatch, tmp_path):
    from _v4_provenance_resource_fixture import synthetic_resources

    fx.install_policy_resource(monkeypatch, tmp_path, fx.TRUST_POLICY)
    monkeypatch.setenv("HRAMATKA_V4_ADMISSION_ENABLED", "1")
    monkeypatch.setattr(mechanism, "_ARRANGE_BASES", {})
    with synthetic_resources():
        yield


def _build(base: Path) -> dict:
    for relative in (ADMISSION_FILE, FROZEN_FILE):
        (base / relative).parent.mkdir(parents=True, exist_ok=True)
        (base / relative).write_text('{"row": 1}\n', encoding="utf-8")
    return {"value": [1, 2, 3]}


def _arranged(tmp_path: Path, builder=_build) -> tuple[Path, dict, dict]:
    return mechanism._arrange_base("guard", builder, tmp_path)


def test_an_untouched_base_is_served_again_without_rebuilding(tmp_path: Path) -> None:
    calls = []
    first = _arranged(tmp_path, lambda base: calls.append(1) or _build(base))
    second = _arranged(tmp_path, lambda base: calls.append(1) or _build(base))
    assert first[0] == second[0]
    assert calls == [1]


def test_a_failed_build_is_never_cached(tmp_path: Path) -> None:
    calls = []

    def failing(base: Path) -> dict:
        calls.append(1)
        raise AssertionError("arrange-time validation refused")

    for _ in range(2):
        with pytest.raises(AssertionError, match="arrange-time validation refused"):
            _arranged(tmp_path, failing)
    assert calls == [1, 1]


def test_a_mutated_writable_base_file_fails_loudly(tmp_path: Path) -> None:
    base, _, _ = _arranged(tmp_path)
    (base / ADMISSION_FILE).write_text('{"row": 2}\n', encoding="utf-8")
    with pytest.raises(pytest.fail.Exception, match="shared base tree content was mutated"):
        _arranged(tmp_path)


def test_an_in_place_write_to_a_frozen_file_fails_loudly(tmp_path: Path) -> None:
    base, _, _ = _arranged(tmp_path)
    frozen = base / FROZEN_FILE
    frozen.chmod(0o644)
    frozen.write_text('{"row": 9}\n', encoding="utf-8")
    with pytest.raises(pytest.fail.Exception, match="shared base tree content was mutated"):
        _arranged(tmp_path)


def test_the_full_content_digest_catches_a_write_that_restores_size_and_mtime(tmp_path: Path) -> None:
    base, _, _ = _arranged(tmp_path)
    entry = mechanism._ARRANGE_BASES["guard"]
    frozen = base / FROZEN_FILE
    before = frozen.stat()
    frozen.chmod(0o644)
    frozen.write_text('{"row": 7}\n', encoding="utf-8")  # same length
    os.utime(frozen, ns=(before.st_atime_ns, before.st_mtime_ns))
    frozen.chmod(0o444)
    assert mechanism._tree_digest(base, hash_frozen=False) == entry.tree_digest  # per-hit check is blind to it
    assert mechanism._tree_digest(base, hash_frozen=True) != entry.full_tree_digest  # the module-end proof is not


def test_a_mutated_shared_in_memory_value_fails_loudly(tmp_path: Path) -> None:
    _, built, _ = _arranged(tmp_path)
    built["value"].append(4)
    with pytest.raises(pytest.fail.Exception, match="shared in-memory arrange values were mutated"):
        _arranged(tmp_path)


def test_a_monkeypatched_builder_dependency_fails_loudly(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _arranged(tmp_path)
    monkeypatch.setattr(mechanism.ledger, "sha256_text", lambda text: "0" * 64)
    with pytest.raises(pytest.fail.Exception, match=r"module attribute .*sha256_text"):
        _arranged(tmp_path)


def test_a_changed_environment_variable_fails_loudly(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _arranged(tmp_path)
    monkeypatch.setenv("HRAMATKA_V4_ADMISSION_ENABLED", "0")
    with pytest.raises(pytest.fail.Exception, match="environment variable HRAMATKA_V4_ADMISSION_ENABLED"):
        _arranged(tmp_path)


def test_a_changed_on_disk_input_of_the_build_fails_loudly(tmp_path: Path) -> None:
    source = tmp_path.parent / "guard-external-input.txt"
    source.write_text("one", encoding="utf-8")

    def reads_external(base: Path) -> dict:
        _build(base)
        return {"external": source.read_text(encoding="utf-8")}

    _arranged(tmp_path, reads_external)
    assert os.fspath(source) in mechanism._ARRANGE_BASES["guard"].disk_inputs
    source.write_text("two-longer", encoding="utf-8")
    with pytest.raises(pytest.fail.Exception, match="on-disk file the build read changed"):
        _arranged(tmp_path, reads_external)
