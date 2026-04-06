#!/usr/bin/env python3
"""Claude Code token usage analyzer.

Adapted from kieranklaassen's gist. Analyzes ~/.claude/projects/ JSONL files
for token usage patterns across learn-ukrainian and kubedojo projects.

Usage:
    .venv/bin/python scripts/token_usage.py                # All time
    SINCE_DAYS=7 .venv/bin/python scripts/token_usage.py   # Last 7 days
    SINCE_DATE=2026-04-01 .venv/bin/python scripts/token_usage.py
"""

import json
import os
import sys
from collections import defaultdict
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

PROJECTS_DIR = Path.home() / ".claude" / "projects"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "docs" / "token-usage"

# Map directory prefixes to readable project names
PROJECT_MAP = {
    "-Users-krisztiankoos-projects-learn-ukrainian": "learn-ukrainian",
    "-Users-krisztiankoos-projects-kubedojo": "kubedojo",
}

# Filter: only include sessions within the last N days (None = all time)
SINCE_DAYS = int(os.environ.get("SINCE_DAYS", "0")) or None
SINCE_DATE = os.environ.get("SINCE_DATE")


def extract_text_content(content):
    """Extract text from message content (string or list)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    parts.append(item.get("text", ""))
            elif isinstance(item, str):
                parts.append(item)
        return "\n".join(parts).strip()
    return ""


def is_human_prompt(msg_obj):
    """Check if this is a human-originated prompt (not tool result)."""
    content = msg_obj.get("message", {}).get("content", "")
    if isinstance(content, list):
        types = [i.get("type") for i in content if isinstance(i, dict)]
        if types and all(t == "tool_result" for t in types):
            return False
    return True


def parse_session(jsonl_path, is_subagent=False):
    """Parse a single JSONL session file."""
    usage_total = defaultdict(int)
    prompts = []
    agent_id = None
    session_id = None
    timestamp_start = None
    timestamp_end = None
    model = None
    subagent_sessions = []

    try:
        with open(jsonl_path) as f:
            lines = f.readlines()
    except Exception:
        return None

    for line in lines:
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue

        msg_type = obj.get("type")
        ts = obj.get("timestamp")

        if ts:
            if not timestamp_start:
                timestamp_start = ts
            timestamp_end = ts

        if not agent_id:
            agent_id = obj.get("agentId")

        if not session_id:
            session_id = obj.get("sessionId")

        if msg_type == "assistant":
            msg = obj.get("message", {})
            usage = msg.get("usage", {})
            usage_total["input_tokens"] += usage.get("input_tokens", 0)
            usage_total["cache_creation_input_tokens"] += usage.get(
                "cache_creation_input_tokens", 0
            )
            usage_total["cache_read_input_tokens"] += usage.get(
                "cache_read_input_tokens", 0
            )
            usage_total["output_tokens"] += usage.get("output_tokens", 0)

            if not model and msg.get("model"):
                model = msg["model"]

        elif msg_type == "user":
            user_type = obj.get("userType", "")
            is_sidechain = obj.get("isSidechain", False)
            content = obj.get("message", {}).get("content", "")
            text = extract_text_content(content)

            if (
                text
                and not is_sidechain
                and is_human_prompt(obj)
                and user_type != "tool"
            ):
                prompts.append(
                    {
                        "text": text,
                        "timestamp": obj.get("timestamp"),
                        "entrypoint": obj.get("entrypoint", ""),
                    }
                )

    # Check for subagent sessions
    session_dir = jsonl_path.parent / jsonl_path.stem
    if session_dir.is_dir():
        subagents_dir = session_dir / "subagents"
        if subagents_dir.is_dir():
            for sub_file in sorted(subagents_dir.glob("*.jsonl")):
                sub_data = parse_session(sub_file, is_subagent=True)
                if sub_data:
                    sub_data["subagent_file"] = str(sub_file.name)
                    subagent_sessions.append(sub_data)

    total_tokens = sum(usage_total.values())

    return {
        "file": str(jsonl_path),
        "session_id": session_id or jsonl_path.stem,
        "agent_id": agent_id,
        "model": model,
        "is_subagent": is_subagent,
        "timestamp_start": timestamp_start,
        "timestamp_end": timestamp_end,
        "usage": dict(usage_total),
        "total_tokens": total_tokens,
        "prompts": prompts,
        "subagent_sessions": subagent_sessions,
    }


def resolve_project_name(dir_name):
    """Map directory name to readable project name, or None to skip."""
    for prefix, name in PROJECT_MAP.items():
        if dir_name.startswith(prefix):
            return name
    return None


def get_cutoff():
    """Return a UTC-aware datetime cutoff, or None for all time."""
    if SINCE_DATE:
        return datetime.fromisoformat(SINCE_DATE).replace(tzinfo=UTC)
    if SINCE_DAYS:
        return datetime.now(UTC) - timedelta(days=SINCE_DAYS)
    return None


def session_in_range(session, cutoff):
    """Check if session falls within the date range."""
    if not cutoff or not session["timestamp_start"]:
        return True
    try:
        ts = datetime.fromisoformat(
            session["timestamp_start"].replace("Z", "+00:00")
        )
        return ts >= cutoff
    except ValueError:
        return True


def analyze_all():
    """Analyze all tracked projects and sessions."""
    projects = defaultdict(list)
    cutoff = get_cutoff()

    for project_dir in sorted(PROJECTS_DIR.iterdir()):
        if not project_dir.is_dir():
            continue

        project_name = resolve_project_name(project_dir.name)
        if not project_name:
            continue

        for jsonl_file in sorted(project_dir.glob("*.jsonl")):
            session = parse_session(jsonl_file)
            if (
                session
                and session["total_tokens"] > 0
                and session_in_range(session, cutoff)
            ):
                projects[project_name].append(session)

    return projects


def fmt(n):
    """Format token count with commas."""
    return f"{n:,}"


def summarize_projects(projects):
    """Build per-project summary."""
    summaries = []

    for project_name, sessions in projects.items():
        total = defaultdict(int)
        all_subagent_tokens = 0
        subagent_count = 0

        for session in sessions:
            for k, v in session["usage"].items():
                total[k] += v
            for sub in session["subagent_sessions"]:
                all_subagent_tokens += sub["total_tokens"]
                subagent_count += 1

        summaries.append(
            {
                "project": project_name,
                "sessions": len(sessions),
                "usage": dict(total),
                "total_tokens": sum(total.values()),
                "subagent_tokens": all_subagent_tokens,
                "subagent_count": subagent_count,
            }
        )

    summaries.sort(key=lambda x: x["total_tokens"], reverse=True)
    return summaries


def find_costly_sessions(projects, top_n=20):
    """Find the most token-heavy sessions across all projects."""
    all_sessions = []
    for project_name, sessions in projects.items():
        for session in sessions:
            all_sessions.append((project_name, session))
    all_sessions.sort(key=lambda x: x[1]["total_tokens"], reverse=True)
    return all_sessions[:top_n]


def find_costly_subagents(projects, top_n=20):
    """Find the most token-heavy subagent sessions."""
    all_subs = []
    for project_name, sessions in projects.items():
        for session in sessions:
            for sub in session["subagent_sessions"]:
                all_subs.append((project_name, session["session_id"], sub))
    all_subs.sort(key=lambda x: x[2]["total_tokens"], reverse=True)
    return all_subs[:top_n]


def daily_breakdown(projects):
    """Compute per-day token usage per project."""
    daily = defaultdict(lambda: defaultdict(int))

    for project_name, sessions in projects.items():
        for session in sessions:
            if not session["timestamp_start"]:
                continue
            try:
                day = session["timestamp_start"][:10]
            except (IndexError, TypeError):
                continue
            daily[day][project_name] += session["total_tokens"]
            # Include subagent tokens
            for sub in session["subagent_sessions"]:
                daily[day][project_name] += sub["total_tokens"]

    return dict(sorted(daily.items()))


def write_report(projects, summaries):
    """Write the analysis report."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = OUTPUT_DIR / "token_report.md"

    lines = []
    cutoff = get_cutoff()
    date_range = (
        f"Since {cutoff.strftime('%Y-%m-%d')}" if cutoff else "All time"
    )

    lines.append("# Claude Code Token Usage")
    lines.append(
        f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        f" | Range: {date_range}\n"
    )

    # Grand totals
    grand_input = sum(
        s["usage"].get("input_tokens", 0) for s in summaries
    )
    grand_cache_create = sum(
        s["usage"].get("cache_creation_input_tokens", 0) for s in summaries
    )
    grand_cache_read = sum(
        s["usage"].get("cache_read_input_tokens", 0) for s in summaries
    )
    grand_output = sum(
        s["usage"].get("output_tokens", 0) for s in summaries
    )
    grand_total = sum(s["total_tokens"] for s in summaries)
    total_sessions = sum(s["sessions"] for s in summaries)
    total_subagent_tokens = sum(s["subagent_tokens"] for s in summaries)
    total_subagent_count = sum(s["subagent_count"] for s in summaries)

    lines.append("## Grand Totals\n")
    lines.append(f"- **Projects**: {len(summaries)}")
    lines.append(f"- **Sessions**: {total_sessions:,}")
    lines.append(f"- **Total tokens**: {fmt(grand_total)}")
    lines.append(f"  - Input: {fmt(grand_input)}")
    lines.append(f"  - Cache creation: {fmt(grand_cache_create)}")
    lines.append(f"  - Cache read: {fmt(grand_cache_read)}")
    lines.append(f"  - Output: {fmt(grand_output)}")
    lines.append(
        f"- **Subagent sessions**: {total_subagent_count:,}"
        f" ({fmt(total_subagent_tokens)} tokens)"
    )
    lines.append("")

    # Per-project breakdown
    lines.append("## By Project\n")
    lines.append(
        "| Project | Sessions | Total | Input | Cache Create"
        " | Cache Read | Output | Subagents |"
    )
    lines.append(
        "|---------|----------|-------|-------|--------------|"
        "------------|--------|-----------|"
    )

    for s in summaries:
        u = s["usage"]
        lines.append(
            f"| {s['project']} | {s['sessions']}"
            f" | {fmt(s['total_tokens'])}"
            f" | {fmt(u.get('input_tokens', 0))}"
            f" | {fmt(u.get('cache_creation_input_tokens', 0))}"
            f" | {fmt(u.get('cache_read_input_tokens', 0))}"
            f" | {fmt(u.get('output_tokens', 0))}"
            f" | {s['subagent_count']} ({fmt(s['subagent_tokens'])}) |"
        )
    lines.append("")

    # Daily breakdown
    daily = daily_breakdown(projects)
    if daily:
        lines.append("## Daily Usage\n")
        project_names = sorted(
            {p for d in daily.values() for p in d}
        )
        header = "| Date | " + " | ".join(project_names) + " | Total |"
        sep = "|------|" + "|".join(["------"] * len(project_names)) + "|-------|"
        lines.append(header)
        lines.append(sep)

        for day, proj_tokens in daily.items():
            day_total = sum(proj_tokens.values())
            cols = " | ".join(
                fmt(proj_tokens.get(p, 0)) for p in project_names
            )
            lines.append(f"| {day} | {cols} | {fmt(day_total)} |")
        lines.append("")

    # Most costly sessions
    lines.append("## Most Costly Sessions (Top 25)\n")
    costly = find_costly_sessions(projects, top_n=25)

    for i, (proj, session) in enumerate(costly, 1):
        model_str = f" ({session['model']})" if session.get("model") else ""
        lines.append(
            f"### {i}. {proj}{model_str}"
            f" — {fmt(session['total_tokens'])} tokens"
        )
        lines.append(f"- **Session**: `{session['session_id']}`")

        if session["timestamp_start"]:
            lines.append(
                f"- **Started**: "
                f"{session['timestamp_start'][:19].replace('T', ' ')}"
            )

        u = session["usage"]
        lines.append(
            f"- **Tokens**: input={fmt(u.get('input_tokens', 0))},"
            f" cache_create={fmt(u.get('cache_creation_input_tokens', 0))},"
            f" cache_read={fmt(u.get('cache_read_input_tokens', 0))},"
            f" output={fmt(u.get('output_tokens', 0))}"
        )
        lines.append(
            f"- **Subagents in session**: {len(session['subagent_sessions'])}"
        )

        if session["prompts"]:
            first = session["prompts"][0]["text"][:400].replace("\n", " ")
            lines.append(f"- **First prompt**: {first}")
        lines.append("")

    # Most costly subagents
    lines.append("## Most Costly Subagents (Top 20)\n")
    costly_subs = find_costly_subagents(projects, top_n=20)

    lines.append(
        "| # | Project | Parent Session | Subagent File"
        " | Total Tokens | Input | Output |"
    )
    lines.append(
        "|---|---------|----------------|---------------|"
        "--------------|-------|--------|"
    )

    for i, (proj, parent_id, sub) in enumerate(costly_subs, 1):
        u = sub["usage"]
        all_input = (
            u.get("input_tokens", 0)
            + u.get("cache_creation_input_tokens", 0)
            + u.get("cache_read_input_tokens", 0)
        )
        lines.append(
            f"| {i} | {proj} | `{parent_id[:8]}...`"
            f" | `{sub.get('subagent_file', '?')}`"
            f" | {fmt(sub['total_tokens'])}"
            f" | {fmt(all_input)}"
            f" | {fmt(u.get('output_tokens', 0))} |"
        )
    lines.append("")

    with open(report_path, "w") as f:
        f.write("\n".join(lines))

    print(f"Report written: {report_path}")
    return report_path


