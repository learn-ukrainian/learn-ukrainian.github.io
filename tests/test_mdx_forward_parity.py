from __future__ import annotations

from pathlib import Path

from scripts.audit import check_mdx_forward_parity as forward_parity


def test_detects_folk_module_source() -> None:
    path = forward_parity.SOURCE_DIR / "folk/narodna-kultura-yak-systema/module.md"

    assert forward_parity.affected_source_targets([path]) == {
        forward_parity.ModuleTarget("folk", "narodna-kultura-yak-systema")
    }


def test_detects_seminar_plan_source() -> None:
    path = forward_parity.SOURCE_DIR / "plans/folk/narodna-kultura-yak-systema.yaml"

    assert forward_parity.affected_source_targets([path]) == {
        forward_parity.ModuleTarget("folk", "narodna-kultura-yak-systema")
    }


def test_ignores_core_track_source() -> None:
    path = forward_parity.SOURCE_DIR / "a1/things-have-gender/module.md"

    assert forward_parity.affected_source_targets([path]) == set()


def test_normalize_strips_nav_frontmatter_and_trailing_whitespace() -> None:
    generated = (
        "---\n"
        'title: "Demo"\n'
        "prev: false\n"
        "next: after\n"
        "---\n"
        "Body   \n"
    )
    committed = """---
title: "Demo"
prev: before
next: false
---
Body
"""

    assert forward_parity.normalize_mdx_for_parity(generated) == forward_parity.normalize_mdx_for_parity(committed)


def test_check_targets_flags_stale_committed_mdx(tmp_path: Path, monkeypatch) -> None:
    source_dir = tmp_path / "curriculum/l2-uk-en"
    mdx_dir = tmp_path / "site/src/content/docs"
    module_dir = source_dir / "folk/demo"
    module_dir.mkdir(parents=True)
    mdx_path = mdx_dir / "folk/demo.mdx"
    mdx_path.parent.mkdir(parents=True)
    mdx_path.write_text("---\ntitle: Demo\n---\nCommitted\n", encoding="utf-8")

    monkeypatch.setattr(forward_parity, "SOURCE_DIR", source_dir)
    monkeypatch.setattr(forward_parity, "MDX_DIR", mdx_dir)

    def fake_assemble(target: forward_parity.ModuleTarget, output_path: Path) -> str:
        return "---\ntitle: Demo\n---\nGenerated\n"

    monkeypatch.setattr(forward_parity, "_assemble_target", fake_assemble)

    assert forward_parity.check_targets({forward_parity.ModuleTarget("folk", "demo")}) == [
        "source changed but site MDX stale for folk/demo — regenerate "
        "(assemble_mdx / `make` path) and commit site/src/content/docs/folk/demo.mdx"
    ]


def test_check_targets_accepts_nav_only_drift(tmp_path: Path, monkeypatch) -> None:
    source_dir = tmp_path / "curriculum/l2-uk-en"
    mdx_dir = tmp_path / "site/src/content/docs"
    module_dir = source_dir / "folk/demo"
    module_dir.mkdir(parents=True)
    mdx_path = mdx_dir / "folk/demo.mdx"
    mdx_path.parent.mkdir(parents=True)
    mdx_path.write_text(
        "---\ntitle: Demo\nprev: before\nnext: after\n---\nSame body  \n",
        encoding="utf-8",
    )

    monkeypatch.setattr(forward_parity, "SOURCE_DIR", source_dir)
    monkeypatch.setattr(forward_parity, "MDX_DIR", mdx_dir)

    def fake_assemble(target: forward_parity.ModuleTarget, output_path: Path) -> str:
        return "---\ntitle: Demo\nprev: false\nnext: false\n---\nSame body\n"

    monkeypatch.setattr(forward_parity, "_assemble_target", fake_assemble)

    assert forward_parity.check_targets({forward_parity.ModuleTarget("folk", "demo")}) == []
