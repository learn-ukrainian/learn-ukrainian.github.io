"""PR1 runner slice lookup that does not rewrite sealed fixtures (#9001)."""

from __future__ import annotations

from pathlib import Path

from scripts.lexicon.runner.generate_pr1_fixture import resolve_sources_slice


def sources_slice(dest_dir: Path) -> Path:
    """Sources sqlite for runner tests.

    Builds the gitignored slice into ``dest_dir`` when the checkout does not
    already have one. Never writes under ``tests/fixtures/``.
    """
    return resolve_sources_slice(dest_dir)
