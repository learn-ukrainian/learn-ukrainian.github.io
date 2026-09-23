"""Real-data group: the resolver against the real VESUM, trie and word-store builder.

Skipped only when data/sources.db or data/vesum.db is absent (resolved by Sources()'s
main-root rule, never a relative path). Records are built by the canonical word-store
builder (`words.build_words`, dry run) from VESUM entries; no form, stress or gloss is
typed here — the only Ukrainian in this file is the spellings being looked up.

Replay of the Codex seat's measurement: textbook_sections 6286 (ULP lesson 10), the
bilingual story only, one unit per non-empty line, stress stripped, apostrophes
normalised. A change that moves these numbers must be reported, not hidden.
"""

from __future__ import annotations

from contextlib import closing
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
    assert by_class[codes.STRESS_OPEN] == ["зараз"]
    assert len(by_class[codes.STRESS_CERTAIN_IDENTITY_OPEN]) == 15
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
    assert len(zaraz["candidates"]) == 2 and "pending" in zaraz["message"]
    vona = next(t for t in cyrillic if t["token"] == "Вона")
    assert vona["class"] == codes.RESOLVED and vona["surface"] == codes.SENTENCE_TOKEN
    assert stream.reports == []

    assert stream.to_bytes() == resolve(story, allowed, src).to_bytes()
    batch = build_questions(stream, story, allowed)
    validate_questions(batch)
    assert len(batch["questions"]) == 16 and [q["token"] for q in batch["questions"] if q["blocking"]] == ["зараз"]


def test_named_real_cases(real, store):
    src = real[0]
    zamok = _records(store, real, "замок", pos="noun")
    assert len(zamok) == 2
    # The trie cannot split the homograph by tags and ULIF has no entry: both records are pending.
    assert _classes(resolve(_doc("замок"), Allowlist.from_records(zamok), src), "замок") == [codes.PENDING_STRESS]

    zaraz = resolve(_doc("зараз"), Allowlist.from_records(_records(store, real, "зараз", pos="adv")), src)
    assert _classes(zaraz, "зараз") == [codes.RESOLVED]

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
