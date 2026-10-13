"""Frozen routing evidence with scoped, hash-pinned approved overlays."""

from __future__ import annotations

import gzip
import hashlib
import json
import pickle
import re
import runpy
import shutil
import subprocess
import sys
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass
from functools import lru_cache, partial
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from scripts.fleet import credit_lane
from scripts.review.model_catalog import load_model_catalog
from scripts.review.reviewer_resolver import ResolverInputs, resolve_reviewer
from scripts.review.role_resolution import expanded_legacy_view

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures/routing_baseline"
BASELINE = json.loads(gzip.decompress((FIXTURE / "baseline.json.gz").read_bytes()))
INPUTS = json.loads((FIXTURE / "inputs.json").read_bytes())
CAPTURE = runpy.run_path(str(FIXTURE / "capture.py"))

# Keep the frozen capture script byte-pinned. Apply the cache only inside its
# fresh subprocess, leaving production catalog validation unchanged.
CAPTURE_RUNNER = """
import runpy
import sys
source = sys.argv[sys.argv.index("--source-root") + 1]
sys.path[:0] = [source, source + "/scripts", source + "/packages/v4-runtime/src"]
from tests.agent_runtime.agy_hook_helpers import register_agy_hooks
cached_capture_reads = runpy.run_path(source + "/tests/review/test_model_catalog.py")["cached_capture_reads"]
sys.argv = sys.argv[1:]
capture = runpy.run_path(sys.argv[0])
original = capture["capture"]
def cached_capture(*args, **kwargs):
    # Enter only after main has installed its hermetic environment.
    if args:
        register_agy_hooks(args[1], home=args[1] / "home")
    with cached_capture_reads():
        return original(*args, **kwargs)
capture["main"].__globals__["capture"] = cached_capture
capture["main"]()
"""


@contextmanager
def cached_capture_reads():
    """Reuse validated catalog inputs and parser construction in one capture.

    Key validation by exact content, and return independent copies so mutations
    cannot reuse stale proof or change cached results. Production is untouched.
    """
    from scripts import delegate
    from scripts.review import model_catalog

    validate = model_catalog.validate_catalog
    cache = {}

    def cached(data):
        key = pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)
        if key not in cache:
            cache[key] = deepcopy(validate(data))
        return deepcopy(cache[key])

    with (
        patch.object(model_catalog, "validate_catalog", cached),
        patch.object(delegate, "build_parser", lru_cache(maxsize=1)(delegate.build_parser)),
    ):
        yield


CAPACITY_FIXTURE = Path(__file__).parent / "fixtures"


def approved_review_baseline(baseline):
    """Apply #10016 reviewer and #10083 advisor/launcher-help revisions.

    Launcher wording comes from the existing #10083 commit e1c5699496.
    Keep the historical capture, inputs and source census byte-pinned.
    """
    overlay = json.loads(gzip.decompress((CAPACITY_FIXTURE / "routing-10016.json.gz").read_bytes()))
    assert set(overlay) == {"reviewer"}
    advisor = json.loads((CAPACITY_FIXTURE / "claude-advisor-10083.json").read_bytes())
    adapters = deepcopy(baseline["adapters"])
    for index in advisor["adapter_rows"]:
        env = adapters[index]["value"]["env_overrides"]
        assert env == {"CLAUDE_CODE_DISABLE_BACKGROUND_TASKS": "1"}
        env.update(advisor["env_overrides"])
    launchers = deepcopy(baseline["launchers"])
    for index in advisor["launcher_rows"]:
        for replacement in advisor["launcher_help_replacements"]:
            before, after = replacement["before"], replacement["after"]
            assert launchers[index]["stdout"].count(before) == 1
            launchers[index]["stdout"] = launchers[index]["stdout"].replace(before, after)
    return {**baseline, **overlay, "adapters": adapters, "launchers": launchers}


REVIEW_CAPACITY_BASELINE = approved_review_baseline(BASELINE)
GEMINI_OVERLAY_PATH = CAPACITY_FIXTURE / "routing-10073.json.gz"
GEMINI_OVERLAY = json.loads(gzip.decompress(GEMINI_OVERLAY_PATH.read_bytes()))


def approved_cursor_trailer_baseline(baseline):
    """#10273 AC-04 changes only the two frozen Cursor refusal trailers."""
    launchers = deepcopy(baseline["launchers"])
    for index, seat in ((41, "interactive session"), (46, "driver")):
        old = f"not certified for the cursor {seat}; pin grok-4.7-high or composer-2.5.\n"
        new = old.removesuffix(".\n") + "; never Auto, Fast or a previous generation.\n"
        assert launchers[index]["stderr"].endswith(old)
        launchers[index]["stderr"] = launchers[index]["stderr"].removesuffix(old) + new
    return {**baseline, "launchers": launchers}


def test_cursor_trailer_revision_preserves_all_other_frozen_receipts():
    revised = approved_cursor_trailer_baseline(BASELINE)
    assert {key: value for key, value in revised.items() if key != "launchers"} == {
        key: value for key, value in BASELINE.items() if key != "launchers"
    }
    changed = [
        index
        for index, (old, new) in enumerate(zip(BASELINE["launchers"], revised["launchers"], strict=True))
        if old != new
    ]
    assert changed == [41, 46]
    for index in changed:
        old, new = BASELINE["launchers"][index], revised["launchers"][index]
        assert {key: value for key, value in old.items() if key != "stderr"} == {
            key: value for key, value in new.items() if key != "stderr"
        }
        assert new["stderr"] == old["stderr"].removesuffix(".\n") + "; never Auto, Fast or a previous generation.\n"


RESOURCE_OVERLAY_PATH = FIXTURE / "routing-10263.json.gz"
RESOURCE_OVERLAY = json.loads(gzip.decompress(RESOURCE_OVERLAY_PATH.read_bytes()))


def approved_launcher_canary_baseline(baseline):
    """Apply #10266's paragraph after surface overlays, preserving other help edits."""
    canary = json.loads((CAPACITY_FIXTURE / "launcher-canary-10266.json").read_bytes())
    launchers = deepcopy(baseline["launchers"])
    for index in canary["launcher_rows"]:
        for replacement in canary["launcher_help_replacements"]:
            before, after = replacement["before"], replacement["after"]
            assert launchers[index]["stdout"].count(before) == 1
            launchers[index]["stdout"] = launchers[index]["stdout"].replace(before, after)
    return {**baseline, "launchers": launchers}


def approved_claude_cap_baseline(baseline):
    """Apply #10355's Claude weekly-cap help lines (99% stop, Opus always blocked)."""
    cap = json.loads((CAPACITY_FIXTURE / "claude-cap-10355.json").read_bytes())
    launchers = deepcopy(baseline["launchers"])
    for replacement in cap["launcher_help_replacements"]:
        before, after = replacement["before"], replacement["after"]
        for index in replacement["rows"]:
            assert launchers[index]["stdout"].count(before) == 1
            launchers[index]["stdout"] = launchers[index]["stdout"].replace(before, after)
    return {**baseline, "launchers": launchers}


def approved_cto_wrappers_baseline(baseline):
    """Apply #10453's CTO-wrapper help lines on top of #10355's cap wording."""
    cto = json.loads((CAPACITY_FIXTURE / "cto-wrappers-10453.json").read_bytes())
    launchers = deepcopy(baseline["launchers"])
    for replacement in cto["launcher_help_replacements"]:
        before, after = replacement["before"], replacement["after"]
        for index in replacement["rows"]:
            assert launchers[index]["stdout"].count(before) == 1
            launchers[index]["stdout"] = launchers[index]["stdout"].replace(before, after)
    return {**baseline, "launchers": launchers}


SEATS_OVERLAY_PATH = CAPACITY_FIXTURE / "routing-10464.json.gz"
SEATS_OVERLAY = json.loads(gzip.decompress(SEATS_OVERLAY_PATH.read_bytes()))
GEMINI_INPUTS = {**INPUTS, **GEMINI_OVERLAY["inputs"]}


def dispatch_key(row):
    return json.dumps(row, sort_keys=True)


