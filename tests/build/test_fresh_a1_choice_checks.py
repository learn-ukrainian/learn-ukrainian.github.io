"""A1 post-resolution choice checks using independently inspected VESUM forms.

VESUM source locations: брат 487702-487719, книга 2614480-2614493,
бути 542216-542245, читати 6561736-6561760, великий 611137-611177,
м'яч 3260520-3260537, подарунок 4543231-4543247, каша 2522268-2522281,
кордон 2712390-2712406, діло 1540652-1540666, кіт 2592011-2592029.
The negation particle is the A1 word store's record W-061 (VESUM entry 226767).
"""

from __future__ import annotations

import copy
import sqlite3
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from scripts.build.fresh import cli
from scripts.build.fresh.candidates import item_candidates
from scripts.build.fresh.requires_confirm import questions_from_draft, record_answers
from scripts.build.fresh.runner import NEGATION_PARTICLE_RECORD, check_4_activities, check_7_a1_choices
from scripts.curriculum.evidence import lock
from scripts.curriculum.resolver import receipts
from scripts.curriculum.resolver.inputs import ResolverError

ROOT = Path(__file__).resolve().parents[2]
A1_STORE = ROOT / "curriculum/l2-uk-en/evidence/a1/_words.yaml"
STORE_WORDS = yaml.safe_load(A1_STORE.read_text(encoding="utf-8"))["words"]
NEGATION = next(record for record in STORE_WORDS if record["id"] == NEGATION_PARTICLE_RECORD)
W075 = next(record for record in STORE_WORDS if record["id"] == "W-075")
W031 = next(record for record in STORE_WORDS if record["id"] == "W-031")
W047 = next(record for record in STORE_WORDS if record["id"] == "W-047")


def _record(number: int, lemma: str, forms: list[tuple[str, str]]) -> dict:
    return {
        "id": f"W-{number}",
        "lemma": lemma,
        "forms": [{"form": text, "tags": tags, "learner": True} for text, tags in forms],
    }


BROTHER = _record(
    1,
    "брат",
    [
        ("брата", "noun:anim:m:v_rod"),
        ("брата", "noun:anim:m:v_zna"),
        ("брату", "noun:anim:m:v_dav"),
        ("брату", "noun:anim:m:v_mis"),
    ],
)
BOOK = _record(
    2,
    "книга",
    [
        ("книги", "noun:inanim:f:v_rod"),
        ("книги", "noun:inanim:p:v_naz"),
        ("книги", "noun:inanim:p:v_zna"),
        ("книгу", "noun:inanim:f:v_zna"),
    ],
)
BE = _record(
    3,
    "бути",
    [
        ("буду", "verb:imperf:futr:s:1"),
        ("буде", "verb:imperf:futr:s:3"),
        ("будемо", "verb:imperf:futr:p:1"),
    ],
)
READ = _record(
    4,
    "читати",
    [
        ("читати", "verb:imperf:inf"),
        ("читаю", "verb:imperf:pres:s:1"),
        ("читаєш", "verb:imperf:pres:s:2"),
        ("читав", "verb:imperf:past:m"),
    ],
)
BIG = _record(
    6,
    "великий",
    [
        ("велике", "adj:n:v_naz:compb"),
        ("великому", "adj:n:v_dav:compb"),
    ],
)
BREAKFAST = _record(
    7,
    "поснідати",
    [
        ("поснідала", "verb:perf:past:f"),
        ("поснідали", "verb:perf:past:p"),
        ("поснідав", "verb:perf:past:m"),
    ],
)
WATCH = _record(8, "дивитися", [("дивився", "verb:rev:imperf:past:m"), ("дивилися", "verb:rev:imperf:past:p")])
GIVE = _record(
    9,
    "дати",
    [
        ("дай", "verb:perf:impr:s:2"),
        ("дати", "verb:perf:inf"),
        ("дайте", "verb:perf:impr:p:2"),
    ],
)
COST = _record(
    10,
    "коштувати",
    [("коштує", "verb:imperf:pres:s:3"), ("коштувала", "verb:imperf:past:f")],
)
WORK = _record(
    11,
    "працювати",
    [("працюємо", "verb:imperf:pres:p:1"), ("працювали", "verb:imperf:past:p")],
)
BLUE = _record(
    13,
    "синій",
    [
        ("синя", "adj:f:v_naz:compb"),
        ("синій", "adj:m:v_naz:compb"),
        ("синій", "adj:m:v_zna:rinanim:compb"),
        ("синій", "adj:m:v_kly:compb"),
        ("синій", "adj:f:v_dav:compb"),
        ("синій", "adj:f:v_mis:compb"),
    ],
)
BLUE_VERB = _record(14, "синіти", [("синій", "verb:imperf:impr:s:2")])
PORRIDGE = _record(
    15,
    "каша",
    [
        ("кашу", "noun:inanim:f:v_zna"),
        ("каші", "noun:inanim:f:v_rod"),
        ("каші", "noun:inanim:f:v_dav"),
        ("каші", "noun:inanim:f:v_mis"),
        ("каші", "noun:inanim:p:v_naz"),
        ("каші", "noun:inanim:p:v_zna"),
        ("каші", "noun:inanim:p:v_kly"),
        ("каша", "noun:inanim:f:v_naz"),
    ],
)
FUTURE_BE = _record(
    16,
    "бути",
    [
        ("будуть", "verb:imperf:futr:p:3"),
        ("будемо", "verb:imperf:futr:p:1"),
        ("буде", "verb:imperf:futr:s:3"),
    ],
)

VESUM_LOCATIONS = {
    "W-1": "487702-487719",
    "W-2": "2614480-2614493",
    "W-3": "542216-542245",
    "W-4": "6561736-6561760",
    "W-6": "611137-611177",
    "W-7": "4758815-4758831",
    "W-8": "1503099-1503139",
    "W-9": "1380770-1380786",
    "W-10": "2752427-2752449",
    "W-11": "4832237-4832260",
    "W-12": "1380770-1380786",
    "W-13": "5594828-5594871",
    "W-15": "2522268-2522281",
    "W-16": "542216-542245",
    "W-17": "6445807-6445825",
    "W-18": "4543231-4543247",
    "W-20": "2712390-2712406",
    "W-21": "1540652-1540666",
    "W-22": "2592011-2592029",
}


def _check(
    tmp_path: Path,
    item: dict,
    record: dict,
    *,
    extra_records: list[dict] | None = None,
    lookup=None,
    typ: str = "quiz",
    receipt: bool = True,
) -> dict:
    draft = {"activities": [{"id": "a1", "items": [item]}], "steps": []}
    lesson = {"activities": [{"id": "a1", "type": typ}]}
    words = {"words": [record, *(extra_records or [])]}
    stream = SimpleNamespace(
        lesson={"level": "a1", "slug": "sample", "n": 1}, inputs={"draft_sha256": "a" * 64}, tokens=[]
    )
    if receipt and item.get("kind") == "form" and not receipts.requirement_receipt_path(tmp_path, 1).exists():
        _write_form_receipt(tmp_path, item)
    return check_7_a1_choices(
        draft,
        lesson,
        words,
        stream,
        state_dir=tmp_path,
        lesson_n=1,
        vesum_lookup=lookup or (lambda words: {word: [] for word in words}),
    )


