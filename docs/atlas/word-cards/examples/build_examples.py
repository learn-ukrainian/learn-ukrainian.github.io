"""Build the worked-example word cards (#8978) as JSON instances of schemas/word-card-v1.schema.json.

Every Ukrainian value below is quoted from data/sources.db, data/vesum.db or data/atlas.db
(read-only queries recorded in docs/atlas/word-cards/worked-examples.md). Nothing is
model-written. Card/sense ids are opaque example ids; assertion ids are derived with the
formula in schema.md §4 so a rebuild reproduces them.

Round 2 (Astra REVISE, 2026-09-28): the resolver honours declared doublets, excludes rejected
reviews from voting, compares fields by class (scalar / keyed / text), reports non-voting
evidence and whether the selected mapping is evidenced; links are canonical records with typed
endpoints; assertions carry a durable source-record key; the build manifest hashes input
content and names the identity registry; a split card is a distinct state from a redirect.

Round 3 (Astra REVISE r2, 2026-09-28): assembly consumes a frozen registry and refuses ids it
does not allocate (`MissingAllocation`); every build input carries a content hash; source records
have a persistent identity (`sr_`) with aliases and an explicit ambiguous-correspondence hold;
evidence is counted per proposition (per value, per paradigm slot); several tier-1 doublet
declarations must agree and a reviewed overlay `variant` resolves conflicting scalars;
`card_version` covers everything a consumer can read; derivation ids include rules and
configuration, and a generated assertion names the derivation that produced it so invalidation
walks source -> generated assertion -> consumer; public projections recompute before tombstoning.

Run:  /home/ops/learn-ukrainian/.venv/bin/python docs/atlas/word-cards/examples/build_examples.py
"""

from __future__ import annotations

import hashlib
import json
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
RULES = "rules-v1-draft"
NORMALISER = "norm-v1"
REGISTER_VERSION = 2
# sha256sum docs/sources/permissions-register.yaml (merged #8979 register, schema_version 2) on 2026-09-28
REGISTER_SHA256 = "eb286a61a5a68ca282482bf747ac27f546022b1becdadb32bfbd707c2bac8873"

ULIF_SNAP = "ulif@ulif-dictua-v2/2026-09-22..2026-09-27"
VESUM_SNAP = "vesum@53923150073b4fc7"
ATLAS0_SNAP = "atlas0@manifest-0.1/2026-09-11"
SOURCES_SNAP = "sources.db@2026-09-28"


def canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def sha256_of(obj) -> str:
    return hashlib.sha256(canonical(obj).encode("utf-8")).hexdigest()


class MissingAllocation(RuntimeError):
    """Assembly found a card or sense id that the frozen identity registry does not allocate (schema.md §13)."""


# Register source id -> (independence group, tier). Provisional; schema.md §9.1.
GROUPS = {
    "ulif": ("G-ULIF", 1),
    "sum20": ("G-ULIF", 1),
    "frazeolohichnyi": ("G-ULIF", 1),
    "slovnyk_me": ("G-ULIF", 1),
    "vesum": ("G-VESUM", 1),
    "kaikki": ("G-WIKI", 2),
    "wiktionary": ("G-WIKI", 2),
    "puls": ("G-PULS", 2),
    "ukrainian_word_stress": ("G-UWS?", 2),
    "synonyms_karavansky": ("G-KARAVANSKY", 2),
    "vts": ("G-VTS?", 2),
    "grac": ("G-GRAC", 2),
    "course_authored": ("G-PROJECT", 3),
    "grac_estimate": ("G-PROJECT", 3),
    "atlas_curated": ("G-PROJECT", 3),
}

# ---------------------------------------------------------------- ids (opaque examples)
CASTLE, LOCK, SETTLEMENT = "wc_7k3m9q2xw4pd", "wc_c2v8n5rt6yhq", "wc_e9p1s4dz7xkm"
KLIUCH1, KLIUCH2 = "wc_hb4t8k1nq6zv", "wc_m3y6w9dc2sxr"
IDIOM, POVITRIANYI, BUDUVATY = "wc_pq7z2f5jh8na", "wc_s1x4v7gk9tdb", "wc_t6d3h8mp2wqz"
BRONIA_ARMOUR, BRONIA_RESERV = "wc_v5r2b9nx3cfk", "wc_w8g1k4qt7zhm"
VRIADY = "wc_x2j5n8sd1vpc"
VYBIHATY, VYBIHTY = "wc_y9c3q6hw4rtn", "wc_z4f7m1kb8xsq"
LEGACY_ZAMOK = "wc_0a1b2c3d4e5f"  # the pre-card atlas0 article "замок", split into CASTLE + LOCK

SPLIT_OVERLAY = {
    "overlay_id": "ovl-2026-09-28-0001",
    "kind": "split",
    "card_id": LEGACY_ZAMOK,
    "into": [CASTLE, LOCK],
    "author": "human",
    "lane": "language",
    "date": "2026-09-28",
    "evidence": "ulif:entry:76792 родовий за́мку vs ulif:entry:76793 родовий замка́; vesum:entry:128973 xp2 vs 128972 xp1; "
    "site/src/lib/lexicon/curated-heteronyms.ts замок (за́мок castle / замо́к lock)",
    "record": "#8334 curated heteronym side file; identity.md §5 case A",
}

# ---------------------------------------------------------------- source records: persistent identity (schema.md §12.1)
# A source record has a minted, persistent identity (`sr_`, opaque, never reused) that lives in the identity
# registry. The keys a build uses to FIND the record again in a new snapshot are aliases, recorded with their
# kind and the snapshot they were observed in. Measured on 2026-09-28 (read-only, sources.db):
#   - ULIF `register_position` (page:row in the dictionary's own register) is unique over all 262,788
#     checked rows (262,788 distinct, none empty); stability across harvests is untested (Q-I6 rule).
#   - ULIF `content_sha256` is NOT unique: 257,539 distinct values over 262,788 rows.
#   - the r2 key `query#headword#grammatical_label` is NOT unique: 4,276 key groups covering 8,814 checked rows
#     collide; rows 3 and 98008 (`ключ` homonyms 1 and 2) share `ключ#ключ#іменник чоловічого роду`.
# Correspondence (§12.1, `correspond()`): alias kinds are tried in order of strength; the first kind that
# yields exactly one candidate decides; a kind that yields several candidates is an explicit AMBIGUOUS hold
# (a suppression then applies to every candidate until adjudicated), never a fall-through to a weaker key.
ALIAS_ORDER = ("uid", "register_position", "content", "query_headword_label", "vesum_entry_form", "table_row")

# locator head -> (aliases as {kind: key}, note)
SOURCE_RECORD_ALIASES = {
    "ulif:entry:76791": {
        "register_position": "ulif:register:2795:9",
        "content": "ulif:content:dee17911141621fa3def7efc59930a459c9b0f4f4916241ef2d910b40b469daf",
        "query_headword_label": "ulif:record:замок#За́мок#іменник чоловічого роду",
    },
    "ulif:entry:76792": {
        "register_position": "ulif:register:2795:10",
        "content": "ulif:content:75145ac6e52cdf0a7ecaf07ee737c2c5b06be65f9a5a0824c6db426c832ab06f",
        "query_headword_label": "ulif:record:замок#за́мок#іменник чоловічого роду",
    },
    "ulif:entry:76793": {
        "register_position": "ulif:register:2795:11",
        "content": "ulif:content:89baa95b7e74f07a32005d6f8a0ce5d4d6d250656ab653decedcf7ae1d4255cd",
        "query_headword_label": "ulif:record:замок#замо́к#",
    },
    "ulif:entry:3": {
        "register_position": "ulif:register:3662:14",
        "content": "ulif:content:bc9c727ed53928b9d5deb0803f77a0960b3bda0b8e081b3a80879491959ff6fa",
        "query_headword_label": "ulif:record:ключ#ключ#іменник чоловічого роду",
    },
    "ulif:entry:98008": {
        "register_position": "ulif:register:3662:15",
        "content": "ulif:content:fc5fb55c292c5521ed326d6e375ae80666772d8b5e3190fbde4c904aa4262d09",
        "query_headword_label": "ulif:record:ключ#ключ#іменник чоловічого роду",
    },
    "ulif:entry:29074": {
        "register_position": "ulif:register:730:6",
        "content": "ulif:content:656cdc289b9052a73f3a8f957dcb8d891ec6029e670bef8773dc60824303522b",
        "query_headword_label": "ulif:record:броня#бро́ня#іменник жіночого роду",
    },
    "ulif:entry:29075": {
        "register_position": "ulif:register:730:7",
        "content": "ulif:content:bbb7efa5f4b1cb811bc55c0a035edd86b674b1c551f0305814b80c6609c3212e",
        "query_headword_label": "ulif:record:броня#броня́#",
    },
    "ulif:entry:47595": {
        "register_position": "ulif:register:1544:0",
        "content": "ulif:content:0b5949950b192c7f3127f5d92815f34d7be1328ddfe3b034994adb7c5c06f6b3",
        "query_headword_label": "ulif:record:вряди-годи#вряди́-годи́#прислівник",
    },
    "ulif:entry:34097": {
        "register_position": "ulif:register:970:9",
        "content": "ulif:content:a29d4abd9102baa3318d6553f2819f7d060e19498306d2aed8c9ec77dd594b58",
        "query_headword_label": "ulif:record:вибігати#вибіга́ти#дієслово недоконаного виду",
    },
    "ulif:entry:34099": {
        "register_position": "ulif:register:970:11",
        "content": "ulif:content:065f29c6b17051244dab50d0b544c820f18d3c4110962ac44405e72fca0dc45c",
        "query_headword_label": "ulif:record:вибігти#ви́бігти#дієслово доконаного виду",
    },
    "ulif:entry:170125": {
        "register_position": "ulif:register:6547:18",
        "content": "ulif:content:b35e59c472664df5be07c533f0df28d4d226071abdf143d539d78c3b1982d89c",
        "query_headword_label": "ulif:record:повітряний##",
    },
    "vesum:entry:128971": {"vesum_entry_form": "vesum:record:Замок/noun/noun:inanim:m:v_naz:prop:geo"},
    "vesum:entry:128972": {"vesum_entry_form": "vesum:record:замок/noun/noun:inanim:m:v_naz:xp1"},
    "vesum:entry:128973": {"vesum_entry_form": "vesum:record:замок/noun/noun:inanim:m:v_naz:xp2"},
    "vesum:entry:168409": {"vesum_entry_form": "vesum:record:ключ/noun/noun:inanim:m:v_naz"},
    "vesum:entry:30497": {"vesum_entry_form": "vesum:record:броня/noun/noun:inanim:f:v_naz"},
    "vesum:entry:67854": {"vesum_entry_form": "vesum:record:вряди-годи/adv/adv"},
    "vesum:entry:40937": {"vesum_entry_form": "vesum:record:вибігати/verb/verb:imperf:inf"},
    "vesum:entry:40942": {"vesum_entry_form": "vesum:record:вибігти/verb/verb:perf:inf"},
    "sources.puls_cefr:id:4340": {"table_row": "puls:record:замок/іменник/A2"},
    "sources.puls_cefr:id:3768": {"table_row": "puls:record:ключ/іменник/A2"},
    "sources.frazeolohichnyi:id:568": {"table_row": "frazeolohichnyi:record:будувати повітряні замки"},
    "sources.wiktionary:id:11318": {"table_row": "wiktionary:record:броня"},
}
_SR_ALPHABET = "0123456789abcdefghjkmnpqrstvwxyz"


def _example_sr_id(locator_head: str) -> str:
    """Example-only allocation of an opaque `sr_` id (in production: random at minting, stored in I)."""
    digest = hashlib.sha256(f"example-source-record:{locator_head}".encode()).digest()
    return "sr_" + "".join(_SR_ALPHABET[b % 32] for b in digest[:12])


def _snapshot_for(locator_head: str) -> str:
    if locator_head.startswith("ulif:"):
        return ULIF_SNAP
    if locator_head.startswith("vesum:"):
        return VESUM_SNAP
    return SOURCES_SNAP


def _source_of_head(locator_head: str) -> str:
    if locator_head.startswith("sources."):
        return locator_head.split(":")[0].removeprefix("sources.").replace("puls_cefr", "puls")
    return locator_head.split(":")[0]


SOURCE_RECORDS = [
    {
        "source_record_id": _example_sr_id(head),
        "source_id": _source_of_head(head),
        "aliases": [{"kind": k, "key": v, "snapshot_id": _snapshot_for(head)} for k, v in aliases.items()],
        "correspondence": [
            {"snapshot_id": _snapshot_for(head), "locator": head, "status": "unique", "matched_by": "mint"}
        ],
    }
    for head, aliases in SOURCE_RECORD_ALIASES.items()
]
SOURCE_RECORD_BY_HEAD = {head: rec for head, rec in zip(SOURCE_RECORD_ALIASES, SOURCE_RECORDS, strict=True)}
# The r2 key still collides: mark it on both ключ records so a correspondence through it alone is held.
for _head in ("ulif:entry:3", "ulif:entry:98008"):
    for _alias in SOURCE_RECORD_BY_HEAD[_head]["aliases"]:
        if _alias["kind"] == "query_headword_label":
            _alias["note"] = "shared with the other ключ homonym (ULIF rows 3 and 98008): never decides alone"


