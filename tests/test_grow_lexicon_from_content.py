from __future__ import annotations

import inspect
import json
import sqlite3
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace

from scripts.lexicon import enrich_manifest as enrich_manifest_module
from scripts.lexicon import grow_lexicon_from_content as grow
from scripts.lexicon.content_lexicon_reconciler import LemmaExample
from scripts.lexicon.heritage_classifier import classify_lemma

FIXTURE_DB = Path(__file__).resolve().parent / "fixtures" / "heritage_sample.db"
FIXTURE_VESUM_DB = Path(__file__).resolve().parent / "fixtures" / "vesum_sample.db"


def _clean_entry(**overrides: object) -> dict[str, object]:
    entry: dict[str, object] = {
        "lemma": "мама",
        "pos": "noun",
        "heritage_status": {
            "classification": "standard",
            "is_russianism": False,
            "russian_shadow": False,
            "calque_warning": None,
        },
        "enrichment": {
            "meaning": {
                "definitions": ["мати"],
                "source": "fixture",
            }
        },
    }
    entry.update(overrides)
    return entry


def test_split_candidates_gates_dictionary_pos_and_heritage_flags() -> None:
    auto = _clean_entry(lemma="авто")
    no_definition = _clean_entry(lemma="без-дефініції", enrichment={})
    no_pos = _clean_entry(lemma="без-позиції")
    no_pos.pop("pos")
    heritage_flag = _clean_entry(
        lemma="калька",
        heritage_status={
            "classification": "standard",
            "is_russianism": False,
            "russian_shadow": False,
            "curated_calque": {"corrections": ["чинний"]},
        },
    )

    auto_merge, needs_review = grow.split_candidates([auto, no_definition, no_pos, heritage_flag])

    assert auto_merge == [auto]
    assert [item["entry"]["lemma"] for item in needs_review] == [
        "без-дефініції",
        "без-позиції",
        "калька",
    ]
    assert needs_review[0]["reason"] == "missing dictionary definition"
    assert needs_review[1]["reason"] == "unresolved pos"
    assert needs_review[2]["reason"] == "heritage_status flags curated_calque"


def test_build_skeleton_entry_uses_raw_vesum_pos(monkeypatch) -> None:
    def fake_verify_lemma(lemma: str) -> list[dict[str, str]]:
        if lemma == "авантюрний":
            return [{"pos": "adj"}]
        return [{"pos": "noun"}] if lemma == "мама" else []

    monkeypatch.setattr(grow.enrich_manifest, "_base_lemma", lambda lemma: lemma)
    monkeypatch.setattr(grow.enrich_manifest, "verify_lemma", fake_verify_lemma)

    assert grow.build_skeleton_entry("мама") == {"lemma": "мама", "pos": "noun"}
    assert grow.build_skeleton_entry("авантю\u0301рний") == {"lemma": "авантюрний", "pos": "adj"}
    assert grow.build_skeleton_entry("не-знайдено") == {"lemma": "не-знайдено"}


def test_build_skeleton_entry_prefers_non_archaic_exact_pos(monkeypatch) -> None:
    def fake_verify_lemma(lemma: str) -> list[dict[str, str]]:
        assert lemma == "наголос"
        return [
            {"word_form": "наголос", "pos": "adv", "tags": "adv:arch"},
            {"word_form": "наголос", "pos": "noun", "tags": "noun:inanim:m:v_naz"},
        ]

    monkeypatch.setattr(grow.enrich_manifest, "_base_lemma", lambda lemma: lemma)
    monkeypatch.setattr(grow.enrich_manifest, "verify_lemma", fake_verify_lemma)

    assert grow.build_skeleton_entry("наголос") == {"lemma": "наголос", "pos": "noun"}


def test_enrich_entry_attaches_heritage_status_with_fixture_classifier(monkeypatch) -> None:
    _patch_enrich_entry_heavy_helpers(monkeypatch)
    monkeypatch.setattr(
        enrich_manifest_module,
        "classify_lemma",
        lambda lemma: classify_lemma(
            lemma,
            db_path=FIXTURE_DB,
            vesum_db_path=FIXTURE_VESUM_DB,
        ),
    )

    entry = {"lemma": "глагол", "pos": "noun"}
    attached = enrich_manifest_module.enrich_entry(
        entry,
        sqlite3.connect(":memory:"),
        {},
        has_sum11_flags=False,
    )

    assert attached is False
    assert entry["heritage_status"]["classification"] == "authentic-archaism"
    assert entry["heritage_status"]["is_russianism"] is False