def approved_reviewer_seats_baseline(baseline):
    """Apply #10464 (D-129): no Claude model reviews through Cursor.

    The overlay replaces the catalog, role, routing-holder and reviewer surfaces.
    The dispatch matrix is built from budget substitution pins, so deleting the
    Cursor claude-opus-5-5 row only drops that pin's rows; kept rows stay as captured.
    """
    kept = {dispatch_key(row) for row in SEATS_OVERLAY["inputs"]["dispatch"]}
    dispatch = [
        receipt
        for row, receipt in zip(INPUTS["dispatch"], baseline["dispatch"], strict=True)
        if dispatch_key(row) in kept
    ]
    return {**baseline, **SEATS_OVERLAY["surfaces"], "dispatch": dispatch}


# Apply literal paragraph edits last: a surface overlay such as #10291's Grok
# help revision must neither erase this wording nor have its other lines erased.
APPROVED_BASELINE = approved_cto_wrappers_baseline(
    approved_claude_cap_baseline(
        approved_cursor_trailer_baseline(
            approved_launcher_canary_baseline(
                approved_reviewer_seats_baseline(
                    {
                        **REVIEW_CAPACITY_BASELINE,
                        **GEMINI_OVERLAY["surfaces"],
                        **RESOURCE_OVERLAY["surfaces"],
                    }
                )
            )
        )
    )
)
APPROVED_INPUTS = {**GEMINI_INPUTS, **SEATS_OVERLAY["inputs"]}


MUSE_CANDIDATE_ENTRY = {
    "family": "meta",
    "tier": "specialist",
    "lifecycle": "hold",
    "roles": ["candidate_author", "candidate_reviewer"],
    "transports": ["muse"],
    "context_window": 1000000,
    "strengths": ["public_code_candidate"],
    "weaknesses": ["unqualified_no_automatic_routing", "no_security", "no_ukrainian", "no_private_repository"],
    "sources": ["https://dev.meta.ai/models/muse-wonder"],
}


def approved_muse_candidate_catalog(catalog):
    """#10511 adds only the held Muse model to the approved catalog."""
    revised = deepcopy(catalog)
    assert "muse-wonder-1.0" not in revised["models"]
    revised["models"]["muse-wonder-1.0"] = deepcopy(MUSE_CANDIDATE_ENTRY)
    return revised


def test_muse_candidate_overlay_preserves_every_other_catalog_field():
    before = deepcopy(APPROVED_BASELINE["catalog"])
    revised = approved_muse_candidate_catalog(APPROVED_BASELINE["catalog"])
    assert revised["models"].pop("muse-wonder-1.0") == MUSE_CANDIDATE_ENTRY
    assert revised == before
    assert APPROVED_BASELINE["catalog"] == before


# #10511: exact additive cases, with their final input positions and frozen
# receipt references. No seat, ladder or authority is added.
MUSE_REVIEWER_INPUT_ADDITIONS = [
    (94, {"author_model": "muse-wonder-1.0", "risk": "low", "review_profile": "code"}, 0),
    (110, {"author_model": "gpt-6.1-sol", "risk": "low", "review_profile": "code", "author_family": "meta"}, 19),
    (111, {"author_model": "gpt-6.1-sol", "risk": "low", "review_profile": "code", "subject_families": ["meta"]}, 0),
    (282, {"author_model": "muse-wonder-1.0", "risk": "low", "review_profile": "infra"}, 185),
    (298, {"author_model": "gpt-6.1-sol", "risk": "low", "review_profile": "infra", "author_family": "meta"}, 204),
    (299, {"author_model": "gpt-6.1-sol", "risk": "low", "review_profile": "infra", "subject_families": ["meta"]}, 185),
    (470, {"author_model": "muse-wonder-1.0", "risk": "medium", "review_profile": "code"}, 370),
    (486, {"author_model": "gpt-6.1-sol", "risk": "medium", "review_profile": "code", "author_family": "meta"}, 389),
    (
        487,
        {"author_model": "gpt-6.1-sol", "risk": "medium", "review_profile": "code", "subject_families": ["meta"]},
        370,
    ),
    (658, {"author_model": "muse-wonder-1.0", "risk": "medium", "review_profile": "infra"}, 555),
    (674, {"author_model": "gpt-6.1-sol", "risk": "medium", "review_profile": "infra", "author_family": "meta"}, 574),
    (
        675,
        {"author_model": "gpt-6.1-sol", "risk": "medium", "review_profile": "infra", "subject_families": ["meta"]},
        555,
    ),
    (846, {"author_model": "muse-wonder-1.0", "risk": "high", "review_profile": "code"}, 740),
    (862, {"author_model": "gpt-6.1-sol", "risk": "high", "review_profile": "code", "author_family": "meta"}, 759),
    (863, {"author_model": "gpt-6.1-sol", "risk": "high", "review_profile": "code", "subject_families": ["meta"]}, 740),
    (1034, {"author_model": "muse-wonder-1.0", "risk": "high", "review_profile": "infra"}, 925),
    (1050, {"author_model": "gpt-6.1-sol", "risk": "high", "review_profile": "infra", "author_family": "meta"}, 944),
    (
        1051,
        {"author_model": "gpt-6.1-sol", "risk": "high", "review_profile": "infra", "subject_families": ["meta"]},
        925,
    ),
    (1222, {"author_model": "muse-wonder-1.0", "risk": "critical", "review_profile": "code"}, 1110),
    (
        1238,
        {"author_model": "gpt-6.1-sol", "risk": "critical", "review_profile": "code", "author_family": "meta"},
        1129,
    ),
    (
        1239,
        {"author_model": "gpt-6.1-sol", "risk": "critical", "review_profile": "code", "subject_families": ["meta"]},
        1110,
    ),
    (1410, {"author_model": "muse-wonder-1.0", "risk": "critical", "review_profile": "infra"}, 1295),
    (
        1426,
        {"author_model": "gpt-6.1-sol", "risk": "critical", "review_profile": "infra", "author_family": "meta"},
        1314,
    ),
    (
        1427,
        {"author_model": "gpt-6.1-sol", "risk": "critical", "review_profile": "infra", "subject_families": ["meta"]},
        1295,
    ),
]

MUSE_APPROVAL_ROW_ADDITIONS = [
    {
        "author": "muse-wonder-1.0",
        "required": ["claude-opus-5-5", "gpt-6.1-sol"],
        "votes": {"claude-opus-5-5": "absent", "gpt-6.1-sol": "absent"},
        "self_approval_counts": False,
        "outcome": "missing_approval",
    },
    {
        "author": "muse-wonder-1.0",
        "required": ["claude-opus-5-5", "gpt-6.1-sol"],
        "votes": {"claude-opus-5-5": "absent", "gpt-6.1-sol": "approve"},
        "self_approval_counts": False,
        "outcome": "missing_approval",
    },
    {
        "author": "muse-wonder-1.0",
        "required": ["claude-opus-5-5", "gpt-6.1-sol"],
        "votes": {"claude-opus-5-5": "absent", "gpt-6.1-sol": "dissent"},
        "self_approval_counts": False,
        "outcome": "operator_disposition",
    },
    {
        "author": "muse-wonder-1.0",
        "required": ["claude-opus-5-5", "gpt-6.1-sol"],
        "votes": {"claude-opus-5-5": "approve", "gpt-6.1-sol": "absent"},
        "self_approval_counts": False,
        "outcome": "missing_approval",
    },
    {
        "author": "muse-wonder-1.0",
        "required": ["claude-opus-5-5", "gpt-6.1-sol"],
        "votes": {"claude-opus-5-5": "approve", "gpt-6.1-sol": "approve"},
        "self_approval_counts": False,
        "outcome": "approved",
    },
    {
        "author": "muse-wonder-1.0",
        "required": ["claude-opus-5-5", "gpt-6.1-sol"],
        "votes": {"claude-opus-5-5": "approve", "gpt-6.1-sol": "dissent"},
        "self_approval_counts": False,
        "outcome": "operator_disposition",
    },
    {
        "author": "muse-wonder-1.0",
        "required": ["claude-opus-5-5", "gpt-6.1-sol"],
        "votes": {"claude-opus-5-5": "dissent", "gpt-6.1-sol": "absent"},
        "self_approval_counts": False,
        "outcome": "operator_disposition",
    },
    {
        "author": "muse-wonder-1.0",
        "required": ["claude-opus-5-5", "gpt-6.1-sol"],
        "votes": {"claude-opus-5-5": "dissent", "gpt-6.1-sol": "approve"},
        "self_approval_counts": False,
        "outcome": "operator_disposition",
    },
    {
        "author": "muse-wonder-1.0",
        "required": ["claude-opus-5-5", "gpt-6.1-sol"],
        "votes": {"claude-opus-5-5": "dissent", "gpt-6.1-sol": "dissent"},
        "self_approval_counts": False,
        "outcome": "operator_disposition",
    },
]

