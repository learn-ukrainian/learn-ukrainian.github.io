"""Product review checks that machinery review attempts call (machinery move step 4, slice S14).

The dispatcher, the agent runtime and the review contract are machinery. They reach the product
modules below only through this module, which they load by the name configured in
``scripts/curriculum/review_hooks.v1.json`` (``scripts.review.product_hooks.attempt_hooks``).
Each function imports its product module when it is called, as the callers did before, so loading
this module imports nothing else: ``scripts.build.fresh.manifest`` reaches numpy, and a worker that
holds review slots must not import it (``scripts.dispatcher.worker._load_bound_review_code``).
"""

from __future__ import annotations

from pathlib import Path
from types import ModuleType
from typing import Any


def check_prompt(rendered_prompt: str, manifest_source: Path | str | dict[str, Any], **kwargs: Any) -> Any:
    """Check a rendered review prompt against its manifest (``scripts.review.prompts.check``)."""
    from scripts.review.prompts.check import check_prompt as check

    return check(rendered_prompt, manifest_source, **kwargs)


def pinned_entries(doc: Any) -> list[tuple[str, dict[str, Any]]]:
    """Every pinned input of a review manifest, with its location (``scripts.build.fresh.manifest``)."""
    from scripts.build.fresh.manifest import pinned_entries as entries

    return entries(doc)


def pin_refusals(manifest: dict[str, Any], repo_root: Path) -> list[Any]:
    """Every pin that may not reach the reviewer (``scripts.review.prompts.eligibility``)."""
    from scripts.review.prompts.eligibility import pin_refusals as refusals

    return refusals(manifest, repo_root)


def ledger() -> ModuleType:
    """The attempt receipt ledger: ``records``, ``LedgerError``, ``REVIEW_TOOLS`` and ``review_tools``."""
    from scripts.review.receipts import ledger as receipts_ledger

    return receipts_ledger


def openai_structured_output_forbidden_keywords() -> frozenset[str]:
    """The review-output keywords that OpenAI's strict schema does not support."""
    from scripts.audit.post_build_review import OPENAI_STRUCTURED_OUTPUT_FORBIDDEN_KEYWORDS

    return OPENAI_STRUCTURED_OUTPUT_FORBIDDEN_KEYWORDS


# ``scripts.dispatcher.worker.load_post_start_code`` calls the three functions below as the worker
# starts, each inside the import group it replaces, so a checkout change while the worker runs cannot
# mix module versions (#12634).


def bind_evidence_modules() -> None:
    """Import the curriculum evidence codes and lock that every worker's later steps import on demand."""
    from scripts.curriculum.evidence import codes, lock  # noqa: F401


def bind_receipt_modules() -> None:
    """Import the review receipt ledger and outcomes that every worker's later steps import on demand."""
    from scripts.review.receipts import ledger, outcomes  # noqa: F401


def bind_bound_review_modules() -> None:
    """Import the product modules only a bound formal review attempt (``review_attempt.run``) imports."""
    from scripts.build.fresh import manifest  # noqa: F401
    from scripts.curriculum.evidence import sources  # noqa: F401
    from scripts.review.prompts import check, eligibility  # noqa: F401
