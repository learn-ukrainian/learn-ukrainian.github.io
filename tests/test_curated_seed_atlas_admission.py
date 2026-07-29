"""Curated v5 admission uses public Atlas facts rather than invented CEFR."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.lexicon import curated_seed_atlas_admission as admission


def _manifest(path: Path, entries: list[dict[str, object]]) -> Path:
    path.write_text(json.dumps({"entries": entries}, ensure_ascii=False), encoding="utf-8")
    return path


def test_candidates_keep_explicit_verb_expression_type(tmp_path: Path, monkeypatch) -> None:
    manifest = _manifest(
        tmp_path / "manifest.json",
        [{"lemma": "відомий", "url_slug": "відомий", "pos": "adj"}],
    )
    monkeypatch.setattr(admission, "_vesum_pos", lambda word: "verb" if word == "виходити" else None)

    candidates = admission.candidates_for_manifest(
        [{"lemma": "виходити з ладу", "gloss": "to break down"}], manifest
    )

    assert candidates["auto_merge"] == [
        {
            "lemma": "виходити з ладу",
            "gloss": "to break down",
            "pos": None,
            "entry_type": "expression",
            "primary_source": "curated_v5_seed",
        }
    ]


def test_candidates_do_not_duplicate_an_existing_apostrophe_variant_route(tmp_path: Path) -> None:
    manifest = _manifest(
        tmp_path / "manifest.json",
        [{"lemma": "з'ясувати", "url_slug": "з-ясувати", "pos": "verb"}],
    )

    candidates = admission.candidates_for_manifest(
        [{"lemma": "з’ясувати", "gloss": "to find out", "slug": "з-ясувати"}], manifest
    )

    assert candidates == {"auto_merge": [], "needs_review": []}


def test_normalize_rows_projects_private_v5_input_to_replayable_schema() -> None:
    rows = admission.normalize_rows(
        [
            {
                "row": 7,
                "ua": "Вийти з ладу",
                "en": "to break down",
                "sentence": "Пристрій вийшов з ладу.",
                "sentence_status": "ok",
                "provenance": {"source_file": "ukrlib-example", "credit": "Автор"},
                "private_source_path": ".claude/atlas-epic/plans/private/seed.jsonl",
            }
        ]
    )

    assert rows == [
        {
            "seedRow": 7,
            "lemma": "вийти з ладу",
            "gloss": "to break down",
            "slug": "вийти-з-ладу",
            "sentenceStatus": "ok",
            "example": "Пристрій вийшов з ладу.",
            "provenance": {"source_file": "ukrlib-example", "credit": "Автор"},
        }
    ]


def test_fill_missing_manifest_glosses_updates_only_explicit_blank_targets() -> None:
    manifest = {
        "entries": [
            {"lemma": "Лоток", "gloss": None},
            {"lemma": "опік", "gloss": "Burn"},
            {"lemma": "інші", "gloss": None},
        ]
    }
    result = admission.fill_missing_manifest_glosses(
        [
            {"lemma": "лоток", "gloss": "Food container / Tray"},
            {"lemma": "опік", "gloss": "Burn"},
            {"lemma": "інші", "gloss": "Other"},
        ],
        manifest,
        ["ЛОТОК", "опік"],
    )

    assert result.applied == ("Лоток",)
    assert result.skipped_existing == ("опік",)
    assert manifest["entries"] == [
        {"lemma": "Лоток", "gloss": "Food container / Tray"},
        {"lemma": "опік", "gloss": "Burn"},
        {"lemma": "інші", "gloss": None},
    ]


def test_fill_missing_manifest_glosses_strips_terminal_aspect_note() -> None:
    manifest = {"entries": [{"lemma": "доглянути", "gloss": ""}]}

    result = admission.fill_missing_manifest_glosses(
        [{"lemma": "Доглянути", "gloss": "To look after / care for (perf)"}],
        manifest,
        ["доглянути"],
    )

    assert result.applied == ("доглянути",)
    assert manifest["entries"][0]["gloss"] == "To look after / care for"


def test_fill_missing_manifest_glosses_rejects_missing_target_seed() -> None:
    manifest = {"entries": [{"lemma": "лоток", "gloss": None}]}

    with pytest.raises(ValueError, match="missing from curated seed"):
        admission.fill_missing_manifest_glosses([], manifest, ["лоток"])


def test_fill_missing_manifest_pos_uses_vesum_for_explicit_blank_target(monkeypatch) -> None:
    manifest = {
        "entries": [
            {"lemma": "помішувати", "pos": None},
            {"lemma": "обставини", "pos": "noun:pl"},
        ]
    }
    monkeypatch.setattr(admission, "_vesum_pos", lambda lemma: "verb" if lemma == "помішувати" else None)

    result = admission.fill_missing_manifest_pos(manifest, ["помішувати"])

    assert result == admission.PosFillResult(applied=("помішувати",), skipped_existing=())
    assert manifest["entries"][0]["pos"] == "verb"
    assert manifest["entries"][1]["pos"] == "noun:pl"


def test_fill_missing_manifest_pos_preserves_existing_pos(monkeypatch) -> None:
    manifest = {"entries": [{"lemma": "обставини", "pos": "noun:pl"}]}
    monkeypatch.setattr(admission, "_vesum_pos", lambda lemma: pytest.fail(f"unexpected VESUM lookup: {lemma}"))

    result = admission.fill_missing_manifest_pos(manifest, ["обставини"])

    assert result == admission.PosFillResult(applied=(), skipped_existing=("обставини",))


def test_fill_missing_manifest_pos_rejects_unverified_target(monkeypatch) -> None:
    manifest = {"entries": [{"lemma": "помішувати", "pos": None}]}
    monkeypatch.setattr(admission, "_vesum_pos", lambda lemma: None)

    with pytest.raises(ValueError, match="no VESUM POS"):
        admission.fill_missing_manifest_pos(manifest, ["помішувати"])


def test_main_fills_pos_without_input_seed(tmp_path: Path, monkeypatch) -> None:
    manifest_path = _manifest(
        tmp_path / "manifest.json",
        [{"lemma": "помішувати", "pos": None}],
    )
    monkeypatch.setattr(admission, "_vesum_pos", lambda lemma: "verb" if lemma == "помішувати" else None)

    result = admission.main(
        [
            "--manifest",
            str(manifest_path),
            "--fill-existing-pos",
            "--target-lemma",
            "помішувати",
            "--write",
        ]
    )

    assert result == 0
    persisted = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert persisted["entries"][0]["pos"] == "verb"


def test_main_persists_gloss_fill_before_later_pos_fill_failure(tmp_path: Path, monkeypatch) -> None:
    input_path = tmp_path / "seed.jsonl"
    input_path.write_text(
        "\n".join(
            (
                json.dumps({"lemma": "лоток", "gloss": "tray"}),
                json.dumps({"lemma": "невідоме", "gloss": "unknown"}),
            )
        )
        + "\n",
        encoding="utf-8",
    )
    manifest_path = _manifest(
        tmp_path / "manifest.json",
        [
            {"lemma": "лоток", "gloss": None, "pos": "noun"},
            {"lemma": "невідоме", "gloss": "unknown", "pos": None},
        ],
    )
    monkeypatch.setattr(admission, "_vesum_pos", lambda lemma: None)

    with pytest.raises(ValueError, match="target lemma has no VESUM POS: невідоме"):
        admission.main(
            [
                "--input",
                str(input_path),
                "--manifest",
                str(manifest_path),
                "--fill-existing-glosses",
                "--fill-existing-pos",
                "--target-lemma",
                "лоток",
                "--target-lemma",
                "невідоме",
                "--write",
            ]
        )

    persisted = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert persisted["entries"][0]["gloss"] == "tray"


def test_write_json_uses_shared_atomic_write_helper(tmp_path: Path, monkeypatch) -> None:
    output = tmp_path / "nested" / "seed.json"
    observed: dict[str, object] = {}

    def write_atomically(path: Path, content: bytes) -> None:
        observed["path"] = path
        observed["content"] = content

    monkeypatch.setattr(admission, "_write_atomically", write_atomically)

    admission._write_json(output, {"lemma": "відомий"})

    assert observed == {
        "path": output,
        "content": b'{\n  "lemma": "\xd0\xb2\xd1\x96\xd0\xb4\xd0\xbe\xd0\xbc\xd0\xb8\xd0\xb9"\n}\n',
    }


def test_practice_seed_reports_no_hit_and_retains_duplicate_attestations(tmp_path: Path) -> None:
    manifest = _manifest(
        tmp_path / "manifest.json",
        [
            {"lemma": "відомий", "url_slug": "відомий", "pos": "adj", "enrichment": {"cefr": {"level": "A2", "source": "PULS"}}},
            {"lemma": "рідкісний", "url_slug": "рідкісний", "pos": "adj", "enrichment": {"cefr": {"level": "B2", "source": "PULS"}}},
            {"lemma": "неоцінений", "url_slug": "неоцінений", "pos": "adj"},
        ],
    )
    provenance = {"source_file": "ukrlib-example", "credit": "Автор"}
    rows = [
        {"seedRow": 1, "lemma": "відомий", "sentenceStatus": "ok", "example": "Відомий приклад.", "provenance": provenance},
        {"seedRow": 2, "lemma": "відомий", "sentenceStatus": "ok", "example": "Другий приклад.", "provenance": provenance},
        {"seedRow": 3, "lemma": "рідкісний", "sentenceStatus": "no_hit"},
        {"seedRow": 4, "lemma": "неоцінений", "sentenceStatus": "ok", "example": "Неоцінений приклад.", "provenance": provenance},
    ]

    seed, report = admission.prepare_practice_seed(rows, manifest)

    assert len(seed["entries"]) == 2
    assert report["counts"] == {
        "active_seed_rows": 4,
        "unique_seed_lemmas": 3,
        "public_atlas_rows": 4,
        "atlas_failures": 0,
        "sentence_status": {"no_hit": 1, "ok": 3},
        "practice_admitted_rows": 2,
        "practice_skipped_no_cefr": 1,
        "practice_cefr_sources": {"PULS": 2},
    }
    assert report["practice_skipped_no_cefr"] == [{"seedRow": 4, "lemma": "неоцінений"}]
