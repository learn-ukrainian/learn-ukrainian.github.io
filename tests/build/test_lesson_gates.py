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


def test_contains_allows_expanded_explanations():
    orig = {"items": [{"sentence": "___ мене є стіл.", "answer": "У",
                       "explanation": "У мене є... is the I-have phrase."}]}
    new = {"items": [{"sentence": "___ мене́ є стіл.", "answer": "У",
                      "explanation": "У мене́ є... is the I-have phrase. Extra learner gloss."}]}
    assert gates.contains(orig, new)
    orig["items"][0]["explanation"] = "У тебе є...? asks one familiar person."
    new["items"][0]["explanation"] = 'У тебе́ є...? asks one familiar person: "Do you have...?"'
    assert gates.contains(orig, new)
    assert not gates.contains(orig, {"items": [{"sentence": "other", "answer": "У"}]})
    assert not gates.contains({"items": [{"answer": "a"}]}, {"items": [{"answer": "cat"}]})
    assert not gates.contains({"items": [{"answer": "yes"}]}, {"items": [{"answer": "not yes"}]})
    assert gates.contains("", "")
    assert gates.contains("...", "...")
    assert not gates.contains(
        {"explanation": "This is correct."},
        {"explanation": 'Ignore the false claim "This is correct."; the answer is wrong.'},
    )
    assert not gates.contains(
        {"explanation": "This answer is correct"},
        {"explanation": "This answer is correctly rejected."},
    )


def test_contains_allows_expanded_prompts_and_statements():
    orig = {"items": [{"prompt": "Ти студент?", "statement": "Він лікар."}]}
    new = {"items": [{"prompt": "Ти студе́нт? Are you a student?",
                      "statement": "Він лі́кар. He is a doctor."}]}
    assert gates.contains(orig, new)
    assert not gates.contains(
        {"items": [{"prompt": "Ти студент?"}]},
        {"items": [{"prompt": "Хто ти?"}]},
    )


def test_contains_allows_short_gloss_and_middle_dot_continuation():
    assert gates.contains(
        {"prompt": "Так."}, {"prompt": "Так · Yes."}
    )
    assert not gates.contains(
        {"prompt": "So."}, {"prompt": "Sonar."}
    )


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


def test_structural_containment_keeps_answers_and_multiplicity():
    assert gates.contains({"items": ["a", "a"]}, {"items": ["a", "a", "b"]})
    assert not gates.contains({"items": ["a", "a"]}, {"items": ["a", "b"]})
    assert not gates.contains(True, 1)


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


def test_error_correction_stress_contrast_is_not_tautology():
    """Acute-only triples are real choices; do not strip stress before comparing."""
    ok = gates.error_correction_item_defects(
        {
            "sentence": "Це моло́ко. — This is milk.",
            "error": "моло́ко",
            "correction": "молоко́",
            "options": ["молоко́", "мо́локо", "малоко́"],
        },
        level="a1",
    )
    assert ok == []


def test_error_correction_rendered_duplicate_chips_fail():
    """Full-sentence options that collapse to the same replacement are duplicates."""
    collapsed = gates.error_correction_item_defects(
        {
            "sentence": "Сьогодні гарний ден.",
            "error": "ден",
            "correction": "день",
            "options": ["день", "ден", "Сьогодні гарний день."],
        },
        level="a1",
    )
    assert any("duplicate" in d or "distractor" in d for d in collapsed)

    undecomposed = gates.error_correction_item_defects(
        {
            "sentence": "Сього́дні га́рний ден. — Today is a nice day.",
            "error": "ден",
            "correction": "день",
            "options": ["день", "ден", "Сього́дні га́рний день."],
        },
        level="a1",
    )
    assert any("did not reduce to a word chip" in d for d in undecomposed)


