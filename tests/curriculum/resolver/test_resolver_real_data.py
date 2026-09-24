"""Real-data group: the resolver against the real VESUM, trie and word-store builder.

Skipped only when data/sources.db or data/vesum.db is absent (resolved by Sources()'s
main-root rule, never a relative path). Records are built by the canonical word-store
builder (`words.build_words`, dry run) from VESUM entries; no form, stress or gloss is
invented here. The two expected stress readings for `зараз` are checked against
the sources oracle and the ULIF paradigm.

Replay of the Codex seat's measurement: textbook_sections 6286 (ULP lesson 10), the
bilingual story only, one unit per non-empty line, stress stripped, apostrophes
normalised. A change that moves these numbers must be reported, not hidden.
"""

from __future__ import annotations

from contextlib import closing
from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from scripts.curriculum.evidence import sources as sources_module
from scripts.curriculum.evidence import words
from scripts.curriculum.resolver import codes
from scripts.curriculum.resolver.inputs import Allowlist, ExpandedDocument
from scripts.curriculum.resolver.narrow import lower_first
from scripts.curriculum.resolver.questions import build_questions, validate_questions
from scripts.curriculum.resolver.stream import resolve
from scripts.curriculum.resolver.tokenize import Token, tokenize
from scripts.verification import vesum

_PROBE = sources_module.Sources()
HAVE_DATA = _PROBE.sources_db.is_file() and Path(_PROBE.vesum_db).is_file()
pytestmark = pytest.mark.skipif(not HAVE_DATA, reason="requires the real data/sources.db and data/vesum.db")

SECTION_ID = 6286
SOURCE_FILE = "ulp-1-00-lesson-notes"
STORY_FIRST = "Приві́т! Як спра́ви?"
STORY_LAST = "Розкажі́ть!"
# Spellings the brief's named cases need beyond the story.
EXTRA_SPELLINGS = ("стіл", "Київ", "український", "по-українськи", "м'ясо", "ласка", "замок", "будь-ласка")


def orthographic_key(token: Token) -> str:
    """How a reader looks a token up: a sentence-initial capital is orthographic."""
    return lower_first(token.lookup) if token.sentence_initial and token.capitalised else token.lookup


def union_keys(token: Token) -> list[str]:
    return list(dict.fromkeys([token.lookup, orthographic_key(token)]))


@pytest.fixture(scope="module")
def real():
    src = sources_module.Sources()
    with closing(sources_module.open_readonly(src.sources_db)) as conn:
        row = conn.execute(
            "SELECT source_file, full_text FROM textbook_sections WHERE section_id = ?", (SECTION_ID,)
        ).fetchone()
    assert row is not None and row["source_file"] == SOURCE_FILE
    lines = row["full_text"].splitlines()
    first = next(i for i, line in enumerate(lines) if STORY_FIRST in line)
    last = next(i for i, line in enumerate(lines) if STORY_LAST in line)
    units = []
    for number in range(first, last + 1):
        text = sources_module.normalize_spelling(words.strip_combining_stress(lines[number]))
        if text.strip():
            units.append(
                {"tab": "urok", "activity": None, "item": None, "block": number + 1, "role": "narration", "text": text}
            )
    story = ExpandedDocument.from_data({"lesson": {"level": "ulp", "slug": "lesson-10", "n": 10}, "units": units})

    story_keys = [orthographic_key(t) for u in story.units for t in tokenize(u.text) if t.kind == "cyrillic"]
    wanted = list(dict.fromkeys([*story_keys, *EXTRA_SPELLINGS]))
    analyses = src.verify_words(wanted).raw
    marked = {"будь-ласка"}  # its only analysis is `bad`, absent from verify_words' clean view
    entries: dict[str, list[int]] = {}
    request, seen = [], set()
    for spelling in wanted:
        pairs = {(a["lemma"], a["pos"]) for a in analyses[spelling]}
        if spelling in marked:
            inspected = vesum.inspect_word(spelling, db_path=src.vesum_db).as_dict()
            pairs |= {(a["lemma"], a["pos"]) for a in inspected["marked_analyses"]}
        for lemma, pos in sorted(pairs):
            paradigm = src.inspect_lemma_forms(lemma, pos)
            for entry_id, forms in sorted(paradigm.forms_by_entry.items()):
                if any(f["word_form"] == spelling for f in forms):
                    entries.setdefault(spelling, []).append(entry_id)
                    if entry_id not in seen:
                        seen.add(entry_id)
                        request.append(
                            {
                                "lemma": lemma,
                                "pos": pos,
                                "want": "new",
                                "entry": {"source": "vesum", "entry_id": entry_id},
                            }
                        )
    return src, story, analyses, entries, request


