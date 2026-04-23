"""Registers post-review mutators that currently live in the pipeline.

Kept separate from the package ``__init__`` so that test collection can
import the registry without pulling the heavy mutator modules (v6_build
imports sqlite, yaml, research modules, etc.). The registrations here
are name + class only; callables are resolved lazily via
``get_processor_callable``.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parents[2]
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))


def register_existing() -> None:
    from build.post_processors import MutationClass, register_post_processor

    # scripts/pipeline/stress_annotator.py — stress mark annotation.
    # Called AFTER review as the ``stress`` phase (v6_build.py: step_annotate
    # dispatched at phase "stress"). Mutation class: STRESS_MARKS_ONLY.
    register_post_processor(
        "pipeline.stress_annotator.annotate_stress",
        MutationClass.STRESS_MARKS_ONLY,
    )

    # scripts/build/v6_build.py: _post_process_content — deterministic style
    # cleanup (strips duplicate summaries, content notes, manual stress
    # marks, TAB markers, motivational closers, empty intensifiers, stray
    # DSL quotes, writer-generated YouTube embeds). Called post-review
    # when engagement <=7 (v6_build.py:11430) and in the heal loop after
    # prose regen (v6_build.py:11756, 9897). Mutation class:
    # DETERMINISTIC_STRIP — strips content only, never introduces new
    # codepoints.
    register_post_processor(
        "build.v6_build._post_process_content",
        MutationClass.DETERMINISTIC_STRIP,
    )


def get_processor_callable(name: str):
    """Resolve a processor name to a ``text -> text`` callable.

    Separated from registration so that test collection (which imports the
    registry) does not pull heavy modules. Tests call this only for
    processors they actually exercise.
    """
    if name == "pipeline.stress_annotator.annotate_stress":
        from pipeline.stress_annotator import annotate_stress

        def _invoke_stress(text: str) -> str:
            annotated, _count = annotate_stress(text)
            return annotated

        return _invoke_stress

    if name == "build.v6_build._post_process_content":
        import tempfile

        def _invoke_post_process(text: str) -> str:
            from build.v6_build import _post_process_content

            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".md",
                prefix="pp_invariant_",
                delete=False,
                encoding="utf-8",
            ) as handle:
                handle.write(text)
                tmp_path = Path(handle.name)
            try:
                _post_process_content(tmp_path)
                return tmp_path.read_text("utf-8")
            finally:
                tmp_path.unlink(missing_ok=True)

        return _invoke_post_process

    raise KeyError(f"No callable resolver for post-processor {name!r}")