def test_error_correction_render_faithful_and_a1_en_scaffold():
    glossed = gates.error_correction_item_defects(
        {
            "sentence": "Сього́дні ден. — Today den.",
            "error": "ден",
            "correction": "день",
            "options": ["день (day)", "ден", "дєнь"],
        },
        level="a1",
    )
    assert any("correctForm" in d or "exact" in d for d in glossed)

    no_en = gates.error_correction_item_warnings(
        {
            "sentence": "Сього́дні га́рний ден.",
            "error": "ден",
            "correction": "день",
            "options": ["день", "дєнь", "дэнь"],
        },
        level="a1",
    )
    assert any("explanation" in d and "English" in d for d in no_en)

    # English on the sentence does not satisfy the scaffold; explanation does.
    stem_en = gates.error_correction_item_warnings(
        {
            "sentence": "Сього́дні га́рний ден. — Today is a nice day.",
            "error": "ден",
            "correction": "день",
            "options": ["день", "дєнь", "дэнь"],
        },
        level="a1",
    )
    assert any("explanation" in d for d in stem_en)
    explained = gates.error_correction_item_warnings(
        {
            "sentence": "Сього́дні га́рний ден.",
            "error": "ден",
            "correction": "день",
            "options": ["день", "дєнь", "дэнь"],
            "explanation": "День потребує м'якого знака. — Day needs a soft sign.",
        },
        level="a1",
    )
    assert explained == []

    # Missing EN is advisory, not a hard defect.
    assert (
        gates.error_correction_item_defects(
            {
                "sentence": "Сього́дні га́рний ден.",
                "error": "ден",
                "correction": "день",
                "options": ["день", "дєнь", "дэнь"],
            },
            level="a1",
        )
        == []
    )

    # Fresh B1 builds do not require EN scaffolds on EC stems.
    b1_ok = gates.error_correction_item_warnings(
        {
            "sentence": "Сього́дні га́рний ден.",
            "error": "ден",
            "correction": "день",
            "options": ["день", "дєнь", "дэнь"],
        },
        level="b1",
    )
    assert b1_ok == []


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


def test_contains_allows_expanded_error_correction_options():
    orig = {
        "items": [
            {
                "sentence": "Сього́дні ден.",
                "error": "ден",
                "correction": "день",
                "options": ["день", "ден"],
            }
        ]
    }
    expanded = {
        "items": [
            {
                "sentence": "Сього́дні ден.",
                "error": "ден",
                "correction": "день",
                "options": ["день", "ден", "дєнь"],
            }
        ]
    }
    assert gates.contains(orig, expanded)


def test_gold_preservation_activity_and_vocabulary_semantics(gold):
    report = gates.run_lesson_gates(*gold)
    # A missing rendered page must fail, but cannot conceal content results.
    assert not report["passed"]
    assert report["facts"]["preservation"] == {
        "long_paragraphs": 47, "lost": 0, "duplicated": 0, "misplaced": 0}
    content = [d for d in report["diagnostics"] if not any(
        label in d for label in ("stress oracle unavailable", "l2_exposure_floor", "render"))]
    assert content == []


def test_converted_fence_accepts_mdx_filename_keys(gold):
    module, source, plan = gold
    from scripts.generate_mdx.converters import _dialogue_box_mdx
    fence = "```text\nAlice: Hello there my friend!\nBob: Goodbye until next time!\n```"
    src = source / "module.md"
    src.write_text(fence + "\n\n" + src.read_text())
    box = _dialogue_box_mdx(
        [{"speaker": "Alice", "text": "Hello there my friend!"},
         {"speaker": "Bob", "text": "Goodbye until next time!"}],
        "Dialogue",
    )
    report = gates.run_lesson_gates(module, source, plan, rendered={"1.mdx": box})
    assert report["facts"]["preservation"]["misplaced"] == 0
    assert not any("belongs to lesson" in d for d in report["blocking"])


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


def test_copied_archived_name_line_is_not_unattributed(gold):
    module, source, plan = gold
    line = "If you want extra listening support, open ULP Season 1."
    (source / "module.md").write_text((source / "module.md").read_text() + "\n" + line + "\n")
    path = module / "lesson-1/module.md"
    path.write_text(path.read_text() + "\n" + line + "\n")
    report = gates.run_lesson_gates(module, source, plan)
    assert not any("unattributed reference-name" in d for d in report["blocking"])


def test_name_substring_of_archived_citation_is_still_unattributed(gold):
    module, source, plan = gold
    (source / "module.md").write_text(
        (source / "module.md").read_text() + "\nQuoted from Anna Ohoiko.\n"
    )
    path = module / "lesson-1/module.md"
    path.write_text(path.read_text() + "\nAnna\n")
    report = gates.run_lesson_gates(module, source, plan)
    assert any("unattributed reference-name" in d for d in report["blocking"])


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


