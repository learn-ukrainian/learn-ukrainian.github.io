"""Held-out gold artifacts are hash-checked fixtures, never published as lessons."""

from pathlib import Path

import pytest
import yaml

from scripts.build.lesson_assembler import assemble_lessons
from tests.build.upgrade_fixtures import UPGRADED, extract_upgrade_fixtures, fixture_text

pytestmark = pytest.mark.reads_content


@pytest.fixture
def gold(tmp_path, monkeypatch):
    from scripts.generate_mdx import atlas_links

    atlas = tmp_path / "atlas.json"
    atlas.write_text('{"entries": []}')
    monkeypatch.setattr(atlas_links, "_DEFAULT_MANIFEST", atlas)
    extract_upgrade_fixtures(tmp_path)
    module = tmp_path / UPGRADED
    plan = tmp_path / "plan.yaml"
    plan.write_text(fixture_text("baseline", "curriculum/l2-uk-en/plans/a1/things-have-gender.yaml"))
    return module, plan


def test_gold_assembler(gold, tmp_path):
    module, plan = gold
    output = tmp_path / "site"
    pages = assemble_lessons(module, output, plan)
    assert set(pages) == {"index", "1", "2", "3"}
    assert sorted(path.name for path in output.iterdir()) == ["1.mdx", "2.mdx", "3.mdx", "index.mdx"]
    for n in range(1, 4):
        mdx = pages[str(n)]
        assert yaml.safe_load(mdx.split("---", 2)[1])["draft"] is False
        assert mdx.count("<TabItem ") == 4
        assert 'aria-label="Lesson navigation"' in mdx
        assert f"/a1/things-have-gender/{n}/" in pages["index"]
    assert "<DialogueBox\n" in pages["1"]
    assert "<OddOneOut " in "".join(pages.values())
    manifest = yaml.safe_load(pages["index"].split("---", 2)[1])
    assert manifest["draft"] is False
    assert [item["n"] for item in manifest["lessons"]] == [1, 2, 3]
    # Earlier first-use vocabulary remains available in every subsequent lesson.
    vocab = yaml.safe_load((module / "lesson-1/vocabulary.yaml").read_text())
    for row in vocab:
        assert row["lemma"] in pages["3"]
        assert row["lemma"] in pages["index"]


def test_invalid_numbering_fails_before_writing(gold, tmp_path):
    module, plan = gold
    path = module / "lessons.yaml"
    manifest = yaml.safe_load(path.read_text())
    manifest["lessons"][1]["n"] = 4
    path.write_text(yaml.safe_dump(manifest))
    with pytest.raises(ValueError, match="contiguous"):
        assemble_lessons(module, tmp_path / "output", plan)
    assert not (tmp_path / "output").exists()


def test_gold_activity_payloads_and_render(gold, tmp_path):
    from scripts.build.mdx_render_gate import check_mdx_render

    module, plan = gold
    pages = assemble_lessons(module, tmp_path / "site", plan)
    components = {
        "quiz": "Quiz", "fill-in": "FillIn", "match-up": "MatchUp",
        "group-sort": "GroupSort", "true-false": "TrueFalse", "unjumble": "Unjumble",
        "translate": "Translate", "observe": "Observe", "odd-one-out": "OddOneOut",
        "error-correction": "ErrorCorrection",
    }
    for n in range(1, 4):
        activities = yaml.safe_load((module / f"lesson-{n}/activities.yaml").read_text())
        mdx = pages[str(n)]
        assert check_mdx_render(mdx)["passed"] is True
        for placement in ("inline", "workbook"):
            for activity in activities[placement]:
                assert f'<{components[activity["type"]]} ' in mdx
                if activity["type"] == "unjumble":
                    for item in activity["words"]:
                        assert item["answer"] in mdx
                if activity["type"] == "odd-one-out":
                    for item in activity["items"]:
                        for choice in item.get("words", item.get("options", [])):
                            assert choice in mdx
                if activity["type"] == "error-correction":
                    for item in activity["items"]:
                        assert item["correction"] in mdx.replace("\\'", "'")
                if activity["type"] == "fill-in":
                    for item in activity["items"]:
                        if item.get("explanation"):
                            assert item["explanation"] in mdx
        for anchor in ("vocabulary", "activities", "resources"):
            assert f'<span id="{anchor}">' in mdx


