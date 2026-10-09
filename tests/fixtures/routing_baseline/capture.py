"""Provider-free capture for the #9302 contract and approved routing revisions.

Run in a fresh process: imports must come from --source-root, including its
runtime package. See SPEC.md for the pinned census and approved expectations.
"""

from __future__ import annotations

import argparse
import contextlib
import gzip
import hashlib
import importlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from dataclasses import asdict, is_dataclass
from datetime import UTC, datetime
from functools import lru_cache, partial
from pathlib import Path
from unittest.mock import patch
from urllib.parse import quote

import yaml

BASE_SHA = "dae3d752426d6c11c5dc82260ec07ae8164e7730"
EXECUTION_BASE_SHA = "0d98123470b5a6870512571d01590f3e3210b268"
FIXED_NOW = datetime(2026, 10, 6, 12, tzinfo=UTC)
CLI_VERSIONS = {
    "claude": "2.1.289 (Claude Code)",
    "agy": "1.2.10",
    **dict.fromkeys(("codex", "gemini", "grok", "opencode", "hermes", "cursor-agent", "kimi"), "1.0.0"),
}


def capture_environment(scratch, configuration="host-cli"):
    """Stage discovery/version inputs; never inherit installed agent binaries."""
    binary_root = scratch / "bin"
    binary_root.mkdir()
    # Only the tools used by the capture itself are real. Do not append the
    # system PATH: it may contain provider CLIs (including npx) on CI or locally.
    for name in ("bash", "git", "cat"):
        executable = shutil.which(name, path="/usr/bin:/bin")
        if executable is None:
            raise RuntimeError(f"capture requires system tool: {name}")
        (binary_root / name).symlink_to(executable)
    for name, version in CLI_VERSIONS.items() if configuration == "host-cli" else []:
        stub = binary_root / name
        stub.write_text(
            "#!/bin/sh\n"
            f"if [ \"$#\" = 1 ] && [ \"$1\" = --version ]; then printf '%s\\n' '{version}'; exit 0; fi\n"
            "printf '%s\\n' 'capture stub refuses provider execution' >&2\nexit 97\n"
        )
        stub.chmod(0o755)
    if configuration == "no-cli":
        stub = binary_root / "npx"
        stub.write_text(
            "#!/bin/sh\n"
            'if [ "$#" = 2 ] && '
            '[ "$1" = @anthropic-ai/claude-code@latest ] && [ "$2" = --version ]; '
            "then printf '%s\\n' '2.1.289 (Claude Code)'; exit 0; fi\n"
            "printf '%s\\n' 'capture stub refuses provider execution' >&2\nexit 97\n"
        )
        stub.chmod(0o755)
    (scratch / "home").mkdir()
    return {
        "PATH": str(binary_root),
        "HOME": str(scratch / "home"),
        "TMPDIR": str(scratch),
        "LU_MCP_SOURCES_LOG_DIR": str(scratch / "logs"),
        "LU_TASKS_DIR": str(scratch / "tasks"),
        "LC_ALL": "C.UTF-8",
        "TZ": "UTC",
        "PYTHONHASHSEED": "0",
    }


def plain(value):
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
    stdout, stderr = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        try:
            result = {"exit_status": 0, "value": plain(call())}
        except (Exception, SystemExit) as exc:
            result = {
                "exit_status": exc.code if isinstance(exc, SystemExit) else 1,
                "exception": type(exc).__name__,
                "error": str(exc),
            }
    return {**result, "stdout": stdout.getvalue(), "stderr": stderr.getvalue()}


