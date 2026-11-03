"""Private human audit packets and proposals for the existing review ledger.

Only the steward admits a real human decision to approved_reviews. These
functions never write that authority or grant site/dataset approval.
"""

import argparse
import hashlib
import html
import json
import random
from datetime import datetime
from pathlib import Path

from scripts.atlas import word_card_golden_set as gold
from scripts.atlas.a1_card_receipts import _BINDING_FIELDS, _payload_text, digest, verify_receipt
from scripts.atlas.word_card_assertion_check import CONTEXT_FIELDS, canonical_source


def select_cards(cards, decisions, *, frozen_at=None, seed=None, seed_issued_at=None):
    """Census through 299, otherwise steward-seeded uniform sampling and class extras."""
    gold.require(0 < len(cards) <= 10000, "Changed-card batch must contain 1..10000 cards")
    by_card = {}
    for row in decisions:
        if row["field"] in CONTEXT_FIELDS:
            by_card.setdefault(row["card_id"], set()).add(row["field"])
    population = sorted(by_card)
    if len(population) <= 299:
        return population, {"method": "census", "population": len(population), "random_count": len(population),
                            "class_extras": [], "seed_sha256": None}
    gold.require(isinstance(seed, str) and bool(seed) and frozen_at and seed_issued_at,
                 "A post-freeze steward seed is required")
    frozen = datetime.fromisoformat(frozen_at.replace("Z", "+00:00"))
    issued = datetime.fromisoformat(seed_issued_at.replace("Z", "+00:00"))
    gold.require(frozen.tzinfo is not None and issued.tzinfo is not None and issued > frozen,
                 "Steward seed must follow the freeze")
    rng = random.Random(int(hashlib.sha256(seed.encode()).hexdigest(), 16))
    selected = set(rng.sample(population, 299))
    extras = set()
    for field in sorted({field for fields in by_card.values() for field in fields}):
        stratum = [card for card in population if field in by_card[card]]
        extras.update(rng.sample(stratum, min(12, len(stratum))))
    return sorted(selected | extras), {"method": "uniform-without-replacement-plus-class-extras",
        "population": len(population), "random_count": 299, "class_extras": sorted(extras - selected),
        "seed_sha256": hashlib.sha256(seed.encode()).hexdigest(), "frozen_at": frozen_at,
        "seed_issued_at": seed_issued_at}