def test_canonical_site_routes_and_frontmatter_groups(gold, tmp_path):
    """Execute the actual Astro route function and group builder with content entries."""
    import json
    import subprocess

    probe = r'''
const fs = require('fs');
const ts = require('typescript');
const demodule = (src) => src
  .replace(/^\s*import\s[\s\S]*?;\s*$/gm, '')
  .replaceAll('export ', '');
const source = fs.readFileSync('site/src/pages/[...slug].astro', 'utf8').split('---')[1];
const tree = ts.createSourceFile('route.ts', source, ts.ScriptTarget.Latest, true);
const wanted = new Set(['TRACKS', 'HIDDEN_DOCS', 'normalizeId', 'allDocs', 'visibleDocs',
 'deployedDocsByTrack', 'landingDocsByTrack', 'HIDDEN_LINK_TRACKS', 'hrefFromRoute', 'sidebar']);
const selected = tree.statements.filter(statement => {
 if (ts.isFunctionDeclaration(statement)) return statement.name?.text === 'getStaticPaths';
 if (ts.isVariableStatement(statement)) {
   return statement.declarationList.declarations.some(declaration => wanted.has(declaration.name.getText(tree)));
 }
 if (ts.isForOfStatement(statement)) {
   return statement.expression.getText(tree) === 'visibleDocs'
       || statement.expression.getText(tree) === 'deployedDocsByTrack.values()';
 }
 return false;
}).map(statement => statement.getText(tree)).join('\n').replace('export async function', 'async function').replaceAll('import.meta.env.PROD', 'true');
const helper = demodule(fs.readFileSync('site/src/lib/a1-archive-routes.ts', 'utf8'));
const nav = demodule(fs.readFileSync('site/src/lib/doc-nav.ts', 'utf8'));
const compiled = ts.transpileModule(helper + '\n' + nav + '\n' + selected, {
  compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.CommonJS },
}).outputText.replace(/^\s*exports?\.[^\n]*\n/gm, '').replace(/^\s*export\s*\{\s*\}\s*;?\s*$/gm, '');
const docs = JSON.parse(fs.readFileSync(0, 'utf8'));
const AsyncFunction = Object.getPrototypeOf(async function(){}).constructor;
// `sidebar` reads the page-level `props`/`docRoute`/`docTrack`; bind them to one lesson page.
const lessonId = 'a1/things-have-gender/2';
const prelude = `const props = {kind: 'doc', entry: allDocs.find(e => normalizeId(e.id) === '${lessonId}')};
const docRoute = '${lessonId}'; const docTrack = 'a1';`;
const body = compiled.replace(/^const sidebar\b/m, prelude + '\nconst sidebar');
new AsyncFunction('getCollection', 'moduleCount', 'formatLessonCount', body + '\nreturn {routes: (await getStaticPaths()).map(r => ({params: r.params, kind: r.props.kind})), sidebar, visible: [...deployedDocsByTrack.keys()]};')(
 async name => name === 'docs' ? docs : [], () => 0, count => ({en: `${count} lessons`, uk: `${count} уроки`})
).then(result => process.stdout.write(JSON.stringify(result))).catch(error => {console.error(error); process.exitCode = 1;});
'''
    module, plan = gold
    pages = assemble_lessons(module, tmp_path / "site", plan)
    docs = [{"id": "a1-v1/things-have-gender", "data": {"title": "Original", "sidebar": {"order": 7}}}]
    docs.extend({"id": f"a1/things-have-gender/{name}", "data": yaml.safe_load(mdx.split("---", 2)[1])}
                for name, mdx in pages.items())
    docs.append({"id": "a1/draft/index", "data": {"title": "Draft", "draft": True, "lessons": []}})
    # The generated arc landing (`arc_kind: landing`) is the track's landing doc.
    docs.append({"id": "a1", "data": {"title": "A1", "arc_kind": "landing", "arc_level": "a1"}})
    result = json.loads(subprocess.check_output(["node", "-e", probe], input=json.dumps(docs), text=True, timeout=30))
    kinds = {route["params"]["slug"]: route["kind"] for route in result["routes"]}
    assert {
        "a1-v1", "a1-v1/things-have-gender", "a1", "a1/things-have-gender",
        "a1/things-have-gender/1", "a1/things-have-gender/2", "a1/things-have-gender/3",
    } <= kinds.keys()
    assert kinds["a1"] == "landingDoc"
    assert kinds["a1/things-have-gender"] == kinds["a1/things-have-gender/2"] == "doc"
    assert "a1/draft" not in kinds
    assert "a1" in result["visible"]
    sidebar = result["sidebar"]
    assert sidebar["backHref"] == "/a1/"
    assert [link["num"] for link in sidebar["links"]] == ["01", "02", "03"]
    assert [link["active"] for link in sidebar["links"]] == [False, True, False]
    assert [link["href"] for link in sidebar["links"]] == [
        f"/a1/things-have-gender/{n}/" for n in (1, 2, 3)
    ]
    assert (sidebar["progressDone"], sidebar["progressTotal"]) == (2, 3)