def _write_form_receipt(tmp_path: Path, item: dict, *, decision: str = "confirm") -> None:
    (tmp_path / "lesson-1.writer.yaml").write_text("model: gpt-6-sol\n", encoding="utf-8")
    options = item["options"]
    key = item.get("correct", 0)
    evidence_id = "vesum:" + VESUM_LOCATIONS[item["option_records"][0]]
    doc = {
        "requirements_schema": 2,
        "lesson": {"level": "a1", "slug": "sample", "n": 1},
        "inputs": {"draft_sha256": "a" * 64},
        "items": [
            {
                "activity": "a1",
                "item": 0,
                "requires": item["requires"],
                "payload_sha256": receipts.requirement_payload_sha256(
                    receipts.requirement_sentence(item), options, key, item["requires"]
                ),
                "decision": decision,
                "reason": "source-backed unique reading" if decision == "confirm" else "alternative reading",
                "requires_forced": decision == "confirm",
                "options": [
                    {"text": text, "judgement": "valid" if i == key else "invalid", "evidence": [evidence_id]}
                    for i, text in enumerate(options)
                ],
                "writer": {"seat": "codex@sol", "family": "openai"},
                "reviewer": {"seat": "claude@sonnet", "family": "anthropic", "lane": "language"},
            }
        ],
    }
    receipts.write_requirement_receipts(receipts.requirement_receipt_path(tmp_path, 1), doc)


def _form(options: list[str], record: dict, demand: dict[str, str], *, key: int = 0, taught: str = "Case") -> dict:
    return {
        "kind": "form",
        "sentence": "___",
        "options": options,
        "correct": key,
        "option_records": [record["id"]] * len(options),
        "tests_feature": taught,
        "requires": demand,
    }


GIFT = _record(
    18,
    "подарунок",
    [
        ("подарунка", "noun:inanim:m:v_rod"),
        ("подарунка", "noun:inanim:m:v_zna:var"),
        ("подарунок", "noun:inanim:m:v_naz"),
        ("подарунок", "noun:inanim:m:v_zna"),
        ("подарунком", "noun:inanim:m:v_oru"),
    ],
)
BORDER = _record(
    20,
    "кордон",
    [
        ("кордонами", "noun:inanim:p:v_oru"),
        ("кордони", "noun:inanim:p:v_naz"),
        ("кордони", "noun:inanim:p:v_zna"),
        ("кордони", "noun:inanim:p:v_kly"),
        ("кордонів", "noun:inanim:p:v_rod"),
    ],
)
DEED = _record(
    21,
    "діло",
    [
        ("діло", "noun:inanim:n:v_naz"),
        ("діло", "noun:inanim:n:v_zna"),
        ("діло", "noun:inanim:n:v_kly"),
        ("діла", "noun:inanim:n:v_rod"),
        ("діла", "noun:inanim:p:v_naz"),
        ("діла", "noun:inanim:p:v_zna"),
        ("діла", "noun:inanim:p:v_kly"),
    ],
)
CAT = _record(
    22,
    "кіт",
    [
        ("кота", "noun:anim:m:v_rod"),
        ("кота", "noun:anim:m:v_zna"),
        ("кіт", "noun:anim:m:v_naz"),
    ],
)