def test_generate_candidates_writes_expected_json_shape(tmp_path, monkeypatch) -> None:
    missing = (
        LemmaExample("авто", "авто", tmp_path / "a.mdx"),
        LemmaExample("ревю", "ревю", tmp_path / "b.mdx"),
    )
    result = SimpleNamespace(missing_lemmas=missing)
    out = tmp_path / "grow_candidates.json"

    monkeypatch.setattr(grow, "discover_content_mdx_paths", lambda: [tmp_path / "a.mdx"])
    monkeypatch.setattr(grow, "reconcile_content", lambda paths, *, manifest_path: result)
    monkeypatch.setattr(grow, "_source_connection", lambda path: nullcontext(object()))
    monkeypatch.setattr(grow.enrich_manifest, "_load_kaikki_lookup", lambda: {})
    monkeypatch.setattr(grow.enrich_manifest, "_sum11_has_flag_columns", lambda conn: False)
    monkeypatch.setattr(
        grow,
        "build_skeleton_entry",
        lambda lemma: {"lemma": lemma, "pos": "noun"},
    )

    def fake_enrich_entry(entry, conn, kaikki_lookup, *, has_sum11_flags) -> bool:
        entry["heritage_status"] = {
            "classification": "standard",
            "is_russianism": False,
            "russian_shadow": False,
        }
        if entry["lemma"] == "авто":
            entry["enrichment"] = {
                "meaning": {
                    "definitions": ["автомобіль"],
                    "source": "fixture",
                }
            }
        return True

    monkeypatch.setattr(grow.enrich_manifest, "enrich_entry", fake_enrich_entry)

    payload = grow.generate_candidates(limit=2, out=out)
    written = json.loads(out.read_text(encoding="utf-8"))

    assert payload == written
    assert written["generated_from"] == grow.GENERATED_FROM
    assert written["counts"] == {
        "total_delta": 2,
        "processed": 2,
        "auto_merge": 1,
        "needs_review": 1,
    }
    assert written["auto_merge"][0]["lemma"] == "авто"
    assert written["needs_review"][0]["entry"]["lemma"] == "ревю"
    assert written["needs_review"][0]["reason"] == "missing dictionary definition"


def test_wiki_reference_cache_is_preserved(tmp_path, monkeypatch) -> None:
    cache = tmp_path / "wiki_reference.json"
    original = '{"старий": null}\n'
    cache.write_text(original, encoding="utf-8")
    monkeypatch.setattr(grow.enrich_manifest, "WIKI_REFERENCE_CACHE", cache)
    monkeypatch.setattr(grow.enrich_manifest, "_WIKI_REFERENCE_CACHE_DATA", {"старий": None})
    monkeypatch.setattr(grow.enrich_manifest, "_WIKI_REFERENCE_CACHE_DIRTY", False)

    with grow._preserve_wiki_reference_cache():
        cache.write_text('{"новий": null}\n', encoding="utf-8")
        grow.enrich_manifest._WIKI_REFERENCE_CACHE_DATA = {"новий": None}
        grow.enrich_manifest._WIKI_REFERENCE_CACHE_DIRTY = True

    assert cache.read_text(encoding="utf-8") == original
    assert grow.enrich_manifest._WIKI_REFERENCE_CACHE_DATA == {"старий": None}
    assert grow.enrich_manifest._WIKI_REFERENCE_CACHE_DIRTY is False


def test_enrich_entry_exists_and_enrich_delegates_to_it() -> None:
    assert callable(enrich_manifest_module.enrich_entry)
    enrich_source = inspect.getsource(enrich_manifest_module.enrich)

    # enrich() must delegate enrichment to enrich_entry() rather than reimplement it.
    # Collapse whitespace so the assertion is robust to call formatting (single- vs
    # multi-line) and to appended kwargs such as pointer_synonym_relations (#4950).
    compact = "".join(enrich_source.split())
    assert "enrich_entry(entry,conn,kaikki_lookup,has_sum11_flags=has_sum11_flags" in compact


def _patch_enrich_entry_heavy_helpers(monkeypatch) -> None:
    monkeypatch.setattr(enrich_manifest_module, "_slovnyk_cache", lambda lemma: {})
    monkeypatch.setattr(enrich_manifest_module, "_definition_cards", lambda *args, **kwargs: [])
    monkeypatch.setattr(enrich_manifest_module, "_warning_slovnyk", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest_module, "_curated_calque", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest_module, "_reverse_calques", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest_module, "_kaikki_pronunciation", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest_module, "_synonyms_slovnyk", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest_module, "_antonyms_wiktionary", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest_module, "_idioms", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest_module, "_stress_display_form", lambda *args, **kwargs: "")
    monkeypatch.setattr(enrich_manifest_module, "_kaikki_stress", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest_module, "_cefr", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest_module, "_morphology", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest_module, "_meaning", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest_module, "_etymology", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest_module, "_literary_attestation", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest_module, "_translation", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest_module, "_wiki_reference", lambda *args, **kwargs: None)
