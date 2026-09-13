"""Held-out gold artifacts are hash-checked fixtures, never published as lessons."""

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
 'deployedDocsByTrack', 'landingDocsByTrack', 'plannedModuleGroups']);
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
const helper = fs.readFileSync('site/src/lib/a1-archive-routes.ts', 'utf8').replace('export function', 'function');
const compiled = ts.transpileModule(helper + '\n' + selected, {compilerOptions: {target: ts.ScriptTarget.ES2022}}).outputText;
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
    modules = result["groups"][0]["items"]
    assert len(modules) == 1
    assert modules[0]["slug"] == "things-have-gender"
    assert [item["n"] for item in modules[0]["lessons"]] == [1, 2, 3]


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


def test_a1_landing_without_original_keeps_bilingual_heading(gold, tmp_path):
    module, plan = gold
    pages = assemble_lessons(module, tmp_path / "site", plan)
    lesson_tab = pages["index"].split('<TabItem label="Урок — Lesson">', 1)[1].split("</TabItem>", 1)[0]
    assert "## Objectives" not in lesson_tab
    assert "## Цілі — Objectives" in lesson_tab
    assert "## Уроки — Lessons" in lesson_tab


def test_custom_artifact_directory_keeps_plan_slug(gold, tmp_path):
    import shutil

    module, plan = gold
    custom = tmp_path / "custom-writer-output"
    shutil.copytree(module, custom)
    pages = assemble_lessons(custom, tmp_path / "custom-site-output", plan)
    assert "/a1/things-have-gender/1/" in pages["index"]
    assert "/a1/things-have-gender/2/" in pages["1"]
    assert "/a1/custom-writer-output/" not in "".join(pages.values())