def make_packet(cards, decisions, batches, register, frozen, original_selection, original_input, *, selection=None):
    """Place exact captured evidence beside every judgment and original50 assertion."""
    by_card = {card["card_id"]: card for card in cards}
    gold.require(len(by_card) == len(cards), "Duplicate human-packet card")
    chosen, sampling = select_cards(cards, decisions, **(selection or {}))
    gold.require(original_selection["selected"] == len(original_input["cards"]) == 50
                 and len(original_selection["versions"]) == 50
                 and {c["card_id"] for c in original_input["cards"]} == set(original_selection["versions"])
                 and original_input["selection"] == original_selection, "Original50 membership changed")
    records, receipts = {}, {}
    links = {}
    for assembly, sources in batches:
        for record in sources["records"].values():
            key = digest({field: record[field] for field in _BINDING_FIELDS})
            if key in records:
                gold.require(records[key]["payload"] == record["payload"], "Ambiguous captured source body")
            records[key] = record
        for receipt in assembly["receipts"]:
            gold.require(receipt["receipt_id"] not in receipts or receipts[receipt["receipt_id"]] == receipt,
                         "Ambiguous human-packet receipt")
            receipts[receipt["receipt_id"]] = receipt
        links.update(assembly["assertion_receipts"])
    evidence, bodies = {}, {}
    decision_by_id = {row["assertion_id"]: row for row in decisions}

    def item(card, assertion, item_receipts, item_links):
        assertion_id = assertion["assertion_id"]
        decision = decision_by_id.get(assertion_id)
        additional = {r["receipt_id"]: r for r in (decision or {}).get("additional_receipts", [])}
        refs, unavailable = [], []
        for rid in dict.fromkeys([*item_links.get(assertion_id, []), *additional]):
            receipt = item_receipts.get(rid, additional.get(rid))
            if receipt is None:
                unavailable.append({"receipt_id": rid, "reason": "receipt_missing"})
                continue
            key = digest({field: receipt[field] for field in _BINDING_FIELDS})
            record = records.get(key)
            if record is None:
                unavailable.append({"receipt_id": rid, "reason": "captured_body_missing"})
                continue
            verify_receipt(receipt, {receipt["record_key"]: record}, receipt["entry_id"], receipt["sense_key"])
            source = canonical_source(record["source_id"], register)
            body_id = digest(record["payload"])
            bodies[body_id] = record["payload"]
            source = {key: source[key] for key in ("id", "name", "role", "fields_used") if key in source} if source else None
            value = {"receipt": receipt, "source": source,
                     "source_role": record.get("source_role") or (source or {}).get("role"),
                     "facet": assertion["field"], "body_sha256": body_id,
                     "context": _payload_text(record["payload"], receipt["payload_pointer"])}
            evidence_id = digest(value)
            evidence[evidence_id] = value
            refs.append(evidence_id)
        return {"assertion": assertion, "decision": decision, "evidence": refs,
                "missing": unavailable or ([] if refs else [{"reason": "receipt_missing"}])}

    judgment = []
    for card_id in chosen:
        card = by_card[card_id]
        rows = [item(card, a, receipts, links) for a in card["assertions"] if a["field"] in CONTEXT_FIELDS]
        judgment.append({"card_id": card_id, "card_version": card["build"]["card_version"],
                         "card": card, "assertions": rows, "evidence_sha256": digest(rows)})
    original = []
    for card in original_input["cards"]:
        cid, version = card["card_id"], card["build"]["card_version"]
        gold.require(original_selection["versions"].get(cid) == version, "Original50 version changed")
        original.append({"card_id": cid, "card_version": version,
            "current_version_matches": cid in by_card and by_card[cid]["build"]["card_version"] == version,
            "card": card, "assertions": [item(card, a, original_input["receipts"], original_input["assertion_receipts"])
                                          for a in card["assertions"]]})
    return {"schema_version": "word-card-human-packet.v1", "frozen": frozen,
            "batch_fingerprint": digest({"frozen": frozen, "cards": {c["card_id"]: digest(c) for c in cards}}),
            "card_count": len(cards), "assertion_count": len(decisions), "sampling": sampling,
            "judgment_cards": judgment, "original50": original, "evidence": evidence, "bodies": bodies,
            "decision_status": "PENDING_HUMAN", "original50_status": "SEPARATE_OBLIGATION_PENDING"}


def decision_records(packet, submission):
    """Validate a human submission and return proposed approved_reviews rows only."""
    packet_sha = digest(packet)
    gold.require(submission.get("packet_sha256") == packet_sha, "Human decision packet changed")
    gold.require(isinstance(submission.get("reviewer_record"), str) and submission["reviewer_record"].strip(),
                 "Actual human reviewer record is required")
    rows = submission["decisions"]
    expected = {row["card_id"]: row for row in packet["judgment_cards"]}
    observed = {row["card_id"] for row in rows}
    rejected = any(row.get("verdict") == "reject" for row in rows)
    gold.require(len(rows) == len(observed) and observed <= set(expected)
                 and (rejected or observed == set(expected)),
                 "Incomplete or duplicate human decision coverage")
    records = []
    for decision in rows:
        gold.require(set(decision) == {"card_id", "verdict", "field", "reason"}, "Unknown human decision fields")
        item = expected[decision["card_id"]]
        gold.require(decision.get("verdict") in {"accept", "reject"}, "Pending is never human approval")
        gold.require(isinstance(decision.get("reason"), str) and decision["reason"].strip(),
                     "Human decision requires an inspection reason")
        if decision["verdict"] == "reject":
            gold.require(decision.get("field") in {r["assertion"]["field"] for r in item["assertions"]},
                         "Rejected field must identify the material finding")
        gold.require(decision["verdict"] == "reject" or all(not row["missing"] and row["decision"]
                         and row["decision"]["extraction"] == "exact" for row in item["assertions"]),
                     "Missing source evidence cannot be accepted by a human pass")
        records.append({"card_id": item["card_id"], "card_version": item["card_version"],
            "status": "active", "record": submission["reviewer_record"], "lane": "human", "approved_for": [],
            "human_audit": {"schema_version": "word-card-human-decision.v1", "reviewer_kind": "human",
                "packet_sha256": packet_sha, "batch_fingerprint": packet["batch_fingerprint"],
                "assertion_scope": [r["assertion"]["assertion_id"] for r in item["assertions"]],
                "evidence_sha256": item["evidence_sha256"], **decision}})
    return records


