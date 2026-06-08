"""Tests for dossier-grounded wiki compilation prompts."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))


def _write_prompt_template(prompts_dir: Path, template: str) -> None:
    prompts_dir.mkdir(parents=True, exist_ok=True)
    (prompts_dir / "compile_article.md").write_text(
        template,
        encoding="utf-8",
    )


def test_load_dossier_text_returns_none_for_missing_path(tmp_path, monkeypatch):
    from wiki import sources

    monkeypatch.setattr(sources, "PROJECT_ROOT", tmp_path)

    assert sources.load_dossier_text("bio", "missing") is None


def test_load_dossier_text_returns_existing_dossier(tmp_path, monkeypatch):
    from wiki import sources

    dossier_path = tmp_path / "docs" / "research" / "bio" / "demo.md"
    dossier_path.parent.mkdir(parents=True)
    dossier_path.write_text("# Demo dossier\n\nVerified fact.\n", encoding="utf-8")
    monkeypatch.setattr(sources, "PROJECT_ROOT", tmp_path)

    assert sources.load_dossier_text("bio", "demo") == (
        "# Demo dossier\n\nVerified fact.\n"
    )


def test_build_prompt_injects_authoritative_dossier(tmp_path):
    from wiki.compiler import _build_prompt

    prompts_dir = tmp_path / "prompts"
    _write_prompt_template(
        prompts_dir,
        "# Compile {topic}\n\n{dossier_section}## Sources\n{sources}\n",
    )
    dossier_text = "# Dossier\n\nFact tier: verified.\n"

    with patch("wiki.compiler.PROMPTS_DIR", prompts_dir):
        prompt = _build_prompt(
            topic="Demo",
            slug="demo",
            domain="figures",
            sources=[{"chunk_id": "c1", "text": "Retrieved chunk."}],
            track="bio",
            dossier_text=dossier_text,
        )

    assert "## AUTHORITATIVE DOSSIER" in prompt
    assert "# Dossier\n\nFact tier: verified." in prompt
    assert "DOSSIER WINS" in prompt
    assert prompt.index("## AUTHORITATIVE DOSSIER") < prompt.index("## Sources")


def test_build_prompt_without_dossier_preserves_existing_prompt(tmp_path):
    from wiki.compiler import _build_prompt

    old_prompts_dir = tmp_path / "old-prompts"
    new_prompts_dir = tmp_path / "new-prompts"
    old_template = "# Compile {topic}\n\n## Sources\n{sources}\n"
    new_template = "# Compile {topic}\n\n{dossier_section}## Sources\n{sources}\n"
    _write_prompt_template(old_prompts_dir, old_template)
    _write_prompt_template(new_prompts_dir, new_template)
    kwargs = {
        "topic": "Demo",
        "slug": "demo",
        "domain": "figures",
        "sources": [{"chunk_id": "c1", "text": "Retrieved chunk."}],
        "track": "bio",
    }

    with patch("wiki.compiler.PROMPTS_DIR", old_prompts_dir):
        before = _build_prompt(**kwargs)
    with patch("wiki.compiler.PROMPTS_DIR", new_prompts_dir):
        after = _build_prompt(**kwargs)

    assert after == before
    assert "AUTHORITATIVE DOSSIER" not in after


def test_cmd_compile_one_passes_dossier_text_to_compile_article():
    from wiki.compile import cmd_compile_one

    chunks = [{"chunk_id": "c1", "text": "Retrieved chunk."}]

    with (
        patch("wiki.compile._get_domain", return_value="figures"),
        patch("wiki.compile._compiled_article_is_ready", return_value=False),
        patch("wiki.compile.gather_discovery_sources", return_value={}),
        patch("wiki.compile.enrich_sources", return_value=chunks),
        patch("wiki.compile._slug_to_topic", return_value="Demo"),
        patch("wiki.compile.load_dossier_text", return_value="Dossier fact."),
        patch("wiki.compile.compile_article", return_value=None) as compile_article,
        patch("wiki.state.is_compiled", return_value=False),
    ):
        assert cmd_compile_one("bio", "demo", dry_run=True) is True

    assert compile_article.call_args.kwargs["dossier_text"] == "Dossier fact."


def test_cmd_compile_one_dossier_only_proceeds_when_no_discovery():
    """A slug with a dossier but no discovery file compiles dossier-only.

    New seminar topics (folk broad-scope, bio new-130) have a verified dossier
    but no discovery file. The compile must proceed grounded on the dossier
    rather than bailing at the discovery gate.
    """
    from wiki.compile import cmd_compile_one

    with (
        patch("wiki.compile._get_domain", return_value="ritual"),
        patch("wiki.compile._compiled_article_is_ready", return_value=False),
        patch(
            "wiki.compile.gather_discovery_sources",
            return_value={"error": "No discovery file for folk/demo"},
        ),
        patch(
            "wiki.compile.enrich_sources",
            return_value=[{"chunk_id": "stub", "text": "x"}],
        ) as enrich,
        patch("wiki.compile._slug_to_topic", return_value="Демо"),
        patch("wiki.compile.load_dossier_text", return_value="# Демо\n\nVerified."),
        patch("wiki.compile.compile_article", return_value=None) as compile_article,
        patch("wiki.state.is_compiled", return_value=False),
    ):
        assert cmd_compile_one("folk", "demo", dry_run=True) is True

    # The dossier-only path hands enrich_sources an empty sources_info ...
    assert enrich.call_args.args[2] == {}
    # ... and still injects the dossier as the authoritative grounding tier.
    assert compile_article.call_args.kwargs["dossier_text"] == "# Демо\n\nVerified."


def test_cmd_compile_one_fails_when_no_discovery_and_no_dossier():
    """The discovery gate still hard-fails when there is ALSO no dossier."""
    from wiki.compile import cmd_compile_one

    with (
        patch("wiki.compile._get_domain", return_value="ritual"),
        patch("wiki.compile._compiled_article_is_ready", return_value=False),
        patch(
            "wiki.compile.gather_discovery_sources",
            return_value={"error": "No discovery file for folk/ghost"},
        ),
        patch("wiki.compile.load_dossier_text", return_value=None),
        patch("wiki.compile.compile_article") as compile_article,
        patch("wiki.state.is_compiled", return_value=False),
    ):
        assert cmd_compile_one("folk", "ghost", dry_run=True) is False

    compile_article.assert_not_called()


def test_dossier_title_extracts_cyrillic_h1(monkeypatch):
    from wiki import compile as compile_mod

    monkeypatch.setattr(
        compile_mod,
        "load_dossier_text",
        lambda track, slug: "# Календарна обрядовість і звичаї\n\n- **Slug:** `x`\n",
    )
    assert compile_mod._dossier_title("folk", "x") == "Календарна обрядовість і звичаї"


def test_dossier_title_strips_research_dossier_suffix(monkeypatch):
    from wiki import compile as compile_mod

    monkeypatch.setattr(
        compile_mod,
        "load_dossier_text",
        lambda track, slug: "# Тарас Григорович Шевченко — Research Dossier\n\nbody\n",
    )
    assert compile_mod._dossier_title("bio", "x") == "Тарас Григорович Шевченко"


def test_dossier_title_none_when_no_dossier(monkeypatch):
    from wiki import compile as compile_mod

    monkeypatch.setattr(compile_mod, "load_dossier_text", lambda track, slug: None)
    assert compile_mod._dossier_title("folk", "x") is None


def test_slug_to_topic_uses_dossier_title_when_no_keywords(monkeypatch):
    """Dossier-only topics get a Cyrillic title, never a Latin-slug transliteration."""
    from wiki import compile as compile_mod

    monkeypatch.setattr(
        compile_mod,
        "load_dossier_text",
        lambda track, slug: "# Календарна обрядовість і звичаї\n\nbody\n",
    )
    topic = compile_mod._slug_to_topic("kalendarna-obriadovist-zvychai", "folk", None)
    assert topic == "Український фольклор: Календарна обрядовість і звичаї"
    assert "Kalendarna" not in topic