@pytest.fixture(scope="module")
def store(real, tmp_path_factory):
    src, _story, _analyses, _entries, request = real
    root = tmp_path_factory.mktemp("real-store")
    request_path = root / "request.yaml"
    request_path.write_text(
        yaml.safe_dump({"request_schema": 1, "level": "ulp-replay", "words": request}, allow_unicode=True),
        encoding="utf-8",
    )
    result = words.build_words(
        "ulp-replay",
        request_path,
        evidence_dir=root / "evidence",
        plans_dir=root / "plans",
        sources_instance=src,
        dry_run=True,
        mcp_commit="0" * 40,
    )
    return result["store"]


def _records(store, real, *spellings: str, pos: str | None = None) -> list[dict]:
    entries = {e for spelling in spellings for e in real[3].get(spelling, [])}
    return [w for w in store["words"] if w["entry"]["entry_id"] in entries and (pos is None or w["pos"] == pos)]


def _doc(*texts: str) -> ExpandedDocument:
    units = [
        {"tab": "urok", "activity": None, "item": None, "block": i, "role": "narration", "text": t}
        for i, t in enumerate(texts)
    ]
    return ExpandedDocument.from_data({"lesson": {"level": "ulp", "slug": "real-cases", "n": 1}, "units": units})


def _classes(stream, text: str) -> list[str]:
    return [t["class"] for t in stream.tokens if t["token"] == text]


def _assert_zaraz_contract(token: dict, allowed: Allowlist, *, noun_checked: bool) -> None:
    """The noun's ULIF paradigm resolves its stress only after that group is checked."""
    assert token["class"] == codes.STRESS_OPEN
    assert token["selected"] is None and token["provenance"] is None
    assert len(token["candidates"]) == len(token["readings"]) == 2
    assert set(token["candidates"]) == {r["record"] for r in token["readings"]}
    for reading in token["readings"]:
        assert {"record", "stressed", "stress_source", "forms"} <= reading.keys()
        assert reading["record"] in allowed.records and reading["forms"]
    by_lemma = {allowed.records[r["record"]]["lemma"]: r for r in token["readings"]}
    assert set(by_lemma) == {"зараз", "зараза"}
    assert by_lemma["зараз"]["stressed"] == "за́раз"
    assert by_lemma["зараз"]["stress_source"] in {"trie", "ulif"}
    noun = by_lemma["зараза"]
    if noun_checked:
        assert noun["stressed"] == "зара́з" and noun["stress_source"] == "ulif"
        assert "message" not in token
    else:
        assert noun["stressed"] is None and noun["stress_source"] == "pending"
        assert noun["record"] in token["message"] and "pending" in token["message"]


