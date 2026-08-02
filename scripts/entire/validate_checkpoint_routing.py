"""Validate Entire checkpoint routing and the private native-recall policy."""

from __future__ import annotations

import json
from pathlib import Path

PRIVATE_CHECKPOINT_REPO = "learn-ukrainian/entire-checkpoints-private"
EXPECTED_PRIVATE_RECALL = {
    "schema": "entire-private-recall.v1",
    "enabled": True,
    "required_cli_version": "0.8.42",
    "source_repo": "learn-ukrainian/learn-ukrainian.github.io",
    "checkpoint_repo": PRIVATE_CHECKPOINT_REPO,
    "entire_access_principals": [{"handle": "github:krisztiankoos", "role": "writer"}],
    "authoritative": False,
    "automatic_intake": True,
    "public_promotion": False,
    "preflight": ["scripts/entire/private_mode_preflight.py"],
    "operations": {
        "search": [
            "search",
            "<query>",
            "--json",
            "--limit",
            "<1-10>",
            "--repo",
            "learn-ukrainian/learn-ukrainian.github.io",
        ],
        "explain_metadata": ["checkpoint", "explain", "<id-or-sha>", "--json"],
        "explain_full": [
            "checkpoint",
            "explain",
            "<id-or-sha>",
            "--full",
            "--no-pager",
        ],
        "recap": ["recap", "--static", "<--day|--week|--month|--90>"],
        "dispatch": ["dispatch", "--local", "--all-branches", "--since", "<window>"],
        "handoff": ["dispatch", "--local", "--all-branches", "--since", "<window>"],
        "resume": ["session", "resume", "<branch>"],
    },
    "external_disclosure_requires_operator_review": [
        "search",
        "explain_full",
        "recap",
        "dispatch",
        "handoff",
    ],
    "operator_request_required": [
        "recap",
        "dispatch",
        "handoff",
        "resume",
    ],
    "private_context_operations": [
        "search",
        "explain_full",
        "recap",
        "dispatch",
        "handoff",
    ],
    "forbidden_flags": [
        "--all-repos",
        "--code",
        "--generate",
        "--force",
        "--raw-transcript",
        "--transcript",
    ],
}


def _read_object(path: Path) -> dict | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def validate(root: Path) -> str | None:
    settings = _read_object(root / ".entire/settings.json")
    allowlist = _read_object(root / ".entire/phase05-allowlist.json")
    policy = _read_object(root / ".entire/private-recall.json")
    if settings is None or allowlist is None or policy is None:
        return "Entire routing configuration must contain valid JSON objects"
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
    if allowed_repo != PRIVATE_CHECKPOINT_REPO:
        return "checkpoint destination must be the approved private repository"
    if policy != EXPECTED_PRIVATE_RECALL:
        return "private recall policy does not match the canonical private-only contract"
    if policy["checkpoint_repo"] != allowed_repo:
        return "private recall policy does not match checkpoint routing"
    return None


if __name__ == "__main__":
    failure = validate(Path.cwd())
    if failure:
        raise SystemExit(f"Entire checkpoint routing invalid: {failure}")
    print("Entire checkpoint routing is consistent.")
