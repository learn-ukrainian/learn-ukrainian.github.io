import subprocess
from pathlib import Path

import pytest
import yaml

from scripts.audit.check_writer_prompt_size import (
    WRITER_PROMPT_CEILING_BYTES,
    render_fixture_writer_prompt,
)
from scripts.build import linear_pipeline
from scripts.level_config import base_level
from scripts.pipeline import learner_state
from scripts.verification import vesum
from wiki import config as wiki_config
from wiki import sources_db as wiki_sources_db

pytestmark = pytest.mark.reads_content

# Committed module inputs for the A1 letter ceiling check. A sparse checkout
# omits these trees; the bytes still live in HEAD.
_A1_LETTER_PLAN = "curriculum/l2-uk-en/plans/a1/sounds-letters-and-hello.yaml"
_A1_LETTER_WIKI = "wiki/pedagogy/a1/sounds-letters-and-hello.md"
_A1_LETTER_SOURCES = "wiki/pedagogy/a1/sounds-letters-and-hello.sources.yaml"
_A1_CURRICULUM = "curriculum/l2-uk-en/curriculum.yaml"
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


def _learner_state_plan_slugs(curriculum_text: str, track: str, module_num: int) -> list[str]:
    """Plan slugs ``build_learner_state`` reads for this module.

    Module 1 with a non-empty roster reads only the next module's plan. An
    empty roster reads none. Later modules also read each preceding plan.
    """
    data = yaml.safe_load(curriculum_text) or {}
    levels = data.get("levels") if isinstance(data, dict) else None
    entry = levels.get(track) if isinstance(levels, dict) else None
    modules = entry.get("modules") if isinstance(entry, dict) else None
    if not isinstance(modules, list):
        modules = []
    if not modules or module_num <= 1:
        if len(modules) > 1:
            return [learner_state._parse_slug(modules[1])]
        return []
    slugs = [learner_state._parse_slug(item) for item in modules[: module_num - 1]]
    if module_num < len(modules):
        slugs.append(learner_state._parse_slug(modules[module_num]))
    return slugs


def _stage_learner_state_inputs(root: Path, plan_text: str) -> Path:
    """Stage the curriculum manifest and any plan ``build_learner_state`` opens."""
    plan = yaml.safe_load(plan_text)
    track = str(plan["level"]).strip().lower()
    module_num = int(plan["sequence"])
    curriculum_path = _stage_checkout_file(root, _A1_CURRICULUM)
    curriculum_root = root / "curriculum" / "l2-uk-en"
    plan_track = base_level(track, manifest=curriculum_path)
    for slug in _learner_state_plan_slugs(curriculum_path.read_text(encoding="utf-8"), track, module_num):
        _stage_checkout_file(root, f"curriculum/l2-uk-en/plans/{plan_track}/{slug}.yaml")
    return curriculum_root


def _pin_base_level_manifest(monkeypatch: pytest.MonkeyPatch, manifest: Path) -> None:
    """Send ``base_level()`` at the staged manifest, not the checkout file.

    Activity config and immersion call ``base_level(track)``. The manifest
    default is bound on the function, and ``scripts`` on ``sys.path`` can load
    ``level_config`` as a second module. Both copies have to move together.
    """
    import level_config
    import scripts.level_config as scripts_level_config

    seen_modules: set[int] = set()
    seen_fns: set[int] = set()
    for module in (level_config, scripts_level_config):
        if id(module) in seen_modules:
            continue
        seen_modules.add(id(module))
        monkeypatch.setattr(module, "MANIFEST", manifest)
        fn = module.base_level
        if id(fn) in seen_fns:
            continue
        seen_fns.add(id(fn))
        kwdefaults = dict(fn.__kwdefaults__ or {})
        kwdefaults["manifest"] = manifest
        monkeypatch.setattr(fn, "__kwdefaults__", kwdefaults)


