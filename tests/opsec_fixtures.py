"""Synthetic matcher and repository fixtures: no private rules or host strings."""

from __future__ import annotations

import ast
import json
import shutil
import subprocess
from importlib.util import resolve_name
from pathlib import Path

import pytest

TOKEN = "SENTINEL-HOST-TOKEN"
ROOT = Path(__file__).resolve().parents[1]
MATCHER = """import re
from dataclasses import dataclass
@dataclass(frozen=True)
class Hit:
    class_id: int
    rule_id: str
    span: tuple[int,int]
class Matcher:
    def __init__(self, rules):
        self.rules = rules
    def scan(self, text):
        return [Hit(int(level), row["id"], hit.span())
                for level, group in self.rules.items() for row in group["patterns"]
                for hit in re.finditer(row["regex"], text)]
"""


# A synthetic stand-in for the private override module the public guard loads
# from private_tooling().parent (PUBLIC-1104 6(b)). It admits one flagged write
# per reason and appends an audit row; the private module scopes admission per
# command and is tested privately.
OVERRIDE = """import hashlib, json, os
OVERRIDE = "LU_OPSEC_OVERRIDE"
class OverrideBlocked(RuntimeError):
    pass
def internal_environment(source=None):
    return {k: v for k, v in (os.environ if source is None else source).items() if k != OVERRIDE}
def take_override(environment):
    return environment.pop(OVERRIDE, "")
def command_keys(reason):
    return ["synthetic-command"]
def authorize(destination, blocks, reason, log_path):
    if not reason.strip():
        return False
    log_path.parent.mkdir(parents=True, exist_ok=True)
    claim = log_path.parent / ("consumed-" + hashlib.sha256(reason.encode()).hexdigest())
    try:
        claim.open("x").close()
    except FileExistsError:
        raise OverrideBlocked("OPSEC: override already consumed; use a fresh command-scoped reason.") from None
    row = {"timestamp": "synthetic", "destination": destination,
           "rule_ids": sorted({rule for rule, _ in blocks}), "reason": reason}
    with log_path.open("a") as stream:
        stream.write(json.dumps(row) + "\\n")
    return True
"""


def install_override(tooling, source=OVERRIDE):
    """Write an override module where the guard looks for it, beside the private tooling."""
    path = tooling.parent / "opsec_override" / "override.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source)
    return path


def synthetic_rules(rule="synthetic-rule", level=1, pattern=TOKEN):
    # The machinery package finds its own policy file, so this holds in either checkout layout.
    from lu_machinery.common.repo_root import machinery_path

    policy = json.loads(machinery_path("opsec/blocking.json").read_text())
    rules = {"6": {"patterns": [{"id": name, "regex": r"(?!)"} for name in policy["class6_block_ids"]]}}
    rows = rules.setdefault(str(level), {"patterns": []})["patterns"]
    rows[:] = [row for row in rows if row["id"] != rule]
    rows.append({"id": rule, "regex": pattern})
    return rules


RULES = synthetic_rules()
CATALOG = {
    "public": {"github": "unit/public", "default": True, "local_name": "public-fixture", "role": "public-monorepo",
               "verdict_recorder": True},
    "infra-private": {
        "github": "unit/private",
        "default": False,
        "local_name": "private-fixture",
        "role": "private-infra",
        "verdict_recorder": True,
    },
}


def recorded_approval(head, login="unit"):
    """One trusted exact-head APPROVE comment as the verdict recorder posts it (#12031)."""
    marker = (
        f"### Cross-family review\nhead: {head}\nReviewer family: openai\nVERDICT: APPROVED\n"
        "Reviewer model: gpt-6.1-sol\nTask id: review-one\n\n"
        f"<!-- cf-verdict v1 sha={head} task=review-one started=2026-10-29T10:00:00.000001+00:00 "
        "verdict=APPROVED model=gpt-6.1-sol family=openai -->"
    )
    return {"id": 1, "body": marker, "user": {"login": login}, "author_association": "OWNER",
            "created_at": "2026-10-29T10:05:00Z", "updated_at": "2026-10-29T10:05:00Z"}


def make_tooling(directory):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "matcher.py").write_text(MATCHER)
    (directory / "rules.json").write_text(json.dumps(RULES))
    install_override(directory)
    return directory


@pytest.fixture
def synthetic_opsec(tmp_path, monkeypatch):
    import importlib

    directory = make_tooling(tmp_path / "tooling")
    monkeypatch.setattr(importlib.import_module("lu_machinery.opsec.prepublish"), "private_tooling", lambda: directory)
    return directory


@pytest.fixture
def publisher_transport(monkeypatch):
    """Explicitly inject existing subprocess spies at the typed transport boundary."""
    import importlib

    github = importlib.import_module("lu_machinery.publish.github")

    def send(argv, *, runner, _original=github._send, **kwargs):
        return _original(argv, runner=subprocess.run if runner is None else runner, **kwargs)

    monkeypatch.setattr(github, "_send", send)


def copy_publisher_scripts(source: Path, destination: Path) -> None:
    """Stage publisher assets and their transitive local Python imports.

    Parse imports without executing modules, including imports inside functions.
    Only reachable dependency modules are staged; sibling tools are unnecessary.
    """
    pending = []
    for package in ("opsec", "publish"):
        shutil.copytree(source / package, destination / package, ignore=shutil.ignore_patterns("__pycache__"))
        pending.extend((source / package).rglob("*.py"))
    visited = set()

    package_name = source.name

    def stage(module: str) -> None:
        parts = module.split(".")
        if parts[0] != package_name:
            return
        # Package initializers can have dependencies of their own.
        for length in range(1, len(parts) + 1):
            relative = Path(*parts[1:length])
            path = source / relative / "__init__.py"
            if not path.is_file() and length > 1:
                path = (source / relative).with_suffix(".py")
            if path.is_file() and path not in visited:
                target = destination / path.relative_to(source)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
                pending.append(path)

    stage(package_name)
    while pending:
        path = pending.pop()
        if path in visited:
            continue
        visited.add(path)
        module = (package_name, *path.relative_to(source).with_suffix("").parts)
        package = ".".join(module[:-1])
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"), filename=str(path))):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    stage(alias.name)
            elif isinstance(node, ast.ImportFrom):
                name = node.module or ""
                if node.level:
                    name = resolve_name("." * node.level + name, package)
                stage(name)
                for alias in node.names:
                    if alias.name != "*":
                        stage(f"{name}.{alias.name}")
