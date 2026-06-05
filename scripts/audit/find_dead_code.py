import argparse
import datetime
import subprocess
from pathlib import Path

# Directory NAMES never walked by the filesystem scanners (categories A/B/F).
# Critically includes `.worktrees`: live dispatch worktrees are full repo
# copies, so scanning them multiplies every hit by the number of active
# worktrees (observed 2026-06-06: 11 worktrees → 77% of the report was
# `.worktrees/` noise). `archive` is the Phase-4 holding pen for already-
# triaged deletions — re-reporting it as "dead code" is pure noise. The other
# names are virtualenvs / vendored deps / VCS internals.
EXCLUDE_DIR_NAMES = (
    ".venv",
    "embed-venv",
    "node_modules",
    "site-packages",
    ".git",
    ".worktrees",
    "archive",
)


def _is_excluded(path: Path) -> bool:
    """True if any path component is an excluded directory name."""
    return any(part in EXCLUDE_DIR_NAMES for part in path.parts)


def _ugrep_exclude_flags() -> list[str]:
    """`--exclude-dir=<name>` flags for every excluded directory."""
    return [f"--exclude-dir={name}" for name in EXCLUDE_DIR_NAMES]


def _vulture_exclude_glob() -> str:
    """Comma-joined `*/<name>/*` globs for vulture's --exclude."""
    return ",".join(f"*/{name}/*" for name in EXCLUDE_DIR_NAMES)


def run_cmd(cmd, cwd=None):
    try:
        res = subprocess.run(cmd, cwd=cwd, shell=isinstance(cmd, str), capture_output=True, text=True, check=False)
        return res
    except FileNotFoundError:
        return None


def category_a(root: Path):
    hits = []
    try:
        for p in root.rglob("*.py"):
            if _is_excluded(p):
                continue
            try:
                content = p.read_text(encoding="utf-8")
                if "OBSOLETE" in content:
                    # check for callers
                    stem = p.stem
                    cmd = [
                        "ugrep",
                        "-rlw",
                        stem,
                        str(root),
                        *_ugrep_exclude_flags(),
                    ]
                    res = run_cmd(cmd)
                    if res and res.stdout.strip():
                        callers = res.stdout.strip().splitlines()
                        callers = [c for c in callers if str(p) not in c and "__pycache__" not in c]
                        if callers:
                            hits.append(f"{p.relative_to(root)} (has callers: {len(callers)})")
                        else:
                            hits.append(f"{p.relative_to(root)} (no live callers found)")
                    else:
                        hits.append(f"{p.relative_to(root)} (no live callers found)")
            except Exception:
                pass
    except Exception:
        pass
    return hits


def category_b(root: Path):
    vulture_path = root / ".venv" / "bin" / "vulture"
    if not vulture_path.exists():
        return ["NEEDS-MANUAL-REVIEW: vulture-unavailable"]
    res = run_cmd(
        [
            str(vulture_path),
            str(root),
            "--min-confidence",
            "80",
            "--exclude",
            _vulture_exclude_glob(),
        ]
    )
    if not res:
        return ["NEEDS-MANUAL-REVIEW: vulture failed to run"]
    lines = res.stdout.strip().splitlines()
    return lines


def category_c(root: Path):
    docs_dir = root / "docs"
    if not docs_dir.exists():
        return []
    cmd = [
        "ugrep",
        "-rnE",
        "v6_build|pipeline_v5",
        str(docs_dir),
        "--exclude-dir=bug-autopsies",
        "--exclude-dir=session-state",
    ]
    res = run_cmd(cmd)
    if not res or not res.stdout.strip():
        return []
    hits = []
    for line in res.stdout.strip().splitlines():
        hits.append(line.replace(str(root) + "/", ""))
    return hits


