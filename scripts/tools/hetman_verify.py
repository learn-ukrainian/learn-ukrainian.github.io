#!/usr/bin/env python3
"""
Hetman Verification Gate — hard pass/fail check for fully-complete modules.

This script is the ONLY way to confirm that hetman succeeded. Gemini MUST run
this and it MUST exit 0 before declaring a module fully complete.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Hard pass/fail verification gate for fully-complete modules (hetman).",
        epilog="What it checks:\n"
               "  1. Runs FULL audit (no --skip-activities)\n"
               "  2. Reads the status JSON — ALL gates must pass (no deferred, no fail)\n"
               "  3. Verifies activities YAML and vocabulary YAML exist\n"
               "  4. Prints a definitive PASS or FAIL verdict\n"
               "\n"
               "Exit codes:\n"
               "  0 = PASS — module is fully complete, all gates pass\n"
               "  1 = FAIL — module has failing or deferred gates\n"
               "\n"
               "Examples:\n"
               "  %(prog)s curriculum/l2-uk-en/a1/the-gender-code.md\n"
               "  %(prog)s curriculum/l2-uk-en/b1/aspect-basics.md\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("content_md", type=Path,
                        help="Path to the module content .md file")
    args = parser.parse_args()

    content_path = args.content_md.resolve()
    if not content_path.exists():
        print(f"FAIL: File not found: {content_path}")
        sys.exit(1)

    # Derive paths
    slug = content_path.stem
    bare_slug = slug.split("-", 1)[1] if slug[0].isdigit() and "-" in slug else slug
    track_dir = content_path.parent
    status_file = track_dir / "status" / f"{bare_slug}.json"
    activities_file = track_dir / "activities" / f"{bare_slug}.yaml"
    vocab_file = track_dir / "vocabulary" / f"{bare_slug}.yaml"

    project_root = Path(__file__).resolve().parent.parent.parent
    audit_script = project_root / "scripts" / "audit_module.sh"

    print(f"{'='*60}")
    print(f"  HETMAN VERIFY: {bare_slug}")
    print(f"{'='*60}")
    print()

    # ── Step 1: Run FULL audit (no --skip-activities) ─────────
    print("[1/4] Running full audit...")
    result = subprocess.run(
        [str(audit_script), str(content_path)],
        capture_output=True, text=True, cwd=str(project_root),
    )
    audit_exit = result.returncode

    # ── Step 2: Check sidecar files exist ─────────────────────
    print("[2/4] Checking sidecar files...")
    missing_files = []
    if not activities_file.exists():
        missing_files.append(f"activities/{bare_slug}.yaml")
    if not vocab_file.exists():
        missing_files.append(f"vocabulary/{bare_slug}.yaml")

    # ── Step 3: Read status JSON ──────────────────────────────
    print("[3/4] Reading status JSON...")
    if not status_file.exists():
        print(f"  FAIL: No status file at {status_file.relative_to(project_root)}")
        print()
        _fail_verdict(bare_slug, ["No status JSON — audit did not run or crashed"])
        sys.exit(1)

    with open(status_file) as f:
        status = json.load(f)

    overall = status.get("overall", {})
    gates = status.get("gates", {})
    overall_status = overall.get("status", "unknown")
    blocking = overall.get("blocking_issues", [])

    failing_gates = []
    deferred_gates = []
    for gate_name, gate_data in gates.items():
        g_status = gate_data.get("status", "")
        msg = gate_data.get("message", "no details")
        if g_status == "fail":
            failing_gates.append(f"  {gate_name}: {msg}")
        elif g_status == "deferred":
            deferred_gates.append(f"  {gate_name}: still deferred — activities not generated")

    # ── Step 4: Check overall status is "pass" ────────────────
    print("[4/4] Checking overall status...")

    problems = []

    if audit_exit != 0:
        problems.append("audit script returned non-zero exit code")

    if overall_status != "pass":
        problems.append(f"overall status is '{overall_status}' (must be 'pass')")
        problems.extend(blocking)

    if failing_gates:
        problems.append("failing gates:")
        problems.extend(failing_gates)

    if deferred_gates:
        problems.append("deferred gates (activities not generated):")
        problems.extend(deferred_gates)

    if missing_files:
        problems.append("missing sidecar files:")
        for f in missing_files:
            problems.append(f"  {f}")

    # ── Verdict ───────────────────────────────────────────────
    print()

    if problems:
        _fail_verdict(bare_slug, problems)
        audit_lines = result.stdout.strip().splitlines()
        if audit_lines:
            print()
            print("─── Audit output (last 15 lines) ───")
            for line in audit_lines[-15:]:
                print(f"  {line}")
        sys.exit(1)
    else:
        _pass_verdict(bare_slug, gates)
        sys.exit(0)


def _fail_verdict(slug, problems):
    print(f"{'─'*60}")
    print("  VERDICT: FAIL")
    print(f"  Module:  {slug}")
    print(f"{'─'*60}")
    for p in problems:
        print(f"  {p}")
    print()
    print("  Hetman has NOT completed this module.")
    print("  Fix the issues above and re-run this script.")


def _pass_verdict(slug, gates):
    pass_count = sum(1 for g in gates.values() if g.get("status") == "pass")
    info_count = sum(1 for g in gates.values() if g.get("status") == "info")

    print(f"{'─'*60}")
    print("  VERDICT: PASS")
    print(f"  Module:  {slug}")
    print(f"  Gates:   {pass_count} pass, {info_count} info")
    print(f"{'─'*60}")
    print()
    print("  Module is FULLY COMPLETE.")
    print("  Hetman may now write completion.md and proceed.")


if __name__ == "__main__":
    main()
