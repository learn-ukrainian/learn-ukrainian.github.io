"""Build and replay the host-only A1 word-card preview and parity ledger."""

import hashlib
import json
import re
import subprocess
from collections import Counter, defaultdict
from contextlib import ExitStack
from dataclasses import asdict, dataclass
from html import escape
from typing import Literal
from urllib.parse import quote

from lu_machinery.storage.topology import store_data_dir

from scripts.atlas import a1_card_examples as examples
from scripts.atlas import word_card_assembly as assembly
from scripts.atlas import word_card_assertion_check as checker
from scripts.atlas import word_card_foundation as foundation
from scripts.atlas import word_card_meanings as meanings
from scripts.atlas import word_card_sources as src
from scripts.atlas.a1_card_capture import _entry_candidates, _group_text, _paradigm, _tag_list
from scripts.atlas.a1_card_receipts import Refusal, canonical, digest
from scripts.atlas.allocate_pilot_identities import is_proper_name, label_pos
from scripts.atlas.atlas_db import ENRICHMENT_SECTIONS
from scripts.lexicon.enrich_manifest import _slovnyk_ukreng_glosses
from scripts.lexicon.runner.ulif_dictua_parse import (
    normalize_ulif_spelling,
    parse_ulif_entry,
    parse_ulif_relation_groups,
)
from scripts.rag.word_identity import normalize_evidence_form
from scripts.wiki.sources_db import _fold_dict_key
from scripts.wiki.sum20_mirror import MIRROR_ATTRIBUTION_LABEL, MIRROR_ONLY, MIRROR_SOURCE_ID
from scripts.wiki.sum20_official import Sum20ParseError, parse_sum20_article

OWNER = "codex-atlas"
GROUPS = ("synonyms", "antonyms", "phraseology")
REQUIRED = ("stress", "pos", "paradigm", "definition_uk", "gloss_en", "cefr", "examples")
VTS = "vts_busel_slovnyk_me"
VTS_NOT_CAPTURED = "ВТС not captured"
REGISTER_LABEL = object()
GAP_SOURCES = {
    "stress": ("ulif", "vesum", "sum20", MIRROR_SOURCE_ID),
    "pos": ("vesum",),
    "gender": ("vesum",),
    "aspect": ("vesum",),
    "paradigm": ("vesum", "ulif"),
    "definition_uk": ("sum20", MIRROR_SOURCE_ID, VTS),
    "gloss_en": ("dmklinger", "slovnyk_me"),
    "cefr": ("puls",),
    "examples": examples.SOURCES,
}
# These VESUM tags name displayed forms outside the core inflection
# signature. Do not use them to match a VESUM entry to a ULIF homonym.
VESUM_EXTRA_SLOTS = {"verb": {"impers"}, "adv": {"compc", "comps"}}


@dataclass(frozen=True)
class EntryValue:
    field: str
    source_id: str
    source_label: str
    locator: str
    value: str | dict | list
    scope: Literal["entry", "source_sense", "source_group", "slot", "context"] = "entry"
    source_key: str | None = None


def bound_ulif(homonyms, vesum_entries, target):
    """Reuse the authenticated paradigm matcher, including unknown competitors."""
    winners = []
    for entry_id, candidate in homonyms.items():
        if target not in (candidate["candidates"] or ()):
            continue
        competing = {
            other_id: other for other_id, other in homonyms.items()
            if other["candidates"] is None or set(other["candidates"]).intersection(candidate["candidates"])
        }
        matches = {key: vesum_entries[key] for key in candidate["candidates"]}
        result = src.match_identity(entry_id, competing, matches)
        if result["confidence"] == "high" and result["vesum_entry"] == target:
            winners.append(entry_id)
    return winners[0] if len(winners) == 1 else None


def ulif_candidates(sources, lemma, vesum_rows):
    rows = sources.sources.execute(
        "SELECT * FROM ulif_dictua_entries WHERE normalized_query=? ORDER BY homonym_index,id",
        (normalize_ulif_spelling(lemma),),
    )
    out = {}
    observed = list(map(dict, rows))
    sources._use(f"projection:ulif_entries:{lemma}", observed)
    for row in observed:
        head = row["canonical_headword"]
        # An authenticated competitor for another spelling or class cannot
        # steal a match. An empty or unverified head can.
        candidates = (_entry_candidates(row, vesum_rows, lemma) if src.unstressed(head) == lemma
                      else [] if head and src.unstressed(head).casefold() == lemma.casefold() else None)
        raw, forms, reason = {}, None, "unverified_entry_identity"
        if row["status"] == "ok" and row["homonym_checked"] == 1:
            try:
                raw_ref = row["raw_response_ref"]
                if not isinstance(raw_ref, str):
                    raise ValueError("invalid_ulif_raw_reference")
                raw = json.loads(sources._raw(raw_ref.removeprefix("sha256:"), "ulif:entry"))
                if not isinstance(raw, dict) or not isinstance(raw.get("paradigm"), str):
                    raise ValueError("invalid_ulif_raw_manifest")
                html = sources._raw(raw["paradigm"].removeprefix("sha256:"), "ulif:paradigm")
                parsed = parse_ulif_entry(html.decode(), homonym_index=row["homonym_index"])
                forms = sources.forms(row["id"])
                if any(parsed[key] != row[key] for key in ("canonical_headword", "grammatical_label", "sense_gloss")):
                    forms, reason = None, "ulif_raw_identity_mismatch"
                else:
                    reason = sources.forms_status(row["id"]) or sources.forms_failed(row["id"])
                    if reason == "stale_source_snapshot":
                        stored = list(map(dict, sources.sources.execute(
                            "SELECT * FROM ulif_forms WHERE entry_id=? ORDER BY id", (row["id"],),
                        )))
                        page = raw["paradigm"].removeprefix("sha256:")
                        if (all(form["source_page_sha256"] == page
                                and form["parser_version"] == src.FORMS_PARSER_VERSION for form in stored)
                                and list(map(src._comparable, stored)) == list(map(src._comparable, parsed["forms"]))):
                            forms, reason = stored, None
            except (src.SourceAuthenticityError, KeyError, ValueError):
                reason = "ulif_raw_capture_unavailable"
        if reason and not candidates:
            candidates = None
        paradigm = None
        if forms and reason is None and candidates is not None:
            paradigm = src.ulif_paradigm(forms, pronoun=row["grammatical_label"].startswith("займенник"))
        out[row["id"]] = {
            "row": row, "head": head, "aspect": assembly.parse_aspect(row["grammatical_label"]),
            "paradigm": paradigm, "forms": forms, "raw": raw, "candidates": candidates,
            "reason": reason or (None if paradigm is not None else "ulif_paradigm_missing"),
        }
    return out


