"""Shared fixtures for the evaluation-harness tests."""

from __future__ import annotations

import shutil
import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from scripts.eval.uk_preamble.common import enclosing_work_tree


def _span(text: str, fragment: str, ident: str, occurrence: int = 0, **extra: Any) -> dict[str, Any]:
    start = -1
    for _ in range(occurrence + 1):
        start = text.index(fragment, start + 1)
    return {"id": ident, "start": start, "end": start + len(fragment), "span": fragment, **extra}


def build_mini_set() -> dict[str, Any]:
    """A hand-built set covering hits, alternatives, protected spans, overlap and insertion errors."""
    r1 = "Вчора я приймав участь у зборах. Ми обговорювали питання на протязі години, а Галя принесла пляцки."
    r2 = "Дякую, пане Петре, за допомогу в п'ятницю."
    r3 = "Цей пункт являється слідуючим кроком."
    r4 = "Я знаю що він прийде."
    comma = r4.index(" що")
    return {
        "set_id": "mini",
        "review": [
            {
                "id": "R1",
                "text": r1,
                "errors": [
                    _span(r1, "приймав участь", "R1-e1", error_type="lexical-russianism", accepted=["брав участь"]),
                    _span(
                        r1,
                        "на протязі години",
                        "R1-e2",
                        error_type="prepositional-calque",
                        accepted=["протягом години", "упродовж години"],
                    ),
                ],
                "protected": [_span(r1, "пляцки", "R1-p1", kind="regional")],
            },
            {
                "id": "R2",
                "text": r2,
                "errors": [],
                "protected": [
                    _span(r2, "пане Петре", "R2-p1", kind="vocative"),
                    _span(r2, "п'ятницю", "R2-p2", kind="apostrophe"),
                ],
            },
            {
                "id": "R3",
                "text": r3,
                "errors": [
                    _span(r3, "являється", "R3-e1", error_type="lexical-russianism", accepted=["є"]),
                    _span(r3, "слідуючим", "R3-e2", error_type="lexical-russianism", accepted=["наступним"]),
                ],
                "protected": [],
            },
            {
                "id": "R4",
                "text": r4,
                "errors": [
                    {
                        "id": "R4-e1",
                        "start": comma,
                        "end": comma,
                        "span": "",
                        "error_type": "punctuation",
                        "accepted": [","],
                    }
                ],
                "protected": [],
            },
        ],
        "writing": [
            {"id": "W1", "level": "B1", "instruction": "Опишіть свій вихідний день.", "min_words": 3, "max_words": 200},
            {"id": "W2", "level": "B2", "instruction": "Напишіть короткий лист другові."},
        ],
    }


def build_full_set() -> dict[str, Any]:
    """A synthetic set at the Protocol v2 minimums: 60 errors, 60 protected spans, writing at A2-C1."""
    review = []
    for i in range(60):
        text = f"Вчора в пункті {i} я приймав участь у зборах, а Галя принесла пляцки."
        review.append(
            {
                "id": f"F{i:02d}",
                "text": text,
                "errors": [
                    _span(
                        text,
                        "приймав участь",
                        f"F{i:02d}-e1",
                        error_type="lexical-russianism",
                        accepted=["брав участь"],
                    )
                ],
                "protected": [_span(text, "пляцки", f"F{i:02d}-p1", kind="regional")],
            }
        )
    writing = [
        {"id": f"W{level}", "level": level, "instruction": "Опишіть свій вихідний день."}
        for level in ("A2", "B1", "B2", "C1")
    ]
    return {"set_id": "full", "review": review, "writing": writing}


@pytest.fixture
def mini_set_dict() -> dict[str, Any]:
    return build_mini_set()


@pytest.fixture
def full_set_dict() -> dict[str, Any]:
    return build_full_set()


@pytest.fixture
def outside_dir(tmp_path: Path) -> Iterator[Path]:
    """A fresh directory outside every Git work tree (results directories are refused inside one).

    ``tmp_path`` when it qualifies; otherwise a new directory under the first
    system temporary root that does. Skips, naming the reason, when none does.
    """
    if enclosing_work_tree(tmp_path.resolve()) is None:
        yield tmp_path
        return
    for root in (tempfile.gettempdir(), "/tmp", "/var/tmp", "/dev/shm"):
        base = Path(root).resolve()
        if not base.is_dir() or enclosing_work_tree(base) is not None:
            continue
        try:
            made = Path(tempfile.mkdtemp(prefix="uk9623-test-", dir=base)).resolve()
        except OSError:
            continue
        try:
            yield made
        finally:
            shutil.rmtree(made, ignore_errors=True)
        return
    pytest.skip(
        f"no temporary directory outside a Git work tree: {tmp_path} is inside "
        f"{enclosing_work_tree(tmp_path.resolve())} and no system temporary root qualifies"
    )
