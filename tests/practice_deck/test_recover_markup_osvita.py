"""Fixture tests for osvita.ua ZNO markup recovery (no network)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from bs4 import BeautifulSoup

from scripts.practice_deck.recover_markup_osvita import (
    extract_option_from_answer,
    main,
    match_recovered_tasks,
    merge_overlay_items,
    parse_tasks_with_option_marks,
    write_overlay,
)

ZNO_203_HTML = """
<html><body>
<div class="task-card" id="q11">
  <div class="question"><p>Підкреслені літери позначають однаковий звук у кожному слові рядка</p></div>
  <div class="answer"><span class="marker">А</span><u><b>с</b></u>ьомий, ші<u><b>с</b></u>ть, <u><b>с</b></u>юди </div>
  <div class="answer"><span class="marker">Б</span><u><b>з</b></u>догад, <u><b>з</b></u>яблик, ни<u><b>з</b></u>ка </div>
  <div class="answer"><span class="marker">В</span>лі<u><b>т</b></u>ак, кві<u><b>т</b></u>чати, ни<u><b>т</b></u>ка </div>
  <div class="answer"><span class="marker">Г</span>ме<u><b>ж</b></u>а, ло<u><b>ж</b></u>ці, ду<u><b>ж</b></u>ка </div>
  <div class="answer"><span class="marker">Д</span>лу<u><b>к</b></u>, ане<u><b>к</b></u>дот, <u><b>к</b></u>овдра</div>
</div>
<div class="task-card" id="q12">
  <div class="question"><p>На другий склад падає наголос у слові</p></div>
  <div class="answer"><span class="marker">А</span>молодість</div>
</div>
</body></html>
"""

ZNO_203_OPTIONS = [
    "сьомий, шість, сюди",
    "здогад, зяблик, низка",
    "літак, квітчати, нитка",
    "межа, ложці, дужка",
    "лук, анекдот, ковдра",
]

ZNO_203_MARKS = [
    [
        {"start": 0, "end": 1, "style": "underline"},
        {"start": 10, "end": 11, "style": "underline"},
        {"start": 15, "end": 16, "style": "underline"},
    ],
    [
        {"start": 0, "end": 1, "style": "underline"},
        {"start": 8, "end": 9, "style": "underline"},
        {"start": 18, "end": 19, "style": "underline"},
    ],
    [
        {"start": 2, "end": 3, "style": "underline"},
        {"start": 10, "end": 11, "style": "underline"},
        {"start": 19, "end": 20, "style": "underline"},
    ],
    [
        {"start": 2, "end": 3, "style": "underline"},
        {"start": 8, "end": 9, "style": "underline"},
        {"start": 15, "end": 16, "style": "underline"},
    ],
    [
        {"start": 2, "end": 3, "style": "underline"},
        {"start": 8, "end": 9, "style": "underline"},
        {"start": 14, "end": 15, "style": "underline"},
    ],
]

BOLD_ONLY_HTML = """
<html><body>
<div class="task-card" id="q1">
  <div class="question"><p>Однаковий звук позначають букви, виділені в кожному слові рядка</p></div>
  <div class="answer"><span class="marker">А</span>бі<b>г</b>ти, порі<b>г</b>, зле<b>г</b>ка</div>
  <div class="answer"><span class="marker">Б</span>пові<b>с</b>ть, <b>с</b>яйво, <b>с</b>вічка</div>
  <div class="answer"><span class="marker">В</span>лі<b>ч</b>ба, поча<b>с</b>ти, <b>ч</b>ітко</div>
  <div class="answer"><span class="marker">Г</span>кі<b>с</b>тці, тім'я, жи<b>т</b>ній</div>