def test_a1_landing_uses_lesson_map_pitch_not_original_body(gold, tmp_path):
    """A1 landing: title + lesson-map pitch + cards; never L1/archive academic prose."""
    module, plan = gold
    original = tmp_path / "curriculum/l2-uk-en/a1-v1/things-have-gender/module.md"
    original.parent.mkdir(parents=True, exist_ok=True)
    original.write_text(fixture_text("baseline", "curriculum/l2-uk-en/a1-v1/things-have-gender/module.md"))
    (module / "landing-overview.md").write_text(
        "Teacher Oksana's routine for this module is short.\n\n"
        "By the end, you can:\n\n- ask **який?** with a noun.\n\n"
        "Keep the scope small.\n",
        encoding="utf-8",
    )
    pages = assemble_lessons(module, tmp_path / "site", plan)
    lesson_tab = pages["index"].split('<TabItem label="Урок — Lesson">', 1)[1].split("</TabItem>", 1)[0]
    plan_data = yaml.safe_load(plan.read_text(encoding="utf-8"))
    lessons = yaml.safe_load((module / "lessons.yaml").read_text(encoding="utf-8"))["lessons"]
    assert "## Objectives" not in lesson_tab
    assert "## Уроки — Lessons" in lesson_tab
    assert f"**{plan_data['title']}**" in lesson_tab
    assert f"This module has **{len(lessons)}** lessons" in lesson_tab
    for lesson in lessons:
        assert lesson["title"] in lesson_tab
    assert "By the end, you can" in lesson_tab
    assert "ask **який?** with a noun" in lesson_tab
    assert "Teacher Oksana" not in lesson_tab
    assert "English has \"he,\"" not in lesson_tab


def test_a1_landing_without_outcomes_still_has_lesson_map_pitch(gold, tmp_path):
    """No outcomes file and no L1 \"By the end\" → pitch + cards, never plan YAML dump."""
    module, plan = gold
    pages = assemble_lessons(module, tmp_path / "site", plan)
    lesson_tab = pages["index"].split('<TabItem label="Урок — Lesson">', 1)[1].split("</TabItem>", 1)[0]
    plan_data = yaml.safe_load(plan.read_text(encoding="utf-8"))
    assert "## Objectives" not in lesson_tab
    assert "## Цілі — Objectives" not in lesson_tab
    assert "## Уроки — Lessons" in lesson_tab
    assert f"**{plan_data['title']}**" in lesson_tab
    assert "This module has **3** lessons" in lesson_tab


def test_a1_landing_outcomes_only_from_writer_overview(gold, tmp_path):
    module, plan = gold
    (module / "landing-overview.md").write_text(
        "You already know **він**. Now describe things.\n\n"
        "By the end, you can:\n\n- ask **який?** with a noun.\n\n"
        "Keep the scope small. Today is not a full declension lesson.\n"
    )
    pages = assemble_lessons(module, tmp_path / "site", plan)
    lesson_tab = pages["index"].split('<TabItem label="Урок — Lesson">', 1)[1].split("</TabItem>", 1)[0]
    assert "You already know **він**" not in lesson_tab
    assert "Keep the scope small" not in lesson_tab
    assert "By the end, you can" in lesson_tab
    assert "ask **який?** with a noun" in lesson_tab
    assert "## Уроки — Lessons" in lesson_tab


