"""Frozen routing evidence with scoped, hash-pinned approved overlays."""

from __future__ import annotations

import gzip
import hashlib
import json
import pickle
import runpy
import shlex
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
cached_capture_reads = runpy.run_path(source + "/tests/review/test_model_catalog.py")["cached_capture_reads"]
sys.argv = sys.argv[1:]
capture = runpy.run_path(sys.argv[0])
original = capture["capture"]
def cached_capture(*args, **kwargs):
    # Enter only after main has installed its hermetic environment.
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
    changed = [index for index, (old, new) in enumerate(zip(BASELINE["launchers"], revised["launchers"], strict=True))
               if old != new]
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


# Apply literal paragraph edits last: a surface overlay such as #10291's Grok
# help revision must neither erase this wording nor have its other lines erased.
APPROVED_BASELINE = approved_claude_cap_baseline(approved_cursor_trailer_baseline(
    approved_launcher_canary_baseline({
        **REVIEW_CAPACITY_BASELINE, **GEMINI_OVERLAY["surfaces"], **RESOURCE_OVERLAY["surfaces"],
    })
))
APPROVED_INPUTS = {**INPUTS, **GEMINI_OVERLAY["inputs"]}


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
    before = approved_cursor_trailer_baseline(approved_launcher_canary_baseline({
        **approved_review_baseline(json.loads(gzip.decompress(path.read_bytes()))),
        **GEMINI_OVERLAY["surfaces"], **RESOURCE_OVERLAY["surfaces"],
    }))
    after = approved_claude_cap_baseline(before)
    assert {k: v for k, v in after.items() if k != "launchers"} == {k: v for k, v in before.items() if k != "launchers"}
    changed = [i for i, (old, new) in enumerate(zip(before["launchers"], after["launchers"], strict=True)) if old != new]
    assert changed == list(range(4, 70, 5))
    for index in changed:
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
        row["stdout"] = row["stdout"].replace(
            "Usage: ./start-grok-driver.sh [OPTIONS] [PROMPT ...] [-- PROVIDER_ARGS ...]",
            "Usage: ./start-grok-driver.sh [OPTIONS] [-- PROVIDER_ARGS ...]",
        ).replace(
            "Hermes (opt-in only):\n",
            "Native Grok driver:\n"
            "  Runs from the inspected checkout; positional prompts and subcommands are refused.\n\n"
            "Hermes (opt-in only):\n",
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
        removed = [row for row in expected["substitutions"]
                   if row["currently_uses"] == "linear_pipeline.invoke_writer(writer='claude-tools')"]
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
        "4b16188c215c068f232d4c11ddc661c6dc67788a762c8d4b5c691aad562a2ffe"
    )
    assert set(GEMINI_OVERLAY["surfaces"]) == {"catalog", "roles", "routing_holders", "reviewer"}
    assert set(GEMINI_OVERLAY["inputs"]) == {"roles", "reviewer"}
    def key(value):
        return json.dumps(value, sort_keys=True)
    for surface in ("roles", "reviewer"):
        new_inputs = {key(row) for row in APPROVED_INPUTS[surface]}
        assert all(key(row) in new_inputs for row in INPUTS[surface])
    receipts = dict(zip(map(key, APPROVED_INPUTS["reviewer"]), APPROVED_BASELINE["reviewer"], strict=True))
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
    "SHA256SUMS": "43c6936a6e4864a245e630af2286f63f9dabb1bbe70cd5a29bad16b46fdaba76",
    "SPEC.md": "958f43d7368d0552cbf1b5706df35da56cdc9408e4834e05bb0911754ae58455",
    "baseline.json.gz": "17e8448e163677920a9a6c7a357c84ea28eac2f7e65380cfe013dbb10d1dddc2",
    "capture.py": "4593850ca030a5e25fe7b0d09d629bc8014322a1c574070fb0b317e3bc368b3b",
    "inputs.json": "4f9d9dd89acff3872a9e627a9627516c65b7e410da28464a4dda9105c0ec34b0",
    "no-cli/SHA256SUMS": "7284c77ab0b02c2de844e407e37ff3eb55c56ed412521c98212d0d7309e406ba",
    "no-cli/baseline.json.gz": "c9be87f384a751f5c228e20fa10a283e2d4e495959d8fd82535f85217f298d31",
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


@pytest.mark.parametrize("entrypoint,args", [
    ("scripts/review/model_catalog.py", ["--resolve-role", "bounded_advisor"]),
    ("scripts/lint/lint_model_catalog.py", ["--as-of", "2026-10-07"]),
])
def test_direct_catalog_callers_without_repository_pythonpath(entrypoint, args, tmp_path):
    source = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [sys.executable, "-I", str(source / entrypoint), *args],
        cwd=tmp_path, capture_output=True, text=True, timeout=30,
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


