"""Tests for scripts/lexicon/repair_truncated_definition_cards.py (#6736)."""

import json

import pytest

from scripts.lexicon import enrich_manifest
from scripts.lexicon import repair_truncated_definition_cards as repair


def _long_body() -> str:
    body = (
        "1》 Відправлятися, вирушати куди-небудь. "
        "2》 Приступати до якої-небудь служби, діяльності. "
        "3》 Переміщуватися, відхилятися в якому-небудь напрямку. "
        "4》 Піддаватися дії чого-небудь. "
        "5》 Прогинатися, вгинатися під дією чого-небудь. "
        "6》 перен. Відступати від чого-небудь, поступатися чимсь кому-небудь. "
        "7》 Худнути, марніти, занепадати здоров'ям. "
        "8》 розм. Ставати на місце, заступати. "
    )
    while len(body) <= 901:
        body += "|| Додаткове значення з прикладами вживання. "
    return body.strip()


def _chopped(body: str) -> str:
    """Reproduce the pre-#6437 cut: ``cleaned[:899].rstrip() + "…"``."""
    return body[:899].rstrip() + "…"


def _entry_with_card(lemma: str, card_id: str, definitions: list[str]) -> dict:
    return {
        "lemma": lemma,
        "url_slug": lemma,
        "enrichment": {
            "definition_cards": [
                {
                    "id": card_id,
                    "source": "Великий тлумачний словник сучасної української мови",
                    "source_pill": "ВТС",
                    "definitions": definitions,
                    "source_url": f"https://slovnyk.me/dict/vts/{lemma}",
                }
            ]
        },
    }