def test_extract_outcomes_keeps_wrapped_by_the_end_bullets():
    """Indented wrap lines after a bullet stay in the outcomes block."""
    from scripts.build.lesson_assembler import _extract_outcomes_block

    text = (
        "Teacher Oksana's routine is short.\n\n"
        "By the end, you can:\n\n"
        "- recognize **ь** and apostrophe in common A1 words;\n"
        "- read **день**, **кінь**, **сіль**, and **вчи́тель** without adding an extra\n"
        "  vowel;\n"
        "- read **сім'я́** with **й** after the apostrophe;\n"
        "- sort words into **м'яки́й знак** and **апо́строф**;\n"
        "- choose the safer form when a visual habit creates a mistake.\n\n"
        "Keep the scope small.\n"
    )
    block = _extract_outcomes_block(text)
    assert block is not None
    assert "without adding an extra\n  vowel;" in block
    assert "read **сім'я́** with **й** after the apostrophe;" in block
    assert "sort words into **м'яки́й знак** and **апо́строф**;" in block
    assert "choose the safer form when a visual habit creates a mistake." in block
    assert "Teacher Oksana" not in block
    assert "Keep the scope small" not in block


def test_a1_landing_five_lessons_from_map_excludes_teacher_oksana(tmp_path, monkeypatch):
    """Generated landing lists all five lesson titles + By the end; never Teacher Oksana."""
    from scripts.generate_mdx import atlas_links

    atlas = tmp_path / "atlas.json"
    atlas.write_text('{"entries": []}')
    monkeypatch.setattr(atlas_links, "_DEFAULT_MANIFEST", atlas)

    module = tmp_path / "curriculum/l2-uk-en/a1/special-signs"
    titles = [
        "М'яки́й знак (Ь) та африка́ти · Soft Sign (Ь) and Affricates",
        "Йото́вані лі́тери · Iotated Vowels",
        "За́вжди два зву́ки · Always Two Sounds",
        "Апо́строф і три контра́сти · The Apostrophe and Three Contrasts",
        "Си́нтез особли́вих зна́ків · Special Signs Synthesis",
    ]
    lessons = [{"n": n, "title": title, "minutes": 60} for n, title in enumerate(titles, start=1)]
    module.mkdir(parents=True)
    (module / "lessons.yaml").write_text(
        yaml.safe_dump({"lessons": lessons}, allow_unicode=True), encoding="utf-8",
    )
    for lesson in lessons:
        lesson_dir = module / f"lesson-{lesson['n']}"
        lesson_dir.mkdir()
        (lesson_dir / "vocabulary.yaml").write_text("vocabulary: []\n", encoding="utf-8")
        (lesson_dir / "resources.yaml").write_text("resources: []\n", encoding="utf-8")
        (lesson_dir / "activities.yaml").write_text(
            "inline: []\nworkbook: []\n", encoding="utf-8",
        )
        body = f"# {lesson['title']}\n\nLesson body.\n\n## Section\n\nText.\n"
        if lesson["n"] == 1:
            body = (
                "# Soft Sign\n\n"
                "Teacher Oksana's routine for this module is short: find the sign.\n\n"
                "By the end, you can:\n\n"
                "- recognize **ь** and apostrophe in common A1 words;\n"
                "- read **день** without adding an extra vowel.\n\n"
                "## Section\n\nBody.\n"
            )
        (lesson_dir / "module.md").write_text(body, encoding="utf-8")

    plan = tmp_path / "plan.yaml"
    plan.write_text(
        "level: A1\nslug: special-signs\nsequence: 3\n"
        "title: Особливі знаки\n"
        "subtitle: Ь, апостроф і три ключові контрасти\n",
        encoding="utf-8",
    )
    pages = assemble_lessons(module, tmp_path / "site", plan)
    lesson_tab = pages["index"].split('<TabItem label="Урок — Lesson">', 1)[1].split("</TabItem>", 1)[0]
    assert "This module has **5** lessons" in lesson_tab
    assert "**Особливі знаки**" in lesson_tab
    for title in titles:
        assert title in lesson_tab
    assert "By the end, you can" in lesson_tab
    assert "recognize **ь** and apostrophe" in lesson_tab
    assert "Teacher Oksana" not in lesson_tab
    assert "## Уроки — Lessons" in lesson_tab


