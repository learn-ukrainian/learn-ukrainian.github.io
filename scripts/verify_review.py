from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

FINDING_RE = re.compile(r"(?ms)^FINDING:\s*\n(?P<body>.*?)(?=^FINDING:|\Z)")
QUOTE_RE = re.compile(
    r"^CURRENT CODE \(verbatim from branch\):\s*```(?:\w+)?\n(?P<quote>.*?)\n```",
    re.M | re.S,
)


def _run(cmd: list[str], input_text: str | None = None) -> str:
    return subprocess.run(
        cmd, check=True, capture_output=True, text=True, input=input_text
    ).stdout


def _read_review(issue: int | None, from_stdin: bool) -> str:
    if from_stdin:
        return sys.stdin.read()
    data = json.loads(_run(["gh", "issue", "view", str(issue), "--json", "comments"]))
    comments = data.get("comments") or []
    return comments[-1]["body"] if comments else ""


def _normalize_lines(text: str) -> list[tuple[int, str]]:
    rows = []
    for line_no, raw in enumerate(text.replace("```", "").replace("`", "").splitlines(), start=1):
        clean = " ".join(raw.strip().split())
        if clean:
            rows.append((line_no, clean))
    return rows


def _parse_finding(body: str, finding_id: int) -> dict[str, object]:
    line_match = re.search(r"^FILE:LINE:\s*(.+):(\d+)\s*$", body, re.M)
    quote_match = QUOTE_RE.search(body)
    missing = [
        name
        for name, ok in (
            ("file_line", bool(line_match)),
            ("current_code", bool(quote_match)),
            ("why_wrong", bool(re.search(r"^WHY WRONG:\s*$", body, re.M))),
            ("fix", bool(re.search(r"^FIX:\s*$", body, re.M))),
            ("severity", bool(re.search(r"^SEVERITY:\s*(blocker|major|minor|nit)\s*$", body, re.M))),
        )
        if not ok
    ]
    if missing:
        return {"finding_id": finding_id, "outcome": "discarded", "reason": f"missing_fields:{','.join(missing)}"}
    return {
        "finding_id": finding_id,
        "file": line_match.group(1),
        "line": int(line_match.group(2)),
        "quote": quote_match.group("quote"),
    }


def _load_file(path: str, branch: str | None) -> str:
    return _run(["git", "show", f"{branch}:{path}"]) if branch else Path(path).read_text("utf-8")


def _verify_finding(finding: dict[str, object], branch: str | None) -> dict[str, object]:
    if finding.get("outcome") == "discarded":
        return finding
    try:
        file_rows = _normalize_lines(_load_file(str(finding["file"]), branch))
    except Exception as exc:
        return {**finding, "outcome": "quote_missing", "evidence": f"file_unavailable:{exc}"}
    quote_rows = [text for _, text in _normalize_lines(str(finding["quote"]))]
    start = next(
        (
            i
            for i in range(len(file_rows) - len(quote_rows) + 1)
            if [text for _, text in file_rows[i:i + len(quote_rows)]] == quote_rows
        ),
        -1,
    )
    if start < 0:
        return {**finding, "outcome": "quote_missing", "evidence": "normalized_quote_not_found"}
    actual_line = file_rows[start][0]
    outcome = "verified" if actual_line == finding["line"] else "line_mismatch"
    return {**finding, "outcome": outcome, "evidence": f"matched_at_line:{actual_line}"}


def _post_summary(issue: int, results: list[dict[str, object]]) -> None:
    counts: dict[str, int] = {}
    for result in results:
        counts[str(result["outcome"])] = counts.get(str(result["outcome"]), 0) + 1
    lines = [f"verify_review summary for latest comment on #{issue}:"]
    lines.extend(f"- {name}: {counts.get(name, 0)}" for name in ("verified", "line_mismatch", "quote_missing", "discarded"))
    _run(["gh", "issue", "comment", str(issue), "--body", "\n".join(lines)])


def main() -> int:
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--issue", type=int)
    source.add_argument("--from-stdin", action="store_true")
    parser.add_argument("--branch")
    parser.add_argument("--post-comment", action="store_true")
    args = parser.parse_args()
    if args.post_comment and args.issue is None:
        parser.error("--post-comment requires --issue")

    review = _read_review(args.issue, args.from_stdin)
    results = [_verify_finding(_parse_finding(m.group("body"), i), args.branch) for i, m in enumerate(FINDING_RE.finditer(review), start=1)]
    for result in results:
        print(json.dumps(result, ensure_ascii=False))
    if args.post_comment:
        _post_summary(args.issue, results)
    return 1 if any(result["outcome"] == "quote_missing" for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
