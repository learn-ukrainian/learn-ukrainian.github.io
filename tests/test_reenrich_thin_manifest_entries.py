import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

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


def test_cached_slovnyk_only_skips_uncached_slovnyk_lookup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    entry = {"lemma": "невідоме", "enrichment": {}}

    def fake_translation(conn, lemma, kaikki_lookup, *, entry_pos=None, gloss_hints=None, slovnyk_cache=None):
        assert slovnyk_cache is None
        return None

    def fail_live_slovnyk(*args, **kwargs):
        raise AssertionError("_slovnyk_cache must not be called when cached_slovnyk_only=True")

    monkeypatch.setattr(enrich_manifest, "SLOVNYK_CACHE", tmp_path)
    monkeypatch.setattr(enrich_manifest, "_translation", fake_translation)
    monkeypatch.setattr(enrich_manifest, "_base_lookup_for_entry", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest, "_slovnyk_cache", fail_live_slovnyk)

    with sqlite3.connect(":memory:") as conn:
        _reenrich_translation_only(conn, entry, {}, cached_slovnyk_only=True)

    assert "translation" not in entry["enrichment"]


def test_cached_slovnyk_only_does_not_live_fetch_missing_ukreng(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    entry = {"lemma": "бризки", "gloss": "splashes", "enrichment": {}}

    def fail_fetch(*args, **kwargs):
        raise AssertionError("cached-only mode must not live-fetch Slovnyk")

    def fail_live_slovnyk(*args, **kwargs):
        raise AssertionError("_slovnyk_cache must not be called when cached_slovnyk_only=True")

    monkeypatch.setattr(enrich_manifest, "SLOVNYK_CACHE", tmp_path)
    monkeypatch.setattr(enrich_manifest, "_DMKLINGER_INDEX", None)
    monkeypatch.setattr(enrich_manifest, "_BALLA_REVERSE_INDEX", {})
    monkeypatch.setattr(enrich_manifest, "query_goroh_translate", lambda lemma: [])
    monkeypatch.setattr(enrich_manifest, "_slovnyk_cache", fail_live_slovnyk)
    monkeypatch.setattr(enrich_manifest, "_fetch_slovnyk_entry", fail_fetch)
    monkeypatch.setattr(enrich_manifest, "_base_lookup_for_entry", lambda *args, **kwargs: None)

    cache_path = tmp_path / "бризки.json"
    cache_path.write_text(
        json.dumps(
            {
                "schema_version": enrich_manifest._SLOVNYK_CACHE_SCHEMA_VERSION,
                "lemma": "бризки",
                "lookup_word": "бризки",
                "lookups": {},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    with sqlite3.connect(":memory:") as conn:
        conn.execute("CREATE TABLE dmklinger_uk_en (word TEXT, pos TEXT, translations TEXT)")
        _reenrich_translation_only(conn, entry, {}, cached_slovnyk_only=True)

    assert "translation" not in entry["enrichment"]


def test_reenrich_thin_manifest_entries_fills_from_goroh_fixture(monkeypatch) -> None:
    entry = {"lemma": "анімізм", "pos": "noun", "enrichment": {}}

    monkeypatch.setattr(enrich_manifest, "_DMKLINGER_INDEX", None)
    monkeypatch.setattr(enrich_manifest, "_BALLA_REVERSE_INDEX", {})
    monkeypatch.setattr(enrich_manifest, "_slovnyk_cache", lambda lemma: {"lookups": {"ukreng": None}})
    monkeypatch.setattr(
        enrich_manifest,
        "query_goroh_translate",
        lambda lemma: ["animism"] if lemma == "анімізм" else [],
    )
    monkeypatch.setattr(enrich_manifest, "_base_lookup_for_entry", lambda *args, **kwargs: None)

    with sqlite3.connect(":memory:") as conn:
        conn.execute("CREATE TABLE dmklinger_uk_en (word TEXT, pos TEXT, translations TEXT)")
        _reenrich_translation_only(conn, entry, {})

    assert entry["enrichment"]["translation"] == {
        "en": ["animism"],
        "source": "Горох (переклад)",
        "mirror_source_url": "https://goroh.pp.ua/Переклад/%D0%B0%D0%BD%D1%96%D0%BC%D1%96%D0%B7%D0%BC",
    }
    assert "Горох (переклад)" in entry["enrichment"]["sources"]


def test_reenrich_pointer_write_blocks_richness_regression_before_gzip(tmp_path, monkeypatch) -> None:
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
    monkeypatch.setattr(reenrich, "gzip_manifest", lambda manifest, gzip_path: gzip_calls.append(manifest))
    monkeypatch.setattr(
        "scripts.audit.audit_atlas_poc_richness.audit_manifest",
        lambda manifest: manifest["richness_summary"],
    )

    with pytest.raises(ManifestPublishError, match=r"publish blocked \(#4515\)"):
        reenrich._write_default_release_pointer(manifest_path)

    assert gzip_calls == []


def test_reenrich_no_pointer_skips_pointer_write(tmp_path, monkeypatch) -> None:
    manifest_path = tmp_path / "lexicon-manifest.json"
    manifest_path.write_text('{"entries": [{"lemma": "тест", "url_slug": "тест"}]}\n', encoding="utf-8")
    pointer_called = []

    monkeypatch.setattr(
        reenrich,
        "_write_default_release_pointer",
        lambda *args, **kwargs: pointer_called.append(True),
    )
    monkeypatch.setattr(
        reenrich,
        "reenrich_thin_entries",
        lambda *args, **kwargs: {"target": "missing-translation", "targets": 1},
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "reenrich_thin_manifest_entries.py",
            "--manifest",
            str(manifest_path),
            "--local",
            "--write",
            "--no-pointer",
        ],
    )
    res = reenrich.main()
    assert res == 0
    assert pointer_called == []



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
        res = reenrich.run_canary_check(conn, {})

    assert res["success"] is True


def test_canary_check_fails_and_aborts_mutation_check(monkeypatch) -> None:
    """Mutation check: breaking the cache/source path causes canary check to FAIL."""

    def broken_enrich_entry(entry, conn, me_lookup, *, has_sum11_flags=False):
        # Broken cache / source: missing proverbs and grinchenko
        entry["sections"] = {"usage_notes": {"essay": "Note"}}
        entry["enrichment"] = {"morphology": {"forms": [{"form": entry["lemma"]}]}}

    monkeypatch.setattr(enrich_manifest, "enrich_entry", broken_enrich_entry)

    with sqlite3.connect(":memory:") as conn:
        res = reenrich.run_canary_check(conn, {})

    assert res["success"] is False
    assert res["failed_layer"] == "proverbs"
    assert "proverbs" in res["missing_layers"]


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


def test_already_enriched_prefix_does_not_trip_circuit_breaker(monkeypatch) -> None:
    """Already-enriched entries (e.g. resume run) must not trip the circuit breaker."""
    manifest = {
        "entries": [
            {
                "lemma": f"item{i}",
                "url_slug": f"item{i}",
                "pos": "noun",
                "enrichment": {"translation": {"en": ["word"], "source": "slovnyk.me"}},
            }
            for i in range(60)
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
            circuit_breaker_limit=50,
        )

    assert summary["circuit_breaker_tripped"] is False
    assert summary["consecutive_misses"] == 0


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


def test_derive_adverb_en_gloss_patterns() -> None:
    assert reenrich._derive_adverb_en_gloss("abstract") == "abstractly"
    assert (
        reenrich._derive_adverb_en_gloss("abstract (apart from practice or reality; not concrete)")
        == "abstractly (apart from practice or reality; not concrete)"
    )
    assert reenrich._derive_adverb_en_gloss("heroic") == "heroically"
    assert (
        reenrich._derive_adverb_en_gloss("flexible (easily bent without breaking)")
        == "flexibly (easily bent without breaking)"
    )
    assert reenrich._derive_adverb_en_gloss("cloudless (without any clouds)") == "cloudlessly (without any clouds)"
    assert (
        reenrich._derive_adverb_en_gloss("(literally) cloudless, unclouded, clear")
        == "(literally) cloudlessly, uncloudedly, clearly"
    )
    assert reenrich._derive_adverb_en_gloss("colourful (UK), colorful (US)") == "colourfully (UK), colorfully (US)"
    assert reenrich._derive_adverb_en_gloss("simple") == "simply"
    assert reenrich._derive_adverb_en_gloss("easy") == "easily"
    assert reenrich._derive_adverb_en_gloss("public") == "publicly"
    assert reenrich._derive_adverb_en_gloss("whole") == "wholly"
    assert reenrich._derive_adverb_en_gloss("full") == "fully"
    assert reenrich._derive_adverb_en_gloss("true") == "truly"
    assert reenrich._derive_adverb_en_gloss("good") == "well"


def test_deadjectival_adverb_fallback_fills_abstractly(monkeypatch) -> None:
    manifest = {
        "entries": [
            {
                "lemma": "абстрактний",
                "pos": "adjective",
                "url_slug": "абстрактний",
                "enrichment": {
                    "translation": {
                        "en": ["abstract (apart from practice or reality; not concrete)"],
                        "source": "dmklinger",
                        "pos": "adjective",
                    },
                    "sources": ["dmklinger"],
                },
            },
            {
                "lemma": "абстрактно",
                "pos": "adverb",
                "url_slug": "абстрактно",
                "enrichment": {},
            },
        ]
    }

    # Direct translation misses for both lemmas so adverb fallback triggers
    monkeypatch.setattr(enrich_manifest, "_translation", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest, "_base_lookup_for_entry", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest, "_slovnyk_cache", lambda lemma: {})
    monkeypatch.setattr(
        reenrich,
        "verify_word",
        lambda word, pos_filter=None, **kwargs: (
            [{"lemma": word, "pos": pos_filter or "adv"}]
            if (word == "абстрактно" and pos_filter in ("adv", None))
            or (word == "абстрактний" and pos_filter in ("adj", None))
            else []
        ),
    )

    with sqlite3.connect(":memory:") as conn:
        summary = reenrich.reenrich_thin_entries(
            manifest,
            conn=conn,
            kaikki_lookup={},
            target="missing-translation",
        )

    adv_entry = manifest["entries"][1]
    assert summary["filled_translation"] == 1
    assert adv_entry["enrichment"]["translation"] == {
        "en": ["abstractly (apart from practice or reality; not concrete)"],
        "source": "dmklinger (base form абстрактний)",
        "pos": "adverb",
    }
    assert "dmklinger (base form абстрактний)" in adv_entry["enrichment"]["sources"]


def test_deadjectival_adverb_fallback_no_fill_when_adjective_missing_en(monkeypatch) -> None:
    manifest = {
        "entries": [
            {
                "lemma": "гамірний",
                "pos": "adjective",
                "url_slug": "гамірний",
                "enrichment": {
                    "sources": ["VESUM"],
                },
            },
            {
                "lemma": "гамірно",
                "pos": "adverb",
                "url_slug": "гамірно",
                "enrichment": {},
            },
        ]
    }

    monkeypatch.setattr(enrich_manifest, "_translation", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest, "_base_lookup_for_entry", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest, "_slovnyk_cache", lambda lemma: {})
    monkeypatch.setattr(
        reenrich,
        "verify_word",
        lambda word, pos_filter=None, **kwargs: (
            [{"lemma": word, "pos": pos_filter or "adv"}]
            if (word == "гамірно" and pos_filter in ("adv", None))
            or (word == "гамірний" and pos_filter in ("adj", None))
            else []
        ),
    )

    with sqlite3.connect(":memory:") as conn:
        summary = reenrich.reenrich_thin_entries(
            manifest,
            conn=conn,
            kaikki_lookup={},
            target="missing-translation",
        )

    adv_entry = manifest["entries"][1]
    assert summary["filled_translation"] == 0
    assert "translation" not in adv_entry["enrichment"]


def test_deadjectival_adverb_fallback_no_uk_lemma_invention(monkeypatch) -> None:
    # Attest only real lemmas in VESUM mock
    def fake_verify(word: str, pos_filter: str | None = None, **kwargs) -> list[dict]:
        if word == "абстрактно" and pos_filter in ("adv", None):
            return [{"lemma": "абстрактно", "pos": "adv"}]
        if word == "абстрактний" and pos_filter in ("adj", None):
            return [{"lemma": "абстрактний", "pos": "adj"}]
        return []

    monkeypatch.setattr(reenrich, "verify_word", fake_verify)

    # 1. Made-up adverb lemma not in VESUM
    fake_adv_entry = {
        "lemma": "вигаданоневідомо",
        "pos": "adverb",
        "url_slug": "вигаданоневідомо",
        "enrichment": {},
    }
    manifest_index = {
        "вигаданоневідомий": {
            "lemma": "вигаданоневідомий",
            "pos": "adjective",
            "enrichment": {"translation": {"en": ["invented"], "source": "test"}},
        }
    }
    res = reenrich._deadjectival_adverb_translation(fake_adv_entry, manifest_index)
    assert res is None

    # 2. Adverb attested in VESUM, but candidate adjective not in VESUM as adj / not in manifest
    adv_entry = {
        "lemma": "абстрактно",
        "pos": "adverb",
        "url_slug": "абстрактно",
        "enrichment": {},
    }
    empty_index: dict[str, dict[str, Any]] = {}
    res2 = reenrich._deadjectival_adverb_translation(adv_entry, empty_index)
    assert res2 is None


def test_deadjectival_adverb_fallback_fails_closed_on_vesum_error(monkeypatch) -> None:
    def raise_vesum_error(*args, **kwargs):
        raise FileNotFoundError("vesum.db not found")

    monkeypatch.setattr(reenrich, "verify_word", raise_vesum_error)

    adv_entry = {
        "lemma": "абстрактно",
        "pos": "adverb",
        "url_slug": "абстрактно",
        "enrichment": {},
    }
    manifest_index = {
        "абстрактний": {
            "lemma": "абстрактний",
            "pos": "adjective",
            "enrichment": {"translation": {"en": ["abstract"], "source": "test"}},
        }
    }
    res = reenrich._deadjectival_adverb_translation(adv_entry, manifest_index)
    assert res is None


def test_deadjectival_adverb_fallback_on_loaded_manifest_pair(monkeypatch) -> None:
    monkeypatch.setattr(
        reenrich,
        "verify_word",
        lambda word, pos_filter=None, **kwargs: (
            [{"lemma": word, "pos": pos_filter or "adv"}]
            if (word == "абстрактно" and pos_filter in ("adv", None))
            or (word == "абстрактний" and pos_filter in ("adj", None))
            else []
        ),
    )

    manifest = {
        "entries": [
            {
                "lemma": "абстрактний",
                "pos": "adjective",
                "url_slug": "абстрактний",
                "enrichment": {
                    "translation": {
                        "en": ["abstract"],
                        "source": "dmklinger",
                    },
                    "sources": ["dmklinger"],
                },
            },
            {
                "lemma": "абстрактно",
                "pos": "adverb",
                "url_slug": "абстрактно",
                "enrichment": {},
            },
        ]
    }
    by_lemma = {e.get("lemma"): e for e in manifest.get("entries", []) if isinstance(e, dict) and e.get("lemma")}

    abstr_adv = by_lemma["абстрактно"]
    res = reenrich._deadjectival_adverb_translation(abstr_adv, by_lemma)
    assert res is not None
    assert isinstance(res.get("en"), list)
    assert "abstractly" in res["en"][0]
    assert "base form абстрактний" in str(res.get("source"))


def test_diminutive_fallback_fills_in_reenrich_thin_entries(monkeypatch) -> None:
    manifest = {
        "entries": [
            {
                "lemma": "білка",
                "pos": "noun",
                "url_slug": "білка",
                "enrichment": {
                    "translation": {
                        "en": ["squirrel"],
                        "source": "dmklinger",
                    },
                    "sources": ["dmklinger"],
                },
            },
            {
                "lemma": "білочка",
                "pos": "noun",
                "url_slug": "білочка",
                "enrichment": {},
            },
        ]
    }

    monkeypatch.setattr(enrich_manifest, "_translation", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest, "_base_lookup_for_entry", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest, "_slovnyk_cache", lambda lemma: {})

    with sqlite3.connect(":memory:") as conn:
        summary = reenrich.reenrich_thin_entries(
            manifest,
            conn=conn,
            kaikki_lookup={},
            target="missing-translation",
        )

    dim_entry = manifest["entries"][1]
    assert summary["filled_translation"] == 1
    assert dim_entry["enrichment"]["translation"] == {
        "en": ["squirrel (diminutive)"],
        "source": "dmklinger (diminutive of білка)",
    }
    assert "dmklinger (diminutive of білка)" in dim_entry["enrichment"]["sources"]


def test_augmentative_fallback_fills_in_reenrich_thin_entries(monkeypatch) -> None:
    manifest = {
        "entries": [
            {
                "lemma": "вовк",
                "pos": "noun",
                "url_slug": "вовк",
                "enrichment": {
                    "translation": {
                        "en": ["wolf"],
                        "source": "slovnyk.me: fixture",
                    },
                    "sources": ["slovnyk.me: fixture"],
                },
            },
            {
                "lemma": "вовчище",
                "pos": "noun",
                "url_slug": "вовчище",
                "enrichment": {},
            },
        ]
    }

    monkeypatch.setattr(enrich_manifest, "_translation", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest, "_base_lookup_for_entry", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest, "_slovnyk_cache", lambda lemma: {})

    with sqlite3.connect(":memory:") as conn:
        summary = reenrich.reenrich_thin_entries(
            manifest,
            conn=conn,
            kaikki_lookup={},
            target="missing-translation",
        )

    aug_entry = manifest["entries"][1]
    assert summary["filled_translation"] == 1
    assert aug_entry["enrichment"]["translation"] == {
        "en": ["wolf (augmentative)"],
        "source": "slovnyk.me: fixture (augmentative of вовк)",
    }
    assert "slovnyk.me: fixture (augmentative of вовк)" in aug_entry["enrichment"]["sources"]


def test_diminutive_fallback_no_fill_when_base_missing_en(monkeypatch) -> None:
    manifest = {
        "entries": [
            {
                "lemma": "білка",
                "pos": "noun",
                "url_slug": "білка",
                "enrichment": {
                    "sources": ["VESUM"],
                },
            },
            {
                "lemma": "білочка",
                "pos": "noun",
                "url_slug": "білочка",
                "enrichment": {},
            },
        ]
    }

    monkeypatch.setattr(enrich_manifest, "_translation", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest, "_base_lookup_for_entry", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest, "_slovnyk_cache", lambda lemma: {})

    with sqlite3.connect(":memory:") as conn:
        summary = reenrich.reenrich_thin_entries(
            manifest,
            conn=conn,
            kaikki_lookup={},
            target="missing-translation",
        )

    dim_entry = manifest["entries"][1]
    assert summary["filled_translation"] == 0
    assert "translation" not in dim_entry.get("enrichment", {})


def test_diminutive_fallback_precedence_after_direct_and_base_lookup(monkeypatch) -> None:
    manifest = {
        "entries": [
            {
                "lemma": "білка",
                "pos": "noun",
                "url_slug": "білка",
                "enrichment": {
                    "translation": {
                        "en": ["squirrel"],
                        "source": "dmklinger",
                    },
                    "sources": ["dmklinger"],
                },
            },
            {
                "lemma": "білочка",
                "pos": "noun",
                "url_slug": "білочка",
                "enrichment": {},
            },
        ]
    }

    # Case 1: Direct translation succeeds -> direct wins
    def direct_trans(conn, lemma, *args, **kwargs):
        if lemma == "білочка":
            return {"en": ["little squirrel"], "source": "direct source"}
        return None

    monkeypatch.setattr(enrich_manifest, "_translation", direct_trans)
    monkeypatch.setattr(enrich_manifest, "_base_lookup_for_entry", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest, "_slovnyk_cache", lambda lemma: {})

    manifest_index = reenrich.manifest_lemma_index(manifest)
    with sqlite3.connect(":memory:") as conn:
        trans = reenrich._translation_for_entry(
            conn,
            manifest["entries"][1],
            {},
            manifest_index=manifest_index,
        )

    assert trans == {"en": ["little squirrel"], "source": "direct source"}

    # Case 2: Direct misses, base lookup succeeds -> base lookup wins
    def base_trans(conn, lemma, *args, **kwargs):
        if lemma == "білка_base":
            return {"en": ["squirrel base"], "source": "base source"}
        return None

    monkeypatch.setattr(enrich_manifest, "_translation", base_trans)
    monkeypatch.setattr(
        enrich_manifest, "_base_lookup_for_entry", lambda lemma, pos: "білка_base" if lemma == "білочка" else None
    )

    with sqlite3.connect(":memory:") as conn:
        trans2 = reenrich._translation_for_entry(
            conn,
            manifest["entries"][1],
            {},
            manifest_index=manifest_index,
        )

    assert trans2 == {"en": ["squirrel base"], "source": "base source (base form білка_base)"}


def test_diminutive_fallback_fails_closed_when_vesum_rejects(monkeypatch) -> None:
    import scripts.verification.vesum

    manifest = {
        "entries": [
            {
                "lemma": "неіснуючабілка",
                "pos": "noun",
                "url_slug": "неіснуючабілка",
                "enrichment": {
                    "translation": {
                        "en": ["fake squirrel"],
                        "source": "fixture",
                    },
                },
            },
            {
                "lemma": "неіснуючабілочка",
                "pos": "noun",
                "url_slug": "неіснуючабілочка",
                "enrichment": {},
            },
        ]
    }

    monkeypatch.setattr(enrich_manifest, "_translation", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest, "_base_lookup_for_entry", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest, "_slovnyk_cache", lambda lemma: {})
    # Mock verify_word in scripts.verification.vesum: return empty list for fake words
    monkeypatch.setattr(scripts.verification.vesum, "verify_word", lambda word, pos_filter=None: [])

    with sqlite3.connect(":memory:") as conn:
        summary = reenrich.reenrich_thin_entries(
            manifest,
            conn=conn,
            kaikki_lookup={},
            target="missing-translation",
        )

    dim_entry = manifest["entries"][1]
    assert summary["filled_translation"] == 0
    assert "translation" not in dim_entry.get("enrichment", {})
