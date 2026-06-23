from __future__ import annotations

import json

from scripts.lexicon.generate_daily_pool import build_pool, compute_weight, main


def fixture_entries() -> list[dict[str, object]]:
    return [
        {
            "lemma": "баба",
            "url_slug": "baba",
            "gloss": "grandmother",
            "primary_source": "course",
            "course_usage": [
                {
                    "track": "a1",
                    "module_num": 1,
                    "slug": "family",
                    "context": "Баба вдома.",
                }
            ],
            "enrichment": {"cefr": "B2"},
        },
        {
            "lemma": "авось",
            "url_slug": "avos",
            "gloss": "avoid: ану ж",
            "primary_source": "surzhyk_to_avoid",
            "course_usage": [],
        },
        {
            "lemma": "дім",
            "url_slug": "dim",
            "gloss": "house",
            "primary_source": "course",
            "course_usage": [],
            "enrichment": {"cefr": "A1"},
        },
        {
            "lemma": "жмур",
            "url_slug": "zhmur",
            "gloss": None,
            "primary_source": "remainder",
            "course_usage": [],
        },
        {
            "lemma": "добрий день",
            "url_slug": "dobryi-den",
            "gloss": "good afternoon",
            "primary_source": "remainder",
            "course_usage": [],
        },
    ]


def test_compute_weight_rules() -> None:
    entries = fixture_entries()

    assert compute_weight(entries[0]) == 3
    assert compute_weight(entries[1]) == 2
    assert compute_weight(entries[2]) == 2
    assert compute_weight(entries[3]) == 0
    assert compute_weight(entries[4]) == 0


def test_build_pool_schema_sorting_and_filters() -> None:
    pool = build_pool(fixture_entries(), size=10)

    assert [item["lemma"] for item in pool] == ["авось", "баба", "добрий день", "дім"]
    assert "жмур" not in {item["lemma"] for item in pool}
    assert "добрий день" in {item["lemma"] for item in pool}

    by_lemma = {item["lemma"]: item for item in pool}
    assert by_lemma["баба"] == {
        "lemma": "баба",
        "slug": "baba",
        "gloss": "grandmother",
        "weight": 3,
        "lessonTag": "a1",
    }
    assert by_lemma["дім"] == {
        "lemma": "дім",
        "slug": "dim",
        "gloss": "house",
        "weight": 2,
        "cefr": "A1",
    }
    assert set(by_lemma["добрий день"]) == {"lemma", "slug", "gloss", "weight"}


def test_build_pool_top_n_uses_weight_then_lemma() -> None:
    pool = build_pool(fixture_entries(), size=2)

    assert [item["lemma"] for item in pool] == ["авось", "баба"]


def test_main_writes_deterministic_json_bytes(tmp_path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps({"entries": fixture_entries()}, ensure_ascii=False),
        encoding="utf-8",
    )
    out_one = tmp_path / "one.json"
    out_two = tmp_path / "two.json"

    assert main(["--manifest", str(manifest), "--out", str(out_one), "--size", "10"]) == 0
    assert main(["--manifest", str(manifest), "--out", str(out_two), "--size", "10"]) == 0

    assert out_one.read_bytes() == out_two.read_bytes()
    assert out_one.read_text(encoding="utf-8").endswith("\n")
