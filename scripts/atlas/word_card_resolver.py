"""Field resolution, assertion identity and card versions for word cards (schema.md §4, §8, §11).

One implementation of the contract, shared by the worked-example generator
(`docs/atlas/word-cards/examples/build_examples.py`) and the pilot assembler
(`scripts/atlas/word_card_assembly.py`). Pure functions over assertion dicts: no
I/O, no registry access. Pinned by `tests/validate/test_word_card_examples.py`.
"""

from __future__ import annotations

import hashlib
import json


def canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


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
    # The declared entry is a shown proposition with no source assertion behind it: it stays unevidenced and
    # therefore keeps the field-level `mapping_evidenced` false (rule 7; review never promotes, Q5).
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
    """Field-level evidence = every shown proposition is evidenced; corroboration = the weakest shown one.
    EVERY shown proposition counts, including an overlay-declared set (`declared_by`) that no source assertion
    states (Astra r3): it is unevidenced, so a field whose only declaration is an overlay is not evidenced as a
    whole and its minimum corroboration is 0; an item that consumes one member reads that member's entry."""
    shown = _shown_entries(res)
    return {
        "mapping_evidenced": bool(shown) and all(v["mapping_evidenced"] for v in shown),
        "independence_groups_evidenced": min((v["independence_groups_evidenced"] for v in shown), default=0),
    }


def _resolve_keyed(voting: list[dict], overlay: dict | None) -> dict:
    """One proposition per slot (`rod.sg=замку`). Evidence and corroboration are recorded per slot in
    `propositions`; an item that consumes one slot reads that slot. The field-level flags are the conjunction
    (evidence) and the minimum (corroboration) over the slots, so one evidenced slot never covers another.

    A source that lists several forms for one slot declares a set (`rod.sg=замку|замка`): the slot key is removed
    before the scalar rule reads the set, so the members are forms, not `slot=form` strings."""
    parts: dict[str, list[dict]] = {}
    for a in voting:
        parts.setdefault(a["value_norm"].split("=", 1)[0], []).append(a)
    per_key = {}
    for k, xs in sorted(parts.items()):
        bare = [{**a, "value_norm": a["value_norm"].split("=", 1)[1]} for a in xs]
        res = _resolve_scalar(bare, overlay)
        for v in res["values"]:
            v["value_norm"] = f"{k}={v['value_norm']}"
        per_key[k] = res
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
