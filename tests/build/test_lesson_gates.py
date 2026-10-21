"""Held-out Phase 0 fixture and adversarial preservation tests (no writer)."""

import pytest
import yaml

from scripts.build import lesson_gates as gates
from tests.build.upgrade_fixtures import fixture_text

pytestmark = pytest.mark.reads_content


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


def test_fence_dialogue_counts_as_preserved():
    para = "```text\nМарія: Привіт!\nОленка: Класно!\n```"
    page = (
        '<DialogueBox exchanges={JSON.parse(`[{"speaker":"Марія","text":"Привіт!"},'
        '{"speaker":"Оленка","text":"Класно!"}]`)} />'
    )
    assert gates._fence_preserved_as_dialogue(para, page)
    assert not gates._fence_preserved_as_dialogue(para, "<p>no box</p>")
    swapped = (
        '<DialogueBox exchanges={JSON.parse(`[{"speaker":"Оленка","text":"Привіт!"},'
        '{"speaker":"Марія","text":"Класно!"}]`)} />'
    )
    assert not gates._fence_preserved_as_dialogue(para, swapped)
    reversed_box = (
        '<DialogueBox exchanges={JSON.parse(`[{"speaker":"Оленка","text":"Класно!"},'
        '{"speaker":"Марія","text":"Привіт!"}]`)} />'
    )
    assert not gates._fence_preserved_as_dialogue(para, reversed_box)
    from scripts.generate_mdx.converters import _dialogue_box_mdx
    quoted_page = _dialogue_box_mdx([{"speaker": "Alice", "text": 'Say "hello"!'}], "Dialogue")
    assert gates._fence_preserved_as_dialogue('```text\nAlice: Say "hello"!\n```', quoted_page)
    paren_page = _dialogue_box_mdx([{"speaker": "Alice", "text": "Use ('hello') here."}], "Dialogue")
    assert gates._dialogue_pairs_from_page(paren_page) == [("Alice", "Use ('hello') here.")]
    two = _dialogue_box_mdx(
        [{"speaker": "Марія", "text": "Привіт!"}, {"speaker": "Оленка", "text": "Класно!"}],
        "Dialogue",
    )
    assert not gates._fence_preserved_as_dialogue(para, two + "\n" + two)
    avoid_md = "| Avoid | Use |\n| --- | --- |\n| вкусний суп | **смачни́й суп** |\n"
    blanked = gates._blank_avoid_cells(avoid_md)
    assert "вкусний" not in blanked
    assert "смачни́й" in blanked
    assert "вкусний" in gates.missing_stress("Це вкусний суп.", set())


def test_fill_in_blanked_strings_count_as_rendered():
    assert gates._visible_in_render("Київ — {столиця}.", gates.norm_text("Київ — ___."))
    assert gates._visible_in_render("лі́теру [Я]", gates.norm_text("лі́теру ___"))
    assert not gates._visible_in_render("missing sentence here", "other page")
    landing = gates.norm_text('{"instruction":"Example ___."}')
    assert gates._visible_in_render("Example {answer}.", landing)
    assert gates._visible_in_render("де__ (soft sign)", gates.norm_text("де___ (soft sign)"))
    escaped = gates.unescape_published(
        'pairs={JSON.parse(`[{"right": "Informal \\\\"Hi!\\\\" for friends and family"}]`)}'
    )
    hay = gates.norm_text(escaped)
    assert gates._visible_in_render('Informal "Hi!" for friends and family', hay)
    mashed = "Тарас : Привіт, Оксано! — Hi, Oksana! Оксана : Привіт, Тарасе!"
    assert gates._dialogue_turns(mashed) == [
        ("Тарас", "Привіт, Оксано!"),
        ("Оксана", "Привіт, Тарасе!"),
    ]
    quoted = "> **Окса́на**: До́брий день!\n> **Іва́н**: До́брий день, вчи́телю!"
    assert gates._dialogue_turns(quoted) == [
        ("Оксана", "Добрий день!"),
        ("Іван", "Добрий день, вчителю!"),
    ]
    italic = "> **Тара́с**: Сього́дні свя́то! *(Today is a holiday!)*"
    assert gates._dialogue_turns(italic) == [("Тарас", "Сьогодні свято!")]
    clause = "> **Alice:** Keep this complete first sentence — retain this essential second clause too."
    assert gates._dialogue_turns(clause) == [
        ("Alice", "Keep this complete first sentence — retain this essential second clause too."),
    ]
    hay_full = 'exchanges=[{"speaker":"Alice","text":"Keep this complete first sentence — retain this essential second clause too."}]'
    hay_cut = 'exchanges=[{"speaker":"Alice","text":"Keep this complete first sentence"}]'
    spoken = "Keep this complete first sentence — retain this essential second clause too."
    assert gates._spoken_in_hay(spoken, hay_full)
    assert not gates._spoken_in_hay(spoken, hay_cut)
    hay = 'exchanges=[{"speaker":"Тарас","text":"This sentence is retained."}]'
    assert not gates._spoken_in_hay(
        "This sentence is retained. This other sentence has disappeared completely.",
        hay,
    )
    assert gates._spoken_in_hay("This sentence is retained.", hay)


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
    commented = (
        '<!-- <DialogueBox exchanges={JSON.parse(\'[{"speaker":"Тарас","text":"свято"}]\')} /> -->'
        '<DialogueBox exchanges={JSON.parse(\'[{"speaker":"Оксана","text":"Привіт"}]\')} />'
    )
    hay2 = gates._dialogue_props_text(commented)
    assert "Привіт" in hay2
    assert "Тарас" not in hay2
    assert "свято" not in hay2