def _write_cache(cache_dir, lemma: str, slug: str, text: str, *, schema_version: int = 3) -> None:
    payload = {
        "schema_version": schema_version,
        "lookups": {slug: {"text": text, "word": lemma, "source_url": f"https://slovnyk.me/dict/{slug}/{lemma}"}},
    }
    (cache_dir / f"{lemma}.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


@pytest.fixture
def slovnyk_cache_dir(tmp_path, monkeypatch):
    cache_dir = tmp_path / "slovnyk_cache"
    cache_dir.mkdir()
    monkeypatch.setattr(enrich_manifest, "SLOVNYK_CACHE", cache_dir)
    monkeypatch.setattr(enrich_manifest, "_vesum_base_lemma", lambda word: None)
    return cache_dir


def test_find_chopped_cards_matches_only_the_cap_signature() -> None:
    body = _long_body()
    manifest = {
        "entries": [
            _entry_with_card("подаватися", "vts", [_chopped(body)]),
            _entry_with_card("повний", "vts", [body]),
            _entry_with_card("короткий", "sum20", ["Те саме, що інше…"]),
            _entry_with_card("грінченко", "grinchenko", [_chopped(body)]),
            _entry_with_card("два", "vts", [_chopped(body), "other"]),
        ]
    }
    hits = repair.find_chopped_cards(manifest)
    assert [entry["lemma"] for entry, _card in hits] == ["подаватися"]


def test_repair_restores_full_body_from_local_cache(slovnyk_cache_dir) -> None:
    body = _long_body()
    chopped = _chopped(body)
    _write_cache(slovnyk_cache_dir, "подаватися", "vts", body)
    manifest = {"entries": [_entry_with_card("подаватися", "vts", [chopped])]}

    summary = repair.repair_truncated_cards(manifest)

    card = manifest["entries"][0]["enrichment"]["definition_cards"][0]
    assert card["definitions"] == [body]
    # Only the chopped text changes; card metadata is preserved.
    assert card["source_pill"] == "ВТС"
    assert card["source_url"] == "https://slovnyk.me/dict/vts/подаватися"
    assert summary["repaired"] == 1
    assert summary["residual_no_cache"] == []
    assert summary["residual_guard_mismatch"] == []


def test_repair_uses_unambiguous_base_lemma_cache(slovnyk_cache_dir, monkeypatch) -> None:
    body = _long_body()
    _write_cache(slovnyk_cache_dir, "мій", "newsum", body)
    monkeypatch.setattr(enrich_manifest, "_vesum_base_lemma", lambda word: {"моєму": "мій"}.get(word))
    manifest = {"entries": [_entry_with_card("моєму", "sum20", [_chopped(body)])]}

    summary = repair.repair_truncated_cards(manifest)

    assert manifest["entries"][0]["enrichment"]["definition_cards"][0]["definitions"] == [body]
    assert summary["repaired"] == 1


def test_repair_is_fail_closed_on_prefix_mismatch(slovnyk_cache_dir) -> None:
    chopped = _chopped(_long_body())
    _write_cache(slovnyk_cache_dir, "подаватися", "vts", "1》 Зовсім інша стаття. " * 40)
    manifest = {"entries": [_entry_with_card("подаватися", "vts", [chopped])]}

    summary = repair.repair_truncated_cards(manifest)

    assert manifest["entries"][0]["enrichment"]["definition_cards"][0]["definitions"] == [chopped]
    assert summary["repaired"] == 0
    assert summary["residual_guard_mismatch"] == ["подаватися:vts"]


def test_repair_reports_residual_when_cache_row_missing(slovnyk_cache_dir) -> None:
    chopped = _chopped(_long_body())
    manifest = {"entries": [_entry_with_card("подаватися", "vts", [chopped])]}

    summary = repair.repair_truncated_cards(manifest)

    assert manifest["entries"][0]["enrichment"]["definition_cards"][0]["definitions"] == [chopped]
    assert summary["repaired"] == 0
    assert summary["residual_no_cache"] == ["подаватися:vts"]


def test_repair_ignores_stale_schema_cache(slovnyk_cache_dir) -> None:
    chopped = _chopped(_long_body())
    _write_cache(slovnyk_cache_dir, "подаватися", "vts", _long_body(), schema_version=2)
    manifest = {"entries": [_entry_with_card("подаватися", "vts", [chopped])]}

    summary = repair.repair_truncated_cards(manifest)

    assert summary["repaired"] == 0
    assert summary["residual_no_cache"] == ["подаватися:vts"]


def test_repair_limit_bounds_targets(slovnyk_cache_dir) -> None:
    body = _long_body()
    _write_cache(slovnyk_cache_dir, "перше", "vts", body)
    _write_cache(slovnyk_cache_dir, "друге", "vts", body)
    manifest = {
        "entries": [
            _entry_with_card("перше", "vts", [_chopped(body)]),
            _entry_with_card("друге", "vts", [_chopped(body)]),
        ]
    }

    summary = repair.repair_truncated_cards(manifest, limit=1)

    assert summary["chopped_cards"] == 1
    assert summary["repaired"] == 1


def test_repair_tolerates_whitespace_drift_from_renormalized_cache(slovnyk_cache_dir) -> None:
    body = _long_body()
    chopped = _chopped(body)
    # Cache row re-normalized by newer fetch code: extra spaces around punctuation.
    drifted = body.replace(". ", " . ").replace(", ", " , ")
    _write_cache(slovnyk_cache_dir, "подаватися", "vts", drifted)
    manifest = {"entries": [_entry_with_card("подаватися", "vts", [chopped])]}

    summary = repair.repair_truncated_cards(manifest)

    card = manifest["entries"][0]["enrichment"]["definition_cards"][0]
    assert card["definitions"] == [drifted.strip()]
    assert summary["repaired"] == 1


def test_parse_slovnyk_entry_keeps_articles_beyond_the_retired_fetch_cap() -> None:
    """#6736: the 5000-char fetch cap chopped the longest VTS/СУМ-20 articles at
    ingest; raw ingestion now stores the full attested article text."""
    long_text = "Дуже довга стаття. " * 400  # ~7600 chars > old 5000 cap
    html = (
        '<html><body><section id="dictionary-article"><article>'
        "<h1>слово</h1>"
        f"<p><span>{long_text}</span></p>"
        "</article></section></body></html>"
    )
    row = enrich_manifest._parse_slovnyk_entry(
        html,
        lemma="слово",
        lookup_word="слово",
        slug="vts",
        url="https://slovnyk.me/dict/vts/слово",
    )
    assert row is not None
    assert len(row["text"]) > 5000
    assert long_text.strip() in row["text"]
