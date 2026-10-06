"""C2: complete, source-cited ULIF/VESUM slot agreement.

Frozen census: SELECT COUNT(*) FROM (SELECT entry_id, grammatical_tags
FROM ulif_forms GROUP BY entry_id, grammatical_tags) = 4,113,650.
The minimum form primary key identifies each slot, including accounting rows.
No Ukrainian text is constructed: printed values come from held source fields.
"""

import json
from collections import defaultdict
from typing import ClassVar

from scripts.lexicon.runner.ulif_dictua_parse import ULIF_LABEL_TAGS

from ..attribution import Attribution
from ..components import ComponentContext
from ..contract import Candidate, Citation, Value, digest
from ..errors import BuildError, require
from ..gate import evidence_id
from ..table_layout import layout

STORE = "sources.db"
VESUM = "vesum.db"
FROZEN_COUNT = 4_113_650
LOCK = "scripts/config/vesum_source.lock.json"
ULIF_FORM = "«Словники України online», Український мовно-інформаційний фонд НАН України, https://lcorp.ulif.org.ua/dictua/ (entry reference and retrieval date per field)"
VESUM_FORM = "Рисін А., Старко В. Великий електронний словник української мови (ВЕСУМ). Версія <used version>. 2005-2026. URL: https://vesum.nlp.net.ua/ — licence CC BY-NC-SA 4.0, changes indicated."

POLICY = {
    "labels": {label: {"tags": list(mapping.tags), "role": mapping.role} for label, mapping in ULIF_LABEL_TAGS.items()},
    "data_classes": ["td_inner_style", "td_inner_center_style"],
    "stress_marker": "\u0301",
    "column_roles": ["number", "gender", "axis"],
    "row_exclusive_roles": ["case", "verbform"],
    "axis_labels": [k for k, v in ULIF_LABEL_TAGS.items() if v.role == "axis"],
    "section_roles": ["tense", "mood", "verbform"],
    "subsection_role": "verbform",
    "row_roles": ["case", "gender", "person", "verbform"],
    "gender_role": "gender",
    "plural_tag": "p",
    "number_tags": ["s", "p"],
    "person_tags": ["1", "2", "3"],
}
# POS and aspect describe the lemma, not the paradigm axes. Noun gender is
# intrinsic, whereas adjective/participle gender is an explicit slot axis.
VOCABULARY = sorted({tag for mapping in ULIF_LABEL_TAGS.values() if mapping.role != "grammar" for tag in mapping.tags})
PROJECTION = {"vocabulary": VOCABULARY, "separator": ":", "ignore_when": {"noun": ["m", "f", "n"]}}
TOKENS = "json_each('[\"' || replace(v.tags, ':', '\",\"') || '\"]')"
VOCAB_SQL = ",".join("'" + tag + "'" for tag in VOCABULARY)
VESUM_MATCH = f"""v.lemma=replace(?,char(769),'') AND
 NOT EXISTS (SELECT 1 FROM json_each(?) u WHERE NOT EXISTS (SELECT 1 FROM {TOKENS} t WHERE t.value=u.value AND NOT (substr(v.tags,1,5)='noun:' AND t.value IN ('m','f','n')))) AND
 NOT EXISTS (SELECT 1 FROM {TOKENS} t WHERE t.value IN ({VOCAB_SQL})
 AND NOT (substr(v.tags,1,5)='noun:' AND t.value IN ('m','f','n'))
 AND NOT EXISTS (SELECT 1 FROM json_each(?) u WHERE u.value=t.value))"""


def query(sql, store=STORE):
    return {"kind": "sql", "store": store, "sql": sql}


def ref(slot, area="slots", **kwargs):
    return {"area": area, "slot": slot, **kwargs}


