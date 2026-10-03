from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from scripts.atlas import atlas_db
from scripts.audit import generate_search_index
from scripts.audit.generate_search_index import (
    DEFAULT_BROWSE_DIR,
    DEFAULT_BROWSE_META_OUT,
    DEFAULT_SEARCH_OUT,
    UKRAINIAN_ALPHABET,
    _sanitize_typeahead_gloss,
    _search_gloss,
    build_atlas_db_search_artifacts,
    build_browse_outputs,
    build_index,
    classification_code,
    display_gloss,
    guard_browse_staleness,
    main,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


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
    curated_calque: dict[str, object] | None = None,
    attestations: list[dict[str, object]] | None = None,
    sum20: str | None = None,
) -> dict[str, object]:
    heritage: dict[str, object] = {}
    if classification:
        heritage["classification"] = classification
    if is_russianism:
        heritage["is_russianism"] = True
    if warning_severity:
        heritage["warning_severity"] = warning_severity
    if curated_calque:
        heritage["curated_calque"] = curated_calque
    if attestations:
        heritage["attestations"] = attestations

    row: dict[str, object] = {
        "lemma": lemma,
        "url_slug": slug or lemma,
        "gloss": gloss,
        "primary_source": primary_source,
    }
    if heritage:
        row["enrichment"] = {"heritage": heritage}
    if sum20:
        enrichment = row.setdefault("enrichment", {})
        assert isinstance(enrichment, dict)
        enrichment["definition_cards"] = [{"id": "sum20", "definitions": [sum20]}]
    if cefr is not None:
        row["cefr"] = cefr
    return row


def _named(lemma: str) -> dict[str, object]:
    """A stored lexical record whose own excerpt names ``lemma``; alone it binds nothing (#9603)."""
    return {
        "kind": "lexical",
        "corrections": ["інше"],
        "evidence": [f"antonenko-davydovych-yak-my-hovorymo_p000: слово {lemma} уживати не слід, кажіть інакше"],
    }


def _proof(lemma: str) -> dict[str, object]:
    """Current curated proof: a reviewed judgment rejecting ``lemma`` (fixture passage)."""
    passage = f"Слова {lemma} в українській мові нема, кажіть інше."
    return {
        "kind": "lexical",
        "corrections": ["інше"],
        "sense": "fixture sense",
        "citations": [],
        "judgments": [
            {
                "locator": "antonenko-davydovych-yak-my-hovorymo_p000",
                "passage": passage,
                "passageSha256": generate_search_index._HERITAGE_CLASSIFIER.source_text_digest(passage),
                "rejectedForm": lemma,
                "endorsedForm": "інше",
                "sense": "fixture sense",
            }
        ],
    }