def ulif_groups(sources, entry_id, identity, add, report):
    rows = list(map(dict, sources.sources.execute(
        "SELECT * FROM ulif_dictua_sections WHERE entry_id=? ORDER BY source_order,id", (entry_id,),
    )))
    sources._use(f"projection:ulif_sections:{entry_id}", rows)
    for kind in GROUPS:
        stored = [row for row in rows if row["kind"] == kind]
        ref = identity["raw"].get(kind)
        if not ref:
            report(kind, "ulif", "missing_capture" if not stored else "group_raw_capture_missing", len(stored))
            continue
        if not isinstance(ref, str):
            report(kind, "ulif", "malformed_group_capture", len(stored))
            continue
        try:
            raw = sources._raw(ref.removeprefix("sha256:"), f"ulif:{kind}")
            groups = [_group_text(group) for group in parse_ulif_relation_groups(raw.decode(), kind)]
        except (src.SourceAuthenticityError, ValueError):
            report(kind, "ulif", "group_raw_capture_refused", len(stored))
            continue
        projected = [_group_text(json.loads(row["payload_json"])) for row in stored]
        keys = [row["sense_or_group_id"] for row in stored]
        order = [(row["id"], row["source_order"]) for row in stored]
        if (group_structure(groups) != group_structure(projected) or len(set(keys)) != len(keys)
                or any((group["sense_or_group_id"], group["source_order"]) != (key, slot)
                       for group, key, (_, slot) in zip(groups, keys, order, strict=True))):
            report(kind, "ulif", "group_replay_mismatch", max(len(groups), len(stored)))
            continue
        if not groups:
            report(kind, "ulif", "checked_none")
        for group, row in zip(groups, stored, strict=True):
            add(kind, "ulif", f"ulif_dictua_sections:{row['id']}", group, scope="source_group",
                source_key=group["sense_or_group_id"])


def group_structure(value):
    """Ignore parser-version differences in the spacing around HTML tags."""
    if isinstance(value, dict):
        return {key: group_structure(child) for key, child in value.items()}
    if isinstance(value, list):
        return [group_structure(child) for child in value]
    return "".join(value.split()) if isinstance(value, str) else value


def mirror_definitions(part):
    """Locate staged definitions verbatim inside the bound mirror partition."""
    row = part["row"]
    try:
        parsed = json.loads(row["senses_json"])
    except ValueError:
        return []
    # The staged parse has one article-level sense list, even for pages
    # containing several numbered homonyms. Only a lone partition owns it.
    if part["partition"] != "article" or not isinstance(parsed, dict):
        return []
    head = parsed.get("headword", "")
    if not isinstance(head, str) or (head and src.nfc(head.lower()) != part["head"]):
        return []
    senses = parsed.get("senses")
    if not isinstance(senses, list):
        return []
    definitions = []
    cursor = 0
    for order, sense in enumerate(senses, 1):
        if not isinstance(sense, dict) or type(sense.get("sense_num")) is not int or sense["sense_num"] != order:
            return []
        raw = sense.get("raw_text")
        definition = sense.get("definition")
        if not isinstance(raw, str) or not isinstance(definition, str) or not definition.strip():
            return []
        # The staged parse sometimes carries the sense number's full stop
        # into the definition. Advance the quotation past that delimiter.
        if definition.startswith(". ") and raw.startswith(f"{order}{definition}"):
            definition = definition.removeprefix(". ")
        start = part["text"].find(raw, cursor)
        within = raw.find(definition)
        if start < 0 or within < 0:
            return []
        cursor = start + len(raw)
        first = part["span"][0] + start + within
        definitions.append((order, definition, first, first + len(definition)))
    return definitions


def modern_meanings(sources, lemma, homonyms, entry_id, vesum_stress, add, report):
    candidates = meanings.candidates(sources, lemma)
    for source, parts in candidates.items():
        field = "definition_uk"
        if source == MIRROR_SOURCE_ID and candidates["sum20"]:
            for facet in (field, "stress"):
                report(facet, source, "preferred_official_article_present")
            continue
        if not parts:
            report(field, source, VTS_NOT_CAPTURED if source == VTS else "capture_absent")
            if source == MIRROR_SOURCE_ID:
                report("stress", source, "capture_absent")
            continue
        if source == MIRROR_SOURCE_ID and len({part["row"]["id"] for part in parts}) != 1:
            for facet in (field, "stress"):
                report(facet, source, "mirror_article_not_unique", len(parts))
            continue
        # Unknown competitors prevent a unique partition match.
        competing = {key: value for key, value in homonyms.items() if value["head"]}
        seen = set()
        for part in parts:
            locator = part["locator"]
            if locator in seen:
                raise Refusal("duplicate_dictionary_partition")
            seen.add(locator)
            reason = part["reason"]
            if source == VTS and reason == "full_source_unavailable":
                reason = VTS_NOT_CAPTURED
            identities = competing
            # The VESUM comment is correspondence evidence only. Its stress
            # spelling cannot itself become a learner-facing stress value.
            if (entry_id in identities and src.ACUTE not in identities[entry_id]["head"]
                    and part["head"] in vesum_stress):
                identities = {**competing, entry_id: {**competing[entry_id], "head": part["head"]}}
            if not reason and (entry_id is None or len(competing) != len(homonyms)
                               or not meanings.correspondence(part, identities, entry_id)):
                reason = "unbound_partition"
            if reason:
                report(field, source, reason, 1, locator)
                if source == MIRROR_SOURCE_ID:
                    report("stress", source, reason, 1, locator)
                continue
            row = part["row"]
            if source == "sum20":
                try:
                    parsed = parse_sum20_article(row["article_html"], row["wordid"])
                except Sum20ParseError:
                    report(field, source, "official_article_replay_refused", 1, locator)
                    continue
                sense_rows = [
                    (item["sense_order"], item["definition"], json.loads(item["register_labels"]))
                    for item in sources.sources.execute(
                        "SELECT * FROM sum20_senses WHERE article_id=? ORDER BY sense_order,id", (row["id"],))
                ]
                citations = [
                    (item["sense_ref"], item["order"], item["citation_text"])
                    for item in sources.sources.execute(
                        'SELECT * FROM sum20_citations WHERE article_id=? ORDER BY "order",id', (row["id"],))
                ]
                expected_senses = [(item.sense_order, item.definition, item.register_labels) for item in parsed.senses]
                expected_citations = [(item.sense_ref, item.citation_order, item.citation_text) for item in parsed.citations]
                if (parsed.content_sha256 != row["content_sha256"] or parsed.article_text != part["text"]
                        or parsed.stressed_headword != row["stressed_headword"] or parsed.grammar != row["grammar"]
                        or sense_rows != expected_senses or citations != expected_citations):
                    report(field, source, "official_article_replay_mismatch", 1, locator)
                    continue
                if (src.ACUTE not in competing[entry_id]["head"]
                        and part["head"] in vesum_stress and src.ACUTE in parsed.stressed_headword):
                    add("stress", source, f"{locator}/stressed_headword", parsed.stressed_headword)
                definitions = [item for item in parsed.senses if item.definition]
                if not definitions or len(definitions) != len(parsed.senses):
                    report(field, source, "definition_sense_missing", 1, locator)
                for sense in definitions:
                    add(field, source, f"{locator}/sense/{sense.sense_order}", sense.definition,
                        scope="source_sense", source_key=f"{row['wordid']}:{sense.sense_order}")
                    for index, label in enumerate(sense.register_labels):
                        add("register", source, f"{locator}/sense/{sense.sense_order}/register/{index}", label,
                            scope="source_sense", source_key=f"{row['wordid']}:{sense.sense_order}")
                for citation in parsed.citations:
                    if not any(sense.sense_order == citation.sense_ref for sense in definitions):
                        report("examples", source, "illustration_without_bound_sense", 1, locator)
                        continue
                    add("examples", source, f"{locator}/citation/{citation.citation_order}", citation.citation_text,
                        scope="source_sense", source_key=f"{row['wordid']}:{citation.sense_ref}")
            elif source == MIRROR_SOURCE_ID:
                if part["relation"] != MIRROR_ONLY:
                    for facet in (field, "stress"):
                        report(facet, source, "mirror_article_not_fallback", 1, locator)
                    continue
                if hashlib.sha256(row["article_text"].encode()).hexdigest() != row["content_sha256"]:
                    for facet in (field, "stress"):
                        report(facet, source, "mirror_body_digest_mismatch", 1, locator)
                    continue
                if src.ACUTE in part["head"]:
                    start = part["span"][0]
                    # The comma also follows any source-local homonym number.
                    end = start + len(part["text"].partition(",")[0].rstrip(meanings.SUPERSCRIPTS))
                    add("stress", source, f"sum20_mirror_articles:{row['id']} [article_text:{start}:{end}]",
                        part["head"], label=MIRROR_ATTRIBUTION_LABEL)
                else:
                    report("stress", source, "bound_headword_has_no_explicit_stress", 1, locator)
                definitions = mirror_definitions(part)
                if not definitions:
                    report(field, source, "mirror_definition_unresolved", 1, locator)
                for order, definition, start, end in definitions:
                    add(field, source, f"sum20_mirror_articles:{row['id']} [article_text:{start}:{end}]",
                        definition, label=MIRROR_ATTRIBUTION_LABEL, scope="source_sense",
                        source_key=f"{row['id']}:{order}")
            else:
                add(field, source, locator, part["text"], label=row["dictionary_label"],
                    source_key=part["partition"])