def test_one_syllable_acute_is_not_undeclared_stress():
    assert gates.wrong_stress("ка́ ли́ ко́", set()) == []


def test_wrong_stress_option_is_pedagogy_not_an_oracle_failure():
    """нови́й vs но́вий is a real distractor pair; only the wrong option is exempt."""
    acts = {
        "inline": [{"id": "act-stress", "type": "fill-in",
                    "items": [{"sentence": "Це ___ комп'ютер.", "answer": "нови́й",
                               "options": ["нови́й", "но́вий"]}]}],
        "workbook": [],
    }
    errors = gates.pedagogical_error_forms(acts)
    assert any(gates.strip_acute(form) == "новий" and form != "нови́й" for form in errors)
    skip = {gates.nfc(w).lower() for w in errors}
    assert gates.wrong_stress("но́вий", set(), exact_skip=skip) == []
    assert gates.wrong_stress("но́вий", set())  # without skip, the false acute is a miss


def test_error_correction_wrong_spellings_are_not_missing_stress():
    acts = {
        "inline": [],
        "workbook": [{
            "id": "act-err",
            "type": "error-correction",
            "items": [{"sentence": "Не пиши сімя без апо́строфа.", "error": "сімя"}],
        }],
    }
    allow = gates.pedagogical_error_forms(acts)
    assert "сімя" in allow
    assert "сімя" not in gates.missing_stress("Не пиши сімя без апо́строфа.", allow)
    gapped = {
        "inline": [{"id": "act-fill", "type": "fill-in",
                    "items": [{"sentence": "вчител_.", "answer": "ь"}]}],
        "workbook": [],
    }
    allow2 = gates.pedagogical_error_forms(gapped)
    assert "вчител" in allow2
    italic = {
        "inline": [{"id": "act-i", "type": "fill-in",
                    "items": [{"sentence": "_книга_ на столі.", "answer": "книга"}]}],
        "workbook": [],
    }
    assert "книга" not in gates.pedagogical_error_forms(italic)
    quiz = {
        "inline": [],
        "workbook": [{
            "id": "act-q",
            "type": "quiz",
            "items": [{"options": [{"text": "сімя", "correct": False},
                                   {"text": "сім'я́", "correct": True}]}],
        }],
    }
    assert "сімя" in gates.pedagogical_error_forms(quiz)
    fill_opts = {
        "inline": [{"id": "act-fo", "type": "fill-in",
                    "items": [{"sentence": "Це ___.", "answer": "книга",
                               "options": ["книга", "сімя"]}]}],
        "workbook": [],
    }
    forms = gates.pedagogical_error_forms(fill_opts)
    assert "сімя" in forms
    assert "книга" not in forms


def test_error_forms_do_not_exempt_the_same_spelling_in_another_activity():
    """A wrong option in one item must not skip missing-stress on the same token elsewhere."""
    quiz = {
        "id": "act-wrong",
        "type": "quiz",
        "items": [{"options": [{"text": "книга", "correct": False},
                               {"text": "кни́га", "correct": True}]}],
    }
    prose = {
        "id": "act-prose",
        "type": "match",
        "instruction": "Прочитай: книга на столі.",
        "items": [{"left": "книга", "right": "book"}],
    }
    quiz_allow = gates.pedagogical_error_forms({"inline": [quiz], "workbook": []})
    prose_allow = gates.pedagogical_error_forms({"inline": [prose], "workbook": []})
    assert "книга" in quiz_allow
    assert "книга" not in prose_allow
    assert "книга" in gates.missing_stress("книга на столі", prose_allow)
    assert "книга" not in gates.missing_stress("книга на столі", quiz_allow)
    indexed = {
        "inline": [{"id": "act-ix", "type": "quiz",
                    "questions": [{"options": ["книга", "сімя"], "correct": 0}]}],
        "workbook": [],
    }
    allow_ix = gates.pedagogical_error_forms(indexed)
    assert "сімя" in allow_ix
    assert "книга" not in allow_ix
    assert "книга" in gates.missing_stress("книга", allow_ix)


def test_hyphenation_models_are_not_missing_stress():
    text = "Мо́делі: дере-в'яний, Мар'-яна, бур'-ян."
    assert gates.missing_stress(text, set()) == []
    flagged = gates.wrong_stress("дере́-в'яний Мар'-я́на", set())
    assert flagged == []
    assert gates.missing_stress("дере__", set()) == []
    assert "книга" in gates.missing_stress("-книга", set())
    assert "книга" in gates.missing_stress("_книга_", set())
    assert "книга" in gates.missing_stress("__книга__", set())
    assert "книга" in gates.missing_stress("книга_", set())
    assert gates.missing_stress("мален_кий", set()) == []


