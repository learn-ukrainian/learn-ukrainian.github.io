"""Capture source evidence for A1 word cards."""

import hashlib
import json
import re
from collections import Counter, defaultdict
from contextlib import ExitStack
from pathlib import Path

from lu_machinery.storage.topology import StoreRefusal, resolve_store, store_data_dir

from scripts.atlas import word_card_assembly as assembly
from scripts.atlas import word_card_foundation as foundation
from scripts.atlas import word_card_meanings as meanings
from scripts.atlas import word_card_sources as source_rules
from scripts.atlas.a1_card_receipts import Refusal, digest, require_lemma_call, selected_rows
from scripts.atlas.allocate_pilot_identities import is_proper_name, label_pos
from scripts.lexicon.runner.ulif_dictua_parse import normalize_ulif_spelling
from scripts.wiki.sources_db import compute_ulif_entry_fingerprint
from scripts.wiki.sum20_mirror import served_rows

ULIF_FIELDS = ("stress", "paradigm", "synonyms", "antonyms", "phraseology")
ULIF_GROUPS = ULIF_FIELDS[2:]
ULIF_CAPTURE_VERSION = "atlas-a1-ulif-cards.v1"


def response_text(call):
    return "\n".join(c.get("text", "") for c in call["response"]["content"])


def capture(tool_dir: Path, inventory: dict, root: Path) -> dict:
    """Read saved tool replies and authenticate cached VTS text; never fetch or write stores."""
    words = sorted({r["mapping"]["lemma"] for r in selected_rows(inventory)})
    calls = {p.stem: json.loads(p.read_text()) for p in sorted(tool_dir.glob("*.json"))}
    records = {}

    def add(key, call_key, source, payload, *, locator, url="", fetched="", content="", parser="", role=None):
        call = calls[call_key]
        record = {
            "source_id": source, "snapshot_id": source + "@sha256:" + digest(payload),
            "locator": locator, "source_url": url, "retrieved_at": fetched,
            "content_sha256": content or digest(payload), "parser_version": parser,
            "payload": payload, "tool": call["tool"], "arguments": call["arguments"],
            "response_sha256": digest(call["response"]), "call_key": call_key,
        }
        if role is not None:
            record["source_role"] = role
        records[key] = record

    binding = resolve_store("sources", root)
    if isinstance(binding, StoreRefusal):
        raise Refusal("sources_store_unavailable:" + binding.reason)
    with ExitStack() as stack:
        connection = foundation.readonly(stack, binding.path)
        for index, word in enumerate(words):
            for suffix in ("ulif", "vesum", "vts", "sum20", "cefr", "frequency", "heritage"):
                require_lemma_call(calls[f"{index}-{suffix}"], word)
            ulif_call = calls[f"{index}-ulif"]
            entries = json.loads(response_text(ulif_call))["records"][0]["entries"]
            if len(entries) != 1 or not entries[0]["verified"]:
                raise Refusal("ulif_identity_not_unique")
            entry = entries[0]
            if not entry["identity_from_raw"].get("stored_matches_raw"):
                raise Refusal("ulif_raw_identity_mismatch")
            if source_rules.norm_v1(entry["canonical_headword"].replace(source_rules.ACUTE, "")) != word:
                raise Refusal("ulif_lemma_mismatch")
            add(f"ulif:{word}", f"{index}-ulif", "ulif", entry,
                locator=f"ulif:entry:{entry['entry_id']}", url="https://lcorp.ulif.org.ua/dictua",
                fetched=entry["retrieved_at"], content=entry["content_sha256"], parser=entry["parser_version"])
            inspection = json.loads(response_text(calls[f"{index}-vesum"]).split("- Raw payload: ", 1)[1])
            if inspection["lemma"] != word:
                raise Refusal("vesum_lemma_mismatch")
            if inspection["pipeline_identity"] != inventory["sources"]["vesum_pipeline_identity"]:
                raise Refusal("vesum_import_drift")
            add(f"vesum:{word}", f"{index}-vesum", "vesum", inspection,
                locator="vesum:lemma:" + word, parser=inventory["sources"]["vesum_pipeline_identity"]["schema_version"])
            rows = [dict(row) for row in connection.execute(
                "SELECT * FROM slovnyk_me_entries WHERE dictionary_slug='vts' AND normalized_word=? ORDER BY id",
                (word,))]
            if len(rows) != 1:
                raise Refusal("admitted_vts_not_unique")
            row = rows[0]
            text, reason = meanings.full_vts(row, store_data_dir(binding.path).parent)
            if reason or text is None:
                raise Refusal(reason or "vts_text_unavailable")
            if hashlib.sha256(text.encode()).hexdigest() != row["content_sha256"]:
                raise Refusal("vts_snapshot_mismatch")
            add(f"vts:{word}", f"{index}-vts", "vts_busel_slovnyk_me", {"row": row, "text": text},
                locator=f"vts:slovnyk_me_entries:{row['id']}", url=row["source_url"],
                fetched=row["fetched_at"], content=row["content_sha256"], parser=row["importer_version"], role="admitted")
            for mirror, relation in served_rows(connection, word):
                if mirror["article_text"] not in response_text(calls[f"{index}-sum20"]):
                    raise Refusal("sum20_tool_snapshot_mismatch")
                add(f"sum20:{word}", f"{index}-sum20", "sum20_slovnyk_mirror", mirror,
                    locator=f"sum20_mirror_articles:{mirror['id']}", url=mirror["source_url"],
                    fetched=mirror["fetched_at"], content=mirror["content_sha256"],
                    parser="sum20-mirror-rule-v1", role=relation)
            for label, source in (("cefr", "puls"), ("frequency", "grac"), ("heritage", "grinchenko")):
                reply = calls[f"{index}-{label}"]["response"]
                add(f"{label}:{word}", f"{index}-{label}", source,
                    reply.get("structuredContent") or {"text": response_text(calls[f"{index}-{label}"])},
                    locator=f"{source}:query:{word}")
        if "school-context" in calls:
            add("textbook:school", "school-context", "textbooks",
                {"text": response_text(calls["school-context"])},
                locator="textbook:1-klas-bukvar-zaharijchuk-2025-1::1-klas-bukvar-zaharijchuk-2025-1_s0002")
        for key, call in calls.items():
            if key.startswith("balla-"):
                add(key, key, "balla", call["response"].get("structuredContent") or {"text": response_text(call)},
                    locator="balla:query:" + call["arguments"]["query"])
    return {"schema_version": "atlas-a1-slice2-sources.v1", "calls": calls, "records": records,
            "inventory_sha256": digest(inventory)}


