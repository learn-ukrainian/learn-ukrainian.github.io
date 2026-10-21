"""dual-write-status / inventory-derived session stream registry (Sol PR-H)."""

from __future__ import annotations

from pathlib import Path

import yaml

from agents_extensions.shared.session_streams.dual_write import (
    resolve_handoff_path,
)
from agents_extensions.shared.session_streams.inventory import (
    epic_handoff_map,
)


def test_resolve_handoff_path_first_existing(tmp_path: Path):
    cfg = tmp_path / "scripts" / "config"
    cfg.mkdir(parents=True)
    (cfg / "issue_streams.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "streams": {"atlas-practice": {"title": "Atlas", "epics": [4387]}},
            }
        ),
        encoding="utf-8",
    )
    stream = "epic:4387"
    candidates = epic_handoff_map(tmp_path)[stream]
    second = tmp_path / candidates[1]
    second.parent.mkdir(parents=True, exist_ok=True)
    second.write_text("handoff\n", encoding="utf-8")
    resolved = resolve_handoff_path(stream, tmp_path)
    assert resolved == second.resolve()
