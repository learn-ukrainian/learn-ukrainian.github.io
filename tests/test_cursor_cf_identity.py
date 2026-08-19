"""Cursor CF identity smoke tests (#6957).

Pins the attested-vs-unattested Cursor identity contract for the formal
cross-family review gate:

1. An attested ``cursor:composer-2.5`` author + same-family reviewer -> refuse
   (same-family checks use the ATTESTED model family: Cursor ``composer-2.5``
   is Moonshot, Cursor ``grok-4.6`` is xAI — neither may be reviewed by its
   native sibling).
2. An attested Cursor author + eligible other-family exact-head -> allowed.
3. ``cursor:auto`` with ``resolved_model=null`` -> not driver-of-record and
   never a single-reviewer CF identity (Auto cannot launder into fake CF).
4. The #6489 dual-family quorum path still exists for generic
   unattested-harness authors (retained fallback history per #6955 — do not
   delete it).
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import delegate

from scripts.review import reviewer_resolver
from scripts.review.model_catalog import CURSOR_AUTO_EXPECTED_ATTESTATION_RULE, load_model_catalog
from scripts.review.reviewer_resolver import (
    CURSOR_AUTO_MODEL_TOKENS,
    CURSOR_AUTO_UNION_FAMILIES,
    CURSOR_AUTO_UNION_FAMILY,
    REVIEW_CANDIDATES,
    TERRA,
    UNATTESTED_AUTHOR_FAMILY,
    ResolverInputs,
    evaluate_candidate,
    resolve_author_family,
    resolve_reviewer,
)

_EXACT_HEAD = "6957cf" + "a" * 34  # 40-hex exact PR head


# --- box 1: attested author + same-family reviewer -> refuse -------------------


def test_cursor_attested_composer_author_refuses_same_family_review():
    """Attested cursor:composer-2.5 is Moonshot: Kimi/Composer reviewers refuse."""
    inputs = ResolverInputs(author_model="cursor:composer-2.5", risk="medium")
    assert resolve_author_family(inputs.author_model) == "moonshot"

    for name in ("composer-2.5", "kimi-k3"):
        result = evaluate_candidate(REVIEW_CANDIDATES[name], inputs)
        assert result.status == "excluded", (name, result.status)
        assert "same family" in result.reason

    resolution = resolve_reviewer(inputs)
    assert resolution.fail_closed_reason is None
    assert resolution.selected is not None
    assert resolution.selected.family != "moonshot"
    for entry in resolution.trace:
        assert entry.family != "moonshot" or entry.status == "excluded", entry.name


def test_cursor_attested_grok_author_refuses_same_family_review():
    """Attested cursor:grok-4.6 is xAI: neither native Grok nor the Cursor
    grok fallback may review it — the attested family binds, not the harness."""
    inputs = ResolverInputs(author_model="cursor:grok-4.6", risk="medium")
    assert resolve_author_family(inputs.author_model) == "xai"

    for name in ("grok-4.6", "grok-4.6-cursor-fallback"):
        result = evaluate_candidate(REVIEW_CANDIDATES[name], inputs)
        assert result.status == "excluded", (name, result.status)
        assert "same family" in result.reason

    resolution = resolve_reviewer(inputs)
    assert resolution.fail_closed_reason is None
    assert resolution.selected is not None
    assert resolution.selected.family != "xai"


# --- box 2: attested author + eligible other family exact-head -> allowed ------


def test_cursor_attested_author_allows_other_family_exact_head_review():
    for token, forbidden_family in (("cursor:composer-2.5", "moonshot"), ("cursor:grok-4.6", "xai")):
        inputs = ResolverInputs(author_model=token, risk="medium", exact_head=_EXACT_HEAD)
        resolution = resolve_reviewer(inputs)
        assert resolution.fail_closed_reason is None, token
        assert resolution.selected is not None, token
        assert resolution.selected.family != forbidden_family, token
        assert resolution.selected.transport != "cursor", token
        assert resolution.selected.selection_score is not None, token
        assert resolution.quorum == (), token

        # Exact-head selection is deterministic: same head, same reviewer.
        again = resolve_reviewer(inputs)
        assert again.selected is not None
        assert again.selected.name == resolution.selected.name, token
        assert again.selected.selection_score == resolution.selected.selection_score, token


# --- box 3: cursor:auto + resolved_model=null -> not driver-of-record, not CF --


def test_cursor_auto_null_resolved_model_is_not_driver_of_record():
    """An Auto run whose telemetry carries no concrete model (JSON null) is
    recorded as unattested: the ``auto`` selector is never promoted to family
    proof, so the session cannot be driver-of-record."""
    unattested_null = delegate._cursor_model_state(
        agent="cursor",
        result=object(),
        substitution={"actual_model": None, "actual_model_known": False, "source": "unattested-harness"},
    )
    assert unattested_null == {
        "resolved_model": "unattested-harness",
        "resolved_model_known": False,
        "resolved_model_source": "unattested-harness",
    }

    # A literal "null" string from stream-json is equally non-concrete.
    unattested_str = delegate._cursor_model_state(
        agent="cursor",
        result=object(),
        substitution={"actual_model": "null", "actual_model_known": True, "source": "cursor-stream-json"},
    )
    assert unattested_str["resolved_model"] == "unattested-harness"
    assert unattested_str["resolved_model_known"] is False

    # Positive control: an attested concrete model IS promoted (driver-of-record
    # requires exactly this attestation).
    attested = delegate._cursor_model_state(
        agent="cursor",
        result=object(),
        substitution={"actual_model": "composer-2.5", "actual_model_known": True, "source": "cursor-stream-json"},
    )
    assert attested["resolved_model"] == "composer-2.5"
    assert attested["resolved_model_known"] is True
    assert attested["model"] == "composer-2.5"

    # The versioned catalog pins the driver-of-record attestation rule.
    catalog = load_model_catalog()
    cursor_seat = catalog["orchestrator_seats"]["cursor"]
    assert cursor_seat["attestation_rule"] == CURSOR_AUTO_EXPECTED_ATTESTATION_RULE
    assert cursor_seat["attestation_rule"] == "driver_of_record_requires_attested_resolved_model"


def test_cursor_unattested_auto_is_not_a_single_reviewer_cf_identity():
    """cursor:auto is never an acceptable formal-review identity: it resolves
    to the allowlist-union sentinel (not a concrete family), no Auto candidate
    exists on the review ladder, and an Auto author's reviewer comes from
    OUTSIDE the {xAI, Moonshot} union — never a Cursor transport."""
    assert resolve_author_family("cursor:auto") == CURSOR_AUTO_UNION_FAMILY
    # The union sentinel is a resolution outcome, not a concrete vendor family.
    assert CURSOR_AUTO_UNION_FAMILY not in {candidate.family for candidate in REVIEW_CANDIDATES.values()}

    # No formal-review candidate is an unattested Cursor Auto identity.
    assert "cursor-auto" not in REVIEW_CANDIDATES
    for candidate in REVIEW_CANDIDATES.values():
        assert candidate.family != CURSOR_AUTO_UNION_FAMILY, candidate.name
        if candidate.transport == "cursor" or candidate.route == "cursor":
            assert candidate.concrete_model not in CURSOR_AUTO_MODEL_TOKENS, candidate.name

    resolution = resolve_reviewer(ResolverInputs(author_model="cursor:auto", risk="medium"))
    assert resolution.fail_closed_reason is None
    assert resolution.selected is not None
    assert resolution.selected.family not in CURSOR_AUTO_UNION_FAMILIES
    assert resolution.selected.transport != "cursor"
    assert resolution.quorum == ()


# --- box 4: #6489 dual-family quorum path still exists -------------------------


def test_cursor_unattested_author_dual_family_quorum_path_is_retained(monkeypatch):
    """The #6489 dual-family quorum fallback is retained for generic
    unattested-harness authors (superseded for Cursor Auto by the #6955 union
    rule, but not deleted).

    No current author token produces the unattested-harness sentinel — Cursor
    Auto now resolves to the union family — so this test substitutes the
    sentinel at the identity-resolution seam to exercise the quorum branch
    itself. It does NOT touch resolved_model attestation: it simulates a
    future/generic unattested multi-model harness, the exact case the quorum
    machinery is kept for.
    """
    monkeypatch.setattr(
        reviewer_resolver,
        "resolve_author_family",
        lambda *args, **kwargs: UNATTESTED_AUTHOR_FAMILY,
    )

    resolution = reviewer_resolver.resolve_reviewer(
        ResolverInputs(author_model="generic-unattested-harness", risk="medium", exact_head=_EXACT_HEAD)
    )
    assert resolution.fail_closed_reason is None
    # There is no single reviewer of record: BOTH quorum seats must pass.
    assert resolution.selected is None
    assert len(resolution.quorum) == 2
    first, second = resolution.quorum
    assert first.family != second.family
    assert first.status == second.status == "selected"
    assert resolution.quorum_rule is not None
    assert "two independent exact-head PASS verdicts" in resolution.quorum_rule
    assert "distinct attested" in resolution.quorum_rule


def test_cursor_unattested_quorum_fail_closed_and_pin_cannot_substitute(monkeypatch):
    monkeypatch.setattr(
        reviewer_resolver,
        "resolve_author_family",
        lambda *args, **kwargs: UNATTESTED_AUTHOR_FAMILY,
    )

    # Fewer than two eligible distinct families fails closed — no quorum.
    one_family = reviewer_resolver.resolve_reviewer(
        ResolverInputs(author_model="generic-unattested-harness"),
        ladder=((TERRA,),),
    )
    assert one_family.selected is None
    assert one_family.quorum == ()
    assert "dual-family quorum unsatisfiable" in one_family.fail_closed_reason

    # An explicit reviewer pin can never substitute for the quorum.
    pinned = reviewer_resolver.resolve_reviewer(
        ResolverInputs(
            author_model="generic-unattested-harness",
            pinned_candidate="claude-sonnet-5",
            pressure_override_reason="probe",
        )
    )
    assert pinned.selected is None
    assert pinned.quorum == ()
    assert "dual-family quorum" in pinned.fail_closed_reason
