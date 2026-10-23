"""Advisory small-batch measurement for #11470; never a CI Gate dependency."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path

from scripts.common.git_context import sanitized_git_env
from scripts.review.target_resolution import is_test_path

POLICY = Path(__file__).resolve().parents[2] / "agents_extensions/shared/rules/workflow.md"
SHA = re.compile(r"[0-9a-fA-F]{40}")


def git(repo: Path, *args: str, data: bytes | None = None) -> bytes:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        env=sanitized_git_env(),
        input=data,
        capture_output=True,
        timeout=60,
        check=False,
    )
    if result.returncode:
        # Git stderr can contain attacker-controlled paths and credentials.
        raise ValueError(f"git {args[0]} failed (exit {result.returncode})")
    return result.stdout


def measure(repo: Path, base: str, head: str) -> dict:
    if not SHA.fullmatch(base) or not SHA.fullmatch(head):
        raise ValueError("base and head must be full 40-hex commit SHAs")
    for sha in (base, head):
        git(repo, "cat-file", "-e", f"{sha}^{{commit}}")
    bases = git(repo, "merge-base", "--all", base, head).decode("ascii").splitlines()
    if len(bases) != 1 or not SHA.fullmatch(bases[0]):
        raise ValueError("exactly one merge-base is required")
    merge_base = bases[0]
    options = ("--no-ext-diff", "--no-textconv", "--find-renames", merge_base, head, "--")
    deleted = set(git(repo, "diff", "--name-only", "-z", "--diff-filter=D", *options).split(b"\0"))
    fields = git(repo, "diff", "--numstat", "-z", *options).split(b"\0")
    if fields.pop() != b"":
        raise ValueError("incomplete numstat output")
    entries = []
    fields = iter(fields)
    for field in fields:
        added, removed, path = field.split(b"\t", 2)
        old = None
        if not path:  # -z rename record: counts TAB TAB NUL old NUL new NUL
            old, path = next(fields), next(fields)
        entries.append((added, removed, path, old))
    paths = [entry[2] for entry in entries]
    attributes = {}
    if paths:
        raw = git(
            repo,
            "check-attr",
            f"--source={head}",
            "-z",
            "--stdin",
            "linguist-generated",
            data=b"\0".join(paths) + b"\0",
        ).split(b"\0")
        if raw.pop() != b"" or len(raw) != len(paths) * 3:
            raise ValueError("incomplete generated-attribute output")
        attributes = {raw[i]: raw[i + 2] for i in range(0, len(raw), 3)}
    excluded = {"fixtures": 0, "generated": 0, "whole_file_deletions": 0}
    files, lines, binary = 0, 0, 0
    details = []
    for added, removed, path, old in entries:
        name = os.fsdecode(path)
        parts = name.split("/")
        reason = None
        if path in deleted:
            reason = "whole_file_deletions"
        elif "fixtures" in parts or "__fixtures__" in parts:
            reason = "fixtures"
        elif attributes[path] in {b"set", b"true"}:
            reason = "generated"
        if reason:
            excluded[reason] += 1
        else:
            files += 1
            if not is_test_path(name):
                if added == removed == b"-":
                    binary += 1
                elif added.isdigit() and removed.isdigit():
                    lines += int(added) + int(removed)
                else:
                    raise ValueError("unrecognized numstat counts")
        details.append({"path": name, "renamed_from": os.fsdecode(old) if old else None, "excluded": reason})
    return {
        "base_sha": base,
        "head_sha": head,
        "merge_base_sha": merge_base,
        "eligible_files": files,
        "changed_non_test_lines": None if binary else lines,
        "eligible_binary_files": binary,
        "excluded_files": excluded,
        "files": details,
    }


def report(args: argparse.Namespace) -> dict:
    result = {
        "status": "unknown",
        "eligible_files": None,
        "changed_non_test_lines": None,
        "limits": None,
        "over_limit": None,
        "justification_present": None,
        "diagnostics": [],
        "policy_source": "agents_extensions/shared/rules/workflow.md#merge-policy",
    }
    try:
        # Read the ordered trial's numbers, rather than maintaining another policy source.
        policy = POLICY.read_text(encoding="utf-8").split("**Small batches (", 1)[1].split("**Revert first", 1)[0]
        limits = re.search(r"above about (\d+) changed non-test lines or about (\d+) files", policy)
        if limits is None:
            raise ValueError("small-batches policy limits unavailable")
        result["limits"] = {"changed_non_test_lines": int(limits[1]), "eligible_files": int(limits[2])}
        base, head = args.base, args.head
        if args.event_path:
            event = json.loads(args.event_path.read_text(encoding="utf-8"))
            pr = event["pull_request"]
            base, head = pr["base"]["sha"], pr["head"]["sha"]
            body = pr["body"]
            if body is not None and not isinstance(body, str):
                raise ValueError("PR body must be a string or null")
            result["justification_present"] = bool(
                re.search(
                    r"(?im)^[ \t]*(?:size|small[- ]batch) justification:[ \t]*\S[^\r\n]*$",
                    (body or "").replace("\r\n", "\n").replace("\r", "\n"),
                )
            )
        result.update(measure(args.repo, base or "", head or ""))
        if result["eligible_binary_files"]:
            result["diagnostics"].append("eligible binary files have unknown changed-line counts")
        else:
            result["status"] = "measured"
        if result["eligible_files"] > result["limits"]["eligible_files"] or (
            result["changed_non_test_lines"] is not None
            and result["changed_non_test_lines"] > result["limits"]["changed_non_test_lines"]
        ):
            result["over_limit"] = True
        elif result["status"] == "measured":
            result["over_limit"] = False
    except (OSError, ValueError, KeyError, TypeError, IndexError, StopIteration, subprocess.TimeoutExpired) as exc:
        result["diagnostics"].append(f"measurement unavailable ({type(exc).__name__})")
    return result


def display(value: object) -> str:
    return "UNKNOWN" if value is None else str(value)


def emit(result: dict, summary: Path | None) -> None:
    numbers = (
        f"{display(result['changed_non_test_lines'])} changed non-test lines; "
        f"{display(result['eligible_files'])} eligible files"
    )
    limits = result["limits"]
    text = ["### Small-batch size warning", "", f"Status: {result['status']}", "", numbers]
    if limits:
        text += [
            f"Trial limits: {limits['changed_non_test_lines']} changed non-test lines / {limits['eligible_files']} eligible files."
        ]
    text += [
        f"Size justification present: {display(result['justification_present'])} (data only; does not suppress warnings).",
        "Record a one-line `Size justification: <reason>` in the PR body when needed.",
    ]
    if "excluded_files" in result:
        text += [
            "",
            "Excluded files: " + ", ".join(f"{key}={value}" for key, value in result["excluded_files"].items()),
        ]
    text += [
        "",
        "Lines = additions + removals from the exact merge-base diff; renames counted once at the destination.",
        "Ordinary test source files count toward eligible files but contribute zero non-test lines.",
        "Both measures exclude fixtures, generated files and whole-file deletions.",
        "Tests use review.target_resolution.is_test_path; fixtures use fixtures/__fixtures__ directories.",
        "Generated files use only committed head-attribute linguist-generated=true/set declarations.",
        "Whole-output declarations in .gitattributes cite their producers; other paths remain eligible.",
        "Advisory only. CI Gate is unchanged.",
    ]
    if result["diagnostics"]:
        text += ["", *result["diagnostics"]]
    if summary:
        try:
            with summary.open("a", encoding="utf-8") as stream:
                stream.write("\n".join(text) + "\n")
        except OSError:
            result["diagnostics"].append("job summary unavailable")
    print(json.dumps(result, sort_keys=True, ensure_ascii=True))
    if result["over_limit"]:
        print(
            f"::warning title=Small-batch size::{numbers}. Above the trial limit; split the PR or record Size justification: <reason> in the PR body."
        )
    if result["status"] == "unknown" or result["diagnostics"]:
        print(
            f"::notice title=Small-batch measurement incomplete::{numbers}. Measurement or reporting is incomplete; see JSON diagnostics. CI Gate is unchanged."
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Report PR size using the existing small-batches trial.\n"
        "Use for advisory PR reporting, never as a required CI gate.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python -m scripts.ci.pr_size_warning --event-path event.json
  .venv/bin/python -m scripts.ci.pr_size_warning --base <40-hex-sha> --head <40-hex-sha>
Outputs: JSON and advisory annotations on stdout; appends to --summary/GITHUB_STEP_SUMMARY.
Exit codes: 0 for measured or unknown size; 2 for invalid CLI usage. No Git writes or network calls.
Related: #11470; agents_extensions/shared/rules/workflow.md, Small batches.
""",
    )
    parser.add_argument(
        "--repo", type=Path, default=Path.cwd(), help="Git checkout to measure (default: cwd; example: .)."
    )
    parser.add_argument(
        "--base", help="Base commit, full 40-hex SHA (default: absent; event payload takes precedence)."
    )
    parser.add_argument(
        "--head", help="Head commit, full 40-hex SHA (default: absent; event payload takes precedence)."
    )
    parser.add_argument(
        "--event-path",
        type=Path,
        default=os.environ.get("GITHUB_EVENT_PATH"),
        help="PR event JSON path (default: GITHUB_EVENT_PATH, otherwise absent; example: event.json).",
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=os.environ.get("GITHUB_STEP_SUMMARY"),
        help="Append Markdown summary here (default: GITHUB_STEP_SUMMARY, otherwise absent; example: summary.md).",
    )
    args = parser.parse_args()
    emit(report(args), args.summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
