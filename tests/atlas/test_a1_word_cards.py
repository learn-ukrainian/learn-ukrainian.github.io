"""Five slice-2 contract tests approved in #11943 issuecomment-6536581112.

Synthetic source text exercises receipt mechanics, not Ukrainian correctness.
"""

import copy
import hashlib
import json
from collections import Counter
from pathlib import Path

import pytest

from scripts.atlas import a1_word_cards as cards
from scripts.atlas import word_card_resolver as resolver
from scripts.atlas.a1_card_receipts import Refusal, make_receipt, selected_rows

ROOT = Path(__file__).resolve().parents[2]
TARGET = "wc_6bt62wd6zzzf"
SENSE = "ws_000000000001"
OTHER_SENSE = "ws_000000000002"
VTS = "vts_busel_slovnyk_me"
ACUTE = "\u0301"
SELECTED = [
    ("a1-finale", 23, "wc_5b36dst0her6", 429081),
    ("around-the-city", 6, "wc_qpcdgkctp7ne", 425814),
    ("checkpoint-communication", 21, "wc_vq34ms5wtfev", 441799),
    ("checkpoint-places", 14, "wc_qpcdgkctp7ne", 425814),
    ("emergencies", 13, "wc_ppr39m6qsr4e", 423800),
    ("euphony", 11, "wc_qpcdgkctp7ne", 425814),
    ("food-and-drink", 28, TARGET, 436914),
    ("holidays", 18, "wc_n1g44brn5vs2", 428619),
    ("i-eat-i-drink", 31, TARGET, 436914),
    ("i-eat-i-drink", 32, TARGET, 436914),
    ("i-want-i-can", 34, "wc_08svjhdbe0fq", 428572),
    ("linking-ideas", 11, "wc_8mhjfw05sm0t", 421145),
    ("linking-ideas", 18, "wc_da7t5vpprjw3", 441309),
    ("my-city", 6, "wc_qpcdgkctp7ne", 425814),
    ("my-morning", 29, "wc_0r1cdw5z36cd", 423808),
    ("my-story", 15, "wc_5b36dst0her6", 429081),
    ("weather", 7, "wc_5btr8jkdzvd1", 442128),
    ("where-is-it", 4, "wc_qpcdgkctp7ne", 425814),
    ("where-to", 16, "wc_qpcdgkctp7ne", 425814),
]


def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")


