"""Tests for Anna Ohoiko quality textbook enrichment (#7452).

Tests run completely standalone with deterministic fixtures (no live sources.db
required in CI):
1. 1000-words chunk parser (lemmas, gloss, wrapped two-column examples, locators).
2. 500-verbs chunk parser (verb lemmas, 'to ...' gloss, locator, morphology exclusion).
3. Translation duplicate detection and sense-preserving merge.
4. Examples deduplication and <=2 cap.
5. End-to-end enrichment on stub manifest entries.
6. Coverage of all 9 #7397 Ohoiko-provenance heads.
"""

from __future__ import annotations

from typing import Any

from scripts.lexicon.ohoiko_quality_enrichment import (
    HEADS_7397,
    apply_ohoiko_quality_enrichment,
    enrich_entry_with_ohoiko,
    is_duplicate_sense,
    is_plausible_example,
    merge_examples,
    merge_translation,
    parse_500_verbs_chunk,
    parse_1000_words_chunk,
)

# ---------------------------------------------------------------------------
# Fixtures for 1000-words chunks
# ---------------------------------------------------------------------------

SAMPLE_1000_CHUNKS: dict[str, tuple[str, str, str]] = {
    # (chunk_id, title, text)
    "e0001": (
        "anna-ohoiko-1000-words-2nd-ed_e0001",
        "а",
        "1. а  and, but\n(contrast between sentences)\n"
        "Я люблю́ готува́ти, а ти?                       I like to cook, and you (informal)?\n",
    ),
    "e0002": (
        "anna-ohoiko-1000-words-2nd-ed_e0002",
        "або́ = чи",
        "2. або́ = чи  or\nЗа́раз або́ ніко́ли.                            Now or never.\n"
        "Хо́чеш ча́ю чи ка́ви?                           Do you (informal) want tea or coffee?\n"
        "(a list of choices)\n",
    ),
    "e0003": (
        "anna-ohoiko-1000-words-2nd-ed_e0003",
        "авто́бус",
        "3. авто́бус  bus\nСашко́ ї́здить в шко́лу                         Sashko goes to school by bus.\n"
        "авто́бусом.\n",
    ),
    "e0006": (
        "anna-ohoiko-1000-words-2nd-ed_e0006",
        "акто́р, акто́рка",
        "6. акто́р, акто́рка  actor, actress\n"
        "Він хо́че ста́ти акто́ром.                      He wants to become an actor.\n"
        "Вона́ хо́че ста́ти акто́ркою.                   She wants to become an actress.\n",
    ),
    "e0007": (
        "anna-ohoiko-1000-words-2nd-ed_e0007",
        "а́кція",
        "7. а́кція  promotion (in sales)\n"
        "У нас сього́дні а́кція — зни́жка                Today we have a promotion — a\n"
        "30%.                                            30% discount.\n",
    ),
    "e0023": (
        "anna-ohoiko-1000-words-2nd-ed_e0023",
        "ба́чити, поба́чити",
        "23. ба́чити, поба́чити  to see\n(imperfective, perfective)\n"
        "Ти ба́чиш мене́?                                Do you see me?\n"
        "Поживе́мо — поба́чимо.                          We will live — we will see.\n"
        "(Ukrainian saying)\n",
    ),
    "e0047": (
        "anna-ohoiko-1000-words-2nd-ed_e0047",
        "боя́ тися, забоя́ тися",
        "47. боя́ тися, забоя́ тися  to fear, to be afraid\n(imperfective, perfective)\n"
        "Він бої́ться павукі́в.                          He is afraid of spiders.\n"
        "Головне́ — не забоя́тися.                       The main thing is not to become\n"
        "afraid.\n",
    ),
    "e0099": (
        "anna-ohoiko-1000-words-2nd-ed_e0099",
        "вихо́дити за́між, ви́йти за́між",
        "99. вихо́дити за́між, ви́йти  to marry (a man)\n"
        "за́між                                         (imperfective, perfective)\n"
        "Коли́сь дівча́та вихо́дили за́між Once upon a time, girls were getting\n"
        "ду́же ра́но.                       married very early.\n"
        "Ната́лка ви́йшла за́між за Петра́. Natalka married Petro.\n",
    ),
    "e0208": (
        "anna-ohoiko-1000-words-2nd-ed_e0208",
        "день ти́жня",
        "208. день ти́жня  day of the week\n"
        "Яки́й сього́дні день ти́жня?                   What day of the week is it today?\n",
    ),
    "e0336": (
        "anna-ohoiko-1000-words-2nd-ed_e0336",
        "карто́пля фрі",
        "336. карто́пля фрі  French fries\n"
        "Вели́ку карто́плю фрі з                        Large fries with ketchup, please.\n"
        "ке́тчупом, будь ла́ска.\n",
    ),
    "e0352": (
        "anna-ohoiko-1000-words-2nd-ed_e0352",
        "кліє́нт, кліє́нтка",
        "352. клієн\ń т, клієн\ń тка                              client (male, female)\n"
        "Ці лю́ди — мої́ кліє́нти.                       These people are my clients.\n",
    ),
    "e0542": (
        "anna-ohoiko-1000-words-2nd-ed_e0542",
        "одна́ково = так са́мо",
        "542. одна́ково = так са́мо  equally, the same way, alike\n"
        "Ма́ти лю́бить свої́х діте́й                     A mother loves her children equally.\n"
        "одна́ково (так са́мо).\n"
        "Усі́ пови́нні були́ жи́ти й ду́мати             Everyone had to live and think alike.\n"
        "одна́ково.\n",
    ),
    "e0589": (
        "anna-ohoiko-1000-words-2nd-ed_e0589",
        "пе́ред тим як",
        "589. пе́ред тим як  before (an action)\n"
        "Пе́ред тим як почина́ти, хо́чу                  Before I start (\"starting\"), I want to\n"
        "подя́кувати вам усі́м.                          thank you all.\n"
        "перемага́ти, перемогти́\n",
    ),
    "e0685": (
        "anna-ohoiko-1000-words-2nd-ed_e0685",
        "проє́кт",
        "685. проєк\ń т                                        project\n"
        "Це наш нови́й проє́кт.                         This is our new project.\n",
    ),
    "e0762": (
        "anna-ohoiko-1000-words-2nd-ed_e0762",
        "сільське́ господа́рство",
        "762. сільське́ господа́рство  agriculture\n"
        "Оре́ст працю́є в сільсько́му                     Orest works in agriculture.\n"
        "господа́рстві.\n",
    ),
    "e0841": (
        "anna-ohoiko-1000-words-2nd-ed_e0841",
        "так са́мо",
        "841. так са́мо  the same (adverb),\nin the same manner\n"
        "Та́ня одя́гнена так са́мо, як я.                Tania is dressed the same as me.\n",
    ),
    "e0843": (
        "anna-ohoiko-1000-words-2nd-ed_e0843",
        "таки́й са́мий",
        "843. таки́й са́мий  same (adjective)\n"
        "У нас такі́ са́мі пробле́ми.                    We have the same problems.\n",
    ),
    "e0143": (
        "anna-ohoiko-1000-words-2nd-ed_e0143",
        "вчи́тися = учи́тися =",
        "143. вчи́тися = учи́тися =  to study (somewhere or in\n"
        "навча́тися, навчи́тися                         a certain way), to learn\n"
        "(imperfective, perfective)\n"
        "Я мо́жу вчи́тися (навча́тися),                 I can study only when it is quiet.\n"
        "ті́льки коли́ ти́хо.\n"
        "Наза́р уже́ навчи́вся чита́ти.                 Nazar has already learned to read.\n",
    ),
    "e0214": (
        "anna-ohoiko-1000-words-2nd-ed_e0214",
        "дзвони́ти, задзвони́ти (1), 1) to ring;",
        "214. дзвони́ти, задзвони́ти (1), 1) to ring;\n"
        "подзвони́ти (2)                                2) to call, to give a call\n"
        "(imperfective, perfective)\n"
        "У це́ркві дзво́нять дзво́ни.                   Bells are ringing in the church.\n"
        "У це́ркві задзвони́ли дзво́ни.                 Bells started to ring in the church.\n"
        "Я дзвоню́ йому́ за́раз.                        I am calling him now.\n"
        "Я подзвоню́ йому́ за́втра.                     I will give him a call tomorrow.\n"
        "диви́тися, подиви́тися\n",
    ),
    "e0405": (
        "anna-ohoiko-1000-words-2nd-ed_e0405",
        "ліво́руч = злі́ва (1) =",
        "405. ліво́руч = злі́ва (1) =  1) on the left, to the left;\n"
        "налі́во (2)                                    2) left (direction)\n"
        "Ліво́руч (злі́ва) від Оле́ни — її́             To the left of Olena is her son Nazar.\n"
        "син Наза́р.\n"
        "Велосипеди́ст поверну́в ліво́руч               The cyclist turned left.\n"
        "(налі́во).\n",
    ),
    "e0543": (
        "anna-ohoiko-1000-words-2nd-ed_e0543",
        "одру́жуватися,",
        "543. одру́жуватися,  1) to get married;\n"
        "одружи́тися                                     2) to marry a woman\n"
        "(imperfective, perfective)\n"
        "Бага́то пар одру́жуються влі́тку.               Many couples get married in the\n"
        "summer.\n"
        "Оле́г одружи́вся з Мар’я́ною.                   Oleh married Mariana.\n",
    ),
    "e0658": (
        "anna-ohoiko-1000-words-2nd-ed_e0658",
        "право́руч = спра́ва (1) =",
        "658. право́руч = спра́ва (1) =  1) on the right, to the right;\n"
        "напра́во (2)                                   2) right (direction)\n"
        "Мій буди́нок право́руч (= спра́ва) My house is to the right of the shop.\n"
        "від магази́ну.\n"
        "Маши́на поверну́ла право́руч       The car turned right.\n"
        "(= напра́во).\n",
    ),
    "e0945": (
        "anna-ohoiko-1000-words-2nd-ed_e0945",
        "час від ча́су = ча́сом",
        "945. час від ча́су = ча́сом  from time to time, occasionally\n"
        "Час від ча́су (ча́сом) ми готу́ємо              We cook fish from time to time.\n"
        "ри́бу.\n",
    ),
}

