"""Local dictionary witnesses for already-resolved pilot lexemes.

Dictionary partitions never decide VESUM/ULIF identity. Complete article text is
retained verbatim on an allocated unsplit sense, without cross-source sense
alignment. Ambiguous or incomplete witnesses stay in the accounting report.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from scripts.atlas import word_card_foundation as foundation
from scripts.atlas import word_card_sources as src
from scripts.storage.topology import store_locality
from scripts.wiki import sum20_mirror

SOURCES = ("sum20", "sum20_slovnyk_mirror", "vts_busel_slovnyk_me")
VERSION = "pilot-meanings-v3"
HEAD_TOKEN = re.compile(r"[А-Яа-яІіЇїЄєҐґ'’ʼ`́-]+")
SOURCE_TAIL = re.compile(r"\s+Джерело:.*$", re.IGNORECASE | re.DOTALL)


def key(text: str) -> str:
    return src.unstressed(text).casefold()


def vts_stress(text: str) -> str:
    # The mirror uses both combining acute and a backtick BEFORE its vowel.
    return src.nfc(re.sub(r"`([аеєиіїоуюяАЕЄИІЇОУЮЯ])", r"\1́", text))


def grammar_pos(text: str) -> str | None:
    """Only explicit dictionary grammar, never a guess from the definition."""
    text = text.casefold()
    for pattern, pos in (
        (r"\bзайм\.", "noun"), (r"\bприсл\.", "adv"),
        (r"\b(?:недок|док)\.", "verb"), (r"\bприкм\.", "adj"),
        (r"\bчисл\.", "numr"), (r"\bприйм\.", "prep"),
        (r"\bспол\.", "conj"), (r"\bчаст\.", "part"),
        (r"\bвиг\.", "intj"), (r"(?:^|[ ,])(?:ч|ж|с|мн)\.", "noun"),
        (r"(?:^|[ ,])-?а,\s*-?е\.", "adj"),
    ):
        if re.search(pattern, text):
            return pos
    return None


def vts_partitions(text: str, spelling: str) -> list[dict]:
    """Retain source-local Roman partitions only when their headers are explicit.

    A bare Roman marker or an implicit head cannot establish a lexeme. Such an
    article is held whole rather than distributing its meanings by ordinal.
    Offsets address the authenticated full cache text, before any normalization.
    """
    lookup = re.match(rf"\s*{re.escape(spelling)}\s+", text, re.IGNORECASE)
    start = lookup.end() if lookup else 0
    footer = SOURCE_TAIL.search(text)
    end = footer.start() if footer else len(text)
    markers = list(re.compile(r"(?<!\S)[IVX]+(?=\s)").finditer(text, start, end))
    if not markers:
        spans = [(start, end)]
    else:
        # Inline references also contain Roman numerals. Without markup these
        # cannot safely be distinguished from implicit homonym headers.
        spans = [(m.start(), markers[i + 1].start() if i + 1 < len(markers) else end)
                 for i, m in enumerate(markers)]
        if any(not re.match(r"[IVX]+\s+\S+", text[a:b]) for a, b in spans):
            return []
    out = []
    for start, end in spans:
        while start < end and text[start].isspace():
            start += 1
        while start < end and text[end - 1].isspace():
            end -= 1
        body = text[start:end]
        header = re.sub(r"^[IVX]+\s+", "", body)
        tokens = header.split()
        head = re.match(r"[А-Яа-яІіЇїЄєҐґ'’`́-]+", tokens[0]) if tokens else None
        stressed = vts_stress(head[0]) if head else ""
        # Some headers join the inflection suffix directly to the headword.
        while key(stressed) != spelling and "-" in stressed:
            stressed = stressed.rsplit("-", 1)[0]
        if key(stressed) != spelling:
            return []
        grammar = header[header.find(head[0]) + len(stressed):] if head else ""
        grammar = re.sub(r"^\s*1》\s*", "", grammar)
        grammar = re.split(r"\d+》", grammar, maxsplit=1)[0]
        # Only the grammar prefix before the first full stop belongs to the
        # header. Include that stop so abbreviated POS labels remain available.
        grammar = grammar.partition(".")[0] + "."
        out.append({"text": body, "head": stressed, "pos": grammar_pos(grammar),
                    "aspect": "imperf" if "недок." in grammar else "perf" if "док." in grammar else None,
                    "partition": body.split()[0] if markers else "article", "span": [start, end]})
    return out


def mirror_partition(row: dict, spelling: str) -> dict:
    """The article body of one served СУМ-20 mirror row, bounded like the ВТС spans.

    The page repeats its headword before the article and appends a source
    footer; neither belongs to the witness. The head is the article's first
    word, and the grammar is the text up to its first full stop. A head that does
    not spell the card's lexeme leaves the partition unresolved.
    """
    text = row["article_text"]
    lookup = re.match(rf"\s*{re.escape(row['headword'])}\s+", text, re.IGNORECASE)
    start = lookup.end() if lookup else 0
    footer = SOURCE_TAIL.search(text, start)
    end = footer.start() if footer else len(text)
    body = text[start:end].strip()
    start = text.index(body, start) if body else start
    head = HEAD_TOKEN.match(body)
    stressed = src.nfc(head[0].lower()) if head else ""
    if not body or key(stressed) != spelling:
        return {"text": None, "head": "", "pos": None, "aspect": None, "partition": "unresolved", "span": [0, 0],
                "reason": "source_partition_unresolved"}
    grammar = body[len(head[0]):].partition(".")[0] + "."
    return {"text": body, "head": stressed, "pos": grammar_pos(grammar),
            "aspect": "imperf" if "недок." in grammar else "perf" if "док." in grammar else None,
            "partition": "article", "span": [start, start + len(body)], "reason": None}


def full_vts(row: dict, root: Path | None) -> tuple[str | None, str | None]:
    """Authenticate the admitted full witness; never fetch or follow a reference."""
    text = row["text"]
    digest = row["content_sha256"]
    if hashlib.sha256(text.encode()).hexdigest() == digest:
        return text, None
    relative = Path(row["cache_path"])
    if root is None or relative.parts[:3] != ("data", "lexicon", "slovnyk_cache") or len(relative.parts) != 4:
        return None, "full_source_unavailable"
    path = root / relative
    if not path.resolve().is_relative_to((root / "data/lexicon/slovnyk_cache").resolve()) \
            or store_locality(path) != "local":
        return None, "full_source_unavailable"
    try:
        lookup = json.loads(path.read_text())["lookups"]["vts"]
        text = lookup["text"]
        if (lookup["dictionary_slug"], lookup["source_url"], key(lookup["word"])) != (
                "vts", row["source_url"], row["normalized_word"]):
            return None, "source_snapshot_mismatch"
        if hashlib.sha256(text.encode()).hexdigest() != digest:
            return None, "source_snapshot_mismatch"
    except (OSError, ValueError, KeyError, TypeError):
        return None, "full_source_unavailable"
    return text, None


def candidates(sources: src.PilotSources, spelling: str) -> dict[str, list[dict]]:
    """Exact local lookups, including negative results in the consumed ledger."""
    out = {source: [] for source in SOURCES}
    articles = [src.row_dict(r) for r in sources.sources.execute(
        "SELECT * FROM sum20_articles WHERE lower(headword)=? OR normalized_lookup_key=? ORDER BY id",
        (spelling, spelling))]
    sources._use(f"meaning:sum20:{spelling}", articles)
    for row in articles:
        senses = [src.row_dict(r) for r in sources.sources.execute(
            "SELECT * FROM sum20_senses WHERE article_id=? ORDER BY sense_order,id", (row["id"],))]
        sources._use(f"meaning:sum20_senses:{row['id']}", senses)
        grammar = row["grammar"]
        out["sum20"].append({"row": row, "head": row["stressed_headword"].lower(),
            "pos": grammar_pos(grammar), "aspect": "imperf" if "недок." in grammar else
            "perf" if "док." in grammar else None, "text": row["article_text"],
            "partition": str(row["wordid"]), "reason": "source_quarantined" if row["quarantine_reason"] else None,
            "locator": f"sum20:sum20_articles:id:{row['id']} [article_text]",
            "snapshot": "sum20-article@sha256:" + foundation.digest({"article": row, "senses": senses}),
            "url": row["official_url"]})
    # Only the mirror rows sum20-mirror-rule-v1 serves: an agreeing row adds nothing to the official one.
    served = sum20_mirror.served_rows(sources.sources, sum20_mirror.mirror_key(spelling))
    sources._use(f"meaning:sum20_mirror:{spelling}", [[row, relation] for row, relation in served])
    for row, relation in served:
        part = mirror_partition(row, spelling)
        start, end = part["span"]
        out["sum20_slovnyk_mirror"].append({**part, "row": row, "relation": relation,
            "locator": f"sum20_slovnyk_mirror:sum20_mirror_articles:id:{row['id']} [article_text:{start}:{end}]",
            "snapshot": "sum20-mirror-article@sha256:" + foundation.digest(row), "url": row["source_url"]})
    rows = [src.row_dict(r) for r in sources.sources.execute(
        "SELECT * FROM slovnyk_me_entries WHERE dictionary_slug='vts' AND normalized_word=? ORDER BY id",
        (spelling,))]
    sources._use(f"meaning:vts:{spelling}", rows)
    for row in rows:
        text, reason = full_vts(row, sources.meaning_cache_root)
        sources._use(f"meaning:vts_full:{row['id']}", {"text": text, "reason": reason})
        partitions = vts_partitions(text, spelling) if text else []
        if not partitions:
            partitions = [{"text": None, "head": "", "pos": None, "aspect": None,
                           "partition": "unresolved", "span": [0, 0]}]
            reason = reason or "source_partition_unresolved"
        for part in partitions:
            start, end = part["span"]
            out["vts_busel_slovnyk_me"].append({**part, "row": row, "reason": reason,
                "locator": f"vts_busel_slovnyk_me:slovnyk_me_entries:id:{row['id']} [full_text:{start}:{end}]",
                "snapshot": "vts-article@sha256:" + foundation.digest(row), "url": row["source_url"]})
    return out


def correspondence(candidate: dict, homonyms: dict, entry_id: int) -> bool:
    """Both sides must uniquely support this already-established lexeme."""
    if candidate["reason"] or not candidate["text"] or not candidate["pos"]:
        return False
    head = candidate["head"].casefold()
    compatible = []
    for eid, h in homonyms.items():
        row = h["row"]
        from scripts.atlas.allocate_pilot_identities import label_pos
        if label_pos(row["grammatical_label"]) != candidate["pos"]:
            continue
        if candidate["aspect"] and candidate["aspect"] != h["aspect"]:
            continue
        readings = {s.casefold() for s in src.stress_forms(h["head"])}
        if key(head) != key(h["head"]):
            continue
        if src.ACUTE in head and not readings.intersection(s.casefold() for s in src.stress_forms(head)):
            continue
        compatible.append(eid)
    return compatible == [entry_id]


def select(sources: src.PilotSources, spelling: str, homonyms: dict, entry_id: int,
           identity_resolved: bool, proper: bool) -> dict:
    """Availability and correspondence are separate, including for unresolved identities."""
    result = {}
    for source, rows in candidates(sources, spelling).items():
        selected = [c for c in rows if correspondence(c, homonyms, entry_id)]
        reason = ("identity_unresolved" if not identity_resolved else "proper_identity_unresolved" if proper else
                  "source_absent" if not rows else None)
        if reason is None and len(selected) != 1:
            reason = next((c["reason"] for c in rows if c["reason"]), "source_correspondence_unresolved")
        if reason is None and any(c["reason"] or not c["pos"] for c in rows):
            reason = "source_correspondence_unresolved"
        result[source] = {"has": bool(rows), "reason": reason,
                          "witness": selected[0] if reason is None else None}
    return result
