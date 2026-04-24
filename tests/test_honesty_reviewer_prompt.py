"""Policy-pinning tests for the Honesty reviewer prompt.

The `v6-review-honesty.md` prompt encodes rules that the reviewer uses
to judge whether a writer-emitted `<!-- VERIFY -->` marker satisfies a
precise claim. Before #1529 post-Phase-A tightening the rubric let the
reviewer double-count already-marked claims and nitpick marker format
(observed on a1/1 rebuild 2026-04-24 — three false-positive Honesty
findings on claims that DID carry markers).

These tests guard against two regression classes:

  1. Re-tightening the "source must be named" preference into a gate
     (would re-create the marker-format nitpick finding class).
  2. Deleting or shortening the same-line / same-paragraph vicinity
     rule (would re-create the missing-marker finding on claims that
     already carry a marker).

The tests are intentionally phrasing-flexible (substring checks, not
exact-string matches) so minor wording edits stay green as long as the
operative rules are preserved.
"""

from __future__ import annotations

from pathlib import Path

import pytest

_PROMPT_PATH = (
    Path(__file__).resolve().parent.parent
    / "scripts"
    / "build"
    / "phases"
    / "v6-review"
    / "v6-review-honesty.md"
)


@pytest.fixture(scope="module")
def prompt_text() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


# ── Version tag hygiene ─────────────────────────────────────────────


def test_prompt_exists(prompt_text: str) -> None:
    assert prompt_text.strip(), f"Prompt file is empty: {_PROMPT_PATH}"


def test_prompt_has_version_tag(prompt_text: str) -> None:
    """Every reviewer prompt starts with a semver-style version comment."""
    first_line = prompt_text.splitlines()[0]
    assert first_line.startswith("<!-- version:"), (
        f"Prompt must start with a `<!-- version: X.Y.Z | ... -->` tag; "
        f"got {first_line!r}"
    )


# ── Presence rule — marker presence satisfies a claim ──────────────


def test_prompt_states_presence_rule(prompt_text: str) -> None:
    """The rubric must tell the reviewer that a marker's presence
    satisfies a claim. Without this, the reviewer re-creates the
    double-counting finding class observed on a1/1 (marker on line,
    reviewer emits missing-marker finding anyway)."""
    lowered = prompt_text.lower()
    assert "presence" in lowered and "satisfies" in lowered, (
        "Rubric must state the presence rule — a VERIFY marker's "
        "presence must explicitly satisfy a precise claim. Expected "
        "both 'presence' and 'satisfies' to appear together."
    )


def test_prompt_forbids_missing_marker_finding_when_marker_present(
    prompt_text: str,
) -> None:
    """Stronger guard — the prompt must explicitly tell the reviewer
    NOT to emit a missing-marker finding when a marker is already
    attached. Positive 'presence satisfies' language alone can be read
    ambiguously; the prohibition must be explicit."""
    lowered = prompt_text.lower()
    forbidden_phrases = (
        "must not emit a finding",
        "must not emit a honesty finding",
        "do not emit a finding",
    )
    assert any(phrase in lowered for phrase in forbidden_phrases), (
        "Rubric must contain an explicit 'do not emit a finding when "
        "a marker is present' instruction. Expected one of "
        f"{forbidden_phrases!r}."
    )


# ── Vicinity rule — same line or same paragraph ───────────────────


def test_prompt_defines_marker_vicinity(prompt_text: str) -> None:
    """The rubric must define the vicinity in which a marker counts
    for a claim. Without an explicit definition the reviewer picks a
    stricter vicinity than the writer+annotator and double-counts."""
    lowered = prompt_text.lower()
    assert "same line" in lowered, (
        "Rubric must define vicinity as including 'same line'."
    )
    assert "same paragraph" in lowered, (
        "Rubric must define vicinity as including 'same paragraph'."
    )


# ── Marker-format nitpicks — out of scope ─────────────────────────