def _case_offer(
    sentence: str,
    *,
    options: list[str] | None = None,
    target_record: dict | None = None,
    option_records: list[str] | None = None,
    lookup_table: dict[str, list[dict]] | None = None,
    key: int = 0,
    demand: dict[str, str] | None = None,
    feature: str = "Case",
    kind: str = "form",
    level: str = "a1",
    extra_records: list[dict] | None = None,
    sentence_field: str = "sentence",
    particle: dict | None = NEGATION,
) -> dict:
    rec = target_record or GIFT
    opts = options or ["подарунка", "подарунок", "подарунком"]
    req = demand or {"Case": "Gen"}
    item = _form(opts, rec, req, key=key, taught=feature)
    if option_records is not None:
        item["option_records"] = option_records
    item["kind"] = kind
    item["option_why"] = ["Why."] * len(opts)
    item[sentence_field] = sentence
    if sentence_field != "sentence":
        item.pop("sentence")
    draft = {"activities": [{"id": "a1", "items": [item]}]}
    lesson = {"level": level, "activities": [{"id": "a1", "type": "quiz"}]}
    # VESUM analyses for these surfaces were independently inspected for this regression.
    table: dict[str, list[dict]] = {
        "маю": [{"tags": "verb:imperf:pres:s:1"}],
        "знаю": [{"tags": "verb:imperf:pres:s:1"}],
        "розумію": [{"tags": "verb:imperf:pres:s:1"}],
        "працюю": [{"tags": "verb:imperf:pres:s:1"}],
        "бачу": [{"tags": "verb:imperf:pres:s:1:insert"}],
        "люблю": [{"tags": "verb:imperf:pres:s:1"}],
        "має": [{"tags": "verb:imperf:pres:s:3"}],
        "роблю": [{"tags": "verb:imperf:pres:s:1"}],
        "гуляємо": [{"tags": "verb:imperf:pres:p:1"}],
        "йде": [{"tags": "verb:imperf:pres:s:3"}],
        "купую": [{"tags": "verb:imperf:pres:s:1"}],
        "знаєш": [{"tags": "verb:imperf:pres:s:2:insert"}],
        "у": [{"tags": "prep"}],
        "в": [{"tags": "prep"}],
        "за": [
            {"pos": "adv", "tags": "adv:predic"},
            {"pos": "part", "tags": "part"},
            {"pos": "prep", "tags": "prep"},
        ],
        "при": [
            {"pos": "verb", "tags": "verb:imperf:impr:s:2"},
            {"pos": "prep", "tags": "prep"},
        ],
        "цьому": [
            {"tags": "noun:inanim:n:v_dav:pron:dem"},
            {"tags": "noun:inanim:n:v_mis:pron:dem"},
            {"tags": "adj:m:v_dav:pron:dem"},
            {"tags": "adj:m:v_mis:pron:dem"},
            {"tags": "adj:n:v_dav:pron:dem"},
            {"tags": "adj:n:v_mis:pron:dem"},
        ],
        "манної": [{"tags": "adj:f:v_rod"}],
        "сухопутних": [
            {"tags": "adj:p:v_rod"},
            {"tags": "adj:p:v_zna:ranim"},
            {"tags": "adj:p:v_mis"},
        ],
        "добре": [
            {"pos": "adv", "tags": "adv:compb:predic"},
            {"pos": "adj", "tags": "adj:n:v_naz:compb"},
            {"pos": "adj", "tags": "adj:n:v_zna:compb"},
            {"pos": "adj", "tags": "adj:n:v_kly:compb"},
        ],
        "подарунка": [
            {"pos": "noun", "tags": "noun:inanim:m:v_rod"},
            {"pos": "noun", "tags": "noun:inanim:m:v_zna:var"},
        ],
        "подарунок": [
            {"pos": "noun", "tags": "noun:inanim:m:v_naz"},
            {"pos": "noun", "tags": "noun:inanim:m:v_zna"},
        ],
        "подарунком": [
            {"pos": "noun", "tags": "noun:inanim:m:v_oru"},
        ],
        "каші": [
            {"pos": "noun", "tags": "noun:inanim:f:v_rod"},
            {"pos": "noun", "tags": "noun:inanim:f:v_dav"},
            {"pos": "noun", "tags": "noun:inanim:f:v_mis"},
            {"pos": "noun", "tags": "noun:inanim:p:v_naz"},
            {"pos": "noun", "tags": "noun:inanim:p:v_zna"},
            {"pos": "noun", "tags": "noun:inanim:p:v_kly"},
        ],
        "книги": [
            {"pos": "noun", "tags": "noun:inanim:f:v_rod"},
            {"pos": "noun", "tags": "noun:inanim:p:v_naz"},
            {"pos": "noun", "tags": "noun:inanim:p:v_zna"},
            {"pos": "noun", "tags": "noun:inanim:p:v_kly"},
        ],
        "брата": [
            {"pos": "noun", "tags": "noun:anim:m:v_rod"},
            {"pos": "noun", "tags": "noun:anim:m:v_zna"},
        ],
        "кордонів": [
            {"pos": "noun", "tags": "noun:inanim:p:v_rod"},
        ],
        "діло": [
            {"pos": "noun", "tags": "noun:inanim:n:v_naz"},
            {"pos": "noun", "tags": "noun:inanim:n:v_zna"},
            {"pos": "noun", "tags": "noun:inanim:n:v_kly"},
            {"pos": "verb", "tags": "verb:perf:past:n"},
        ],
        "діла": [
            {"pos": "noun", "tags": "noun:inanim:n:v_rod"},
            {"pos": "noun", "tags": "noun:inanim:p:v_naz"},
            {"pos": "noun", "tags": "noun:inanim:p:v_zna"},
            {"pos": "noun", "tags": "noun:inanim:p:v_kly"},
            {"pos": "verb", "tags": "verb:perf:past:f"},
        ],
        "нового": [
            {"tags": "noun:inanim:n:v_rod"},
            {"tags": "adj:m:v_rod:compb"},
            {"tags": "adj:m:v_zna:ranim:compb"},
            {"tags": "adj:n:v_rod:compb"},
        ],
        "бо": [
            {"tags": "conj:subord"},
            {"tags": "part"},
        ],
        "як": [
            {"tags": "adv:pron:int:rel"},
            {"tags": "conj:subord"},
            {"tags": "noun:anim:m:v_naz"},
            {"tags": "part"},
        ],
        "ти": [
            {"tags": "noun:anim:s:v_naz:pron:pers:2"},
            {"tags": "noun:anim:s:v_kly:pron:pers:2"},
        ],
        "ніколи": [
            {"tags": "adv:pron:emph:predic"},
            {"tags": "adv:pron:neg"},
        ],
        "країна": [{"tags": "noun:inanim:f:v_naz"}],
        "ця": [{"tags": "adj:f:v_naz:pron:dem"}],
        "я": [{"tags": "noun:anim:s:v_naz:pron:pers:1"}],
        "це": [
            {"tags": "noun:inanim:n:v_naz:pron:dem"},
            {"tags": "noun:inanim:n:v_zna:pron:dem"},
            {"tags": "part"},
            {"tags": "adj:n:v_naz:pron:dem"},
            {"tags": "adj:n:v_zna:pron:dem"},
        ],
    }
    if lookup_table:
        table.update(lookup_table)

    def lookup(words: list[str]) -> dict:
        return {word: table.get(word, []) for word in words}

    store = [rec, *([particle] if particle else []), *(extra_records or [])]
    return check_4_activities(draft, lesson, {"words": store}, {}, level=level, vesum_lookup=lookup)[0]


@pytest.mark.parametrize(
    "sentence",
    [
        "Скоро мамине свято, а я ще ___ не маю.",
        "Я не знаю ___.",
        "Я не розумію ___.",
    ],
)
def test_a1_case_contrast_with_negated_finite_verb_stops_at_offer(sentence: str) -> None:
    row = _case_offer(sentence)
    assert (row["check"], row["code"], row["layer"]) == (4, "a1_case_contrast_under_negated_verb", "writer")


def test_prompt_sentence_is_used_by_offer_question_and_payload() -> None:
    sentence = "Скоро мамине свято, а я ще ___ не маю."
    assert _case_offer(sentence, sentence_field="prompt")["code"] == "a1_case_contrast_under_negated_verb"
    item = _form(["подарунка", "подарунок", "подарунком"], GIFT, {"Case": "Gen"})
    item.update({"prompt": sentence, "question": "different sentence ___"})
    batch = questions_from_draft(
        {"activities": [{"id": "a1", "type": "quiz", "items": [item]}]},
        {"lesson": {"level": "a1", "slug": "sample", "n": 1}, "activities": [{"id": "a1", "type": "quiz"}]},
        {"draft_sha256": "a" * 64},
    )
    question = batch["questions"][0]
    assert question["sentence"] == sentence
    assert question["payload_sha256"] == receipts.requirement_payload_sha256(
        sentence, question["options"], question["key_index"], question["requires"]
    )


def test_form_with_empty_rendered_sentence_is_refused() -> None:
    assert _case_offer("", sentence_field="prompt")["code"] == "form_sentence_missing"


def test_shared_accusative_case_does_not_trigger_negation_rule() -> None:
    # Under rev 6.5, options whose learner Case sets are all identical (Acc) do not contrast in case.
    coffee = _record(30, "кава", [("каву", "noun:inanim:f:v_zna")])
    tea = _record(31, "чай", [("чай", "noun:inanim:m:v_zna")])
    water = _record(32, "вода", [("воду", "noun:inanim:f:v_zna")])
    item = {
        "kind": "vocabulary",
        "prompt": "Вранці я не п'ю ___.",
        "options": ["каву", "чай", "воду"],
        "correct": 0,
        "option_records": ["W-30", "W-31", "W-32"],
        "target_record": "W-30",
    }
    lesson = {"level": "a1", "activities": [{"id": "a1", "type": "quiz"}]}
    draft = {"activities": [{"id": "a1", "items": [item]}]}
    row = check_4_activities(draft, lesson, {"words": [coffee, tea, water, NEGATION]}, {}, level="a1")[0]
    assert row.get("code") != "a1_case_contrast_under_negated_verb"


