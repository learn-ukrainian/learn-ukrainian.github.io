from __future__ import annotations

import json
from pathlib import Path

from scripts.atlas import atlas_db
from scripts.audit.generate_daily_pool import (
    build_pool,
    compute_weight,
    load_db_entries,
    main,
)


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
            # Real manifest shape: enrichment.cefr is a dict, not a bare string (#PR2 regression guard).
            "enrichment": {"cefr": {"level": "B2", "source": "estimated", "text": "B2"}},
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
            "enrichment": {"cefr": {"level": "A1", "source": "estimated", "text": "A1"}},
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
        "k": "other",
        "weight": 3,
        "lessonTag": "a1",
    }
    assert by_lemma["дім"] == {
        "lemma": "дім",
        "slug": "dim",
        "gloss": "house",
        "k": "other",
        "weight": 2,
        "cefr": "A1",
    }
    assert set(by_lemma["добрий день"]) == {"lemma", "slug", "gloss", "k", "weight"}


def test_build_pool_top_n_uses_weight_then_lemma() -> None:
    pool = build_pool(fixture_entries(), size=2)

    assert [item["lemma"] for item in pool] == ["авось", "баба"]


def test_build_pool_excludes_derived_forms_and_reserves_surzhyk() -> None:
    entries = [
        # Inflected/normalized duplicate — must be dropped even though it has a gloss + course.
        {
            "lemma": "автобусом",
            "url_slug": "avtobusom",
            "gloss": "by bus (instr.)",
            "primary_source": "built_vocabulary_form",
            "course_usage": [{"track": "a1", "module_num": 2, "slug": "transport", "context": "x"}],
            "enrichment": {"cefr": {"level": "A1", "source": "estimated", "text": "A1"}},
        },
        # Highest possible weight (course + early CEFR = 5).
        {
            "lemma": "автобус",
            "url_slug": "avtobus",
            "gloss": "bus",
            "primary_source": "built_vocabulary",
            "course_usage": [{"track": "a1", "module_num": 2, "slug": "transport", "context": "x"}],
            "enrichment": {"cefr": {"level": "A1", "source": "estimated", "text": "A1"}},
        },
        # Lower weight (surzhyk + gloss = 2) — but reserved, so it must still appear at size=1.
        {
            "lemma": "всьо",
            "url_slug": "vso",
            "gloss": "avoid: все",
            "primary_source": "surzhyk_to_avoid",
            "course_usage": [],
        },
    ]

    assert "автобусом" not in {item["lemma"] for item in build_pool(entries, size=10)}
    assert [item["lemma"] for item in build_pool(entries, size=1)] == ["всьо"]


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



def _daily_atlas_db(tmp_path: Path) -> Path:
    """Materialize a fixture atlas.db from a small manifest via the real migrator.

    Two eligible public lemma articles, one gloss-less lemma (admission-excluded),
    and one ``form_of`` alias route (payload-only, no ``articles`` row) that the
    entry-model SSOT must keep out of Word-of-the-Day.
    """
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "lemma": "баба",
                        "url_slug": "baba",
                        "gloss": "grandmother",
                        "primary_source": "course",
                        "course_usage": [
                            {"track": "a1", "module_num": 1, "slug": "family", "context": "x"}
                        ],
                        "enrichment": {"cefr": {"level": "A1", "source": "est", "text": "A1"}},
                    },
                    {
                        "lemma": "дім",
                        "url_slug": "dim",
                        "gloss": "house",
                        "primary_source": "course",
                        "course_usage": [],
                        "enrichment": {"cefr": {"level": "A1", "source": "est", "text": "A1"}},
                    },
                    # No gloss → admission-excluded by build_pool, but still an article row.
                    {"lemma": "жмур", "url_slug": "zhmur", "primary_source": "remainder"},
                    # form_of alias route: public payload, NO articles row → structurally excluded.
                    {"lemma": "бабу", "url_slug": "babu", "form_of": {"url_slug": "baba"}},
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    db = tmp_path / "atlas.db"
    atlas_db.migrate_manifest(manifest, db)
    return db


def test_load_db_entries_returns_only_approved_public_articles(tmp_path) -> None:
    entries = load_db_entries(_daily_atlas_db(tmp_path))

    slugs = {entry["url_slug"] for entry in entries}
    # form_of alias route (babu) has no articles row → never a candidate.
    assert slugs == {"baba", "dim", "zhmur"}
    assert "babu" not in slugs


def test_db_mode_matches_manifest_admission_and_excludes_form_of(tmp_path) -> None:
    db = _daily_atlas_db(tmp_path)

    # payload_json stores the exact public manifest entry, so DB-sourced admission
    # is identical to manifest-sourced admission over the same article rows.
    article_entries = [
        {
            "lemma": "баба",
            "url_slug": "baba",
            "gloss": "grandmother",
            "primary_source": "course",
            "course_usage": [{"track": "a1", "module_num": 1, "slug": "family", "context": "x"}],
            "enrichment": {"cefr": {"level": "A1", "source": "est", "text": "A1"}},
        },
        {
            "lemma": "дім",
            "url_slug": "dim",
            "gloss": "house",
            "primary_source": "course",
            "course_usage": [],
            "enrichment": {"cefr": {"level": "A1", "source": "est", "text": "A1"}},
        },
        {"lemma": "жмур", "url_slug": "zhmur", "primary_source": "remainder"},
    ]
    assert build_pool(load_db_entries(db), 300) == build_pool(article_entries, 300)

    out = tmp_path / "pool.json"
    assert main(["--db", str(db), "--out", str(out), "--size", "300"]) == 0
    pool = json.loads(out.read_text(encoding="utf-8"))
    assert [item["lemma"] for item in pool] == ["баба", "дім"]  # жмур dropped (no gloss)
    assert "babu" not in {item["slug"] for item in pool}


def test_db_mode_writes_deterministic_json_bytes(tmp_path) -> None:
    db = _daily_atlas_db(tmp_path)
    out_one = tmp_path / "one.json"
    out_two = tmp_path / "two.json"

    assert main(["--db", str(db), "--out", str(out_one), "--size", "300"]) == 0
    assert main(["--db", str(db), "--out", str(out_two), "--size", "300"]) == 0
    assert out_one.read_bytes() == out_two.read_bytes()
    assert out_one.read_text(encoding="utf-8").endswith("\n")


def test_build_pool_keeps_source_inventory_browse_only_by_default() -> None:
    entries = [
        {
            "lemma": "барабан",
            "url_slug": "baraban",
            "gloss": "drum",
            "primary_source": "source_inventory_grow",
            "course_usage": [],
            "enrichment": {"cefr": {"level": "A1", "source": "fixture", "text": "A1"}},
        },
        {
            "lemma": "кіт",
            "url_slug": "kit",
            "gloss": "cat",
            "primary_source": "source_inventory_grow",
            "course_usage": [],
            "enrichment": {"cefr": {"level": "A1", "source": "fixture", "text": "A1"}},
            "surface_admission": {"daily": True},
        },
    ]

    assert [item["lemma"] for item in build_pool(entries, size=10)] == ["кіт"]