# ── alphabet-module machinery (#8237) ────────────────────────────────────────

ALPHABET_SLUGS = ("sounds-letters-and-hello", "reading-ukrainian", "special-signs")


def test_fill_in_no_sign_wording_fails_but_empty_string_passes():
    for bad in ("без знака", "без зна́ка — no sign", "Немає знака", "No sign"):
        in_options = gates.fill_in_item_defects(
            {"sentence": "ден___ь", "answer": "ь", "options": ["ь", bad]}
        )
        assert any("empty string" in d for d in in_options), bad
        as_answer = gates.fill_in_item_defects(
            {"sentence": "ден___ь", "answer": bad, "options": ["ь", bad]}
        )
        assert any("empty string" in d for d in as_answer), bad

    assert gates.fill_in_item_defects(
        {"sentence": "ден___ь", "answer": "", "options": ["", "ь", "'"]}
    ) == []


def test_fill_in_activity_defects_only_looks_at_fill_in():
    fill = {"id": "act-1", "type": "fill-in",
            "items": [{"sentence": "a___", "answer": "без знака", "options": ["без знака", ""]}]}
    assert gates.fill_in_activity_defects(fill)
    assert gates.fill_in_activity_defects({**fill, "type": "quiz"}) == []


@pytest.mark.parametrize("slug", ALPHABET_SLUGS)
def test_alphabet_slugs_reject_line_break_activities_and_models(slug):
    divide = {"id": "a1", "type": "divide-words", "title": "Поділ", "items": [{"word": "мама"}]}
    assert any("divide-words" in d for d in gates.alphabet_line_break_defects(
        slug=slug, activities=[divide], prose=""))

    perenos = {"id": "a2", "type": "quiz", "instruction": "Перенос слів — Word breaks", "items": []}
    assert any("перенос" in d for d in gates.alphabet_line_break_defects(
        slug=slug, activities=[perenos], prose=""))

    titled = {"id": "a3", "type": "quiz", "title": "Правила переносу", "items": []}
    assert gates.alphabet_line_break_defects(slug=slug, activities=[titled], prose="")

    for model in ("Мар'-яна", "дере-в'яний", "бур'-ян", "паль-ці", "Мар’-яна"):
        assert gates.alphabet_line_break_defects(
            slug=slug, activities=[], prose=f"Пишемо {model} тут."), model
        assert gates.alphabet_line_break_defects(
            slug=slug, activities=[{"id": "a4", "type": "quiz", "items": [{"q": model}]}], prose=""), model

    clean = {"id": "a5", "type": "quiz", "title": "Склади", "instruction": "Оберіть склад", "items": [{"q": "ма-ма"}]}
    assert gates.alphabet_line_break_defects(slug=slug, activities=[clean], prose="Це мама.") == []


def test_other_slugs_keep_line_break_activities():
    divide = {"id": "a1", "type": "divide-words", "title": "Перенос", "items": []}
    assert gates.alphabet_line_break_defects(
        slug="my-family", activities=[divide], prose="бур'-ян") == []


@pytest.mark.parametrize("phrase", [
    "mastery of all 33 letters",
    "comprehensive command of the complete 33-letter",
    "use only prepared models",
    "before you leave the lesson tab",
    "Stay inside Ukrainian for this lesson",
])
def test_banned_learner_phrases_fail_case_insensitively(phrase):
    assert gates.banned_phrase_defects(f"Intro. {phrase.upper()}, then more.", "lesson 1 prose")
    assert gates.banned_phrase_defects(f"Intro. {phrase.lower()} ok", "module landing")


def test_bare_mastery_is_not_banned():
    assert gates.banned_phrase_defects("Mastery comes with practice.", "lesson 1 prose") == []


def _alphabet_gold(gold, slug="reading-ukrainian"):
    module, source, plan = gold
    plan["slug"] = slug
    return module, source, plan


def _line_break_blocks(report):
    return [d for d in report["blocking"] if "перенос" in d or "line break" in d]