def test_error_correction_options_gate_rejects_tautology_and_empty():
    empty = gates.error_correction_item_defects(
        {"sentence": "Сього́дні ден. — Today den.", "error": "ден", "correction": "день", "options": []},
        level="a1",
    )
    assert any("empty" in d for d in empty)

    binary = gates.error_correction_item_defects(
        {
            "sentence": "Сього́дні ден. — Today den.",
            "error": "ден",
            "correction": "день",
            "options": ["день", "ден"],
        },
        level="a1",
    )
    assert any("must not contain the spotted error" in d for d in binary)

    # A three-chip set that still carries the error fails too (live defect:
    # `день` / `ден` / `дєнь` after the learner already clicked `ден`).
    three_with_error = gates.error_correction_item_defects(
        {
            "sentence": "Сього́дні га́рний ден. — Today is a nice day (misspelled).",
            "error": "ден",
            "correction": "день",
            "options": ["день", "ден", "дєнь"],
        },
        level="a1",
    )
    assert any("must not contain the spotted error" in d for d in three_with_error)

    # Case differences do not hide the error token.
    cased = gates.error_correction_item_defects(
        {
            "sentence": "Сього́дні га́рний ден.",
            "error": "ден",
            "correction": "день",
            "options": ["день", "Ден", "дєнь", "дэнь"],
        },
        level="a1",
    )
    assert any("must not contain the spotted error" in d for d in cased)

    meta = gates.error_correction_item_defects(
        {
            "sentence": "Find the soft-sign error in this word.",
            "error": "ден",
            "correction": "день",
            "options": ["день", "дєнь", "дэнь"],
        },
        level="a1",
    )
    assert any("meta-prompt" in d or "Ukrainian-first" in d for d in meta)

    ok = gates.error_correction_item_defects(
        {
            "sentence": "Сього́дні га́рний ден. — Today is a nice day (misspelled).",
            "error": "ден",
            "correction": "день",
            "options": ["день", "дєнь", "дэнь"],
        },
        level="a1",
    )
    assert ok == []


def test_error_correction_unaccented_correct_copy_fails():
    """Bare «ложка» against stressed «ло́жка» is not a spelling distractor."""
    bad = gates.error_correction_item_defects(
        {
            "sentence": "На столі́ лежи́ть льожка. — A spoon is on the table.",
            "error": "льожка",
            "correction": "ло́жка",
            "options": ["ло́жка", "льожка", "ложка"],
        },
        level="a1",
    )
    assert any("unaccented copy" in d for d in bad)

    # Genuine different-stress triple still passes.
    assert (
        gates.error_correction_item_defects(
            {
                "sentence": "Це моло́ко. — This is milk.",
                "error": "моло́ко",
                "correction": "молоко́",
                "options": ["молоко́", "мо́локо", "малоко́"],
            },
            level="a1",
        )
        == []
    )


def test_correct_keys_includes_error_correction_winning_form():
    keys = gates._correct_keys(
        {
            "error": "Кийи́в",
            "correction": "Ки́їв",
            "options": ["Ки́їв", "Кийи́в", "Ки́ів"],
        }
    )
    assert "ки́їв" in keys
    errors = gates.pedagogical_error_forms(
        {
            "inline": [
                {
                    "type": "error-correction",
                    "items": [
                        {
                            "error": "Кийи́в",
                            "correction": "Ки́їв",
                            "options": ["Ки́їв", "Кийи́в", "Ки́ів"],
                        }
                    ],
                }
            ],
            "workbook": [],
        }
    )
    assert "ки́їв" not in errors
    assert "кийи́в" in errors


def test_wrong_stress_checks_proper_names_against_oracle():
    # Proper names must not be exempt from wrong-stress via allow.
    bad = gates.wrong_stress("Ми ї́демо в Киї́в.", set(), {"Київ"})
    assert any("Киї́в" in x for x in bad)
    good = gates.wrong_stress("Ми ї́демо в Ки́їв.", set(), {"Київ"})
    assert good == []


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


def _dump_lesson_resources(items):
    import json

    from scripts.build.linear_pipeline import _parse_and_dump_writer_json_artifact

    return yaml.safe_load(_parse_and_dump_writer_json_artifact(
        "resources.yaml", json.dumps(items, ensure_ascii=False), 1, lesson_mode=True,
    ))


def test_lesson_resource_source_ref_is_accepted_as_source():
    dumped = _dump_lesson_resources([
        {"title": "Буквар", "source_ref": "Захарійчук, 1 клас, с. 14"},
        {"title": "Чанк", "chunk_id": "1-klas-bukvar_s0014"},
        {"title": "Має source", "source": "оригінал", "source_ref": "інше"},
    ])
    assert dumped[0]["source"] == "Захарійчук, 1 клас, с. 14"
    assert dumped[0]["source_ref"] == "Захарійчук, 1 клас, с. 14"
    assert "source" not in dumped[1] and "url" not in dumped[1]
    assert dumped[2]["source"] == "оригінал"


@pytest.mark.parametrize("item", [
    {"title": "", "source_ref": "Захарійчук, 1 клас, с. 14"},
    {"title": "Буквар", "source_ref": "  "},
    {"title": "Буквар", "source_ref": 14},
    {"title": "Буквар"},
])
def test_lesson_resource_without_title_or_locator_still_fails(item):
    from scripts.build.linear_pipeline import LinearPipelineError

    with pytest.raises(LinearPipelineError, match="requires title and url/chunk_id/source"):
        _dump_lesson_resources([item])


