"""The rate-limit reclassifier walks archived records too (#8625)."""

from __future__ import annotations

from scripts.maintenance import reclassify_dispatch_status as rds


def test_reclassify_walks_hot_then_archived_records(tmp_path, monkeypatch):
    tasks = tmp_path / "tasks"
    (tasks / "archive").mkdir(parents=True)
    (tasks / "hot.json").write_text("{}", encoding="utf-8")
    (tasks / "archive" / "old.json").write_text("{}", encoding="utf-8")
    seen: list[str] = []

    def probe(path, **_kwargs):
        seen.append(str(path.relative_to(tasks)))
        return ("skipped", path.stem, "probe")

    monkeypatch.setattr(rds, "_reclassify_task", probe)
    monkeypatch.setattr(rds, "_load_usage_by_task_id", lambda _usage_dir: {})

    outcome = rds.reclassify_rate_limited_tasks(tasks_dir=tasks, usage_dir=tmp_path / "usage", dry_run=True)

    assert seen == ["hot.json", "archive/old.json"]
    assert outcome["skipped"] == [("hot", "probe"), ("old", "probe")]
