"""Positive private-target admission preserves existing seats (#10511)."""

import argparse
from copy import deepcopy
from unittest.mock import patch

import pytest

from scripts import delegate
from scripts.agent_runtime import registry, target_admission
from scripts.review.model_catalog import load_model_catalog, model_aliases

EXISTING_MODELS = (
    None,
    *sorted(
        {alias for alias, model in model_aliases(load_model_catalog()).items() if model != "muse-wonder-1.0"}
        | {"auto", "opus", "sonnet", "haiku", "qwen3.6-plus"}
    ),
)


@pytest.mark.parametrize(
    "repo", ["public-monorepo", "private-infra", "private-product", "infra-private", "hramatka", "unknown"]
)
@pytest.mark.parametrize("seat", tuple(seat for seat in registry.AGENTS if seat != "muse"))
def test_existing_seat_matrix_identical(repo, seat, monkeypatch):
    catalog = load_model_catalog()
    monkeypatch.setattr("scripts.review.model_catalog.load_model_catalog", lambda: catalog)

    def outcome(model):
        try:
            return ("admitted", target_admission.resolve_and_admit((seat,), model=model, mode="read-only", repo=repo))
        except Exception as exc:
            return (type(exc).__name__, str(exc))

    for model in EXISTING_MODELS:
        actual = outcome(model)
        with patch.object(target_admission, "refuse_private_repository_target", lambda *args, **kwargs: None):
            before = outcome(model)
        assert actual == before, (repo, seat, model)


@pytest.mark.parametrize("repo", ["infra-private", "hramatka", "unknown", "private-infra", "private-product"])
@pytest.mark.parametrize(
    "seat,model",
    [
        ("muse", None),
        ("muse", "gpt-6.1-sol"),
        ("muse", "muse-wonder-1.0"),
        ("codex", "muse-wonder-1.0"),
        ("codex", "meta/muse-wonder-1.0"),
        ("codex", "MUSE-WONDER-1.0[1m]"),
        ("future-seat", None),
    ],
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


@pytest.mark.parametrize("family,transports", [("meta", ["native_codex"]), ("openai", ["muse"])])
def test_private_model_identification_uses_catalog_metadata(family, transports):
    catalog = deepcopy(load_model_catalog())
    catalog["models"]["gpt-6.1-sol"]["family"] = family
    catalog["models"]["gpt-6.1-sol"]["transports"] = transports
    with patch("scripts.review.model_catalog.load_model_catalog", return_value=catalog):
        with pytest.raises(ValueError, match="PRIVATE_REPOSITORY_SEAT_NOT_ALLOWED"):
            target_admission.refuse_private_repository_target(("codex",), ("openai/gpt-6.1-sol",), repo="private-infra")


@pytest.mark.parametrize(
    "seat,model",
    [("cursor", "auto"), ("claude", "sonnet"), ("claude", "opus"), ("claude", "haiku"), ("qwen", "qwen3.6-plus")],
)
def test_documented_private_model_labels_still_admitted(seat, model):
    (target,) = target_admission.resolve_and_admit((seat,), model=model, mode="read-only", repo="private-infra")
    assert target.recipient == seat
    assert target.model == model


def test_dispatch_private_refusal_is_typed():
    args = argparse.Namespace(agent="muse", model="muse-wonder-1.0", mode="read-only", task_id="muse-test")
    refusal, target = delegate._admit_dispatch_target(args, agent="muse", trees=(), repo_role="private-infra")
    assert target is None and "PRIVATE_REPOSITORY_SEAT_NOT_ALLOWED" in refusal
