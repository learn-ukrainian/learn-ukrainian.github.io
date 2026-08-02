from __future__ import annotations

import json
from pathlib import Path

from scripts.entire.validate_checkpoint_routing import validate


def _write_config(root: Path, *, configured: str, allowed: list[str]) -> None:
    entire = root / ".entire"
    entire.mkdir()
    (entire / "settings.json").write_text(
        json.dumps(
            {
                "strategy_options": {
                    "checkpoint_remote": {"provider": "github", "repo": configured}
                }
            }
        )
    )
    (entire / "phase05-allowlist.json").write_text(
        json.dumps({"checkpoint_endpoints": [{"github_repo": repo} for repo in allowed]})
    )


def test_accepts_matching_single_private_destination(tmp_path: Path) -> None:
    _write_config(tmp_path, configured="org/private", allowed=["org/private"])

    assert validate(tmp_path) is None


def test_rejects_routing_drift(tmp_path: Path) -> None:
    _write_config(tmp_path, configured="org/private", allowed=["org/other"])

    assert validate(tmp_path) == (
        "checkpoint_remote.repo does not match the egress allowlist"
    )


def test_rejects_multiple_destinations(tmp_path: Path) -> None:
    _write_config(
        tmp_path,
        configured="org/private",
        allowed=["org/private", "org/other"],
    )

    assert validate(tmp_path) == (
        "checkpoint_endpoints must contain exactly one destination"
    )
