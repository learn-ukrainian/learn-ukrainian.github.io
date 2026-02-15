#!/usr/bin/env python3
"""
Otaman Verification Gate — hard pass/fail check for content-complete modules.

This script is the ONLY way to confirm that otaman succeeded. Gemini MUST run
this and it MUST exit 0 before declaring a module content-complete.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Hard pass/fail verification gate for content-complete modules (otaman).",
        epilog="What it checks:\n"
               "  1. Runs audit with --skip-activities\n"
               "  2. Reads the status JSON and checks each non-deferred gate\n"
               "  3. Verifies orchestration artifacts exist (phase-2 sections, placeholders)\n"
               "  4. Prints a definitive PASS or FAIL verdict\n"
               "\n"
               "Exit codes:\n"
               "  0 = PASS — module is content-complete, all content gates pass\n"
               "  1 = FAIL — module has failing gates (printed to stdout)\n"
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
    orch_dir = track_dir / "orchestration" / bare_slug

    project_root = Path(__file__).resolve().parent.parent
    audit_script = project_root / "scripts" / "audit_module.sh"

    print(f"{'='*60}")
    print(f"  OTAMAN VERIFY: {bare_slug}")
    print(f"{'='*60}")
    print()

    # ── Step 1: Run the actual audit ──────────────────────────
    print("[1/3] Running audit with --skip-activities...")
    result = subprocess.run(
        [str(audit_script), "--skip-activities", str(content_path)],
        capture_output=True, text=True, cwd=str(project_root),
    )
    audit_exit = result.returncode

    # ── Step 2: Read status JSON (written by audit) ───────────
    print("[2/3] Reading status JSON...")
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
    for gate_name, gate_data in gates.items():
        g_status = gate_data.get("status", "")
        if g_status == "fail":
            msg = gate_data.get("message", "no details")
            failing_gates.append(f"  {gate_name}: {msg}")

    # ── Step 3: Check orchestration artifacts ─────────────────
    print("[3/3] Checking orchestration artifacts...")
    missing_artifacts = []

    if not orch_dir.exists():
        missing_artifacts.append("orchestration directory missing")
    else:
        phase2_files = list(orch_dir.glob("phase-2-p2-*-section_content.md"))
        if not phase2_files:
            missing_artifacts.append("no Phase 2 section content files")
        if not (orch_dir / "placeholders.yaml").exists():
            missing_artifacts.append("placeholders.yaml missing")

    # ── Verdict ───────────────────────────────────────────────
    print()
    problems = []

    if audit_exit != 0:
        problems.append("audit script returned non-zero exit code")

    if overall_status == "fail":
        problems.extend(blocking)

    if failing_gates:
        problems.append("failing gates:")
        problems.extend(failing_gates)

    if missing_artifacts:
        problems.append("missing orchestration artifacts:")
        for a in missing_artifacts:
            problems.append(f"  {a}")

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
    print(f"  VERDICT: FAIL")
    print(f"  Module:  {slug}")
    print(f"{'─'*60}")
    for p in problems:
        print(f"  {p}")
    print()
    print("  Otaman has NOT completed this module.")
    print("  Fix the issues above and re-run this script.")


def _pass_verdict(slug, gates):
    pass_count = sum(1 for g in gates.values() if g.get("status") == "pass")
    deferred_count = sum(1 for g in gates.values() if g.get("status") == "deferred")
    info_count = sum(1 for g in gates.values() if g.get("status") == "info")

    print(f"{'─'*60}")
    print(f"  VERDICT: PASS")
    print(f"  Module:  {slug}")
    print(f"  Gates:   {pass_count} pass, {deferred_count} deferred, {info_count} info")
    print(f"{'─'*60}")
    print()
    print("  Module is CONTENT-COMPLETE.")
    print("  Otaman may now write completion.md and proceed.")


if __name__ == "__main__":
    main()