def test_alphabet_full_gate_rejects_prose_teaching_line_breaks(gold):
    module, source, plan = _alphabet_gold(gold)
    path = module / "lesson-1/module.md"
    path.write_text(path.read_text() + "\n\nПеренос слова: пишемо стіл-ець, а не стілець, коли рядок закінчується.\n")
    assert any("prose mentions перенос" in d for d in _line_break_blocks(
        gates.run_lesson_gates(module, source, plan)))


def test_alphabet_full_gate_rejects_quiz_stem_about_hyphenation(gold):
    module, source, plan = _alphabet_gold(gold)
    path = module / "lesson-1/activities.yaml"
    data = yaml.safe_load(path.read_text())
    data["inline"].append({"id": "act-lb", "type": "quiz", "instruction": "Оберіть відповідь",
                           "items": [{"question": "Як зробити перенос слова «книга»?",
                                      "options": ["кни-га", "ки-нга"], "answer": "кни-га"}]})
    path.write_text(yaml.safe_dump(data, allow_unicode=True))
    assert any("act-lb" in d for d in _line_break_blocks(
        gates.run_lesson_gates(module, source, plan)))


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


def test_alphabet_gate_does_not_require_a_dropped_line_break_baseline_section(gold):
    module, source, plan = _alphabet_gold(gold, "special-signs")
    path = source / "module.md"
    path.write_text(path.read_text() + "\n\n## Перенос і письмо\n\n"
                    "You will sometimes see words split across a line in printed Ukrainian today.\n")
    report = gates.run_lesson_gates(module, source, plan)
    assert not any("has no lesson mapping" in d for d in report["blocking"])

    # Any other unmapped baseline section is still a checker-config error.
    path.write_text(path.read_text() + "\n\n## Зайвий розділ\n\nЦе ще один абзац без жодного уроку.\n")
    report = gates.run_lesson_gates(module, source, plan)
    assert any("baseline section 'Зайвий розділ' has no lesson mapping" in d for d in report["blocking"])


def test_non_alphabet_gate_still_requires_a_line_break_baseline_section(gold):
    module, source, plan = gold
    path = source / "module.md"
    path.write_text(path.read_text() + "\n\n## Перенос і письмо\n\nПеренос слів у цьому модулі.\n")
    report = gates.run_lesson_gates(module, source, plan)
    assert any("baseline section 'Перенос і письмо' has no lesson mapping" in d for d in report["blocking"])


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


def test_alphabet_surviving_paragraph_in_the_dropped_sections_lesson_is_misplaced(gold):
    module, source, plan = _alphabet_gold(gold, "special-signs")
    _install_dropped_hyphenation_section(module, source, cue_lesson=2)
    assert any("belongs to lesson 1 but is in [2]" in d and "Open your notebook" in d
               for d in _misplaced(gates.run_lesson_gates(module, source, plan)))


def test_non_alphabet_paragraph_stays_with_its_own_hyphenation_section(gold):
    module, source, plan = gold
    _install_dropped_hyphenation_section(module, source, cue_lesson=1)
    assert any("belongs to lesson 2 but is in [1]" in d and "Open your notebook" in d
               for d in _misplaced(gates.run_lesson_gates(module, source, plan)))


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


def test_alphabet_dirty_archive_copy_still_fails_fill_in_and_ec_gates(gold):
    module, source, plan = _alphabet_gold(gold, "special-signs")
    _install_archive_originals(module, source, rewrite=False)
    blocking = gates.run_lesson_gates(module, source, plan)["blocking"]
    for aid in ("act-3", "act-w5"):
        assert any(f" {aid}[" in d and "words the empty choice" in d for d in blocking), blocking
    for aid in ("act-4", "act-w3"):
        # Alphabet slugs count unique chips (>=2 passes), so the archive's
        # [correction, error] blocks on the error chip, not on the count.
        assert any(f" {aid}[" in d and "must not contain the spotted error" in d for d in blocking), blocking


def test_non_alphabet_preservation_still_compares_the_raw_archive(gold):
    module, source, plan = gold
    _install_archive_originals(module, source, rewrite=True)
    assert _not_preserved(gates.run_lesson_gates(module, source, plan)) == sorted(_ARCHIVE_ORIGINALS)


