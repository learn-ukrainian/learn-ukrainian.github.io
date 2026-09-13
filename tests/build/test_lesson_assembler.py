"""Held-out gold artifacts are hash-checked fixtures, never published as lessons."""

from pathlib import Path

import pytest
import yaml

from scripts.build.lesson_assembler import assemble_lessons
from tests.build.upgrade_fixtures import UPGRADED, extract_upgrade_fixtures, fixture_text


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
const source = fs.readFileSync('site/src/pages/[...slug].astro', 'utf8').split('---')[1];
const tree = ts.createSourceFile('route.ts', source, ts.ScriptTarget.Latest, true);
const wanted = new Set(['TRACKS', 'HIDDEN_DOCS', 'normalizeId', 'allDocs', 'visibleDocs',
 'deployedDocsByTrack', 'landingDocsByTrack', 'plannedModuleGroups', 'A1_UNITS']);
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
const helper = fs.readFileSync('site/src/lib/a1-archive-routes.ts', 'utf8').replaceAll('export ', '');
const units = fs.readFileSync('site/src/data/a1-v1-modules.ts', 'utf8').replaceAll('export ', '');
const compiled = ts.transpileModule(helper + '\n' + units + '\n' + selected, {compilerOptions: {target: ts.ScriptTarget.ES2022}}).outputText;
const docs = JSON.parse(fs.readFileSync(0, 'utf8'));
const AsyncFunction = Object.getPrototypeOf(async function(){}).constructor;
new AsyncFunction('getCollection', 'moduleCount', compiled + '\nreturn {routes: await getStaticPaths(), groups: plannedModuleGroups("a1", TRACKS["a1"]), visible: [...deployedDocsByTrack.keys()]};')(
 async name => name === 'docs' ? docs : [], () => 0
).then(result => process.stdout.write(JSON.stringify(result))).catch(error => {console.error(error); process.exitCode = 1;});
'''
    module, plan = gold
    pages = assemble_lessons(module, tmp_path / "site", plan)
    docs = [{"id": "a1-v1/things-have-gender", "data": {"title": "Original", "sidebar": {"order": 7}}}]
    docs.extend({"id": f"a1/things-have-gender/{name}", "data": yaml.safe_load(mdx.split("---", 2)[1])}
                for name, mdx in pages.items())
    docs.append({"id": "a1/draft/index", "data": {"title": "Draft", "draft": True, "lessons": []}})
    result = json.loads(subprocess.check_output(["node", "-e", probe], input=json.dumps(docs), text=True, timeout=30))
    routes = {route["params"]["slug"] for route in result["routes"]}
    assert {
        "a1-v1", "a1-v1/things-have-gender", "a1", "a1/things-have-gender",
        "a1/things-have-gender/1", "a1/things-have-gender/2", "a1/things-have-gender/3",
    } <= routes
    assert "a1/draft" not in routes
    assert "a1" in result["visible"]
    assert result["groups"][0]["unit"].startswith("A1.1")
    upgraded = next(
        item for group in result["groups"] for item in group["items"]
        if item["slug"] == "things-have-gender"
    )
    assert [item["n"] for item in upgraded["lessons"]] == [1, 2, 3]


def test_a1_landing_follows_original_bilingual_intro(gold, tmp_path):
    """A1 landing: original English-carrier intro + UK terms, never an English-only Objectives dump."""
    module, plan = gold
    original = tmp_path / "curriculum/l2-uk-en/a1-v1/things-have-gender/module.md"
    original.parent.mkdir(parents=True, exist_ok=True)
    original.write_text(fixture_text("baseline", "curriculum/l2-uk-en/a1-v1/things-have-gender/module.md"))
    pages = assemble_lessons(module, tmp_path / "site", plan)
    lesson_tab = pages["index"].split('<TabItem label="Урок — Lesson">', 1)[1].split("</TabItem>", 1)[0]
    assert "## Objectives" not in lesson_tab
    assert "## Уроки — Lessons" in lesson_tab
    # English carrier with embedded Ukrainian target terms.
    assert "By the end, you can" in lesson_tab
    assert "він" in lesson_tab
    assert "вона" in lesson_tab


def test_a1_landing_without_original_is_lesson_list_only(gold, tmp_path):
    """No original summary and no writer overview → cards only, never plan YAML."""
    module, plan = gold
    pages = assemble_lessons(module, tmp_path / "site", plan)
    lesson_tab = pages["index"].split('<TabItem label="Урок — Lesson">', 1)[1].split("</TabItem>", 1)[0]
    assert "## Objectives" not in lesson_tab
    assert "## Цілі — Objectives" not in lesson_tab
    assert "## Уроки — Lessons" in lesson_tab


def test_a1_landing_prefers_writer_overview(gold, tmp_path):
    module, plan = gold
    (module / "landing-overview.md").write_text(
        "You already know **він**. Now describe things.\n\n"
        "By the end, you can:\n\n- ask **який?** with a noun.\n\n"
        "Keep the scope small. Today is not a full declension lesson.\n"
    )
    pages = assemble_lessons(module, tmp_path / "site", plan)
    lesson_tab = pages["index"].split('<TabItem label="Урок — Lesson">', 1)[1].split("</TabItem>", 1)[0]
    assert "You already know **він**" in lesson_tab
    assert "By the end, you can" in lesson_tab
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