def correspond(record: dict, candidates: list[dict]) -> dict:
    """Find `record` among the rows of a new snapshot (schema.md §12.1). `candidates` are rows of the new
    snapshot as {locator, aliases: {kind: key}}. Alias kinds are tried from strongest to weakest; the first
    kind with exactly one hit decides; several hits on one kind is an explicit `ambiguous` hold (every
    candidate is treated as the record for suppression purposes until a lane adjudicates); no hit on any
    kind is `missing`."""
    mine = {a["kind"]: a["key"] for a in record["aliases"]}
    for kind in ALIAS_ORDER:
        if kind not in mine:
            continue
        hits = [c["locator"] for c in candidates if c["aliases"].get(kind) == mine[kind]]
        if len(hits) == 1:
            return {"status": "unique", "matched_by": kind, "locator": hits[0]}
        if len(hits) > 1:
            return {
                "status": "ambiguous",
                "matched_by": kind,
                "candidates": sorted(hits),
                "hold": "suppression applies to every candidate; correspondence needs an overlay identity entry",
            }
    return {"status": "missing"}


def selector_targets(selector: dict, correspondence: dict) -> list[str]:
    """Locators a `source_record` selector suppresses in a snapshot, given the record's correspondence there."""
    if correspondence["status"] == "unique":
        return [correspondence["locator"]]
    if correspondence["status"] == "ambiguous":
        return list(correspondence["candidates"])
    return []


# ---------------------------------------------------------------- normaliser versions (schema.md §12.1, Q1)
def normalise(value: str, version: str) -> str:
    """Every normaliser version stays available so a content selector pinned at an older version still
    matches the raw value under a newer build (the selector never has to guess the new form)."""
    if version == "norm-v1":  # NFC, combining acute kept, lower-cased, whitespace collapsed, trailing punctuation cut
        text = unicodedata.normalize("NFC", value).lower().strip().rstrip(".,;:!?")
        return " ".join(text.split())
    if version == "norm-v2-hypothetical":  # a later normaliser that also drops accents (used only by the tests)
        return normalise(value, "norm-v1").replace("́", "")
    raise KeyError(version)


NORMALISERS = ("norm-v1", "norm-v2-hypothetical")


def content_selector_matches(selector: dict, assertion: dict) -> bool:
    """`assertion_content` selector (schema.md §12.1): compares the selector's pinned value_norm with the
    assertion's RAW value re-normalised by the selector's own normaliser version, whatever the build's."""
    if selector["source_id"] != assertion["source_id"] or selector["field"] != assertion["field"]:
        return False
    if "value_norm" not in selector:
        return True
    raw = assertion["value"] if isinstance(assertion["value"], str) else assertion["value_norm"]
    return normalise(raw, selector["normaliser_version"]) == selector["value_norm"]


def record_key(locator: str) -> str | None:
    """The alias current at extraction (kept on the assertion as `source_record_key`): the strongest alias."""
    rec = SOURCE_RECORD_BY_HEAD.get(_locator_head(locator))
    if not rec:
        return None
    by_kind = {a["kind"]: a["key"] for a in rec["aliases"]}
    return next(by_kind[k] for k in ALIAS_ORDER if k in by_kind)


def record_id(locator: str) -> str | None:
    rec = SOURCE_RECORD_BY_HEAD.get(_locator_head(locator))
    return rec["source_record_id"] if rec else None


def _locator_head(locator: str) -> str:
    return locator.split(" ", 1)[0].split("/section:", 1)[0]


# ---------------------------------------------------------------- the frozen identity registry (input I)
def _entry(card_id, kind, key, senses=(), state="active", created="example-2026-09-28", **extra):
    e = {
        "card_id": card_id,
        "card_kind": kind,
        "state": state,
        "key_at_creation": key,
        "created_in_build": created,
        "senses": [{"sense_id": sid, "order": i + 1, "state": st} for i, (sid, st) in enumerate(senses)],
    }
    e.update(extra)
    return e


def _sk(*pairs):
    return [{"source_id": s, "key": k} for s, k in pairs]


REGISTRY = {
    "schema_version": "1",
    "registry_version": 2,
    "entries": sorted(
        [
            _entry(
                LEGACY_ZAMOK,
                "lexeme",
                {
                    "spelling": "замок",
                    "stress_patterns": ["за́мок"],
                    "pos": "noun",
                    "source_keys": _sk(("atlas0", "atlas0:slug:замок")),
                },
                state="split",
                created="atlas0-migration-M1",
                split_into=[CASTLE, LOCK],
            ),
            _entry(
                CASTLE,
                "lexeme",
                {
                    "spelling": "замок",
                    "stress_patterns": ["за́мок"],
                    "pos": "noun",
                    "paradigm_key": "vesum:entry:128973",
                    "source_keys": _sk(("vesum", "vesum:entry:128973"), ("ulif", "ulif:entry:76792")),
                },
                [("ws_a1b2c3d4e5f6", "active"), ("ws_b2c3d4e5f6g7", "active"), ("ws_c3d4e5f6g7h8", "unsplit")],
            ),
            _entry(
                LOCK,
                "lexeme",
                {
                    "spelling": "замок",
                    "stress_patterns": ["замо́к"],
                    "pos": "noun",
                    "paradigm_key": "vesum:entry:128972",
                    "source_keys": _sk(("vesum", "vesum:entry:128972"), ("ulif", "ulif:entry:76793")),
                },
                [("ws_d4e5f6g7h8j9", "active"), ("ws_e5f6g7h8j9k1", "active"), ("ws_f6g7h8j9k1m2", "active")],
            ),
            _entry(
                SETTLEMENT,
                "proper_name",
                {
                    "spelling": "Замок",
                    "stress_patterns": ["За́мок"],
                    "pos": "noun",
                    "paradigm_key": "vesum:entry:128971",
                },
                [("ws_g7h8j9k1m2n3", "active")],
            ),
            _entry(
                KLIUCH1,
                "lexeme",
                {"spelling": "ключ", "stress_patterns": ["ключ"], "pos": "noun", "paradigm_key": "vesum:entry:168409"},
                [
                    (s, "active")
                    for s in (
                        "ws_h8j9k1m2n3p4",
                        "ws_j9k1m2n3p4q5",
                        "ws_k1m2n3p4q5r6",
                        "ws_m2n3p4q5r6s7",
                        "ws_n3p4q5r6s7t8",
                        "ws_p4q5r6s7t8v9",
                        "ws_q5r6s7t8v9w1",
                    )
                ],
            ),
            _entry(
                KLIUCH2,
                "lexeme",
                {
                    "spelling": "ключ",
                    "stress_patterns": ["ключ"],
                    "pos": "noun",
                    "paradigm_key": "vesum:entry:168409",
                    "source_keys": _sk(("ulif", "ulif:entry:98008")),
                },
            ),
            _entry(
                IDIOM,
                "mwe",
                {
                    "spelling": "будувати повітряні замки",
                    "pos": "phrase",
                    "mwe_key": "ulif:entry:76792/section:96932|будувати повітряні замки",
                },
                [("ws_r6s7t8v9w1x2", "active")],
            ),
            _entry(
                BRONIA_ARMOUR,
                "lexeme",
                {"spelling": "броня", "stress_patterns": ["броня́"], "pos": "noun", "paradigm_key": "vesum:entry:30497"},
                [("ws_s7t8v9w1x2y3", "active")],
            ),
            _entry(
                BRONIA_RESERV,
                "lexeme",
                {"spelling": "броня", "stress_patterns": ["бро́ня"], "pos": "noun", "paradigm_key": "vesum:entry:30497"},
                [("ws_t8v9w1x2y3z4", "active")],
            ),
            _entry(VRIADY, "lexeme", {"spelling": "вряди-годи", "pos": "adv", "paradigm_key": "vesum:entry:67854"}),
            _entry(
                VYBIHATY,
                "lexeme",
                {
                    "spelling": "вибігати",
                    "stress_patterns": ["вибіга́ти"],
                    "pos": "verb",
                    "paradigm_key": "vesum:entry:40937",
                },
            ),
            _entry(
                VYBIHTY,
                "lexeme",
                {
                    "spelling": "вибігти",
                    "stress_patterns": ["ви́бігти"],
                    "pos": "verb",
                    "paradigm_key": "vesum:entry:40942",
                },
            ),
        ],
        key=lambda e: e["card_id"],
    ),
    "source_records": SOURCE_RECORDS,
    "events": [
        {
            "event_id": "ie_0001",
            "kind": "mint",
            "build_id": "atlas0-migration-M1",
            "cards": [LEGACY_ZAMOK],
            "evidence": "atlas0:slug:замок (articles.slug)",
        },
        {
            "event_id": "ie_0002",
            "kind": "split",
            "build_id": "example-2026-09-28",
            "overlay_id": SPLIT_OVERLAY["overlay_id"],
            "from": [LEGACY_ZAMOK],
            "to": [CASTLE, LOCK],
            "evidence": SPLIT_OVERLAY["evidence"],
        },
        {
            "event_id": "ie_0003",
            "kind": "source_record_mint",
            "build_id": "allocate-2026-09-28-r3",
            "evidence": "ulif register_position unique over 262,788 checked rows; content_sha256 257,539 distinct; "
            "query#headword#label collides in 4,276 groups (8,814 rows), e.g. ULIF rows 3 and 98008 ключ",
        },
    ],
}
ALLOCATED_CARDS = {e["card_id"]: {s["sense_id"] for s in e["senses"]} for e in REGISTRY["entries"]}

OVERLAY = {"schema_version": "1", "entries": [SPLIT_OVERLAY]}

SUPPRESSIONS = {
    "schema_version": "1",
    "entries": [
        {
            "suppression_id": "sup-example-0001",
            "issue": "https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8980",
            "date": "2026-09-28",
            "selector": {
                "kind": "source_record",
                "source_id": "ulif",
                "source_record_id": SOURCE_RECORD_BY_HEAD["ulif:entry:76793"]["source_record_id"],
                "alias_at_creation": "ulif:register:2795:11",
                "on_ambiguous": "suppress_all_candidates",
            },
            "scope": ["site", "dataset"],
            "applies_to": {"reharvest": True, "rollback": True},
            "note": "example: every assertion extracted from the ULIF lock record, in any snapshot; the record is found "
            "by correspondence (schema.md §12.1), an ambiguous correspondence suppresses every candidate",
        },
        {
            "suppression_id": "sup-example-0002",
            "issue": "https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8980",
            "date": "2026-09-28",
            "selector": {
                "kind": "assertion_content",
                "source_id": "ukrainian_word_stress",
                "field": "stress",
                "subject_spelling": "вряди-годи",
                "value_norm": "вряди́-го́ди",
                "normaliser_version": NORMALISER,
            },
            "scope": ["site", "dataset", "internal"],
            "applies_to": {"reharvest": True, "rollback": True},
            "note": "example: one value from one source on one spelling; matched by re-normalising the raw value with "
            "the pinned normaliser version, so a normaliser change never silently drops the selector",
        },
        {
            "suppression_id": "sup-example-0003",
            "issue": "https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8980",
            "date": "2026-09-28",
            "selector": {
                "kind": "assertion_id",
                "assertion_id": "wa_000000000000000000000000",
                "fallback": {
                    "kind": "assertion_content",
                    "source_id": "kaikki",
                    "field": "stress",
                    "subject_spelling": "замок",
                    "value_norm": "за́мок",
                    "normaliser_version": NORMALISER,
                },
            },
            "scope": ["site"],
            "applies_to": {"reharvest": True, "rollback": True},
            "note": "example of the id selector shape: the fallback is a complete assertion_content selector (the "
            "schema rejects an empty one); the placeholder id shows that the fallback, not the id, is durable",
        },
    ],
}


# ---------------------------------------------------------------- build manifest: every input by content hash (§13)
# Measured 2026-09-28, read-only (recipes in schema.md §17):
#   ULIF: sha256 over the concatenated, sorted content_sha256 of the 262,788 checked rows.
#   sources.db tables: sha256 over rows ordered by id, each row as canonical JSON {column: value} + "\n".
#   atlas0: sha256sum of data/atlas.db (frozen manifest 0.1 file; covers kaikki, ВТС, slovnyk.me, Караванський,
#   ukrainian-word-stress, GRAC estimates and learner_english_gloss payloads that only exist there).
#   curated-heteronyms.ts: sha256sum of the file. VESUM: vesum_build_metadata.canonical_jsonl_sha256.
#   I and O: sha256 of the canonical JSON of the committed companion files (the same bytes the tests re-hash).
def _input(ref: str, content_sha256: str | None = None, note: str | None = None, version: str | None = None) -> dict:
    d = {"ref": ref}
    if version:
        d["version"] = version
    if content_sha256:
        d["content_sha256"] = content_sha256
    if note:
        d["note"] = note
    return d