def audit_status(packet, ledger):
    """Read only steward-admitted exact-version decisions from the existing ledger."""
    selected = {row["card_id"]: row for row in packet["judgment_cards"]}
    packet_sha = digest(packet)
    accepted = set()
    for row in ledger["approved_reviews"]:
        audit = row.get("human_audit", {})
        if audit.get("batch_fingerprint") != packet["batch_fingerprint"]:
            continue
        if audit.get("verdict") == "reject":
            return "MATERIAL_FINDING_HOLDS_BATCH"
        item = selected.get(row["card_id"])
        if (item is None or row.get("status") != "active" or row.get("lane") != "human"
                or row.get("card_version") != item["card_version"] or not row.get("record")
                or audit.get("schema_version") != "word-card-human-decision.v1"
                or audit.get("reviewer_kind") != "human" or audit.get("verdict") != "accept"
                or not isinstance(audit.get("reason"), str) or not audit["reason"].strip()
                or audit.get("packet_sha256") != packet_sha
                or audit.get("evidence_sha256") != item["evidence_sha256"]
                or audit.get("assertion_scope") != [r["assertion"]["assertion_id"] for r in item["assertions"]]):
            return "MISSING_STALE_OR_WITHDRAWN_HUMAN_DECISION"
        if any(r["missing"] or not r["decision"] or r["decision"]["extraction"] != "exact" for r in item["assertions"]):
            return "MISSING_SOURCE_EVIDENCE"
        accepted.add(row["card_id"])
    return "HUMAN_AUDIT_ACCEPTED" if accepted == set(selected) else "PENDING_HUMAN"


def render_packet(packet):
    """Render all captured context locally, without external assets or truncation."""
    def esc(value):
        return html.escape(str(value))
    parts = ['<!doctype html><html lang="en"><meta charset="utf-8"><title>A1 human source review</title>',
        '<style>body{font:17px system-ui;max-width:1100px;margin:2em auto;padding:1em}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f4f4f4;padding:1em}article{border-top:2px solid #555;margin-top:2em}label{display:block;margin:1em}textarea{width:95%;min-height:4em}mark{background:#fff39c}</style>',
        '<h1>A1 human source review</h1><p>Decisions are pending. Downloading decisions creates a proposal for the steward. It does not update the review ledger or approve publication.</p>',
        f'<p>Batch {esc(packet["batch_fingerprint"])}. {packet["card_count"]} cards, {packet["assertion_count"]} assertions. Judgment population {packet["sampling"]["population"]}. Original50 remains a separate obligation.</p>',
        '<label>Human reviewer record or decision reference <input id="reviewer"></label>',
        '<button id="download">Download human decision proposal</button><p id="error"></p>']
    for obligation, cards in (("Judgment audit", packet["judgment_cards"]), ("Original50 separate obligation", packet["original50"])):
        parts.append(f'<h2>{obligation}</h2>')
        for card in cards:
            cid = card["card_id"]
            parts.append(f'<article><h3>{esc(card["card"]["key_at_creation"]["spelling"])} · {esc(cid)}</h3><p>Version {esc(card["card_version"])}</p>')
            if card.get("current_version_matches") is False:
                parts.append('<p>UNRESOLVED: original version differs from current population.</p>')
            for row in card["assertions"]:
                assertion = row["assertion"]
                parts.append(f'<h4>{esc(assertion["field"])} · {esc(assertion["assertion_id"])}</h4><pre>{esc(json.dumps(assertion["value"], ensure_ascii=False, indent=2))}</pre>')
                decision = row["decision"] or {"status": "unresolved", "reason": "decision_missing"}
                parts.append(f'<p>{esc(decision["status"])}: {esc(decision["reason"])}. Missing evidence: {esc(row["missing"])}</p>')
                for eid in row["evidence"]:
                    evidence = packet["evidence"][eid]
                    receipt, context = evidence["receipt"], evidence["context"]
                    start, end = receipt["span"]
                    source = evidence["source"] or {"name": "Unknown source"}
                    parts.append(f'<p>{esc(source["name"])} · {esc(evidence["facet"])} · {esc(evidence["source_role"])}</p><pre>{esc(context[:start])}<mark>{esc(context[start:end])}</mark>{esc(context[end:])}</pre>')
                    parts.append(f'<details><summary>Exact receipt and source identity</summary><pre>{esc(json.dumps(evidence, ensure_ascii=False, indent=2))}</pre></details><p><a href="#body-{esc(evidence["body_sha256"])}">Complete captured source body</a></p>')
            parts.append(f'<details><summary>Complete exact card</summary><pre>{esc(json.dumps(card["card"],ensure_ascii=False,indent=2))}</pre></details>')
            if obligation == "Judgment audit":
                parts.append(f'<div class="decision" data-card="{esc(cid)}"><label>Decision <select><option value="">Pending</option><option>accept</option><option>reject</option></select></label><label>Rejected field <input class="field"></label><label>Inspection reason <textarea></textarea></label></div>')
            parts.append('</article>')
    fingerprint = json.dumps(digest(packet))
    parts.append('<h2>Complete captured source bodies</h2>')
    for key, body in packet["bodies"].items():
        parts.append(f'<details id="body-{esc(key)}"><summary>Source body SHA-256 {esc(key)}</summary><pre>{esc(json.dumps(body,ensure_ascii=False,indent=2))}</pre></details>')
    parts.append('''<script>
document.getElementById('download').onclick=()=>{try{
 const reviewer_record=document.getElementById('reviewer').value.trim();
 if(!reviewer_record)throw Error('Enter the human reviewer record.');
 const nodes=[...document.querySelectorAll('.decision')];
 const decisions=nodes.filter(e=>e.querySelector('select').value).map(e=>{
  const verdict=e.querySelector('select').value,reason=e.querySelector('textarea').value.trim(),field=e.querySelector('.field').value.trim();
  if(!reason||(verdict==='reject'&&!field))throw Error('Each decision needs an inspection reason; a rejection needs its field.');
  return{card_id:e.dataset.card,verdict,field:field||null,reason};
 });
 if(!decisions.some(d=>d.verdict==='reject')&&decisions.length!==nodes.length)throw Error('Acceptance requires every selected card. A material rejection can be recorded immediately.');
 const data={packet_sha256:PACKET,reviewer_record,decisions};
 const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));
 a.download='human-decisions.json';a.click();URL.revokeObjectURL(a.href);
}catch(e){document.getElementById('error').textContent=e.message}};
</script></html>'''.replace('PACKET', fingerprint))
    return '\n'.join(parts)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Render a private source-complete human audit or validate a ledger proposal.\nUse only for frozen certification evidence; this never records live approval.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python -m scripts.atlas.word_card_human_audit --packet packet.json --sha256 HASH --output packet.html
  .venv/bin/python -m scripts.atlas.word_card_human_audit --packet packet.json --sha256 HASH --decisions human-decisions.json --output proposal.json