def _pin_a1_letter_prompt_inputs(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Render the committed module with no gitignored corpus database.

    ``build_knowledge_packet`` reads ``data/vesum.db`` and ``data/sources.db``
    (including a primary-checkout fallback from a sparse worktree). Those files
    are not in CI. When they exist, dictionary style notes and textbook search
    hits push this prompt over ``WRITER_PROMPT_CEILING_BYTES``.

    Corpus-absent coverage boundary (#9343, #9344): those databases stay
    unread here. #9343 is the full-corpus textbook-excerpt overrun; #9344 is
    the corpus-present heritage fallback that accepts mixed-case surfaces.
    """
    plan_path = _stage_checkout_file(tmp_path, _A1_LETTER_PLAN)
    article_path = _stage_checkout_file(tmp_path, _A1_LETTER_WIKI)
    _stage_checkout_file(tmp_path, _A1_LETTER_SOURCES)
    curriculum_root = _stage_learner_state_inputs(tmp_path, plan_path.read_text(encoding="utf-8"))
    absent_db = tmp_path / "no-corpus.db"

    monkeypatch.setattr(linear_pipeline, "plan_path_for", lambda *_args: plan_path)
    monkeypatch.setattr(wiki_config, "WIKI_DIR", tmp_path / "wiki")
    monkeypatch.setattr(linear_pipeline, "_wiki_article_paths", lambda *_args: [article_path])
    monkeypatch.setattr(vesum, "VESUM_DB_PATH", absent_db)
    monkeypatch.setattr(linear_pipeline, "TEXTBOOK_SOURCES_DB_PATH", absent_db)
    monkeypatch.setattr(wiki_sources_db, "_conn", None)
    monkeypatch.setattr(wiki_sources_db, "_read_db_path", lambda: absent_db)
    monkeypatch.setattr(learner_state, "CURRICULUM_ROOT", curriculum_root)
    _pin_base_level_manifest(monkeypatch, curriculum_root / "curriculum.yaml")


def test_a1_letter_prompt_keeps_six_distinct_corpus_excerpts_whole_under_ceiling(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Fixture corpus only: no excerpt is traded for the prompt's editorial history."""
    from tests.test_textbook_grounding import _seed_textbook_db

    _pin_a1_letter_prompt_inputs(monkeypatch, tmp_path)
    plan_path = linear_pipeline.plan_path_for("a1", "sounds-letters-and-hello")
    plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
    references = [
        {"title": f"Караман Grade 10, p.{page}", "notes": f"Fixture grounding {page}."}
        for page in range(1, 7)
    ]
    plan["references"] = references
    plan_path.write_text(yaml.safe_dump(plan, allow_unicode=True, sort_keys=False), encoding="utf-8")
    rows = [
        {
            "chunk_id": f"fixture-source-{page}_s{page:04d}",
            "source_file": f"fixture-source-{page}",
            "title": f"Fixture page {page}",
            "grade": "10",
            "author_uk": "Караман",
            "text": f"BEGIN-{page} " + (f"whole excerpt {page} " * 70) + f"END-{page}",
        }
        for page in range(1, 7)
    ]
    db_path = tmp_path / "fixture-corpus.db"
    _seed_textbook_db(db_path, rows)
    monkeypatch.setattr(linear_pipeline, "TEXTBOOK_SOURCES_DB_PATH", db_path)

    prompt = render_fixture_writer_prompt("a1", "sounds-letters-and-hello")

    assert prompt.count("\n## Plan References\n") == 1
    for page, (reference, row) in enumerate(zip(references, rows, strict=True), start=1):
        quote = "\n".join(f"> {line}" for line in row["text"].splitlines())
        section = prompt.split(f"### {reference['title']}\n", 1)[1].split("\n##", 1)[0]
        assert quote in section
        assert f"Source: {row['title']} (Караман, Grade 10, p.{page}, {row['source_file']})" in section
        assert prompt.count(quote) == 1
    size = len(prompt.encode("utf-8"))
    assert size <= WRITER_PROMPT_CEILING_BYTES, f"Fixture-corpus prompt: {size} bytes"
    print(f"Fixture corpus: 6/6 whole distinct excerpts; {size}/{WRITER_PROMPT_CEILING_BYTES} bytes.")


def _render_pinned_a1_letter_prompt(monkeypatch: pytest.MonkeyPatch, root: Path) -> str:
    _pin_a1_letter_prompt_inputs(monkeypatch, root)
    return render_fixture_writer_prompt("a1", "sounds-letters-and-hello")


def _outside(path: Path, root: Path) -> bool:
    """True when ``path`` is neither ``root`` nor a path inside it."""
    resolved = path.resolve()
    root_resolved = root.resolve()
    return resolved != root_resolved and root_resolved not in resolved.parents


def test_a1_letter_prompt_bytes_ignore_staged_root(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Stage location does not change the rendered prompt bytes.

    Outside the checkout: a short root and a long root whose name contains a
    quote and a backslash. Inside the checkout: two different depths under a
    temporary project tree with the same relative layout. A normal read of the
    same article, at that tree's ``wiki/`` path, stores today's
    repository-relative wiki path. All five renders are the same bytes.
    ``PROJECT_ROOT`` for the inside and normal cases is the temporary tree.
    """
    real_root = Path(wiki_config.PROJECT_ROOT).resolve()
    checkout = (tmp_path / "checkout-9335").resolve()
    outside_short = tmp_path / "stage-root-short-9335"
    outside_long = tmp_path.joinpath(
        "n" * 180,
        "n" * 180,
        'stage-root-"9335\\',
        "n" * 180,
    )
    inside_shallow = checkout / "tmp" / "impl-9335-r4-shallow"
    inside_deep = checkout / "tmp" / "impl-9335-r4-deep" / "nested" / "stage"
    checkout_article = checkout / _A1_LETTER_WIKI
    expected_wiki_path = '"wiki_path": "wiki/pedagogy/a1/sounds-letters-and-hello.md"'
    today = "wiki/pedagogy/a1/sounds-letters-and-hello.md"

    assert _outside(tmp_path, real_root)
    for path in (checkout, outside_short, outside_long, inside_shallow, inside_deep, checkout_article):
        assert _outside(path, real_root)
    assert _outside(outside_short, checkout)
    assert _outside(outside_long, checkout)
    shallow_depth = len(inside_shallow.resolve().relative_to(checkout).parts)
    deep_depth = len(inside_deep.resolve().relative_to(checkout).parts)
    assert shallow_depth < deep_depth
    assert checkout in inside_shallow.resolve().parents
    assert checkout in inside_deep.resolve().parents

    prompts: list[str] = []

    def _accept(prompt: str) -> None:
        assert "stage-root-" not in prompt
        assert "impl-9335-r4-" not in prompt
        assert "checkout-9335" not in prompt
        assert expected_wiki_path in prompt
        prompts.append(prompt)

    for root in (outside_short, outside_long):
        _accept(_render_pinned_a1_letter_prompt(monkeypatch, root))

    monkeypatch.setattr(wiki_config, "PROJECT_ROOT", checkout)
    for root in (inside_shallow, inside_deep):
        assert Path(wiki_config.PROJECT_ROOT).resolve() in root.resolve().parents
        _accept(_render_pinned_a1_letter_prompt(monkeypatch, root))

    _stage_checkout_file(checkout, _A1_LETTER_WIKI)
    _stage_checkout_file(checkout, _A1_LETTER_SOURCES)
    _pin_a1_letter_prompt_inputs(monkeypatch, outside_short)
    monkeypatch.setattr(wiki_config, "PROJECT_ROOT", checkout)
    monkeypatch.setattr(wiki_config, "WIKI_DIR", checkout / "wiki")
    monkeypatch.setattr(linear_pipeline, "_wiki_article_paths", lambda *_args: [checkout_article])
    checkout_prompt = render_fixture_writer_prompt("a1", "sounds-letters-and-hello")
    stored_today = checkout_article.resolve().relative_to(Path(wiki_config.PROJECT_ROOT).resolve()).as_posix()
    assert stored_today == today
    assert f'"wiki_path": "{stored_today}"' in checkout_prompt
    assert "checkout-9335" not in checkout_prompt
    prompts.append(checkout_prompt)

    for prompt in prompts[1:]:
        assert prompt == prompts[0]
    assert len(prompts[0].encode("utf-8")) <= WRITER_PROMPT_CEILING_BYTES
