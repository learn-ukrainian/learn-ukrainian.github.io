"""Build deterministic, item-keyed ZNO/НМТ practice-deck shards.

The ZNO corpus is assessment content, not Atlas vocabulary.  This builder keeps
the item identity and Ukrainian source text intact, emits only valid
single-choice tasks, and reports every excluded candidate instead of attempting
to repair it.  Learner-facing attribution is always УЦОЯО; mirror/document
metadata remains inside the source database and is never exported.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.practice_deck.markup_integrity import (
    apply_markup_overlay,
    assert_emit_integrity,
    load_markup_overlay,
    stem_requires_markup,
)

DEFAULT_DB = ROOT / "data" / "sources.db"
DEFAULT_OUT_DIR = ROOT / "site" / "src" / "data"
DEFAULT_MARKUP_OVERLAY = ROOT / "data" / "practice" / "zno-markup-overlay.json"
DEFAULT_FILL_RESIDUAL = ROOT / "batch_state" / "practice" / "zno-fill-residual.json"
LETTER_TO_INDEX = {"А": 0, "Б": 1, "В": 2, "Г": 3, "Д": 4}

# Pinned live denominators for review visibility when predicates or corpus change.
MORPHOLOGY_LIVE_CANDIDATE_COUNT = 195
LEXICAL_NORM_LIVE_CANDIDATE_COUNT = 40
PARONYM_LIVE_CANDIDATE_COUNT = 7

# This is deliberately an exact, reviewable predicate rather than an attempt to
# infer lexical suitability from stem wording.  Its live count is recorded with
# the PR whenever this wave is published.
LEXICAL_NORM_SQL = """
SELECT t.id, t.year, t.exam, t.session, t.task_no, t.stem, t.options_json,
       t.correct_json, t.topic_tag
FROM zno_tasks AS t
WHERE t.task_format = 'single-choice'
  AND trim(t.correct_json) IN ('А', 'Б', 'В', 'Г', 'Д')
  AND (
    trim(t.topic_norm) = 'lexical_norm'
    OR trim(t.task_subtype) = 'lexical_error'
  )
ORDER BY t.year, t.exam, t.session, t.task_no, t.id
""".strip()

MORPHOLOGICAL_NORM_SQL = """
SELECT t.id, t.year, t.exam, t.session, t.task_no, t.stem, t.options_json,
       t.correct_json, t.topic_tag
FROM zno_tasks AS t
WHERE t.task_format = 'single-choice'
  AND trim(t.correct_json) IN ('А', 'Б', 'В', 'Г', 'Д')
  AND trim(t.topic_norm) = 'morphological_norm'
ORDER BY t.year, t.exam, t.session, t.task_no, t.id
""".strip()

SYNTACTIC_NORM_SQL = """
SELECT t.id, t.year, t.exam, t.session, t.task_no, t.stem, t.options_json,
       t.correct_json, t.topic_tag
FROM zno_tasks AS t
WHERE t.task_format = 'single-choice'
  AND trim(t.correct_json) IN ('А', 'Б', 'В', 'Г', 'Д')
  AND trim(t.topic_norm) = 'syntactic_norm'
ORDER BY t.year, t.exam, t.session, t.task_no, t.id
""".strip()

# Pinned from the live source-database query published with ZNO wave 2.  SQLite's
# built-in lower() does not case-fold Ukrainian, so this deliberately matches the
# canonical capitalized topic-family label emitted by the ZNO annotation pipeline.
ORTHOGRAPHY_LIVE_CANDIDATE_COUNT = 168
ORTHOGRAPHY_SQL = """
SELECT t.id, t.year, t.exam, t.session, t.task_no, t.stem, t.options_json,
       t.correct_json, t.topic_tag
FROM zno_tasks AS t
WHERE t.task_format = 'single-choice'
  AND trim(t.correct_json) IN ('А', 'Б', 'В', 'Г', 'Д')
  AND instr(t.topic_tag, 'Орфограф') > 0
ORDER BY t.year, t.exam, t.session, t.task_no, t.id
""".strip()

# Wave 3 (#6620): broad topic_tag families that were sitting untapped in the
# corpus while only four thin/repetitive decks shipped. Same single-choice +
# letter-validity gates as every deck above; no new leniency.
#
# `topic_tag` for `instr(topic_tag, 'Синтаксис')` already carries the
# "Розділові знаки" (punctuation) subtags — e.g. "Синтаксис. Розділові знаки в
# складному реченні." — so punctuation is folded into this syntax deck rather
# than split into a fifth near-duplicate deck.
MORPHOLOGY_SQL = """
SELECT t.id, t.year, t.exam, t.session, t.task_no, t.stem, t.options_json,
       t.correct_json, t.topic_tag
