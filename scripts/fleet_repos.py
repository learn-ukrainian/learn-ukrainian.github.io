"""Allowlisted fleet repository resolution for multi-repo dispatch (#672 P2.1).

The public primary that owns ``scripts/delegate.py`` remains the control-plane
root. ``--repo`` selects which sibling git checkout receives worktree creation
and GitHub targeting.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

_CONFIG_PATH = Path(__file__).resolve().parent / "config" / "fleet_repos.yaml"


@dataclass(frozen=True)
class FleetRepo:
    key: str
    github: str
    local_name: str
    role: str
    default: bool = False

    @property
    def owner(self) -> str:
        return self.github.split("/", 1)[0]

    @property
    def name(self) -> str:
        return self.github.split("/", 1)[1]


class FleetRepoError(ValueError):
    """Unknown key, bad catalog, or missing sibling checkout."""


def load_fleet_repos(path: Path | None = None) -> dict[str, FleetRepo]:
    cfg_path = path or _CONFIG_PATH
    raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping):
        raise FleetRepoError(f"fleet_repos catalog must be a mapping: {cfg_path}")
    repos_raw = raw.get("repos")
    if not isinstance(repos_raw, Mapping) or not repos_raw:
        raise FleetRepoError(f"fleet_repos.repos missing or empty: {cfg_path}")
    out: dict[str, FleetRepo] = {}
    defaults = 0
    for key, body in repos_raw.items():
        if not isinstance(key, str) or not key.strip():
            raise FleetRepoError("fleet_repos key must be a non-empty string")
        if not isinstance(body, Mapping):
            raise FleetRepoError(f"fleet_repos[{key!r}] must be a mapping")
        github = body.get("github")
        local_name = body.get("local_name")
        role = body.get("role") or ""
        default = bool(body.get("default", False))
        if not isinstance(github, str) or "/" not in github:
            raise FleetRepoError(f"fleet_repos[{key!r}].github must be owner/name")
        if not isinstance(local_name, str) or not local_name.strip():
            raise FleetRepoError(f"fleet_repos[{key!r}].local_name must be a non-empty string")
        if default:
            defaults += 1
        out[key] = FleetRepo(
            key=key,
            github=github,
            local_name=local_name.strip(),
            role=str(role),
            default=default,
        )
    if defaults != 1:
        raise FleetRepoError("fleet_repos must mark exactly one default repo")
    return out


def default_repo_key(repos: Mapping[str, FleetRepo] | None = None) -> str:
    catalog = repos or load_fleet_repos()
    for key, repo in catalog.items():
        if repo.default:
            return key
    raise FleetRepoError("no default fleet repo")


def resolve_fleet_repo(
    key: str | None,
    *,
    primary_root: Path,
    repos: Mapping[str, FleetRepo] | None = None,
    require_checkout: bool = True,
) -> tuple[FleetRepo, Path]:
    """Return ``(FleetRepo, absolute checkout path)`` for *key*.

    ``primary_root`` is the public Learn Ukrainian checkout that owns delegate.
    Sibling checkouts live at ``primary_root.parent / local_name``. The public
    entry resolves to ``primary_root`` itself even when ``local_name`` differs
    from the directory basename (worktree / rename safety).
    """
    catalog = repos or load_fleet_repos()
    resolved_key = (key or default_repo_key(catalog)).strip()
    if resolved_key not in catalog:
        known = ", ".join(sorted(catalog))
        raise FleetRepoError(f"unknown --repo {resolved_key!r}; allowlisted: {known}")
    repo = catalog[resolved_key]
    primary = primary_root.resolve()
    checkout = primary if repo.default else (primary.parent / repo.local_name).resolve()
    if require_checkout and not (checkout / ".git").exists() and not checkout.is_dir():
        raise FleetRepoError(
            f"--repo {repo.key} expects sibling checkout at {checkout}; "
            f"clone {repo.github} next to {primary.name} first"
        )
    if require_checkout:
        git_dir = checkout / ".git"
        if not git_dir.exists():
            raise FleetRepoError(
                f"--repo {repo.key} path {checkout} is not a git checkout "
                f"(clone {repo.github} as ../{repo.local_name} beside the public primary)"
            )
    return repo, checkout


def fleet_repo_as_dict(repo: FleetRepo, checkout: Path) -> dict[str, Any]:
    return {
        "key": repo.key,
        "github": repo.github,
        "local_name": repo.local_name,
        "role": repo.role,
        "default": repo.default,
        "checkout": str(checkout),
    }
