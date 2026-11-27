"""Select verbatim A1 examples from read-only, attributable source rows."""

import hashlib
import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from functools import lru_cache

from scripts.atlas import word_card_assembly as assembly
from scripts.atlas import word_card_assertion_check as checker
from scripts.atlas import word_card_sources as src
from scripts.atlas.a1_card_receipts import canonical
from scripts.atlas.allocate_pilot_identities import label_pos
from scripts.audit.generate_sentence_inventory import UK_TOKEN_RE, WORKSHEET_RE
from scripts.rag.word_identity import normalize_evidence_form
from scripts.wiki.chunking import _UK_ABBREVIATIONS, _last_alpha_token
from scripts.wiki.sum20_mirror import MIRROR_SOURCE_ID

MAX_WORDS = 7  # P95 of the grade-one primer sentences (see the A1 inventory runbook).
MAX_EXAMPLES = 2
TEXTBOOKS = "textbooks"
LITERARY = "literary_corpus"
UKRLIB_URL = "https://www.ukrlib.com.ua/"
SOURCES = ("sum20", TEXTBOOKS, LITERARY)
SENSE_UNDECIDABLE = "example sense not decidable by code"
REGISTER = re.compile(r"(?<!\w)(?:діал|діялект|заст|архаїч|старовин)\.", re.IGNORECASE)
VTS_SENSE_SEPARATOR = re.compile(r"\|\||//|♦|(?<!\d)[0-9]+》")
VTS_SENSE_RANGE = re.compile(r"\b\d+\s*[-–,]\s*\d+\s*\)")
SENTENCE_BREAK = re.compile(r"(?<=[.!?…])\s+|\r?\n[ \t]*\r?\n\s*")
SENTENCE_TEXT = re.compile(r"[А-ЩЬЮЯЄІЇҐ][А-ЩЬЮЯЄІЇҐа-щьюяєіїґ'’ʼ, \-]*[.!?]")
CONTEXT_MARKS = re.compile(r"[«»\"“”„‟‹›\[\]():;…—–]|\.{2,}")
QUOTE_MARKS = re.compile(r'[«»"“”„‟‹›]')
POSSIBLE_HEADING = re.compile(r"[\r\n]\s*[А-ЩЬЮЯЄІЇҐ]")
# Exercise layout around or inside a span marks a task item, not a model
# sentence. A mark detached by whitespace leaves an answer slot. A preceding
# segment that is only a label (an item number such as 5., 107.1., 63°. or
# 487*.; a Roman numeral; one letter; a sequence of them such as 25 І.; a
# capitalized label word with a number such as Крок 2. or Мал. 4.; § or №
# with a number) or only marks (the
# previous item's answer slot) makes the span an exercise item. After the
# span, underscores, empty brackets, two or more marks (a dot leader or blank
# answer lines), or one mark that no word follows is an empty slot or a
# table-of-contents line. One mark or one ellipsis followed by a word is a
# textbook icon or the opening of the next sentence, so the span stays.
DETACHED_MARK = re.compile(r"\s[,.!?]")
LABEL_TOKEN = r"(?:\d+(?:\.\d+)*[°*]*|[IVXLCІХ]+)"
ITEM_LABEL = re.compile(
    rf"(?:\A|\n)[ \t]*(?:"
    rf"(?:[§№][ \t]*|[А-ЩЬЮЯЄІЇҐ][А-ЩЬЮЯЄІЇҐа-щьюяєіїґ'’ʼ-]*\.?[ \t]+)?(?:{LABEL_TOKEN}[ \t]+)*{LABEL_TOKEN}\."
    rf"|(?:{LABEL_TOKEN}[ \t]+)*[А-ЩЬЮЯЄІЇҐа-щьюяєіїґ]\."
    rf"|[.…?!](?:\s*[.…?!])*"
    rf")\Z"
)
# Answer options А–Д open a line or follow a sentence end. A chunk with two
# or more option letters, one of them Б, Г or Д, is an option list; there an
# option opened by А or В is a label, even before a capitalized name.
OPTION_START = re.compile(r"(?m)(?:^[ \t]*|(?<=[.!?…] ))([АБВГД])[ \t]+(?=[А-ЩЬЮЯЄІЇҐ])")
OPTION_SPAN = re.compile(r"[АБВГД][ \t]+[А-ЩЬЮЯЄІЇҐ]")
MARK = r"(?>\.{3}|[.…?!])"
SLOT_AFTER = re.compile(rf"\s*(?:_|\(\s*\)|\[\s*\]|{MARK}(?:\s*{MARK})+|{MARK}(?!\s*[^\W\d_]))")
# One-letter Ukrainian words; any other capital letter opening a span is an
# answer-option label (А–Г lists) or an initial split from its name. A
# one-letter word followed by a capitalized word that VESUM does not attest
# with a capital (not a name) is an option label too, such as В Нам ….
ONE_LETTER_WORDS = frozenset("аівузйоєя")
FUNCTION_LABELS = frozenset({"прийменник", "сполучник", "частка"})
FINITE_VERB_TAGS = frozenset({"pres", "past", "futr", "impr", "impers"})
OBLIQUE_CASES = frozenset({"v_rod", "v_dav", "v_zna", "v_oru", "v_mis"})
DISALLOWED_MARKERS = frozenset({"archaic", "dialect", "arch", *src.HIDDEN_MARKERS})


