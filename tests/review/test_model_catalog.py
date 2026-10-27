"""Frozen routing evidence with scoped, hash-pinned approved overlays."""

from __future__ import annotations

import gzip
import hashlib
import json
import pickle
import runpy
import shutil
import subprocess
import sys
from contextlib import contextmanager
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from scripts.review.model_catalog import (
    ModelCatalogError,
    _require_routable_model,
    load_model_catalog,
    require_execution_model,
)

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


ARGON_OVERLAY_PATH = CAPACITY_FIXTURE / "routing-10568.json.gz"
ARGON_OVERLAY = json.loads(gzip.decompress(ARGON_OVERLAY_PATH.read_bytes()))


def approved_argon_trial_baseline(baseline, configuration):
    """Apply #10568's Argon catalog, approval and reviewer additions.

    Historical baseline bytes stay put. Pro, registry, launcher and adapter
    receipts retain their baseline values. Refusal help lists the added slugs.
    """
    updated = {**baseline, **ARGON_OVERLAY["surfaces"]}
    for surface, rows in ARGON_OVERLAY["row_patches"].items():
        copied = deepcopy(updated[surface])
        for index, row in rows.items():
            copied[int(index)] = row
        updated[surface] = copied
    adapters = deepcopy(updated["adapters"])
    for index, row in ARGON_OVERLAY["adapter_patches"][configuration].items():
        adapters[int(index)] = row
    updated["adapters"] = adapters
    return updated


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


def approved_hermes_effort_baseline(baseline):
    """Apply #10751's constant Hermes effort warning to the frozen adapter stderr.

    The warning no longer carries the requested effort value, so the captured
    text drops ``='high'``; every other adapter field and surface is unchanged.
    """
    fixture = json.loads((CAPACITY_FIXTURE / "hermes-effort-10751.json").read_bytes())
    adapters = deepcopy(baseline["adapters"])
    for replacement in fixture["adapter_stderr_replacements"]:
        before, after = replacement["before"], replacement["after"]
        for index in replacement["rows"]:
            assert adapters[index]["stderr"].count(before) == 1
            adapters[index]["stderr"] = adapters[index]["stderr"].replace(before, after)
    return {**baseline, "adapters": adapters}


# Claude worker adapter rows whose command carries the shared guard settings.
HOOK_FAILURE_ROWS = list(range(8, 24, 2))
# Guard -> (captured timeout, approved timeout, refuses the call on hook failure).
HOOK_FAILURE_POLICY = {
    "enforce-venv.sh": (3, 10, True),
    "heal-core-bare.py": (3, 10, False),
    "guard-branch-switch-in-main.py": (3, 10, True),
    "guard-admin-merge.py": (30, 30, True),
    "guard-pr-merge.py": (30, 30, True),
    "guard-secret-print.py": (5, 10, True),
    "guard-primary-checkout-write.py": (5, 10, True),
    "guard-public-github-text.py": (5, 10, True),
}


def settings_index(row):
    cmd = row["value"]["cmd"]
    assert cmd.count("--settings") == 1
    return cmd.index("--settings") + 1


def approved_hook_failure_baseline(baseline):
    """Apply #10848's fail-closed guard policy to the Claude worker settings.

    Only the ``--settings`` argument of the eight Claude worker adapter rows
    changes: each shared PreToolUse guard takes its approved timeout, and every
    refusing guard gains ``onFailure: block``. Other fields and surfaces stay.
    """
    adapters = deepcopy(baseline["adapters"])
    for index in HOOK_FAILURE_ROWS:
        cmd = adapters[index]["value"]["cmd"]
        position = settings_index(adapters[index])
        settings = json.loads(cmd[position])
        guards = [hook for group in settings["hooks"]["PreToolUse"] for hook in group["hooks"]]
        assert len(guards) == 9
        for hook in guards:
            before, after, blocks = HOOK_FAILURE_POLICY[Path(hook["command"]).name]
            assert hook["timeout"] == before and "onFailure" not in hook
            hook["timeout"] = after
            if blocks:
                hook["onFailure"] = "block"
        cmd[position] = json.dumps(settings, separators=(",", ":"))
    return {**baseline, "adapters": adapters}