def soviet_context(row):
    """Project the historical article with an unconditional context marker."""
    keywords = row["sovietization_keywords"]
    risk = row["sovietization_risk"]
    if not isinstance(keywords, str) or type(risk) is not int:
        raise Refusal("malformed_soviet_context")
    return {
        "text": row["definition"], "red_flag": True,
        "sovietization_risk": risk,
        "sovietization_keywords": keywords,
        "ideological_markers": row.get("ideological_markers") or [
            marker.strip() for marker in keywords.split(",") if marker.strip()
        ],
    }


def entry_witnesses(sources, lemma, unambiguous, gloss_bound, pos, add, report):
    specs = (
        ("esum_etymology", "lemma", "etymology_text", "etymology", "esum"),
        ("grinchenko", "word", "word", "heritage", "grinchenko"),
        ("dmklinger_uk_en", "word", "translations", "gloss_en", "dmklinger"),
        ("sum11", "word", "definition", "soviet_colonization_context", "sum11"),
    )
    for table, key, column, field, source in specs:
        # The table and column identifiers are fixed by the source contracts above.
        rows = list(map(dict, sources.sources.execute(
            f"SELECT rowid AS record_id,* FROM {table} WHERE {key}=? ORDER BY rowid", (lemma,),
        )))
        sources._use(f"projection:{table}:{lemma}", rows)
        if not rows:
            report(field, source, "checked_none")
        for row in rows:
            locator = f"{table}:{row['record_id']}"
            if not row[column]:
                report(field, source, "empty_source_value", 1, locator)
            elif field == "soviet_colonization_context":
                # Context describes the spelling, including historical dictionary divisions.
                add(field, source, locator, soviet_context(row), scope="context", label=row["source"])
            elif (not (gloss_bound if field == "gloss_en" else unambiguous)
                  or (row.get("pos") and pos not in {label_pos(row["pos"]), row["pos"]})):
                report(field, source, "entry_witness_unbound", 1, locator)
            else:
                value = row[column]
                label = row.get("source")
                if field == "gloss_en":
                    value = json.loads(value)
                    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
                        report(field, source, "malformed_gloss_capture", 1, locator)
                        continue
                if field == "etymology":
                    label = f"ЕСУМ, т. {row['vol']}, с. {row['page']}"
                add(field, source, locator, value, label=label)
    wiktionary = list(map(dict, sources.sources.execute(
        "SELECT word,source FROM wiktionary WHERE word=? ORDER BY id", (lemma,),
    )))
    sources._use(f"projection:wiktionary:{lemma}", wiktionary)
    if wiktionary and unambiguous:
        add("wiki_reference", "wiktionary", "wiktionary:word:" + lemma,
            "https://uk.wiktionary.org/wiki/" + quote(lemma), label=wiktionary[0]["source"])
    else:
        report("wiki_reference", "wiktionary", "entry_witness_unbound" if wiktionary else "checked_none",
               len(wiktionary))


def secondary_witnesses(sources, lemma, bound, gloss_bound, add, report):
    facets = {
        "synonyms": ("synonyms", "synonyms_dictionary"),
        "phraseology": ("phraseology", "frazeolohichnyi"),
        "proverbs": ("proverbs", "slovnyk_me"),
        "ukreng": ("gloss_en", "slovnyk_me"),
    }
    rows = defaultdict(list)
    for row in map(dict, sources.sources.execute(
        "SELECT * FROM slovnyk_me_entries WHERE normalized_word=? "
        "AND dictionary_slug IN ('synonyms','phraseology','proverbs','ukreng') ORDER BY id", (lemma,),
    )):
        rows[row["dictionary_slug"]].append(row)
    sources._use(f"projection:slovnyk:{lemma}", dict(rows))
    for slug, (field, source) in facets.items():
        if not rows[slug]:
            report(field, source, "capture_absent")
        for row in rows[slug]:
            locator = f"slovnyk_me_entries:{row['id']}"
            if not (gloss_bound if slug == "ukreng" else bound) or row["use_role"] != "reference":
                report(field, source, "entry_witness_unbound", 1, locator)
                continue
            text, reason = meanings.full_slovnyk(row, sources.meaning_cache_root)
            sources._use(f"projection:slovnyk_full:{row['id']}", {"text": text, "reason": reason})
            if reason:
                report(field, source, reason, 1, locator)
            elif slug == "ukreng":
                found, reason = literal_ukreng_glosses(row, text, lemma)
                if not found:
                    report(field, source, reason, 1, locator)
                for index, gloss in enumerate(found):
                    add(field, source, f"{locator}/gloss/{index}", gloss, label=row["dictionary_label"])
            else:
                add(field, source, locator, text, label=row["dictionary_label"])


def literal_ukreng_glosses(row, text, lemma):
    """Read literal glosses only inside the exact captured, unsplit article."""
    article = meanings.SOURCE_TAIL.sub("", text)
    head, _, body = article.partition(" ")
    if (head != lemma or row["word"] != lemma
            or row["source_url"] != "https://slovnyk.me/dict/ukreng/" + quote(lemma, safe="")):
        return [], "bilingual_ukreng_article_mismatch"
    if re.match(r"\s*[IVX]+(?=[.\s])", body):
        return [], "bilingual_homonym_partition_unresolved"
    glosses = _slovnyk_ukreng_glosses({**row, "text": article}, lemma, limit=len(article))
    return [
        gloss for gloss in glosses
        if re.search(rf"(?<![\w'’‐‑-]){re.escape(gloss)}(?![\w'’‐‑-])", body)
    ], "no_literal_bilingual_gloss"


