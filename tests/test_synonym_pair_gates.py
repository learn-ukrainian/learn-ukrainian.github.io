"""Synonym-pair emission gates (#8714).

A synonym card ships only on ULIF synonym-dictionary evidence: the two words
are the dominant and an unmarked member of one sense cluster of a checked
ULIF group, and the dominant's note is the displayed sense.  Aspect pairs,
reflexive and spelling variants, gender counterparts, motion-verb pairs and
different-POS pairs never ship.  Every candidate direction that does not
ship is listed once, with one reason.

ULIF rows below are excerpts of real checked groups from ``sources.db``
(links removed, members elided) unless marked as a fixture row.
"""

from __future__ import annotations

import json
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.audit.generate_practice_deck import (
    BuildConfig,
    JsonVesumVerifier,
    ReviewedSourceAllowlist,
    build_practice_shards,
    read_ulif_synonym_groups,
    validate_mode_items,
    validate_synonym_option_sets,
)
from scripts.practice.ulif_synonym_groups import (
    UlifSynonymDataUnavailable,
    UlifSynonymGroups,
    payload_from_row_html,
)

SYNONYM_VERDICTS_YAML = PROJECT_ROOT / "registry" / "lexicon" / "synonym_pair_verdicts.yaml"

ZANEPAD = (
    "<b>ЗАНЕ́ПАД</b> (погіршення загального стану, зниження рівня розвитку), <b>РЕГРЕ́С</b>, "
    "<b>ДЕГРАДА́ЦІЯ</b>, <b>ДЕПРЕ́СІЯ</b>, <b>ЗАНЕПА́ДОК</b> <i>заст.; </i> <b>ПІДУПА́Д</b> <i>рідше</i> "
    "(у дещо меншій мірі); <b>ДЕКАДА́НС</b> <i>книжн.</i> (у мистецтві, літературі і т. п.); <b>РО́ЗКЛАД</b> "
    "(у суспільстві, моралі тощо)."
)
ISTY = (
    "<b>Ї́СТИ</b> (приймати їжу), <b>СПОЖИВА́ТИ</b>, <b>ЗАЖИВА́ТИ</b>, <b>КУСА́ТИ</b> <i>розм.,</i> "
    "<b>ЖУВА́ТИ</b> <i>розм.,</i> <i>ірон.,</i> <b>РУБА́ТИ</b> <i>розм.,</i> <b>ТЬО́ПАТИ</b> <i>розм.</i>. "
    "- Док.: <b>з'ї́сти</b>, <b>спожи́ти</b>, <b>укуси́ти</b> <b>[вкуси́ти]</b>, <b>зжува́ти</b>."
)
KOPATY = (
    "<b>КОПА́ТИ</b> (лопатою, заступом тощо робити заглиблення в землі, снігу і т. ін.; видобувати щось із "
    "землі, снігу тощо), <b>РИ́ТИ</b>, <b>ВИКО́ПУВАТИ</b>, <b>ВИРИВА́ТИ</b>, <b>ВИБИРА́ТИ</b> (видобувати із "
    "землі вирощену картоплю); <b>КОПА́ТИСЯ</b> (робити заглиблення в землі).  - Док.: <b>ви́копати</b>, "
    "<b>ви́рити</b>, <b>ви́брати</b>."
)
SHTOVKHNUTY = (
    "<b>ШТОВХНУ́ТИ</b> (коротким різким рухом торкнутися когось, чогось), <b>ШТОВХОНУ́ТИ</b>, <b>ПХНУ́ТИ</b>, "
    "<b>ТУРНУ́ТИ</b> <i>розм.,</i> <b>СУНУ́ТИ</b> <i>розм.,</i> <b>СОВМАНУ́ТИ</b> <i>діал.;</i> <b>КО́ПНУТИ</b> "
    "(ногою); <b>ПІДШТОВХНУ́ТИ</b>, <b>ТОРКНУ́ТИ</b> (злегка)."
)
DUZHE = (
    "<b>ДУ́ЖЕ</b> (великою мірою), <b>НЕМА́ЛО</b>, <b>ЗНА́ЧНО</b>, <b>ЧИМА́ЛО</b>; <b>НЕДОСЯ́ЖНО</b>, "
    "<b>ТРИ́ЧІ</b> <i>розм.</i> (указує на дуже високий ступінь ознаки); <b>НАБАГА́ТО</b>, <b>ДАЛЕ́КО</b> "
    "(при вищому ступені прикметників і прислівників)."
)
MOVA = (
    "<b>МО́ВА</b> (здатність людини говорити, висловлювати свої думки; манера говорити), <b>ЯЗИ́К</b> "
    "<i>заст.,</i> <b>РІЧ</b> <i>розм.,</i> <b>СЛО́ВО</b> <i>розм.,</i> <b>ГЛАГО́Л</b> <i>ц.-с.;</i> "
    "<b>МО́ВЛЕННЯ</b>, <b>БЕ́СІДА</b> <i>діал.</i> (спілкування людей між собою за допомогою органів говоріння)."
)
ITY = (
    "<b>ІТИ́</b> <b>[ЙТИ]</b> (про дощ, сніг), <b>ПА́ДАТИ</b>, <b>ВИПАДА́ТИ</b> (час від часу); <b>ПОРОШИ́ТИ</b>, "
    "<b>МОТРОШИ́ТИ</b> <i>розм.</i> (перев. про сніг); <b>ДОЩИ́ТИ</b> <i>розм.</i> (про дощ - безперервно). "
    "- Док.: <b>піти́</b>, <b>ви́пасти</b>."
)
SPYSOK = (
    "<b>СПИ́СОК</b> (опис з перерахуванням яких-небудь осіб або предметів), <b>РЕЄСТР</b>, <b>ПЕРЕ́ЛІК</b>, "
    "<b>ПРЕЙСКУРА́НТ</b>, <b>ІНДЕКС</b>, <b>РЕГІ́СТР</b> <i>спец.; </i> <b>КАТАЛО́Г</b> (перелік книжок, "
    "рукописів, картин тощо, складений у певному порядку)."
)
# Filed under НЕСАМОВИ́ТІСТЬ, ЛЮТЬ, ШАЛ and ten more headwords, never under a checked ГНІВ entry;
# ГНІВ is one of its terms only through the closing "Пор." cross-reference.
NESAMOVYTIST = (
    "<p><b>НЕСАМОВИ́ТІСТЬ</b> (стан несамовитої людини); <b>ШАЛ</b>, <b>ШАЛЕ́НСТВО</b>, <b>ШАЛЕ́НІСТЬ</b>, "
    "<b>РАЖ</b> <i>розм. рідко</i> (від збудження, роздратування, гніву тощо). <i>Щезла свідомість. Повна "
    "нестяма. Шаленість</i> (М. Коцюбинський). - Пор. <b>гнів</b>, <b>лють</b>, 1. <b>нестя́ма</b>.</p>"
)
OBLYCHCHIA = (
    "<b>ОБЛИ́ЧЧЯ</b> (передня частина голови людини), <b>ЛИЦЕ́</b>, <b>ВИД</b>, <b>О́БРАЗ</b> <i>розм.,</i> "
    "<b>ЛИК</b> <i>поет., заст.</i>."
)
MAISTER = (
    "<b>МА́ЙСТЕР</b> (той, хто досяг високої майстерності, досконалості в своїй роботі, творчості), "
    "<b>ВІРТУО́З</b>, <b>МИТЕ́ЦЬ</b>, <b>МАСТА́К</b> <i>розм.;</i> <b>УМІ́ЛЕЦЬ</b> <b>[ВМІ́ЛЕЦЬ]</b> "
    "(той, хто досяг найбільшої вмілості в чомусь)."
)
VIDNOVLIUVATYSIA = (
    "<b>ВІДНО́ВЛЮВАТИСЯ</b> (про думки, почуття тощо - появлятися знову, виявлятися з новою силою), "
    "<b>ВІДНОВЛЯ́ТИСЯ</b>, <b>ОЖИВА́ТИ</b>, <b>ПОВЕРТА́ТИ</b>, <b>ПОВЕРТА́ТИСЯ</b>. - Док.: <b>віднови́тися</b>, "
    "<b>ожи́ти</b>, <b>поверну́ти</b>, <b>поверну́тися</b>."
)