def _ulif_targets(inventory):
    """Keep exact VESUM IDs from resolved rows and leave ambiguous occurrences visible."""
    targets = defaultdict(lambda: {"vesum_entry_ids": set(), "ambiguous_row_ids": []})
    for row in inventory["rows"]:
        mapping = row["mapping"]
        if mapping["kind"] == "lemma":
            targets[mapping["lemma"]]["vesum_entry_ids"].add(mapping["entry_id"])
        elif mapping["kind"] == "ambiguous" and len(row["key"].split()) == 1:
            targets[row["key"]]["ambiguous_row_ids"].append(row["id"])
    return {
        lemma: {"vesum_entry_ids": sorted(target["vesum_entry_ids"]),
                "ambiguous_row_ids": sorted(target["ambiguous_row_ids"])}
        for lemma, target in sorted(targets.items())
    }


def _witness(value, row, source, table, snapshot):
    """Bind the emitted value and exact stored row to the same locator."""
    receipt = {
        "source_id": source, "snapshot_id": snapshot, "entry_id": row.get("entry_id", row["id"]),
        "locator": f"{source}:{table}:id:{row['id']}", "row_id": row["id"],
        "content_sha256": digest(row), "value_sha256": digest(value),
        "extraction_rule": ULIF_CAPTURE_VERSION,
    }
    if row.get("source_page_sha256"):
        receipt["source_page_sha256"] = row["source_page_sha256"]
    return {
        "value": value,
        "receipt": receipt,
    }


