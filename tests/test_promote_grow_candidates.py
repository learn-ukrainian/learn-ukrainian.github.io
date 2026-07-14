from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
import yaml

from scripts.lexicon import promote_grow_candidates as promote


def test_manifest_entry_from_candidate_is_schema_conformant() -> None:
    candidate = _candidate(
        lemma="мама",
        source_context={
            "track": "a1",
            "module_num": 1,
            "slug": "hello",
            "context": "content_mdx",
        },
    )

    entry = promote.manifest_entry_from_candidate(candidate)

    assert entry["lemma"] == "мама"
    assert entry["url_slug"] == "мама"
    assert entry["gloss"] == "mother"
    assert entry["pos"] == "noun"
    assert entry["primary_source"] == promote.PRIMARY_SOURCE
    assert entry["course_usage"] == [
        {
            "track": "a1",
            "module_num": 1,
            "slug": "hello",
            "context": "content_mdx",
        }
    ]
    assert entry["heritage_status"] == candidate["heritage_status"]
    assert entry["enrichment"] == candidate["enrichment"]


def test_manifest_entry_retains_source_inventory_provenance() -> None:
    provenance = [
        {
            "source_id": "ulp-001",
            "source_title": "ULP Lesson 1",
            "source_locator": "p.12",
            "context": "lesson headword",
        }
    ]
    candidate = _candidate(lemma="риба", source_provenance=provenance)

    entry = promote.manifest_entry_from_candidate(candidate)

    assert entry["source_provenance"] == provenance
    # Provenance is distinct from course_usage; a source-inventory candidate
    # without source_context/source_contexts still yields empty course usage.
    assert entry["course_usage"] == []


def test_manifest_entry_preserves_source_inventory_primary_source() -> None:
    entry = promote.manifest_entry_from_candidate(
        _candidate(lemma="ананас", primary_source="source_inventory_grow")
    )

    assert entry["primary_source"] == "source_inventory_grow"


def test_manifest_entry_prefers_curated_candidate_gloss_over_meaning() -> None:
    entry = promote.manifest_entry_from_candidate(
        _candidate(
            lemma="ананас",
            gloss="pineapple",
            enrichment={
                "meaning": {
                    "definitions": [{"text": "dictionary definition should not win"}]
                }
            },
        )
    )

    assert entry["gloss"] == "pineapple"


def test_manifest_entry_omits_provenance_when_candidate_has_none() -> None:
    entry = promote.manifest_entry_from_candidate(_candidate(lemma="кіт"))

    assert "source_provenance" not in entry


def test_write_promotes_candidate_in_sorted_order_and_updates_stats(tmp_path: Path) -> None:
    manifest_path = _write_manifest(tmp_path, [_entry("авто"), _entry("якір")])
    candidates_path = _write_candidates(tmp_path, [_candidate("мама")], [])
    needs_review_path = tmp_path / "grow_needs_review.json"
    fingerprint_path = tmp_path / "lexicon-manifest.fingerprint.json"

    result = promote.promote_grow_candidates(
        candidates_path=candidates_path,
        manifest_path=manifest_path,
        needs_review_path=needs_review_path,
        fingerprint_path=fingerprint_path,
        write=True,
        self_check=lambda _path: 0,
        fingerprint_writer=_fingerprint_writer,
    )

    manifest = _read_json(manifest_path)
    assert [entry["lemma"] for entry in manifest["entries"]] == ["авто", "мама", "якір"]
    assert manifest["generated_at"] != "2026-06-22T00:00:00+00:00"
    assert str(manifest["generated_at"]).endswith("+00:00")
    assert manifest["stats"]["lemmas_total"] == 3
    assert manifest["stats"]["enriched_count"] == 3
    assert manifest["enrichment_generated"] is True
    assert result.promoted == ("мама",)
    assert result.manifest_written is True
    assert result.fingerprint_written is True
    assert result.needs_review_written is True
    assert _read_json(needs_review_path) == []
    assert _read_json(fingerprint_path) == {"fingerprint": "fixture"}