MUSE_REGISTRY_ENTRY = {
    "adapter": "scripts.agent_runtime.adapters.muse:MuseAdapter",
    "default_model": None,
    "cost_tier": "unknown",
    "capabilities": [],
    "cli_available": True,
    "resume_policy": "never",
}

MUSE_ADAPTER_INPUT_ADDITIONS = [
    {"agent": "muse", "mode": "read-only", "isolation": False},
    {"agent": "muse", "mode": "read-only", "isolation": True},
    {"agent": "muse", "mode": "workspace-write", "isolation": False},
    {"agent": "muse", "mode": "workspace-write", "isolation": True},
]

MUSE_AUTHOR_REFUSAL = "author identity unknown — cannot resolve a model family from author_model='muse-wonder-1.0'"
MUSE_SUBJECT_REFUSAL = (
    "unknown subject family 'meta'; expected one of anthropic, cursor, deepseek, "
    "google, moonshot, openai, poolside, qwen, xai, zhipu"
)


def approved_muse_candidate_inputs(inputs):
    """#10511 adds exactly 24 reviewer cases and four held adapter probes."""
    revised = deepcopy(inputs)
    for index, case, _ in MUSE_REVIEWER_INPUT_ADDITIONS:
        revised["reviewer"].insert(index, deepcopy(case))
    revised["adapters"] = revised["adapters"] + deepcopy(MUSE_ADAPTER_INPUT_ADDITIONS)
    return revised


def approved_muse_candidate_approval(approval):
    """#10511 adds nine author-side vote rows, preserving the 387 originals."""
    revised = deepcopy(approval)
    revised["rows"][351:351] = deepcopy(MUSE_APPROVAL_ROW_ADDITIONS)
    return revised


def muse_reviewer_receipt(baseline, case, reference):
    """Reuse a frozen equivalent receipt or apply one exact refusal string."""
    receipt = deepcopy(baseline["reviewer"][reference])
    if case["author_model"] == "muse-wonder-1.0":
        receipt["value"]["fail_closed_reason"] = MUSE_AUTHOR_REFUSAL
    elif "subject_families" in case:
        receipt["value"]["fail_closed_reason"] = MUSE_SUBJECT_REFUSAL
    return receipt


def approved_muse_candidate_baseline(baseline):
    """#10511 adds only the literal held candidate and its exact capture rows."""
    revised = deepcopy(baseline)
    revised["catalog"] = approved_muse_candidate_catalog(baseline["catalog"])
    revised["registry"]["muse"] = deepcopy(MUSE_REGISTRY_ENTRY)
    revised["approval"] = approved_muse_candidate_approval(baseline["approval"])
    for index, case, reference in MUSE_REVIEWER_INPUT_ADDITIONS:
        revised["reviewer"].insert(index, muse_reviewer_receipt(baseline, case, reference))
    adapter_rows = []
    for case in MUSE_ADAPTER_INPUT_ADDITIONS:
        adapter_rows.append(
            {
                "error": "MUSE_GUARD_PARITY_UNPROVEN: "
                + case["mode"]
                + " has no native forbidden-action proof; shell, credential, publish, "
                "destructive-command and filesystem guards remain unproven",
                "exception": "MuseGuardParityRefused",
                "exit_status": 1,
                "stderr": "",
                "stdout": "",
            }
        )
    revised["adapters"] = revised["adapters"] + adapter_rows
    return revised


def test_muse_candidate_capture_overlay_is_exact():
    assert_frozen_surfaces(approved_muse_candidate_baseline(APPROVED_BASELINE))


def test_muse_candidate_input_overlay_preserves_all_original_cases():
    before = deepcopy(APPROVED_INPUTS)
    revised = approved_muse_candidate_inputs(APPROVED_INPUTS)
    assert len(MUSE_REVIEWER_INPUT_ADDITIONS) == 24
    assert len(revised["reviewer"]) == 1504
    for index, case, _ in reversed(MUSE_REVIEWER_INPUT_ADDITIONS):
        assert revised["reviewer"].pop(index) == case
    assert revised["adapters"][-4:] == MUSE_ADAPTER_INPUT_ADDITIONS
    del revised["adapters"][-4:]
    assert revised == before == APPROVED_INPUTS


def test_muse_candidate_approval_overlay_preserves_authority_and_original_rows():
    before = deepcopy(BASELINE["approval"])
    actual = CAPTURE["approval_contract_rows"](Path(__file__).resolve().parents[2], load_model_catalog())
    assert actual == approved_muse_candidate_approval(before)
    assert len(actual["rows"]) == 396
    assert len(before["rows"]) == 387
    assert [row for row in actual["rows"] if row["author"] != "muse-wonder-1.0"] == before["rows"]
    added = [row for row in actual["rows"] if row["author"] == "muse-wonder-1.0"]
    assert added == MUSE_APPROVAL_ROW_ADDITIONS
    assert len(added) == 9
    assert actual["holders"] == ["claude-opus-5-5", "gpt-6.1-sol"]
    for row in added:
        assert set(row) == {"author", "required", "votes", "self_approval_counts", "outcome"}
        assert row["required"] == actual["holders"]
        assert set(row["votes"]) == set(actual["holders"])
        assert row["self_approval_counts"] is False
    assert BASELINE["approval"] == before


def test_muse_candidate_capture_overlay_preserves_all_frozen_receipts():
    before = deepcopy(APPROVED_BASELINE)
    revised = approved_muse_candidate_baseline(before)
    for index, case, reference in reversed(MUSE_REVIEWER_INPUT_ADDITIONS):
        assert revised["reviewer"].pop(index) == muse_reviewer_receipt(before, case, reference)
    assert len(revised["reviewer"]) == 1480
    assert CAPTURE["encode"](revised["reviewer"]) == CAPTURE["encode"](before["reviewer"])
    assert revised["registry"].pop("muse") == MUSE_REGISTRY_ENTRY
    assert len(revised["adapters"][-4:]) == 4
    del revised["adapters"][-4:]
    assert revised["catalog"]["models"].pop("muse-wonder-1.0") == MUSE_CANDIDATE_ENTRY
    del revised["approval"]["rows"][351:360]
    assert revised == before == APPROVED_BASELINE


@pytest.mark.parametrize("index,case,reference", MUSE_REVIEWER_INPUT_ADDITIONS)
def test_muse_added_reviewer_case_never_selects_muse(index, case, reference, tmp_path, monkeypatch):
    typed = deepcopy(case)
    if "subject_families" in typed:
        typed["subject_families"] = frozenset(typed["subject_families"])
    monkeypatch.setattr(
        credit_lane,
        "routing_facts",
        partial(credit_lane.routing_facts, now=CAPTURE["FIXED_NOW"], usage_dir=tmp_path / "usage"),
    )
    monkeypatch.setattr(
        credit_lane, "published_credit_relief", partial(credit_lane.published_credit_relief, now=CAPTURE["FIXED_NOW"])
    )
    result = resolve_reviewer(ResolverInputs(**typed))
    if result.selected is not None:
        assert result.selected.route != "muse"
        assert result.selected.concrete_model != "muse-wonder-1.0"
    for candidate in (*result.trace, *result.advisory, *result.quorum):
        assert candidate.route != "muse"
        assert candidate.concrete_model != "muse-wonder-1.0"
    actual = CAPTURE["observed"](lambda: result)
    assert json.loads(CAPTURE["encode"](actual)) == muse_reviewer_receipt(APPROVED_BASELINE, case, reference)


