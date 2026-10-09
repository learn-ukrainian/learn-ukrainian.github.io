#!/usr/bin/env python3
"""Block ordinary Git and GitHub publish commands from a read-only Claude Bash tool.

The adapter registers this hook only for read-only runs. The deny list, this
hook, and the push rewrite stop ordinary command forms only. Code the reviewer
runs (Python, scripts, HTTP) can publish using the host's credentials: it can
override its git config to push or write through the GitHub API.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


def _shell_parser():
    """Load the existing Bash parser without adding another tokenizer."""
    source = Path(__file__).with_name("guard-primary-checkout-write.py")
    spec = importlib.util.spec_from_file_location("primary_checkout_guard_parser", source)
    if spec is None or spec.loader is None:
        raise RuntimeError("reviewer publish guard parser unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_PR_ISSUE_WRITES = frozenset({"merge", "create", "comment", "review", "edit", "close", "reopen"})
_API_FIELDS = frozenset({"-f", "-F", "--field", "--raw-field", "--input"})


def _gh_args(args: list[str]) -> list[str]:
    """Skip gh global options before locating the command group."""
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in {"-R", "--repo", "--hostname", "-H"}:
            i += 2
        elif arg.startswith(("--repo=", "--hostname=")):
            i += 1
        else:
            break
    return args[i:]


def _api_writes(args: list[str]) -> bool:
    for i, arg in enumerate(args):
        if arg in _API_FIELDS or arg.startswith(("-f", "-F", "--field=", "--raw-field=", "--input=")):
            return True
        if arg in {"-X", "--method"} and (i + 1 >= len(args) or args[i + 1].upper() != "GET"):
            return True
        if arg.startswith("--method=") and arg.partition("=")[2].upper() != "GET":
            return True
        if arg.startswith("-X") and len(arg) > 2 and arg[2:].upper() != "GET":
            return True
    return False


def blocked(command: str, parser=None, depth: int = 0) -> str | None:
    if depth > 8:
        return "nested shell command exceeds reviewer inspection depth"
    parser = parser or _shell_parser()
    for segment in parser._expanded_segments(command):
        segment = parser._without_redirects(segment)
        binary, index = parser._command_word(segment)
        args = [str(word) for word in segment[index + 1 :]]
        if binary == "git":
            _, rest = parser._git_global_prefix(args)
            if rest and rest[0] == "push":
                return "git push"
        elif binary == "gh":
            rest = _gh_args(args)
            if not rest:
                continue
            group = rest[0]
            group_args = _gh_args(rest[1:])
            if group in {"pr", "issue"} and group_args and group_args[0] in _PR_ISSUE_WRITES:
                return f"gh {group} {group_args[0]}"
            if group == "api" and _api_writes(rest[1:]):
                return "gh api write"
            if group == "release" or (group == "workflow" and len(rest) > 1 and rest[1] == "run"):
                return f"gh {group} publish"
        elif binary and Path(binary).name.startswith("python"):
            if args[:2] == ["-m", "scripts.publish"]:
                tail = args[2:]
                if tail != ["--help"] and not (len(tail) == 2 and tail[-1] == "--help"):
                    return "typed GitHub publisher"
            elif args and args[0].endswith("scripts/publish/github.py"):
                return "typed GitHub publisher"
        elif binary in {"bash", "sh", "eval"}:
            if binary == "eval":
                body = " ".join(args)
            else:
                body = ""
                for i, arg in enumerate(args):
                    if arg == "-c" or (arg.startswith("-") and "c" in arg[1:]):
                        if i + 1 < len(args):
                            body = args[i + 1]
                        break
            if body:
                reason = blocked(body, parser, depth + 1)
                if reason:
                    return reason
    return None


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        if payload.get("tool_name") != "Bash":
            return 0
        command = payload.get("tool_input", {}).get("command", "")
        reason = blocked(command)
    except (OSError, ValueError, TypeError, RuntimeError) as exc:
        print(f"BLOCKED by guard-reviewer-publish: cannot inspect command ({type(exc).__name__}).", file=sys.stderr)
        return 2
    if reason:
        print(f"BLOCKED by guard-reviewer-publish: {reason} is unavailable in read-only review.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