@pytest.mark.parametrize("unreadable", [False, True])
def test_check_4_default_vesum_outage_is_named(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, unreadable: bool
) -> None:
    db_path = tmp_path / "vesum.db"
    if unreadable:
        db_path.write_text("not a database", encoding="utf-8")
    monkeypatch.setenv("VESUM_DB_PATH", str(db_path))
    item = _form(["подарунка", "подарунок", "подарунком"], GIFT, {"Case": "Gen"})
    item["prompt"] = "Я не знаю ___."
    row = check_4_activities(
        {"activities": [{"id": "a1", "items": [item]}]},
        {"level": "a1", "activities": [{"id": "a1", "type": "quiz"}]},
        {"words": [GIFT, NEGATION]},
        {},
        level="a1",
    )[0]
    assert (row["check"], row["code"]) == (4, "a1_choice_source_unavailable")


@pytest.mark.parametrize("sentence", ["Без мого ___.", "У мене немає ___."])
def test_non_negated_case_contrast_passes_check_4_without_vesum(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, sentence: str
) -> None:
    monkeypatch.setenv("VESUM_DB_PATH", str(tmp_path / "missing-vesum.db"))
    item = _form(["подарунка", "подарунок", "подарунком"], GIFT, {"Case": "Gen"})
    item.update(prompt=sentence, option_why=["Genitive after the phrase.", "Nominative.", "Instrumental."])
    row = check_4_activities(
        {"activities": [{"id": "a1", "items": [item]}]},
        {"level": "a1", "activities": [{"id": "a1", "type": "quiz"}]},
        {"words": [GIFT, NEGATION]},
        {},
        level="a1",
    )[0]
    assert row["status"] == "passed", row


def test_negation_particle_record_is_bound_in_the_a1_store() -> None:
    assert (NEGATION["pos"], NEGATION["entry"]) == ("part", {"entry_id": 226767, "source": "vesum"})


@pytest.mark.parametrize(
    "particle",
    [
        None,
        {**NEGATION, "pos": "noun"},
        {**NEGATION, "lemma": ""},
        {**NEGATION, "entry": None},
        {**NEGATION, "entry": {"source": "manual", "entry_id": 226767}},
    ],
)
def test_store_without_negation_particle_record_is_named(particle: dict | None) -> None:
    row = _case_offer("Я не знаю ___.", particle=particle)
    assert (row["check"], row["code"], row["layer"]) == (4, "a1_negation_particle_record_invalid", "word_store")


def test_negation_record_rebound_to_another_particle_is_refused() -> None:
    # W-061 carrying another store particle's lemma and VESUM binding (the real W-062 record).
    another = next(record for record in STORE_WORDS if record["id"] == "W-062")
    other = {**NEGATION, "lemma": another["lemma"], "entry": another["entry"]}
    row = _case_offer("Я не знаю ___.", particle=other)
    assert (row["check"], row["code"], row["layer"]) == (4, "a1_negation_particle_record_invalid", "word_store")


def test_real_a1_store_negation_particle_passes_identity_check() -> None:
    assert _case_offer("Я не знаю ___.")["code"] == "a1_case_contrast_under_negated_verb"


@pytest.mark.parametrize(
    "sentence",
    ["Це не хліб, а ___", "Немає ___", "Ні, ___", "Без ___", "Ось ___"],
)
def test_a1_case_contrast_without_negated_finite_verb_reaches_existing_checks(sentence: str) -> None:
    assert _case_offer(sentence).get("code") != "a1_case_contrast_under_negated_verb"


def test_a1_case_contrast_cannot_bypass_by_declaring_another_feature() -> None:
    assert _case_offer("Я не знаю ___", feature="Number")["code"] == "a1_case_contrast_under_negated_verb"


def test_a1_case_contrast_cannot_bypass_by_declaring_another_kind() -> None:
    assert _case_offer("Я не знаю ___", kind="vocabulary")["code"] == "a1_case_contrast_under_negated_verb"


def test_a1_case_contrast_accepts_store_finite_analysis_without_vesum() -> None:
    know = _record(19, "знати", [("знаю", "verb:imperf:pres:s:1")])
    assert _case_offer("Я не знаю ___ і не хліб", extra_records=[know])["code"] == "a1_case_contrast_under_negated_verb"


@pytest.mark.parametrize("level", ["a2", "b1"])
def test_negated_case_contrast_does_not_apply_above_a1(level: str) -> None:
    assert _case_offer("Я не знаю ___", level=level).get("code") != "a1_case_contrast_under_negated_verb"


def test_case_contrast_blocker_1_two_options_with_shared_accusative_refused() -> None:
    row = _case_offer("Я не маю ___.", options=["подарунка", "подарунок"])
    assert (row["check"], row["code"], row["layer"]) == (4, "a1_case_contrast_under_negated_verb", "writer")


def test_adjacent_preposition_e1_exempts_case_contrast() -> None:
    row = _case_offer("Я ніколи не працюю у ___.", options=["подарунка", "подарунок"])
    assert row.get("code") != "a1_case_contrast_under_negated_verb"
    assert row["status"] == "passed"


def test_non_adjacent_preposition_e1_refuses_case_contrast() -> None:
    row = _case_offer("Я не бачу в цьому ___.", options=["подарунка", "подарунок"])
    assert (row["check"], row["code"], row["layer"]) == (4, "a1_case_contrast_under_negated_verb", "writer")


def test_adjacent_unambiguous_adjective_e3_exempts_feminine_genitive() -> None:
    row = _case_offer(
        "Я не люблю манної ___.",
        options=["кашу", "каші", "каша"],
        target_record=PORRIDGE,
        key=1,
    )
    assert row.get("code") != "a1_case_contrast_under_negated_verb"
    assert row["status"] == "passed"


def test_adjacent_unambiguous_adjective_e3_exempts_plural_genitive_with_animacy_contrast() -> None:
    row = _case_offer(
        "Ця країна не має сухопутних ___.",
        options=["кордонами", "кордони", "кордонів"],
        target_record=BORDER,
        key=2,
    )
    assert row.get("code") != "a1_case_contrast_under_negated_verb"
    assert row["status"] == "passed"


def test_adjacent_modifier_with_adverb_analysis_fails_e3_and_refuses() -> None:
    row = _case_offer(
        "Я не роблю добре ___.",
        options=["діло", "діла"],
        target_record=DEED,
        key=0,
        demand={"Case": "Nom"},
    )
    assert (row["check"], row["code"], row["layer"]) == (4, "a1_case_contrast_under_negated_verb", "writer")


def test_adjacent_modifier_with_noun_analysis_fails_e3_and_refuses() -> None:
    row = _case_offer(
        "Я не бачу нового ___.",
        options=["кота", "кіт"],
        target_record=CAT,
        key=0,
        demand={"Case": "Gen"},
    )
    assert (row["check"], row["code"], row["layer"]) == (4, "a1_case_contrast_under_negated_verb", "writer")


