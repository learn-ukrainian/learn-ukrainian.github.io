#!/usr/bin/env python3
"""Recover ZNO/НМТ option letter marks from zno.osvita.ua HTML.

Official interactive pages keep ``<u>`` / ``<u><b>`` (and, on ukrmova, bare
``<b>``) around highlighted letters.  Plain-text ingest drops those marks, so
markup-dependent stems are quarantined by ``markup_integrity`` unless a tracked
overlay supplies ``optionMarks``.

Operator recipe (network scan + deck rebuild)::

    .venv/bin/python scripts/practice_deck/recover_markup_osvita.py \\
      --scan-from 200 --scan-to 500 \\
      --merge-overlay data/practice/zno-markup-overlay.json
    .venv/bin/python scripts/practice_deck/zno.py

Only HTML-derived ranges that match ``zno_tasks.options_json`` exactly are
written.  Failed recovery never weakens the quarantine gate.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup, NavigableString, Tag

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.practice_deck.markup_integrity import (
    DEFAULT_OVERLAY,
    load_markup_overlay,
    overlay_has_required_marks,
    stem_requires_markup,
    stem_requires_option_marks,
    stem_requires_passage_marks,
)

DEFAULT_DB = ROOT / "data" / "sources.db"
DEFAULT_CATALOGUE = "ukrainian"
DEFAULT_SCAN_FROM = 200
DEFAULT_SCAN_TO = 500
USER_AGENT = "learn-ukrainian-zno-markup-recovery/1.0 (+https://github.com/learn-ukrainian/learn-ukrainian.github.io)"
REQUEST_PAUSE_S = 0.35


@dataclass(frozen=True)
class RecoveredOption:
    text: str
    marks: list[dict[str, Any]]


@dataclass(frozen=True)
class RecoveredTask:
    catalogue: str
    test_id: int
    task_no: int
    stem: str
    options: list[RecoveredOption]

    @property
    def option_texts(self) -> list[str]:
        return [option.text for option in self.options]

    @property
    def option_marks(self) -> list[list[dict[str, Any]]]:
        return [option.marks for option in self.options]


def _is_marker_span(node: Tag) -> bool:
    classes = node.get("class") or []
    return node.name == "span" and "marker" in classes


def _collect_marked_text(node: Tag | NavigableString, *, active_style: str | None) -> tuple[str, list[dict[str, Any]]]:
    """Walk an answer node; return plain text + char-range marks."""
    if isinstance(node, NavigableString):
        text = str(node)
        if not text:
            return "", []
        if active_style is None:
            return text, []
        return text, [{"start": 0, "end": len(text), "style": active_style}]

    if not isinstance(node, Tag):
        return "", []
    if _is_marker_span(node):
        return "", []

    style = active_style
    if node.name == "u":
        style = "underline"
    elif node.name in {"b", "strong"} and style is None:
        style = "bold"

    chunks: list[str] = []
    marks: list[dict[str, Any]] = []
    cursor = 0
    for child in node.children:
        child_text, child_marks = _collect_marked_text(child, active_style=style)
        if not child_text:
            continue
        for mark in child_marks:
            marks.append(
                {
                    "start": cursor + int(mark["start"]),
                    "end": cursor + int(mark["end"]),
                    "style": mark["style"],
                }
            )
        chunks.append(child_text)
        cursor += len(child_text)
    return "".join(chunks), marks


def _finalize_option(text: str, marks: list[dict[str, Any]]) -> RecoveredOption:
    leading = len(text) - len(text.lstrip())
    stripped = text.strip()
    adjusted: list[dict[str, Any]] = []
    for mark in marks:
        start = int(mark["start"]) - leading
        end = int(mark["end"]) - leading
        if start < 0 or end > len(stripped) or end <= start:
            continue
        entry: dict[str, Any] = {"start": start, "end": end}
        style = mark.get("style")
        if style in {"underline", "bold"}:
            entry["style"] = style
        adjusted.append(entry)
    return RecoveredOption(text=stripped, marks=adjusted)


def extract_option_from_answer(answer: Tag) -> RecoveredOption | None:
    """Extract one answer option's plain text and letter-mark ranges."""
    text, marks = _collect_marked_text(answer, active_style=None)
    option = _finalize_option(text, marks)
    if not option.text:
        return None
    return option


