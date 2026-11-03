"""Synthetic Phase 5 mechanics. These fixtures never certify Ukrainian or real cards."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from scripts.atlas import word_card_certification as cert
from scripts.atlas import word_card_golden_set as gold
from tests.test_word_card_golden_set import write
from tests.word_card_certification_fixtures import CertificationFixture, certification_fixture  # noqa: F401


@pytest.fixture
def packet(tmp_path, certification):
    root = tmp_path / "phase5"
    root.mkdir()
    return CertificationFixture(root, certification)


def _native50_engine_shape(tmp_path):
    """Parser controls only: no task approval, live authority, or cohort certification."""
    frozen = {key: "a" * 64 for key in ("implementation_sha256", "rules_sha256", "inputs_sha256")}
    spec = {"frozen": frozen,
            "original50_selection": {"path": "ENGINE", "sha256": cert.ORIGINAL50_SELECTION_SHA256},
            "original50_input": {"path": "ENGINE", "sha256": cert.ORIGINAL50_INPUT_SHA256}}
    population = {"original50": [{"card_id": f"ENGINE-{i}", "card_version": "ENGINE-v1",
        "current_version_matches": True, "assertions": [],
        "card": {"key_at_creation": {"spelling": "ENGINE"}}} for i in range(50)]}
    actor = {"task_id": "ENGINE-AUTHOR", "run_nonce": "b" * 32, "model": "gpt-6.1-sol", "family": "openai"}
    record = tmp_path / "engine-freeze.txt"
    record.write_text("ENGINE-FREEZER gpt-6.1-sol")
    freezer = {"identity": "ENGINE-FREEZER", "model": "gpt-6.1-sol", "task": None,
               "identity_span": [0, 14], "model_identity_span": [0, 14], "model_span": [15, 26],
               "record": {"path": str(record), "sha256": gold.sha(record.read_bytes())},
               "model_record": {"path": str(record), "sha256": gold.sha(record.read_bytes())}}
    opaque = {"path": "ENGINE", "sha256": "c" * 64}
    inspection = {"schema_version": "a1-original50-inspection.v1", "frozen": frozen,
        "selection_sha256": cert.ORIGINAL50_SELECTION_SHA256, "input_sha256": cert.ORIGINAL50_INPUT_SHA256,
        "scope_sha256": cert.digest({"frozen": frozen, "original50": population["original50"]}),
        "authors": [actor], "freezer": freezer, "producer": {**actor, "task_id": "ENGINE-PRODUCER", "family": "google"},
        "transcript": opaque, "result": opaque}
    return inspection, population, spec


def test_native_original50_membership_version_and_source_drift_refuse(tmp_path):
    """Granted native50 class A: the real adapter's exact scope never shrinks."""
    inspection, population, spec = _native50_engine_shape(tmp_path)
    assert cert._native50_scope(inspection, population, spec) == inspection["scope_sha256"]
    for fault in ("membership", "version", "source"):
        changed = copy.deepcopy(population)
        if fault == "membership":
            changed["original50"].pop()
        elif fault == "version":
            changed["original50"][0]["card_version"] = "ENGINE-v2"
        else:
            changed["original50"][0]["assertions"] = [{"source_changed": True}]
        with pytest.raises(ValueError, match="original50_membership_version_or_source_changed"):
            cert._native50_scope(inspection, changed, spec)