@pytest.mark.parametrize("configuration", ("host-cli", "no-cli"))
def test_claude_cap_fixture_adds_only_cap_help_lines(configuration):
    fixture_path = CAPACITY_FIXTURE / "claude-cap-10355.json"
    assert hashlib.sha256(fixture_path.read_bytes()).hexdigest() == (
        "54de3ec4e4166708c3cb2a54ef62256fdf283bc85cd160661db3abe82ddc249f"
    )
    cap = json.loads(fixture_path.read_bytes())
    assert set(cap) == {"launcher_help_replacements"}
    assert [row["rows"] for row in cap["launcher_help_replacements"]] == [[4, 9], list(range(4, 70, 5))]
    for row in cap["launcher_help_replacements"]:
        assert row["after"].startswith(row["before"].splitlines(True)[0])
        assert row["after"].endswith(row["before"].splitlines(True)[1])
    text = "".join(row["after"] for row in cap["launcher_help_replacements"])
    assert "stops at 99% weekly used" in text
    assert "Opus is always blocked" in text
    for retired in ("LU_CLAUDE_STOP_PCT", "LU_CLAUDE_OPUS_MAX_PCT", "default 90", "default 80"):
        assert retired not in text
    path = FIXTURE / ("baseline.json.gz" if configuration == "host-cli" else "no-cli/baseline.json.gz")
    before = approved_cursor_trailer_baseline(
        approved_launcher_canary_baseline(
            {
                **approved_review_baseline(json.loads(gzip.decompress(path.read_bytes()))),
                **GEMINI_OVERLAY["surfaces"],
                **RESOURCE_OVERLAY["surfaces"],
            }
        )
    )
    after = approved_claude_cap_baseline(before)
    assert {k: v for k, v in after.items() if k != "launchers"} == {k: v for k, v in before.items() if k != "launchers"}
    changed = [
        i for i, (old, new) in enumerate(zip(before["launchers"], after["launchers"], strict=True)) if old != new
    ]
    assert changed == list(range(4, 70, 5))
    for index in changed:
        assert {k: v for k, v in before["launchers"][index].items() if k != "stdout"} == {
            k: v for k, v in after["launchers"][index].items() if k != "stdout"
        }


@pytest.mark.parametrize("configuration", ("host-cli", "no-cli"))
def test_cto_wrappers_fixture_changes_only_cto_help_lines(configuration):
    fixture_path = CAPACITY_FIXTURE / "cto-wrappers-10453.json"
    assert hashlib.sha256(fixture_path.read_bytes()).hexdigest() == (
        "b13c3c443bddb9fb81fff9e5546e95fb1f10ef067a22646f397a2faad38d9daf"
    )
    cto = json.loads(fixture_path.read_bytes())
    assert set(cto) == {"launcher_help_replacements"}
    replacements = cto["launcher_help_replacements"]
    assert [set(row) for row in replacements] == [{"rows", "before", "after"}] * 3
    assert [row["rows"] for row in replacements] == [list(range(4, 70, 5)), [4, 9], list(range(9, 70, 10))]
    force, cap, lanes = replacements
    assert force["after"].splitlines(True) == [
        force["before"].splitlines(True)[0],
        " " * 29 + "CTO wrappers reject it with exit 2.\n",
        force["before"].splitlines(True)[1],
    ]
    assert lanes["after"] == lanes["before"].replace("Valid lane selectors:\n", "Valid lane selectors:\n  epics\n")
    assert cap["after"].startswith(cap["before"].splitlines(True)[0])
    assert "Opus is always blocked outside start-claude-cto.sh on epics:" in cap["after"]
    assert "Opus stays blocked" in cap["before"] and "Opus stays blocked" not in cap["after"]
    path = FIXTURE / ("baseline.json.gz" if configuration == "host-cli" else "no-cli/baseline.json.gz")
    before = approved_claude_cap_baseline(
        approved_cursor_trailer_baseline(
            approved_launcher_canary_baseline(
                {
                    **approved_review_baseline(json.loads(gzip.decompress(path.read_bytes()))),
                    **GEMINI_OVERLAY["surfaces"],
                    **RESOURCE_OVERLAY["surfaces"],
                }
            )
        )
    )
    after = approved_cto_wrappers_baseline(before)
    assert {k: v for k, v in after.items() if k != "launchers"} == {k: v for k, v in before.items() if k != "launchers"}
    changed = [
        i for i, (old, new) in enumerate(zip(before["launchers"], after["launchers"], strict=True)) if old != new
    ]
    assert changed == list(range(4, 70, 5))
    for index in changed:
        assert INPUTS["launchers"][index]["variant"] == "help"
        assert {k: v for k, v in before["launchers"][index].items() if k != "stdout"} == {
            k: v for k, v in after["launchers"][index].items() if k != "stdout"
        }


@pytest.mark.parametrize("configuration", ["", "no-cli"])
def test_launcher_canary_fixture_changes_only_driver_help_paragraph(configuration):
    fixture_path = CAPACITY_FIXTURE / "launcher-canary-10266.json"
    assert hashlib.sha256(fixture_path.read_bytes()).hexdigest() == (
        "9dca36ee148f7d1e178c2ef2084da9be612e887b0c3c39365a9e35eefed8fef4"
    )
    canary = json.loads(fixture_path.read_bytes())
    assert set(canary) == {"launcher_rows", "launcher_help_replacements"}
    assert len(canary["launcher_help_replacements"]) == 1
    baseline = json.loads(gzip.decompress((FIXTURE / configuration / "baseline.json.gz").read_bytes()))
    original = deepcopy(baseline)
    updated = approved_launcher_canary_baseline(baseline)
    changed = []
    assert len(baseline["launchers"]) == len(updated["launchers"]) == 70
    for index, (before, after) in enumerate(zip(baseline["launchers"], updated["launchers"], strict=True)):
        if before == after:
            continue
        changed.append(index)
        assert INPUTS["launchers"][index]["variant"] == "help"
        restored = deepcopy(after)
        for replacement in canary["launcher_help_replacements"]:
            assert restored["stdout"].count(replacement["after"]) == 1
            restored["stdout"] = restored["stdout"].replace(replacement["after"], replacement["before"])
        assert restored == before
    assert changed == canary["launcher_rows"] == [4, 9, 14, 19, 24, 29, 34, 39, 44, 49]
    for surface in baseline.keys() - {"launchers"}:
        assert updated[surface] == baseline[surface]
    assert baseline == original


def test_launcher_canary_paragraph_preserves_independent_grok_help_edits():
    def grok_help_edits(baseline):
        updated = deepcopy(baseline)
        row = updated["launchers"][39]
        # #10291 changes the usage and adds a native-driver block, outside the
        # driver paragraph. Exercise edits on both sides of that paragraph.
        row["stdout"] = (
            row["stdout"]
            .replace(
                "Usage: ./start-grok-driver.sh [OPTIONS] [PROMPT ...] [-- PROVIDER_ARGS ...]",
                "Usage: ./start-grok-driver.sh [OPTIONS] [-- PROVIDER_ARGS ...]",
            )
            .replace(
                "Hermes (opt-in only):\n",
                "Native Grok driver:\n"
                "  Runs from the inspected checkout; positional prompts and subcommands are refused.\n\n"
                "Hermes (opt-in only):\n",
            )
        )
        assert row != baseline["launchers"][39]
        return updated

    baseline = deepcopy(REVIEW_CAPACITY_BASELINE)
    assert approved_launcher_canary_baseline(grok_help_edits(baseline)) == grok_help_edits(
        approved_launcher_canary_baseline(baseline),
    )


def test_resource_policy_fixture_changes_only_approved_fallback_rows():
    assert set(RESOURCE_OVERLAY) == {"surfaces"}
    assert set(RESOURCE_OVERLAY["surfaces"]) == {"fallbacks"}
    after = RESOURCE_OVERLAY["surfaces"]["fallbacks"]
    for path in (FIXTURE / "baseline.json.gz", FIXTURE / "no-cli/baseline.json.gz"):
        before = json.loads(gzip.decompress(path.read_bytes()))["fallbacks"]
        expected = deepcopy(before)
        expected.pop("post_2026_06_15_hard_rule")
        removed = [
            row
            for row in expected["substitutions"]
            if row["currently_uses"] == "linear_pipeline.invoke_writer(writer='claude-tools')"
        ]
        assert len(removed) == 1
        expected["substitutions"].remove(removed[0])
        expected["worker_resource_policy"] = (
            "Sol is the default eligible code worker. Use native Claude CLI workers as\n"
            "heavily as their subscription allows, respecting task fit and hard gates.\n"
            "Cursor Grok or Gemini routes are language-free overflow only; resolve admitted\n"
            "models and transports from the live catalog, never infer route availability.\n"
            "Writer selection follows core rules and the canonical writer policy, with no\n"
            "excluded-writer recommendation in this substitution table.\n"
        )
        assert after == expected


