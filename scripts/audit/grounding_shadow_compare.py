#!/usr/bin/env python3
"""Grounding Gate Shadow Compare.

This script runs a read-only dual-run over stored bakeoff cell artifacts to
compare the admissibility/grounding results of the v1 exact substring match
gate vs. the v2 fuzzy provenance anchoring gate. It produces a JSON report
and a Markdown summary table.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Any

from scripts.audit import grounding_gate_v2
from scripts.audit.llm_reviewer_dispatch import (
    _event_output_text,
    _grounding_matches_events,
    _normalize_for_match,
    tool_events_from_dispatch_meta,
)
from scripts.audit.qg_bakeoff import (
    _artifact_arm_from_path,
    _is_bakeoff_cell,
    _match_rows_to_claims,
    load_fixtures,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dual-run grounding gates v1 vs v2 over bakeoff cells.")
    parser.add_argument(
        "--artifacts-dir",
        type=Path,
        required=True,
        help="Directory containing *.json bakeoff cell files.",
    )
    parser.add_argument(
        "--tau",
        type=float,
        default=None,
        help="Custom confidence threshold tau (overrides QG_GROUNDING_GATE_V2_TAU).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Output path. Generates path.json and path.md.",
    )
    parser.add_argument(
        "--fixtures-dir",
        type=Path,
        default=Path("tests/fixtures/qg_bakeoff"),
        help="Directory containing gold-labeled fixtures.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not args.artifacts_dir.is_dir():
        print(f"Error: Artifacts directory not found: {args.artifacts_dir}", file=sys.stderr)
        return 1

    tau = args.tau
    if tau is None:
        env_tau = os.environ.get("QG_GROUNDING_GATE_V2_TAU")
        if env_tau is not None:
            try:
                tau = float(env_tau)
            except ValueError:
                tau = grounding_gate_v2.DEFAULT_TAU
        else:
            tau = grounding_gate_v2.DEFAULT_TAU

    # Load fixtures
    fixtures = {}
    if args.fixtures_dir.is_dir():
        fixtures = {f.slug: f for f in load_fixtures(args.fixtures_dir)}
    else:
        print(f"Warning: Fixtures directory not found: {args.fixtures_dir}. False positive rates won't be calculated.", file=sys.stderr)

    records: list[dict[str, Any]] = []

    # Find and process all bakeoff cell json files
    for path in sorted(args.artifacts_dir.glob("*.json")):
        try:
            artifact = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"Warning: Failed to parse {path.name}: {exc}", file=sys.stderr)
            continue

        if not _is_bakeoff_cell(artifact):
            continue

        payload = artifact.get("payload") or {}
        dispatch_meta = artifact.get("dispatch") or {}
        slug = (artifact.get("fixture") or {}).get("slug")
        fixture = fixtures.get(slug) if isinstance(slug, str) else None
        arm = _artifact_arm_from_path(path, artifact)
        seat = artifact.get("seat") or artifact.get("model") or "unknown"

        events = tool_events_from_dispatch_meta(dispatch_meta)

        fact_checks = payload.get("fact_checks", [])
        if not isinstance(fact_checks, list):
            fact_checks = []

        row_to_claim = {}
        if fixture is not None:
            matched, _ = _match_rows_to_claims([dict(fc) for fc in fact_checks], fixture)
            for claim_id, row in matched.items():
                row_to_claim[id(row)] = claim_id

        for fc in fact_checks:
            if not isinstance(fc, Mapping):
                continue
            grounding = fc.get("grounding")
            if not isinstance(grounding, Mapping):
                continue

            claim_text = str(fc.get("claim") or "")
            excerpt_text = str(grounding.get("evidence_excerpt") or "")

            # Run v1
            v1_admissible = _grounding_matches_events(grounding, events)

            # Run v2
            res_v2 = grounding_gate_v2.anchor_evidence_to_events(grounding, events, tau=tau)
            v2_anchored = res_v2.anchored
            v2_abstained = res_v2.abstained
            similarity = res_v2.similarity

            tool_query_matched = False
            if res_v2.source_index is not None:
                tool_query_matched = grounding_gate_v2._tool_query_match(grounding, events[res_v2.source_index])

            best_span_preview = ""
            if res_v2.span is not None and res_v2.source_index is not None:
                out_text = _event_output_text(events[res_v2.source_index])
                if out_text is not None:
                    norm_out = _normalize_for_match(out_text)
                    best_span_preview = norm_out[res_v2.span[0]:res_v2.span[1]][:160]

            gold_is_true = None
            if (claim_id := row_to_claim.get(id(fc))) and fixture is not None:
                claim_obj = next((c for c in fixture.claims if c.claim_id == claim_id), None)
                if claim_obj is not None:
                    gold_is_true = claim_obj.is_true

            records.append({
                "fixture": slug or "unknown",
                "seat_arm": f"{seat}/{arm}",
                "claim": claim_text,
                "excerpt": excerpt_text,
                "v1_admissible": v1_admissible,
                "v2_anchored": v2_anchored,
                "v2_abstained": v2_abstained,
                "similarity": similarity,
                "tool_query_matched": tool_query_matched,
                "best_span_preview": best_span_preview,
                "gold_is_true": gold_is_true,
            })

    # Calculate statistics
    total = len(records)
    v1_count = sum(1 for r in records if r["v1_admissible"])
    v2_count = sum(1 for r in records if r["v2_anchored"])
    recovered = sum(1 for r in records if not r["v1_admissible"] and r["v2_anchored"])
    regressions = sum(1 for r in records if r["v1_admissible"] and not r["v2_anchored"])
    abstains = sum(1 for r in records if r["v2_abstained"])

    fp_total = sum(1 for r in records if r["gold_is_true"] is False)
    fp_count = sum(1 for r in records if r["gold_is_true"] is False and r["v2_anchored"])

    # Breakdown by seat_arm
    seat_stats = defaultdict(lambda: {"total": 0, "v1": 0, "v2": 0, "rec": 0, "reg": 0, "abs": 0})
    for r in records:
        sa = r["seat_arm"]
        seat_stats[sa]["total"] += 1
        if r["v1_admissible"]:
            seat_stats[sa]["v1"] += 1
        if r["v2_anchored"]:
            seat_stats[sa]["v2"] += 1
        if not r["v1_admissible"] and r["v2_anchored"]:
            seat_stats[sa]["rec"] += 1
        if r["v1_admissible"] and not r["v2_anchored"]:
            seat_stats[sa]["reg"] += 1
        if r["v2_abstained"]:
            seat_stats[sa]["abs"] += 1

    # Breakdown by fixture
    fixture_stats = defaultdict(lambda: {"total": 0, "v1": 0, "v2": 0, "rec": 0, "reg": 0, "abs": 0})
    for r in records:
        f = r["fixture"]
        fixture_stats[f]["total"] += 1
        if r["v1_admissible"]:
            fixture_stats[f]["v1"] += 1
        if r["v2_anchored"]:
            fixture_stats[f]["v2"] += 1
        if not r["v1_admissible"] and r["v2_anchored"]:
            fixture_stats[f]["rec"] += 1
        if r["v1_admissible"] and not r["v2_anchored"]:
            fixture_stats[f]["reg"] += 1
        if r["v2_abstained"]:
            fixture_stats[f]["abs"] += 1

    # Format paths
    out_path = Path(args.out)
    if out_path.suffix == ".json":
        json_path = out_path
        md_path = out_path.with_suffix(".md")
    else:
        json_path = out_path.with_name(out_path.name + ".json")
        md_path = out_path.with_name(out_path.name + ".md")

    # Save JSON report
    report_data = {
        "metadata": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "tau": tau,
            "artifacts_dir": str(args.artifacts_dir),
            "total_groundings_checked": total,
        },
        "summary": {
            "v1_admissible": v1_count,
            "v2_anchored": v2_count,
            "recovered_legit": recovered,
            "regressions": regressions,
            "abstains": abstains,
            "false_positives_on_fabricated": {
                "total_fabricated_checked": fp_total,
                "v2_false_accepts": fp_count,
                "rate": fp_count / fp_total if fp_total > 0 else 0.0
            }
        },
        "breakdown": {
            "by_seat_arm": dict(seat_stats),
            "by_fixture": dict(fixture_stats),
        },
        "records": records,
    }

    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Generate Markdown Summary
    v1_pct = (v1_count / total * 100) if total > 0 else 0.0
    v2_pct = (v2_count / total * 100) if total > 0 else 0.0
    rec_pct = (recovered / total * 100) if total > 0 else 0.0
    reg_pct = (regressions / total * 100) if total > 0 else 0.0
    abs_pct = (abstains / total * 100) if total > 0 else 0.0
    fp_pct = (fp_count / fp_total * 100) if fp_total > 0 else 0.0

    regression_records = [r for r in records if r["v1_admissible"] and not r["v2_anchored"]]
    regressions_list_content = ""
    if regression_records:
        regressions_list_content += "\n| Fixture | Seat/Arm | Claim | Excerpt | similarity |\n| :--- | :--- | :--- | :--- | :--- |\n"
        for r in regression_records:
            claim_trunc = r["claim"][:80] + "..." if len(r["claim"]) > 80 else r["claim"]
            excerpt_trunc = r["excerpt"][:80] + "..." if len(r["excerpt"]) > 80 else r["excerpt"]
            regressions_list_content += f"| {r['fixture']} | {r['seat_arm']} | {claim_trunc} | {excerpt_trunc} | {r['similarity']:.4f} |\n"
    else:
        regressions_list_content = "*No regressions observed (v1 accept ∧ v2 reject).*"

    seat_rows = ""
    for sa, s in sorted(seat_stats.items()):
        seat_rows += f"| {sa} | {s['total']} | {s['v1']} | {s['v2']} | {s['rec']} | {s['reg']} | {s['abs']} |\n"

    fixture_rows = ""
    for f, s in sorted(fixture_stats.items()):
        fixture_rows += f"| {f} | {s['total']} | {s['v1']} | {s['v2']} | {s['rec']} | {s['reg']} | {s['abs']} |\n"

    md_content = f"""# Grounding Gate Shadow Compare Report (v1 vs v2)