def test_native_original50_untrusted_identity_freezer_and_per_card_sources_refuse(tmp_path, monkeypatch):
    """Granted class B: no accepted human/model evidence is created by these controls."""
    from scripts.review import record_cf_verdict as reviews

    inspection, _, _ = _native50_engine_shape(tmp_path)
    producer = inspection["producer"]
    task_root = tmp_path / "tasks"
    task_root.mkdir()
    reply = b'ENGINE_FIXTURE_NOT_HUMAN_APPROVAL'
    (task_root / (producer["task_id"] + ".result")).write_bytes(reply)
    task = {"status": "done", "review_branch": "engine-control", "agent": "codex", "model": "gpt-6.1-sol",
        "resolved_model": "gpt-6.1-sol", "resolved_model_known": True, "resolved_model_source": "codex-stream-json",
        "repository": "learn-ukrainian/learn-ukrainian.github.io", "run_nonce": producer["run_nonce"],
        "result_sha256": gold.sha(reply), "returncode": 0, "error": None}
    for fault in ("unfinished", "nonce", "model-family"):
        bad = {**task, **({"status": "cancelled"} if fault == "unfinished" else
                         {"run_nonce": "d" * 32} if fault == "nonce" else {})}
        (task_root / (producer["task_id"] + ".json")).write_text(json.dumps(bad))
        reason = {"unfinished": "review task is not done", "nonce": "original50_task_identity_mismatch",
                  "model-family": "original50_actor_model_mismatch"}[fault]
        with pytest.raises((ValueError, reviews.RecordError), match=reason):
            cert._native_task(producer, task_root)
    freezer = inspection["freezer"]
    # The corrected criterion allows the same model family, with a different traced identity.
    cert._native50_freezer(freezer, inspection["authors"], producer, tmp_path)
    for identity in (inspection["authors"][0]["task_id"], producer["task_id"], "UNTRACEABLE"):
        changed = {**freezer, "identity": identity}
        if identity != "UNTRACEABLE":
            record = tmp_path / "same-task.txt"
            record.write_text(identity + " " + freezer["model"])
            changed.update(record={"path": str(record), "sha256": gold.sha(record.read_bytes())},
                           model_record={"path": str(record), "sha256": gold.sha(record.read_bytes())},
                           identity_span=[0, len(identity)], model_identity_span=[0, len(identity)],
                           model_span=[len(identity) + 1, len(record.read_text())])
        with pytest.raises(ValueError, match="original50_freezer"):
            cert._native50_freezer(changed, inspection["authors"], producer, tmp_path)
    score = {"reason": "ENGINE only", "calls": [{"conversation_id": "ENGINE", "step_index": 1,
        "quote": "ENGINE", "span": [0, 6]}]}
    call = {"parameters": {"ToolName": "query_sum20", "Arguments": {"word": "ENGINE"}}, "output": "ENGINE capture"}
    for facet in ("meaning", "stress"):
        for fault in ("absent", "wrong-card", "missing-body", "wrong-quote"):
            altered = copy.deepcopy(call)
            if fault == "wrong-card":
                altered["parameters"]["Arguments"]["word"] = "OTHER"
            elif fault == "missing-body":
                altered["output"] = ""
            elif fault == "wrong-quote":
                altered["output"] = "OTHER capture"
            with pytest.raises(ValueError, match=r"original50_(per_card_sources_missing|source_quote_unsupported)"):
                cert._native50_sources(score, facet, "ENGINE", {} if fault == "absent" else {("ENGINE", 1): altered})
    # A complete engine protocol exercises the real custody/parser boundary.
    # These temporary records cannot enter evaluate_certification's real A1 path.
    from types import SimpleNamespace

    primary = tmp_path / "engine-primary"
    task_root = primary / "batch_state/tasks"
    (task_root / "logs").mkdir(parents=True)
    monkeypatch.setattr(reviews, "_review_repository_root", lambda *_args: primary)
    inspection, population, spec = _native50_engine_shape(tmp_path)
    producer = inspection["producer"]
    producer.update(model="gemini-3.8-flash-high", family="google")
    judgments = {"schema_version": "a1-original50-judgments.v1", "scope_sha256": inspection["scope_sha256"], "items": []}
    events = [{"event": "init", "init": {"model": producer["model"]}}]
    for index, card in enumerate(population["original50"]):
        row = {"card_id": card["card_id"], "card_version": card["card_version"]}
        for offset, facet in enumerate(("meaning", "stress")):
            step = index * 2 + offset
            row[facet] = {"verdict": "pass", "reason": "ENGINE_FIXTURE_NOT_HUMAN_APPROVAL", "findings": [],
                "calls": [{"conversation_id": "ENGINE", "step_index": step, "quote": "ENGINE", "span": [0, 6]}]}
            events.append({"event": "step_update", "step_update": {"conversation_id": "ENGINE", "state": "DONE",
                "step_index": step, "tool_name": "call_mcp_tool", "tool_info": {
                    "parameters": {"ServerName": "sources", "ToolName": "query_sum20", "Arguments": {"word": "ENGINE"}},
                    "output": "ENGINE source capture"}}})
        judgments["items"].append(row)
    text = json.dumps(judgments)
    events.append({"event": "result", "result": {"status": "SUCCESS", "response": text}})
    transcript = task_root / "logs" / (producer["task_id"] + ".stdout.log")
    transcript.write_text("\n".join(json.dumps(event) for event in events) + "\n")
    for actor in [*inspection["authors"], producer]:
        output = text.encode() if actor is producer else reply
        (task_root / (actor["task_id"] + ".result")).write_bytes(output)
        record = {**task, "run_nonce": actor["run_nonce"], "model": actor["model"], "resolved_model": actor["model"],
            "agent": "agy" if actor is producer else "codex", "result_sha256": gold.sha(output),
            "resolved_model_source": "agy-stream-json" if actor is producer else "codex-stream-json",
            "review_profile": "ukrainian", "sources_mcp_call_count": 100}
        (task_root / (actor["task_id"] + ".json")).write_text(json.dumps(record))
    result = task_root / (producer["task_id"] + ".result")
    inspection.update(transcript={"path": str(transcript), "sha256": gold.sha(transcript.read_bytes())},
                      result={"path": str(result), "sha256": gold.sha(result.read_bytes())})
    spec["original50_receipt"] = {"path": "ENGINE_INSPECTION", "sha256": cert.digest(inspection)}
    authority = SimpleNamespace(reviews={c["card_id"]: {"status": "active", "card_version": c["card_version"],
        "record": "ENGINE_FIXTURE_NOT_HUMAN_APPROVAL", "original50_inspection": spec["original50_receipt"],
        "original50_authors": inspection["authors"], "original50_freezer": inspection["freezer"]}
        for c in population["original50"]})
    assert cert._verify_native50(inspection, population, spec, tmp_path, authority) == [
        {"id": inspection["authors"][0]["task_id"], "family": "openai"}]
    broken = copy.deepcopy(inspection)
    broken["transcript"]["sha256"] = "0" * 64
    with pytest.raises(ValueError):
        cert._verify_native50(broken, population, spec, tmp_path, authority)