def sha(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def mint(number, kind, identity, evidence):
    return {"event_id": f"ie_{900000 + number}", "kind": kind, "build_id": "fixture-slice2",
            "to": [identity], "evidence": encoded(evidence).decode("utf-8")}


def pinned_union(base, companion):
    """Calculate the expected literal append independently of the allocation validator."""
    effective = copy.deepcopy(base)
    for addition in companion["senses"]:
        for entry in effective["entries"]:
            if entry["card_id"] == addition["card_id"]:
                entry["senses"].append(copy.deepcopy(addition["sense"]))
        effective["events"].append(copy.deepcopy(addition["event"]))
    effective["source_records"] += copy.deepcopy(companion["source_records"])
    effective["events"] += copy.deepcopy(companion["events"])
    effective["registry_version"] += bool(companion["senses"] or companion["source_records"])
    return {"base_sha256": sha(base), "companion_sha256": sha(companion), "combined_sha256": sha(effective)}


def recipe(field, record_key="vts", pointer="/article", text="A literal definition.", sense_id=SENSE):
    claim = {"card_id": TARGET, "entry_id": 436914, "field": field, "record_key": record_key,
             "pointer": pointer, "span": [0, len(text)]}
    if sense_id is not None:
        claim.update(sense_id=sense_id, source_sense_key="fixture:sense:1", scope_key=field)
    return claim


def add_scope(manifest, claim):
    manifest["scopes"][claim["scope_key"]] = {
        "record_key": claim["record_key"], "source_sense_key": claim["source_sense_key"],
        "span": claim["span"][:], "card_id": claim["card_id"], "sense_id": claim["sense_id"],
        "pointer": claim["pointer"],
    }


@pytest.fixture
def batch():
    inventory = json.loads((ROOT / "registry/atlas/a1-v1-inventory.json").read_text())
    base = json.loads((ROOT / "registry/atlas/identity/registry.json").read_text())
    companion = {"schema_version": "atlas-a1-slice2-allocation.v1", "base_sha256": sha(base),
                 "senses": [], "source_records": [], "events": []}
    for index, sense_id in enumerate((SENSE, OTHER_SENSE), 1):
        evidence = {"card_id": TARGET, "source_id": VTS, "source_sense_key": f"fixture:sense:{index}"}
        companion["senses"].append({"card_id": TARGET, "sense": {"sense_id": sense_id, "order": index + 1,
                                                                  "state": "active"},
                                    "event": mint(index, "sense_mint", sense_id, evidence)})
    sources = {"inventory_sha256": sha(inventory), "calls": {}, "records": {}}
    literal = {
        "vts": (VTS, "query_slovnyk_me", "served_dictionary", {
            "source_entry_id": 77, "homonym": 1,
            "article": "A literal definition.\nadjacent label\nДжерело: fixture footer",
            "example": "An exact cited sentence.", "register": "formal", "synonym": "paired-term",
            "antonym": "opposite-term", "collocation": "paired phrase"}),
        "ulif": ("ulif", "query_ulif_records", "official", {"entry_id": 8077, "headword": "unit1" + ACUTE}),
        "vesum": ("vesum", "inspect_lemma", "official", {"clean_analyses": [
            {"entry_id": 436914, "word_form": "fixture-form", "tags": "noun:n:v_naz"}]}),
        "sum20": ("sum20", "query_sum20", "official", {"headword": "unit2" + ACUTE}),
        "mirror": ("sum20_slovnyk_mirror", "query_sum20", "mirror", {"headword": "unit3" + ACUTE,
                                                                 "article": "A mirror definition."}),
        "balla": ("balla", "translate_en_uk", "dictionary", {
            "direction": "en-uk", "english": "English fixture gloss", "usage_pair": "fixture-pair"}),
    }
    source_record_ids = {}
    for index, (key, (source, tool, role, payload)) in enumerate(literal.items(), 10):
        arguments = {"query": "fixture", "dictionary": source}
        sources["calls"][key] = {"tool": tool, "arguments": arguments, "response": copy.deepcopy(payload)}
        record = {"source_id": source, "snapshot_id": f"fixture:{key}:snapshot:1", "locator": f"fixture:{key}:row:77",
                  "source_url": f"https://example.invalid/{key}/77", "retrieved_at": "2026-01-01T00:00:00Z",
                  "content_sha256": sha(payload), "parser_version": "fixture-v1", "payload": payload,
                  "tool": tool, "arguments": arguments, "response_sha256": sha(payload), "call_key": key,
                  "source_role": role}
        sources["records"][key] = record
        identity = f"sr_{index:012d}"
        source_record_ids[key] = identity
        companion["source_records"].append({"source_record_id": identity, "source_id": source,
            "aliases": [{"kind": "table_row", "key": record["locator"], "snapshot_id": record["snapshot_id"]}],
            "correspondence": [{"snapshot_id": record["snapshot_id"], "status": "unique", "locator": record["locator"]}]})
        companion["events"].append(mint(index, "source_record_mint", identity,
            {"source_id": source, "snapshot_id": record["snapshot_id"], "locator": record["locator"]}))
    card_ids = sorted({card for _, _, card, _ in SELECTED})
    definition = recipe("definition_uk")
    form = recipe("paradigm", "vesum", "/clean_analyses/0/word_form", "fixture-form", None)
    form["slot"] = "noun:n:v_naz"
    stress = recipe("stress", "ulif", "/headword", "unit1" + ACUTE, None)
    manifest = {"card_ids": card_ids, "denominator": {"all_rows": 2144, "selected_rows": 19},
        "inventory_sha256": sha(inventory), "sources_sha256": sha(sources), "claims": [definition, form],
        "stress_attempts": {card: [{"source_id": source, "state": "not_found"} for source in
                                    ("ulif", "sum20", VTS)] for card in card_ids},
        "scopes": {}, "example_approvals": {}, "field_residuals": {}, "field_dependencies": {},
        "held_units": [], "source_record_ids": source_record_ids}
    manifest["stress_attempts"][TARGET][0].update(state="supported", claim=stress)
    add_scope(manifest, definition)
    pins = pinned_union(base, companion)
    manifest["allocation_pins"] = pins
    register = {"schema_version": 2, "sources": [{"id": source, "appears_in": ["internal"]}
                for source in sorted({record["source_id"] for record in sources["records"].values()})]}
    return {"inventory": inventory, "base": base, "companion": companion, "manifest": manifest,
            "sources": sources, "pins": pins, "register": register}


def assemble(batch):
    return cards.build(**batch)


def target(result):
    return next(card for card in result["cards"] if card["card_id"] == TARGET)


def account(result, field, sense_id=None, card_id=TARGET):
    return next(row for row in result["accounting"] if
                (row["card_id"], row["sense_id"], row["field"]) == (card_id, sense_id, field))


def values(result, field, sense_id=None):
    return [a["value"] for a in target(result)["assertions"]
            if a["field"] == field and a["subject"]["id"] == (sense_id or TARGET)]


def refresh(batch, key):
    record = batch["sources"]["records"][key]
    batch["sources"]["calls"][record["call_key"]]["response"] = copy.deepcopy(record["payload"])
    record["response_sha256"] = sha(record["payload"])
    record["content_sha256"] = sha(record["payload"])
    batch["manifest"]["sources_sha256"] = sha(batch["sources"])


def set_stress(batch, source, text):
    key = "vts" if source == VTS else source
    batch["sources"]["records"][key]["payload"]["headword"] = text
    refresh(batch, key)
    claim = recipe("stress", key, "/headword", text, None)
    for attempt in batch["manifest"]["stress_attempts"][TARGET]:
        attempt["state"] = "supported" if attempt["source_id"] == source else "not_found"
        if attempt["source_id"] == source:
            attempt["claim"] = claim
    return claim


def example_claim(batch):
    claim = recipe("examples", pointer="/example", text="An exact cited sentence.")
    batch["manifest"]["claims"].append(claim)
    add_scope(batch["manifest"], claim)
    return claim


def approve_example(batch, claim):
    receipt = make_receipt(claim["record_key"], batch["sources"]["records"][claim["record_key"]],
                           claim["pointer"], claim["span"], claim["entry_id"], claim["source_sense_key"])
    batch["manifest"]["example_approvals"][receipt["receipt_id"]] = {
        "receipt_sha256": sha(receipt), "entry_id": 436914, "sense_id": SENSE,
        "reviewer_family": "google", "verdict": "APPROVE", "record": "fixture-independent-review",
        "quotation": "An exact cited sentence.", "span": claim["span"][:],
        "source_sense_key": "fixture:sense:1", "sources_sha256": sha(batch["sources"])}


def test_reconciles_frozen_rows_and_preserves_pilot_identities(batch):
    """Catch dropped occurrences, reminted identities and self-authenticating allocation swaps."""
    protected = ["registry/atlas/a1-v1-inventory.json", "registry/atlas/identity/registry.json",
                 "registry/atlas/pilot/pilot-v1.json", "registry/atlas/pilot/pilot-v1.register-pin.json",
                 "registry/atlas/pilot/batch1_manifest.json"]
    before = {path: (ROOT / path).read_bytes() for path in protected}
    frozen_inputs = encoded(batch)
    selected = selected_rows(batch["inventory"])
    assert [(row["id"], row["mapping"]["pilot"]["card_id"], row["mapping"]["entry_id"]) for row in selected] == [
        (f"curriculum/l2-uk-en/a1-v1/{lesson}/vocabulary.yaml#/{index}", card, entry)
        for lesson, index, card, entry in SELECTED]
    result = assemble(batch)
    assert Counter(row["state"] for row in result["rows"]) == {"card_produced": 19, "deferred_outside_slice2": 2125}
    assert len(result["rows"]) == len({row["inventory_row_id"] for row in result["rows"]}) == 2144
    assert len(result["cards"]) == 11
    assert sorted(card["card_id"] for card in result["cards"]) == sorted({card for _, _, card, _ in SELECTED})
    assert [row["mapping"] for row in result["rows"]] == [row["mapping"] for row in batch["inventory"]["rows"]]
    assert [row["inventory_row_id"] for row in result["rows"] if row["card_id"] == TARGET] == [
        "curriculum/l2-uk-en/a1-v1/food-and-drink/vocabulary.yaml#/28",
        "curriculum/l2-uk-en/a1-v1/i-eat-i-drink/vocabulary.yaml#/31",
        "curriculum/l2-uk-en/a1-v1/i-eat-i-drink/vocabulary.yaml#/32"]
    original = {entry["card_id"]: entry for entry in batch["base"]["entries"]}
    for card in result["cards"]:
        prior = original[card["card_id"]]
        assert card["key_at_creation"] == prior["key_at_creation"]
        assert [sense["sense_id"] for sense in card["senses"]][:len(prior["senses"])] == [
            sense["sense_id"] for sense in prior["senses"]]
    assert values(result, "definition_uk", SENSE) == ["A literal definition."]
    assert account(result, "mwe_form")["state"] == "not_applicable"
    for kind in ("sense", "record", "alias", "snapshot", "event", "missing_event", "duplicate_event",
                 "coherent_sense", "coherent_record"):
        bad = copy.deepcopy(batch)
        companion = bad["companion"]
        if kind == "sense":
            companion["senses"][0]["sense"]["sense_id"], companion["senses"][1]["sense"]["sense_id"] = OTHER_SENSE, SENSE
        elif kind == "record":
            companion["source_records"][0]["source_record_id"] = companion["source_records"][1]["source_record_id"]
        elif kind == "alias":
            companion["source_records"][0]["aliases"][0]["key"] = "fixture:substitute"
        elif kind == "snapshot":
            companion["source_records"][0]["correspondence"][0]["snapshot_id"] = "substitute-snapshot"
        elif kind == "event":
            companion["senses"][0]["event"]["evidence"] = encoded({"card_id": TARGET,
                "source_id": VTS, "source_sense_key": "fixture:sense:2"}).decode()
        elif kind == "missing_event":
            companion["events"].pop()
        elif kind == "duplicate_event":
            companion["events"].append(copy.deepcopy(companion["events"][0]))
        elif kind == "coherent_sense":
            for addition, identity in zip(companion["senses"], (OTHER_SENSE, SENSE), strict=True):
                addition["sense"]["sense_id"] = identity
                addition["event"]["to"] = [identity]
        else:
            first, second = companion["source_records"][:2]
            first["source_record_id"], second["source_record_id"] = second["source_record_id"], first["source_record_id"]
            companion["events"][0]["to"] = [first["source_record_id"]]
            companion["events"][1]["to"] = [second["source_record_id"]]
        bad["pins"]["companion_sha256"] = sha(companion)
        with pytest.raises(Refusal, match="combined_digest_mismatch" if kind.startswith("coherent") else None):
            assemble(bad)
    assert encoded(batch) == frozen_inputs
    assert {path: (ROOT / path).read_bytes() for path in protected} == before


def test_rejects_wrong_lexeme_sense_span_and_source_role(batch):
    """Catch cross-lexeme/sense receipts, overwide definitions, footer capture and false official attribution."""
    valid = assemble(batch)
    assert values(valid, "definition_uk", SENSE) == ["A literal definition."]
    assert account(valid, "definition_uk", OTHER_SENSE)["state"] == "empty"
    assert account(valid, "definition_uk", OTHER_SENSE)["reason"] == "source_sense_claim_unresolved"
    for kind, reason in (("lexeme", "claim_lexeme_mismatch"), ("sense", "scope_subject_mismatch"),
                         ("adjacent", "outside_sense_span"), ("whole_article", "outside_sense_span"),
                         ("hash", "source_snapshot_drift"), ("footer", "dictionary_footer")):
        bad = copy.deepcopy(batch)
        claim = bad["manifest"]["claims"][0]
        if kind == "lexeme":
            claim["entry_id"] = 425814
        elif kind == "sense":
            claim["sense_id"] = OTHER_SENSE
        elif kind == "adjacent":
            claim["span"] = [22, 36]
        elif kind == "whole_article":
            claim["span"][1] = len(bad["sources"]["records"]["vts"]["payload"]["article"])
        elif kind == "hash":
            bad["sources"]["records"]["vts"]["content_sha256"] = "f" * 64
        else:
            claim["span"] = [37, len(bad["sources"]["records"]["vts"]["payload"]["article"])]
            bad["manifest"]["scopes"]["definition_uk"]["span"] = claim["span"][:]
        with pytest.raises(Refusal, match=reason):
            assemble(bad)
    mirror = copy.deepcopy(batch)
    claim = mirror["manifest"]["claims"][0]
    claim.update(record_key="mirror", span=[0, 20])
    add_scope(mirror["manifest"], claim)
    mirror_result = assemble(mirror)
    assert values(mirror_result, "definition_uk", SENSE) == ["A mirror definition."]
    assert next(a for a in target(mirror_result)["assertions"] if a["field"] == "definition_uk")["source_id"] == "sum20_slovnyk_mirror"
    mirror["sources"]["records"]["mirror"]["source_role"] = "official"
    mirror["manifest"]["sources_sha256"] = sha(mirror["sources"])
    with pytest.raises(Refusal):
        assemble(mirror)
    for kind in ("entry", "sense", "value", "receipt_subject"):
        altered = copy.deepcopy(valid)
        assertion = next(a for a in target(altered)["assertions"] if a["field"] == "definition_uk")
        rid = altered["assertion_receipts"][assertion["assertion_id"]][0]
        receipt = next(r for r in altered["receipts"] if r["receipt_id"] == rid)
        if kind == "value":
            assertion["value"] = "A substituted displayed definition."
        elif kind == "receipt_subject":
            assertion["subject"]["id"] = OTHER_SENSE
        else:
            receipt["entry_id" if kind == "entry" else "sense_key"] = 425814 if kind == "entry" else "fixture:sense:2"
            receipt["receipt_id"] = "wr_" + sha({key: value for key, value in receipt.items() if key != "receipt_id"})
            altered["assertion_receipts"][assertion["assertion_id"]] = [receipt["receipt_id"]]
        target(altered)["build"]["card_version"] = resolver.card_version(target(altered))
        with pytest.raises(Refusal):
            cards.verify(altered, batch["sources"], batch["manifest"])


def test_stress_fallback_and_forms_require_independent_receipts(batch):
    """Catch skipped stress authorities, discarded doublets and foreign-entry or unreceipted accented forms."""
    for source, text in (("ulif", "unit1" + ACUTE), ("sum20", "unit2" + ACUTE), (VTS, "unit3" + ACUTE)):
        case = copy.deepcopy(batch)
        chosen = set_stress(case, source, text)
        result = assemble(case)
        assert values(result, "stress") == [text]
        assert values(result, "paradigm") == [{"slot": "noun:n:v_naz", "forms": ["fixture-form"],
                                                "entry_id": 436914, "tags": "noun:n:v_naz"}]
        receipt = next(r for r in result["receipts"] if r["quotation"] == text)
        assert receipt["source_id"] == source
        assert receipt["span"] == [0, len(text)]
        assert cards.choose_stress(case["manifest"]["stress_attempts"][TARGET]) == (chosen, None)
    precedence = copy.deepcopy(batch)
    attempts = precedence["manifest"]["stress_attempts"][TARGET]
    attempts[1].update(state="supported", claim={"sentinel": "lower authority"})
    assert values(assemble(precedence), "stress") == ["unit1" + ACUTE]
    variants = copy.deepcopy(batch)
    set_stress(variants, "ulif", "unit1" + ACUTE + "unit2" + ACUTE)
    assert values(assemble(variants), "stress") == [["unit1" + ACUTE + "unit2", "unit1unit2" + ACUTE]]
    for state in ("ambiguous", "conflict"):
        case = copy.deepcopy(batch)
        set_stress(case, VTS, "unit3" + ACUTE)
        case["manifest"]["stress_attempts"][TARGET][0]["state"] = state
        result = assemble(case)
        assert values(result, "stress") == []
        assert (account(result, "stress")["state"], account(result, "stress")["reason"]) == (
            "empty", "higher_priority_stress_" + state)
    for kind, reason in (("entry", "form_entry_mismatch"), ("slot", "form_slot_mismatch"),
                         ("accent", "accented_form_requires_stress")):
        case = copy.deepcopy(batch)
        analysis = case["sources"]["records"]["vesum"]["payload"]["clean_analyses"][0]
        if kind == "entry":
            analysis["entry_id"] = 425814
        elif kind == "slot":
            case["manifest"]["claims"][1]["slot"] = "noun:n:v_rod"
        else:
            analysis["word_form"] = "form1" + ACUTE
            case["manifest"]["claims"][1]["span"] = [0, len(analysis["word_form"])]
        refresh(case, "vesum")
        with pytest.raises(Refusal, match=reason):
            assemble(case)
    accented = copy.deepcopy(batch)
    accented["sources"]["records"]["vesum"]["payload"]["clean_analyses"][0]["word_form"] = "form1" + ACUTE
    accented["manifest"]["claims"][1].update(span=[0, 6], stress_receipt="wr_" + "0" * 64)
    refresh(accented, "vesum")
    with pytest.raises(Refusal):
        assemble(accented)
    supported = copy.deepcopy(batch)
    stress_claim = set_stress(supported, "ulif", "form1" + ACUTE)
    stress_receipt = make_receipt("ulif", supported["sources"]["records"]["ulif"], "/headword", [0, 6], 436914)
    supported["sources"]["records"]["vesum"]["payload"]["clean_analyses"][0]["word_form"] = "form1" + ACUTE
    supported["manifest"]["claims"][1].update(span=[0, 6], stress_receipt=stress_receipt["receipt_id"])
    refresh(supported, "vesum")
    result = assemble(supported)
    assert values(result, "paradigm") == [{"slot": "noun:n:v_naz", "forms": ["form1" + ACUTE],
                                           "entry_id": 436914, "tags": "noun:n:v_naz"}]
    assert values(result, "stress") == ["form1" + ACUTE]
    form_receipts = account(result, "paradigm")["receipt_ids"]
    stress_receipts = account(result, "stress")["receipt_ids"]
    assert stress_receipts == [stress_receipt["receipt_id"]]
    assert len(form_receipts) == 1 and form_receipts[0] != stress_receipts[0]
    assert cards.choose_stress(supported["manifest"]["stress_attempts"][TARGET]) == (stress_claim, None)
    delivered = assemble(batch)
    assertion = next(a for a in target(delivered)["assertions"] if a["field"] == "paradigm")
    assertion["value"]["forms"] = ["foreign-form"]
    target(delivered)["build"]["card_version"] = resolver.card_version(target(delivered))
    with pytest.raises(Refusal):
        cards.verify(delivered, batch["sources"], batch["manifest"])


def test_unreviewed_examples_and_unaligned_rich_fields_stay_empty(batch):
    """Catch suitability bypass, rewritten examples, cross-sense rich fields and reversed bilingual matches."""
    claim = example_claim(batch)
    batch["manifest"]["field_residuals"]["examples"] = "independent_a1_review_pending"
    rich = {"register": ("/register", "formal"), "synonyms": ("/synonym", "paired-term"),
            "antonyms": ("/antonym", "opposite-term"), "collocations": ("/collocation", "paired phrase"),
            "gloss_en": ("/english", "English fixture gloss")}
    for field in rich:
        batch["manifest"]["field_residuals"][field] = "source_sense_alignment_unresolved"
        batch["manifest"]["field_dependencies"][field] = "reviewed correspondence for fixture:sense:1"
    pending = assemble(batch)
    assert values(pending, "examples", SENSE) == []
    assert pending["pending_examples"][0]["receipt"]["quotation"] == "An exact cited sentence."
    assert account(pending, "examples", SENSE)["reason"] == "independent_a1_review_pending"
    for field in rich:
        residual = account(pending, field, SENSE)
        assert (residual["state"], residual["reason"], residual["dependency"], residual["owner"]) == (
            "empty", "source_sense_alignment_unresolved", "reviewed correspondence for fixture:sense:1", "Atlas coordinator")
        assert values(pending, field, SENSE) == []
    approve_example(batch, claim)
    approved = assemble(batch)
    assert values(approved, "examples", SENSE) == ["An exact cited sentence."]
    assert account(approved, "examples", SENSE)["state"] == "supported"
    for kind in ("wrong_sense", "wrong_digest", "wrong_reviewer"):
        bad = copy.deepcopy(batch)
        approval = next(iter(bad["manifest"]["example_approvals"].values()))
        approval[{"wrong_sense": "sense_id", "wrong_digest": "receipt_sha256", "wrong_reviewer": "reviewer_family"}[kind]] = {
            "wrong_sense": OTHER_SENSE, "wrong_digest": "f" * 64, "wrong_reviewer": "openai"}[kind]
        with pytest.raises(Refusal, match="example_review_binding_mismatch"):
            assemble(bad)
    rewritten = copy.deepcopy(batch)
    rewritten["sources"]["records"]["vts"]["payload"]["example"] = "An invented replacement."
    refresh(rewritten, "vts")
    assert values(assemble(rewritten), "examples", SENSE) == []
    aligned = copy.deepcopy(batch)
    for field, (pointer, literal) in rich.items():
        candidate = recipe(field, "balla" if field == "gloss_en" else "vts", pointer, literal)
        if field == "gloss_en":
            candidate.update(translation_direction="en-uk", usage_pair="fixture-pair")
        aligned["manifest"]["claims"].append(candidate)
        add_scope(aligned["manifest"], candidate)
    accepted = assemble(aligned)
    for field, (_, literal) in rich.items():
        assert values(accepted, field, SENSE) == [literal]
        assert account(accepted, field, SENSE)["state"] == "supported"
    wrong_sense = copy.deepcopy(aligned)
    wrong_sense["manifest"]["claims"][-1]["sense_id"] = OTHER_SENSE
    with pytest.raises(Refusal, match="scope_subject_mismatch"):
        assemble(wrong_sense)
    reversed_pair = copy.deepcopy(aligned)
    reversed_pair["manifest"]["claims"][-1]["translation_direction"] = "uk-en"
    with pytest.raises(Refusal):
        assemble(reversed_pair)


def test_replay_is_deterministic_and_refuses_input_drift(batch, tmp_path, monkeypatch, capsys):
    """Catch nondeterministic output, source writes and accepted partial output after snapshot drift."""
    fixture_root = tmp_path / "inputs"
    paths = {cards.MANIFEST: batch["manifest"], cards.COMPANION: batch["companion"],
             "registry/atlas/a1-v1-inventory.json": batch["inventory"],
             "registry/atlas/identity/registry.json": batch["base"],
             "docs/sources/permissions-register.yaml": batch["register"], "sources.json": batch["sources"]}
    for relative, content in paths.items():
        path = fixture_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(encoded(content) + b"\n")
    before = {relative: (fixture_root / relative).read_bytes() for relative in paths}
    monkeypatch.setattr(cards, "ROOT", fixture_root)
    monkeypatch.setattr(cards, "MANIFEST_SHA256", sha(batch["manifest"]))
    source_path = fixture_root / "sources.json"
    first, second, rejected = (tmp_path / name for name in ("first.json", "second.json", "rejected.json"))
    for output in (first, second):
        assert cards.main(["--sources", str(source_path), "--output", str(output)]) == 0
        counts = json.loads(capsys.readouterr().out)
        assert (counts["cards"], counts["rows"]) == (11, 2144)
    assert first.read_bytes() == second.read_bytes()
    assert values(json.loads(first.read_bytes()), "definition_uk", SENSE) == ["A literal definition."]
    assert cards.main(["--sources", str(source_path), "--output", str(first), "--check"]) == 0
    capsys.readouterr()
    assert {relative: (fixture_root / relative).read_bytes() for relative in paths} == before
    changed = copy.deepcopy(batch["sources"])
    changed["records"]["vts"]["payload"]["article"] = "Changed consumed bytes."
    source_path.write_bytes(encoded(changed) + b"\n")
    source_after_drift = source_path.read_bytes()
    accepted_before = first.read_bytes()
    for output in (rejected, first):
        assert cards.main(["--sources", str(source_path), "--output", str(output)]) == 1
        assert "source_snapshot_drift" in capsys.readouterr().err
    assert not rejected.exists()
    assert first.read_bytes() == accepted_before
    assert source_path.read_bytes() == source_after_drift
    assert {relative: (fixture_root / relative).read_bytes() for relative in paths if relative != "sources.json"} == {
        relative: content for relative, content in before.items() if relative != "sources.json"}
