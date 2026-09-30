import json
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from scripts.audit.check_writer_prompt_size import (
    WRITER_PROMPT_CEILING_BYTES,
    render_fixture_writer_prompt,
)
from scripts.build import linear_pipeline
from scripts.build.phases.implementation_map import seed_implementation_map
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
# build_learner_state("a1", 1) loads grammar from modules[1] when that list is non-empty.
_A1_NEXT_PLAN = "curriculum/l2-uk-en/plans/a1/reading-ukrainian.yaml"


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


def _curriculum_with_named_next_module(curriculum_text: str) -> str:
    """Committed manifest plus an A1 roster whose second plan is readable."""
    data = yaml.safe_load(curriculum_text) or {}
    if not isinstance(data, dict):
        data = {}
    levels = data.setdefault("levels", {})
    if not isinstance(levels, dict):
        levels = {}
        data["levels"] = levels
    entry = levels.get("a1")
    if not isinstance(entry, dict):
        entry = {"type": "core"}
        levels["a1"] = entry
    entry["modules"] = ["sounds-letters-and-hello", "reading-ukrainian"]
    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False)


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


def _write_curriculum_root(root: Path, curriculum_text: str | None, plans: dict[str, str] | None = None) -> Path:
    curriculum_root = root / "curriculum" / "l2-uk-en"
    curriculum_root.mkdir(parents=True, exist_ok=True)
    if curriculum_text is not None:
        (curriculum_root / "curriculum.yaml").write_text(curriculum_text, encoding="utf-8")
    for rel, text in (plans or {}).items():
        dest = curriculum_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding="utf-8")
    return curriculum_root


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


def _a1_letter_prompt_size() -> int:
    prompt = render_fixture_writer_prompt("a1", "sounds-letters-and-hello")
    return len(prompt.encode("utf-8"))


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

    assert _a1_letter_prompt_size() <= WRITER_PROMPT_CEILING_BYTES


def _render_pinned_a1_letter_prompt(monkeypatch: pytest.MonkeyPatch, root: Path) -> str:
    _pin_a1_letter_prompt_inputs(monkeypatch, root)
    return render_fixture_writer_prompt("a1", "sounds-letters-and-hello")