UNIT_QUERY = query("SELECT cast(entry_id AS TEXT)||';'||min(id) FROM ulif_forms GROUP BY entry_id,grammatical_tags")
ANCHOR = ref("unit")
ENTRY = ref("lemma", field="id")
TAGS = ref("unit", field="grammatical_tags")
ENTRY_ID = ref("unit", field="entry_id")
LEMMA = ref("lemma", field="normalized_query")
VESUM_LEMMA = ref("lemma", field="canonical_headword")
FORMS = ref("form", "response", match="all")
SUPPORT = {**FORMS, "citation": 1}

# Authenticate the complete homonym group, including parse-error entries and
# missing slots. A different complete form set refuses even a visible gloss.
HOMONYM_QUERY = query("""SELECT count(*) FROM ulif_dictua_entries e WHERE e.normalized_query=? AND
 (EXISTS (SELECT form_stressed FROM ulif_forms WHERE entry_id=e.id AND grammatical_tags=?
 EXCEPT SELECT form_stressed FROM ulif_forms WHERE entry_id=? AND grammatical_tags=?) OR
 EXISTS (SELECT form_stressed FROM ulif_forms WHERE entry_id=? AND grammatical_tags=?
 EXCEPT SELECT form_stressed FROM ulif_forms WHERE entry_id=e.id AND grammatical_tags=?))""")
HOMONYM_PARAMS = [LEMMA, TAGS, ENTRY_ID, TAGS, ENTRY_ID, TAGS, TAGS]
PARSE_QUERY = query("SELECT count(*) FROM ulif_dictua_entries WHERE normalized_query=? AND status='parse_error'")
# Match the catalog's Unicode whitespace presence test without changing source
# bytes. Derive the complete set from the task's pinned interpreter.
SQL_WHITESPACE = "char(" + ",".join(str(i) for i in range(0x110000) if chr(i).isspace()) + ")"
SENSE_QUERY = query(
    f"SELECT count(*) FROM ulif_dictua_entries WHERE normalized_query=? AND trim(sense_gloss,{SQL_WHITESPACE})=trim(?,{SQL_WHITESPACE}) AND id<>?"
)
SENSE_EMPTY = query(
    f"SELECT CASE WHEN trim(sense_gloss,{SQL_WHITESPACE})='' THEN 1 ELSE 0 END FROM ulif_dictua_entries WHERE id=?"
)

BINDING = {
    "schema": "binding-spec.v1",
    "rules": [
        {"op": "same_row", "values": [ref("lemma"), ref("sense")]},
        {"op": "one_group", "values": [ENTRY, ENTRY_ID, {**FORMS, "field": "entry_id"}]},
        {"op": "one_group", "values": [TAGS, {**FORMS, "field": "grammatical_tags"}]},
        {"op": "equal", "normalizer": "unstress_nfc", "values": [ref("lemma"), {**SUPPORT, "field": "lemma"}]},
        {"op": "literal", "values": [ref("lemma", field="status")], "expected": "ok"},
        *[
            {"op": "literal", "values": [{**FORMS, "field": field}], "expected": expected}
            for field, expected in (
                ("marked_asterisk", 0),
                ("preposition", ""),
                ("unmapped_labels", "[]"),
                ("is_lemma", 0),
            )
        ],
        {
            "op": "form_agreement",
            "values": [FORMS, SUPPORT],
            "left_tags": {"field": "grammatical_tags"},
            "right_tags": {"field": "tags"},
            "tag_projection": PROJECTION,
        },
        {
            "op": "set_query_equal",
            "values": [FORMS],
            "normalizer": "unstress_nfc",
            "queries": [
                {
                    "query": query("SELECT form_unstressed FROM ulif_forms WHERE entry_id=? AND grammatical_tags=?"),
                    "parameters": [ENTRY_ID, TAGS],
                },
                {
                    "query": query("SELECT v.word_form FROM forms_all v WHERE " + VESUM_MATCH, VESUM),
                    "parameters": [VESUM_LEMMA, TAGS, TAGS],
                },
            ],
        },
        {
            "op": "ordered_query_equal",
            "values": [FORMS],
            "normalizer": "identity",
            "queries": [
                {
                    "query": query(
                        "SELECT form_stressed FROM ulif_forms WHERE entry_id=? AND grammatical_tags=? ORDER BY variant_order,id"
                    ),
                    "parameters": [ENTRY_ID, TAGS],
                }
            ],
        },
        {
            "op": "table_binding",
            "values": [FORMS],
            "anchor": ANCHOR,
            "table": ref("table"),
            "entry_field": "entry_id",
            "tags_field": "grammatical_tags",
            "section_prefix": "section_",
            "row_slot": "row",
            "column_prefix": "column_",
            "variant_separator": ",",
            "policy": POLICY,
        },
    ],
}