@pytest.fixture(autouse=True)
def _fixture_usage_sources(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fixture headwords get current proof next to the actual curated projection."""
    proofs = {lemma: _proof(lemma) for lemma in ("всьо", "avoid", "red", "calque", "бета", "калька")}
    monkeypatch.setattr(generate_search_index, "_USAGE_SOURCES", {**generate_search_index.usage_sources(), **proofs})


def _avoid_entry(lemma: str, gloss: str) -> dict[str, object]:
    return entry(
        lemma,
        gloss=gloss,
        primary_source="surzhyk_to_avoid",
        classification="russianism",
        is_russianism=True,
        curated_calque=_named(lemma),
    )


_ESUM_BORROWING = [{"source": "esum", "ref": "борщ:1:1", "word": "борщ", "detail": "борщ «страва» — запозичення"}]


def sum20(head: str, label: str) -> str:
    return f"{head.upper()}, у, ч., {label} Значення слова."


def fixture_entries() -> list[dict[str, object]]:
    return [
        entry("офіс", gloss="office"),
        _avoid_entry("всьо", "avoid: все"),
        entry("дім", gloss="house", primary_source="plan_required", cefr="A1"),
        entry("кава", gloss="coffee", primary_source="plan_recommended", cefr={"level": "b1"}),
        entry("баба", slug="baba", gloss=7, primary_source="remainder"),
        {"lemma": "", "url_slug": "empty", "gloss": "skip"},
        {"lemma": "нема", "url_slug": "", "gloss": "skip"},
    ]


def atlas_db_fixture(
    tmp_path: Path,
    *,
    entries: list[dict[str, object]] | None = None,
) -> Path:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "entries": entries
                if entries is not None
                else [
                    entry("Іван", slug="іван", gloss="Ivan"),
                    entry("автобус", gloss="bus"),
                    {"lemma": "Іване", "url_slug": "іване", "form_of": {"url_slug": "іван"}},
                    {"lemma": "автобусом", "url_slug": "автобусом", "form_of": {"url_slug": "автобус"}},
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    db = tmp_path / "atlas.db"
    atlas_db.migrate_manifest(manifest, db)
    return db


def test_db_artifacts_keep_articles_and_aliases_separate_and_deduplicate(tmp_path: Path) -> None:
    db = atlas_db_fixture(tmp_path)
    conn = sqlite3.connect(db)
    conn.execute(
        "INSERT INTO aliases(alias, kind, source, target_slug, visibility) VALUES (?,?,?,?,?)",
        ("Іване", "spelling_variant", "test", "іван", "public"),
    )
    conn.commit()
    conn.close()

    articles, aliases, counts = build_atlas_db_search_artifacts(db)

    assert [row["s"] for row in articles] == ["автобус", "іван"]
    assert all(row["t"] == "lemma" for row in articles)
    assert {row["a"]: (row["s"], row["h"]) for row in aliases}["Іване"] == ("іван", "Іван")
    assert {row["a"]: row["s"] for row in aliases}["автобусом"] == "автобус"
    assert len([row for row in aliases if row["a"] == "Іване" and row["s"] == "іван"]) == 1
    assert counts["reviewed_entries"] == 2
    assert counts["public_alias_records"] == 6
    assert counts["emitted_aliases"] == 5
    assert counts["deduplicated_aliases"] == 1


def test_db_artifact_build_fails_on_the_site_build_entry_model_gates(tmp_path: Path) -> None:
    db = atlas_db_fixture(tmp_path)
    conn = sqlite3.connect(db)
    conn.execute(
        "INSERT INTO aliases(alias, kind, source, target_slug, visibility) VALUES (?,?,?,?,?)",
        ("привид", "spelling_variant", "test", "missing", "public"),
    )
    conn.commit()
    conn.close()

    with pytest.raises(ValueError, match="alias_target_integrity failure"):
        build_atlas_db_search_artifacts(db)


def test_db_artifacts_emit_only_provenance_safe_gerund_parents(tmp_path: Path) -> None:
    dictionary_gerund = entry("читаючи", gloss="while reading")
    dictionary_gerund["enrichment"] = {
        "definition_cards": [
            {
                "id": "sum20",
                "source": "СУМ-20",
                "definitions": ["чита́ючи Дієприсл. недоконаного виду до чита́ти."],
            }
        ]
    }
    meaning_gerund = entry("прочитавши", gloss="having read")
    meaning_gerund["enrichment"] = {
        "meaning": {
            "source": "словник",
            "definitions": ["Дієприсл. доконаного виду до прочита́ти."],
        }
    }
    vesum_hint = entry("йдучи", gloss="while going")
    vesum_hint["enrichment"] = {
        "morphology": {
            "source": "VESUM",
            "pos": "advp",
            "paradigm": {"kind": "other", "verb": "іти"},
        }
    }
    pos_only = entry("сидячи", gloss="while sitting")
    pos_only["enrichment"] = {
        "morphology": {"source": "VESUM", "pos": "advp", "paradigm": {"kind": "other"}}
    }
    non_vesum = entry("лежачи", gloss="while lying")
    non_vesum["enrichment"] = {
        "morphology": {
            "source": "manual",
            "pos": "advp",
            "paradigm": {"kind": "other", "verb": "лежати"},
        }
    }
    wrong_vesum_pos = entry("стоячи", gloss="while standing")
    wrong_vesum_pos["enrichment"] = {
        "morphology": {
            "source": "VESUM",
            "pos": "adverbial participle",
            "paradigm": {"kind": "other", "verb": "стояти"},
        }
    }
    missing_parent = entry("кажучи", gloss="while saying")
    missing_parent["enrichment"] = {
        "definition_cards": [
            {"id": "sum20", "source": "СУМ-20", "definitions": ["Ка́жучи, дієприсл."]}
        ]
    }
    conflicting_parents = entry("роблячи", gloss="while doing")
    conflicting_parents["enrichment"] = {
        "meaning": {
            "source": "словник",
            "definitions": ["Дієприсл. недоконаного виду до роби́ти."],
        },
        "definition_cards": [
            {
                "id": "sum20",
                "source": "СУМ-20",
                "definitions": ["Роблячи Дієприсл. до вико́нувати."],
            }
        ],
    }
    unsourced_definition = entry("співаючи", gloss="while singing")
    unsourced_definition["enrichment"] = {
        "definition_cards": [
            {"id": "unattributed", "definitions": ["Дієприсл. до співа́ти."]}
        ]
    }
    learner_gloss = entry("танцюючи", gloss="Дієприсл. до танцюва́ти.")
    passive_participle = entry("читаний", gloss="read")
    passive_participle["enrichment"] = {
        "definition_cards": [
            {
                "id": "sum20",
                "source": "СУМ-20",
                "definitions": ["Дієпр. пас. мин. часу до чита́ти."],
            }
        ]
    }
    anna_copy = entry("працюючи", gloss="while working")
    anna_copy["enrichment"] = {
        "meaning": {
            "source": "Anna Ohoiko",
            "definitions": ["Дієприсл. до працюва́ти."],
        }
    }

    db = atlas_db_fixture(
        tmp_path,
        entries=[
            entry("читати"),
            entry("прочитати"),
            entry("іти"),
            dictionary_gerund,
            meaning_gerund,
            vesum_hint,
            pos_only,
            non_vesum,
            wrong_vesum_pos,
            missing_parent,
            conflicting_parents,
            unsourced_definition,
            learner_gloss,
            passive_participle,
            anna_copy,
        ],
    )

    articles, _, _ = build_atlas_db_search_artifacts(db)
    by_slug = {row["s"]: row for row in articles}

    assert by_slug["читаючи"]["p"] == "чита́ти"
    assert by_slug["прочитавши"]["p"] == "прочита́ти"
    assert by_slug["йдучи"]["p"] == "іти"
    for slug in (
        "сидячи",
        "лежачи",
        "стоячи",
        "кажучи",
        "роблячи",
        "співаючи",
        "танцюючи",
        "читаний",
        "працюючи",
    ):
        assert "p" not in by_slug[slug]


def test_db_mode_preserves_gerund_parent_in_search_rows_and_shards(tmp_path: Path) -> None:
    gerund = entry("говорячи", gloss="while speaking")
    gerund["enrichment"] = {
        "definition_cards": [
            {
                "id": "sum20",
                "source": "СУМ-20",
                "definitions": ["гово́рячи Дієприсл. до говори́ти."],
            }
        ]
    }
    db = atlas_db_fixture(tmp_path, entries=[entry("говорити"), gerund])
    search_out = tmp_path / "search.json"
    aliases_out = tmp_path / "aliases.json"
    search_shards_out = tmp_path / "search-shards.json"
    search_shard_dir = tmp_path / "search-shards"
    browse_meta_out = tmp_path / "browse-meta.json"
    browse_flagged_out = tmp_path / "browse-flagged.json"
    browse_dir = tmp_path / "browse"

    assert (
        main(
            [
                "--db",
                str(db),
                "--out",
                str(search_out),
                "--aliases-out",
                str(aliases_out),
                "--search-shards-out",
                str(search_shards_out),
                "--search-shard-dir",
                str(search_shard_dir),
                "--browse-meta-out",
                str(browse_meta_out),
                "--browse-flagged-out",
                str(browse_flagged_out),
                "--browse-dir",
                str(browse_dir),
            ]
        )
        == 0
    )

    search_rows = json.loads(search_out.read_text(encoding="utf-8"))
    gerund_row = next(row for row in search_rows if row["s"] == "говорячи")
    assert gerund_row["p"] == "говори́ти"

    search_shards = json.loads(search_shards_out.read_text(encoding="utf-8"))
    shard_key = next(
        key
        for key in search_shards["shards"]
        if any(
            row["s"] == "говорячи"
            for row in json.loads((search_shard_dir / f"{key}.json").read_text(encoding="utf-8"))
        )
    )
    shard_rows = json.loads((search_shard_dir / f"{shard_key}.json").read_text(encoding="utf-8"))
    assert next(row for row in shard_rows if row["s"] == "говорячи")["p"] == "говори́ти"
    assert all("p" not in row for row in json.loads((browse_dir / "Г.json").read_text(encoding="utf-8")))


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
def test_build_index_uses_translation_when_gloss_missing() -> None:
    rows = build_index(
        [
            {
                "lemma": "помішувати",
                "url_slug": "помішувати",
                "gloss": None,
                "primary_source": "built_vocabulary_normalized",
                "enrichment": {
                    "translation": {
                        "en": ["stir", "mix lightly"],
                        "source": "test",
                    }
                },
            }
        ]
    )

    assert rows == [
        {
            "l": "помішувати",
            "s": "помішувати",
            "g": "stir; mix lightly",
            "r": "pomishuvaty",
            "k": "vyv",
        }
    ]


_VOYEVODA_MASHED_GLOSS = (
    "1. У давній Русі та інших слов’янських державах — вождь, полководець, "
    "а також правитель міста, округу в XVI-XVIII ст. А в Римі свято. "
    "Велике свято! Тиск народу, Зо всього царств..."
)

# Cloned from lemma ба: Unicode ellipsis precedes a later ASCII ``...``.
_BA_MIXED_ELLIPSIS_GLOSS = (
    "Уживається для вираження здивування, здогаду і т. ін.; значенням близький "
    "до дивись. — Ти, як те сонечко, закрасиш мою смутну хату, розвеселиш "
    "матір… — Ба! У тебе й мати є? А я ..."
)


def test_sanitize_typeahead_gloss_keeps_sense_one_only_for_voyevoda_mash() -> None:
    gloss = _sanitize_typeahead_gloss(_VOYEVODA_MASHED_GLOSS)
    assert gloss is not None
    assert gloss.startswith("У давній Русі")
    assert "А в Римі свято" not in gloss
    assert "Велике свято" not in gloss
    assert "царств" not in gloss
    assert not gloss.endswith("...")
    assert not gloss.endswith("…")
    assert len(gloss) <= 180


def test_sanitize_typeahead_gloss_cuts_at_earliest_ellipsis_for_ba_mixed_markers() -> None:
    """Unicode ``…`` before ASCII ``...`` must win by index, not tuple order."""
    assert _BA_MIXED_ELLIPSIS_GLOSS.find("…") < _BA_MIXED_ELLIPSIS_GLOSS.find("...")
    gloss = _sanitize_typeahead_gloss(_BA_MIXED_ELLIPSIS_GLOSS)
    assert gloss is not None
    assert "…" not in gloss
    assert "..." not in gloss
    assert "— Ба!" not in gloss
    assert "мати є" not in gloss
    assert "дивись" in gloss
    assert len(gloss) <= 180


def test_sanitize_typeahead_gloss_leaves_short_voda_shaped_gloss_unchanged() -> None:
    assert _sanitize_typeahead_gloss("water") == "water"
    assert _sanitize_typeahead_gloss("shore, bank") == "shore, bank"


def test_search_gloss_falls_through_to_translation_when_empty_or_missing() -> None:
    translation_entry = {
        "lemma": "помішувати",
        "url_slug": "помішувати",
        "gloss": None,
        "enrichment": {"translation": {"en": ["stir", "mix lightly"]}},
    }
    assert _search_gloss(translation_entry) == "stir; mix lightly"
    assert _search_gloss({**translation_entry, "gloss": ""}) == "stir; mix lightly"
    assert _search_gloss({**translation_entry, "gloss": "   "}) == "stir; mix lightly"
    assert _search_gloss({"lemma": "x", "url_slug": "x", "gloss": None}) is None


def test_build_index_sanitizes_mashed_voyevoda_gloss_for_typeahead() -> None:
    rows = build_index(
        [
            entry("воєвода", gloss=_VOYEVODA_MASHED_GLOSS),
            entry("вода", gloss="water"),
        ]
    )
    by_lemma = {row["l"]: row for row in rows}
    assert by_lemma["вода"]["g"] == "water"
    assert by_lemma["воєвода"]["g"] is not None
    assert "А в Римі свято" not in by_lemma["воєвода"]["g"]
    assert "Велике свято" not in by_lemma["воєвода"]["g"]
    assert by_lemma["воєвода"]["g"].startswith("У давній Русі")


def test_classification_code_precedence_and_standard_omit() -> None:
    cases = [
        # #9603 D01: avoid-list provenance strengthens a bound Russianism only.
        (_avoid_entry("avoid", "avoid: x"), "avoid"),
        (
            entry(
                "borrowed",
                primary_source="surzhyk_to_avoid",
                warning_severity="russianism_red",
                classification="borrowing",
            ),
            None,
        ),
        (entry("bare", primary_source="surzhyk_to_avoid", classification="russianism", is_russianism=True), None),
        # A stored excerpt naming the headword is not proof without a current judgment.
        (entry("stored", classification="russianism", is_russianism=True, curated_calque=_named("stored")), None),
        (entry("red", classification="russianism", is_russianism=True, curated_calque=_named("red")), "rus"),
        (entry("calque", classification="calque", curated_calque=_named("calque")), "calq"),
        (entry("arch", classification="authentic-archaism", sum20=sum20("arch", "заст.")), "arch"),
        (entry("dial", classification="dialect", sum20=sum20("dial", "діал.")), "dial"),
        (entry("hist", classification="historism", sum20=sum20("hist", "іст.")), "hist"),
        (entry("борщ", classification="borrowing", attestations=_ESUM_BORROWING), "borr"),
        (entry("standard", classification="standard"), None),
    ]

    assert [classification_code(row) for row, _ in cases] == [
        expected for _, expected in cases
    ]


def test_classification_code_never_trusts_unscoped_stored_fields() -> None:
    """#9603 negative controls: stale severity, bare classifications, shadows."""
    cases = [
        entry("stale-red", warning_severity="russianism_red"),
        entry("shadow", classification="unknown", is_russianism=True),
        entry("stale-calque", warning_severity="calque_yellow"),
        entry("arch", classification="authentic-archaism"),
        entry("dial", classification="dialect"),
        entry("hist", classification="historism"),
        entry("borr", classification="borrowing"),
        # The modern dictionary labels only one sense / leaves the headword unlabelled.
        entry("диван", classification="historism", sum20="ДИВА́Н, у, ч. 1. іст. Рада. 2. Меблі."),
        entry("город", classification="authentic-archaism", sum20="ГОРО́Д, а, ч. Ділянка землі."),
        # A curated sense-restricted record is contextual; a bare one is unresolved.
        entry("біля", classification="standard", curated_calque={"kind": "sense_restricted", "source": ["litvinova-7"]}),
        entry("x", classification="calque", curated_calque={"kind": "lexical", "source": ["ua-gec"]}),
        # D05: a citation is not evidence; ``participle`` and unknown kinds state no scope.
        entry("x", classification="calque", curated_calque={"kind": "lexical", "source": ["antonenko-p044"]}),
        entry("x", classification="calque", curated_calque={**_named("x"), "kind": "participle"}),
        entry("x", classification="calque", curated_calque={**_named("x"), "kind": "unspecified"}),
        # The excerpt must name this headword.
        entry("y", classification="russianism", is_russianism=True, curated_calque=_named("x")),
        # D04: a card for another headword binds nothing.
        entry("живий", classification="historism", sum20="ВО́ЗНИЙ, ного, ч., іст. Судовий урядовець."),
    ]
    assert [classification_code(row) for row in cases] == [None] * len(cases)


def test_russianism_does_not_override_treasured_authentic_classifications() -> None:
    card = sum20("другоє", "заст.")
    assert (
        classification_code(
            entry("другоє", classification="authentic-archaism", is_russianism=True, sum20=card)
        )
        == "arch"
    )
    assert (
        classification_code(
            entry("ґазда", classification="dialect", is_russianism=True, sum20=sum20("ґазда", "діал."))
        )
        == "dial"
    )
    assert (
        classification_code(
            entry("осавул", classification="historism", is_russianism=True, sum20=sum20("осавул", "іст."))
        )
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
                sum20=card,
            )
        )
        == "arch"
    )


