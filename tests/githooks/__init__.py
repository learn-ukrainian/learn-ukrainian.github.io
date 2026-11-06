"""Synthetic dependencies for repositories exercising the tracked hook chain."""

import shutil
from pathlib import Path

import yaml

from tests.helpers import machinery_package
from tests.opsec_fixtures import CATALOG, ROOT, make_tooling


def install_message_scanner(repo: Path) -> None:
    package = machinery_package()
    shutil.copytree(ROOT / package / "opsec", repo / package / "opsec",
                    ignore=shutil.ignore_patterns("__pycache__"))
    config = repo / package / "config/fleet_repos.yaml"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(yaml.safe_dump({"repos": CATALOG}), encoding="utf-8")
    make_tooling(repo.parent / "private-fixture/tools/public_opsec_scan")