- **Date:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
- **Tau (τ):** {tau}
- **Artifacts Directory:** `{args.artifacts_dir}`

## Summary Totals

| Metric | Count | Percentage |
| :--- | :--- | :--- |
| Total Groundings Checked | {total} | 100.0% |
| v1 Admissible | {v1_count} | {v1_pct:.2f}% |
| v2 Anchored | {v2_count} | {v2_pct:.2f}% |
| Recovered Legit (v1 Reject ∧ v2 Anchor) | {recovered} | {rec_pct:.2f}% |
| Regressions (v1 Accept ∧ v2 Reject) | {regressions} | {reg_pct:.2f}% |
| Abstains | {abstains} | {abs_pct:.2f}% |
| New FP Rate (on Labeled False Claims) | {fp_count}/{fp_total} | {fp_pct:.2f}% |

## Seat/Arm Breakdown

| Seat/Arm | Total | v1 Admissible | v2 Anchored | Recovered | Regressions | Abstains |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
{seat_rows}
## Fixture Breakdown

| Fixture | Total | v1 Admissible | v2 Anchored | Recovered | Regressions | Abstains |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
{fixture_rows}
## Regressions List (v1 Accept ∧ v2 Reject)

{regressions_list_content}
"""

    md_path.write_text(md_content, encoding="utf-8")
    print("Shadow report generated successfully:")
    print(f"- JSON: {json_path}")
    print(f"- MD:   {md_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
