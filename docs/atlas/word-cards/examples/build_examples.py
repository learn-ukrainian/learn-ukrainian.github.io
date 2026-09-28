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

Run:  /home/ops/learn-ukrainian/.venv/bin/python docs/atlas/word-cards/examples/build_examples.py
"""

from __future__ import annotations

import hashlib
import json
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
    "course_authored": ("G-PROJECT", 3),
    "grac_estimate": ("G-PROJECT", 3),
    "atlas_curated": ("G-PROJECT", 3),
}

# Build inputs are content hashes, not row counts (schema.md §13). Measured 2026-09-28, read-only:
#   sha256 over the sorted content_sha256 of the 262,788 checked ULIF rows; sha256 over the canonical
#   JSON of the 5,939 puls_cefr rows; sha256 of data/atlas.db (the frozen atlas0 snapshot file);
#   vesum_build_metadata.canonical_jsonl_sha256; sha256 of the register file.
BUILD = {
    "build_id": "example-2026-09-28-r2",
    "rules_version": RULES,
    "inputs": {
        "S": {
            "sources.ulif_dictua_entries": "sha256(sorted content_sha256, homonym_checked=1, 262788 rows)=fe9f52cb261736443f511a85b52e8ee6fe05b51165c56384cfa969b411429b98",
            "sources.puls_cefr": "sha256(canonical rows, 5939)=c2586b0bd4830bac7fc08d7bd59e98460d6f5acd468a5f323308668134780d55",
            "atlas0": "atlas.db manifest 0.1 generated_at 2026-09-11T10:12:36+00:00; file sha256=fcf802bda35dd4cd99e95317da0f4a1fa9315024befc83e73673c106278ebfca (retained read-only for migrated assertions)",
        },
        "V": {"vesum.canonical_jsonl_sha256": "53923150073b4fc7bee419fe7b071acbe17b6a9aba76cfb2d0336c95f5188680"},
        "I": {
            "identity_registry": "examples/companion/identity-registry.json registry_version 1 (example allocations)"
        },
        "O": {"overlay": "examples/companion/overlay.json (one split entry; examples otherwise overlay-free)"},
        "R": {
            "rules": RULES,
            "normaliser": NORMALISER,
            "register": f"docs/sources/permissions-register.yaml schema_version {REGISTER_VERSION} sha256={REGISTER_SHA256}",
        },
    },
}

# Durable source-record keys (schema.md §12.1): content-derived, never a local row id, so a suppression
# selector or a reharvest correspondence survives renumbering. ULIF: query#stressed headword (canonical
# or paradigm-recovered)#grammatical_label, all as stored on 2026-09-28. VESUM: lemma/pos/lemma-form tags.
RECORD_KEYS = {
    "ulif:entry:76791": "ulif:record:замок#За́мок#іменник чоловічого роду",
    "ulif:entry:76792": "ulif:record:замок#за́мок#іменник чоловічого роду",
    "ulif:entry:76793": "ulif:record:замок#замо́к#",
    "ulif:entry:3": "ulif:record:ключ#ключ#іменник чоловічого роду",
    "ulif:entry:29074": "ulif:record:броня#бро́ня#іменник жіночого роду",
    "ulif:entry:29075": "ulif:record:броня#броня́#",
    "ulif:entry:47595": "ulif:record:вряди-годи#вряди́-годи́#прислівник",
    "ulif:entry:34097": "ulif:record:вибігати#вибіга́ти#дієслово недоконаного виду",
    "ulif:entry:34099": "ulif:record:вибігти#ви́бігти#дієслово доконаного виду",
    "ulif:entry:170125": "ulif:record:повітряний##",
    "vesum:entry:128971": "vesum:record:Замок/noun/noun:inanim:m:v_naz:prop:geo",
    "vesum:entry:128972": "vesum:record:замок/noun/noun:inanim:m:v_naz:xp1",
    "vesum:entry:128973": "vesum:record:замок/noun/noun:inanim:m:v_naz:xp2",
    "vesum:entry:168409": "vesum:record:ключ/noun/noun:inanim:m:v_naz",
    "vesum:entry:30497": "vesum:record:броня/noun/noun:inanim:f:v_naz",
    "vesum:entry:67854": "vesum:record:вряди-годи/adv/adv",
    "vesum:entry:40937": "vesum:record:вибігати/verb/verb:imperf:inf",
    "vesum:entry:40942": "vesum:record:вибігти/verb/verb:perf:inf",
    "sources.puls_cefr:id:4340": "puls:record:замок/іменник/A2",
    "sources.puls_cefr:id:3768": "puls:record:ключ/іменник/A2",
    "sources.frazeolohichnyi:id:568": "frazeolohichnyi:record:будувати повітряні замки",
    "sources.wiktionary:id:11318": "wiktionary:record:броня",
}


def record_key(locator: str) -> str | None:
    head = locator.split(" ", 1)[0].split("/section:", 1)[0]
    return RECORD_KEYS.get(head)


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


def _mapping_evidenced(assertions: list[dict]) -> bool:
    """A spelling-keyed source row on a spelling with several cards does not evidence this card (§9.5)."""
    return all(not a.get("mapping", {}).get("ambiguous", False) for a in assertions)


def _groups(xs: list[dict]) -> list[str]:
    return sorted({x["independence_group"] for x in xs if not x["independence_group"].endswith("?")})


def _value_entry(vn: str, xs: list[dict], declared: bool = False) -> dict:
    entry = {
        "value_norm": vn,
        "assertion_ids": sorted(x["assertion_id"] for x in xs),
        "independence_groups": _groups(xs),
    }
    if declared:
        entry["declared_set"] = True
    return entry


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
    # A tier-1 source that itself lists the doublet declares a variant; observed values inside the set agree.
    for d in declared:
        if observed <= set(d["value_norm"].split("|")):
            return {
                "state": "variant",
                "selected": sorted(a["assertion_id"] for a in voting),
                "values": values,
                "independence_groups_agreeing": len(_groups(voting)),
            }
    if declared:  # a declared set that does not contain an observed value is a disagreement
        return {"state": "conflict", "selected": None, "values": values, "independence_groups_agreeing": 0}
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
    return {"state": "conflict", "selected": None, "values": values, "independence_groups_agreeing": 0}


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


def _resolve_keyed(voting: list[dict], overlay: dict | None) -> dict:
    parts: dict[str, list[dict]] = {}
    for a in voting:
        parts.setdefault(a["value_norm"].split("=", 1)[0], []).append(a)
    per_key = {k: _resolve_scalar(xs, overlay) for k, xs in sorted(parts.items())}
    worst = max(per_key.values(), key=lambda r: STATE_RANK[r["state"]])
    selected = [r["selected"] for r in per_key.values() if isinstance(r["selected"], str)]
    for r in per_key.values():
        if isinstance(r["selected"], list):
            selected += r["selected"]
    return {
        "state": worst["state"],
        "selected": sorted(selected) if worst["state"] != "conflict" else None,
        "values": [v for r in per_key.values() for v in r["values"]],
        "independence_groups_agreeing": min(r["independence_groups_agreeing"] for r in per_key.values()),
    }


def resolve(assertions: list[dict], field: str, subject_id: str, overlay: dict | None = None) -> dict:
    """Reference implementation of schema.md §8 (field resolution). Kept small on purpose."""
    mine = [a for a in assertions if a["field"] == field and a["subject"]["id"] == subject_id]
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
        return {"state": state, "selected": None, "values": [], "mapping_evidenced": False, **base}
    voting = [a for a in active if a["tier"] in (1, 2)]
    if not voting:
        first = sorted(active, key=lambda a: a["assertion_id"])[0]
        return {
            "state": "unverified",
            "selected": first["assertion_id"],
            "values": [_value_entry(first["value_norm"], active)],
            "independence_groups_agreeing": 0,
            "mapping_evidenced": _mapping_evidenced(active),
            "independence_groups_evidenced": 0,
            **base,
        }
    if cls == "text":
        res = _resolve_text(voting)
    elif cls == "keyed":
        res = _resolve_keyed(voting, overlay)
    else:
        res = _resolve_scalar(voting, overlay)
    sel = res["selected"]
    sel_ids = set(sel if isinstance(sel, list) else ([sel] if sel else []))
    shown = {vn for v in res["values"] for vn in [v["value_norm"]] if sel_ids & set(v["assertion_ids"])}
    # Evidence for a dependent eligibility rule: only assertions whose mapping to THIS card is not ambiguous.
    evidenced = [a for a in voting if a["value_norm"] in shown and not a.get("mapping", {}).get("ambiguous", False)]
    res["mapping_evidenced"] = bool(evidenced)
    res["independence_groups_evidenced"] = len(_groups(evidenced))
    res.update(base)
    return res


def _proposition(cls: str, field: str, subject_id: str) -> str:
    if cls == "keyed":
        return f"{field}({subject_id})[<key>] = <value>; one proposition per key"
    if cls == "text":
        return f"{field}({subject_id}) ∋ <text>; parallel texts, identical texts corroborate"
    return f"{field}({subject_id}) = <value_norm>"


def card_version(card_public: dict) -> str:
    body = {
        k: card_public[k]
        for k in ("card_id", "card_kind", "state", "merged_into", "split_into", "senses", "links", "fields")
    }
    return "cv_" + hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:24]


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
    card_fields = sorted({a["field"] for a in assertions if a["subject"]["kind"] == "card"})
    fields = {f: resolve(assertions, f, card_id) for f in card_fields}
    if fields.get("english_gloss"):
        fields["english_gloss"]["level_policy"] = "scaffold: shown at A1 by design, never raised from A2 (#8983)"
    for s in senses:
        sf = sorted({a["field"] for a in assertions if a["subject"]["id"] == s["sense_id"]})
        s["fields"] = {f: resolve(assertions, f, s["sense_id"]) for f in sf}
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
        "fields": fields,
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
        "build": BUILD,
    }
    out["build"] = {**BUILD, "card_version": card_version(out)}
    return out


def public_projection(c: dict) -> dict:
    """Public outputs carry suppressed assertions as tombstones: id, status and reference only (schema.md §12.3)."""
    out = json.loads(json.dumps(c, ensure_ascii=False))
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


def sense(sense_id, order, smap, state="active"):
    return {"sense_id": sense_id, "order": order, "state": state, "merged_into": None, "sense_map": smap, "fields": {}}


# ---------------------------------------------------------------- ids (opaque examples)
CASTLE, LOCK, SETTLEMENT = "wc_7k3m9q2xw4pd", "wc_c2v8n5rt6yhq", "wc_e9p1s4dz7xkm"
KLIUCH1, KLIUCH2 = "wc_hb4t8k1nq6zv", "wc_m3y6w9dc2sxr"
IDIOM, POVITRIANYI, BUDUVATY = "wc_pq7z2f5jh8na", "wc_s1x4v7gk9tdb", "wc_t6d3h8mp2wqz"
BRONIA_ARMOUR, BRONIA_RESERV = "wc_v5r2b9nx3cfk", "wc_w8g1k4qt7zhm"
VRIADY = "wc_x2j5n8sd1vpc"
VYBIHATY, VYBIHTY = "wc_y9c3q6hw4rtn", "wc_z4f7m1kb8xsq"
LEGACY_ZAMOK = "wc_0a1b2c3d4e5f"  # the pre-card atlas0 article "замок", split into CASTLE + LOCK

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
            "cefr",
            "B2",
            source="grac_estimate",
            snapshot=ATLAS0_SNAP,
            locator="atlas0:enrichment:броня/cefr 'estimated (GRAC frequency)' 0.55/million rank 2792/4161",
            producer={"kind": "estimator", "name": "GRAC frequency → CEFR estimate", "version": "atlas0"},
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
    """Identity registry: the versioned build input that fixes every card and sense id (schema.md §13)."""
    entries = []
    for c in sorted(cards.values(), key=lambda c: c["card_id"]):
        e = {
            "card_id": c["card_id"],
            "card_kind": c["card_kind"],
            "state": c["state"],
            "key_at_creation": c["key_at_creation"],
            "created_in_build": "atlas0-migration-M1" if c["card_id"] == LEGACY_ZAMOK else "example-2026-09-28",
            "senses": [{"sense_id": s["sense_id"], "order": s["order"], "state": s["state"]} for s in c["senses"]],
        }
        if c["merged_into"]:
            e["merged_into"] = c["merged_into"]
        if c["split_into"]:
            e["split_into"] = c["split_into"]
        entries.append(e)
    entries.append(
        {
            "card_id": KLIUCH2,
            "card_kind": "lexeme",
            "state": "active",
            "key_at_creation": {
                "spelling": "ключ",
                "stress_patterns": ["ключ"],
                "pos": "noun",
                "paradigm_key": "vesum:entry:168409",
                "source_keys": [{"source_id": "ulif", "key": "ulif:entry:98008"}],
            },
            "created_in_build": "example-2026-09-28",
            "senses": [],
        }
    )
    entries.sort(key=lambda e: e["card_id"])
    events = [
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
    ]
    return {"schema_version": "1", "registry_version": 1, "entries": entries, "events": events}


def build_overlay() -> dict:
    return {"schema_version": "1", "entries": [SPLIT_OVERLAY]}


def build_suppressions() -> dict:
    """Persistent suppression selectors (schema.md §12.1): keyed by durable source-record keys or by assertion
    content, never by local row ids, so they survive reharvest, remapping and rollback."""
    return {
        "schema_version": "1",
        "entries": [
            {
                "suppression_id": "sup-example-0001",
                "issue": "https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8980",
                "date": "2026-09-28",
                "selector": {
                    "kind": "source_record",
                    "source_id": "ulif",
                    "source_record_key": "ulif:record:замок#замо́к#",
                },
                "scope": ["site", "dataset"],
                "applies_to": {"reharvest": True, "rollback": True},
                "note": "example: every assertion extracted from the ULIF lock record, in any snapshot",
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
                },
                "scope": ["site", "dataset", "internal"],
                "applies_to": {"reharvest": True, "rollback": True},
                "note": "example: one value from one source on one spelling, whatever its assertion id after re-normalisation",
            },
        ],
    }


def build_derivations(cards: dict) -> dict:
    """Dependency records (schema.md §11): every derived item names its input assertions, the card versions it
    read and its own output identity, so a withdrawn assertion invalidates exactly the outputs that used it."""
    castle = cards["zamok-castle"]
    stress_ids = castle["fields"]["stress"]["values"][0]["assertion_ids"]
    inputs = {
        "assertion_ids": sorted(stress_ids),
        "card_ids": [castle["card_id"]],
        "card_versions": {castle["card_id"]: castle["build"]["card_version"]},
    }
    output = {"kind": "exercise", "key": "practice/stress/wc_7k3m9q2xw4pd/1", "content_sha256": "0" * 64}
    ident = json.dumps(
        {
            "generator": "stress_item",
            "generator_version": "example",
            "inputs": inputs,
            "output": {"kind": output["kind"], "key": output["key"]},
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return {
        "schema_version": "1",
        "entries": [
            {
                "derived_id": "wd_" + hashlib.sha256(ident.encode()).hexdigest()[:24],
                "kind": "exercise",
                "generator": "stress_item",
                "generator_version": "example",
                "rules_version": RULES,
                "build_id": BUILD["build_id"],
                "inputs": inputs,
                "output": output,
                "status": "active",
            }
        ],
    }


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
