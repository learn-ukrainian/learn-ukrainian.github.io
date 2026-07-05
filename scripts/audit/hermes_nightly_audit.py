#!/usr/bin/env python3
"""Run nightly deterministic curriculum track audits sequentially.

This script runs the deterministic audit checks for tracks a1, a2, b1, b2 sequentially.
It gathers findings, counts, severities, optionally appends a 'hermes insights' snapshot,
and writes the aggregated results to both Markdown and JSON files in batch_state/hermes_cron/.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from collections import Counter
from datetime import UTC, datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def run_track_audit(track: str) -> dict:
    """Run track_deterministic_audit.py for a single track and return its JSON output."""
    script_path = PROJECT_ROOT / "scripts" / "audit" / "track_deterministic_audit.py"
    cmd = [
        sys.executable,
        str(script_path),
        "--track",
        track,
        "--format",
        "json",
        "--fail-on",
        "never",
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(res.stdout)
    except subprocess.CalledProcessError as e:
        # If it failed to run (e.g. exit code 1), check if we got JSON output anyway
        try:
            return json.loads(e.stdout)
        except Exception:
            return {
                "track": track,
                "summary": {
                    "findings_total": 1,
                    "findings_by_severity": {
                        "blocker": 1,
                        "high": 0,
                        "medium": 0,
                        "low": 0,
                        "info": 0,
                    },
                    "modules_selected": 0,
                    "modules_built": 0,
                    "modules_not_built": 0,
                    "skipped_checks": 0,
                },
                "findings": [
                    {
                        "track": track,
                        "module_num": None,
                        "slug": None,
                        "category": "process",
                        "severity": "blocker",
                        "file": "scripts/audit/track_deterministic_audit.py",
                        "line": None,
                        "message": f"Audit process exited with error code {e.returncode}",
                        "evidence": f"stdout: {e.stdout}\nstderr: {e.stderr}",
                        "auto_fixable": False,
                        "recommended_remediation_batch": "infrastructure",
                    }
                ],
            }
    except Exception as e:
        return {
            "track": track,
            "summary": {
                "findings_total": 1,
                "findings_by_severity": {
                    "blocker": 1,
                    "high": 0,
                    "medium": 0,
                    "low": 0,
                    "info": 0,
                },
                "modules_selected": 0,
                "modules_built": 0,
                "modules_not_built": 0,
                "skipped_checks": 0,
            },
            "findings": [
                {
                    "track": track,
                    "module_num": None,
                    "slug": None,
                    "category": "process",
                    "severity": "blocker",
                    "file": None,
                    "line": None,
                    "message": f"Failed to invoke audit runner: {e}",
                    "evidence": str(e),
                    "auto_fixable": False,
                    "recommended_remediation_batch": "infrastructure",
                }
            ],
        }


def get_hermes_insights(insights_cmd: str = "hermes") -> str:
    """Retrieve hermes insights snapshot if available, otherwise return 'insights unavailable'."""
    try:
        res = subprocess.run([insights_cmd, "insights"], capture_output=True, text=True, check=True)
        return res.stdout
    except Exception:
        return "insights unavailable"


def build_markdown_report(timestamp: str, track_results: dict[str, dict], insights: str) -> str:
    """Assemble a beautifully formatted Markdown report of the sweep results."""
    # Compute totals
    total_findings = 0
    total_by_severity = Counter()
    total_modules_selected = 0
    total_modules_built = 0
    total_modules_not_built = 0

    for _track, data in track_results.items():
        summary = data.get("summary", {})
        total_findings += summary.get("findings_total", 0)
        total_modules_selected += summary.get("modules_selected", 0)
        total_modules_built += summary.get("modules_built", 0)
        total_modules_not_built += summary.get("modules_not_built", 0)
        for sev, count in summary.get("findings_by_severity", {}).items():
            total_by_severity[sev] += count

    lines = [
        "# Hermes Nightly Audit Report",
        f"Generated at: `{timestamp}`",
        "",
        "## Summary of Findings",
        "",
        "| Severity | Count |",
        "| :--- | :--- |",
        f"| 🔴 Blocker | {total_by_severity['blocker']} |",
        f"| 🟠 High | {total_by_severity['high']} |",
        f"| 🟡 Medium | {total_by_severity['medium']} |",
        f"| 🔵 Low | {total_by_severity['low']} |",
        f"| ⚪ Info | {total_by_severity['info']} |",
        f"| **Total Findings** | **{total_findings}** |",
        "",
        "## Track Details",
        "",
    ]

    for track, data in track_results.items():
        summary = data.get("summary", {})
        lines.extend([
            f"### Track `{track.upper()}`",
            f"- **Modules**: Selected {summary.get('modules_selected', 0)} (Built: {summary.get('modules_built', 0)}, Not Built: {summary.get('modules_not_built', 0)})",
            f"- **Findings**: Total {summary.get('findings_total', 0)}",
            f"  - Blocker: {summary.get('findings_by_severity', {}).get('blocker', 0)}",
            f"  - High: {summary.get('findings_by_severity', {}).get('high', 0)}",
            f"  - Medium: {summary.get('findings_by_severity', {}).get('medium', 0)}",
            f"  - Low: {summary.get('findings_by_severity', {}).get('low', 0)}",
            f"  - Info: {summary.get('findings_by_severity', {}).get('info', 0)}",
        ])

        findings = data.get("findings", [])
        if findings:
            lines.append("  - **Top Findings**:")
            # Display up to 10 findings for this track
            for item in findings[:10]:
                location = item.get("file") or "<repo>"
                if item.get("line"):
                    location = f"{location}:{item['line']}"
                module = f"M{item.get('module_num', 0):02d} {item.get('slug', '')}" if item.get("module_num") else "track"
                lines.append(f"    - `[{item.get('severity', 'info')}]` {module} ({item.get('category', '')}) `{location}`: {item.get('message', '')}")
            if len(findings) > 10:
                lines.append(f"    - ... and {len(findings) - 10} more findings")
        else:
            lines.append("  - No findings reported.")
        lines.append("")

    lines.extend([
        "## Hermes Insights Snapshot",
        "```",
        insights.strip(),
        "```",
        "",
    ])

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run nightly deterministic curriculum track audits sequentially and aggregate findings.\n"
                    "Use this tool to verify repository structural health, case parity, and findings status.\n"
                    "Do NOT use this tool for mutating curriculum data or running LLM tasks.",
        epilog="Examples:\n"
               "  .venv/bin/python scripts/audit/hermes_nightly_audit.py\n"
               "  .venv/bin/python scripts/audit/hermes_nightly_audit.py --tracks a1\n"
               "  .venv/bin/python scripts/audit/hermes_nightly_audit.py --tracks a1,a2 --insights-cmd /usr/local/bin/hermes\n\n"
               "Outputs:\n"
               "  batch_state/hermes_cron/audit_YYYYMMDD_HHMMSS.md   - Markdown report of findings and insights.\n"
               "  batch_state/hermes_cron/audit_YYYYMMDD_HHMMSS.json - Machine-readable JSON sidecar.\n"
               "  batch_state/hermes_cron/latest.md                  - Copy of the latest Markdown report.\n"
               "  batch_state/hermes_cron/latest.json                - Copy of the latest JSON report.\n\n"
               "Exit codes:\n"
               "  0 - Sweep completed and reports written successfully.\n"
               "  1 - Unexpected script execution failure.\n\n"
               "Related:\n"
               "  Prompt template: agents_extensions/shared/prompts/hermes-nightly-audit.md\n"
               "  Monitor Router: scripts/api/hermes_cron_router.py\n"
               "  Auditor script: scripts/audit/track_deterministic_audit.py\n"
               "  Specification: docs/best-practices/hermes-usage.md",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--tracks",
        default="a1,a2,b1,b2",
        help="Comma-separated track IDs to audit (default: 'a1,a2,b1,b2'). Example: '--tracks a1,a2'.",
    )
    parser.add_argument(
        "--insights-cmd",
        default="hermes",
        help="The command name or path to the hermes binary for retrieving insights (default: 'hermes').",
    )

    args = parser.parse_args()

    track_list = [t.strip().lower() for t in args.tracks.split(",") if t.strip()]
    if not track_list:
        print("Error: No tracks specified to audit.", file=sys.stderr)
        return 1

    print(f"Starting sequential audit for tracks: {track_list}")
    track_results = {}
    for track in track_list:
        print(f"Auditing track '{track}'...")
        track_results[track] = run_track_audit(track)

    print("Retrieving Hermes insights snapshot...")
    insights = get_hermes_insights(args.insights_cmd)

    now = datetime.now(UTC)
    timestamp_str = now.strftime("%Y%m%d_%H%M%S")
    iso_timestamp = now.isoformat().replace("+00:00", "Z")

    # Compute overall totals for JSON
    overall_by_severity = Counter()
    total_findings = 0
    for _track, data in track_results.items():
        summary = data.get("summary", {})
        total_findings += summary.get("findings_total", 0)
        for sev, count in summary.get("findings_by_severity", {}).items():
            overall_by_severity[sev] += count

    json_data = {
        "timestamp": iso_timestamp,
        "summary": {
            "findings_total": total_findings,
            "findings_by_severity": dict(overall_by_severity),
        },
        "tracks": track_results,
        "insights": insights,
    }

    markdown_report = build_markdown_report(iso_timestamp, track_results, insights)

    # Write output to batch_state/hermes_cron/ (gitignored)
    output_dir = PROJECT_ROOT / "batch_state" / "hermes_cron"
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"Error: Failed to create output directory {output_dir}: {e}", file=sys.stderr)
        return 1

    md_path = output_dir / f"audit_{timestamp_str}.md"
    json_path = output_dir / f"audit_{timestamp_str}.json"
    latest_md_path = output_dir / "latest.md"
    latest_json_path = output_dir / "latest.json"

    try:
        md_path.write_text(markdown_report, encoding="utf-8")
        json_path.write_text(json.dumps(json_data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        shutil.copy2(md_path, latest_md_path)
        shutil.copy2(json_path, latest_json_path)

        print(f"Reports successfully written to:\n  - {md_path}\n  - {json_path}\nAnd copied to latest links.")
    except Exception as e:
        print(f"Error writing reports: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
