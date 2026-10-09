"""Synthetic matcher and repository fixtures: no private rules or host strings."""

from __future__ import annotations

import ast
import json
import os
import shutil
import subprocess
import sys
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


def synthetic_rules(rule="synthetic-rule", level=1, pattern=TOKEN):
    policy = json.loads((ROOT / "scripts/opsec/blocking.json").read_text())
    rules = {"6": {"patterns": [{"id": name, "regex": r"(?!)"} for name in policy["class6_block_ids"]]}}
    rows = rules.setdefault(str(level), {"patterns": []})["patterns"]
    rows[:] = [row for row in rows if row["id"] != rule]
    rows.append({"id": rule, "regex": pattern})
    return rules


RULES = synthetic_rules()
CATALOG = {
    "public": {"github": "unit/public", "default": True, "local_name": "public-fixture", "role": "public-monorepo"},
    "infra-private": {
        "github": "unit/private",
        "default": False,
        "local_name": "private-fixture",
        "role": "private-infra",
    },
}


def make_tooling(directory):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "matcher.py").write_text(MATCHER)
    (directory / "rules.json").write_text(json.dumps(RULES))
    return directory


@pytest.fixture
def synthetic_opsec(tmp_path, monkeypatch):
    from scripts.opsec import prepublish

    directory = make_tooling(tmp_path / "tooling")
    monkeypatch.setattr(prepublish, "private_tooling", lambda: directory)
    return directory


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

    def stage(module: str) -> None:
        parts = module.split(".")
        if parts[0] != "scripts":
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

    stage("scripts")
    while pending:
        path = pending.pop()
        if path in visited:
            continue
        visited.add(path)
        module = ("scripts", *path.relative_to(source).with_suffix("").parts)
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


@pytest.fixture
def gh_shim_sandbox(tmp_path):
    root = tmp_path / "public-fixture"
    root.mkdir()
    scripts = root / "scripts"
    scripts.mkdir()
    copy_publisher_scripts(ROOT / "scripts", scripts)
    # The advisory classifier reads workflow policy as well as importing code.
    workflow = root / ".github/workflows/ci.yml"
    workflow.parent.mkdir(parents=True)
    shutil.copy2(ROOT / ".github/workflows/ci.yml", workflow)
    shim = scripts / "agent_runtime/shims/gh"
    shim.parent.mkdir(parents=True)
    shutil.copy2(ROOT / "scripts/agent_runtime/shims/gh", shim)
    (scripts / "config").mkdir()
    (scripts / "config/fleet_repos.yaml").write_text(json.dumps({"repos": CATALOG}))
    (root / ".venv").symlink_to(Path(sys.executable).parent.parent, target_is_directory=True)
    tooling = make_tooling(tmp_path / "private-fixture/tools/public_opsec_scan")
    env = {k: v for k, v in os.environ.items() if not k.startswith(("GIT_", "PRE_COMMIT", "LU_OPSEC"))}
    git = shutil.which("git", path=os.defpath)
    subprocess.run([git, "init", "-q", str(root)], env=env, check=True, timeout=30)
    subprocess.run(
        [git, "-C", str(root), "remote", "add", "origin", "https://github.com/unit/public.git"],
        env=env,
        check=True,
        timeout=30,
    )
    return root, shim, tooling


@pytest.fixture
def publisher_transport(monkeypatch):
    """Explicitly inject existing subprocess spies at the typed transport boundary."""
    from scripts.publish import github
    original = github._send
    def send(argv, *, runner, **kwargs):
        return original(argv, runner=subprocess.run if runner is None else runner, **kwargs)
    monkeypatch.setattr(github, "_send", send)