@dataclass
class ExampleGap:
    lemma: str
    entry_id: int
    pos: str
    forms: frozenset[str]
    senses: tuple[dict, ...]
    values: list[dict] = field(default_factory=list)
    # The count accounts for all rejected candidates. The first locator
    # lets a reviewer retrieve an exact example of each refusal class.
    attempts: dict = field(default_factory=dict)

    def report(self, source, reason, locator=None):
        count, first = self.attempts.get((source, reason), (0, locator))
        self.attempts[source, reason] = (count + 1, first)


def bound_senses(values, vts_source, inputs):
    """Read the sense boundary of the admitted entry, without aligning dictionaries."""
    definitions = [row for row in values if row["field"] == "definition_uk"]
    official = [row for row in definitions if row["source_id"] == "sum20"]
    if official:
        if len(official) != 1:
            return ()
        row, = official
        wordid = row["source_key"].split(":", 1)[0]
        article = inputs.sources.execute("SELECT article_html FROM sum20_articles WHERE wordid=?", (wordid,)).fetchone()
        # The official parser exposes main senses. It does not expose SHD
        # subdivisions as separate senses, so their presence rules out a
        # mechanical single-sense fallback for the prose corpora.
        if not article or re.search(r'\bclass=["\'][^"\']*\bSHD\b', article[0]):
            return ()
        return (row,)
    mirror = [row for row in definitions if row["source_id"] == MIRROR_SOURCE_ID]
    if mirror:
        if len(mirror) != 1:
            return ()
        row, = mirror
        article_id, _, order = row["source_key"].partition(":")
        article = inputs.sources.execute(
            "SELECT senses_json FROM sum20_mirror_articles WHERE id=?", (article_id,),
        ).fetchone()
        if not article or order != "1":
            return ()
        try:
            parsed = json.loads(article[0])
        except (TypeError, ValueError):
            return ()
        if not isinstance(parsed, dict) or parsed.get("entry_type") != "monosemous":
            return ()
        senses = parsed.get("senses")
        if not isinstance(senses, list) or len(senses) != 1 or not isinstance(senses[0], dict):
            return ()
        sense, = senses
        labels = (parsed.get("header_grammar", ""), sense.get("labels", ""))
        if sense.get("sub_senses") or any(not isinstance(label, str) or REGISTER.search(label) for label in labels):
            return ()
        return (row,)
    vts = [row for row in definitions if row["source_id"] == vts_source]
    if len(vts) != 1:
        return ()
    row, = vts
    # ВТС serializes numbered meanings and subordinate meanings explicitly.
    # A single initial 1 marker is allowed. Any other separator makes the
    # whole bound partition insufficient to place an unaligned citation.
    marks = VTS_SENSE_SEPARATOR.findall(row["value"])
    if (marks not in ([], ["1》"]) or row["value"].count("》") != marks.count("1》")
            or VTS_SENSE_RANGE.search(row["value"])):
        return ()
    return (row,)


def surface_readings(inputs):
    """Use VESUM's folded-form index, retaining entry identity and register markers."""
    @lru_cache(maxsize=32_768)
    def read(form):
        rows = [src.row_dict(row) for row in inputs.vesum.execute(
            "SELECT f.id,f.entry_id,f.word_form,f.lemma,f.pos,f.tags,"
            " (SELECT group_concat(marker) FROM (SELECT DISTINCT marker FROM form_markers "
            " WHERE form_id=f.id ORDER BY marker)) AS markers "
            "FROM forms_all AS f WHERE f.word_form_folded=? ORDER BY f.id", (form,),
        )]
        inputs._use(f"projection:example:vesum:{form}", rows)
        return rows

    return read


def a1_reading(row, puls_by_word):
    tags = set(row["tags"].split(":"))
    if "pron" in tags:
        return True
    aspect = src.vesum_aspect_of([row["tags"]])
    levels = set()
    for hit in puls_by_word.get(normalize_evidence_form(row["lemma"]), ()):
        label = hit["pos"] or ""
        pos = label_pos(label) or {"вигук": "intj", "числівник": "numr", "частка": "part"}.get(label)
        if pos == "numr" and hit["guideword"] == "порядковий числівник" and "numr" in tags:
            pos = "adj"
        source_aspect = "imperf" if "(недок.)" in label else "perf" if "(док.)" in label else None
        if (pos == row["pos"] and src.aspect_compatible(source_aspect, aspect)
                and assembly.puls_matches_identity(hit, row["lemma"], "prop" in tags)):
            levels.add(hit["level"])
    return bool(levels) and levels <= {"A1", "A2"}