def _fixture_row(dominant: str, *members: str) -> str:
    """A synthetic core row (not ULIF text): the dominant with a fixture note and plain members."""
    return (
        ", ".join([f"<b>{dominant.upper()}</b> (fixture)", *(f"<b>{member.upper()}</b>" for member in members)]) + "."
    )


def _ulif(*rows: str) -> UlifSynonymGroups:
    return UlifSynonymGroups.from_payloads(payload_from_row_html(row) for row in rows)


def _entry(
    lemma: str,
    pos: str,
    gloss: str,
    *,
    en: list[str] | None = None,
    level: str = "B1",
    aspect_partner: str | None = None,
) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "lemma": lemma,
        "url_slug": lemma,
        "gloss": gloss,
        "pos": pos,
        "primary_source": "course_vocab",
        "course_usage": [{"track": level.lower(), "slug": f"{level.lower()}-synonyms"}],
        "enrichment": {
            "cefr": {"level": level},
            "translation": {"en": list(en) if en is not None else [gloss], "source": "fixture", "pos": pos},
        },
    }
    if aspect_partner:
        entry["enrichment"]["verb_pedagogy"] = {"aspect_partner": {"lemma": aspect_partner, "source": "fixture"}}
    return entry


_NOUN_FILLERS = [
    _entry("книга", "noun", "book"),
    _entry("стіл", "noun", "table"),
    _entry("вікно", "noun", "window"),
    _entry("місто", "noun", "city"),
    _entry("ріка", "noun", "river"),
]
_VERB_FILLERS = [
    _entry("читати", "verb", "read", en=["to read"]),
    _entry("писати", "verb", "write", en=["to write"]),
    _entry("спати", "verb", "sleep", en=["to sleep"]),
    _entry("малювати", "verb", "draw", en=["to draw"]),
]
_PERF_VERB_FILLERS = [
    _entry("прочитати", "verb", "read", en=["to read through"]),
    _entry("написати", "verb", "write", en=["to write down"]),
    _entry("заснути", "verb", "fall asleep", en=["to fall asleep"]),
    _entry("намалювати", "verb", "draw", en=["to draw up"]),
]
_ADJ_FILLERS = [
    _entry("старий", "adj", "old"),
    _entry("новий", "adj", "new"),
    _entry("чистий", "adj", "clean"),
    _entry("теплий", "adj", "warm"),
]
_ADV_FILLERS = [
    _entry("повільно", "adverb", "slowly"),
    _entry("тихо", "adverb", "quietly"),
    _entry("голосно", "adverb", "loudly"),
    _entry("рано", "adverb", "early"),
]
_CONJ_FILLERS = [
    _entry("щоб", "conj", "so that"),
    _entry("ніж", "conj", "than"),
    _entry("поки", "conj", "while"),
    _entry("бо", "conj", "because"),
    _entry("якщо", "conj", "if"),
]