def puls_witnesses(rows, lemma, bound, citation, add, report):
    """Use the exact headword fold of query_cefr_level and keep the bound class."""
    if not rows:
        report("cefr", "puls", "checked_none")
        return
    tags = {token for row in citation for token in row["tags"].split(":")}
    pos = "pron" if "pron" in tags else citation[0]["pos"] if citation else None
    proper = "prop" in tags
    aspect = assembly.vesum_aspect(citation)
    eligible = []
    for row in rows:
        label = row["pos"] or ""
        source_pos = label_pos(label) or {
            "займенник": "pron", "вигук": "intj", "частка": "part", "числівник": "numr",
        }.get(label)
        if source_pos == "numr" and row["guideword"] == "порядковий числівник" and "numr" in tags:
            source_pos = "adj"
        source_aspect = "imperf" if "(недок.)" in label else "perf" if "(док.)" in label else None
        locator = f"puls_cefr:{row['id']}"
        if not bound:
            report("cefr", "puls", "entry_witness_unbound", 1, locator)
        elif (source_pos != pos or not src.aspect_compatible(source_aspect, aspect)
              or not assembly.puls_matches_identity(row, lemma, proper)):
            report("cefr", "puls", "entry_witness_grammar_mismatch", 1, locator)
        elif row["level"] not in {"A1", "A2", "B1", "B2", "C1"}:
            report("cefr", "puls", "invalid_cefr_level", 1, locator)
        else:
            eligible.append((locator, row))
    conflicting = len({row["level"] for _, row in eligible}) > 1
    for locator, row in eligible:
        if conflicting:
            report("cefr", "puls", "conflicting_cefr_levels", 1, locator)
        else:
            add("cefr", "puls", locator, row["level"], label=row["source"])


def card_values(sources, lemma, target, register, puls_rows, unique_card, ulif_anchor=None):
    values, decisions = [], []

    def report(field, source, reason, count=0, locator=None):
        decisions.append({"field": field, "source": source, "status": "withheld" if count else "missing",
                          "reason": reason, "count": count, "locator": locator, "owner": OWNER})

    def add(field, source, locator, value, *, label=REGISTER_LABEL, scope="entry", source_key=None):
        source_label = label
        if label is REGISTER_LABEL:
            spec = checker.canonical_source(source, register)
            source_label = spec.get("name") if spec else None
        decision = checker.check_entry_projection(field, source, scope, register, source_label=source_label)
        if decision not in {"supported", "context_only"}:
            report(field, source, decision, 1, locator)
        elif value:
            values.append(asdict(EntryValue(field, source, source_label, locator, value, scope, source_key)))
        else:
            report(field, source, "empty_source_value", 1, locator)

    vesum_rows = src.group_by(sources.vesum_forms(lemma), lambda row: row["entry_id"])
    homonyms = ulif_candidates(sources, lemma, vesum_rows)
    if target is None and ulif_anchor is not None:
        anchor_id = ulif_anchor["id"]
        live = homonyms.get(anchor_id, {}).get("row", {})
        identity_columns = ("normalized_query", "canonical_headword", "grammatical_label", "homonym_index")
        if all(live.get(key) == ulif_anchor[key] for key in identity_columns):
            entries = src.vesum_paradigm(
                [row for rows in vesum_rows.values() for row in rows],
                label_pos(ulif_anchor["grammatical_label"]) in {"adj", "verb"},
            )
            matches = [key for key in entries if bound_ulif(homonyms, entries, key) == anchor_id]
            if len(matches) == 1:
                target = matches[0]
    entry_id = None
    target_rows = vesum_rows.get(target, [])
    citation = [row for row in target_rows if row["word_form"] == lemma]
    vesum_stress = set()
    if citation:
        pos = target_rows[0]["pos"]
        candidates = {key: row for key, row in homonyms.items()
                      if row["candidates"] is None or target in row["candidates"]
                      or set(row["candidates"]).intersection(vesum_rows)}
        keep_gender = pos in {"verb", "adj"} or any(
            any(tag in _tag_list(form, "grammatical_tags") for tag in src.GENDERS)
            for candidate in candidates.values() for form in candidate["forms"] or [] if not form["is_lemma"]
        )
        entry_paradigms = src.vesum_paradigm([row for rows in vesum_rows.values() for row in rows], keep_gender)
        entry_id = bound_ulif(candidates, entry_paradigms, target)
        vesum_stress = {reading.casefold() for reading in entry_paradigms[target]["stress"]}
        add("pos", "vesum", f"forms_all:entry:{target}/pos", pos)
        for gender in assembly.vesum_gender(citation):
            add("gender", "vesum", f"forms_all:entry:{target}/gender/{gender}", gender)
        aspect = assembly.vesum_aspect(target_rows)
        if aspect:
            add("aspect", "vesum", f"forms_all:entry:{target}/aspect", aspect)
        forms = homonyms[entry_id]["forms"] if entry_id is not None else []
        _, paradigm = _paradigm(forms, target_rows, {"ulif": "", "vesum": ""}, None, "paradigm_page")
        for slot in paradigm["slots"]:
            for source in ("vesum", "ulif"):
                for item in slot[source]:
                    slot_name = slot["slot"]
                    if slot_name is None and source == "vesum":
                        tags = set(item["value"]["tags"].split(":"))
                        explicit = tags & VESUM_EXTRA_SLOTS.get(pos, set())
                        if len(explicit) == 1:
                            slot_name, = explicit
                    ulif_hold = source == "ulif" and (
                        slot["reason"] or item["value"]["marked_asterisk"] or item["value"]["preposition"]
                    )
                    if slot_name is None or ulif_hold:
                        report("paradigm", source, slot["reason"] or "qualified_form", 1, item["receipt"]["locator"])
                    else:
                        add("paradigm", source, item["receipt"]["locator"], item["value"]["form"],
                            scope="slot", source_key=slot_name)
        if entry_id is not None:
            identity = homonyms[entry_id]
            locator = f"ulif_dictua_entries:{entry_id}/canonical_headword"
            if src.ACUTE in identity["head"]:
                add("stress", "ulif", locator, identity["head"])
            else:
                report("stress", "ulif", "bound_headword_has_no_explicit_stress", 1, locator)
            ulif_groups(sources, entry_id, identity, add, report)
        else:
            report("identity", "ulif", "ulif_vesum_correspondence_unresolved")
            report("stress", "ulif", "ulif_vesum_correspondence_unresolved" if homonyms else "capture_absent")
    else:
        pos = None
        target = None
        report("identity", "vesum", "inventory_entry_unavailable")
        for field in ("pos", "gender", "aspect", "paradigm", "stress"):
            report(field, "vesum", "inventory_entry_unavailable")
        report("stress", "ulif", "no_bound_vesum_entry" if homonyms else "capture_absent")
    for other_id, entry in homonyms.items():
        if other_id != entry_id:
            reason = entry["reason"] or "entry_not_bound"
            report("identity", "ulif", reason, 1, f"ulif_dictua_entries:{other_id}")
            for row in sources.sources.execute(
                "SELECT id,kind FROM ulif_dictua_sections WHERE entry_id=? ORDER BY id", (other_id,)
            ):
                report(row["kind"], "ulif", reason, 1, f"ulif_dictua_sections:{row['id']}")
            for row in sources.sources.execute("SELECT id FROM ulif_forms WHERE entry_id=? ORDER BY id", (other_id,)):
                report("paradigm", "ulif", reason, 1, f"ulif_forms:{row['id']}")

    modern_meanings(sources, lemma, homonyms, entry_id, vesum_stress, add, report)
    if not any(value["field"] == "stress" and value["source_id"] == "sum20" for value in values):
        report("stress", "sum20", "no_bound_stressed_headword")
    unambiguous = len(vesum_rows) == len(homonyms) == 1 and entry_id is not None
    # Spelling-keyed evidence can describe a singleton VESUM lexeme. ULIF
    # provides a competing-entry check here. Its own values still need the
    # independent paradigm, aspect and stress match above.
    competing = []
    for homonym in homonyms.values():
        head, row = homonym["head"], homonym["row"]
        separate_name = (lemma.islower() and homonym["candidates"] == [] and not homonym["reason"]
                         and src.unstressed(head) != lemma and is_proper_name(
                             row["grammatical_label"], head, row["sense_gloss"],
                         ))
        if not separate_name:
            competing.append(homonym)
    singleton = competing[0] if len(competing) == 1 else None
    spelling_bound = bool(unique_card and len(vesum_rows) == 1 and citation and singleton
                          and singleton["forms"] and not singleton["reason"]
                          and singleton["candidates"] == [target]
                          and (not vesum_stress or any(
                              reading.casefold() in vesum_stress for reading in src.stress_forms(singleton["head"])
                          ))
                          and (ulif_anchor is None or singleton["row"]["id"] == ulif_anchor["id"]))
    common = not any("prop" in row["tags"].split(":") for row in citation)
    sources._use(f"projection:puls:{lemma}", puls_rows)
    puls_witnesses(puls_rows, lemma, spelling_bound, citation, add, report)
    entry_witnesses(sources, lemma, unambiguous, spelling_bound if common else unambiguous, pos, add, report)
    secondary_witnesses(sources, lemma, unambiguous, spelling_bound and common, add, report)
    keys = [(value["field"], value["source_id"], value["locator"], value["source_key"]) for value in values]
    if len(keys) != len(set(keys)):
        raise Refusal("duplicate_projection_receipt")
    available = {value["field"] for value in values if value["scope"] != "context"}
    required = list(REQUIRED)
    if pos == "noun" and any({"m", "f", "n"}.intersection(row["tags"].split(":")) for row in target_rows):
        required.append("gender")
    if pos == "verb":
        required.append("aspect")
    holds = [f"required_{field}" for field in required if field not in available]
    if any(item["reason"] == "definition_sense_missing" for item in decisions):
        holds.append("required_definition_per_sense")
    if any(item["field"] == "paradigm" and item["source"] == "vesum" and item["reason"] == "unmapped_slot"
           for item in decisions):
        holds.append("required_paradigm_unmapped_slots")
    return target, values, decisions, holds