def test_exact_receipt_and_export(packet):
    result = packet.evaluate()
    assert result["status"] == "CERTIFIED"
    assert result["case_count"] == 1
    assert result["strata"] == {"ordinary-control": 1}
    assert result["scores"] == {facet: {"passed": 2, "denominator": 2} for facet in cert.FACETS}
    assert result["controls"] == {name: {"detected": 2, "denominator": 2} for name in cert.CONTROL_FACETS}
    assert result["findings"] == []
    assert cert.verify_certification_receipt(packet.receipt(), packet.root) == result
    packet.approve()
    assert cert.load_certified_card_for_export(packet.card) == packet.card


def test_receipt_paths_replay_from_another_root(packet, tmp_path):
    reports = packet.root / "reports"
    reports.mkdir()
    packet.evaluation_path = reports / "evaluation.json"
    packet.save_evaluation()
    receipt = packet.evaluate()
    assert receipt["spec"] == {"path": "certification-spec.json", "sha256": packet.spec_sha}
    assert receipt["evaluation"] == {"path": "reports/evaluation.json", "sha256": packet.evaluation_sha}

    relocated = tmp_path / "relocated"
    (relocated / "reports").mkdir(parents=True)
    spec_path = relocated / packet.spec_path.name
    evaluation_path = relocated / "reports/evaluation.json"
    spec_path.write_bytes(packet.spec_path.read_bytes())
    evaluation_path.write_bytes(packet.evaluation_path.read_bytes())
    replay = cert.evaluate_certification(spec_path, packet.spec_sha, evaluation_path, packet.evaluation_sha)
    assert gold.canonical(replay) == gold.canonical(receipt)
    ref = write(relocated / "receipt.json", receipt)
    ref["path"] = "relocated/receipt.json"
    assert cert.verify_certification_receipt(ref, tmp_path) == receipt
    assert cert.certification_summary(ref, tmp_path)["status"] == "CERTIFIED"


@pytest.mark.parametrize("reader", [cert.verify_certification_receipt, cert.certification_summary])
@pytest.mark.parametrize("receipt", [None, [], {}, {"schema_version": "unknown"},
                                    {"schema_version": "word-card-certification-receipt.v1",
                                     "status": "CERTIFIED"}])
def test_malformed_receipt_envelope_is_typed_refusal(tmp_path, reader, receipt):
    ref = write(tmp_path / "receipt.json", receipt)
    with pytest.raises(cert.UncertifiedCardRefusal, match="Invalid exact-artifact receipt"):
        reader(ref, tmp_path)