def test_browse_meta_counts_and_shards() -> None:
    rows = build_index(
        [
            entry("абетка", gloss="alphabet"),
            entry("архаїзм", gloss="archaism", classification="authentic-archaism", sum20=sum20("архаїзм", "заст.")),
            entry("бета", gloss="beta", classification="russianism", is_russianism=True, curated_calque=_named("бета")),
            entry("борщ", gloss="borshch", classification="borrowing", attestations=_ESUM_BORROWING),
            _avoid_entry("всьо", "avoid all"),
            entry("гетьман", gloss="hetman", classification="historism", sum20=sum20("гетьман", "іст.")),
            entry("ґанок", gloss="porch", classification="dialect", sum20=sum20("ґанок", "діал.")),
            entry("ґазда", gloss="host", classification="dialect", sum20=sum20("ґазда", "діал.")),
            entry("калька", gloss="calque", classification="calque", curated_calque=_named("калька")),
        ]
    )

    meta, shards, flagged = build_browse_outputs(rows)

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

    assert flagged == [
        {"l": "архаїзм", "s": "архаїзм", "g": "archaism", "c": None, "cls": "arch", "letter": "А"},
        {"l": "бета", "s": "бета", "g": "beta", "c": None, "cls": "rus", "letter": "Б"},
        {"l": "борщ", "s": "борщ", "g": "borshch", "c": None, "cls": "borr", "letter": "Б"},
        {"l": "всьо", "s": "всьо", "g": "avoid all", "c": None, "cls": "avoid", "letter": "В"},
        {"l": "гетьман", "s": "гетьман", "g": "hetman", "c": None, "cls": "hist", "letter": "Г"},
        {"l": "ґазда", "s": "ґазда", "g": "host", "c": None, "cls": "dial", "letter": "Ґ"},
        {"l": "ґанок", "s": "ґанок", "g": "porch", "c": None, "cls": "dial", "letter": "Ґ"},
        {"l": "калька", "s": "калька", "g": "calque", "c": None, "cls": "calq", "letter": "К"},
    ]

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
    search_shards_out = tmp_path / "search-shards.json"
    search_shard_dir = tmp_path / "search-shards"
    meta_out = tmp_path / "meta.json"
    flagged_out = tmp_path / "flagged.json"
    browse_dir = tmp_path / "browse"
    manifest.write_text(
        json.dumps(
            {
                "entries": [
                    entry("арка", gloss="arch"),
                    _avoid_entry("всьо", "avoid all"),
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
                "--search-shards-out",
                str(search_shards_out),
                "--search-shard-dir",
                str(search_shard_dir),
                "--browse-meta-out",
            str(meta_out),
            "--browse-flagged-out",
            str(flagged_out),
            "--browse-dir",
            str(browse_dir),
            ]
        )
        == 0
    )

    search_rows = json.loads(search_out.read_text(encoding="utf-8"))
    search_shards = json.loads(search_shards_out.read_text(encoding="utf-8"))
    search_shard = json.loads((search_shard_dir / "u0432.json").read_text(encoding="utf-8"))
    meta = json.loads(meta_out.read_text(encoding="utf-8"))
    flagged = json.loads(flagged_out.read_text(encoding="utf-8"))
    shard = json.loads((browse_dir / "В.json").read_text(encoding="utf-8"))

    assert search_rows[1]["cls"] == "avoid"
    assert search_shards["total"] == 2
    assert search_shards["shards"]["u0432"]["count"] == 1
    assert search_shard == [search_rows[1]]
    assert meta["total"] == 2
    assert meta["chipCounts"] == {"avoid": 1}
    assert flagged == [{"l": "всьо", "s": "всьо", "g": "avoid all", "c": None, "cls": "avoid", "letter": "В"}]
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


def test_committed_browse_records_remain_distinct_from_article_search_entries() -> None:
    search_rows = json.loads((PROJECT_ROOT / DEFAULT_SEARCH_OUT).read_text(encoding="utf-8"))
    meta = json.loads((PROJECT_ROOT / DEFAULT_BROWSE_META_OUT).read_text(encoding="utf-8"))
    letter_counts = meta["letterCounts"]

    assert set(letter_counts) == set(UKRAINIAN_ALPHABET)
    # Browse keeps legacy route records for compatibility; the DB-derived
    # search index contains reviewed articles only and is the only surface
    # whose count is an entry total.
    assert all("t" in row for row in search_rows)
    assert meta["total"] >= len(search_rows)

    shard_total = 0
    for letter in UKRAINIAN_ALPHABET:
        shard_path = PROJECT_ROOT / DEFAULT_BROWSE_DIR / f"{letter}.json"
        rows = json.loads(shard_path.read_text(encoding="utf-8")) if shard_path.exists() else []
        assert len(rows) == letter_counts[letter]
        shard_total += len(rows)

    assert shard_total == meta["total"]


def test_legacy_run_refuses_to_overwrite_article_index(tmp_path, monkeypatch) -> None:
    """A plain (manifest-lemma) run must not clobber the DB-derived articles index (#5080)."""
    import scripts.audit.generate_search_index as gsi

    article_out = tmp_path / "lexicon-search-index.json"
    article_out.write_text(json.dumps([{"t": "Стаття", "l": "стаття"}]), encoding="utf-8")
    monkeypatch.setattr(gsi, "DEFAULT_SEARCH_OUT", article_out)

    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"entries": []}), encoding="utf-8")

    with pytest.raises(SystemExit, match="refusing legacy manifest-lemma run"):
        gsi.main(["--manifest", str(manifest)])

    # Lemma-format existing file (no "t") does NOT trip the guard.
    article_out.write_text(json.dumps([{"l": "стаття", "s": "стаття"}]), encoding="utf-8")
    rc = gsi.main(
        [
            "--manifest", str(manifest),
            "--aliases-out", str(tmp_path / "aliases.json"),
            "--search-shards-out", str(tmp_path / "shards.json"),
            "--search-shard-dir", str(tmp_path / "shard-dir"),
            "--browse-meta-out", str(tmp_path / "browse-meta.json"),
            "--browse-flagged-out", str(tmp_path / "browse-flagged.json"),
            "--browse-dir", str(tmp_path / "browse"),
        ]
    )
    assert rc == 0


