"""Fail-closed PR-tier classification; stdlib only for the Changes job."""

from __future__ import annotations

import json
import os
import subprocess
import urllib.parse
from pathlib import Path

from scripts.ci.frontend_change_scope import load_denominator, path_in_denominator

# Content CI owns these trees. Other exemptions are Markdown in known docs trees.
CONTENT_PREFIXES = ("wiki/", "curriculum/")
DOC_PREFIXES = (
    "docs/", "agents_extensions/shared/skills/", ".claude/", ".codex/", ".agent/",
)


def is_docs(path: str) -> bool:
    if path.startswith(CONTENT_PREFIXES):
        return True
    return path.endswith(".md") and ("/" not in path or path.startswith(DOC_PREFIXES))


def classify(
    paths: list[str], *, event: str, labels: list[str], shard_count: int,
    denominator: list[str],
) -> dict[str, str]:
    """Unknown paths run every pytest shard; only explicit docs may skip."""
    if shard_count < 1:
        raise ValueError("shard_count must be positive")
    full = {"docs_only": "false", "frontend": "true",
            "shards": json.dumps(list(range(1, shard_count + 1)))}
    if event != "pull_request" or "full-ci" in labels or not paths or len(paths) >= 300:
        return full
    frontend = any(path_in_denominator(path, denominator) for path in paths)
    docs_only = all(is_docs(path) for path in paths) and not frontend
    return {
        "docs_only": str(docs_only).lower(),
        "frontend": str(frontend).lower(),
        "shards": "[1]" if docs_only else full["shards"],
    }


def compare_paths(base: str, head: str, repo: str) -> list[str]:
    """Keep rename sources and structured filenames; never split paths on newlines."""
    if not base or set(base) <= {"0"} or not head:
        raise ValueError("missing comparison SHA")
    spec = urllib.parse.quote(f"{base}...{head}", safe=".")
    # GitHub returns files only on the first page, capped at 300. No commit
    # pagination is needed; classify() treats reaching the file cap as full.
    raw = subprocess.check_output(
        ["gh", "api", f"repos/{repo}/compare/{spec}"], text=True, timeout=60,
    )
    files = json.loads(raw)["files"]
    if not isinstance(files, list):
        raise ValueError("invalid comparison files")
    paths = []
    for item in files:
        name = item["filename"]
        previous = item.get("previous_filename")
        if not isinstance(name, str) or not name:
            raise ValueError("invalid comparison filename")
        paths.append(name)
        if previous is not None:
            if not isinstance(previous, str) or not previous:
                raise ValueError("invalid previous filename")
            paths.append(previous)
    return paths


def main() -> None:
    shard_count = int(os.environ["PYTEST_SHARD_COUNT"])
    event = os.environ.get("EVENT_NAME", "")
    paths: list[str] = []
    labels: list[str] = []
    denominator: list[str] = []
    try:
        payload = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8"))
        if event == "pull_request":
            labels = [label["name"] for label in payload["pull_request"]["labels"]]
            if "full-ci" not in labels:
                denominator = load_denominator()["paths"]
                paths = compare_paths(os.environ.get("BASE", ""), os.environ.get("HEAD", ""), os.environ["REPO"])
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        # Missing/malformed event, denominator, or API response cannot grant a skip.
        paths = []
    result = classify(paths, event=event, labels=labels, shard_count=shard_count, denominator=denominator)
    print(f"files={len(paths)} " + " ".join(f"{key}={value}" for key, value in result.items()))
    if output := os.environ.get("GITHUB_OUTPUT"):
        with Path(output).open("a", encoding="utf-8") as handle:
            handle.write("".join(f"{key}={value}\n" for key, value in result.items()))


if __name__ == "__main__":
    main()
