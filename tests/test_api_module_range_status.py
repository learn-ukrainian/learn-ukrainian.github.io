from __future__ import annotations

from pathlib import Path

import pytest

from scripts.api import state_build

pytestmark = pytest.mark.reads_content


def _write_module_files(root: Path, slug: str) -> None:
    module_dir = root / "curriculum" / "l2-uk-en" / "b2" / slug
    module_dir.mkdir(parents=True, exist_ok=True)
    (module_dir / "module.md").write_text("# Module\n", encoding="utf-8")
    (module_dir / "activities.yaml").write_text("version: '1.0'\n", encoding="utf-8")
    (module_dir / "vocabulary.yaml").write_text("[]\n", encoding="utf-8")

    mdx_dir = root / "site" / "src" / "content" / "docs" / "b2"
    mdx_dir.mkdir(parents=True, exist_ok=True)
    (mdx_dir / f"{slug}.mdx").write_text("---\ntitle: Module\n---\n", encoding="utf-8")


def test_compute_module_range_status_reports_complete_and_remaining(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        state_build,
        "get_plan_slugs",
        lambda track_id, *args, **kwargs: [(32, "m32"), (33, "m33"), (34, "m34")],
    )

    _write_module_files(tmp_path, "m32")
    _write_module_files(tmp_path, "m33")
    score_dir = tmp_path / "docs" / "audits"
    score_dir.mkdir(parents=True)
    (score_dir / "b2-current-llm-scores-test.md").write_text(
        "B2 M32 `m32`,9/10,B+,Yes,done\n",
        encoding="utf-8",
    )
    (score_dir / "a1-current-llm-scores-test.md").write_text(
        "A1 M33 `m33`,9/10,B+,Yes,wrong track\n",
        encoding="utf-8",
    )

    result = state_build.compute_module_range_status(
        "b2",
        {"path": "b2"},
        start=32,
        end=34,
        curriculum_root=tmp_path / "curriculum" / "l2-uk-en",
        project_root=tmp_path,
    )

    assert result["deterministic"] is True
    assert result["total"] == 3
    assert result["complete"] == 1
    assert result["content_complete"] == 2
    assert result["score_persisted"] == 1
    assert result["incomplete"] == 2
    assert result["remaining"] == [
        {"num": 33, "slug": "m33", "missing": ["score"]},
        {
            "num": 34,
            "slug": "m34",
            "missing": ["module", "activities", "vocabulary", "mdx", "score"],
        },
    ]
    assert result["modules"][0]["status"] == "complete"
    assert result["modules"][1]["status"] == "partial"
    assert result["modules"][2]["status"] == "missing"
