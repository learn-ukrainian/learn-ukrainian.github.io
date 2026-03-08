#!/usr/bin/env python3
"""
Batch verification for a track — trust nothing, check everything.

Run this AFTER Gemini claims to have finished modules. It re-runs the real
audit on every module that has a content file, and prints a summary showing
which modules actually pass vs which ones Gemini lied about.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

# ANSI colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"


def load_curriculum():
    """Load curriculum manifest."""
    import yaml
    manifest = Path(__file__).resolve().parent.parent / "curriculum" / "l2-uk-en" / "curriculum.yaml"
    with open(manifest) as f:
        return yaml.safe_load(f)


def get_modules(track, module_range=None):
    """Get module slugs for a track, optionally filtered by range."""
    data = load_curriculum()
    level_data = data.get("levels", {}).get(track)
    if not level_data:
        print(f"Unknown track: {track}")
        sys.exit(1)

    modules = level_data.get("modules", [])
    if module_range:
        start, end = module_range
        modules = modules[start - 1:end]  # 1-indexed to 0-indexed

    return modules


def find_content_file(track_dir, slug):
    """Find the content .md file — could be bare slug or numbered."""
    bare = track_dir / f"{slug}.md"
    if bare.exists():
        return bare
    for f in track_dir.glob(f"*-{slug}.md"):
        return f
    return None


def run_audit(content_path, skip_activities, project_root):
    """Run the audit script and return exit code."""
    audit_script = project_root / "scripts" / "audit_module.sh"
    cmd = [str(audit_script)]
    if skip_activities:
        cmd.append("--skip-activities")
    cmd.append(str(content_path))

    result = subprocess.run(
        cmd, capture_output=True, text=True, cwd=str(project_root),
    )
    return result.returncode, result.stdout


def read_status(status_file):
    """Read and parse a status JSON file."""
    if not status_file.exists():
        return None
    with open(status_file) as f:
        return json.load(f)


def is_status_stale(status_file, content_file):
    """Check if the status cache is stale (content modified after audit ran).

    Returns True if content file is strictly newer than the status file.
    Equal mtimes (e.g., from git checkout) are NOT treated as stale (#602).
    For robust equal-mtime handling, use content hashing (see #618).
    """
    if not status_file.exists() or not content_file or not content_file.exists():
        return False
    return content_file.stat().st_mtime > status_file.stat().st_mtime


def classify_module(status, full_mode):
    """Classify a module as pass/content-complete/fail based on status JSON."""
    if status is None:
        return "no-status", []

    overall = status.get("overall", {})
    gates = status.get("gates", {})
    overall_status = overall.get("status", "unknown")

    problems = []
    failing = []
    deferred = []

    for gate_name, gate_data in gates.items():
        g_status = gate_data.get("status", "")
        msg = gate_data.get("message", "")
        if g_status == "fail":
            failing.append(f"{gate_name}: {msg}")
        elif g_status == "deferred":
            deferred.append(gate_name)

    if failing:
        problems.extend(failing)

    if full_mode and deferred:
        problems.append(f"deferred gates: {', '.join(deferred)}")

    if problems:
        return "fail", problems

    if deferred and not full_mode:
        return "content-complete", [f"deferred: {', '.join(deferred)}"]

    if overall_status == "pass":
        return "pass", []

    return "fail", [f"overall status: {overall_status}"]


def check_sidecar_files(track_dir, slug, full_mode):
    """Check for activities and vocabulary YAML files."""
    missing = []
    if full_mode:
        if not (track_dir / "activities" / f"{slug}.yaml").exists():
            missing.append("activities YAML missing")
        if not (track_dir / "vocabulary" / f"{slug}.yaml").exists():
            missing.append("vocabulary YAML missing")
    return missing


def parse_range(range_str):
    """Parse '1-5' into (1, 5)."""
    parts = range_str.split("-")
    if len(parts) != 2:
        raise argparse.ArgumentTypeError(f"Range must be N-M, got: {range_str}")
    return (int(parts[0]), int(parts[1]))


def main():
    parser = argparse.ArgumentParser(
        description="Batch verification for a track. Re-runs audits and reports which modules actually pass.",
        epilog="Examples:\n"
               "  %(prog)s a1                    # Verify all A1 modules (fresh audit)\n"
               "  %(prog)s a1 --range 12-15      # Verify modules 12-15 only\n"
               "  %(prog)s a1 --full             # Require full pass (activities + vocab)\n"
               "  %(prog)s a1 --quick            # Fast: read cached status, skip re-audit\n"
               "  %(prog)s a1 --range 1-5 --full # Modules 1-5, all gates must pass\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("track", help="Track to verify (e.g., a1, b1, bio)")
    parser.add_argument("--range", type=parse_range, metavar="N-M",
                        help="Only verify modules N through M (1-indexed)")
    parser.add_argument("--full", action="store_true",
                        help="Require full pass — all gates including activities/vocab (default: content-only)")
    parser.add_argument("--quick", action="store_true",
                        help="Skip re-audit, read cached status JSON only (fast but may be stale)")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    track_dir = project_root / "curriculum" / "l2-uk-en" / args.track
    modules = get_modules(args.track, args.range)

    mode_label = "FULL (all gates)" if args.full else "CONTENT-COMPLETE (prose gates only)"
    method_label = "cached status JSON" if args.quick else "fresh audit"

    print(f"{'=' * 70}")
    print(f"  VERIFY TRACK: {args.track} ({len(modules)} modules)")
    print(f"  Mode: {mode_label}")
    print(f"  Method: {method_label}")
    print(f"{'=' * 70}")
    print()

    results = []
    start_num = args.range[0] if args.range else 1

    for i, slug in enumerate(modules):
        num = start_num + i
        content_file = find_content_file(track_dir, slug)

        if content_file is None:
            results.append((num, slug, "no-file", ["content .md not found"], False))
            print(f"  {DIM}M{num:02d} {slug}: no content file{RESET}")
            continue

        if not args.quick:
            skip_activities = not args.full
            run_audit(content_file, skip_activities, project_root)

        status_file = track_dir / "status" / f"{slug}.json"
        status = read_status(status_file)
        classification, problems = classify_module(status, args.full)

        # Staleness detection: flag passes that may be outdated (#602)
        stale = False
        if args.quick and classification in ("pass", "content-complete") and is_status_stale(status_file, content_file):
            stale = True
            problems.insert(0, "STALE: content modified after last audit")

        sidecar_missing = check_sidecar_files(track_dir, slug, args.full)
        if sidecar_missing:
            problems.extend(sidecar_missing)
            if classification == "pass":
                classification = "fail"

        results.append((num, slug, classification, problems, stale))

        if stale:
            icon = f"{YELLOW}STALE{RESET}"
        elif classification == "pass":
            icon = f"{GREEN}PASS{RESET}"
        elif classification == "content-complete":
            icon = f"{YELLOW}PROSE{RESET}"
        elif classification == "no-status":
            icon = f"{RED}NO STATUS{RESET}"
        else:
            icon = f"{RED}FAIL{RESET}"

        problem_summary = f" — {problems[0]}" if problems else ""
        print(f"  M{num:02d} {slug}: {icon}{DIM}{problem_summary}{RESET}")

    # Summary
    print()
    print(f"{'=' * 70}")

    total = len(results)
    pass_count = sum(1 for _, _, s, _, _ in results if s == "pass")
    prose_count = sum(1 for _, _, s, _, _ in results if s == "content-complete")
    fail_count = sum(1 for _, _, s, _, _ in results if s == "fail")
    no_file_count = sum(1 for _, _, s, _, _ in results if s == "no-file")
    no_status_count = sum(1 for _, _, s, _, _ in results if s == "no-status")
    stale_count = sum(1 for _, _, _, _, st in results if st)

    print(f"  {BOLD}SUMMARY: {args.track}{RESET}")
    print(f"  Total:            {total}")
    print(f"  {GREEN}Pass:             {pass_count}{RESET}")
    if not args.full:
        print(f"  {YELLOW}Content-complete: {prose_count}{RESET}")
    print(f"  {RED}Fail:             {fail_count}{RESET}")
    if stale_count:
        print(f"  {YELLOW}Stale passes:     {stale_count}{RESET}  (re-run without --quick to revalidate)")
    if no_file_count:
        print(f"  {DIM}No content file:  {no_file_count}{RESET}")
    if no_status_count:
        print(f"  {DIM}No status JSON:   {no_status_count}{RESET}")
    print(f"{'=' * 70}")

    failing = [(n, s, p) for n, s, cls, p, _ in results if cls == "fail"]
    if failing:
        print()
        print(f"  {RED}{BOLD}FAILING MODULES:{RESET}")
        for num, slug, problems in failing:
            print(f"    M{num:02d} {slug}:")
            for p in problems:
                print(f"      - {p}")
        print()

    sys.exit(1 if fail_count > 0 else 0)


if __name__ == "__main__":
    main()