_IMPERF = [
    "кидати",
    "жбурляти",
    "вітати",
    "вітатися",
    "говорити",
    "базікати",
    "балакати",
    "читати",
    "писати",
    "спати",
    "малювати",
    "рити",
    "вибирати",
    "рубати",
    "дощити",
    "падати",
    "носити",
    "нести",
    "відновлюватися",
    "повертати",
]
_PERF = ["кинути", "сунути", "копнути", "вкусити", "прочитати", "написати", "заснути", "намалювати"]
_VESUM_VERBS = {
    **{verb: [{"lemma": verb, "pos": "verb", "tags": "verb:imperf:inf"}] for verb in _IMPERF},
    **{verb: [{"lemma": verb, "pos": "verb", "tags": "verb:perf:inf"}] for verb in _PERF},
    # Person nouns: the gender-counterpart rule needs VESUM animacy and gender.
    "кравець": [{"lemma": "кравець", "pos": "noun", "tags": "noun:anim:m:v_naz"}],
    "кравчиня": [{"lemma": "кравчиня", "pos": "noun", "tags": "noun:anim:f:v_naz"}],
    "буханець": [{"lemma": "буханець", "pos": "noun", "tags": "noun:inanim:m:v_naz"}],
    "буханка": [{"lemma": "буханка", "pos": "noun", "tags": "noun:inanim:f:v_naz"}],
}

_WITHHELD = re.compile(r"^WITHHELD synonym direction \[(\w+)\] (.+?) → (.+?) \((\w+)\): (\w+)$")
_SUMMARY = re.compile(r"^synonym directions \(#8714\): candidates=(\d+) emitted=(\d+) withheld=(\d+)")


def _approved(a: str, b: str, *, sources: list[str] | None = None, polarity: str = "synonym") -> dict[str, Any]:
    return {"a": a, "b": b, "polarity": polarity, "sources": ["synonyms"] if sources is None else sources}