SAMPLE_500_CHUNKS: dict[str, tuple[str, str, str]] = {
    "v0001": (
        "anna-ohoiko-500-verbs_e0001",
        "аналізува́ти | проаналізува́ти",
        "аналізува́ти | проаналізува́ти                                        Present / Future Stems: аналізу- | проаналізу-\n"
        "to analyze\n"
        "ОСОБА                          НЕДОКОНАНИЙ ВИД                                                 ДОКОНАНИЙ ВИД\n"
        "ТЕПЕРІШНІЙ ЧАС ― PRESENT TENSE\n"
        "я                   аналізу́ю\n"
        "ти                  аналізу́єш\n",
    ),
    "v0004": (
        "anna-ohoiko-500-verbs_e0004",
        "ба́чити [ся] | поба́чити [ся]",
        "ба́чити [ся] | поба́чити [ся]                                                               Present / Future Stems: бач- | побач-\n"
        "to see [to see each other, to meet]\n"
        "ОСОБА                                 НЕДОКОНАНИЙ ВИД                                                 ДОКОНАНИЙ ВИД\n"
        "ТЕПЕРІШНІЙ ЧАС ― PRESENT TENSE\n"
        "я                      ба́чу [ся]\n"
        "ти                     ба́чиш [ся]\n",
    ),
    "v0018": (
        "anna-ohoiko-500-verbs_e0018",
        "будува́ти | збудува́ти, побудува́ти",
        "будува́ти | збудува́ти, побудува́ти                                                  Present / Future Stems: буду- | збуду-\n"
        "to build\n"
        "ОСОБА                           НЕДОКОНАНИЙ ВИД                                                 ДОКОНАНИЙ ВИД\n"
        "ТЕПЕРІШНІЙ ЧАС ― PRESENT TENSE\n"
        "я                   буду́ю\n"
        "ти                  буду́єш\n",
    ),
    "v0277": (
        "anna-ohoiko-500-verbs_e0277",
        "об’єд",
        "об’єд\n"
        "to unite sth/sb [to come together, to unite]\n"
        "́ нувати [ся] | об’єдна́ти [ся]                                                Present / Future Stems: об’єдну- | об’єдна-\n"
        "ОСОБА                                    НЕДОКОНАНИЙ ВИД                                              ДОКОНАНИЙ ВИД\n"
        "ТЕПЕРІШНІЙ ЧАС ― PRESENT TENSE\n"
        "я                       об’єд́ ную [ся]\n",
    ),
    "v0341": (
        "anna-ohoiko-500-verbs_e0341",
        "поєд",
        "поєд\n"
        "to combine sth [to combine]\n"
        "́ нувати [ся] | поєдна́ти [ся]                                                Present / Future Stems: поєдну- | поєдна-\n"
        "ОСОБА                              НЕДОКОНАНИЙ ВИД                                                 ДОКОНАНИЙ ВИД\n"
        "ТЕПЕРІШНІЙ ЧАС ― PRESENT TENSE\n"
        "я                     поєд́ ную [ся]\n",
    ),
    "v0365": (
        "anna-ohoiko-500-verbs_e0365",
        "приєд",
        "приєд\n"
        "to add, to attach, to join sth [to join]\n"
        "́ нувати [ся] | приєдна́ти [ся]                                                  Present / Future Stems: приєдну- | приєдна-\n"
        "ОСОБА                                     НЕДОКОНАНИЙ ВИД                                                 ДОКОНАНИЙ ВИД\n"
        "ТЕПЕРІШНІЙ ЧАС ― PRESENT TENSE\n"
        "я                         приєд́ ную [ся]\n",
    ),
    "v0383": (
        "anna-ohoiko-500-verbs_e0383",
        "Present / Future Stems: прош-/прос- | попрош-/попрос-                                         проси́ти | попроси́ти",
        "Present / Future Stems: прош-/прос- | попрош-/попрос-                                         проси́ти | попроси́ти\n"
        "Conjugation: 2nd (-ять)                                                                                   to ask (for); to request\n"
        "ОСОБА                            НЕДОКОНАНИЙ ВИД                                                 ДОКОНАНИЙ ВИД\n"
        "ТЕПЕРІШНІЙ ЧАС ― PRESENT TENSE\n"
        "я                   прошу́\n",
    ),
}