@pytest.mark.parametrize(
    "sentence",
    [
        "Ми не гуляємо, бо йде ___.",
        "Я не купую, як ти знаєш, ___.",
    ],
)
def test_intervening_clause_or_verb_has_no_nearest_verb_exemption_refused(sentence: str) -> None:
    row = _case_offer(sentence, options=["подарунка", "подарунок"])
    assert (row["check"], row["code"], row["layer"]) == (4, "a1_case_contrast_under_negated_verb", "writer")


def test_sentence_without_negated_verb_is_unaffected() -> None:
    row = _case_offer("Я купую ___.", options=["подарунка", "подарунок"])
    assert row.get("code") != "a1_case_contrast_under_negated_verb"
    assert row["status"] == "passed"


@pytest.mark.parametrize(
    ("sentence", "opts", "rec", "extra", "key", "req"),
    [
        (
            "Я не роблю добре ___.",
            ["діло", "діла"],
            DEED,
            [W075],
            0,
            {"Case": "Nom"},
        ),
        (
            "Я ніколи не працюю за ___.",
            ["подарунка", "подарунок"],
            GIFT,
            [W031],
            0,
            {"Case": "Gen"},
        ),
        (
            "Я не при ___.",
            ["подарунка", "подарунок"],
            GIFT,
            [W047],
            0,
            {"Case": "Gen"},
        ),
    ],
)
def test_store_records_narrower_than_vesum_cannot_earn_exemption(
    sentence: str,
    opts: list[str],
    rec: dict,
    extra: list[dict],
    key: int,
    req: dict[str, str],
) -> None:
    # W-075 «добре», W-031 «за» and W-047 «при» are present in the store as subsets of VESUM.
    # The union with VESUM lookup provides their extra analyses, preventing false exemptions.
    row = _case_offer(
        sentence,
        options=opts,
        target_record=rec,
        extra_records=extra,
        key=key,
        demand=req,
    )
    assert (row["check"], row["code"], row["layer"]) == (4, "a1_case_contrast_under_negated_verb", "writer")


def test_adjacent_unambiguous_adjective_e3_refuses_when_two_options_agree() -> None:
    # "Я не люблю манної ___." with манної (adj:f:v_rod).
    # Two options каші (PORRIDGE, noun:inanim:f:v_rod) and книги (BOOK, noun:inanim:f:v_rod)
    # both agree in Genitive Fem Sing with the modifier run.
    # E3 requires exactly one agreeing option; two agreeing options refuses (pins "exactly one").
    row = _case_offer(
        "Я не люблю манної ___.",
        options=["каші", "книги"],
        target_record=PORRIDGE,
        option_records=["W-15", "W-2"],
        extra_records=[BOOK],
        key=0,
        demand={"Case": "Gen"},
    )
    assert (row["check"], row["code"], row["layer"]) == (4, "a1_case_contrast_under_negated_verb", "writer")


def test_case_contrast_pins_var_accusative_reading() -> None:
    # подарунка has Case=Gen (v_rod) and Case=Acc (v_zna:var).
    # брата has Case=Gen (v_rod) and Case=Acc (v_zna).
    # Their shared Accusative comes from the var reading on подарунка.
    # With var kept: Case sets are identical ({Gen, Acc}), so not a case contrast (passed).
    # If var were dropped: Case sets would contrast ({Gen, Acc} vs {Gen}), wrongly refusing under negated verb.
    row = _case_offer(
        "Я не бачу ___.",
        options=["брата", "подарунка"],
        target_record=GIFT,
        option_records=["W-1", "W-18"],
        extra_records=[BROTHER],
        kind="vocabulary",
        key=0,
    )
    assert row.get("code") != "a1_case_contrast_under_negated_verb"
    assert row["status"] == "passed"

    # Counterpart: against Genitive-only кордонів ({Gen}):
    # With var kept: подарунка is {Gen, Acc} vs кордонів {Gen}, contrasting -> refused.
    # If var were dropped: both would be {Gen} (identical), wrongly passing without case contrast.
    row_contrast = _case_offer(
        "Я не бачу ___.",
        options=["кордонів", "подарунка"],
        target_record=GIFT,
        option_records=["W-20", "W-18"],
        extra_records=[BORDER],
        kind="vocabulary",
        key=0,
    )
    assert (row_contrast["check"], row_contrast["code"], row_contrast["layer"]) == (
        4,
        "a1_case_contrast_under_negated_verb",
        "writer",
    )


@pytest.mark.parametrize("exc", [sqlite3.OperationalError("disk I/O error"), OSError("connection lost")])
def test_choice_checks_vesum_lookup_error_fails_closed_when_store_records_present(exc: Exception) -> None:
    def failing_lookup(words: list[str]) -> dict:
        raise exc

    item = _form(["діло", "діла"], DEED, {"Case": "Nom"}, key=0)
    item["sentence"] = "Я не роблю добре ___."
    row = check_4_activities(
        {"activities": [{"id": "a1", "items": [item]}]},
        {"level": "a1", "activities": [{"id": "a1", "type": "quiz"}]},
        {"words": [DEED, NEGATION, W075]},
        {},
        level="a1",
        vesum_lookup=failing_lookup,
    )[0]
    assert (row["check"], row["code"], row["layer"]) == (4, "a1_choice_source_unavailable", "pack")


def test_brother_accusative_requires_receipt(tmp_path: Path) -> None:
    item = _form(["брата", "брату"], BROTHER, {"Case": "Acc"})
    assert _check(tmp_path, item, BROTHER, receipt=False)["code"] == "requires_receipt_missing"
    row = _check(tmp_path, item, BROTHER)
    assert row["status"] == "passed"
    assert row["details"]["requirement_receipts"] == [{"activity": "a1", "item": 0, "requirement": "confirmed"}]
    swapped = copy.deepcopy(item)
    swapped["correct"] = 1
    assert _check(tmp_path, swapped, BROTHER)["code"] == "form_not_unique_for_requires"


def test_book_plural_accusative_needs_singular_demand(tmp_path: Path) -> None:
    item = _form(["книгу", "книги"], BOOK, {"Case": "Acc", "Number": "Sing"}, taught="Number")
    assert _check(tmp_path, item, BOOK)["status"] == "passed"
    item["requires"] = {"Case": "Acc"}
    item["tests_feature"] = "Case"
    assert _check(tmp_path, item, BOOK)["code"] == "form_not_unique_for_requires"