COMMON_PREDICATES = [{"query": HOMONYM_QUERY, "parameters": HOMONYM_PARAMS, "expected": [0]}]
SPEC = {
    "operations": ["agreed_form"],
    "unit_grain": "ULIF entry × grammatical slot (all variants)",
    "reasons": {
        "accepted": ["complete_agreement"],
        "rejected": [],
        "excluded": [],
        "withheld": [
            "marked_asterisk",
            "preposition_bound",
            "unmapped_labels",
            "failed_entry",
            "entry_unavailable",
            "parse_error",
            "header_unauthenticated",
            "homonym_unbridgeable",
            "sense_not_discriminating",
            "source_order_unavailable",
            "form_set_disagreement",
            "lemma_unauthenticated",
            "attribution_unresolved",
            "locator_unavailable",
            "catalog_inapplicable",
        ],
    },
    "response_serializer": "json_array",
    "slot_serializers": {
        "slot": {
            "id": "c2-header-cells.v2",
            "section": {"prefix": "section_"},
            "row": {"slot": "row", "optional": True},
            "column": {"prefix": "column_"},
        }
    },
    "operation_specs": {
        "agreed_form": {
            "unit_query": UNIT_QUERY,
            "frozen_count": FROZEN_COUNT,
            "unit_id": {
                "separator": ";",
                "primary": [
                    {"selector": ref("lemma"), "store": STORE, "table": "ulif_dictua_entries", "key": "id"},
                    {"selector": ANCHOR, "store": STORE, "table": "ulif_forms", "key": "id"},
                ],
            },
            "binding": BINDING,
            "applicability": {
                "with_sense": [
                    *COMMON_PREDICATES,
                    {"query": SENSE_EMPTY, "parameters": [ENTRY], "expected": [0]},
                    {"query": SENSE_QUERY, "parameters": [LEMMA, ref("sense"), ENTRY], "expected": [0]},
                ],
                "without_sense": [
                    *COMMON_PREDICATES,
                    {"query": SENSE_EMPTY, "parameters": [ENTRY], "expected": [1]},
                    {"query": PARSE_QUERY, "parameters": [LEMMA], "expected": [0]},
                ],
            },
        }
    },
}


class UlifAttribution:
    def resolve(self, form, citation, row, reader):
        require(
            form == ULIF_FORM and citation.table in {"ulif_forms", "ulif_dictua_entries", "ulif_dictua_sections"},
            "attribution_unresolved",
        )
        entry_id = row["id"] if citation.table == "ulif_dictua_entries" else row["entry_id"]
        conn = reader.connections[STORE]
        entry = conn.execute("SELECT * FROM ulif_dictua_entries WHERE id=?", (entry_id,)).fetchone()
        require(
            entry is not None
            and bool(entry["retrieved_at"])
            and bool(entry["raw_response_ref"])
            and bool(entry["response_sha256"]),
            "attribution_unresolved",
        )
        # Bibliography is the exact complete register form, with its parenthetic
        # locator instruction resolved from held harvest metadata.
        bibliography = form.partition(" (entry reference and retrieval date per field)")[0]
        return Attribution(bibliography + "; " + entry["retrieved_at"], form)