def _group_text(value):
    """Keep the dictionary's structured text and row order without serving HTML."""
    if isinstance(value, dict):
        return {key: _group_text(item) for key, item in value.items()
                if key not in {"raw_html", "raw_response_ref"}}
    if isinstance(value, list):
        return [_group_text(item) for item in value]
    return value


def _section_payload(row):
    payload = json.loads(row["payload_json"])
    if not isinstance(payload, dict):
        raise Refusal(f"ulif_section_payload_invalid:row_id:{row['id']}")
    return payload


def _entry_candidates(entry, vesum_entries, head):
    """Match the exact citation spelling and grammar before comparing any forms."""
    label = entry["grammatical_label"]
    pos = label_pos(label)
    head_class = label.split(maxsplit=1)[0].rstrip(",") if label else ""
    pos = pos or {"частка": "part", "вигук": "intj", "числівник": "numr"}.get(head_class)
    pronoun = head_class == "займенник"
    if pos is None and not pronoun:
        return None
    genders = set(assembly.parse_gender(label)) if pos == "noun" else set()
    aspect = assembly.parse_aspect(label) if pos == "verb" else None
    proper = is_proper_name(label, head, entry["sense_gloss"],
                            [row for rows in vesum_entries.values() for row in rows])
    candidates = []
    for entry_id, rows in vesum_entries.items():
        citation = [row for row in rows if row["word_form"] == head]
        if not citation:
            continue
        cases = [(row["pos"], set(row["tags"].split(":"))) for row in citation]
        if not any(("prop" in tags) == proper and ("pron" in tags) == pronoun
                   and (pos is None or row_pos == pos) for row_pos, tags in cases):
            continue
        vesum_genders = set(assembly.vesum_gender(citation)) if genders else set()
        if genders and vesum_genders and genders.isdisjoint(vesum_genders):
            continue
        vesum_aspect = source_rules.vesum_aspect_of([row["tags"] for row in rows])
        if source_rules.aspect_compatible(aspect, vesum_aspect):
            candidates.append(entry_id)
    return candidates


def _form_lineage(entry, sections, forms):
    if not forms:
        return "no_forms"
    entry_id = entry["id"]
    head = entry["canonical_headword"]
    if any(row["parser_version"] != source_rules.FORMS_PARSER_VERSION
           or source_rules.unstressed(row["form_stressed"]) != row["form_unstressed"]
           or (row["is_lemma"] and row["form_stressed"] != head) for row in forms):
        raise Refusal(f"ulif_forms_invalid:entry_id:{entry_id}")
    fingerprint = compute_ulif_entry_fingerprint(entry, sections)
    if all(row["source_entry_fingerprint"] == fingerprint for row in forms):
        return "entry_fingerprint"
    # Relation sections can change independently of the paradigm. Check the
    # exact page digest recorded in the current entry's paradigm section.
    pages = {_section_payload(row).get("raw_response_ref") for row in sections if row["kind"] == "paradigm"}
    if all(foundation.hex_digest(row["source_page_sha256"]) and f"sha256:{row['source_page_sha256']}" in pages
           for row in forms):
        return "paradigm_page"
    # The current head authenticates the citation spelling and stress only.
    if len(forms) == 1 and forms[0]["is_lemma"]:
        return "entry_headword"
    raise Refusal(f"ulif_form_lineage_mismatch:entry_id:{entry_id}")


def _tag_list(row, column):
    value = json.loads(row[column])
    if not isinstance(value, list) or any(not isinstance(tag, str) for tag in value):
        raise Refusal(f"ulif_form_tags_invalid:row_id:{row['id']}")
    return value


