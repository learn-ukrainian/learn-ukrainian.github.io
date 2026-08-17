#!/usr/bin/env python3
"""Frontend / frontend-e2e changed-path scope for CI cheap-exit (#6917).

Required jobs stay unconditionally scheduled. After checkout, this helper
decides whether the diff touches the single-source denominator. Out of scope
→ exit 0 with a loud auditable decision (job stays ``success``). In scope →
continue the remaining job steps.

Stdlib only so GitHub runners can invoke it with system ``python3`` before
``actions/setup-python``.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path, PurePosixPath

DENOMINATOR_REL = "scripts/ci/frontend_change_denominator.json"
PACKAGE_JSON_REL = "site/package.json"
HYDRATE_ROOT_SCRIPT = "hydrate"

_NPM_RUN_RE = re.compile(r"\bnpm\s+run\s+([A-Za-z0-9:_-]+)")
_NODE_SCRIPT_RE = re.compile(r"\bnode(?:\s+--experimental-strip-types)?\s+(\./scripts/[^\s]+|scripts/[^\s]+)")
_PYTHON_MODULE_RE = re.compile(r"(?:^|[\s\"'])-m\s+(scripts(?:\.[A-Za-z0-9_]+)+)")
_PYTHON_FILE_RE = re.compile(r"(?:^|[\s\"'])(scripts/[A-Za-z0-9_./-]+\.py)\b")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def denominator_path(root: Path | None = None) -> Path:
    return (root or repo_root()) / DENOMINATOR_REL


def load_denominator(path: Path | None = None) -> dict:
    target = path or denominator_path()
    data = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{target}: expected a JSON object")
    paths = data.get("paths")
    if not isinstance(paths, list) or not paths or not all(isinstance(p, str) and p for p in paths):
        raise ValueError(f"{target}: 'paths' must be a non-empty list of strings")
    version = data.get("version")
    if version is None or version == "":
        raise ValueError(f"{target}: missing 'version'")
    return data


def path_in_denominator(path: str, patterns: Sequence[str]) -> bool:
    """Return True when a repo-relative POSIX path matches any denominator entry."""
    text = PurePosixPath(path).as_posix()
    for pattern in patterns:
        if pattern.endswith("/"):
            prefix = pattern.rstrip("/")
            if text == prefix or text.startswith(pattern):
                return True
        elif text == pattern:
            return True
    return False


def matching_paths(changed: Iterable[str], patterns: Sequence[str]) -> list[str]:
    return sorted({path for path in changed if path_in_denominator(path, patterns)})


def comparison_range(base: str, head: str = "HEAD") -> str:
    return base if "..." in base else f"{base}...{head}"


def _parse_nul_delimited_paths(raw: bytes) -> list[str]:
    """Decode ``git diff --name-only -z`` bytes without misparsing odd filenames."""
    return sorted(path.decode("utf-8", errors="surrogateescape") for path in raw.split(b"\0") if path)


def changed_files(git_range: str, *, cwd: Path | None = None) -> list[str]:
    # core.quotePath=false + -z: non-ASCII / quote / backslash names stay literal
    # (default quotePath C-quotes them and breaks denominator prefix matching).
    result = subprocess.run(
        [
            "git",
            "-c",
            "core.quotePath=false",
            "diff",
            "--no-ext-diff",
            "--name-only",
            "-z",
            git_range,
        ],
        check=True,
        capture_output=True,
        cwd=cwd or repo_root(),
    )
    return _parse_nul_delimited_paths(result.stdout)


def _module_to_path(module: str) -> str:
    return "/".join(module.split(".")) + ".py"


def _normalize_site_script(raw: str) -> str:
    cleaned = raw[2:] if raw.startswith("./") else raw
    if cleaned.startswith("scripts/"):
        return f"site/{cleaned}"
    return cleaned


def resolve_script_command(command: str, scripts: dict[str, str], *, _stack: frozenset[str] | None = None) -> set[str]:
    """Resolve one npm script command string into repo-relative file paths."""
    found: set[str] = set()
    stack = _stack or frozenset()

    for name in _NPM_RUN_RE.findall(command):
        if name in stack:
            continue
        nested = scripts.get(name)
        if nested is None:
            continue
        found.update(resolve_script_command(nested, scripts, _stack=stack | {name}))

    for node_path in _NODE_SCRIPT_RE.findall(command):
        found.add(_normalize_site_script(node_path))

    for module in _PYTHON_MODULE_RE.findall(command):
        found.add(_module_to_path(module))

    for py_path in _PYTHON_FILE_RE.findall(command):
        found.add(py_path)

    return found


def resolve_hydrate_entrypoints(package_json: Path | None = None) -> list[str]:
    """Resolve hydrate entrypoints that ``site/package.json`` actually invokes."""
    path = package_json or (repo_root() / PACKAGE_JSON_REL)
    data = json.loads(path.read_text(encoding="utf-8"))
    scripts = data.get("scripts")
    if not isinstance(scripts, dict):
        raise ValueError(f"{path}: missing scripts object")
    hydrate = scripts.get(HYDRATE_ROOT_SCRIPT)
    if not isinstance(hydrate, str) or not hydrate.strip():
        raise ValueError(f"{path}: missing scripts.{HYDRATE_ROOT_SCRIPT}")
    return sorted(resolve_script_command(hydrate, {k: str(v) for k, v in scripts.items()}))


def assert_hydrate_entrypoints_in_denominator(
    *,
    denominator: dict | None = None,
    package_json: Path | None = None,
) -> list[str]:
    """Fail when any hydrate-resolved path escapes the denominator."""
    data = denominator or load_denominator()
    patterns = list(data["paths"])
    entrypoints = resolve_hydrate_entrypoints(package_json)
    escaped = [path for path in entrypoints if not path_in_denominator(path, patterns)]
    if escaped:
        raise AssertionError(
            "hydrate entrypoints outside frontend change denominator: "
            + ", ".join(escaped)
            + f" (denominator version={data['version']})"
        )
    return entrypoints


def decision_line(*, decision: str, version: object, changed_count: int, matched_count: int) -> str:
    return (
        f"frontend-scope: decision={decision} denominator_version={version} "
        f"changed_files={changed_count} matched={matched_count}"
    )


def write_github_output(run: bool, path: Path | None = None) -> None:
    output = path
    if output is None:
        raw = os.environ.get("GITHUB_OUTPUT")
        if not raw:
            return
        output = Path(raw)
    with output.open("a", encoding="utf-8") as handle:
        handle.write(f"run={'true' if run else 'false'}\n")


def write_step_summary(line: str, path: Path | None = None) -> None:
    summary = path
    if summary is None:
        raw = os.environ.get("GITHUB_STEP_SUMMARY")
        if not raw:
            return
        summary = Path(raw)
    with summary.open("a", encoding="utf-8") as handle:
        handle.write("## Frontend change scope (#6917)\n\n")
        handle.write(f"`{line}`\n")


def decide_from_changed(
    changed: Sequence[str],
    *,
    denominator: dict | None = None,
) -> tuple[bool, str, list[str]]:
    data = denominator or load_denominator()
    matched = matching_paths(changed, list(data["paths"]))
    run = bool(matched)
    line = decision_line(
        decision="run" if run else "cheap_exit",
        version=data["version"],
        changed_count=len(changed),
        matched_count=len(matched),
    )
    return run, line, matched


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base",
        default="",
        help="base SHA/ref (pull_request.base.sha || merge_group.base_sha || before)",
    )
    parser.add_argument("--head", default="HEAD", help="head SHA/ref (default: HEAD)")
    parser.add_argument(
        "--denominator",
        type=Path,
        default=None,
        help=f"denominator JSON (default: {DENOMINATOR_REL})",
    )
    args = parser.parse_args(argv)

    denominator = load_denominator(args.denominator)
    base = (args.base or "").strip()
    if not base or set(base) == {"0"}:
        line = decision_line(
            decision="run",
            version=denominator["version"],
            changed_count=-1,
            matched_count=-1,
        )
        # Fail open when the event gives no usable base — never silent cheap-exit.
        line = f"{line} reason=missing_base_sha"
        print(line)
        write_step_summary(line)
        write_github_output(True)
        return 0

    try:
        changed = changed_files(comparison_range(base, args.head))
    except subprocess.CalledProcessError as exc:
        line = (
            f"frontend-scope: decision=run denominator_version={denominator['version']} "
            f"changed_files=-1 matched=-1 reason=git_diff_failed exit={exc.returncode}"
        )
        print(line, file=sys.stderr)
        write_step_summary(line)
        write_github_output(True)
        return 0

    run, line, _matched = decide_from_changed(changed, denominator=denominator)
    print(line)
    write_step_summary(line)
    write_github_output(run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
