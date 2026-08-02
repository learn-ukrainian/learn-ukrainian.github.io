"""Validate that Entire product routing matches the public egress allowlist."""

from __future__ import annotations

import json
from pathlib import Path


def validate(root: Path) -> str | None:
    settings = json.loads((root / ".entire/settings.json").read_text())
    allowlist = json.loads((root / ".entire/phase05-allowlist.json").read_text())
    try:
        remote = settings["strategy_options"]["checkpoint_remote"]
        endpoints = allowlist["checkpoint_endpoints"]
        allowed_repo = endpoints[0]["github_repo"]
    except (IndexError, KeyError, TypeError):
        return "checkpoint routing has an incomplete schema"
    if remote.get("provider") != "github":
        return "checkpoint_remote.provider must be github"
    if len(endpoints) != 1:
        return "checkpoint_endpoints must contain exactly one destination"
    if remote.get("repo") != allowed_repo:
        return "checkpoint_remote.repo does not match the egress allowlist"
    return None


if __name__ == "__main__":
    failure = validate(Path.cwd())
    if failure:
        raise SystemExit(f"Entire checkpoint routing invalid: {failure}")
    print("Entire checkpoint routing is consistent.")