def test_resource_policy_fallbacks_equal_approved_overlay():
    source = Path(__file__).resolve().parents[2]
    actual = yaml.safe_load((source / "scripts/config/agent_fallback_substitutions.yaml").read_text())
    assert actual == RESOURCE_OVERLAY["surfaces"]["fallbacks"]


def test_gemini_fixture_preserves_historical_cases_and_other_seat_eligibility():
    assert hashlib.sha256(GEMINI_OVERLAY_PATH.read_bytes()).hexdigest() == (
        "94cf67d477b22eac788c43a0306218e6017550edc2a6ac35c504da0b52185d25"
    )
    assert set(GEMINI_OVERLAY["surfaces"]) == {"catalog", "roles", "routing_holders", "reviewer"}
    assert set(GEMINI_OVERLAY["inputs"]) == {"roles", "reviewer"}

    def key(value):
        return json.dumps(value, sort_keys=True)

    for surface in ("roles", "reviewer"):
        new_inputs = {key(row) for row in GEMINI_INPUTS[surface]}
        assert all(key(row) in new_inputs for row in INPUTS[surface])
    gemini_receipts = GEMINI_OVERLAY["surfaces"]["reviewer"]
    receipts = dict(zip(map(key, GEMINI_INPUTS["reviewer"]), gemini_receipts, strict=True))
    for inputs, before in zip(INPUTS["reviewer"], REVIEW_CAPACITY_BASELINE["reviewer"], strict=True):
        after = receipts[key(inputs)]
        if before == after:
            continue
        old, new = deepcopy(before), deepcopy(after)
        assert isinstance(old["value"], dict) and isinstance(new["value"], dict)
        chosen = new["value"]["selected"]
        if chosen != old["value"]["selected"]:
            assert inputs["risk"] in {"low", "medium"}
            assert inputs["review_profile"] == "code"
            assert chosen["name"] == "gemini-3.8-flash-high"
        new["value"]["trace"] = [row for row in new["value"]["trace"] if row["family"] != "google"]
        for receipt in (old, new):
            for row in receipt["value"]["trace"]:
                if row["status"] == "selected":
                    row["status"] = "eligible"
            for field in ("selected", "fail_closed_reason", "substitution_note"):
                receipt["value"].pop(field, None)
        assert old == new, inputs


def test_reviewer_seats_fixture_only_removes_claude_cursor_review_rows():
    """#10464 (D-129): the overlay drops every Opus-on-Cursor row and changes nothing else."""
    assert hashlib.sha256(SEATS_OVERLAY_PATH.read_bytes()).hexdigest() == (
        "b11f33cdad1152f6a99c8bdba56395b9670213bccd786c3a91e143b4b5e5fc40"
    )
    assert set(SEATS_OVERLAY["surfaces"]) == {"catalog", "roles", "routing_holders", "reviewer"}
    assert set(SEATS_OVERLAY["inputs"]) == {"dispatch", "roles", "reviewer"}
    route = "claude-opus-5-5-cursor-fallback"

    def key(value):
        return json.dumps(value, sort_keys=True)

    def claude_on_cursor(row):
        return isinstance(row, dict) and row.get("family") == "anthropic" and row.get("transport") == "cursor"

    # Inputs: an order-preserving removal of only the rows naming the removed route or pin.
    for surface in ("dispatch", "roles", "reviewer"):
        before, after = GEMINI_INPUTS[surface], SEATS_OVERLAY["inputs"][surface]
        kept = {key(row) for row in after}
        assert [row for row in before if key(row) in kept] == after
        removed = [row for row in before if key(row) not in kept]
        assert removed
        for row in removed:
            assert row["model"] == "claude-opus-5-5" if surface == "dispatch" else route in key(row)
    assert all(row["model"] != "claude-opus-5-5" for row in SEATS_OVERLAY["inputs"]["dispatch"])
    assert [len(SEATS_OVERLAY["inputs"][name]) for name in ("dispatch", "roles", "reviewer")] == [880, 855, 1480]

    # Reviewer receipts: only the removed trace row differs; no selection moves.
    previous = dict(zip(map(key, GEMINI_INPUTS["reviewer"]), GEMINI_OVERLAY["surfaces"]["reviewer"], strict=True))
    for inputs, after in zip(SEATS_OVERLAY["inputs"]["reviewer"], SEATS_OVERLAY["surfaces"]["reviewer"], strict=True):
        before = deepcopy(previous[key(inputs)])
        if isinstance(before.get("value"), dict) and "trace" in before["value"]:
            before["value"]["trace"] = [row for row in before["value"]["trace"] if row["name"] != route]
            assert not any(claude_on_cursor(row) for row in after["value"]["trace"])
        assert before == after, inputs

    # Role receipts: only the Opus Cursor candidate disappears.
    previous = dict(zip(map(key, GEMINI_INPUTS["roles"]), GEMINI_OVERLAY["surfaces"]["roles"], strict=True))
    for inputs, after in zip(SEATS_OVERLAY["inputs"]["roles"], SEATS_OVERLAY["surfaces"]["roles"], strict=True):
        before = deepcopy(previous[key(inputs)])
        if isinstance(before.get("value"), dict) and "candidates" in before["value"]:
            before["value"]["candidates"] = [row for row in before["value"]["candidates"] if not claude_on_cursor(row)]
        assert before == after, inputs

    # Routing holders: only the anthropic_authority Cursor route disappears.
    before = deepcopy(GEMINI_OVERLAY["surfaces"]["routing_holders"])
    for holders in before["roles"].values():
        holders[:] = [h for h in holders if (h["seat"], h["route_name"]) != ("anthropic_authority", "cursor_fallback")]
    del before["seats"]["anthropic_authority"]["wire_ids"]["cursor_fallback"]
    assert before == SEATS_OVERLAY["surfaces"]["routing_holders"]

    catalog = json.dumps(SEATS_OVERLAY["surfaces"]["catalog"])
    assert route not in catalog and "claude-opus-5-5-high" not in catalog
    assert "grok-4.7-cursor-fallback" in catalog


CLAUDE_MODEL = re.compile(r"\bclaude-(?:opus|sonnet|fable|haiku)-[0-9a-z.-]+")


def test_catalog_authorizes_no_claude_review_through_cursor():
    """#10464 AC-01/AC-02: no Claude review seat on Cursor; Sonnet reviews routine code only."""
    catalog = load_model_catalog()
    candidates = catalog["review_candidates"]
    family = {name: catalog["models"][row["model_id"]]["family"] for name, row in candidates.items()}
    assert not [
        name for name, row in candidates.items() if family[name] == "anthropic" and row["transport"] == "cursor"
    ]
    ladders = catalog["review_ladders"]
    for risk in ("critical", "high", "medium", "low"):
        for rung in ladders[risk]:
            for name in rung:
                assert not (family[name] == "anthropic" and candidates[name]["transport"] == "cursor"), (risk, name)
        on_ladder = {name for rung in ladders[risk] for name in rung}
        assert ("claude-sonnet-5-5" in on_ladder) == (risk in {"medium", "low"}), risk
        assert {"claude-opus-5-5", "grok-4.7", "grok-4.7-cursor-fallback"} <= on_ladder, risk
    for risk in ("low", "medium", "high", "critical"):
        routes = catalog["roles"][f"code_review_{risk}"]["routes"]
        assert "anthropic_authority/cursor_fallback" not in routes
        assert "xai_reviewer/cursor_fallback" in routes
    assert set(catalog["seats"]["anthropic_authority"]["routes"]) == {"native"}
    assert set(catalog["seats"]["xai_reviewer"]["routes"]) == {"native", "cursor_fallback"}
    assert catalog["seats"]["xai_reviewer"]["routes"]["cursor_fallback"]["transport_fallback_for"] == "grok-4.7"
    opus = catalog["models"]["claude-opus-5-5"]
    assert (opus["routing_wire_ids"], opus["transports"]) == (
        {"native_claude": "claude-opus-5-5", "agy": "claude-opus-5-5-high"},
        ["native_claude", "agy"],
    )
    cursor = catalog["budget_substitution_models"]["cursor"]
    assert "claude-opus-5-5" not in cursor
    assert cursor["claude-fable-5-1"] == "claude-fable-5-1-thinking-high"
    for kept in ("claude-fable-5-1", "claude-sonnet-5-5"):
        assert "cursor" in catalog["models"][kept]["transports"], kept


