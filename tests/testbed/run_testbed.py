#!/usr/bin/env python3
"""Testbed runner — build, audit, and review fixed modules for regression testing.

Usage:
    %(prog)s build                    # Build all testbed modules (sandbox → mdx)
    %(prog)s build --restart-from content  # Rebuild from content phase
    %(prog)s audit                    # Audit only (no builds, no reviews)
    %(prog)s review                   # Run content-review + prompt-review (Claude API)
    %(prog)s full                     # Build + audit + compare to baseline
    %(prog)s full --review            # Build + audit + review + compare
    %(prog)s report                   # Show latest results vs baseline
    %(prog)s baseline                 # Save current results as the baseline

Builds every module in config.yaml, runs audit, tracks grades in results/.
Reviews (content-review + prompt-review) run as Claude subagent skills after build.

Issue: #754
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import yaml
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

TESTBED_DIR = Path(__file__).resolve().parent
ROOT_DIR = TESTBED_DIR.parent.parent
SCRIPTS_DIR = ROOT_DIR / "scripts"
CURDIR = ROOT_DIR / "curriculum" / "l2-uk-en"
RESULTS_DIR = TESTBED_DIR / "core" / "results"
GRADES_CSV = TESTBED_DIR / "core" / "grades.csv"
BASELINE_JSON = TESTBED_DIR / "core" / "baseline.json"
PYTHON = str(ROOT_DIR / ".venv" / "bin" / "python")

sys.path.insert(0, str(SCRIPTS_DIR))

GRADE_ORDER = {"A": 0, "B": 1, "C": 2, "F": 3, "N/A": 4}


def load_config(track_filter: str | None = None) -> list[dict]:
    """Load testbed module list from config.yaml, optionally filtered by track."""
    config_path = TESTBED_DIR / "config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)
    modules = config.get("core_modules", [])
    if track_filter:
        modules = [m for m in modules if m["track"] == track_filter]
    return modules


def build_module(mod: dict, restart_from: str | None = None, full: bool = False) -> bool:
    """Build a single module via build_module_v5.py. Returns True on success."""
    track, num, slug = mod["track"], mod["num"], mod["slug"]
    cmd = [PYTHON, str(SCRIPTS_DIR / "build_module_v5.py"), track, str(num)]
    if full:
        cmd += ["--rebuild"]
    elif restart_from:
        cmd += ["--restart-from", restart_from]
    else:
        # Default: restart from sandbox (skip research/discover if already done)
        orch_dir = CURDIR / track / "orchestration" / slug
        if (orch_dir / "state.json").exists():
            cmd += ["--restart-from", "sandbox"]

    print(f"\n{'='*60}", flush=True)
    print(f"  BUILD: {track} M{num} ({slug})", flush=True)
    print(f"  CMD: {' '.join(cmd)}", flush=True)
    print(f"{'='*60}", flush=True)

    t0 = time.time()
    result = subprocess.run(cmd, cwd=str(ROOT_DIR))
    elapsed = time.time() - t0
    ok = result.returncode == 0
    print(f"  {'PASS' if ok else 'FAIL'} in {elapsed:.0f}s", flush=True)
    return ok


def audit_module(mod: dict) -> dict:
    """Run audit on a module, return structured results."""
    track, num, slug = mod["track"], mod["num"], mod["slug"]
    content_path = CURDIR / track / f"{slug}.md"

    if not content_path.exists():
        return {"slug": slug, "track": track, "num": num, "status": "NO_CONTENT"}

    # Run audit_module.py and capture output
    cmd = [PYTHON, str(SCRIPTS_DIR / "audit_module.py"), str(content_path)]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT_DIR))
    output = result.stdout + result.stderr

    # Read structured status JSON (written by audit — authoritative source)
    status_path = CURDIR / track / "status" / f"{slug}.json"
    gates = {}
    passed = False
    words = 0
    word_target = 0

    if status_path.exists():
        with open(status_path) as f:
            status_data = json.load(f)
        # Determine pass/fail based on content gates only (review is separate phase)
        content_gates_ok = all(
            g_info.get("status") != "fail"
            for g_name, g_info in status_data.get("gates", {}).items()
            if g_name != "review"
        )
        passed = content_gates_ok
        for gate_name, gate_info in status_data.get("gates", {}).items():
            status = gate_info.get("status", "")
            # pass/info/deferred/skipped = not failing; only "fail" = failing
            gates[gate_name] = status != "fail"
        # Extract word count from lesson gate message: "1574/1200 (raw: 1638)"
        lesson_msg = status_data.get("gates", {}).get("lesson", {}).get("message", "")
        m = re.search(r"(\d+)/(\d+)", lesson_msg)
        if m:
            words = int(m.group(1))
            word_target = int(m.group(2))
    else:
        # Fallback: parse stdout (status JSON not written on crash)
        passed = "AUDIT PASSED" in output
        for line in output.split("\n"):
            line = line.strip()
            if not line:
                continue
            if "✅" in line or "❌" in line:
                parts = line.split(None, 1)
                if len(parts) >= 2 and parts[0][0].isalpha():
                    gate_name = parts[0].strip()
                    gate_pass = "✅" in line
                    gates[gate_name] = gate_pass
        for line in output.split("\n"):
            if "Words" in line and ("✅" in line or "❌" in line):
                m = re.search(r"(\d+)/(\d+)", line)
                if m:
                    words = int(m.group(1))
                    word_target = int(m.group(2))

    # Check orchestration state for fix loop count and self-audit status
    from pipeline_v5 import load_state as _load_v5_state
    from pipeline_lib import ModuleContext as _MC
    _ctx = MagicMock(spec=_MC)
    _ctx.orch_dir = CURDIR / track / "orchestration" / slug
    _ctx.track = track
    _ctx.slug = slug
    state = _load_v5_state(_ctx) if _ctx.orch_dir.exists() else {"phases": {}}
    validate_phase = state.get("phases", {}).get("validate", {})
    fix_attempts = validate_phase.get("attempts", 0)
    self_audited = state.get("phases", {}).get("content", {}).get("self_audited", False)

    # Count failing gates (exclude review — it's a separate pipeline phase)
    failing_gates = [g for g, v in gates.items() if not v and g != "review"]
    # Track review status separately
    review_gate_pass = gates.get("review", True)

    # Extract naturalness score from meta.yaml
    nat_score = None
    meta_path = CURDIR / track / "meta" / f"{slug}.yaml"
    if meta_path.exists():
        try:
            with open(meta_path) as f:
                meta_data = yaml.safe_load(f) or {}
            nat = meta_data.get("naturalness", {})
            if isinstance(nat, dict) and nat.get("score"):
                nat_score = nat["score"]
        except Exception:
            pass

    # Parse existing reviews
    content_review = parse_content_review(track, slug)
    prompt_review = parse_prompt_review(track, slug)

    return {
        "slug": slug,
        "track": track,
        "num": num,
        "status": "PASS" if passed else "FAIL",
        "words": words,
        "word_target": word_target,
        "gates": gates,
        "failing_gates": failing_gates,
        "fix_attempts": fix_attempts,
        "self_audited": self_audited,
        "nat_score": nat_score,
        "content_review": content_review,
        "prompt_review": prompt_review,
    }


def review_module(mod: dict) -> dict:
    """Run content-review and prompt-review on a module via Claude skills.

    Returns dict with review results. Requires ``claude`` CLI to be installed.
    Reviews are expensive (Claude API calls) — always opt-in.
    """
    track, slug = mod["track"], mod["slug"]
    results: dict = {"content_review": None, "prompt_review": None}

    for kind, skill in [("content_review", "content-review"), ("prompt_review", "prompt-review")]:
        skill_arg = f"/{skill} {track} {slug}"
        cmd = ["claude", "-p", skill_arg, "--allowedTools", ""]
        print(f"  REVIEW ({skill}): {track} {slug} ...", end="", flush=True)
        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300, cwd=str(ROOT_DIR),
            )
            ok = proc.returncode == 0
            print(f" {'OK' if ok else 'FAIL'}", flush=True)
            if not ok and proc.stderr:
                print(f"    stderr: {proc.stderr[:200]}", flush=True)
        except FileNotFoundError:
            print(" SKIP (claude CLI not found)", flush=True)
            continue
        except subprocess.TimeoutExpired:
            print(" TIMEOUT (300s)", flush=True)
            continue

        # Re-parse the review file that the skill just wrote
        if kind == "content_review":
            results[kind] = parse_content_review(track, slug)
        else:
            results[kind] = parse_prompt_review(track, slug)

    return results


def grade_module(audit_result: dict) -> str:
    """Assign A/B/C/F grade based on audit results.

    Successful fix loops are normal in v5 — they mean validation caught
    issues and Gemini fixed them. Fewer attempts = better, but passing
    after fixes is not penalized vs passing on first try.

    Grading:
      F: audit failed
      C: passed but >3 fix attempts (excessive churn)
      B: passed, words within target range
      A: passed, words ≥ 110% target (rich content), ≤3 fix attempts
    """
    if audit_result["status"] == "NO_CONTENT":
        return "N/A"
    if audit_result["status"] != "PASS":
        return "F"

    fix = audit_result["fix_attempts"]
    words = audit_result["words"]
    target = audit_result["word_target"]
    word_ratio = words / target if target > 0 else 0

    if fix > 3:
        return "C"  # Excessive fix churn — something is off
    elif word_ratio >= 1.1:
        return "A"  # Rich content, reasonable fix count
    else:
        return "B"  # Passed but content is close to minimum


def combined_grade(audit_grade: str, review_grade: str | None) -> str:
    """Produce combined grade from audit grade and content review grade.

    Takes the worst of audit and review grades. If no review exists,
    returns the audit grade unchanged.
    """
    if not review_grade or review_grade == "?":
        return audit_grade

    # Normalize review grade: strip +/- for comparison
    review_base = review_grade.rstrip("+-")
    order = {"A": 0, "B": 1, "C": 2, "F": 3, "N/A": 4}
    audit_rank = order.get(audit_grade, 4)
    review_rank = order.get(review_base, 4)

    # Worst-of: higher rank number = worse grade
    if review_rank > audit_rank:
        return review_base
    return audit_grade


def parse_content_review(track: str, slug: str) -> dict | None:
    """Parse existing content-review file for grade and issue counts."""

    review_path = CURDIR / track / "audit" / f"{slug}-content-review.md"
    if not review_path.exists():
        return None

    text = review_path.read_text()

    # Parse grade: "**Grade: B**" or "Grade: A." or "**Grade: B+**"
    grade_match = re.search(r"[Gg]rade:\s*([ABCF][+\-]?)", text)
    grade = grade_match.group(1) if grade_match else "?"

    # Count issues by severity
    critical = len(re.findall(r"CRITICAL", text, re.IGNORECASE))
    high = len(re.findall(r"\bHIGH\b", text))
    medium = len(re.findall(r"\bMEDIUM\b", text))

    return {
        "grade": grade,
        "critical": critical,
        "high": high,
        "medium": medium,
        "path": str(review_path),
    }


def parse_prompt_review(track: str, slug: str) -> dict | None:
    """Parse existing prompt-review file for template health and fix count."""

    review_path = CURDIR / track / "audit" / f"{slug}-prompt-review.md"
    if not review_path.exists():
        return None

    text = review_path.read_text()

    # Parse template health: "Template Health: GOOD/NEEDS_WORK/BROKEN"
    health_match = re.search(r"[Tt]emplate\s+[Hh]ealth[:\s]+(\w+)", text)
    health = health_match.group(1).upper() if health_match else "?"

    # Count fix loops mentioned
    fix_match = re.search(r"[Ff]ix\s+[Ll]oop[s]?[:\s]+(\d+)", text)
    fix_loops = int(fix_match.group(1)) if fix_match else 0

    # Count friction points
    friction_count = len(re.findall(r"[Ff]riction", text))

    return {
        "health": health,
        "fix_loops": fix_loops,
        "friction_count": friction_count,
        "path": str(review_path),
    }


def save_results(results: list[dict], run_id: str) -> Path:
    """Save results to JSON and append to grades CSV."""
    # Save detailed JSON
    result_file = RESULTS_DIR / f"{run_id}.json"
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(result_file, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Append to grades CSV
    csv_exists = GRADES_CSV.exists()
    with open(GRADES_CSV, "a", newline="") as f:
        writer = csv.writer(f)
        if not csv_exists:
            writer.writerow(["date", "run_id", "track", "num", "slug", "audit_grade",
                             "review_grade", "nat_score", "status", "words", "target",
                             "fix_attempts", "self_audited", "failing_gates"])
        for r in results:
            cr = r.get("content_review")
            writer.writerow([
                datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                run_id,
                r["track"], r["num"], r["slug"],
                r.get("grade", "?"),
                cr["grade"] if cr else "-",
                r.get("nat_score", "-"),
                r["status"],
                r.get("words", 0), r.get("word_target", 0),
                r.get("fix_attempts", 0),
                "Y" if r.get("self_audited") else "N",
                ";".join(r.get("failing_gates", [])),
            ])

    return result_file


def load_baseline() -> dict[str, dict] | None:
    """Load baseline results for comparison."""
    if not BASELINE_JSON.exists():
        return None
    with open(BASELINE_JSON) as f:
        baseline = json.load(f)
    return {f"{r['track']}-{r['slug']}": r for r in baseline}


def save_baseline(results: list[dict]):
    """Save current results as the baseline."""
    with open(BASELINE_JSON, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nBaseline saved: {BASELINE_JSON}")


def print_report(results: list[dict], baseline: dict[str, dict] | None = None):
    """Print summary table."""

    print(f"\n{'='*98}")
    print(f"  TESTBED RESULTS — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*98}")
    print(f"{'#':>3} {'Track':>5} {'Slug':<34} {'Audit':>5} {'Review':>6} {'Comb':>4} {'Nat':>3} {'Fix':>3} {'SA':>2} {'Words':>9} {'Delta':>6}")
    print(f"{'-'*3:>3} {'-'*5:>5} {'-'*34:<34} {'-'*5:>5} {'-'*6:>6} {'-'*4:>4} {'-'*3:>3} {'-'*3:>3} {'-'*2:>2} {'-'*9:>9} {'-'*6:>6}")

    a_count = 0
    total = 0

    for r in results:
        grade = r.get("grade", "?")
        key = f"{r['track']}-{r['slug']}"
        delta = ""
        if baseline and key in baseline:
            old_grade = baseline[key].get("grade", "?")
            if old_grade != grade:
                old_ord = GRADE_ORDER.get(old_grade, 9)
                new_ord = GRADE_ORDER.get(grade, 9)
                if new_ord < old_ord:
                    delta = f"+{old_grade}→{grade}"
                elif new_ord > old_ord:
                    delta = f"-{old_grade}→{grade}"
                else:
                    delta = "="
            else:
                delta = "="

        # Content review grade
        cr = r.get("content_review")
        review_str = cr["grade"] if cr else "-"

        comb = r.get("combined_grade", grade)
        words_str = f"{r.get('words', 0)}/{r.get('word_target', 0)}"
        sa_str = "Y" if r.get("self_audited") else "-"
        nat_str = str(r.get("nat_score", "-")) if r.get("nat_score") is not None else "-"
        slug_short = r['slug'][:34]
        print(f"{r['num']:>3} {r['track']:>5} {slug_short:<34} {grade:>5} {review_str:>6} {comb:>4} {nat_str:>3} {r.get('fix_attempts', 0):>3} {sa_str:>2} {words_str:>9} {delta:>6}")

        if grade == "A":
            a_count += 1
        if r["status"] != "NO_CONTENT":
            total += 1

    print(f"\n  Audit: {a_count}/{total} A-grade", end="")
    if baseline:
        old_a = sum(1 for r in baseline.values() if r.get("grade") == "A")
        old_total = sum(1 for r in baseline.values() if r.get("status") != "NO_CONTENT")
        diff = a_count - old_a
        print(f" (baseline: {old_a}/{old_total}, delta: {'+' if diff >= 0 else ''}{diff})", end="")

    # Self-audit summary
    sa_count = sum(1 for r in results if r.get("self_audited"))
    if total:
        print(f"\n  Self-audit: {sa_count}/{total} modules self-audited", end="")

    # Review summary
    reviewed = [r for r in results if r.get("content_review")]
    if reviewed:
        review_grades = [r["content_review"]["grade"] for r in reviewed]
        a_reviews = sum(1 for g in review_grades if g.startswith("A"))
        print(f"\n  Review: {a_reviews}/{len(reviewed)} A-grade (from content-review files)", end="")

    # Prompt review summary
    pr_modules = [r for r in results if r.get("prompt_review")]
    if pr_modules:
        healths = [r["prompt_review"]["health"] for r in pr_modules]
        good = sum(1 for h in healths if h == "GOOD")
        print(f"\n  Prompt: {good}/{len(pr_modules)} GOOD template health", end="")

    print("\n")


def cmd_build(args):
    """Build all testbed modules."""
    modules = load_config(track_filter=getattr(args, "track", None))
    restart_from = getattr(args, "restart_from", None)
    full = getattr(args, "full", False)

    print(f"\nBuilding {len(modules)} module(s)...\n")
    for mod in modules:
        build_module(mod, restart_from=restart_from, full=full)


def cmd_audit(args):
    """Audit all testbed modules and report."""
    modules = load_config(track_filter=getattr(args, "track", None))
    results = []

    for mod in modules:
        r = audit_module(mod)
        r["grade"] = grade_module(r)
        cr = r.get("content_review")
        review_grade = cr["grade"] if cr else None
        r["combined_grade"] = combined_grade(r["grade"], review_grade)
        results.append(r)

    run_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    result_file = save_results(results, run_id)
    baseline = load_baseline()
    print_report(results, baseline)
    print(f"  Results saved: {result_file}")

    return results


def cmd_review(args):
    """Run content-review + prompt-review on testbed modules."""
    modules = load_config(track_filter=getattr(args, "track", None))
    print(f"\nReviewing {len(modules)} module(s) (this uses Claude API calls)...\n")

    for mod in modules:
        review_result = review_module(mod)
        cr = review_result.get("content_review")
        pr = review_result.get("prompt_review")
        cr_grade = cr["grade"] if cr else "—"
        pr_health = pr["health"] if pr else "—"
        print(f"  {mod['track']} M{mod['num']} {mod['slug']}: "
              f"content={cr_grade} prompt={pr_health}")


def cmd_full(args):
    """Build + audit + [review] + report."""
    cmd_build(args)
    results = cmd_audit(args)

    # Optional review phase
    if getattr(args, "review", False):
        modules = load_config(track_filter=getattr(args, "track", None))
        print(f"\nRunning reviews ({len(modules)} modules)...\n")
        for i, mod in enumerate(modules):
            review_result = review_module(mod)
            # Update the audit result with fresh review data
            results[i]["content_review"] = review_result.get("content_review")
            results[i]["prompt_review"] = review_result.get("prompt_review")

    # Compute combined grades
    for r in results:
        cr = r.get("content_review")
        review_grade = cr["grade"] if cr else None
        r["combined_grade"] = combined_grade(r.get("grade", "N/A"), review_grade)

    # Regression check
    baseline = load_baseline()
    if baseline:
        for r in results:
            key = f"{r['track']}-{r['slug']}"
            if key in baseline:
                old_grade = baseline[key].get("grade", "?")
                new_grade = r.get("grade", "?")
                if GRADE_ORDER.get(new_grade, 9) > GRADE_ORDER.get(old_grade, 9):
                    print(f"  ⚠️  REGRESSION: {r['track']} M{r['num']} {r['slug']}: {old_grade} → {new_grade}")


def cmd_report(args):
    """Show latest results vs baseline."""
    # Find latest result file
    result_files = sorted(RESULTS_DIR.glob("*.json"))
    if not result_files:
        print("No results yet. Run 'audit' or 'full' first.")
        return

    with open(result_files[-1]) as f:
        results = json.load(f)

    baseline = load_baseline()
    print_report(results, baseline)


def cmd_baseline(args):
    """Save current audit results as baseline."""
    results = cmd_audit(args)
    save_baseline(results)


def find_regressions(results: list[dict], baseline: dict) -> list[str]:
    """Compare audit results against baseline, return list of regression descriptions."""
    regressions = []
    for r in results:
        key = f"{r['track']}-{r['slug']}"
        if key not in baseline:
            continue
        old_grade = baseline[key].get("grade", "?")
        new_grade = r.get("grade", "?")
        if GRADE_ORDER.get(new_grade, 9) > GRADE_ORDER.get(old_grade, 9):
            regressions.append(f"{r['track']} M{r['num']} {r['slug']}: {old_grade} → {new_grade}")
    return regressions


def cmd_check(args):
    """CI-friendly check: audit existing content and compare vs baseline.

    No builds, no API calls. Exits non-zero on regression.
    """
    baseline = load_baseline()
    if not baseline:
        print("ERROR: No baseline found. Run 'baseline' first.")
        sys.exit(1)

    modules = load_config(track_filter=getattr(args, "track", None))
    results = []
    for mod in modules:
        r = audit_module(mod)
        r["grade"] = grade_module(r)
        results.append(r)

    print_report(results, baseline)

    regressions = find_regressions(results, baseline)
    if regressions:
        print(f"\n{'='*60}")
        print(f"  REGRESSION DETECTED ({len(regressions)} module(s))")
        print(f"{'='*60}")
        for line in regressions:
            print(line)
        sys.exit(1)
    else:
        print("  ✅ No regressions vs baseline")


def main():
    parser = argparse.ArgumentParser(
        description="Testbed runner — regression testing for pipeline quality",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # build
    p_build = sub.add_parser("build", help="Build all testbed modules")
    p_build.add_argument("--restart-from", help="Restart from phase (e.g., sandbox, content)")
    p_build.add_argument("--full", action="store_true", help="Full rebuild from research (nuke state)")
    p_build.add_argument("--track", help="Filter by track (e.g., a1, a2, b1)")
    p_build.set_defaults(func=cmd_build)

    # audit
    p_audit = sub.add_parser("audit", help="Audit only (no builds)")
    p_audit.add_argument("--track", help="Filter by track (e.g., a1, a2, b1)")
    p_audit.set_defaults(func=cmd_audit)

    # review
    p_review = sub.add_parser("review", help="Run content-review + prompt-review (Claude API)")
    p_review.add_argument("--track", help="Filter by track (e.g., a1, a2, b1)")
    p_review.set_defaults(func=cmd_review)

    # full
    p_full = sub.add_parser("full", help="Build + audit + compare")
    p_full.add_argument("--restart-from", help="Restart from phase")
    p_full.add_argument("--full", action="store_true", help="Full rebuild from research")
    p_full.add_argument("--review", action="store_true", help="Include reviews after build+audit (expensive)")
    p_full.add_argument("--track", help="Filter by track (e.g., a1, a2, b1)")
    p_full.set_defaults(func=cmd_full)

    # report
    p_report = sub.add_parser("report", help="Show latest results")
    p_report.add_argument("--track", help="Filter by track (e.g., a1, a2, b1)")
    p_report.set_defaults(func=cmd_report)

    # baseline
    p_baseline = sub.add_parser("baseline", help="Save current results as baseline")
    p_baseline.add_argument("--track", help="Filter by track (e.g., a1, a2, b1)")
    p_baseline.set_defaults(func=cmd_baseline)

    # check (CI mode)
    p_check = sub.add_parser("check", help="CI mode: audit + compare vs baseline (no builds)")
    p_check.add_argument("--track", help="Filter by track (e.g., a1, a2, b1)")
    p_check.set_defaults(func=cmd_check)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