BUILD = {
    "build_id": "example-2026-09-28-r3",
    "rules_version": RULES,
    "inputs": {
        "S": {
            "ulif": _input(
                "sources.ulif_dictua_entries + ulif_dictua_sections",
                "fe9f52cb261736443f511a85b52e8ee6fe05b51165c56384cfa969b411429b98",
                "sorted content_sha256 of the 262,788 checked rows; sections are parsed from the same responses",
            ),
            "puls": _input(
                "sources.puls_cefr",
                "98fc5be3e986f944fcf84cad34325ecbf770d22fc2dc54caa4b548f06e7f6b5a",
                "5,939 rows, canonical-row recipe",
            ),
            "frazeolohichnyi": _input(
                "sources.frazeolohichnyi",
                "9889123be2ce073528ee038c66824ba35af118d2b702b4e8cb0723156015f108",
                "24,683 rows, canonical-row recipe",
            ),
            "wiktionary": _input(
                "sources.wiktionary",
                "ead3e1bc521293fde1cdbc3767d0131aca41e6b2e1701e93de17f919e3a89d69",
                "50,278 rows, canonical-row recipe",
            ),
            "atlas0": _input(
                "data/atlas.db manifest 0.1 generated_at 2026-09-11T10:12:36+00:00",
                "fcf802bda35dd4cd99e95317da0f4a1fa9315024befc83e73673c106278ebfca",
                "frozen file; source of the migrated kaikki, vts, slovnyk_me, synonyms_karavansky, "
                "ukrainian_word_stress, grac, grac_estimate and course_authored assertions",
            ),
            "atlas_curated": _input(
                "site/src/lib/lexicon/curated-heteronyms.ts",
                "14d56cb53fdf14dd7e8b0155a2f1770f740cff93b3e10f8f0eb5bfb67be72f99",
                "420-lemma side file (retired into the overlay at M2)",
            ),
        },
        "V": {
            "vesum": _input(
                "data/vesum.db vesum_build_metadata.canonical_jsonl_sha256",
                "53923150073b4fc7bee419fe7b071acbe17b6a9aba76cfb2d0336c95f5188680",
                "schema_version vesum-reingest-v1",
            )
        },
        "I": {
            "identity_registry": _input(
                "examples/companion/identity-registry.json",
                sha256_of(REGISTRY),
                "frozen before assembly; assembly refuses ids it does not allocate",
                version=f"registry_version {REGISTRY['registry_version']}",
            )
        },
        "O": {
            "overlay": _input("examples/companion/overlay.json", sha256_of(OVERLAY), "one split entry"),
            "suppressions": _input(
                "examples/companion/suppression-selectors.json", sha256_of(SUPPRESSIONS), "three selectors"
            ),
        },
        "R": {
            "rules": _input("resolve() in build_examples.py", version=RULES),
            "normaliser": _input("normalise() in build_examples.py", version=NORMALISER),
            "register": _input(
                "docs/sources/permissions-register.yaml",
                REGISTER_SHA256,
                version=f"schema_version {REGISTER_VERSION}, register_date 2026-09-28",
            ),
        },
    },
}
# Which manifest input every source id is read from (the test walks every assertion through this).
SOURCE_INPUT = {
    "ulif": ("S", "ulif"),
    "puls": ("S", "puls"),
    "frazeolohichnyi": ("S", "frazeolohichnyi"),
    "wiktionary": ("S", "wiktionary"),
    "atlas_curated": ("S", "atlas_curated"),
    "vesum": ("V", "vesum"),
    **{
        s: ("S", "atlas0")
        for s in (
            "kaikki",
            "vts",
            "slovnyk_me",
            "synonyms_karavansky",
            "ukrainian_word_stress",
            "grac",
            "grac_estimate",
            "course_authored",
        )
    },
}


def aid(
    source_id: str, snapshot_id: str, locator: str, subject: dict, field: str, value_norm: str, extraction_version: str
) -> str:
    payload = {
        "source_id": source_id,
        "snapshot_id": snapshot_id,
        "locator": locator,
        "subject": subject,
        "field": field,
        "value_norm": value_norm,
        "extraction_version": extraction_version,
    }
    canon = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return "wa_" + hashlib.sha256(canon.encode("utf-8")).hexdigest()[:24]


def derivation_id(
    generator: str,
    generator_version: str,
    rules_version: str,
    configuration_sha256: str,
    inputs: dict,
    output_kind: str,
    output_key: str,
) -> str:
    """`wd_` + sha256 over generator, its version, the rules version, the configuration digest, the inputs and
    the output identity (schema.md §11): two revisions of one output under different rules or settings are
    two records, they never collide."""
    ident = {
        "generator": generator,
        "generator_version": generator_version,
        "rules_version": rules_version,
        "configuration_sha256": configuration_sha256,
        "inputs": inputs,
        "output": {"kind": output_kind, "key": output_key},
    }
    return "wd_" + hashlib.sha256(canonical(ident).encode()).hexdigest()[:24]


# The GRAC→CEFR estimate on броня (armour) is a GENERATED assertion: it names the derivation that produced it
# (`producer.derived_id`), and that derivation names the frequency assertion it read, so invalidation can walk
# source -> generated assertion -> consumer (schema.md §11, §12.2). Ids are computed up front because the
# assertion id does not depend on the producer block.
_BRONIA_SUBJECT = {"kind": "card", "id": BRONIA_ARMOUR}
BRONIA_FREQ_LOCATOR = "atlas0:enrichment:броня/cefr text 'GRAC 0.55/million, rank 2792/4161'"
BRONIA_CEFR_LOCATOR = "atlas0:enrichment:броня/cefr 'estimated (GRAC frequency)' 0.55/million rank 2792/4161"
BRONIA_FREQ_AID = aid(
    "grac",
    ATLAS0_SNAP,
    BRONIA_FREQ_LOCATOR,
    _BRONIA_SUBJECT,
    "frequency",
    "grac:0.55/million;rank 2792/4161",
    "atlas0-migration",
)
BRONIA_CEFR_AID = aid("grac_estimate", ATLAS0_SNAP, BRONIA_CEFR_LOCATOR, _BRONIA_SUBJECT, "cefr", "B2", "v1")
ESTIMATE_CONFIGURATION = {
    "ref": "atlas0 GRAC-frequency band settings (migrated; not recorded separately, pinned by the atlas0 file)",
    "sha256": "fcf802bda35dd4cd99e95317da0f4a1fa9315024befc83e73673c106278ebfca",
}
ESTIMATE_INPUTS = {"assertion_ids": [BRONIA_FREQ_AID], "card_ids": [], "card_versions": {}}
ESTIMATE_DERIVATION_ID = derivation_id(
    "grac_frequency_cefr_estimator",
    "atlas0",
    RULES,
    ESTIMATE_CONFIGURATION["sha256"],
    ESTIMATE_INPUTS,
    "assertion",
    BRONIA_CEFR_AID,
)


# ---------------------------------------------------------------- links (canonical records, schema.md §7.2)
# Symmetric types have one record for both cards; endpoints are ordered by role rank, then by id.
SYMMETRIC = {"aspect_pair", "homograph_of", "stress_variant_of", "synonym", "antonym", "russification_contrast"}
ROLE_RANK = {"imperfective": 0, "perfective": 1, "norm": 0, "imposed": 1}


def link(link_type: str, endpoints: list[dict], assertion_ids: list[str], *, basis: str = "asserted", derived_by=None):
    eps = [dict(e) for e in endpoints]
    if link_type in SYMMETRIC:
        eps.sort(key=lambda e: (ROLE_RANK.get(e.get("role", ""), 9), e["id"]))
    canon = "|".join(f"{e['id']}:{e.get('role', '')}:{e.get('sense_id', '')}" for e in eps)
    rec = {
        "link_id": "wl_" + hashlib.sha256(f"{link_type}|{canon}".encode()).hexdigest()[:24],
        "type": link_type,
        "endpoints": eps,
        "basis": basis,
        "assertion_ids": sorted(assertion_ids),
        "state": "active" if assertion_ids else "suppressed",
    }
    if derived_by:
        rec["derived_by"] = derived_by
    return rec


def A(
    subject_kind,
    subject_id,
    field,
    value,
    *,
    source,
    snapshot,
    locator,
    xv="v1",
    xconf="high",
    producer=None,
    review=None,
    value_norm=None,
    mapping=None,
    status="active",
    suppression_ref=None,
):
    subject = {"kind": subject_kind, "id": subject_id}
    vn = (
        value_norm
        if value_norm is not None
        else (value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, sort_keys=True))
    )
    group, tier = GROUPS[source if source in GROUPS else "course_authored"]
    a = {
        "assertion_id": aid(source, snapshot, locator, subject, field, vn, xv),
        "subject": subject,
        "field": field,
        "value": value,
        "value_norm": vn,
        "source_id": source,
        "snapshot_id": snapshot,
        "locator": locator,
        "extraction_version": xv,
        "extraction_confidence": xconf,
        "producer": producer or {"kind": "source_extract", "name": f"{source} extractor", "version": xv},
        "review": review or {"status": "none"},
        "licence_ref": {"register_source_id": source, "register_version": REGISTER_VERSION},
        "independence_group": group,
        "tier": tier,
        "status": status,
    }
    rk = record_key(locator)
    if rk:
        a["source_record_id"] = record_id(locator)
        a["source_record_key"] = rk
    if mapping:
        a["mapping"] = mapping
    if suppression_ref:
        a["suppression_ref"] = suppression_ref
    return a


# ---------------------------------------------------------------- field resolution (schema.md §8)
# Comparison class per field: what proposition two assertions are compared on.
#   scalar: one proposition per (subject, field); different value_norms contradict (stress, pos, cefr ...).
#   keyed:  value_norm is "<key>=<value>"; one proposition per key; contradiction only inside a key (paradigm).
#   text:   each source's text is its own proposition; different texts are parallel, never a conflict.
KEYED_FIELDS = {"paradigm"}
TEXT_FIELDS = {
    "definition_uk",
    "gloss_en",
    "english_gloss",
    "sense_label",
    "examples",
    "collocations",
    "russification_exposed",
    "synonyms",
    "antonyms",
    "spelling_variants",
    "register",
    "mwe_frame",
}
CONF_ORDER = ["high", "medium", "low"]
STATE_RANK = {"verified": 0, "variant": 1, "single-source": 2, "unverified": 3, "conflict": 4, "suppressed": 5}


def comparison_class(field: str) -> str:
    if field in KEYED_FIELDS:
        return "keyed"
    if field in TEXT_FIELDS:
        return "text"
    return "scalar"


def _groups(xs: list[dict]) -> list[str]:
    return sorted({x["independence_group"] for x in xs if not x["independence_group"].endswith("?")})


def _unambiguous(xs: list[dict]) -> list[dict]:
    """Assertions whose mapping to THIS card is not an ambiguous spelling-level match (§9.5)."""
    return [a for a in xs if not a.get("mapping", {}).get("ambiguous", False)]


def _value_entry(vn: str, xs: list[dict], declared: bool = False, declared_by: str | None = None) -> dict:
    """One proposition (`field = vn`, or `field ∈ set` for a declared set) with its own evidence counts.
    Evidence is per proposition (Astra gap 4): a proposition is evidenced when at least one assertion stating
    it maps to this card unambiguously; corroboration among evidenced assertions is counted on it alone."""
    ev = _unambiguous(xs)
    entry = {
        "value_norm": vn,
        "assertion_ids": sorted(x["assertion_id"] for x in xs),
        "independence_groups": _groups(xs),
        "mapping_evidenced": bool(ev),
        "independence_groups_evidenced": len(_groups(ev)),
    }
    if declared:
        entry["declared_set"] = True
    if declared_by:
        entry["declared_by"] = declared_by
    return entry


def _conflict(values: list[dict], **extra) -> dict:
    return {"state": "conflict", "selected": None, "values": values, "independence_groups_agreeing": 0, **extra}


def _resolve_scalar(voting: list[dict], overlay: dict | None) -> dict:
    declared = [a for a in voting if a["tier"] == 1 and "|" in a["value_norm"]]
    members = [a for a in voting if a not in declared]
    by_value: dict[str, list[dict]] = {}
    for a in members:
        by_value.setdefault(a["value_norm"], []).append(a)
    values = [_value_entry(vn, xs) for vn, xs in sorted(by_value.items())]
    by_decl: dict[str, list[dict]] = {}
    for d in declared:
        by_decl.setdefault(d["value_norm"], []).append(d)
    values += [_value_entry(vn, xs, declared=True) for vn, xs in sorted(by_decl.items())]
    observed = set(by_value)
    declared_sets = {frozenset(vn.split("|")) for vn in by_decl}
    # Reviewed overlay `variant` (§8.2 rule 4, §12): the language lane declares the set with evidence; it resolves
    # both conflicting single values and disagreeing tier-1 declarations. Every observed value must be a member.
    if overlay and overlay.get("kind") == "variant":
        members_declared = set(overlay["members"])
        vn = "|".join(sorted(members_declared))
        values.append(_value_entry(vn, [], declared=True, declared_by=overlay["overlay_id"]))
        if observed <= members_declared and all(s <= members_declared for s in declared_sets):
            return {
                "state": "variant",
                "selected": sorted(a["assertion_id"] for a in voting),
                "values": values,
                "independence_groups_agreeing": len(_groups(voting)),
                "resolution_ref": overlay["overlay_id"],
            }
        return _conflict(values, resolution_ref=overlay["overlay_id"])
    # Compatibility of several tier-1 declarations (Astra gap 5): declared sets corroborate only when they are
    # EQUAL as sets. Disjoint (`a|b` vs `c|d`) or partially overlapping (`a|b` vs `a|b|c`) declarations are a
    # disagreement about which stresses are permitted -> conflict, listed for the language lane (an overlay
    # `variant` is the reviewed way out). Never resolved by rule to the union or the intersection.
    if len(declared_sets) > 1:
        return _conflict(values)
    # One declared set: every observed single value must be a member (declaration alone, or one member, is fine).
    if declared_sets:
        (the_set,) = declared_sets
        if observed <= the_set:
            return {
                "state": "variant",
                "selected": sorted(a["assertion_id"] for a in voting),
                "values": values,
                "independence_groups_agreeing": len(_groups(voting)),
            }
        return _conflict(values)  # a declared set that does not contain an observed value is a disagreement
    if len(by_value) == 1:
        v = values[0]
        n = len(v["independence_groups"])
        return {
            "state": "verified" if n >= 2 else "single-source",
            "selected": v["assertion_ids"][0],
            "values": values,
            "independence_groups_agreeing": n,
        }
    if overlay and overlay.get("kind") == "resolve":
        chosen = overlay["assertion_id"]
        v = next(x for x in values if chosen in x["assertion_ids"])
        n = len(v["independence_groups"])
        return {
            "state": "verified" if n >= 2 else "single-source",
            "selected": chosen,
            "values": values,
            "independence_groups_agreeing": n,
            "resolution_ref": overlay["overlay_id"],
        }
    return _conflict(values)