def test_catalog_text_records_d129_and_grok_static_review():
    """#10464 AC-01/AC-03: retired Cursor sentences are gone; the critical ladder names CI as Grok's proof."""
    text = (Path(__file__).resolve().parents[2] / "scripts/config/model_catalog.yaml").read_text(encoding="utf-8")
    assert "explicitly verified Cursor slug" not in text
    assert "natively or through Cursor" not in text
    lines = text[text.index("\nreview_ladders:\n") :].splitlines()
    critical = lines.index("  critical:")
    comment = " ".join(line.strip(" #") for line in lines[1:critical] if line.lstrip().startswith("#"))
    assert "CI is its execution proof" in comment
    assert "requests no execution" in comment


def test_rules_carry_no_claude_cursor_review_pin():
    """#10464 AC-03/AC-04: no Claude model is a Cursor review pin; Grok's static review stays CI-backed."""
    rules = Path(__file__).resolve().parents[2] / "agents_extensions/shared/rules"
    assignment = (rules / "model-assignment.md").read_text(encoding="utf-8")
    core = (rules / "core.md").read_text(encoding="utf-8")
    for name, text in (("model-assignment.md", assignment), ("core.md", core)):
        # A Claude id with a -high suffix is a Cursor wire slug; native Claude ids carry none.
        assert not [model for model in CLAUDE_MODEL.findall(text) if model.endswith("-high")], name
        for line in text.splitlines():
            if "cursor" in line.lower():
                assert not [model for model in CLAUDE_MODEL.findall(line) if f"--model {model}" in line], (name, line)
        assert "Other Models slug" not in text, name
        assert "Other Models pool" not in text, name
    # Cursor-authored work still needs a reviewer outside {xAI, Moonshot}.
    assert "Require a **single** cross-family reviewer from outside {xAI, Moonshot}" in assignment
    assert "**Cursor-as-reviewer:** Eligible only against authors outside {xAI, Moonshot}." in assignment
    assert "through native CLI and Cursor with runtime model attestation" in core
    assert "Grok briefs: diff/CI evidence, no execution requests." in core


@pytest.mark.parametrize("configuration", ["", "no-cli"])
def test_advisor_fixture_changes_only_headless_environment_and_launcher_help(configuration):
    assert hashlib.sha256((CAPACITY_FIXTURE / "claude-advisor-10083.json").read_bytes()).hexdigest() == (
        "6c4f6b3a080fcc5edfab6dff6d8bec8fb8cd3527f2c36a0a0be474066a24f8e1"
    )
    baseline = json.loads(gzip.decompress((FIXTURE / configuration / "baseline.json.gz").read_bytes()))
    original = deepcopy(baseline)
    updated = approved_review_baseline(baseline)
    advisor = json.loads((CAPACITY_FIXTURE / "claude-advisor-10083.json").read_bytes())
    assert advisor["adapter_rows"] == [8, 10, 12, 14, 16, 18, 20, 22]
    assert advisor["env_overrides"] == {"CLAUDE_CODE_DISABLE_ADVISOR_TOOL": "1"}
    changed = []
    for index, (before, after) in enumerate(zip(baseline["adapters"], updated["adapters"], strict=True)):
        if before != after:
            changed.append(index)
            assert INPUTS["adapters"][index]["agent"].startswith("claude")
            assert INPUTS["adapters"][index]["isolation"] is False
            restored = deepcopy(after)
            assert restored["value"]["env_overrides"].pop("CLAUDE_CODE_DISABLE_ADVISOR_TOOL") == "1"
            assert restored == before
    assert changed == advisor["adapter_rows"]
    assert len(updated["adapters"]) == len(baseline["adapters"])
    launcher_changes = []
    for index, (before, after) in enumerate(zip(baseline["launchers"], updated["launchers"], strict=True)):
        if before != after:
            launcher_changes.append(index)
            assert INPUTS["launchers"][index]["variant"] == "help"
            restored = deepcopy(after)
            for replacement in advisor["launcher_help_replacements"]:
                assert restored["stdout"].count(replacement["after"]) == 1
                restored["stdout"] = restored["stdout"].replace(replacement["after"], replacement["before"])
            assert restored == before
    assert launcher_changes == advisor["launcher_rows"] == list(range(4, 70, 5))
    assert len(updated["launchers"]) == len(baseline["launchers"])
    for surface in baseline.keys() - {"reviewer", "adapters", "launchers"}:
        assert updated[surface] == baseline[surface]
    assert baseline == original


def test_review_capacity_fixture_is_pinned_and_scope_bounded():
    assert hashlib.sha256((CAPACITY_FIXTURE / "routing-10016.json.gz").read_bytes()).hexdigest() == (
        "7446be4dfbedb928fa3760bdb508785cc82b95995fc09d4662a67d6a2c6b1b1a"
    )

    def original_receipt(value):
        if isinstance(value, list):
            return [original_receipt(row) for row in value]
        if isinstance(value, dict):
            return {
                key: row[:1] + row[2:] if key == "selection_score" and row is not None else original_receipt(row)
                for key, row in value.items()
                if key != "capacity"
            }
        return value

    before = BASELINE["reviewer"]
    after = REVIEW_CAPACITY_BASELINE["reviewer"]
    assert len(before) == len(after) == len(INPUTS["reviewer"]) == 1480
    semantic_changes = selection_changes = 0
    approved_labels = (
        {"claude": "near_cap", "codex": "near_cap"},
        {"agents": {"codex": {"health": {"healthy": True}, "status": "near_cap"}}, "diagnostics": {"stale": False}},
        {"agents": {"codex": {"health": {"healthy": True}, "status": "hot"}}, "diagnostics": {"stale": True}},
    )
    for old, new, inputs in zip(before, after, INPUTS["reviewer"], strict=True):
        if original_receipt(new) != old:
            semantic_changes += 1
            assert inputs["routing_snapshot"] in approved_labels
        old_pick = (old["value"]["selected"] or {}).get("name")
        new_pick = (new["value"]["selected"] or {}).get("name")
        if old_pick != new_pick:
            selection_changes += 1
            assert inputs["routing_snapshot"] == approved_labels[0]
            assert old_pick == "grok-4.7"
            assert new_pick == ("claude-sonnet-5-5" if inputs["risk"] in {"low", "medium"} else "claude-opus-5-5")
    assert (semantic_changes, selection_changes) == (24, 8)


# Literal digests bind the #10205 Cursor wire pin and allowlist revision and
# the #10262 explicit AGY review-risk refusals in both configurations; see SPEC.md.
PINNED_DIGESTS = {
    "routing-10263.json.gz": "3385853a0070ab9a2f77e1fb40d9178ce195e44e7fd6b8c8245702ec529b7d16",
    "SHA256SUMS": "4cba22dff8338f75c8ae96b35119c3da2bea3b3d7d6418c49e466ddc0ddf73a8",
    "SPEC.md": "958f43d7368d0552cbf1b5706df35da56cdc9408e4834e05bb0911754ae58455",
    "baseline.json.gz": "2cf8945084c13d7ce0b55e98a91522e897baee5ba53648f21ec7ae7b66cdaa5d",
    "capture.py": "4593850ca030a5e25fe7b0d09d629bc8014322a1c574070fb0b317e3bc368b3b",
    "inputs.json": "4f9d9dd89acff3872a9e627a9627516c65b7e410da28464a4dda9105c0ec34b0",
    "no-cli/SHA256SUMS": "7e5b78a91bd237a012805983da7d40f854c9802eae969d0f5e4fabcc0d2afea8",
    "no-cli/baseline.json.gz": "d3b4e4776f701d3f1304a48de75c0e9bb1d488a1837000bb9113957eace9896d",
    "no-cli/inputs.json": "4f9d9dd89acff3872a9e627a9627516c65b7e410da28464a4dda9105c0ec34b0",
    "no-cli/occurrences.json.gz": "8ca9e434a36e330dab713ddcc8c2c368c18e31666ee18bef2de2505b15aa12c7",
    "occurrences.json.gz": "8ca9e434a36e330dab713ddcc8c2c368c18e31666ee18bef2de2505b15aa12c7",
}


