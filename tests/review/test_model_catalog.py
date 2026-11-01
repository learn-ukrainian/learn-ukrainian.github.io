"""Frozen routing evidence with scoped, hash-pinned approved overlays."""

from __future__ import annotations

import gzip
import hashlib
import io
import json
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from dataclasses import asdict, is_dataclass
from datetime import UTC, datetime
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
FIXED_NOW = datetime(2026, 10, 6, 12, tzinfo=UTC)


def plain(value):
    """Convert resolver values into stable JSON values without running a launcher."""
    if is_dataclass(value):
        return plain(asdict(value))
    if isinstance(value, dict):
        return {key: plain(item) for key, item in value.items()}
    if isinstance(value, (set, frozenset)):
        return sorted(plain(item) for item in value)
    if isinstance(value, (tuple, list)):
        return [plain(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def encode(value):
    return (json.dumps(plain(value), ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def observed(call):
    """Record a pure catalog/resolver call and its output streams."""
    stdout, stderr = io.StringIO(), io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        try:
            result = {"exit_status": 0, "value": plain(call())}
        except (Exception, SystemExit) as exc:
            result = {
                "exit_status": exc.code if isinstance(exc, SystemExit) else 1,
                "exception": type(exc).__name__,
                "error": str(exc),
            }
    return {**result, "stdout": stdout.getvalue(), "stderr": stderr.getvalue()}


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


# The ULIF tools became read-only when they stopped fetching and caching
# (ULIF local-copy order, 2026-10-28, PR #11918).
ULIF_LOCAL_TOOLS = ("query_ulif", "query_ulif_antonyms", "query_ulif_phraseology", "query_ulif_synonyms")


def approved_sources_tool_baseline(baseline):
    """Apply approved #11084 word-card, #9628 cached Wikipedia and #11918 local ULIF grants.

    Historical captures stay byte-pinned. Only the two Codex reader rows gain
    the explicitly approved tools; every other field and surface stays.
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
    for index in WORD_CARD_TOOL_ROWS:
        cmd = adapters[index]["value"]["cmd"]
        enabled = next(i for i, value in enumerate(cmd) if value.startswith("mcp_servers.sources.enabled_tools="))
        approvals = next(i for i, value in enumerate(cmd) if value.startswith("mcp_servers.sources.tools="))
        names = json.loads(cmd[enabled].split("=", 1)[1])
        assert not {"query_wikipedia_cached", *ULIF_LOCAL_TOOLS} & set(names)
        assert cmd[approvals] == "mcp_servers.sources.tools={" + ",".join(f'{name}={{approval_mode="approve"}}' for name in names) + "}"
        names = sorted([*names, "query_wikipedia_cached", *ULIF_LOCAL_TOOLS])
        cmd[enabled] = "mcp_servers.sources.enabled_tools=" + json.dumps(names)
        cmd[approvals] = "mcp_servers.sources.tools={" + ",".join(f'{name}={{approval_mode="approve"}}' for name in names) + "}"
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
    approved_agy_mode_baseline(approved_sources_tool_baseline(DRIVER_BRIEF_BASELINE))
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
    before = approved_agy_mode_baseline(approved_sources_tool_baseline(DRIVER_BRIEF_BASELINE))
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
def test_sources_tool_overlay_adds_only_approved_read_only_grants(configuration):
    """Only the approved word-card and cached Wikipedia grants alter the captured argv."""
    from scripts.agent_runtime.sources_read_only import sources_tool_sets

    path = FIXTURE / ("baseline.json.gz" if configuration == "host-cli" else "no-cli/baseline.json.gz")
    before = json.loads(gzip.decompress(path.read_bytes()))
    original = deepcopy(before)
    after = approved_sources_tool_baseline(before)
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
        assert json.loads(enabled) == sorted(
            [*json.loads(old_cmd[tokens[0]].split("=", 1)[1]), "word_card", "query_wikipedia_cached", *ULIF_LOCAL_TOOLS]
        )
        assert approvals == "{" + ",".join(f'{name}={{approval_mode="approve"}}' for name in read_only) + "}"


def test_grok_ukrainian_role_confers_no_ukrainian_review_route():
    """The catalog role is descriptive: no Grok review route lists the ukrainian profile (#10835)."""
    source = Path(__file__).resolve().parents[2]
    catalog = yaml.safe_load((source / "scripts/config/model_catalog.yaml").read_text(encoding="utf-8"))
    assert "ukrainian_review" in catalog["models"]["grok-4.7"]["roles"]
    xai = [seat for seat in catalog["seats"].values() if seat.get("model_id") == "grok-4.7"]
    assert xai, "grok-4.7 reviewer seat missing"
    routes = [route for candidate in xai for route in candidate["routes"].values()]
    assert {route["transport"] for route in routes} == {"cursor"}
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
        assert {"claude-opus-5-5", "grok-4.7-cursor-fallback"} <= on_ladder, risk
    for risk in ("low", "medium", "high", "critical"):
        routes = catalog["roles"][f"code_review_{risk}"]["routes"]
        assert "anthropic_authority/cursor_fallback" not in routes
        assert "xai_reviewer/cursor_fallback" in routes
    assert list(catalog["seats"]["anthropic_authority"]["routes"]) == ["native", "agy"]
    assert set(catalog["seats"]["xai_reviewer"]["routes"]) == {"cursor_fallback"}
    assert "transport_fallback_for" not in catalog["seats"]["xai_reviewer"]["routes"]["cursor_fallback"]
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
    "v2-baseline.json.gz": "399cf15d4a0efa36bff57c143a66638a085b792d069c38ccb07955c1dee068ab",
    "routing-10263.json.gz": "3385853a0070ab9a2f77e1fb40d9178ce195e44e7fd6b8c8245702ec529b7d16",
    "SHA256SUMS": "4cba22dff8338f75c8ae96b35119c3da2bea3b3d7d6418c49e466ddc0ddf73a8",
    "SPEC.md": "c0e7d80b83e40e32b230d0fe9baf6a168f32a5965636f1a22f6639421f55823f",
    "baseline.json.gz": "2cf8945084c13d7ce0b55e98a91522e897baee5ba53648f21ec7ae7b66cdaa5d",
    "inputs.json": "4f9d9dd89acff3872a9e627a9627516c65b7e410da28464a4dda9105c0ec34b0",
    "no-cli/SHA256SUMS": "7e5b78a91bd237a012805983da7d40f854c9802eae969d0f5e4fabcc0d2afea8",
    "no-cli/baseline.json.gz": "d3b4e4776f701d3f1304a48de75c0e9bb1d488a1837000bb9113957eace9896d",
    "no-cli/inputs.json": "4f9d9dd89acff3872a9e627a9627516c65b7e410da28464a4dda9105c0ec34b0",
    "no-cli/occurrences.json.gz": "8ca9e434a36e330dab713ddcc8c2c368c18e31666ee18bef2de2505b15aa12c7",
    "occurrences.json.gz": "8ca9e434a36e330dab713ddcc8c2c368c18e31666ee18bef2de2505b15aa12c7",
}


def _is_direct_fixture_bytecode(root: Path, path: Path) -> bool:
    """True only for a regular ``__pycache__/*.pyc`` file directly under ``root``.

    Generated test bytecode is not fixture content (#10615). A symlink, a
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


# The current fixture contains only the expanded catalog and the existing 1432
# reviewer cases. It was computed with pure resolver calls, without launching workers.
_V2_BASELINE_PATH = FIXTURE / "v2-baseline.json.gz"
assert hashlib.sha256(_V2_BASELINE_PATH.read_bytes()).hexdigest() == "399cf15d4a0efa36bff57c143a66638a085b792d069c38ccb07955c1dee068ab"
_V2_BASELINE = json.loads(gzip.decompress(_V2_BASELINE_PATH.read_bytes()))
CURRENT_BASELINE = _V2_BASELINE["baseline"]
CURRENT_INPUTS = _V2_BASELINE["inputs"]
# Gemini 3.8 Flash High is a general worker (#12291). The gzip fixture stays
# byte-identical; the loaded catalog drops the retired fallback block so frozen
# compares and re-validation match the live route keys.
CURRENT_BASELINE["catalog"]["execution_routing"]["sol_advised_bounded"].pop("bounded_fallback_worker")

MUSE_REVIEW_CANDIDATE = {
    "model_id": "muse-wonder-full-1.0", "route": "muse", "transport": "native_muse",
    "invocation": ".venv/bin/python scripts/dispatch.py dispatch --agent muse --model muse-wonder-full-1.0 --effort high",
    "review_profiles": ["code"], "capabilities": ["code_review"], "suitability_roles": ["routine_review"],
}
def _pop_budget_elevation_role(catalog):
    """Remove the elevated-tier grant role (cto-7923-adv-clog-sol, item 3b) and return what it added."""
    role = "review_budget_elevation"
    # The envelope role is the one advisory_roles entry of the bounded route; it is checked against the
    # route's advisor, not frozen here, and the elevation's frozen receipt stays what it was.
    envelope = catalog["advisory_roles"].pop("bounded_advisory_envelope")
    advisor = catalog["execution_routing"]["sol_advised_bounded"]["advisor"]
    assert (envelope["effort"], envelope["output_fields"]) == (advisor["effort"], advisor["output_fields"])
    catalog["review_scheduler"]["activity_roles"]["consult"].remove(role)
    holders = sorted(model_id for model_id, model in catalog["models"].items() if role in model["roles"])
    for model_id in holders:
        catalog["models"][model_id]["roles"].remove(role)
    entry = catalog["advisory_roles"].pop(role)
    # It is the only advisory role left once the envelope role is popped, so its key goes too.
    assert catalog.pop("advisory_roles") == {}
    return {"advisory_role": entry, "consult": role, "holders": holders}


def with_advisory_roles(frozen):
    """A frozen pre-advisory catalog plus the live ``advisory_roles`` section, its holders and consult roles.

    Validation requires the section (bounded admission reads the envelope role from it), so the
    historical pins are checked as the pin plus this overlay, and ``without_advisory_roles`` returns the pin.
    """
    live = load_model_catalog()
    catalog = deepcopy(frozen)
    catalog["advisory_roles"] = deepcopy(live["advisory_roles"])
    consult = catalog["review_scheduler"]["activity_roles"]["consult"]
    for role in catalog["advisory_roles"]:
        for model_id, model in live["models"].items():
            if role in model["roles"] and role not in catalog["models"][model_id]["roles"]:
                catalog["models"][model_id]["roles"].append(role)
        if role in live["review_scheduler"]["activity_roles"]["consult"] and role not in consult:
            consult.append(role)
    return catalog


def without_advisory_roles(catalog):
    """``with_advisory_roles`` undone: the frozen catalog the overlay was built from."""
    catalog = deepcopy(catalog)
    _pop_budget_elevation_role(catalog)
    return catalog


def assert_frozen_surfaces(actual, *, surfaces):
    """Compare surviving catalog/resolver results with the literal current fixture."""
    assert set(actual) == set(surfaces)
    for surface in surfaces:
        value = deepcopy(actual[surface])
        if surface == "catalog":
            # Assert the entire operator-approved exception before comparing every other field.
            if "red_team_only" in value["models"]["gpt-6-astra"]:
                assert hashlib.sha256(encode(value["models"]["gpt-6-astra"])).hexdigest() == "80bcd99f8ecf8e25423683302239e2cdb26e0ea48abdbcb5e7848d31e6a690a6"
                exception = value["review_candidates"].pop("openai_red_team_exception")
                assert hashlib.sha256(encode(exception)).hexdigest() == "ba9c4c63a08db1d9173ace99f6f6da2735f4e5c5402f305d24300c29fbde4a5c"
                endpoint = value["review_scheduler"]["endpoints"]["codex"]
                assert endpoint["models"] == ["gpt-6.1-sol", "gpt-6-astra"]
                endpoint["models"] = ["gpt-6.1-sol"]
                value["models"]["gpt-6-astra"] = deepcopy(CURRENT_BASELINE["catalog"]["models"]["gpt-6-astra"])
            # Carbon is held inventory only; every prior seat and route stays frozen.
            carbon = value["models"].pop("gemini-4-carbon")
            assert hashlib.sha256(encode(carbon)).hexdigest() == "5e7dd56ff656759fae9e85e0120c0eb74ae49ea78122db95c288ad3631c960b7"
            # The coder-only Terra addition leaves every frozen seat and review route intact.
            terra = value["models"].pop("gpt-6.1-terra")
            assert hashlib.sha256(encode(terra)).hexdigest() == "5f22691f96e42246fb4cca6a474c8d9dab1465a75ba720ed7bc153f2c47b3f9d"
            # The elevated-tier grant role is a consult role held by Sol and Opus; it moves no seat,
            # route or review ranking. It replaced the retired budget extension role.
            elevation = _pop_budget_elevation_role(value)
            assert hashlib.sha256(encode(elevation)).hexdigest() == "4a395379ef040f47f69be6badd96376bcbc1041d8698ff0703bc9209e399592d"
            # Muse operator decision 2026-11-01: low/medium review ladders and contributor mode off
            if ["muse"] in value["review_ladders"]["low"]:
                value["review_ladders"]["low"] = [m for m in value["review_ladders"]["low"] if m != ["muse"]]
            if ["muse"] in value["review_ladders"]["medium"]:
                value["review_ladders"]["medium"] = [m for m in value["review_ladders"]["medium"] if m != ["muse"]]
            muse_cand = value["review_candidates"]["muse"]
            assert "--contributor-mode off" in muse_cand["invocation"]
            assert "infra" in muse_cand["review_profiles"]
            value["review_candidates"]["muse"] = deepcopy(CURRENT_BASELINE["catalog"]["review_candidates"]["muse"])
            value["models"]["muse-wonder-full-1.0"]["notes"] = CURRENT_BASELINE["catalog"]["models"]["muse-wonder-full-1.0"]["notes"]
        assert value == CURRENT_BASELINE[surface], f"current surface differs: {surface}"


def refresh_current_baseline():
    """Recapture the existing cases with frozen time, no live usage, and no dispatches."""
    from functools import partial

    from scripts.fleet import credit_lane
    from scripts.review.reviewer_resolver import ResolverInputs, resolve_reviewer
    from scripts.review.role_resolution import expanded_legacy_view
    from tests.claude_route_accounts import HOST_ACCOUNT

    capture = deepcopy(_V2_BASELINE)
    catalog = plain(expanded_legacy_view())
    catalog["models"].pop("gemini-4-carbon")
    catalog["models"].pop("gpt-6.1-terra")
    _pop_budget_elevation_role(catalog)
    capture["baseline"]["catalog"] = catalog
    usage_dir = _V2_BASELINE_PATH.parent / ".recapture-no-live-usage"
    assert not usage_dir.exists()
    receipts = []
    with (
        patch("scripts.agent_runtime.model_pause.load_policy", return_value={}),
        patch.object(credit_lane, "routing_facts", partial(credit_lane.routing_facts, now=FIXED_NOW, usage_dir=usage_dir)),
        patch.object(credit_lane, "published_credit_relief", partial(credit_lane.published_credit_relief, now=FIXED_NOW)),
    ):
        for raw_case in capture["inputs"]["reviewer"]:
            case = deepcopy(raw_case)
            for key in ("required_capabilities", "subject_seats", "subject_families", "author_families"):
                if key in case:
                    case[key] = frozenset(case[key])
            if "owned_paths" in case:
                case["owned_paths"] = tuple(case["owned_paths"])
            receipts.append(observed(lambda case=case: resolve_reviewer(ResolverInputs(**case, claude_account=HOST_ACCOUNT))))
    capture["baseline"]["reviewer"] = receipts
    assert capture["inputs"] == _V2_BASELINE["inputs"]
    raw = gzip.compress(encode(capture), mtime=0)
    _V2_BASELINE_PATH.write_bytes(raw)
    print(json.dumps({"cases": len(receipts), "inputs_sha256": hashlib.sha256(encode(capture["inputs"])).hexdigest(),
                      "baseline_sha256": hashlib.sha256(raw).hexdigest()}))


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
