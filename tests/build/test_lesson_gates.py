"""Held-out Phase 0 fixture and adversarial preservation tests (no writer)."""

import pytest
import yaml

from scripts.build import lesson_gates as gates
from tests.build.upgrade_fixtures import fixture_text


@pytest.fixture
def gold(tmp_path, monkeypatch):
    from scripts.generate_mdx import atlas_links

    atlas = tmp_path / "atlas.json"
    atlas.write_text('{"entries": []}')
    monkeypatch.setattr(atlas_links, "_DEFAULT_MANIFEST", atlas)
    # Content fixture tests deliberately run without the optional local oracle.
    # Production must reject unavailable correctness evidence, which these tests assert.
    def unavailable(*args):
        raise RuntimeError("fixture has no stress oracle")
    monkeypatch.setattr(gates, "wrong_stress", unavailable)
    source = tmp_path / "a1-v1"
    module = tmp_path / "a1"
    source.mkdir()
    module.mkdir()
    root = "curriculum/l2-uk-en"
    for name in ("module.md", "activities.yaml", "vocabulary.yaml", "resources.yaml"):
        (source / name).write_text(fixture_text("baseline", f"{root}/a1-v1/things-have-gender/{name}"))
        for n in (1, 2, 3):
            d = module / f"lesson-{n}"
            d.mkdir(exist_ok=True)
            (d / name).write_text(fixture_text("gold", f"{root}/a1/things-have-gender/lesson-{n}/{name}"))
    (module / "lessons.yaml").write_text(fixture_text("gold", f"{root}/a1/things-have-gender/lessons.yaml"))
    plan = yaml.safe_load(fixture_text("baseline", f"{root}/plans/a1/things-have-gender.yaml"))
    return module, source, plan


def test_fill_in_blanked_strings_count_as_rendered():
    assert gates._visible_in_render("Київ — {столиця}.", gates.norm_text("Київ — ___."))
    assert gates._visible_in_render("лі́теру [Я]", gates.norm_text("лі́теру ___"))
    assert not gates._visible_in_render("missing sentence here", "other page")
    landing = gates.norm_text('{"instruction":"Example ___."}')
    assert gates._visible_in_render("Example {answer}.", landing)
    assert gates._visible_in_render("де__ (soft sign)", gates.norm_text("де___ (soft sign)"))


def test_dialogue_props_ignore_unrelated_prose():
    page = (
        'Тарас Сьогодні свято '
        '<DialogueBox exchanges={JSON.parse(\'[{"speaker":"Оксана","text":"Привіт"}]\')} />'
    )
    hay = gates._dialogue_props_text(page)
    assert "Привіт" in hay
    assert "Оксана" in hay
    assert "Тарас" not in hay
    assert "свято" not in hay


def test_one_syllable_acute_is_not_undeclared_stress():
    assert gates.wrong_stress("ка́ ли́ ко́", set()) == []


def test_structural_containment_keeps_answers_and_multiplicity():
    assert gates.contains({"items": ["a", "a"]}, {"items": ["a", "a", "b"]})
    assert not gates.contains({"items": ["a", "a"]}, {"items": ["a", "b"]})
    assert not gates.contains(True, 1)


def test_gold_preservation_activity_and_vocabulary_semantics(gold):
    report = gates.run_lesson_gates(*gold)
    # A missing rendered page must fail, but cannot conceal content results.
    assert not report["passed"]
    assert report["facts"]["preservation"] == {
        "long_paragraphs": 47, "lost": 0, "duplicated": 0, "misplaced": 0}
    content = [d for d in report["diagnostics"] if not any(
        label in d for label in ("stress oracle unavailable", "l2_exposure_floor", "render"))]
    assert content == []