@pytest.mark.repo_wide
def test_frozen_artifacts_are_pinned_independently_of_manifest():
    assert PINNED_DIGESTS
    assert set(PINNED_DIGESTS) == {str(p.relative_to(FIXTURE)) for p in FIXTURE.rglob("*") if p.is_file()}
    for name, expected in PINNED_DIGESTS.items():
        assert hashlib.sha256((FIXTURE / name).read_bytes()).hexdigest() == expected, name


def test_frozen_hashes_and_matrix_denominator():
    for row in (FIXTURE / "SHA256SUMS").read_text().splitlines():
        digest, name = row.split()
        assert hashlib.sha256((FIXTURE / name).read_bytes()).hexdigest() == digest
    assert INPUTS["base_sha"] == CAPTURE["BASE_SHA"]
    for surface in ("reviewer", "roles", "capacity", "dispatch", "adapters", "launchers"):
        assert len(INPUTS[surface]) == len(BASELINE[surface])
    assert {row["risk"] for row in INPUTS["reviewer"]} == {"low", "medium", "high", "critical"}
    assert {row["review_profile"] for row in INPUTS["reviewer"]} == {"code", "infra"}
    ledger = json.loads(gzip.decompress((FIXTURE / "occurrences.json.gz").read_bytes()))
    assert ledger and all(row["disposition"] and row["purpose"] and row["owner"] for row in ledger)


def test_legacy_catalog_equals_approved_routing_baseline():
    assert expanded_legacy_view() == approved_muse_candidate_catalog(APPROVED_BASELINE["catalog"])


@pytest.mark.parametrize(
    "entrypoint,args",
    [
        ("scripts/review/model_catalog.py", ["--resolve-role", "bounded_advisor"]),
        ("scripts/lint/lint_model_catalog.py", ["--as-of", "2026-10-07"]),
    ],
)
def test_direct_catalog_callers_without_repository_pythonpath(entrypoint, args, tmp_path):
    source = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [sys.executable, "-I", str(source / entrypoint), *args],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    if entrypoint.endswith("lint_model_catalog.py"):
        assert payload["ok"] is True
    else:
        assert payload["candidates"][0]["model_id"] == "gpt-6.1-sol"


@pytest.mark.parametrize("host_clis", ["absent", "present"])
def test_fresh_capture_equals_every_frozen_surface(tmp_path, host_clis):
    source = Path(__file__).resolve().parents[2]
    output = tmp_path / "capture"
    host_bin = tmp_path / "host-bin"
    host_bin.mkdir()
    for name in ("bash", "git", "cat"):
        (host_bin / name).symlink_to(shutil.which(name, path="/usr/bin:/bin"))
    if host_clis == "present":
        for name in (*CAPTURE["CLI_VERSIONS"], "npx"):
            stub = host_bin / name
            stub.write_text("#!/bin/sh\nprintf 'ambient CLI must not run\\n' >&2\nexit 99\n")
            stub.chmod(0o755)
    host_home = tmp_path / "host-home"
    host_home.mkdir()
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            CAPTURE_RUNNER,
            str(FIXTURE / "capture.py"),
            "--source-root",
            str(source),
            "--output",
            str(output),
            "--project-python",
            sys.executable,
        ],
        cwd=tmp_path,
        env={
            "PATH": str(host_bin),
            "TMPDIR": str(tmp_path),
            "HOME": str(host_home),
            "LAUNCHER_MODEL": "unregistered-model",
            "CODEX_HOME": str(host_home),
            "LEARN_UK_AGY_MODEL": "unregistered-model",
            "LU_ACPX_TRANSPORT": "shadow",
            "LEARN_UK_KIMI_BIN": str(host_bin / "kimi"),
            "TZ": "Pacific/Honolulu",
        },
        capture_output=True,
        text=True,
        timeout=600,
    )
    assert result.returncode == 0, result.stderr
    actual = json.loads(gzip.decompress((output / "baseline.json.gz").read_bytes()))
    assert_frozen_surfaces(actual)
    assert json.loads((output / "inputs.json").read_bytes()) == approved_muse_candidate_inputs(APPROVED_INPUTS)
    assert (output / "occurrences.json.gz").read_bytes() == (FIXTURE / "occurrences.json.gz").read_bytes()


def assert_frozen_surfaces(actual):
    assert actual.keys() == BASELINE.keys()
    expected = approved_muse_candidate_baseline(APPROVED_BASELINE)
    for surface in BASELINE:
        assert actual[surface] == expected[surface], f"approved surface differs: {surface}"
    assert len(actual["launchers"]) == len(BASELINE["launchers"]) == 70


