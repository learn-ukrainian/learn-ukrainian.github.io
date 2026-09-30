#!/usr/bin/env python3
"""Print the git hook types a pre-commit config declares, one per line (sorted).

The set is the union of ``default_install_hook_types`` (pre-commit's default:
``pre-commit``), ``default_stages``, and every configured hook's ``stages``. An
absent ``default_stages`` adds nothing: pre-commit then runs unstaged hooks on
whichever hook types are installed. Legacy stage names map to git hook names and
``manual`` is dropped because no git hook runs it.

Stages a remote repository's own manifest declares, without a ``stages``
override in the config, are not visible here.

Exits 2 with a message on stderr when the config cannot be read, is not valid
YAML, or has a shape or stage name pre-commit would reject, so callers fail closed.

Usage: declared_hook_stages.py <path/to/.pre-commit-config.yaml>
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

# pre-commit's hook types (clientlib) — every one is a git hook name.
HOOK_TYPES = frozenset(
    {
        "commit-msg",
        "post-checkout",
        "post-commit",
        "post-merge",
        "post-rewrite",
        "pre-commit",
        "pre-merge-commit",
        "pre-push",
        "pre-rebase",
        "prepare-commit-msg",
    }
)
LEGACY_STAGES = {"commit": "pre-commit", "push": "pre-push", "merge-commit": "pre-merge-commit"}
DEFAULT_INSTALL_HOOK_TYPES = ["pre-commit"]


class ConfigError(Exception):
    pass


def _stage_list(value: object, where: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ConfigError(f"{where} must be a list of stage names, got {value!r}")
    return value


def _hook_type(stage: str, where: str) -> str | None:
    stage = LEGACY_STAGES.get(stage, stage)
    if stage == "manual":
        return None
    if stage not in HOOK_TYPES:
        raise ConfigError(f"{where} has unknown stage {stage!r}")
    return stage


def declared_stages(config: object) -> set[str]:
    if not isinstance(config, dict):
        raise ConfigError("top level must be a mapping")
    sources: list[tuple[str, list[str]]] = [
        (
            "default_install_hook_types",
            _stage_list(
                config.get("default_install_hook_types", DEFAULT_INSTALL_HOOK_TYPES),
                "default_install_hook_types",
            ),
        )
    ]
    if "default_stages" in config:
        sources.append(("default_stages", _stage_list(config["default_stages"], "default_stages")))

    repos = config.get("repos")
    if not isinstance(repos, list):
        raise ConfigError(f"repos must be a list, got {repos!r}")
    for repo_index, repo in enumerate(repos):
        if not isinstance(repo, dict) or not isinstance(repo.get("hooks"), list):
            raise ConfigError(f"repos[{repo_index}] must be a mapping with a hooks list")
        for hook_index, hook in enumerate(repo["hooks"]):
            if not isinstance(hook, dict):
                raise ConfigError(f"repos[{repo_index}].hooks[{hook_index}] must be a mapping")
            if "stages" in hook:
                where = f"hook {hook.get('id', hook_index)!r} stages"
                sources.append((where, _stage_list(hook["stages"], where)))

    stages = set()
    for where, values in sources:
        for value in values:
            hook_type = _hook_type(value, where)
            if hook_type is not None:
                stages.add(hook_type)
    return stages


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: declared_hook_stages.py <pre-commit-config>", file=sys.stderr)
        return 2
    path = Path(argv[0])
    try:
        config = yaml.safe_load(path.read_text(encoding="utf-8"))
        stages = declared_stages(config)
    except (OSError, UnicodeDecodeError, yaml.YAMLError, ConfigError) as exc:
        print(f"{path}: cannot determine declared hook stages: {exc}", file=sys.stderr)
        return 2
    for stage in sorted(stages):
        print(stage)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