class VesumAttribution:
    def resolve(self, form, citation, row, reader):
        require(form == VESUM_FORM and citation.table == "forms_all", "attribution_unresolved")
        try:
            lock = json.loads(reader.read_repository_config(LOCK))
        except (OSError, ValueError):
            raise BuildError("attribution_unresolved") from None
        require(
            isinstance(lock, dict) and lock.get("schema_version") == "vesum-source-lock-v1", "attribution_unresolved"
        )
        asset, expected = lock.get("release_asset"), lock.get("expected")
        require(isinstance(asset, dict) and isinstance(expected, dict), "attribution_unresolved")
        canonical_digest = expected.get("canonical_jsonl_sha256")
        require(
            isinstance(canonical_digest, str)
            and len(canonical_digest) == 64
            and all(c in "0123456789abcdef" for c in canonical_digest),
            "attribution_unresolved",
        )
        version = asset.get("version")
        require(
            isinstance(version, str) and bool(version) and "<" not in version and ">" not in version,
            "attribution_unresolved",
        )
        stored = dict(reader.connections[VESUM].execute("SELECT key,value FROM vesum_build_metadata"))
        require(
            stored.get("canonical_jsonl_sha256") == canonical_digest,
            "attribution_unresolved",
        )
        return Attribution(form.replace("<used version>", version), form)


ULIF_ADAPTER = UlifAttribution()
VESUM_ADAPTER = VesumAttribution()


def value(row, table, field, slot, *, support=(), store=STORE, source="ulif"):
    column, _, pointer = field.partition("#")
    text = row[column]
    selected = json.loads(text) if pointer else text
    if pointer:
        for part in pointer.split("/")[1:]:
            selected = selected[int(part)] if isinstance(selected, list) else selected[part]
    c = Citation(
        source, store, table, f"id={row['id']}", field, f"{table}:id={row['id']};{field}", digest(text.encode())
    )
    return Value(slot, selected, (c, *support), None, "verbatim")


def projected_tags(tags):
    tokens = set(tags.split(":"))
    result = tokens & set(VOCABULARY)
    if "noun" in tokens:
        result -= {"m", "f", "n"}
    return result


