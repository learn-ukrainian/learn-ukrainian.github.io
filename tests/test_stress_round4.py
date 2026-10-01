"""Round-4 regressions: real, read-only ULIF and VESUM rows captured at intake."""

import json
import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.verification import stress, stress_comparison, teaching_stress
from scripts.verification.ulif_stress import compatible, joined_analyses
from scripts.wiki import sources_db

CAPTURE = json.loads((Path(__file__).parent / "fixtures/stress-round4.json").read_text())


@pytest.fixture
def real_rows(tmp_path, monkeypatch):
    conn = sqlite3.connect(tmp_path / "source.sqlite")
    conn.row_factory = sqlite3.Row
    for table, rows in [
        ("ulif_forms_build", [CAPTURE["build"]]),
        ("ulif_forms", CAPTURE["forms"]),
        ("ulif_dictua_entries", CAPTURE["entries"]),
    ]:
        keys = list(rows[0])
        conn.execute(f"CREATE TABLE {table} ({','.join(keys)})")
        conn.executemany(
            f"INSERT INTO {table} VALUES ({','.join('?' for _ in keys)})", [list(row.values()) for row in rows]
        )
    conn.commit()
    monkeypatch.setattr(sources_db, "_get_conn", lambda: conn)
    monkeypatch.setattr(stress, "_vesum_lookup", lambda form: CAPTURE["vesum"].get(form, []))
    yield conn
    conn.close()


@pytest.mark.parametrize(
    "required,supplied,expected",
    [
        (set(), {"PronType=Int", "PronType=Rel"}, True),
        ({"PronType=Int"}, {"PronType=Int", "PronType=Rel"}, True),
        ({"PronType=Rel"}, {"PronType=Int", "PronType=Rel"}, True),
        ({"PronType=Neg"}, {"PronType=Int", "PronType=Rel"}, False),
        ({"upos=NOUN"}, {"upos=PROPN"}, False),
        ({"upos=PROPN"}, {"upos=NOUN"}, False),
    ],
)
def test_feature_values_are_sets_with_distinct_proper_pos(required, supplied, expected):
    assert compatible(required, supplied) is expected


@pytest.mark.parametrize(
    "form,lemma,expected",
    [
        ("кому", "хто", "кому́"),
        ("кого", "хто", "кого́"),
        ("чому", "чому", "чому́"),
        ("чого", "що", "чого́"),
        ("коли", "коли", "коли́"),
        ("куди", "куди", "куди́"),
        ("звідки", "звідки", "зві́дки"),
        ("котра", "котрий", "котра́"),
        ("чиє", "чий", "чиє́"),
        ("якому", "який", "яко́му"),
        ("тому", "тому", "тому́"),
    ],
)
def test_interrogative_relative_real_analyses_resolve(real_rows, form, lemma, expected):
    # СУМ-20, https://slovnyk.me/dict/newsum/хто, attests кого́ and кому́.
    # Dat context distinguishes кому́ from the independently attested locative.
    result = stress.verify_stress(
        form,
        lemma=lemma,
        pos="ADV" if form == "тому" else None,
        tags="Case=Dat" if form == "кому" else None,
    )
    assert result["status"] == "ok"
    assert {m["stressed_form"] for m in result["matches"]} == {expected}


@pytest.mark.parametrize(
    "form,expected",
    [
        ("була", "була́"),
        ("велика", "вели́ка"),
        ("добра", "до́бра"),
        ("зелена", "зеле́на"),
        ("беру", "беру́"),
        ("брати", "бра́ти"),
        ("дорога", "доро́га"),
        ("жінки", "жі́нки"),
    ],
)
def test_uncovered_analysis_never_drops_proven_readings(real_rows, form, expected):
    result = stress.verify_stress(form)
    assert result["status"] == "ambiguous"
    assert expected in {m["stressed_form"] for m in result["matches"]}
    assert result["uncovered_vesum_analyses"]


def test_context_resolves_partial_coverage(real_rows):
    result = stress.verify_stress("була", lemma="бути")
    assert result["status"] == "ok"
    assert [m["stressed_form"] for m in result["matches"]] == ["була́"]