@pytest.mark.parametrize(
    ("record", "options", "requires", "focus", "sentence", "other_records"),
    [
        (
            BLUE,
            ["синя", "синій"],
            {"Gender": "Fem", "Number": "Sing", "Case": "Nom"},
            "Gender",
            "Ця книга ___",
            [BLUE_VERB],
        ),
        (
            PORRIDGE,
            ["кашу", "каші"],
            {"Case": "Acc", "Number": "Sing", "Gender": "Fem"},
            "Case",
            "Я їм одну ___",
            [],
        ),
        (
            FUTURE_BE,
            ["будуть", "будемо", "буде"],
            {"Person": "3", "Number": "Plur", "VerbForm": "Fin"},
            "Person",
            "Вони ___",
            [],
        ),
    ],
)
def test_excluded_distractors_are_offered_and_pass_check_7(
    tmp_path: Path,
    record: dict,
    options: list[str],
    requires: dict[str, str],
    focus: str,
    sentence: str,
    other_records: list[dict],
) -> None:
    item = _form(options, record, requires, taught=focus)
    item["sentence"] = sentence
    item["option_why"] = ["Fits the slot."] + ["Conflicts with the slot."] * (len(options) - 1)
    offered = {
        candidate["form"]: candidate for candidate in item_candidates(item, {"words": [record, *other_records]}, "quiz")
    }
    assert set(options) <= offered.keys()
    assert offered[options[0]]["admitted"] is True
    assert all(offered[option]["admitted"] is False for option in options[1:])
    draft = {"activities": [{"id": "a1", "items": [item]}]}
    lesson = {"activities": [{"id": "a1", "type": "quiz"}]}
    assert (
        check_4_activities(draft, lesson, {"words": [record, NEGATION, *other_records]}, {}, level="a1")[0]["status"]
        == "passed"
    )
    assert _check(tmp_path, item, record, extra_records=other_records)["status"] == "passed"


@pytest.mark.parametrize(
    ("record", "options", "requires"),
    [
        (COST, ["коштує", "коштувала"], {"Person": "3", "Number": "Sing", "VerbForm": "Fin"}),
        (WORK, ["працюємо", "працювали"], {"Person": "1", "Number": "Plur", "VerbForm": "Fin"}),
    ],
)
def test_tense_only_distractor_is_not_offered_and_fails_check_7(
    tmp_path: Path, record: dict, options: list[str], requires: dict[str, str]
) -> None:
    item = _form(options, record, requires, taught="Person")
    offered = {candidate["form"] for candidate in item_candidates(item, {"words": [record]}, "quiz")}
    assert options[0] in offered
    assert options[1] not in offered
    assert _check(tmp_path, item, record)["code"] == "form_option_missing_required_group"


@pytest.mark.parametrize(
    ("record", "options", "requires", "taught", "expected"),
    [
        (
            BREAKFAST,
            ["поснідала", "поснідали"],
            {"Gender": "Fem", "Number": "Sing", "VerbForm": "Fin"},
            "Gender",
            "passed",
        ),
        (
            BREAKFAST,
            ["поснідала", "поснідав"],
            {"Gender": "Fem", "Number": "Sing", "VerbForm": "Fin"},
            "Gender",
            "passed",
        ),
        (WATCH, ["дивився", "дивилися"], {"Gender": "Masc", "Number": "Sing", "VerbForm": "Fin"}, "Gender", "passed"),
        (GIVE, ["дай", "дати"], {"Number": "Sing", "Person": "2", "VerbForm": "Fin"}, "Number", "passed"),
        (GIVE, ["дай", "дайте"], {"Number": "Sing", "Person": "2", "VerbForm": "Fin"}, "Number", "passed"),
        (
            COST,
            ["коштує", "коштувала"],
            {"Person": "3", "Number": "Sing"},
            "Person",
            "form_option_missing_required_group",
        ),
        (
            WORK,
            ["працюємо", "працювали"],
            {"Person": "1", "Number": "Plur"},
            "Person",
            "form_option_missing_required_group",
        ),
        (READ, ["читаю", "читав"], {"Person": "1", "Number": "Sing"}, "Person", "form_option_missing_required_group"),
    ],
)
def test_carried_feature_exclusion_and_key_swaps(
    tmp_path: Path, record: dict, options: list[str], requires: dict[str, str], taught: str, expected: str
) -> None:
    item = _form(options, record, requires, taught=taught)
    row = _check(tmp_path, item, record)
    if expected == "passed":
        assert row["status"] == "passed"
    else:
        assert row["code"] == expected
    item["correct"] = 1
    swapped = _check(tmp_path, item, record)
    assert swapped["code"] == (
        "form_not_unique_for_requires" if expected == "passed" else "form_option_missing_required_group"
    )


def test_one_noncontradicting_analysis_makes_distractor_undecidable(tmp_path: Path) -> None:
    # Both tags for «дати» are sourced VESUM analyses of that surface. This synthetic
    # bound record forces the checker to consider the noun homograph too.
    mixed = _record(
        12,
        "дати",
        [
            ("дайте", "verb:perf:impr:p:2"),
            ("дати", "verb:perf:inf"),
            ("дати", "noun:inanim:p:v_naz"),
        ],
    )
    item = _form(["дайте", "дати"], mixed, {"Person": "2", "Number": "Plur", "VerbForm": "Fin"}, taught="Person")
    assert _check(tmp_path, item, mixed)["code"] == "form_option_missing_required_group"
    item["correct"] = 1
    assert _check(tmp_path, item, mixed)["code"] == "form_option_missing_required_group"


@pytest.mark.parametrize(
    ("sentence", "record", "options", "requires", "feature"),
    [
        ("Я ___ книгу", READ, ["читаю", "читаєш"], {"Person": "1", "Number": "Sing"}, "Person"),
        (
            "Вікно ___ і чисте",
            BIG,
            ["велике", "великому"],
            {"Gender": "Neut", "Number": "Sing", "Case": "Nom"},
            "Gender",
        ),
    ],
)
def test_header_agreement_examples_reject_swapped_key(
    tmp_path: Path, sentence: str, record: dict, options: list[str], requires: dict[str, str], feature: str
) -> None:
    item = _form(options, record, requires, taught=feature)
    item["sentence"] = sentence
    assert _check(tmp_path, item, record)["status"] == "passed"
    item["correct"] = 1
    assert _check(tmp_path, item, record)["code"] == "form_not_unique_for_requires"


@pytest.mark.parametrize(
    ("seat", "family"),
    [("claude@opus-5-5", "anthropic"), ("codex@gpt-6-sol", "openai"), ("agy@gemini-3-pro", "google")],
)
def test_language_lanes_admit_claude_codex_and_agy(seat: str, family: str) -> None:
    assert receipts.language_seat_family(seat, what="test") == family


def test_language_lanes_refuse_grok() -> None:
    assert "grok" not in receipts.LANGUAGE_LANES
    with pytest.raises(ResolverError, match="language lane"):
        receipts.language_seat_family("grok@grok-4.7", what="test")