def test_unavailable_stress_oracle_fails_closed(gold, monkeypatch):
    def unavailable(*args):
        raise RuntimeError("unavailable")
    monkeypatch.setattr(gates, "wrong_stress", unavailable)
    report = gates.run_lesson_gates(*gold)
    assert any("stress oracle unavailable" in d for d in report["diagnostics"])


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
    assert "Find-and-Fix" in prompt or "error-correction" in prompt
    assert "DISTRACTOR_INVENTORY" not in prompt  # must be substituted
    assert ">=3" in prompt or "≥3" in prompt
    assert "Distractor inventory" in prompt
    for name in ("writer_prompt.md", "reviewer_prompt.md", "writer_raw.md"):
        (module / "lesson-1" / name).write_text(prompt)
    after = gates.run_lesson_gates(module, source, plan)
    assert after["diagnostics"] == before["diagnostics"]
    # The same reference remains blocking when it leaks into a learner file.
    learner_path = module / "lesson-1/module.md"
    learner_path.write_text(learner_path.read_text() + "\n\nULP\n")
    leaked = gates.run_lesson_gates(module, source, plan)
    assert not any("unattributed reference-name" in d for d in leaked["blocking"])
    assert any("unattributed reference-name" in d for d in leaked["warnings"])


# ── alphabet-module machinery (#8237) ────────────────────────────────────────


def _alphabet_gold(gold, slug="reading-ukrainian"):
    module, source, plan = gold
    plan["slug"] = slug
    return module, source, plan


def _line_break_blocks(report):
    return [d for d in report["blocking"] if "перенос" in d or "line break" in d]


def test_alphabet_full_gate_ignores_heading_and_skips_dropped_provenance(gold):
    """lessons.yaml is never hand-edited: a row for a dropped original is skipped (#8237 r2)."""
    module, source, plan = _alphabet_gold(gold)
    path = module / "lesson-1/module.md"
    path.write_text(path.read_text() + "\n\n## Перенос і підсумок\n")
    assert _line_break_blocks(gates.run_lesson_gates(module, source, plan)) == []

    base = yaml.safe_load((source / "activities.yaml").read_text())
    base["inline"][0]["instruction"] = "Перенос слів"
    (source / "activities.yaml").write_text(yaml.safe_dump(base, allow_unicode=True))
    lessons_before = (module / "lessons.yaml").read_text()
    report = gates.run_lesson_gates(module, source, plan)
    assert not any("provenance" in d for d in report["diagnostics"]), report["diagnostics"]
    assert (module / "lessons.yaml").read_text() == lessons_before


def test_alphabet_gate_still_blocks_other_provenance_errors(gold):
    module, source, plan = _alphabet_gold(gold)
    base = yaml.safe_load((source / "activities.yaml").read_text())
    base["inline"][0]["instruction"] = "Перенос слів"
    (source / "activities.yaml").write_text(yaml.safe_dump(base, allow_unicode=True))
    path = module / "lessons.yaml"
    ly = yaml.safe_load(path.read_text())
    row = next(p for p in ly["provenance"] if p["new_id"] == "act-2")

    row["new_id"] = "act-3"  # a kept original renamed
    path.write_text(yaml.safe_dump(ly, allow_unicode=True))
    report = gates.run_lesson_gates(module, source, plan)
    assert not report["passed"]
    assert any("provenance" in d for d in report["diagnostics"]), report["diagnostics"]

    row["new_id"] = "act-2"
    ly["provenance"].remove(row)  # a kept original lost
    path.write_text(yaml.safe_dump(ly, allow_unicode=True))
    report = gates.run_lesson_gates(module, source, plan)
    assert not report["passed"]
    assert "Original activity indexes must be contiguous" in report["diagnostics"]


_NOTEBOOK_CUE = "Open your notebook and copy each new word by hand three times, saying it aloud as you write."


def _install_dropped_hyphenation_section(module, source, *, cue_lesson):
    """Archive ``Контраст і пастки`` (lesson 1) then ``Перенос і письмо`` (lesson 2) with a surviving cue."""
    contrast = "Compare the two spellings side by side and read each pair aloud before you check the answer."
    path = source / "module.md"
    path.write_text(path.read_text().replace(
        "## Предмети навколо",
        f"## Контраст і пастки\n\n{contrast}\n\n## Перенос і письмо\n\n"
        "Перенос слів: a word splits across a line only between its syllables.\n\n"
        f"{_NOTEBOOK_CUE}\n\n## Предмети навколо", 1))
    path = module / "lessons.yaml"
    ly = yaml.safe_load(path.read_text())
    ly["lessons"][0]["sections"].append("Контраст і пастки")
    ly["lessons"][1]["sections"].insert(0, "Перенос і письмо")
    path.write_text(yaml.safe_dump(ly, allow_unicode=True))
    for n, extra in ((1, contrast), (cue_lesson, _NOTEBOOK_CUE)):
        path = module / f"lesson-{n}/module.md"
        path.write_text(path.read_text() + f"\n\n{extra}\n")


def _misplaced(report):
    return [d for d in report["blocking"] if "original paragraph belongs to lesson" in d]


