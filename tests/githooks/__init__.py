"""Synthetic dependencies for repositories exercising the tracked hook chain."""

import shutil
from importlib.resources import files
from pathlib import Path

import yaml

from tests.helpers import machinery_package
from tests.opsec_fixtures import CATALOG, make_tooling


def install_message_scanner(repo: Path) -> None:
    package = machinery_package()
    shutil.copytree(Path(str(files("lu_machinery.opsec"))), repo / package / "opsec",
                    ignore=shutil.ignore_patterns("__pycache__"))
    config = repo / package / "config/fleet_repos.yaml"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(yaml.safe_dump({"repos": CATALOG}), encoding="utf-8")
    make_tooling(repo.parent / "private-fixture/tools/public_opsec_scan")
