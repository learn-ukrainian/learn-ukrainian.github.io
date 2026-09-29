from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.audit.generate_practice_deck import BuildConfig, JsonVesumVerifier, _select_practice_lexemes
from scripts.audit.lexeme_filter import is_practice_eligible, practice_ineligibility_reason
from scripts.audit.measure_curated_membership import measure_membership
from scripts.lexicon.curated_membership import apply_membership, build_membership, read_membership

ROOT = Path(__file__).resolve().parents[1]
MEMBERSHIP = ROOT / "site/src/data/lexicon-teacher-curated-membership.json"
PENDING = ROOT / "registry/lexicon/curated-membership-pending-admission-9151.json"
REVIEW = ROOT / "registry/lexicon/curated-membership-reconciliation-9151.json"
PENDING_SCHEMA = ROOT / "schemas/curated-membership-pending-admission-9151.schema.json"


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
    homework = tmp_path / "homework.jsonl"
    homework.write_text(
        json.dumps(
            {
                "seedRow": 1,
                "lemma": "слово",
                "gloss": "word",
                "sentenceStatus": "has_candidates",
                "admission": {"practice": True, "mode": "local_practice_private_teacher"},
                "vesumAttestation": {"attested": True},
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    teacher = tmp_path / "teacher.json"
    _write_json(
        teacher,
        {
            "cloze": [
                {"lemmaId": "слово", "sentence": "Never read this."},
                {"lemmaId": "книга", "options": [{"label": "Never read this either."}]},
                {"lemmaId": "(чайний) сервіз", "lemma": "сервіз"},
            ]
        },
    )
    manifest = tmp_path / "manifest.json"
    _write_json(
        manifest,
        {
            "entries": [
                {"lemma": "слово", "url_slug": "слово", "gloss": "word", "cefr": "A1"},
                {"lemma": "книга", "url_slug": "книга", "gloss": "book", "cefr": "A1"},
                {"lemma": "сервіз", "url_slug": "сервіз", "gloss": "service", "cefr": "A2"},
            ]
        },
    )
    return homework, teacher, manifest


def test_build_membership_uses_only_exact_inventory_keys_and_no_teacher_prose(tmp_path: Path) -> None:
    homework, teacher, manifest = _inputs(tmp_path)

    payload, report = build_membership(
        homework_seed_path=homework,
        teacher_inventory_path=teacher,
        manifest_path=manifest,
    )

    assert [member["slug"] for member in payload["members"]] == ["книга", "слово"]
    assert report["teacher_inventory"]["unique_keys"] == 3
    assert report["teacher_inventory"]["resolved_keys"] == 2
    assert "Never read this" not in json.dumps(payload, ensure_ascii=False)


def test_apply_membership_unlocks_practice_but_not_cloze() -> None:
    entries = [
        {
            "lemma": "слово",
            "url_slug": "слово",
            "gloss": "word",
            "cefr": "A1",
            "primary_source": "source_inventory_grow",
            "surface_admission": {"cloze": False},
        }
    ]

    merged, report = apply_membership(
        entries,
        [{"lemma": "слово", "slug": "слово", "sources": ["homework"]}],
    )

    assert report == {"members": 1, "resolved": 1}
    assert merged[0]["curated_membership"] is True
    assert merged[0]["surface_admission"] == {"cloze": False, "practice": True}
    assert is_practice_eligible(merged[0]) is True
    assert practice_ineligibility_reason(merged[0]) is None


def test_apply_membership_rejects_missing_atlas_route() -> None:
    with pytest.raises(ValueError, match="unresolved Atlas route"):
        apply_membership([], [{"lemma": "слово", "slug": "слово", "sources": ["homework"]}])


def test_pending_admission_is_recorded_outside_fail_closed_membership() -> None:
    pending = json.loads(PENDING.read_text(encoding="utf-8"))
    schema = json.loads(PENDING_SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(pending)
    reviewed = json.loads(REVIEW.read_text(encoding="utf-8"))["rows"]
    members = read_membership(MEMBERSHIP)
    pending_by_slug = {row["slug"]: row for row in pending["members"]}
    member_slugs = {row["slug"] for row in members}

    assert len(pending_by_slug) == len(pending["members"]) == 64
    assert member_slugs.isdisjoint(pending_by_slug)
    assert {row["slug"] for row in reviewed} == pending_by_slug.keys()
    assert all(
        pending_by_slug[row["slug"]]["decision"] == row["decision"]
        and pending_by_slug[row["slug"]]["lemma"] == row["lemma"]
        and pending_by_slug[row["slug"]]["sources"] == row["source"]
        for row in reviewed
    )
    assert Counter(row["pending_reason"] for row in pending["members"]) == {
        "no_allowed_english_anchor": 22,
        "no_reviewed_source_locator": 25,
        "admissible_pending_publication": 16,
        "removed_dialectal": 1,
    }
    no_anchor = {
        "бджолярство",
        "валер'янка",
        "вебсайт",
        "вигуляти",
        "вкритися",
        "впакувати",
        "вполювати",
        "деталька",
        "закладений",
        "кріпатура",
        "наживати",
        "нажити",
        "непопулярний",
        "нищівний",
        "озвучка",
        "поплатитися",
        "постригтися",
        "пукнути",
        "розпоряджатися",
        "сплюндрований",
        "строчити",
        "чізкейк",
    }
    assert {
        row["lemma"] for row in pending["members"] if row["pending_reason"] == "no_allowed_english_anchor"
    } == no_anchor
    assert {
        row["slug"]
        for row in reviewed
        if row["decision"] == "ADMIT" and row["promotion_input"]["source_locator"] is None
    } == {row["slug"] for row in pending["members"] if row["pending_reason"] == "no_reviewed_source_locator"}
    assert pending_by_slug["запинитися"]["pending_reason"] == "removed_dialectal"

    # A pending route has no Atlas entry in this fixture and is not applied.
    held = pending_by_slug["вифлеєм"]
    assert held["decision"] == "ADMIT"
    assert held["slug"] not in member_slugs
    active = members[0]
    merged, report = apply_membership([{"lemma": active["lemma"], "url_slug": active["slug"]}], [active])
    assert [row["url_slug"] for row in merged] == [active["slug"]]
    assert report == {"members": 1, "resolved": 1}

    # A missing route from neither list is still rejected by the unchanged gate.
    unknown = {"lemma": "невідома", "slug": "невідома", "sources": ["teacher_inventory"]}
    assert unknown["slug"] not in (pending_by_slug.keys() | member_slugs)
    with pytest.raises(ValueError, match="1 unresolved Atlas route"):
        apply_membership([], [unknown])


def test_membership_entries_are_selected_before_the_general_practice_pool() -> None:
    entries = [
        {
            "lemma": "книга",
            "url_slug": "книга",
            "gloss": "book",
            "cefr": "A1",
            "primary_source": "source_inventory_grow",
            "surface_admission": {"cloze": False},
        },
        {
            "lemma": "школа",
            "url_slug": "школа",
            "gloss": "school",
            "cefr": "A1",
            "course_usage": [{"module": "fixture"}],
        },
    ]
    merged, _report = apply_membership(
        entries,
        [{"lemma": "книга", "slug": "книга", "sources": ["teacher_inventory"]}],
    )

    selected, _lexemes, _by_plain_lemma, _by_id = _select_practice_lexemes(
        merged,
        JsonVesumVerifier.from_path(Path("tests/fixtures/lexicon-practice-vesum.json")),
        BuildConfig(target=1, source_label="fixture"),
    )

    assert [entry["url_slug"] for entry, _lexeme in selected] == ["книга"]


def test_measurement_reports_union_floor_and_recognition_modes(tmp_path: Path) -> None:
    homework, teacher, manifest = _inputs(tmp_path)
    membership_payload, _report = build_membership(
        homework_seed_path=homework,
        teacher_inventory_path=teacher,
        manifest_path=manifest,
    )
    membership = tmp_path / "membership.json"
    _write_json(membership, membership_payload)
    practice_dir = tmp_path / "practice"
    practice_dir.mkdir()
    _write_json(
        practice_dir / "practice-index.A1.json",
        {
            "items": [
                {"lemmaId": "слово", "cefr": "A1", "modes": ["flashcards", "matching", "choice"]},
                {"lemmaId": "книга", "cefr": "A1", "modes": ["flashcards", "matching"]},
            ]
        },
    )

    measured = measure_membership(
        homework_seed_path=homework,
        teacher_inventory_path=teacher,
        manifest_path=manifest,
        membership_path=membership,
        practice_dir=practice_dir,
    )

    assert read_membership(membership)[0]["slug"] == "книга"
    assert measured["homework"]["missing_from_curated_keys"] == 0
    assert measured["homework"]["missing_from_practice_indexes"] == 0
    assert measured["teacher_inventory"] == {
        "cards": 3,
        "unique_keys": 3,
        "resolved_membership_routes": 2,
    }
    assert measured["recognition_mode_eligibility"]["A1"] == {
        "lexemes": 2,
        "flashcards": 2,
        "matching": 2,
        "choice": 1,
    }
