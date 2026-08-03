"""Contract tests for Phase 2 complements with mandatory locator binding."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Callable
from copy import deepcopy
from pathlib import Path

import pytest

from scripts.projects.open_model_data import document_signal_manifest as signals
from scripts.projects.open_model_data import source_capability_complements as complements

ROOT = Path(__file__).resolve().parents[1]
ASSETS = {
    "literary": "db.literary_texts",
    "public_textbooks": "db.textbooks.public",
    "external_articles": "db.external_articles",
    "wikipedia": "db.wikipedia",
}


def _write(path: Path, value: object) -> None:
    path.write_text(signals.canonical_json(value) + "\n", encoding="utf-8")


def _phase1(tmp_path: Path, families: tuple[str, ...] = ("wikipedia",)) -> tuple[Path, Path, list[dict]]:
    sources, admissions, receipt_families = [], [], []
    for _number, family in enumerate(families):
        database = tmp_path / f"{family}.db"
        with sqlite3.connect(database) as connection:
            connection.execute(
                "CREATE TABLE documents (id INTEGER PRIMARY KEY, source TEXT, work TEXT, text TEXT, period TEXT, genre TEXT, register TEXT)"
            )
            connection.executemany(
                "INSERT INTO documents(source, work, text, period, genre, register) VALUES (?, ?, ?, ?, ?, ?)",
                [
                    (f"{family}-a", f"{family}-one", "SENTINEL SOURCE TEXT", "modern", "article", "neutral"),
                    (f"{family}-a", f"{family}-two", "SECOND SENTINEL", "modern", "article", "neutral"),
                ],
            )
        sources.append(
            {
                "source_family": family,
                "inventory_asset_id": ASSETS[family],
                "evidence": {
                    "rights_status": "accepted",
                    "permitted_use": "local",
                    "origin_status": "known",
                    "contamination_status": "not_checked",
                },
                "expected": {"rows": 2},
                "adapter": {
                    "database": database.name,
                    "table": "documents",
                    "id_column": "id",
                    "text_column": "text",
                    "locator_column": "id",
                    "dimensions": {
                        "period": {"column": "period"},
                        "genre": {"column": "genre"},
                        "register": {"column": "register"},
                        "origin": {"constant": "human_authored_source"},
                    },
                },
            }
        )
        admissions.append(
            {
                "source_family": family,
                "source_group_column": "source",
                "work_group_column": "work",
                "evidence": {
                    "provenance": "accepted",
                    "rights": "accepted",
                    "origin": "known",
                    "contamination": "not_checked",
                    "acquisition": "accepted",
                    "snapshot": "accepted",
                },
            }
        )
        receipt_families.append(
            {"source_family": family, "actual": {"rows": 2}, "dispositions": {"unresolved": {"rows": 2}}}
        )
    for name, value in (
        ("profile.json", {"sources": sources}),
        ("admission.json", {"families": admissions}),
        (
            "admission-receipt.json",
            {"coverage": {"complete": True}, "training_eligible_emitted": False, "families": receipt_families},
        ),
        (
            "config.json",
            {
                "schema_version": "document_signal_config_v1",
                "manifest_id": "phase2-fixture",
                "profile_config": "profile.json",
                "admission_config": "admission.json",
                "admission_receipt": "admission-receipt.json",
            },
        ),
    ):
        _write(tmp_path / name, value)
    manifest, receipt = tmp_path / "phase1.jsonl", tmp_path / "phase1-receipt.json"
    signals.build_manifest(
        config_path=tmp_path / "config.json", input_root=tmp_path, manifest_output=manifest, receipt_output=receipt
    )
    return manifest, receipt, [json.loads(line) for line in manifest.read_text().splitlines()]


def _locator(path: Path, rows: list[dict]) -> Path:
    locator_rows = []
    for row in rows:
        family = row["source_family"]
        locator = {
            "schema_version": "source_work_locator_v1",
            "locator_id": "locator." + hashlib.sha256((row["source_id"] + row["work_id"]).encode()).hexdigest()[:24],
            "source_family": family,
            "inventory_asset_id": row["inventory_asset_id"],
            "source_id": row["source_id"],
            "work_id": row["work_id"],
            "affected_records": 1,
        }
        if family == "literary":
            locator.update(
                {
                    "source_locator": {"source_file": "fixture-literary"},
                    "work_locator": {"work_id": row["work_id"]},
                    "canonical_url": "https://example.test/literary",
                    "metadata": {"title": "Literary fixture", "author": "Author", "year": "1900"},
                    "metadata_publication": {
                        "title": "public_metadata",
                        "author": "public_metadata",
                        "year": "public_metadata",
                    },
                    "missing_evidence_keys": [],
                }
            )
        elif family == "public_textbooks":
            locator.update(
                {
                    "source_locator": {"source_file": "fixture-textbook"},
                    "work_locator": {"title": row["work_id"]},
                    "canonical_url": None,
                    "metadata": {
                        "title": "Textbook fixture",
                        "author": "Author",
                        "author_uk": "Автор",
                        "grade": "7",
                        "subject": "history",
                    },
                    "metadata_publication": {
                        "title": "public_metadata",
                        "author": "public_metadata",
                        "author_uk": "public_metadata",
                        "grade": "public_metadata",
                        "subject": "public_metadata",
                    },
                    "missing_evidence_keys": ["canonical_source_url"],
                }
            )
        elif family == "external_articles":
            locator.update(
                {
                    "source_locator": {"source_file": "fixture-external"},
                    "work_locator": {
                        "url_normalized": "https://example.test/external",
                        "url": "https://example.test/external",
                    },
                    "canonical_url": "https://example.test/external",
                    "metadata": {
                        "title": "External fixture",
                        "speaker": "Speaker",
                        "domain": "example.test",
                        "publish_date": "2026-01-01",
                        "channel_id": "channel",
                    },
                    "metadata_publication": {
                        "title": "public_metadata",
                        "speaker": "public_metadata",
                        "domain": "public_metadata",
                        "publish_date": "public_metadata",
                        "channel_id": "public_metadata",
                    },
                    "missing_evidence_keys": [],
                }
            )
        else:
            locator.update(
                {
                    "source_locator": {"fetched_at": "2026-01-01T00:00:00Z"},
                    "work_locator": {"title": row["work_id"]},
                    "canonical_url": "https://example.test/wiki",
                    "metadata": {"title": "Wiki fixture"},
                    "metadata_publication": {"title": "public_metadata"},
                    "missing_evidence_keys": [],
                }
            )
        locator_rows.append(locator)
    locator_rows.sort(
        key=lambda value: (
            value["source_family"],
            value["source_id"],
            value["work_id"],
            signals.canonical_json(value["source_locator"]),
        )
    )
    path.write_text("".join(signals.canonical_json(value) + "\n" for value in locator_rows), encoding="utf-8")
    return path


def _policy(tmp_path: Path, mutate: Callable[[dict], None] | None = None) -> Path:
    value = json.loads((ROOT / "data/projects/open_model_data/evidence/source_capability_policy_v1.json").read_text())
    if mutate is not None:
        mutate(value)
    _write(tmp_path / "policy.json", value)
    return tmp_path / "policy.json"


def _build(
    tmp_path: Path,
    families: tuple[str, ...] = ("wikipedia",),
    policy_mutate: Callable[[dict], None] | None = None,
) -> tuple[Path, Path, Path, Path, list[dict]]:
    manifest, phase1_receipt, rows = _phase1(tmp_path, families)
    locator = _locator(tmp_path / "locators.jsonl", rows)
    complement, worklist, receipt = (
        tmp_path / "complement.jsonl",
        tmp_path / "worklist.jsonl",
        tmp_path / "receipt.json",
    )
    complements.build(
        phase1_manifest=manifest,
        phase1_receipt=phase1_receipt,
        policy_path=_policy(tmp_path, policy_mutate),
        locator_index=locator,
        complement_output=complement,
        worklist_output=worklist,
        receipt_output=receipt,
    )
    return complement, worklist, receipt, locator, rows


def test_build_binds_every_row_and_worklist_to_locator(tmp_path: Path) -> None:
    complement, worklist, receipt, locator, rows = _build(tmp_path)
    built = [json.loads(line) for line in complement.read_text().splitlines()]
    work = [json.loads(line) for line in worklist.read_text().splitlines()]
    body = complement.read_text() + worklist.read_text() + receipt.read_text()
    assert len(built) == len(rows) == 2
    assert all(
        row["locator_binding"]["locator_index_sha256"] == hashlib.sha256(locator.read_bytes()).hexdigest()
        for row in built
    )
    assert all(item["locator_references"] for item in work)
    assert "SENTINEL SOURCE TEXT" not in body and "SECOND SENTINEL" not in body
    assert (
        json.loads(receipt.read_text())["inputs"]["locator_index"]["sha256"]
        == hashlib.sha256(locator.read_bytes()).hexdigest()
    )


def test_verify_rebuilds_locator_bound_bundle(tmp_path: Path) -> None:
    complement, worklist, receipt, locator, _rows = _build(tmp_path)
    assert complements.verify(
        policy_path=_policy(tmp_path),
        phase1_manifest=tmp_path / "phase1.jsonl",
        phase1_receipt=tmp_path / "phase1-receipt.json",
        locator_index=locator,
        complement=complement,
        worklist=worklist,
        receipt=receipt,
    )


@pytest.mark.parametrize("mutation", ["reorder", "duplicate", "missing", "extra", "family", "inventory"])
def test_build_rejects_locator_mapping_drift(tmp_path: Path, mutation: str) -> None:
    manifest, phase1_receipt, rows = _phase1(tmp_path)
    locator = _locator(tmp_path / "locators.jsonl", rows)
    values = [json.loads(line) for line in locator.read_text().splitlines()]
    if mutation == "reorder":
        values.reverse()
    elif mutation == "duplicate":
        values.append(values[0])
    elif mutation == "missing":
        values.pop()
    elif mutation == "extra":
        extra = dict(values[0])
        extra["work_id"] = "work.wikipedia." + "0" * 24
        extra["locator_id"] = "locator." + "1" * 24
        values.append(extra)
    elif mutation == "family":
        values[0]["source_family"] = "literary"
    elif mutation == "inventory":
        values[0]["inventory_asset_id"] = "wrong.asset"
    locator.write_text("".join(signals.canonical_json(value) + "\n" for value in values), encoding="utf-8")
    with pytest.raises(complements.ComplementError):
        complements.build(
            phase1_manifest=manifest,
            phase1_receipt=phase1_receipt,
            policy_path=_policy(tmp_path),
            locator_index=locator,
            complement_output=tmp_path / "out.jsonl",
            worklist_output=tmp_path / "work.jsonl",
            receipt_output=tmp_path / "out.json",
        )


@pytest.mark.parametrize("target", ["complement", "worklist", "receipt", "locator"])
def test_verify_rejects_tampered_binding(tmp_path: Path, target: str) -> None:
    complement, worklist, receipt, locator, _rows = _build(tmp_path)
    path = {"complement": complement, "worklist": worklist, "receipt": receipt, "locator": locator}[target]
    path.write_bytes(path.read_bytes() + b"{}\n")
    with pytest.raises(complements.ComplementError):
        complements.verify(
            policy_path=_policy(tmp_path),
            phase1_manifest=tmp_path / "phase1.jsonl",
            phase1_receipt=tmp_path / "phase1-receipt.json",
            locator_index=locator,
            complement=complement,
            worklist=worklist,
            receipt=receipt,
        )


def test_filter_remains_faithful_and_text_free(tmp_path: Path) -> None:
    complement, _worklist, _receipt, _locator_path, _rows = _build(tmp_path)
    found = list(complements.filter_rows(complement, "local_model_learning", "evidenced", "candidate", True))
    assert found and all("SENTINEL SOURCE TEXT" not in value for value in found)


def test_complement_schema_requires_locator_binding(tmp_path: Path) -> None:
    complement, _worklist, _receipt, _locator_path, _rows = _build(tmp_path)
    value = json.loads(complement.read_text().splitlines()[0])
    value.pop("locator_binding")
    with pytest.raises(complements.ComplementError, match="schema failure"):
        complements._validate(value, complements._validator(complements.SCHEMAS["complement"]), "row")


def test_bundle_promotion_rollback_preserves_prior_outputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    complement, worklist, receipt, locator, _rows = _build(tmp_path)
    prior = {path: path.read_bytes() for path in (complement, worklist, receipt)}
    original = complements._replace

    def fail(source: Path, target: Path) -> None:
        if target == worklist:
            raise OSError("planned failure")
        original(source, target)

    monkeypatch.setattr(complements, "_replace", fail)
    with pytest.raises(complements.ComplementError, match="prior outputs restored"):
        complements.build(
            phase1_manifest=tmp_path / "phase1.jsonl",
            phase1_receipt=tmp_path / "phase1-receipt.json",
            policy_path=_policy(tmp_path),
            locator_index=locator,
            complement_output=complement,
            worklist_output=worklist,
            receipt_output=receipt,
        )
    assert {path: path.read_bytes() for path in prior} == prior


def test_integrated_four_family_build_has_exact_locator_grade_and_representation_coverage(tmp_path: Path) -> None:
    families = ("literary", "public_textbooks", "external_articles", "wikipedia")
    complement, _worklist, receipt, _locator_path, _rows = _build(tmp_path, families)
    body = json.loads(receipt.read_text())
    rows = [json.loads(line) for line in complement.read_text().splitlines()]
    assert body["coverage"]["by_family"] == {family: 2 for family in families}
    assert body["coverage"]["locator_by_family"] == {family: 2 for family in families}
    assert body["coverage"]["by_textbook_grade"] == {"7": 2}
    assert body["representation_totals"] == {
        "faithful": {"candidate": 2, "metadata_only": 6},
        "loss_masked": {"not_classified_phase2": 8},
        "protected": {"not_classified_phase2": 8},
    }
    assert {row["source_family"] for row in rows} == set(families)


@pytest.mark.parametrize(
    ("state", "route"),
    [("evidenced", "candidate"), ("unresolved", "metadata_only"), ("blocked", "blocked"), ("excluded", "excluded")],
)
def test_each_policy_state_maps_to_its_independent_route(tmp_path: Path, state: str, route: str) -> None:
    def mutate(policy: dict) -> None:
        decision = {"state": state, "evidence_refs": [], "missing_evidence_keys": ["explicit_license_or_permission"]}
        if state == "evidenced":
            decision = {
                "state": state,
                "evidence_refs": [policy["evidence_catalog"][0]["evidence_id"]],
                "missing_evidence_keys": [],
            }
        next(scope for scope in policy["family_defaults"] if scope["source_family"] == "wikipedia")["decisions"][
            "raw_redistribution"
        ] = decision

    complement, _worklist, _receipt, _locator_path, _rows = _build(tmp_path, policy_mutate=mutate)
    row = json.loads(complement.read_text().splitlines()[0])
    assert row["routes"]["capabilities"]["raw_redistribution"] == route


def test_faithful_requires_both_preparation_and_learning(tmp_path: Path) -> None:
    def mutate(policy: dict) -> None:
        next(scope for scope in policy["family_defaults"] if scope["source_family"] == "wikipedia")["decisions"][
            "local_preparation"
        ] = {"state": "blocked", "evidence_refs": [], "missing_evidence_keys": ["explicit_license_or_permission"]}

    complement, _worklist, _receipt, _locator_path, _rows = _build(tmp_path, policy_mutate=mutate)
    row = json.loads(complement.read_text().splitlines()[0])
    assert row["routes"]["capabilities"]["local_model_learning"] == "candidate"
    assert row["routes"]["representations"]["faithful"] == "metadata_only"


def test_source_override_beats_family_default(tmp_path: Path) -> None:
    manifest, phase1_receipt, rows = _phase1(tmp_path)
    source_id = rows[0]["source_id"]

    def mutate(policy: dict) -> None:
        policy["source_overrides"].append(
            {
                "source_id": source_id,
                "source_family": "wikipedia",
                "scope_id": "scope.override",
                "decisions": {
                    "local_model_learning": {
                        "state": "blocked",
                        "evidence_refs": [],
                        "missing_evidence_keys": ["explicit_license_or_permission"],
                    }
                },
            }
        )

    locator = _locator(tmp_path / "locators.jsonl", rows)
    output = tmp_path / "complement.jsonl"
    complements.build(
        phase1_manifest=manifest,
        phase1_receipt=phase1_receipt,
        policy_path=_policy(tmp_path, mutate),
        locator_index=locator,
        complement_output=output,
        worklist_output=tmp_path / "worklist.jsonl",
        receipt_output=tmp_path / "receipt.json",
    )
    assert all(
        json.loads(line)["routes"]["capabilities"]["local_model_learning"] == "blocked"
        for line in output.read_text().splitlines()
    )


@pytest.mark.parametrize("kind", ["family_mismatch", "unused"])
def test_invalid_source_overrides_fail_closed(tmp_path: Path, kind: str) -> None:
    manifest, phase1_receipt, rows = _phase1(tmp_path)

    def mutate(policy: dict) -> None:
        source_id = rows[0]["source_id"] if kind == "family_mismatch" else "source.wikipedia." + "0" * 24
        policy["source_overrides"].append(
            {
                "source_id": source_id,
                "source_family": "literary" if kind == "family_mismatch" else "wikipedia",
                "scope_id": "scope.invalid",
                "decisions": {
                    "local_preparation": {
                        "state": "blocked",
                        "evidence_refs": [],
                        "missing_evidence_keys": ["explicit_license_or_permission"],
                    }
                },
            }
        )

    with pytest.raises(complements.ComplementError, match=r"family disagrees|does not match"):
        complements.build(
            phase1_manifest=manifest,
            phase1_receipt=phase1_receipt,
            policy_path=_policy(tmp_path, mutate),
            locator_index=_locator(tmp_path / "locators.jsonl", rows),
            complement_output=tmp_path / "out",
            worklist_output=tmp_path / "work",
            receipt_output=tmp_path / "receipt",
        )


@pytest.mark.parametrize(
    "kind", ["evidence", "family", "override", "unknown_ref", "evidenced_missing", "non_evidenced_no_missing"]
)
def test_policy_integrity_failures_are_rejected(tmp_path: Path, kind: str) -> None:
    def mutate(policy: dict) -> None:
        wikipedia = next(scope for scope in policy["family_defaults"] if scope["source_family"] == "wikipedia")
        if kind == "evidence":
            policy["evidence_catalog"].append(deepcopy(policy["evidence_catalog"][0]))
        elif kind == "family":
            policy["family_defaults"].append(deepcopy(wikipedia))
        elif kind == "override":
            override = {
                "source_id": "source.wikipedia." + hashlib.sha256(b"wikipedia-a").hexdigest()[:24],
                "source_family": "wikipedia",
                "scope_id": "scope.duplicate",
                "decisions": {
                    "local_preparation": {
                        "state": "blocked",
                        "evidence_refs": [],
                        "missing_evidence_keys": ["explicit_license_or_permission"],
                    }
                },
            }
            policy["source_overrides"] = [override, deepcopy(override)]
        elif kind == "unknown_ref":
            wikipedia["decisions"]["local_preparation"]["evidence_refs"] = ["evidence.unknown"]
        elif kind == "evidenced_missing":
            wikipedia["decisions"]["local_preparation"] = {
                "state": "evidenced",
                "evidence_refs": [policy["evidence_catalog"][0]["evidence_id"]],
                "missing_evidence_keys": ["explicit_license_or_permission"],
            }
        else:
            wikipedia["decisions"]["local_preparation"] = {
                "state": "blocked",
                "evidence_refs": [],
                "missing_evidence_keys": [],
            }

    with pytest.raises(complements.ComplementError, match=r"duplicate|unknown evidence|requires"):
        _build(tmp_path, policy_mutate=mutate)


def test_phase1_evidence_fields_are_copied_and_text_fingerprints_absent(tmp_path: Path) -> None:
    complement, worklist, receipt, _locator_path, phase1_rows = _build(tmp_path)
    built = json.loads(complement.read_text().splitlines()[0])
    source = phase1_rows[0]
    for field in (
        "dimensions",
        "content_sha256",
        "admission_evidence_state",
        "capability_evidence",
        "signals",
        "exact_duplicate",
        "near_duplicate",
        "heldout_contamination",
    ):
        assert built[field] == source[field]
    output = complement.read_text() + worklist.read_text() + receipt.read_text()
    assert "SENTINEL SOURCE TEXT" not in output and "evaluation_registry" not in output


def test_two_builds_are_byte_identical(tmp_path: Path) -> None:
    first = _build(tmp_path)
    before = [path.read_bytes() for path in first[:3]]
    complements.build(
        phase1_manifest=tmp_path / "phase1.jsonl",
        phase1_receipt=tmp_path / "phase1-receipt.json",
        policy_path=_policy(tmp_path),
        locator_index=first[3],
        complement_output=first[0],
        worklist_output=first[1],
        receipt_output=first[2],
    )
    assert [path.read_bytes() for path in first[:3]] == before


def test_static_phase1_hashes_are_not_recomputed_per_row(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manifest, phase1_receipt, rows = _phase1(tmp_path)
    original, calls = complements.sha256_file, []

    def counted(path: Path) -> str:
        calls.append(path)
        return original(path)

    monkeypatch.setattr(complements, "sha256_file", counted)
    complements.build(
        phase1_manifest=manifest,
        phase1_receipt=phase1_receipt,
        policy_path=_policy(tmp_path),
        locator_index=_locator(tmp_path / "locators.jsonl", rows),
        complement_output=tmp_path / "out",
        worklist_output=tmp_path / "work",
        receipt_output=tmp_path / "receipt",
    )
    assert sum(path == manifest for path in calls) <= 3


@pytest.mark.parametrize("mutation", ["reorder", "truncate", "extra"])
def test_phase1_manifest_drift_is_rejected(tmp_path: Path, mutation: str) -> None:
    manifest, receipt, rows = _phase1(tmp_path)
    lines = manifest.read_text().splitlines()
    if mutation == "reorder":
        lines.reverse()
    elif mutation == "truncate":
        lines.pop()
    else:
        lines.append(lines[0])
    manifest.write_text("\n".join(lines) + "\n")
    with pytest.raises(complements.ComplementError):
        complements.build(
            phase1_manifest=manifest,
            phase1_receipt=receipt,
            policy_path=_policy(tmp_path),
            locator_index=_locator(tmp_path / "locators.jsonl", rows),
            complement_output=tmp_path / "out",
            worklist_output=tmp_path / "work",
            receipt_output=tmp_path / "receipt",
        )


@pytest.mark.parametrize("mutation", ["policy", "schema", "generator"])
def test_verify_rejects_policy_schema_and_generator_binding_drift(
    tmp_path: Path, mutation: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    complement, worklist, receipt, locator, _rows = _build(tmp_path)
    policy = _policy(tmp_path)
    if mutation == "policy":
        value = json.loads(policy.read_text())
        value["context"]["actor_scope"] = "changed"
        _write(policy, value)
    elif mutation == "schema":
        monkeypatch.setattr(
            complements,
            "sha256_file",
            lambda path: (
                "0" * 64 if path.name.startswith("prepared_data") else hashlib.sha256(path.read_bytes()).hexdigest()
            ),
        )
    else:
        monkeypatch.setattr(
            complements,
            "sha256_file",
            lambda path: (
                "0" * 64 if path == Path(complements.__file__) else hashlib.sha256(path.read_bytes()).hexdigest()
            ),
        )
    with pytest.raises(complements.ComplementError):
        complements.verify(
            policy_path=policy,
            phase1_manifest=tmp_path / "phase1.jsonl",
            phase1_receipt=tmp_path / "phase1-receipt.json",
            locator_index=locator,
            complement=complement,
            worklist=worklist,
            receipt=receipt,
        )


def test_worklist_has_exact_decision_evidence_and_locator_references(tmp_path: Path) -> None:
    _complement, worklist, _receipt, locator, _rows = _build(tmp_path)
    locator_rows = [json.loads(line) for line in locator.read_text().splitlines()]
    item = next(
        json.loads(line)
        for line in worklist.read_text().splitlines()
        if line and json.loads(line)["capability"] == "dataset_publication"
    )
    decision = next(
        scope
        for scope in json.loads(_policy(tmp_path).read_text())["family_defaults"]
        if scope["source_family"] == "wikipedia"
    )["decisions"]["dataset_publication"]
    assert (
        item["missing_evidence_keys"] == decision["missing_evidence_keys"]
        and item["evidence_refs"] == decision["evidence_refs"]
    )
    assert {reference["locator_id"] for reference in item["locator_references"]} == {
        row["locator_id"] for row in locator_rows
    }


@pytest.mark.parametrize("affected", [0, 2])
def test_locator_affected_records_under_or_over_count_fails(tmp_path: Path, affected: int) -> None:
    manifest, phase1_receipt, rows = _phase1(tmp_path)
    locator = _locator(tmp_path / "locators.jsonl", rows)
    values = [json.loads(line) for line in locator.read_text().splitlines()]
    values[0]["affected_records"] = affected
    locator.write_text("".join(signals.canonical_json(value) + "\n" for value in values))
    with pytest.raises(complements.ComplementError):
        complements.build(
            phase1_manifest=manifest,
            phase1_receipt=phase1_receipt,
            policy_path=_policy(tmp_path),
            locator_index=locator,
            complement_output=tmp_path / "out",
            worklist_output=tmp_path / "work",
            receipt_output=tmp_path / "receipt",
        )


def test_new_output_promotion_failure_leaves_no_partial_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manifest, phase1_receipt, rows = _phase1(tmp_path)
    original = complements._replace

    def fail(source: Path, target: Path) -> None:
        if target.name == "work":
            raise OSError("planned failure")
        original(source, target)

    monkeypatch.setattr(complements, "_replace", fail)
    with pytest.raises(complements.ComplementError, match="prior outputs restored"):
        complements.build(
            phase1_manifest=manifest,
            phase1_receipt=phase1_receipt,
            policy_path=_policy(tmp_path),
            locator_index=_locator(tmp_path / "locators.jsonl", rows),
            complement_output=tmp_path / "out",
            worklist_output=tmp_path / "work",
            receipt_output=tmp_path / "receipt",
        )
    assert not any((tmp_path / name).exists() for name in ("out", "work", "receipt"))
    assert not list(tmp_path.glob(".*.tmp")) and not list(tmp_path.glob(".*.rollback"))
