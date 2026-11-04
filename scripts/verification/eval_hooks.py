"""Product calls for the lesson, preamble, and behaviour eval harnesses.

The eval package stays machinery and loads this module from a JSON entry
point. Each function reads the product implementation on the call, so a
patch of that module still applies.
"""

from __future__ import annotations

from typing import Any


def _stress_positions_in_marked_string(marked: str) -> tuple[str, list[int]]:
    from scripts.verification.stress import _stress_positions_in_marked_string as impl

    return impl(marked)


def verify_stress(word: str, *args: Any, **kwargs: Any) -> dict[str, Any]:
    from scripts.verification.stress import verify_stress as impl

    return impl(word, *args, **kwargs)


def check_text(*args: Any, **kwargs: Any) -> dict[str, Any]:
    from scripts.verification.check_text import check_text as impl

    return impl(*args, **kwargs)


def verify_words(*args: Any, **kwargs: Any) -> dict[str, list[dict[str, Any]]]:
    from scripts.verification.vesum import verify_words as impl

    return impl(*args, **kwargs)


def query_cefr_levels(*args: Any, **kwargs: Any) -> dict[str, list[dict[str, Any]]]:
    from scripts.wiki.sources_db import query_cefr_levels as impl

    return impl(*args, **kwargs)


def render_lesson_prompt(*args: Any, **kwargs: Any) -> str:
    from scripts.build.fresh.prompt import render_lesson_prompt as impl

    return impl(*args, **kwargs)


def parse_and_validate_reply(*args: Any, **kwargs: Any) -> dict[str, Any]:
    from scripts.build.fresh.writer import parse_and_validate_reply as impl

    return impl(*args, **kwargs)


def create_empty_ledger(*args: Any, **kwargs: Any) -> Any:
    from scripts.review.receipts.ledger import create_empty_ledger as impl

    return impl(*args, **kwargs)


def append(*args: Any, **kwargs: Any) -> str:
    from scripts.review.receipts.ledger import append as impl

    return impl(*args, **kwargs)


def records(*args: Any, **kwargs: Any) -> list[dict[str, Any]]:
    from scripts.review.receipts.ledger import records as impl

    return impl(*args, **kwargs)


def dumps(record: dict[str, Any]) -> str:
    from scripts.review.receipts.ledger import dumps as impl

    return impl(record)


def search_outcome(status: str, facts: dict[str, Any]) -> str | None:
    from scripts.review.receipts.outcomes import search_outcome as impl

    return impl(status, facts)


def __getattr__(name: str) -> Any:
    if name == "LedgerError":
        from scripts.review.receipts.ledger import LedgerError

        return LedgerError
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