@pytest.mark.parametrize(
    ("seat", "accepted"),
    [
        ("codex@gpt-6-sol", False),
        ("claude@opus-5-5", True),
        ("agy@gemini-3-pro", True),
        ("grok@grok-4.7", False),
        ("cursor@grok-4.7", False),
        ("codex@grok-4.7", False),
        ("grok@unknown", False),
        ("kimi@kimi-k2", False),
    ],
)
def test_ambiguous_group_entry_needs_other_family_language_seat(tmp_path: Path, seat: str, accepted: bool) -> None:
    (tmp_path / "lesson-1.writer.yaml").write_text("model: gpt-6-sol\n", encoding="utf-8")
    activity = {
        "id": "a1",
        "grouping_feature": "Case",
        "groups": [
            {"value": "Gen", "items": [{"text": "книги", "record": "W-2", "why": "Selected by context."}]},
            {"value": "Nom", "items": []},
        ],
    }
    stream = SimpleNamespace(
        lesson={"level": "a1", "slug": "sample", "n": 1},
        inputs={},
        tokens=[
            {
                "unit": {"activity": "a1", "block": "group_0_0"},
                "provenance": f"question:{seat}:Q-001",
            }
        ],
    )
    row = check_7_a1_choices(
        {"activities": [activity], "steps": []},
        {"activities": [{"id": "a1", "type": "group-sort"}]},
        {"words": [BOOK]},
        stream,
        state_dir=tmp_path,
        lesson_n=1,
        vesum_lookup=lambda words: {word: [] for word in words},
    )
    assert row["status"] == ("passed" if accepted else "failed")
    if not accepted:
        assert row["code"] == "group_entry_ambiguous_without_receipt"


def test_analytic_future_uses_single_store_forms(tmp_path: Path) -> None:
    aux = _form(["буду", "буде", "будемо"], BE, {"Person": "1", "Number": "Sing"}, taught="Person")
    assert _check(tmp_path, aux, BE)["status"] == "passed"
    infinitive = _form(["читати", "читаю", "читав"], READ, {"VerbForm": "Inf"}, taught="VerbForm")
    _write_form_receipt(tmp_path, infinitive)
    assert _check(tmp_path, infinitive, READ)["status"] == "passed"
    infinitive["options"][0] = "буду читати"
    assert _check(tmp_path, infinitive, READ)["code"] == "form_option_without_analysis"


def test_requirement_confirmation_is_bound_to_demand_and_other_family(tmp_path: Path) -> None:
    item = _form(["брата", "брату"], BROTHER, {"Case": "Acc"})
    _write_form_receipt(tmp_path, item)
    assert _check(tmp_path, item, BROTHER)["details"]["requirement_receipts"][0]["requirement"] == "confirmed"
    item["sentence"] = "Changed ___"
    assert _check(tmp_path, item, BROTHER)["code"] == "requires_receipt_stale"
    item["sentence"] = "___"
    path = receipts.requirement_receipt_path(tmp_path, 1)
    doc = receipts.read_requirement_receipts(path)
    doc["items"][0]["requires"] = {"Case": "Gen"}
    receipts.write_requirement_receipts(path, doc)
    assert _check(tmp_path, item, BROTHER)["code"] == "requires_receipt_stale"
    doc["items"][0]["requires"] = {"Case": "Acc"}
    doc["items"][0]["options"][0]["judgement"] = "invalid"
    doc["items"][0]["options"][1]["judgement"] = "valid"
    receipts.write_requirement_receipts(path, doc)
    assert _check(tmp_path, item, BROTHER)["code"] == "requires_receipt_denied"


def test_requirement_payload_binding_and_formatting() -> None:
    demand = {"Case": "Acc", "Number": "Sing"}
    original = receipts.requirement_payload_sha256("Можна ___?", ["хліб", "хліба"], 0, demand)
    assert original == receipts.requirement_payload_sha256(
        " Можна  ___? ", [" хліб ", "хліба"], 0, {"Number": "Sing", "Case": "Acc"}
    )
    for sentence, options, key, requires in [
        ("Дайте ___?", ["хліб", "хліба"], 0, demand),
        ("Можна ___?", ["хліб", "хлібу"], 0, demand),
        ("Можна ___?", ["хліб", "хліба"], 1, demand),
        ("Можна ___?", ["хліб", "хліба"], 0, {"Case": "Acc"}),
    ]:
        assert receipts.requirement_payload_sha256(sentence, options, key, requires) != original


def test_requirement_inputs_ignore_only_form_formatting() -> None:
    draft = {
        "activities": [
            {
                "id": "a1",
                "items": [
                    {
                        "kind": "form",
                        "sentence": "Можна ___?",
                        "options": ["хліб", "хліба"],
                        "requires": {"Case": "Acc"},
                    }
                ],
            }
        ]
    }
    before = receipts.requirement_inputs({"expanded_sha256": "a" * 64, "words_lock": "b" * 64}, draft)
    formatted = copy.deepcopy(draft)
    formatted["activities"][0]["items"][0]["sentence"] = " Можна  ___? "
    formatted["activities"][0]["items"][0]["options"][0] = " хліб "
    assert receipts.requirement_inputs({"expanded_sha256": "c" * 64, "words_lock": "b" * 64}, formatted) == before
    formatted["activities"][0]["items"][0]["options"][0] = "хліба"
    assert receipts.requirement_inputs({"expanded_sha256": "c" * 64, "words_lock": "b" * 64}, formatted) != before


def test_denied_partitive_item_fails_check_7(tmp_path: Path) -> None:
    # inspect-words: хліб noun:inanim:m:v_zna; хліба noun:inanim:m:v_rod;
    # хлібу noun:inanim:m:v_dav and noun:inanim:m:v_mis (VESUM 6445807-6445825).
    bread = _record(
        17,
        "хліб",
        [("хліб", "noun:inanim:m:v_zna"), ("хліба", "noun:inanim:m:v_rod"), ("хлібу", "noun:inanim:m:v_dav")],
    )
    item = _form(["хліб", "хліба", "хлібу"], bread, {"Case": "Acc", "Number": "Sing"})
    item["sentence"] = "Можна ___?"
    _write_form_receipt(tmp_path, item, decision="deny")
    assert _check(tmp_path, item, bread)["code"] == "requires_receipt_denied"
    item["sentence"] = "Дайте ___?"
    assert _check(tmp_path, item, bread)["code"] == "requires_receipt_stale"