# ---------------------------------------------------------------------------
# Tests: 1000-words Chunk Parser
# ---------------------------------------------------------------------------


def test_parse_1000_words_simple_entry() -> None:
    cid, title, text = SAMPLE_1000_CHUNKS["e0003"]
    parsed = parse_1000_words_chunk(cid, title, text)
    assert parsed.entry_number == 3
    assert parsed.locator == "ohoiko-1000-words entry 3"
    assert parsed.lemmas == ["автобус"]
    assert parsed.gloss == "bus"
    assert parsed.example is not None
    assert parsed.example["uk"] == "Сашко́ ї́здить в шко́лу авто́бусом."
    assert parsed.example["en"] == "Sashko goes to school by bus."
    assert parsed.example["source"] == "Anna Ohoiko"
    assert parsed.example["locator"] == "ohoiko-1000-words entry 3"


def test_parse_1000_words_paired_equal_headword() -> None:
    cid, title, text = SAMPLE_1000_CHUNKS["e0002"]
    parsed = parse_1000_words_chunk(cid, title, text)
    assert parsed.entry_number == 2
    assert parsed.lemmas == ["або", "чи"]
    assert parsed.gloss == "or"
    assert parsed.example == {
        "uk": "За́раз або́ ніко́ли.",
        "en": "Now or never.",
        "source": "Anna Ohoiko",
        "locator": "ohoiko-1000-words entry 2",
    }


