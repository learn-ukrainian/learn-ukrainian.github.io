"""Shared fixtures for the evaluation-harness tests."""

from __future__ import annotations

from typing import Any

import pytest


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