def parse_tasks_with_option_marks(html: str, *, catalogue: str, test_id: int) -> list[RecoveredTask]:
    """Parse task-cards that need option marks and carry HTML letter highlights."""
    soup = BeautifulSoup(html, "html.parser")
    recovered: list[RecoveredTask] = []
    for card in soup.find_all(class_="task-card"):
        if not isinstance(card, Tag):
            continue
        card_id = str(card.get("id") or "")
        digits = "".join(ch for ch in card_id if ch.isdigit())
        if not digits:
            continue
        task_no = int(digits)

        question = card.find(class_="question")
        stem = question.get_text(" ", strip=True) if isinstance(question, Tag) else ""
        if not stem_requires_option_marks(stem):
            continue

        options: list[RecoveredOption] = []
        for answer in card.find_all(class_="answer"):
            if not isinstance(answer, Tag):
                continue
            # Matching columns use numeric markers; skip non letter options.
            marker = answer.find("span", class_="marker")
            marker_text = marker.get_text(strip=True) if isinstance(marker, Tag) else ""
            if marker_text and marker_text not in {"А", "Б", "В", "Г", "Д", "A", "B", "C", "D", "E"}:
                continue
            option = extract_option_from_answer(answer)
            if option is None:
                continue
            options.append(option)

        if len(options) < 2:
            continue
        if not any(option.marks for option in options):
            continue
        recovered.append(
            RecoveredTask(
                catalogue=catalogue,
                test_id=test_id,
                task_no=task_no,
                stem=stem,
                options=options,
            )
        )
    return recovered


def fetch_test_html(catalogue: str, test_id: int, *, timeout: float = 30.0) -> str | None:
    """Fetch one interactive test page.  Returns None on HTTP errors."""
    url = f"https://zno.osvita.ua/{catalogue}/{test_id}/"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="replace")
    except urllib.error.HTTPError as exc:
        if exc.code in {404, 410}:
            return None
        raise
    except urllib.error.URLError:
        raise


def load_markup_tasks(db_path: Path) -> list[dict[str, Any]]:
    """Load single-choice tasks that still need visual marks."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT id, stem, options_json
            FROM zno_tasks
            WHERE task_format = 'single-choice'
            ORDER BY id
            """
        ).fetchall()
    finally:
        conn.close()

    tasks: list[dict[str, Any]] = []
    for row in rows:
        stem = str(row["stem"])
        if not stem_requires_markup(stem):
            continue
        try:
            options = json.loads(str(row["options_json"]))
        except json.JSONDecodeError:
            continue
        if not isinstance(options, list) or not all(isinstance(item, str) for item in options):
            continue
        tasks.append(
            {
                "znoTaskId": f"zno:{int(row['id'])}",
                "stem": stem,
                "options": options,
                "needs_option": stem_requires_option_marks(stem),
                "needs_passage": stem_requires_passage_marks(stem),
            }
        )
    return tasks


def index_tasks_by_options(tasks: list[dict[str, Any]]) -> dict[tuple[str, ...], list[dict[str, Any]]]:
    index: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    for task in tasks:
        if not task["needs_option"]:
            continue
        key = tuple(task["options"])
        index.setdefault(key, []).append(task)
    return index


def match_recovered_tasks(
    recovered: list[RecoveredTask],
    tasks_by_options: dict[tuple[str, ...], list[dict[str, Any]]],
) -> dict[str, dict[str, Any]]:
    """Map HTML-recovered option marks onto ``zno:{id}`` when options match exactly."""
    matched: dict[str, dict[str, Any]] = {}
    for task in recovered:
        key = tuple(task.option_texts)
        candidates = tasks_by_options.get(key) or []
        if not candidates:
            continue
        payload = {"optionMarks": task.option_marks}
        for candidate in candidates:
            if len(candidate["options"]) != len(task.options):
                continue
            if not overlay_has_required_marks(payload, stem=candidate["stem"], options=candidate["options"]):
                continue
            matched[candidate["znoTaskId"]] = payload
    return matched


def merge_overlay_items(
    existing: dict[str, dict[str, Any]],
    recovered: dict[str, dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], dict[str, int]]:
    """Idempotent merge: keep existing entries; add only new exact recoveries."""
    merged = dict(existing)
    added = 0
    unchanged = 0
    conflicts = 0
    for task_id, payload in recovered.items():
        if task_id not in merged:
            merged[task_id] = payload
            added += 1
            continue
        if merged[task_id] == payload:
            unchanged += 1
            continue
        conflicts += 1
    return merged, {"added": added, "unchanged": unchanged, "conflicts": conflicts}


