import json
import sqlite3
from pathlib import Path

import pytest

from scripts.lexicon import enrich_manifest
from scripts.lexicon import reenrich_thin_manifest_entries as reenrich
from scripts.lexicon.publish_manifest import ManifestPublishError
from scripts.lexicon.reenrich_thin_manifest_entries import (
    _load_slug_filter,
    _preserve_existing_metadata,
    _reenrich_translation_only,
    reenrich_thin_entries,
)


def test_reenrich_translation_only_preserves_existing_enrichment(monkeypatch) -> None:
    entry = {
        "lemma": "помішувати",
        "enrichment": {
            "stress": {"form": "помі́шувати", "source": "ukrainian-word-stress"},
            "cefr": {"level": "C1", "source": "estimated (GRAC frequency)"},
            "sources": ["VESUM"],
        },
        "atlas_normalizations": [
            {
                "reason": (
                    "VESUM: inflected surface «помішуйте» (surface gloss='stir', "
                    "pos='imperative') folded into a NEWLY-CREATED lemma page «помішувати»."
                )
            }
        ],
    }

    def fake_translation(conn, lemma, kaikki_lookup, *, entry_pos=None, gloss_hints=None, slovnyk_cache=None):
        assert gloss_hints == {"stir"}
        assert slovnyk_cache is not None
        return {"en": ["stir"], "source": "fixture source"}

    monkeypatch.setattr(enrich_manifest, "_translation", fake_translation)
    monkeypatch.setattr(enrich_manifest, "_base_lookup_for_entry", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest, "_slovnyk_cache", lambda lemma: {})

    with sqlite3.connect(":memory:") as conn:
        _reenrich_translation_only(conn, entry, {})

    assert entry["enrichment"]["translation"] == {"en": ["stir"], "source": "fixture source"}
    assert entry["enrichment"]["stress"] == {
        "form": "помі́шувати",
        "source": "ukrainian-word-stress",
    }
    assert entry["enrichment"]["cefr"] == {
        "level": "C1",
        "source": "estimated (GRAC frequency)",
    }
    assert entry["enrichment"]["sources"] == ["VESUM", "fixture source"]


def test_preserve_existing_metadata_restores_cefr_and_wiki_reference() -> None:
    entry = {
        "enrichment": {
            "translation": {"en": ["stir"], "source": "fixture source"},
            "sources": ["fixture source"],
        }
    }

    _preserve_existing_metadata(
        entry,
        existing_cefr={"level": "B1", "source": "estimated (GRAC frequency)"},
        existing_wiki_reference={"wikipedia": {"title": "Помішувати"}},
    )

    assert entry["enrichment"]["cefr"] == {
        "level": "B1",
        "source": "estimated (GRAC frequency)",
    }
    assert entry["enrichment"]["sources"] == ["estimated (GRAC frequency)", "fixture source"]
    assert entry["wiki_reference"] == {"wikipedia": {"title": "Помішувати"}}


def test_missing_translation_target_fills_only_entries_without_translation(monkeypatch) -> None:
    manifest = {
        "entries": [
            {
                "lemma": "бризки",
                "gloss": "splashes",
                "enrichment": {"stress": {"form": "бри́зки", "source": "fixture"}},
            },
            {
                "lemma": "вершки",
                "gloss": "cream",
                "enrichment": {
                    "translation": {"en": ["cream"], "source": "existing source"},
                    "sources": ["existing source"],
                },
            },
        ],
    }
    seen: list[str] = []

    def fake_translation(conn, lemma, kaikki_lookup, *, entry_pos=None, gloss_hints=None, slovnyk_cache=None):
        seen.append(lemma)
        return {"en": ["splashes"], "source": "slovnyk.me: Українсько-англійський словник"}

    monkeypatch.setattr(enrich_manifest, "_translation", fake_translation)
    monkeypatch.setattr(enrich_manifest, "_base_lookup_for_entry", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest, "_slovnyk_cache", lambda lemma: {})

    with sqlite3.connect(":memory:") as conn:
        summary = reenrich_thin_entries(
            manifest,
            conn=conn,
            kaikki_lookup={},
            target="missing-translation",
        )

    assert seen == ["бризки"]
    assert summary["target"] == "missing-translation"
    assert summary["targets"] == 1
    assert summary["filled_translation"] == 1
    assert manifest["entries"][0]["enrichment"]["translation"] == {
        "en": ["splashes"],
        "source": "slovnyk.me: Українсько-англійський словник",
    }
    assert manifest["entries"][1]["enrichment"]["translation"] == {
        "en": ["cream"],
        "source": "existing source",
    }