def test_alphabet_preservation_still_requires_sentence_error_correction_and_real_options(gold):
    module, source, plan = _alphabet_gold(gold, "special-signs")
    _install_archive_originals(module, source, rewrite=True)
    for path in module.glob("lesson-*/activities.yaml"):
        data = yaml.safe_load(path.read_text())
        for act in data.get("inline") or []:
            if act.get("id") == "act-4":
                act["items"][0]["error"] = "сімʼя"
            if act.get("id") == "act-3":
                act["items"][0]["options"] = ["'", ""]  # the real ь option lost
        path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False))
    assert _not_preserved(gates.run_lesson_gates(module, source, plan)) == ["act-3", "act-4"]


def test_alphabet_preservation_baseline_drops_banned_phrase_paragraphs(gold):
    module, source, plan = _alphabet_gold(gold, "special-signs")
    path = source / "module.md"
    clean = gates.run_lesson_gates(module, source, plan)["facts"]["baseline"]["long_paragraphs"]
    first_heading = path.read_text().index("\n## ")
    end = path.read_text().index("\n\n", first_heading + 1)
    text = path.read_text()
    banned = ("Stay inside Ukrainian for this lesson. The apostrophe and soft sign already\n"
              "have Ukrainian jobs.\n\nBefore you leave the lesson\ntab, check that you can do these things today:")
    path.write_text(text[:end] + "\n\n" + banned + text[end:])
    report = gates.run_lesson_gates(module, source, plan)
    assert report["facts"]["baseline"]["long_paragraphs"] == clean
    assert not any("not preserved verbatim" in d for d in report["blocking"]), report["blocking"]

    plan["slug"] = "things-have-gender"
    report = gates.run_lesson_gates(module, source, plan)
    assert report["facts"]["baseline"]["long_paragraphs"] == clean + 2


# ── letter-module immersion floors (#7994) ───────────────────────────────────

def _fail_letter_floors(monkeypatch, *, tab3=4, dialogue_short=False):
    from scripts.build import linear_pipeline

    def long_uk(*args, **kwargs):
        return {"passed": False, "reason": "long_uk_without_gloss", "offending_runs": ["— Приві́т! Як спра́ви?"]}

    def floor(*args, **kwargs):
        required = {"uk_dialogue_lines": 10 if dialogue_short else 0, "uk_tab3_activities": 5}
        return {"passed": False, "required": required,
                "observed": {"uk_dialogue_lines": 3, "uk_tab3_activities": tab3}, "reason": "too_few"}

    monkeypatch.setattr(linear_pipeline, "_long_uk_ceiling_gate", long_uk)
    monkeypatch.setattr(linear_pipeline, "_l2_exposure_floor_gate", floor)


def _floor_lines(lines):
    return [d for d in lines if "long_uk_ceiling" in d or "l2_exposure_floor" in d]


def test_alphabet_long_uk_and_four_tab3_activities_are_advisory(gold, monkeypatch):
    module, source, plan = _alphabet_gold(gold, "special-signs")
    _fail_letter_floors(monkeypatch)
    report = gates.run_lesson_gates(module, source, plan)
    assert _floor_lines(report["blocking"]) == []
    assert len(_floor_lines(report["warnings"])) == 6  # both gates, three lessons
    assert report["facts"]["immersion"][1]["long_uk_ceiling"]["passed"] is False  # still recorded


def test_alphabet_floor_still_blocks_three_tab3_or_a_dialogue_shortfall(gold, monkeypatch):
    module, source, plan = _alphabet_gold(gold, "special-signs")
    _fail_letter_floors(monkeypatch, tab3=3)
    blocking = gates.run_lesson_gates(module, source, plan)["blocking"]
    assert len([d for d in blocking if "l2_exposure_floor failed" in d]) == 3
    _fail_letter_floors(monkeypatch, dialogue_short=True)
    blocking = gates.run_lesson_gates(module, source, plan)["blocking"]
    assert len([d for d in blocking if "l2_exposure_floor failed" in d]) == 3


def test_non_alphabet_a1_floors_stay_blocking(gold, monkeypatch):
    module, source, plan = gold
    _fail_letter_floors(monkeypatch)
    report = gates.run_lesson_gates(module, source, plan)
    assert len(_floor_lines(report["blocking"])) == 6
    assert _floor_lines(report["warnings"]) == []