def test_a1_letter_prompt_bytes_ignore_staged_root(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Stage location does not change the rendered prompt bytes.

    Outside the checkout: a short root and a long root whose name contains a
    quote and a backslash. Inside the checkout: two different depths. A normal
    checkout read of the same article stores today's repository-relative wiki
    path. All five renders are the same bytes.
    """
    project_root = Path(wiki_config.PROJECT_ROOT).resolve()
    outside_short = tmp_path / "stage-root-short-9335"
    outside_long = tmp_path.joinpath(
        "n" * 180,
        "n" * 180,
        'stage-root-"9335\\',
        "n" * 180,
    )
    inside_shallow = project_root / "tmp" / "impl-9335-r4-shallow"
    inside_deep = project_root / "tmp" / "impl-9335-r4-deep" / "nested" / "stage"
    checkout_wiki = project_root / "wiki"
    checkout_article = checkout_wiki / "pedagogy" / "a1" / "sounds-letters-and-hello.md"
    checkout_sources = checkout_article.with_suffix(".sources.yaml")
    expected_wiki_path = '"wiki_path": "wiki/pedagogy/a1/sounds-letters-and-hello.md"'
    today = "wiki/pedagogy/a1/sounds-letters-and-hello.md"

    outside_resolved = outside_short.resolve()
    assert project_root != outside_resolved and project_root not in outside_resolved.parents
    shallow_depth = len(inside_shallow.resolve().relative_to(project_root).parts)
    deep_depth = len(inside_deep.resolve().relative_to(project_root).parts)
    assert shallow_depth < deep_depth

    wiki_existed = checkout_wiki.exists()
    prompts: list[str] = []
    try:
        for root in (outside_short, outside_long, inside_shallow, inside_deep):
            prompt = _render_pinned_a1_letter_prompt(monkeypatch, root)
            prompts.append(prompt)
            assert "stage-root-" not in prompt
            assert "impl-9335-r4-" not in prompt
            assert expected_wiki_path in prompt

        checkout_article.parent.mkdir(parents=True, exist_ok=True)
        checkout_article.write_text(_checkout_text(_A1_LETTER_WIKI), encoding="utf-8")
        checkout_sources.write_text(_checkout_text(_A1_LETTER_SOURCES), encoding="utf-8")
        _pin_a1_letter_prompt_inputs(monkeypatch, outside_short)
        monkeypatch.setattr(wiki_config, "WIKI_DIR", checkout_wiki)
        monkeypatch.setattr(linear_pipeline, "_wiki_article_paths", lambda *_args: [checkout_article])
        checkout_prompt = render_fixture_writer_prompt("a1", "sounds-letters-and-hello")
        stored_today = checkout_article.resolve().relative_to(project_root).as_posix()
        assert stored_today == today
        assert f'"wiki_path": "{stored_today}"' in checkout_prompt
        prompts.append(checkout_prompt)

        for prompt in prompts[1:]:
            assert prompt == prompts[0]
        assert len(prompts[0].encode("utf-8")) <= WRITER_PROMPT_CEILING_BYTES
    finally:
        shutil.rmtree(inside_shallow, ignore_errors=True)
        shutil.rmtree(project_root / "tmp" / "impl-9335-r4-deep", ignore_errors=True)
        stage_tmp = project_root / "tmp"
        if stage_tmp.is_dir() and not any(stage_tmp.iterdir()):
            stage_tmp.rmdir()
        if wiki_existed:
            checkout_article.unlink(missing_ok=True)
            checkout_sources.unlink(missing_ok=True)
        else:
            shutil.rmtree(checkout_wiki, ignore_errors=True)


def test_a1_letter_prompt_size_ignores_ambient_curriculum(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Checkout curriculum.yaml present, absent, or modified does not move the size.

    ``writer_context`` reads that manifest from ``build_learner_state`` (and the
    next plan when the roster has one) and from ``base_level`` while resolving
    activity config. Both readers are pinned to the staged committed file.
    The three roots below stand in for that checkout file: the same bytes, no
    file, and a roster whose successor plan would otherwise enter the prompt.
    """
    committed = _checkout_text(_A1_CURRICULUM)
    roots = {
        "present": _write_curriculum_root(tmp_path / "present", committed),
        "absent": _write_curriculum_root(tmp_path / "absent", None),
        "modified": _write_curriculum_root(
            tmp_path / "modified",
            _curriculum_with_named_next_module(committed),
            {"plans/a1/reading-ukrainian.yaml": _checkout_text(_A1_NEXT_PLAN)},
        ),
    }
    _pin_a1_letter_prompt_inputs(monkeypatch, tmp_path)
    pinned = _a1_letter_prompt_size()
    staged_manifest = learner_state.CURRICULUM_ROOT / "curriculum.yaml"

    sizes: dict[str, int] = {}
    for mode, root in roots.items():
        monkeypatch.setattr(learner_state, "CURRICULUM_ROOT", root)
        _pin_a1_letter_prompt_inputs(monkeypatch, tmp_path)
        pinned_root = tmp_path / "curriculum" / "l2-uk-en"
        assert pinned_root == learner_state.CURRICULUM_ROOT
        assert base_level.__kwdefaults__["manifest"] == staged_manifest
        sizes[mode] = _a1_letter_prompt_size()

    assert sizes["present"] == sizes["absent"] == sizes["modified"] == pinned
    assert pinned <= WRITER_PROMPT_CEILING_BYTES

    # The same modified manifest changes the prompt when learner state is not pinned.
    # Activity-config ``base_level`` stays on the staged manifest so a missing
    # checkout file cannot abort the render before the size comparison.
    monkeypatch.setattr(learner_state, "CURRICULUM_ROOT", roots["modified"])
    assert _a1_letter_prompt_size() != pinned


def test_a1_m20_writer_prompt_stays_under_ceiling() -> None:
    prompt = render_fixture_writer_prompt("a1", "my-morning")

    assert len(prompt.encode("utf-8")) <= WRITER_PROMPT_CEILING_BYTES


def test_c1_sample_writer_prompt_stays_under_ceiling() -> None:
    prompt = _render_c1_sample_prompt()

    assert len(prompt.encode("utf-8")) <= WRITER_PROMPT_CEILING_BYTES
