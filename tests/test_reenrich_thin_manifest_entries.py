import sqlite3

from scripts.lexicon import enrich_manifest
from scripts.lexicon.reenrich_thin_manifest_entries import (
    _preserve_existing_metadata,
    _reenrich_translation_only,
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

    def fake_translation(conn, lemma, kaikki_lookup, *, entry_pos=None, gloss_hints=None):
        assert gloss_hints == {"stir"}
        return {"en": ["stir"], "source": "fixture source"}

    monkeypatch.setattr(enrich_manifest, "_translation", fake_translation)
    monkeypatch.setattr(enrich_manifest, "_base_lookup_for_entry", lambda *args, **kwargs: None)

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