def test_db_mode_writes_browse_artifacts(tmp_path: Path) -> None:
    db = atlas_db_fixture(tmp_path)
    search_out = tmp_path / "search.json"
    aliases_out = tmp_path / "aliases.json"
    search_shards_out = tmp_path / "search-shards.json"
    meta_out = tmp_path / "browse-meta.json"
    flagged_out = tmp_path / "browse-flagged.json"
    browse_dir = tmp_path / "browse"

    assert (
        main(
            [
                "--db",
                str(db),
                "--out",
                str(search_out),
                "--aliases-out",
                str(aliases_out),
                "--search-shards-out",
                str(search_shards_out),
                "--browse-meta-out",
                str(meta_out),
                "--browse-flagged-out",
                str(flagged_out),
                "--browse-dir",
                str(browse_dir),
            ]
        )
        == 0
    )

    _, _, counts = build_atlas_db_search_artifacts(db)
    meta = json.loads(meta_out.read_text(encoding="utf-8"))
    flagged = json.loads(flagged_out.read_text(encoding="utf-8"))
    search_rows = json.loads(search_out.read_text(encoding="utf-8"))

    assert counts["reviewed_entries"] == 2
    assert len(search_rows) == 2
    assert meta["schema"] == "atlas-browse-meta"
    assert meta["total"] == 2
    assert meta["letterCounts"]["А"] == 1
    assert meta["letterCounts"]["І"] == 1
    assert flagged == []
    assert json.loads((browse_dir / "А.json").read_text(encoding="utf-8")) == [
        {
            "l": "автобус",
            "s": "автобус",
            "g": "bus",
            "c": None,
            "hay": "автобус bus avtobus",
        },
    ]
    assert json.loads((browse_dir / "І.json").read_text(encoding="utf-8")) == [
        {
            "l": "Іван",
            "s": "іван",
            "g": "Ivan",
            "c": None,
            "hay": "іван ivan ivan",
        },
    ]


