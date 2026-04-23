"""Post-processor mutation-class registry + invariant.

EPIC #1451 Phase 4-C. Every text mutator that runs after the reviewer has
scored must declare an allowed mutation class; CI fails if actual behavior
on any golden fixture exceeds the declaration.

Structural defense against the #1448 bug class (silent base-character
mutation of Cyrillic content after reviewer has passed).

Mutation classes:
    STRESS_MARKS_ONLY    — adds/removes combining stress marks (U+0301) only.
                           Stripping U+0301 from input and output must yield
                           byte-identical text (no NFC/NFD normalization —
                           that would erase the #1448 bug shape).
    WRAP_ONLY            — adds/removes HTML/MDX tags around existing text.
                           Text content (tags stripped) must be equal modulo
                           whitespace collapse.
    APPENDIX_ONLY        — rstrip'd input must be a prefix of output. Only
                           the tail may grow.
    DETERMINISTIC_STRIP  — may remove text. The casefolded NFD-base
                           codepoint multiset of the output must be a
                           submultiset of the input. No new codepoints may
                           appear.
    NONE                 — read-only. Input must equal output.

Adding a new post-processor to the pipeline without registering it here
fails ``test_post_processor_mutation_invariant.py`` at collection time.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

STRESS_MARK = "\u0301"  # Combining acute accent
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


class MutationClass(Enum):
    STRESS_MARKS_ONLY = "stress_marks_only"
    WRAP_ONLY = "wrap_only"
    APPENDIX_ONLY = "appendix_only"
    DETERMINISTIC_STRIP = "deterministic_strip"
    NONE = "none"


@dataclass(frozen=True)
class Violation:
    kind: str
    processor: str
    before_fragment: str
    after_fragment: str
    note: str


REGISTRY: dict[str, MutationClass] = {}


def register_post_processor(name: str, mutation_class: MutationClass) -> None:
    """Register a post-review mutator under its declared class.

    Idempotent on re-registration with the same class (module reloads are
    safe). Raises ValueError on a class-conflict re-registration so tests
    catch drift.
    """
    if name in REGISTRY and REGISTRY[name] is not mutation_class:
        raise ValueError(
            f"Post-processor {name!r} re-registered with different class: "
            f"{REGISTRY[name].value} != {mutation_class.value}"
        )
    REGISTRY[name] = mutation_class


# --- Verifiers ---


def _strip_stress_only(s: str) -> str:
    """Remove ONLY the stress-mark codepoint (U+0301); preserve everything else byte-wise.

    NOTE: intentionally does NOT NFD-normalize first. Normalizing would
    erase the #1448 bug shape — two byte sequences that are
    Unicode-equivalent but not byte-equal (e.g. precomposed й vs decomposed
    и + combining breve). The #1448 class of bug is exactly a silent
    normalization that breaks downstream byte-sensitive consumers, so
    stress-mark-only mutators must preserve bytes modulo U+0301 only.
    """
    return s.replace(STRESS_MARK, "")


def _casefolded_base_counter(s: str) -> dict[int, int]:
    """Casefolded NFD-base codepoint multiset (combining marks dropped)."""
    counter: dict[int, int] = {}
    for ch in unicodedata.normalize("NFD", s).casefold():
        if unicodedata.combining(ch):
            continue
        cp = ord(ch)
        counter[cp] = counter.get(cp, 0) + 1
    return counter


def _first_divergence(a: str, b: str) -> int | None:
    for i, (ca, cb) in enumerate(zip(a, b, strict=False)):
        if ca != cb:
            return i
    if len(a) != len(b):
        return min(len(a), len(b))
    return None


def _window(s: str, i: int, radius: int = 20) -> str:
    return s[max(0, i - radius) : i + radius]


def verify_stress_marks_only(processor: str, before: str, after: str) -> list[Violation]:
    before_ns = _strip_stress_only(before)
    after_ns = _strip_stress_only(after)
    idx = _first_divergence(before_ns, after_ns)
    if idx is None:
        return []
    return [
        Violation(
            kind="stress_marks_only_violation",
            processor=processor,
            before_fragment=_window(before_ns, idx),
            after_fragment=_window(after_ns, idx),
            note=(
                "STRESS_MARKS_ONLY: stripping U+0301 from input and output "
                f"should yield byte-identical text; diverges at offset {idx}. "
                "Any other codepoint change (including NFC/NFD normalization "
                "of й, ї, etc.) is the #1448 class bug this invariant defends."
            ),
        )
    ]


def verify_wrap_only(processor: str, before: str, after: str) -> list[Violation]:
    before_text = _TAG_RE.sub("", before)
    after_text = _TAG_RE.sub("", after)
    before_norm = _WS_RE.sub(" ", before_text).strip()
    after_norm = _WS_RE.sub(" ", after_text).strip()
    if before_norm == after_norm:
        return []
    idx = _first_divergence(before_norm, after_norm) or 0
    return [
        Violation(
            kind="wrap_only_content_changed",
            processor=processor,
            before_fragment=_window(before_norm, idx),
            after_fragment=_window(after_norm, idx),
            note=(
                "WRAP_ONLY: text content (with tags stripped + whitespace "
                "collapsed) must not change"
            ),
        )
    ]


def verify_appendix_only(processor: str, before: str, after: str) -> list[Violation]:
    prefix = before.rstrip()
    if after.startswith(prefix):
        return []
    idx = _first_divergence(prefix, after) or 0
    return [
        Violation(
            kind="appendix_only_prefix_violation",
            processor=processor,
            before_fragment=_window(prefix, idx),
            after_fragment=_window(after, idx),
            note=(
                "APPENDIX_ONLY: the rstrip'd input must be a prefix of the "
                f"output; diverges at offset {idx}"
            ),
        )
    ]


def verify_deterministic_strip(
    processor: str, before: str, after: str
) -> list[Violation]:
    before_cnt = _casefolded_base_counter(before)
    after_cnt = _casefolded_base_counter(after)
    for cp, cnt in after_cnt.items():
        before_count = before_cnt.get(cp, 0)
        if before_count < cnt:
            ch = chr(cp)
            try:
                name = unicodedata.name(ch)
            except ValueError:
                name = f"U+{cp:04X}"
            return [
                Violation(
                    kind="deterministic_strip_new_codepoint",
                    processor=processor,
                    before_fragment="",
                    after_fragment=ch,
                    note=(
                        f"DETERMINISTIC_STRIP: character {ch!r} ({name}) "
                        f"appears {cnt} time(s) casefolded in output but only "
                        f"{before_count} in input — post-review mutator "
                        f"introduced a new codepoint (#1448 class)"
                    ),
                )
            ]
    return []


def verify_none(processor: str, before: str, after: str) -> list[Violation]:
    if before == after:
        return []
    idx = _first_divergence(before, after) or 0
    return [
        Violation(
            kind="none_class_mutated",
            processor=processor,
            before_fragment=_window(before, idx),
            after_fragment=_window(after, idx),
            note=f"NONE: processor must not mutate; diverges at offset {idx}",
        )
    ]


_VERIFIERS: dict[MutationClass, Callable[[str, str, str], list[Violation]]] = {
    MutationClass.STRESS_MARKS_ONLY: verify_stress_marks_only,
    MutationClass.WRAP_ONLY: verify_wrap_only,
    MutationClass.APPENDIX_ONLY: verify_appendix_only,
    MutationClass.DETERMINISTIC_STRIP: verify_deterministic_strip,
    MutationClass.NONE: verify_none,
}


def verify_mutation(processor_name: str, before: str, after: str) -> list[Violation]:
    if processor_name not in REGISTRY:
        raise KeyError(
            f"Post-processor {processor_name!r} is not registered. "
            f"Call register_post_processor() at import time."
        )
    return _VERIFIERS[REGISTRY[processor_name]](processor_name, before, after)


__all__ = [
    "REGISTRY",
    "MutationClass",
    "Violation",
    "register_post_processor",
    "verify_appendix_only",
    "verify_deterministic_strip",
    "verify_mutation",
    "verify_none",
    "verify_stress_marks_only",
    "verify_wrap_only",
]

# Register the post-review mutators that currently live in the pipeline.
# Done at module import so any caller of ``REGISTRY`` sees a complete set.
# The actual callable for each processor is resolved lazily by
# ``get_processor_callable`` to avoid pulling heavy imports at registration.
from build.post_processors._migrations import register_existing

register_existing()
