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
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from scripts.review.model_catalog import load_model_catalog
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


def approved_claude_account_dispatch_baseline(baseline):
    """Apply #10619's account option and argparse usage reflow to refusals."""
    indent = " " * 28
    before = (
        f"{indent}[--mode {{read-only,workspace-write,danger}}] [--model MODEL] [--provider {{openrouter}}]\n"
        f"{indent}[--effort {{low,medium,high,xhigh,max}}] [--repo KEY] [--cwd CWD] [--worktree [WORKTREE]]\n"
        f"{indent}[--pr PR] [--pinned-head SHA] [--branch EXISTING] [--keep-worktree] [--finalize-open-pr]\n"
        f"{indent}[--require-review-verdict] [--review-profile {{code,infra,ukrainian}}]\n"
    )
    after = (
        f"{indent}[--mode {{read-only,workspace-write,danger}}] [--model MODEL] [--claude-account LABEL]\n"
        f"{indent}[--provider {{openrouter}}] [--effort {{low,medium,high,xhigh,max}}] [--repo KEY] [--cwd CWD]\n"
        f"{indent}[--worktree [WORKTREE]] [--pr PR] [--pinned-head SHA] [--branch EXISTING] [--keep-worktree]\n"
        f"{indent}[--finalize-open-pr] [--require-review-verdict] [--review-profile {{code,infra,ukrainian}}]\n"
    )
    dispatch = deepcopy(baseline["dispatch"])
    for row in dispatch:
        if row["stderr"].startswith("usage: delegate.py dispatch "):
            assert row["stderr"].count(before) == 1
            row["stderr"] = row["stderr"].replace(before, after)
    return {**baseline, "dispatch": dispatch}