def test_browse_staleness_guard_fires_when_browse_would_stay_pinned(tmp_path: Path) -> None:
    stale_meta = tmp_path / "browse-meta.json"
    stale_meta.write_text(json.dumps({"total": 1}), encoding="utf-8")

    with pytest.raises(SystemExit, match="browse-meta stale"):
        guard_browse_staleness(stale_meta, reviewed_article_count=5, will_refresh_browse=False)


def test_browse_staleness_guard_allows_refresh_when_browse_will_be_rewritten(tmp_path: Path) -> None:
    stale_meta = tmp_path / "browse-meta.json"
    stale_meta.write_text(json.dumps({"total": 1}), encoding="utf-8")

    guard_browse_staleness(stale_meta, reviewed_article_count=5, will_refresh_browse=True)


def _db_entry(
    lemma: str,
    heritage_status: dict[str, object],
    *,
    cards: list[dict[str, object]] | None = None,
    primary_source: str = "built_vocabulary",
    gloss: str = "gloss",
) -> dict[str, object]:
    row: dict[str, object] = {
        "lemma": lemma,
        "url_slug": lemma,
        "gloss": gloss,
        "primary_source": primary_source,
        "heritage_status": heritage_status,
    }
    if cards:
        row["enrichment"] = {"definition_cards": cards}
    return row