@pytest.mark.parametrize("gate", ["complete_data_receipt", "mechanics_receipt", "gold_spec", "gold_seal", "isolation"])
def test_missing_prerequisite_refused(packet, gate):
    Path(packet.spec[gate]["path"]).unlink()
    with pytest.raises((ValueError, OSError)):
        packet.evaluate()


@pytest.mark.parametrize("gate", ["complete_data_receipt", "mechanics_receipt", "gold_spec", "gold_seal", "isolation"])
def test_pinned_prerequisite_drift_refused(packet, gate):
    Path(packet.spec[gate]["path"]).chmod(0o600)
    Path(packet.spec[gate]["path"]).write_bytes(b"{}")
    with pytest.raises(ValueError):
        packet.evaluate()


@pytest.mark.parametrize("fault", ["self", "same-family", "duplicate", "qualification", "one-family"])
def test_independent_qualified_evaluators_required(packet, fault):
    actors = packet.spec["evaluators"]
    if fault == "self":
        actors[0]["id"] = "code-author"
    elif fault == "same-family":
        actors[0]["family"] = "author-family"
    elif fault == "duplicate":
        actors[1]["id"] = actors[0]["id"]
    elif fault == "one-family":
        actors[1]["family"] = actors[0]["family"]
    else:
        actors[0]["qualification"]["sha256"] = "b" * 64
    packet.save_spec()
    with pytest.raises(ValueError):
        packet.evaluate()


@pytest.mark.parametrize("facet", cert.FACETS)
def test_each_semantic_facet_can_block_with_owned_findings(packet, facet):
    score = next(item for item in packet.evaluation["reports"][0]["items"][0]["scores"] if item["facet"] == facet)
    score.update(verdict="fail", findings=[{"code": "invented_ukrainian" if facet == "source_fidelity" else "material",
                                           "owner": "source-owner", "dependency": "new authenticated source evidence",
                                           "evidence": packet.gold.opaque}])
    packet.save_evaluation()
    result = packet.evaluate()
    assert result["status"] == "FAILED"
    assert result["scores"][facet] == {"passed": 1, "denominator": 2}
    assert result["findings"][0]["findings"][0]["owner"] == "source-owner"
    with pytest.raises(ValueError, match="Failed or stale"):
        cert.verify_certification_receipt(packet.receipt(), packet.root)


@pytest.mark.parametrize("name", cert.CONTROL_FACETS)
def test_missed_control_blocks_even_when_literal_comparator_detects_it(packet, name):
    index = next(i + 1 for i, row in enumerate(packet.spec["controls"]) if row["class"] == name)
    facet = cert.CONTROL_FACETS[name]
    score = next(row for row in packet.evaluation["reports"][0]["items"][index]["scores"] if row["facet"] == facet)
    score.update(verdict="pass", findings=[])
    packet.save_evaluation()
    result = packet.evaluate()
    assert result["status"] == "FAILED"
    assert result["controls"][name] == {"detected": 1, "denominator": 2}
    assert result["findings"][0]["findings"][0]["dependency"] == "repair missed planted control"


@pytest.mark.parametrize("fault", ["implementation", "rules", "parser", "source", "overlay", "suppression",
                                 "permissions", "gold", "evaluation", "card", "receipt", "spec"])
def test_exact_artifact_changes_invalidate_receipt(packet, fault, monkeypatch):
    ref = packet.receipt()
    if fault in {"implementation", "parser"}:
        packet.authority.code.write_text("changed parser or implementation")
    elif fault == "rules":
        packet.authority.rules.write_text("changed rules")
    elif fault == "permissions":
        packet.authority.register.write_text("changed register")
    elif fault in {"source", "overlay", "suppression"}:
        category, name = {"source": ("S", "source"), "overlay": ("O", "overlay"),
                          "suppression": ("O", "suppressions")}[fault]
        packet.authority.snapshots[category, name].write_text("changed input")
    elif fault == "gold":
        path = packet.gold.bundle / "answers.json"
        path.chmod(0o600)
        path.write_bytes(b"{}")
    else:
        path = {"evaluation": packet.evaluation_path, "card": packet.card_path,
                "receipt": Path(ref["path"]), "spec": packet.spec_path}[fault]
        path.write_bytes(b"{}")
    with pytest.raises((ValueError, KeyError)):
        cert.verify_certification_receipt(ref, packet.root)