LEGACY_FIELDS = {
    "meaning": "definition_uk", "definition_cards": "definition_uk", "morphology": "paradigm",
    "literary_attestation": "examples", "translation": "gloss_en", "idioms": "phraseology",
    "heritage_status": "heritage",
}
SECTION_ORDER = (
    ("definition_uk", "Meaning"),
    ("examples", "Examples and citations"), ("pos", "Part of speech"), ("gender", "Gender"),
    ("aspect", "Aspect"), ("paradigm", "Forms"), ("synonyms", "Synonyms"),
    ("antonyms", "Antonyms"), ("phraseology", "Idioms"), ("proverbs", "Proverbs"),
    ("etymology", "Etymology"), ("heritage", "Pre-Soviet attestation"),
    ("gloss_en", "English gloss, entry-level"), ("cefr", "CEFR"), ("register", "Register labels"),
    ("wiki_reference", "References"),
)


def leaves(value, pointer="", label=None):
    """Enumerate the literal payload positions, including empty containers."""
    if isinstance(value, dict) and value:
        label = value.get("source", label)
        for key, child in value.items():
            yield from leaves(child, pointer + "/" + key.replace("~", "~0").replace("/", "~1"), label)
    elif isinstance(value, list) and value:
        for index, child in enumerate(value):
            yield from leaves(child, f"{pointer}/{index}", label)
    else:
        yield pointer, label, value


def legacy_payloads(atlas, lemma, frozen_slugs):
    slugs = sorted({row[0] for row in atlas.execute("SELECT slug FROM articles WHERE lemma=?", (lemma,))}
                   | set(frozen_slugs))
    for slug in slugs:
        for table, labels in (("articles", "NULL"), ("article_provenance", "source_family")):
            rows = atlas.execute(f"SELECT *,{labels} AS parity_label FROM {table} WHERE slug=? ORDER BY rowid", (slug,))
            for index, row in enumerate(rows):
                record = dict(row)
                yield slug, f"{table}:{index}", "header", record.pop("parity_label"), record
        for row in atlas.execute(
            "SELECT alias,kind,source,visibility FROM aliases WHERE target_slug=? ORDER BY alias,kind", (slug,)
        ):
            yield slug, f"aliases:{row['kind']}:{row['alias']}", "aliases", row["source"], dict(row)
        for row in atlas.execute("SELECT section,source,payload_json FROM enrichment WHERE slug=? ORDER BY section",
                                 (slug,)):
            yield slug, "enrichment", row["section"], row["source"], json.loads(row["payload_json"])
        for row in atlas.execute(
            "SELECT related_slug,entry_type,relation,component_role,provenance "
            "FROM related_entries WHERE slug=? ORDER BY related_slug,relation,provenance", (slug,),
        ):
            locator = f"related_entries:{row['related_slug']}:{row['relation']}:{row['provenance']}"
            yield slug, locator, "related_entries", None, dict(row)
        for row in atlas.execute("SELECT payload_json FROM article_payloads WHERE slug=?", (slug,)):
            payload = json.loads(row["payload_json"])
            if not isinstance(payload, dict) or not isinstance(payload.get("sections", {}), dict):
                raise Refusal("malformed_atlas_payload")
            sections = payload.get("sections", {})
            for section, value in sorted(sections.items()):
                label = value.get("source") if isinstance(value, dict) else None
                yield slug, "article_payloads/sections", section, label, value
            yield slug, "article_payloads", "header", None, {
                key: value for key, value in payload.items() if key != "sections"
            }


def parity(payloads, values, bound_slug):
    """Conserve all Atlas payload paths, even when they are ineligible to render."""
    published = defaultdict(set)
    for value in values:
        key = value["field"], value["source_label"]
        published[key].update(digest(leaf) for _, _, leaf in leaves(value["value"]))
    out = []
    for slug, table, section, label, payload in payloads:
        field = LEGACY_FIELDS.get(section, section)
        counts = Counter()
        value_rows = []
        for pointer, leaf_label, leaf in leaves(payload, label=label):
            leaf_digest = digest(leaf)
            status = "withheld"
            reason = "legacy_value_provenance_unverified"
            if slug != bound_slug:
                reason = "atlas_slug_unbound"
            elif leaf is None or leaf == "" or isinstance(leaf, (dict, list)):
                status, reason = "missing", "empty_legacy_value"
            elif "wordnet" in str(leaf_label).casefold():
                reason = "source_facet_not_permitted"
            elif isinstance(leaf_label, str) and leaf_digest in published[field, leaf_label]:
                status, reason = "admitted", "exact_bound_value_and_label"
            counts[status] += 1
            value_rows.append({"pointer": pointer, "label": leaf_label, "sha256": leaf_digest,
                               "status": status, "reason": reason,
                               "owner": None if status == "admitted" else OWNER})
        out.append({"slug": slug, "table": table, "section": section, "label": label, "counts": dict(counts),
                    "values": value_rows})
    return out


