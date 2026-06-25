from __future__ import annotations

import json
from pathlib import Path

from scripts.audit.generate_search_index import (
    build_browse_outputs,
    build_index,
    classification_code,
    main,
)


def entry(
    lemma: str,
    *,
    slug: str | None = None,
    gloss: object = "gloss",
    primary_source: str = "built_vocabulary",
    classification: str | None = None,
    is_russianism: bool = False,
    warning_severity: str | None = None,
    cefr: object | None = None,
) -> dict[str, object]:
    heritage: dict[str, object] = {}
    if classification:
        heritage["classification"] = classification
    if is_russianism:
        heritage["is_russianism"] = True
    if warning_severity:
        heritage["warning_severity"] = warning_severity

    row: dict[str, object] = {
        "lemma": lemma,
        "url_slug": slug or lemma,
        "gloss": gloss,
        "primary_source": primary_source,
    }
    if heritage:
        row["enrichment"] = {"heritage": heritage}
    if cefr is not None:
        row["cefr"] = cefr
    return row


def fixture_entries() -> list[dict[str, object]]:
    return [
        entry("офіс", gloss="office"),
        entry("всьо", gloss="avoid: все", primary_source="surzhyk_to_avoid"),
        entry("дім", gloss="house", primary_source="plan_required", cefr="A1"),
        entry("кава", gloss="coffee", primary_source="plan_recommended", cefr={"level": "b1"}),
        entry("баба", slug="baba", gloss=7, primary_source="remainder"),
        {"lemma": "", "url_slug": "empty", "gloss": "skip"},
        {"lemma": "нема", "url_slug": "", "gloss": "skip"},
    ]


def test_build_index_schema_sorting_filters_and_kind_buckets() -> None:
    rows = build_index(fixture_entries())

    assert [row["l"] for row in rows] == ["баба", "всьо", "дім", "кава", "офіс"]
    assert rows == [
        {"l": "баба", "s": "baba", "g": None, "r": "baba", "k": "other"},
        {"l": "всьо", "s": "всьо", "g": "avoid: все", "r": "vso", "k": "avoid", "cls": "avoid"},
        {"l": "дім", "s": "дім", "g": "house", "r": "dim", "k": "obov", "c": "A1"},
        {"l": "кава", "s": "кава", "g": "coffee", "r": "kava", "k": "rek", "c": "B1"},
        {"l": "офіс", "s": "офіс", "g": "office", "r": "ofis", "k": "vyv"},
    ]


def test_classification_code_precedence_and_standard_omit() -> None:
    cases = [
        (
            entry(
                "avoid",
                primary_source="surzhyk_to_avoid",
                warning_severity="russianism_red",
                classification="borrowing",
            ),
            "avoid",
        ),
        (entry("red", warning_severity="russianism_red"), "rus"),
        (entry("shadow", classification="unknown", is_russianism=True), "rus"),
        (entry("calque", warning_severity="calque_yellow"), "calq"),
        (entry("arch", classification="authentic-archaism"), "arch"),
        (entry("dial", classification="dialect"), "dial"),
        (entry("hist", classification="historism"), "hist"),
        (entry("borr", classification="borrowing"), "borr"),
        (entry("standard", classification="standard"), None),
    ]

    assert [classification_code(row) for row, _ in cases] == [
        expected for _, expected in cases
    ]


def test_russianism_does_not_override_treasured_authentic_classifications() -> None:
    assert (
        classification_code(
            entry("другоє", classification="authentic-archaism", is_russianism=True)
        )
        == "arch"
    )
    assert classification_code(entry("ґазда", classification="dialect", is_russianism=True)) == "dial"
    assert (
        classification_code(entry("осавул", classification="historism", is_russianism=True))
        == "hist"
    )
    # A stale/hand-edited row may carry BOTH an authentic classification AND
    # warning_severity=russianism_red; the authentic class must still win (the
    # russianism_red branch was previously unconditional — cursor review catch).
    assert (
        classification_code(
            entry(
                "другоє",
                classification="authentic-archaism",
                warning_severity="russianism_red",
            )
        )
        == "arch"
    )


def test_browse_meta_counts_and_shards() -> None:
    rows = build_index(
        [
            entry("абетка", gloss="alphabet"),
            entry("архаїзм", gloss="archaism", classification="authentic-archaism"),
            entry("бета", gloss="beta", warning_severity="russianism_red"),
            entry("борщ", gloss="borshch", classification="borrowing"),
            entry("всьо", gloss="avoid all", primary_source="surzhyk_to_avoid"),
            entry("гетьман", gloss="hetman", classification="historism"),
            entry("ґанок", gloss="porch", classification="dialect"),
            entry("ґазда", gloss="host", classification="dialect"),
            entry("калька", gloss="calque", warning_severity="calque_yellow"),
        ]
    )

    meta, shards = build_browse_outputs(rows)

    assert meta["total"] == 9
    assert meta["letterCounts"]["А"] == 2
    assert meta["letterCounts"]["Б"] == 2
    assert meta["letterCounts"]["В"] == 1
    assert meta["letterCounts"]["Ґ"] == 2
    assert meta["letterCounts"]["Я"] == 0
    assert meta["chipCounts"] == {
        "avoid": 1,
        "rus": 1,
        "calq": 1,
        "arch": 1,
        "dial": 2,
        "hist": 1,
        "borr": 1,
    }
    assert meta["letterChip"]["А"]["arch"] == 1
    assert meta["letterChip"]["А"]["rus"] == 0
    assert meta["letterChip"]["Ґ"]["dial"] == 2
    assert meta["letterChip"]["Я"]["avoid"] == 0

    assert list(shards) == ["А", "Б", "В", "Г", "Ґ", "К"]
    assert [row["l"] for row in shards["Ґ"]] == ["ґазда", "ґанок"]
    assert shards["А"][0] == {
        "l": "абетка",
        "s": "абетка",
        "g": "alphabet",
        "c": None,
        "hay": "абетка alphabet abetka",
    }
    assert shards["А"][1]["cls"] == "arch"
    assert shards["В"][0]["cls"] == "avoid"
    assert set(shards["Б"][0]) == {"l", "s", "g", "c", "hay", "cls"}


def test_main_writes_search_meta_and_per_letter_shards(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    search_out = tmp_path / "search.json"
    meta_out = tmp_path / "meta.json"
    browse_dir = tmp_path / "browse"
    manifest.write_text(
        json.dumps(
            {
                "entries": [
                    entry("арка", gloss="arch"),
                    entry("всьо", gloss="avoid all", primary_source="surzhyk_to_avoid"),
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    assert (
        main(
            [
                "--manifest",
                str(manifest),
                "--out",
                str(search_out),
                "--browse-meta-out",
                str(meta_out),
                "--browse-dir",
                str(browse_dir),
            ]
        )
        == 0
    )

    search_rows = json.loads(search_out.read_text(encoding="utf-8"))
    meta = json.loads(meta_out.read_text(encoding="utf-8"))
    shard = json.loads((browse_dir / "В.json").read_text(encoding="utf-8"))

    assert search_rows[1]["cls"] == "avoid"
    assert meta["total"] == 2
    assert meta["chipCounts"] == {"avoid": 1}
    assert shard == [
        {
            "l": "всьо",
            "s": "всьо",
            "g": "avoid all",
            "c": None,
            "hay": "всьо avoid all vso",
            "cls": "avoid",
        }
    ]
