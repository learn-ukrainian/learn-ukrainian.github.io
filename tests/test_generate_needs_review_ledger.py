"""Tests for needs_review re-entry ledger generation + promotion (#5230)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
import yaml

from scripts.lexicon import generate_needs_review_ledger as gen
from scripts.lexicon import promote_grow_candidates as promote


def test_cli_refuses_without_write_or_dry_run() -> None:
    with pytest.raises(SystemExit) as exc:
        gen.main([])
    assert exc.value.code == 2


def test_generator_round_trip_maps_actions(tmp_path: Path) -> None:
    candidates_path, triage_path = _write_fixture_pair(tmp_path)
    out = tmp_path / "ledger.yaml"

    result = gen.generate_needs_review_ledger(
        candidates_path=candidates_path,
        triage_path=triage_path,
        out_path=out,
        write=True,
        reviewed_at="2026-07-18",
    )

    assert result.written is True
    assert result.approve_count == 1
    assert result.deferred_count == 2
    assert result.heritage_count == 1
    assert result.total == 3
    assert out.exists()

    payload = yaml.safe_load(out.read_text(encoding="utf-8"))
    assert payload["kind"] == promote.NEEDS_REVIEW_LEDGER_KIND
    assert payload["provenance"]["candidates_sha256"] == hashlib.sha256(
        candidates_path.read_bytes()
    ).hexdigest()
    assert payload["provenance"]["triage_sha256"] == hashlib.sha256(
        triage_path.read_bytes()
    ).hexdigest()

    by_lemma = {row["lemma"]: row for row in payload["decisions"]}
    assert by_lemma["хата"]["decision"] == "approve"
    assert by_lemma["хата"]["approved_gloss"] == {
        "text": "house; home",
        "source": "dmklinger",
        "lemma": "хата",
        "slug": "хата",
    }
    assert by_lemma["абонплата"]["decision"] == "deferred"
    assert by_lemma["абонплата"]["reason"] == "truly_missing"
    assert by_lemma["верф"]["decision"] == "deferred"
    assert by_lemma["верф"]["heritage"] is True
    assert by_lemma["верф"]["reason"] == "heritage_flag"

    # Round-trip: re-read path is loadable by promote helpers.
    rows = promote.parse_ledger_decision_rows(
        payload["decisions"],
        label="needs-review ledger",
    )
    assert set(rows) == {
        promote._candidate_decision_key({"lemma": "хата", "pos": "noun"}),
        promote._candidate_decision_key({"lemma": "абонплата", "pos": "noun"}),
        promote._candidate_decision_key({"lemma": "верф", "pos": "noun"}),
    }


def test_generator_fails_on_coverage_mismatch(tmp_path: Path) -> None:
    candidates_path, triage_path = _write_fixture_pair(tmp_path)
    triage = json.loads(triage_path.read_text(encoding="utf-8"))
    triage["entries"] = triage["entries"][:1]
    triage_path.write_text(json.dumps(triage, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="does not exactly cover"):
        gen.generate_needs_review_ledger(
            candidates_path=candidates_path,
            triage_path=triage_path,
            out_path=tmp_path / "ledger.yaml",
            write=False,
        )


def test_promote_needs_review_ledger_promotes_only_approve_with_gloss(tmp_path: Path) -> None:
    candidates_path, triage_path = _write_fixture_pair(tmp_path)
    ledger_path = tmp_path / "nr-ledger.yaml"
    gen.generate_needs_review_ledger(
        candidates_path=candidates_path,
        triage_path=triage_path,
        out_path=ledger_path,
        write=True,
        reviewed_at="2026-07-18",
    )

    manifest_path = _write_manifest(tmp_path, [_entry("авто")])
    result = promote.promote_grow_candidates(
        candidates_path=candidates_path,
        manifest_path=manifest_path,
        needs_review_path=tmp_path / "grow_needs_review.json",
        fingerprint_path=tmp_path / "lexicon-manifest.fingerprint.json",
        needs_review_ledger_path=ledger_path,
        write=True,
        self_check=lambda _path: 0,
        fingerprint_writer=_fingerprint_writer,
    )

    lemmas = [entry["lemma"] for entry in _read_json(manifest_path)["entries"]]
    assert lemmas == ["авто", "хата"]
    assert result.promoted == ("хата",)
    assert result.needs_review_approved == 1
    assert result.needs_review_deferred == 2
    assert {item.lemma for item in result.held} == {"абонплата", "верф"}

    promoted = next(e for e in _read_json(manifest_path)["entries"] if e["lemma"] == "хата")
    assert promoted["gloss"] == "house; home"
    assert promoted["enrichment"]["meaning"]["definitions"] == ["house; home"]
    assert promoted["enrichment"]["translation"]["en"] == ["house; home"]
    assert "dmklinger" in promoted["enrichment"]["sources"]


def test_promote_needs_review_deferred_and_heritage_never_promoted(tmp_path: Path) -> None:
    candidates_path, triage_path = _write_fixture_pair(tmp_path)
    # Force only deferred/heritage actions.
    triage = json.loads(triage_path.read_text(encoding="utf-8"))
    for row in triage["entries"]:
        if row["machine_action"] == "promote_with_gloss":
            row["machine_action"] = "truly_missing"
            row["best_gloss"] = None
    triage_path.write_text(json.dumps(triage, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ledger_path = tmp_path / "nr-ledger.yaml"
    gen.generate_needs_review_ledger(
        candidates_path=candidates_path,
        triage_path=triage_path,
        out_path=ledger_path,
        write=True,
    )

    manifest_path = _write_manifest(tmp_path, [_entry("авто")])
    result = promote.promote_grow_candidates(
        candidates_path=candidates_path,
        manifest_path=manifest_path,
        needs_review_path=tmp_path / "grow_needs_review.json",
        fingerprint_path=tmp_path / "fp.json",
        needs_review_ledger_path=ledger_path,
        write=True,
        self_check=lambda _path: 0,
        fingerprint_writer=_fingerprint_writer,
    )

    assert result.promoted == ()
    assert result.needs_review_approved == 0
    assert result.needs_review_deferred == 3
    assert [e["lemma"] for e in _read_json(manifest_path)["entries"]] == ["авто"]


def test_promote_needs_review_fails_on_candidates_sha_mismatch(tmp_path: Path) -> None:
    candidates_path, triage_path = _write_fixture_pair(tmp_path)
    ledger_path = tmp_path / "nr-ledger.yaml"
    gen.generate_needs_review_ledger(
        candidates_path=candidates_path,
        triage_path=triage_path,
        out_path=ledger_path,
        write=True,
    )
    candidates_path.write_text(candidates_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="candidates_sha256"):
        promote.promote_grow_candidates(
            candidates_path=candidates_path,
            manifest_path=_write_manifest(tmp_path, [_entry("авто")]),
            needs_review_ledger_path=ledger_path,
            self_check=lambda _path: 0,
            fingerprint_writer=_fingerprint_writer,
        )


def test_promote_needs_review_fails_on_coverage_mismatch(tmp_path: Path) -> None:
    candidates_path, triage_path = _write_fixture_pair(tmp_path)
    ledger_path = tmp_path / "nr-ledger.yaml"
    gen.generate_needs_review_ledger(
        candidates_path=candidates_path,
        triage_path=triage_path,
        out_path=ledger_path,
        write=True,
    )
    payload = yaml.safe_load(ledger_path.read_text(encoding="utf-8"))
    payload["decisions"] = payload["decisions"][:1]
    # Keep sha valid so coverage is the failure mode under test.
    payload["provenance"]["candidates_sha256"] = hashlib.sha256(
        candidates_path.read_bytes()
    ).hexdigest()
    ledger_path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")

    with pytest.raises(ValueError, match="does not exactly cover"):
        promote.promote_grow_candidates(
            candidates_path=candidates_path,
            manifest_path=_write_manifest(tmp_path, [_entry("авто")]),
            needs_review_ledger_path=ledger_path,
            self_check=lambda _path: 0,
            fingerprint_writer=_fingerprint_writer,
        )


def test_promote_needs_review_fails_when_triage_sha_missing(tmp_path: Path) -> None:
    candidates_path, triage_path = _write_fixture_pair(tmp_path)
    ledger_path = tmp_path / "nr-ledger.yaml"
    gen.generate_needs_review_ledger(
        candidates_path=candidates_path,
        triage_path=triage_path,
        out_path=ledger_path,
        write=True,
    )
    payload = yaml.safe_load(ledger_path.read_text(encoding="utf-8"))
    del payload["provenance"]["triage_sha256"]
    ledger_path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")

    with pytest.raises(ValueError, match="triage_sha256"):
        promote.promote_grow_candidates(
            candidates_path=candidates_path,
            manifest_path=_write_manifest(tmp_path, [_entry("авто")]),
            needs_review_ledger_path=ledger_path,
            self_check=lambda _path: 0,
            fingerprint_writer=_fingerprint_writer,
        )


def test_inject_approved_gloss_sets_anchor_fields() -> None:
    candidate = {
        "lemma": "хата",
        "pos": "noun",
        "enrichment": {"sources": ["VESUM"], "cefr": {"level": "A1"}},
    }
    injected = promote.inject_approved_gloss(
        candidate,
        {"text": "house", "source": "sum11", "lemma": "хата", "slug": "хата"},
    )
    assert injected["gloss"] == "house"
    assert injected["enrichment"]["meaning"]["definitions"] == ["house"]
    assert injected["enrichment"]["meaning"]["source"] == "sum11"
    assert injected["enrichment"]["translation"]["en"] == ["house"]
    assert "sum11" in injected["enrichment"]["sources"]
    assert injected["enrichment"]["cefr"] == {"level": "A1"}


def test_inject_approved_gloss_refuses_russian_cyrillic_definition() -> None:
    candidate = {"lemma": "а-а-а", "pos": "interjection", "url_slug": "а-а-а"}
    with pytest.raises(ValueError, match="learner English"):
        promote.inject_approved_gloss(
            candidate,
            {
                "text": "Колыбельный припев: бай-бай!",
                "source": "grinchenko",
                "lemma": "а-а-а",
            },
        )


def test_inject_approved_gloss_refuses_sum11_stub() -> None:
    candidate = {"lemma": "атакуючи", "pos": "adverb", "url_slug": "атакуючи"}
    with pytest.raises(ValueError, match="СУМ-11 stub"):
        promote.inject_approved_gloss(
            candidate,
            {
                "text": "Дієпр. акт. теп. ч. до атакува́ти",
                "source": "sum11",
                "lemma": "атакуючи",
            },
        )


def test_inject_approved_gloss_refuses_lemma_mismatch() -> None:
    candidate = {"lemma": "багатити", "pos": "verb", "url_slug": "багатити"}
    with pytest.raises(ValueError, match="lemma/slug"):
        promote.inject_approved_gloss(
            candidate,
            {
                "text": "to enrich; to make wealthy",
                "source": "grinchenko",
                "lemma": "багатитися",
                "slug": "багатитися",
            },
        )


def test_inject_approved_gloss_allows_dictionary_style_english_note() -> None:
    candidate = {"lemma": "баль", "pos": "noun", "url_slug": "баль"}
    note = (
        "historical spelling of бал ('ball, dance'); older orthography note"
    )
    injected = promote.inject_approved_gloss(
        candidate,
        {"text": note, "source": "wiktionary", "lemma": "баль", "slug": "баль"},
    )
    assert injected["gloss"] == note
    assert injected["enrichment"]["translation"]["en"] == [note]


def test_generator_defers_non_injectable_promote_with_gloss(tmp_path: Path) -> None:
    held = [
        {
            "entry": _candidate("а-а-а", enrichment={"sources": ["VESUM"]}),
            "reason": "missing dictionary definition",
        }
    ]
    candidates_path = _write_candidates(tmp_path, [], held)
    triage_path = tmp_path / "triage.json"
    triage_path.write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "lemma": "а-а-а",
                        "pos": "noun",
                        "held_reason": "missing dictionary definition",
                        "best_gloss": {
                            "text": "Колыбельный припев: бай-бай!",
                            "source": "grinchenko",
                            "lemma": "а-а-а",
                        },
                        "machine_action": "promote_with_gloss",
                    }
                ]
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    result = gen.generate_needs_review_ledger(
        candidates_path=candidates_path,
        triage_path=triage_path,
        out_path=tmp_path / "ledger.yaml",
        write=True,
    )
    assert result.approve_count == 0
    assert result.deferred_count == 1
    payload = yaml.safe_load((tmp_path / "ledger.yaml").read_text(encoding="utf-8"))
    assert payload["decisions"][0]["decision"] == "deferred"
    assert payload["decisions"][0]["reason"] == "non_english_gloss"


def test_needs_review_and_auto_merge_ledgers_compose(tmp_path: Path) -> None:
    auto = _candidate("мама")
    held = [
        {
            "entry": _candidate("хата", enrichment={"sources": ["fixture"]}),
            "reason": "missing dictionary definition",
        }
    ]
    candidates_path = _write_candidates(tmp_path, [auto], held)
    triage_path = tmp_path / "triage.json"
    triage_path.write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "lemma": "хата",
                        "pos": "noun",
                        "held_reason": "missing dictionary definition",
                        "best_gloss": {"text": "house", "source": "sum11"},
                        "machine_action": "promote_with_gloss",
                    }
                ]
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    nr_ledger = tmp_path / "nr.yaml"
    gen.generate_needs_review_ledger(
        candidates_path=candidates_path,
        triage_path=triage_path,
        out_path=nr_ledger,
        write=True,
    )
    approval = tmp_path / "auto.yaml"
    approval.write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "kind": promote.APPROVAL_LEDGER_KIND,
                "provenance": {
                    "candidates_sha256": hashlib.sha256(candidates_path.read_bytes()).hexdigest(),
                },
                "decisions": [
                    {"lemma": "мама", "pos": "noun", "decision": "approve"},
                ],
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    result = promote.promote_grow_candidates(
        candidates_path=candidates_path,
        manifest_path=_write_manifest(tmp_path, [_entry("авто")]),
        needs_review_path=tmp_path / "held.json",
        fingerprint_path=tmp_path / "fp.json",
        approval_ledger_path=approval,
        needs_review_ledger_path=nr_ledger,
        write=True,
        self_check=lambda _path: 0,
        fingerprint_writer=_fingerprint_writer,
    )

    assert set(result.promoted) == {"мама", "хата"}
    assert result.needs_review_approved == 1
    assert result.needs_review_deferred == 0


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _write_fixture_pair(tmp_path: Path) -> tuple[Path, Path]:
    held = [
        {
            "entry": _candidate("хата", enrichment={"sources": ["VESUM"]}),
            "reason": "missing dictionary definition",
        },
        {
            "entry": _candidate("абонплата", enrichment={"sources": ["VESUM"]}),
            "reason": "missing dictionary definition",
        },
        {
            "entry": _candidate(
                "верф",
                enrichment={"sources": ["VESUM"]},
                heritage_status={
                    "classification": "russianism",
                    "is_russianism": True,
                    "russian_shadow": False,
                    "calque_warning": "calque",
                },
            ),
            "reason": "heritage_status flags russianism; heritage_status flags calque_warning",
        },
    ]
    candidates_path = _write_candidates(tmp_path, [], held)
    triage_path = tmp_path / "needs-review-triage.json"
    triage_path.write_text(
        json.dumps(
            {
                "generated_by": "scripts/lexicon/triage_needs_review.py",
                "counts": {"total": 3},
                "entries": [
                    {
                        "lemma": "хата",
                        "pos": "noun",
                        "held_reason": "missing dictionary definition",
                        "best_gloss": {"text": "house; home", "source": "dmklinger"},
                        "machine_action": "promote_with_gloss",
                    },
                    {
                        "lemma": "абонплата",
                        "pos": "noun",
                        "held_reason": "missing dictionary definition",
                        "best_gloss": None,
                        "machine_action": "truly_missing",
                    },
                    {
                        "lemma": "верф",
                        "pos": "noun",
                        "held_reason": (
                            "heritage_status flags russianism; heritage_status flags calque_warning"
                        ),
                        "best_gloss": {"text": "shipyard", "source": "sum11"},
                        "machine_action": "heritage_flag",
                    },
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return candidates_path, triage_path


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
            "meaning": {"definitions": [lemma], "source": "fixture"},
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


def _write_candidates(
    tmp_path: Path,
    auto_merge: list[dict[str, object]],
    needs_review: list[dict[str, object]],
) -> Path:
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


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _fingerprint_writer(path: Path) -> None:
    path.write_text('{"fingerprint": "fixture"}\n', encoding="utf-8")