def test_promotion_embeds_matching_manifest_fingerprint(tmp_path: Path) -> None:
    # publish_manifest.py rejects a manifest whose embedded fingerprint does not
    # match the sidecar; promotion must re-stamp it from the canonical builder.
    manifest_path = _write_manifest(tmp_path, [_entry("авто")])
    candidates_path = _write_candidates(tmp_path, [_candidate("мама")], [])

    promote.promote_grow_candidates(
        candidates_path=candidates_path,
        manifest_path=manifest_path,
        needs_review_path=tmp_path / "grow_needs_review.json",
        fingerprint_path=tmp_path / "lexicon-manifest.fingerprint.json",
        write=True,
        self_check=lambda _path: 0,
        fingerprint_writer=_fingerprint_writer,
    )

    embedded = _read_json(manifest_path)["manifest_fingerprint"]
    expected = promote.build_fingerprint(promote.PROJECT_ROOT)
    assert embedded == {
        "schema_version": expected["schema_version"],
        "fingerprint": expected["fingerprint"],
    }


def test_second_run_is_idempotent(tmp_path: Path) -> None:
    manifest_path = _write_manifest(tmp_path, [_entry("авто"), _entry("якір")])
    candidates_path = _write_candidates(tmp_path, [_candidate("мама")], [])
    needs_review_path = tmp_path / "grow_needs_review.json"
    fingerprint_path = tmp_path / "lexicon-manifest.fingerprint.json"

    first = promote.promote_grow_candidates(
        candidates_path=candidates_path,
        manifest_path=manifest_path,
        needs_review_path=needs_review_path,
        fingerprint_path=fingerprint_path,
        write=True,
        self_check=lambda _path: 0,
        fingerprint_writer=_fingerprint_writer,
    )
    after_first = manifest_path.read_text(encoding="utf-8")
    second = promote.promote_grow_candidates(
        candidates_path=candidates_path,
        manifest_path=manifest_path,
        needs_review_path=needs_review_path,
        fingerprint_path=fingerprint_path,
        write=True,
        self_check=lambda _path: 0,
        fingerprint_writer=_fingerprint_writer,
    )

    assert first.promoted == ("мама",)
    assert second.promoted == ()
    assert second.skipped_existing == ("мама",)
    assert second.manifest_written is False
    assert second.fingerprint_written is False
    assert manifest_path.read_text(encoding="utf-8") == after_first


def test_existing_lemma_is_skipped_case_insensitively(tmp_path: Path) -> None:
    manifest_path = _write_manifest(tmp_path, [_entry("Мама")])
    candidates_path = _write_candidates(tmp_path, [_candidate("мама")], [])
    needs_review_path = tmp_path / "grow_needs_review.json"

    result = promote.promote_grow_candidates(
        candidates_path=candidates_path,
        manifest_path=manifest_path,
        needs_review_path=needs_review_path,
        write=True,
        self_check=lambda _path: 0,
        fingerprint_writer=_fingerprint_writer,
    )

    manifest = _read_json(manifest_path)
    assert [entry["lemma"] for entry in manifest["entries"]] == ["Мама"]
    assert result.promoted == ()
    assert result.skipped_existing == ("мама",)
    assert result.manifest_written is False
    assert _read_json(needs_review_path) == []


def test_needs_review_is_reported_but_never_promoted(tmp_path: Path) -> None:
    manifest_path = _write_manifest(tmp_path, [_entry("авто")])
    held = [{"entry": _candidate("сумнів"), "reason": "missing dictionary definition"}]
    candidates_path = _write_candidates(tmp_path, [], held)
    needs_review_path = tmp_path / "grow_needs_review.json"

    result = promote.promote_grow_candidates(
        candidates_path=candidates_path,
        manifest_path=manifest_path,
        needs_review_path=needs_review_path,
        write=True,
        self_check=lambda _path: 0,
        fingerprint_writer=_fingerprint_writer,
    )

    assert [entry["lemma"] for entry in _read_json(manifest_path)["entries"]] == ["авто"]
    assert result.promoted == ()
    assert result.held == (promote.HeldLemma("сумнів", "missing dictionary definition"),)
    assert _read_json(needs_review_path) == [
        {"lemma": "сумнів", "reason": "missing dictionary definition"}
    ]
    report = promote.format_summary(result, report=True)
    assert "- сумнів: missing dictionary definition" in report