def _resolve_text(voting: list[dict]) -> dict:
    """Texts are parallel propositions: identical texts corroborate, different texts never conflict."""
    by_value: dict[str, list[dict]] = {}
    for a in voting:
        by_value.setdefault(a["value_norm"], []).append(a)
    values = [_value_entry(vn, xs) for vn, xs in sorted(by_value.items())]

    # shown first: the value with most independent groups, then lowest tier, then lowest assertion id
    def rank(v):
        tier = min(a["tier"] for a in by_value[v["value_norm"]])
        return (-len(v["independence_groups"]), tier, v["assertion_ids"][0])

    best = sorted(values, key=rank)[0]
    n = len(best["independence_groups"])
    return {
        "state": "verified" if n >= 2 else "single-source",
        "selected": best["assertion_ids"][0],
        "values": values,
        "independence_groups_agreeing": n,
    }


def _shown_entries(res: dict) -> list[dict]:
    sel = res["selected"]
    sel_ids = set(sel if isinstance(sel, list) else ([sel] if sel else []))
    return [v for v in res["values"] if sel_ids & set(v["assertion_ids"]) or v.get("declared_by")]


def _evidence_of(res: dict) -> dict:
    """Field-level evidence = every shown proposition is evidenced; corroboration = the weakest shown one."""
    shown = [v for v in _shown_entries(res) if v["assertion_ids"]]
    return {
        "mapping_evidenced": bool(shown) and all(v["mapping_evidenced"] for v in shown),
        "independence_groups_evidenced": min((v["independence_groups_evidenced"] for v in shown), default=0),
    }


def _resolve_keyed(voting: list[dict], overlay: dict | None) -> dict:
    """One proposition per slot (`rod.sg=замку`). Evidence and corroboration are recorded per slot in
    `propositions`; an item that consumes one slot reads that slot. The field-level flags are the conjunction
    (evidence) and the minimum (corroboration) over the slots, so one evidenced slot never covers another."""
    parts: dict[str, list[dict]] = {}
    for a in voting:
        parts.setdefault(a["value_norm"].split("=", 1)[0], []).append(a)
    per_key = {k: _resolve_scalar(xs, overlay) for k, xs in sorted(parts.items())}
    worst = max(per_key.values(), key=lambda r: STATE_RANK[r["state"]])
    selected = [r["selected"] for r in per_key.values() if isinstance(r["selected"], str)]
    for r in per_key.values():
        if isinstance(r["selected"], list):
            selected += r["selected"]
    propositions = {
        k: {"state": r["state"], "selected": r["selected"], **_evidence_of(r)}
        | ({"resolution_ref": r["resolution_ref"]} if "resolution_ref" in r else {})
        for k, r in per_key.items()
    }
    return {
        "state": worst["state"],
        "selected": sorted(selected) if worst["state"] != "conflict" else None,
        "values": [v for r in per_key.values() for v in r["values"]],
        "independence_groups_agreeing": min(r["independence_groups_agreeing"] for r in per_key.values()),
        "propositions": propositions,
        "mapping_evidenced": all(p["mapping_evidenced"] for p in propositions.values()),
        "independence_groups_evidenced": min(p["independence_groups_evidenced"] for p in propositions.values()),
    }


def resolve(assertions: list[dict], field: str, subject_id: str, overlay: dict | None = None) -> dict:
    """Reference implementation of schema.md §8 (field resolution). Kept small on purpose."""
    mine = [a for a in assertions if a.get("field") == field and a.get("subject", {}).get("id") == subject_id]
    cls = comparison_class(field)
    non_voting: list[dict] = []
    active: list[dict] = []
    for a in mine:
        if a["status"] != "active":
            continue
        conf = a.get("mapping", {}).get("confidence", "high")
        if conf not in ("high", "medium"):
            non_voting.append({"assertion_id": a["assertion_id"], "reason": f"mapping {conf}"})
        elif a["review"]["status"] == "rejected":
            non_voting.append({"assertion_id": a["assertion_id"], "reason": "review rejected"})
        else:
            active.append(a)
    base = {"comparison": cls, "proposition": _proposition(cls, field, subject_id)}
    if non_voting:
        base["non_voting"] = sorted(non_voting, key=lambda x: x["assertion_id"])
    if not active:
        state = "suppressed" if any(a["status"] == "suppressed" for a in mine) else "unverified"
        return {
            "state": state,
            "selected": None,
            "values": [],
            "mapping_evidenced": False,
            "independence_groups_evidenced": 0,
            **base,
        }
    voting = [a for a in active if a["tier"] in (1, 2)]
    if not voting:
        first = sorted(active, key=lambda a: a["assertion_id"])[0]
        entry = _value_entry(first["value_norm"], active)
        return {
            "state": "unverified",
            "selected": first["assertion_id"],
            "values": [entry],
            "independence_groups_agreeing": 0,
            "mapping_evidenced": entry["mapping_evidenced"],
            "independence_groups_evidenced": 0,
            **base,
        }
    if cls == "text":
        res = _resolve_text(voting)
    elif cls == "keyed":
        res = _resolve_keyed(voting, overlay)
    else:
        res = _resolve_scalar(voting, overlay)
    if "mapping_evidenced" not in res:
        res.update(_evidence_of(res))
    res.update(base)
    return res


def _proposition(cls: str, field: str, subject_id: str) -> str:
    if cls == "keyed":
        return f"{field}({subject_id})[<key>] = <value>; one proposition per key"
    if cls == "text":
        return f"{field}({subject_id}) ∋ <text>; parallel texts, identical texts corroborate"
    return f"{field}({subject_id}) = <value_norm>"


def card_version(card_public: dict) -> str:
    """`cv_` + sha256 over EVERYTHING a consumer can read from the public card (schema.md §11): identity and
    key, state and successors, senses with their resolutions, links, fields, the retained assertions (as the
    projection carries them), quality including eligibility and review, and the overlay applied. Only the
    `build` block is excluded (it contains the version itself). Changing identity confidence, an eligibility
    verdict or a review status therefore changes the version and invalidates the derivations that pinned it."""
    body = {k: v for k, v in card_public.items() if k != "build"}
    return "cv_" + hashlib.sha256(canonical(body).encode()).hexdigest()[:24]


def card(
    card_id,
    kind,
    key,
    identity,
    senses,
    links,
    assertions,
    eligibility,
    review=None,
    state="active",
    merged_into=None,
    split_into=None,
    overlay=None,
):
    # Assembly consumes a FROZEN registry (schema.md §13): it never mints. An id the registry does not
    # allocate is a hard failure, not a random allocation; allocation is a separate committed step.
    if card_id not in ALLOCATED_CARDS:
        raise MissingAllocation(f"card {card_id} is not allocated in identity registry v{REGISTRY['registry_version']}")
    for s in senses:
        if s["sense_id"] not in ALLOCATED_CARDS[card_id]:
            raise MissingAllocation(f"sense {s['sense_id']} of {card_id} is not allocated in the identity registry")
    out = {
        "schema_version": "1",
        "card_id": card_id,
        "card_kind": kind,
        "state": state,
        "merged_into": merged_into,
        "split_into": split_into,
        "key_at_creation": key,
        "identity": identity,
        "senses": senses,
        "links": links,
        "fields": {},
        "assertions": assertions,
        "quality": {
            "identity_confidence": identity["confidence"],
            # the card's summary is the WORST extraction confidence among its assertions
            "extraction_confidence_min": max((a["extraction_confidence"] for a in assertions), key=CONF_ORDER.index)
            if assertions
            else "high",
            "linguistic_review": review or {"status": "none"},
            "practice_eligibility": eligibility,
        },
        "overlay_applied": overlay or [],
        "build": dict(BUILD),
    }
    _recompute(out)
    out["build"]["card_version"] = card_version(_project(out))
    return out


def _recompute(c: dict) -> None:
    """Field resolutions and link states from the assertions as they are NOW (schema.md §12.2): called at
    assembly and again before every public projection, so a suppression is reflected everywhere."""
    asr = c["assertions"]
    card_fields = sorted({a["field"] for a in asr if a.get("subject", {}).get("kind") == "card"})
    c["fields"] = {f: resolve(asr, f, c["card_id"]) for f in card_fields}
    if c["fields"].get("english_gloss"):
        c["fields"]["english_gloss"]["level_policy"] = "scaffold: shown at A1 by design, never raised from A2 (#8983)"
    for s in c["senses"]:
        sf = sorted({a["field"] for a in asr if a.get("subject", {}).get("id") == s["sense_id"]})
        s["fields"] = {f: resolve(asr, f, s["sense_id"]) for f in sf}
    known = {a["assertion_id"]: a["status"] for a in asr if "assertion_id" in a}
    for link_rec in c["links"]:
        cited = [
            known[i] for i in link_rec["assertion_ids"] if i in known
        ]  # cross-card evidence is checked at build level
        if cited and all(st != "active" for st in cited):
            link_rec["state"] = "suppressed"


def _project(c: dict) -> dict:
    out = json.loads(json.dumps(c, ensure_ascii=False))
    _recompute(out)
    out["assertions"] = [
        a
        if a["status"] != "suppressed"
        else {
            "assertion_id": a["assertion_id"],
            "status": "suppressed",
            "suppression_ref": a.get("suppression_ref", ""),
        }
        for a in out["assertions"]
    ]
    return out


def public_projection(c: dict) -> dict:
    """Public outputs are RECOMPUTED from the surviving assertions and then carry suppressed assertions as
    tombstones only (schema.md §12.3): a withdrawn value is gone from `fields`, `senses[].fields`, `links`
    and `assertions` alike, and the projection's `card_version` reflects the withdrawal."""
    out = _project(c)
    out["build"]["card_version"] = card_version(out)
    return out


def sense(sense_id, order, smap, state="active"):
    return {"sense_id": sense_id, "order": order, "state": state, "merged_into": None, "sense_map": smap, "fields": {}}


PULS_SPELLING = {
    "confidence": "medium",
    "basis": "spelling",
    "ambiguous": True,
    "note": "PULS rows are keyed by spelling and this spelling has several cards; retained and shown, "
    "but not evidence for a dependent eligibility rule until an overlay maps the row (schema.md §9.5)",
}

# Spelling assertions per example card, used as the derived evidence of homograph_of links.
SPELLINGS = {
    CASTLE: ("замок", [("vesum", VESUM_SNAP, "vesum:entry:128973"), ("ulif", ULIF_SNAP, "ulif:entry:76792")]),
    LOCK: ("замок", [("vesum", VESUM_SNAP, "vesum:entry:128972"), ("ulif", ULIF_SNAP, "ulif:entry:76793")]),
    SETTLEMENT: (
        "Замок",
        [
            ("vesum", VESUM_SNAP, "vesum:entry:128971 (noun:inanim:m:v_naz:prop:geo)"),
            ("ulif", ULIF_SNAP, "ulif:entry:76791"),
        ],
    ),
    KLIUCH1: ("ключ", [("vesum", VESUM_SNAP, "vesum:entry:168409"), ("ulif", ULIF_SNAP, "ulif:entry:3")]),
    KLIUCH2: ("ключ", [("ulif", ULIF_SNAP, "ulif:entry:98008")]),
    BRONIA_ARMOUR: ("броня", [("vesum", VESUM_SNAP, "vesum:entry:30497"), ("ulif", ULIF_SNAP, "ulif:entry:29075")]),
    BRONIA_RESERV: ("броня", [("ulif", ULIF_SNAP, "ulif:entry:29074")]),
}


def spelling_aids(cid: str) -> list[str]:
    sp, rows = SPELLINGS[cid]
    return [aid(src, snap, loc, {"kind": "card", "id": cid}, "spelling", sp, "v1") for src, snap, loc in rows]


def homograph(a: str, b: str) -> dict:
    """Derived link: two active cards whose key_at_creation.spelling is equal ignoring case. Evidence =
    the spelling assertions of both endpoints (schema.md §7.2: a link with no evidence is suppressed)."""
    return link(
        "homograph_of",
        [{"id": a}, {"id": b}],
        spelling_aids(a) + spelling_aids(b),
        basis="derived",
        derived_by=f"rules:{RULES} equal key_at_creation.spelling (case-insensitive), distinct identity",
    )