def test_removed_original_paragraph_fails(gold):
    module, source, plan = gold
    paragraph = next(p for p in gates.paragraphs(gates.sections((source / "module.md").read_text())["__intro__"])
                     if len(p.split()) >= 8)
    path = module / "lesson-1/module.md"
    text = path.read_text()
    # Stress-normalize both sides solely to locate the verbatim original fixture paragraph.
    text = gates.strip_acute(text).replace(gates.strip_acute(paragraph), "")
    path.write_text(text)
    report = gates.run_lesson_gates(module, source, plan)
    assert report["facts"]["preservation"]["lost"] > 0


def test_list_shaped_baseline_activities_do_not_crash(gold):
    module, source, plan = gold
    data = yaml.safe_load((source / "activities.yaml").read_text())
    combined = list(data.get("inline") or []) + list(data.get("workbook") or [])
    (source / "activities.yaml").write_text(yaml.safe_dump(combined, allow_unicode=True))
    report = gates.run_lesson_gates(module, source, plan)
    assert "passed" in report
    assert not any("has no attribute" in d for d in report["diagnostics"])


def test_homograph_pair_is_not_a_payload_contradiction():
    from scripts.build.lesson_gates import contradictions

    payload = {
        "pairs": [
            {"left": "за́мок", "right": "castle"},
            {"left": "замо́к", "right": "lock"},
        ]
    }
    assert contradictions(payload, "act-w2") == []
    dup = {"items": ["за́мок", "за́мок"]}
    assert any("appears 2x" in c for c in contradictions(dup, "act-3"))
    nfc = {"items": ["й", "и\u0306"]}
    assert any("appears 2x" in c for c in contradictions(nfc, "act-nfc"))


def test_writer_artifact_allows_original_inline_error_correction():
    from scripts.build.linear_pipeline import _validate_lesson_writer_artifact

    _validate_lesson_writer_artifact("activities.yaml", {
        "inline": [{
            "id": "act-4",
            "type": "error-correction",
            "instruction": "Виправте.",
            "items": [{"incorrect": "a", "correct": "b"}] * 4,
        }],
        "workbook": [{
            "id": "act-w1",
            "type": "quiz",
            "instruction": "Оберіть.",
            "questions": [{"question": "q", "choices": ["a"]}],
        }],
    })


def test_original_inline_error_correction_skips_workbook_only_placement(gold):
    module, source, plan = gold
    data = yaml.safe_load((source / "activities.yaml").read_text())
    data["inline"].append({
        "id": "act-err",
        "type": "error-correction",
        "title": "Пастки",
        "items": [{"sentence": "x", "correction": "y"}] * 6,
    })
    (source / "activities.yaml").write_text(yaml.safe_dump(data, allow_unicode=True))
    lesson_acts = yaml.safe_load((module / "lesson-1" / "activities.yaml").read_text())
    lesson_acts["inline"].append({
        "id": "act-err",
        "type": "error-correction",
        "title": "Пастки",
        "items": [{"sentence": "x", "correction": "y"}] * 6,
    })
    (module / "lesson-1" / "activities.yaml").write_text(yaml.safe_dump(lesson_acts, allow_unicode=True))
    md = (module / "lesson-1" / "module.md").read_text()
    (module / "lesson-1" / "module.md").write_text(
        md + "\n<!-- INJECT_ACTIVITY: act-err -->\n"
    )
    report = gates.run_lesson_gates(module, source, plan)
    assert not any("act-err type error-correction is workbook-only" in d for d in report["diagnostics"])


def test_unavailable_stress_oracle_fails_closed(gold, monkeypatch):
    def unavailable(*args):
        raise RuntimeError("unavailable")
    monkeypatch.setattr(gates, "wrong_stress", unavailable)
    report = gates.run_lesson_gates(*gold)
    assert any("stress oracle unavailable" in d for d in report["diagnostics"])


def test_wrong_activity_answer_fails(gold):
    module, source, plan = gold
    path = module / "lesson-1/activities.yaml"
    data = yaml.safe_load(path.read_text())
    original = next(a for a in data["inline"] if a["id"] == "act-1")
    for field in gates.LIST_FIELDS:
        if field in original:
            original[field] = []
    path.write_text(yaml.safe_dump(data, allow_unicode=True))
    report = gates.run_lesson_gates(module, source, plan)
    assert any("act-1: original items/answers/groups not preserved" in d for d in report["diagnostics"])