def population(root, inventory):
    """Preserve every frozen ID and inventory row without minting release identities."""
    def read(relative):
        obj = foundation.load(root / relative)
        if not isinstance(obj, dict):
            raise Refusal("malformed_frozen_registry")
        return obj

    if not isinstance(inventory, dict) or not isinstance(inventory.get("rows"), list):
        raise Refusal("malformed_inventory")

    base = read("registry/atlas/identity/registry.json")
    by_id = {item["card_id"]: item for item in base["entries"]}
    row_cards = defaultdict(set)
    slices = defaultdict(set)
    for number in range(2, 7):
        manifest = read(f"registry/atlas/a1-v1-slice{number}.json")
        if manifest["inventory_sha256"] != digest(inventory):
            raise Refusal("slice_inventory_digest_mismatch")
        companion = read(f"registry/atlas/identity/a1-v1-slice{number}.json")
        by_id.update((item["card_id"], item) for item in companion.get("entries", []))
        for card_id in manifest["card_ids"]:
            slices[card_id].add(number)
        bindings = manifest.get("row_card_ids", {})
        if not isinstance(bindings, dict):
            raise Refusal("malformed_frozen_registry")
        for row_id, card_id in bindings.items():
            row_cards[row_id].add(card_id)
    # Read the approved pilot pairing whether or not the release files are checked out.
    path = "data/datasets/word-cards/releases/v0.1.0-pilot/pairing-atlas0.json"
    try:
        pairing_bytes = subprocess.check_output(["git", "-C", str(root), "show", f"HEAD:{path}"], timeout=30)
    except subprocess.SubprocessError as error:
        raise Refusal("frozen_pilot_pairing_unavailable") from error
    pairing = json.loads(pairing_bytes)
    if not isinstance(pairing, dict) or not isinstance(pairing.get("entries"), list):
        raise Refusal("malformed_frozen_pairing")
    pilot = read("registry/atlas/pilot/pilot-v1.json")["selection"]
    pilot_rows = {record["locator"]: record["raw_row"] for record in pilot["source_records"]
                  if record["table"] == "ulif_dictua_entries"}
    by_slug = {}
    for row in pairing["entries"]:
        if not isinstance(row, dict):
            raise Refusal("malformed_frozen_pairing")
        card_id = row["card_id"]
        slices[card_id].add(1)
        if row["status"] == "paired":
            locator = row.get("atlas0_slug")
            if not isinstance(locator, str) or not locator.startswith("atlas0:slug:"):
                raise Refusal("malformed_frozen_pairing")
            by_slug[card_id] = locator.removeprefix("atlas0:slug:")
    cards = {}
    for card_id, numbers in sorted(slices.items()):
        if re.fullmatch(r"wc_[a-z0-9]{12}", card_id) is None:
            raise Refusal("invalid_frozen_card_id")
        key = by_id[card_id]["key_at_creation"]
        source_keys = key["source_keys"]
        if not isinstance(key["spelling"], str) or not isinstance(source_keys, list) or any(
            not isinstance(item, dict) or not isinstance(item.get("key"), str) for item in source_keys
        ):
            raise Refusal("malformed_frozen_registry")
        entry_ids = [item["key"].removeprefix("vesum:entry:") for item in source_keys
                     if item["source_id"] == "vesum" and item["key"].startswith("vesum:entry:")]
        anchors = [pilot_rows[item["key"]] for item in source_keys if item["key"] in pilot_rows]
        cards[card_id] = {"lemma": key["spelling"], "entry_ids": {int(item) for item in entry_ids},
                          "ulif_anchor": anchors[0] if len(anchors) == 1 else None,
                          "slices": sorted(numbers), "rows": [],
                          "frozen_slug": by_slug.get(card_id)}
    by_entry = defaultdict(list)
    for card_id, card in cards.items():
        for entry in card["entry_ids"]:
            by_entry[card["lemma"], entry].append(card_id)
    gaps = defaultdict(list)
    for row in inventory["rows"]:
        if not isinstance(row, dict) or not isinstance(row.get("mapping"), dict):
            raise Refusal("malformed_inventory_row")
        mapping = row["mapping"]
        lemma = mapping.get("lemma") or row["key"]
        if not isinstance(lemma, str) or not isinstance(row["key"], str):
            raise Refusal("malformed_inventory_row")
        entry = mapping.get("entry_id")
        ids = row_cards[row["id"]].copy()
        pilot_mapping = mapping.get("pilot", {})
        if not isinstance(pilot_mapping, dict):
            raise Refusal("malformed_inventory_row")
        pilot_id = pilot_mapping.get("card_id")
        if not ids and pilot_id in cards:
            ids.add(pilot_id)
        if not ids and entry is not None:
            ids.update(by_entry[lemma, entry])
        if len(ids) == 1:
            card_id, = ids
            card = cards[card_id]
            if entry is not None and card["lemma"] == lemma:
                card["entry_ids"].add(entry)
            group = card["rows"]
        elif not ids and entry is not None:
            card_id = "candidate-" + digest((lemma, entry))[:20]
            card = cards.setdefault(card_id, {"lemma": lemma, "entry_ids": {entry}, "ulif_anchor": None,
                                              "slices": [], "rows": [], "frozen_slug": None})
            group = card["rows"]
        else:
            group = gaps[row["key"]]
        group.append({"id": row["id"], "disposition": mapping["kind"],
                      "reason": "multiple_card_bindings" if len(ids) > 1 else mapping["reason"],
                      "entry_id": entry})
    covered = Counter(row["id"] for rows in [*(card["rows"] for card in cards.values()), *gaps.values()] for row in rows)
    if covered != Counter(row["id"] for row in inventory["rows"]):
        raise Refusal("inventory_conservation_failed")
    return cards, dict(gaps)


def build(root, inventory, register):
    store_paths = {name: assembly.store_path(name, None) for name in ("sources", "vesum", "atlas")}
    targets, gaps = population(root, inventory)
    with ExitStack() as stack:
        sources, vesum, atlas = (foundation.readonly(stack, store_paths[name]) for name in ("sources", "vesum", "atlas"))
        raw = foundation.readonly(stack, assembly.raw_cache_path(store_paths["sources"]))
        inputs = src.PilotSources(sources, vesum, raw, store_data_dir(store_paths["sources"]).parent)
        actual = dict(vesum.execute("SELECT key,value FROM vesum_build_metadata"))
        expected = inventory["sources"]["vesum_pipeline_identity"]
        if not isinstance(expected, dict) or not expected or any(
            actual.get(key) != value for key, value in expected.items()
        ):
            raise Refusal("vesum_import_drift")
        books = foundation.load_register(root / "docs/l2-uk-direct/textbook-selection.yaml")["sources"]
        return assemble_population(targets, gaps, inputs, atlas, register, digest(inventory), books)