def reviewer_inputs(catalog):
    authors = sorted(
        set(catalog["models"])
        | {alias for entry in catalog["models"].values() for alias in entry.get("aliases", [])}
        | {"claude", "codex", "cursor", "cursor:auto", "unknown", "cursor:grok-4.7-high"}
    )
    cases = []
    for risk in ("low", "medium", "high", "critical"):
        for profile in ("code", "infra"):
            for author in authors:
                cases.append({"author_model": author, "risk": risk, "review_profile": profile})
            common = {"author_model": "gpt-6.1-sol", "risk": risk, "review_profile": profile}
            for family in sorted({m["family"] for m in catalog["models"].values()}):
                cases.append({**common, "author_family": family})
                cases.append({**common, "subject_families": [family]})
            for seat in catalog["review_candidates"]:
                cases.append({**common, "subject_seats": [seat]})
                cases.append({**common, "pinned_candidate": seat})
                cases.append({**common, "pinned_candidate": seat, "pressure_override_reason": "frozen-input"})
            for extra in (
                {"isolation_required": True},
                {"required_capabilities": ["sealed_evidence"]},
                {"required_capabilities": ["unsupported"]},
                {"data_egress_policy": "local_interactive"},
                {"formal_review": False},
                {"requested_role": "critical_review"},
                {"owned_paths": ["scripts/agent_runtime/adapters/claude.py"]},
                {"author_families": ["openai", "anthropic"]},
            ):
                cases.append({**common, **extra})
            for status in (
                None,
                "unknown",
                "unavailable",
                "stale",
                "healthy",
                "degraded",
                "degraded_telemetry",
                "near_cap",
                "unhealthy",
            ):
                snapshot = None if status is None else {"claude": status, "codex": status}
                cases.append({**common, "routing_snapshot": snapshot})
                cases.append({**common, "routing_snapshot": {"missing-key": status or "healthy"}})
            for status, healthy, stale in (
                ("cool", True, False),
                ("unavailable", True, False),
                ("cool", False, False),
                ("near_cap", True, False),
                ("hot", True, True),
            ):
                cases.append(
                    {
                        **common,
                        "routing_snapshot": {
                            "agents": {"codex": {"status": status, "health": {"healthy": healthy}}},
                            "diagnostics": {"stale": stale},
                        },
                    }
                )
            for balance in (None, 0, 1):
                cases.append(
                    {
                        **common,
                        "author_model": "claude-opus-5-5",
                        "routing_snapshot": {
                            "agents": {
                                "codex": {
                                    "status": "near_cap",
                                    "health": {"healthy": True},
                                    "remaining_pct": 1,
                                    "freshness": "fresh",
                                    "age_s": 0,
                                    "credit_balance": balance,
                                    "fetched_at": FIXED_NOW.isoformat(),
                                }
                            },
                            "diagnostics": {"stale": False},
                        },
                    }
                )
    return cases


def approval_contract_rows(source, catalog):
    """Execute today's operator-contract truth table, not a PR 5 approval engine.

    There is no production approval evaluator at this base. Read the current
    checkout's wording and identities, and fail on a changed contract instead
    of hashing an old Git blob or inventing additional-family admission.
    """
    text = (source / "agents_extensions/shared/rules/operator-expectations.md").read_text()
    contract = text.split("12. **Advisor / operator approval gate", 1)[1].split("13. **", 1)[0]
    holders = re.findall(r"`((?:claude|gpt)-[^`]+)`", contract)
    assert len(holders) == 2 and len(set(holders)) == 2
    assert "the other's\n    approval completes it" in contract
    assert "needs both; if they disagree, the operator decides" in contract
    assert set(holders) <= set(catalog["models"])
    rows = []
    for author in sorted(catalog["models"]):
        required = [holder for holder in holders if holder != author]
        for left in ("absent", "approve", "dissent"):
            for right in ("absent", "approve", "dissent"):
                votes = dict(zip(holders, (left, right), strict=True))
                dissent = any(votes[h] == "dissent" for h in required)
                approved = all(votes[h] == "approve" for h in required)
                rows.append(
                    {
                        "author": author,
                        "required": required,
                        "votes": votes,
                        "self_approval_counts": False,
                        "outcome": "operator_disposition"
                        if dissent
                        else "approved"
                        if approved
                        else "missing_approval",
                    }
                )
    return {
        "evidence_kind": "current_tree_operator_contract_evaluation",
        "contract": contract,
        "holders": holders,
        "rows": rows,
    }


def capture(source, scratch, project_python):
    sys.path[:0] = [str(source), str(source / "scripts"), str(source / "packages/v4-runtime/src")]
    from scripts.fleet import credit_lane

    # Every row reads the same unchanged policy. Validate it with the real
    # reader once per argument set, without retaining it between captures or
    # bypassing any routing decision. Restore the reader even on failure.
    with patch.object(credit_lane, "load_policy", lru_cache(maxsize=None)(credit_lane.load_policy)):
        return _capture_surfaces(source, scratch, project_python)