def parser_guard_adapter_baseline(adapters, interpreter):
    """Account for the PR's three explicit parser-interpreter invocations only.

    The frozen capture remains byte-pinned. Every setting, hook target, timeout,
    argument and other adapter field still compares exactly.
    """
    expected = deepcopy(adapters)
    targets = {
        f"<SOURCE_ROOT>/agents_extensions/shared/hooks/guard-{name}.py"
        for name in ("admin-merge", "pr-merge", "branch-switch-in-main")
    }
    for row in expected:
        cmd = row.get("value", {}).get("cmd", [])
        if "--settings" not in cmd:
            continue
        index = cmd.index("--settings") + 1
        settings = json.loads(cmd[index])
        changed = 0
        for group in settings["hooks"]["PreToolUse"]:
            for hook in group["hooks"]:
                if hook["command"] in targets:
                    hook["command"] = interpreter + " " + hook["command"]
                    changed += 1
        assert changed == 3
        cmd[index] = json.dumps(settings, separators=(",", ":"))
    return expected


def parser_guard_interpreter():
    from scripts.common.repo_root import project_interpreter

    source = Path(__file__).resolve().parents[2]
    return shlex.quote(str(project_interpreter(source))).replace(str(source), "<SOURCE_ROOT>")


def assert_frozen_surfaces(actual):
    assert actual.keys() == BASELINE.keys()
    for surface in BASELINE:
        expected = APPROVED_BASELINE[surface]
        if surface == "adapters":
            expected = parser_guard_adapter_baseline(expected, parser_guard_interpreter())
        assert actual[surface] == expected, f"approved surface differs: {surface}"
    assert len(actual["launchers"]) == len(BASELINE["launchers"]) == 70


def test_capture_runner_activates_and_restores_scoped_caches(tmp_path):
    source = Path(__file__).resolve().parents[2]
    capture = tmp_path / "capture.py"
    capture.write_text('''from scripts import delegate
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
''')
    result = subprocess.run(
        [sys.executable, "-c", CAPTURE_RUNNER, str(capture), "--source-root", str(source)],
        cwd=tmp_path, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "caches active\ncaches restored\n"


@pytest.mark.parametrize("surface", BASELINE)
def test_fresh_capture_comparison_rejects_each_mutated_surface(surface):
    actual = deepcopy(APPROVED_BASELINE)
    actual["adapters"] = parser_guard_adapter_baseline(actual["adapters"], parser_guard_interpreter())
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
        policy_path.write_text(policy_text.replace("near_cap_remaining_pct: 10.0", f"near_cap_remaining_pct: {threshold}"))
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
    expected_baseline = approved_claude_cap_baseline(approved_cursor_trailer_baseline(
        approved_launcher_canary_baseline({
            **approved_review_baseline(original), **GEMINI_OVERLAY["surfaces"], **RESOURCE_OVERLAY["surfaces"],
        })
    ))
    expected_baseline["adapters"] = parser_guard_adapter_baseline(
        expected_baseline["adapters"], parser_guard_interpreter(),
    )
    assert actual == expected_baseline
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


@pytest.mark.parametrize("configuration", ["baseline.json.gz", "no-cli/baseline.json.gz"])
def test_parser_guard_adapter_delta_is_exact_and_preserves_frozen_inputs(configuration):
    frozen = json.loads(gzip.decompress((FIXTURE / configuration).read_bytes()))["adapters"]
    before = deepcopy(frozen)
    updated = parser_guard_adapter_baseline(frozen, "fixture-python")
    changed_rows = 0
    for old, new in zip(frozen, updated, strict=True):
        if old == new:
            continue
        changed_rows += 1
        cmd = new["value"]["cmd"]
        index = cmd.index("--settings") + 1
        settings = json.loads(cmd[index])
        changed_hooks = 0
        for group in settings["hooks"]["PreToolUse"]:
            for hook in group["hooks"]:
                words = shlex.split(hook["command"])
                if words[0] == "fixture-python":
                    assert len(words) == 2
                    assert Path(words[1]).name in {
                        "guard-admin-merge.py", "guard-pr-merge.py", "guard-branch-switch-in-main.py",
                    }
                    hook["command"] = words[1]
                    changed_hooks += 1
        assert changed_hooks == 3
        cmd[index] = json.dumps(settings, separators=(",", ":"))
        assert old == new
    assert changed_rows == 8
    assert frozen == before


@pytest.mark.parametrize("mutation", ["interpreter", "target", "arguments", "timeout", "missing-hook"])
def test_parser_guard_adapter_comparison_rejects_additional_drift(mutation):
    actual = deepcopy(APPROVED_BASELINE)
    actual["adapters"] = parser_guard_adapter_baseline(actual["adapters"], parser_guard_interpreter())
    row = next(row for row in actual["adapters"] if "--settings" in row.get("value", {}).get("cmd", []))
    cmd = row["value"]["cmd"]
    index = cmd.index("--settings") + 1
    settings = json.loads(cmd[index])
    hooks = settings["hooks"]["PreToolUse"][0]["hooks"]
    hook = next(hook for hook in hooks if "guard-pr-merge.py" in hook["command"])
    if mutation == "interpreter":
        words = shlex.split(hook["command"])
        hook["command"] = shlex.join(["foreign-python", *words[1:]])
    elif mutation == "target":
        hook["command"] = hook["command"].replace("guard-pr-merge.py", "foreign-guard.py")
    elif mutation == "arguments":
        hook["command"] += " --extra"
    elif mutation == "timeout":
        hook["timeout"] += 1
    else:
        hooks.remove(hook)
    cmd[index] = json.dumps(settings, separators=(",", ":"))
    with pytest.raises(AssertionError, match="approved surface differs: adapters"):
        assert_frozen_surfaces(actual)