</div>
</body></html>
"""


def test_extract_option_marks_from_u_b_snippet() -> None:
    soup = BeautifulSoup(ZNO_203_HTML, "html.parser")
    answer = soup.find(class_="answer")
    assert answer is not None
    option = extract_option_from_answer(answer)
    assert option is not None
    assert option.text == "сьомий, шість, сюди"
    assert option.marks == ZNO_203_MARKS[0]


def test_parse_tasks_recovers_zno_203_style_underlines() -> None:
    tasks = parse_tasks_with_option_marks(ZNO_203_HTML, catalogue="ukrainian", test_id=429)
    assert len(tasks) == 1
    task = tasks[0]
    assert task.task_no == 11
    assert task.option_texts == ZNO_203_OPTIONS
    assert task.option_marks == ZNO_203_MARKS


def test_match_recovered_options_to_zno_task_id() -> None:
    recovered = parse_tasks_with_option_marks(ZNO_203_HTML, catalogue="ukrainian", test_id=429)
    tasks_by_options = {
        tuple(ZNO_203_OPTIONS): [
            {
                "znoTaskId": "zno:203",
                "stem": "Підкреслені літери позначають однаковий звук у кожному слові рядка",
                "options": ZNO_203_OPTIONS,
                "needs_option": True,
                "needs_passage": False,
            }
        ]
    }
    matched = match_recovered_tasks(recovered, tasks_by_options)
    assert matched == {"zno:203": {"optionMarks": ZNO_203_MARKS}}


def test_merge_overlay_is_idempotent() -> None:
    existing = {"zno:457": {"optionMarks": [[{"start": 2, "end": 3, "style": "underline"}]]}}
    recovered = {
        "zno:203": {"optionMarks": ZNO_203_MARKS},
        "zno:457": {"optionMarks": [[{"start": 2, "end": 3, "style": "underline"}]]},
    }
    once, stats_once = merge_overlay_items(existing, recovered)
    twice, stats_twice = merge_overlay_items(once, recovered)
    assert once == twice
    assert stats_once["added"] == 1
    assert stats_once["unchanged"] == 1
    assert stats_twice["added"] == 0
    assert stats_twice["unchanged"] == 2
    assert stats_twice["conflicts"] == 0


def test_bold_only_letters_recover_as_bold_style() -> None:
    tasks = parse_tasks_with_option_marks(BOLD_ONLY_HTML, catalogue="ukrmova", test_id=623)
    assert len(tasks) == 1
    assert tasks[0].option_marks[0] == [
        {"start": 2, "end": 3, "style": "bold"},
        {"start": 11, "end": 12, "style": "bold"},
        {"start": 17, "end": 18, "style": "bold"},
    ]


def test_cli_html_file_dry_run_writes_report(tmp_path: Path) -> None:
    db_path = tmp_path / "sources.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE zno_tasks (
            id INTEGER PRIMARY KEY, task_format TEXT, stem TEXT, options_json TEXT
        )
        """
    )
    conn.execute(
        "INSERT INTO zno_tasks VALUES (?, ?, ?, ?)",
        (
            203,
            "single-choice",
            "Підкреслені літери позначають однаковий звук у кожному слові рядка",
            json.dumps(ZNO_203_OPTIONS, ensure_ascii=False),
        ),
    )
    conn.commit()
    conn.close()

    html_path = tmp_path / "429.html"
    html_path.write_text(ZNO_203_HTML, encoding="utf-8")
    overlay_path = tmp_path / "overlay.json"
    write_overlay(overlay_path, {}, source_note="test")
    report_path = tmp_path / "report.json"

    rc = main(
        [
            "--db",
            str(db_path),
            "--html-file",
            str(html_path),
            "--test-id",
            "429",
            "--merge-overlay",
            str(overlay_path),
            "--dry-run",
            "--report",
            str(report_path),
        ]
    )
    assert rc == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["matchedTaskIds"] == ["zno:203"]
    assert report["merge"]["added"] == 1
    # dry-run must not rewrite overlay
    assert json.loads(overlay_path.read_text(encoding="utf-8"))["items"] == {}