def test_alphabet_surviving_paragraph_follows_the_heading_the_writer_sees(gold):
    """The prompt drops ``## Перенос і письмо``, so its surviving cue reads under ``Контраст і пастки`` (#8236)."""
    module, source, plan = _alphabet_gold(gold, "special-signs")
    _install_dropped_hyphenation_section(module, source, cue_lesson=1)
    report = gates.run_lesson_gates(module, source, plan)
    assert _misplaced(report) == []
    assert report["facts"]["preservation"]["lost"] == 0


# ── upgrade preservation vs empty-sign / error-correction rewrite (#8236) ─────

_NO_SIGN = "без знака — no sign"


def _archive_fill_in(extra_sentence):
    return {"type": "fill-in", "title": "Додай знак — Add a sign",
            "instruction": "Обери ь, апо́строф або без знака. — Choose ь, an apostrophe, or no sign.",
            "items": [
                {"sentence": "сім___я", "answer": "'", "options": ["'", "ь", _NO_SIGN]},
                {"sentence": "ден___", "answer": "ь", "options": ["ь", "'", _NO_SIGN]},
                {"sentence": extra_sentence, "answer": _NO_SIGN, "options": [_NO_SIGN, "'", "ь"]},
            ]}


def _archive_error_correction(sentence):
    return {"type": "error-correction", "title": "Виправ пастки — Correct the traps",
            "instruction": "Обери правильну українську форму. — Choose the correct Ukrainian form.",
            "items": [
                {"sentence": sentence, "error": "сімя", "correction": "сім'я́", "options": ["сім'я́", "сімя"],
                 "explanation": "У слові сім'я́ потрібен апо́строф. — In the word сім'я́ an apostrophe is needed."},
                {"sentence": "Сього́дні га́рний і те́плий ден.", "error": "ден", "correction": "день",
                 "options": ["день", "ден"],
                 "explanation": "День потребує м'якого знака. — День requires a soft sign."},
            ]}


_ARCHIVE_ORIGINALS = {
    "act-3": ("inline", 2, _archive_fill_in("У слові свя́то правильний вибір — ___ .")),
    "act-4": ("inline", 4, _archive_error_correction("Моя́ дру́жна сімя живе́ у Ки́єві.")),
    "act-w3": ("workbook", 2, _archive_error_correction("Це на́ша дру́жна сімя.")),
    "act-w5": ("workbook", 4, _archive_fill_in("У слові цвях правильний вибір — ___ .")),
}
_EC_DISTRACTORS = {"сімя": ["сімья", "сім'йа"], "ден": ["день'", "дьен"]}


def _legal_rewrite(activity):
    """What an obedient upgrade writer ships: ``""`` chips; EC without the error token, plus a distractor."""
    out = yaml.safe_load(yaml.safe_dump(activity, allow_unicode=True))
    for item in out["items"]:
        if out["type"] == "fill-in":
            item["options"] = ["" if o == _NO_SIGN else o for o in item["options"]]
            item["answer"] = "" if item["answer"] == _NO_SIGN else item["answer"]
        else:
            item["options"] = [item["correction"], *_EC_DISTRACTORS[item["error"]]]
    return out


def _install_archive_originals(module, source, *, rewrite):
    base_path = source / "activities.yaml"
    base = yaml.safe_load(base_path.read_text())
    for aid, (placement, index, activity) in _ARCHIVE_ORIGINALS.items():
        base[placement][index] = {**({"id": aid} if placement == "inline" else {}), **activity}
    base_path.write_text(yaml.safe_dump(base, allow_unicode=True, sort_keys=False))
    seen = set()
    for path in sorted(module.glob("lesson-*/activities.yaml")):
        data = yaml.safe_load(path.read_text())
        for placement in ("inline", "workbook"):
            for i, act in enumerate(data.get(placement) or []):
                if act.get("id") in _ARCHIVE_ORIGINALS:
                    original = _ARCHIVE_ORIGINALS[act["id"]][2]
                    data[placement][i] = {"id": act["id"], **(_legal_rewrite(original) if rewrite else original)}
                    seen.add(act["id"])
        path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False))
    assert seen == set(_ARCHIVE_ORIGINALS)


def _not_preserved(report):
    return sorted(d.split(":")[0] for d in report["blocking"] if "not preserved structurally" in d)


def test_alphabet_preservation_accepts_the_legal_rewrite_of_archive_activities(gold):
    module, source, plan = _alphabet_gold(gold, "special-signs")
    _install_archive_originals(module, source, rewrite=True)
    report = gates.run_lesson_gates(module, source, plan)
    assert _not_preserved(report) == []
    for aid in _ARCHIVE_ORIGINALS:
        assert not any(f" {aid}[" in d and ("fill-in" in d or "error-correction" in d)
                       for d in report["blocking"]), report["blocking"]


# ── letter-module immersion floors (#7994) ───────────────────────────────────


# ── #7994: EC explanations may grow mid-sentence; phonetic tokens; A1 landing ──

def _rewrite_act4(module, mutate):
    for path in module.glob("lesson-*/activities.yaml"):
        data = yaml.safe_load(path.read_text())
        for act in data.get("inline") or []:
            if act.get("id") == "act-4":
                mutate(act["items"][0])
        path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False))