def needs_antecedent(row):
    tags = set(row["tags"].split(":"))
    demonstrative_manner = row["lemma"] in {"так", "отак"} and "dem" in tags
    third_person_pronoun = row["lemma"] in {"він", "вона", "воно", "вони"} and "pron" in tags
    return demonstrative_manner or (third_person_pronoun and bool(tags & OBLIQUE_CASES))


def self_contained_question(analyses):
    """Keep questions whose speech participants are available in the sentence."""
    tag_sets = [set(row["tags"].split(":")) for rows in analyses for row in rows]
    addresses_reader = any(tags & {"1", "2"} and tags & {"pers", "verb"} for tags in tag_sets)
    points_to_context = any({"pron", "dem"} <= tags and "adj" in tags for tags in tag_sets)
    asks_for_missing_context = any({"pron", "int"} <= tags for tags in tag_sets) and not addresses_reader
    return not (points_to_context or asks_for_missing_context)


def refusal(text, tokens, gap, readings, puls_by_word, *, register=""):
    """Require one exact target reading and elementary support for the surrounding words."""
    if len(tokens) > MAX_WORDS:
        return "example exceeds word limit"
    if REGISTER.search(register):
        return "example has archaic or dialect register"
    if (CONTEXT_MARKS.search(text) or WORKSHEET_RE.search(text) or DETACHED_MARK.search(text)
            or not SENTENCE_TEXT.fullmatch(text)):
        return "example needs context or is not a complete sentence"
    if len(tokens) < 2 or text.isupper() or (len(tokens[0]) == 1 and tokens[0].lower() not in ONE_LETTER_WORDS):
        return "example needs context or is not a complete sentence"

    analyses = []
    for index, word in enumerate(tokens):
        rows = readings(normalize_evidence_form(word))
        # A word at a sentence boundary may be capitalized in the source.
        # Elsewhere, retain the attested case so a common reading cannot
        # stand in for an unrelated name (or vice versa).
        if index or not word.istitle():
            rows = [row for row in rows if row["word_form"].islower() == word.islower()
                    and row["word_form"].isupper() == word.isupper()]
        analyses.append(rows)
    if len(tokens[0]) == 1 and tokens[1][0].isupper() and not analyses[1]:
        return "example needs context or is not a complete sentence"
    target = (gap.entry_id, gap.lemma, gap.pos)
    hits = {index for index, rows in enumerate(analyses) if rows and {
        (row["entry_id"], row["lemma"], row["pos"]) for row in rows
    } == {target}}
    if not hits:
        return "example target entry or part of speech unresolved"
    if any(set((row["markers"] or "").split(",")) & DISALLOWED_MARKERS
           for rows in analyses for row in rows):
        return "example has nonstandard, archaic or dialect morphology"
    # A punctuated list or offcut is common in the corpus. A finite verb is
    # positive, code-verifiable evidence for a standalone sentence.
    if not any(rows and all(row["pos"] == "verb" and FINITE_VERB_TAGS.intersection(row["tags"].split(":"))
                            for row in rows) for rows in analyses):
        return "example needs context or is not a complete sentence"
    if any(needs_antecedent(row) for rows in analyses for row in rows):
        return "example needs context or is not a complete sentence"
    if text.endswith("?") and not self_contained_question(analyses):
        return "example needs context or is not a complete sentence"
    if any(not rows or any(not a1_reading(row, puls_by_word) for row in rows)
           for index, rows in enumerate(analyses) if index not in hits):
        return "example word outside verified A1–A2"
    if len(gap.senses) != 1:
        return SENSE_UNDECIDABLE
    return None


def sentence_spans(chunk):
    """Yield whole punctuated spans, with offsets into the unmodified source row."""
    start = 0
    inside_quote = False
    previous = ""
    options = set(OPTION_START.findall(chunk))
    option_list = len(options) > 1 and bool(options & {"Б", "Г", "Д"})
    for boundary in [*SENTENCE_BREAK.finditer(chunk), None]:
        end = boundary.start() if boundary else len(chunk)
        segment = chunk[start:end]
        raw = segment.strip()
        if boundary and _last_alpha_token(raw).lower() in _UK_ABBREVIATIONS:
            continue
        if raw:
            begin = start + len(segment) - len(segment.lstrip())
            quotes = QUOTE_MARKS.findall(raw)
            exercise = (ITEM_LABEL.search(previous) or SLOT_AFTER.match(chunk, begin + len(raw))
                        or (option_list and OPTION_SPAN.match(raw)))
            yield begin, begin + len(raw), bool(inside_quote or quotes or POSSIBLE_HEADING.search(raw) or exercise)
            previous = raw
            if len(quotes) % 2:
                inside_quote = not inside_quote
        if boundary:
            start = boundary.end()