def test_missing_translation_target_respects_slug_filter(monkeypatch) -> None:
    manifest = {
        "entries": [
            {"lemma": "абзац", "url_slug": "абзац", "enrichment": {}},
            {"lemma": "агент", "url_slug": "агент", "enrichment": {}},
        ],
    }
    seen: list[str] = []

    def fake_translation(conn, lemma, kaikki_lookup, *, entry_pos=None, gloss_hints=None, slovnyk_cache=None):
        seen.append(lemma)
        return {"en": ["agent"], "source": "fixture source"}

    monkeypatch.setattr(enrich_manifest, "_translation", fake_translation)
    monkeypatch.setattr(enrich_manifest, "_base_lookup_for_entry", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest, "_slovnyk_cache", lambda lemma: {})

    with sqlite3.connect(":memory:") as conn:
        summary = reenrich_thin_entries(
            manifest,
            conn=conn,
            kaikki_lookup={},
            target="missing-translation",
            slug_filter={"агент"},
        )

    assert seen == ["агент"]
    assert summary["targets"] == 1
    assert "translation" not in manifest["entries"][0]["enrichment"]
    assert manifest["entries"][1]["enrichment"]["translation"] == {
        "en": ["agent"],
        "source": "fixture source",
    }


def test_load_slug_filter_accepts_bare_array(tmp_path) -> None:
    path = tmp_path / "slugs.json"
    path.write_text(json.dumps(["абзац", "агент"]), encoding="utf-8")

    assert _load_slug_filter(path) == {"абзац", "агент"}


def test_load_slug_filter_accepts_class_b_detail_dump(tmp_path) -> None:
    path = tmp_path / "residual.json"
    path.write_text(
        json.dumps({"class_b_detail": [{"slug": "абзац"}, {"slug": "агент", "lemma": "агент"}]}),
        encoding="utf-8",
    )

    assert _load_slug_filter(path) == {"абзац", "агент"}


def test_load_slug_filter_rejects_unknown_shape(tmp_path) -> None:
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"nope": []}), encoding="utf-8")

    with pytest.raises(ValueError, match="class_b_detail"):
        _load_slug_filter(path)


def test_cached_slovnyk_only_skips_uncached_slovnyk_lookup(monkeypatch) -> None:
    entry = {"lemma": "невідоме", "enrichment": {}}

    def fake_translation(conn, lemma, kaikki_lookup, *, entry_pos=None, gloss_hints=None, slovnyk_cache=None):
        assert slovnyk_cache is None
        return None

    monkeypatch.setattr(enrich_manifest, "_translation", fake_translation)
    monkeypatch.setattr(enrich_manifest, "_base_lookup_for_entry", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest, "_slovnyk_cache", lambda lemma: {})

    with sqlite3.connect(":memory:") as conn:
        _reenrich_translation_only(conn, entry, {}, cached_slovnyk_only=True)

    assert "translation" not in entry["enrichment"]


def test_cached_slovnyk_only_does_not_live_fetch_missing_ukreng(monkeypatch) -> None:
    entry = {"lemma": "бризки", "gloss": "splashes", "enrichment": {}}

    def fail_fetch(*args, **kwargs):
        raise AssertionError("cached-only mode must not live-fetch Slovnyk")

    monkeypatch.setattr(enrich_manifest, "_DMKLINGER_INDEX", None)
    monkeypatch.setattr(enrich_manifest, "_BALLA_REVERSE_INDEX", {})
    monkeypatch.setattr(enrich_manifest, "_slovnyk_cache", lambda lemma: {"lookups": {}})
    monkeypatch.setattr(enrich_manifest, "_fetch_slovnyk_entry", fail_fetch)
    monkeypatch.setattr(enrich_manifest, "_base_lookup_for_entry", lambda *args, **kwargs: None)

    with sqlite3.connect(":memory:") as conn:
        conn.execute("CREATE TABLE dmklinger_uk_en (word TEXT, pos TEXT, translations TEXT)")
        _reenrich_translation_only(conn, entry, {}, cached_slovnyk_only=True)

    assert "translation" not in entry["enrichment"]


def test_reenrich_pointer_write_blocks_richness_regression_before_gzip(
    tmp_path, monkeypatch
) -> None:
    manifest_path = tmp_path / "lexicon-manifest.json"
    manifest_path.write_text(
        '{"richness_summary": {"poc_thin_pages": 2, "search_no_visible_gloss": 0, '
        '"old_gate_no_english_anchor": 0, "form_stub_broken": 0}}\n',
        encoding="utf-8",
    )
    baseline = {
        "richness_summary": {
            "poc_thin_pages": 1,
            "search_no_visible_gloss": 0,
            "old_gate_no_english_anchor": 0,
            "form_stub_broken": 0,
        }
    }
    gzip_calls = []

    monkeypatch.setattr(reenrich, "DEFAULT_MANIFEST", manifest_path)
    monkeypatch.setattr(
        "scripts.lexicon.publish_manifest.download_published_manifest",
        lambda **kwargs: baseline,
    )
    monkeypatch.setattr(
        reenrich, "gzip_manifest", lambda manifest, gzip_path: gzip_calls.append(manifest)
    )
    monkeypatch.setattr(
        "scripts.audit.audit_atlas_poc_richness.audit_manifest",
        lambda manifest: manifest["richness_summary"],
    )

    with pytest.raises(ManifestPublishError, match=r"publish blocked \(#4515\)"):
        reenrich._write_default_release_pointer(manifest_path)

    assert gzip_calls == []


