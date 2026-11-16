"""Synthetic dependencies for repositories exercising the tracked hook chain."""

from importlib.resources import files
from pathlib import Path

import yaml

from tests.opsec_fixtures import CATALOG, copy_publisher_scripts, make_tooling


def install_message_scanner(repo: Path) -> None:
    package = "lu_machinery"
    copy_publisher_scripts(Path(str(files(package))), repo / package)
    config = repo / package / "config/fleet_repos.yaml"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(yaml.safe_dump({"repos": CATALOG}), encoding="utf-8")
    make_tooling(repo.parent / "private-fixture/tools/public_opsec_scan")