def test_db_mode_browse_flags_only_lemma_scoped_named_labels(tmp_path: Path) -> None:
    """#9603: stored DB records keep source scope through the browse projection."""
    entries = [
        # Recommended replacement of «являтися» (reverse calque) with stale severity.
        _db_entry(
            "бути",
            {
                "classification": "standard",
                "attestations": [{"source": "VESUM", "ref": "бути"}],
                "warning_severity": "calque_yellow",
                "reverse_calques": [{"calque": "являтися", "kind": "sense_restricted"}],
            },
        ),
        # Reconciled Russianism with only a replacement suggestion.
        _db_entry(
            "вид",
            {
                "classification": "russianism",
                "is_russianism": True,
                "attestations": [{"source": "standard_alternative", "ref": "вигляд"}],
                "calque_warning": {"standard_alternatives": ["вигляд"]},
                "warning_severity": "russianism_red",
            },
        ),
        # Historism marker on one СУМ-20 sense only.
        _db_entry(
            "диван",
            {"classification": "historism", "warning_severity": "treasured"},
            cards=[{"id": "sum20", "definitions": ["ДИВА́Н, у, ч. 1. іст. Рада. 2. Меблі."]}],
        ),
        # D04: a СУМ-20 card for another headword.
        _db_entry(
            "живий",
            {"classification": "historism", "warning_severity": "treasured"},
            cards=[{"id": "sum20", "definitions": ["ВО́ЗНИЙ, ного, ч., іст. Судовий урядовець."]}],
        ),
        # D01: actual stored слідуючий shape; the avoid list and a drill about «следующий» bind nothing.
        _db_entry(
            "слідуючий",
            {
                "classification": "russianism",
                "is_russianism": True,
                "warning_severity": "russianism_red",
                "curated_calque": {
                    "kind": "lexical",
                    "corrections": ["наступний"],
                    "source": ["voron-9", "zabolotnyi-5"],
                    "evidence": ["9-klas-ukrajinska-mova-voron-2017_s0232: следующий — тут: наступний; ... наступний"],
                },
            },
            primary_source="surzhyk_to_avoid",
            gloss="avoid: наступний",
        ),
        # Positive controls: СУМ-20 headword label, an ЕСУМ headword historism
        # with the article's referent (D02) and a lexical Russianism bound by a
        # passage naming the headword (sources MCP: style_guide id 44).
        _db_entry(
            "возний",
            {"classification": "historism", "warning_severity": "treasured"},
            cards=[{"id": "sum20", "definitions": ["ВО́ЗНИЙ, ного, ч., іст. Судовий урядовець."]}],
        ),
        _db_entry(
            "гридь",
            {
                "classification": "historism",
                "warning_severity": "treasured",
                "attestations": [
                    {
                        "source": "esum",
                        "ref": "гридь:1:592",
                        "word": "гридь",
                        "detail": "гридь (іст.) «нижча верхівка княжої дружини», грйдень «охоронець князя»",
                    }
                ],
            },
            gloss="У стародавній Русі — нижча верства княжої дружини.",
        ),
        _db_entry(
            "міроприємство",
            {
                "classification": "russianism",
                "is_russianism": True,
                "warning_severity": "russianism_red",
                # Actual stored shape: the excerpt names only the etymon and the
                # replacement; the current reviewed judgment (p031) binds the word.
                "curated_calque": {
                    "kind": "lexical",
                    "corrections": ["захід", "заходи"],
                    "source": ["antonenko-p044", "glazova-10"],
                    "evidence": ["Антоненко-Давидович: Відповідником до російських мера, мероприятие є захід"],
                },
            },
            primary_source="surzhyk_to_avoid",
            gloss="avoid: захід",
        ),
        # Round 3: ЕСУМ 5:580 marker followed by a parenthetical explanation.
        _db_entry(
            "тіун",
            {
                "classification": "historism",
                "warning_severity": "treasured",
                "attestations": [
                    {
                        "source": "esum",
                        "ref": "тіун:5:580",
                        "word": "тіун",
                        "detail": "тіун (іст.) (назва ряду службових осіб на Русі управитель княжим господарством)",
                    }
                ],
            },
            gloss="У Київській Русі — господарський управитель князя, бояр.",
        ),
        # Old stored являтися record citing s0162: sense-scoped, never a browse flag.
        _db_entry(
            "являтися",
            {
                "classification": "standard",
                "warning_severity": "calque_yellow",
                "curated_calque": {
                    "kind": "sense_restricted",
                    "corrections": ["бути", "є"],
                    "evidence": ["9-klas-ukrajinska-mova-avramenko-2017_s0162: Неправильно: являтися переможцем"],
                },
            },
        ),
    ]
    db = atlas_db_fixture(tmp_path, entries=entries)
    flagged_out = tmp_path / "browse-flagged.json"
    meta_out = tmp_path / "browse-meta.json"
    assert (
        main(
            [
                "--db",
                str(db),
                "--out",
                str(tmp_path / "search.json"),
                "--aliases-out",
                str(tmp_path / "aliases.json"),
                "--search-shards-out",
                str(tmp_path / "search-shards.json"),
                "--browse-meta-out",
                str(meta_out),
                "--browse-flagged-out",
                str(flagged_out),
                "--browse-dir",
                str(tmp_path / "browse"),
            ]
        )
        == 0
    )
    flagged = json.loads(flagged_out.read_text(encoding="utf-8"))
    assert [(row["l"], row["cls"]) for row in flagged] == [
        ("возний", "hist"),
        ("гридь", "hist"),
        ("міроприємство", "avoid"),
        ("тіун", "hist"),
    ]
    meta = json.loads(meta_out.read_text(encoding="utf-8"))
    assert meta["chipCounts"] == {"avoid": 1, "hist": 3}
    # The projection entry pages consume: current proof plus its input digests.
    usage = meta["usageSources"]
    assert usage["schema"] == "atlas-usage-sources.v1"
    assert set(usage["inputs"]) == {"registry/lexicon/heritage_pairs.yaml", "scripts/lexicon/calque_corrections.py"}
    assert [item["locator"] for item in usage["records"]["являтися"]["citations"]] == [
        "9-klas-ukrajinska-mova-avramenko-2017_s0159"
    ]
    # Editorial gloss metadata: verbatim only on the lemma-bound warning, a
    # qualified note in browse and search otherwise; ordinary glosses unchanged.
    browse = {row["l"]: row for path in (tmp_path / "browse").glob("*.json") for row in json.loads(path.read_text(encoding="utf-8"))}
    search = {row["l"]: row for row in json.loads((tmp_path / "search.json").read_text(encoding="utf-8"))}
    note = "примітка Атласу: радять «наступний»; обсяг застереження не встановлено"
    assert (browse["слідуючий"]["g"], search["слідуючий"]["g"]) == (note, note)
    assert "avoid:" not in browse["слідуючий"]["hay"]
    assert (browse["міроприємство"]["g"], search["міроприємство"]["g"]) == ("avoid: захід", "avoid: захід")
    assert (browse["тіун"]["g"], search["тіун"]["g"]) == ("У Київській Русі — господарський управитель князя, бояр.",) * 2