def test_approval_ledger_promotes_only_explicit_approvals(tmp_path: Path) -> None:
    manifest_path = _write_manifest(tmp_path, [_entry("авто")])
    candidates_path = _write_candidates(tmp_path, [_candidate("мама"), _candidate("тато")], [])
    approval_ledger = _write_approval_ledger(
        candidates_path,
        [
            {"lemma": "мама", "pos": "noun", "decision": "approve"},
            {"lemma": "тато", "pos": "noun", "decision": "deferred"},
        ],
    )

    result = promote.promote_grow_candidates(
        candidates_path=candidates_path,
        manifest_path=manifest_path,
        needs_review_path=tmp_path / "grow_needs_review.json",
        fingerprint_path=tmp_path / "lexicon-manifest.fingerprint.json",
        approval_ledger_path=approval_ledger,
        write=True,
        self_check=lambda _path: 0,
        fingerprint_writer=_fingerprint_writer,
    )

    assert [entry["lemma"] for entry in _read_json(manifest_path)["entries"]] == ["авто", "мама"]
    assert result.promoted == ("мама",)


def test_approval_ledger_fails_closed_when_candidate_is_unlisted(tmp_path: Path) -> None:
    candidates_path = _write_candidates(tmp_path, [_candidate("мама"), _candidate("тато")], [])
    approval_ledger = _write_approval_ledger(
        candidates_path,
        [{"lemma": "мама", "pos": "noun", "decision": "approve"}],
    )

    with pytest.raises(ValueError, match="does not exactly cover"):
        promote.promote_grow_candidates(
            candidates_path=candidates_path,
            manifest_path=_write_manifest(tmp_path, [_entry("авто")]),
            approval_ledger_path=approval_ledger,
            self_check=lambda _path: 0,
            fingerprint_writer=_fingerprint_writer,
        )


def test_approval_ledger_fails_closed_when_candidate_bytes_change(tmp_path: Path) -> None:
    candidates_path = _write_candidates(tmp_path, [_candidate("мама")], [])
    approval_ledger = _write_approval_ledger(
        candidates_path,
        [{"lemma": "мама", "pos": "noun", "decision": "approve"}],
    )
    candidates_path.write_text(candidates_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="SHA-256"):
        promote.promote_grow_candidates(
            candidates_path=candidates_path,
            manifest_path=_write_manifest(tmp_path, [_entry("авто")]),
            approval_ledger_path=approval_ledger,
            self_check=lambda _path: 0,
            fingerprint_writer=_fingerprint_writer,
        )


def test_cached_anchor_fill_runs_only_for_newly_promoted_entries(tmp_path: Path, monkeypatch) -> None:
    manifest_path = _write_manifest(tmp_path, [_entry("авто")])
    candidates_path = _write_candidates(tmp_path, [_candidate("мама")], [])
    monkeypatch.setattr(promote, "_slovnyk_cache_path", lambda _lemma: tmp_path / "cache.json")
    monkeypatch.setattr(promote, "_load_slovnyk_cache_file", lambda _path: {"text": "mother"})

    def fill(entry: dict[str, object], lemma: str, _cache: object) -> bool:
        entry.setdefault("enrichment", {})["translation"] = {"en": ["mother"]}
        return lemma == "мама"

    monkeypatch.setattr(promote, "_fill_learner_english_anchor_from_slovnyk_cache", fill)

    result = promote.promote_grow_candidates(
        candidates_path=candidates_path,
        manifest_path=manifest_path,
        needs_review_path=tmp_path / "grow_needs_review.json",
        fingerprint_path=tmp_path / "lexicon-manifest.fingerprint.json",
        write=True,
        self_check=lambda _path: 0,
        fingerprint_writer=_fingerprint_writer,
    )

    assert result.cached_anchor_fills == ("мама",)
    assert result.anchorless_promoted == ()


def test_gate_failure_aborts_without_writing(tmp_path: Path, monkeypatch) -> None:
    manifest_path = _write_manifest(tmp_path, [_entry("авто")])
    before = manifest_path.read_text(encoding="utf-8")
    candidates_path = _write_candidates(tmp_path, [_candidate("мама")], [])
    needs_review_path = tmp_path / "grow_needs_review.json"
    fingerprint_path = tmp_path / "lexicon-manifest.fingerprint.json"
    monkeypatch.setattr(promote, "verify_prospective_manifest", lambda _path: 2)

    code = promote.main(
        [
            "--candidates",
            str(candidates_path),
            "--manifest",
            str(manifest_path),
            "--needs-review",
            str(needs_review_path),
            "--fingerprint",
            str(fingerprint_path),
            "--write",
        ]
    )

    assert code != 0
    assert manifest_path.read_text(encoding="utf-8") == before
    assert not needs_review_path.exists()
    assert not fingerprint_path.exists()


