"""Tests for the build-time slovnyk.me cache mirror (#3097, #6524)."""

import json

from scripts.lexicon import build_slovnyk_mirror
from scripts.lexicon import enrich_manifest as enrich_manifest_module


def _write_cache(cache_path, schema_version: int) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(
        json.dumps(
            {
                "schema_version": schema_version,
                "lemma": "книга",
                "lookup_word": "книга",
                "fetched_at": "2026-01-01T00:00:00+00:00",
                "lookups": {"orthoepy": {"dictionary_slug": "orthoepy", "text": "кн и га [кн и га] -гие"}},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def test_is_fully_cached_rejects_stale_schema_version(monkeypatch, tmp_path) -> None:
    """#6524 P2 (codex re-verdict): a "complete" v2 row -- every lookup slug present --
    must NOT read as already-cached. v2 predates the #6465 corrupted-join fix, so it can
    still carry corrupted ``text``. Before this gate, ``main()`` dropped such a row from
    ``todo`` and it was skipped forever, never healed by a real ``_slovnyk_cache()`` run
    even though the concurrent pre-fix job kept rewriting it."""
    monkeypatch.setattr(enrich_manifest_module, "SLOVNYK_CACHE", tmp_path)
    monkeypatch.setattr(build_slovnyk_mirror, "_SLOVNYK_LOOKUP_SLUGS", ("orthoepy",))
    _write_cache(enrich_manifest_module._slovnyk_cache_path("книга"), schema_version=2)

    assert build_slovnyk_mirror._is_fully_cached("книга") is False


def test_is_fully_cached_accepts_current_schema_version(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(enrich_manifest_module, "SLOVNYK_CACHE", tmp_path)
    monkeypatch.setattr(build_slovnyk_mirror, "_SLOVNYK_LOOKUP_SLUGS", ("orthoepy",))
    _write_cache(
        enrich_manifest_module._slovnyk_cache_path("книга"),
        schema_version=enrich_manifest_module._SLOVNYK_CACHE_SCHEMA_VERSION,
    )

    assert build_slovnyk_mirror._is_fully_cached("книга") is True