def test_alphabet_preservation_does_not_require_original_ec_options(gold):
    module, source, plan = _alphabet_gold(gold, "special-signs")
    _install_archive_originals(module, source, rewrite=True)
    for path in module.glob("lesson-*/activities.yaml"):
        data = yaml.safe_load(path.read_text())
        for act in data.get("inline") or []:
            if act.get("id") == "act-4":  # three distinct chips, none copied from a one-chip list
                act["items"][0]["options"] = ["сімья", "сім'я́", "сім'йа"]
        path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False))
    assert _not_preserved(gates.run_lesson_gates(module, source, plan)) == []


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


def test_non_alphabet_preservation_still_compares_error_correction_explanations(gold):
    module, source, plan = gold
    _install_archive_originals(module, source, rewrite=False)
    assert _not_preserved(gates.run_lesson_gates(module, source, plan)) == []
    _rewrite_act4(module, lambda item: item.update(explanation="У слові сім'я́ потрібен апо́строф після губного."))
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


_LANDING = (
    "Two small signs change how you read: **м'яки́й знак** and **апо́строф**.\n\n"
    "By the end, you can:\n\n- read **день** and **сім'я́**;\n- choose the sign you hear.\n\n"
    "Keep the scope small: two signs, a handful of words.\n"
)


def _strip_original_outcomes(source):
    path = source / "module.md"
    _head, sep, rest = path.read_text().partition("\n## ")
    path.write_text("# Title\n\nA short opening paragraph that carries no outcome list at all.\n" + sep + rest)


def _landing_blocks(report):
    return [d for d in report["blocking"] if "landing-overview.md" in d]


def test_a1_upgrade_without_a_landing_overview_is_blocked(gold):
    module, source, plan = gold
    assert _landing_blocks(gates.run_lesson_gates(module, source, plan)) == []  # the original opening carries the outcomes
    _strip_original_outcomes(source)
    blocks = _landing_blocks(gates.run_lesson_gates(module, source, plan))
    assert len(blocks) == 1 and "missing at the module root" in blocks[0]


def test_a1_upgrade_with_a_bilingual_landing_overview_passes_the_landing_check(gold):
    module, source, plan = gold
    _strip_original_outcomes(source)
    (module / "landing-overview.md").write_text(_LANDING)
    assert _landing_blocks(gates.run_lesson_gates(module, source, plan)) == []


@pytest.mark.parametrize(("text", "needle"), [
    (_LANDING.replace("By the end, you can:", "You will learn:"), "By the end, you can"),
    ("Two small signs change how you read them. By the end, you can: read and choose the sign you hear.", "bilingual"),
    ("By the end, you can: **день**.", "unusable"),
])
def test_a_present_but_unusable_landing_overview_is_blocked(gold, text, needle):
    module, source, plan = gold
    (module / "landing-overview.md").write_text(text)
    blocks = _landing_blocks(gates.run_lesson_gates(module, source, plan))
    assert len(blocks) == 1 and needle in blocks[0]


def test_landing_overview_is_not_required_above_a1(gold):
    module, source, plan = gold
    _strip_original_outcomes(source)
    assert gates.landing_overview_defects(module, source, {**plan, "level": "a2"}) == []


@pytest.mark.parametrize("token", ["шчу́ка", "пло́шча", "Шчи́рий"])
def test_shcha_sound_transcription_skips_the_stress_dictionary(token):
    assert gates._is_phonetic_token(token)
    assert gates.wrong_stress(token, set(), phonetic=True) == []
    assert gates.missing_stress(gates.strip_acute(token), set(), phonetic=True) == []
    assert gates.missing_stress(gates.strip_acute(token), set())  # alphabet slugs only


def test_real_shcha_words_are_still_stress_checked():
    assert not gates._is_phonetic_token("щу́ка")
    assert gates.wrong_stress("щука́ пло́ща", set(), phonetic=True) == ["щука́→щу́ка"]
    assert gates.missing_stress("площа", set(), phonetic=True) == ["площа"]


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

def test_dictionary_stressed_forms_cover_unmarked_copies_but_not_rejected_marks():
    text = "сім'я́ і сім''я, дере́в'яний стіл, до ньо́го"
    wrong = gates.wrong_stress(text, set(), phonetic=True)
    covered = gates.dictionary_stressed_forms(text, wrong, phonetic=True)
    assert "сім'я" in covered
    assert "дерев'яний" not in covered  # contradicts the dictionary
    assert "нього" not in covered  # unverified stress never vouches for a bare copy
    assert gates.missing_stress("сім''я і дерев'яний", covered, phonetic=True) == ["дерев'яний"]


