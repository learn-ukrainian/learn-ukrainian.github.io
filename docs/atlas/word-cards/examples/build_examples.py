"""Build the worked-example word cards (#8978) as JSON instances of schemas/word-card-v1.schema.json.

Every Ukrainian value below is quoted from data/sources.db, data/vesum.db or data/atlas.db
(read-only queries recorded in docs/atlas/word-cards/worked-examples.md). Nothing is
model-written. Card/sense ids are opaque example ids; assertion ids are derived with the
formula in schema.md §4 so a rebuild reproduces them.

Run:  /home/ops/learn-ukrainian/.venv/bin/python docs/atlas/word-cards/examples/build_examples.py
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RULES = "rules-v1-draft"
REGISTER_VERSION = 2

ULIF_SNAP = "ulif@ulif-dictua-v2/2026-09-22..2026-09-27"
VESUM_SNAP = "vesum@53923150073b4fc7"
ATLAS0_SNAP = "atlas0@manifest-0.1/2026-09-11"
SOURCES_SNAP = "sources.db@2026-09-28"

# Register source id -> (independence group, tier). Provisional; schema.md §7.
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

BUILD = {
    "build_id": "example-2026-09-28",
    "rules_version": RULES,
    "inputs": {
        "vesum.canonical_jsonl_sha256": "53923150073b4fc7bee419fe7b071acbe17b6a9aba76cfb2d0336c95f5188680",
        "sources.ulif_dictua_entries": "262788 rows homonym_checked=1, parser ulif-dictua-v2, retrieved_at 2026-09-22T07:16:23Z..2026-09-27T23:36:03Z",
        "sources.ulif_dictua_sections": "336369 rows (paradigm 250183, synonyms 75952, phraseology 8131, antonyms 2103)",
        "atlas0.manifest": "atlas.db manifest_metadata version 0.1 generated_at 2026-09-11T10:12:36+00:00",
        "overlay": "none (examples)",
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


def lid(link_type: str, frm: str, to: str) -> str:
    return "wl_" + hashlib.sha256(f"{link_type}|{frm}|{to}".encode()).hexdigest()[:24]


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
    if mapping:
        a["mapping"] = mapping
    if suppression_ref:
        a["suppression_ref"] = suppression_ref
    return a


def resolve(assertions: list[dict], field: str, subject_id: str, overlay: dict | None = None) -> dict:
    """Reference implementation of schema.md §8 (field resolution). Kept tiny on purpose."""
    mine = [a for a in assertions if a["field"] == field and a["subject"]["id"] == subject_id]
    active = [
        a
        for a in mine
        if a["status"] == "active" and a.get("mapping", {}).get("confidence", "high") in ("high", "medium")
    ]
    if not active:
        if any(a["status"] == "suppressed" for a in mine):
            return {"state": "suppressed", "selected": None, "values": []}
        return {"state": "unverified", "selected": None, "values": []}
    voting = [a for a in active if a["tier"] in (1, 2)]
    if not voting:
        first = sorted(active, key=lambda a: a["assertion_id"])[0]
        return {
            "state": "unverified",
            "selected": first["assertion_id"],
            "values": [
                {
                    "value_norm": first["value_norm"],
                    "assertion_ids": [x["assertion_id"] for x in active],
                    "independence_groups": sorted({x["independence_group"] for x in active}),
                }
            ],
            "independence_groups_agreeing": 0,
        }
    by_value: dict[str, list[dict]] = {}
    for a in voting:
        by_value.setdefault(a["value_norm"], []).append(a)
    values = [
        {
            "value_norm": vn,
            "assertion_ids": sorted(x["assertion_id"] for x in xs),
            "independence_groups": sorted(
                {x["independence_group"] for x in xs if not x["independence_group"].endswith("?")}
            ),
        }
        for vn, xs in sorted(by_value.items())
    ]
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
    declared = [a for a in voting if a["tier"] == 1 and "|" in a["value_norm"]]
    for d in declared:
        members = set(d["value_norm"].split("|"))
        if members == set(by_value):
            return {
                "state": "variant",
                "selected": sorted(a["assertion_id"] for a in voting),
                "values": values,
                "independence_groups_agreeing": 0,
            }
    return {"state": "conflict", "selected": None, "values": values, "independence_groups_agreeing": 0}


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
    overlay=None,
):
    card_fields = sorted({a["field"] for a in assertions if a["subject"]["kind"] == "card"})
    fields = {f: resolve(assertions, f, card_id) for f in card_fields}
    if fields.get("english_gloss"):
        fields["english_gloss"]["level_policy"] = "scaffold: shown at A1 by design, never raised from A2 (#8983)"
    for s in senses:
        sf = sorted({a["field"] for a in assertions if a["subject"]["id"] == s["sense_id"]})
        s["fields"] = {f: resolve(assertions, f, s["sense_id"]) for f in sf}
    return {
        "schema_version": "1",
        "card_id": card_id,
        "card_kind": kind,
        "state": state,
        "merged_into": merged_into,
        "key_at_creation": key,
        "identity": identity,
        "senses": senses,
        "links": links,
        "fields": fields,
        "assertions": assertions,
        "quality": {
            "identity_confidence": identity["confidence"],
            "extraction_confidence_min": min(
                (a["extraction_confidence"] for a in assertions), key=["high", "medium", "low"].index
            ),
            "linguistic_review": review or {"status": "none"},
            "practice_eligibility": eligibility,
        },
        "overlay_applied": overlay or [],
        "build": BUILD,
    }


def sense(sense_id, order, smap, state="active"):
    return {"sense_id": sense_id, "order": order, "state": state, "merged_into": None, "sense_map": smap, "fields": {}}


# ---------------------------------------------------------------- ids (opaque examples)
CASTLE, LOCK, SETTLEMENT = "wc_7k3m9q2xw4pd", "wc_c2v8n5rt6yhq", "wc_e9p1s4dz7xkm"
KLIUCH1, KLIUCH2 = "wc_hb4t8k1nq6zv", "wc_m3y6w9dc2sxr"
IDIOM, POVITRIANYI, BUDUVATY = "wc_pq7z2f5jh8na", "wc_s1x4v7gk9tdb", "wc_t6d3h8mp2wqz"
BRONIA_ARMOUR, BRONIA_RESERV = "wc_v5r2b9nx3cfk", "wc_w8g1k4qt7zhm"
VRIADY = "wc_x2j5n8sd1vpc"
VYBIHATY, VYBIHTY = "wc_y9c3q6hw4rtn", "wc_z4f7m1kb8xsq"

PULS_SPELLING = {
    "confidence": "medium",
    "note": "PULS rows are keyed by spelling; which замок the A2 rating means is not stated",
}


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
            mapping={"confidence": "medium", "note": "kaikki row is spelling-keyed; its stress matches this card only"},
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
            s1,
            "synonyms",
            ["фортеця", "бастіон", "цитадель", "шато"],
            source="synonyms_karavansky",
            snapshot=ATLAS0_SNAP,
            locator="atlas0:enrichment:замок/synonyms (slovnyk.me: Словник синонімів Караванського)",
            mapping={"confidence": "medium", "note": "spelling-keyed; members are castle words"},
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
                {
                    "source_id": "synonyms_karavansky",
                    "source_sense_key": "slovnyk_me:synonyms_karavansky:замок",
                    "mapped_by": "rules: single sense on source side",
                },
            ],
        ),
        sense(s2, 2, [{"source_id": "vts", "source_sense_key": "vts:замок#I/2"}]),
        sense(s3, 3, [{"source_id": "ulif", "source_sense_key": "ulif:section:96930"}], state="unsplit"),
    ]
    links = [
        {
            "link_id": lid("homograph_of", cid, LOCK),
            "type": "homograph_of",
            "from": cid,
            "to": LOCK,
            "assertion_ids": [],
            "state": "active",
        },
        {
            "link_id": lid("homograph_of", cid, SETTLEMENT),
            "type": "homograph_of",
            "from": cid,
            "to": SETTLEMENT,
            "assertion_ids": [],
            "state": "active",
        },
    ]
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
            "eligible": True,
            "rules_version": RULES,
            "reasons": ["stress verified (3 groups)", "identity high", "cefr A2 (single-source, spelling-keyed)"],
        },
        {
            "mode": "synonyms",
            "eligible": True,
            "rules_version": RULES,
            "reasons": ["sense s1 synonyms single-source ULIF + Караванський", "sense s3 unsplit excluded"],
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
    links = [
        {
            "link_id": lid("homograph_of", cid, CASTLE),
            "type": "homograph_of",
            "from": cid,
            "to": CASTLE,
            "assertion_ids": [],
            "state": "active",
        }
    ]
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
            "eligible": True,
            "rules_version": RULES,
            "reasons": ["stress verified (ULIF paradigm + VESUM comment)"],
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
        [
            {
                "link_id": lid("homograph_of", cid, CASTLE),
                "type": "homograph_of",
                "from": cid,
                "to": CASTLE,
                "assertion_ids": [],
                "state": "active",
            }
        ],
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
            mapping={"confidence": "medium", "note": "spelling-keyed"},
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
            mapping={"confidence": "medium", "note": "aligned to ВТС I/2 by curator"},
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
    links = [
        {
            "link_id": lid("homograph_of", cid, KLIUCH2),
            "type": "homograph_of",
            "from": cid,
            "to": KLIUCH2,
            "assertion_ids": [],
            "state": "active",
        }
    ]
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
            "eligible": True,
            "rules_version": RULES,
            "reasons": [
                "sense s1 definition_uk single-source ВТС; cefr A2; identity medium accepted for meaning mode by rules-v1-draft (open question Q7)"
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
            "link_id": lid("component_of", cid, CASTLE),
            "type": "component_of",
            "from": cid,
            "to": CASTLE,
            "role": "anchor (за́мки ↔ ULIF uid=47336 ЗА́МОК, castle)",
            "assertion_ids": [asr[0]["assertion_id"]],
            "state": "active",
        },
        {
            "link_id": lid("component_of", cid, POVITRIANYI),
            "type": "component_of",
            "from": cid,
            "to": POVITRIANYI,
            "role": "component (ULIF uid=115867)",
            "assertion_ids": [asr[1]["assertion_id"]],
            "state": "active",
        },
        {
            "link_id": lid("component_of", cid, BUDUVATY),
            "type": "component_of",
            "from": cid,
            "to": BUDUVATY,
            "role": "component (ULIF uid=10839)",
            "assertion_ids": [asr[0]["assertion_id"]],
            "state": "active",
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
            mapping={"confidence": "medium", "note": "spelling-keyed; matches this homonym's stress"},
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
            mapping={"confidence": "medium", "note": "spelling-keyed frequency"},
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
    links = [
        {
            "link_id": lid("homograph_of", cid, BRONIA_RESERV),
            "type": "homograph_of",
            "from": cid,
            "to": BRONIA_RESERV,
            "assertion_ids": [],
            "state": "active",
        }
    ]
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
            "Sources disagree on identity: VESUM one lemma with two stresses, ULIF two homonyms with distinct senses (бро́ня закріплення; документ про закріплення / броня́). Rules follow the finer division when stress and sense both differ; confidence medium until a language lane confirms."
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
    links = [
        {
            "link_id": lid("homograph_of", cid, BRONIA_ARMOUR),
            "type": "homograph_of",
            "from": cid,
            "to": BRONIA_ARMOUR,
            "assertion_ids": [],
            "state": "active",
        }
    ]
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
    for cid, other, role, ul, ve, hw, label, tag in (
        (
            VYBIHATY,
            VYBIHTY,
            "imperfective",
            "ulif:entry:34097",
            "vesum:entry:40937",
            "вибіга́ти",
            "дієслово недоконаного виду",
            "verb:imperf:inf",
        ),
        (
            VYBIHTY,
            VYBIHATY,
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
                    mapping={"confidence": "medium", "note": "spelling-keyed; covers both вибігати homonyms"},
                )
            )
        link_id = lid("aspect_pair", VYBIHATY, VYBIHTY)
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
        links = [
            {
                "link_id": link_id,
                "type": "aspect_pair",
                "from": cid,
                "to": other,
                "role": role,
                "assertion_ids": [link_asr["assertion_id"]],
                "state": "active",
            }
        ]
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


def main() -> None:
    out = {
        "zamok-castle": build_castle(),
        "zamok-lock": build_lock(),
        "zamok-settlement": build_settlement(),
        "kliuch-1": build_kliuch(),
        "idiom-buduvaty-povitriani-zamky": build_idiom(),
        "bronia-armour": build_bronia_armour(),
        "bronia-reservation": build_bronia_reserv(),
        "vriady-hody-conflict": build_vriady(),
    }
    for i, c in enumerate(build_aspect_pair()):
        out[["vybihaty-imperf", "vybihty-perf"][i]] = c
    for name, c in out.items():
        (HERE / f"{name}.json").write_text(json.dumps(c, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(out)} cards to {HERE}")


if __name__ == "__main__":
    main()