def build_castle():
    cid = CASTLE
    s1, s2, s3 = "ws_a1b2c3d4e5f6", "ws_b2c3d4e5f6g7", "ws_c3d4e5f6g7h8"
    asr = [
        A("card", cid, "spelling", "замок", source="vesum", snapshot=VESUM_SNAP, locator="vesum:entry:128973"),
        A("card", cid, "spelling", "замок", source="ulif", snapshot=ULIF_SNAP, locator="ulif:entry:76792"),
        A(
            "card",
            cid,
            "stress",
            "за́мок",
            source="ulif",
            snapshot=ULIF_SNAP,
            locator="ulif:entry:76792 canonical_headword",
        ),
        A(
            "card",
            cid,
            "stress",
            "за́мок (будівля)",
            value_norm="за́мок",
            source="vesum",
            snapshot=VESUM_SNAP,
            locator="vesum:entry:128973 source_comment",
            xconf="medium",
        ),
        A(
            "card",
            cid,
            "stress",
            "за́мок",
            source="kaikki",
            snapshot=ATLAS0_SNAP,
            locator="atlas0:enrichment:замок/stress (kaikki/Wiktionary)",
            mapping={
                "confidence": "medium",
                "basis": "stress",
                "note": "kaikki row is spelling-keyed; its stress за́мок matches this card only (lock is замо́к)",
            },
        ),
        A("card", cid, "pos", "noun", source="vesum", snapshot=VESUM_SNAP, locator="vesum:entry:128973 pos"),
        A(
            "card",
            cid,
            "pos",
            "іменник чоловічого роду",
            value_norm="noun",
            source="ulif",
            snapshot=ULIF_SNAP,
            locator="ulif:entry:76792 grammatical_label",
        ),
        A(
            "card",
            cid,
            "gender",
            "m",
            source="vesum",
            snapshot=VESUM_SNAP,
            locator="vesum:entry:128973 tags noun:inanim:m:v_naz:xp2",
        ),
        A(
            "card",
            cid,
            "gender",
            "іменник чоловічого роду",
            value_norm="m",
            source="ulif",
            snapshot=ULIF_SNAP,
            locator="ulif:entry:76792 grammatical_label",
        ),
        A(
            "card",
            cid,
            "paradigm",
            [["називний", "за́мок", "за́мки"], ["родовий", "за́мку", "за́мків"], ["давальний", "за́мку, за́мкові", "за́мкам"]],
            value_norm="rod.sg=замку",
            source="ulif",
            snapshot=ULIF_SNAP,
            locator="ulif:entry:76792/section:96929 rows[1..3]",
        ),
        A(
            "card",
            cid,
            "paradigm",
            {"v_rod_sg": "замку", "v_dav_sg": ["замкові", "замку"]},
            value_norm="rod.sg=замку",
            source="vesum",
            snapshot=VESUM_SNAP,
            locator="vesum:entry:128973 forms",
        ),
        A(
            "card",
            cid,
            "cefr",
            "A2",
            source="puls",
            snapshot=ATLAS0_SNAP,
            locator="sources.puls_cefr:id:4340 (замок, іменник)",
            mapping=PULS_SPELLING,
        ),
        A(
            "card",
            cid,
            "english_gloss",
            "castle",
            source="kaikki",
            snapshot=ATLAS0_SNAP,
            locator="atlas0:enrichment:замок/meaning definitions[0]",
            mapping={
                "confidence": "medium",
                "basis": "sense",
                "note": "spelling-keyed list [castle, lock]; item mapped by rule: matches ULIF sense_gloss (будівля)",
            },
        ),
        A(
            "card",
            cid,
            "english_gloss",
            "castle, fortress, palace",
            source="atlas_curated",
            snapshot=ATLAS0_SNAP,
            locator="site/src/lib/lexicon/curated-heteronyms.ts замок[0].gloss",
            producer={"kind": "curator", "name": "curated-heteronyms batch", "version": "13 batches"},
            review={"status": "reviewed", "lane": "human", "record": "#8334 side file"},
        ),
        A(
            "sense",
            s1,
            "definition_uk",
            "Укріплене житло феодала доби середньовіччя з оборонними, господарськими, культовими і т. ін. будівлями, зазвичай оточене високим кам'яним муром із кількома вежами. || Великий поміщицький будинок; палац.",
            source="vts",
            snapshot=ATLAS0_SNAP,
            locator="atlas0:enrichment:замок/definition_cards vts 'I з`амок' 1》",
            mapping={"confidence": "high", "note": "ВТС homonym I = castle (stress mark after з)"},
        ),
        A(
            "sense",
            s1,
            "synonyms",
            ["ПАЛА́Ц", "ПАЛА́ТИ", "ДВІРО́К", "ДВОРЕ́ЦЬ", "ЗА́МОК"],
            source="ulif",
            snapshot=ULIF_SNAP,
            locator="ulif:entry:76792/section:96931 (synonyms:2) terms",
        ),
        A(
            "sense",
            s3,
            "synonyms",
            ["фортеця", "бастіон", "цитадель", "шато"],
            source="synonyms_karavansky",
            snapshot=ATLAS0_SNAP,
            locator="atlas0:enrichment:замок/synonyms (slovnyk.me: Словник синонімів Караванського)",
            mapping={
                "confidence": "medium",
                "basis": "spelling",
                "ambiguous": True,
                "note": "spelling-keyed; one unit on the source side does not align it to a sense (§6): held unsplit",
            },
        ),
        A(
            "sense",
            s2,
            "definition_uk",
            "заст., рідко. Тюремна будівля; тюрма.",
            source="vts",
            snapshot=ATLAS0_SNAP,
            locator="atlas0:enrichment:замок/definition_cards vts 'I з`амок' 2》",
        ),
        A(
            "sense",
            s2,
            "register",
            "заст., рідко",
            source="vts",
            snapshot=ATLAS0_SNAP,
            locator="atlas0:enrichment:замок/definition_cards vts 'I з`амок' 2》 label",
        ),
        A(
            "sense",
            s3,
            "synonyms",
            ["КРЕМЛЬ", "ДИТИ́НЕЦЬ", "ЗА́МОК"],
            source="ulif",
            snapshot=ULIF_SNAP,
            locator="ulif:entry:76792/section:96930 (synonyms:1) terms",
        ),
    ]
    senses = [
        sense(
            s1,
            1,
            [
                {"source_id": "vts", "source_sense_key": "vts:замок#I/1"},
                {"source_id": "ulif", "source_sense_key": "ulif:section:96931"},
            ],
        ),
        sense(s2, 2, [{"source_id": "vts", "source_sense_key": "vts:замок#I/2"}]),
        sense(
            s3,
            3,
            [
                {"source_id": "ulif", "source_sense_key": "ulif:section:96930"},
                {
                    "source_id": "synonyms_karavansky",
                    "source_sense_key": "slovnyk_me:synonyms_karavansky:замок",
                    "mapped_by": "rules: single unit on the source side only; awaiting a sense_map overlay",
                },
            ],
            state="unsplit",
        ),
    ]
    links = [homograph(cid, LOCK), homograph(cid, SETTLEMENT)]
    identity = {
        "confidence": "high",
        "method": "stress_and_paradigm",
        "decided_by": f"rules:{RULES}",
        "source_keys": [
            {
                "source_id": "vesum",
                "key": "vesum:entry:128973",
                "snapshot_id": VESUM_SNAP,
                "match_note": "xp2 за́мок (будівля); v_rod замку",
            },
            {
                "source_id": "ulif",
                "key": "ulif:entry:76792",
                "snapshot_id": ULIF_SNAP,
                "match_note": "homonym 2 за́мок (будівля); родовий за́мку",
            },
            {
                "source_id": "vts",
                "key": "vts:замок#I",
                "snapshot_id": ATLAS0_SNAP,
                "match_note": "'I з`амок' stress after з",
            },
            {
                "source_id": "atlas0",
                "key": "atlas0:slug:замок",
                "snapshot_id": ATLAS0_SNAP,
                "match_note": "legacy merged article castle / lock; split",
            },
            {"source_id": "atlas0", "key": "atlas0:heteronym:замок/за́мок", "snapshot_id": ATLAS0_SNAP},
        ],
        "notes": [
            "VESUM and ULIF number the homonyms differently (vesum xp1 = lock, xp2 = castle; ulif 1 = settlement, 2 = castle, 3 = lock); matched by genitive singular and stress, never by number or spelling."
        ],
    }
    elig = [
        {
            "mode": "stress",
            "eligible": False,
            "rules_version": RULES,
            "reasons": [
                "stress verified (3 groups), identity high",
                "cefr A2 is single-source but mapping_evidenced=false: PULS row 4340 is spelling-keyed and the spelling has "
                "two lexeme cards; the level band rule is unmet until an overlay maps the row (§9.5)",
            ],
        },
        {
            "mode": "synonyms",
            "eligible": False,
            "rules_version": RULES,
            "reasons": [
                "sense s1 synonyms single-source (ULIF group 96931)",
                "cefr not evidenced for this card (see stress mode)",
                "Караванський group held unsplit on s3 (§6), excluded",
            ],
            "sense_id": s1,
        },
        {
            "mode": "meaning",
            "eligible": False,
            "rules_version": RULES,
            "reasons": [
                "definition_uk single-source ВТС; english_gloss single-source; needs sampled review before A1–B1 meaning items"
            ],
        },
    ]
    return card(
        cid,
        "lexeme",
        {
            "spelling": "замок",
            "stress_patterns": ["за́мок"],
            "pos": "noun",
            "paradigm_key": "vesum:entry:128973",
            "source_keys": [
                {"source_id": "vesum", "key": "vesum:entry:128973"},
                {"source_id": "ulif", "key": "ulif:entry:76792"},
            ],
        },
        identity,
        senses,
        links,
        asr,
        elig,
    )


def build_lock():
    cid = LOCK
    s1, s2, s3 = "ws_d4e5f6g7h8j9", "ws_e5f6g7h8j9k1", "ws_f6g7h8j9k1m2"
    asr = [
        A("card", cid, "spelling", "замок", source="vesum", snapshot=VESUM_SNAP, locator="vesum:entry:128972"),
        A("card", cid, "spelling", "замок", source="ulif", snapshot=ULIF_SNAP, locator="ulif:entry:76793"),
        A(
            "card",
            cid,
            "stress",
            "замо́к",
            source="ulif",
            snapshot=ULIF_SNAP,
            locator="ulif:entry:76793/section:96933 rows[1][1]",
            xconf="medium",
            producer={"kind": "source_extract", "name": "ulif paradigm-row headword recovery", "version": "v1"},
        ),
        A(
            "card",
            cid,
            "stress",
            "замо́к (пристрій)",
            value_norm="замо́к",
            source="vesum",
            snapshot=VESUM_SNAP,
            locator="vesum:entry:128972 source_comment",
            xconf="medium",
        ),
        A("card", cid, "pos", "noun", source="vesum", snapshot=VESUM_SNAP, locator="vesum:entry:128972 pos"),
        A(
            "card",
            cid,
            "gender",
            "m",
            source="vesum",
            snapshot=VESUM_SNAP,
            locator="vesum:entry:128972 tags noun:inanim:m:v_naz:xp1",
        ),
        A(
            "card",
            cid,
            "paradigm",
            [["називний", "замо́к", "замки́"], ["родовий", "замка́", "замкі́в"], ["давальний", "замку́, замко́ві", "замка́м"]],
            value_norm="rod.sg=замка",
            source="ulif",
            snapshot=ULIF_SNAP,
            locator="ulif:entry:76793/section:96933 rows[1..3]",
        ),
        A(
            "card",
            cid,
            "paradigm",
            {"v_rod_sg": "замка", "v_dav_sg": ["замкові", "замку"]},
            value_norm="rod.sg=замка",
            source="vesum",
            snapshot=VESUM_SNAP,
            locator="vesum:entry:128972 forms",
        ),
        A(
            "card",
            cid,
            "cefr",
            "A2",
            source="puls",
            snapshot=ATLAS0_SNAP,
            locator="sources.puls_cefr:id:4340 (замок, іменник)",
            mapping=PULS_SPELLING,
        ),
        A(
            "card",
            cid,
            "english_gloss",
            "lock, locks",
            source="course_authored",
            snapshot=ATLAS0_SNAP,
            locator="atlas0:enrichment:замок/translation learner_english_gloss en[0]",
            producer={"kind": "generator", "name": "learner_english_gloss", "version": "atlas0"},
        ),
        A(
            "card",
            cid,
            "english_gloss",
            "lock (door lock, padlock)",
            source="atlas_curated",
            snapshot=ATLAS0_SNAP,
            locator="site/src/lib/lexicon/curated-heteronyms.ts замок[1].gloss",
            producer={"kind": "curator", "name": "curated-heteronyms batch", "version": "13 batches"},
            review={"status": "reviewed", "lane": "human", "record": "#8334 side file"},
        ),
        A(
            "sense",
            s1,
            "synonyms",
            ["ЗАМО́К", "ЗАПІ́Р", "ЗА́ПІРКА", "КОЛО́ДКА"],
            source="ulif",
            snapshot=ULIF_SNAP,
            locator="ulif:entry:76793/section:96935 (synonyms:2) terms",
        ),
        A(
            "sense",
            s1,
            "register",
            ["рідше", "діал."],
            source="ulif",
            snapshot=ULIF_SNAP,
            locator="ulif:entry:76793/section:96935 register_labels",
        ),
        A(
            "sense",
            s1,
            "sense_label",
            "пристрій для замикання дверей",
            source="ulif",
            snapshot=ULIF_SNAP,
            locator="ulif:entry:76793/section:96935 citations[0]",
        ),
        A(
            "sense",
            s2,
            "synonyms",
            ["БЛИ́СКАВКА", "ЗАМО́К", "ЗАМО́ЧОК", "ЗМІ́ЙКА"],
            source="ulif",
            snapshot=ULIF_SNAP,
            locator="ulif:entry:76793/section:96934 (synonyms:1) terms",
        ),
        A(
            "sense",
            s3,
            "synonyms",
            ["ЗА́ЩІПКА", "ГАЧО́К", "ГАК", "ЗА́ЩІБКА"],
            source="ulif",
            snapshot=ULIF_SNAP,
            locator="ulif:entry:76793/section:96936 (synonyms:3) terms",
        ),
    ]
    senses = [
        sense(s1, 1, [{"source_id": "ulif", "source_sense_key": "ulif:section:96935"}]),
        sense(s2, 2, [{"source_id": "ulif", "source_sense_key": "ulif:section:96934"}]),
        sense(s3, 3, [{"source_id": "ulif", "source_sense_key": "ulif:section:96936"}]),
    ]
    links = [homograph(CASTLE, cid)]
    identity = {
        "confidence": "high",
        "method": "stress_and_paradigm",
        "decided_by": f"rules:{RULES}",
        "source_keys": [
            {
                "source_id": "vesum",
                "key": "vesum:entry:128972",
                "snapshot_id": VESUM_SNAP,
                "match_note": "xp1 замо́к (пристрій); v_rod замка",
            },
            {
                "source_id": "ulif",
                "key": "ulif:entry:76793",
                "snapshot_id": ULIF_SNAP,
                "match_note": "homonym 3, header not parsed (canonical_headword=''); paradigm родовий замка́",
            },
            {"source_id": "atlas0", "key": "atlas0:heteronym:замок/замо́к", "snapshot_id": ATLAS0_SNAP},
        ],
        "notes": [
            "ULIF homonym 3 has an empty header (one of 12,899 checked rows); the stressed headword is recovered from the paradigm table, so its stress assertion carries extraction_confidence medium."
        ],
    }
    elig = [
        {
            "mode": "stress",
            "eligible": False,
            "rules_version": RULES,
            "reasons": [
                "stress verified (ULIF paradigm + VESUM comment), identity high",
                "cefr A2 mapping_evidenced=false (PULS row 4340 spelling-keyed, two lexeme cards): level band rule unmet",
            ],
        },
        {
            "mode": "meaning",
            "eligible": False,
            "rules_version": RULES,
            "reasons": ["english_gloss unverified (tier-3 producers only)", "no definition_uk assertion"],
        },
    ]
    return card(
        cid,
        "lexeme",
        {
            "spelling": "замок",
            "stress_patterns": ["замо́к"],
            "pos": "noun",
            "paradigm_key": "vesum:entry:128972",
            "source_keys": [
                {"source_id": "vesum", "key": "vesum:entry:128972"},
                {"source_id": "ulif", "key": "ulif:entry:76793"},
            ],
        },
        identity,
        senses,
        links,
        asr,
        elig,
    )