def test_prompt_excludes_marker_format_nitpicks(prompt_text: str) -> None:
    """The rubric must explicitly put marker-format nitpicks out of
    scope. Without this, the reviewer re-creates findings like
    'marker does not cite a specific packet section' (observed on
    a1/1 Finding #3)."""
    lowered = prompt_text.lower()
    assert "out of scope" in lowered, (
        "Rubric must state that marker-format nitpicks are 'out of "
        "scope' for Honesty. Expected the exact phrase 'out of scope'."
    )


def test_prompt_accepts_generic_markers(prompt_text: str) -> None:
    """Generic markers (that name the claim but not a specific packet
    section) must be accepted. The only insufficient marker shape is
    the bare `<!-- VERIFY -->`."""
    lowered = prompt_text.lower()
    assert "generic" in lowered, (
        "Rubric must mention that generic markers are acceptable."
    )
    # The word "bare" should appear in the context of the sole
    # insufficient marker shape.
    assert "bare" in lowered, (
        "Rubric must identify the bare `<!-- VERIFY -->` as the sole "
        "insufficient marker shape."
    )


# ── Worked examples — WRONG vs RIGHT ──────────────────────────────


def test_prompt_contains_worked_examples_section(prompt_text: str) -> None:
    """The rubric must include a worked-examples section. This is a
    high-leverage calibration surface for reviewer prompts — the
    brief explicitly requires it."""
    lowered = prompt_text.lower()
    assert "worked example" in lowered, (
        "Rubric must include a 'Worked examples' section heading. "
        "Reviewers are calibrated by concrete WRONG/RIGHT patterns, "
        "not by prose rules alone."
    )


def test_prompt_has_wrong_right_pattern(prompt_text: str) -> None:
    """Worked examples must be structured as WRONG/RIGHT pairs.
    Unlabelled examples leave the reviewer to infer the correct
    behavior, which is the failure mode this section closes."""
    # The bolded markdown labels used in the rubric.
    assert "**WRONG:**" in prompt_text, (
        "Worked examples must label WRONG behavior explicitly."
    )
    assert "**RIGHT:**" in prompt_text, (
        "Worked examples must label RIGHT behavior explicitly."
    )


def test_prompt_covers_restoration_of_g_example(prompt_text: str) -> None:
    """The rubric must include the Ґ-restoration worked example from
    the brief — it's the canonical case of the miscalibration this
    fix closes (Finding #1 on a1/1 sounds-letters-and-hello)."""
    assert "restoration of Ґ" in prompt_text, (
        "Worked examples must include the Ґ-restoration case — it is "
        "the canonical past-failure pattern this rubric fix addresses."
    )


# ── Preserved behavior — unmarked claims still enforced ────────────


def test_prompt_preserves_unmarked_claim_enforcement(prompt_text: str) -> None:
    """The tightening must NOT weaken enforcement on genuinely
    unmarked precise claims. The brief explicitly requires this."""
    # Look for any of the phrases that preserve the enforcement intent.
    preserved_phrases = (
        "do not weaken enforcement",
        "do not weaken",
        "does not weaken",
        "not weakening",
        "preserved behavior",
        "preserved behaviour",
        "preserved)",
    )
    lowered = prompt_text.lower()
    assert any(phrase in lowered for phrase in preserved_phrases), (
        "Rubric must state that the presence + vicinity rules tighten "
        "acceptance of MARKED claims without weakening enforcement on "
        f"UNMARKED ones. Expected one of {preserved_phrases!r}."
    )


def test_prompt_keeps_reject_rule_for_zero_markers(prompt_text: str) -> None:
    """Zero-marker modules with 3+ precise claims must still REJECT.
    If this test fires, the tightening has over-softened the rubric."""
    lowered = prompt_text.lower()
    assert "three or more precise claims" in lowered or "zero verify markers" in lowered, (
        "Rubric must preserve the 'REJECT when 3+ precise claims and "
        "zero markers' rule. If this fires, the hidden-uncertainty "
        "guard has been removed."
    )
