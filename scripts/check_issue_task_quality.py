#!/usr/bin/env python3
"""Advisory task-quality checker for GitHub issue / brief bodies (#7854).

Fail-open by default: prints PASS or WARN and exits 0. Use --strict to exit 1
on WARN. Does not invent a control plane; nests under docs/best-practices/task-quality.md.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass

HTML_COMMENT_RE = re.compile(r"(?s)<!--.*?-->")
PLACEHOLDER_RE = re.compile(
    r"(?i)^(?:todo|tbd|n/?a|…|\.\.\.|\[.*\]|<.*>|criterion \d+|path/to/)\s*$"
)
EXPLICIT_NONE_RE = re.compile(r"(?i)^(?:none|n/?a|na)\s*(?:[—\-].*)?$")
TERMINAL_GOALS = ("merge", "deploy", "certify", "decision-only", "audit-only")


@dataclass(frozen=True)
class FieldCheck:
    key: str
    label: str
    heading: re.Pattern[str]


# Locate sections by heading; values must be substantive (not empty/placeholder).
FIELDS: tuple[FieldCheck, ...] = (
    FieldCheck(
        "outcome",
        "user-visible outcome / what",
        re.compile(
            r"(?im)^#{1,3}\s*(?:user[- ]visible\s+outcome|outcome|overview|problem(?:\s+statement)?)\s*$"
            r"|^\*\*what\*\*\s*:"
        ),
    ),
    FieldCheck(
        "why",
        "why / evidence",
        re.compile(r"(?im)^#{1,3}\s*(?:why(?:\s*/\s*evidence)?|evidence|repro)\s*$"),
    ),
    FieldCheck(
        "in_scope",
        "in scope / paths",
        re.compile(r"(?im)^#{1,3}\s*(?:in\s+scope|scope|affected)\s*$"),
    ),
    FieldCheck(
        "non_goals",
        "non-goals / out of scope",
        re.compile(r"(?im)^#{1,3}\s*(?:non[- ]goals?|out of scope)\s*$"),
    ),
    FieldCheck(
        "denominator",
        "denominator / scope size",
        re.compile(r"(?im)^#{1,3}\s*(?:denominator)\s*$"),
    ),
    FieldCheck(
        "verify",
        "verify commands / held-out check",
        re.compile(r"(?im)^#{1,3}\s*(?:verify|verification|test plan)\s*$"),
    ),
    FieldCheck(
        "deps",
        "dependencies (or explicit none)",
        re.compile(r"(?im)^#{1,3}\s*(?:deps|dependencies|blockers)\s*$"),
    ),
    FieldCheck(
        "dod",
        "definition of done / acceptance criteria",
        re.compile(
            r"(?im)^#{1,3}\s*(?:definition of done|acceptance criteria(?:\s*/\s*definition of done)?|done)\s*$"
        ),
    ),
    FieldCheck(
        "terminal_goal",
        "terminal goal (merge|deploy|certify|decision-only|audit-only)",
        re.compile(r"(?im)^#{1,3}\s*(?:terminal goal)\s*$"),
    ),
    FieldCheck(
        "residual",
        "residual / leftover owner",
        re.compile(r"(?im)^#{1,3}\s*(?:residual|leftovers?)\s*$"),
    ),
)

TRIVIAL_RE = re.compile(
    r"(?im)^(?:\*\*)?(?:trivial|typo-only|single-line)(?:\*\*)?\s*:\s*(?:yes|true|exempt)\b"
    r"|^(?:trivial|typo-only)\s+fix\b"
)
HEADING_LINE_RE = re.compile(r"(?m)^(#{1,6}\s+\S.*|\*\*[^*]+\*\*\s*:.*)$")


def _strip_noise(text: str) -> str:
    return HTML_COMMENT_RE.sub("", text or "")


def _section_body(text: str, heading: re.Pattern[str]) -> str | None:
    match = heading.search(text)
    if not match:
        return None
    rest = text[match.end() :]
    next_heading = HEADING_LINE_RE.search(rest)
    chunk = rest if next_heading is None else rest[: next_heading.start()]
    return chunk.strip()


def _substantive(chunk: str | None, *, allow_none: bool = False) -> bool:
    if chunk is None:
        return False
    lines = []
    for raw in chunk.splitlines():
        stripped = raw.strip()
        if not stripped:
            continue
        if re.match(r"^(```|~~~)", stripped):
            continue
        # Markdown headings / hash comments; keep "#1234" issue refs.
        if (
            stripped.startswith("#")
            and not re.match(r"^#\d", stripped)
            and re.match(r"^#{1,6}(?:\s|$)", stripped)
        ):
            continue
        line = stripped.lstrip("-* ").strip()
        line = re.sub(r"^\[\s*[xX ]\s*\]\s*", "", line).strip()
        if not line or line in {"```", "~~~"}:
            continue
        # Bare fence language tags are not content.
        if re.fullmatch(r"[a-zA-Z0-9_+-]+", line) and re.match(
            r"^(```|~~~)", raw.strip()
        ):
            continue
        if allow_none and EXPLICIT_NONE_RE.match(line):
            lines.append(line)
            continue
        if PLACEHOLDER_RE.match(line):
            continue
        lines.append(line)
    return bool(lines)


def _terminal_goal_ok(chunk: str | None) -> bool:
    if not chunk:
        return False
    lowered = chunk.lower()
    return any(re.search(rf"(?i)\b{re.escape(goal)}\b", lowered) for goal in TERMINAL_GOALS)


def score_body(body: str, *, trivial: bool = False) -> dict[str, object]:
    text = _strip_noise(body or "")
    if trivial or TRIVIAL_RE.search(text):
        return {
            "verdict": "PASS",
            "trivial": True,
            "missing": [],
            "present": [f.key for f in FIELDS],
            "notes": ["trivial exemption — full card not required"],
        }

    missing: list[str] = []
    present: list[str] = []
    for field in FIELDS:
        chunk = _section_body(text, field.heading)
        if field.key == "terminal_goal":
            ok = _terminal_goal_ok(chunk)
        else:
            ok = _substantive(
                chunk, allow_none=field.key in {"deps", "residual", "non_goals"}
            )
        if ok:
            present.append(field.key)
        else:
            missing.append(field.key)

    verdict = "PASS" if not missing else "WARN"
    return {
        "verdict": verdict,
        "trivial": False,
        "missing": missing,
        "present": present,
        "notes": [],
    }


def _fetch_issue_body(repo: str, number: int) -> str:
    raw = subprocess.check_output(
        [
            "gh",
            "issue",
            "view",
            str(number),
            "-R",
            repo,
            "--json",
            "body,title,labels",
        ],
        text=True,
        timeout=60,
    )
    data = json.loads(raw)
    labels = " ".join(label.get("name", "") for label in data.get("labels") or [])
    return f"{data.get('title') or ''}\n{labels}\n{data.get('body') or ''}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Advisory DoR/DoD field check for an issue body (#7854)."
    )
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--issue", type=int, help="GitHub issue number (uses gh)")
    src.add_argument("--body-file", type=str, help="Path to markdown body")
    src.add_argument("--body", type=str, help="Inline markdown body")
    parser.add_argument(
        "--repo",
        default="learn-ukrainian/learn-ukrainian.github.io",
        help="owner/repo for --issue",
    )
    parser.add_argument(
        "--trivial",
        action="store_true",
        help="Treat as trivial exempt even without the word in the body",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 on WARN (default: always 0 — fail-open advisory)",
    )
    parser.add_argument("--json", action="store_true", help="Machine-readable result")
    args = parser.parse_args(argv)

    try:
        if args.issue is not None:
            body = _fetch_issue_body(args.repo, args.issue)
        elif args.body_file:
            with open(args.body_file, encoding="utf-8") as handle:
                body = handle.read()
        else:
            body = args.body or ""
        result = score_body(body, trivial=args.trivial)
    except (
        OSError,
        subprocess.SubprocessError,
        json.JSONDecodeError,
        UnicodeError,
        ValueError,
    ) as exc:
        result = {
            "verdict": "WARN",
            "trivial": False,
            "missing": ["input"],
            "present": [],
            "notes": [f"input_error:{type(exc).__name__}:{exc}"],
        }

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"verdict={result['verdict']}")
        if result["trivial"]:
            print("trivial=true")
        if result["missing"]:
            print("missing=" + ",".join(str(x) for x in result["missing"]))
        if result["present"]:
            print("present=" + ",".join(str(x) for x in result["present"]))
        for note in result["notes"]:
            print(f"note={note}")
        print("canonical=docs/best-practices/task-quality.md")

    if args.strict and result["verdict"] == "WARN":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
