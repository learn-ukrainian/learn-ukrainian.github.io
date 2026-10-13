"""Positive private-target admission preserves existing seats (#10511)."""

import argparse
from unittest.mock import patch

import pytest

from scripts import delegate
from scripts.agent_runtime import registry, target_admission


@pytest.mark.parametrize(
    "repo", ["public-monorepo", "private-infra", "private-product", "infra-private", "hramatka", "unknown"]
)
@pytest.mark.parametrize("seat", tuple(seat for seat in registry.AGENTS if seat != "muse"))
def test_existing_seat_matrix_identical(repo, seat):
    def outcome():
        try:
            return ("admitted", target_admission.resolve_and_admit((seat,), mode="read-only", repo=repo))
        except Exception as exc:
            return (type(exc).__name__, str(exc))

    actual = outcome()
    with patch.object(target_admission, "refuse_private_repository_target", lambda *args, **kwargs: None):
        before = outcome()
    assert actual == before


@pytest.mark.parametrize("repo", ["infra-private", "hramatka", "unknown", "private-infra", "private-product"])
@pytest.mark.parametrize(
    "seat,model", [("muse", "muse-wonder-1.0"), ("codex", "muse-wonder-1.0"), ("future-seat", None)]
)
def test_new_seat_and_model_private_target_denied(repo, seat, model):
    with pytest.raises(ValueError, match="PRIVATE_REPOSITORY_SEAT_NOT_ALLOWED"):
        target_admission.resolve_and_admit((seat,), model=model, mode="read-only", repo=repo)


@pytest.mark.parametrize("review,role", [(False, None), (True, "review"), (False, "advisor")])
def test_private_muse_refused_before_review_or_advisor_effects(review, role):
    with patch.object(target_admission, "_refuse_non_review_models", side_effect=AssertionError("review reached")):
        with pytest.raises(ValueError, match="PRIVATE_REPOSITORY_SEAT_NOT_ALLOWED"):
            target_admission.resolve_and_admit(
                ("muse",),
                model="muse-wonder-1.0",
                mode="read-only",
                repo="private-infra",
                review=review,
                task_role=role,
            )


def test_resolved_private_target_is_rechecked():
    with pytest.raises(ValueError, match="PRIVATE_REPOSITORY_SEAT_NOT_ALLOWED"):
        target_admission.resolve_and_admit(
            ("codex",), mode="read-only", repo="private-infra", resolver=lambda name: "future-seat"
        )


def test_attached_private_target_is_checked():
    with pytest.raises(ValueError, match="PRIVATE_REPOSITORY_SEAT_NOT_ALLOWED"):
        target_admission.resolve_and_admit(
            ("codex",), mode="read-only", repo="private-infra", attachments=({"to_model": "muse-wonder-1.0"},)
        )


def test_dispatch_private_refusal_is_typed():
    args = argparse.Namespace(agent="muse", model="muse-wonder-1.0", mode="read-only", task_id="muse-test")
    refusal, target = delegate._admit_dispatch_target(args, agent="muse", trees=(), repo_role="private-infra")
    assert target is None and "PRIVATE_REPOSITORY_SEAT_NOT_ALLOWED" in refusal
