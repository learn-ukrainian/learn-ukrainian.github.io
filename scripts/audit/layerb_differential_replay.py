#!/usr/bin/env python3
"""Replay pinned QG groundings and prove Layer A extraction has no decision drift.

The tool serializes every ``AnchorResult`` field, including ``repr`` of the
float similarity, against a recorded BASE-SHA result set.  It intentionally
does not write generated audit artifacts into the repository: callers provide
explicit output paths (normally under ``/tmp``) and may commit only the pinned
test fixture produced with ``--write-expected``.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
from types import ModuleType
from typing import Any

# Direct script execution sets sys.path to scripts/audit rather than repository
# root; retain module execution compatibility without a launcher dependency.
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
for import_root in (REPOSITORY_ROOT / "scripts", REPOSITORY_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from scripts.audit import anchor_primitives, grounding_gate_v2

ANCHOR_RESULT_FIELDS = (
    "anchored",
    "abstained",
    "similarity",
    "source_index",
    "span",
    "reason",
    "anchor_low_signal_reason",
)
DEFAULT_EXPECTED_GROUNDINGS = 1_310


def _sha256_bytes(value: bytes) -> str:
    return sha256(value).hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _event_sort_key(event: Mapping[str, Any]) -> tuple[str, str, str, str, str]:
    """Pin a deterministic event order independently of JSON object order."""
    output = anchor_primitives.event_output_text(event) or ""
    return (
        anchor_primitives.canonical_tool_name(event.get("tool")),
        _canonical_json(event.get("input") if "input" in event else {}),
        str(event.get("status") or ""),
        _sha256_bytes(output.encode("utf-8")),
        str(event.get("tool_call_id") or ""),
    )


def _iter_groundings(artifacts_dir: Path) -> Iterable[tuple[str, Mapping[str, Any], tuple[Mapping[str, Any], ...]]]:
    """Yield fact-check groundings with fixed cell and event order."""
    for path in sorted(artifacts_dir.glob("*.json")):
        artifact = json.loads(path.read_text(encoding="utf-8"))
        payload = artifact.get("payload")
        dispatch = artifact.get("dispatch")
        if not isinstance(payload, Mapping) or not isinstance(dispatch, Mapping):
            continue
        fact_checks = payload.get("fact_checks")
        events = dispatch.get("tool_events")
        if not isinstance(fact_checks, list) or not isinstance(events, list):
            continue
        ordered_events = tuple(sorted((event for event in events if isinstance(event, Mapping)), key=_event_sort_key))
        for index, fact_check in enumerate(fact_checks):
            if not isinstance(fact_check, Mapping):
                continue
            grounding = fact_check.get("grounding")
            if isinstance(grounding, Mapping):
                yield f"{path.name}#fact_checks[{index}]", grounding, ordered_events


def _iter_fixture_groundings(
    fixtures_dir: Path,
) -> Iterable[tuple[str, Mapping[str, Any], tuple[Mapping[str, Any], ...]]]:
    """Make deterministic one-event replays for each source fixture."""
    for path in sorted(fixtures_dir.glob("*.json")):
        fixture = json.loads(path.read_text(encoding="utf-8"))
        passage = fixture.get("passage_md")
        slug = fixture.get("slug")
        if not isinstance(passage, str) or not isinstance(slug, str):
            continue
        event = {
            "tool": "sources_query_wikipedia",
            "input": {"query": slug},
            "output": passage,
            "status": "completed",
            "tool_call_id": f"fixture-{slug}",
        }
        grounding = {
            "tool": "sources_query_wikipedia",
            "query": slug,
            "evidence_excerpt": passage,
        }
        yield f"{path.name}#synthetic-passage", grounding, (event,)


def _iter_case_groundings(
    cases_path: Path,
) -> Iterable[tuple[str, Mapping[str, Any], tuple[Mapping[str, Any], ...]]]:
    """Load committed deterministic replay cases for focused CI probes."""
    document = json.loads(cases_path.read_text(encoding="utf-8"))
    cases = document.get("cases")
    if not isinstance(cases, list):
        raise ValueError("case fixture cases must be a list")
    for case in cases:
        if not isinstance(case, Mapping):
            continue
        key = case.get("key")
        grounding = case.get("grounding")
        events = case.get("events")
        if not isinstance(key, str) or not isinstance(grounding, Mapping) or not isinstance(events, list):
            continue
        ordered_events = tuple(sorted((event for event in events if isinstance(event, Mapping)), key=_event_sort_key))
        yield key, grounding, ordered_events


def _result_record(result: Any) -> dict[str, Any]:
    """Serialize all required fields without losing float identity."""
    payload = asdict(result)
    return {
        "anchored": payload["anchored"],
        "abstained": payload["abstained"],
        "similarity": repr(payload["similarity"]),
        "source_index": payload["source_index"],
        "span": list(payload["span"]) if payload["span"] is not None else None,
        "reason": payload["reason"],
        "anchor_low_signal_reason": payload["anchor_low_signal_reason"],
    }


def _load_gate_revision(revision: str) -> ModuleType:
    """Load the historical gate source without switching branches or worktrees."""
    source = subprocess.run(
        ["git", "show", f"{revision}:scripts/audit/grounding_gate_v2.py"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    module_name = f"_layerb_gate_{revision.replace('/', '_').replace('-', '_')}"
    spec = importlib.util.spec_from_loader(module_name, loader=None)
    if spec is None:
        raise RuntimeError(f"cannot create module spec for revision {revision}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    exec(compile(source, f"<git:{revision}:grounding_gate_v2.py>", "exec"), module.__dict__)
    return module


def _helper_hashes(revision: str | None) -> dict[str, str]:
    """Record source hashes used by this exact replay."""
    if revision is None:
        primitive_path = Path("scripts/audit/anchor_primitives.py")
        return {"anchor_primitives.py": _sha256_bytes(primitive_path.read_bytes())}
    source = subprocess.run(
        ["git", "show", f"{revision}:scripts/audit/grounding_gate_v2.py"],
        check=True,
        capture_output=True,
    ).stdout
    return {"grounding_gate_v2.py": _sha256_bytes(source)}


def replay_gate_results(
    artifacts_dir: Path | None = None,
    *,
    tau: float,
    gate_module: ModuleType = grounding_gate_v2,
    fixtures_dir: Path | None = None,
    cases_path: Path | None = None,
) -> list[dict[str, Any]]:
    """Replay all stored fact-check groundings through one gate implementation."""
    input_count = sum(path is not None for path in (artifacts_dir, fixtures_dir, cases_path))
    if input_count != 1:
        raise ValueError("provide exactly one replay input directory")
    if artifacts_dir is not None:
        iterator = _iter_groundings(artifacts_dir)
    elif fixtures_dir is not None:
        iterator = _iter_fixture_groundings(fixtures_dir)
    else:
        iterator = _iter_case_groundings(cases_path)
    records: list[dict[str, Any]] = []
    for grounding_key, grounding, events in iterator:
        # Pin mutable legacy module state at every isolated grounding replay.
        gate_module._last_search_truncated = False
        result = gate_module.anchor_evidence_to_events(grounding, events, tau=tau)
        records.append({"grounding_key": grounding_key, "anchor_result": _result_record(result)})
    return records


def _comparison_failures(expected: Sequence[Mapping[str, Any]], actual: Sequence[Mapping[str, Any]]) -> list[str]:
    expected_by_key = {str(record["grounding_key"]): record["anchor_result"] for record in expected}
    actual_by_key = {str(record["grounding_key"]): record["anchor_result"] for record in actual}
    failures: list[str] = []
    if set(expected_by_key) != set(actual_by_key):
        failures.append(f"grounding key set differs: expected={len(expected_by_key)} actual={len(actual_by_key)}")
    for grounding_key in sorted(set(expected_by_key).intersection(actual_by_key)):
        expected_result = expected_by_key[grounding_key]
        actual_result = actual_by_key[grounding_key]
        for field in ANCHOR_RESULT_FIELDS:
            if expected_result.get(field) != actual_result.get(field):
                failures.append(
                    f"{grounding_key} {field}: expected={expected_result.get(field)!r} "
                    f"actual={actual_result.get(field)!r}"
                )
                if len(failures) >= 20:
                    return failures
    return failures


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--artifacts-dir", type=Path)
    input_group.add_argument("--fixtures-dir", type=Path)
    input_group.add_argument("--cases", type=Path)
    parser.add_argument("--out", type=Path, required=True, help="Replay summary JSON path.")
    parser.add_argument("--expected", type=Path, help="Recorded BASE-SHA per-grounding results.")
    parser.add_argument("--write-expected", type=Path, help="Write a BASE-SHA expected result fixture.")
    parser.add_argument("--gate-revision", help="Read gate source from this git revision instead of HEAD worktree.")
    parser.add_argument("--tau", type=float, default=0.75)
    parser.add_argument("--expected-groundings", type=int, default=DEFAULT_EXPECTED_GROUNDINGS)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_dir = args.artifacts_dir or args.fixtures_dir or args.cases
    input_exists = input_dir.is_file() if args.cases else input_dir.is_dir()
    if not input_exists:
        print(f"ERROR replay input does not exist: {input_dir}", file=sys.stderr)
        return 2
    if bool(args.expected) == bool(args.write_expected):
        print("ERROR provide exactly one of --expected or --write-expected", file=sys.stderr)
        return 2
    gate_module = _load_gate_revision(args.gate_revision) if args.gate_revision else grounding_gate_v2
    records = replay_gate_results(
        args.artifacts_dir,
        fixtures_dir=args.fixtures_dir,
        cases_path=args.cases,
        tau=args.tau,
        gate_module=gate_module,
    )
    if len(records) != args.expected_groundings:
        print(
            f"ERROR expected {args.expected_groundings} groundings, replayed {len(records)}; refusing incomplete proof",
            file=sys.stderr,
        )
        return 3
    result_document = {
        "schema_version": "qg-layerb-anchor-differential.v1",
        "metadata": {
            "gate_revision": args.gate_revision or "WORKTREE_HEAD",
            "tau": args.tau,
            "groundings": len(records),
            "input_kind": "artifacts" if args.artifacts_dir else "fixtures" if args.fixtures_dir else "cases",
            "event_order": "canonical-tool,input,status,raw-output-sha256,tool-call-id",
            "last_search_truncated_initial": False,
            "helper_sha256": _helper_hashes(args.gate_revision),
        },
        "records": records,
    }
    if args.write_expected:
        args.write_expected.parent.mkdir(parents=True, exist_ok=True)
        args.write_expected.write_text(_canonical_json(result_document) + "\n", encoding="utf-8")
        summary = {
            "mode": "record-base",
            "groundings": len(records),
            "anchor_result_fields": list(ANCHOR_RESULT_FIELDS),
            "helper_sha256": result_document["metadata"]["helper_sha256"],
            "status": "PASS",
        }
    else:
        expected_document = json.loads(args.expected.read_text(encoding="utf-8"))
        expected_records = expected_document.get("records")
        if not isinstance(expected_records, list):
            print("ERROR expected fixture records is missing or malformed", file=sys.stderr)
            return 2
        failures = _comparison_failures(expected_records, records)
        summary = {
            "mode": "compare-head",
            "groundings": len(records),
            "anchor_result_fields": list(ANCHOR_RESULT_FIELDS),
            "helper_sha256": result_document["metadata"]["helper_sha256"],
            "compared_fields": len(records) * len(ANCHOR_RESULT_FIELDS),
            "mismatches": len(failures),
            "status": "PASS" if not failures else "FAIL",
            "failure_examples": failures,
        }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(_canonical_json(summary) + "\n", encoding="utf-8")
    print(
        "DIFFERENTIAL_REPLAY "
        f"mode={summary['mode']} status={summary['status']} groundings={summary['groundings']} "
        f"fields={len(ANCHOR_RESULT_FIELDS)} mismatches={summary.get('mismatches', 0)} "
        f"helper_sha256={_canonical_json(summary['helper_sha256'])}"
    )
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