def test_capture_runner_activates_and_restores_scoped_caches(tmp_path):
    source = Path(__file__).resolve().parents[2]
    capture = tmp_path / "capture.py"
    capture.write_text("""from scripts import delegate
from scripts.review import model_catalog

original_validator = model_catalog.validate_catalog
original_parser = delegate.build_parser

def capture():
    assert model_catalog.validate_catalog is not original_validator
    assert delegate.build_parser is not original_parser
    print("caches active")

def main():
    capture()
    assert model_catalog.validate_catalog is original_validator
    assert delegate.build_parser is original_parser
    print("caches restored")
""")
    result = subprocess.run(
        [sys.executable, "-c", CAPTURE_RUNNER, str(capture), "--source-root", str(source)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "caches active\ncaches restored\n"


@pytest.mark.parametrize("surface", BASELINE)
def test_fresh_capture_comparison_rejects_each_mutated_surface(surface):
    actual = approved_muse_candidate_baseline(APPROVED_BASELINE)
    actual[surface] = {"mutated": True}
    with pytest.raises(AssertionError, match=f"approved surface differs: {surface}"):
        assert_frozen_surfaces(actual)


@pytest.mark.parametrize("fail", [False, True])
def test_capture_catalog_cache_revalidates_mutations_and_restores_validator(monkeypatch, mocker, fail):
    from scripts import delegate
    from scripts.review import model_catalog

    catalog = deepcopy(load_model_catalog())
    validator = mocker.Mock(wraps=model_catalog.validate_catalog)
    monkeypatch.setattr(model_catalog, "validate_catalog", validator)
    parser_factory = mocker.Mock(wraps=delegate.build_parser)
    monkeypatch.setattr(delegate, "build_parser", parser_factory)

    def exercise():
        with cached_capture_reads():
            first = model_catalog.validate_catalog(catalog)
            first["models"].clear()
            assert model_catalog.validate_catalog(deepcopy(catalog))["models"] == catalog["models"]
            assert validator.call_count == 1
            catalog["schema_version"] = "invalid"
            with pytest.raises(model_catalog.ModelCatalogError):
                model_catalog.validate_catalog(catalog)
            assert validator.call_count == 2
            parser = delegate.build_parser()
            args = parser.parse_args(["dispatch", "--agent", "codex", "--task-id", "one", "--prompt", "first"])
            args.task_id = "mutated"
            fresh = delegate.build_parser().parse_args(
                ["dispatch", "--agent", "claude", "--task-id", "two", "--prompt", "second"]
            )
            assert (fresh.agent, fresh.task_id, fresh.prompt) == ("claude", "two", "second")
            assert parser_factory.call_count == 1
            if fail:
                raise RuntimeError("capture failed")

    if fail:
        with pytest.raises(RuntimeError, match="capture failed"):
            exercise()
    else:
        exercise()
    assert model_catalog.validate_catalog is validator
    assert delegate.build_parser is parser_factory
    with cached_capture_reads():
        model_catalog.validate_catalog(load_model_catalog())
        delegate.build_parser()
    assert validator.call_count == 3
    assert parser_factory.call_count == 2


def test_capture_environment_controls_lookup_and_version_probes(tmp_path):
    env = CAPTURE["capture_environment"](tmp_path)
    assert env["PATH"] == str(tmp_path / "bin")
    assert env["HOME"] == str(tmp_path / "home")
    assert env["TZ"] == "UTC"
    for name, version in CAPTURE["CLI_VERSIONS"].items():
        binary = shutil.which(name, path=env["PATH"])
        assert binary == str(tmp_path / "bin" / name)
        probe = subprocess.run([binary, "--version"], env=env, capture_output=True, text=True, timeout=5)
        assert (probe.returncode, probe.stdout, probe.stderr) == (0, version + "\n", "")
        invoke = subprocess.run([binary, "-p", "fixture"], env=env, capture_output=True, text=True, timeout=5)
        assert invoke.returncode == 97
        assert invoke.stderr == "capture stub refuses provider execution\n"
    assert shutil.which("npx", path=env["PATH"]) is None


@pytest.mark.parametrize("fail", [False, True])
def test_capture_policy_cache_is_scoped_and_restores_reader(tmp_path, monkeypatch, mocker, fail):
    from scripts.fleet import credit_lane

    policy_path = tmp_path / "policy.yaml"
    policy_text = credit_lane.POLICY_PATH.read_text()
    reader = mocker.Mock(wraps=credit_lane.load_policy)
    monkeypatch.setattr(credit_lane, "load_policy", reader)
    monkeypatch.setattr(sys, "path", sys.path.copy())

    def surfaces(source, scratch, project_python):
        policy = credit_lane.load_policy(policy_path)
        assert credit_lane.load_policy(policy_path) is policy
        if fail:
            raise RuntimeError("capture failed")
        return policy.near_cap_remaining_pct

    monkeypatch.setitem(CAPTURE["capture"].__globals__, "_capture_surfaces", surfaces)
    for calls, threshold in enumerate((11.0, 12.0), start=1):
        policy_path.write_text(
            policy_text.replace("near_cap_remaining_pct: 10.0", f"near_cap_remaining_pct: {threshold}")
        )
        if fail:
            with pytest.raises(RuntimeError, match="capture failed"):
                CAPTURE["capture"](tmp_path, tmp_path, Path(sys.executable))
        else:
            assert CAPTURE["capture"](tmp_path, tmp_path, Path(sys.executable)) == threshold
        assert reader.call_count == calls
        reader.assert_called_with(policy_path)
        assert credit_lane.load_policy is reader


def test_capture_encodes_structures_without_reordering_arrays():
    @dataclass
    class Row:
        values: frozenset[str]
        path: Path

    value = {"rows": [Row(frozenset({"b", "a"}), Path("fixture")), "last"]}
    assert json.loads(CAPTURE["encode"](value)) == {"rows": [{"values": ["a", "b"], "path": "fixture"}, "last"]}


@pytest.mark.parametrize("exception", [ValueError("refused"), SystemExit(2)])
def test_capture_preserves_refusals(exception):
    def refuse():
        raise exception

    result = CAPTURE["observed"](refuse)
    assert result["exit_status"] == (2 if isinstance(exception, SystemExit) else 1)
    assert result["exception"] == type(exception).__name__
    assert result["error"] == str(exception)


def test_capture_preserves_success_and_streams(capsys):
    def succeed():
        print("receipt")
        return ["second", "first"]

    assert CAPTURE["observed"](succeed) == {
        "exit_status": 0,
        "value": ["second", "first"],
        "stdout": "receipt\n",
        "stderr": "",
    }
    assert capsys.readouterr().out == ""


def test_capture_matrix_is_frozen():
    assert (
        CAPTURE["reviewer_inputs"](load_model_catalog()) == approved_muse_candidate_inputs(APPROVED_INPUTS)["reviewer"]
    )


def test_no_cli_capture_equals_separate_frozen_surface(tmp_path):
    source = Path(__file__).resolve().parents[2]
    output = tmp_path / "capture"
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            CAPTURE_RUNNER,
            str(FIXTURE / "capture.py"),
            "--configuration",
            "no-cli",
            "--source-root",
            str(source),
            "--output",
            str(output),
            "--project-python",
            sys.executable,
        ],
        cwd=tmp_path,
        env={"PATH": "/usr/bin:/bin", "TMPDIR": str(tmp_path)},
        capture_output=True,
        text=True,
        timeout=600,
    )
    assert result.returncode == 0, result.stderr
    expected = FIXTURE / "no-cli"
    assert json.loads((output / "inputs.json").read_bytes()) == approved_muse_candidate_inputs(APPROVED_INPUTS)
    assert (output / "occurrences.json.gz").read_bytes() == (expected / "occurrences.json.gz").read_bytes()
    for row in (output / "SHA256SUMS").read_text().splitlines():
        digest, name = row.split()
        assert hashlib.sha256((output / name).read_bytes()).hexdigest() == digest
    actual = json.loads(gzip.decompress((output / "baseline.json.gz").read_bytes()))
    original = json.loads(gzip.decompress((expected / "baseline.json.gz").read_bytes()))
    approved = approved_cto_wrappers_baseline(
        approved_claude_cap_baseline(
            approved_cursor_trailer_baseline(
                approved_launcher_canary_baseline(
                    approved_reviewer_seats_baseline(
                        {
                            **approved_review_baseline(original),
                            **GEMINI_OVERLAY["surfaces"],
                            **RESOURCE_OVERLAY["surfaces"],
                        }
                    )
                )
            )
        )
    )
    assert actual == approved_muse_candidate_baseline(approved)
    assert len(actual["launchers"]) == 70
    errors = [row.get("error", "") for row in actual["adapters"]]
    assert any("grok" in error and "PATH" in error for error in errors)
    assert any("cursor-agent" in error for error in errors)
    assert any(
        row.get("value", {}).get("cmd", [])[:2] == ["npx", "@anthropic-ai/claude-code@latest"]
        for row in actual["adapters"]
    )
    assert any("model probe for cursor could not verify" in row["stderr"] for row in actual["dispatch"])


def test_no_cli_environment_has_only_pinned_npx_probe(tmp_path):
    env = CAPTURE["capture_environment"](tmp_path, "no-cli")
    for name in CAPTURE["CLI_VERSIONS"]:
        assert shutil.which(name, path=env["PATH"]) is None
    assert list((tmp_path / "home").iterdir()) == []
    npx = shutil.which("npx", path=env["PATH"])
    probe = subprocess.run(
        [npx, "@anthropic-ai/claude-code@latest", "--version"], env=env, capture_output=True, text=True, timeout=5
    )
    assert (probe.returncode, probe.stdout, probe.stderr) == (0, "2.1.289 (Claude Code)\n", "")
    for argv in ([npx, "--version"], [npx, "@anthropic-ai/claude-code@latest", "-p", "fixture"]):
        assert subprocess.run(argv, env=env, capture_output=True, timeout=5).returncode == 97


def test_extended_capture_denominator_and_current_contract():
    catalog = load_model_catalog()
    assert set(BASELINE["routing_holders"]["roles"]) == set(catalog["roles"])
    assert set(BASELINE["routing_holders"]["seats"]) == set(catalog["seats"])
    pins = {row["model"] for row in INPUTS["dispatch"]}
    assert {pin for mapping in catalog["budget_substitution_models"].values() for pin in mapping} <= pins
    assert {row["review_attempt"] for row in INPUTS["dispatch"]} == {None, "frozen-review-attempt.yaml"}
    contract = CAPTURE["approval_contract_rows"](Path(__file__).resolve().parents[2], catalog)
    assert contract == approved_muse_candidate_approval(BASELINE["approval"])
    assert len(contract["rows"]) == len(catalog["models"]) * 9
    assert {row["outcome"] for row in contract["rows"]} == {"approved", "missing_approval", "operator_disposition"}
    assert all(not row["self_approval_counts"] for row in contract["rows"])
