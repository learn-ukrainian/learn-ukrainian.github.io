"""Tests for scripts/practice/deck_variety_metrics.py (#5376 check 5)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.practice.deck_variety_metrics import main


def _item(idx: int, modes: list[str]) -> dict:
    return {
        "lemmaId": f"w{idx}",
        "lemma": f"w{idx}",
        "cefr": "A1",
        "modes": modes,
        "hasCloze": False,
        "clozeIds": [],
        "newOrder": idx,
    }


def _write_index(dir_path: Path, level: str, items: list[dict]) -> None:
    (dir_path / f"practice-index.{level}.json").write_text(
        json.dumps({"deckVersion": "test", "level": level, "items": items}),
        encoding="utf-8",
    )


def test_healthy_deck_passes(tmp_path: Path) -> None:
    modes = ["flashcards", "matching", "choice", "cloze", "stress", "classify"]
    items = [_item(i, modes[: 3 + (i % 4)]) for i in range(60)]
    _write_index(tmp_path, "A1", items)
    assert main(["--practice-dir", str(tmp_path)]) == 0


def test_samey_single_mode_deck_fails(tmp_path: Path) -> None:
    items = [_item(i, ["flashcards"]) for i in range(60)]
    _write_index(tmp_path, "A1", items)
    assert main(["--practice-dir", str(tmp_path)]) == 1


def test_singleton_mode_pool_fails(tmp_path: Path) -> None:
    items = [_item(i, ["flashcards", "matching", "choice", "cloze"]) for i in range(60)]
    items[0]["modes"] = items[0]["modes"] + ["heritage"]  # pool of exactly 1
    _write_index(tmp_path, "A1", items)
    assert main(["--practice-dir", str(tmp_path)]) == 1


def test_empty_deck_fails(tmp_path: Path) -> None:
    _write_index(tmp_path, "A1", [])
    assert main(["--practice-dir", str(tmp_path)]) == 1


def test_missing_shards_fail_closed(tmp_path: Path) -> None:
    assert main(["--practice-dir", str(tmp_path)]) == 1


def test_thin_pool_warns_but_passes(tmp_path: Path, capsys) -> None:
    modes = ["flashcards", "matching", "choice", "cloze", "stress"]
    items = [_item(i, list(modes)) for i in range(60)]
    for i in range(5):  # thin paronym pool: warns, does not fail
        items[i]["modes"] = items[i]["modes"] + ["paronym"]
    _write_index(tmp_path, "A1", items)
    assert main(["--practice-dir", str(tmp_path)]) == 0
    assert "warn" in capsys.readouterr().out


def test_strict_promotes_warnings(tmp_path: Path) -> None:
    modes = ["flashcards", "matching", "choice", "cloze", "stress"]
    items = [_item(i, list(modes)) for i in range(60)]
    for i in range(5):
        items[i]["modes"] = items[i]["modes"] + ["paronym"]
    _write_index(tmp_path, "A1", items)
    assert main(["--practice-dir", str(tmp_path), "--strict"]) == 1


def test_json_report_written(tmp_path: Path) -> None:
    items = [_item(i, ["flashcards", "matching", "choice", "cloze"]) for i in range(30)]
    _write_index(tmp_path, "A1", items)
    out = tmp_path / "report.json"
    assert main(["--practice-dir", str(tmp_path), "--json", str(out)]) == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["sessionSize"] == 10
    assert report["levels"][0]["modePools"]["flashcards"] == 30
