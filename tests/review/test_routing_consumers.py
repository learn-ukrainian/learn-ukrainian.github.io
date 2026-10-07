"""PR 2 consumer migration: references, rotations and file-path error identity."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from scripts.review.family_exclusions import family_exclusion
from scripts.review.model_catalog import (
    CATALOG_PATH,
    ModelCatalogError,
    bounded_execution_policy,
    cursor_pinned_models,
    validate_catalog,
)
from scripts.review.role_resolution import expand_routing_references, resolve_routing_reference


def raw_catalog():
    return yaml.safe_load(CATALOG_PATH.read_text())


@pytest.mark.parametrize(
    "seat,new_id",
    [
        ("openai_frontier", "gpt-99-sol"),
        ("anthropic_authority", "claude-opus-99"),
        ("xai_reviewer", "grok-99"),
        ("bounded_worker", "gpt-99-luna"),
        ("google_bounded", "gemini-99-flash-high"),
        ("anthropic_practical", "claude-sonnet-99"),
        ("local_reviewer", "glm-99"),
        ("cursor_coder", "composer-99"),
        ("volume_reviewer", "poolside/laguna-s-99"),
        ("light_reviewer", "poolside/laguna-xs-99"),
    ],
)
def test_one_holder_edit_moves_all_consumer_references(seat, new_id):
    raw = raw_catalog()
    old_id = raw["seats"][seat]["model_id"]
    replacement = deepcopy(raw["models"][old_id])
    replacement["aliases"] = []
    replacement["runtime_model_ids"] = [new_id]
    replacement["routing_wire_ids"] = {
        transport: new_id + ("-high" if wire.endswith("-high") and transport == "cursor" else "")
        for transport, wire in replacement["routing_wire_ids"].items()
    }
    if "glm_routes" in replacement:
        replacement["glm_routes"]["glmcc_alias"] = new_id
    raw["models"][new_id] = replacement
    raw["seats"][seat]["model_id"] = new_id
    result = validate_catalog(raw)
    baseline = validate_catalog(raw_catalog())

    # No migration caller rebinds a role, ladder, endpoint or default.
    def changed_ids(before, after):
        if isinstance(before, dict):
            for key in before:
                if key == "transport_fallback_for":
                    continue  # Receipt labels remain immutable until PR 4.
                yield from changed_ids(before[key], after[key])
        elif isinstance(before, list):
            for left, right in zip(before, after, strict=True):
                yield from changed_ids(left, right)
        elif isinstance(before, str) and before == old_id:
            yield after

    sections = (
        "execution_routing",
        "orchestrator_seats",
        "formal_cf_defaults",
        "review_candidates",
        "review_scheduler",
    )
    moved = [value for section in sections for value in changed_ids(baseline[section], result[section])]
    assert moved, "holder edit did not reach any consumer"
    assert set(moved) == {new_id}, "a consumer retained the predecessor's holder"
    for route in raw["seats"][seat]["routes"].values():
        label = route.get("legacy_name")
        if label:
            assert result["review_candidates"][label]["model_id"] == new_id
            assert result["review_candidates"][label]["route"] == baseline["review_candidates"][label]["route"]
    if seat == "openai_frontier":
        policy = bounded_execution_policy(result)
        assert policy.advisor_model_id == new_id
        assert result["execution_routing"]["sol_advised_bounded"]["preferred_worker"]["escalate_to"] == new_id
        assert result["formal_cf_defaults"]["codex"]["model_id"] == new_id
        assert result["review_scheduler"]["endpoints"]["codex"]["models"] == [new_id]
        assert result["budget_substitution_models"]["codex"][old_id] == new_id
    if seat == "xai_reviewer":
        assert cursor_pinned_models(result)[0] == new_id
        assert result["review_scheduler"]["endpoints"]["cursor"]["models"] == [new_id]
    if seat == "anthropic_authority":
        assert result["budget_substitution_models"]["cursor"][old_id] == new_id + "-high"
    if seat == "bounded_worker":
        assert bounded_execution_policy(result).bounded_worker_model_id == new_id
    if seat == "google_bounded":
        assert bounded_execution_policy(result).bounded_fallback_model_id == new_id
    assert (
        resolve_routing_reference({"role": "legacy_reviewers", "seat": "xai_reviewer"}, result)
        == result["orchestrator_seats"]["cursor"]["model_id"]
    )


@pytest.mark.parametrize(
    "reference",
    [
        {"role": "missing"},
        {"role": "legacy_reviewers"},
        {"role": "legacy_reviewers", "seat": "missing"},
        {"role": "openai_frontier_coder", "transport": "cursor"},
        {"role": "openai_frontier_coder", "field": "unsupported"},
        {"role": "openai_frontier_coder", "extra": True},
        {"role": "legacy_reviewers", "field": "candidate"},
    ],
)
def test_unresolved_or_ambiguous_references_fail_closed(reference):
    with pytest.raises(ModelCatalogError):
        resolve_routing_reference(reference, raw_catalog())


def test_expansion_preserves_inputs_and_explicit_identity_pins():
    raw = raw_catalog()
    before = deepcopy(raw)
    expanded = expand_routing_references(raw)
    assert raw == before
    assert "gpt-6.1-sol" in expanded["budget_substitution_models"]["codex"]
    assert "openai_frontier_coder" not in expanded["budget_substitution_models"]["codex"]
    assert expanded["models"] == raw["models"]


@pytest.mark.parametrize("bad", ["bad-version", None])
@pytest.mark.parametrize("entrypoint", ["file", "module"])
def test_catalog_file_path_role_validation_is_clean_exit_two(tmp_path, bad, entrypoint):
    root = Path(__file__).resolve().parents[2]
    review = tmp_path / "scripts/review"
    review.mkdir(parents=True)
    for name in ("model_catalog.py", "role_resolution.py", "family_exclusions.py", "__init__.py"):
        shutil.copyfile(root / "scripts/review" / name, review / name)
    config = tmp_path / "scripts/config"
    config.mkdir()
    raw = raw_catalog()
    raw["routing_schema_version"] = bad
    (config / "model_catalog.yaml").write_text(yaml.safe_dump(raw))
    command = [str(review / "model_catalog.py")] if entrypoint == "file" else ["-m", "scripts.review.model_catalog"]
    result = subprocess.run(
        [sys.executable, *command, "--check-retired-model", "gpt-6.1-sol"],
        cwd=tmp_path,
        env={"PATH": os.defpath},
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 2
    assert "routing_schema_version" in result.stderr
    assert "Traceback" not in result.stderr


def test_legacy_allowlist_cannot_expand_from_injected_cursor_candidates():
    from tests.review.test_model_catalog import BASELINE

    catalog = deepcopy(BASELINE["catalog"])
    new_id = "grok-99"
    catalog["models"][new_id] = deepcopy(catalog["models"]["grok-4.7"])
    catalog["models"][new_id]["aliases"] = []
    candidate = deepcopy(catalog["review_candidates"]["grok-4.7-cursor-fallback"])
    candidate["model_id"] = new_id
    candidate.pop("transport_fallback_for")
    candidate["invocation"] = candidate["invocation"].replace("grok-4.7", new_id)
    catalog["review_candidates"][new_id] = candidate
    catalog["orchestrator_seats"]["cursor"]["auto_allowlist"].append(new_id)
    with pytest.raises(ModelCatalogError, match="auto_allowlist must equal exactly"):
        validate_catalog(catalog)


def test_verdict_recorder_follows_rotated_holder_and_own_runtime_ids(monkeypatch):
    from scripts.review import model_catalog, record_cf_verdict

    raw = raw_catalog()
    new_id = "grok-99"
    replacement = deepcopy(raw["models"]["grok-4.7"])
    replacement["aliases"] = []
    replacement["runtime_model_ids"] = [new_id + "-build"]
    replacement["routing_wire_ids"] = {
        transport: new_id + ("-high" if transport == "cursor" else "")
        for transport in replacement["routing_wire_ids"]
    }
    raw["models"][new_id] = replacement
    raw["seats"]["xai_reviewer"]["model_id"] = new_id
    catalog = validate_catalog(raw)
    monkeypatch.setattr(record_cf_verdict, "load_model_catalog", lambda: catalog)
    monkeypatch.setattr(model_catalog, "load_model_catalog", lambda: catalog)
    assert record_cf_verdict._native_grok_reviewer_identity() == (new_id, [new_id + "-build"])
    record_cf_verdict._require_formal_reviewer(
        cursor=False, reported=new_id + "-build", model=new_id, family="xai", native_grok=True
    )
    with pytest.raises(record_cf_verdict.RecordError, match="not a formal reviewer"):
        record_cf_verdict._require_formal_reviewer(
            cursor=False, reported="grok-4.7-build", model="grok-4.7", family="xai", native_grok=True
        )


@pytest.mark.parametrize(
    "family,route,excluded",
    [
        ("google", "codex", True),
        ("moonshot", "cursor", True),
        ("deepseek", "codex", True),
        ("openai", "agy", True),
        ("openai", "codex", False),
        ("anthropic", "claude", False),
    ],
)
def test_shared_role_family_exclusion(family, route, excluded):
    assert bool(family_exclusion(family=family, route=route, transport=route)) is excluded


def test_shared_author_independence_and_advisory_outcomes():
    params = {"route": "codex", "transport": "native_codex", "family": "openai"}
    assert family_exclusion(**params, author_family="anthropic") is None
    assert family_exclusion(**params, author_family="openai")[0] == "excluded"
    assert (
        family_exclusion(**params, author_family="openai", advisory_only_for_author_families=frozenset({"openai"}))[0]
        == "advisory_only"
    )


def test_cursor_bridge_and_substitution_defaults_use_role_api(monkeypatch):
    from scripts import delegate
    from scripts.ai_agent_bridge import _cursor
    from scripts.review import model_catalog

    monkeypatch.setattr(model_catalog, "routing_model", lambda *args, **kwargs: "role-holder")
    assert _cursor.cursor_default_model() == "role-holder"
    assert delegate._lane_default_model("codex") == "role-holder"
    assert delegate._lane_default_model("cursor") == "role-holder"


def test_routing_model_uses_resolved_snapshot_and_rejects_unresolved_values(monkeypatch):
    from scripts.review import model_catalog

    source = validate_catalog(raw_catalog())
    monkeypatch.setattr(model_catalog, "load_model_catalog", lambda: source)
    assert (
        model_catalog.routing_model("orchestrator_seats", "cursor")
        == source["orchestrator_seats"]["cursor"]["model_id"]
    )
    source["orchestrator_seats"]["cursor"]["model_id"] = "composer-2.5"
    assert model_catalog.routing_model("orchestrator_seats", "cursor") == "composer-2.5"
    source["orchestrator_seats"]["cursor"]["model_id"] = {"role": "missing"}
    with pytest.raises(ModelCatalogError, match="not a resolved model"):
        model_catalog.routing_model("orchestrator_seats", "cursor")


def test_legacy_adapter_expands_raw_authored_references():
    from scripts.review.role_resolution import expanded_legacy_view
    from tests.review.test_model_catalog import BASELINE

    assert expanded_legacy_view(raw_catalog()) == BASELINE["catalog"]