# Real VESUM analyses for the forms below; data/vesum.db is not available in CI.
_VESUM_ATTESTED = {"нього": "він", "Мар'яною": "Мар'яна"}


@pytest.fixture
def vesum_stub(monkeypatch):
    from scripts.verification import vesum

    def verify_word(word, *args, **kwargs):
        lemma = _VESUM_ATTESTED.get(word)
        return [{"lemma": lemma, "pos": "noun", "tags": ""}] if lemma else []

    monkeypatch.setattr(vesum, "verify_word", verify_word)


def test_split_attested_undeclared_keeps_typos_and_contradictions_blocking(vesum_stub):
    wrong = gates.wrong_stress("до ньо́го з Мар'я́ною, вчі́тель, дере́в'яний", set(), {"Мар'яна"})
    blocking, attested = gates.split_attested_undeclared(wrong)
    assert sorted(e.split(":")[0] for e in attested) == ["Мар'я́ною", "ньо́го"]
    assert any(e.startswith("вчі́тель") for e in blocking)
    assert any(e.startswith("дере́в'яний→") for e in blocking)


def _stress_blocks(report):
    return [d for d in report["blocking"] if "without stress mark" in d or "contradict the stress dictionary" in d]


_REAL_WRONG_STRESS = gates.wrong_stress  # the gold fixture stubs the oracle out


_SAME_LESSON = "\n\nЦе сім'я́. Моя́ сім'я вели́ка. Я йду́ до ньо́го з Мар'я́ною.\n"


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
    assert any("ньо́го" in w and "Мар'я́ною" in w for w in report["warnings"])


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
    assert "ними" in blocks  # dictionary lemma with no mark


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
    assert "сім'я" in blocks and "ньо́го: undeclared unverified stress" in blocks


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


def test_alphabet_error_correction_counts_unique_options():
    """#7994: alphabet slugs count chips unique; two distinct chips pass with a warning."""
    cloned = {
        "sentence": "Це моя́ сімя́.",
        "error": "сімя́",
        "correction": "сім'я́",
        "options": ["сім'я́", "сім'я́", "сьім'я"],
        "explanation": "Apostrophe after м before я.",
    }
    assert gates.error_correction_item_defects(cloned, level="a1", alphabet=True) == []
    warnings = gates.error_correction_item_warnings(cloned, level="a1", alphabet=True)
    assert any("2 distinct options" in w for w in warnings)
    # Non-alphabet still blocks the duplicate.
    assert any(
        "duplicates" in d for d in gates.error_correction_item_defects(cloned, level="a1")
    )
    assert not any(
        "distinct" in w for w in gates.error_correction_item_warnings(cloned, level="a1")
    )

    winner_only = {
        "sentence": "Це ло́шка.",
        "error": "ло́шка",
        "correction": "ло́жка",
        "options": ["ло́жка", "ло́жка", "ло́жка"],
    }
    blocked = gates.error_correction_item_defects(winner_only, level="a1", alphabet=True)
    assert any(">=2 distinct" in d for d in blocked)

    with_error = {**cloned, "options": ["сім'я́", "сімя́", "сьім'я"]}
    assert any(
        "must not contain the spotted error" in d
        for d in gates.error_correction_item_defects(with_error, level="a1", alphabet=True)
    )

    no_correction = {**cloned, "options": ["сьім'я", "сем'я"]}
    assert gates.error_correction_item_defects(no_correction, level="a1", alphabet=True)

    three = {**cloned, "options": ["сім'я́", "сьім'я", "сем'я"]}
    assert gates.error_correction_item_defects(three, level="a1", alphabet=True) == []
    assert not any(
        "distinct" in w
        for w in gates.error_correction_item_warnings(three, level="a1", alphabet=True)
    )


def test_error_correction_render_drops_repeated_chip():
    from scripts.build.activity_renderer import unique_error_correction_options

    assert unique_error_correction_options(["сім'я́", "сім'я́", "сьім'я"]) == ["сім'я́", "сьім'я"]