def test_gold_assembler_coverage_and_explicit_immersion_residual(gold, tmp_path):
    from scripts.build.lesson_assembler import assemble_lessons

    module, source, plan = gold
    plan_path = tmp_path / "plan.yaml"
    plan_path.write_text(yaml.safe_dump(plan, allow_unicode=True))
    pages = assemble_lessons(module, tmp_path / "pages", plan_path)
    report = gates.run_lesson_gates(module, source, plan, pages)
    assert not report["passed"]
    for n, observed in ((1, 5), (2, 0), (3, 0)):
        exposure = report["facts"]["immersion"][n]["l2_exposure_floor"]
        assert exposure["required"]["uk_dialogue_lines"] == 13
        assert exposure["observed"]["uk_dialogue_lines"] == observed
        assert exposure["reason"] == "too_few_uk_dialogue_lines"
    unexpected = [d for d in report["diagnostics"]
                  if "l2_exposure_floor" not in d
                  and "stress oracle unavailable" not in d
                  and "render lacks lesson paragraph" not in d]
    assert unexpected == []


def test_invalid_yaml_fails_closed(gold):
    module, source, plan = gold
    (module / "lesson-1/activities.yaml").write_text("inline: [")
    assert not gates.run_lesson_gates(module, source, plan)["passed"]


def test_stress_correctness_compares_positions_to_oracle(monkeypatch):
    import re

    from scripts.verification import stress

    # The oracle response is controlled test input, not a language assertion.
    md = fixture_text("gold", "curriculum/l2-uk-en/a1/things-have-gender/lesson-1/module.md")
    token = next(t for t in re.findall(rf"[{gates.CYR}{gates.ACUTE}]+", md)
                 if gates.ACUTE in t and len(gates.strip_acute(t)) > 3)
    monkeypatch.setattr(stress, "verify_stress", lambda _: {
        "status": "ok", "matches": [{"stressed_form": token}]})
    assert gates.wrong_stress(token, set()) == []
    bare = gates.strip_acute(token)
    wrong = bare + gates.ACUTE if not token.endswith(gates.ACUTE) else gates.ACUTE + bare
    assert gates.wrong_stress(wrong, set())


def test_writer_prompt_is_not_a_learner_attribution_surface(gold):
    from scripts.build.linear_pipeline import render_upgrade_prompt

    module, source, plan = gold
    lesson_map = yaml.safe_load((module / "lessons.yaml").read_text())
    before = gates.run_lesson_gates(module, source, plan)
    prompt = render_upgrade_prompt(plan, source, lesson_map, lesson=1)
    assert gates.NAME_RE.search(prompt), "real prompt must exercise the attribution regression"
    for name in ("writer_prompt.md", "reviewer_prompt.md", "writer_raw.md"):
        (module / "lesson-1" / name).write_text(prompt)
    after = gates.run_lesson_gates(module, source, plan)
    assert after["diagnostics"] == before["diagnostics"]
    # The same reference remains blocking when it leaks into a learner file.
    learner_path = module / "lesson-1/module.md"
    learner_path.write_text(learner_path.read_text() + "\n\nULP\n")
    assert any("unattributed reference-name" in d
               for d in gates.run_lesson_gates(module, source, plan)["diagnostics"])


def test_configured_word_target_is_enforced(gold):
    module, source, plan = gold
    path = module / "lessons.yaml"
    lesson_map = yaml.safe_load(path.read_text())
    observed = len(gates.strip_comments((module / "lesson-1/module.md").read_text()).split())
    assert observed >= 550
    lesson_map["lessons"][0]["word_target"] = observed + 1
    path.write_text(yaml.safe_dump(lesson_map, allow_unicode=True))
    report = gates.run_lesson_gates(module, source, plan)
    assert f"lesson 1: prose tokens {observed} < {observed + 1} minimum" in report["diagnostics"]
