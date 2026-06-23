from __future__ import annotations

import json

from scripts.audit.generate_search_index import build_index, main


def fixture_entries() -> list[dict[str, object]]:
    return [
        {
            "lemma": "офіс",
            "url_slug": "офіс",
            "gloss": "office",
            "primary_source": "built_vocabulary",
        },
        {
            "lemma": "всьо",
            "url_slug": "всьо",
            "gloss": "avoid: все",
            "primary_source": "surzhyk_to_avoid",
        },
        {
            "lemma": "дім",
            "url_slug": "дім",
            "gloss": "house",
            "primary_source": "plan_required",
        },
        {
            "lemma": "кава",
            "url_slug": "кава",
            "gloss": "coffee",
            "primary_source": "plan_recommended",
        },
        {
            "lemma": "баба",
            "url_slug": "baba",
            "gloss": 7,
            "primary_source": "remainder",
        },
        {"lemma": "", "url_slug": "empty", "gloss": "skip"},
        {"lemma": "нема", "url_slug": "", "gloss": "skip"},
    ]


def test_build_index_schema_sorting_filters_and_kind_buckets() -> None:
    rows = build_index(fixture_entries())

    assert [row["l"] for row in rows] == ["баба", "всьо", "дім", "кава", "офіс"]
    assert rows == [
        {"l": "баба", "s": "baba", "g": None, "r": "baba", "k": "other"},
        {"l": "всьо", "s": "всьо", "g": "avoid: все", "r": "vso", "k": "avoid"},
        {"l": "дім", "s": "дім", "g": "house", "r": "dim", "k": "obov"},
        {"l": "кава", "s": "кава", "g": "coffee", "r": "kava", "k": "rek"},
        {"l": "офіс", "s": "офіс", "g": "office", "r": "ofis", "k": "vyv"},
    ]


def test_main_writes_deterministic_compact_json_bytes(tmp_path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps({"entries": fixture_entries()}, ensure_ascii=False),
        encoding="utf-8",
    )
    out_one = tmp_path / "one.json"
    out_two = tmp_path / "two.json"

    assert main(["--manifest", str(manifest), "--out", str(out_one)]) == 0
    assert main(["--manifest", str(manifest), "--out", str(out_two)]) == 0

    assert out_one.read_bytes() == out_two.read_bytes()
    assert out_one.read_text(encoding="utf-8").endswith("\n")
    assert json.loads(out_one.read_text(encoding="utf-8")) == build_index(fixture_entries())