@pytest.mark.parametrize("fault", ["case", "item", "evaluator", "facet", "claim", "card-hash", "spec-hash", "inspection",
                                 "owner", "hidden-finding"])
def test_denominator_and_evidence_omissions_refused(packet, fault):
    report = packet.evaluation["reports"][0]
    score = report["items"][0]["scores"][0]
    if fault == "case":
        packet.spec["cases"].clear()
        packet.save_spec()
    elif fault == "item":
        report["items"].pop()
    elif fault == "evaluator":
        packet.evaluation["reports"].pop()
    elif fault == "facet":
        report["items"][0]["scores"].pop()
    elif fault == "claim":
        score["source_claims_sha256"] = "b" * 64
    elif fault == "card-hash":
        report["items"][0]["card_sha256"] = "b" * 64
    elif fault == "spec-hash":
        packet.evaluation["spec_sha256"] = "b" * 64
    elif fault == "inspection":
        report["items"][0]["inspected_complete_card"] = False
    elif fault == "owner":
        score.update(verdict="fail", findings=[])
    else:
        score["findings"] = [{"code": "wrong_identity", "owner": "repair", "dependency": "identity correction",
                               "evidence": packet.gold.opaque}]
    packet.save_evaluation()
    with pytest.raises(ValueError):
        packet.evaluate()


def test_legacy_approval_without_phase5_receipt_cannot_unlock_export(certification):
    certification.ledger["approved_reviews"][0].pop("certification_receipt")
    write(certification.ledger_path, certification.ledger)
    with pytest.raises(cert.UncertifiedCardRefusal, match="invalid certification authority"):
        cert.load_certified_card_for_export(certification.card)


def test_inventory_caches_receipt_only_within_one_run(packet, monkeypatch):
    packet.approve()
    original = cert.evaluate_certification
    calls = []

    def counted(*args):
        calls.append(True)
        return original(*args)

    monkeypatch.setattr(cert, "evaluate_certification", counted)
    with cert.certification_run():
        assert cert.load_certified_card_for_export(packet.card) == packet.card
        assert cert.load_certified_card_for_export(packet.card) == packet.card
    assert len(calls) == 1
    packet.authority.rules.write_text("changed after earlier run")
    with pytest.raises(cert.UncertifiedCardRefusal):
        cert.load_certified_card_for_export(packet.card)


@pytest.mark.parametrize("fault", ["missing-class", "unchanged", "foreign", "unrelated-change", "duplicate-id"])
def test_invalid_controls_refused(packet, fault):
    control = packet.spec["controls"][0]
    if fault == "missing-class":
        packet.spec["controls"].pop()
    elif fault == "duplicate-id":
        control["control_id"] = "case-001"
    else:
        card = json.loads(Path(control["card"]["path"]).read_bytes())
        if fault == "unchanged":
            card = packet.card
        elif fault == "foreign":
            card["card_id"] = "wc_abcdef012345"
        else:
            card["key_at_creation"]["spelling"] = "unrelated change"
        control["card"] = write(Path(control["card"]["path"]), card)
    packet.save_spec()
    with pytest.raises(ValueError):
        packet.evaluate()


@pytest.mark.parametrize("fault", ["status", "frozen", "cards", "author", "family", "evidence"])
def test_mechanics_acceptance_not_a_status_string(packet, fault):
    if fault == "status":
        packet.mechanics["status"] = "mechanics_only_uncertified"
    elif fault == "frozen":
        packet.mechanics["frozen"] = {**packet.mechanics["frozen"], "rules_sha256": "b" * 64}
    elif fault == "cards":
        packet.mechanics["cards_sha256"] = "b" * 64
    elif fault == "author":
        packet.mechanics["accepted_by"]["id"] = "code-author"
    elif fault == "family":
        packet.mechanics["accepted_by"]["family"] = "author-family"
    else:
        packet.mechanics["evidence"][0] = {"path": "missing-independent-proof", "sha256": "b" * 64}
    packet.spec["mechanics_receipt"] = write(packet.mechanics_path, packet.mechanics)
    packet.save_spec()
    with pytest.raises((ValueError, OSError)):
        packet.evaluate()


