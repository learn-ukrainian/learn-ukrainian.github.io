import json
import subprocess
from pathlib import Path

import pytest

from scripts.audit.check_writer_prompt_size import (
    WRITER_PROMPT_CEILING_BYTES,
    render_fixture_writer_prompt,
)
from scripts.build import linear_pipeline
from scripts.build.phases.implementation_map import seed_implementation_map
from scripts.verification import vesum
from wiki import config as wiki_config
from wiki import sources_db as wiki_sources_db

pytestmark = pytest.mark.reads_content

# Committed module inputs for the A1 letter ceiling check. A sparse checkout
# omits these trees; the bytes still live in HEAD.
_A1_LETTER_PLAN = "curriculum/l2-uk-en/plans/a1/sounds-letters-and-hello.yaml"
_A1_LETTER_WIKI = "wiki/pedagogy/a1/sounds-letters-and-hello.md"
_A1_LETTER_SOURCES = "wiki/pedagogy/a1/sounds-letters-and-hello.sources.yaml"


def _checkout_text(rel: str) -> str:
    """Working-tree file when this checkout has it, otherwise the HEAD blob."""
    path = Path(rel)
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return subprocess.check_output(
        ["git", "show", f"HEAD:{rel}"],
        text=True,
        encoding="utf-8",
        timeout=30,
    )


def _stage_checkout_file(root: Path, rel: str) -> Path:
    dest = root / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(_checkout_text(rel), encoding="utf-8")
    return dest


def _pin_a1_letter_prompt_inputs(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Render the committed module with no gitignored corpus database.

    ``build_knowledge_packet`` reads ``data/vesum.db`` and ``data/sources.db``
    (including a primary-checkout fallback from a sparse worktree). Those files
    are not in CI. When they exist, dictionary style notes and textbook search
    hits push this prompt over ``WRITER_PROMPT_CEILING_BYTES``.
    """
    plan_path = _stage_checkout_file(tmp_path, _A1_LETTER_PLAN)
    article_path = _stage_checkout_file(tmp_path, _A1_LETTER_WIKI)
    _stage_checkout_file(tmp_path, _A1_LETTER_SOURCES)
    absent_db = tmp_path / "no-corpus.db"

    monkeypatch.setattr(linear_pipeline, "plan_path_for", lambda *_args: plan_path)
    monkeypatch.setattr(wiki_config, "WIKI_DIR", tmp_path / "wiki")
    monkeypatch.setattr(linear_pipeline, "_wiki_article_paths", lambda *_args: [article_path])
    monkeypatch.setattr(vesum, "VESUM_DB_PATH", absent_db)
    monkeypatch.setattr(linear_pipeline, "TEXTBOOK_SOURCES_DB_PATH", absent_db)
    monkeypatch.setattr(wiki_sources_db, "_conn", None)
    monkeypatch.setattr(wiki_sources_db, "_read_db_path", lambda: absent_db)


def _stub_manifest(level: str, slug: str) -> dict:
    return {
        "slug": slug,
        "wiki_path": f"wiki/pedagogy/{level}/{slug}.md",
        "sequence_steps": [],
        "l2_errors": [],
        "phonetic_rules": [],
        "decolonization_bans": [],
        "external_resources": [],
    }


def _render_c1_sample_prompt() -> str:
    level = "c1"
    slug = "abstract-writing"
    plan_path = linear_pipeline.plan_path_for(level, slug)
    plan = linear_pipeline.load_plan(plan_path)
    manifest = _stub_manifest(level, slug)
    return linear_pipeline.render_writer_prompt(
        plan=plan,
        plan_content=plan_path.read_text(encoding="utf-8"),
        knowledge_packet="Knowledge packet stub for C1 prompt-size smoke.",
        wiki_manifest=json.dumps(manifest, ensure_ascii=False, indent=2),
        implementation_map=seed_implementation_map(manifest, plan=plan),
    )


def test_a1_letter_module_writer_prompt_stays_under_ceiling(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _pin_a1_letter_prompt_inputs(monkeypatch, tmp_path)
    prompt = render_fixture_writer_prompt("a1", "sounds-letters-and-hello")

    assert len(prompt.encode("utf-8")) <= WRITER_PROMPT_CEILING_BYTES


def test_a1_m20_writer_prompt_stays_under_ceiling() -> None:
    prompt = render_fixture_writer_prompt("a1", "my-morning")

    assert len(prompt.encode("utf-8")) <= WRITER_PROMPT_CEILING_BYTES


def test_c1_sample_writer_prompt_stays_under_ceiling() -> None:
    prompt = _render_c1_sample_prompt()

    assert len(prompt.encode("utf-8")) <= WRITER_PROMPT_CEILING_BYTES