# Apply literal paragraph edits last: a surface overlay such as #10291's Grok
# help revision must neither erase this wording nor have its other lines erased.
APPROVED_BASELINE = approved_claude_account_dispatch_baseline(
    approved_cto_wrappers_baseline(
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
)
APPROVED_INPUTS = {**GEMINI_INPUTS, **SEATS_OVERLAY["inputs"]}


# #10622 is an append-only policy overlay. Prior captures and every input stay frozen.
P2_OVERLAY_PATH = CAPACITY_FIXTURE / "routing-10622.json.gz"
P2_CURSOR_REASON = "native Grok only; Cursor transport is not a formal reviewer (#10622)"
P2_LAST_RESORT = {"openai_frontier", "grok-4.7", "claude-sonnet-5-5", "gemini-3.8-flash-high"}
P2_LADDERS = {
    "critical": [
        ["claude-opus-5-5"],
        ["grok-4.7-cursor-fallback"],
        ["composer-2.5"],
        ["pool"],
        ["pool-xs"],
        ["openai_frontier"],
        ["grok-4.7"],
    ],
    "high": [["claude-opus-5-5"], ["grok-4.7-cursor-fallback"], ["openai_frontier"], ["grok-4.7"]],
    "medium": [
        ["claude-opus-5-5"],
        ["grok-4.7-cursor-fallback"],
        ["composer-2.5"],
        ["pool"],
        ["pool-xs"],
        ["openai_frontier"],
        ["grok-4.7", "claude-sonnet-5-5", "gemini-3.8-flash-high"],
    ],
    "low": [
        ["claude-opus-5-5"],
        ["grok-4.7-cursor-fallback"],
        ["composer-2.5"],
        ["pool"],
        ["pool-xs"],
        ["openai_frontier"],
        ["grok-4.7", "claude-sonnet-5-5", "gemini-3.8-flash-high"],
    ],
}

P2_NATIVE_NOTE = "GPT-6 routes are native Codex only until Cursor exposes a verified GPT-6 slug. Claude Opus 5.5 reviews and drives through native Claude only; no Claude model reviews through Cursor (operator decision D-129, #10464). Grok authors through native CLI or Cursor grok-4.7-high and reviews through native CLI only at grok-4.7; it is not a stream driver (#10622). Only the standalone launcher Hermes opt-in remains security follow-up #10628. Cursor and Hermes are not formal review routes. The cursor orchestrator pin stays grok-4.7 because the seat allowlist and cursor bridge require it; that pin is not a stream driver and not a formal reviewer. Operator decision 2026-10-05 (#9769): native Grok reviews code and infra at every risk, including critical; verdicts require runtime model attestation and exclude xAI-authored changes. Native Grok does not outrank eligible Opus or Sol. Operator order 2026-09-22 (#8464) rotates from grok-4.6; #6865 previously retired opencode first-party xai/grok-* for orchestrator seats — opencode remains unsanctioned for grok. Hermes and OpenRouter grok routes remain banned. grok-4.6 and grok-4.7-build-fast are not admitted."
P2_CURSOR_NOTE = (
    "Cursor harness pin (parent #6952, #6955). The seat runs the concrete pin "
    "grok-4.7 (#8464; the launcher sends grok-4.7-high) or another allowlisted pin. "
    "Operator decision 2026-09-30 (#9274): Auto runs only a well-defined coding task "
    "(auto_scope: a write-capable dispatch typed --research-role implementation, with owned "
    "paths and a green DoR issue card, in agent mode) and only within the explicit allowlist (currently grok-4.7 [xAI], "
    "composer-2.5 [Moonshot]; refresh under the catalog ~30-day contract). The driver "
    "seat, review, design, consults, discussions and recon never run Auto. "
    "Cursor Auto selectors use the Cursor author family (#9951), even when the "
    "runtime reports a concrete model. Reviewers from other families can review "
    "Cursor-authored work; Cursor reviewers cannot. The legacy "
    "unknown_auto_union_families field describes the concrete allowlist only. "
    "A concrete Cursor grok-4.7 pin uses the xAI family and supports ordinary authoring "
    "through grok-4.7-high. Grok authoring also uses native CLI; formal Grok review uses "
    "native CLI only (#10622). This harness inventory grants neither formal-review "
    "eligibility nor a stream-driver assignment. Any driver-of-record claim still requires "
    "an attested concrete resolved_model from the run. "
    "Concurrency is 1 (the driver session is the Cursor lane; do not dispatch --agent cursor "
    "from within the driver session)."
)


def expected_p2_catalog(before):
    """Literal policy edits, independent of catalog expansion and capture output."""
    expected = deepcopy(before)
    for section in ("formal_cf_defaults", "orchestrator_seats"):
        assert expected[section]["grok"].pop("fallback_transport") == "cursor"
        assert expected[section]["grok"].pop("fallback_model_id") == "grok-4.7"
    expected["orchestrator_seats"]["grok"]["note"] = (
        "native grok-4.7 harness pin; not a stream driver and not a Cursor fallback (#10622)"
    )
    expected["orchestrator_seats"]["cursor"]["note"] = P2_CURSOR_NOTE
    expected["policy"]["notes"][2] = P2_NATIVE_NOTE
    for name in P2_LAST_RESORT:
        expected["review_candidates"][name]["last_resort"] = True
    expected["review_ladders"] = deepcopy(P2_LADDERS)
    endpoint = expected["review_scheduler"]["endpoints"]["cursor"]
    assert endpoint["formal_review_eligible"] is True
    endpoint.update(formal_review_eligible=False, formal_review_exclusion_reason=P2_CURSOR_REASON)
    return expected


def expected_p2_roles(before, inputs):
    """Only risk-typed roles gain the Cursor endpoint exclusion; inventory stays data."""
    expected = deepcopy(before)
    for case, receipt in zip(inputs, expected, strict=True):
        if case["role"] not in {f"code_review_{risk}" for risk in P2_LADDERS}:
            continue
        for candidate in receipt.get("value", {}).get("candidates", []):
            if (candidate["seat"], candidate["route_name"]) == ("xai_reviewer", "cursor_fallback"):
                candidate["exclusion_reasons"].append("formal_endpoint_not_eligible")
    return expected


def expected_p2_reviewer(before, case):
    """Keep frozen gate results and identities; apply only the ordered P2 delta.

    This is deliberately scoped to the historical matrix, not another resolver.
    Eligible unpinned Opus wins; other picks and all earlier gates stay frozen.
    A Cursor endpoint refusal precedes capability/isolation and pin checks.
    """
    expected = deepcopy(before)
    value = expected["value"]
    if not value["trace"]:
        return expected
    trace = {row["name"]: row for row in value["trace"]}
    old_pick = (value["selected"] or {}).get("name")
    for name, row in trace.items():
        if row["status"] == "selected":
            row["status"] = "eligible"
        endpoint_reasons = (
            {
                None,
                "isolation required but candidate does not support process isolation",
                "missing required capabilities: ['sealed_evidence']",
                "missing required capabilities: ['unsupported']",
            }
            if name == "grok-4.7-cursor-fallback"
            else {"sealed endpoint 'cursor' is not pinned for model 'composer-2.5'"}
        )
        if (
            case.get("formal_review", True)
            and name in {"grok-4.7-cursor-fallback", "composer-2.5"}
            and row["reason"] in endpoint_reasons
        ):
            row.update(status="excluded", reason=P2_CURSOR_REASON, selection_score=None, suitability_rank=None)
    # Explicit pins never inherit automatic preference; their hard gates still bind.
    pick = old_pick
    if old_pick == "grok-4.7-cursor-fallback":
        assert case["pinned_candidate"] == old_pick
        pick = None
        value["fail_closed_reason"] = f"explicit reviewer pin {old_pick!r} failed a hard eligibility gate"
    elif (
        old_pick
        and case.get("formal_review", True)
        and not case.get("pinned_candidate")
        and trace["claude-opus-5-5"]["status"] == "eligible"
    ):
        pick = "claude-opus-5-5"
    if pick:
        trace[pick]["status"] = "selected"
    value["selected"] = deepcopy(trace[pick]) if pick else None
    if pick != old_pick:
        assert pick in {None, "claude-opus-5-5"}
        value["substitution_note"] = None
    elif pick in P2_LAST_RESORT:
        prefix = f"last resort selected {pick}: no eligible primary remained or an explicit pin was requested"
        value["substitution_note"] = "; ".join(filter(None, (prefix, value["substitution_note"])))
    order = [name for rung in P2_LADDERS[value["resolved_risk"]] for name in rung]
    extras = [name for name in trace if name not in order]
    assert not extras or extras == [case["pinned_candidate"]]
    value["trace"] = [trace[name] for name in [*order, *extras]]
    return expected


def validate_p2_overlay(baseline, inputs, overlay):
    """Reject every field outside the literal policy delta, including input changes."""
    assert set(overlay) == {"catalog", "roles", "reviewer"}
    assert overlay["catalog"] == expected_p2_catalog(baseline["catalog"])
    assert overlay["roles"] == expected_p2_roles(baseline["roles"], inputs["roles"])
    expected = [
        expected_p2_reviewer(old, case) for old, case in zip(baseline["reviewer"], inputs["reviewer"], strict=True)
    ]
    assert overlay["reviewer"] == expected


def approved_p2_baseline(baseline):
    """Apply #10622 equally to host-CLI and no-CLI expectations."""
    overlay = json.loads(gzip.decompress(P2_OVERLAY_PATH.read_bytes()))
    return {**baseline, **overlay}


PRE_P2_BASELINE = APPROVED_BASELINE
APPROVED_BASELINE = approved_p2_baseline(PRE_P2_BASELINE)


P2_OVERLAY_DIGEST = "15d22cce723f25a3d265a2891b9b1d517c0742272ea2325d524d5caea0839ffd"
PRE_P2_FIXTURE_BLOBS = {
    "tests/fixtures/routing_baseline/SHA256SUMS": "5a6ba3c155a7c8ab1f8f6bf9980d47ebf5868853",
    "tests/fixtures/routing_baseline/baseline.json.gz": "b4cba3427d617e955870d18264e2d85e1bbbab27",
    "tests/fixtures/routing_baseline/capture.py": "4a404984031ecfdb31ed9abf4befbae9504b785f",
    "tests/fixtures/routing_baseline/inputs.json": "1f5b36cd526da500fcb1013933c0eba1ba986e22",
    "tests/fixtures/routing_baseline/no-cli/SHA256SUMS": "4e75c343979c8d9cd0a7558e0a6afb8c6fdb430c",
    "tests/fixtures/routing_baseline/no-cli/baseline.json.gz": "d842a3c7734f1586c31247360df22e5203533971",
    "tests/fixtures/routing_baseline/no-cli/inputs.json": "1f5b36cd526da500fcb1013933c0eba1ba986e22",
    "tests/fixtures/routing_baseline/no-cli/occurrences.json.gz": "ba9c8c0357c2fe10b1588a3ce37348f8318ec502",
    "tests/fixtures/routing_baseline/occurrences.json.gz": "ba9c8c0357c2fe10b1588a3ce37348f8318ec502",
    "tests/fixtures/routing_baseline/routing-10263.json.gz": "c706611601703ca8abd792c55c19be26a23d35be",
    "tests/review/fixtures/claude-advisor-10083.json": "dded4c0e422ad15e23543f9558bd5dcc35ef9d62",
    "tests/review/fixtures/claude-cap-10355.json": "60cee5798fced0992427f66a574221391262af52",
    "tests/review/fixtures/cto-wrappers-10453.json": "7440359cbda5e2d0456ee5d1271168c62c284da9",
    "tests/review/fixtures/fenced_returns/plan-review-a1-p2-agy-r7.yaml": "d70a663e8da6750eaa6a83a81383363305bdba26",
    "tests/review/fixtures/fenced_returns/plan-review-a1-p3-agy-r2.yaml": "499e4e57e32dfd4114df65b194674961dff7c825",
    "tests/review/fixtures/isolated-main-prompts/lesson-rereview.md.j2": "69b4747b352cd15fe1e63bcd30c4306b76de2a16",
    "tests/review/fixtures/isolated-main-prompts/lesson-review.md.j2": "ced41c0aad621a68982ad2bec05e0abbf2b26e17",
    "tests/review/fixtures/isolated-main-prompts/plan-review.md.j2": "b72f7e936f6f664a15d4aa0746ab60bbbdc332f5",
    "tests/review/fixtures/launcher-canary-10266.json": "94e378722fb1e70bc5f5cfe6ab45190a520fc23b",
    "tests/review/fixtures/routing-10016.json.gz": "28c6c43395c1f34c7a30277636240f20b34ecaf1",
    "tests/review/fixtures/routing-10016.md": "df834617bfd496eeee889fdba080013fddbf3196",
    "tests/review/fixtures/routing-10073.json.gz": "a37189e451203328e538b4e5f40f6fb6376492e7",
    "tests/review/fixtures/routing-10073.md": "18ef33da05e46f178f2456723fb00ae636e01adf",
    "tests/review/fixtures/routing-10464.json.gz": "b432e7dd5dc186c27450efe344925667e277ed93",
}


@pytest.mark.parametrize("configuration", ("host-cli", "no-cli"))
def test_p2_overlay_is_pinned_and_exactly_policy_scoped(configuration):
    raw = P2_OVERLAY_PATH.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == P2_OVERLAY_DIGEST
    assert raw[4:8] == bytes(4)
    overlay = json.loads(gzip.decompress(raw))
    # The only configuration-specific data is outside this overlay's three surfaces.
    original = json.loads(
        gzip.decompress((FIXTURE / ("no-cli" if configuration == "no-cli" else "") / "baseline.json.gz").read_bytes())
    )
    assert {key: original[key] for key in ("catalog", "roles", "reviewer")} == {
        key: BASELINE[key] for key in ("catalog", "roles", "reviewer")
    }
    before = deepcopy(PRE_P2_BASELINE)
    validate_p2_overlay(before, APPROVED_INPUTS, overlay)
    after = approved_p2_baseline(before)
    assert before == PRE_P2_BASELINE
    assert {key: value for key, value in after.items() if key not in overlay} == {
        key: value for key, value in before.items() if key not in overlay
    }
    assert sum(a != b for a, b in zip(before["roles"], after["roles"], strict=True)) == 220
    assert sum(a != b for a, b in zip(before["reviewer"], after["reviewer"], strict=True)) == 1136
    assert (
        sum(
            a["value"]["selected"] != b["value"]["selected"]
            for a, b in zip(before["reviewer"], after["reviewer"], strict=True)
        )
        == 494
    )


@pytest.mark.parametrize(
    "mutation",
    (
        "surface",
        "input",
        "catalog_identity",
        "catalog_capability",
        "endpoint",
        "role_identity",
        "role_health",
        "legacy_permission",
        "review_identity",
        "review_health",
        "review_capability",
        "review_selection",
        "review_reason",
        "review_score",
        "review_risk",
        "review_metadata",
        "review_note",
    ),
)
def test_p2_scope_guard_rejects_unauthorized_changes(mutation):
    overlay = json.loads(gzip.decompress(P2_OVERLAY_PATH.read_bytes()))
    if mutation == "surface":
        overlay["adapters"] = []
    elif mutation == "input":
        overlay["inputs"] = APPROVED_INPUTS
    elif mutation == "catalog_identity":
        overlay["catalog"]["models"]["grok-4.7"]["family"] = "openai"
    elif mutation == "catalog_capability":
        overlay["catalog"]["models"]["grok-4.7"]["roles"].append("ukrainian_review")
    elif mutation == "endpoint":
        overlay["catalog"]["review_scheduler"]["endpoints"]["cursor"]["formal_review_eligible"] = True
    elif mutation.startswith("role_") or mutation == "legacy_permission":
        index = next(i for i, case in enumerate(APPROVED_INPUTS["roles"]) if case["role"] == "legacy_reviewers")
        row = next(row for row in overlay["roles"][index]["value"]["candidates"] if row["transport"] == "cursor")
        if mutation == "role_identity":
            row["wire_id"] = "grok-4.7-high-fast"
        elif mutation == "role_health":
            row["health"] = "healthy"
        else:
            row["exclusion_reasons"].append("formal_endpoint_not_eligible")
    else:
        value = overlay["reviewer"][84]["value"]
        row = next(row for row in value["trace"] if row["name"] == "grok-4.7-cursor-fallback")
        if mutation == "review_identity":
            row["family"] = "openai"
        elif mutation == "review_health":
            row["health"] = "healthy"
        elif mutation == "review_capability":
            row["requires_silence_timeout"] = True
        elif mutation == "review_selection":
            value["selected"] = row
        elif mutation == "review_reason":
            row["reason"] = None
        elif mutation == "review_score":
            row["selection_score"] = [0]
        elif mutation == "review_risk":
            value["resolved_risk"] = "critical"
        elif mutation == "review_metadata":
            value["catalog_reviewed_on"] = "2099-01-01"
        elif mutation == "review_note":
            value["substitution_note"] = "approved"
    with pytest.raises(AssertionError):
        validate_p2_overlay(PRE_P2_BASELINE, APPROVED_INPUTS, overlay)


def test_all_prior_fixture_blobs_remain_frozen():
    root = Path(__file__).resolve().parents[2]
    assert len(PRE_P2_FIXTURE_BLOBS) == 24
    for name, expected_blob in PRE_P2_FIXTURE_BLOBS.items():
        raw = (root / name).read_bytes()
        assert hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest() == expected_blob, name


@pytest.mark.parametrize("configuration", ("host-cli", "no-cli"))
def test_claude_account_dispatch_baseline_changes_only_usage_option(configuration):
    path = FIXTURE / ("no-cli" if configuration == "no-cli" else "") / "baseline.json.gz"
    original = json.loads(gzip.decompress(path.read_bytes()))
    before = deepcopy(original)
    after = approved_claude_account_dispatch_baseline(original)
    assert original == before
    assert {key: value for key, value in after.items() if key != "dispatch"} == {
        key: value for key, value in before.items() if key != "dispatch"
    }
    changed = 0
    for old, new in zip(before["dispatch"], after["dispatch"], strict=True):
        assert {key: value for key, value in old.items() if key != "stderr"} == {
            key: value for key, value in new.items() if key != "stderr"
        }
        if old["stderr"].startswith("usage: delegate.py dispatch "):
            changed += 1
            assert new["stderr"].count("[--claude-account LABEL]") == 1
            assert new["stderr"].replace("[--claude-account LABEL]", "").split() == old["stderr"].split()
        else:
            assert new == old
    assert changed > 0


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
    assert (
        "**Cursor-as-reviewer:** Not a formal reviewer (#10622), including against authors outside {xAI, Moonshot}. The endpoint is not formal-review eligible."
        in assignment
    )
    assert "through the native CLI with runtime model attestation" in core
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
    "SPEC.md": "df10c35d9c5360cb488961ce466658d5b163c92f73815446f70247c8a415709c",
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
    assert expanded_legacy_view() == APPROVED_BASELINE["catalog"]


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
    assert json.loads((output / "inputs.json").read_bytes()) == APPROVED_INPUTS
    assert (output / "occurrences.json.gz").read_bytes() == (FIXTURE / "occurrences.json.gz").read_bytes()


def assert_frozen_surfaces(actual):
    assert actual.keys() == BASELINE.keys()
    for surface in BASELINE:
        assert actual[surface] == APPROVED_BASELINE[surface], f"approved surface differs: {surface}"
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
    actual = dict(APPROVED_BASELINE)
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
    assert CAPTURE["reviewer_inputs"](load_model_catalog()) == APPROVED_INPUTS["reviewer"]


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
    assert json.loads((output / "inputs.json").read_bytes()) == APPROVED_INPUTS
    assert (output / "occurrences.json.gz").read_bytes() == (expected / "occurrences.json.gz").read_bytes()
    for row in (output / "SHA256SUMS").read_text().splitlines():
        digest, name = row.split()
        assert hashlib.sha256((output / name).read_bytes()).hexdigest() == digest
    actual = json.loads(gzip.decompress((output / "baseline.json.gz").read_bytes()))
    original = json.loads(gzip.decompress((expected / "baseline.json.gz").read_bytes()))
    expected_p2_input = approved_claude_account_dispatch_baseline(
        approved_cto_wrappers_baseline(
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
    )
    assert actual == approved_p2_baseline(expected_p2_input)
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
    assert contract == BASELINE["approval"]
    assert len(contract["rows"]) == len(catalog["models"]) * 9
    assert {row["outcome"] for row in contract["rows"]} == {"approved", "missing_approval", "operator_disposition"}
    assert all(not row["self_approval_counts"] for row in contract["rows"])
