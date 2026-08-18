#!/usr/bin/env python3
"""Fail-closed gate: untrusted GitHub context must not reach ``run:`` scripts.

Root cause this guards against (script-injection class): any ``${{ }}``
expression expanded directly inside a ``run:`` script is substituted by the
Actions runner *before* the shell sees it. If the expression carries
attacker-controlled text (issue/PR titles and bodies, comment bodies, branch
names), a crafted value injects arbitrary shell. GitHub's own hardening guide
prescribes the intermediate-``env:`` pattern instead:

    env:
      TITLE: ${{ github.event.pull_request.title }}   # allowed: env mapping
    run: echo "$TITLE"                                # allowed: quoted shell var

This checker scans every ``run:`` block (inline and ``|``/``>`` multiline) in
``.github/workflows/*.yml`` and fails on untrusted contexts. It deliberately
does NOT flag:

    - ``env:`` mappings (the safe pattern above),
    - SHAs and refs: ``github.sha``, ``github.ref``,
      ``github.event.pull_request.*.sha``, ``github.event.before/after``
      (not attacker-controlled text),
    - ``if:`` / ``concurrency`` / ``with:`` expressions (not shell expansion),
    - trusted contexts such as ``github.workflow`` / ``github.event_name``.

Stdlib-only on purpose: it runs from ``scripts/audit/check_workflows.sh`` in
the always-on actionlint CI job with whatever python3 is at hand.

Usage:
    scripts/audit/check_untrusted_workflow_interpolation.py                # all workflows
    scripts/audit/check_untrusted_workflow_interpolation.py path/to/w.yml  # specific file(s)

Exit codes: 0 = clean, 1 = findings.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_WORKFLOWS_DIR = _REPO_ROOT / ".github" / "workflows"

# Attacker-controllable contexts (issue/PR/comment text, branch names, commit
# messages). SHAs and github.ref are excluded: they are not attacker text.
_UNTRUSTED = re.compile(
    r"""
    github\.event\.(?:
        (?:issue|comment|review|review_comment|discussion|head_commit|commits|pages|workflow_run)\b
        | pull_request\.(?:title|body)\b
        | pull_request\.head\.(?:ref|label|repo)\b
    )
    | github\.head_ref\b
    """,
    re.VERBOSE,
)

_EXPRESSION = re.compile(r"\$\{\{(.*?)\}\}", re.DOTALL)
# `run:` key, optionally after a `- ` step marker. Content indent is measured
# from the line start so both `run: |` and `- run: |` blocks parse alike.
_RUN_KEY = re.compile(r"^(?P<indent>\s*)(?:-\s+)?run:\s*(?P<value>.*)$")


def run_blocks(text: str) -> list[tuple[int, str]]:
    """Yield (start_line, body) for every ``run:`` script in workflow text.

    ``start_line`` is the 1-based line of the first body line (inline value or
    first block-scalar line). Only ``run:`` values are returned, so ``env:``
    mappings and ``if:``/``with:``/``concurrency`` expressions never reach the
    untrusted-context scan.
    """
    lines = text.splitlines()
    blocks: list[tuple[int, str]] = []
    i = 0
    while i < len(lines):
        match = _RUN_KEY.match(lines[i])
        if not match:
            i += 1
            continue
        indent = len(match.group("indent"))
        value = match.group("value").strip()
        if value.startswith(("|", ">")):  # block scalar: consume deeper-indented lines
            body_lines: list[str] = []
            j = i + 1
            while j < len(lines):
                line = lines[j]
                if line.strip() == "" or (len(line) - len(line.lstrip())) > indent:
                    body_lines.append(line)
                    j += 1
                else:
                    break
            blocks.append((i + 2, "\n".join(body_lines)))
            i = j
        else:
            blocks.append((i + 1, value))
            i += 1
    return blocks


def findings_for(path: Path) -> list[str]:
    """Return human-readable findings for one workflow file (empty = clean)."""
    text = path.read_text(encoding="utf-8")
    findings: list[str] = []
    for start_line, body in run_blocks(text):
        for match in _EXPRESSION.finditer(body):
            expression = match.group(1)
            untrusted = _UNTRUSTED.search(expression)
            if not untrusted:
                continue
            line_no = start_line + body[: match.start()].count("\n")
            findings.append(
                f"{path}:{line_no}: untrusted context `{untrusted.group(0)}` "
                f"interpolated into a run: script — use env: + a quoted shell "
                f"variable instead: {expression.strip()!r}"
            )
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "files",
        nargs="*",
        type=Path,
        help="workflow files to scan (default: .github/workflows/*.yml|yaml)",
    )
    args = parser.parse_args(argv)

    if args.files:
        targets = sorted(args.files)
    else:
        targets = sorted(
            p for p in _WORKFLOWS_DIR.iterdir() if p.suffix in (".yml", ".yaml")
        )

    findings: list[str] = []
    for target in targets:
        if not target.is_file():
            findings.append(f"{target}: file not found")
            continue
        findings.extend(findings_for(target))

    if findings:
        print("❌ untrusted GitHub context interpolated into run: scripts:", file=sys.stderr)
        for finding in findings:
            print(f"  {finding}", file=sys.stderr)
        return 1
    print(f"✅ no untrusted-context interpolation in {len(targets)} workflow file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
