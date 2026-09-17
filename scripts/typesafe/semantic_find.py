"""Line-level semantic find over TypeSafe System One (Jev).

Cookbook: https://docs.typesafe.ai/cookbooks/semantic_find.md
Fleet best practice: docs/best-practices/typesafe-jev.md

Ranks every line of a document against a natural-language query with a Choice
question, and separately checks whether any line addresses the query at all
with a Noul question. The two are asked together because Choice probabilities
always sum to 1 — some line ranks first even when none of them actually
answers the query — so the Noul is what tells "real answer" apart from
"closest irrelevant line."

Credentials: ``TYPESAFE_API_KEY`` or ``~/.secrets/typsafe-ai.key``.
"""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Protocol

DEFAULT_MODEL = "jev-latest"
_SECRET_PATH = Path.home() / ".secrets" / "typsafe-ai.key"


class _SystemOneClient(Protocol):
    def system_one(
        self,
        state: Any,
        questions: Mapping[str, Any],
        *,
        model: str | None = None,
    ) -> Any: ...

    def close(self) -> None: ...


def _question_primitives():
    """Return Choice/Noul/NoulCriteria; stub when SDK absent (hermetic CI)."""
    try:
        from typesafe_sdk import Choice, Noul, NoulCriteria

        return Choice, Noul, NoulCriteria
    except ImportError:  # pragma: no cover - exercised in CI without extra-index
        # Mirror the real SDK's public attribute surface (`.instructions`,
        # `.criteria`) so callers and tests work unchanged either way.
        class Noul:
            def __init__(self, *, instructions=None, criteria=None):
                self.instructions = instructions
                self.criteria = criteria

        class Choice:
            def __init__(self, *, instructions=None, criteria):
                self.instructions = instructions
                self.criteria = criteria

        NoulCriteria = dict

        return Choice, Noul, NoulCriteria


def load_typesafe_api_key() -> str:
    env = os.environ.get("TYPESAFE_API_KEY", "").strip()
    if env:
        return env
    return _SECRET_PATH.read_text(encoding="utf-8").splitlines()[0].strip()


def _build_client() -> _SystemOneClient:
    """Construct a sync TypeSafeClient (lazy import)."""
    from typesafe_sdk import TypeSafeClient

    return TypeSafeClient(api_key=load_typesafe_api_key())


def _line_id(index: int) -> str:
    return f"L{index:03d}"


def _tag_lines(lines: Sequence[str]) -> str:
    return "\n".join(f"{_line_id(i)}| {line}" for i, line in enumerate(lines))


def _where_question(lines: Sequence[str], query: str):
    Choice, _Noul, _NoulCriteria = _question_primitives()
    return Choice(
        instructions=f'Which line of the document contains the answer to: "{query}"?',
        criteria={_line_id(i): None for i in range(len(lines))},
    )


def _exists_question(query: str):
    _Choice, Noul, NoulCriteria = _question_primitives()
    return Noul(
        instructions=f'Does any line of the document address or answer: "{query}"?',
        criteria=NoulCriteria(
            true="At least one line of the document states or directly implies the answer",
            false="No line of the document addresses this",
        ),
    )


def find(
    lines: Sequence[str],
    query: str,
    *,
    client: _SystemOneClient | None = None,
    model: str = DEFAULT_MODEL,
) -> dict:
    """Find which line(s) of `lines` answer `query`.

    Returns `{"exists": float, "relevance": list[float]}` — `exists` is the
    Noul probability that any line addresses the query, `relevance` gives one
    Choice probability per line in `lines`, in order.

    Pass `client` (anything satisfying `_SystemOneClient`, e.g. a test fake)
    to skip talking to the real API; otherwise a `TypeSafeClient` is built
    from `TYPESAFE_API_KEY` and closed afterward.
    """
    if not lines:
        return {"exists": 0.0, "relevance": []}

    owns_client = client is None
    active_client = client if client is not None else _build_client()
    try:
        response = active_client.system_one(
            state=_tag_lines(lines),
            questions={
                "where": _where_question(lines, query),
                "exists": _exists_question(query),
            },
            model=model,
        )
        probabilities = response.choices["where"].probabilities
        return {
            "exists": response.nouls["exists"].noul,
            "relevance": [probabilities.get(_line_id(i), 0.0) for i in range(len(lines))],
        }
    finally:
        if owns_client:
            active_client.close()