@pytest.mark.parametrize("fault", ["raw-source", "accounting-output", "qualification", "custody"])
def test_transitive_evidence_replayed(packet, fault):
    if fault == "raw-source":
        packet.gold.source.raw.write_bytes(b"modified source capture")
    elif fault == "accounting-output":
        path = Path(packet.gold.refs["accounting_receipt"]["path"]).parent / "SRC-ULIF.json"
        path.write_bytes(b"{}")
    elif fault == "custody":
        packet.gold.isolation["access_log"][0]["allowed"] = True
        packet.gold.save_custody()
        packet.spec["isolation"]["sha256"] = packet.gold.isolation_sha
        packet.save_spec()
    else:
        Path(packet.gold.opaque["path"]).write_bytes(b"modified proof")
    with pytest.raises(ValueError):
        packet.evaluate()


@pytest.mark.parametrize("fault", ["spec", "evaluation", "receipt"])
def test_copied_status_cannot_certify(packet, fault):
    if fault == "spec":
        packet.spec["frozen"]["implementation_sha256"] = "b" * 64
        packet.save_spec()
        with pytest.raises(ValueError):
            packet.evaluate()
    elif fault == "evaluation":
        packet.evaluation = {"schema_version": "word-card-language-evaluation.v1", "status": "CERTIFIED"}
        packet.save_evaluation()
        with pytest.raises(ValueError):
            packet.evaluate()
    else:
        ref = write(packet.root / "forged.json", {"schema_version": "word-card-certification-receipt.v1", "status": "CERTIFIED"})
        with pytest.raises((ValueError, KeyError)):
            cert.verify_certification_receipt(ref, packet.root)


def test_summary_publishes_counts_and_receipt_digest_without_private_content(packet):
    ref = packet.receipt()
    summary = cert.certification_summary(ref, packet.root)
    assert summary == {"schema_version": "word-card-certification-summary.v1", "status": "CERTIFIED",
                       "receipt_sha256": ref["sha256"], "case_count": 1, "evaluator_count": 2,
                       "scores": {facet: {"passed": 2, "denominator": 2} for facet in cert.FACETS},
                       "controls": {name: {"detected": 2, "denominator": 2} for name in cert.CONTROL_FACETS},
                       "finding_count": 0, "finding_codes": {}}
    assert all(value not in json.dumps(summary) for value in (str(packet.root), "case-001", "judge-one", "fixture-key"))


def test_failed_summary_retains_material_finding_counts(packet):
    score = packet.evaluation["reports"][0]["items"][0]["scores"][0]
    score.update(verdict="fail", findings=[{"code": "wrong_identity", "owner": "source-repair",
                                           "dependency": "correct attachment", "evidence": packet.gold.opaque}])
    packet.save_evaluation()
    summary = cert.certification_summary(packet.receipt(), packet.root)
    assert summary["status"] == "FAILED"
    assert summary["finding_count"] == 1
    assert summary["finding_codes"] == {"wrong_identity": 1}


def test_receipt_cannot_unlock_an_unevaluated_card(packet):
    packet.approve()
    other = copy.deepcopy(packet.card)
    other["card_id"] = "wc_abcdef012345"
    packet.authority.approve(other)
    packet.authority.ledger["approved_reviews"][-1]["certification_receipt"] = packet.receipt()
    write(packet.authority.ledger_path, packet.authority.ledger)
    with pytest.raises(cert.UncertifiedCardRefusal, match="outside exact-artifact"):
        cert.load_certified_card_for_export(other)


@pytest.mark.parametrize("fault", ["duplicate-item", "duplicate-facet", "duplicate-case", "missing-gold-field",
                                 "shared-projection", "shared-gold-field", "unscored-gold-field"])
def test_no_reduced_or_duplicated_denominators(packet, fault):
    if fault == "duplicate-item":
        row = copy.deepcopy(packet.evaluation["reports"][0]["items"][0])
        row["card_sha256"] = "b" * 64
        packet.evaluation["reports"][0]["items"].append(row)
    elif fault == "duplicate-facet":
        row = copy.deepcopy(packet.evaluation["reports"][0]["items"][0]["scores"][0])
        row["reason"] = "duplicate score"
        packet.evaluation["reports"][0]["items"][0]["scores"].append(row)
    elif fault == "duplicate-case":
        packet.spec["cases"].append(copy.deepcopy(packet.spec["cases"][0]))
    elif fault == "missing-gold-field":
        packet.spec["projections"]["stress"]["gold_field"] = "absent"
    elif fault == "shared-projection":
        packet.spec["projections"]["stress"]["card_pointer"] = packet.spec["projections"]["identity"]["card_pointer"]
    elif fault == "shared-gold-field":
        packet.spec["projections"]["stress"]["gold_field"] = "identity"
    else:
        packet.spec["projections"]["abstention"]["gold_field"] = "unscored"
    packet.save_spec()
    packet.evaluation["spec_sha256"] = packet.spec_sha
    packet.save_evaluation()
    with pytest.raises(ValueError):
        packet.evaluate()


