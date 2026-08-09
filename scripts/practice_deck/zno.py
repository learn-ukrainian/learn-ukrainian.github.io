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
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "sources.db"
DEFAULT_OUT_DIR = ROOT / "site" / "src" / "data"
LETTER_TO_INDEX = {"А": 0, "Б": 1, "В": 2, "Г": 3, "Д": 4}

# This is deliberately an exact, reviewable predicate rather than an attempt to
# infer lexical suitability from stem wording.  Its live count is recorded with
# the PR whenever this wave is published.
LEXICAL_NORM_SQL = """
SELECT t.id, t.year, t.exam, t.session, t.task_no, t.stem, t.options_json,
       t.correct_json, t.topic_tag
FROM zno_tasks AS t
WHERE t.task_format = 'single-choice'
  AND trim(t.correct_json) IN ('А', 'Б', 'В', 'Г', 'Д')
  AND trim(t.topic_norm) = 'lexical_norm'
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
  )
ORDER BY t.year, t.exam, t.session, t.task_no, t.id
""".strip(),
        thin=True,
    ),
    DeckDefinition(key="lexical-norm", title="Лексична норма", predicate_sql=LEXICAL_NORM_SQL),
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


def _residual_counts(conn: sqlite3.Connection, emitted: int) -> dict[str, int]:
    corpus = int(conn.execute("SELECT count(*) FROM zno_tasks").fetchone()[0])
    return {
        "corpusTasks": corpus,
        "emptyTopicTag": int(conn.execute("SELECT count(*) FROM zno_tasks WHERE trim(topic_tag) = ''").fetchone()[0]),
        "emptyTopicNorm": int(conn.execute("SELECT count(*) FROM zno_tasks WHERE trim(topic_norm) = ''").fetchone()[0]),
        "emptyKeyOwnStatement": int(conn.execute("SELECT count(*) FROM zno_tasks WHERE task_format = 'own-statement' AND trim(correct_json) = ''").fetchone()[0]),
        "documentsFetchNotOk": int(conn.execute("SELECT count(*) FROM zno_documents WHERE fetch_status <> 'ok'").fetchone()[0]),
        "waveOneEmitted": emitted,
        "intentionalCut": corpus - emitted,
    }


def build_zno_shards(db_path: Path) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Build three deterministic deck payloads and their fail-closed receipt."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        shards: dict[str, dict[str, Any]] = {}
        deck_receipts: dict[str, Any] = {}
        emitted_total = 0
        for definition in DECKS:
            rows = conn.execute(definition.predicate_sql).fetchall()
            dropped: Counter[str] = Counter()
            items: list[dict[str, Any]] = []
            for row in rows:
                item, reason = _item_from_row(row)
                if item is None:
                    dropped[reason or "invalid_item"] += 1
                    continue
                items.append(item)
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
        residual = {
            "schema": "zno-practice-residual-report",
            "schemaVersion": 1,
            "decks": deck_receipts,
            "namedResidual": _residual_counts(conn, emitted_total),
        }
        return shards, residual
    finally:
        conn.close()


def write_zno_shards(shards: dict[str, dict[str, Any]], residual: dict[str, Any], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for key, payload in shards.items():
        (out_dir / f"practice-zno.{key}.json").write_bytes(_compact_json(payload))
    (out_dir / "practice-zno.residual.json").write_bytes(_compact_json(residual))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args(argv)
    shards, residual = build_zno_shards(args.db)
    write_zno_shards(shards, residual, args.out_dir)
    for key in (definition.key for definition in DECKS):
        receipt = residual["decks"][key]
        print(f"{key}: candidates={receipt['candidates']} emitted={receipt['emitted']} dropped={sum(receipt['dropped'].values())}")
    print(f"named residual: {residual['namedResidual']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
