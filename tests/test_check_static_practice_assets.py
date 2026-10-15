from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

import scripts.audit.check_static_practice_assets as check_static_practice_assets
from scripts.audit.check_static_practice_assets import check_assets
from scripts.audit.daily_cefr import CEFR_LEVELS
from scripts.audit.generate_daily_pool import CEFR_LEVELS as GENERATOR_CEFR_LEVELS
from tests.helpers.restore_import_state import restore_import_state
from tests.project_python import project_python

pytestmark = pytest.mark.reads_content

DRILL_MODES = ("stress", "classify", "paradigm", "synonym", "heritage", "paronym", "antonym")


def test_daily_cefr_levels_match_generator_ssot() -> None:
    from scripts.audit.check_static_practice_assets import DAILY_CEFR_LEVELS

    assert DAILY_CEFR_LEVELS == CEFR_LEVELS == GENERATOR_CEFR_LEVELS
    assert {"A1", "A2", "B1", "B2", "C1", "C2"} == DAILY_CEFR_LEVELS


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _budget() -> dict[str, int | bool]:
    return {
        "rawBytes": 100,
        "gzipBytes": 80,
        "rawLimitBytes": 550_000,
        "gzipLimitBytes": 140_000,
        "ok": True,
    }


def _write_daily_pool(path: Path) -> None:
    _write_json(
        path,
        [
            {
                "lemma": "дім",
                "slug": "дім",
                "gloss": "house",
                "k": "vyv",
                "cefr": "A1",
                "weight": 3,
            },
            {
                "lemma": "авось",
                "slug": "авось",
                "gloss": "avoid: ану ж",
                "k": "avoid",
                "weight": 2,
            },
        ],
    )


def _write_reviewed_sources(path: Path, *, reviewed: bool = False) -> None:
    rows = [{"status": "reviewed", "path": "curriculum/l2-uk-en/a1/vocabulary/home.yaml"}] if reviewed else []
    _write_json(path, {"reviewed": rows})


def _write_level(practice_dir: Path, *, level: str = "A1", with_cloze: bool = False) -> None:
    deck_version = "atlas-practice-v1-test"
    cloze_id = "dim-cloze-1"
    modes = ["flashcards", "matching", "choice"]
    cloze_ids: list[str] = []
    cloze_rows: list[dict[str, object]] = []
    if with_cloze:
        modes.append("cloze")
        cloze_ids = [cloze_id]
        cloze_rows = [
            {
                "clozeId": cloze_id,
                "lemmaId": "dim",
                "sentenceFrameId": "home-1",
                "sentence": "Я живу у ___.",
                "blankCase": "locative",
                "form": "домі",
                "caseRule": {"caseLabel": "місцевий", "feedback": "у + місцевий"},
                "clozeEn": "I live in a house.",
                "options": [
                    {"label": "домі", "kind": "answer", "case": "locative", "lemmaId": "dim"},
                    {"label": "місті", "kind": "decoy", "case": "locative", "lemmaId": "misto"},
                    {"label": "школі", "kind": "decoy", "case": "locative", "lemmaId": "shkola"},
                    {"label": "кімнаті", "kind": "decoy", "case": "locative", "lemmaId": "kimnata"},
                ],
                "provenance": {
                    "status": "reviewed",
                    "path": "curriculum/l2-uk-en/a1/vocabulary/home.yaml",
                },
            }
        ]

    _write_json(
        practice_dir / f"practice-index.{level}.json",
        {
            "schema": "atlas-practice-index",
            "schemaVersion": 1,
            "deckVersion": deck_version,
            "level": level,
            "source": "fixture",
            "sizeBudget": _budget(),
            "counts": {
                "lexemes": 1,
                "cloze": len(cloze_rows),
                "clozeEligibleLexemes": 1 if with_cloze else 0,
                "clozeCoverage": 1.0 if with_cloze else 0.0,
                "modeCounts": {
                    "cloze": len(cloze_rows),
                    **{mode: 0 for mode in DRILL_MODES},
                },
                "modeCoverage": {
                    "cloze": 1.0 if with_cloze else 0.0,
                    **{mode: 0.0 for mode in DRILL_MODES},
                },
            },
            "items": [
                {
                    "lemmaId": "dim",
                    "lemma": "дім",
                    "cefr": level,
                    "modes": modes,
                    "hasCloze": bool(cloze_ids),
                    "clozeIds": cloze_ids,
                    "newOrder": 0,
                }
            ],
        },
    )
    for mode in DRILL_MODES:
        _write_json(
            practice_dir / f"practice-{mode}.{level}.json",
            {
                "schema": f"atlas-practice-{mode}",
                "schemaVersion": 1,
                "deckVersion": deck_version,
                "level": level,
                "source": "fixture",
                "sizeBudget": _budget(),
                mode: [],
            },
        )
    _write_json(
        practice_dir / f"practice-lexemes.{level}.json",
        {
            "schema": "atlas-practice-lexemes",
            "schemaVersion": 1,
            "deckVersion": deck_version,
            "level": level,
            "source": "fixture",
            "sizeBudget": _budget(),
            "lexemes": [
                {
                    "lemmaId": "dim",
                    "lemma": "дім",
                    "lemmaPlain": "дім",
                    "ipa": None,
                    "gloss": "house",
                    "pos": "noun",
                    "cefr": level,
                    "heritage": None,
                    "severity": None,
                    "paradigm": {"cases": {}},
                }
            ],
        },
    )
    _write_json(
        practice_dir / f"practice-cloze.{level}.json",
        {
            "schema": "atlas-practice-cloze",
            "schemaVersion": 1,
            "deckVersion": deck_version,
            "level": level,
            "source": "fixture",
            "sizeBudget": _budget(),
            "cloze": cloze_rows,
        },
    )


def _add_heritage_item(practice_dir: Path, *, options: list[dict[str, object]], level: str = "A1") -> None:
    heritage_path = practice_dir / f"practice-heritage.{level}.json"
    heritage_payload = json.loads(heritage_path.read_text(encoding="utf-8"))
    heritage_payload["heritage"] = [
        {
            "heritageId": "her_fixture",
            "lemmaId": "dim",
            "srsKey": "dim::heritage",
            "lemma": "дім",
            "nativeLemma": "дім",
            "calqueLabel": "дом",
            "kind": "lexical",
            "prompt": "Я бачу ___.",
            "answer": "дім",
            "calque": "дом",
            "origin": "fixture",
            "frameIndex": 1,
            "cefr": level,
            "options": options,
            "rationale": "fixture rationale",
            "citations": ["fixture:heritage"],
            "corrections": ["дім"],
            "sourceFamily": "fixture",
        }
    ]
    _write_json(heritage_path, heritage_payload)

    index_path = practice_dir / f"practice-index.{level}.json"
    index_payload = json.loads(index_path.read_text(encoding="utf-8"))
    index_payload["items"][0]["modes"].append("heritage")
    index_payload["counts"]["modeCounts"]["heritage"] = 1
    index_payload["counts"]["modeCoverage"]["heritage"] = 1.0
    _write_json(index_path, index_payload)