FROM zno_tasks AS t
WHERE t.task_format = 'single-choice'
  AND trim(t.correct_json) IN ('А', 'Б', 'В', 'Г', 'Д')
  AND (
    instr(t.topic_tag, 'Морфолог') > 0
    OR instr(t.topic_tag, 'Словотвір') > 0
    OR instr(t.topic_tag, 'Будова слова') > 0
  )
ORDER BY t.year, t.exam, t.session, t.task_no, t.id
""".strip()

SYNTAX_SQL = """
SELECT t.id, t.year, t.exam, t.session, t.task_no, t.stem, t.options_json,
       t.correct_json, t.topic_tag
FROM zno_tasks AS t
WHERE t.task_format = 'single-choice'
  AND trim(t.correct_json) IN ('А', 'Б', 'В', 'Г', 'Д')
  AND instr(t.topic_tag, 'Синтаксис') > 0
ORDER BY t.year, t.exam, t.session, t.task_no, t.id
""".strip()

PHONETICS_SQL = """
SELECT t.id, t.year, t.exam, t.session, t.task_no, t.stem, t.options_json,
       t.correct_json, t.topic_tag
FROM zno_tasks AS t
WHERE t.task_format = 'single-choice'
  AND trim(t.correct_json) IN ('А', 'Б', 'В', 'Г', 'Д')
  AND instr(t.topic_tag, 'Фонетик') > 0
ORDER BY t.year, t.exam, t.session, t.task_no, t.id
""".strip()


@dataclass(frozen=True)
class DeckDefinition:
    key: str
    title: str
    predicate_sql: str
    thin: bool = False


DECKS = (
    DeckDefinition(
        key="stress",
        title="Наголос",
        predicate_sql="""
SELECT t.id, t.year, t.exam, t.session, t.task_no, t.stem, t.options_json,
       t.correct_json, t.topic_tag
FROM zno_tasks AS t
WHERE t.task_format = 'single-choice'
  AND trim(t.correct_json) IN ('А', 'Б', 'В', 'Г', 'Д')
  AND instr(t.topic_tag, 'Наголос') > 0
ORDER BY t.year, t.exam, t.session, t.task_no, t.id
""".strip(),
    ),
    DeckDefinition(
        key="paronym",
        title="Пароніми",
        predicate_sql="""
SELECT t.id, t.year, t.exam, t.session, t.task_no, t.stem, t.options_json,
       t.correct_json, t.topic_tag
FROM zno_tasks AS t
WHERE t.task_format = 'single-choice'
  AND trim(t.correct_json) IN ('А', 'Б', 'В', 'Г', 'Д')
  AND (
    instr(t.topic_tag, 'Паронім') > 0
    OR trim(t.task_subtype) = 'paronym'
    OR trim(t.paronym_pair) <> ''
    OR (
      instr(t.stem, 'Обидва слова') > 0
      AND instr(t.stem, 'дужках') > 0
      AND instr(t.stem, 'можливі') > 0
    )
  )