def test_canary_check_passes_when_all_layers_filled(monkeypatch) -> None:
    def fake_enrich_entry(entry, conn, me_lookup, *, has_sum11_flags=False):
        entry["sections"] = {
            "proverbs": {"items": ["Слово не горобець"]},
            "usage_notes": {"essay": "Note"},
        }
        entry["enrichment"] = {
            "literary_attestation": [{"id": "grinchenko", "source": "Грінченко"}],
            "morphology": {"forms": [{"form": entry["lemma"]}]},
        }

    monkeypatch.setattr(enrich_manifest, "enrich_entry", fake_enrich_entry)

    with sqlite3.connect(":memory:") as conn:
        res = reenrich.run_canary_check(conn, {}, canary_lemmas=["вода"])

    assert res["success"] is True
    assert res["details"]["вода"]["passed"] is True
    assert res["details"]["вода"]["proverbs"] is True
    assert res["details"]["вода"]["usage_notes"] is True
    assert res["details"]["вода"]["grinchenko"] is True
    assert res["details"]["вода"]["forms"] is True


def test_canary_check_fails_and_aborts_mutation_check(monkeypatch) -> None:
    """Mutation check: breaking the cache/source path causes canary check to FAIL."""

    def broken_enrich_entry(entry, conn, me_lookup, *, has_sum11_flags=False):
        # Broken cache / source: missing proverbs and grinchenko
        entry["sections"] = {"usage_notes": {"essay": "Note"}}
        entry["enrichment"] = {"morphology": {"forms": [{"form": entry["lemma"]}]}}

    monkeypatch.setattr(enrich_manifest, "enrich_entry", broken_enrich_entry)

    with sqlite3.connect(":memory:") as conn:
        res = reenrich.run_canary_check(conn, {}, canary_lemmas=["вода"])

    assert res["success"] is False
    assert res["failed_lemma"] == "вода"
    assert "proverbs" in res["missing_layers"]
    assert "grinchenko" in res["missing_layers"]


def test_write_target_snapshot(tmp_path: Path) -> None:
    targets = [{"url_slug": "вода"}, {"url_slug": "хліб"}]
    snapshot_path = tmp_path / "target_snapshot.json"
    info = reenrich.write_target_snapshot(targets, snapshot_path)

    assert info["count"] == 2
    assert isinstance(info["sha256"], str)
    assert snapshot_path.exists()

    data = json.loads(snapshot_path.read_text(encoding="utf-8"))
    assert data["slugs"] == ["вода", "хліб"]
    assert data["count"] == 2
    assert data["sha256"] == info["sha256"]


def test_full_catalog_target_and_categorical_binning(monkeypatch) -> None:
    manifest = {
        "entries": [
            {
                "lemma": "вода",
                "url_slug": "вода",
                "pos": "noun",
                "enrichment": {
                    "translation": {"en": ["water"], "source": "slovnyk"},
                    "morphology": {"forms": [{"form": "вода"}]},
                },
                "sections": {"proverbs": {"items": ["Вода"]}},
            },
            {
                "lemma": "Київ",
                "url_slug": "київ",
                "pos": "proper noun",
                "enrichment": {},
            },
            {
                "lemma": "невідоме",
                "url_slug": "невідоме",
                "pos": "noun",
                "enrichment": {},
            },
        ]
    }

    def noop_enrich(entry, conn, me_lookup, *, has_sum11_flags=False):
        pass

    monkeypatch.setattr(enrich_manifest, "enrich_entry", noop_enrich)

    with sqlite3.connect(":memory:") as conn:
        summary = reenrich.reenrich_thin_entries(
            manifest,
            conn=conn,
            kaikki_lookup={},
            target="full-catalog",
        )

    assert summary["target"] == "full-catalog"
    assert summary["targets"] == 3
    bins = summary["categorical_binning"]
    assert bins["ENRICHED"] == 1
    assert bins["DETERMINISTIC_EXCLUSION"] == 1
    assert bins["UNRESOLVED_RESIDUAL"] == 1
    layers = summary["layer_counters"]
    assert layers["proverbs"] == 1
    assert layers["forms"] == 1


def test_circuit_breaker_trips_on_consecutive_misses(monkeypatch) -> None:
    manifest = {
        "entries": [
            {"lemma": "item1", "url_slug": "item1", "enrichment": {}},
            {"lemma": "item2", "url_slug": "item2", "enrichment": {}},
            {"lemma": "item3", "url_slug": "item3", "enrichment": {}},
        ]
    }

    def noop_enrich(entry, conn, me_lookup, *, has_sum11_flags=False):
        pass

    monkeypatch.setattr(enrich_manifest, "enrich_entry", noop_enrich)

    with sqlite3.connect(":memory:") as conn:
        summary = reenrich.reenrich_thin_entries(
            manifest,
            conn=conn,
            kaikki_lookup={},
            target="full-catalog",
            circuit_breaker_limit=2,
        )

    assert summary["circuit_breaker_tripped"] is True
    assert summary["consecutive_misses"] == 2