@pytest.mark.parametrize(
    "form,expected",
    [
        ("Іванові", "Іва́нові"),
        ("Вона", "Вона́"),
        ("Мене", "Мене́"),
        ("Зелена", "Зеле́на"),
        ("Тому", "Тому́"),
        ("Усі", "Усі́"),
        ("віку", "ві́ку"),
        ("себе", "себе́"),
        ("яка", "яка́"),
        ("яку", "яку́"),
    ],
)
def test_capitalized_and_cross_pos_readings_include_adjudication(real_rows, form, expected):
    result = stress.verify_stress(form)
    assert result["status"] in ("ok", "ambiguous")
    assert expected in {m["stressed_form"] for m in result["matches"]}
    for match in result["matches"]:
        for entry in match.get("evidence", []):
            row = next(
                r
                for r in sources_db.ulif_stress_rows(form.lower()) + sources_db.ulif_stress_rows(form)
                if r["id"] == entry["id"]
            )
            assert joined_analyses(row, match["vesum_analyses"])


def test_common_noun_row_never_stresses_proper_name(real_rows):
    row = next(r for r in sources_db.ulif_stress_rows("вона") if r["entry_key"] == "вон#1")
    assert joined_analyses(row, CAPTURE["vesum"]["Вона"]) == []
    assert stress.verify_stress("Вона", pos="PRON")["matches"][0]["stressed_form"] == "Вона́"
    assert stress.verify_stress("Мене", pos="PRON")["matches"][0]["stressed_form"] == "Мене́"


def test_gate_does_not_reject_correct_or_offer_other_word(real_rows):
    from scripts.build.lesson_gates import wrong_stress

    assert wrong_stress("беру́ була́ вели́ка Коли́ Зеле́на Мене́ Вона́", set()) == []


@pytest.mark.parametrize("apostrophe", ["'", "’", "ʼ"])
def test_vesum_apostrophe_lookup_is_normalized(apostrophe, monkeypatch):
    from scripts.verification import vesum

    seen = []
    monkeypatch.setattr(vesum, "verify_word", lambda form: seen.append(form) or [])
    stress._vesum_lookup(f"м{apostrophe}ясо")
    assert seen == ["м'ясо"]


@pytest.mark.parametrize("apostrophe", ["'", "’", "ʼ"])
def test_apostrophes_in_oracle_mcp_gate_annotator(real_rows, apostrophe, monkeypatch):
    from scripts.build.lesson_gates import wrong_stress
    from scripts.pipeline import stress_annotator as annotator

    original = stress._vesum_lookup
    monkeypatch.setattr(stress, "_vesum_lookup", lambda form: original(form.translate(str.maketrans("’ʼ", "''"))))
    bare = f"м{apostrophe}ясо"
    expected = f"м{apostrophe}я́со"
    result = stress.verify_stress(bare)
    assert result["stress_source"] == "ulif"
    assert [m["stressed_form"] for m in result["matches"]] == [expected]
    assert stress.verify_stresses([bare])["words"][0]["readings"][0]["stressed_form"] == expected
    assert wrong_stress(expected, set()) == []
    assert annotator._oracle_choice(bare) == expected


def test_comparison_records_returned_ambiguity_with_single_proven_choice(real_rows):
    record = stress_comparison.compare_form("велика")
    assert record["status"] == record["oracle"]["status"] == "ambiguous"
    assert record["ambiguous"] is True
    assert len(record["oracle"]["matches"]) == 1


def test_practice_keeps_pending_morphologically_attested_imperative(monkeypatch):
    from scripts.audit.generate_practice_deck import _imperative_display

    _imperative_display.cache_clear()
    monkeypatch.setattr(stress, "verify_stress", lambda *a, **k: {"status": "pending", "matches": []})
    assert _imperative_display("захистіть", "p") == "захистіть"
    monkeypatch.setattr(stress, "verify_stress", lambda *a, **k: {"status": "ambiguous", "matches": []})
    _imperative_display.cache_clear()
    assert _imperative_display("захистіть", "p") is None
    _imperative_display.cache_clear()