def test_source_projection_mismatch_is_zero_tolerance_even_when_judges_pass(packet):
    packet.card["assertions"][1]["value"] = "invented fixture claim"
    packet.authority.approve(packet.card)
    packet.spec["cases"][0]["card"] = write(packet.card_path, packet.card)
    packet.mechanics["cards_sha256"] = cert.digest([packet.card])
    packet.spec["mechanics_receipt"] = write(packet.mechanics_path, packet.mechanics)
    # Keep controls derived from the same baseline, so this isolates an ordinary-case failure.
    for row in packet.spec["controls"]:
        card = copy.deepcopy(packet.card)
        index = cert.FACETS.index(cert.CONTROL_FACETS[row["class"]])
        card["assertions"][index]["value"] = "planted source-free wrong value"
        row["card"] = write(Path(row["card"]["path"]), card)
    packet.save_spec()
    packet.make_evaluation()
    result = packet.evaluate()
    assert result["status"] == "FAILED"
    assert result["scores"]["sense_binding"] == {"passed": 0, "denominator": 2}
    assert all(row["findings"][0]["owner"] == "open-model-data" for row in result["findings"])


def test_appropriate_abstention_preserves_missing_value(tmp_path, certification):
    root = tmp_path / "abstention"
    root.mkdir()
    packet = CertificationFixture(root, certification, abstention=True)
    assert packet.card["assertions"][-1]["value"] is None
    assert packet.evaluate()["scores"]["abstention"] == {"passed": 2, "denominator": 2}
    assert packet.evaluate()["status"] == "CERTIFIED"


@pytest.mark.parametrize("fault", ["version", "schema", "empty-sources", "missing-vesum", "missing-overlay",
                                 "stale-normaliser", "stale-rules", "stale-register"])
def test_frozen_inputs_fail_closed(packet, fault):
    card = copy.deepcopy(packet.card)
    inputs = card["build"]["inputs"]
    if fault == "version":
        card["build"]["card_version"] = "cv_" + "a" * 24
    elif fault == "schema":
        card["schema_version"] = "unknown"
    elif fault == "empty-sources":
        inputs["S"] = {}
    elif fault == "missing-vesum":
        inputs["V"]["other"] = inputs["V"].pop("vesum")
        packet.authority.ledger["snapshot_bindings"]["V"]["other"] = packet.authority.ledger["snapshot_bindings"]["V"]["vesum"]
        write(packet.authority.ledger_path, packet.authority.ledger)
    elif fault == "missing-overlay":
        inputs["O"].pop("overlay")
    elif fault == "stale-normaliser":
        inputs["R"]["normaliser"]["version"] = "changed"
    elif fault == "stale-rules":
        inputs["R"]["rules"]["version"] = "changed"
    else:
        inputs["R"]["register"]["content_sha256"] = "b" * 64
    with pytest.raises(ValueError):
        cert.frozen_artifact(cert.CertificationAuthority(), [card])


@pytest.mark.parametrize("raw", [b'{"status":1,"status":2}', b'{"unused":NaN}', b'{"unused":"\\ud800"}'])
def test_certification_uses_strict_json_reader(packet, raw):
    packet.spec_path.write_bytes(raw)
    packet.spec_sha = gold.sha(raw)
    with pytest.raises(ValueError):
        packet.evaluate()


@pytest.mark.parametrize("replacement", [True, 1.0])
def test_receipt_replay_is_type_exact(packet, replacement):
    receipt = packet.evaluate()
    receipt["case_count"] = replacement
    ref = write(packet.root / "type-forged-receipt.json", receipt)
    with pytest.raises(ValueError, match="Failed or stale"):
        cert.verify_certification_receipt(ref, packet.root)
    with pytest.raises(ValueError, match="Stale evaluation summary"):
        cert.certification_summary(ref, packet.root)