def build_settlement():
    cid = SETTLEMENT
    asr = [
        A(
            "card",
            cid,
            "spelling",
            "Замок",
            source="vesum",
            snapshot=VESUM_SNAP,
            locator="vesum:entry:128971 (noun:inanim:m:v_naz:prop:geo)",
        ),
        A("card", cid, "spelling", "Замок", source="ulif", snapshot=ULIF_SNAP, locator="ulif:entry:76791"),
        A(
            "card",
            cid,
            "stress",
            "За́мок",
            source="ulif",
            snapshot=ULIF_SNAP,
            locator="ulif:entry:76791 canonical_headword",
        ),
        A("card", cid, "pos", "noun", source="vesum", snapshot=VESUM_SNAP, locator="vesum:entry:128971 pos"),
        A(
            "card",
            cid,
            "grammatical_label",
            "іменник чоловічого роду",
            source="ulif",
            snapshot=ULIF_SNAP,
            locator="ulif:entry:76791 grammatical_label",
        ),
        A(
            "sense",
            "ws_g7h8j9k1m2n3",
            "sense_label",
            "(населений пункт в Україні)",
            source="ulif",
            snapshot=ULIF_SNAP,
            locator="ulif:entry:76791 sense_gloss",
        ),
    ]
    senses = [sense("ws_g7h8j9k1m2n3", 1, [{"source_id": "ulif", "source_sense_key": "ulif:entry:76791 sense_gloss"}])]
    identity = {
        "confidence": "high",
        "method": "unique_match",
        "decided_by": f"rules:{RULES}",
        "source_keys": [
            {"source_id": "vesum", "key": "vesum:entry:128971"},
            {"source_id": "ulif", "key": "ulif:entry:76791"},
        ],
        "notes": [
            "Proper name: VESUM :prop:geo tag and ULIF capitalised headword; never merged with the common nouns."
        ],
    }
    return card(
        cid,
        "proper_name",
        {"spelling": "Замок", "stress_patterns": ["За́мок"], "pos": "noun", "paradigm_key": "vesum:entry:128971"},
        identity,
        senses,
        [homograph(CASTLE, cid)],
        asr,
        [
            {
                "mode": "*",
                "eligible": False,
                "rules_version": RULES,
                "reasons": ["proper names are excluded from vocabulary practice modes"],
            }
        ],
    )


def build_kliuch():
    cid = KLIUCH1
    S = [
        "ws_h8j9k1m2n3p4",
        "ws_j9k1m2n3p4q5",
        "ws_k1m2n3p4q5r6",
        "ws_m2n3p4q5r6s7",
        "ws_n3p4q5r6s7t8",
        "ws_p4q5r6s7t8v9",
        "ws_q5r6s7t8v9w1",
    ]
    gloss = "(знаряддя; засіб для розуміння; найважливіший пункт; вимикач у телеграфному апараті; знак на початку нотного рядка; ряд однорідних предметів або живих істот, які рухаються один за одним, утворюючи кут)"
    parts = [
        "знаряддя",
        "засіб для розуміння",
        "найважливіший пункт",
        "вимикач у телеграфному апараті",
        "знак на початку нотного рядка",
        "ряд однорідних предметів або живих істот, які рухаються один за одним, утворюючи кут",
    ]
    asr = [
        A("card", cid, "spelling", "ключ", source="vesum", snapshot=VESUM_SNAP, locator="vesum:entry:168409"),
        A("card", cid, "spelling", "ключ", source="ulif", snapshot=ULIF_SNAP, locator="ulif:entry:3"),
        A(
            "card",
            cid,
            "stress",
            "ключ",
            source="ulif",
            snapshot=ULIF_SNAP,
            locator="ulif:entry:3 canonical_headword (monosyllable, unmarked)",
        ),
        A(
            "card",
            cid,
            "stress",
            "клю́ч",
            value_norm="ключ",
            source="kaikki",
            snapshot=ATLAS0_SNAP,
            locator="atlas0:enrichment:ключ/stress",
            mapping={
                "confidence": "medium",
                "basis": "spelling",
                "ambiguous": True,
                "note": "spelling-keyed; ULIF homonyms 1 and 2 share the paradigm, stress decides nothing here",
            },
        ),
        A("card", cid, "pos", "noun", source="vesum", snapshot=VESUM_SNAP, locator="vesum:entry:168409 pos"),
        A(
            "card",
            cid,
            "pos",
            "іменник чоловічого роду",
            value_norm="noun",
            source="ulif",
            snapshot=ULIF_SNAP,
            locator="ulif:entry:3 grammatical_label",
        ),
        A(
            "card",
            cid,
            "cefr",
            "A2",
            source="puls",
            snapshot=ATLAS0_SNAP,
            locator="sources.puls_cefr:id:3768 (ключ, іменник)",
            mapping=PULS_SPELLING,
        ),
        A(
            "card",
            cid,
            "english_gloss",
            "key",
            source="kaikki",
            snapshot=ATLAS0_SNAP,
            locator="atlas0:enrichment:ключ/meaning definitions[0]",
            mapping={"confidence": "medium", "basis": "spelling", "ambiguous": True, "note": "spelling-keyed"},
        ),
        A(
            "sense",
            S[0],
            "definition_uk",
            "Знаряддя для замикання та відмикання замка, засува та ін.",
            source="vts",
            snapshot=ATLAS0_SNAP,
            locator="atlas0:enrichment:ключ/definition_cards vts 'I' 1》",
        ),
        A(
            "sense",
            S[1],
            "definition_uk",
            "Інструмент для загвинчування або відгвинчування гайок, болтів і т. ін.",
            source="vts",
            snapshot=ATLAS0_SNAP,
            locator="atlas0:enrichment:ключ/definition_cards vts 'I' 2》",
        ),
        A(
            "sense",
            S[1],
            "gloss_en",
            "wrench, spanner, screw wrench",
            source="kaikki",
            snapshot=ATLAS0_SNAP,
            locator="atlas0:enrichment:ключ/meaning definitions[1]",
            mapping={
                "confidence": "medium",
                "basis": "curator",
                "note": "aligned to ВТС I/2 by curator (no overlay entry yet)",
            },
        ),
        A(
            "sense",
            S[6],
            "synonyms",
            ["ЛАНЦЮГО́М", "НИ́ЗКОЮ", "ЛАНЦЮЖКО́М", "ВЕРВЕ́ЧКОЮ", "ВА́ЛКОЮ", "ЦЕ́ПОМ", "КЛЮЧЕ́М", "КЛЮЧА́МИ"],
            source="ulif",
            snapshot=ULIF_SNAP,
            locator="ulif:entry:3/section:124670 (synonyms:1) terms",
        ),
    ]
    for i, p in enumerate(parts):
        asr.append(
            A(
                "sense",
                S[i if i == 0 else i + 1],
                "sense_label",
                p,
                source="ulif",
                snapshot=ULIF_SNAP,
                locator=f"ulif:entry:3 sense_gloss item {i + 1} of {gloss!r}"[:160],
                xconf="medium",
                producer={"kind": "source_extract", "name": "ulif sense_gloss ';' splitter", "version": "v1"},
            )
        )
    senses = [
        sense(
            S[0],
            1,
            [
                {"source_id": "vts", "source_sense_key": "vts:ключ#I/1"},
                {"source_id": "ulif", "source_sense_key": "ulif:entry:3 sense_gloss[1]"},
            ],
        ),
        sense(
            S[1],
            2,
            [
                {"source_id": "vts", "source_sense_key": "vts:ключ#I/2"},
                {"source_id": "kaikki", "source_sense_key": "kaikki:ключ definitions[1]", "mapped_by": "curator"},
            ],
        ),
        sense(S[2], 3, [{"source_id": "ulif", "source_sense_key": "ulif:entry:3 sense_gloss[2]"}]),
        sense(S[3], 4, [{"source_id": "ulif", "source_sense_key": "ulif:entry:3 sense_gloss[3]"}]),
        sense(S[4], 5, [{"source_id": "ulif", "source_sense_key": "ulif:entry:3 sense_gloss[4]"}]),
        sense(S[5], 6, [{"source_id": "ulif", "source_sense_key": "ulif:entry:3 sense_gloss[5]"}]),
        sense(
            S[6],
            7,
            [
                {"source_id": "ulif", "source_sense_key": "ulif:entry:3 sense_gloss[6]"},
                {"source_id": "ulif", "source_sense_key": "ulif:section:124670"},
            ],
        ),
    ]
    links = [homograph(cid, KLIUCH2)]
    identity = {
        "confidence": "medium",
        "method": "overlay",
        "decided_by": "rules: dictionary homonym division (ULIF 1/2, ВТС I/II) with identical paradigm — see identity.md §5 case D",
        "source_keys": [
            {
                "source_id": "vesum",
                "key": "vesum:entry:168409",
                "match_note": "one VESUM entry for both ULIF homonyms; mapped to both, paradigm shared",
            },
            {"source_id": "ulif", "key": "ulif:entry:3", "match_note": "homonym 1 (six sub-senses in sense_gloss)"},
            {"source_id": "vts", "key": "vts:ключ#I"},
            {"source_id": "atlas0", "key": "atlas0:slug:ключ"},
        ],
        "notes": [
            "ULIF homonym 2 ключ (джерело) is a separate card (wc_m3y6w9dc2sxr); the paradigm table is byte-identical (2,184 chars) so only the dictionaries' homonym division separates them."
        ],
    }
    elig = [
        {
            "mode": "meaning",
            "eligible": False,
            "rules_version": RULES,
            "reasons": [
                "identity medium (dictionary-division split, paradigm shared with wc_m3y6w9dc2sxr): meaning practice needs "
                "reviewed high identity for this card and sense (Q7 decision, schema.md §9.5)",
                "cefr A2 mapping_evidenced=false (PULS row 3768 spelling-keyed, two cards)",
                "sense s1 definition_uk single-source ВТС",
            ],
            "sense_id": S[0],
        },
        {
            "mode": "synonyms",
            "eligible": False,
            "rules_version": RULES,
            "reasons": ["only ULIF group is the 'flock' sense (s7); no CEFR for that sense; register unknown"],
            "sense_id": S[6],
        },
    ]
    return card(
        cid,
        "lexeme",
        {"spelling": "ключ", "stress_patterns": ["ключ"], "pos": "noun", "paradigm_key": "vesum:entry:168409"},
        identity,
        senses,
        links,
        asr,
        elig,
    )