def test_ulp_lesson_10_replay(real, store):
    src, story, analyses, _entries, _request = real
    tokens = [t for u in story.units for t in tokenize(u.text) if t.kind == "cyrillic"]
    assert len(tokens) == 91
    # Reader's lookup (the Codex seat's 41) and, for the record, the union with the capitalised spelling.
    assert sum(1 for t in tokens if len(analyses[orthographic_key(t)]) > 1) == 41
    union = src.verify_words([k for t in tokens for k in union_keys(t)]).raw
    assert sum(1 for t in tokens if sum(len(union[k]) for k in union_keys(t)) > 1) == 42

    allowed = Allowlist.from_records(store["words"], gloss_ids={w["id"] for w in store["words"]}, label="ulp-replay")
    stream = resolve(story, allowed, src)
    cyrillic = [t for t in stream.tokens if not t["class"].startswith(codes.SKIPPED_PREFIX)]
    assert len(cyrillic) == 91
    by_class: dict[str, list[str]] = {}
    for token in cyrillic:
        by_class.setdefault(token["class"], []).append(token["token"])
    assert "зараз" in by_class[codes.STRESS_OPEN]
    assert by_class[codes.LEMMA_OUTSIDE_STATE] == ["Огойко"]
    outside = next(t for t in cyrillic if t["class"] == codes.LEMMA_OUTSIDE_STATE)
    assert outside["surface"] == codes.PROPER_NOUN
    # The word store stores zero-vowel prepositions as pending (its monosyllable gate counts
    # exactly one vowel); the resolver reports that, it does not repair it.
    assert sorted(by_class[codes.PENDING_STRESS]) == ["в", "в", "в", "в", "з"]
    assert set(by_class) == {
        codes.RESOLVED,
        codes.STRESS_OPEN,
        codes.STRESS_CERTAIN_IDENTITY_OPEN,
        codes.LEMMA_OUTSIDE_STATE,
        codes.PENDING_STRESS,
    }
    zaraz = next(t for t in cyrillic if t["token"] == "зараз")
    noun_group = src.ulif_entries(["зараза"]).raw["зараза"]
    noun_checked = src.ulif_group_checked(noun_group)
    noun_record = next(w for w in store["words"] if w["lemma"] == "зараза" and w["pos"] == "noun")
    assert isinstance(noun_record["ulif"], dict) == noun_checked
    _assert_zaraz_contract(zaraz, allowed, noun_checked=noun_checked)
    vona = next(t for t in cyrillic if t["token"] == "Вона")
    assert vona["class"] == codes.RESOLVED and vona["surface"] == codes.SENTENCE_TOKEN
    assert stream.reports == []

    assert stream.to_bytes() == resolve(story, allowed, src).to_bytes()
    batch = build_questions(stream, story, allowed)
    validate_questions(batch)
    open_tokens = [t for t in cyrillic if t["class"] in codes.OPEN_CLASSES]
    assert len(batch["questions"]) == len(open_tokens)
    assert [q["token"] for q in batch["questions"]] == [t["token"] for t in open_tokens]
    assert [q["token"] for q in batch["questions"] if q["blocking"]] == by_class[codes.STRESS_OPEN]


@pytest.mark.parametrize("noun_checked", [False, True])
def test_zaraz_checked_and_unchecked_contract(real, store, noun_checked):
    # Replay both word-store states even when the live walk has reached one of them.
    records = deepcopy(_records(store, real, "зараз"))
    noun = next(w for w in records if w["lemma"] == "зараза" and w["pos"] == "noun")
    forms = [f for f in noun["forms"] if f["form"] == "зараз" and f["learner"]]
    assert len(forms) == 1
    if noun_checked:
        forms[0]["stressed"] = "зара́з"
        forms[0]["stress_source"] = "ulif"
    else:
        forms[0].pop("stressed", None)
        forms[0]["stress_source"] = "pending"
    allowed = Allowlist.from_records(records)
    document = _doc("зараз")
    stream = resolve(document, allowed, real[0])
    token = stream.tokens[0]
    _assert_zaraz_contract(token, allowed, noun_checked=noun_checked)
    questions = build_questions(stream, document, allowed)
    validate_questions(questions)
    assert len(questions["questions"]) == 1
    assert questions["questions"][0]["token"] == "зараз"
    assert questions["questions"][0]["blocking"] is True
    assert {c["stressed"] for c in questions["questions"][0]["candidates"]} == (
        {"за́раз", "зара́з"} if noun_checked else {"за́раз", None}
    )