def _build(
    capsys: pytest.CaptureFixture[str],
    manifest: list[dict[str, Any]],
    approved: list[dict[str, Any]],
    ulif: UlifSynonymGroups | None,
    *,
    rejected: list[dict[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], dict[tuple[str, str], str], tuple[int, int, int]]:
    """Synonym items, withheld ledger ``{(prompt, target): reason}`` and (candidates, emitted, withheld)."""
    capsys.readouterr()
    shards = build_practice_shards(
        manifest,
        ReviewedSourceAllowlist.from_payload([]),
        JsonVesumVerifier(_VESUM_VERBS),
        cloze_sources=None,
        config=BuildConfig(target=200),
        synonym_verdicts={"approved": approved, "rejected": rejected or []},
        ulif_synonym_groups=ulif,
    )
    err = capsys.readouterr().err.splitlines()
    ledger: dict[tuple[str, str], str] = {}
    for line in err:
        match = _WITHHELD.match(line)
        if match:
            key = (match.group(2), match.group(3))
            assert key not in ledger, f"direction recorded twice: {key}"
            ledger[key] = match.group(5)
    summary = next(tuple(int(value) for value in m.groups()) for m in map(_SUMMARY.match, err) if m)
    items = [item for level in shards for item in shards[level].get("synonym", {}).get("synonym", [])]
    return items, ledger, summary  # type: ignore[return-value]


def _pairs(items: list[dict[str, Any]]) -> set[tuple[str, str]]:
    return {(item["prompt"], item["answer"]) for item in items}


@pytest.mark.parametrize(
    ("prompt", "target", "manifest", "rows", "reason"),
    [
        # Issue example syn_47451f934c94: one ULIF row, but декаданс/розклад sit in later clusters.
        (
            "депресія",
            "розклад",
            [_entry("депресія", "noun", "depression"), _entry("розклад", "noun", "schedule"), *_NOUN_FILLERS],
            [ZANEPAD],
            "ulif_not_core_pair",
        ),
        # тільки → трохи: no ULIF group lists both.
        (
            "тільки",
            "трохи",
            [_entry("тільки", "adverb", "only"), _entry("трохи", "adverb", "a little"), *_ADV_FILLERS],
            [ZANEPAD],
            "not_in_ulif_group",
        ),
        # вкусити → рубати: рубати is a розм. member of ЇСТИ, вкусити a perfective; aspects differ first.
        (
            "вкусити",
            "рубати",
            [_entry("вкусити", "verb", "bite", en=["to bite"]), _entry("рубати", "verb", "chop"), *_VERB_FILLERS],
            [ISTY],
            "aspect_pair",
        ),
        # рити → вибирати: вибирати carries its own narrower note (картопля).
        (
            "рити",
            "вибирати",
            [_entry("рити", "verb", "dig"), _entry("вибирати", "verb", "choose"), *_VERB_FILLERS],
            [KOPATY],
            "ulif_not_core_pair",
        ),
        # сунути → копнути: сунути is розм., копнути a later cluster (ногою).
        (
            "сунути",
            "копнути",
            [_entry("сунути", "verb", "shove"), _entry("копнути", "verb", "kick"), *_PERF_VERB_FILLERS],
            [SHTOVKHNUTY],
            "ulif_not_core_pair",
        ),
        # Gemini review: далеко → набагато, глагол → річ, дощити → падати.
        (
            "далеко",
            "набагато",
            [_entry("далеко", "adverb", "far"), _entry("набагато", "adverb", "much"), *_ADV_FILLERS],
            [DUZHE],
            "ulif_not_core_pair",
        ),
        (
            "глагол",
            "річ",
            [_entry("глагол", "noun", "word (archaic)"), _entry("річ", "noun", "thing"), *_NOUN_FILLERS],
            [MOVA],
            "ulif_not_core_pair",
        ),
        (
            "дощити",
            "падати",
            [_entry("дощити", "verb", "drizzle"), _entry("падати", "verb", "fall"), *_VERB_FILLERS],
            [ITY],
            "ulif_not_core_pair",
        ),
        # Gemini review: кравець → кравчиня and носити → нести never ship, even on a core fixture row.
        (
            "кравець",
            "кравчиня",
            [_entry("кравець", "noun", "tailor"), _entry("кравчиня", "noun", "seamstress"), *_NOUN_FILLERS],
            [_fixture_row("кравець", "кравчиня")],
            "gender_counterpart",
        ),
        (
            "носити",
            "нести",
            [_entry("носити", "verb", "carry"), _entry("нести", "verb", "carry"), *_VERB_FILLERS],
            [_fixture_row("нести", "носити")],
            "motion_verb_pair",
        ),
    ],
)
def test_quoted_wrong_pair_is_withheld_in_both_directions(
    capsys: pytest.CaptureFixture[str],
    prompt: str,
    target: str,
    manifest: list[dict[str, Any]],
    rows: list[str],
    reason: str,
) -> None:
    items, ledger, _summary = _build(capsys, manifest, [_approved(prompt, target)], _ulif(*rows))
    assert _pairs(items) == set(), _pairs(items)
    assert ledger == {(prompt, target): reason, (target, prompt): reason}


def test_review_rejected_core_pairs_are_rejected_verdicts() -> None:
    # These pairs are dominant + plain member in a real ULIF row, so the dictionary gate
    # admits them; the #8714 language review rejected them for learners, and the
    # adjudication lives in the verdict registry.
    data = yaml.safe_load(SYNONYM_VERDICTS_YAML.read_text(encoding="utf-8"))

    def keys(section: str) -> set[tuple[str, str, str]]:
        return {(*sorted((item["a"], item["b"])), item["polarity"]) for item in data[section]}

    rejected, approved = keys("rejected"), keys("approved")
    reviewed = [
        ("обличчя", "вид"),
        ("далеко", "набагато"),
        ("чверть", "квартал"),
        ("глагол", "річ"),
        ("дощити", "падати"),
        ("відновлюватися", "повертати"),
        ("кравець", "кравчиня"),
        ("носити", "нести"),
        ("розповідь", "переказ"),
        ("митець", "майстер"),
        ("депресія", "розклад"),
        ("тільки", "трохи"),
        ("вкусити", "рубати"),
        ("рити", "вибирати"),
        ("сунути", "копнути"),
        ("індекс", "список"),
    ]
    for a, b in reviewed:
        key = (*sorted((a, b)), "synonym")
        assert key in rejected and key not in approved, key


def test_rejected_verdict_overrides_ulif_core_evidence(capsys: pytest.CaptureFixture[str]) -> None:
    manifest = [
        _entry("індекс", "noun", "index"),
        _entry("список", "noun", "list"),
        _entry("обличчя", "noun", "face"),
        _entry("вид", "noun", "kind"),
        *_NOUN_FILLERS,
    ]
    ulif = _ulif(SPYSOK, OBLYCHCHIA)
    approved = [_approved("індекс", "список"), _approved("обличчя", "вид")]
    admitted, _ledger, _summary = _build(capsys, manifest, approved, ulif)
    assert ("список", "індекс") in _pairs(admitted) and ("обличчя", "вид") in _pairs(admitted)
    rejected = [{**record, "reason": "fixture"} for record in approved]
    items, ledger, summary = _build(capsys, manifest, approved, ulif, rejected=rejected)
    assert items == [] and ledger == {} and summary == (0, 0, 0)


@pytest.mark.parametrize(
    ("rows", "a", "b", "manifest"),
    [
        (
            [MAISTER],
            "майстер",
            "митець",
            [_entry("майстер", "noun", "master"), _entry("митець", "noun", "artist"), *_NOUN_FILLERS],
        ),
        (
            [VIDNOVLIUVATYSIA],
            "відновлюватися",
            "повертати",
            [_entry("відновлюватися", "verb", "recover"), _entry("повертати", "verb", "return"), *_VERB_FILLERS],
        ),
    ],
)
def test_review_rejected_pairs_are_dictionary_core_pairs(
    capsys: pytest.CaptureFixture[str], rows: list[str], a: str, b: str, manifest: list[dict[str, Any]]
) -> None:
    # Documents why the registry rejection is needed: ULIF alone admits these.
    items, _ledger, _summary = _build(capsys, manifest, [_approved(a, b)], _ulif(*rows))
    assert (a, b) in _pairs(items)


def test_core_pair_ships_with_ulif_sense_and_evidence(capsys: pytest.CaptureFixture[str]) -> None:
    manifest = [_entry("список", "noun", "list"), _entry("перелік", "noun", "list, enumeration"), *_NOUN_FILLERS]
    items, ledger, summary = _build(capsys, manifest, [_approved("список", "перелік")], _ulif(SPYSOK))
    assert _pairs(items) == {("список", "перелік"), ("перелік", "список")}
    assert ledger == {} and summary == (2, 2, 0)
    for item in items:
        assert item["source"] == "ulif-synonyms"
        assert item["sense"] == "опис з перерахуванням яких-небудь осіб або предметів"
        assert item["evidence"]["dominant"] == "список"
        assert item["evidence"]["url"] == "https://lcorp.ulif.org.ua/dictua"
        assert len(item["evidence"]["groupId"]) == 16


def test_prompt_without_ulif_group_never_ships(capsys: pytest.CaptureFixture[str]) -> None:
    # Gemini review: одначе is also correct for зате; ULIF has no synonym row for зате yet.
    manifest = [_entry("зате", "conj", "but, on the other hand"), _entry("одначе", "conj", "but, however")]
    items, ledger, _summary = _build(capsys, [*manifest, *_CONJ_FILLERS], [_approved("зате", "одначе")], _ulif(SPYSOK))
    assert items == []
    assert ledger == {("зате", "одначе"): "not_in_ulif_group", ("одначе", "зате"): "not_in_ulif_group"}


def test_distractor_never_shares_a_ulif_group_with_prompt_or_answer(capsys: pytest.CaptureFixture[str]) -> None:
    manifest = [
        _entry("список", "noun", "list"),
        _entry("перелік", "noun", "enumeration"),
        _entry("реєстр", "noun", "register"),
        _entry("каталог", "noun", "catalogue"),
        _entry("регістр", "noun", "register (technical)"),
        *_NOUN_FILLERS,
    ]
    items, _ledger, _summary = _build(capsys, manifest, [_approved("список", "перелік")], _ulif(SPYSOK))
    assert items
    for item in items:
        distractors = {option["label"] for option in item["options"] if option["kind"] == "distractor"}
        assert distractors.isdisjoint({"реєстр", "каталог", "регістр"}), distractors


def test_ledger_partitions_candidate_directions(capsys: pytest.CaptureFixture[str]) -> None:
    manifest = [
        _entry("список", "noun", "list"),
        _entry("перелік", "noun", "enumeration"),
        _entry("депресія", "noun", "depression"),
        _entry("розклад", "noun", "schedule"),
        _entry("великий", "adj", "big"),
        _entry("величезний", "adj", "huge"),
        *_NOUN_FILLERS,
    ]
    approved = [_approved("список", "перелік"), _approved("депресія", "розклад"), _approved("великий", "величезний")]
    ulif = _ulif(SPYSOK, ZANEPAD, _fixture_row("великий", "величезний"))
    items, ledger, summary = _build(capsys, manifest, approved, ulif)
    candidates, emitted, withheld = summary
    assert (candidates, emitted, withheld) == (6, 2, 4)
    assert emitted == len(items) and withheld == len(ledger)
    assert _pairs(items).isdisjoint(ledger)
    assert ledger == {
        ("депресія", "розклад"): "ulif_not_core_pair",
        ("розклад", "депресія"): "ulif_not_core_pair",
        # No other adjective in the deck: the pair is admitted but cannot be drilled.
        ("великий", "величезний"): "insufficient_distractors",
        ("величезний", "великий"): "insufficient_distractors",
    }


def test_aspect_pair_is_withheld_but_same_aspect_synonym_ships(capsys: pytest.CaptureFixture[str]) -> None:
    # Issue example syn_542704e10746: кидати → кинути (perfective partner, not a synonym).
    manifest = [
        _entry("кидати", "verb", "throw", en=["to throw"], aspect_partner="кинути"),
        _entry("кинути", "verb", "throw", en=["to throw"], aspect_partner="кидати"),
        _entry("жбурляти", "verb", "hurl", en=["to hurl"]),
        *_VERB_FILLERS,
    ]
    ulif = _ulif(_fixture_row("кидати", "кинути", "жбурляти"))
    items, ledger, _summary = _build(
        capsys, manifest, [_approved("кидати", "кинути"), _approved("кидати", "жбурляти")], ulif
    )
    assert ("кидати", "жбурляти") in _pairs(items)
    assert ledger[("кидати", "кинути")] == ledger[("кинути", "кидати")] == "aspect_pair"


def test_aspect_pair_is_withheld_on_vesum_tags_alone(capsys: pytest.CaptureFixture[str]) -> None:
    manifest = [
        _entry("кидати", "verb", "throw", en=["to throw"]),
        _entry("кинути", "verb", "throw", en=["to throw"]),
        *_VERB_FILLERS,
    ]
    items, ledger, _summary = _build(
        capsys, manifest, [_approved("кидати", "кинути")], _ulif(_fixture_row("кидати", "кинути"))
    )
    assert items == [] and set(ledger.values()) == {"aspect_pair"}


@pytest.mark.parametrize(
    ("a", "b", "manifest", "reason"),
    [
        # вітатися → вітати (reflexive/active pair with different meanings).
        (
            "вітати",
            "вітатися",
            [_entry("вітати", "verb", "greet"), _entry("вітатися", "verb", "say hello"), *_VERB_FILLERS],
            "reflexive_pair",
        ),
        # високий (adj) → високо (adverb).
        (
            "високий",
            "високо",
            [_entry("високий", "adj", "high, tall"), _entry("високо", "adverb", "high"), *_ADJ_FILLERS],
            "pos_mismatch",
        ),
        # учитель → вчитель is an euphonic spelling variant, not a synonym.
        (
            "учитель",
            "вчитель",
            [_entry("учитель", "noun", "teacher"), _entry("вчитель", "noun", "teacher"), *_NOUN_FILLERS],
            "spelling_variant",
        ),
    ],
)
def test_structural_gate_wins_over_dictionary_evidence(
    capsys: pytest.CaptureFixture[str], a: str, b: str, manifest: list[dict[str, Any]], reason: str
) -> None:
    items, ledger, _summary = _build(capsys, manifest, [_approved(a, b)], _ulif(_fixture_row(a, b)))
    assert items == []
    assert ledger == {(a, b): reason, (b, a): reason}


def test_gender_counterpart_needs_animate_person_nouns(capsys: pytest.CaptureFixture[str]) -> None:
    # буханець / буханка share a stem and a -ка ending but are inanimate: not a gender pair,
    # so only the dictionary evidence decides (a fixture core row admits it here).
    manifest = [_entry("буханець", "noun", "small loaf"), _entry("буханка", "noun", "loaf"), *_NOUN_FILLERS]
    items, ledger, _summary = _build(
        capsys, manifest, [_approved("буханець", "буханка")], _ulif(_fixture_row("буханка", "буханець"))
    )
    assert _pairs(items) == {("буханець", "буханка"), ("буханка", "буханець")} and ledger == {}


def test_distractor_is_never_an_accepted_synonym_of_the_prompt(capsys: pytest.CaptureFixture[str]) -> None:
    # Issue example syn_0bd5164f658d: але → одначе offered проте and однак as distractors,
    # although both are accepted answers for але elsewhere in the same deck.
    manifest = [
        _entry("але", "conj", "but"),
        _entry("одначе", "conj", "but, however"),
        _entry("проте", "conj", "however, but"),
        _entry("однак", "conj", "however", en=["however, but"]),
        *_CONJ_FILLERS,
    ]
    ulif = _ulif(_fixture_row("але", "одначе", "проте", "однак"))
    approved = [_approved("але", "одначе"), _approved("але", "проте"), _approved("але", "однак")]
    items, _ledger, _summary = _build(capsys, manifest, approved, ulif)
    but_items = [item for item in items if item["prompt"] == "але"]
    assert {item["answer"] for item in but_items} == {"одначе", "проте", "однак"}
    for item in but_items:
        distractors = {option["label"] for option in item["options"] if option["kind"] == "distractor"}
        assert distractors.isdisjoint({"одначе", "проте", "однак"}), (item["answer"], distractors)
    assert validate_synonym_option_sets(items) == []


def test_distractor_sharing_an_english_sense_with_the_prompt_is_excluded(capsys: pytest.CaptureFixture[str]) -> None:
    # балакати is in no ULIF row here, yet it shares the sense "to talk"; it must not be
    # marked wrong as a distractor.
    manifest = [
        _entry("говорити", "verb", "speak, talk", en=["to speak", "to talk"]),
        _entry("базікати", "verb", "chatter, talk", en=["to chatter", "to talk"]),
        _entry("балакати", "verb", "talk, chat", en=["to talk", "to chat"]),
        *_VERB_FILLERS,
    ]
    ulif = _ulif(_fixture_row("говорити", "базікати"))
    items, _ledger, _summary = _build(capsys, manifest, [_approved("говорити", "базікати")], ulif)
    assert ("говорити", "базікати") in _pairs(items), _pairs(items)
    for item in items:
        distractors = {option["label"] for option in item["options"] if option["kind"] == "distractor"}
        assert "балакати" not in distractors, (item["prompt"], item["answer"], distractors)


def test_antonym_pair_needs_a_dictionary_source_not_ulif(capsys: pytest.CaptureFixture[str]) -> None:
    manifest = [_entry("швидко", "adverb", "quickly"), _entry("повільно", "adverb", "slowly"), *_ADV_FILLERS[1:]]
    manifest.append(_entry("далеко", "adverb", "far"))
    dictionary = [_approved("швидко", "повільно", sources=["synonyms_karavansky"], polarity="antonym")]
    items, ledger, _summary = _build(capsys, manifest, dictionary, None)
    assert _pairs(items) == {("швидко", "повільно"), ("повільно", "швидко")} and ledger == {}
    assert {item["source"] for item in items} == {"synonyms_karavansky"}
    assert all("evidence" not in item for item in items)
    school_site = [_approved("швидко", "повільно", sources=["miyklas.com.ua"], polarity="antonym")]
    items, ledger, _summary = _build(capsys, manifest, school_site, None)
    assert items == [] and set(ledger.values()) == {"no_dictionary_source"}


def _sources_db(path: Path, rows_by_headword: dict[str, str]) -> Path:
    """A minimal ``sources.db`` whose checked entries file each row under its headword."""
    with sqlite3.connect(path) as conn:
        conn.executescript(
            """
            CREATE TABLE ulif_dictua_entries (
                id INTEGER PRIMARY KEY, normalized_query TEXT, homonym_checked INTEGER, status TEXT
            );
            CREATE TABLE ulif_dictua_sections (
                id INTEGER PRIMARY KEY, entry_id INTEGER, kind TEXT, source_order INTEGER, payload_json TEXT
            );
            """
        )
        for entry_id, (headword, row) in enumerate(rows_by_headword.items(), start=1):
            conn.execute("INSERT INTO ulif_dictua_entries VALUES (?, ?, 1, 'ok')", (entry_id, headword))
            conn.execute(
                "INSERT INTO ulif_dictua_sections VALUES (?, ?, 'synonyms', 0, ?)",
                (entry_id, entry_id, json.dumps(payload_from_row_html(row), ensure_ascii=False)),
            )
    return path


def test_distractor_never_shares_a_group_filed_under_a_third_headword(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # Reviewer probe (cf-8714-r3-codex): the reader loaded only groups filed under
    # an approved pair's own headwords, so шал, which shares the НЕСАМОВИТІСТЬ group
    # with the answer гнів, stayed eligible as a distractor.
    db = _sources_db(
        tmp_path / "sources.db",
        {"гнів": _fixture_row("гнів", "злість"), "несамовитість": NESAMOVYTIST},
    )
    approved = [_approved("гнів", "злість")]
    ulif = read_ulif_synonym_groups(db, {"approved": approved, "rejected": []})
    assert ulif is not None and len(ulif) == 2
    assert ulif.shares_group("гнів", "шал")
    manifest = [
        _entry("гнів", "noun", "anger"),
        _entry("злість", "noun", "spite"),
        _entry("шал", "noun", "frenzy"),
        _entry("підручник", "noun", "textbook"),
        _entry("бібліотека", "noun", "library"),
        _entry("університет", "noun", "university"),
    ]
    items, _ledger, _summary = _build(capsys, manifest, approved, ulif)
    assert _pairs(items) == {("гнів", "злість"), ("злість", "гнів")}
    for item in items:
        distractors = {option["label"] for option in item["options"] if option["kind"] == "distractor"}
        assert "шал" not in distractors, (item["prompt"], item["answer"], distractors)


def test_synonym_build_fails_without_ulif(capsys: pytest.CaptureFixture[str]) -> None:
    # Reviewer probe: with ULIF data unavailable the build warned and shipped an empty
    # synonym mode.
    manifest = [_entry("список", "noun", "list"), _entry("перелік", "noun", "enumeration"), *_NOUN_FILLERS]
    with pytest.raises(UlifSynonymDataUnavailable):
        _build(capsys, manifest, [_approved("список", "перелік")], None)


@pytest.mark.parametrize("state", ["no_path", "missing_file", "no_tables", "no_checked_group"])
def test_ulif_reader_fails_when_approved_synonyms_need_missing_data(tmp_path: Path, state: str) -> None:
    db: Path | None = tmp_path / "sources.db"
    if state == "no_path":
        db = None
    elif state == "no_tables":
        sqlite3.connect(tmp_path / "sources.db").close()
    elif state == "no_checked_group":
        _sources_db(tmp_path / "sources.db", {})
    verdicts = {"approved": [_approved("список", "перелік")], "rejected": []}
    with pytest.raises(UlifSynonymDataUnavailable):
        read_ulif_synonym_groups(db, verdicts)


def test_ulif_reader_is_not_needed_without_approved_synonyms(tmp_path: Path) -> None:
    antonyms = {"approved": [_approved("швидко", "повільно", polarity="antonym")], "rejected": []}
    assert read_ulif_synonym_groups(tmp_path / "missing.db", antonyms) is None
    assert read_ulif_synonym_groups(None, {"approved": [], "rejected": []}) is None


def _item(prompt: str, answer: str, distractors: list[str], polarity: str = "synonym") -> dict[str, Any]:
    options = [{"label": answer, "lemmaId": answer, "kind": "answer"}]
    options.extend({"label": label, "lemmaId": label, "kind": "distractor"} for label in distractors)
    return {
        "synonymId": f"syn_{prompt}_{answer}",
        "lemmaId": prompt,
        "targetLemmaId": answer,
        "polarity": polarity,
        "prompt": prompt,
        "answer": answer,
        "options": options,
        "source": "fixture",
    }


def test_build_gate_rejects_distractor_that_is_another_items_answer() -> None:
    # Planted failure: the same deck accepts проте for але, so проте cannot be a
    # distractor of але → одначе.
    planted = [
        _item("але", "одначе", ["проте", "щоб", "ніж"]),
        _item("але", "проте", ["щоб", "ніж", "поки"]),
    ]
    errors = validate_mode_items("synonym", planted)
    assert any("проте" in error and "одначе" in error for error in errors), errors

    clean = [
        _item("але", "одначе", ["бо", "щоб", "ніж"]),
        _item("але", "проте", ["щоб", "ніж", "поки"]),
    ]
    assert validate_synonym_option_sets(clean) == []
    # Antonym-polarity answers are a different relation; they are not synonym answers.
    mixed = [
        _item("великий", "величезний", ["малий", "новий", "старий"]),
        _item("великий", "малий", ["новий", "старий", "теплий"], polarity="antonym"),
    ]
    assert validate_synonym_option_sets(mixed) == []