def test_alphabet_preservation_accepts_a_mid_sentence_explanation_gloss(gold):
    module, source, plan = _alphabet_gold(gold, "special-signs")
    _install_archive_originals(module, source, rewrite=True)
    expanded = ("У слові сім'я́ потрібен апо́строф після губного м перед я. — "
                "In the word сім'я́ an apostrophe is needed after the labial м before я.")
    _rewrite_act4(module, lambda item: item.update(explanation=expanded))
    original = _ARCHIVE_ORIGINALS["act-4"][2]["items"][0]["explanation"]
    assert not gates.contains(original, expanded, expand_explanations=True)  # not a prefix: a mid-sentence gloss
    assert _not_preserved(gates.run_lesson_gates(module, source, plan)) == []

    _rewrite_act4(module, lambda item: item.update(error="сімья"))
    assert _not_preserved(gates.run_lesson_gates(module, source, plan)) == ["act-4"]


@pytest.mark.parametrize("token", ["йа́блуко", "Йу́шка", "мойа́", "л'у́ди", "па́л'ц'і", "п’йат’"])
def test_phonetic_transcriptions_skip_the_stress_dictionary_in_alphabet_lessons(token):
    assert gates._is_phonetic_token(token)
    assert gates.wrong_stress(token, set(), phonetic=True) == []
    bare = gates.strip_acute(token)
    assert gates.missing_stress(bare, set(), phonetic=True) == []


@pytest.mark.parametrize("word", ["сім'я́", "бур'я́н", "комп’ю́тер", "його́", "я́блуко", "моя́"])
def test_real_words_are_not_phonetic_tokens(word):
    assert not gates._is_phonetic_token(word)


def test_real_apostrophe_words_are_still_stress_checked():
    assert gates.wrong_stress("сі́м'я", set(), phonetic=True)  # wrong acute still caught
    assert gates.wrong_stress("сім'я́", set(), phonetic=True) == []
    assert "сімя" not in gates.missing_stress("сім'я", set(), phonetic=True)
    assert gates.missing_stress("сім'я", set(), phonetic=True) == ["сім'я"]
    # Outside alphabet slugs a transcription is an unstressed unknown word, as before.
    assert gates.missing_stress("мойа", set()) == ["мойа"]


_MISSPELT_ACTS = {
    "inline": [{"id": "act-ec", "type": "error-correction", "items": [
        {"sentence": "Це вчител.", "error": "вчител", "correction": "вчи́тель"},
        {"sentence": "Це моя́ сімя.", "error": "сімя", "correction": "сім'я́"},
        {"sentence": "Це ___ дім.", "answer": "нови́й", "options": ["нови́й", "но́вий"]},
    ]}],
    "workbook": [],
}


def test_pedagogical_misspellings_are_non_words_only():
    misspelt = gates.pedagogical_misspellings(_MISSPELT_ACTS)
    assert {"вчител", "сімя"} <= misspelt
    # A real word used as a distractor is exempt only inside its own activity.
    assert not {"новий", "но́вий", "нови́й", "сім'я́", "сім'я"} & misspelt
    allow = {gates.strip_acute(w) for w in misspelt}
    assert gates.wrong_stress("вчи́тел", allow, exact_skip=misspelt) == []
    assert gates.missing_stress("Це сімя.", allow) == []
    assert gates.wrong_stress("сі́м'я", allow, exact_skip=misspelt)  # still dictionary-checked
    assert gates.missing_stress("сім'я", allow) == ["сім'я"]


def _unstressed(report):
    return [d for d in report["blocking"] if "without stress mark" in d]


def _quote_act4_error_in_prose(module):
    for path in module.glob("lesson-*/activities.yaml"):
        if "act-4" in path.read_text():
            prose = path.parent / "module.md"
            prose.write_text(prose.read_text() + "\n\nNever write сімя: the apostrophe is missing.\n")


def test_alphabet_prose_may_quote_the_activity_error_token(gold):
    module, source, plan = _alphabet_gold(gold, "special-signs")
    _install_archive_originals(module, source, rewrite=True)
    _rewrite_act4(module, lambda item: item.update(error="сімя"))
    _quote_act4_error_in_prose(module)
    assert not any("сімя" in d for d in _unstressed(gates.run_lesson_gates(module, source, plan)))


def test_non_alphabet_prose_quoting_an_error_token_still_blocks(gold):
    module, source, plan = gold
    _install_archive_originals(module, source, rewrite=False)
    _rewrite_act4(module, lambda item: item.update(error="сімя"))
    _quote_act4_error_in_prose(module)
    assert any("сімя" in d for d in _unstressed(gates.run_lesson_gates(module, source, plan)))


# ── alphabet stress: same-lesson marked forms + VESUM-attested inflections (#7994) ──

def test_dictionary_stressed_forms_cover_verified_copies_but_not_rejected_marks():
    text = "сім'я́ і сім''я, дере́в'яний стіл, до ньо́го"
    wrong = gates.wrong_stress(text, set(), phonetic=True)
    covered = gates.dictionary_stressed_forms(text, wrong, phonetic=True)
    assert "сім'я" in covered
    assert "дерев'яний" not in covered  # contradicts the dictionary
    assert "ньо́го: undeclared unverified stress" in wrong
    assert "нього" not in covered  # pending stress cannot vouch for a bare copy
    assert gates.missing_stress("сім''я і дерев'яний", covered, phonetic=True) == ["дерев'яний"]