def source_rows(inputs, source, books):
    """Pair corpus chunks with attributable, modern publication records."""
    if source == TEXTBOOKS:
        rows = inputs.sources.execute(
            "SELECT id,chunk_id,source_file,title,text,grade FROM textbooks "
            "WHERE grade IN ('1','2','3','4','5','6','7','8','9','10','11') "
            "ORDER BY CAST(grade AS INTEGER),source_file,id",
        )
        for row in rows:
            book = books.get(row["source_file"])
            if (not book or book.get("kind") != "textbook" or book.get("grade") != int(row["grade"])
                    or not isinstance(book.get("year"), int) or book["year"] < 1991
                    or not book.get("author") or not book.get("title")):
                continue
            label = f"{book['author']} · {book['title']} ({book['year']})"
            if book.get("part"):
                label += f" · {book['part']}"
            if row["title"]:
                label += f" · {row['title']}"
            yield row, label
        return
    for row in inputs.sources.execute(
        "SELECT id,chunk_id,source_file,text,author,work,work_id,source_url FROM literary_texts "
        "WHERE language_period='modern' AND genre IN ('prose','fable') "
        "AND source_file GLOB 'ukrlib-*' ORDER BY source_file,id"
    ):
        if all(row[key] and row[key].strip() for key in ("author", "work", "work_id")):
            yield row, f"{row['author']} · {row['work']}"


def search_corpora(gaps, inputs, register, books, puls_by_word):
    """Scan each registered corpus once in priority order using exact VESUM form keys."""
    readings = surface_readings(inputs)
    for source in (TEXTBOOKS, LITERARY):
        record = checker.canonical_source(source, register)
        decision = checker.check_entry_projection(
            "examples", source, "source_sense", register, source_label=record.get("name") if record else None,
        )
        waiting = []
        for gap in gaps:
            if len(gap.values) < MAX_EXAMPLES:
                waiting.append(gap)
            elif source != TEXTBOOKS:
                gap.report(source, "filled from preferred source")
        if not waiting:
            continue
        if decision != "supported":
            for gap in waiting:
                gap.report(source, decision)
            continue

        by_form = defaultdict(set)
        for index, gap in enumerate(waiting):
            for form in gap.forms:
                by_form[form].add(index)
        found = set()
        source_hash = hashlib.sha256()
        table = "textbooks" if source == TEXTBOOKS else "literary_texts"
        for row, label in source_rows(inputs, source, books):
            if not row["chunk_id"]:
                continue
            source_hash.update(canonical([src.row_dict(row), label]) + b"\n")
            chunk = row["text"]
            for start, end, needs_context in sentence_spans(chunk):
                raw = chunk[start:end]
                unstressed = raw.replace(src.ACUTE, "")
                text = " ".join(unstressed.split())
                tokens = UK_TOKEN_RE.findall(text)
                forms = tuple(map(normalize_evidence_form, tokens))
                matching = set().union(*(by_form.get(form, ()) for form in forms))
                for index in sorted(matching):
                    gap = waiting[index]
                    if len(gap.values) == MAX_EXAMPLES:
                        continue
                    found.add(index)
                    locator = f"{table}:{row['source_file']}:{row['chunk_id']}:{row['id']} [text:{start}:{end}]"
                    if any(forms == tuple(map(normalize_evidence_form, UK_TOKEN_RE.findall(item["value"])))
                           for item in gap.values):
                        gap.report(source, "duplicate source sentence", locator)
                        continue
                    register_text = " ".join(sense["value"] for sense in gap.senses)
                    reason = ("example needs context or is not a complete sentence" if needs_context else
                              refusal(text, tokens, gap, readings, puls_by_word, register=register_text))
                    if reason:
                        gap.report(source, reason, locator)
                        continue
                    decision = checker.check_entry_projection(
                        "examples", source, "source_sense", register, source_label=label,
                    )
                    if decision != "supported":
                        gap.report(source, decision, locator)
                        continue
                    sense, = gap.senses
                    gap.values.append({"field": "examples", "source_id": source, "source_label": label,
                                       "locator": locator, "scope": "source_sense", "source_key": sense["source_key"],
                                       "value": text, "evidence": {"normalization": {
                                           "whitespace": " ".join(raw.split()) != raw,
                                           "stress_marks": unstressed != raw,
                                       }, "sense_source": sense["source_id"], "sense_locator": sense["locator"]}})
        inputs._use(f"projection:examples:{source}", source_hash.hexdigest())
        for index, gap in enumerate(waiting):
            if index not in found:
                gap.report(source, "no source sentence with a VESUM target form")