def test_display_gloss_qualifies_editorial_metadata_outside_lemma_scope() -> None:
    """#9603: an editorial gloss is a word-wide instruction only for a bound Russianism or calque."""
    for code in ("avoid", "rus", "calq"):
        assert display_gloss("avoid: захід", code) == "avoid: захід"
    for code in (None, "hist", "arch"):
        assert display_gloss("avoid: наступний", code) == "примітка Атласу: радять «наступний»; обсяг застереження не встановлено"
    assert display_gloss(" RUS:  інший ", None) == "примітка Атласу: русизм — «інший»; обсяг застереження не встановлено"
    assert display_gloss("calque: брати участь", None) == "примітка Атласу: калька — «брати участь»; обсяг застереження не встановлено"
    switch = "to switch over (Russian calque; standard Ukrainian: перемкнути)"
    assert display_gloss(switch, "calq") == switch
    for code in (None, "hist"):
        assert display_gloss(switch, code) == (
            "to switch over (примітка Атласу: «Russian calque; standard Ukrainian: перемкнути»; обсяг застереження не встановлено)"
        )
    # Ordinary glosses, parentheticals naming Russia or avoidance, empty and non-string values pass through.
    for gloss in ("next", "to avoid: dodge", "avoid:", None, 3, "RF (Russian Federation)", "to save (avoid the expenditure of)"):
        assert display_gloss(gloss, None) == gloss


