"""dual-write-status / inventory-derived session stream registry (Sol PR-H)."""

from __future__ import annotations

from pathlib import Path

import yaml

from agents_extensions.shared.session_streams.dual_write import (
    list_handoff_candidates,
    resolve_handoff_path,
)
from agents_extensions.shared.session_streams.inventory import (
    epic_handoff_map,
    inventory_covers_issue_streams,
    load_stream_epic_inventory,
)


def test_inventory_covers_repo_issue_streams():
    repo = Path(__file__).resolve().parents[1]
    ok, missing = inventory_covers_issue_streams(repo)
    assert ok is True
    assert missing == []
    records = load_stream_epic_inventory(repo)
    # issue_streams.yaml has more than the old hard-coded four epics
    assert len(records) >= 10
    ids = {r.stream_id for r in records}
    assert "epic:4387" in ids
    assert "epic:4707" in ids
    assert "epic:4542" in ids
    assert "epic:2836" in ids  # folk — was not in the hard-coded four


def test_list_handoff_candidates_marks_missing(tmp_path: Path):
    # Minimal issue_streams fixture
    streams = {
        "schema_version": 1,
        "streams": {
            "demo": {"title": "Demo", "epics": [9999]},
        },
    }
    yml = tmp_path / "issue_streams.yaml"
    yml.write_text(yaml.safe_dump(streams), encoding="utf-8")
    # Point inventory at fixture via writing under scripts/config path structure
    cfg = tmp_path / "scripts" / "config"
    cfg.mkdir(parents=True)
    (cfg / "issue_streams.yaml").write_text(yaml.safe_dump(streams), encoding="utf-8")
    rows = list_handoff_candidates(tmp_path)
    assert rows
    assert all(r.exists is False for r in rows)
    assert any(r.stream_id == "epic:9999" for r in rows)


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
