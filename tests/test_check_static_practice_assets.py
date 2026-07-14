from __future__ import annotations

import json
import subprocess
from pathlib import Path

from scripts.audit.check_static_practice_assets import check_assets

DRILL_MODES = ("stress", "classify", "paradigm", "synonym", "heritage", "paronym")


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
    rows = (
        [{"status": "reviewed", "path": "curriculum/l2-uk-en/a1/vocabulary/home.yaml"}]
        if reviewed
        else []
    )
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
                "cefr": "B2",
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
            ".venv/bin/python",
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
        ],
        check=False,
        capture_output=True,
        text=True,
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
    assert any("A1 synonym coverage 0.0000 is below thin-deck threshold 0.05" in warning for warning in summary["warnings"])
    assert any("A1 paronym coverage 0.0000 is below thin-deck threshold 0.01" in warning for warning in summary["warnings"])


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
            ".venv/bin/python",
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
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Practice mode coverage (% of lexemes):" in result.stdout
    assert "cloze" in result.stdout and "synonym" in result.stdout
    assert "0.0%*" in result.stdout
    assert "* below thin-deck warning threshold" in result.stdout