def test_parse_1000_words_comma_pair_and_gender() -> None:
    cid, title, text = SAMPLE_1000_CHUNKS["e0006"]
    parsed = parse_1000_words_chunk(cid, title, text)
    assert parsed.entry_number == 6
    assert parsed.lemmas == ["актор", "акторка"]
    assert parsed.gloss == "actor, actress"
    assert parsed.example is not None
    assert parsed.example["uk"] == "Він хо́че ста́ти акто́ром."
    assert parsed.example["en"] == "He wants to become an actor."


def test_parse_1000_words_two_col_wrap_discount() -> None:
    cid, title, text = SAMPLE_1000_CHUNKS["e0007"]
    parsed = parse_1000_words_chunk(cid, title, text)
    assert parsed.entry_number == 7
    assert parsed.lemmas == ["акція"]
    assert parsed.gloss == "promotion (in sales)"
    assert parsed.example == {
        "uk": "У нас сього́дні а́кція — зни́жка 30%.",
        "en": "Today we have a promotion — a 30% discount.",
        "source": "Anna Ohoiko",
        "locator": "ohoiko-1000-words entry 7",
    }


def test_parse_1000_words_ocr_accent_split() -> None:
    cid, title, text = SAMPLE_1000_CHUNKS["e0352"]
    parsed = parse_1000_words_chunk(cid, title, text)
    assert parsed.entry_number == 352
    assert parsed.lemmas == ["клієнт", "клієнтка"]
    assert parsed.gloss == "client (male, female)"
    assert parsed.example is not None
    assert parsed.example["uk"] == "Ці лю́ди — мої́ кліє́нти."
    assert parsed.example["en"] == "These people are my clients."