def _add_synonym_item(practice_dir: Path, *, level: str = "A2") -> None:
    synonym_path = practice_dir / f"practice-synonym.{level}.json"
    synonym_payload = json.loads(synonym_path.read_text(encoding="utf-8"))
    synonym_payload["synonym"] = [
        {
            "synonymId": "syn_fixture",
            "lemmaId": "dim",
            "targetLemmaId": "slovo",
            "polarity": "synonym",
            "prompt": "дім",
            "answer": "слово",
            "options": [
                {"label": "слово", "lemmaId": "slovo", "kind": "answer"},
                {"label": "сад", "lemmaId": "sad", "kind": "distractor"},
                {"label": "ліс", "lemmaId": "lis", "kind": "distractor"},
                {"label": "місто", "lemmaId": "misto", "kind": "distractor"},
            ],
            "source": "fixture",
        }
    ]
    _write_json(synonym_path, synonym_payload)

    index_path = practice_dir / f"practice-index.{level}.json"
    index_payload = json.loads(index_path.read_text(encoding="utf-8"))
    index_payload["counts"]["modeCounts"]["synonym"] = 1
    index_payload["counts"]["modeCoverage"]["synonym"] = 1.0
    _write_json(index_path, index_payload)


def _fixture_paths(tmp_path: Path) -> tuple[Path, Path, Path]:
    daily_pool = tmp_path / "lexicon-daily-pool.json"
    practice_dir = tmp_path / "lexicon"
    reviewed_sources = tmp_path / "lexicon-practice-reviewed-sources.json"
    _write_daily_pool(daily_pool)
    _write_reviewed_sources(reviewed_sources)
    _write_level(practice_dir)
    return daily_pool, practice_dir, reviewed_sources


def test_check_assets_accepts_static_fallback_assets(tmp_path: Path) -> None:
    daily_pool, practice_dir, reviewed_sources = _fixture_paths(tmp_path)

    summary = check_assets(
        daily_pool=daily_pool,
        practice_dir=practice_dir,
        reviewed_sources=reviewed_sources,
        levels=("A1",),
        min_daily_pool_size=2,
        min_practice_lexemes_per_level=1,
    )

    assert summary["ok"] is True
    assert summary["daily"]["count"] == 2
    assert summary["practice"]["A1"]["lexemes"] == 1
    assert summary["total_cloze"] == 0


def test_check_assets_fails_closed_for_unallowlisted_cloze(tmp_path: Path) -> None:
    daily_pool = tmp_path / "lexicon-daily-pool.json"
    practice_dir = tmp_path / "lexicon"
    reviewed_sources = tmp_path / "lexicon-practice-reviewed-sources.json"
    _write_daily_pool(daily_pool)
    _write_reviewed_sources(reviewed_sources)
    _write_level(practice_dir, with_cloze=True)

    summary = check_assets(
        daily_pool=daily_pool,
        practice_dir=practice_dir,
        reviewed_sources=reviewed_sources,
        levels=("A1",),
        min_daily_pool_size=2,
        min_practice_lexemes_per_level=1,
    )

    assert summary["ok"] is False
    assert summary["total_cloze"] == 1
    assert any("not in reviewed source allowlist" in error for error in summary["errors"])
    assert any("reviewed allowlist is empty" in error for error in summary["errors"])


def test_check_assets_accepts_allowlisted_cloze(tmp_path: Path) -> None:
    daily_pool = tmp_path / "lexicon-daily-pool.json"
    practice_dir = tmp_path / "lexicon"
    reviewed_sources = tmp_path / "lexicon-practice-reviewed-sources.json"
    _write_daily_pool(daily_pool)
    _write_reviewed_sources(reviewed_sources, reviewed=True)
    _write_level(practice_dir, with_cloze=True)

    summary = check_assets(
        daily_pool=daily_pool,
        practice_dir=practice_dir,
        reviewed_sources=reviewed_sources,
        levels=("A1",),
        min_daily_pool_size=2,
        min_practice_lexemes_per_level=1,
    )

    assert summary["ok"] is True
    assert summary["reviewed_sources"] == 1
    assert summary["total_cloze"] == 1


def test_check_assets_rejects_heritage_option_metadata_leaks(tmp_path: Path) -> None:
    daily_pool, practice_dir, reviewed_sources = _fixture_paths(tmp_path)
    _add_heritage_item(
        practice_dir,
        options=[
            {"label": "дім", "kind": "answer", "lemmaId": "dim", "pos": "noun"},
            {"label": "дом", "kind": "calque"},
            {"label": "сад", "kind": "distractor", "lemmaId": "sad", "pos": "noun"},
            {"label": "ліс", "kind": "distractor", "lemmaId": "lis", "pos": "noun"},
        ],
    )

    summary = check_assets(
        daily_pool=daily_pool,
        practice_dir=practice_dir,
        reviewed_sources=reviewed_sources,
        levels=("A1",),
        min_daily_pool_size=2,
        min_practice_lexemes_per_level=1,
    )

    assert summary["ok"] is False
    assert any("heritage options must expose only label" in error for error in summary["errors"])


def test_check_assets_reports_bad_daily_pool_rows(tmp_path: Path) -> None:
    daily_pool, practice_dir, reviewed_sources = _fixture_paths(tmp_path)
    _write_json(
        daily_pool,
        [
            {
                "lemma": "дім",
                "slug": "дім",
                "gloss": "house",
                "k": "vyv",
                # Not a CEFR band — B2/C1/C2 are valid after #6728 true-CEFR emission.
                "cefr": "X9",
            },
            {
                "lemma": "інший",
                "slug": "дім",
                "gloss": "",
                "k": "vyv",
            },
        ],
    )

    summary = check_assets(
        daily_pool=daily_pool,
        practice_dir=practice_dir,
        reviewed_sources=reviewed_sources,
        levels=("A1",),
        min_daily_pool_size=2,
        min_practice_lexemes_per_level=1,
    )

    assert summary["ok"] is False
    assert any("outside daily levels" in error for error in summary["errors"])
    assert any("duplicate slug" in error for error in summary["errors"])
    assert any("missing learner gloss" in error for error in summary["errors"])
    assert any("missing CEFR for non-avoid" in error for error in summary["errors"])


def test_check_assets_accepts_a1_through_c2_daily_cefr(tmp_path: Path) -> None:
    """#6728: validator must admit the same A1–C2 set the generator emits."""
    daily_pool, practice_dir, reviewed_sources = _fixture_paths(tmp_path)
    _write_json(
        daily_pool,
        [
            {
                "lemma": "дім",
                "slug": "дім",
                "gloss": "house",
                "k": "vyv",
                "cefr": "A1",
                "weight": 3,
            },
            {
                "lemma": "абсурд",
                "slug": "абсурд",
                "gloss": "absurdity",
                "k": "vyv",
                "cefr": "B2",
                "weight": 2,
            },
            {
                "lemma": "абстракція",
                "slug": "абстракція",
                "gloss": "abstraction",
                "k": "vyv",
                "cefr": "C1",
                "weight": 2,
            },
            {
                "lemma": "апорія",
                "slug": "апорія",
                "gloss": "aporia",
                "k": "vyv",
                "cefr": "C2",
                "weight": 1,
            },
        ],
    )

    summary = check_assets(
        daily_pool=daily_pool,
        practice_dir=practice_dir,
        reviewed_sources=reviewed_sources,
        levels=("A1",),
        min_daily_pool_size=4,
        min_practice_lexemes_per_level=1,
    )

    assert not any("outside daily levels" in error for error in summary["errors"])
    assert summary["daily"]["by_cefr"] == {"A1": 1, "B2": 1, "C1": 1, "C2": 1}