def test_a1_opening_hygiene_four_shapes():
    from scripts.build.lesson_assembler import _clean_a1_landing_prose

    root = Path("curriculum/l2-uk-en/a1-v1")
    if not root.exists():
        pytest.skip("a1-v1 archive not in this checkout")

    def opening(slug: str) -> str:
        text = (root / slug / "module.md").read_text(encoding="utf-8")
        return text.split("## ", 1)[0]

    nine = _clean_a1_landing_prose(opening("what-is-it-like"))
    assert nine is not None
    assert "By the end, you can" in nine
    assert ":::" not in nine

    eight = _clean_a1_landing_prose(opening("things-have-gender"))
    assert eight is not None
    assert "By the end, you can" in eight
    assert ":::" not in eight
    assert "Treat gender as part of the noun card" not in eight

    morning = _clean_a1_landing_prose(opening("my-morning"))
    assert morning is not None
    assert "By the end" not in morning
    assert "прокидаюся" in morning

    questions = _clean_a1_landing_prose(opening("questions"))
    assert questions is not None
    assert "Хто ти?" not in questions
    assert "|" not in questions
    assert "The safest A1 pattern is" not in questions
    assert "Questions turn the verbs" in questions


def test_a1_landing_prose_rejects_previous_edition_banned_text(tmp_path):
    from scripts.build.lesson_assembler import (
        _clean_a1_landing_prose,
        _original_intro,
        _writer_landing_overview,
    )

    banned = (
        "# Special Signs\n\nThis module completes your mastery of all 33 le\u0301tters "
        "and gives you the soft sign and the apostrophe in real words.\n"
    )
    line_breaks = (
        "# Special Signs\n\nYou read the soft sign and the apostrophe in real words, "
        "then learn word hyphenation rules for dividing a word across lines.\n"
    )
    clean = "# Special Signs\n\nYou read the soft sign and the apostrophe in real Ukrainian words.\n"
    assert _clean_a1_landing_prose(banned) is None
    assert _clean_a1_landing_prose(line_breaks) is None
    assert _clean_a1_landing_prose(clean) == clean.split("\n\n", 1)[1].strip()

    # Neither source may republish it: not the writer overview, not the a1-v1 opening.
    module_dir = tmp_path / "curriculum/l2-uk-en/a1/special-signs"
    archive = tmp_path / "curriculum/l2-uk-en/a1-v1/special-signs"
    module_dir.mkdir(parents=True)
    archive.mkdir(parents=True)
    (module_dir / "landing-overview.md").write_text(banned, encoding="utf-8")
    (archive / "module.md").write_text(line_breaks + "\n## Section\n\nBody.\n", encoding="utf-8")
    assert _writer_landing_overview(module_dir) is None
    assert _original_intro(module_dir, "special-signs") is None


@pytest.mark.parametrize(
    "sentence",
    [
        "This module completes your **mastery** of all 33 letters and introduces the soft sign.",
        "This module completes your mastery of all 33 letters and introduces the soft sign.",
        "This module completes your _mastery_ of `all 33` le\u0301tters and introduces the soft sign.",
        "This module completes your mas**tery** of all 33 letters and introduces the soft sign.",
        "You read the soft sign in real words, then learn **word** *hyphenation* rules for line ends.",
    ],
)
def test_a1_landing_prose_rejects_banned_text_split_by_inline_markdown(tmp_path, sentence):
    from scripts.build.lesson_assembler import _clean_a1_landing_prose, _original_intro

    assert _clean_a1_landing_prose(f"# Special Signs\n\n{sentence}\n") is None

    # The a1-v1 fallback must not republish it either, from module.md or the published mdx.
    module_dir = tmp_path / "curriculum/l2-uk-en/a1/special-signs"
    archive = tmp_path / "curriculum/l2-uk-en/a1-v1/special-signs"
    module_dir.mkdir(parents=True)
    archive.mkdir(parents=True)
    (archive / "module.md").write_text(
        f"# Special Signs\n\n{sentence}\n\n## Section\n\nBody.\n", encoding="utf-8"
    )
    assert _original_intro(module_dir, "special-signs") is None

    (archive / "module.md").unlink()
    published = tmp_path / "site/src/content/docs/a1-v1/special-signs.mdx"
    published.parent.mkdir(parents=True)
    published.write_text(
        f'<Tabs>\n<TabItem label="Lesson">\n\n{sentence}\n\n## Section\n\nBody.\n</TabItem>\n</Tabs>\n',
        encoding="utf-8",
    )
    assert _original_intro(module_dir, "special-signs") is None