def test_parse_1000_words_ocr_space_collapse_zabojatysja() -> None:
    cid, title, text = SAMPLE_1000_CHUNKS["e0047"]
    parsed = parse_1000_words_chunk(cid, title, text)
    assert parsed.entry_number == 47
    assert parsed.lemmas == ["боятися", "забоятися"]
    assert parsed.gloss == "to fear, to be afraid"
    assert parsed.example is not None
    assert parsed.example["uk"] == "Він бої́ться павукі́в."
    assert parsed.example["en"] == "He is afraid of spiders."


def test_parse_1000_words_vchytysia_entry_143() -> None:
    cid, title, text = SAMPLE_1000_CHUNKS["e0143"]
    parsed = parse_1000_words_chunk(cid, title, text)
    assert parsed.entry_number == 143
    assert parsed.lemmas == ["вчитися", "учитися", "навчатися", "навчитися"]
    assert parsed.gloss == "to study (somewhere or in a certain way), to learn"
    assert parsed.example is not None
    # Must NOT be the gloss fragment "навча́тися, навчи́тися" / "a certain way), to learn (imperfective, perfective)"
    assert parsed.example["uk"] == "Я мо́жу вчи́тися (навча́тися), ті́льки коли́ ти́хо."
    assert parsed.example["en"] == "I can study only when it is quiet."
    assert parsed.example["source"] == "Anna Ohoiko"
    assert parsed.example["locator"] == "ohoiko-1000-words entry 143"


def test_parse_1000_words_dzvonyty_entry_214() -> None:
    cid, title, text = SAMPLE_1000_CHUNKS["e0214"]
    parsed = parse_1000_words_chunk(cid, title, text)
    assert parsed.entry_number == 214
    assert parsed.lemmas == ["дзвонити", "задзвонити", "подзвонити"]
    assert parsed.gloss == "to ring; 2) to call, to give a call"
    assert parsed.example is not None
    # Must NOT be the gloss fragment "подзвони́ти (2)" / "2) to call, to give a call"
    assert parsed.example["uk"] == "У це́ркві дзво́нять дзво́ни."
    assert parsed.example["en"] == "Bells are ringing in the church."


def test_parse_1000_words_livoruch_entry_405() -> None:
    cid, title, text = SAMPLE_1000_CHUNKS["e0405"]
    parsed = parse_1000_words_chunk(cid, title, text)
    assert parsed.entry_number == 405
    assert parsed.lemmas == ["ліворуч", "зліва", "наліво"]
    assert parsed.gloss == "1) on the left, to the left; 2) left (direction)"
    assert parsed.example is not None
    # Must NOT be the gloss fragment "налі́во (2)" / "2) left (direction)"
    assert parsed.example["uk"] == "Ліво́руч (злі́ва) від Оле́ни — її́ син Наза́р."
    assert parsed.example["en"] == "To the left of Olena is her son Nazar."