def test_check_assets_reports_schema_and_index_inconsistencies(tmp_path: Path) -> None:
    daily_pool, practice_dir, reviewed_sources = _fixture_paths(tmp_path)
    index_path = practice_dir / "practice-index.A1.json"
    index_payload = json.loads(index_path.read_text(encoding="utf-8"))
    index_payload["schema"] = "wrong-schema"
    index_payload["items"][0]["hasCloze"] = True
    index_payload["items"][0]["modes"] = ["flashcards", "made-up-mode"]
    index_payload["counts"]["lexemes"] = 99
    _write_json(index_path, index_payload)

    summary = check_assets(
        daily_pool=daily_pool,
        practice_dir=practice_dir,
        reviewed_sources=reviewed_sources,
        levels=("A1",),
        min_daily_pool_size=2,
        min_practice_lexemes_per_level=1,
    )

    assert summary["ok"] is False
    assert any("wrong-schema" in error for error in summary["errors"])
    assert any("unknown modes" in error for error in summary["errors"])
    assert any("hasCloze does not match clozeIds" in error for error in summary["errors"])
    assert any("counts.lexemes" in error for error in summary["errors"])


def test_cli_reports_missing_static_shard(tmp_path: Path) -> None:
    daily_pool, practice_dir, reviewed_sources = _fixture_paths(tmp_path)
    (practice_dir / "practice-lexemes.A1.json").unlink()

    result = subprocess.run(
        [
            str(project_python()),
            "scripts/audit/check_static_practice_assets.py",
            "--daily-pool",
            str(daily_pool),
            "--practice-dir",
            str(practice_dir),
            "--reviewed-sources",
            str(reviewed_sources),
            "--levels",
            "A1",
            "--min-daily-pool-size",
            "2",
            "--min-practice-lexemes-per-level",
            "1",
            "--no-run-qa-gate",
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode == 1
    assert "practice-lexemes.A1.json: missing" in result.stdout


def _set_tatoeba_cloze_metadata(practice_dir: Path, *, with_attribution: bool) -> None:
    cloze_path = practice_dir / "practice-cloze.A1.json"
    payload = json.loads(cloze_path.read_text(encoding="utf-8"))
    item = payload["cloze"][0]
    item["provenance"] = {
        "status": "tatoeba",
        "path": "tatoeba:101",
        "license": "CC-BY 2.0 FR",
        "author": "uk-author",
        "sentenceId": 101,
        "enSentenceId": 202,
        "enAuthor": "en-author",
        "enLicense": "CC-BY 2.0 FR",
    }
    if with_attribution:
        item["attribution"] = {
            "source": "Tatoeba",
            "sourceUrl": "https://tatoeba.org/en/sentences/show/101",
            "uk": {"sentenceId": 101, "author": "uk-author", "license": "CC-BY 2.0 FR"},
            "en": {"sentenceId": 202, "author": "en-author", "license": "CC-BY 2.0 FR"},
        }
    _write_json(cloze_path, payload)


def test_check_assets_requires_tatoeba_attribution(tmp_path: Path) -> None:
    daily_pool = tmp_path / "lexicon-daily-pool.json"
    practice_dir = tmp_path / "lexicon"
    reviewed_sources = tmp_path / "lexicon-practice-reviewed-sources.json"
    _write_daily_pool(daily_pool)
    _write_json(reviewed_sources, {"reviewed": [{"status": "tatoeba", "path": "tatoeba:101"}]})
    _write_level(practice_dir, with_cloze=True)
    _set_tatoeba_cloze_metadata(practice_dir, with_attribution=False)

    summary = check_assets(
        daily_pool=daily_pool,
        practice_dir=practice_dir,
        reviewed_sources=reviewed_sources,
        levels=("A1",),
        min_daily_pool_size=2,
        min_practice_lexemes_per_level=1,
    )

    assert summary["ok"] is False
    assert any("missing Tatoeba attribution" in error for error in summary["errors"])


def test_check_assets_accepts_tatoeba_attributed_cloze(tmp_path: Path) -> None:
    daily_pool = tmp_path / "lexicon-daily-pool.json"
    practice_dir = tmp_path / "lexicon"
    reviewed_sources = tmp_path / "lexicon-practice-reviewed-sources.json"
    _write_daily_pool(daily_pool)
    _write_json(reviewed_sources, {"reviewed": [{"status": "tatoeba", "path": "tatoeba:101"}]})
    _write_level(practice_dir, with_cloze=True)
    _set_tatoeba_cloze_metadata(practice_dir, with_attribution=True)
    cloze_path = practice_dir / "practice-cloze.A1.json"
    cloze_payload = json.loads(cloze_path.read_text(encoding="utf-8"))
    cloze_payload["cloze"][0]["provenance"].pop("sentenceId")
    _write_json(cloze_path, cloze_payload)

    summary = check_assets(
        daily_pool=daily_pool,
        practice_dir=practice_dir,
        reviewed_sources=reviewed_sources,
        levels=("A1",),
        min_daily_pool_size=2,
        min_practice_lexemes_per_level=1,
    )

    assert summary["ok"] is True
    assert summary["total_cloze"] == 1


def _retarget_level_lexeme(practice_dir: Path, *, level: str, lemma_id: str, lemma: str) -> None:
    """Point a level's lexeme + index shards at a different lemma so the default
    fixture lemma ('dim') is NOT present at that level."""
    lexemes_path = practice_dir / f"practice-lexemes.{level}.json"
    payload = json.loads(lexemes_path.read_text(encoding="utf-8"))
    payload["lexemes"][0]["lemmaId"] = lemma_id
    payload["lexemes"][0]["lemma"] = lemma
    payload["lexemes"][0]["lemmaPlain"] = lemma
    _write_json(lexemes_path, payload)

    index_path = practice_dir / f"practice-index.{level}.json"
    index_payload = json.loads(index_path.read_text(encoding="utf-8"))
    index_payload["items"][0]["lemmaId"] = lemma_id
    index_payload["items"][0]["lemma"] = lemma
    _write_json(index_path, index_payload)


_VALID_HERITAGE_OPTIONS: list[dict[str, object]] = [
    {"label": "дім"},
    {"label": "дом"},
    {"label": "сад"},
    {"label": "ліс"},
]


def test_heritage_lemma_from_lower_level_shard_is_allowed(tmp_path: Path) -> None:
    """#4720 availability floor: a heritage item floored to A2 may reference a native
    lexeme that lives in the A1 shard — the client loads lexeme shards cumulatively."""
    daily_pool, practice_dir, reviewed_sources = _fixture_paths(tmp_path)  # A1: lemma 'dim'
    _write_level(practice_dir, level="A2")
    _retarget_level_lexeme(practice_dir, level="A2", lemma_id="slovo", lemma="слово")
    # Heritage item at A2 referencing 'dim' (present only in the A1 lexeme shard).
    _add_heritage_item(practice_dir, options=_VALID_HERITAGE_OPTIONS, level="A2")

    summary = check_assets(
        daily_pool=daily_pool,
        practice_dir=practice_dir,
        reviewed_sources=reviewed_sources,
        levels=("A1", "A2"),
        min_daily_pool_size=2,
        min_practice_lexemes_per_level=1,
    )

    assert summary["ok"] is True, summary["errors"]


def test_synonym_lemma_from_lower_level_shard_is_allowed(tmp_path: Path) -> None:
    """B1-floor synonym cards can use a prompt from a lower cumulative shard."""
    daily_pool, practice_dir, reviewed_sources = _fixture_paths(tmp_path)
    _write_level(practice_dir, level="A2")
    _retarget_level_lexeme(practice_dir, level="A2", lemma_id="slovo", lemma="слово")
    _add_synonym_item(practice_dir, level="A2")

    summary = check_assets(
        daily_pool=daily_pool,
        practice_dir=practice_dir,
        reviewed_sources=reviewed_sources,
        levels=("A1", "A2"),
        min_daily_pool_size=2,
        min_practice_lexemes_per_level=1,
    )

    assert summary["ok"] is True, summary["errors"]


def test_heritage_lemma_unknown_at_or_below_level_still_fails(tmp_path: Path) -> None:
    daily_pool, practice_dir, reviewed_sources = _fixture_paths(tmp_path)
    _write_level(practice_dir, level="A2")
    _retarget_level_lexeme(practice_dir, level="A2", lemma_id="slovo", lemma="слово")
    _add_heritage_item(practice_dir, options=_VALID_HERITAGE_OPTIONS, level="A2")

    heritage_path = practice_dir / "practice-heritage.A2.json"
    payload = json.loads(heritage_path.read_text(encoding="utf-8"))
    payload["heritage"][0]["lemmaId"] = "ghost"
    _write_json(heritage_path, payload)

    summary = check_assets(
        daily_pool=daily_pool,
        practice_dir=practice_dir,
        reviewed_sources=reviewed_sources,
        levels=("A1", "A2"),
        min_daily_pool_size=2,
        min_practice_lexemes_per_level=1,
    )

    assert summary["ok"] is False
    assert any("missing from lexeme shards at or below A2" in error for error in summary["errors"])


def test_non_heritage_modes_stay_strictly_same_level(tmp_path: Path) -> None:
    """The cumulative carve-out is heritage-only: a stress item referencing a
    lower-level lexeme must still fail."""
    daily_pool, practice_dir, reviewed_sources = _fixture_paths(tmp_path)
    _write_level(practice_dir, level="A2")
    _retarget_level_lexeme(practice_dir, level="A2", lemma_id="slovo", lemma="слово")

    stress_path = practice_dir / "practice-stress.A2.json"
    payload = json.loads(stress_path.read_text(encoding="utf-8"))
    payload["stress"] = [{"lemmaId": "dim"}]
    _write_json(stress_path, payload)
    index_path = practice_dir / "practice-index.A2.json"
    index_payload = json.loads(index_path.read_text(encoding="utf-8"))
    index_payload["counts"]["modeCounts"]["stress"] = 1
    index_payload["counts"]["modeCoverage"]["stress"] = 1.0
    _write_json(index_path, index_payload)

    summary = check_assets(
        daily_pool=daily_pool,
        practice_dir=practice_dir,
        reviewed_sources=reviewed_sources,
        levels=("A1", "A2"),
        min_daily_pool_size=2,
        min_practice_lexemes_per_level=1,
    )

    assert summary["ok"] is False
    assert any("lemmaId 'dim' missing from A2 lexeme shard" in error for error in summary["errors"])


def test_thin_deck_warnings(tmp_path: Path) -> None:
    daily_pool, practice_dir, reviewed_sources = _fixture_paths(tmp_path)
    summary = check_assets(
        daily_pool=daily_pool,
        practice_dir=practice_dir,
        reviewed_sources=reviewed_sources,
        levels=("A1",),
        min_daily_pool_size=2,
        min_practice_lexemes_per_level=1,
    )
    assert summary["ok"] is True
    assert any(
        "A1 synonym coverage 0.0000 is below thin-deck threshold 0.05" in warning for warning in summary["warnings"]
    )
    assert any(
        "A1 paronym coverage 0.0000 is below thin-deck threshold 0.01" in warning for warning in summary["warnings"]
    )


def test_check_assets_summary_includes_coverage_structure(tmp_path: Path) -> None:
    daily_pool, practice_dir, reviewed_sources = _fixture_paths(tmp_path)
    _write_level(practice_dir, level="A2")
    index_path = practice_dir / "practice-index.A2.json"
    index_payload = json.loads(index_path.read_text(encoding="utf-8"))
    index_payload["counts"]["modeCoverage"]["cloze"] = 0.5
    index_payload["counts"]["modeCoverage"]["synonym"] = 0.08
    _write_json(index_path, index_payload)

    summary = check_assets(
        daily_pool=daily_pool,
        practice_dir=practice_dir,
        reviewed_sources=reviewed_sources,
        levels=("A1", "A2"),
        min_daily_pool_size=2,
        min_practice_lexemes_per_level=1,
    )

    coverage = summary["coverage"]
    assert coverage["modes"] == [
        "cloze",
        "stress",
        "classify",
        "paradigm",
        "synonym",
        "heritage",
        "paronym",
        "antonym",
        "homonym",
        "imperative",
    ]
    assert coverage["levels"]["A1"]["cloze"] == {"ratio": 0.0, "pct": 0.0, "thin": True}
    assert coverage["levels"]["A1"]["synonym"] == {"ratio": 0.0, "pct": 0.0, "thin": True}
    assert coverage["levels"]["A1"]["heritage"] == {"ratio": 0.0, "pct": 0.0, "thin": True}
    assert coverage["levels"]["A2"]["cloze"] == {"ratio": 0.5, "pct": 50.0, "thin": False}
    assert coverage["levels"]["A2"]["synonym"] == {"ratio": 0.08, "pct": 8.0, "thin": False}


def test_cli_prints_coverage_table(tmp_path: Path) -> None:
    daily_pool, practice_dir, reviewed_sources = _fixture_paths(tmp_path)

    result = subprocess.run(
        [
            str(project_python()),
            "scripts/audit/check_static_practice_assets.py",
            "--daily-pool",
            str(daily_pool),
            "--practice-dir",
            str(practice_dir),
            "--reviewed-sources",
            str(reviewed_sources),
            "--levels",
            "A1",
            "--min-daily-pool-size",
            "2",
            "--min-practice-lexemes-per-level",
            "1",
            "--no-run-qa-gate",
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode == 0
    assert "Practice mode coverage (% of lexemes):" in result.stdout
    assert "cloze" in result.stdout and "synonym" in result.stdout
    assert "0.0%*" in result.stdout
    assert "* below thin-deck warning threshold" in result.stdout


def test_check_assets_runs_qa_gate_with_fixtures(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify check_assets forwards and catches QA violations when run_qa_gate=True."""
    # This import must work without the audit directory on sys.path.
    audit_dir = Path(__file__).resolve().parents[1] / "scripts" / "audit"
    with restore_import_state("practice_quality_gate"):
        monkeypatch.delitem(sys.modules, "practice_quality_gate", raising=False)
        monkeypatch.setattr(sys, "path", [entry for entry in sys.path if Path(entry).resolve() != audit_dir])
        daily_pool, practice_dir, reviewed_sources = _fixture_paths(tmp_path)
        cloze_path = tmp_path / "bad_cloze.json"
        cloze_path.write_text(
            json.dumps(
                {
                    "cloze": [
                        {
                            "clozeId": "c_bad",
                            "sentence": "НЕПРАВИЛЬНО ПРАВИЛЬНО _____ речення",
                            "form": "гарне",
                            "options": [
                                {"label": "гарне", "kind": "answer"},
                                {"label": "погане", "kind": "distractor"},
                            ],
                        }
                    ]
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        ec_path = tmp_path / "valid_ec.json"
        ec_path.write_text(json.dumps({"drills": []}), encoding="utf-8")
        si_path = tmp_path / "valid_si.json"
        si_path.write_text(json.dumps({"sentences": []}), encoding="utf-8")

        summary = check_assets(
            daily_pool=daily_pool,
            practice_dir=practice_dir,
            reviewed_sources=reviewed_sources,
            levels=("A1",),
            min_daily_pool_size=2,
            min_practice_lexemes_per_level=1,
            teacher_cloze=cloze_path,
            error_corrections=ec_path,
            sentence_inventory=si_path,
            run_qa_gate=True,
        )
        assert summary["ok"] is False
        assert any("practice_quality_gate [teacher_cloze] INTENTIONAL_ERROR_LEAK" in err for err in summary["errors"])


def test_check_assets_runs_qa_gate_after_audit_dir_removed_from_sys_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """QA gate still runs after scripts/audit is removed from sys.path.

    tests/test_curated_ohoiko_ulp_repromote.py imports
    apply_source_inventory_provenance, which removes that directory at import
    time. The checker module stays cached, so a later bare import of
    practice_quality_gate fails.
    """
    audit_dir = check_static_practice_assets.AUDIT_DIR.resolve()
    monkeypatch.setattr(
        sys,
        "path",
        [entry for entry in sys.path if not entry or Path(entry).resolve() != audit_dir],
    )
    assert not any(entry and Path(entry).resolve() == audit_dir for entry in sys.path)

    daily_pool, practice_dir, reviewed_sources = _fixture_paths(tmp_path)
    cloze_path = tmp_path / "bad_cloze.json"
    cloze_path.write_text(
        json.dumps(
            {
                "cloze": [
                    {
                        "clozeId": "c_bad",
                        "sentence": "НЕПРАВИЛЬНО ПРАВИЛЬНО _____ речення",
                        "form": "гарне",
                        "options": [
                            {"label": "гарне", "kind": "answer"},
                            {"label": "погане", "kind": "distractor"},
                        ],
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    ec_path = tmp_path / "valid_ec.json"
    ec_path.write_text(json.dumps({"drills": []}), encoding="utf-8")
    si_path = tmp_path / "valid_si.json"
    si_path.write_text(json.dumps({"sentences": []}), encoding="utf-8")

    summary = check_assets(
        daily_pool=daily_pool,
        practice_dir=practice_dir,
        reviewed_sources=reviewed_sources,
        levels=("A1",),
        min_daily_pool_size=2,
        min_practice_lexemes_per_level=1,
        teacher_cloze=cloze_path,
        error_corrections=ec_path,
        sentence_inventory=si_path,
        run_qa_gate=True,
    )
    assert summary["ok"] is False
    assert any("practice_quality_gate [teacher_cloze] INTENTIONAL_ERROR_LEAK" in err for err in summary["errors"])


def test_audit_dir_off_sys_path_preserves_added_entries(monkeypatch: pytest.MonkeyPatch) -> None:
    audit_dir = str(check_static_practice_assets.AUDIT_DIR.resolve())
    sentinel = "/existing/sentinel/path"
    monkeypatch.setattr(sys, "path", [audit_dir, sentinel])
    added_entry = "/added/during/import"

    with check_static_practice_assets._audit_dir_off_sys_path():
        assert audit_dir not in sys.path
        sys.path.insert(0, added_entry)

    assert sys.path[0] == audit_dir
    assert sys.path[1] == added_entry
    assert sentinel in sys.path


def test_audit_dir_off_sys_path_restores_on_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    audit_dir = str(check_static_practice_assets.AUDIT_DIR.resolve())
    sentinel = "/existing/sentinel/path"
    monkeypatch.setattr(sys, "path", [audit_dir, sentinel])
    added_entry = "/added/before/error"

    with pytest.raises(RuntimeError, match="guarded import failed"):
        with check_static_practice_assets._audit_dir_off_sys_path():
            sys.path.insert(0, added_entry)
            raise RuntimeError("guarded import failed")

    assert sys.path[0] == audit_dir
    assert sys.path[1] == added_entry
    assert sentinel in sys.path


def test_cli_runs_qa_gate_with_fixtures(tmp_path: Path) -> None:
    """Verify CLI forwards --run-qa-gate and catches QA violations on fixtures."""
    daily_pool, practice_dir, reviewed_sources = _fixture_paths(tmp_path)
    cloze_path = tmp_path / "bad_cloze.json"
    cloze_path.write_text(
        json.dumps(
            {
                "cloze": [
                    {
                        "clozeId": "c_bad",
                        "sentence": "НЕПРАВИЛЬНО ПРАВИЛЬНО _____ речення",
                        "form": "гарне",
                        "options": [
                            {"label": "гарне", "kind": "answer"},
                            {"label": "погане", "kind": "distractor"},
                        ],
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    ec_path = tmp_path / "valid_ec.json"
    ec_path.write_text(json.dumps({"drills": []}), encoding="utf-8")
    si_path = tmp_path / "valid_si.json"
    si_path.write_text(json.dumps({"sentences": []}), encoding="utf-8")

    result = subprocess.run(
        [
            str(project_python()),
            "scripts/audit/check_static_practice_assets.py",
            "--daily-pool",
            str(daily_pool),
            "--practice-dir",
            str(practice_dir),
            "--reviewed-sources",
            str(reviewed_sources),
            "--levels",
            "A1",
            "--min-daily-pool-size",
            "2",
            "--min-practice-lexemes-per-level",
            "1",
            "--teacher-cloze",
            str(cloze_path),
            "--error-corrections",
            str(ec_path),
            "--sentence-inventory",
            str(si_path),
            "--run-qa-gate",
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 1
    assert "practice_quality_gate [teacher_cloze] INTENTIONAL_ERROR_LEAK" in result.stdout, result.stderr


def _input_snapshot(root: Path) -> dict[str, tuple[bytes, int, int]]:
    return {
        str(path.relative_to(root)): (path.read_bytes(), path.stat().st_ino, path.stat().st_mtime_ns)
        for path in root.rglob("*") if path.is_file()
    }


def _check_fixture(root: Path, *, levels: tuple[str, ...] = ("A1",)) -> dict:
    return check_assets(
        daily_pool=root / "lexicon-daily-pool.json",
        practice_dir=root / "lexicon",
        reviewed_sources=root / "lexicon-practice-reviewed-sources.json",
        levels=levels,
        min_daily_pool_size=2,
        min_practice_lexemes_per_level=1,
    )


def test_fallback_validation_preserves_supplied_inputs(tmp_path: Path) -> None:
    _fixture_paths(tmp_path)
    before = _input_snapshot(tmp_path)
    summary = _check_fixture(tmp_path)
    assert summary["ok"] is True, summary["errors"]
    assert _input_snapshot(tmp_path) == before
    for mode in ("homonym", "imperative"):
        assert mode not in summary["practice"]["A1"]
        assert mode not in summary["coverage"]["levels"]["A1"]
        assert f"A1 {mode} unavailable" in summary["warnings"]


@pytest.mark.parametrize("count", [0, 1])
def test_missing_required_stress_is_an_error_without_repairs(tmp_path: Path, count: int) -> None:
    _, practice, _ = _fixture_paths(tmp_path)
    (practice / "practice-stress.A1.json").unlink()
    index = practice / "practice-index.A1.json"
    payload = json.loads(index.read_text())
    payload["counts"]["modeCounts"]["stress"] = count
    _write_json(index, payload)
    before = _input_snapshot(tmp_path)
    summary = _check_fixture(tmp_path)
    assert summary["ok"] is False
    assert any("practice-stress.A1.json: missing" in error for error in summary["errors"])
    assert _input_snapshot(tmp_path) == before


@pytest.mark.parametrize("counter", ["modeCounts", "modeCoverage"])
def test_present_mode_requires_supplied_counter(tmp_path: Path, counter: str) -> None:
    _, practice, _ = _fixture_paths(tmp_path)
    index = practice / "practice-index.A1.json"
    payload = json.loads(index.read_text())
    del payload["counts"][counter]["stress"]
    _write_json(index, payload)
    before = _input_snapshot(tmp_path)
    summary = _check_fixture(tmp_path)
    assert summary["ok"] is False
    assert any(f"counts.{counter}.stress" in error for error in summary["errors"])
    assert _input_snapshot(tmp_path) == before


def _add_empty_mode(practice: Path, mode: str, *, level: str = "A1") -> None:
    _write_json(practice / f"practice-{mode}.{level}.json", {
        "schema": f"atlas-practice-{mode}", "schemaVersion": 1,
        "deckVersion": "atlas-practice-v1-test", "level": level,
        "sizeBudget": {"ok": True, "rawBytes": 0, "gzipBytes": 0,
                       "rawLimitBytes": 0, "gzipLimitBytes": 0}, mode: [],
    })
    index = practice / f"practice-index.{level}.json"
    payload = json.loads(index.read_text())
    payload["counts"]["modeCounts"][mode] = 0
    payload["counts"]["modeCoverage"][mode] = 0.0
    _write_json(index, payload)


@pytest.mark.parametrize("mode", ["homonym", "imperative"])
@pytest.mark.parametrize("reference", ["modeCounts", "modeCoverage", "item", "index"])
def test_missing_optional_mode_with_any_reference_errors(tmp_path: Path, mode: str, reference: str) -> None:
    _, practice, _ = _fixture_paths(tmp_path)
    path = practice / "practice-index.A1.json"
    payload = json.loads(path.read_text())
    if reference in ("modeCounts", "modeCoverage"):
        payload["counts"][reference][mode] = 0
    elif reference == "item":
        payload["items"][0]["modes"].append(mode)
    else:
        payload["modes"] = [mode]
    _write_json(path, payload)
    before = _input_snapshot(tmp_path)
    summary = _check_fixture(tmp_path)
    assert summary["ok"] is False
    assert any(f"practice-{mode}.A1.json: missing" in error for error in summary["errors"])
    assert _input_snapshot(tmp_path) == before


@pytest.mark.parametrize(("field", "value", "error"), [
    ("schemaVersion", 2, "schemaVersion must be 1"),
    ("schemaVersion", True, "schemaVersion must be 1"),
    ("deckVersion", "", "missing deckVersion"),
    ("deckVersion", 1, "missing deckVersion"),
    ("deckVersion", "other-version", "shard deckVersion mismatch"),
])
def test_invalid_shard_classification_errors_without_writes(tmp_path: Path, field: str, value: object, error: str) -> None:
    _, practice, _ = _fixture_paths(tmp_path)
    path = practice / "practice-stress.A1.json"
    payload = json.loads(path.read_text())
    payload[field] = value
    _write_json(path, payload)
    before = _input_snapshot(tmp_path)
    summary = _check_fixture(tmp_path)
    assert summary["ok"] is False
    assert any(error in entry for entry in summary["errors"])
    assert _input_snapshot(tmp_path) == before


@pytest.mark.parametrize("damage", ["invalid-json", "missing-index", "missing-directory", "counter-type"])
def test_corrupt_or_absent_inputs_are_read_only_errors(tmp_path: Path, damage: str) -> None:
    _, practice, _ = _fixture_paths(tmp_path)
    if damage == "invalid-json":
        (practice / "practice-stress.A1.json").write_text("{")
        expected = "invalid JSON"
    elif damage == "missing-index":
        (practice / "practice-index.A1.json").unlink()
        expected = "practice-index.A1.json: missing"
    elif damage == "missing-directory":
        practice.rename(tmp_path / "supplied")
        expected = "practice-index.A1.json: missing"
    else:
        index = practice / "practice-index.A1.json"
        payload = json.loads(index.read_text())
        payload["counts"]["modeCoverage"]["stress"] = "unknown"
        _write_json(index, payload)
        expected = "counts.modeCoverage.stress 'unknown' != 0.0"
    before = _input_snapshot(tmp_path)
    summary = _check_fixture(tmp_path)
    assert summary["ok"] is False
    assert any(expected in error for error in summary["errors"])
    assert _input_snapshot(tmp_path) == before


def test_mixed_unavailable_and_empty_custom_modes_keep_distinct_reports(tmp_path: Path, capsys) -> None:
    _, practice, _ = _fixture_paths(tmp_path)
    _write_level(practice, level="A2")
    _add_empty_mode(practice, "homonym", level="A2")
    _add_empty_mode(practice, "imperative", level="A2")
    before = _input_snapshot(tmp_path)
    summary = _check_fixture(tmp_path, levels=("A1", "A2"))
    assert summary["ok"] is True, summary["errors"]
    assert "homonym" not in summary["practice"]["A1"]["mode_coverage"]
    assert summary["practice"]["A2"]["homonym"] == 0
    assert summary["coverage"]["levels"]["A2"]["homonym"] == {"ratio": 0.0, "pct": 0.0, "thin": True}
    assert summary["coverage"]["levels"]["A2"]["imperative"] == {"ratio": 0.0, "pct": 0.0, "thin": False}
    assert any("A2 imperative: custom origin unknown" in warning for warning in summary["warnings"])
    assert not any("A1 homonym coverage" in warning for warning in summary["warnings"])
    check_static_practice_assets._print_summary(summary)
    output = capsys.readouterr().out
    assert "homonym=N/A imperative=N/A" in output
    assert "homonym=0 imperative=0" in output
    assert "N/A*" not in output
    assert output.count("N/A") == 4
    assert "0.0%*" in output
    assert _input_snapshot(tmp_path) == before


def _pin_package(practice: Path, pointer_path: Path) -> bytes:
    import gzip
    import hashlib

    entries = []
    contents = []
    for path in sorted(practice.glob("*.json")):
        payload = json.loads(path.read_text())
        data = path.read_bytes()
        kind, level = path.name.removeprefix("practice-").removesuffix(".json").split(".")
        entries.append({"path": path.name, "kind": kind, "level": level,
                        "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                        "counts": payload.get("counts", {})})
        contents.append({"path": path.name, "content": data.decode()})
    version = json.loads((practice / "practice-index.A1.json").read_text())["deckVersion"]
    package = json.dumps({"schema": "atlas-practice-deck-package", "schemaVersion": 1,
                          "deckVersion": version, "files": contents}).encode()
    compressed = gzip.compress(package)
    _write_json(pointer_path, {
        "asset_url": "https://github.com/learn-ukrainian/learn-ukrainian.github.io/releases/download/test/deck.gz",
        "release_tag": "test", "deck_version": version, "package_schema_version": 1,
        "gz_sha256": hashlib.sha256(compressed).hexdigest(), "gz_bytes": len(compressed),
        "package_sha256": hashlib.sha256(package).hexdigest(), "package_bytes": len(package),
        "file_count": len(entries), "files": entries,
    })
    return compressed


def test_pinned_inventory_requires_its_zero_files_and_rejects_stale_custom_shards(tmp_path: Path, monkeypatch) -> None:
    _, practice, _ = _fixture_paths(tmp_path)
    _add_empty_mode(practice, "homonym")
    pointer_path = tmp_path / "pointer.json"
    _pin_package(practice, pointer_path)
    monkeypatch.setattr(check_static_practice_assets, "DEFAULT_POINTER", pointer_path)
    assert _check_fixture(tmp_path)["ok"] is True
    (practice / "practice-homonym.A1.json").unlink()
    missing = _check_fixture(tmp_path)
    assert missing["ok"] is False
    assert any("practice-homonym.A1.json: missing" in error for error in missing["errors"])
    _add_empty_mode(practice, "homonym")
    _add_empty_mode(practice, "imperative")
    before = _input_snapshot(tmp_path)
    stale = _check_fixture(tmp_path)
    assert stale["ok"] is False
    assert any("practice-imperative.A1.json: not listed in pinned deck" in error for error in stale["errors"])
    assert _input_snapshot(tmp_path) == before


@pytest.mark.parametrize("damage", ["missing", "json", "shape", "files", "version", "metadata", "uncovered", "schema-type"])
def test_pointer_failure_never_falls_back_to_custom_success(tmp_path: Path, monkeypatch, damage: str) -> None:
    _, practice, _ = _fixture_paths(tmp_path)
    pointer_path = tmp_path / "pointer.json"
    _pin_package(practice, pointer_path)
    payload = json.loads(pointer_path.read_text())
    if damage == "missing":
        pointer_path.unlink()
    elif damage == "json":
        pointer_path.write_text("{")
    elif damage == "shape":
        pointer_path.write_text("[]")
    else:
        if damage == "files":
            payload["files"] = [None] * payload["file_count"]
        elif damage == "version":
            payload["deck_version"] = ""
        elif damage == "schema-type":
            payload["package_schema_version"] = True
        elif damage == "metadata":
            payload["files"][0]["kind"] = "wrong"
        else:
            payload["files"] = []
            payload["file_count"] = 0
        _write_json(pointer_path, payload)
    monkeypatch.setattr(check_static_practice_assets, "DEFAULT_POINTER", pointer_path)
    before = _input_snapshot(tmp_path)
    summary = _check_fixture(tmp_path)
    assert summary["ok"] is False
    assert any(str(pointer_path) in error for error in summary["errors"])
    assert _input_snapshot(tmp_path) == before


def test_consistent_opaque_custom_versions_and_cross_level_mismatch(tmp_path: Path) -> None:
    _, practice, _ = _fixture_paths(tmp_path)
    _write_level(practice, level="A2")
    for path in practice.glob("*.json"):
        payload = json.loads(path.read_text())
        payload["deckVersion"] = "opaque custom version / 42"
        _write_json(path, payload)
    assert _check_fixture(tmp_path, levels=("A1", "A2"))["ok"] is True
    for path in practice.glob("*.A2.json"):
        payload = json.loads(path.read_text())
        payload["deckVersion"] = "another custom"
        _write_json(path, payload)
    before = _input_snapshot(tmp_path)
    summary = _check_fixture(tmp_path, levels=("A1", "A2"))
    assert summary["ok"] is False
    assert any("cross-level deckVersion mismatch" in error for error in summary["errors"])
    assert _input_snapshot(tmp_path) == before


@pytest.mark.parametrize("failure", [False, True])
def test_repeated_default_relative_absolute_library_and_default_qa_cli_are_pure(tmp_path: Path, monkeypatch, failure: bool) -> None:
    import shutil
    import sqlite3

    supplied = tmp_path / "supplied"
    daily, practice, reviewed = _fixture_paths(supplied)
    sandbox = tmp_path / "sandbox"
    (sandbox / "site/src/data").mkdir(parents=True)
    (sandbox / "site/public").mkdir(parents=True)
    shutil.copytree(practice, sandbox / "site/public/lexicon")
    shutil.copyfile(daily, sandbox / check_static_practice_assets.DEFAULT_DAILY_POOL)
    shutil.copyfile(reviewed, sandbox / check_static_practice_assets.DEFAULT_REVIEWED_SOURCES)
    teacher, corrections, inventory = (sandbox / name for name in ("teacher.json", "corrections.json", "inventory.json"))
    _write_json(teacher, {"cloze": []})
    _write_json(corrections, {"drills": []})
    _write_json(inventory, {"schema": "atlas-sentence-inventory", "schemaVersion": 1, "rows": [], "sentences": []})
    db = sandbox / "vesum.db"
    with sqlite3.connect(db) as connection:
        connection.execute("CREATE TABLE fixture (value TEXT)")
    if failure:
        (sandbox / "site/public/lexicon/practice-stress.A1.json").unlink()
    script = Path(check_static_practice_assets.__file__).resolve()
    monkeypatch.chdir(sandbox)
    before = _input_snapshot(sandbox)
    common = dict(levels=("A1",), min_daily_pool_size=2, min_practice_lexemes_per_level=1,
                  run_qa_gate=True, teacher_cloze=teacher, error_corrections=corrections,
                  sentence_inventory=inventory, vesum_db=db)
    for _ in range(2):
        relative = check_assets(**common)
        absolute = check_assets(**common, practice_dir=(sandbox / "site/public/lexicon").resolve())
        assert relative["ok"] is (not failure), relative["errors"]
        assert absolute["ok"] is (not failure), absolute["errors"]
        for output_format in ("json", "summary"):
            result = subprocess.run([
                sys.executable, str(script), "--levels", "A1", "--min-daily-pool-size", "2",
                "--min-practice-lexemes-per-level", "1", "--teacher-cloze", str(teacher),
                "--error-corrections", str(corrections), "--sentence-inventory", str(inventory),
                "--vesum-db", str(db), "--format", output_format,
            ], cwd=sandbox, capture_output=True, text=True, timeout=60, check=False)
            assert result.returncode == int(failure), result.stdout + result.stderr
            if output_format == "json":
                summary = json.loads(result.stdout)
                assert summary["ok"] is (not failure)
                assert "imperative" not in summary["coverage"]["levels"]["A1"]
            else:
                assert "imperative=N/A" in result.stdout
                assert "N/A*" not in result.stdout
                assert "A1 imperative unavailable" in result.stderr
        assert _input_snapshot(sandbox) == before


def _make_sandbox(tmp_path: Path) -> tuple[Path, Path]:
    """Run the real Make recipe and checker, with only release transport redirected."""
    import os
    import shutil

    sandbox = tmp_path / "make-tmp_path"
    _, release, _ = _fixture_paths(tmp_path / "release")
    for level in ("A2", "B1", "B2", "C1"):
        _write_level(release, level=level)
    # Meet the unchanged CLI volume gates with distinct valid fixture rows.
    for path in release.glob("practice-index.*.json"):
        payload = json.loads(path.read_text())
        payload["items"] = [{**payload["items"][0], "lemmaId": f"dim-{n}"} for n in range(25)]
        payload["counts"]["lexemes"] = 25
        _write_json(path, payload)
    for path in release.glob("practice-lexemes.*.json"):
        payload = json.loads(path.read_text())
        payload["lexemes"] = [{**payload["lexemes"][0], "lemmaId": f"dim-{n}"} for n in range(25)]
        _write_json(path, payload)
    pointer = tmp_path / "pointer.json"
    compressed = _pin_package(release, pointer)
    (tmp_path / "release.gz").write_bytes(compressed)
    (sandbox / "scripts/audit").mkdir(parents=True)
    shutil.copyfile(Path(check_static_practice_assets.PROJECT_ROOT) / "Makefile", sandbox / "Makefile")
    (sandbox / "site/src/data").mkdir(parents=True)
    # Use the existing positive daily fixture's kind, not a second daily contract.
    sample = json.loads((tmp_path / "release/lexicon-daily-pool.json").read_text())[0]
    rows = [{**sample, "lemmaId": f"daily-{n}", "id": f"daily-{n}", "slug": f"daily-{n}"} for n in range(250)]
    _write_json(sandbox / "site/src/data/lexicon-daily-pool.json", rows)
    _write_json(sandbox / "site/src/data/lexicon-practice-reviewed-sources.json", {"reviewed": []})
    (sandbox / "data").mkdir()
    (sandbox / "data/vesum.db").write_bytes(b"")
    original_script = str(Path(check_static_practice_assets.__file__).resolve())
    # The wrapper records the actual checker invocation; its flags/default QA stay intact.
    (sandbox / "scripts/audit/check_static_practice_assets.py").write_text(
        "import runpy, sys\nfrom pathlib import Path\n"
        "sys.path.insert(0, str(Path.cwd()))\nimport scripts\n"
        "with Path('events').open('a') as stream: stream.write('check\\n')\n"
        f"runpy.run_path({original_script!r}, run_name='__main__')\n"
    )
    (sandbox / "scripts/__init__.py").write_text(
        "import os, sys\nfrom pathlib import Path\n"
        f"__path__.append({str(check_static_practice_assets.PROJECT_ROOT / 'scripts')!r})\n"
        "from scripts.practice_deck import io\n"
        f"io.DEFAULT_POINTER = Path({str(pointer)!r})\n"
        "original = io.ensure_practice_deck_hydrated\n"
        "def download(pointer, *, attempt=0):\n"
        "    if os.environ.get('PREP_CASE') == 'download': raise OSError('fixture download failure')\n"
        f"    return Path({str(tmp_path / 'release.gz')!r}).read_bytes()\n"
        "io._download = download\n"
        "def prepare():\n"
        "    with Path('events').open('a') as stream: stream.write('prepare\\n')\n"
        "    if os.environ.get('PREP_CASE') == 'untyped':\n"
        "        raise RuntimeError('refusing to overwrite local practice deck')\n"
        "    return original(Path('site/public/lexicon'), io.DEFAULT_POINTER)\n"
        "io.ensure_practice_deck_hydrated = prepare\n"
    )
    assert Path(sys.executable).is_absolute()
    assert os.path.samefile(sys.executable, project_python())
    return sandbox, pointer


@pytest.mark.parametrize("case", ["success", "richer", "stale", "download", "hash", "pointer", "untyped", "check-fails"])
def test_actual_make_prepares_before_validation_and_preserves_precise_refusal(tmp_path: Path, case: str) -> None:
    import os
    import shutil

    sandbox, pointer_path = _make_sandbox(tmp_path)
    if case in {"richer", "stale"}:
        local = sandbox / "site/public/lexicon"
        shutil.copytree(tmp_path / "release/lexicon", local)
        if case == "richer":
            for path in local.glob("*.json"):
                payload = json.loads(path.read_text())
                payload["deckVersion"] = "richer-custom"
                if "items" in payload:
                    payload["items"].append({**payload["items"][0], "lemmaId": "extra"})
                    payload["counts"]["lexemes"] = 26
                if "lexemes" in payload:
                    payload["lexemes"].append({**payload["lexemes"][0], "lemmaId": "extra"})
                _write_json(path, payload)
        else:
            _add_empty_mode(local, "imperative")
            # Force real preparation to rewrite pinned indexes, retaining the stale shard.
            index = local / "practice-index.A1.json"
            payload = json.loads(index.read_text())
            payload["deckVersion"] = "old-custom"
            _write_json(index, payload)
    if case == "hash":
        (tmp_path / "release.gz").write_bytes(b"bad download")
    if case == "pointer":
        pointer_path.write_text("{}")
    if case == "check-fails":
        (sandbox / "site/src/data/lexicon-daily-pool.json").write_text("[]")
    before = _input_snapshot(sandbox / "site")
    env = {**os.environ, "PREP_CASE": case}
    result = subprocess.run(["make", "practice-deck-linguistic-gate", f"PYTHON={sys.executable}"],
                            cwd=sandbox, env=env, capture_output=True, text=True, check=False, timeout=60)
    assert (sandbox / "events").exists(), result.stdout + result.stderr
    events = (sandbox / "events").read_text().splitlines()
    if case in {"download", "hash", "pointer", "untyped"}:
        assert result.returncode != 0
        assert events == ["prepare"]
        expected = {"download": "failed to download", "hash": "gz sha256 mismatch",
                    "pointer": "missing required keys", "untyped": "RuntimeError: refusing to overwrite"}[case]
        assert expected in result.stderr
        assert _input_snapshot(sandbox / "site") == before
    else:
        assert events == ["prepare", "check"]
        assert result.returncode == (0 if case in {"success", "richer"} else 2), result.stdout + result.stderr
        if case == "richer":
            assert _input_snapshot(sandbox / "site") == before
            assert "custom origin unknown" in result.stderr
        elif case == "stale":
            assert "practice-imperative.A1.json: not listed in pinned deck" in result.stdout
            stale = "public/lexicon/practice-imperative.A1.json"
            assert _input_snapshot(sandbox / "site")[stale] == before[stale]
        elif case == "check-fails":
            assert "daily pool has 0 entries, expected at least 250" in result.stdout
        else:
            assert "imperative=N/A" in result.stdout


@pytest.mark.parametrize("failure", [False, True])
@pytest.mark.parametrize("output_format", ["json", "summary"])
def test_public_main_keeps_default_qa_and_unavailable_reporting(tmp_path: Path, capsys, failure: bool, output_format: str) -> None:
    daily, practice, reviewed = _fixture_paths(tmp_path)
    teacher, corrections, inventory = (tmp_path / name for name in ("teacher.json", "ec.json", "si.json"))
    _write_json(teacher, {"cloze": []})
    _write_json(corrections, {"drills": []})
    _write_json(inventory, {"sentences": []})
    if failure:
        (practice / "practice-stress.A1.json").write_text("{")
    before = _input_snapshot(tmp_path)
    assert check_static_practice_assets.main([
        "--daily-pool", str(daily), "--practice-dir", str(practice), "--reviewed-sources", str(reviewed),
        "--levels", "A1", "--min-daily-pool-size", "2", "--min-practice-lexemes-per-level", "1",
        "--teacher-cloze", str(teacher), "--error-corrections", str(corrections),
        "--sentence-inventory", str(inventory), "--format", output_format,
    ]) == int(failure)
    output = capsys.readouterr()
    if output_format == "json":
        assert json.loads(output.out)["ok"] is (not failure)
    else:
        assert "imperative=N/A" in output.out
        assert "A1 imperative unavailable" in output.err
        assert ("invalid JSON" in output.out) is failure
    assert _input_snapshot(tmp_path) == before


def test_explicit_io_preparation_is_separate_from_pure_validation(tmp_path: Path, monkeypatch, capsys) -> None:
    from functools import partial

    from scripts.practice_deck import io

    _, practice, _ = _fixture_paths(tmp_path)
    pointer = tmp_path / "pointer.json"
    compressed = _pin_package(practice, pointer)
    practice.rename(tmp_path / "release")
    monkeypatch.setattr(check_static_practice_assets, "DEFAULT_POINTER", pointer)
    before = _input_snapshot(tmp_path)
    missing = _check_fixture(tmp_path)
    assert missing["ok"] is False
    assert not practice.exists()
    assert _input_snapshot(tmp_path) == before
    monkeypatch.setattr(io, "_download", lambda pointer, *, attempt=0: compressed)
    monkeypatch.setattr(io, "ensure_practice_deck_hydrated", partial(
        io.ensure_practice_deck_hydrated, practice_dir=practice, pointer_path=pointer,
    ))
    assert io.main() == 0
    assert "(10 shards)" in capsys.readouterr().out
    prepared = _input_snapshot(tmp_path)
    summary = _check_fixture(tmp_path)
    assert summary["ok"] is True, summary["errors"]
    assert "imperative" not in summary["practice"]["A1"]
    assert _input_snapshot(tmp_path) == prepared