# Apply literal paragraph edits last: a surface overlay such as #10291's Grok
# help revision must neither erase this wording nor have its other lines erased.
PRE_ARGON_HOST_BASELINE = approved_hook_failure_baseline(
    approved_hermes_effort_baseline(
        approved_claude_account_dispatch_baseline(
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
    )
)
GROK_LANGUAGE_OVERLAY_PATH = CAPACITY_FIXTURE / "routing-10835.json"
GROK_LANGUAGE_OVERLAY = json.loads(GROK_LANGUAGE_OVERLAY_PATH.read_bytes())


def approved_grok_language_seat_baseline(baseline):
    """Apply #10835 (operator order 2026-10-16) last: two literal field edits.

    ``grok-4.7`` gains the ``ukrainian_review`` role and the fallback
    ``worker_resource_policy`` states the Sonnet worker default, the native Grok
    measurement rule and the Gemini 4 hold. Each edit checks its recorded
    ``before`` value, so a drifted baseline fails instead of being overwritten.
    """
    catalog = deepcopy(baseline["catalog"])
    for row in GROK_LANGUAGE_OVERLAY["catalog_model_fields"]:
        assert catalog["models"][row["model"]][row["field"]] == row["before"]
        catalog["models"][row["model"]][row["field"]] = row["after"]
    fallbacks = deepcopy(baseline["fallbacks"])
    for row in GROK_LANGUAGE_OVERLAY["fallbacks_fields"]:
        assert fallbacks[row["field"]] == row["before"]
        fallbacks[row["field"]] = row["after"]
    return {**baseline, "catalog": catalog, "fallbacks": fallbacks}


ARGON_HOST_BASELINE = approved_argon_trial_baseline(PRE_ARGON_HOST_BASELINE, "host-cli")
GROK_LANGUAGE_BASELINE = approved_grok_language_seat_baseline(ARGON_HOST_BASELINE)


def approved_driver_brief_baseline(baseline):
    """Apply only #10919's Haiku fields and Luna recon/classification roles."""
    path = CAPACITY_FIXTURE / "haiku-luna-brief-10919.json"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == (
        "39b9928c4ce9a261ee329e8f1cb87833a9f9243b9a84298eb2cafbdf056652eb"
    )
    changes = json.loads(path.read_bytes())
    catalog = deepcopy(baseline["catalog"])
    for row in changes["catalog_model_fields"]:
        assert (row["model"], row["field"]) in {
            ("claude-haiku-5-5", "roles"), ("claude-haiku-5-5", "weaknesses"),
            ("claude-haiku-5-5", "notes"), ("gpt-6-luna", "roles"),
        }
        assert catalog["models"][row["model"]][row["field"]] == row["before"]
        catalog["models"][row["model"]][row["field"]] = row["after"]
    dispatch = deepcopy(baseline["dispatch"])
    for row in changes["dispatch_refusals"]:
        target = dispatch[row["index"]]["value"]
        assert target["refusal"] == row["before"]
        assert row["after"] == row["before"].replace(
            "bounded_investigation; review_scheduler",
            "bounded_investigation, readonly_recon, mechanical_classification; review_scheduler",
        )
        target["refusal"] = row["after"]
    return {**baseline, "catalog": catalog, "dispatch": dispatch}


def approved_budget_pin_baseline(baseline):
    """Apply #11110's exhausted, unmapped Claude pin refusals after the other overlays."""
    path = CAPACITY_FIXTURE / "budget-pin-11110.json"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == (
        "4b30a903b56b91349d05eeeb79cdb5a1c13b447e9bcc1aa80b546c54e777418e"
    )
    fixture = json.loads(path.read_bytes())
    dispatch = deepcopy(baseline["dispatch"])
    for replacement in fixture["dispatch_refusal_replacements"]:
        before, after = replacement["before"], replacement["after"]
        for index in replacement["rows"]:
            refusal = dispatch[index]["value"]["refusal"]
            assert refusal.count(before) == 1
            dispatch[index]["value"]["refusal"] = refusal.replace(before, after)
    return {**baseline, "dispatch": dispatch}


WORD_CARD_TOOL_PATH = CAPACITY_FIXTURE / "word-card-tool-11084.json"
# Codex and Codex Desktop read-only rows, which grant every read-only Sources tool.
WORD_CARD_TOOL_ROWS = [0, 4]


def approved_word_card_tool_baseline(baseline):
    """Apply #11084's read-only ``word_card`` Sources grant to the Codex worker argv.

    The two read-only Codex rows derive their Sources ``enabled_tools`` and
    approval map from the server's tool declarations, so each gains exactly
    ``word_card``. Every other row, field and surface stays.
    """
    assert hashlib.sha256(WORD_CARD_TOOL_PATH.read_bytes()).hexdigest() == (
        "d0a1a006af2440f0d823508c8d59228cd7fda6a0dc51eaa894fecf8a47598fb4"
    )
    adapters = deepcopy(baseline["adapters"])
    for replacement in json.loads(WORD_CARD_TOOL_PATH.read_bytes())["adapter_cmd_replacements"]:
        before, after = replacement["before"], replacement["after"]
        assert replacement["rows"] == WORD_CARD_TOOL_ROWS
        for index in replacement["rows"]:
            cmd = adapters[index]["value"]["cmd"]
            assert cmd.count(before) == 1
            cmd[cmd.index(before)] = after
    return {**baseline, "adapters": adapters}


MUSE_SEAT_PATH = CAPACITY_FIXTURE / "muse-seat-11026.json"


def approved_muse_seat_baseline(baseline):
    """Apply #11026's Muse subject-seat name to frozen unknown-seat refusals."""
    raw = MUSE_SEAT_PATH.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == (
        "eec3a5ff2ff3c4799a6635567b0abb82a83f2dc999968c0a626b8e13e20e0b99"
    )
    reviewer = deepcopy(baseline["reviewer"])
    for replacement in json.loads(raw)["reviewer_fail_closed_reason_replacements"]:
        before, after = replacement["before"], replacement["after"]
        for index in replacement["rows"]:
            reason = reviewer[index]["value"]["fail_closed_reason"]
            assert reason.count(before) == 1
            reviewer[index]["value"]["fail_closed_reason"] = reason.replace(before, after)
    return {**baseline, "reviewer": reviewer}


AGY_MODE_PATH = CAPACITY_FIXTURE / "agy-mode-11152.json"
AGY_AUTHORING_ROWS = [108, 110]
AGY_REVIEW_ROWS = [109, 111]


def approved_agy_mode_baseline(baseline):
    """Apply #11152's auto mode and native MCP config metadata to AGY authoring."""
    assert hashlib.sha256(AGY_MODE_PATH.read_bytes()).hexdigest() == (
        "858a1ef91de7803d0996469ee437788e1ca624a2aa659268271a1304e0712c54"
    )
    fixture = json.loads(AGY_MODE_PATH.read_bytes())
    adapters = deepcopy(baseline["adapters"])
    for replacement in fixture["adapter_cmd_replacements"]:
        before, after = replacement["before"], replacement["after"]
        assert replacement["rows"] == AGY_AUTHORING_ROWS
        for index in replacement["rows"]:
            cmd = adapters[index]["value"]["cmd"]
            assert cmd.count(before) == 1
            assert "--mode" not in cmd
            position = cmd.index(before)
            cmd[position:position + 1] = after.split()
    for replacement in fixture["adapter_metadata_replacements"]:
        before, after = replacement["before"], replacement["after"]
        assert replacement["rows"] == AGY_AUTHORING_ROWS
        for index in replacement["rows"]:
            metadata = json.dumps(adapters[index]["value"]["metadata"])
            assert metadata.count(before) == 1
            adapters[index]["value"]["metadata"] = json.loads(metadata.replace(before, after))
    return {**baseline, "adapters": adapters}


DRIVER_BRIEF_BASELINE = approved_driver_brief_baseline(GROK_LANGUAGE_BASELINE)
RETIREMENT_11327_PATH = CAPACITY_FIXTURE / "routing-11327.json"
RETIREMENT_11327_DIGEST = "354f97d4d02d46a98b966e59aa64ff46f1ccc484ee44989ff9bf1d77aace9774"
PRE_RETIREMENT_INPUTS = {**GEMINI_INPUTS, **SEATS_OVERLAY["inputs"], **ARGON_OVERLAY["inputs"]}


def _drop_cooler_seat(refusal: str, seat: str) -> str:
    """Remove one exact cooler-list seat. Neighboring names such as grok-build stay."""
    marker = "Cooler seats from budget snapshot: "
    head, tail = refusal.split(marker, 1)
    seats, rest = tail.split(". Re-route", 1)
    items = [item.strip() for item in seats.split(",")]
    assert items.count(seat) == 1, seat
    items.remove(seat)
    return f"{head}{marker}{', '.join(items)}. Re-route{rest}"


def approved_retirement_11327_inputs(inputs):
    """Drop the parked Fable 5.1 default budget pin from the dispatch matrix."""
    return {
        **inputs,
        "dispatch": [row for row in inputs["dispatch"] if row["model"] != "claude-fable-5-1"],
    }


def approved_retirement_11327_baseline(baseline, inputs):
    """Apply #11327 last: park Fable 5.1, retire Kimi, and share the Grok/Cursor meter.

    The historical fixture bytes stay. This edits the catalog fields those ids
    own, drops only their removed dispatch pin, collapses the shared cooler
    meter, and refuses the Kimi launcher default.
    """
    assert hashlib.sha256(RETIREMENT_11327_PATH.read_bytes()).hexdigest() == RETIREMENT_11327_DIGEST
    fixture = json.loads(RETIREMENT_11327_PATH.read_text(encoding="utf-8"))
    catalog = deepcopy(baseline["catalog"])
    assert "usage_pools" not in catalog
    catalog["usage_pools"] = fixture["usage_pools"]
    for row in fixture["model_fields"]:
        model = catalog["models"][row["model"]]
        if row["before_missing"]:
            assert row["field"] not in model
        else:
            assert model[row["field"]] == row["before"], (row["model"], row["field"])
        model[row["field"]] = row["after"]
    endpoint = catalog["review_scheduler"]["endpoints"]["kimicc"]
    assert endpoint["models"] == fixture["kimicc_models"]["before"]
    endpoint["models"] = fixture["kimicc_models"]["after"]
    assert catalog["policy"]["notes"] == fixture["policy_notes"]["before"]
    catalog["policy"]["notes"] = fixture["policy_notes"]["after"]
    lane = fixture["remove_budget_pin"]["lane"]
    pin = fixture["remove_budget_pin"]["model"]
    assert pin in catalog["budget_substitution_models"][lane]
    del catalog["budget_substitution_models"][lane][pin]

    approval = deepcopy(baseline["approval"])
    assert approval["contract"] == fixture["approval_contract"]["before"]
    approval["contract"] = fixture["approval_contract"]["after"]

    assert len(inputs["dispatch"]) == len(baseline["dispatch"])
    dispatch = []
    for row_in, row in zip(inputs["dispatch"], baseline["dispatch"], strict=True):
        if row_in["model"] == pin:
            continue
        updated = deepcopy(row)
        refusal = (updated.get("value") or {}).get("refusal")
        if isinstance(refusal, str) and "Cooler seats from budget snapshot:" in refusal:
            drop = "grok" if row_in["agent"] == "cursor" else "cursor"
            updated["value"]["refusal"] = _drop_cooler_seat(refusal, drop)
        dispatch.append(updated)

    launchers = deepcopy(baseline["launchers"])
    for index, recorded in fixture["launcher_rows"].items():
        assert launchers[int(index)] == recorded["old"]
        launchers[int(index)] = recorded["new"]
    return {
        **baseline,
        "catalog": catalog,
        "approval": approval,
        "dispatch": dispatch,
        "launchers": launchers,
    }


def approved_review_usage_11449_baseline(baseline, inputs):
    """Remove usage ordering and non-Claude cap exclusions from approved receipts."""
    reviewer = deepcopy(baseline["reviewer"])
    for case, receipt in zip(inputs["reviewer"], reviewer, strict=True):
        value = receipt.get("value")
        if not isinstance(value, dict) or "trace" not in value:
            continue
        for candidate in [value["selected"], *value["trace"]]:
            if candidate is not None and candidate["selection_score"] is not None:
                score = candidate["selection_score"]
                assert len(score) == 8
                # Keep workload, in-flight counts, failures and the stable tie.
                candidate["selection_score"] = score[2:4] + score[5:]
        for candidate in value["trace"]:
            if candidate["route"] == "claude" or candidate["reason"] != (
                "quota bucket is near cap — automatic assignments are prohibited"
            ):
                continue
            assert candidate["name"] == "openai_frontier"
            record = case["routing_snapshot"]["agents"]["codex"]
            assert record["status"] == "near_cap" and record["health"] == {"healthy": True}
            assert candidate["capacity"]["near_cap"] and candidate["capacity"]["hard_reason"] is None
            # Reuse the already-approved same-input receipt without usage data.
            reference_case = {key: item for key, item in case.items() if key != "routing_snapshot"}
            reference = baseline["reviewer"][inputs["reviewer"].index(reference_case)]["value"]
            admitted = reference["selected"]
            assert admitted["name"] == candidate["name"] and admitted["status"] == "selected"
            value["selected"] = next(row for row in value["trace"] if row["status"] == "selected")
            value["selected"]["status"] = "eligible"
            for field in ("status", "reason", "suitability_rank"):
                candidate[field] = admitted[field]
            score = admitted["selection_score"]
            assert len(score) == 8
            candidate["selection_score"] = score[2:4] + score[5:]
            candidate["health"] = "healthy"
            value["selected"] = deepcopy(candidate)
            value["substitution_note"] = reference["substitution_note"]
    return {**baseline, "reviewer": reviewer}


def approved_native_grok_help_baseline(baseline):
    """Apply #11451's three shared help lines; keep all other receipt fields."""
    before = "  --                         Pass all remaining arguments verbatim to the provider CLI.\n"
    after = (
        before
        + "                             Native Grok drivers take prompt words before this separator;\n"
        "                             after it, only supported session options are accepted.\n"
        "                             For option-looking text, use a prompt such as 'Task: --flag'.\n"
    )
    launchers = deepcopy(baseline["launchers"])
    help_rows = (4, 9, 14, 19, 24, 29, 34, 39, 44, 49, 54, 59, 64, 69)
    assert tuple(i for i, row in enumerate(INPUTS["launchers"]) if row["variant"] == "help") == help_rows
    for index in help_rows:
        assert launchers[index]["stdout"].count(before) == 1
        assert "Native Grok drivers take prompt words" not in launchers[index]["stdout"]
        launchers[index]["stdout"] = launchers[index]["stdout"].replace(before, after)
    return {**baseline, "launchers": launchers}


PRE_BUDGET_PIN_BASELINE = approved_muse_seat_baseline(
    approved_agy_mode_baseline(approved_word_card_tool_baseline(DRIVER_BRIEF_BASELINE))
)
PRE_RETIREMENT_BASELINE = approved_budget_pin_baseline(PRE_BUDGET_PIN_BASELINE)
APPROVED_INPUTS = approved_retirement_11327_inputs(PRE_RETIREMENT_INPUTS)
PRE_REVIEW_USAGE_BASELINE = approved_native_grok_help_baseline(
    approved_retirement_11327_baseline(PRE_RETIREMENT_BASELINE, PRE_RETIREMENT_INPUTS)
)
APPROVED_BASELINE = approved_review_usage_11449_baseline(PRE_REVIEW_USAGE_BASELINE, APPROVED_INPUTS)


def test_review_usage_11449_overlay_changes_only_usage_exclusion_and_ordering():
    """Reject unrelated receipt drift, including operational or Claude-cap changes."""
    before = deepcopy(PRE_REVIEW_USAGE_BASELINE)
    original = deepcopy(before)
    after = approved_review_usage_11449_baseline(before, APPROVED_INPUTS)
    assert before == original
    assert after == APPROVED_BASELINE
    assert {k: v for k, v in after.items() if k != "reviewer"} == {
        k: v for k, v in before.items() if k != "reviewer"
    }
    changed = admitted = 0
    for case, old, new in zip(APPROVED_INPUTS["reviewer"], before["reviewer"], after["reviewer"], strict=True):
        if old == new:
            continue
        changed += 1
        assert old.keys() == new.keys() and old["exit_status"] == new["exit_status"]
        old, new = old["value"], new["value"]
        assert {k: v for k, v in old.items() if k not in {"selected", "trace", "substitution_note"}} == {
            k: v for k, v in new.items() if k not in {"selected", "trace", "substitution_note"}
        }
        newly_selected = False
        for prior, current in zip(old["trace"], new["trace"], strict=True):
            expected = deepcopy(prior)
            score = expected["selection_score"]
            if score is not None:
                expected["selection_score"] = score[2:4] + score[5:]
            if prior["status"] == "excluded" and current["status"] == "selected":
                admitted += 1
                newly_selected = True
                assert prior["name"] == "openai_frontier" and prior["route"] == "codex"
                assert prior["reason"] == "quota bucket is near cap — automatic assignments are prohibited"
                assert prior["capacity"]["near_cap"] and prior["capacity"]["hard_reason"] is None
                assert current["health"] == "healthy" and current["reason"] is None
                assert current["suitability_rank"] == {
                    "low": 1, "medium": 0, "high": 2 if case["review_profile"] == "infra" else 1, "critical": 0,
                }[new["resolved_risk"]]
                assert current["selection_score"] == [True, 0.0, [True, 0], [True, 0], "e0279cd4ab474a86717d52ddc8ea496d0fcf6eccab3d60917c1a68ba6db6cdeb"]
                for field in ("status", "reason", "health", "suitability_rank", "selection_score"):
                    expected[field] = current[field]
            elif prior["status"] == "selected" and current["status"] == "eligible":
                assert new["selected"]["name"] == "openai_frontier"
                expected["status"] = "eligible"
            assert current == expected
        assert new["selected"] == next((row for row in new["trace"] if row["status"] == "selected"), None)
        if newly_selected:
            assert new["substitution_note"] is None
        else:
            assert new["substitution_note"] == old["substitution_note"]
            expected = deepcopy(old["selected"])
            if expected is not None and expected["selection_score"] is not None:
                score = expected["selection_score"]
                expected["selection_score"] = score[2:4] + score[5:]
            assert new["selected"] == expected
    assert changed == 1152
    assert admitted == 24


def test_muse_seat_overlay_changes_only_unknown_seat_receipts():
    fixture = json.loads(MUSE_SEAT_PATH.read_bytes())
    assert set(fixture) == {"reviewer_fail_closed_reason_replacements"}
    replacements = fixture["reviewer_fail_closed_reason_replacements"]
    named = [index for row in replacements for index in row["rows"]]
    assert len(named) == len(set(named)) == 56
    before = approved_agy_mode_baseline(approved_word_card_tool_baseline(DRIVER_BRIEF_BASELINE))
    original = deepcopy(before)
    after = approved_muse_seat_baseline(before)
    assert before == original
    assert after == PRE_BUDGET_PIN_BASELINE
    assert {k: v for k, v in after.items() if k != "reviewer"} == {
        k: v for k, v in before.items() if k != "reviewer"
    }
    changed = [
        index for index, (old, new) in enumerate(zip(before["reviewer"], after["reviewer"], strict=True))
        if old != new
    ]
    assert changed == sorted(named)
    unnamed = set(range(len(before["reviewer"]))) - set(named)
    assert unnamed
    for index in unnamed:
        assert after["reviewer"][index] == before["reviewer"][index]
    for replacement in replacements:
        old_reason, new_reason = replacement["before"], replacement["after"]
        assert old_reason.startswith("unknown subject seat ")
        assert old_reason.count("kimi, pool, qwen") == 1
        assert new_reason == old_reason.replace("kimi, pool, qwen", "kimi, muse, pool, qwen")
        for index in replacement["rows"]:
            expected = deepcopy(before["reviewer"][index])
            assert expected["value"]["fail_closed_reason"] == old_reason
            expected["value"]["fail_closed_reason"] = new_reason
            assert after["reviewer"][index] == expected
    with pytest.raises(AssertionError):
        approved_muse_seat_baseline(after)

    # Exercise the final shared boundary, not just the adapter's overrides.
    import os
    from unittest.mock import MagicMock

    from scripts import delegate
    from scripts.agent_runtime import telemetry
    from scripts.agent_runtime.adapters.base import InvocationPlan
    from scripts.agent_runtime.env_sanitize import build_agent_env
    from scripts.review.model_catalog import activity_role_refusal

    with (
        patch.dict(os.environ, {"PATH": "/usr/bin", "HOME": "/nonexistent", "MUSE_OTHER": "drop"}, clear=True),
        patch("scripts.agent_runtime.agent_github_identity.resolve_agent_github_identity", return_value=None),
    ):
        env = build_agent_env(provider="muse", overrides={"MUSE_NO_AUTO_UPDATE": "1"})
        assert env["MUSE_NO_AUTO_UPDATE"] == "1"
        assert "MUSE_OTHER" not in env
        assert "MUSE_NO_AUTO_UPDATE" not in build_agent_env(
            provider="codex", overrides={"MUSE_NO_AUTO_UPDATE": "1"}
        )
        assert "MUSE_NO_AUTO_UPDATE" not in build_agent_env(
            provider="muse", overrides={"MUSE_NO_AUTO_UPDATE": "sk-not-a-real-key"}
        )

    for model in ("muse-wonder-full-1.0", "muse-spark-1.3"):
        for activity in ("review", "consult"):
            assert (activity_role_refusal(model, activity, load_model_catalog()) is None) == (
                model == "muse-wonder-full-1.0"
            )
        args = delegate.build_parser().parse_args([
            "dispatch", "--agent", "muse", "--model", model, "--task-id", "worker-contract",
            "--prompt", "fixture", "--mode", "read-only", "--research-role", "investigation",
        ])
        assert delegate._muse_dispatch_refusal(args) == (
            None if model == "muse-wonder-full-1.0" else "muse_execution_not_admitted"
        )
        args.research_role = "driver"
        assert delegate._muse_dispatch_refusal(args) == "muse_ordinary_worker_only"
        args.research_role = "investigation"
        args.model = "gpt-6.1-sol"
        assert delegate._muse_dispatch_refusal(args) == "muse_worker_model_refused"
        plan = InvocationPlan(
            cmd=["/fixture/muse", "exec", "--model", model, "--reasoning-effort", "high"],
            cwd=Path("/fixture/workspace"),
            metadata={"cli_version": "Muse Code 1.4.11 (1.4.11-R6667.1)"},
        )
        with patch.object(telemetry, "_ORIGINAL_SUBPROCESS_POPEN") as spawn:
            resolved = telemetry.resolve_invocation_telemetry(
                agent_name="muse", plan=plan, requested_model="wrong-request", requested_effort="low"
            )
            assert (resolved.model, resolved.effort, resolved.cli_version) == (model, "high", "1.4.11")
            plan.metadata.clear()
            assert telemetry.resolve_invocation_telemetry(
                agent_name="muse", plan=plan, requested_model=model, requested_effort="high"
            ).cli_version == "unknown"
            spawn.assert_not_called()
    process = MagicMock()
    process.returncode = 0
    process.communicate.return_value = ("Muse Code 1.4.11 (1.4.11-R6667.1)", "")
    with (
        patch.dict(os.environ, {
            "MUSE_NO_AUTO_UPDATE": "0", "GH_TOKEN": "sentinel-parent",
            "OPENAI_API_KEY": "sentinel-parent", "SSH_AUTH_SOCK": "/fixture/socket",
            "LD_PRELOAD": "/fixture/inject.so", "LU_PROBE_TOKEN": "sentinel-parent",
        }, clear=True),
        patch("scripts.agent_runtime.adapters.muse.require_muse_execution_model"),
        patch("scripts.agent_runtime.agent_github_identity.resolve_agent_github_identity") as identity,
        patch.object(telemetry, "_ORIGINAL_SUBPROCESS_POPEN", return_value=process) as spawn,
    ):
        resolved = telemetry.resolve_dispatch_start_telemetry(
            agent_name="muse", requested_model=None, requested_effort=None
        )
        assert (resolved.model, resolved.effort, resolved.cli_version) == ("muse-wonder-full-1.0", "high", "1.4.11")
        assert spawn.call_args.args[0] == ["muse", "--version"]
        assert spawn.call_args.kwargs["env"] == {"MUSE_NO_AUTO_UPDATE": "1"}
        identity.assert_not_called()
        process.returncode = 1
        assert telemetry.resolve_dispatch_start_telemetry(
            agent_name="muse", requested_model=None, requested_effort=None
        ).cli_version == "unknown"
    with patch.object(telemetry, "_ORIGINAL_SUBPROCESS_POPEN", side_effect=OSError("unavailable")):
        assert telemetry.resolve_dispatch_start_telemetry(
            agent_name="muse", requested_model=None, requested_effort=None
        ).cli_version == "unknown"



@pytest.mark.parametrize("configuration", ("host-cli", "no-cli"))
def test_agy_mode_overlay_changes_only_authoring_mode_and_mcp_metadata(configuration):
    path = FIXTURE / ("baseline.json.gz" if configuration == "host-cli" else "no-cli/baseline.json.gz")
    before = json.loads(gzip.decompress(path.read_bytes()))
    original = deepcopy(before)
    after = approved_agy_mode_baseline(before)
    assert before == original
    assert {k: v for k, v in after.items() if k != "adapters"} == {k: v for k, v in before.items() if k != "adapters"}
    changed = [i for i, (old, new) in enumerate(zip(before["adapters"], after["adapters"], strict=True)) if old != new]
    assert changed == AGY_AUTHORING_ROWS
    assert [i for i, row in enumerate(INPUTS["adapters"]) if row["agent"] == "agy" and not row["isolation"]] == changed
    for index in changed:
        old, new = before["adapters"][index], after["adapters"][index]
        expected = deepcopy(old)
        expected["value"]["cmd"][1:1] = ["--mode", "auto"]
        expected["value"]["metadata"]["agy_mcp_config_path"] = "<CAPTURE_ROOT>/home/.gemini/config/mcp_config.json"
        assert new == expected
    assert [i for i, row in enumerate(INPUTS["adapters"]) if row["agent"] == "agy" and row["isolation"]] == AGY_REVIEW_ROWS
    for index in AGY_REVIEW_ROWS:
        assert after["adapters"][index] == before["adapters"][index]
        assert APPROVED_BASELINE["adapters"][index] == before["adapters"][index]
        assert "--mode" not in after["adapters"][index].get("value", {}).get("cmd", [])
    with pytest.raises(AssertionError):
        approved_agy_mode_baseline(after)


def test_retirement_11327_overlay_is_limited_to_fable_kimi_and_the_shared_meter():
    """#11327 parks Fable, retires five Kimi ids, and shares the Grok/Cursor meter."""
    before = deepcopy(PRE_RETIREMENT_BASELINE)
    after = approved_retirement_11327_baseline(deepcopy(before), PRE_RETIREMENT_INPUTS)
    untouched = set(before) - {"catalog", "approval", "dispatch", "launchers"}
    for surface in untouched:
        assert before[surface] == after[surface], surface
    old_models, new_models = before["catalog"]["models"], after["catalog"]["models"]
    assert {mid for mid in old_models if old_models[mid] != new_models[mid]} == {
        "claude-fable-5-1",
        "kimi-code/k3",
        "kimi-code/k3-256k",
        "kimi-code/kimi-for-coding",
        "kimi-code/kimi-for-coding-highspeed",
        "kimi-k3-max",
    }
    assert new_models["claude-fable-5"] == old_models["claude-fable-5"]
    assert new_models["claude-fable-5-1"] == {**old_models["claude-fable-5-1"], "transports": ["native_claude"]}
    assert new_models["claude-fable-5-1"]["lifecycle"] == "active"
    assert new_models["claude-fable-5-1"]["transports"] == ["native_claude"]
    assert all(new_models[mid]["lifecycle"] == "retired" and new_models[mid]["transports"] == [] for mid in (
        "kimi-code/k3",
        "kimi-code/k3-256k",
        "kimi-code/kimi-for-coding",
        "kimi-code/kimi-for-coding-highspeed",
        "kimi-k3-max",
    ))
    assert after["catalog"]["usage_pools"] == {"grok_cursor": {"seats": ["grok", "cursor"]}}
    assert "claude-fable-5-1" not in after["catalog"]["budget_substitution_models"]["cursor"]
    assert set(before["catalog"]["budget_substitution_models"]["cursor"]) - {"claude-fable-5-1"} == set(
        after["catalog"]["budget_substitution_models"]["cursor"]
    )
    removed = [
        row for row in PRE_RETIREMENT_INPUTS["dispatch"] if row["model"] == "claude-fable-5-1"
    ]
    assert removed and len(after["dispatch"]) == len(before["dispatch"]) - len(removed)
    kept = [
        (row_in, old, new)
        for row_in, old, new in zip(
            [row for row in PRE_RETIREMENT_INPUTS["dispatch"] if row["model"] != "claude-fable-5-1"],
            [old for row_in, old in zip(PRE_RETIREMENT_INPUTS["dispatch"], before["dispatch"], strict=True) if row_in["model"] != "claude-fable-5-1"],
            after["dispatch"],
            strict=True,
        )
    ]
    changed = [(row_in, old, new) for row_in, old, new in kept if old != new]
    assert len(changed) == 33
    for row_in, old, new in changed:
        assert {key: value for key, value in old.items() if key != "value"} == {
            key: value for key, value in new.items() if key != "value"
        }
        assert {key: value for key, value in old["value"].items() if key != "refusal"} == {
            key: value for key, value in new["value"].items() if key != "refusal"
        }
        dropped = "grok" if row_in["agent"] == "cursor" else "cursor"
        assert new["value"]["refusal"] == _drop_cooler_seat(old["value"]["refusal"], dropped)
        assert row_in["model"] != "claude-fable-5-1"
    launcher_changed = [
        index for index, (old, new) in enumerate(zip(before["launchers"], after["launchers"], strict=True)) if old != new
    ]
    assert launcher_changed == [50, 55]
    assert after["approval"]["rows"] == before["approval"]["rows"]
    assert after["approval"]["holders"] == before["approval"]["holders"]
    assert "Fable 5.1 is parked: not routed by default, explicit pin only;" in after["approval"]["contract"]
    with pytest.raises(AssertionError):
        approved_retirement_11327_baseline(after, PRE_RETIREMENT_INPUTS)


@pytest.mark.parametrize("configuration", ("host-cli", "no-cli"))
def test_budget_pin_overlay_changes_only_exhausted_unmapped_claude_refusals(configuration):
    path = FIXTURE / ("baseline.json.gz" if configuration == "host-cli" else "no-cli/baseline.json.gz")
    before = approved_reviewer_seats_baseline(json.loads(gzip.decompress(path.read_bytes())))
    original = deepcopy(before)
    after = approved_budget_pin_baseline(before)
    assert before == original
    assert set(after) == set(before)
    assert {k: v for k, v in after.items() if k != "dispatch"} == {
        k: v for k, v in before.items() if k != "dispatch"
    }
    changed = [i for i, (old, new) in enumerate(zip(before["dispatch"], after["dispatch"], strict=True)) if old != new]
    models = {
        62: "claude-sonnet-5-5", 66: "claude-fable-5-1", 70: "composer-2.5",
        82: "grok-4.7", 86: "unregistered-model",
    }
    assert changed == list(models)
    fixture = json.loads((CAPACITY_FIXTURE / "budget-pin-11110.json").read_bytes())
    assert set(fixture) == {"dispatch_refusal_replacements"}
    assert [r["rows"] for r in fixture["dispatch_refusal_replacements"]] == [[i] for i in models]
    for index, model in models.items():
        assert PRE_RETIREMENT_INPUTS["dispatch"][index] == {
            "agent": "claude", "budget_status": "near_cap", "model": model, "review_attempt": None,
        }
        old, new = before["dispatch"][index], after["dispatch"][index]
        expected = deepcopy(old)
        expected["value"]["refusal"] = (
            "BUDGET_PINNED_MODEL_EXHAUSTED: --agent claude is exhausted/near_cap "
            f"(unknown; near_cap (>90% used on FRESH snapshot)); explicit --model {model} has no mapping "
            "accepted by --agent codex. Supported remedies: wait for reset, request a mapped model, "
            "or select the other Claude account label where policy permits. Refusing before spawn."
        )
        assert new == expected
    # Historical input rows 86/90 become 74/78 after the existing seat overlay.
    for historical, index in ((86, 74), (90, 78)):
        assert PRE_RETIREMENT_INPUTS["dispatch"][index] == INPUTS["dispatch"][historical]
        assert after["dispatch"][index] == before["dispatch"][index]


def test_budget_pin_overlay_refuses_drifted_refusal():
    drifted = deepcopy(PRE_BUDGET_PIN_BASELINE)
    drifted["dispatch"][62]["value"]["refusal"] = "unapproved refusal"
    with pytest.raises(AssertionError):
        approved_budget_pin_baseline(drifted)


@pytest.mark.parametrize("index,field", [(63, "refusal"), (62, "target")])
def test_budget_pin_overlay_still_rejects_other_dispatch_changes(index, field):
    actual = deepcopy(CURRENT_BASELINE)
    actual["dispatch"][index]["value"][field] = "unapproved change"
    with pytest.raises(AssertionError, match="current surface differs: dispatch"):
        assert_frozen_surfaces(actual)


@pytest.mark.parametrize("configuration", ("host-cli", "no-cli"))
def test_word_card_tool_overlay_adds_only_the_read_only_grant(configuration):
    """#11084 adds ``word_card`` to the two Codex read-only Sources grants and nothing else."""
    from scripts.agent_runtime.sources_read_only import sources_tool_sets

    path = FIXTURE / ("baseline.json.gz" if configuration == "host-cli" else "no-cli/baseline.json.gz")
    before = json.loads(gzip.decompress(path.read_bytes()))
    original = deepcopy(before)
    after = approved_word_card_tool_baseline(before)
    assert before == original
    assert {k: v for k, v in after.items() if k != "adapters"} == {k: v for k, v in before.items() if k != "adapters"}
    changed = [i for i, (old, new) in enumerate(zip(before["adapters"], after["adapters"], strict=True)) if old != new]
    assert changed == WORD_CARD_TOOL_ROWS
    read_only = list(sources_tool_sets()[0])
    assert "word_card" in read_only
    for index in changed:
        assert INPUTS["adapters"][index] == {
            "agent": ("codex", "codex-desktop")[changed.index(index)],
            "isolation": False,
            "mode": "read-only",
        }
        old, new = before["adapters"][index], after["adapters"][index]
        assert {k: v for k, v in old.items() if k != "value"} == {k: v for k, v in new.items() if k != "value"}
        assert {k: v for k, v in old["value"].items() if k != "cmd"} == {
            k: v for k, v in new["value"].items() if k != "cmd"
        }
        old_cmd, new_cmd = old["value"]["cmd"], new["value"]["cmd"]
        tokens = [k for k, (a, b) in enumerate(zip(old_cmd, new_cmd, strict=True)) if a != b]
        assert [old_cmd[k].split("=", 1)[0] for k in tokens] == [
            "mcp_servers.sources.enabled_tools",
            "mcp_servers.sources.tools",
        ]
        enabled, approvals = (new_cmd[k].split("=", 1)[1] for k in tokens)
        assert json.loads(enabled) == read_only
        assert json.loads(enabled) == sorted([*json.loads(old_cmd[tokens[0]].split("=", 1)[1]), "word_card"])
        assert approvals == "{" + ",".join(f'{name}={{approval_mode="approve"}}' for name in read_only) + "}"


def test_grok_ukrainian_role_confers_no_ukrainian_review_route():
    """The catalog role is descriptive: no Grok review route lists the ukrainian profile (#10835)."""
    source = Path(__file__).resolve().parents[2]
    catalog = yaml.safe_load((source / "scripts/config/model_catalog.yaml").read_text(encoding="utf-8"))
    assert "ukrainian_review" in catalog["models"]["grok-4.7"]["roles"]
    xai = [seat for seat in catalog["seats"].values() if seat.get("model_id") == "grok-4.7"]
    assert xai, "grok-4.7 reviewer seat missing"
    routes = [route for candidate in xai for route in candidate["routes"].values()]
    assert {route["transport"] for route in routes} == {"native_grok", "cursor"}
    for route in routes:
        assert route["review_profiles"] == ["code", "infra"]


def guard_policy(settings):
    return [
        (group["matcher"], Path(hook["command"]).name, hook["timeout"], hook.get("onFailure"))
        for group in settings["hooks"]["PreToolUse"]
        for hook in group["hooks"]
    ]


@pytest.mark.parametrize("configuration", ("host-cli", "no-cli"))
def test_hook_failure_overlay_changes_only_worker_guard_settings(configuration):
    path = FIXTURE / ("baseline.json.gz" if configuration == "host-cli" else "no-cli/baseline.json.gz")
    before = json.loads(gzip.decompress(path.read_bytes()))
    original = deepcopy(before)
    after = approved_hook_failure_baseline(before)
    assert before == original
    assert {k: v for k, v in after.items() if k != "adapters"} == {k: v for k, v in before.items() if k != "adapters"}
    changed = [i for i, (old, new) in enumerate(zip(before["adapters"], after["adapters"], strict=True)) if old != new]
    assert changed == HOOK_FAILURE_ROWS
    assert [i for i, row in enumerate(before["adapters"]) if "--settings" in row.get("value", {}).get("cmd", [])] == (
        HOOK_FAILURE_ROWS
    )
    source = json.loads((Path(__file__).resolve().parents[2] / "agents_extensions/shared/settings.json").read_bytes())
    tracked = {name: (timeout, on_failure) for _, name, timeout, on_failure in guard_policy(source)}
    for index in changed:
        old, new = before["adapters"][index], after["adapters"][index]
        assert INPUTS["adapters"][index]["agent"] in {"claude", "claude-desktop", "claude-infra", "claude-monitor"}
        position = settings_index(old)
        old_cmd, new_cmd = old["value"]["cmd"], new["value"]["cmd"]
        assert old_cmd[:position] + old_cmd[position + 1 :] == new_cmd[:position] + new_cmd[position + 1 :]
        assert {k: v for k, v in old["value"].items() if k != "cmd"} == {
            k: v for k, v in new["value"].items() if k != "cmd"
        }
        assert {k: v for k, v in old.items() if k != "value"} == {k: v for k, v in new.items() if k != "value"}
        old_settings, new_settings = json.loads(old_cmd[position]), json.loads(new_cmd[position])
        assert {k: v for k, v in old_settings.items() if k != "hooks"} == {
            k: v for k, v in new_settings.items() if k != "hooks"
        }
        old_policy, new_policy = guard_policy(old_settings), guard_policy(new_settings)
        assert [row[:2] for row in old_policy] == [row[:2] for row in new_policy]
        assert {row[3] for row in old_policy} == {None}
        for matcher, name, timeout, on_failure in new_policy:
            assert (timeout, on_failure) == tracked[name], (matcher, name)
        assert [row[1] for row in new_policy if row[3] is None] == ["heal-core-bare.py"]


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
    assert "claude-fable-5-1" not in cursor
    assert catalog["models"]["claude-fable-5-1"]["lifecycle"] == "active"
    assert catalog["models"]["claude-fable-5-1"]["transports"] == ["native_claude"]
    assert "cursor" in catalog["models"]["claude-sonnet-5-5"]["transports"]


# Literal digests bind the #10205 Cursor wire pin and allowlist revision and
# the #10262 explicit AGY review-risk refusals in both configurations, and the #10630
# capture-driver account; see SPEC.md.
PINNED_DIGESTS = {
    "routing-10263.json.gz": "3385853a0070ab9a2f77e1fb40d9178ce195e44e7fd6b8c8245702ec529b7d16",
    "SHA256SUMS": "4cba22dff8338f75c8ae96b35119c3da2bea3b3d7d6418c49e466ddc0ddf73a8",
    "SPEC.md": "8d2e59acb08b7642874f6363d84cacea1c04a83a202f266b22b304c4f53c3e45",
    "baseline.json.gz": "2cf8945084c13d7ce0b55e98a91522e897baee5ba53648f21ec7ae7b66cdaa5d",
    "capture.py": "7571955c784ecf973931ba3b3a86c50bc4ee9f5bf2c2bdcfdbcbe096381222ea",
    "inputs.json": "4f9d9dd89acff3872a9e627a9627516c65b7e410da28464a4dda9105c0ec34b0",
    "no-cli/SHA256SUMS": "7e5b78a91bd237a012805983da7d40f854c9802eae969d0f5e4fabcc0d2afea8",
    "no-cli/baseline.json.gz": "d3b4e4776f701d3f1304a48de75c0e9bb1d488a1837000bb9113957eace9896d",
    "no-cli/inputs.json": "4f9d9dd89acff3872a9e627a9627516c65b7e410da28464a4dda9105c0ec34b0",
    "no-cli/occurrences.json.gz": "8ca9e434a36e330dab713ddcc8c2c368c18e31666ee18bef2de2505b15aa12c7",
    "occurrences.json.gz": "8ca9e434a36e330dab713ddcc8c2c368c18e31666ee18bef2de2505b15aa12c7",
}


def _is_direct_fixture_bytecode(root: Path, path: Path) -> bool:
    """True only for a regular ``__pycache__/*.pyc`` file directly under ``root``.

    Pytest's assertion rewriter writes that cache when ``capture.py`` is named
    on the command line (#10615). It is not fixture content. A symlink, a
    non-``.pyc`` name, and any nested cache stay visible to the pin.
    """
    relative = path.relative_to(root)
    if len(relative.parts) != 2:
        return False
    cache_name, name = relative.parts
    if cache_name != "__pycache__" or not name.endswith(".pyc"):
        return False
    return not path.is_symlink() and path.is_file()


def routing_fixture_pin_members(root: Path) -> set[str]:
    """Relative files the pin binds. Generated bytecode caches are omitted."""
    return {
        str(path.relative_to(root))
        for path in root.rglob("*")
        if path.is_file() and not _is_direct_fixture_bytecode(root, path)
    }


def assert_frozen_routing_fixture_pinned(root: Path) -> None:
    """Require every literal digest, and no other fixture content, under ``root``."""
    assert PINNED_DIGESTS
    members = routing_fixture_pin_members(root)
    missing = sorted(set(PINNED_DIGESTS) - members)
    extra = sorted(members - set(PINNED_DIGESTS))
    assert not missing and not extra, f"pin membership missing={missing} extra={extra}"
    for name, expected in PINNED_DIGESTS.items():
        actual = hashlib.sha256((root / name).read_bytes()).hexdigest()
        assert actual == expected, f"{name} pinned digest mismatch"


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
    inputs = json.loads((output / "inputs.json").read_bytes())
    assert_frozen_surfaces(actual, inputs=inputs)
    assert {
        **inputs,
        **{
            surface: [case for case in inputs[surface] if case in CURRENT_INPUTS[surface]]
            for surface in ("adapters", "dispatch", "reviewer", "roles")
        },
    } == CURRENT_INPUTS
    assert (
        hashlib.sha256((output / "occurrences.json.gz").read_bytes()).hexdigest()
        == _RETIREMENT_DATA["occurrences_sha256"]
    )


# The 2026-10-23 subscription retirement is a new capture. Prior approved
# overlays remain byte-pinned historical evidence above.
_RETIREMENT_CAPTURE = CAPACITY_FIXTURE / "routing-retirement-20261023.json.gz"
assert (
    hashlib.sha256(_RETIREMENT_CAPTURE.read_bytes()).hexdigest()
    == "024471fb8b0413f52b30788aa9c6961928720ae98c1e756336cbd41838155a59"
)
_RETIREMENT_DATA = json.loads(gzip.decompress(_RETIREMENT_CAPTURE.read_bytes()))
def dispatcher_catalog_baseline(value):
    """Apply C-2188 command changes without rewriting frozen receipts."""
    if isinstance(value, dict):
        result = {key: dispatcher_catalog_baseline(item) for key, item in value.items()}
        migrate_invocation = (
            result.get("transport") != "native_grok"
            and result.get("model_id", result.get("concrete_model")) not in {"gpt-6-luna", "gemini-3.8-flash-high"}
        )
        if "invocation" in result and migrate_invocation:
            result["invocation"] = result["invocation"].replace(
                "scripts/delegate.py dispatch", "scripts/dispatch.py dispatch"
            )
        if isinstance(result.get("argv"), list) and migrate_invocation:
            result["argv"] = ["scripts/dispatch.py" if arg == "scripts/delegate.py" else arg for arg in result["argv"]]
        return result
    if isinstance(value, list):
        return [dispatcher_catalog_baseline(item) for item in value]
    return value


CURRENT_BASELINE = dispatcher_catalog_baseline(_RETIREMENT_DATA["baseline"])
CURRENT_INPUTS = _RETIREMENT_DATA["inputs"]

MUSE_REVIEW_CANDIDATE = {
    "model_id": "muse-wonder-full-1.0", "route": "muse", "transport": "native_muse",
    "invocation": ".venv/bin/python scripts/dispatch.py dispatch --agent muse --model muse-wonder-full-1.0 --effort high",
    "review_profiles": ["code"], "capabilities": ["code_review"], "suitability_roles": ["routine_review"],
}
MUSE_REVIEW_ROLES = {"legacy_reviewers"}


def approved_muse_review_receipt(receipt, case):
    """Add Muse only when the frozen input explicitly pins its review seat."""
    receipt = deepcopy(receipt)
    value = receipt.get("value", {})
    if not value.get("trace") or case.get("pinned_candidate") != "muse":
        return receipt
    reason = None
    if case["review_profile"] != "code":
        reason = "review profile exclusion: muse supports ['code'], got 'infra'"
    elif case.get("required_capabilities"):
        reason = f"missing required capabilities: {sorted(case['required_capabilities'])}"
    elif case.get("isolation_required"):
        reason = "isolation required but candidate does not support process isolation"
    elif case.get("requested_role"):
        reason = f"missing required review role suitability: {case['requested_role']}"
    if value["resolved_risk"] == "high" and reason is None:
        reason = (
            "a formal review at high risk is performed only by gpt-6.1-sol, claude-opus-5-5, grok-4.7 "
            "(operator decisions #9538, #9769); got 'muse-wonder-full-1.0'"
        )
    if value["resolved_risk"] == "critical" and reason is None:
        reason = "missing required review role suitability: code/critical catalog suitability"
    if case["author_model"] == "muse-wonder-full-1.0" or case.get("author_family") == "meta":
        reason = "same family as author (meta) — cross-family review requires a different family"
    if "meta" in case.get("subject_families", []):
        reason = "subject exclusion: muse cannot review a change that governs its own boundary (subject family meta)"
    if "muse" in case.get("subject_seats", []):
        reason = "subject exclusion: muse cannot review a change that governs its own boundary (subject seat muse)"
    capacity = next(row["capacity"] for row in value["trace"] if row["route"] == "grok")
    muse = {
        "name": "muse", "concrete_model": "muse-wonder-full-1.0", "family": "meta",
        "route": "muse", "transport": "native_muse", "invocation": MUSE_REVIEW_CANDIDATE["invocation"],
        "quality_tier": "economical", "requires_silence_timeout": False,
        "status": "excluded" if reason else "eligible", "reason": reason, "health": None,
        "capacity": deepcopy(capacity), "suitability_rank": None if reason else (0 if value["resolved_risk"] == "low" else 3),
        "selection_score": None if reason else [
            True, 0.0, [True, 0], [True, 0],
            "33a1e7b3f2abbe7c82bf263cfe91582906416e24a954bec756da624ebd960f07",
        ], "credit": None,
    }
    value["trace"].append(muse)
    if not reason:
        muse["status"] = "selected"
        value["selected"] = deepcopy(muse)
        value["fail_closed_reason"] = None
        value["substitution_note"] = (
            f"explicit pressure override selected muse: {case['pressure_override_reason']}"
        )
    return receipt


def approved_muse_role_receipt(receipt, case):
    """Extend the frozen role envelope without granting runtime qualification."""
    receipt = deepcopy(receipt)
    if case["role"] not in MUSE_REVIEW_ROLES or "value" not in receipt:
        return receipt
    context = case["context"]
    exclusions = []
    if "meta" in context.get("excluded_families", []):
        exclusions.append("subject_family_excluded")
    if set(context.get("required_capabilities", [])) - {"code_review"}:
        exclusions.append("required_capability_missing")
    if context.get("isolation_required"):
        exclusions.append("isolation_required")
    if context.get("pinned_model") not in {None, "muse-wonder-full-1.0"}:
        exclusions.append("explicit_pin_mismatch")
    receipt["value"]["candidates"].append({
        "seat": "meta_reviewer", "route_name": "native", "model_id": "muse-wonder-full-1.0",
        "family": "meta", "route": "muse", "transport": "native_muse", "wire_id": "muse-wonder-full-1.0",
        "effort": "high", "argv": MUSE_REVIEW_CANDIDATE["invocation"].split(), "legacy_label": "muse",
        "decision_reference": "agents_extensions/shared/rules/model-assignment.md", "qualification_reference": None,
        "health": "unknown", "health_rank": 0, "health_provenance": {
            "snapshot_supplied": case.get("health") is not None, "normalized_key": None, "diagnostic": "HEALTH_UNKNOWN",
        }, "exclusion_reasons": exclusions,
    })
    return receipt



def assert_frozen_surfaces(actual, *, inputs=None, surfaces=None):
    """Permit only the ordered Muse worker/review entries and exact refusal receipts."""
    expected = deepcopy(CURRENT_BASELINE)
    if inputs is None and surfaces is None:
        assert actual.keys() == BASELINE.keys()
        for surface in BASELINE:
            assert actual[surface] == expected[surface], f"current surface differs: {surface}"
        assert len(actual["launchers"]) == len(BASELINE["launchers"]) == 70
        return
    workers = {
        "muse-wonder-full-1.0": {
            "family": "meta", "tier": "economical", "lifecycle": "active",
            "roles": ["coding", "standard_review", "routine_review"], "transports": ["native_muse"],
            "strengths": ["explicit_native_worker"],
            "weaknesses": ["worker_qualification_pending", "review_qualification_pending", "no_driver_authority"],
            "notes": "Explicit native coding and low/medium code-review seat under measurement. "
                     "Private inputs are allowed only with contributor mode off (operator order C-2401). "
                     "No driver, automatic fallback, Ukrainian or security-final authority. "
                     "Formal review only when chosen explicitly. "
                     "Catalog eligibility does not attest provider-origin identity or effective permissions.",
            "sources": ["https://dev.meta.ai/docs/muse-code"],
        },
        "muse-spark-1.3": {
            "family": "meta", "tier": "compatibility", "lifecycle": "hold",
            "roles": ["coding"], "transports": ["native_muse"],
            "strengths": ["explicit_native_worker"],
            "weaknesses": ["worker_qualification_pending", "no_review_or_approval_authority"],
            "notes": "Explicit delegate worker only. Spark cannot approve or review.",
            "sources": ["https://dev.meta.ai/docs/muse-code"],
        },
    }
    assert not workers.keys() & expected["catalog"]["models"].keys()
    expected["catalog"]["models"].update(workers)
    expected["catalog"]["review_candidates"]["muse"] = deepcopy(MUSE_REVIEW_CANDIDATE)
    expected["catalog"]["review_scheduler"]["endpoints"]["muse"] = {
        "formal_review_eligible": True, "models": ["muse-wonder-full-1.0"], "participant": "muse",
        "adapter_transport": "native_muse", "catalog_transport": "native_muse",
        "sealed_executable": "scripts/dispatch.py", "quota_bucket": "muse", "credential_bucket": "muse",
        "quota_limit": 1, "credential_limit": 1, "capacity_weight": 1.0,
    }
    holders = expected["routing_holders"]
    holders["seats"]["meta_reviewer"] = {
        "model_id": "muse-wonder-full-1.0", "wire_ids": {"native": "muse-wonder-full-1.0"},
    }
    for role in MUSE_REVIEW_ROLES:
        holders["roles"][role].append({
            "seat": "meta_reviewer", "route_name": "native", "model_id": "muse-wonder-full-1.0",
            "wire_id": "muse-wonder-full-1.0",
        })
    expected["registry"]["muse"] = {
        "adapter": "scripts.agent_runtime.adapters.muse:MuseAdapter",
        "default_model": "muse-wonder-full-1.0", "default_effort": "high",
        "cost_tier": "unknown", "capabilities": ["code_writing"],
        "cli_available": True, "bridge_spawnable": False, "resume_policy": "never",
    }
    # Additional authors still require both existing authorities, never self approval.
    approval_rows = expected["approval"]["rows"]
    template = [row for row in approval_rows if row["author"] == "gpt-6-luna"]
    assert len(template) == 9
    for model in workers:
        for row in template:
            assert row["required"] == expected["approval"]["holders"]
            approval_rows.append({**deepcopy(row), "author": model})
    approval_rows.sort(key=lambda row: row["author"])
    if inputs is not None:
        assert inputs.keys() == CURRENT_INPUTS.keys()
        additions = {
            "adapters": [
                {"agent": "muse", "mode": mode, "isolation": isolation}
                for mode in ("read-only", "workspace-write") for isolation in (False, True)
            ],
            "dispatch": [
                {"agent": "muse", "model": model, "budget_status": status, "review_attempt": review}
                for model in (None, "muse-wonder-full-1.0", "gpt-6-luna",
                              "gpt-6.1-sol", "grok-4.7", "unregistered-model")
                for status in ("cool", "near_cap") for review in (None, "frozen-review-attempt.yaml")
            ],
            "reviewer": [
                case
                for risk in ("low", "medium", "high", "critical") for profile in ("code", "infra")
                for case in (
                    *({"author_model": model, "risk": risk, "review_profile": profile} for model in workers),
                    {"author_model": "gpt-6.1-sol", "risk": risk, "review_profile": profile, "author_family": "meta"},
                    {"author_model": "gpt-6.1-sol", "risk": risk, "review_profile": profile, "subject_families": ["meta"]},
                    {"author_model": "gpt-6.1-sol", "risk": risk, "review_profile": profile, "subject_seats": ["muse"]},
                    {"author_model": "gpt-6.1-sol", "risk": risk, "review_profile": profile, "pinned_candidate": "muse"},
                    {"author_model": "gpt-6.1-sol", "risk": risk, "review_profile": profile,
                     "pinned_candidate": "muse", "pressure_override_reason": "frozen-input"},
                )
            ],
            "roles": [
                {"role": role, "purpose": "inspect", "context": context, "health": None}
                for role in CURRENT_BASELINE["routing_holders"]["roles"]
                for context in ({"excluded_families": ["meta"]}, {"excluded_seats": ["muse"]},
                                {"pinned_model": "muse-wonder-full-1.0"})
            ],
        }
        for surface, extra_cases in additions.items():
            reference = dict(zip(map(dispatch_key, CURRENT_INPUTS[surface]), expected[surface], strict=True))
            added = [case for case in inputs[surface] if dispatch_key(case) not in reference]
            assert sorted(map(dispatch_key, added)) == sorted(map(dispatch_key, extra_cases))
            assert [case for case in inputs[surface] if dispatch_key(case) in reference] == CURRENT_INPUTS[surface]
            rows = []
            for case in inputs[surface]:
                key = dispatch_key(case)
                if key in reference:
                    receipt = deepcopy(reference[key])
                    if surface == "dispatch":
                        receipt["stderr"] = receipt["stderr"].replace(
                            "--agent {codex,", "--agent\n                            {codex,"
                        ).replace(
                            "cursor,glm}", "cursor,glm,muse}"
                        ).replace("cursor, glm)", "cursor, glm, muse)")
                        refusal = receipt.get("value", {}).get("refusal")
                        if refusal and "Cooler seats from budget snapshot:" in refusal:
                            receipt["value"]["refusal"] = refusal.replace("kimi, qwen.", "kimi, muse, qwen.")
                elif surface == "adapters":
                    receipt = {"exit_status": 1, "exception": "ValueError", "error": "muse_delegate_worker_required",
                               "stdout": "", "stderr": ""}
                elif surface == "reviewer":
                    template_case = {k: v for k, v in case.items()
                                     if k not in {"subject_families", "author_family", "subject_seats", "pinned_candidate", "pressure_override_reason"}}
                    if case["author_model"] == "muse-wonder-full-1.0":
                        template_case["author_model"] = "deepseek-v4.1-flash"
                    elif case["author_model"] in workers:
                        template_case["author_model"] = "unknown"
                    elif "author_family" in case:
                        template_case["author_family"] = "anthropic"
                    receipt = deepcopy(reference[dispatch_key(template_case)])
                    reason = receipt["value"]["fail_closed_reason"]
                    if case["author_model"] == "muse-spark-1.3":
                        receipt["value"]["fail_closed_reason"] = reason.replace(
                            "author_model='unknown'", f"author_model='{case['author_model']}'"
                        )
                    elif "author_family" in case:
                        receipt["value"]["fail_closed_reason"] = reason.replace(
                            "author_family='anthropic'", "author_family='meta'"
                        )
                    elif case.get("pinned_candidate"):
                        value = receipt["value"]
                        value["selected"] = None
                        for row in value["trace"]:
                            if row["status"] == "selected":
                                row["status"] = "eligible"
                        value["fail_closed_reason"] = (
                            "explicit reviewer pin 'muse' failed a hard eligibility gate"
                            if case.get("pressure_override_reason") else
                            "explicit reviewer pin requires a non-empty pressure_override_reason"
                        )
                        if not case.get("pressure_override_reason"):
                            value["trace"], value["advisory"] = [], []
                elif surface == "roles":
                    receipt = deepcopy(reference[dispatch_key({**case, "context": {}})])
                else:
                    model = case["model"]
                    value = {"argv": None, "target": None, "refusal": None,
                             "routing": {"alias_note": None, "requested_agent": None, "substitution": None}}
                    if case["review_attempt"]:
                        if model == "gpt-6-luna":
                            peer = {**case, "agent": "codex"}
                            value = deepcopy(reference[dispatch_key(peer)]["value"])
                        else:
                            value["refusal"] = "REVIEW_TARGET_UNRESOLVED: review attempt target unreadable"
                    else:
                        value["routing"]["requested_agent"] = "muse"
                        if case["budget_status"] == "near_cap":
                            cooler = ", ".join(sorted(set(CURRENT_BASELINE["registry"]) - {"cursor"}))
                            value["refusal"] = (
                                "ROUTING REFUSED: --agent muse is near_cap (>90% used on FRESH snapshot) and "
                                "dispatch_fallbacks has no usable substitute. Cooler seats from budget snapshot: "
                                + cooler + ". Re-route (see `python -m scripts.fleet.capacity_pick`) or pass --force-agent."
                            )
                        else:
                            value["argv"] = ["--agent", "muse", *(["--model", model] if model else [])]
                            value["target"] = {"model": model, "reason": "explicit", "recipient": "muse"}
                    receipt = {"exit_status": 0, "stdout": "", "stderr": "", "value": value}
                if surface == "reviewer":
                    receipt = approved_muse_review_receipt(receipt, case)
                elif surface == "roles":
                    if case.get("context", {}).get("pinned_model") == "muse-wonder-full-1.0":
                        for row in receipt["value"]["candidates"]:
                            row["exclusion_reasons"].append("explicit_pin_mismatch")
                    receipt = approved_muse_role_receipt(receipt, case)
                rows.append(receipt)
            expected[surface] = rows
    else:
        for surface, overlay in (("reviewer", approved_muse_review_receipt), ("roles", approved_muse_role_receipt)):
            expected[surface] = [overlay(row, case) for row, case in zip(expected[surface], CURRENT_INPUTS[surface], strict=True)]
    assert actual.keys() == (BASELINE.keys() if surfaces is None else set(surfaces))
    if "catalog" in expected:
        expected["catalog"]["review_scheduler"]["endpoints"]["agy"]["sealed_executable"] = "scripts/dispatch.py"
    for surface in actual:
        assert actual[surface] == expected[surface], f"current surface differs: {surface}"
    if surfaces is None:
        assert len(actual["launchers"]) == len(BASELINE["launchers"]) == 70


def test_deepseek_flash_execution_requires_opencode():
    catalog = load_model_catalog()
    assert require_execution_model("deepseek-v4.1-flash", transport="opencode", catalog=catalog) == "deepseek-v4.1-flash"
    with pytest.raises(ModelCatalogError, match="requires the opencode transport"):
        require_execution_model("deepseek-v4.1-flash", transport="hermes", catalog=catalog)


@pytest.mark.parametrize("model_id", ["deepseek-v4-pro", "deepseek-v4-flash", "deepseek-other"])
def test_other_deepseek_execution_models_stay_refused(model_id):
    catalog = deepcopy(load_model_catalog())
    # Even an active new catalog entry cannot widen the operator's Flash-only order.
    if model_id == "deepseek-other":
        catalog["models"][model_id] = deepcopy(catalog["models"]["deepseek-v4.1-flash"])
    with pytest.raises(ModelCatalogError, match=r"retired|only deepseek-v4\.1-flash"):
        require_execution_model(model_id, transport="opencode", catalog=catalog)
    with pytest.raises(ModelCatalogError, match=r"retired|only deepseek-v4\.1-flash"):
        _require_routable_model(catalog["models"], model_id, "test execution reference")