def test_a1_landing_prose_keeps_clean_formatted_text():
    from scripts.build.lesson_assembler import _clean_a1_landing_prose

    clean = "You read the **soft sign** and the _apostrophe_ in real Ukrainian words."
    assert _clean_a1_landing_prose(f"# Special Signs\n\n{clean}\n") == clean


def test_a1_assembler_converts_text_fences_to_bilingual_bullets():
    from scripts.build.lesson_assembler import _normalize_a1_example_fences

    raw = (
        "Then make three tiny room lines.\n\n"
        "```text\n"
        "Це моя́ кімна́та.\n"
        "У мене́ є стіл.\n"
        "```\n\n"
        "| Украї́нська | English support |\n"
        "| --- | --- |\n"
        "| **Це моя́ кімна́та.** | This is my room. |\n"
        "| **У мене́ є стіл.** | I have a table. |\n"
    )
    out = _normalize_a1_example_fences(raw)
    assert "```" not in out
    assert "- **Це моя́ кімна́та.** — This is my room." in out
    assert "- **У мене́ є стіл.** — I have a table." in out


def test_a1_assembler_keeps_prose_after_text_fence():
    from scripts.build.lesson_assembler import _normalize_a1_example_fences

    raw = (
        "Then make three tiny room lines.\n\n"
        "```text\n"
        "книга\n"
        "```\n\n"
        "This explanation is needed.\n\n"
        "After\n"
    )
    out = _normalize_a1_example_fences(raw)
    assert "```" not in out
    assert "- **книга**" in out
    assert "This explanation is needed." in out
    assert "After" in out


def test_a1_assembler_pairs_fence_with_following_support_table():
    from scripts.build.lesson_assembler import _normalize_a1_example_fences

    raw = (
        "```text\n"
        "Марія: Це моя кімната.\n"
        "```\n\n"
        "Support after the Ukrainian lines:\n\n"
        "| Украї́нська | English support |\n"
        "| --- | --- |\n"
        "| **Марі́я: Це моя́ кімна́та.** | Mariia: This is my room. |\n"
    )
    out = _normalize_a1_example_fences(raw)
    assert "```" not in out
    assert "Support after the Ukrainian lines:" not in out
    assert "- **Марі́я: Це моя́ кімна́та.** — Mariia: This is my room." in out


def test_a1_assembler_keeps_prose_between_fence_and_table():
    from scripts.build.lesson_assembler import _normalize_a1_example_fences

    raw = (
        "```text\n"
        "книга\n"
        "```\n\n"
        "This explanation is needed.\n\n"
        "| Украї́нська | English support |\n"
        "| --- | --- |\n"
        "| книга | book |\n"
    )
    out = _normalize_a1_example_fences(raw)
    assert "```" not in out
    assert "This explanation is needed." in out
    assert "| книга | book |" in out


def test_a1_assembler_rewrites_module_completion_to_summary():
    from scripts.build.lesson_assembler import _normalize_a1_module_close

    raw = (
        "Workbook practice will make the pattern automatic.\n\n"
        "### Заве́ршення мо́дуля — Module completion\n\n"
        "| Украї́нська | English support |\n"
        "| --- | --- |\n"
        "| **Віта́ємо!** | Congratulations! |\n"
        "| **Тепе́р ви зна́єте рід.** | Now you know gender. |\n"
    )
    out = _normalize_a1_module_close(raw)
    assert "Module completion" not in out
    assert "### Підсумок модуля — Module summary" in out
    assert "- **Віта́ємо!** — Congratulations!" in out
    assert "- **Тепе́р ви зна́єте рід.** — Now you know gender." in out


def test_custom_artifact_directory_keeps_plan_slug(gold, tmp_path):
    import shutil

    module, plan = gold
    custom = tmp_path / "custom-writer-output"
    shutil.copytree(module, custom)
    pages = assemble_lessons(custom, tmp_path / "custom-site-output", plan)
    assert "/a1/things-have-gender/1/" in pages["index"]
    assert "/a1/things-have-gender/2/" in pages["1"]
    assert "/a1/custom-writer-output/" not in "".join(pages.values())