def test_ipa_uses_oracle_and_withholds_ambiguity(real_rows, monkeypatch):
    from scripts.generate_mdx import generate_ipa

    received = []
    monkeypatch.setattr(generate_ipa, "_ipa_overrides", {})
    monkeypatch.setitem(sys.modules, "ipa_uk", SimpleNamespace(ipa=lambda text: received.append(text) or "a"))
    assert generate_ipa.generate_ipa("Вона") == "[a]"
    assert received == ["Вона́"]
    assert generate_ipa.generate_ipa("яка") is None
    assert received == ["Вона́"]


def test_teaching_source_absence_never_relabels_heuristic(real_rows):
    assert teaching_stress.source_info()["available"] is False
    assert teaching_stress.sourced_teaching_choice("мами", [1, 3]) is None
    match = {
        "stressed_form": "ма́ми́",
        "unstressed_form": "мами",
        "vowel_indices": [1, 3],
        "source": "ulif",
        "dual_stress": True,
        "pedagogical_stressed_form": "мами́",
    }
    assert stress.pedagogical_stressed_form(match) == "ма́ми́"
    assert stress.spoken_stressed_form(match) is None


@pytest.mark.parametrize(
    "text,author,expected",
    [
        ("ма́ми і мами́", "Микола Погрібний", "ма́ми"),
        ("мами́, ма́ми", "Микола Погрібний", "мами́"),
        ("ма́ми і мами́", "unknown", None),
        ("мами [м а ми]", "Микола Погрібний", None),
        ("ма́мам", "Микола Погрібний", None),
        ("мами́́", "Микола Погрібний", None),
    ],
)
def test_first_listed_teaching_variant_needs_exact_source(text, author, expected, monkeypatch):
    # Explicitly synthetic dictionary transport fixture tests source parsing;
    # it is never counted as corpus coverage or Ukrainian adjudication.
    row = {
        "id": 1,
        "word": "мами",
        "dictionary_label": author,
        "title": "test fixture",
        "text": text,
        "source_url": "https://example.org/fixture",
    }
    monkeypatch.setattr(teaching_stress, "dictionary_rows", lambda: [row])
    choice = teaching_stress.sourced_teaching_choice("Мами", [1, 3])
    if expected is None:
        assert choice is None
    else:
        match = {"stressed_form": "Ма́ми́", "unstressed_form": "Мами", "vowel_indices": [1, 3], **choice}
        assert stress.pedagogical_stressed_form(match) == expected.capitalize()
        assert stress.spoken_stressed_form(match) == expected.capitalize()
        assert choice["pedagogical_source"][0]["row_id"] == 1


def test_ipa_prose_replacement_uses_text_oracle(real_rows):
    from scripts.generate_mdx.generate_ipa import _stressify_phrase, _stressify_word

    assert _stressify_word("Вона") == "Вона́"
    assert _stressify_word("яка") == "яка"
    assert _stressify_phrase("Вона яка") == "Вона́ яка"


@pytest.mark.parametrize("apostrophe", ["'", "’", "ʼ"])
def test_override_apostrophe_spellings_are_equivalent(apostrophe):
    word = f"сім{apostrophe}я"
    result = stress.verify_stress(word)
    assert result["stress_source"] == "override"
    assert [m["stressed_form"] for m in result["matches"]] == [f"сім{apostrophe}я́"]


def test_teaching_dictionary_conflicts_and_identity_invalidate_choice(monkeypatch):
    row = {
        "id": 1,
        "word": "мами",
        "dictionary_label": "Pohribnyi",
        "title": "synthetic fixture",
        "text": "ма́ми",
        "source_url": "https://example.org/fixture",
    }
    other = {**row, "id": 2, "text": "мами́"}
    monkeypatch.setattr(teaching_stress, "dictionary_rows", lambda: [row])
    first = teaching_stress.source_info()
    assert teaching_stress.sourced_teaching_choice("мами", [1, 3])
    monkeypatch.setattr(teaching_stress, "dictionary_rows", lambda: [row, other])
    assert teaching_stress.source_info()["digest"] != first["digest"]
    assert teaching_stress.sourced_teaching_choice("мами", [1, 3]) is None
    monkeypatch.setattr(teaching_stress, "dictionary_rows", lambda: [{**row, "word": "інші"}])
    assert teaching_stress.sourced_teaching_choice("мами", [1, 3]) is None