def _paradigm(forms, vesum_rows, snapshots, binding_reason, lineage):
    """Use canonical VESUM slots. Retain source flags and unmapped rows as evidence."""
    ulif = defaultdict(list)
    vesum = defaultdict(list)
    source_forms = [(row, _tag_list(row, "grammatical_tags"), _tag_list(row, "unmapped_labels")) for row in forms]
    keep_gender = any(not row["is_lemma"] and not unmapped and set(tags).intersection(source_rules.GENDERS)
                      for row, tags, unmapped in source_forms)
    invariant = ("invariable",)
    one_vesum_form = len({row["word_form"] for row in vesum_rows}) == 1
    for row in vesum_rows:
        tags = row["tags"].split(":")
        slot = source_rules.vesum_slot(tags, keep_gender)
        if slot is None and one_vesum_form and row["word_form"] == row["lemma"]:
            slot = invariant
        value = {"form": row["word_form"], "tags": row["tags"]}
        vesum[slot].append(_witness(value, row, "vesum", "forms_all", snapshots["vesum"]))

    citation = []
    stress = []
    for row, tags, unmapped in source_forms:
        value = {"form": row["form_stressed"], "unstressed": row["form_unstressed"], "tags": tags,
                 "unmapped_labels": unmapped, "variant_order": row["variant_order"],
                 "preposition": row["preposition"], "marked_asterisk": bool(row["marked_asterisk"])}
        witness = _witness(value, row, "ulif", "ulif_forms", snapshots["ulif"])
        if row["is_lemma"]:
            citation.append(witness)
            if source_rules.ACUTE in row["form_stressed"]:
                reading = {"form": row["form_stressed"], "readings": source_rules.stress_forms(row["form_stressed"])}
                stress.append(_witness(reading, row, "ulif", "ulif_forms", snapshots["ulif"]))
            if row["is_invariable"]:
                ulif[invariant].append(witness)
            continue
        slot = None if unmapped else source_rules.ulif_slot(tags)
        ulif[slot].append(witness)

    # ULIF omits number from some case and gender slots. The remaining
    # features must identify exactly one VESUM slot before we align them.
    numbered_slots = defaultdict(list)
    for slot in vesum:
        if slot and {"s", "p"}.intersection(slot) and set(slot).intersection(source_rules.CASES + source_rules.GENDERS):
            numbered_slots[tuple(tag for tag in slot if tag not in {"s", "p"})].append(slot)
    uncertain_number = set()
    for slot in tuple(ulif):
        partners = numbered_slots.get(slot, [])
        if slot in vesum or not partners:
            continue
        if len(partners) == 1 and partners[0] not in ulif:
            ulif[partners[0]] = ulif.pop(slot)
        else:
            uncertain_number.update((slot, *partners))

    # A gendered, numberless ULIF slot can correspond to part of an
    # ungendered VESUM slot. Keep both groupings without claiming absence.
    uncertain_granularity = set()
    for slot in ulif.keys() - vesum.keys() - {None}:
        if {"s", "p"}.intersection(slot):
            continue
        genderless = tuple(tag for tag in slot if tag not in source_rules.GENDERS)
        partners = set(numbered_slots.get(genderless, ())) - ulif.keys()
        if genderless != slot and partners:
            uncertain_granularity.update((slot, *partners))

    def slot_order(slot):
        if slot in (invariant, None):
            return (len(source_rules.SLOT_ORDER) + (slot is None),)
        return tuple(source_rules.SLOT_ORDER.index(tag) for tag in slot)

    slots = []
    for slot in sorted(ulif.keys() | vesum.keys(), key=slot_order):
        u_values, v_values = ulif.get(slot, []), vesum.get(slot, [])
        u_forms = {item["value"]["unstressed"] for item in u_values
                   if not (item["value"]["marked_asterisk"] or item["value"]["preposition"])}
        v_forms = {source_rules.unstressed(item["value"]["form"]) for item in v_values}
        reason = binding_reason
        if slot is None:
            reason = "unmapped_slot"
        elif slot in uncertain_granularity:
            reason = "ulif_slot_granularity_unresolved"
        elif slot in uncertain_number:
            reason = "ulif_slot_number_unresolved"
        elif slot == invariant and lineage == "entry_headword":
            reason = "ulif_invariable_status_unverified"
        elif set(slot).intersection(source_rules.RELATED_FORMS):
            reason = "related_form_outside_vesum_entry_paradigm"
        elif u_values and not u_forms:
            reason = "ulif_slot_has_only_qualified_forms"
        elif (not u_forms and None in ulif) or (not v_forms and None in vesum):
            reason = "other_source_has_unmapped_slots"
        if reason or not forms:
            status = "unresolved"
        elif u_forms and v_forms:
            status = "agrees" if u_forms == v_forms else "differs"
        else:
            status = "ulif_only" if u_forms else "vesum_only"
        slots.append({"slot": source_rules.slot_name(slot) if slot is not None else None,
                      "ulif": u_values, "vesum": v_values, "comparison": status,
                      "reason": reason or ("ulif_forms_absent" if not forms else None)})
    return stress, {"citation_forms": citation, "slots": slots}