def test_parse_1000_words_odruzhuvatysia_entry_543() -> None:
    cid, title, text = SAMPLE_1000_CHUNKS["e0543"]
    parsed = parse_1000_words_chunk(cid, title, text)
    assert parsed.entry_number == 543
    assert parsed.lemmas == ["одружуватися", "одружитися"]
    assert parsed.gloss == "1) to get married; 2) to marry a woman"
    assert parsed.example is not None
    # Must NOT be the gloss fragment "одружи́тися" / "2) to marry a woman"
    assert parsed.example["uk"] == "Бага́то пар одру́жуються влі́тку."
    assert parsed.example["en"] == "Many couples get married in the summer."


def test_parse_1000_words_pravoruch_entry_658() -> None:
    cid, title, text = SAMPLE_1000_CHUNKS["e0658"]
    parsed = parse_1000_words_chunk(cid, title, text)
    assert parsed.entry_number == 658
    assert parsed.lemmas == ["праворуч", "справа", "направо"]
    assert parsed.gloss == "1) on the right, to the right; 2) right (direction)"
    assert parsed.example is not None
    # Must NOT be the gloss fragment "напра́во (2)" / "2) right (direction)"
    assert parsed.example["uk"] == "Мій буди́нок право́руч (= спра́ва) від магази́ну."
    assert parsed.example["en"] == "My house is to the right of the shop."


# ---------------------------------------------------------------------------
# Tests: 500-verbs Chunk Parser
# ---------------------------------------------------------------------------


def test_parse_500_verbs_simple_pair() -> None:
    cid, title, text = SAMPLE_500_CHUNKS["v0001"]
    parsed = parse_500_verbs_chunk(cid, title, text)
    assert parsed.entry_number == 1
    assert parsed.locator == "ohoiko-500-verbs entry 1"
    assert parsed.lemmas == ["аналізувати", "проаналізувати"]
    assert parsed.gloss == "to analyze"
    assert parsed.example is None


def test_parse_500_verbs_reflexive_bracket() -> None:
    cid, title, text = SAMPLE_500_CHUNKS["v0004"]
    parsed = parse_500_verbs_chunk(cid, title, text)
    assert parsed.entry_number == 4
    assert parsed.lemmas == ["бачити", "бачитися", "побачити", "побачитися"]
    assert parsed.gloss == "to see [to see each other, to meet]"
    assert parsed.example is None


def test_parse_500_verbs_multiple_perfectives() -> None:
    cid, title, text = SAMPLE_500_CHUNKS["v0018"]
    parsed = parse_500_verbs_chunk(cid, title, text)
    assert parsed.entry_number == 18
    assert parsed.lemmas == ["будувати", "збудувати", "побудувати"]
    assert parsed.gloss == "to build"
    assert parsed.example is None


def test_parse_500_verbs_ocr_accent_wrapped_entry_277() -> None:
    cid, title, text = SAMPLE_500_CHUNKS["v0277"]
    parsed = parse_500_verbs_chunk(cid, title, text)
    assert parsed.entry_number == 277
    assert parsed.lemmas == ["об’єднувати", "об’єднуватися", "об’єднати", "об’єднатися"]
    assert parsed.gloss == "to unite sth/sb [to come together, to unite]"
    assert parsed.example is None


def test_parse_500_verbs_stems_first_entry_383() -> None:
    cid, title, text = SAMPLE_500_CHUNKS["v0383"]
    parsed = parse_500_verbs_chunk(cid, title, text)
    assert parsed.entry_number == 383
    assert parsed.lemmas == ["просити", "попросити"]
    assert parsed.gloss == "to ask (for); to request"
    assert parsed.example is None


# ---------------------------------------------------------------------------
# Tests: Plausibility Filter
# ---------------------------------------------------------------------------


