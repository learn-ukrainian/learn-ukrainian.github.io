"""V7.2 Step 5 — wiki-driven prompt generator (composition layer).

Composes, from the universal-rules registry + the wiki manifest:

- the **writer** prompt's rules block (`writer.preamble` + `writer.body` +
  `shared.contract`),
- the **reviewer** prompt's rules block (`reviewer.rubric` + `shared.contract`),
- ONE **Obligation Checklist** emitted verbatim into the writer prompt, the
  reviewer prompt, AND derived from the same extraction the
  ``wiki_coverage_gate`` parser uses — so the three consumers read one source.

This module owns ONLY the *composition junction*: it pulls universal rules from
``load_applicable_rules`` and the lesson-specific obligation checklist from the
wiki manifest, then renders both into prompt-ready strings. It is wired into
``linear_pipeline.writer_context`` / ``review_context`` behind the
``use_generator`` opt-in flag (``--use-generator`` on ``v7_build.py``). With the
flag OFF, the legacy ``linear-write.md`` / ``linear-review-dim.md`` templates
drive the build unchanged.

Composition boundary (ADR ``2026-05-28-wiki-driven-prompt-generator``,
design doc ``docs/best-practices/universal-rules-registry.md`` § "What is *not*
in the registry"):

- **Registry** = universal rules (``load_applicable_rules``). Identical text for
  m21 and m22 at the same level.
- **Wiki/RAG** = lesson substance (sequence steps, L2 errors, vocabulary
  minimum, the decolonization contrast pair for *this* lesson). Rendered by the
  existing ``linear_pipeline`` helpers; the Obligation Checklist below is the
  wiki-derived slice.
- The generator never inlines lesson substance into the *registry* path; it only
  joins the two at composition time.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from scripts.build.universal_rules_registry import load_applicable_rules

if TYPE_CHECKING:
    from scripts.build.universal_rules_registry import Rule

# Core CEFR levels map to the ``core`` registry track; everything else
# (seminar / pro codes) maps to ``seminar``. All current fragments use
# ``tracks: [all]``, so this only future-proofs track-scoped rules.
CORE_LEVELS = frozenset({"a1", "a2", "b1", "b2", "c1", "c2"})

# Default activity profile. The registry filters on ``activity_profiles`` and
# every current fragment uses ``[all]``; ``"default"`` matches those and gives
# Step 5+ a concrete profile string to specialise later.
DEFAULT_ACTIVITY_PROFILE = "default"

# Writer prompt receives preamble → body → shared-contract, in that slot order.
# Reviewer prompt receives rubric → shared-contract. ``shared.contract`` is the
# single-source point: every shared rule is emitted into BOTH blocks, so a rule
# the writer is asked to follow is the same text the reviewer is asked to verify.
WRITER_SLOT_ORDER = ("writer.preamble", "writer.body", "shared.contract")
REVIEWER_SLOT_ORDER = ("reviewer.rubric", "shared.contract")


def track_for_level(level: str) -> str:
    """Return the registry track predicate (``core`` / ``seminar``) for a level."""
    return "core" if level.lower() in CORE_LEVELS else "seminar"


def _render_rule(rule: Rule) -> str:
    """Render one registry rule into a prompt block, restoring its ``#R-*`` marker.

    Fragment bodies do NOT carry the ``#R-*`` marker (it lives in the
    frontmatter ``id``). The generator prepends ``rule.telemetry_id`` as both an
    HTML ``rule_id`` comment (matching the legacy template convention the
    pipeline telemetry keys on) and a bold heading, so the rendered prompt keeps
    the marker the gate telemetry + reviewer mirrors rely on — and so parity with
    the legacy templates holds.
    """
    marker = rule.telemetry_id
    heading = f"**{marker}**"
    if rule.description:
        heading = f"{heading} — {rule.description}"
    return f"<!-- rule_id: {marker} -->\n{heading}\n\n{rule.body}".strip()


def _compose_slots(
    level: str,
    track: str,
    activity_profile: str,
    slots: tuple[str, ...],
) -> str:
    """Concatenate every applicable rule across ``slots``, in slot then topo order.

    ``load_applicable_rules`` already topo-sorts (and filename-alphabetical
    tie-breaks) WITHIN each slot. We emit ALL rules the loader returns for each
    slot — the generator never filters further. Slots are disjoint (a rule has
    exactly one slot), but we guard against accidental double-emission anyway.
    """
    blocks: list[str] = []
    seen: set[str] = set()
    for slot in slots:
        for rule in load_applicable_rules(level.lower(), track, activity_profile, slot=slot):
            if rule.id in seen:
                continue
            seen.add(rule.id)
            blocks.append(_render_rule(rule))
    return "\n\n".join(blocks)


def build_writer_rules_block(
    level: str,
    track: str,
    activity_profile: str = DEFAULT_ACTIVITY_PROFILE,
) -> str:
    """Compose the writer prompt's universal-rules block.

    Emits ``writer.preamble`` then ``writer.body`` then ``shared.contract``.
    This applies to the WRITER prompt only; the reviewer block is built by
    :func:`build_reviewer_rules_block`, and the ``shared.contract`` rules appear
    in BOTH.
    """
    return _compose_slots(level, track, activity_profile, WRITER_SLOT_ORDER)


def build_reviewer_rules_block(
    level: str,
    track: str,
    activity_profile: str = DEFAULT_ACTIVITY_PROFILE,
) -> str:
    """Compose the reviewer prompt's universal-rules block.

    Emits ``reviewer.rubric`` then ``shared.contract``. ``reviewer.rubric`` is
    currently empty; the ``shared.contract`` rules carry the reviewer load. This
    is the single-source point — the reviewer verifies the SAME rule text the
    writer was handed.
    """
    return _compose_slots(level, track, activity_profile, REVIEWER_SLOT_ORDER)


def build_obligation_checklist(wiki_manifest: str | Mapping[str, object]) -> str:
    """Render the ONE Obligation Checklist from the wiki manifest's required items.

    Single source across all three consumers:

    - emitted verbatim into the writer prompt (``OBLIGATION_CHECKLIST`` token),
    - emitted verbatim into the reviewer prompt (same token),
    - derived from the SAME ``wiki_coverage_gate`` extraction
      (``_extract_required_items`` / ``_normalize_required_claim``) that
      ``linear_pipeline._render_wiki_coverage_required_items`` uses, so the gate
      parser and the prompts cannot drift.

    Lazy import of ``_render_wiki_coverage_required_items`` keeps this single
    renderer authoritative while avoiding an import cycle with ``linear_pipeline``
    (which imports this module behind the opt-in flag).
    """
    from scripts.build.linear_pipeline import _render_wiki_coverage_required_items

    return _render_wiki_coverage_required_items(wiki_manifest)