def print_summary(summaries, projects):
    """Print a quick summary to stdout."""
    grand_total = sum(s["total_tokens"] for s in summaries)
    total_sessions = sum(s["sessions"] for s in summaries)

    print(
        f"\nTotal: {fmt(grand_total)} tokens across"
        f" {total_sessions} sessions in {len(summaries)} projects\n"
    )

    print(
        f"{'Project':<30} {'Sessions':>8}"
        f" {'Total Tokens':>14} {'Subagents':>10}"
    )
    print("-" * 66)

    for s in summaries:
        print(
            f"{s['project']:<30} {s['sessions']:>8,}"
            f" {fmt(s['total_tokens']):>14} {s['subagent_count']:>10,}"
        )

    print("\nTop 10 costliest sessions:")
    for proj, session in find_costly_sessions(projects, top_n=10):
        ts = (
            session["timestamp_start"][:10]
            if session["timestamp_start"]
            else "?"
        )
        first_prompt = ""
        if session["prompts"]:
            first_prompt = (
                session["prompts"][0]["text"][:80].replace("\n", " ")
            )
        print(
            f"  [{ts}] {proj}: {fmt(session['total_tokens'])}"
            f" — {first_prompt}"
        )


def main():
    print("Scanning projects...")
    projects = analyze_all()
    print(f"Found {len(projects)} projects")

    if not projects:
        print("No matching sessions found.")
        sys.exit(0)

    summaries = summarize_projects(projects)
    print_summary(summaries, projects)
    write_report(projects, summaries)
    print(f"\nFull report: {OUTPUT_DIR / 'token_report.md'}")


if __name__ == "__main__":
    main()
