from pathlib import Path

import pytest

from scripts.audit import check_locked_module_not_published

pytestmark = pytest.mark.reads_content


def _write_track_fixture(tmp_path: Path, *, locked_frontmatter: str) -> Path:
    docs_dir = tmp_path / "docs"
    track_dir = docs_dir / "folk"
    track_dir.mkdir(parents=True)
    (track_dir / "index.mdx").write_text(
        """---
title: Folk
---

<LevelLanding
  modules={[
        { num: 1, slug: "active-module", title: "Active", sub: "Active", status: "active" },
        { num: 2, slug: "locked-module", title: "Locked", sub: "Locked", status: "locked" },
  ]}
/>
""",
        encoding="utf-8",
    )
    (track_dir / "active-module.mdx").write_text("---\ntitle: Active\n---\n\nLive.\n", encoding="utf-8")
    (track_dir / "locked-module.mdx").write_text(locked_frontmatter + "\n\nLocked body.\n", encoding="utf-8")
    return docs_dir


def test_locked_module_without_draft_true_is_reported(tmp_path: Path) -> None:
    docs_dir = _write_track_fixture(tmp_path, locked_frontmatter="---\ntitle: Locked\n---")
    scope = check_locked_module_not_published.CheckScope(tracks=frozenset({"folk"}), modules=frozenset())

    findings = check_locked_module_not_published.check_scope(scope, docs_dir=docs_dir)

    assert len(findings) == 1
    assert findings[0].module.slug == "locked-module"
    assert findings[0].module.status == "locked"
    assert findings[0].mdx_path == docs_dir / "folk" / "locked-module.mdx"