def test_committed_browse_and_search_show_scoped_editorial_glosses() -> None:
    """#9603: committed artifacts carry the projected слідуючий/діюча glosses, not raw avoid: metadata."""
    search = {row["s"]: row["g"] for row in json.loads((PROJECT_ROOT / "site/src/data/lexicon-search-index.json").read_text(encoding="utf-8"))}
    shard = {row["s"]: row for row in json.loads((PROJECT_ROOT / "site/public/lexicon/browse/С.json").read_text(encoding="utf-8"))}
    note = "примітка Атласу: радять «наступний»; обсяг застереження не встановлено"
    assert search["слідуючий"] == shard["слідуючий"]["g"] == note
    assert search["діюча"] == "примітка Атласу: радять «чинна»; обсяг застереження не встановлено"
    assert search["міроприємство"] == "avoid: захід"
    assert not [slug for slug, gloss in search.items() if isinstance(gloss, str) and gloss.startswith(("avoid:", "rus:", "calque:")) and slug != "міроприємство"]
    for slug, letter in (("переключити", "П"), ("кримчанин", "К"), ("просвітитель", "П")):
        shard = {row["s"]: row for row in json.loads((PROJECT_ROOT / f"site/public/lexicon/browse/{letter}.json").read_text(encoding="utf-8"))}
        assert search[slug] == shard[slug]["g"] and "(примітка Атласу: «Russian calque; standard Ukrainian:" in search[slug]
        assert "(russian calque" not in shard[slug]["hay"]


def test_committed_usage_sources_are_bound_to_their_passages() -> None:
    """#9603: every committed judgment keeps the digest of the passage it quotes."""
    meta = json.loads((PROJECT_ROOT / DEFAULT_BROWSE_META_OUT).read_text(encoding="utf-8"))
    records = meta["usageSources"]["records"]
    digest = generate_search_index._HERITAGE_CLASSIFIER.source_text_digest
    normalize = generate_search_index._HERITAGE_CLASSIFIER._normalize_word
    assert records["міроприємство"]["kind"] == "lexical"
    for headword, record in records.items():
        assert record["judgments"] or record["citations"]
        for judgment in record["judgments"]:
            assert normalize(judgment["rejectedForm"]) == headword
            assert judgment["passageSha256"] == digest(judgment["passage"])


def test_committed_browse_flags_never_brand_named_regressions() -> None:
    """#9603 regression seeds stay out of the committed browse filters."""
    flagged = json.loads(
        (PROJECT_ROOT / "site/src/data/lexicon-browse-flagged.json").read_text(encoding="utf-8")
    )
    flagged_lemmas = {row["l"] for row in flagged}
    for lemma in ("бути", "є", "голова", "другий", "вид", "або", "диван", "город"):
        assert lemma not in flagged_lemmas
    assert all(row["cls"] in {"avoid", "rus", "calq", "arch", "dial", "hist", "borr"} for row in flagged)


def test_definition_cards_for_slug_reads_payload_or_fails_closed() -> None:
    import sqlite3

    from scripts.audit.generate_search_index import _definition_cards_for_slug

    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE enrichment (slug TEXT, section TEXT, payload_json TEXT)")
    conn.execute("INSERT INTO enrichment VALUES ('a', 'definition_cards', '[{\"id\": \"sum20\"}]')")
    conn.execute("INSERT INTO enrichment VALUES ('b', 'definition_cards', 'not json')")
    assert _definition_cards_for_slug(conn, "a") == [{"id": "sum20"}]
    assert _definition_cards_for_slug(conn, "b") is None
    assert _definition_cards_for_slug(conn, "missing") is None