def category_d(root: Path):
    res = run_cmd(["git", "ls-files"], cwd=root)
    hits = []
    if res and res.stdout.strip():
        for line in res.stdout.strip().splitlines():
            if line.endswith(".bak") or line.endswith(".orig") or line.endswith(".coverage") or ".coverage" in line:
                hits.append(line)

    # Tracked files that ALSO match a .gitignore rule. `-c` is required with
    # `-i` (else git errors). In this repo broad dir-level ignores overlap many
    # tracked files, so summarize when the list is large rather than flooding
    # the report.
    res2 = run_cmd(["git", "ls-files", "-i", "-c", "--exclude-standard"], cwd=root)
    if res2 and res2.stdout.strip():
        ignored = res2.stdout.strip().splitlines()
        if len(ignored) > 25:
            hits.append(
                f"NEEDS-MANUAL-REVIEW: {len(ignored)} tracked files match .gitignore "
                "patterns (likely broad dir-level ignores; audit .gitignore vs the "
                "tracked tree). First 20 shown:"
            )
            hits.extend(f"{line} (tracked but matches .gitignore)" for line in ignored[:20])
        else:
            hits.extend(f"{line} (tracked but matches .gitignore)" for line in ignored)
    return list(dict.fromkeys(hits))


def category_e(root: Path):
    ss_dir = root / "docs" / "session-state"
    if not ss_dir.exists():
        return []
    hits = []
    threshold = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=30)
    for p in list(ss_dir.glob("*.md")) + list(ss_dir.glob("*.html")):
        if p.name.startswith("current") or "router" in p.name:
            continue
        res = run_cmd(["git", "log", "-1", "--format=%cs", "--", str(p)], cwd=root)
        if res and res.stdout.strip():
            try:
                date_str = res.stdout.strip()
                file_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=datetime.UTC)
                if file_date < threshold:
                    hits.append(f"{p.relative_to(root)} (last commit: {date_str})")
            except ValueError:
                pass
    return hits


def category_f(root: Path):
    hits = ["NEEDS-MANUAL-REVIEW: Candidates for orphaned orchestration artifacts:"]
    for d in root.rglob("orchestration"):
        if (
            d.is_dir()
            and not _is_excluded(d)
            and not (d / "status.json").exists()
            and not (d.parent / "status.json").exists()
        ):
            hits.append(str(d.relative_to(root)))
    if len(hits) == 1:
        hits.append("No obvious candidates found.")
    return hits


def category_g(root: Path):
    scripts_dir = root / "scripts"
    if not scripts_dir.exists():
        return []
    seen = {}
    hits = []
    for p in scripts_dir.rglob("*.py"):
        if p.is_file() and p.name not in {"__init__.py", "__main__.py", "conftest.py"}:
            if p.name in seen:
                hits.append(f"Collision: {p.relative_to(root)} shares basename with {seen[p.name]}")
            else:
                seen[p.name] = p.relative_to(root)
    return hits


def category_h(root: Path):
    exp_dir = root / "experiments"
    if not exp_dir.exists():
        return []
    hits = []
    threshold = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=180)
    for p in exp_dir.iterdir():
        if p.is_dir():
            res = run_cmd(["git", "log", "-1", "--format=%cs", "--", str(p)], cwd=root)
            if res and res.stdout.strip():
                try:
                    date_str = res.stdout.strip()
                    file_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=datetime.UTC)
                    if file_date < threshold:
                        hits.append(f"{p.relative_to(root)} (last commit: {date_str})")
                except ValueError:
                    pass
    return hits


def category_i(root: Path):
    audit_dir = root / "audit"
    if not audit_dir.exists():
        return []
    jsons = list(audit_dir.rglob("*.json"))
    if not jsons:
        return ["NEEDS-MANUAL-REVIEW: No audit JSONs found."]

    ages = []
    for p in jsons:
        res = run_cmd(["git", "log", "-1", "--format=%cs", "--", str(p)], cwd=root)
        date_str = res.stdout.strip() if res and res.stdout.strip() else "1970-01-01"
        ages.append((date_str, p))
    ages.sort(key=lambda x: x[0])

    hits = ["NEEDS-MANUAL-REVIEW: Oldest audit JSONs for manual schema check:"]
    for date_str, p in ages[:5]:
        hits.append(f"{p.relative_to(root)} (last commit: {date_str})")
    return hits