def _ulif_card(sources, vesum, lemma, target, snapshots):
    entries = [dict(row) for row in sources.execute(
        "SELECT * FROM ulif_dictua_entries WHERE normalized_query=? ORDER BY homonym_index, id",
        (normalize_ulif_spelling(lemma),))]
    vesum_entries = source_rules.group_by(
        map(source_rules.row_dict, source_rules.query_vesum_forms(vesum, lemma)), lambda row: row["entry_id"])
    heads = {entry["id"]: source_rules.unstressed(entry["canonical_headword"] or "") for entry in entries}
    candidates = {}
    for entry in entries:
        entry_id = entry["id"]
        if heads[entry_id] == lemma:
            candidates[entry_id] = _entry_candidates(entry, vesum_entries, lemma)

    # A title-case variant needs affirmative evidence for the inventory entry.
    # A competing ULIF homonym or an exact VESUM reading of the alternate case
    # prevents the variant from borrowing the lowercase entry.
    if len(entries) == 1:
        entry = entries[0]
        entry_id = entry["id"]
        head = heads[entry_id]
        if (lemma.islower() and head == lemma[:1].upper() + lemma[1:] and not entry["sense_gloss"]
                and not is_proper_name(entry["grammatical_label"], head, entry["sense_gloss"])
                and not source_rules.query_vesum_forms(vesum, head).fetchone()):
            ids = _entry_candidates(entry, vesum_entries, lemma)
            if ids and len(ids) == 1 and ids[0] in target["vesum_entry_ids"]:
                candidates[entry_id] = ids

    competitors = Counter(entry_id for ids in candidates.values() if ids is not None for entry_id in ids)
    opaque = None in candidates.values() or "" in heads.values()
    card = {"lemma": lemma, **target, "entries": [], "withheld_entries": []}
    for entry in entries:
        entry_id = entry["id"]
        sections = [dict(row) for row in sources.execute(
            "SELECT * FROM ulif_dictua_sections WHERE entry_id=? ORDER BY kind, source_order, id", (entry_id,))]
        forms = [dict(row) for row in sources.execute(
            "SELECT * FROM ulif_forms WHERE entry_id=? ORDER BY id", (entry_id,))]
        if entry["homonym_checked"] != 1 or entry["status"] != "ok" or entry_id not in candidates:
            reason = entry["status"] if entry["status"] != "ok" else "unverified_entry_identity"
            fields = {row["kind"] for row in sections} & set(ULIF_GROUPS)
            if entry["homonym_checked"] == 1 and entry["status"] == "ok":
                reason = "ulif_headword_spelling_unbound"
                if forms:
                    fields.add("paradigm")
                if any(row["is_lemma"] and source_rules.ACUTE in row["form_stressed"] for row in forms):
                    fields.add("stress")
            card["withheld_entries"].append({"entry_id": entry_id, "reason": reason,
                                              "fields": sorted(fields)})
            continue
        ids = candidates[entry_id]
        partner = None
        if ids is None:
            reason = "ulif_grammar_unmapped"
        elif not ids:
            reason = "vesum_entry_not_found"
        elif len(ids) != 1 or competitors[ids[0]] != 1 or opaque:
            reason = "homonym_correspondence_unresolved"
        else:
            partner, reason = ids[0], None

        lineage = _form_lineage(entry, sections, forms)
        stress, paradigm = _paradigm(forms, vesum_entries.get(partner, []), snapshots, reason, lineage)
        groups = {kind: [] for kind in ULIF_GROUPS}
        for row in sections:
            if row["kind"] not in groups:
                continue
            payload = _section_payload(row)
            if (payload.get("source_order"), payload.get("sense_or_group_id")) != (row["source_order"],
                                                                                 row["sense_or_group_id"]):
                raise Refusal(f"ulif_group_identity_mismatch:row_id:{row['id']}")
            groups[row["kind"]].append(_witness(
                _group_text(payload), row, "ulif", "ulif_dictua_sections", snapshots["ulif"]))
        identity = {"headword": entry["canonical_headword"], "grammatical_label": entry["grammatical_label"],
                    "homonym_index": entry["homonym_index"]}
        card["entries"].append({
            "entry": _witness(identity, entry, "ulif", "ulif_dictua_entries", snapshots["ulif"]),
            "vesum_binding": {"entry_id": partner, "candidates": ids or [], "reason": reason,
                              "spelling_relation": "exact" if heads[entry_id] == lemma else "case_variant"},
            "stress": stress, "paradigm": {"lineage": lineage, **paradigm}, **groups,
        })
    return card