def _capture_surfaces(source, scratch, project_python):
    from scripts.agent_runtime.registry import AGENTS
    from scripts.fleet import credit_lane
    from scripts.review.model_catalog import load_model_catalog
    from scripts.review.reviewer_resolver import ResolverInputs, resolve_reviewer

    catalog = load_model_catalog()
    # Ignore additive fields when comparing a migrated checkout to this fixture.
    legacy = {key: value for key, value in catalog.items() if key not in {"seats", "roles", "routing_schema_version"}}
    legacy["models"] = {
        model_id: {key: value for key, value in model.items() if key != "routing_wire_ids"}
        for model_id, model in legacy["models"].items()
    }
    cases = reviewer_inputs(legacy)
    outputs = {"catalog": legacy, "registry": plain(AGENTS), "reviewer": []}
    for case in cases:
        typed = dict(case)
        for key in ("required_capabilities", "subject_seats", "subject_families", "author_families"):
            if key in typed:
                typed[key] = frozenset(typed[key])
        if "owned_paths" in typed:
            typed["owned_paths"] = tuple(typed["owned_paths"])
        with (
            patch.object(
                credit_lane,
                "routing_facts",
                partial(credit_lane.routing_facts, now=FIXED_NOW, usage_dir=scratch / "usage"),
            ),
            patch.object(
                credit_lane, "published_credit_relief", partial(credit_lane.published_credit_relief, now=FIXED_NOW)
            ),
        ):
            outputs["reviewer"].append(observed(lambda typed=typed: resolve_reviewer(ResolverInputs(**typed))))

    from scripts.review.role_resolution import resolve_role

    outputs["routing_holders"] = {
        "schema_version": catalog["routing_schema_version"],
        "seats": {
            name: {
                "model_id": seat["model_id"],
                "wire_ids": {
                    r: catalog["models"][seat["model_id"]]["routing_wire_ids"][v["transport"]]
                    for r, v in seat["routes"].items()
                },
            }
            for name, seat in catalog["seats"].items()
        },
        "roles": {},
    }
    outputs["roles"] = []
    role_inputs = []
    for role in catalog["roles"]:
        outputs["routing_holders"]["roles"][role] = [
            {"seat": c.seat, "route_name": c.route_name, "model_id": c.model_id, "wire_id": c.wire_id}
            for c in resolve_role(role, purpose="inspect").candidates
        ]
        seen_role_inputs = set()
        for case in cases:
            context = {
                target: case[key]
                for key, target in (
                    ("required_capabilities", "required_capabilities"),
                    ("isolation_required", "isolation_required"),
                    ("subject_seats", "excluded_seats"),
                    ("subject_families", "excluded_families"),
                    ("data_egress_policy", "data_egress_policy"),
                )
                if key in case
            }
            # Reviewer pins are receipt labels. Role pins are explicit identities.
            pin = case.get("pinned_candidate")
            if pin in legacy["review_candidates"]:
                context["pinned_model"] = legacy["review_candidates"][pin]["model_id"]
            params = {"role": role, "purpose": "inspect", "context": context, "health": case.get("routing_snapshot")}
            fingerprint = encode(params)
            if fingerprint in seen_role_inputs:
                continue
            seen_role_inputs.add(fingerprint)
            role_inputs.append(params)

            def role_row(params=params):
                result = resolve_role(**params).to_dict()
                # The digest binds catalog bytes, which this migration changes.
                # Compare the complete resolved semantics in its separate envelope.
                result.pop("catalog_digest")
                return result

            outputs["roles"].append(observed(role_row))

    outputs["approval"] = approval_contract_rows(source, catalog)

    # Record the real credit reader over synthetic inputs, with a fixed clock
    # and an empty local usage directory (never live quota/account evidence).
    outputs["capacity"] = []
    capacity_inputs = []
    for status in (None, "unknown", "unavailable", "stale", "cool", "near_cap", "hot"):
        for stale in (False, True):
            for balance in (None, 0, 1):
                record = {
                    "status": status,
                    "health": {"healthy": True},
                    "remaining_pct": 5,
                    "freshness": "fresh",
                    "age_s": 0,
                    "credit_balance": balance,
                    "fetched_at": FIXED_NOW.isoformat(),
                }
                params = {
                    "lane": "codex",
                    "record": record,
                    "model": "gpt-6.1-sol",
                    "snapshot_metadata": {"stale": stale},
                }
                capacity_inputs.append(params)
                outputs["capacity"].append(
                    observed(
                        lambda params=params: credit_lane.routing_facts(
                            **params, now=FIXED_NOW, usage_dir=scratch / "usage"
                        )
                    )
                )

    from scripts import delegate

    dispatch_inputs = []
    outputs["dispatch"] = []
    fallbacks_path = source / "scripts/config/agent_fallback_substitutions.yaml"
    outputs["fallbacks"] = yaml.safe_load(fallbacks_path.read_text())
    for agent, entry in AGENTS.items():
        default = entry.get("default_model")
        canonical = legacy["models"].get(default, {})
        pins = list(
            dict.fromkeys(
                [
                    None,
                    default,
                    *canonical.get("aliases", [])[:1],
                    *sorted({pin for mapping in legacy["budget_substitution_models"].values() for pin in mapping}),
                    "unregistered-model",
                ]
            )
        )
        for pin in pins:
            for budget_status, review_attempt in (
                (status, attempt) for status in ("cool", "near_cap") for attempt in (None, "frozen-review-attempt.yaml")
            ):
                params = {
                    "agent": agent,
                    "model": pin,
                    "budget_status": budget_status,
                    "review_attempt": review_attempt,
                }
                dispatch_inputs.append(params)
                budget = {
                    "agents": {a: {"status": budget_status if a == agent else "cool"} for a in AGENTS},
                    "diagnostics": {"stale": False, "records_loaded": 5},
                }

                def admission(agent=agent, pin=pin, review_attempt=review_attempt):
                    args = delegate.build_parser().parse_args(
                        [
                            "dispatch",
                            "--agent",
                            agent,
                            "--task-id",
                            "frozen-9302",
                            "--prompt",
                            "fixture",
                            "--mode",
                            "read-only",
                            "--check-budget",
                            *(["--model", pin] if pin else []),
                            *(["--review-attempt", review_attempt] if review_attempt else []),
                        ]
                    )
                    routing = delegate._DispatchRouting()
                    refusal, target = delegate._admit_dispatch_target(
                        args,
                        agent=agent,
                        trees=None,
                        route=delegate._dispatch_route(
                            args, routing, language_lane=False, review_attempt=args.review_attempt
                        ),
                    )
                    return {
                        "refusal": refusal,
                        "target": plain(target),
                        "routing": plain(routing),
                        "argv": delegate._worker_route_argv(target) if target else None,
                    }

                with (
                    patch.object(delegate, "_fetch_routing_budget", return_value=budget),
                    patch.object(delegate, "_load_reset_reserve", return_value={}),
                    patch.object(delegate, "_credit_period_refusal", return_value=None),
                ):
                    outputs["dispatch"].append(observed(admission))

    # Adapter construction against staged CLIs: real lookup/version gates run,
    # but no provider invocation is executed. Unsupported isolation is retained.
    outputs["adapters"] = []
    adapter_inputs = []
    for agent, entry in AGENTS.items():
        for mode in ("read-only", "workspace-write"):
            for isolation in (False, True):
                params = {"agent": agent, "mode": mode, "isolation": isolation}
                adapter_inputs.append(params)

                def plan(entry=entry, mode=mode, isolation=isolation):
                    module, name = entry["adapter"].split(":")
                    adapter = getattr(importlib.import_module(module), name)()
                    built = adapter.build_invocation(
                        prompt="routing fixture",
                        mode=mode,
                        cwd=scratch,
                        model=entry.get("default_model"),
                        effort="high",
                        task_id="frozen-9302",
                        session_id=None,
                        tool_config={"review_isolation": True} if isolation else None,
                    )
                    return plain(built)

                with patch("uuid.uuid4", return_value=uuid.UUID(int=1)):
                    outputs["adapters"].append(observed(plan))

    launcher_inputs = []
    outputs["launchers"] = []
    for provider in ("claude", "codex", "gemini", "grok", "cursor", "kimi", "glm"):
        for mode in ("interactive", "driver"):
            for variant in ("default", "environment", "cli", "retired", "help"):
                launcher_inputs.append({"provider": provider, "mode": mode, "variant": variant})
                shell = """source "$1/scripts/lib/launcher_core.sh"
LC_ROOT="$1"; LC_DURABLE_HELPER_ROOT="$2"; LC_PROVIDER="$3"; LC_MODE="$4"
case "$5" in
 environment|cli) export LAUNCHER_MODEL=claude-opus-5-5 LAUNCHER_EFFORT=medium ;;
 retired) export LAUNCHER_MODEL=claude-fable-5 ;;
esac
launcher_defaults
case "$5" in
 cli) launcher_parse --model grok-4.7 --effort high ;;
 help) launcher_parse --help ;;
esac
launcher_normalize_model
launcher_normalize_effort
launcher_validate_driver_certification
printf '%s\\n' "$LC_MODEL" "$LC_EFFORT" "$LC_HARNESS" "$LC_ENDPOINT" "$LC_ISOLATE_CONFIG"
"""
                result = subprocess.run(
                    [
                        "bash",
                        "-c",
                        shell,
                        "capture",
                        str(source),
                        str(project_python.parents[2]),
                        provider,
                        mode,
                        variant,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                outputs["launchers"].append(
                    {"exit_status": result.returncode, "stdout": result.stdout, "stderr": result.stderr}
                )

    # Serving/hash/approval source contracts are byte-bound, not invented
    # executable designated-approval machinery (none exists at this base).
    tracked = (
        subprocess.check_output(["git", "ls-tree", "-rz", "--name-only", BASE_SHA], cwd=source, timeout=30)
        .decode()
        .split("\0")[:-1]
    )
    sources, ledger = {}, []
    identities = sorted(
        set(legacy["models"]) | {a for m in legacy["models"].values() for a in m.get("aliases", [])},
        key=len,
        reverse=True,
    )
    rx = re.compile(
        r"(?<![\w.-])(?:"
        + "|".join(re.escape(x) for x in identities)
        + r"|(?:claude-(?:opus|sonnet|fable|haiku)|gpt|gemini|grok)-[0-9][-0-9.a-z]*"
        + r"|Opus(?:[ -]+5\.5)?|Sol(?:[ -]+6\.1)?)(?![\w.-])"
    )
    for path in tracked:
        if path.startswith(("scripts/launchers/", "agents_extensions/codex-home/")) or path in {
            "scripts/lib/launcher_core.sh",
            "scripts/lib/rules_core.py",
            "agents_extensions/shared/rules/core.md",
            "agents_extensions/shared/rules/operator-expectations.md",
            "tests/test_rules_core_budget.py",
        }:
            raw = subprocess.check_output(["git", "show", f"{BASE_SHA}:{path}"], cwd=source, timeout=30)
            sources[path] = {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
    matches = subprocess.check_output(
        ["git", "grep", "-n", "-I", "-z", "-P", rx.pattern, BASE_SHA], cwd=source, timeout=60
    )
    for row in matches.decode("utf-8", errors="replace").splitlines():
        path, line_number, line = row.split("\0", 2)
        path = path.removeprefix(BASE_SHA + ":")
        for match in rx.finditer(line):
            if path.startswith((".claude/", ".codex/", ".agent/", ".gemini/")):
                disposition, purpose = "preserve_generated_consumer", "deploy from canonical source in PR 3"
            elif path.startswith("tests/"):
                disposition, purpose = (
                    "retain_fixture",
                    "test or historical identity evidence; occurrence-bound guard exception",
                )
            elif path.startswith(("docs/session-state/", "plans/", "docs/audit/")):
                disposition, purpose = (
                    "retain_provenance",
                    "frozen task/design/history evidence; occurrence-bound exception",
                )
            elif path.startswith("scripts/"):
                disposition, purpose = (
                    "migrate_live_selection",
                    "source-review required in PR 2/3/4; identity tables retain exact exceptions",
                )
            else:
                disposition, purpose = (
                    "regenerate_current_instructions",
                    "source-review in PR 3/4; preserve any proven historical occurrence",
                )
            ledger.append(
                {
                    "path": path,
                    "line": int(line_number),
                    "column": match.start() + 1,
                    "literal": match.group(),
                    "context_sha256": hashlib.sha256(line.encode()).hexdigest(),
                    "disposition": disposition,
                    "purpose": purpose,
                    "owner": "9302-infra-driver",
                }
            )
    outputs["source_contracts"] = sources
    manifest = {
        "schema": "routing-baseline-inputs.v1",
        "base_sha": BASE_SHA,
        "clock": FIXED_NOW.isoformat(),
        "execution_base_sha": EXECUTION_BASE_SHA,
        "roles": role_inputs,
        "reviewer": cases,
        "capacity": capacity_inputs,
        "dispatch": dispatch_inputs,
        "adapters": adapter_inputs,
        "launchers": launcher_inputs,
    }
    # Exactly enumerated capture roots; never model/reason/health normalization.
    serialized = encode(outputs).decode().replace(str(scratch), "<CAPTURE_ROOT>").replace(str(source), "<SOURCE_ROOT>")
    # Grok's session directory encodes cwd as a single URL-quoted component.
    serialized = serialized.replace(quote(str(scratch), safe=""), "<CAPTURE_ROOT_URLENCODED>")
    for index, row in enumerate(outputs["adapters"]):
        value = row.get("value", {})
        files = {
            "OUTPUT": value.get("output_file"),
            "LOG": value.get("env_overrides", {}).get("AGY_RUNTIME_LOG_FILE"),
            "WRITE_GUARD": value.get("metadata", {}).get("write_guard_agent_file"),
        }
        for kind, filename in files.items():
            if filename:
                normalized_file = filename.replace(str(scratch), "<CAPTURE_ROOT>").replace(str(source), "<SOURCE_ROOT>")
                serialized = serialized.replace(normalized_file, f"<ADAPTER_{kind}_{index}>")
    return serialized.encode(), encode(manifest), encode(ledger)


def main():
    parser = argparse.ArgumentParser(
        description="Capture routing baseline expectations without provider calls.\nUse only for fixture reproduction, not live routing or health probing.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Outputs: deterministic fixture files under --output. Exit codes: 0 captured; nonzero failed.\nRelated: SPEC.md; #9302.\nExample: capture.py --source-root SCRATCH_CHECKOUT --output FIXTURE_DIR",
    )
    parser.add_argument(
        "--configuration",
        choices=("host-cli", "no-cli"),
        default="host-cli",
        help="Fixed CLI discovery inputs; default: host-cli",
    )
    parser.add_argument("--source-root", type=Path, required=True, help="Checkout of the pinned base or approved routing revision")
    parser.add_argument("--output", type=Path, required=True, help="Destination directory for versioned fixture files")
    parser.add_argument("--project-python", type=Path, required=True, help="Task-prescribed shared project interpreter")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="routing-9302-", dir=os.environ["TMPDIR"]) as temporary:
        scratch = Path(temporary)
        safe_env = capture_environment(scratch, args.configuration)
        with patch.dict(os.environ, safe_env, clear=True):
            baseline, manifest, ledger = capture(args.source_root.resolve(), scratch, args.project_python)
        args.output.mkdir(parents=True, exist_ok=True)
        files = {
            "baseline.json.gz": gzip.compress(baseline, mtime=0),
            "inputs.json": manifest,
            "occurrences.json.gz": gzip.compress(ledger, mtime=0),
        }
        for name, data in files.items():
            (args.output / name).write_bytes(data)
        hashes = "".join(f"{hashlib.sha256(data).hexdigest()}  {name}\n" for name, data in files.items())
        (args.output / "SHA256SUMS").write_text(hashes)
        print(hashes, end="")
        print(f"reviewer_rows={len(json.loads(manifest)['reviewer'])} occurrences={len(json.loads(ledger))}")


if __name__ == "__main__":
    main()