def test_requires_record_rejects_invalid_answers(tmp_path: Path) -> None:
    (tmp_path / "lesson-1.writer.yaml").write_text("model: gpt-6-sol\n", encoding="utf-8")
    question = {
        "activity": "a1",
        "item": 0,
        "sentence": "На столі лежить ___.",
        "options": ["хліб", "хліба"],
        "key_index": 0,
        "requires": {"Case": "Nom", "Number": "Sing"},
        "payload_sha256": receipts.requirement_payload_sha256(
            "На столі лежить ___.", ["хліб", "хліба"], 0, {"Case": "Nom", "Number": "Sing"}
        ),
    }
    batch = {
        "lesson": {"level": "a1", "slug": "sample", "n": 1},
        "inputs": {"draft_sha256": "a" * 64},
        "questions": [question],
    }
    answer = {
        "activity": "a1",
        "item": 0,
        "decision": "confirm",
        "reason": "forced by context",
        "requires_forced": True,
        "options": [
            {"text": "хліб", "judgement": "valid", "evidence": ["vesum:6445807-6445825"]},
            {"text": "хліба", "judgement": "invalid", "evidence": ["vesum:6445807-6445825"]},
        ],
    }

    def record(candidate: dict, *, seat: str = "claude@sonnet", family: str = "anthropic") -> dict:
        return record_answers(
            batch,
            {"answers": [candidate]},
            seat=seat,
            family=family,
            writer_seat="codex@sol",
            writer_family="openai",
            state_dir=tmp_path,
        )

    assert record(answer)["items"][0]["decision"] == "confirm"
    (tmp_path / "lesson-1.writer.yaml").write_text("model: claude-sonnet-4-5\n", encoding="utf-8")
    with pytest.raises(ResolverError, match="writer family disagrees"):
        record(answer)
    (tmp_path / "lesson-1.writer.yaml").write_text("model: gpt-6-sol\n", encoding="utf-8")
    for change in (
        {"options": [{**answer["options"][0], "evidence": []}, answer["options"][1]]},
        {"options": [{**answer["options"][0], "evidence": ["sum11:12"]}, answer["options"][1]]},
        {"requires_forced": False},
        {"options": list(reversed(answer["options"]))},
    ):
        with pytest.raises(ResolverError):
            record({**answer, **change})
    with pytest.raises(ResolverError, match="missing answers"):
        record_answers(
            batch,
            {"answers": []},
            seat="claude@sonnet",
            family="anthropic",
            writer_seat="codex@sol",
            writer_family="openai",
            state_dir=tmp_path,
        )
    with pytest.raises(ResolverError, match="duplicate"):
        record_answers(
            batch,
            {"answers": [answer, answer]},
            seat="claude@sonnet",
            family="anthropic",
            writer_seat="codex@sol",
            writer_family="openai",
            state_dir=tmp_path,
        )
    with pytest.raises(ResolverError, match="family"):
        record(answer, family="OpenAI")
    for seat, family in (
        ("other@model", "openai"),
        ("kimi@kimi-k2", "moonshot"),
        ("deepseek@deepseek-v4", "deepseek"),
        ("qwen@qwen3", "qwen"),
        ("grok@grok-4.7", "xai"),
    ):
        with pytest.raises(ResolverError, match="language lane"):
            record(answer, seat=seat, family=family)
    with pytest.raises(ResolverError, match="unresolved family"):
        record(answer, seat="claude@x", family="anthropic")
    assert record(answer, seat="agy@gemini-3-pro", family="google")["items"][0]["reviewer"]["family"] == "google"
    with pytest.raises(ResolverError, match="family"):
        record(answer, family="google")
    unresolved = {
        **answer,
        "decision": "deny",
        "reason": "unresolved source evidence",
        "options": [{**answer["options"][0], "evidence": []}, answer["options"][1]],
    }
    assert record(unresolved)["items"][0]["decision"] == "deny"
    wrong_key = {
        **answer,
        "decision": "deny",
        "reason": "the keyed form is invalid",
        "options": [{**answer["options"][0], "judgement": "invalid"}, {**answer["options"][1], "judgement": "valid"}],
    }
    assert record(wrong_key)["items"][0]["decision"] == "deny"


def test_requires_cli_writes_questions_prompt_and_denial(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state = tmp_path / "curriculum/l2-uk-en/evidence/a1/_state/sample"
    state.mkdir(parents=True)
    (state / "lesson-1.writer.yaml").write_text("model: gpt-6-sol\n", encoding="utf-8")
    item = _form(["хліб", "хліба"], _record(17, "хліб", []), {"Case": "Acc"})
    item["sentence"] = "Можна ___?"
    (state / "lesson-1.draft.yaml").write_bytes(lock.yaml_bytes({"activities": [{"id": "a1", "items": [item]}]}))
    identity = {"level": "a1", "slug": "sample", "n": 1}
    inputs = {key: "a" * 64 for key in ("expanded_sha256", "allowlist_sha256", "words_lock", "vesum", "trie_digest")}
    receipts.write_receipts(
        state / "lesson-1.resolutions.yaml",
        {"resolutions_schema": 1, "lesson": identity, "inputs": inputs, "tokens": []},
    )
    monkeypatch.setattr(
        cli,
        "_load_lesson_data",
        lambda *args, **kwargs: (
            {},
            {"activities": [{"id": "a1", "type": "quiz"}]},
            {},
            {},
            {"state_dir": state.parent},
        ),
    )
    base = ["a1", "sample", "--lesson", "1", "--repo-root", str(tmp_path)]
    assert cli.main(["requires-questions", *base]) == 0
    batch = yaml.safe_load((state / "lesson-1.requires-questions.yaml").read_text())
    assert batch["questions"][0]["sentence"] == "Можна ___?"
    assert (state / "lesson-1.requires-confirm.prompt.md").is_file()
    answer = {
        "answers": [
            {
                "activity": "a1",
                "item": 0,
                "decision": "deny",
                "reason": "alternative partitive reading",
                "requires_forced": False,
                "options": [
                    {"text": "хліб", "judgement": "valid", "evidence": ["vesum:6445807-6445825"]},
                    {"text": "хліба", "judgement": "depends_on_context", "evidence": ["vesum:6445807-6445825"]},
                ],
            }
        ]
    }
    answers_path = tmp_path / "answers.yaml"
    answers_path.write_bytes(lock.yaml_bytes(answer))
    questions_path = state / "lesson-1.requires-questions.yaml"
    tampered = copy.deepcopy(batch)
    tampered["questions"][0]["requires"] = {"Case": "Gen"}
    lock.write(questions_path, lock.yaml_bytes(tampered))
    assert (
        cli.main(
            [
                "requires-record",
                *base,
                "--answers",
                str(answers_path),
                "--seat",
                "claude@sonnet",
                "--family",
                "anthropic",
                "--writer-seat",
                "codex@sol",
                "--writer-family",
                "openai",
            ]
        )
        == 1
    )
    lock.write(questions_path, lock.yaml_bytes(batch))
    assert (
        cli.main(
            [
                "requires-record",
                *base,
                "--answers",
                str(answers_path),
                "--seat",
                "claude@sonnet",
                "--family",
                "anthropic",
                "--writer-seat",
                "codex@sol",
                "--writer-family",
                "openai",
            ]
        )
        == 0
    )
    doc = receipts.read_requirement_receipts(receipts.requirement_receipt_path(state, 1))
    assert doc["requirements_schema"] == 2 and doc["items"][0]["decision"] == "deny"


def test_missing_vesum_fails_as_named_check_not_exception(tmp_path: Path) -> None:
    # The runner wraps the lookup's FileNotFoundError as a check-7 engine failure;
    # this direct checker still exposes the missing dependency for that wrapper.
    item = {
        "kind": "orthography",
        "mode": "orthography",
        "sentence": "м___яч",
        "options": ["'", ""],
        "answer": "'",
        "target_record": "W-5",
    }
    ball = _record(5, "м'яч", [("м'яч", "noun:inanim:m:v_naz")])
    with pytest.raises(FileNotFoundError):
        _check(
            tmp_path,
            item,
            ball,
            typ="fill-in",
            lookup=lambda _words: (_ for _ in ()).throw(FileNotFoundError("VESUM missing")),
        )