# Real VESUM analyses for the forms below; data/vesum.db is not available in CI.
_VESUM_ATTESTED = {"Мар'яною": "Мар'яна"}


@pytest.fixture
def vesum_stub(monkeypatch):
    from scripts.verification import vesum

    def verify_word(word, *args, **kwargs):
        lemma = _VESUM_ATTESTED.get(word)
        return [{"lemma": lemma, "pos": "noun", "tags": ""}] if lemma else []

    monkeypatch.setattr(vesum, "verify_word", verify_word)


def test_split_attested_undeclared_keeps_typos_and_contradictions_blocking(vesum_stub):
    wrong = gates.wrong_stress("до тебе́ з Мар'я́ною, вчі́тель, дере́в'яний", set(), {"Мар'яна"})
    blocking, attested = gates.split_attested_undeclared(wrong)
    assert sorted(e.split(":")[0] for e in attested) == ["Мар'я́ною"]
    assert not any("тебе́" in e for e in blocking)
    assert any(e.startswith("вчі́тель") for e in blocking)
    assert any(e.startswith("дере́в'яний→") for e in blocking)


def _stress_blocks(report):
    return [d for d in report["blocking"] if "without stress mark" in d or "contradict the stress dictionary" in d]


_REAL_WRONG_STRESS = gates.wrong_stress  # the gold fixture stubs the oracle out


_SAME_LESSON = "\n\nЦе сім'я́. Моя́ сім'я вели́ка. Я йду́ до тебе́ з Мар'я́ною.\n"


def test_alphabet_gate_passes_marked_form_and_attested_inflections(gold, monkeypatch, vesum_stub):
    monkeypatch.setattr(gates, "wrong_stress", _REAL_WRONG_STRESS)
    module, source, plan = _alphabet_gold(gold)
    path = module / "lesson-1/module.md"
    baseline = _stress_blocks(gates.run_lesson_gates(module, source, plan))
    path.write_text(path.read_text() + _SAME_LESSON)
    report = gates.run_lesson_gates(module, source, plan)
    # a swallowed oracle error would empty the stress blocks and pass vacuously
    assert not any("invalid lesson artifacts" in d for d in report["blocking"])
    # the appended twins add nothing; the gold's own contradictions keep blocking
    assert _stress_blocks(report) == baseline
    assert any("Мар'я́ною" in w for w in report["warnings"])
    assert not any("тебе́" in w for w in report["warnings"])


# The unaccented ними is VESUM-attested but still triggers a missing-stress warning.
_NONCE_LESSON = "\n\nЦе фундамета́льні пра́вила. Дере́в'яний стіл стоїть перед ними.\n"


def test_split_nonce_undeclared_keeps_contradictions_blocking():
    wrong = gates.wrong_stress("фундамета́льні, дере́в'яний", set())
    blocking, nonce = gates.split_nonce_undeclared(wrong)
    assert nonce == ["фундамета́льні: undeclared unverified stress"]
    assert len(blocking) == 1 and blocking[0].startswith("дере́в'яний→")


def test_alphabet_gate_warns_on_nonce_but_blocks_contradiction_and_missing(gold, monkeypatch, vesum_stub):
    monkeypatch.setattr(gates, "wrong_stress", _REAL_WRONG_STRESS)
    module, source, plan = _alphabet_gold(gold)
    path = module / "lesson-1/module.md"
    path.write_text(path.read_text() + _NONCE_LESSON)
    report = gates.run_lesson_gates(module, source, plan)
    assert not any("invalid lesson artifacts" in d for d in report["blocking"])
    blocks = "\n".join(_stress_blocks(report))
    assert "фундамета́льні" not in blocks
    assert any("фундамета́льні" in w and "typos or fragments" in w for w in report["warnings"])
    assert "Дере́в'яний→дерев'я́ний" in blocks  # dictionary contradiction
    assert "ними" not in blocks
    assert any("ними" in w and "without stress mark" in w for w in report["warnings"])


def test_non_alphabet_gate_still_blocks_nonce_stress(gold, monkeypatch):
    monkeypatch.setattr(gates, "wrong_stress", _REAL_WRONG_STRESS)
    module, source, plan = gold
    path = module / "lesson-1/module.md"
    path.write_text(path.read_text() + _NONCE_LESSON)
    blocks = "\n".join(_stress_blocks(gates.run_lesson_gates(module, source, plan)))
    assert "фундамета́льні: undeclared unverified stress" in blocks


def test_non_alphabet_gate_still_blocks_unmarked_copy_and_undeclared_inflection(gold, monkeypatch):
    monkeypatch.setattr(gates, "wrong_stress", _REAL_WRONG_STRESS)
    module, source, plan = gold
    path = module / "lesson-1/module.md"
    path.write_text(path.read_text() + _SAME_LESSON)
    blocks = "\n".join(_stress_blocks(gates.run_lesson_gates(module, source, plan)))
    assert "сім'я" in blocks and "Мар'я́ною: undeclared unverified stress" in blocks
    assert "тебе́: undeclared unverified stress" not in blocks