def test_is_plausible_example_rejects_table_headers_and_fragments() -> None:
    # Grammar tags / table labels
    assert is_plausible_example("ОСОБА НЕДОКОНАНИЙ ВИД", "PRESENT TENSE") is False
    assert (
        is_plausible_example(
            "́ нувати [ся] | об’єдна́ти [ся]",
            "Present / Future Stems: об’єдну- | об’єдна-",
        )
        is False
    )
    assert (
        is_plausible_example(
            "навча́тися, навчи́тися",
            "a certain way), to learn (imperfective, perfective)",
        )
        is False
    )
    assert (
        is_plausible_example("подзвони́ти (2)", "2) to call, to give a call (imperfective, perfective)")
        is False
    )
    assert is_plausible_example("налі́во (2)", "2) left (direction)") is False
    assert is_plausible_example("одружи́тися", "2) to marry a woman") is False

    # Unbalanced parentheses / leftover brackets
    assert is_plausible_example("слово)", "word)") is False
    assert is_plausible_example("слово", "word]") is False
    assert is_plausible_example(") слово", ") word") is False

    # Empty / short / single words
    assert is_plausible_example("", "") is False
    assert is_plausible_example("автобус", "bus") is False


def test_is_plausible_example_accepts_valid_sentences() -> None:
    assert (
        is_plausible_example(
            "Сашко́ ї́здить в шко́лу авто́бусом.",
            "Sashko goes to school by bus.",
        )
        is True
    )
    assert (
        is_plausible_example(
            "У це́ркві дзво́нять дзво́ни.",
            "Bells are ringing in the church.",
        )
        is True
    )
    assert (
        is_plausible_example(
            "– Хто хо́че доба́вки? – Я!",
            "– Who wants more food? – Me!",
        )
        is True
    )


# ---------------------------------------------------------------------------
# Tests: Translation Duplicate Detection and Merging
# ---------------------------------------------------------------------------


def test_is_duplicate_sense_exact_and_subterms() -> None:
    assert is_duplicate_sense("to analyze", "to analyze") is True
    assert is_duplicate_sense("bus (vehicle)", "bus") is True
    assert is_duplicate_sense("bus, motorbus", "bus") is True
    assert is_duplicate_sense("coach (long-distance bus)", "bus") is False
    assert is_duplicate_sense("want (to desire)", "to wish, to desire") is False
    assert is_duplicate_sense("to desire, to want, to wish", "to wish, to desire") is True


def test_merge_translation_preserves_distinct_prior_senses() -> None:
    prior = {
        "en": ["bus (vehicle)", "bus, motorbus", "coach (long-distance bus)"],
        "source": "dmklinger",
        "pos": "noun",
    }
    merged = merge_translation(prior, "bus")
    assert merged["source"] == "learner_english_gloss"
    assert merged["en"] == ["bus", "coach (long-distance bus)"]
    assert merged["pos"] == "noun"


def test_merge_translation_empty_prior() -> None:
    merged = merge_translation(None, "agriculture")
    assert merged == {"en": ["agriculture"], "source": "learner_english_gloss"}


# ---------------------------------------------------------------------------
# Tests: Examples Merging
# ---------------------------------------------------------------------------


def test_merge_examples_dedup_and_cap() -> None:
    ex1 = {
        "uk": "Сашко́ ї́здить в шко́лу авто́бусом.",
        "en": "Sashko goes to school by bus.",
        "source": "Anna Ohoiko",
        "locator": "ohoiko-1000-words entry 3",
    }
    ex2 = {
        "uk": "Сашко́ ї́здить в шко́лу авто́бусом.",
        "en": "Sashko goes to school by bus.",
        "source": "Anna Ohoiko",
        "locator": "ohoiko-1000-words entry 3",
    }
    ex3 = {
        "uk": "Він ї́де авто́бусом.",
        "en": "He rides a bus.",
        "source": "Anna Ohoiko",
        "locator": "ohoiko-1000-words entry 3",
    }
    ex4 = {
        "uk": "Авто́бус запі́знюється.",
        "en": "The bus is late.",
        "source": "Anna Ohoiko",
        "locator": "ohoiko-1000-words entry 3",
    }
    res = merge_examples([ex1], [ex2, ex3, ex4])
    assert len(res) == 2
    assert res[0]["uk"] == ex2["uk"]
    assert res[1]["uk"] == ex3["uk"]


