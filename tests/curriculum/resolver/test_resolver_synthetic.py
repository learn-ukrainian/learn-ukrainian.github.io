"""Synthetic group: every class and code of the resolver on invented words.

These prove codes, not the language boundary; the real-data group does that.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
import yaml
from resolver_helpers import allowlist, document, form, record, stressed, unit

from scripts.curriculum.evidence import lock
from scripts.curriculum.resolver import codes
from scripts.curriculum.resolver.inputs import ResolverError
from scripts.curriculum.resolver.questions import build_questions, load_questions, validate_questions, write_questions
from scripts.curriculum.resolver.receipts import apply_answers, build_receipts, check_receipts, write_receipts
from scripts.curriculum.resolver.stream import resolve
from scripts.curriculum.resolver.tokenize import tokenize

REPO_ROOT = Path(__file__).resolve().parents[3]

BZYUK = record(
    1,
    "бзюк",
    "noun",
    [
        form("бзюк", "noun:inanim:m:v_naz", "бзюк"),
        form("бзюк", "noun:inanim:m:v_zna", "бзюк"),
        form("бзюка", "noun:inanim:m:v_rod", stressed("бзюка", 3)),
    ],
    gloss="synthetic-one",
)
FRYAMBA_A = record(2, "фрямба", "noun", [form("фрямба", "noun:inanim:f:v_naz", stressed("фрямба", 2))], "synthetic-a")
FRYAMBA_B = record(3, "фрямба", "noun", [form("фрямба", "noun:anim:f:v_naz", stressed("фрямба", 2))], "synthetic-b")
KVETUR_A = record(4, "кветур", "noun", [form("кветур", "noun:inanim:m:v_naz", stressed("кветур", 2))])
KVETUR_B = record(5, "кветур", "noun", [form("кветур", "noun:inanim:m:v_naz", stressed("кветур", 4))])
ZHMURBAN = record(6, "Жмурбан", "noun", [form("Жмурбан", "noun:anim:m:v_naz:prop:fname", stressed("Жмурбан", 5))])
SHPROK = record(7, "шпрок", "noun", [form("шпрок", "noun:inanim:m:v_naz", "шпрок", source="none")])
MARKED = record(8, "вурдик", "noun", [form("вурдик", "noun:inanim:m:v_naz", stressed("вурдик", 1), markers=["bad"])])


def _only(stream, text):
    found = [t for t in stream.tokens if t["token"] == text]
    assert len(found) == 1, found
    return found[0]


# --- tokenizer ------------------------------------------------------------------


def test_hyphenated_and_apostrophes_stay_one_token():
    tokens = tokenize("фрям-бзюк бз'юк бз’юк бзʼюк бз'юк-фрям")
    assert [t.text for t in tokens] == ["фрям-бзюк", "бз'юк", "бз’юк", "бзʼюк", "бз'юк-фрям"]
    assert {t.lookup for t in tokens[1:4]} == {"бз'юк"}
    assert tokens[4].parts == ("бз'юк", "фрям") and tokens[0].hyphenated
    assert [t.start for t in tokens] == [0, 10, 16, 22, 28]


def test_edges_quotes_kinds_and_sentence_starts():
    tokens = tokenize("— Бзюк, 'глорт' і abc 12 Kвет. «Шпрок» -фрям")
    by_text = {t.text: t for t in tokens}
    assert by_text["Бзюк"].sentence_initial and not by_text["глорт"].sentence_initial
    assert by_text["abc"].kind == "latin" and by_text["12"].kind == "digits"
    assert by_text["Kвет"].kind == "mixed"  # Latin K inside a Cyrillic word
    assert by_text["Шпрок"].sentence_initial and by_text["фрям"].text == "фрям"


# --- classes --------------------------------------------------------------------


def test_one_record_syncretic_forms_resolve_without_question(sources):
    stream = resolve(document(unit("глорт бзюк")), allowlist([BZYUK, SHPROK]), sources)
    token = _only(stream, "бзюк")
    assert token["class"] == codes.RESOLVED and token["provenance"] == "deterministic"
    assert token["selected"] == {
        "record": "W-1",
        "forms": ["noun:inanim:m:v_naz", "noun:inanim:m:v_zna"],
        "stressed": "бзюк",
    }
    assert token["features"] == ["Animacy=Inan", "Gender=Masc", "Number=Sing", "upos=NOUN"]
    assert stream.open_tokens() == []


def test_shared_stress_is_identity_open_non_blocking(sources):
    doc = document(unit("фрямба"))
    stream = resolve(doc, allowlist([FRYAMBA_A, FRYAMBA_B]), sources)
    token = _only(stream, "фрямба")
    assert token["class"] == codes.STRESS_CERTAIN_IDENTITY_OPEN and token["selected"] is None
    batch = build_questions(stream, doc, allowlist([FRYAMBA_A, FRYAMBA_B]))
    validate_questions(batch)
    (question,) = batch["questions"]
    assert question["blocking"] is False and question["id"] == "Q-001"
    assert [c["gloss_en"] for c in question["candidates"]] == ["synthetic-a", "synthetic-b"]


def test_different_stress_is_stress_open_blocking(sources):
    doc = document(unit("кветур"))
    allowed = allowlist([KVETUR_A, KVETUR_B])
    stream = resolve(doc, allowed, sources)
    assert _only(stream, "кветур")["class"] == codes.STRESS_OPEN
    assert build_questions(stream, doc, allowed)["questions"][0]["blocking"] is True
    only_one = resolve(doc, allowlist([KVETUR_A]), sources)
    assert _only(only_one, "кветур")["class"] == codes.RESOLVED


def test_one_record_with_two_stresses_is_stress_open(sources):
    two = record(
        9,
        "бзюки",
        "noun",
        [form("бзюки", "noun:p:v_naz", stressed("бзюки", 2)), form("бзюки", "noun:s:v_rod", stressed("бзюки", 4))],
    )
    doc = document(unit("бзюки"))
    stream = resolve(doc, allowlist([two]), sources)
    assert _only(stream, "бзюки")["class"] == codes.STRESS_OPEN
    batch = build_questions(stream, doc, allowlist([two]))
    with pytest.raises(ResolverError) as error:
        apply_answers(batch, {"answers": [{"id": "Q-001", "record": "W-9"}]}, "synthetic-seat")
    assert error.value.code == codes.INVALID_ANSWER
    chosen = batch["questions"][0]["candidates"][1]["stressed"]
    picked = apply_answers(batch, {"answers": [{"id": "Q-001", "record": "W-9", "stressed": chosen}]}, "synthetic-seat")
    assert picked["Q-001"] == {"record": "W-9", "forms": ["noun:s:v_rod"], "stressed": chosen}


def test_pending_stress(sources):
    lone = record(10, "глорт", "noun", [form("глорт", "noun:inanim:m:v_naz", None)])
    known = record(11, "глорт", "noun", [form("глорт", "noun:anim:m:v_naz", stressed("глорт", 2))])
    doc = document(unit("глорт"))
    assert _only(resolve(doc, allowlist([lone]), sources), "глорт")["class"] == codes.PENDING_STRESS
    competing = resolve(doc, allowlist([lone, known]), sources)
    assert _only(competing, "глорт")["class"] == codes.STRESS_OPEN
    batch = build_questions(competing, doc, allowlist([lone, known]))
    with pytest.raises(ResolverError) as error:
        apply_answers(batch, {"answers": [{"id": "Q-001", "record": "W-10"}]}, "synthetic-seat")
    assert error.value.code == codes.PENDING_STRESS
    assert (
        apply_answers(batch, {"answers": [{"id": "Q-001", "record": "W-11"}]}, "synthetic-seat")["Q-001"]["record"]
        == "W-11"
    )


def test_six_records_are_too_many(sources):
    six = [
        record(20 + i, "фрямба", "noun", [form("фрямба", "noun:inanim:f:v_naz", stressed("фрямба", 2))])
        for i in range(6)
    ]
    stream = resolve(document(unit("фрямба")), allowlist(six), sources)
    assert _only(stream, "фрямба")["class"] == codes.TOO_MANY_CANDIDATES
    assert "synthetic plan a1/synthetic-module lesson 1" in stream.failures[0]["message"]


def test_marked_only_and_unknown_are_outside_state_with_analyses(sources):
    stream = resolve(document(unit("вурдик глорт")), allowlist([MARKED]), sources)
    marked, unknown = stream.tokens
    assert marked["class"] == unknown["class"] == codes.LEMMA_OUTSIDE_STATE
    assert marked["marked"][0]["record"] == "W-8" and "only marked" in marked["message"]
    assert unknown["analyses"] == {"глорт": [{"lemma": "глорт", "pos": "noun", "tags": "noun:inanim:m:v_naz"}]}
    assert [f["token"] for f in stream.failures] == ["вурдик", "глорт"]
    assert stream.failures[1]["text"] == "вурдик глорт"


def test_unknown_hyphenated_token_is_one_failure_naming_its_parts(sources):
    stream = resolve(document(unit("глорт-трямс")), allowlist([SHPROK]), sources)
    (token,) = stream.tokens
    assert token["class"] == codes.LEMMA_OUTSIDE_STATE
    assert set(token["analyses"]) == {"глорт-трямс", "глорт", "трямс"}
    assert "глорт (noun)" in token["message"] and "трямс (verb)" in token["message"]


def test_case_rules_and_proper_nouns(sources):
    lower = record(12, "жмурбан", "noun", [form("жмурбан", "noun:inanim:m:v_naz", stressed("жмурбан", 1))])
    stream = resolve(
        document(unit("Жмурбан шпрок, Жмурбан жмурбан Шпрок")), allowlist([ZHMURBAN, lower, SHPROK]), sources
    )
    first, _, second, third, fourth = stream.tokens
    assert first["class"] == codes.STRESS_OPEN and first["surface"] == codes.PROPER_NOUN  # both records
    assert second["candidates"] == ["W-6"] and second["surface"] == codes.PROPER_NOUN
    assert third["candidates"] == ["W-12"] and third["surface"] == codes.SENTENCE_TOKEN
    assert fourth["class"] == codes.LEMMA_OUTSIDE_STATE and fourth["surface"] == codes.PROPER_NOUN
    initial_lower = resolve(document(unit("Шпрок.")), allowlist([SHPROK]), sources).tokens[0]
    assert initial_lower["selected"]["record"] == "W-7" and initial_lower["surface"] == codes.SENTENCE_TOKEN
    named = resolve(document(unit("шпрок")), allowlist([SHPROK], name_ids={"W-7"}), sources).tokens[0]
    assert named["surface"] == codes.PROPER_NOUN


@pytest.mark.parametrize("role", sorted(codes.SKIPPED_ROLES))
def test_skipped_roles_are_never_looked_up(sources, role):
    stream = resolve(document(unit("вурдик глорт abc 12 Kвет", role)), allowlist([]), sources)
    assert [t["class"] for t in stream.tokens] == [codes.skipped(role)] * 5 and not stream.failures


def test_latin_digits_and_mixed_scripts(sources):
    stream = resolve(document(unit("abc 12 Kвет")), allowlist([]), sources)
    assert [t["class"] for t in stream.tokens] == ["skipped:latin", "skipped:digits", codes.UNCLASSIFIABLE]


def test_phonetics_letters(sources):
    stream = resolve(document(unit("бз зю ґ", "phonetics")), allowlist([], letters={"Б", "З", "Ю"}), sources)
    assert [t["class"] for t in stream.tokens] == [codes.LETTER_OR_SYLLABLE] * 2 + [codes.LETTER_OUTSIDE_STATE]


def test_gloss_refs(sources):
    allowed = allowlist([BZYUK, SHPROK], gloss_ids={"W-1"})
    stream = resolve(
        document(unit("{{gloss:W-1}}", "gloss_ref"), unit("{{gloss:W-7}}", "gloss_ref"), unit("x", "gloss_ref")),
        allowed,
        sources,
    )
    good, outside, empty = stream.tokens
    assert good["class"] == codes.RESOLVED and good["selected"]["record"] == "W-1"
    assert outside["class"] == codes.GLOSS_OUTSIDE_LESSON and empty["class"] == codes.UNCLASSIFIABLE


def test_quoted_term_resolves(sources):
    stream = resolve(document(unit("бзюк", "quoted_term")), allowlist([BZYUK]), sources)
    assert stream.tokens[0]["class"] == codes.RESOLVED


def test_accent_and_bad_shapes_fail_closed():
    with pytest.raises(ResolverError) as error:
        document(unit("бзю́к"))
    assert error.value.code == codes.ACCENT_IN_INPUT and "бзю" in error.value.message
    with pytest.raises(ResolverError) as error:
        document(unit("бзюк", "prose"))
    assert error.value.code == codes.INVALID_INPUT


def test_trie_cross_check_reports_source_changed(sources):
    invented = record(
        13, "кветур", "noun", [form("кветур", "noun:inanim:m:v_naz", stressed("кветур", 2), source="trie")]
    )
    stream = resolve(document(unit("кветур")), allowlist([invented]), sources)
    assert stream.tokens[0]["class"] == codes.RESOLVED
    assert [r["code"] for r in stream.reports] == [codes.SOURCE_CHANGED]
    assert stream.reports[0]["oracle_status"] == "not_found"


# --- questions, answers, receipts ------------------------------------------------


def _open_lesson(sources):
    doc = document(unit("кветур і фрямба", "dialogue_line", activity="a1", item=0, block="line"), unit("бзюк"))
    allowed = allowlist(
        [
            BZYUK,
            FRYAMBA_A,
            FRYAMBA_B,
            KVETUR_A,
            KVETUR_B,
            record(30, "і", "conj", [form("і", "conj:coord", "і", source="none")]),
        ]
    )
    stream = resolve(doc, allowed, sources)
    return doc, allowed, stream, build_questions(stream, doc, allowed)


def test_answers_validation(sources):
    _, _, _, batch = _open_lesson(sources)
    assert [(q["id"], q["token"], q["blocking"]) for q in batch["questions"]] == [
        ("Q-001", "кветур", True),
        ("Q-002", "фрямба", False),
    ]
    for answers, code in (
        ({"answers": [{"id": "Q-001", "record": "W-1"}]}, codes.INVALID_ANSWER),
        ({"answers": [{"id": "Q-009", "record": "W-4"}]}, codes.INVALID_ANSWER),
        ({"answers": [{"id": "Q-001", "record": "W-4"}, {"id": "Q-001", "record": "W-5"}]}, codes.INVALID_ANSWER),
        ({"answers": [{"id": "Q-002", "record": "W-2"}]}, codes.TOKEN_UNRESOLVED),
        ({"answer": []}, codes.INVALID_INPUT),
    ):
        with pytest.raises(ResolverError) as error:
            apply_answers(batch, answers, "synthetic-seat")
        assert error.value.code == code, answers
    with pytest.raises(ResolverError):
        apply_answers(batch, {"answers": [{"id": "Q-001", "record": "W-4"}]}, "seat:with-colon")


def test_receipts_roundtrip_lock_and_rules(sources, tmp_path):
    _, _, stream, batch = _open_lesson(sources)
    selections = apply_answers(batch, {"answers": [{"id": "Q-001", "record": "W-5"}]}, "agy/synthetic-7")
    doc = build_receipts(stream, batch, selections, "agy/synthetic-7")
    by_token = {t["token"]: t for t in doc["tokens"]}
    assert by_token["кветур"]["provenance"] == "question:agy/synthetic-7:Q-001"
    assert by_token["кветур"]["selected"]["record"] == "W-5"
    assert by_token["фрямба"]["selected"] is None and by_token["фрямба"]["provenance"] is None
    assert by_token["кветур"]["unit"] == {"tab": "urok", "activity": "a1", "item": 0, "block": "line"}

    path = tmp_path / "_state/synthetic-module/lesson-1.resolutions.yaml"
    write_receipts(path, doc)
    assert oct(path.stat().st_mode & 0o777) == "0o644"
    assert oct(path.parent.stat().st_mode & 0o777) == oct(path.parent.parent.stat().st_mode & 0o777) == "0o755"
    assert check_receipts(path) == doc
    path.write_bytes(path.read_bytes().replace(b"W-5", b"W-4"))
    with pytest.raises(ResolverError) as error:
        check_receipts(path)
    assert error.value.code == codes.LOCK_MISMATCH

    forged = yaml.safe_load(yaml.safe_dump(doc))
    forged["tokens"][0]["selected"] = {"record": "W-1", "forms": [], "stressed": "x"}
    with pytest.raises(ResolverError) as error:
        write_receipts(tmp_path / "forged.yaml", forged)
    assert error.value.code == codes.RECEIPT_INVALID

    with pytest.raises(ResolverError) as error:
        build_receipts(stream, batch, {}, None)
    assert error.value.code == codes.TOKEN_UNRESOLVED


def test_receipts_refuse_failures_and_stale_questions(sources):
    doc = document(unit("глорт"))
    stream = resolve(doc, allowlist([]), sources)
    with pytest.raises(ResolverError) as error:
        build_receipts(stream, build_questions(stream, doc, allowlist([])), {}, None)
    assert error.value.code == codes.LEMMA_OUTSIDE_STATE
    _, _, open_stream, batch = _open_lesson(sources)
    batch["inputs"] = {**batch["inputs"], "expanded_sha256": "0" * 64}
    with pytest.raises(ResolverError) as error:
        build_receipts(open_stream, batch, {}, None)
    assert error.value.code == codes.STALE_QUESTIONS


def test_questions_file_lock(sources, tmp_path):
    _, _, _, batch = _open_lesson(sources)
    path = tmp_path / "lesson-1.questions.yaml"
    write_questions(path, batch)
    assert load_questions(path) == batch
    path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(ResolverError) as error:
        load_questions(path)
    assert error.value.code == codes.LOCK_MISMATCH


def test_two_runs_are_byte_identical(sources):
    doc, allowed, stream, batch = _open_lesson(sources)
    again = resolve(doc, allowed, sources)
    assert stream.to_bytes() == again.to_bytes()
    assert lock.yaml_bytes(batch) == lock.yaml_bytes(build_questions(again, doc, allowed))


def test_every_subprocess_call_has_a_timeout():
    roots = [REPO_ROOT / "scripts/curriculum/resolver", Path(__file__).parent]
    missing = []
    for path in sorted(p for root in roots for p in root.glob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "subprocess"
                and not any(k.arg == "timeout" for k in node.keywords)
            ):
                missing.append(f"{path.name}:{node.lineno}")
    assert missing == []


def test_unit_step_parsing():
    """Unit.step accepts string or None; non-string raises INVALID_INPUT."""
    doc_none = document(unit("бзюк"))
    assert doc_none.units[0].step is None
    assert "step" not in doc_none.units[0].locator()

    doc_step = document(unit("бзюк", step="step-intro"))
    assert doc_step.units[0].step == "step-intro"
    assert doc_step.units[0].locator()["step"] == "step-intro"

    with pytest.raises(ResolverError) as exc:
        document(unit("бзюк", step=123))
    assert exc.value.code == codes.INVALID_INPUT

    with pytest.raises(ResolverError) as exc:
        document(unit("бзюк", step=["invalid"]))
    assert exc.value.code == codes.INVALID_INPUT


def test_receipts_carry_unit_step(sources):
    """Receipt tokens include unit.step when the originating unit defines step."""
    doc = document(unit("бзюк", step="step-intro"))
    allowed = allowlist([BZYUK])
    stream = resolve(doc, allowed, sources)
    questions = build_questions(stream, doc, allowed)
    receipts = build_receipts(stream, questions, {}, "test-seat")
    by_token = {t["token"]: t for t in receipts["tokens"]}
    assert by_token["бзюк"]["unit"]["step"] == "step-intro"