ORDER BY t.year, t.exam, t.session, t.task_no, t.id
""".strip(),
        thin=True,
    ),
    DeckDefinition(key="lexical-norm", title="Лексична норма", predicate_sql=LEXICAL_NORM_SQL),
    DeckDefinition(
        key="morphological-norm",
        title="Морфологічна норма",
        predicate_sql=MORPHOLOGICAL_NORM_SQL,
    ),
    DeckDefinition(
        key="syntactic-norm",
        title="Синтаксична норма",
        predicate_sql=SYNTACTIC_NORM_SQL,
    ),
    DeckDefinition(key="orthography", title="Орфографія", predicate_sql=ORTHOGRAPHY_SQL),
    DeckDefinition(key="morphology", title="Морфологія", predicate_sql=MORPHOLOGY_SQL),
    DeckDefinition(key="syntax", title="Синтаксис і пунктуація", predicate_sql=SYNTAX_SQL),
    DeckDefinition(key="phonetics", title="Фонетика", predicate_sql=PHONETICS_SQL),
)


def _compact_json(payload: Any) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _exam_label(exam: str) -> str:
    return "НМТ" if exam == "nmt" else "ЗНО"


def _session_label(session: str) -> str:
    labels = {
        "osnovna": "основна сесія",
        "dodatkova": "додаткова сесія",
        "sesiya-1": "сесія 1",
        "sesiya-2": "сесія 2",
    }
    return labels.get(session, session.replace("-", " "))


def learner_attribution(*, year: int, exam: str, session: str, task_no: int) -> str:
    return f"Джерело: УЦОЯО · {_exam_label(exam)} {year}, {_session_label(session)} · завдання №{task_no}"


def _parse_options(value: str, *, correct_index: int) -> list[str] | None:
    try:
        options = json.loads(value)
    except json.JSONDecodeError:
        return None
    if not isinstance(options, list) or correct_index >= len(options) or len(options) < 2:
        return None
    if not all(isinstance(option, str) for option in options):
        return None
    if any(not option.strip() for option in options) or len(set(options)) != len(options):
        return None
    return options


def _item_from_row(row: sqlite3.Row) -> tuple[dict[str, Any] | None, str | None]:
    correct_letter = str(row["correct_json"]).strip()
    correct_index = LETTER_TO_INDEX.get(correct_letter)
    if correct_index is None:
        return None, "invalid_correct_letter"
    options = _parse_options(str(row["options_json"]), correct_index=correct_index)
    if options is None:
        return None, "invalid_options"
    stem = str(row["stem"])
    if not stem.strip():
        return None, "empty_stem"
    task_id = int(row["id"])
    return {
        "znoTaskId": f"zno:{task_id}",
        "znoMode": "choice",
        "taskFormat": "single-choice",
        "stem": stem,
        "options": options,
        "correctLetter": correct_letter,
        "correctIndex": correct_index,
        "year": int(row["year"]),
        "exam": str(row["exam"]),
        "session": str(row["session"]),
        "taskNo": int(row["task_no"]),
        "topicTag": str(row["topic_tag"]),
        "attribution": learner_attribution(
            year=int(row["year"]),
            exam=str(row["exam"]),
            session=str(row["session"]),
            task_no=int(row["task_no"]),
        ),
    }, None


def _task_id(task_id: int) -> str:
    return f"zno:{task_id}"


def _residual_counts(conn: sqlite3.Connection, emitted: int) -> dict[str, int]:
    corpus = int(conn.execute("SELECT count(*) FROM zno_tasks").fetchone()[0])
    return {
        "corpusTasks": corpus,
        "emptyTopicTag": int(conn.execute("SELECT count(*) FROM zno_tasks WHERE trim(topic_tag) = ''").fetchone()[0]),
        "emptyTopicNorm": int(conn.execute("SELECT count(*) FROM zno_tasks WHERE trim(topic_norm) = ''").fetchone()[0]),
        "emptyKeyOwnStatement": int(conn.execute("SELECT count(*) FROM zno_tasks WHERE task_format = 'own-statement' AND trim(correct_json) = ''").fetchone()[0]),
        "documentsFetchNotOk": int(conn.execute("SELECT count(*) FROM zno_documents WHERE fetch_status <> 'ok'").fetchone()[0]),
        "emittedItems": emitted,
        "intentionalCut": corpus - emitted,
    }


def build_zno_shards(
    db_path: Path,
    *,
    markup_overlay_path: Path = DEFAULT_MARKUP_OVERLAY,
) -> tuple[dict[str, dict[str, Any]], dict[str, Any], dict[str, Any]]:
    """Build deterministic deck payloads, summary receipt, and per-task fill residual."""
    overlay_by_id = load_markup_overlay(markup_overlay_path)
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        shards: dict[str, dict[str, Any]] = {}
        deck_receipts: dict[str, Any] = {}
        deck_drops: dict[str, list[dict[str, str]]] = {}
        emitted_ids: set[int] = set()
        emitted_total = 0
        quarantined_markup = 0
        for definition in DECKS:
            rows = conn.execute(definition.predicate_sql).fetchall()
            dropped: Counter[str] = Counter()
            dropped_tasks: list[dict[str, str]] = []
            items: list[dict[str, Any]] = []
            for row in rows:
                item, reason = _item_from_row(row)
                if item is None:
                    drop_reason = reason or "invalid_item"
                    dropped[drop_reason] += 1
                    dropped_tasks.append({"znoTaskId": _task_id(int(row["id"])), "reason": drop_reason})
                    continue
                task_id = str(item["znoTaskId"])
                item, markup_reason = apply_markup_overlay(item, overlay_by_id.get(task_id))
                if item is None:
                    drop_reason = markup_reason or "broken_missing_markup"
                    dropped[drop_reason] += 1
                    dropped_tasks.append({"znoTaskId": _task_id(int(row["id"])), "reason": drop_reason})
                    if stem_requires_markup(str(row["stem"])):
                        quarantined_markup += 1
                    continue
                items.append(item)
                emitted_ids.add(int(row["id"]))
            emitted_total += len(items)
            shards[definition.key] = {
                "schema": "zno-practice-deck",
                "schemaVersion": 1,
                "deckId": f"zno-{definition.key}",
                "title": definition.title,
                "znoMode": "choice",
                "thinDeck": definition.thin,
                "items": items,
            }
            deck_receipts[definition.key] = {
                "predicate": definition.predicate_sql,
                "candidates": len(rows),
                "emitted": len(items),
                "dropped": dict(sorted(dropped.items())),
            }
            deck_drops[definition.key] = dropped_tasks
        residual = {
            "schema": "zno-practice-residual-report",
            "schemaVersion": 1,
            "decks": deck_receipts,
            "namedResidual": _residual_counts(conn, emitted_total),
            "markupIntegrity": {
                "quarantinedMissingMarkup": quarantined_markup,
                "overlayPath": str(markup_overlay_path.relative_to(ROOT))
                if markup_overlay_path.is_relative_to(ROOT)
                else str(markup_overlay_path),
            },
        }
        assert_emit_integrity(shards)
        fill_residual = build_zno_fill_residual(
            conn,
            deck_receipts=deck_receipts,
            deck_drops=deck_drops,
            emitted_ids=emitted_ids,
        )
        return shards, residual, fill_residual
    finally:
        conn.close()


def build_zno_fill_residual(
    conn: sqlite3.Connection,
    *,
    deck_receipts: dict[str, Any],
    deck_drops: dict[str, list[dict[str, str]]],
    emitted_ids: set[int],
) -> dict[str, Any]:
    """Per-deck inventory plus named blocked/unparsed single-choice task ids."""
    inventory = {
        key: {
            "candidates": receipt["candidates"],
            "emitted": receipt["emitted"],
            "dropped": receipt["dropped"],
            "fillRatio": round(receipt["emitted"] / receipt["candidates"], 4) if receipt["candidates"] else 1.0,
        }
        for key, receipt in deck_receipts.items()
    }
    blocked: list[dict[str, str]] = []
    for deck_key, drops in deck_drops.items():
        for entry in drops:
            blocked.append({"deck": deck_key, **entry})

    # Unparsed / blocked single-choice rows that never landed in any deck shard.
    unparsed: list[dict[str, str]] = []
    predicate_miss: Counter[str] = Counter()
    rows = conn.execute(
        """
        SELECT id, topic_tag, topic_norm, task_format, correct_json
        FROM zno_tasks
        WHERE task_format = 'single-choice'
        ORDER BY id
        """
    ).fetchall()
    for row in rows:
        task_id = int(row["id"])
        if task_id in emitted_ids:
            continue
        full_row = conn.execute("SELECT * FROM zno_tasks WHERE id = ?", (task_id,)).fetchone()
        _item, reason = _item_from_row(full_row)
        if reason is not None:
            unparsed.append({"znoTaskId": _task_id(task_id), "reason": reason})
            continue
        topic_norm = str(row["topic_norm"] or "").strip() or "empty"
        predicate_miss[topic_norm] += 1

    return {
        "schema": "zno-practice-fill-residual",
        "schemaVersion": 1,
        "inventory": inventory,
        "deckDrops": deck_drops,
        "blocked": blocked,
        "unparsed": unparsed,
        "predicateMissByTopicNorm": dict(sorted(predicate_miss.items())),
    }


def write_zno_fill_residual(fill_residual: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_compact_json(fill_residual))


def write_zno_shards(shards: dict[str, dict[str, Any]], residual: dict[str, Any], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for key, payload in shards.items():
        (out_dir / f"practice-zno.{key}.json").write_bytes(_compact_json(payload))
    (out_dir / "practice-zno.residual.json").write_bytes(_compact_json(residual))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--markup-overlay", type=Path, default=DEFAULT_MARKUP_OVERLAY)
    parser.add_argument(
        "--fill-residual",
        type=Path,
        default=DEFAULT_FILL_RESIDUAL,
        help="Write per-task fill residual inventory (default: batch_state/practice/zno-fill-residual.json)",
    )
    args = parser.parse_args(argv)
    shards, residual, fill_residual = build_zno_shards(args.db, markup_overlay_path=args.markup_overlay)
    write_zno_shards(shards, residual, args.out_dir)
    write_zno_fill_residual(fill_residual, args.fill_residual)
    for key in (definition.key for definition in DECKS):
        receipt = residual["decks"][key]
        print(f"{key}: candidates={receipt['candidates']} emitted={receipt['emitted']} dropped={sum(receipt['dropped'].values())}")
    print(f"named residual: {residual['namedResidual']}")
    print(f"markup quarantined: {residual['markupIntegrity']['quarantinedMissingMarkup']}")
    print(f"fill residual: {args.fill_residual}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