def write_overlay(
    path: Path,
    items: dict[str, dict[str, Any]],
    *,
    source_note: str,
) -> None:
    ordered = dict(
        sorted(
            items.items(),
            key=lambda pair: int(pair[0].split(":", 1)[1]) if ":" in pair[0] else pair[0],
        )
    )
    payload = {
        "schema": "zno-markup-overlay",
        "schemaVersion": 1,
        "sourceNote": source_note,
        "items": ordered,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def residual_missing_marks(
    tasks: list[dict[str, Any]],
    overlay_items: dict[str, dict[str, Any]],
) -> list[dict[str, str]]:
    residual: list[dict[str, str]] = []
    for task in tasks:
        overlay = overlay_items.get(task["znoTaskId"])
        if overlay_has_required_marks(overlay, stem=task["stem"], options=task["options"]):
            continue
        if task["needs_option"] and task["needs_passage"]:
            stem_class = "option+passage"
        elif task["needs_option"]:
            stem_class = "option"
        else:
            stem_class = "passage"
        residual.append({"znoTaskId": task["znoTaskId"], "stemClass": stem_class})
    return residual


def scan_catalogue(
    *,
    catalogue: str,
    scan_from: int,
    scan_to: int,
    pause_s: float = REQUEST_PAUSE_S,
) -> list[RecoveredTask]:
    if scan_to < scan_from:
        raise ValueError("--scan-to must be >= --scan-from")
    recovered: list[RecoveredTask] = []
    for test_id in range(scan_from, scan_to + 1):
        html = fetch_test_html(catalogue, test_id)
        if html is None:
            print(f"skip {catalogue}/{test_id}: missing", flush=True)
        else:
            page_tasks = parse_tasks_with_option_marks(html, catalogue=catalogue, test_id=test_id)
            if page_tasks:
                print(
                    f"hit  {catalogue}/{test_id}: {len(page_tasks)} markup task(s)",
                    flush=True,
                )
            recovered.extend(page_tasks)
        if pause_s > 0 and test_id < scan_to:
            time.sleep(pause_s)
    return recovered


def build_report(
    *,
    matched: dict[str, dict[str, Any]],
    merge_stats: dict[str, int],
    residual: list[dict[str, str]],
    scanned: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema": "zno-markup-recovery-report",
        "schemaVersion": 1,
        "scanned": scanned,
        "matchedTaskIds": sorted(
            matched.keys(),
            key=lambda task_id: int(task_id.split(":", 1)[1]) if ":" in task_id else task_id,
        ),
        "merge": merge_stats,
        "residualMissingMarks": residual,
        "residualCount": len(residual),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scan-from", type=int, default=DEFAULT_SCAN_FROM)
    parser.add_argument("--scan-to", type=int, default=DEFAULT_SCAN_TO)
    parser.add_argument(
        "--catalogue",
        default=DEFAULT_CATALOGUE,
        choices=("ukrainian", "ukrmova"),
        help="Interactive catalogue under zno.osvita.ua (default: ukrainian)",
    )
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--merge-overlay", type=Path, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--report", type=Path, default=None)
    parser.add_argument(
        "--html-file",
        type=Path,
        action="append",
        default=[],
        help="Offline HTML fixture (repeatable). Skips network when set.",
    )
    parser.add_argument(
        "--test-id",
        type=int,
        default=0,
        help="test_id label for --html-file fixtures (default 0)",
    )
    args = parser.parse_args(argv)

    if not args.db.is_file():
        print(f"error: database not found: {args.db}", file=sys.stderr)
        return 2

    tasks = load_markup_tasks(args.db)
    tasks_by_options = index_tasks_by_options(tasks)

    if args.html_file:
        recovered: list[RecoveredTask] = []
        for path in args.html_file:
            html = path.read_text(encoding="utf-8")
            recovered.extend(
                parse_tasks_with_option_marks(html, catalogue=args.catalogue, test_id=args.test_id)
            )
        scanned = {
            "mode": "html-file",
            "files": [str(path) for path in args.html_file],
            "catalogue": args.catalogue,
        }
    else:
        recovered = scan_catalogue(
            catalogue=args.catalogue,
            scan_from=args.scan_from,
            scan_to=args.scan_to,
        )
        scanned = {
            "mode": "network",
            "catalogue": args.catalogue,
            "scanFrom": args.scan_from,
            "scanTo": args.scan_to,
            "recoveredTasks": len(recovered),
        }

    matched = match_recovered_tasks(recovered, tasks_by_options)
    overlay_path = args.merge_overlay or DEFAULT_OVERLAY
    existing = load_markup_overlay(overlay_path) if overlay_path.is_file() else {}
    merged_items, merge_stats = merge_overlay_items(existing, matched)
    residual = residual_missing_marks(tasks, merged_items)
    report = build_report(
        matched=matched,
        merge_stats=merge_stats,
        residual=residual,
        scanned=scanned,
    )

    print(
        f"recovered_html_tasks={len(recovered)} matched={len(matched)} "
        f"merge_added={merge_stats['added']} residual={len(residual)}"
    )
    for entry in residual:
        print(f"residual\t{entry['znoTaskId']}\t{entry['stemClass']}")

    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"wrote report {args.report}")

    if args.merge_overlay is not None and not args.dry_run and merge_stats["added"]:
        note = (
            "Letter marks recovered from zno.osvita.ua HTML (<u>/<u><b> and bare <b>). "
            "Expand via scripts/practice_deck/recover_markup_osvita.py."
        )
        if overlay_path.is_file():
            try:
                previous = json.loads(overlay_path.read_text(encoding="utf-8"))
                if isinstance(previous.get("sourceNote"), str) and previous["sourceNote"].strip():
                    note = previous["sourceNote"]
            except json.JSONDecodeError:
                pass
        write_overlay(overlay_path, merged_items, source_note=note)
        print(f"merged {merge_stats['added']} new item(s) into {overlay_path}")
    elif args.merge_overlay is not None and args.dry_run:
        print(f"dry-run: would merge {merge_stats['added']} new item(s) into {overlay_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
