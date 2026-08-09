"""Fixture tests for additive slug-keyed EN translation delta merge."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from scripts.lexicon.merge_translation_delta import (
    entry_has_translation,
    entry_translation,
    merge_translation_delta,
    prove_no_nonempty_en_overwrites,
)


def _entry(slug: str, lemma: str, *, en: list[str] | None = None, source: str = "fixture") -> dict:
    entry: dict = {"url_slug": slug, "lemma": lemma, "pos": "noun"}
    if en is not None:
        entry["enrichment"] = {
            "translation": {"en": en, "source": source},
            "sources": [source],
        }
    else:
        entry["enrichment"] = {"stress": {"form": lemma, "source": "fixture"}}
    return entry


def test_copies_missing_en_from_pulled() -> None:
    live = {"entries": [_entry("alpha", "альфа"), _entry("beta", "бета", en=["keep"])]}
    pulled = {
        "entries": [
            _entry("alpha", "альфа", en=["apple"], source="pulled-src"),
            _entry("beta", "бета", en=["banana"], source="pulled-src"),
        ]
    }

    stats = merge_translation_delta(live, pulled, stamp_generated_at=False)

    assert stats.filled == 1
    assert stats.filled_slugs == ["alpha"]
    assert entry_translation(live["entries"][0]) == {"en": ["apple"], "source": "pulled-src"}
    assert "pulled-src" in live["entries"][0]["enrichment"]["sources"]
    assert entry_translation(live["entries"][1]) == {"en": ["keep"], "source": "fixture"}


def test_preserves_existing_en_even_when_pulled_differs() -> None:
    live = {"entries": [_entry("kiwi", "ківі", en=["kiwi 2"], source="live-balla")]}
    pulled = {"entries": [_entry("kiwi", "ківі", en=["different"], source="pulled")]}
    before = copy.deepcopy(live["entries"][0]["enrichment"]["translation"])

    stats = merge_translation_delta(live, pulled, stamp_generated_at=False)

    assert stats.filled == 0
    assert stats.skipped_live_has_translation == 1
    assert live["entries"][0]["enrichment"]["translation"] == before


def test_slug_absent_in_pulled_is_ignored() -> None:
    live = {"entries": [_entry("only-live", "лише"), _entry("shared", "спільне")]}
    pulled = {"entries": [_entry("shared", "спільне", en=["shared"], source="pulled")]}

    stats = merge_translation_delta(live, pulled, stamp_generated_at=False)

    assert stats.filled == 1
    assert stats.skipped_pulled_missing_slug == 1
    assert not entry_has_translation(live["entries"][0])
    assert entry_has_translation(live["entries"][1])


def test_entry_count_invariance_and_no_pulled_only_inserts() -> None:
    live = {
        "entries": [
            _entry("a", "а"),
            _entry("b", "б", en=["bee"]),
            _entry("c", "в"),
        ]
    }
    pulled = {
        "entries": [
            _entry("a", "а", en=["and"]),
            _entry("pulled-only", "зайве", en=["extra"]),
            _entry("c", "в"),  # present but no EN
        ]
    }
    before_slugs = [e["url_slug"] for e in live["entries"]]

    stats = merge_translation_delta(live, pulled, stamp_generated_at=False)

    assert stats.live_entry_count_before == 3
    assert stats.live_entry_count_after == 3
    assert [e["url_slug"] for e in live["entries"]] == before_slugs
    assert stats.filled == 1
    assert stats.filled_slugs == ["a"]
    assert stats.skipped_pulled_lacks_translation == 1
    assert all(e["url_slug"] != "pulled-only" for e in live["entries"])


def test_overwrite_proof_reports_zero_for_clean_merge() -> None:
    live = {
        "entries": [
            _entry("млн", "млн", en=["m", "million"], source="live"),
            _entry("gap", "прогалина"),
        ]
    }
    before_by_slug = {e["url_slug"]: copy.deepcopy(e) for e in live["entries"]}
    pulled = {
        "entries": [
            _entry("млн", "млн", en=["should-not-apply"], source="pulled"),
            _entry("gap", "прогалина", en=["gap"], source="pulled"),
        ]
    }

    merge_translation_delta(live, pulled, stamp_generated_at=False)
    after_by_slug = {e["url_slug"]: e for e in live["entries"]}

    assert prove_no_nonempty_en_overwrites(before_by_slug, after_by_slug) == 0
    assert entry_translation(live["entries"][0]) == {"en": ["m", "million"], "source": "live"}
    assert entry_translation(live["entries"][1]) == {"en": ["gap"], "source": "pulled"}


def test_overwrite_proof_returns_nonzero_when_nonempty_en_changes() -> None:
    """Mutation check: the proof must fail when a nonempty EN object actually changes."""
    before_by_slug = {
        "kiwi": _entry("kiwi", "ківі", en=["kiwi 2"], source="live-balla"),
        "млн": _entry("млн", "млн", en=["m", "million"], source="live"),
    }
    after_by_slug = {
        "kiwi": _entry("kiwi", "ківі", en=["different"], source="mutated"),
        "млн": copy.deepcopy(before_by_slug["млн"]),
    }

    assert prove_no_nonempty_en_overwrites(before_by_slug, after_by_slug) > 0
    assert prove_no_nonempty_en_overwrites(before_by_slug, after_by_slug) == 1


def test_sync_embedded_fingerprint_from_sidecar(tmp_path: Path) -> None:
    sidecar = tmp_path / "lexicon-manifest.fingerprint.json"
    sidecar.write_text(
        json.dumps({"schema_version": 1, "fingerprint": "abc123"}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    live = {"entries": [_entry("x", "ікс")]}
    from scripts.lexicon.merge_translation_delta import sync_embedded_fingerprint_from_sidecar

    payload = sync_embedded_fingerprint_from_sidecar(live, fingerprint_path=sidecar)
    assert payload["fingerprint"] == "abc123"
    assert live["manifest_fingerprint"] == {"schema_version": 1, "fingerprint": "abc123"}


def test_write_roundtrip_preserves_fill(tmp_path: Path) -> None:
    from scripts.lexicon.manifest_io import write_manifest

    live_path = tmp_path / "live.json"
    live = {"version": "0.1", "entries": [_entry("x", "ікс")]}
    pulled = {"version": "0.1", "entries": [_entry("x", "ікс", en=["x"], source="pulled")]}

    stats = merge_translation_delta(live, pulled, stamp_generated_at=False)
    assert stats.filled == 1
    write_manifest(live_path, live)
    rewritten = json.loads(live_path.read_text(encoding="utf-8"))
    assert entry_has_translation(rewritten["entries"][0])