def build_idiom():
    cid = IDIOM
    s1 = "ws_r6s7t8v9w1x2"
    defn = "Придумувати нездійсненні, відірвані від життя плани, мріяти про щось недосяжне."
    cit = (
        "— Наташко, все буде добре… Ти одужаєш. Я вірю в це.— Платоне, не треба будувати повітряні замки (М. Зарудний)."
    )
    asr = [
        A(
            "card",
            cid,
            "mwe_form",
            "будува́́ти пові́́тря́́ні за́́мки .",
            value_norm="будувати повітряні замки",
            source="ulif",
            snapshot=ULIF_SNAP,
            locator="ulif:entry:76792/section:96932 (phraseology:1) terms[0].text",
            xconf="low",
            producer={
                "kind": "source_extract",
                "name": "ulif phraseology terms (doubled U+0301 in source markup)",
                "version": "v1",
            },
        ),
        A(
            "card",
            cid,
            "mwe_form",
            "будува́́ти пові́́тря́́ні за́́мки .",
            value_norm="будувати повітряні замки",
            source="ulif",
            snapshot=ULIF_SNAP,
            locator="ulif:entry:170125/section:218523 (повітряний, phraseology:1) terms[0].text",
            xconf="low",
        ),
        A(
            "card",
            cid,
            "mwe_form",
            "будувати повітряні замки",
            source="frazeolohichnyi",
            snapshot=SOURCES_SNAP,
            locator="sources.frazeolohichnyi:id:568",
        ),
        A(
            "card",
            cid,
            "mwe_form",
            "будувати повітряні замки",
            source="slovnyk_me",
            snapshot=ATLAS0_SNAP,
            locator="atlas0:enrichment:замок/idioms items[0].phrase (slovnyk.me: Фразеологічний словник української мови)",
        ),
        A(
            "card",
            cid,
            "pos",
            "phrase",
            source="ulif",
            snapshot=ULIF_SNAP,
            locator="ulif:entry:76792/section:96932 kind=phraseology",
            xconf="medium",
        ),
        A(
            "sense",
            s1,
            "definition_uk",
            defn,
            source="ulif",
            snapshot=ULIF_SNAP,
            locator="ulif:entry:76792/section:96932 text",
        ),
        A(
            "sense",
            s1,
            "definition_uk",
            defn,
            source="frazeolohichnyi",
            snapshot=SOURCES_SNAP,
            locator="sources.frazeolohichnyi:id:568 definition",
        ),
        A(
            "sense",
            s1,
            "examples",
            [{"text": cit, "attribution": "М. Зарудний"}],
            value_norm=cit,
            source="ulif",
            snapshot=ULIF_SNAP,
            locator="ulif:entry:76792/section:96932 text + citations[0]",
        ),
        A(
            "sense",
            s1,
            "register",
            [],
            value_norm="",
            source="ulif",
            snapshot=ULIF_SNAP,
            locator="ulif:entry:76792/section:96932 register_labels",
        ),
    ]
    senses = [
        sense(
            s1,
            1,
            [
                {"source_id": "ulif", "source_sense_key": "ulif:section:96932"},
                {"source_id": "frazeolohichnyi", "source_sense_key": "frazeolohichnyi:568"},
            ],
        )
    ]
    links = [
        {
            **link(
                "component_of",
                [{"id": cid, "role": "whole"}, {"id": CASTLE, "role": "anchor"}],
                [asr[0]["assertion_id"]],
            ),
            "note": "за́мки ↔ ULIF anchor uid=47336 ЗА́МОК (castle), read from the section HTML",
        },
        {
            **link(
                "component_of",
                [{"id": cid, "role": "whole"}, {"id": POVITRIANYI, "role": "component"}],
                [asr[1]["assertion_id"]],
            ),
            "note": "ULIF anchor uid=115867",
        },
        {
            **link(
                "component_of",
                [{"id": cid, "role": "whole"}, {"id": BUDUVATY, "role": "component"}],
                [asr[0]["assertion_id"]],
            ),
            "note": "ULIF anchor uid=10839",
        },
    ]
    identity = {
        "confidence": "high",
        "method": "unique_match",
        "decided_by": f"rules:{RULES}",
        "source_keys": [
            {"source_id": "ulif", "key": "ulif:entry:76792/section:96932"},
            {"source_id": "ulif", "key": "ulif:entry:170125/section:218523"},
            {"source_id": "frazeolohichnyi", "key": "frazeolohichnyi:568"},
        ],
        "notes": [
            "One MWE card although the idiom is listed under two ULIF headwords; the normalised form is the key.",
            "ULIF phraseology, sources.frazeolohichnyi and slovnyk.me carry the same dictionary text (identical definition and citation), so they form one independence group: the card is single-source, not verified.",
        ],
    }
    elig = [
        {
            "mode": "idioms",
            "eligible": False,
            "rules_version": RULES,
            "reasons": [
                "no cefr assertion for the MWE",
                "definition_uk single-source",
                "idiom modes are B2–C1 (#8984/#8985) and need a sampled language-lane review",
            ],
        },
    ]
    return card(
        cid,
        "mwe",
        {
            "spelling": "будувати повітряні замки",
            "pos": "phrase",
            "mwe_key": "ulif:entry:76792/section:96932|будувати повітряні замки",
        },
        identity,
        senses,
        links,
        asr,
        elig,
    )


def build_bronia_armour():
    cid = BRONIA_ARMOUR
    s1 = "ws_s7t8v9w1x2y3"
    asr = [
        A(
            "card",
            cid,
            "spelling",
            "броня",
            source="vesum",
            snapshot=VESUM_SNAP,
            locator="vesum:entry:30497",
            mapping={
                "confidence": "medium",
                "note": "VESUM has one entry for both ULIF homonyms (comment 'xv2 броня́; бро́ня')",
            },
        ),
        A("card", cid, "spelling", "броня", source="ulif", snapshot=ULIF_SNAP, locator="ulif:entry:29075"),
        A(
            "card",
            cid,
            "stress",
            "броня́",
            source="ulif",
            snapshot=ULIF_SNAP,
            locator="ulif:entry:29075/section:28470 rows[1][1]",
            xconf="medium",
            producer={"kind": "source_extract", "name": "ulif paradigm-row headword recovery", "version": "v1"},
        ),
        A(
            "card",
            cid,
            "stress",
            "броня́",
            source="kaikki",
            snapshot=ATLAS0_SNAP,
            locator="atlas0:enrichment:броня/stress (kaikki/Wiktionary)",
            mapping={
                "confidence": "medium",
                "basis": "stress",
                "note": "spelling-keyed; броня́ matches this homonym only",
            },
        ),
        A(
            "card",
            cid,
            "stress",
            "xv2 броня́; бро́ня",
            value_norm="броня́|бро́ня",
            source="vesum",
            snapshot=VESUM_SNAP,
            locator="vesum:entry:30497 source_comment",
            xconf="medium",
            mapping={
                "confidence": "low",
                "note": "unsplit: VESUM declares both stresses on one lemma; retained as evidence, does not vote on a split card",
            },
        ),
        A("card", cid, "pos", "noun", source="vesum", snapshot=VESUM_SNAP, locator="vesum:entry:30497 pos"),
        A(
            "card",
            cid,
            "gender",
            "f",
            source="vesum",
            snapshot=VESUM_SNAP,
            locator="vesum:entry:30497 tags noun:inanim:f:v_naz",
        ),
        A(
            "card",
            cid,
            "frequency",
            {"per_million": 0.55, "rank": 2792, "of": 4161},
            value_norm="grac:0.55/million;rank 2792/4161",
            source="grac",
            snapshot=ATLAS0_SNAP,
            locator="atlas0:enrichment:броня/cefr text 'GRAC 0.55/million, rank 2792/4161'",
            xv="atlas0-migration",
            xconf="medium",
            mapping={
                "confidence": "medium",
                "basis": "spelling",
                "ambiguous": True,
                "note": "spelling-keyed corpus frequency; covers both броня cards",
            },
        ),
        A(
            "card",
            cid,
            "cefr",
            "B2",
            source="grac_estimate",
            snapshot=ATLAS0_SNAP,
            locator="atlas0:enrichment:броня/cefr 'estimated (GRAC frequency)' 0.55/million rank 2792/4161",
            producer={
                "kind": "estimator",
                "name": "GRAC frequency → CEFR estimate",
                "version": "atlas0",
                "derived_id": ESTIMATE_DERIVATION_ID,
            },
            mapping={
                "confidence": "medium",
                "basis": "spelling",
                "ambiguous": True,
                "note": "spelling-keyed frequency",
            },
        ),
        A(
            "sense",
            s1,
            "definition_uk",
            "металевий одяг для захисту тулуба воїна",
            source="wiktionary",
            snapshot=SOURCES_SNAP,
            locator="sources.wiktionary:id:11318 definitions[0]",
            mapping={
                "confidence": "medium",
                "note": "spelling-keyed list; item mapped to the armour homonym by curator",
            },
        ),
    ]
    senses = [
        sense(
            s1,
            1,
            [
                {
                    "source_id": "wiktionary",
                    "source_sense_key": "wiktionary:11318/definitions[0]",
                    "mapped_by": "curator",
                }
            ],
        )
    ]
    links = [homograph(cid, BRONIA_RESERV)]
    identity = {
        "confidence": "medium",
        "method": "stress_only",
        "decided_by": f"rules:{RULES}",
        "source_keys": [
            {
                "source_id": "ulif",
                "key": "ulif:entry:29075",
                "match_note": "homonym 2, header not parsed; paradigm броня́",
            },
            {
                "source_id": "vesum",
                "key": "vesum:entry:30497",
                "match_note": "shared with wc_w8g1k4qt7zhm; VESUM did not split",
            },
            {"source_id": "atlas0", "key": "atlas0:slug:броня"},
        ],
        "notes": [
            "Sources disagree on identity: VESUM one lemma with two stresses, ULIF two homonyms with distinct senses (бро́ня закріплення; документ про закріплення / броня́). Rules follow the finer division when stress and sense both differ; confidence stays medium until the language-lane read (Gemini, 2026-09-28, two-card reading confirmed) is recorded as an overlay identity entry."
        ],
    }
    elig = [
        {
            "mode": "stress",
            "eligible": False,
            "rules_version": RULES,
            "reasons": ["identity medium", "cefr unverified (estimate only)"],
        }
    ]
    return card(
        cid,
        "lexeme",
        {"spelling": "броня", "stress_patterns": ["броня́"], "pos": "noun", "paradigm_key": "vesum:entry:30497"},
        identity,
        senses,
        links,
        asr,
        elig,
    )


def build_bronia_reserv():
    cid = BRONIA_RESERV
    s1 = "ws_t8v9w1x2y3z4"
    asr = [
        A("card", cid, "spelling", "броня", source="ulif", snapshot=ULIF_SNAP, locator="ulif:entry:29074"),
        A(
            "card",
            cid,
            "stress",
            "бро́ня",
            source="ulif",
            snapshot=ULIF_SNAP,
            locator="ulif:entry:29074 canonical_headword",
        ),
        A(
            "card",
            cid,
            "stress",
            "xv2 броня́; бро́ня",
            value_norm="броня́|бро́ня",
            source="vesum",
            snapshot=VESUM_SNAP,
            locator="vesum:entry:30497 source_comment",
            xconf="medium",
            mapping={"confidence": "low", "note": "unsplit VESUM lemma; evidence only"},
        ),
        A(
            "card",
            cid,
            "grammatical_label",
            "іменник жіночого роду",
            source="ulif",
            snapshot=ULIF_SNAP,
            locator="ulif:entry:29074 grammatical_label",
        ),
        A(
            "sense",
            s1,
            "sense_label",
            "(закріплення; документ про закріплення)",
            source="ulif",
            snapshot=ULIF_SNAP,
            locator="ulif:entry:29074 sense_gloss",
        ),
        A(
            "sense",
            s1,
            "definition_uk",
            "закріплення когось або чогось за ким-, чим-небудь; документ на це закріплення",
            source="wiktionary",
            snapshot=SOURCES_SNAP,
            locator="sources.wiktionary:id:11318 definitions[4]",
            mapping={"confidence": "medium", "note": "mapped by curator to the ULIF sense_gloss"},
        ),
    ]
    senses = [
        sense(
            s1,
            1,
            [
                {"source_id": "ulif", "source_sense_key": "ulif:entry:29074 sense_gloss"},
                {
                    "source_id": "wiktionary",
                    "source_sense_key": "wiktionary:11318/definitions[4]",
                    "mapped_by": "curator",
                },
            ],
        )
    ]
    links = [homograph(BRONIA_ARMOUR, cid)]
    identity = {
        "confidence": "medium",
        "method": "stress_only",
        "decided_by": f"rules:{RULES}",
        "source_keys": [
            {"source_id": "ulif", "key": "ulif:entry:29074", "match_note": "homonym 1 бро́ня (закріплення)"},
            {"source_id": "vesum", "key": "vesum:entry:30497", "match_note": "shared, unsplit"},
        ],
    }
    return card(
        cid,
        "lexeme",
        {"spelling": "броня", "stress_patterns": ["бро́ня"], "pos": "noun", "paradigm_key": "vesum:entry:30497"},
        identity,
        senses,
        links,
        asr,
        [
            {
                "mode": "stress",
                "eligible": False,
                "rules_version": RULES,
                "reasons": ["stress single-source", "identity medium", "no cefr"],
            }
        ],
    )


def build_vriady():
    cid = VRIADY
    asr = [
        A("card", cid, "spelling", "вряди-годи", source="vesum", snapshot=VESUM_SNAP, locator="vesum:entry:67854"),
        A("card", cid, "spelling", "вряди-годи", source="ulif", snapshot=ULIF_SNAP, locator="ulif:entry:47595"),
        A(
            "card",
            cid,
            "stress",
            "вряди́-годи́",
            source="ulif",
            snapshot=ULIF_SNAP,
            locator="ulif:entry:47595 canonical_headword",
        ),
        A(
            "card",
            cid,
            "stress",
            "вряди́-го́ди",
            source="ukrainian_word_stress",
            snapshot=ATLAS0_SNAP,
            locator="atlas0:enrichment:вряди-годи/stress (ukrainian-word-stress)",
        ),
        A("card", cid, "pos", "adv", source="vesum", snapshot=VESUM_SNAP, locator="vesum:entry:67854 pos"),
        A(
            "card",
            cid,
            "pos",
            "прислівник",
            value_norm="adv",
            source="ulif",
            snapshot=ULIF_SNAP,
            locator="ulif:entry:47595 grammatical_label",
        ),
    ]
    identity = {
        "confidence": "high",
        "method": "unique_match",
        "decided_by": f"rules:{RULES}",
        "source_keys": [
            {"source_id": "vesum", "key": "vesum:entry:67854"},
            {"source_id": "ulif", "key": "ulif:entry:47595"},
            {"source_id": "atlas0", "key": "atlas0:slug:вряди-годи"},
        ],
        "notes": [
            "One lemma on every side (VESUM 1 entry, ULIF 1 homonym): the stress disagreement is a real value conflict, not an identity artefact."
        ],
    }
    return card(
        cid,
        "lexeme",
        {"spelling": "вряди-годи", "pos": "adv", "paradigm_key": "vesum:entry:67854"},
        identity,
        [],
        [],
        asr,
        [
            {
                "mode": "stress",
                "eligible": False,
                "rules_version": RULES,
                "reasons": ["stress in conflict; excluded until an overlay `resolve` or a language-lane review"],
            }
        ],
    )