def test_alphabet_mdx_error_correction_matches_gate_chips(monkeypatch):
    """Gate and activity_renderer share error_correction_render_values repair."""
    import json
    import re

    from scripts.build import lesson_gates as gates
    from scripts.build.activity_renderer import render_activity_to_jsx

    item = {
        "sentence": "Вра́нці я пив чаі з лимо́ном.",
        "error": "чаі",
        "correction": "чай",
        "options": ["чай", "чаї́", "чаю"],
        "explanation": "Write й, not і.",
    }
    monkeypatch.setattr(
        "scripts.build.alphabet_modules.vesum_is_word",
        lambda w: gates.strip_acute(gates.nfc(w)).lower() in {"чаю", "чаї"},
    )
    act = {"type": "error-correction", "items": [item], "instruction": "Fix"}
    jsx = render_activity_to_jsx(act, alphabet=True)
    match = re.search(r"items=\{(\[.*\])\}", jsx, flags=re.S)
    assert match, jsx
    rendered = json.loads(match.group(1))[0]["options"]
    _, _, gate_chips = gates._ec_rendered_chips(item, alphabet=True)
    assert rendered == gate_chips
    assert gates.error_correction_item_defects(item, level="a1", alphabet=True) == []


def test_alphabet_assemble_persists_ec_repair_into_activities_yaml(tmp_path, monkeypatch):
    """Assemble writes repaired chips to activities.yaml so gates read YAML."""
    from scripts.build import lesson_gates as gates
    from scripts.build.alphabet_modules import _chip_key

    monkeypatch.setattr("scripts.build.alphabet_modules.vesum_is_word", lambda _w: False)

    module = tmp_path / "module"
    lesson = module / "lesson-1"
    lesson.mkdir(parents=True)
    (module / "lessons.yaml").write_text(
        yaml.safe_dump({"lessons": [{"n": 1, "title": "Знаки", "minutes": 60, "sections": ["s1"], "word_target": 600}]}),
        encoding="utf-8",
    )
    plan = tmp_path / "plan.yaml"
    plan.write_text(
        yaml.safe_dump({"slug": "special-signs", "level": "a1", "sequence": 3, "title": "Special signs"}),
        encoding="utf-8",
    )
    (lesson / "module.md").write_text("# Знаки\n\nBy the end, you can read soft signs.\n\n", encoding="utf-8")
    (lesson / "vocabulary.yaml").write_text("[]\n", encoding="utf-8")
    (lesson / "resources.yaml").write_text("[]\n", encoding="utf-8")
    cloned = {
        "inline": [
            {
                "id": "act-1",
                "type": "error-correction",
                "instruction": "Fix the spelling.",
                "items": [
                    {
                        "sentence": "Це ло́шка.",
                        "error": "ло́шка",
                        "correction": "ло́жка",
                        "options": ["ло́жка", "ло́жка", "ло́жка"],
                        "explanation": "Write ж, not ш.",
                    }
                ],
            }
        ],
        "workbook": [
            {
                "id": "act-w1",
                "type": "error-correction",
                "instruction": "Fix.",
                "items": [
                    {
                        "sentence": "Моя́ сімя́.",
                        "error": "сімя́",
                        "correction": "сім'я́",
                        "options": ["сім'я́", "сім'я́"],
                        "explanation": "Apostrophe.",
                    }
                ],
            }
        ],
    }
    acts_path = lesson / "activities.yaml"
    acts_path.write_text(yaml.safe_dump(cloned, allow_unicode=True, sort_keys=False), encoding="utf-8")

    pages = assemble_lessons(module, tmp_path / "site", plan, validated=False)
    disk = yaml.safe_load(acts_path.read_text(encoding="utf-8"))
    for placement in ("inline", "workbook"):
        opts = disk[placement][0]["items"][0]["options"]
        assert len(opts) == len({_chip_key(c) for c in opts})
        assert len(opts) >= 2
        assert gates.contradictions({"items": disk[placement][0]["items"]}, disk[placement][0]["id"]) == []
    assert "ло́жка" in pages["1"]
    assert "сім'я́" in pages["index"] or "сім\\'я́" in pages["index"]