def field_ledger(values, observations, holds):
    """Account for each checked field, including incomplete sets of values."""
    rows = {}
    for field, sources in GAP_SOURCES.items():
        admitted = [value for value in values if value["field"] == field]
        field_holds = {f"required_{field}"}
        if field == "definition_uk":
            field_holds.add("required_definition_per_sense")
        if field == "paradigm":
            field_holds.add("required_paradigm_unmapped_slots")
        reasons = [reason for reason in holds if reason in field_holds]
        if field == "examples" and reasons:
            observed = {item["reason"] for item in observations if item["field"] == field}
            if examples.SENSE_UNDECIDABLE in observed:
                reasons.append(examples.SENSE_UNDECIDABLE)
        if not admitted and not reasons:
            continue
        rows[field] = {
            "outcome": "held" if reasons else "filled",
            "reasons": reasons,
            "sources_searched": {
                source: {
                    "admitted": sum(value["source_id"] == source for value in admitted),
                    "reasons": dict(Counter(item["reason"] for item in observations
                                            if item["field"] == field and item["source"] == source)),
                }
                for source in sources
            },
        }
    return rows


def assemble_population(targets, gaps, inputs, atlas, register, inventory_sha256, books):
    cards = []
    datasets = Counter()
    # PULS is small. Index every exact folded hit once so a result limit
    # cannot conceal a conflicting row for the same spelling.
    puls_by_word = defaultdict(list)
    example_puls_by_word = defaultdict(list)
    for row in map(dict, inputs.sources.execute("SELECT * FROM puls_cefr ORDER BY id")):
        word = _fold_dict_key(row["word"])
        puls_by_word[word].append(row)
        variants = word.split(",") if row["pos"] in examples.FUNCTION_LABELS else (word,)
        keys = {normalize_evidence_form(variant.strip()) for variant in variants}
        if all(examples.UK_TOKEN_RE.fullmatch(key) for key in keys):
            for key in sorted(keys):
                example_puls_by_word[key].append(row)
    inputs._use("projection:examples:puls", example_puls_by_word)
    by_spelling = Counter(_fold_dict_key(card["lemma"]) for card in targets.values())
    projection_rows = []
    example_gaps = {}
    for card_id, card in targets.items():
        lemma = card["lemma"]
        spelling = _fold_dict_key(lemma)
        entries = sorted(card["entry_ids"])
        target = entries[0] if len(entries) == 1 else None
        target, values, observations, holds = card_values(
            inputs, lemma, target, register, puls_by_word.get(spelling, []), by_spelling[spelling] == 1,
            card["ulif_anchor"],
        )
        if target is not None and target not in entries:
            entries.append(target)
        if target is None:
            holds.append("inventory_entry_unbound")
        if holds == ["required_examples"]:
            target_rows = [row for row in inputs.vesum_forms(lemma) if row["entry_id"] == target]
            example_gaps[card_id] = examples.ExampleGap(
                lemma, target, target_rows[0]["pos"],
                frozenset(normalize_evidence_form(row["word_form"]) for row in target_rows),
                examples.bound_senses(values, VTS, inputs),
            )
        projection_rows.append((card_id, card, lemma, target, entries, values, observations, holds))

    examples.search_corpora(list(example_gaps.values()), inputs, register, books, example_puls_by_word)
    for card_id, card, lemma, target, entries, values, observations, holds in projection_rows:
        if "required_examples" in holds:
            official = [item for item in observations if item["field"] == "definition_uk" and item["source"] == "sum20"]
            refusals = [("sum20", item["reason"], item["count"], item["locator"]) for item in official]
            if not refusals:
                refusals = [("sum20", "no bound sense illustration", 0, None)]
            gap = example_gaps.get(card_id)
            if gap is None:
                refusals.extend((source, "other required sections are held", 0, None)
                                for source in (examples.TEXTBOOKS, examples.LITERARY))
            else:
                refusals.extend((source, reason, count, locator)
                                for (source, reason), (count, locator) in gap.attempts.items())
                if gap.values:
                    values.extend(gap.values)
                    holds.remove("required_examples")
            observations.extend({"field": "examples", "source": source, "status": "withheld" if locator else "missing",
                                 "reason": reason, "count": count, "locator": locator, "owner": OWNER}
                                for source, reason, count, locator in refusals)
        frozen_slug = card["frozen_slug"]
        payloads = list(legacy_payloads(atlas, lemma, [frozen_slug] if frozen_slug else []))
        slug = None
        if frozen_slug and atlas.execute("SELECT 1 FROM articles WHERE slug=? AND lemma=?",
                                         (frozen_slug, lemma)).fetchone():
            slug = frozen_slug
        else:
            slugs = {row[0] for row in atlas.execute("SELECT slug FROM articles WHERE lemma=?", (lemma,))}
            if len(slugs) == 1 and target is not None and len(inputs.vesum_forms(lemma)) and len({
                row["entry_id"] for row in inputs.vesum_forms(lemma)
            }) == 1:
                slug, = slugs
        if slug is None:
            observations.append({"field": "atlas", "source": "atlas", "status": "missing", "count": 0,
                                 "reason": "atlas_slug_unbound", "locator": None, "owner": OWNER})
        ledger = parity(payloads, values, slug)
        observed_sections = {section["section"] for section in ledger}
        observations.extend(
            {"field": section, "source": "atlas", "status": "missing", "count": 0,
             "reason": "legacy_section_absent", "locator": None, "owner": OWNER}
            for section in sorted(ENRICHMENT_SECTIONS - observed_sections)
        )
        status = "held" if holds else "complete"
        datasets[status] += 1
        fields = field_ledger(values, observations, holds)
        datasets["code_fields_complete"] += not any(row["outcome"] == "held" for name, row in fields.items()
                                                     if name != "examples")
        cards.append({"card_id": card_id, "lemma": lemma, "entry_ids": entries, "atlas_slug": slug,
                      "slices": card["slices"], "inventory_rows": card["rows"], "status": status,
                      "version": digest({"lemma": lemma, "entry_ids": entries, "values": values}),
                      "values": values, "legacy": ledger, "observations": observations, "gap_ledger": fields,
                      "holds": [{"reason": reason, "owner": OWNER} for reason in holds]})
    inventory_gaps = [
        {"key": key, "rows": rows, "owner": OWNER, "legacy": parity(legacy_payloads(atlas, key, []), [], None)}
        for key, rows in sorted(gaps.items())
    ]
    legacy_sections = [row for item in [*cards, *inventory_gaps] for row in item["legacy"]]
    legacy_counts = Counter(value["status"] for row in legacy_sections for value in row["values"])
    return {
        "schema_version": "atlas-a1-word-card-preview.v2", "inventory_sha256": inventory_sha256,
        "source_reads_sha256": inputs.consumed_digest(),
        "cards": cards,
        "inventory_gaps": inventory_gaps,
        "counts": {
            "cards": len(cards), "inventory_rows": sum(len(card["inventory_rows"]) for card in cards)
            + sum(map(len, gaps.values())), "inventory_gap_keys": len(gaps), "inventory_gap_rows": sum(map(len, gaps.values())),
            "complete": datasets["complete"], "held": datasets["held"],
            "code_fields_complete": datasets["code_fields_complete"],
            "example_fill": {
                "eligible": len(example_gaps), "filled": sum(bool(gap.values) for gap in example_gaps.values()),
                "literary_cards_filled": sum(any(row["source_id"] == examples.LITERARY for row in gap.values)
                                             for gap in example_gaps.values()),
            },
            "holds": dict(Counter(row["reason"] for card in cards for row in card["holds"])),
            "source_observations": dict(Counter(row["reason"] for card in cards for row in card["observations"])),
            "assertions": dict(Counter("context_only" if row["scope"] == "context" else "supported"
                                       for card in cards for row in card["values"])),
            "legacy_values": dict(legacy_counts),
            "legacy_sections": len(legacy_sections),
            "atlas_enrichment_rows": sum(section["table"] == "enrichment" for section in legacy_sections),
            "legacy_by_reason": dict(Counter(value["reason"] for row in legacy_sections for value in row["values"])),
            "slices": dict(Counter(number for card in cards for number in card["slices"])),
        },
    }