def test_merge_examples_rejects_implausible_pairs() -> None:
    bad1 = {
        "uk": "навча́тися, навчи́тися",
        "en": "a certain way), to learn (imperfective, perfective)",
        "source": "Anna Ohoiko",
    }
    bad2 = {
        "uk": "́ нувати [ся] | об’єдна́ти [ся]",
        "en": "Present / Future Stems: об’єдну- | об’єдна-",
        "source": "Anna Ohoiko",
    }
    good = {
        "uk": "Сашко́ ї́здить в шко́лу авто́бусом.",
        "en": "Sashko goes to school by bus.",
        "source": "Anna Ohoiko",
    }
    # Prior has bad1, new has bad2 and good
    merged = merge_examples([bad1], [bad2, good])
    assert len(merged) == 1
    assert merged[0]["uk"] == good["uk"]
    assert merged[0]["en"] == good["en"]


# ---------------------------------------------------------------------------
# Tests: Enrichment on Stub Manifest Entries
# ---------------------------------------------------------------------------


def test_enrich_entry_with_ohoiko_updates_sources() -> None:
    entry: dict[str, Any] = {
        "lemma": "автобус",
        "enrichment": {
            "sources": ["VESUM"],
            "translation": {"en": ["bus, motorbus"], "source": "dmklinger"},
        },
    }
    example = {
        "uk": "Сашко́ ї́здить в шко́лу авто́бусом.",
        "en": "Sashko goes to school by bus.",
        "source": "Anna Ohoiko",
        "locator": "ohoiko-1000-words entry 3",
    }
    changed = enrich_entry_with_ohoiko(entry, anna_gloss="bus", anna_example=example)
    assert changed is True
    enr = entry["enrichment"]
    assert enr["translation"]["en"] == ["bus"]
    assert enr["translation"]["source"] == "learner_english_gloss"
    assert len(enr["examples"]) == 1
    assert "Anna Ohoiko" in enr["sources"]
    assert "learner_english_gloss" in enr["sources"]
    assert "VESUM" in enr["sources"]


# ---------------------------------------------------------------------------
# Tests: All 9 #7397 Ohoiko Heads Enriched
# ---------------------------------------------------------------------------


def test_all_9_heads_7397_enriched_from_chunks() -> None:
    # Build stub manifest with the 9 #7397 lemmas
    stub_entries = [{"lemma": h, "enrichment": None} for h in sorted(HEADS_7397)]
    manifest = {"entries": stub_entries}

    parsed_1000 = [
        parse_1000_words_chunk(cid, title, text)
        for cid, (cid_full, title, text) in SAMPLE_1000_CHUNKS.items()
    ]
    parsed_500 = [
        parse_500_verbs_chunk(cid, title, text)
        for cid, (cid_full, title, text) in SAMPLE_500_CHUNKS.items()
    ]

    stats = apply_ohoiko_quality_enrichment(
        manifest,
        parsed_1000=parsed_1000,
        parsed_500=parsed_500,
    )

    assert stats["heads_7397_enriched"] == len(HEADS_7397)

    by_lemma = {e["lemma"]: e for e in manifest["entries"]}
    for h in HEADS_7397:
        e = by_lemma[h]
        enr = e.get("enrichment")
        assert enr is not None, f"Enrichment missing for {h}"
        assert enr.get("translation") is not None, f"Translation missing for {h}"
        assert enr["translation"]["source"] == "learner_english_gloss"
        assert len(enr["translation"]["en"]) >= 1
        assert enr.get("examples") is not None, f"Examples missing for {h}"
        assert len(enr["examples"]) >= 1
        assert enr["examples"][0]["source"] == "Anna Ohoiko"
        assert "Anna Ohoiko" in enr["sources"]
        assert "learner_english_gloss" in enr["sources"]