def capture_ulif(inventory, root):
    """Build the full A1 ULIF card data and disagreement report from pinned read transactions."""
    sources_binding = resolve_store("sources", root)
    vesum_binding = resolve_store("vesum", root)
    for binding in (sources_binding, vesum_binding):
        if isinstance(binding, StoreRefusal):
            raise Refusal(f"{binding.store}_store_unavailable:{binding.reason}")
    with ExitStack() as stack:
        sources = foundation.readonly(stack, sources_binding.path)
        vesum = foundation.readonly(stack, vesum_binding.path)
        build = sources.execute("SELECT * FROM ulif_forms_build WHERE id=1").fetchone()
        if (build is None or build["state"] != "complete" or build["parser_version"] != source_rules.FORMS_PARSER_VERSION
                or not foundation.hex_digest(build["source_fingerprint"])):
            raise Refusal("ulif_forms_build_unavailable")
        vesum_version = dict(vesum.execute("SELECT key, value FROM vesum_build_metadata"))
        identity = inventory["sources"]["vesum_pipeline_identity"]
        if not identity or any(vesum_version.get(key) != value for key, value in identity.items()):
            raise Refusal("vesum_import_drift")
        generation = sources_binding.path.name
        snapshots = {
            "ulif": "ulif@" + (generation if re.fullmatch(r"sources\.\d{8}T\d{6}Z-[0-9a-f]{12}\.db", generation)
                               else "forms-sha256:" + build["source_fingerprint"]),
            "vesum": "vesum@sha256:" + identity["canonical_jsonl_sha256"],
        }
        cards = [_ulif_card(sources, vesum, lemma, target, snapshots)
                 for lemma, target in _ulif_targets(inventory).items()]

    coverage = dict.fromkeys(ULIF_FIELDS, 0)
    withheld_gaps, differences = [], []
    slot_counts = Counter()
    for card in cards:
        available = {field for entry in card["entries"] for field in ("stress", *ULIF_GROUPS) if entry[field]}
        if any(e["paradigm"]["citation_forms"] or any(slot["ulif"] for slot in e["paradigm"]["slots"])
               for e in card["entries"]):
            available.add("paradigm")
        card["available_fields"] = [field for field in ULIF_FIELDS if field in available]
        for field in available:
            coverage[field] += 1
        for withheld in card["withheld_entries"]:
            for field in withheld["fields"]:
                if field not in available:
                    withheld_gaps.append({"lemma": card["lemma"], "field": field, "entry_id": withheld["entry_id"],
                                          "reason": withheld["reason"]})
        for entry in card["entries"]:
            for slot in entry["paradigm"]["slots"]:
                status = slot["comparison"]
                slot_counts[status] += 1
                if status in {"differs", "ulif_only", "vesum_only"}:
                    differences.append({"lemma": card["lemma"], "ulif_entry_id": entry["entry"]["receipt"]["entry_id"],
                                        "vesum_entry_id": entry["vesum_binding"]["entry_id"], **slot})
    return {"schema_version": ULIF_CAPTURE_VERSION, "inventory_sha256": digest(inventory), "snapshots": snapshots,
            "cards": cards, "report": {"lemma_count": len(cards), "coverage": coverage,
                                       "withheld_gaps": withheld_gaps, "slot_counts": dict(slot_counts),
                                       "disagreements": differences}}