def category_j(root: Path):
    hits = ["NEEDS-MANUAL-REVIEW: All files under tests/fixtures/ (inventory, not staleness-filtered):"]
    fixtures_dir = root / "tests" / "fixtures"
    if fixtures_dir.exists():
        for p in fixtures_dir.rglob("*"):
            if p.is_file():
                hits.append(f"{p.relative_to(root)}")
    else:
        hits.append("No tests/fixtures directory found.")
    return hits


def main():
    parser = argparse.ArgumentParser(description="Dead-code and stale inventory tool (REPORT-ONLY).")
    parser.add_argument("--root", type=str, default=".", help="Root directory of the repository")
    default_output = f"audit/cleanup-inventory-{datetime.datetime.now().strftime('%Y-%m-%d')}.md"
    parser.add_argument("--output", type=str, default=default_output, help="Path to write the report markdown file")

    args = parser.parse_args()
    root = Path(args.root).resolve()

    print(f"Scanning repository at {root}...")

    categories = {
        "A Marked-obsolete code (M)": (category_a, "Grep for OBSOLETE banners; check live callers via ugrep."),
        "B Dead Python (L)": (
            category_b,
            "vulture --min-confidence 80 (excludes .venv/embed-venv/node_modules/site-packages/.git/.worktrees/archive).",
        ),
        "C Stale docs (L)": (category_c, "ugrep v6_build|pipeline_v5 in docs/ excluding specific subdirs."),
        "D Generated artifacts that escaped (L)": (
            category_d,
            "git ls-files intersected with *.bak, .coverage, *.orig, and ignored files.",
        ),
        "E Old session-state (L)": (category_e, "docs/session-state older than 30 days by git-commit date."),
        "F Orphaned orchestration artifacts (M)": (
            category_f,
            "Per-module orchestration dirs with no matching status.json.",
        ),
        "G Basename collisions across scripts/ (H)": (
            category_g,
            "Files sharing a basename in different subdirs — may indicate incomplete renames OR legitimate module reuse.",
        ),
        "H Stale experiments/ (L)": (category_h, "experiments/ dirs whose last git commit is >180 days old."),
        "I Old audit JSONs (M)": (category_i, "Oldest audit JSONs sorted by git-commit date."),
        "J Test fixtures inventory (H)": (category_j, "All files under tests/fixtures/ for manual review (no staleness filter)."),
    }

    results = {}
    counts = {}
    total_hits = 0

    for name, (func, method_desc) in categories.items():
        hits = func(root)
        # Deterministic ordering for stable diffs across quarterly re-runs:
        # keep NEEDS-MANUAL-REVIEW / "No ..." header lines first, sort the rest.
        hits = sorted(hits, key=lambda h: (not h.startswith(("NEEDS-MANUAL-REVIEW", "No ")), h))
        results[name] = {"desc": method_desc, "hits": hits}
        count = len(
            [
                h
                for h in hits
                if not h.startswith("NEEDS-MANUAL-REVIEW")
                and not h.startswith("No obvious candidates")
                and not h.startswith("No tests/fixtures")
            ]
        )
        counts[name] = count
        total_hits += count
        print(f"  {name}: {count} hits")

    # Generate report
    report = []
    report.append("# Repo Cleanup Inventory Report")
    report.append(f"**Generation Timestamp:** {datetime.datetime.now(datetime.UTC).isoformat()}")
    report.append(f"**Total Hits:** {total_hits}")
    report.append("")
    report.append("## Per-Category Counts")
    for name, count in counts.items():
        report.append(f"- **{name}**: {count}")
    report.append("")

    for name, data in results.items():
        risk = ""
        if "(H)" in name:
            risk = "🚨 **HIGH RISK** - Needs adversarial review + smoke build + manual sanity check."
        elif "(M)" in name:
            risk = "⚠️ **MEDIUM RISK** - Needs adversarial review."

        report.append(f"## {name}")
        if risk:
            report.append(risk)
        report.append(f"**Method:** {data['desc']}")
        report.append("")
        if data["hits"]:
            for hit in data["hits"]:
                report.append(f"- {hit}")
        else:
            report.append("- *No hits found.*")
        report.append("")

    out_path = Path(args.output)
    if not out_path.is_absolute():
        out_path = root / out_path

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(report), encoding="utf-8")
    print(f"Report written to {out_path}")


if __name__ == "__main__":
    main()
