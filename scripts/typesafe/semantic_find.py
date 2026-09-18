"""Line-level semantic find over TypeSafe System One (Jev).

Cookbook: https://docs.typesafe.ai/cookbooks/semantic_find.md
Fleet best practice: docs/best-practices/typesafe-jev.md

Ranks every line of a document against a natural-language query with a Choice
question, and separately checks whether any line addresses the query at all
with a Noul question. The two are asked together because Choice probabilities
always sum to 1 — some line ranks first even when none of them actually
answers the query — so the Noul is what tells "real answer" apart from
"closest irrelevant line."

Credentials: ``TYPESAFE_API_KEY`` or ``~/.secrets/typesafe-ai.key``.
"""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Protocol

DEFAULT_MODEL = "jev-latest"
_SECRET_PATH = Path.home() / ".secrets" / "typesafe-ai.key"
_LEGACY_SECRET_PATH = Path.home() / ".secrets" / "typsafe-ai.key"
# Cap Choice criteria size; TypeSafe Choice needs a closed set
# (same bound as scripts/build/typesafe_curriculum.py pick_preparsed_value).
_MAX_CHOICE_LINES = 24


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
    """Return Choice/Noul; stub when SDK absent (hermetic CI)."""
    try:
        from typesafe_sdk import Choice, Noul

        return Choice, Noul
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

        return Choice, Noul


def load_typesafe_api_key() -> str:
    env = os.environ.get("TYPESAFE_API_KEY", "").strip()
    if env:
        return env
    path = _SECRET_PATH if _SECRET_PATH.is_file() else _LEGACY_SECRET_PATH
    return path.read_text(encoding="utf-8").splitlines()[0].strip()


def _build_client() -> _SystemOneClient:
    """Construct a sync TypeSafeClient (lazy import)."""
    from typesafe_sdk import TypeSafeClient

    return TypeSafeClient(api_key=load_typesafe_api_key())


def _line_id(index: int) -> str:
    return f"L{index:03d}"


def _tag_lines(lines: Sequence[str]) -> str:
    return "\n".join(f"{_line_id(i)}| {line}" for i, line in enumerate(lines))


def _where_question(lines: Sequence[str], query: str):
    Choice, _Noul = _question_primitives()
    # Descriptive criteria strings (required by TypeSafe Choice schema /
    # fleet cookbook). Cap length to keep the closed set bounded.
    capped = list(lines)[:_MAX_CHOICE_LINES]
    criteria = {
        _line_id(i): (line if len(line) <= 120 else line[:117] + "...")
        for i, line in enumerate(capped)
    }
    return Choice(
        instructions=f'Which line of the document contains the answer to: "{query}"?',
        criteria=criteria,
    )


def _exists_question(query: str):
    # Bare Noul(instructions=...) matches every other call site in this repo;
    # do not import NoulCriteria (absent / unused elsewhere) inside the same
    # try that also loads Choice/Noul — a missing symbol would silently stub all three.
    _Choice, Noul = _question_primitives()
    return Noul(
        instructions=(
            f'Does any line of the document address or answer: "{query}"? '
            "True if at least one line states or directly implies the answer; "
            "false if no line addresses this."
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

    At most ``_MAX_CHOICE_LINES`` lines are scored via Choice; longer documents
    truncate the Choice set (Noul still sees the full tagged state).
    """
    if not lines:
        return {"exists": 0.0, "relevance": []}

    owns_client = client is None
    active_client = client if client is not None else _build_client()
    scored_lines = list(lines)[:_MAX_CHOICE_LINES]
    try:
        response = active_client.system_one(
            state=_tag_lines(lines),
            questions={
                "where": _where_question(scored_lines, query),
                "exists": _exists_question(query),
            },
            model=model,
        )
        probabilities = response.choices["where"].probabilities
        relevance = [probabilities.get(_line_id(i), 0.0) for i in range(len(scored_lines))]
        # Pad so callers always get one score per input line.
        if len(relevance) < len(lines):
            relevance.extend([0.0] * (len(lines) - len(relevance)))
        return {
            "exists": response.nouls["exists"].noul,
            "relevance": relevance,
        }
    finally:
        if owns_client:
            active_client.close()