def build_aspect_pair():
    """вибігати (ULIF homonym 2, imperfective) ↔ вибігти (perfective); pairing evidence from the ВТС card."""
    VTS_PAIR = "II вибіг`ати - а ю, - а єш, недок. , в и бігти, -іжу, -іжиш, док. 1》 Бігом залишати, покидати як"
    cards = []
    for cid, role, ul, ve, hw, label, tag in (
        (
            VYBIHATY,
            "imperfective",
            "ulif:entry:34097",
            "vesum:entry:40937",
            "вибіга́ти",
            "дієслово недоконаного виду",
            "verb:imperf:inf",
        ),
        (
            VYBIHTY,
            "perfective",
            "ulif:entry:34099",
            "vesum:entry:40942",
            "ви́бігти",
            "дієслово доконаного виду",
            "verb:perf:inf",
        ),
    ):
        sp = hw.replace("\u0301", "")
        aspect_norm = "imperf" if role == "imperfective" else "perf"
        asr = [
            A("card", cid, "spelling", sp, source="vesum", snapshot=VESUM_SNAP, locator=ve),
            A("card", cid, "spelling", sp, source="ulif", snapshot=ULIF_SNAP, locator=ul),
            A("card", cid, "stress", hw, source="ulif", snapshot=ULIF_SNAP, locator=f"{ul} canonical_headword"),
            A("card", cid, "pos", "verb", source="vesum", snapshot=VESUM_SNAP, locator=f"{ve} pos"),
            A(
                "card",
                cid,
                "aspect",
                tag,
                value_norm=aspect_norm,
                source="vesum",
                snapshot=VESUM_SNAP,
                locator=f"{ve} tags",
            ),
            A(
                "card",
                cid,
                "aspect",
                label,
                value_norm=aspect_norm,
                source="ulif",
                snapshot=ULIF_SNAP,
                locator=f"{ul} grammatical_label",
            ),
        ]
        if cid == VYBIHATY:
            asr.append(
                A(
                    "card",
                    cid,
                    "stress",
                    ":xp1 вибіга́ти    # rv_oru",
                    value_norm="вибіга́ти",
                    source="vesum",
                    snapshot=VESUM_SNAP,
                    locator="vesum:entry:40937 source_comment",
                    xconf="medium",
                )
            )
            asr.append(
                A(
                    "card",
                    cid,
                    "cefr",
                    "B2",
                    source="grac_estimate",
                    snapshot=ATLAS0_SNAP,
                    locator="atlas0:enrichment:вибігати/cefr 'estimated (GRAC frequency)' 0.23/million rank 3290/4161",
                    producer={"kind": "estimator", "name": "GRAC frequency → CEFR estimate", "version": "atlas0"},
                    mapping={
                        "confidence": "medium",
                        "basis": "spelling",
                        "ambiguous": True,
                        "note": "spelling-keyed; covers both вибігати homonyms",
                    },
                )
            )
        endpoints = [{"id": VYBIHATY, "role": "imperfective"}, {"id": VYBIHTY, "role": "perfective"}]
        link_id = link("aspect_pair", endpoints, [])["link_id"]  # id depends on type + canonical endpoints only
        link_asr = A(
            "link",
            link_id,
            "aspect_pair",
            VTS_PAIR,
            value_norm="вибігати(недок.)↔вибігти(док.)",
            source="vts",
            snapshot=ATLAS0_SNAP,
            locator="atlas0:enrichment:вибігати/definition_cards vts 'II вибіг`ати' header (недок. … док.)",
            xconf="medium",
            producer={"kind": "source_extract", "name": "ВТС header 'недок./док.' pair reader", "version": "example"},
        )
        asr.append(link_asr)
        links = [link("aspect_pair", endpoints, [link_asr["assertion_id"]])]  # identical record on both cards
        identity = {
            "confidence": "high",
            "method": "stress_and_paradigm" if cid == VYBIHATY else "unique_match",
            "decided_by": f"rules:{RULES}",
            "source_keys": [{"source_id": "vesum", "key": ve}, {"source_id": "ulif", "key": ul}],
            "notes": (
                [
                    "VESUM numbers the homonyms xp1 = вибіга́ти (imperf), xp2 = ви́бігати (perf); ULIF numbers them 1 = ви́бігати (perf), 2 = вибіга́ти (imperf). Matched by stress + aspect, not by number."
                ]
                if cid == VYBIHATY
                else []
            ),
        }
        cards.append(
            card(
                cid,
                "lexeme",
                {"spelling": sp, "stress_patterns": [hw], "pos": "verb", "paradigm_key": ve},
                identity,
                [],
                links,
                asr,
                [
                    {
                        "mode": "forms",
                        "eligible": False,
                        "rules_version": RULES,
                        "reasons": ["aspect verified (VESUM + ULIF)", "cefr unverified (estimate) or missing"],
                    }
                ],
            )
        )
    return cards


def build_legacy_split():
    """The pre-card atlas0 article 'замок' (one spelling, gloss 'castle / lock'): state `split`, two successors.
    A split is one-to-many and is never a merge redirect (identity.md §7). Its assertions were re-mapped to the
    successors by the matching rules; the card keeps its id, its key and the split event, nothing else."""
    cid = LEGACY_ZAMOK
    identity = {
        "confidence": "high",
        "method": "overlay",
        "decided_by": "overlay:ovl-2026-09-28-0001",
        "source_keys": [
            {
                "source_id": "atlas0",
                "key": "atlas0:slug:замок",
                "snapshot_id": ATLAS0_SNAP,
                "match_note": "merged article castle / lock",
            },
        ],
        "notes": [
            "Split into wc_7k3m9q2xw4pd (за́мок castle) and wc_c2v8n5rt6yhq (замо́к lock); learner progress per identity.md §7.3."
        ],
    }
    return card(
        cid,
        "lexeme",
        {
            "spelling": "замок",
            "stress_patterns": ["за́мок"],
            "pos": "noun",
            "source_keys": [{"source_id": "atlas0", "key": "atlas0:slug:замок"}],
        },
        identity,
        [],
        [],
        [],
        [
            {
                "mode": "*",
                "eligible": False,
                "rules_version": RULES,
                "reasons": ["card is split; resolve split_into first"],
            }
        ],
        state="split",
        split_into=[CASTLE, LOCK],
        overlay=[{k: SPLIT_OVERLAY[k] for k in ("overlay_id", "kind", "author", "lane", "date", "evidence")}],
    )


# ---------------------------------------------------------------- companion instances (schema.md §§5, 11, 12, 13)
def build_registry(cards: dict) -> dict:
    """Identity registry: the frozen input I. Assembly proves consistency with it (every card and sense id it
    emitted is allocated there, every allocated state matches) and never mutates it."""
    for c in cards.values():
        e = next(e for e in REGISTRY["entries"] if e["card_id"] == c["card_id"])
        assert e["state"] == c["state"] and e["key_at_creation"] == c["key_at_creation"], c["card_id"]
        assert [s["sense_id"] for s in e["senses"]] == [s["sense_id"] for s in c["senses"]], c["card_id"]
    return REGISTRY


def build_overlay() -> dict:
    return OVERLAY


def build_suppressions() -> dict:
    return SUPPRESSIONS


def _derivation(kind, generator, version, configuration, inputs, output, *, status="active", **extra) -> dict:
    d = {
        "derived_id": derivation_id(
            generator, version, RULES, configuration["sha256"], inputs, output["kind"], output["key"]
        ),
        "kind": kind,
        "generator": generator,
        "generator_version": version,
        "rules_version": RULES,
        "configuration": configuration,
        "build_id": BUILD["build_id"],
        "inputs": inputs,
        "output": output,
        "status": status,
    }
    d.update(extra)
    return d


def build_derivations(cards: dict) -> dict:
    """Dependency records (schema.md §11) forming one traversable chain:
      GRAC frequency assertion  ->  wd (estimator)  ->  generated cefr assertion  ->  wd (atlas page), wd (exercise draft)
    The generated assertion's `producer.derived_id` points back at the estimator record and the estimator
    record's `output.key` is the generated assertion id, so `transitive_invalidation()` can walk both hops."""
    armour = cards["bronia-armour"]
    by_id = {a["assertion_id"]: a for a in armour["assertions"]}
    cefr = by_id[BRONIA_CEFR_AID]
    assert cefr["producer"]["derived_id"] == ESTIMATE_DERIVATION_ID
    estimate = _derivation(
        "generated_assertion",
        "grac_frequency_cefr_estimator",
        "atlas0",
        ESTIMATE_CONFIGURATION,
        ESTIMATE_INPUTS,
        {"kind": "assertion", "key": BRONIA_CEFR_AID, "content_sha256": sha256_of(cefr)},
    )
    assert estimate["derived_id"] == ESTIMATE_DERIVATION_ID
    page_config = {
        "ref": "export_runtime_shards.py settings (example)",
        "sha256": sha256_of({"shard": "lexicon", "v": 1}),
    }
    active_ids = sorted(a["assertion_id"] for a in armour["assertions"] if a["status"] == "active")
    page = _derivation(
        "atlas_page",
        "export_runtime_shards",
        "example",
        page_config,
        {
            "assertion_ids": active_ids,
            "card_ids": [armour["card_id"]],
            "card_versions": {armour["card_id"]: armour["build"]["card_version"]},
        },
        {
            "kind": "atlas_page",
            "key": f"/lexicon/{armour['card_id']}/",
            "content_sha256": sha256_of(public_projection(armour)),
        },
        note="pages are produced for every card, eligible or not (thin cards are never hidden)",
    )
    stress_ids = armour["fields"]["stress"]["values"][0]["assertion_ids"]
    item_config = {"ref": "stress_item generator settings (example)", "sha256": sha256_of({"choices": 2, "v": 1})}
    draft_content = {
        "card_id": armour["card_id"],
        "field": "stress",
        "answer": stress_ids[0],
        "level_band": BRONIA_CEFR_AID,
    }
    exercise = _derivation(
        "exercise",
        "stress_item",
        "example",
        item_config,
        {
            "assertion_ids": sorted([*stress_ids, BRONIA_CEFR_AID]),
            "card_ids": [armour["card_id"]],
            "card_versions": {armour["card_id"]: armour["build"]["card_version"]},
        },
        {
            "kind": "exercise",
            "key": f"practice/stress/{armour['card_id']}/1",
            "content_sha256": sha256_of(draft_content),
        },
        status="draft",
        unpublished_reason="card ineligible in mode stress (identity medium; cefr is an unevidenced estimate): "
        "the generator records what it would publish, nothing is published",
    )
    return {"schema_version": "1", "entries": [estimate, page, exercise]}


def transitive_invalidation(
    seed_assertion_ids: set[str], derivations: list[dict], suppression_id: str
) -> tuple[set, dict]:
    """Walk schema.md §12.2: a suppressed assertion invalidates every derivation that read it; a derivation
    whose output is itself an assertion suppresses that assertion, which invalidates its consumers in turn.
    Returns (all suppressed assertion ids, {derived_id: invalidated_by})."""
    suppressed = set(seed_assertion_ids)
    invalidated: dict[str, str] = {}
    changed = True
    while changed:
        changed = False
        for d in derivations:
            if d["derived_id"] in invalidated or not (set(d["inputs"]["assertion_ids"]) & suppressed):
                continue
            invalidated[d["derived_id"]] = suppression_id
            changed = True
            if d["output"]["kind"] == "assertion" and d["output"]["key"] not in suppressed:
                suppressed.add(d["output"]["key"])
    return suppressed, invalidated


def build_all() -> tuple[dict, dict]:
    cards = {
        "zamok-castle": build_castle(),
        "zamok-lock": build_lock(),
        "zamok-settlement": build_settlement(),
        "zamok-legacy-split": build_legacy_split(),
        "kliuch-1": build_kliuch(),
        "idiom-buduvaty-povitriani-zamky": build_idiom(),
        "bronia-armour": build_bronia_armour(),
        "bronia-reservation": build_bronia_reserv(),
        "vriady-hody-conflict": build_vriady(),
    }
    for i, c in enumerate(build_aspect_pair()):
        cards[["vybihaty-imperf", "vybihty-perf"][i]] = c
    companions = {
        "identity-registry": build_registry(cards),
        "overlay": build_overlay(),
        "suppression-selectors": build_suppressions(),
        "derivations": build_derivations(cards),
    }
    return cards, companions


def main() -> None:
    cards, companions = build_all()
    for name, c in cards.items():
        (HERE / f"{name}.json").write_text(json.dumps(c, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (HERE / "companion").mkdir(exist_ok=True)
    for name, c in companions.items():
        (HERE / "companion" / f"{name}.json").write_text(
            json.dumps(c, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print(f"wrote {len(cards)} cards and {len(companions)} companion files to {HERE}")


if __name__ == "__main__":
    main()
