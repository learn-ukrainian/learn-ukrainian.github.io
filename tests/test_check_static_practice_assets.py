from __future__ import annotations

import json
import subprocess
from pathlib import Path

from scripts.audit.check_static_practice_assets import check_assets


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
