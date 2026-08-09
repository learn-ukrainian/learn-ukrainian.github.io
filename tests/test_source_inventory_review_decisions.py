from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import pytest
import yaml

from scripts.audit import source_inventory_review_decisions as decisions
from scripts.audit.source_inventory_intake import SourceInventoryError, SourceInventoryRecord

FIRST_BATCH = (
    decisions.DEFAULT_DECISION_DIR / "2026-06-29-first-approved-publish-batch.yaml"
)
EXPECTED_COMMITTED_DECISION_FILE_COUNT = 53
COMMITTED_DECISION_FILES = tuple(sorted(decisions.DEFAULT_DECISION_DIR.glob("*.yaml")))
DECISION_LINE = re.compile(r"^\s+decision:\s+([a-z_]+)\s*$")


def _write_decision_file(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _minimal_payload() -> dict[str, object]:
    source_inventory = {
        "path": "data/lexicon/source-inventory/ohoiko-abetka-keywords.yaml",
        "locator": "letters[А].key_word",
    }
    source_inventory["key"] = decisions.source_inventory_key(
        lemma="ананас",
        inventory_path=str(source_inventory["path"]),
        locator=str(source_inventory["locator"]),
    )
    source_inventory["source_id"] = "ohoiko-abetka-1-keywords"
    source_inventory["source_family"] = "ohoiko"
    return {
        "version": decisions.DECISION_VERSION,
        "kind": decisions.DECISION_KIND,
        "batch_id": "fixture-batch",
        "batch_label": "fixture",
        "reviewer": "test",
        "reviewed_at": "2026-06-29",
        "source_queue": {
            "workflow": decisions.QUEUE_WORKFLOW,
            "generated_from_pr": 4021,
            "total_queue_rows": 1,
            "approved_in_queue": 1,
            "first_promotion_batch_size": 1,
        },
        "production_outputs_updated": [],
        "decisions": [
            {
                "lemma": "ананас",
                "decision": "approve_for_publish",
                "approved_pos": "noun",
                "approved_gloss": "pineapple",
                "sense_note": "fixture",
                "source_inventory": source_inventory,
                "evidence_refs": ["fixture"],
                "review_queue_reasons": [
                    "grow_needs_review:heritage_status flags russian_shadow"
                ],
            }
        ],
    }


def _decision_counts_from_validated_lines(path: Path) -> Counter[str]:
    """Count decision rows without constructing a second 41 MB YAML object graph."""
    counts: Counter[str] = Counter()
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            match = DECISION_LINE.fullmatch(line.rstrip("\n"))
            if match:
                counts[match.group(1)] += 1
    return counts


def test_committed_first_source_inventory_review_batch_validates() -> None:
    summary = decisions.validate_committed_decision_files([FIRST_BATCH])

    assert summary == {
        "files": 1,
        "rows": 20,
        "decision_counts": {"approve_for_publish": 20},
    }


@pytest.fixture(scope="session")
def committed_source_index() -> dict[tuple[str, str, str], SourceInventoryRecord]:
    """Load the immutable committed corpus once in each pytest process."""
    records = decisions.read_source_inventories(
        decisions.COMMITTED_SOURCE_INVENTORIES,
        project_root=decisions.PROJECT_ROOT,
    )
    return decisions._source_record_index(records)


def test_default_committed_decision_file_parametrization_is_complete() -> None:
    discovered = tuple(sorted(decisions.DEFAULT_DECISION_DIR.glob("*.yaml")))

    assert discovered
    assert discovered == COMMITTED_DECISION_FILES
    assert len(COMMITTED_DECISION_FILES) == EXPECTED_COMMITTED_DECISION_FILE_COUNT
    assert len(set(COMMITTED_DECISION_FILES)) == len(COMMITTED_DECISION_FILES)


def test_default_committed_decision_files_keep_aggregate_floors(
    committed_source_index: dict[tuple[str, str, str], SourceInventoryRecord],
) -> None:
    sample_summary = decisions.validate_decision_file(
        FIRST_BATCH,
        source_index=dict(committed_source_index),
    )
    sample_counts = _decision_counts_from_validated_lines(FIRST_BATCH)
    assert sum(sample_counts.values()) == sample_summary["rows"]
    assert sample_counts == Counter(sample_summary["decision_counts"])

    decision_counts: Counter[str] = Counter()
    total_rows = 0
    for path in COMMITTED_DECISION_FILES:
        counts = _decision_counts_from_validated_lines(path)
        total_rows += sum(counts.values())
        decision_counts.update(counts)

    assert len(COMMITTED_DECISION_FILES) >= 1
    assert total_rows >= 20
    assert decision_counts["approve_for_publish"] >= 20


@pytest.mark.parametrize(
    "ledger_path",
    COMMITTED_DECISION_FILES,
    ids=lambda path: path.name,
)
def test_default_committed_decision_files_validate(
    ledger_path: Path,
    committed_source_index: dict[tuple[str, str, str], SourceInventoryRecord],
) -> None:
    # Each ledger gets an independent copy because validation may add records from
    # a present staged inventory. This prevents test order from affecting results.
    summary = decisions.validate_decision_file(
        ledger_path,
        source_index=dict(committed_source_index),
    )

    assert summary["path"] == str(ledger_path)
    assert summary["rows"] >= 1
    assert summary["decision_counts"]
    line_counts = _decision_counts_from_validated_lines(ledger_path)
    assert sum(line_counts.values()) == summary["rows"]
    assert line_counts == Counter(summary["decision_counts"])


def test_committed_decision_validation_reuses_shared_source_index(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inventory = tmp_path / "committed-inventory.yaml"
    first = tmp_path / "first.yaml"
    second = tmp_path / "second.yaml"
    _write_decision_file(first, _minimal_payload())
    _write_decision_file(second, _minimal_payload())
    record = SourceInventoryRecord(
        lemma="ананас",
        source_family="ohoiko",
        extraction_mode="fixture",
        inventory_path="data/lexicon/source-inventory/ohoiko-abetka-keywords.yaml",
        inventory_locator="letters[А].key_word",
        source_id="ohoiko-abetka-1-keywords",
        source_locator="letters[А].key_word",
    )
    calls: list[tuple[Path, ...]] = []

    def read_once(paths: tuple[Path, ...], *, project_root: Path) -> list[SourceInventoryRecord]:
        calls.append(paths)
        return [record]

    monkeypatch.setattr(decisions, "COMMITTED_SOURCE_INVENTORIES", (inventory,))
    monkeypatch.setattr(decisions, "read_source_inventories", read_once)

    summary = decisions.validate_committed_decision_files([first, second])

    assert summary == {
        "files": 2,
        "rows": 2,
        "decision_counts": {"approve_for_publish": 2},
    }
    assert calls == [(inventory,)]


def test_committed_yaml_uses_the_c_safe_loader_when_available() -> None:
    # Guards #5768. `yaml.safe_load` silently uses PyYAML's PURE-PYTHON loader even
    # when libyaml is installed — PyYAML never auto-selects the C implementation. That
    # is why this module parsed 41MB of committed decision YAML at ~590MB peak RSS and
    # hit MemoryError on CI. A refactor that reverts to `yaml.safe_load` must fail
    # here, not silently cost 20% of the suite's memory again three weeks later.
    if not hasattr(yaml, "CSafeLoader"):
        pytest.skip("this PyYAML build has no libyaml C extension")
    assert decisions._SafeLoader is yaml.CSafeLoader


def test_committed_yaml_loader_refuses_python_object_tags(tmp_path: Path) -> None:
    # The security boundary behind the perf fix, asserted behaviourally so it holds
    # whichever loader is wired in. `CSafeLoader` is the C implementation of
    # SafeLoader; `CLoader`/`Loader` are the C/py implementations of the FULL loader
    # and construct arbitrary Python objects from `!!python/object` tags. They differ
    # by four characters and a code-execution boundary, and this module parses
    # committed data files, so that boundary is real and not theoretical.
    hostile = tmp_path / "hostile.yaml"
    hostile.write_text(
        'decisions: !!python/object/apply:os.system ["echo pwned"]\n',
        encoding="utf-8",
    )
    with pytest.raises(yaml.YAMLError):
        decisions._read_yaml_mapping(hostile)


def test_decision_validator_rejects_bad_source_key(tmp_path: Path) -> None:
    payload = _minimal_payload()
    row = payload["decisions"][0]  # type: ignore[index]
    row["source_inventory"]["key"] = "badbadbadbadbad1"  # type: ignore[index]
    path = tmp_path / "bad.yaml"
    _write_decision_file(path, payload)

    with pytest.raises(SourceInventoryError, match="does not match"):
        decisions.validate_committed_decision_files([path])


def test_decision_validator_requires_approved_gloss(tmp_path: Path) -> None:
    payload = _minimal_payload()
    row = payload["decisions"][0]  # type: ignore[index]
    row["approved_gloss"] = ""  # type: ignore[index]
    path = tmp_path / "bad.yaml"
    _write_decision_file(path, payload)

    with pytest.raises(SourceInventoryError, match="approved_gloss"):
        decisions.validate_committed_decision_files([path])


def test_decision_validator_allows_clean_rows_without_flags(tmp_path: Path) -> None:
    payload = _minimal_payload()
    row = payload["decisions"][0]  # type: ignore[index]
    row.pop("review_queue_reasons")  # type: ignore[attr-defined]
    path = tmp_path / "ok.yaml"
    _write_decision_file(path, payload)

    summary = decisions.validate_committed_decision_files([path])

    assert summary["rows"] == 1


def test_decision_validator_allows_general_promotion_batch_size(tmp_path: Path) -> None:
    payload = _minimal_payload()
    source_queue = payload["source_queue"]  # type: ignore[index]
    source_queue.pop("first_promotion_batch_size")  # type: ignore[attr-defined]
    source_queue["promotion_batch_size"] = 1  # type: ignore[index]
    path = tmp_path / "ok.yaml"
    _write_decision_file(path, payload)

    summary = decisions.validate_committed_decision_files([path])

    assert summary["rows"] == 1


def test_decision_validator_discovers_its_staged_inventory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project_root = tmp_path / "project"
    inventory_path = "data/lexicon/source-inventory/curriculum-full-text-intake.json"
    inventory = project_root / inventory_path
    inventory.parent.mkdir(parents=True)
    inventory.write_text(
        json.dumps(
            [
                {
                    "lemma": "кіт",
                    "source_family": "curriculum",
                    "extraction_mode": "module_markdown_token",
                    "source_id": "curriculum-fixture",
                    "source_title": "Fixture curriculum",
                    "source_path": "curriculum/l2-uk-en/a1/fixture/module.md",
                    "source_locator": "curriculum/l2-uk-en/a1/fixture/module.md::module_body",
                    "count": 1,
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    payload = _minimal_payload()
    row = payload["decisions"][0]  # type: ignore[index]
    source_inventory = row["source_inventory"]  # type: ignore[index]
    source_inventory.update(  # type: ignore[union-attr]
        {
            "path": inventory_path,
            "locator": "curriculum/l2-uk-en/a1/fixture/module.md::module_body",
            "source_id": "curriculum-fixture",
            "source_family": "curriculum",
        }
    )
    source_inventory["key"] = decisions.source_inventory_key(  # type: ignore[index]
        lemma="ананас",
        inventory_path=inventory_path,
        locator="curriculum/l2-uk-en/a1/fixture/module.md::module_body",
    )
    row["lemma"] = "кіт"  # type: ignore[index]
    row["approved_gloss"] = "cat"  # type: ignore[index]
    path = tmp_path / "staged-ledger.yaml"
    _write_decision_file(path, payload)
    monkeypatch.setattr(decisions, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(decisions, "SOURCE_INVENTORY_DIR", inventory.parent)
    monkeypatch.setattr(decisions, "COMMITTED_SOURCE_INVENTORIES", ())
    source_inventory["key"] = decisions.source_inventory_key(  # type: ignore[index]
        lemma="кіт",
        inventory_path=inventory_path,
        locator="curriculum/l2-uk-en/a1/fixture/module.md::module_body",
    )
    _write_decision_file(path, payload)

    assert decisions.validate_committed_decision_files([path])["rows"] == 1


def _staged_ledger_in_tmp_project(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    write_inventory: bool,
) -> Path:
    """Write a ledger referencing a staged (regenerable) inventory in an isolated
    project root. When ``write_inventory`` is False the referenced JSON is absent,
    mirroring the gitignored Ohoiko corpus intake on a fresh clone / CI (#4223)."""

    project_root = tmp_path / "project"
    inventory_path = "data/lexicon/source-inventory/ohoiko-corpus-intake.json"
    inventory = project_root / inventory_path
    inventory.parent.mkdir(parents=True)
    if write_inventory:
        inventory.write_text(
            json.dumps(
                [
                    {
                        "lemma": "кіт",
                        "source_family": "ohoiko",
                        "extraction_mode": "content_token",
                        "source_id": "ohoiko-fixture",
                        "source_title": "Fixture Ohoiko",
                        "source_path": None,
                        "source_locator": "ohoiko-book-001::entry-0001",
                        "count": 1,
                    }
                ],
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
    locator = "ohoiko-book-001::entry-0001"
    payload = _minimal_payload()
    row = payload["decisions"][0]  # type: ignore[index]
    row["lemma"] = "кіт"  # type: ignore[index]
    row["approved_gloss"] = "cat"  # type: ignore[index]
    row["source_inventory"].update(  # type: ignore[union-attr]
        {
            "path": inventory_path,
            "locator": locator,
            "source_id": "ohoiko-fixture",
            "source_family": "ohoiko",
            "key": decisions.source_inventory_key(
                lemma="кіт", inventory_path=inventory_path, locator=locator
            ),
        }
    )
    monkeypatch.setattr(decisions, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(decisions, "SOURCE_INVENTORY_DIR", inventory.parent)
    monkeypatch.setattr(decisions, "COMMITTED_SOURCE_INVENTORIES", ())
    path = tmp_path / "staged-ledger.yaml"
    _write_decision_file(path, payload)
    return path


def test_decision_validator_fails_open_on_absent_regenerable_inventory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # JSON absent (gitignored/regenerable): structural key-hash check still passes.
    path = _staged_ledger_in_tmp_project(tmp_path, monkeypatch, write_inventory=False)
    assert decisions.validate_committed_decision_files([path])["rows"] == 1


def test_decision_validator_full_crosscheck_when_inventory_present(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Same ledger, JSON present: full row cross-check runs and passes.
    path = _staged_ledger_in_tmp_project(tmp_path, monkeypatch, write_inventory=True)
    assert decisions.validate_committed_decision_files([path])["rows"] == 1


def test_decision_validator_does_not_mutate_supplied_source_index(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _staged_ledger_in_tmp_project(tmp_path, monkeypatch, write_inventory=True)
    source_index: dict[tuple[str, str, str], SourceInventoryRecord] = {}

    assert decisions.validate_decision_file(path, source_index=source_index)["rows"] == 1
    assert source_index == {}


def test_decision_validator_absent_inventory_still_rejects_bad_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Fail-open does NOT bypass structural integrity: a tampered key is still caught
    # even when the regenerable inventory is absent.
    path = _staged_ledger_in_tmp_project(tmp_path, monkeypatch, write_inventory=False)
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["decisions"][0]["source_inventory"]["key"] = "deadbeefdeadbeef"
    _write_decision_file(path, payload)
    with pytest.raises(SourceInventoryError, match="does not match"):
        decisions.validate_committed_decision_files([path])


def test_decision_validator_requires_committed_inventory_present(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A COMMITTED inventory (not the regenerable staged one) staying strict: if it is
    # absent from disk, validation still hard-errors — fail-open is staged-only.
    path = _staged_ledger_in_tmp_project(tmp_path, monkeypatch, write_inventory=False)
    missing = decisions.SOURCE_INVENTORY_DIR / "committed-but-missing.yaml"
    monkeypatch.setattr(decisions, "COMMITTED_SOURCE_INVENTORIES", (missing,))
    with pytest.raises(SourceInventoryError, match="not found"):
        decisions.validate_committed_decision_files([path])


def test_committed_ohoiko_batch_ledgers_validate() -> None:
    # The real committed per-batch Ohoiko ledgers validate with the regenerable
    # inventory JSON absent (its normal state in git).
    batch = sorted(
        decisions.DEFAULT_DECISION_DIR.glob(
            "2026-07-14-ohoiko-corpus-intake-batch-*.yaml"
        )
    )
    assert len(batch) == 21
    summary = decisions.validate_committed_decision_files(batch)
    assert summary["rows"] == 20848
    assert summary["decision_counts"] == {
        "approve_for_publish": 50,
        "needs_more_evidence": 16237,
        "reject": 4561,
    }


def test_decision_validator_rejects_missing_promotion_batch_size(tmp_path: Path) -> None:
    payload = _minimal_payload()
    source_queue = payload["source_queue"]  # type: ignore[index]
    source_queue.pop("first_promotion_batch_size")  # type: ignore[attr-defined]
    path = tmp_path / "bad.yaml"
    _write_decision_file(path, payload)

    with pytest.raises(SourceInventoryError, match="promotion batch size"):
        decisions.validate_committed_decision_files([path])


def test_decision_validator_rejects_duplicate_promotion_batch_size(tmp_path: Path) -> None:
    payload = _minimal_payload()
    source_queue = payload["source_queue"]  # type: ignore[index]
    source_queue["promotion_batch_size"] = 1  # type: ignore[index]
    path = tmp_path / "bad.yaml"
    _write_decision_file(path, payload)

    with pytest.raises(SourceInventoryError, match="promotion batch size"):
        decisions.validate_committed_decision_files([path])


def test_decision_validator_rejects_duplicate_source_key(tmp_path: Path) -> None:
    payload = _minimal_payload()
    payload["decisions"].append(dict(payload["decisions"][0]))  # type: ignore[index, union-attr]
    path = tmp_path / "bad.yaml"
    _write_decision_file(path, payload)

    with pytest.raises(SourceInventoryError, match=r"duplicate source_inventory\.key"):
        decisions.validate_committed_decision_files([path])


def test_decision_validator_rejects_production_outputs(tmp_path: Path) -> None:
    payload = _minimal_payload()
    payload["production_outputs_updated"] = ["site/src/data/lexicon-manifest.json"]
    path = tmp_path / "bad.yaml"
    _write_decision_file(path, payload)

    with pytest.raises(SourceInventoryError, match=r"production_outputs_updated must be \[\]"):
        decisions.validate_committed_decision_files([path])



def test_decision_accepts_surface_admission_mapping(tmp_path: Path) -> None:
    payload = _minimal_payload()
    payload["decisions"][0]["surface_admission"] = {"daily": False, "practice": True, "cloze": False}
    path = tmp_path / "surface.yaml"
    _write_decision_file(path, payload)

    summary = decisions.validate_committed_decision_files([path])

    assert summary["rows"] == 1


def test_decision_rejects_invalid_surface_admission(tmp_path: Path) -> None:
    payload = _minimal_payload()
    payload["decisions"][0]["surface_admission"] = {"practice": "yes"}
    path = tmp_path / "bad-surface.yaml"
    _write_decision_file(path, payload)

    with pytest.raises(SourceInventoryError, match=r"surface_admission\.practice must be boolean"):
        decisions.validate_committed_decision_files([path])


def test_wrong_kind_document_fails_on_kind_not_field_noise(tmp_path):
    """A non-decision document (e.g. a grow triage ledger, #4888) dropped
    into the decisions directory must fail on `kind` — the actionable error
    pointing at the directory contract — not on a wall of unknown-field
    noise. Regression pin for the 2026-07-10 red-main incident."""
    payload = {
        "version": 1,
        "kind": "atlas_grow_automerge_triage_ledger",
        "batch_id": "grow-ledger-fixture",
        "provenance": {"input_file": "/tmp/fixture.json"},
        "decision_counts": {"approve": 1},
    }
    path = tmp_path / "2026-07-10-fixture-ledger.yaml"
    _write_decision_file(path, payload)
    with pytest.raises(SourceInventoryError, match=r"kind"):
        decisions.validate_decision_file(path)
