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


@dataclass(frozen=True)
class FieldCheck:
    key: str
    label: str
    pattern: re.Pattern[str]


# Coarse, intentional: catch missing *concepts*, not enforce one heading style.
FIELDS: tuple[FieldCheck, ...] = (
    FieldCheck(
        "outcome",
        "user-visible outcome / what",
        re.compile(
            r"(?is)(user[- ]visible\s+outcome|\*\*what\*\*|##\s*(outcome|overview|problem(\s+statement)?)\b)"
        ),
    ),
    FieldCheck(
        "non_goals",
        "non-goals / out of scope",
        re.compile(r"(?is)(non[- ]goals?|out of scope|do not (?:do|file|start))"),
    ),
    FieldCheck(
        "denominator",
        "denominator / scope size",
        re.compile(r"(?is)(denominator|##\s*affected\b|n\s*[≥>=]\s*\d+|sample of)"),
    ),
    FieldCheck(
        "verify",
        "verify commands / held-out check",
        re.compile(
            r"(?is)(##\s*verify\b|verify:|held-out|```(?:bash|shell|text)?\n|\.venv/bin/python|pytest )"
        ),
    ),
    FieldCheck(
        "dod",
        "definition of done / acceptance criteria",
        re.compile(r"(?is)(definition of done|acceptance criteria|##\s*done\b)"),
    ),
    FieldCheck(
        "terminal_goal",
        "terminal goal (merge|deploy|certify|decision-only|audit-only)",
        re.compile(
            r"(?is)(terminal goal|\bmerge\b.*\bdeploy\b|\bcertify\b|decision-only|audit-only)"
        ),
    ),
    FieldCheck(
        "residual",
        "residual / leftover owner",
        re.compile(r"(?is)(residual|leftover|follow[- ]up owner|owner:)"),
    ),
)

# Only explicit markers — do not match prose that merely discusses trivial work.
TRIVIAL_RE = re.compile(
    r"(?im)^(?:\*\*)?(?:trivial|typo-only|single-line)(?:\*\*)?\s*:\s*(?:yes|true|exempt)\b"
    r"|^(?:trivial|typo-only)\s+fix\b"
)


def score_body(body: str, *, trivial: bool = False) -> dict[str, object]:
    text = body or ""
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
        if field.pattern.search(text):
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

    if args.issue is not None:
        body = _fetch_issue_body(args.repo, args.issue)
    elif args.body_file:
        with open(args.body_file, encoding="utf-8") as handle:
            body = handle.read()
    else:
        body = args.body or ""

    result = score_body(body, trivial=args.trivial)
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