def test_dry_run_writes_nothing(tmp_path: Path) -> None:
    manifest_path = _write_manifest(tmp_path, [_entry("авто")])
    before = manifest_path.read_text(encoding="utf-8")
    candidates_path = _write_candidates(tmp_path, [_candidate("мама")], [])
    needs_review_path = tmp_path / "grow_needs_review.json"
    fingerprint_path = tmp_path / "lexicon-manifest.fingerprint.json"

    result = promote.promote_grow_candidates(
        candidates_path=candidates_path,
        manifest_path=manifest_path,
        needs_review_path=needs_review_path,
        fingerprint_path=fingerprint_path,
        write=False,
        self_check=lambda _path: 2,
        fingerprint_writer=_fingerprint_writer,
    )

    assert result.promoted == ("мама",)
    assert result.dry_run is True
    assert result.manifest_written is False
    assert manifest_path.read_text(encoding="utf-8") == before
    assert not needs_review_path.exists()
    assert not fingerprint_path.exists()


def test_missing_candidates_file_is_clean_noop(tmp_path: Path) -> None:
    result = promote.promote_grow_candidates(
        candidates_path=tmp_path / "missing.json",
        manifest_path=tmp_path / "unused-manifest.json",
        write=True,
        self_check=lambda _path: 2,
        fingerprint_writer=_fingerprint_writer,
    )

    assert result.candidates_found is False
    assert result.promoted == ()
    assert "no candidates file" in promote.format_summary(result)


def _candidate(lemma: str = "мама", **overrides: object) -> dict[str, object]:
    candidate: dict[str, object] = {
        "lemma": lemma,
        "pos": "noun",
        "heritage_status": {
            "classification": "standard",
            "attestations": [],
            "is_russianism": False,
            "russian_shadow": False,
            "calque_warning": None,
        },
        "enrichment": {
            "meaning": {
                "definitions": ["mother"],
                "source": "fixture",
            },
            "sources": ["fixture"],
        },
    }
    candidate.update(overrides)
    return candidate


def _entry(lemma: str) -> dict[str, object]:
    return {
        "lemma": lemma,
        "url_slug": lemma.casefold(),
        "gloss": lemma,
        "pos": "noun",
        "ipa": None,
        "primary_source": "built_vocabulary",
        "course_usage": [],
        "heritage_status": {
            "classification": "standard",
            "attestations": [],
            "is_russianism": False,
            "russian_shadow": False,
            "calque_warning": None,
        },
        "enrichment": {
            "meaning": {
                "definitions": [lemma],
                "source": "fixture",
            },
            "sources": ["fixture"],
        },
    }


def _write_manifest(tmp_path: Path, entries: list[dict[str, object]]) -> Path:
    path = tmp_path / "lexicon-manifest.json"
    payload = {
        "version": "0.1",
        "generated_at": "2026-06-22T00:00:00+00:00",
        "stats": {
            "lemmas_total": len(entries),
            "enriched_count": sum(1 for entry in entries if entry.get("enrichment")),
        },
        "modules": [],
        "seed_groups": [],
        "entries": entries,
        "enrichment_generated": True,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _write_candidates(tmp_path: Path, auto_merge: list[dict[str, object]], needs_review: list[dict[str, object]]) -> Path:
    path = tmp_path / "grow_candidates.json"
    payload = {
        "counts": {
            "total_delta": len(auto_merge) + len(needs_review),
            "processed": len(auto_merge) + len(needs_review),
            "auto_merge": len(auto_merge),
            "needs_review": len(needs_review),
        },
        "auto_merge": auto_merge,
        "needs_review": needs_review,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _write_approval_ledger(candidates_path: Path, decisions: list[dict[str, str]]) -> Path:
    path = candidates_path.with_name("grow-promotion-ledger.yaml")
    payload = {
        "version": 1,
        "kind": promote.APPROVAL_LEDGER_KIND,
        "provenance": {
            "candidates_sha256": hashlib.sha256(candidates_path.read_bytes()).hexdigest(),
        },
        "decisions": decisions,
    }
    path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return path


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _fingerprint_writer(path: Path) -> None:
    path.write_text('{"fingerprint": "fixture"}\n', encoding="utf-8")