def test_alphabet_wrong_option_words_skip_stress_but_the_answer_still_checks():
    acts = {
        "inline": [{"id": "act-c", "type": "fill-in",
                    "items": [{"sentence": "Яка́ лі́тера? «...а́шка»", "answer": "Ц (цу́кор)",
                               "options": ["Ц (цу́кор)", "Ч (чу́кор)"]}]},
                   {"id": "act-mc", "type": "quiz",
                    "questions": [{"question": "Де ь?", "correct": 0,
                                   "options": [{"text": "па́лець"}, {"text": "па́лечь"}]}]}],
        "workbook": [],
    }
    assert "чу́кор" not in gates.pedagogical_error_forms(acts)  # non-alphabet unchanged
    forms = gates.pedagogical_error_forms(acts, option_words=True)
    assert {"чу́кор", "а́шка", "па́лечь"} <= forms
    assert "цу́кор" not in forms and "па́лець" not in forms
    misspelt = gates.pedagogical_misspellings(acts, option_words=True)
    assert {"чу́кор", "чукор", "па́лечь"} <= misspelt
    assert gates.wrong_stress("Ч (чу́кор) «...а́шка» па́лечь", set(), exact_skip=misspelt) == []
    assert gates.wrong_stress("Ч (чу́кор)", set()) == ["чу́кор: undeclared unverified stress"]
    assert gates.wrong_stress("цуко́р", set(), exact_skip=misspelt)  # the answer's word still checks


def test_alphabet_citation_surnames_warn_instead_of_block():
    text = "За підру́чником: Захарійчу́к, 1 клас, § 12. Вчі́тель пи́ше да́лі в уро́ці про і́нше, без жо́дного посила́ння."
    surnames = gates.citation_surnames(text)
    assert "Захарійчу́к" in surnames
    wrong = ["Захарійчу́к: undeclared unverified stress", "вчі́тель: undeclared unverified stress",
             "Строка́ль→Стро́каль"]
    blocking, cited = gates.split_citation_surnames(wrong, surnames | {"Строка́ль"})
    assert cited == ["Захарійчу́к: undeclared unverified stress"]
    assert blocking == wrong[1:]
    assert gates.citation_surnames("Строка́ль пи́ше. Далі нічо́го.") == set()


def test_alphabet_error_correction_counts_unique_options(monkeypatch):
    """#7994: alphabet slugs count chips unique; repair fills illegal mutants."""
    cloned = {
        "sentence": "Це моя́ сімя́.",
        "error": "сімя́",
        "correction": "сім'я́",
        "options": ["сім'я́", "сім'я́", "сьім'я"],
        "explanation": "Apostrophe after м before я.",
    }
    # Stub: no option/mutant is a real word, so repair keeps сьім'я and may fill a third.
    monkeypatch.setattr("scripts.build.alphabet_modules.vesum_is_word", lambda _w: False)
    assert gates.error_correction_item_defects(cloned, level="a1", alphabet=True) == []
    _, _, chips = gates._ec_rendered_chips(cloned, alphabet=True)
    assert len(gates._ec_distinct_chips(chips)) >= 2
    # Non-alphabet still blocks the duplicate (no repair).
    assert any(
        "duplicates" in d for d in gates.error_correction_item_defects(cloned, level="a1")
    )

    # Winner-only with every mutant declared a word → unique-2 still blocks.
    monkeypatch.setattr("scripts.build.alphabet_modules.vesum_is_word", lambda _w: True)
    winner_only = {
        "sentence": "Це ло́шка.",
        "error": "ло́шка",
        "correction": "ло́жка",
        "options": ["ло́жка", "ло́жка", "ло́жка"],
    }
    blocked = gates.error_correction_item_defects(winner_only, level="a1", alphabet=True)
    assert any(">=2 distinct" in d for d in blocked)

    # Error chip is dropped by repair; remaining illegal distractors still pass.
    monkeypatch.setattr("scripts.build.alphabet_modules.vesum_is_word", lambda _w: False)
    with_error = {**cloned, "options": ["сім'я́", "сімя́", "сьім'я"]}
    assert gates.error_correction_item_defects(with_error, level="a1", alphabet=True) == []
    _, _, err_chips = gates._ec_rendered_chips(with_error, alphabet=True)
    assert "сімя́" not in err_chips

    no_correction = {**cloned, "options": ["сьім'я", "сем'я"]}
    # Repair always injects the winner, so a missing authored correction chip is fixed.
    assert gates.error_correction_item_defects(no_correction, level="a1", alphabet=True) == []

    three = {**cloned, "options": ["сім'я́", "сьім'я", "сем'я"]}
    assert gates.error_correction_item_defects(three, level="a1", alphabet=True) == []
    assert not any(
        "distinct" in w
        for w in gates.error_correction_item_warnings(three, level="a1", alphabet=True)
    )


def test_alphabet_ec_gate_sees_repaired_chips(monkeypatch):
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
    defects = gates.error_correction_item_defects(item, level="a1", alphabet=True)
    assert defects == []
    _, _, chips = gates._ec_rendered_chips(item, alphabet=True)
    keys = {gates.strip_acute(gates.nfc(c)).lower() for c in chips}
    assert "чаю" not in keys and "чаї" not in keys
    assert "чай" in keys