def render_value(value):
    if isinstance(value, str):
        return escape(value)
    if isinstance(value, list):
        return "<ul>" + "".join(f"<li>{render_value(item)}</li>" for item in value) + "</ul>"
    if isinstance(value, dict):
        # Display only source text. Structural group numbers and extraction metadata stay in the ledger.
        if "rows" in value:
            return render_value(value["rows"])
        if "left" in value and "right" in value:
            return render_value([value["left"], value["right"]])
        if "text" in value:
            return render_value(value["text"])
        return render_value(list(value.values()))
    return escape(str(value))


def render_card(card):
    head = card["lemma"]
    values = defaultdict(list)
    for value in card["values"]:
        values[value["field"]].append(value)
    stress = values["stress"]
    if stress:
        head = stress[0]["value"]

    def render_item(item):
        body = render_value(item["value"])
        if item["field"] == "wiki_reference":
            body = f'<a href="{body}" rel="noreferrer">{escape(item["source_label"])}</a>'
        label = escape(item["source_label"])
        if item.get("source_id") == examples.LITERARY:
            body = f"<q>{body}</q>"
            label += f' · <a href="{examples.UKRLIB_URL}" rel="noreferrer">УкрЛіб</a>'
        if item["scope"] == "slot":
            label += f" · {escape(item['source_key'])}"
        return (f'<li data-value="{digest(item)}" data-scope="{item["scope"]}">'
                f'<div class="quote">{body}</div><small>{label}</small></li>')

    sections = []
    if stress:
        sections.append("<section><h2>Stress</h2><ul>" + "".join(map(render_item, stress)) + "</ul></section>")
    for field, title in SECTION_ORDER:
        if values[field]:
            sections.append(f"<section><h2>{title}</h2><ul>" + "".join(map(render_item, values[field])) + "</ul></section>")
    for item in values["soviet_colonization_context"]:
        risk = item["value"]["sovietization_risk"]
        badge = (f"<p><strong>Risk {risk}</strong> · Soviet ideological framing present.</p>" if risk > 0 else "")
        sections.append(
            '<details class="occupation-context"><summary>СУМ-11 · Soviet-era dictionary, occupation context</summary>'
            + badge + "<ul>" + render_item(item) + "</ul></details>"
        )
    displayed = {"stress", "soviet_colonization_context", *(field for field, _ in SECTION_ORDER)}
    if {value["field"] for value in card["values"]} - displayed:
        raise Refusal("unrendered_source_section")
    notice = ""
    if card.get("status") == "held":
        reasons = "".join(f"<li>{escape(hold['reason'].replace('_', ' '))}</li>" for hold in card["holds"])
        definition = card.get("gap_ledger", {}).get("definition_uk", {})
        if (definition.get("outcome") == "held"
                and VTS_NOT_CAPTURED in definition["sources_searched"][VTS]["reasons"]):
            reasons += f"<li>{VTS_NOT_CAPTURED}</li>"
        notice = f'<aside aria-label="Card status"><strong>Held · incomplete card</strong><ul>{reasons}</ul></aside>'
    return render_page(head, '<p><a href="./index.html">A1 word cards</a></p>' + notice + "".join(sections))


def render_page(title, body):
    title = escape(title)
    return (
        '<!doctype html><html lang="en"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex">'
        f'<title>{title}</title><style>'
        'html{color-scheme:light dark}body{font:1rem/1.6 system-ui;max-width:65ch;margin:2rem auto;padding:0 1rem}'
        'section,details{border-top:1px solid #8886;padding:.5rem 0}small{display:block;margin-bottom:.85rem}'
        '.quote{white-space:pre-wrap;overflow-wrap:anywhere}summary{cursor:pointer}'
        'aside{border:1px solid currentColor;border-radius:.5rem;padding:1rem;margin:1rem 0}</style>'
        f'<main><h1>{title}</h1>{body}</main></html>'
    )


def projections(result):
    complete = [card for card in result["cards"] if card["status"] == "complete"]
    held = [card for card in result["cards"] if card["status"] == "held"]
    descriptions = []
    for card in held:
        reasons = ", ".join(row["reason"].removeprefix("required_").replace("_", " ") for row in card["holds"])
        descriptions.append(f'<li><a href="./held-{card["card_id"]}.html">{escape(card["lemma"])}</a>'
                            f' · {escape(reasons)}</li>')
    links = [f'<li><a href="./{card["card_id"]}.html">{escape(card["lemma"])}</a></li>' for card in complete]
    return {
        "index.html": render_page("A1 word cards", f"<p>{len(complete)} complete · {len(held)} held</p><ul>"
                                  + "".join(links) + "</ul><details><summary>Held cards</summary><ul>"
                                  + "".join(descriptions) + "</ul></details>"),
        **{card["card_id"] + ".html": render_card(card) for card in complete},
        **{"held-" + card["card_id"] + ".html": render_card(card) for card in held},
    }


def run(root, args):
    if args.sources.suffix != ".json" or args.output.suffix != ".json":
        raise Refusal("source_pin_and_output_must_be_json")
    if not args.check:
        assembly.require_host_only([args.output, args.site_output, *([args.sources] if args.capture_sources else [])])
    inventory = foundation.load(root / "registry/atlas/a1-v1-inventory.json")
    register = foundation.load_register(root / "docs/sources/permissions-register.yaml")
    result = build(root, inventory, register)
    output = canonical(result) + b"\n"
    pages = projections(result)
    files = {args.output: output, **{args.site_output / path: html.encode() for path, html in pages.items()}}
    if len(files) != len(pages) + 1 or args.sources.resolve() in {path.resolve() for path in files}:
        raise Refusal("projection_paths_overlap")
    # The freeze pins the exact result of store replay, including absences and refusals.
    pin = canonical({"inventory_sha256": result["inventory_sha256"], "source_reads_sha256": result["source_reads_sha256"],
                     "projection_sha256": hashlib.sha256(output).hexdigest()}) + b"\n"
    if args.capture_sources:
        if args.sources.exists() and args.sources.read_bytes() != pin:
            raise Refusal("frozen_source_pin_already_exists")
        files[args.sources] = pin
    elif args.sources.read_bytes() != pin:
        raise Refusal("frozen_source_replay_mismatch")
    existing = set(args.site_output.glob("*.html"))
    if existing - files.keys():
        raise Refusal("unexpected_preview_pages_use_fresh_directory")
    if args.check:
        if any(path.read_bytes() != data for path, data in files.items()):
            raise Refusal("delivered_output_mismatch")
    else:
        assembly.require_host_only(list(files))
        for path, data in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            foundation.atomic_write(path, data, mode=0o600)
    return result["counts"]