Outputs: private HTML or proposed approved_reviews rows; no live ledger writes or network calls.
Exit codes: 0 rendered/validated; 1 refused evidence; 2 usage error.
Related: #12658, docs/atlas/word-cards/certification-spec.md
""")
    parser.add_argument('--packet', type=Path, required=True, help='Frozen packet JSON path, e.g. packet.json')
    parser.add_argument('--sha256', required=True, help='Steward-pinned exact packet file SHA-256, 64 lowercase hex digits')
    parser.add_argument('--decisions', type=Path, help='Human decision JSON to validate; default: render pending HTML')
    parser.add_argument('--output', type=Path, required=True, help='Private output file, e.g. packet.html or proposal.json')
    args = parser.parse_args(argv)
    try:
        _, packet = gold.read(args.packet, args.sha256)
        gold.require(packet['schema_version'] == 'word-card-human-packet.v1', 'Unsupported human packet')
        gold.require(args.output.resolve() not in {args.packet.resolve(), args.decisions.resolve() if args.decisions else None},
                     'Output must not replace frozen evidence')
        from scripts.atlas import word_card_assembly as assembly
        assembly.require_host_only([args.output])
        if args.decisions:
            _, submission = gold.read(args.decisions)
            output = json.dumps({'schema_version': 'word-card-human-ledger-proposal.v1',
                                 'approved_reviews': decision_records(packet, submission)}, ensure_ascii=False, indent=2)
        else:
            output = render_packet(packet)
        args.output.write_text(output)
        print(json.dumps({'status': 'PROPOSAL_ONLY' if args.decisions else 'PENDING_HUMAN',
                          'packet_sha256': args.sha256, 'output_sha256': hashlib.sha256(output.encode()).hexdigest()}))
        return 0
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print('Human audit refused: ' + str(exc))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