class FormsComponent:
    spec: ClassVar[dict] = SPEC
    adapters: ClassVar[dict] = {"ulif": ULIF_ADAPTER, "vesum": VESUM_ADAPTER}
    files: ClassVar[dict] = {}

    def iter_candidates(self, ctx: ComponentContext):
        connection = ctx.reader.connections[STORE]
        vesum = ctx.reader.connections[VESUM]
        failures = {r[0] for r in connection.execute("SELECT entry_id FROM ulif_forms_failures")}
        # Process one entry at a time; no entire-form-table materialization.
        for entry in connection.execute("SELECT * FROM ulif_dictua_entries ORDER BY id"):
            entry = dict(entry)
            rows = [
                dict(r)
                for r in connection.execute(
                    "SELECT * FROM ulif_forms WHERE entry_id=? ORDER BY variant_order,id", (entry["id"],)
                )
            ]
            if not rows:
                continue
            groups = defaultdict(list)
            for row in rows:
                groups[row["grammatical_tags"]].append(row)
            sections = [
                dict(r)
                for r in connection.execute(
                    "SELECT * FROM ulif_dictua_sections WHERE entry_id=? AND kind='paradigm' ORDER BY source_order,id",
                    (entry["id"],),
                )
            ]
            authenticated = defaultdict(list)
            for section in sections:
                try:
                    for a in layout(json.loads(section["payload_json"]), POLICY):
                        authenticated[tuple(a.tags)].append((section, a))
                except (BuildError, ValueError, TypeError, KeyError):
                    continue
            witnesses = defaultdict(list)
            for r in vesum.execute(
                "SELECT * FROM forms_all WHERE lemma=? ORDER BY id",
                (entry["canonical_headword"].replace("\u0301", ""),),
            ):
                r = dict(r)
                witnesses[frozenset(projected_tags(r["tags"]))].append(r)
            for tags, forms in groups.items():
                anchor = min(forms, key=lambda r: r["id"])
                slots = [
                    value(entry, "ulif_dictua_entries", "canonical_headword", "lemma"),
                    value(entry, "ulif_dictua_entries", "sense_gloss", "sense"),
                    value(anchor, "ulif_forms", "form_unstressed", "unit"),
                ]
                reason = None
                if entry["id"] in failures:
                    reason = "failed_entry"
                elif entry["status"] == "parse_error":
                    reason = "parse_error"
                elif entry["status"] != "ok":
                    reason = "entry_unavailable"
                elif any(f["marked_asterisk"] for f in forms):
                    reason = "marked_asterisk"
                elif any(f["preposition"] for f in forms):
                    reason = "preposition_bound"
                elif any(json.loads(f["unmapped_labels"]) for f in forms):
                    reason = "unmapped_labels"
                elif any(f["is_lemma"] for f in forms):
                    reason = "header_unauthenticated"
                elif (
                    not entry["canonical_headword"]
                    or entry["canonical_headword"].replace("\u0301", "").casefold() != entry["normalized_query"]
                ):
                    reason = "lemma_unauthenticated"
                elif any(f["variant_order"] < 1 for f in forms):
                    reason = "source_order_unavailable"
                hits = authenticated.get(tuple(json.loads(tags)), [])
                if reason is None:
                    signatures = {(s["id"], a.sections, a.row, a.columns) for s, a in hits}
                    printed = [item.strip() for s, a in hits for item in a.cell.text.split(",")]
                    if (
                        len(signatures) != 1
                        or not hits[0][1].headers
                        or any(a.unmapped for s, a in hits)
                        or set(printed) != {f["form_stressed"] for f in forms}
                    ):
                        reason = "header_unauthenticated"
                if reason is None:
                    parameters = [entry["normalized_query"], tags, entry["id"], tags, entry["id"], tags, tags]
                    if (
                        not entry["sense_gloss"].strip()
                        and connection.execute(PARSE_QUERY["sql"], (entry["normalized_query"],)).fetchone()[0]
                    ):
                        reason = "parse_error"
                    elif connection.execute(HOMONYM_QUERY["sql"], parameters).fetchone()[0]:
                        reason = "homonym_unbridgeable"
                    elif (
                        entry["sense_gloss"].strip()
                        and connection.execute(
                            SENSE_QUERY["sql"], (entry["normalized_query"], entry["sense_gloss"], entry["id"])
                        ).fetchone()[0]
                    ):
                        reason = "sense_not_discriminating"
                supported = witnesses[frozenset(json.loads(tags))]
                if reason is None and {f["form_unstressed"] for f in forms} != {r["word_form"] for r in supported}:
                    reason = "form_set_disagreement"
                response = []
                if reason is None:
                    section, a = hits[0]
                    slots.append(value(section, "ulif_dictua_sections", "payload_json#/rows/0/0", "table"))
                    cells = [(f"section_{i}", c) for i, c in enumerate(a.sections)]
                    cells += [("row", a.row)] if a.row else []
                    cells += [(f"column_{i}", c) for i, c in enumerate(a.columns)]
                    for slot, c in cells:
                        slots.append(value(section, "ulif_dictua_sections", "payload_json#" + c.pointer, slot))
                    for f in forms:
                        witness = next(r for r in supported if r["word_form"] == f["form_unstressed"])
                        citation = value(
                            witness, "forms_all", "word_form", "form", store=VESUM, source="vesum"
                        ).citations[0]
                        response.append(value(f, "ulif_forms", "form_stressed", "form", support=(citation,)))
                yield Candidate(
                    "C2",
                    f"{entry['id']};{anchor['id']}",
                    "withheld" if reason else "accepted",
                    reason or "complete_agreement",
                    (evidence_id(slots[2].citations[0]),) if reason else (),
                    "agreed_form",
                    tuple(slots),
                    (),
                    tuple(response),
                    ("dual_stress",) if any(f["dual_stress_flag"] for f in forms) else (),
                )


COMPONENT = FormsComponent()