def test_named_real_cases(real, store):
    src = real[0]
    zamok = _records(store, real, "замок", pos="noun")
    assert len(zamok) == 2
    # The trie cannot split the homograph by tags; the requested VESUM entries
    # do not select one of its three ULIF homonyms, so both records are pending.
    assert _classes(resolve(_doc("замок"), Allowlist.from_records(zamok), src), "замок") == [codes.PENDING_STRESS]

    zaraz = resolve(_doc("зараз"), Allowlist.from_records(_records(store, real, "зараз", pos="adv")), src)
    assert _classes(zaraz, "зараз") == [codes.RESOLVED]
    assert zaraz.tokens[0]["selected"]["stressed"] == "за́раз"

    laska = _records(store, real, "ласка")
    stream = resolve(_doc("ласка"), Allowlist.from_records(laska), src)
    assert len(laska) == 2 and _classes(stream, "ласка") == [codes.STRESS_CERTAIN_IDENTITY_OPEN]
    assert build_questions(stream, _doc("ласка"), Allowlist.from_records(laska))["questions"][0]["blocking"] is False

    stil = resolve(_doc("стіл"), Allowlist.from_records(_records(store, real, "стіл")), src).tokens[0]
    assert stil["class"] == codes.RESOLVED and len(stil["selected"]["forms"]) == 2

    compound = resolve(_doc("по-українськи"), Allowlist.from_records(_records(store, real, "по-українськи")), src)
    assert [t["class"] for t in compound.tokens] == [codes.RESOLVED]

    meat = Allowlist.from_records(_records(store, real, "м'ясо"))
    spellings = resolve(_doc("м'ясо м’ясо мʼясо"), meat, src).tokens
    assert {t["lookup"] for t in spellings} == {"м'ясо"} and {t["class"] for t in spellings} == {codes.RESOLVED}

    bad = _records(store, real, "будь-ласка")
    marked = resolve(_doc("будь-ласка"), Allowlist.from_records(bad), src).tokens
    assert [t["class"] for t in marked] == [codes.LEMMA_OUTSIDE_STATE] and marked[0]["marked"]
    parts = resolve(_doc("будь-ласка"), Allowlist.from_records(_records(store, real, "ласка")), src).tokens
    assert [t["class"] for t in parts] == [codes.LEMMA_OUTSIDE_STATE]
    assert parts[0]["analyses"]["будь"] and parts[0]["analyses"]["ласка"]

    kyiv = _records(store, real, "Київ", pos="noun")
    kyiv_stream = resolve(_doc("Київ — столиця."), Allowlist.from_records(kyiv), src)
    first = kyiv_stream.tokens[0]
    assert first["surface"] == codes.PROPER_NOUN and first["class"] == codes.RESOLVED
    assert first["selected"]["record"] in {w["id"] for w in kyiv if w["lemma"][:1].isupper()}

    vona = _records(store, real, "вона")
    token = resolve(_doc("Вона працює."), Allowlist.from_records(vona), src).tokens[0]
    assert token["class"] == codes.RESOLVED and token["surface"] == codes.SENTENCE_TOKEN
    assert not store_lemma(store, token["selected"]["record"])[:1].isupper()

    adj = resolve(_doc("Це український."), Allowlist.from_records(_records(store, real, "український", pos="adj")), src)
    assert _classes(adj, "український") == [codes.RESOLVED]
    assert next(t for t in adj.tokens if t["token"] == "український")["surface"] == codes.SENTENCE_TOKEN


def store_lemma(store, record_id: str) -> str:
    return next(w["lemma"] for w in store["words"] if w["id"] == record_id)
