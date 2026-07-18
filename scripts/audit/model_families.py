#!/usr/bin/env python3
"""Canonical model-family vocabulary and normalizers for reviewer selection.

Single source of truth consumed by BOTH enforcement layers:

* the live reviewer dispatcher (``scripts.audit.llm_reviewer_dispatch``)
* the Layer-B shadow lineage path (``scripts.audit.layerb_shadow``)
* the formal code-review resolver (``scripts.review.reviewer_resolver``)

``Family.UNKNOWN`` is a first-class answer: an unrecognized lineage is UNKNOWN,
never silently ``None`` and never a raw token smuggled past the gate. The
compatibility wrappers in both consuming modules translate UNKNOWN to their
existing refusal sentinel at the seam, so an unknown writer/reviewer always
produces an explicit refusal (``ReviewerLineageError`` on the live path;
``failure_class=LINEAGE_OR_ROUTE`` in Layer-B) rather than acceptance or a
crash.

Routing decisions codified here (2026-07-17, issue #5385):

* ``grok`` → ``xai`` — a family of its own, SEPARATE from cursor. The old
  Layer-B ``grok-cursor`` merge is gone.
* ``cursor`` / ``composer`` / ``auto`` alone → ``UNKNOWN``. cursor-Auto is
  never an acceptable formal-review identity
  (``agents_extensions/shared/rules/model-assignment.md``); a cursor seat that
  records a pinned model inherits the pin's family.
* ``agy`` / ``gemma`` / ``gemini`` → ``google`` (restored in Layer-B, which
  previously orphaned ``agy``).
* ``codex`` / ``gpt`` / ``openai`` → ``openai`` (unified; Layer-B previously
  used ``gpt``).
* ``claude`` / ``anthropic`` / ``opus`` / ``sonnet`` → ``anthropic``.
* Concrete formal-review model ids additionally resolve to their provider
  families: ``composer-2.5`` / ``kimi-*`` → ``moonshot``; ``glm-*`` /
  ``zhipu`` → ``zhipu``; and ``poolside`` / ``laguna`` → ``poolside``.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from enum import StrEnum
from typing import Any

UNKNOWN_FAMILY = "unknown"
FIXTURE_FAMILY = "fixture"


class Family(StrEnum):
    """Canonical model families. The one vocabulary for the whole chain.

    Members are strings so ``Family.XAI == "xai"`` compares cleanly against
    legacy string-typed call sites. ``UNKNOWN`` and ``FIXTURE`` are
    first-class: UNKNOWN is the answer for any lineage the vocabulary cannot
    classify, FIXTURE marks human/synthetic non-model content.
    """

    GOOGLE = "google"
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    XAI = "xai"
    MOONSHOT = "moonshot"
    ZHIPU = "zhipu"
    POOLSIDE = "poolside"
    QWEN = "qwen"
    FIXTURE = FIXTURE_FAMILY
    UNKNOWN = UNKNOWN_FAMILY


_FIXTURE_MARKERS = frozenset({"fixture", "adversarial-fixture"})

# Lineage-metadata fields that may carry a model-family signal. A pinned model
# (``pin`` / ``resolved_model`` / ``*_model_id``) is more specific than a coarse
# ``family``/``vendor``/``provider`` label, so it can override a cursor seat.
_LINEAGE_FIELDS: tuple[str, ...] = (
    "family",
    "vendor",
    "provider",
    "pin",
    "pin_slug",
    "resolved_model",
    "model",
    "model_id",
    "reviewer_model_id",
    "writer_model_id",
)

# Marker words → family. Matched as whole words (casefolded) so e.g. ``gemmate``
# is NOT mistaken for ``gemma``. cursor/composer/auto are handled separately
# because cursor-Auto is UNKNOWN unless a concrete pin overrides it.
_FAMILY_TOKEN_RULES: tuple[tuple[tuple[str, ...], Family], ...] = (
    (("deepseek",), Family.DEEPSEEK),
    (("gemma", "gemini", "agy", "google"), Family.GOOGLE),
    (("codex", "openai", "gpt"), Family.OPENAI),
    (("anthropic", "claude", "fable", "opus", "sonnet"), Family.ANTHROPIC),
    (("grok", "xai"), Family.XAI),
    (("composer-2.5", "kimi"), Family.MOONSHOT),
    (("glm", "zhipu"), Family.ZHIPU),
    (("poolside", "laguna", "pool"), Family.POOLSIDE),
    (("qwen",), Family.QWEN),
)


def _compile_family_patterns() -> tuple[tuple[re.Pattern[str], Family], ...]:
    compiled: list[tuple[re.Pattern[str], Family]] = []
    for markers, family in _FAMILY_TOKEN_RULES:
        alternation = "|".join(re.escape(marker) for marker in markers)
        compiled.append((re.compile(rf"(?:^|[^a-z0-9])(?:{alternation})(?:$|[^a-z0-9])"), family))
    return tuple(compiled)


_FAMILY_PATTERNS = _compile_family_patterns()
_CURSOR_PATTERN = re.compile(r"(?:^|[^a-z0-9])(?:cursor|composer|auto)(?:$|[^a-z0-9])")
_CONCRETE_CURSOR_MODEL_PATTERN = re.compile(r"(?:^|[^a-z0-9])composer-2\.5(?:$|[^a-z0-9])")


def normalize_family(value: Any) -> Family:
    """Normalize a single token (string or stringifiable) to a ``Family``.

    The one token→family mapping the whole route-refusal chain consumes.
    Returns ``Family.UNKNOWN`` for empty/unrecognized input and for bare
    cursor/composer/auto markers (cursor-Auto). ``composer-2.5`` is an
    exception because it is a concrete model identity accepted by the formal
    review policy. Returns ``Family.FIXTURE`` for the fixture sentinels.
    """

    if value is None:
        return Family.UNKNOWN
    text = str(value).strip().casefold()
    if not text:
        return Family.UNKNOWN
    if text in _FIXTURE_MARKERS:
        return Family.FIXTURE
    if _CURSOR_PATTERN.search(text) and not _CONCRETE_CURSOR_MODEL_PATTERN.search(text):
        # cursor-Auto: identity not pinned, so it is not a usable formal-review
        # family. A cursor seat that records a concrete pin resolves through
        # the pin via ``normalize_lineage_family``. Composer without its 2.5
        # model identity is equally insufficient.
        return Family.UNKNOWN
    for pattern, family in _FAMILY_PATTERNS:
        if pattern.search(text):
            return family
    return Family.UNKNOWN


def _visit(metadata: Any, concrete: set[Family], saw_fixture: list[bool]) -> None:
    if isinstance(metadata, str):
        family = normalize_family(metadata)
        if family is Family.FIXTURE:
            saw_fixture.append(True)
        elif family is not Family.UNKNOWN:
            concrete.add(family)
    elif isinstance(metadata, Mapping):
        for field in _LINEAGE_FIELDS:
            if field in metadata:
                _visit(metadata[field], concrete, saw_fixture)


def normalize_lineage_family(metadata: Any) -> Family:
    """Normalize lineage metadata to a single ``Family``.

    Walks the lineage-metadata fields. A pinned model overrides a coarse
    cursor seat, so ``{"family": "cursor", "pin": "grok-4"}`` resolves to
    ``xai`` while ``{"family": "cursor"}`` (no pin) is ``UNKNOWN``. When two
    or more distinct concrete families appear (e.g. a ``google`` family with a
    ``deepseek`` pin) the signal is ambiguous and the result is ``UNKNOWN``
    (fail closed). Fixture-only metadata is ``FIXTURE``.
    """

    if metadata is None:
        return Family.UNKNOWN
    if isinstance(metadata, str):
        return normalize_family(metadata)
    concrete: set[Family] = set()
    saw_fixture: list[bool] = []
    _visit(metadata, concrete, saw_fixture)
    if len(concrete) == 1:
        return next(iter(concrete))
    if concrete:
        # 2+ distinct concrete families: ambiguous, fail closed.
        return Family.UNKNOWN
    return Family.FIXTURE if saw_fixture else Family.UNKNOWN
