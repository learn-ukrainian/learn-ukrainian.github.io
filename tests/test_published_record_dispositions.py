"""Falsify mandatory six-origin authority and review/supersession bypasses."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest
import yaml

from scripts.lexicon import manifest_io
from scripts.lexicon import published_record_dispositions as dispositions
from scripts.review.record_cf_verdict import build_comment
from scripts.review.review_contract import AgentIdentity, FindingValidation, VerifyContext, build_receipt
from scripts.review.target_resolution import ReviewTarget

ROOT = Path(__file__).resolve().parents[1]


def write_yaml(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, allow_unicode=True, sort_keys=False))


def write_preservation(root: Path, ledger: dict, preserved: dict) -> None:
    path = root / dispositions.PRESERVATION_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(preserved, ensure_ascii=False, indent=2) + "\n")
    ledger["preservation"]["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    write_yaml(root / dispositions.LEDGER_PATH, ledger)


def make_authority(root: Path) -> tuple[dict, dict, dict]:
    """Small transaction with the six actual public payloads and raw origins."""
    real = dispositions.load_dispositions(ROOT)
    ledger, preserved = copy.deepcopy(real.ledger), copy.deepcopy(real.preservation)
    inventory_origin = ledger["decisions"][1]["origin"]
    inventory = dispositions._read_yaml(
        ROOT / "registry/lexicon/source-inventory/oneshot/ohoiko-ulp-curated-2026-07-19-bulk.yaml"
    )
    source = copy.deepcopy(inventory["sources"][0])
    source["headwords"] = []
    old_ledger = dispositions._read_yaml(ROOT / ledger["decisions"][1]["supersedes"][0]["ledger_path"])
    old_rows = []
    built = yaml.safe_load((ROOT / ledger["decisions"][0]["origin"]["path"]).read_text())
    for n, row in enumerate(ledger["decisions"]):
        origin = row["origin"]
        row["projection"]["index_zero_based"] = n + 1
        preserved["records"][n]["original_index_zero_based"] = n + 1
        if origin["kind"] == "built_vocabulary":
            origin["index_zero_based"] = 0
            origin["row_one_based"] = 1
            path = root / origin["path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(yaml.safe_dump([built[18]], allow_unicode=True))
        else:
            old_index = int(origin["structural_locator_one_based"].split("[")[-1][:-1]) - 1
            source["headwords"].append(inventory["sources"][0]["headwords"][old_index])
            origin["structural_locator_one_based"] = f"sources[1].headwords[{n}]"
            old_rows.extend(r for r in old_ledger["decisions"] if r["source_inventory"]["key"] == origin["key"])
    write_yaml(
        root / ("registry/lexicon/source-inventory/" + inventory_origin["path"].split("source-inventory/", 1)[1]),
        {"sources": [source]},
    )
    write_yaml(
        root / ledger["decisions"][1]["supersedes"][0]["ledger_path"],
        {"batch_id": old_ledger["batch_id"], "decisions": old_rows},
    )
    envelope = {
        "version": "fixture",
        "stats": {"lemmas_total": 99, "from_built": 88, "form_of_count": 77, "entries": 19203, "entry_count": 20111},
        "generated_at": "original",
        "entries_count": 8,
        "unknown": {"opaque": True},
    }
    survivors = [
        {"lemma": "fixture-before", "url_slug": "fixture-before", "primary_source": "source_inventory_grow"},
        {
            "lemma": "fixture-after",
            "url_slug": "fixture-after",
            "primary_source": "built_vocabulary",
            "form_of": {"lemma": "fixture-before", "url_slug": "fixture-before"},
        },
    ]
    before = {**envelope, "entries": [survivors[0], *(r["entry"] for r in preserved["records"]), survivors[1]]}
    after = copy.deepcopy(before)
    after["entries"] = survivors
    after["stats"].update(lemmas_total=2, from_built=1, form_of_count=1)
    after["entries_count"] = 2
    preserved["original_manifest_envelope"] = envelope
    preserved["original_top_level_order"] = list(before)
    preserved["transaction"] = {
        "before_sha256": hashlib.sha256(manifest_io.serialize_manifest(before)).hexdigest(),
        "after_sha256": hashlib.sha256(manifest_io.serialize_manifest(after)).hexdigest(),
        "ordered_survivor_sha256": dispositions.ordered_digest(survivors),
        "before_entries": 8,
        "after_entries": 2,
    }
    write_preservation(root, ledger, preserved)
    return ledger, preserved, before


def native_receipt(*, nonblocking: bool = False) -> dict:
    """Native factory interop fixture; never independent review evidence."""
    ctx = VerifyContext(
        issue_ref="#10181",
        scope={"paths": [dispositions.LEDGER_PATH.as_posix()]},
        author=AgentIdentity("gpt-6.1-sol", "openai", "codex", "fixture author"),
        reviewer=AgentIdentity("claude-opus-5-5", "anthropic", "claude-code", "fixture reviewer"),
        target=ReviewTarget("branch", "d" * 40, "a" * 40, (dispositions.LEDGER_PATH.as_posix(),), 1, True, "fixture"),
        repo_root=ROOT,
        input_sha256="b" * 64,
        reviewer_output_sha256="c" * 64,
    )
    findings = (
        [FindingValidation("F1", "verified", disposition="follow_up", disposition_rationale="No behavior impact.")]
        if nonblocking
        else []
    )
    return build_receipt(
        ctx,
        payload={
            "schema_version": "code-review-findings.v1",
            "overall": {"correctness": "correct"},
            "findings": [{"id": finding.id} for finding in findings],
        },
        validations=findings,
        exit_code=1 if nonblocking else 0,
        final_disposition="actionable" if nonblocking else "clean",
    )


def add_release(root: Path, ledger: dict, hold: dict, *, suffix: str = "release", receipt: dict | None = None) -> dict:
    release = copy.deepcopy(hold)
    release.update(
        row_id=hold["row_id"] + "-" + suffix,
        decision="approve_for_publish",
        effect="restore_projection",
        supersedes=[
            {
                "ledger_path": dispositions.LEDGER_PATH.as_posix(),
                "batch_id": ledger["batch_id"],
                "row_id": hold["row_id"],
                "decision": hold["decision"],
                "row_sha256": dispositions.canonical_sha256(hold),
            }
        ],
    )
    digest = dispositions.canonical_sha256(release)
    reviewer = {"model": "claude-opus-5-5", "family": "anthropic", "harness": "claude-code"}
    receipt = native_receipt() if receipt is None else receipt
    body = build_comment(
        sha="a" * 40,
        task_id="fixture-review",
        started="2026-10-09T00:00:00.000000Z",
        verdict="APPROVED",
        model=reviewer["model"],
        family=reviewer["family"],
        reply=f"release-row-sha256: {digest}\nsuperseded-hold-row-sha256: {dispositions.canonical_sha256(hold)}",
    )
    receipt_path = Path(f"reviews/{release['row_id']}.json")
    verdict_path = receipt_path.with_suffix(".md")
    (root / receipt_path).parent.mkdir(exist_ok=True)
    (root / receipt_path).write_text(json.dumps(receipt))
    (root / verdict_path).write_text(body)
    binding = {
        "row_sha256": digest,
        "superseded_row_sha256": dispositions.canonical_sha256(hold),
        "receipt_path": str(receipt_path),
        "receipt_json": (root / receipt_path).read_text(),
        "receipt_sha256": hashlib.sha256((root / receipt_path).read_bytes()).hexdigest(),
        "verdict_path": str(verdict_path),
        "verdict_body": body,
        "verdict_sha256": hashlib.sha256((root / verdict_path).read_bytes()).hexdigest(),
    }
    ledger["decisions"].append(release)
    ledger["release_reviews"].append(binding)
    write_yaml(root / dispositions.LEDGER_PATH, ledger)
    return release


def test_committed_pair_covers_actual_six_and_exact_predecessors():
    authority = dispositions.load_dispositions()
    assert tuple(r["row_id"] for r in authority.active_holds) == dispositions.ROW_IDS
    assert len(authority.preservation["records"]) == 6
    assert authority.preservation["transaction"]["after_entries"] == 27466
    assert authority.released_ids == frozenset()
    assert [r["projection"]["index_zero_based"] for r in authority.active_holds] == [
        6138,
        9729,
        12788,
        14461,
        18228,
        18881,
    ]
    with pytest.raises(dispositions.DispositionError, match="held"):
        authority.validate_manifest({"entries": [r["entry"] for r in authority.preservation["records"]]})


def test_unrelated_predecessor_rewrite_is_not_release(tmp_path):
    ledger, _, _ = make_authority(tmp_path)
    path = tmp_path / ledger["decisions"][1]["supersedes"][0]["ledger_path"]
    old = yaml.safe_load(path.read_text())
    old["decisions"].append({"decision": "approve_for_publish", "source_inventory": {"key": "unrelated"}})
    write_yaml(path, old)
    assert len(dispositions.load_dispositions(tmp_path).active_holds) == 6
    old["decisions"][0]["sense_note"] = "changed"
    write_yaml(path, old)
    with pytest.raises(dispositions.DispositionError, match="predecessor"):
        dispositions.load_dispositions(tmp_path)


@pytest.mark.parametrize(
    "fault",
    [
        "delete_hold",
        "delete_ledger",
        "delete_preservation",
        "wrong_kind",
        "wrong_version",
        "duplicate_row",
        "projection",
        "payload",
        "preservation_coverage",
        "envelope",
        "transaction",
        "origin",
        "key",
        "index",
        "orphan",
    ],
)
def test_authority_changes_fail_closed(tmp_path, fault):
    ledger, preserved, _ = make_authority(tmp_path)
    if fault == "delete_hold":
        ledger["decisions"].pop()
    elif fault == "delete_ledger":
        (tmp_path / dispositions.LEDGER_PATH).unlink()
        return assert_load_fails(tmp_path)
    elif fault == "delete_preservation":
        (tmp_path / dispositions.PRESERVATION_PATH).unlink()
        return assert_load_fails(tmp_path)
    elif fault == "wrong_kind":
        ledger["kind"] = "clearance"
    elif fault == "wrong_version":
        ledger["version"] = True
    elif fault == "duplicate_row":
        ledger["decisions"].append(ledger["decisions"][0])
    elif fault == "projection":
        ledger["decisions"][0]["projection"]["index_zero_based"] = 0
    elif fault == "payload":
        preserved["records"][0]["entry"]["gloss"] = "changed"
    elif fault == "preservation_coverage":
        preserved["records"].pop()
    elif fault == "envelope":
        preserved["original_top_level_order"].append("missing")
    elif fault == "transaction":
        preserved["transaction"]["before_sha256"] = "bad"
    elif fault == "origin":
        ledger["decisions"][0]["origin"]["kind"] = "unknown"
    elif fault == "key":
        ledger["decisions"][1]["origin"]["key"] = "wrong"
    elif fault == "index":
        ledger["decisions"][0]["origin"]["row_one_based"] = 0
    elif fault == "orphan":
        ledger["decisions"].append({**ledger["decisions"][0], "row_id": "orphan"})
    write_preservation(tmp_path, ledger, preserved)
    assert_load_fails(tmp_path)


def assert_load_fails(root):
    with pytest.raises(dispositions.DispositionError):
        dispositions.load_dispositions(root)


@pytest.mark.parametrize("kind", ["built", "inventory"])
@pytest.mark.parametrize("change", ["unrelated", "changed", "moved"])
def test_origin_rows_use_raw_digest_and_exact_position(tmp_path, kind, change):
    ledger, _, _ = make_authority(tmp_path)
    origin = ledger["decisions"][0 if kind == "built" else 1]["origin"]
    path = tmp_path / (
        origin["path"]
        if kind == "built"
        else "registry/lexicon/source-inventory/oneshot/ohoiko-ulp-curated-2026-07-19-bulk.yaml"
    )
    raw = yaml.safe_load(path.read_text())
    rows = raw if kind == "built" else raw["sources"][0]["headwords"]
    if change == "unrelated":
        rows.append({"lemma": "fixture-extra"})
    elif change == "changed":
        rows[0]["gloss"] = "changed"
    else:
        rows.insert(0, {"lemma": "fixture-extra"})
    path.write_text(yaml.safe_dump(raw, allow_unicode=True))
    if change == "unrelated":
        assert len(dispositions.load_dispositions(tmp_path).active_holds) == 6
    else:
        assert_load_fails(tmp_path)


def test_reviewed_release_keeps_hold_and_exact_chain(tmp_path):
    ledger, _, _ = make_authority(tmp_path)
    hold = ledger["decisions"][0]
    add_release(tmp_path, ledger, hold)
    authority = dispositions.load_dispositions(tmp_path)
    assert len(authority.active_holds) == 5
    assert authority.released_ids == {hold["row_id"]}


@pytest.mark.parametrize("nonblocking", [False, True], ids=["native-clean", "native-nonblocking"])
def test_native_factory_release_preserves_receipt_findings(tmp_path, nonblocking):
    ledger, _, _ = make_authority(tmp_path)
    receipt = native_receipt(nonblocking=nonblocking)
    original = copy.deepcopy(receipt)
    hold = ledger["decisions"][0]
    add_release(tmp_path, ledger, hold, receipt=receipt)
    authority = dispositions.load_dispositions(tmp_path)
    assert authority.released_ids == {hold["row_id"]}
    assert receipt == original
    assert json.loads(authority.ledger["release_reviews"][0]["receipt_json"]) == original


@pytest.mark.parametrize(
    "fault",
    [
        "incorrect",
        "uncertain",
        "payload_absent",
        "overall_absent",
        "findings_absent",
        "empty_findings",
        "nonmapping_finding",
        "missing_id",
        "wrong_ids",
        "unverified",
        "stop_and_escalate",
        "invalid_disposition",
        "nonstring_disposition",
        "missing_rationale",
        "blank_rationale",
        "nonstring_rationale",
        "error",
        "missing_error",
        "wrong_exit",
        "wrong_status",
        "clean_wrong_exit",
        "invalid_schema",
    ],
)
def test_native_actionable_release_requires_canonical_qualification(tmp_path, fault):
    ledger, _, _ = make_authority(tmp_path)
    receipt = native_receipt(nonblocking=True)
    finding = receipt["findings"][0]
    if fault in {"incorrect", "uncertain"}:
        receipt["reviewer_payload"]["overall"]["correctness"] = fault
    elif fault == "payload_absent":
        receipt.pop("reviewer_payload")
    elif fault == "overall_absent":
        receipt["reviewer_payload"].pop("overall")
    elif fault == "findings_absent":
        receipt.pop("findings")
    elif fault == "empty_findings":
        receipt["findings"] = []
    elif fault == "nonmapping_finding":
        receipt["findings"] = ["F1"]
    elif fault == "missing_id":
        finding.pop("id")
    elif fault == "wrong_ids":
        receipt["reviewer_payload"]["finding_ids"] = ["F2"]
    elif fault == "unverified":
        finding["outcome"] = "quote_missing"
    elif fault in {"stop_and_escalate", "invalid_disposition", "nonstring_disposition"}:
        finding["disposition"] = 1 if fault == "nonstring_disposition" else fault
    elif fault == "missing_rationale":
        finding.pop("disposition_rationale")
    elif fault in {"blank_rationale", "nonstring_rationale"}:
        finding["disposition_rationale"] = " " if fault == "blank_rationale" else 1
    elif fault == "error":
        receipt["error"] = "incomplete review"
    elif fault == "missing_error":
        receipt.pop("error")
    elif fault == "wrong_exit":
        receipt["exit_code"] = 2
    elif fault == "wrong_status":
        receipt["final_disposition"] = "unverifiable"
    elif fault == "clean_wrong_exit":
        receipt["final_disposition"] = "clean"
    elif fault == "invalid_schema":
        receipt["schema_version"] = "invalid"
    add_release(tmp_path, ledger, ledger["decisions"][0], receipt=receipt)
    with pytest.raises(dispositions.DispositionError, match="canonical code-review receipt"):
        dispositions.load_dispositions(tmp_path)


@pytest.mark.parametrize(
    "fault",
    [
        "no_review",
        "row_binding",
        "hold_binding",
        "retarget",
        "supersession",
        "receipt_digest",
        "body_digest",
        "clearance",
        "bare_approval",
        "model",
        "family",
        "harness",
        "head",
        "self_review",
        "failed_review",
        "fork",
        "cycle",
        "chain",
    ],
)
def test_release_review_cannot_be_asserted_by_clearance(tmp_path, fault):
    ledger, _, _ = make_authority(tmp_path)
    hold = ledger["decisions"][0]
    release = add_release(tmp_path, ledger, hold)
    binding = ledger["release_reviews"][0]
    receipt_path, verdict_path = tmp_path / binding["receipt_path"], tmp_path / binding["verdict_path"]
    receipt = json.loads(receipt_path.read_text())
    if fault == "no_review":
        ledger["release_reviews"] = []
    elif fault == "row_binding":
        binding["row_sha256"] = "0" * 64
    elif fault == "hold_binding":
        binding["superseded_row_sha256"] = "0" * 64
    elif fault == "retarget":
        release["origin"]["path"] = "elsewhere"
    elif fault == "supersession":
        release["supersedes"][0]["row_sha256"] = "0" * 64
    elif fault == "receipt_digest":
        binding["receipt_sha256"] = "0" * 64
    elif fault == "body_digest":
        binding["verdict_sha256"] = "0" * 64
    elif fault == "clearance":
        receipt = {"head": "a" * 40, "verdict": "APPROVE"}
    elif fault == "bare_approval":
        verdict_path.write_text("APPROVED")
    elif fault in {"model", "family", "harness"}:
        receipt["reviewer"].pop(fault)
    elif fault == "head":
        receipt["target"]["head_sha"] = "b" * 40
    elif fault == "self_review":
        receipt["author"]["family"] = receipt["reviewer"]["family"]
    elif fault == "failed_review":
        receipt["exit_code"] = 2
    elif fault == "fork":
        add_release(tmp_path, ledger, hold, suffix="other")
    elif fault == "cycle":
        hold["supersedes"] = [{"row_id": release["row_id"]}]
    elif fault == "chain":
        add_release(tmp_path, ledger, release, suffix="chain")
    if fault in {"clearance", "model", "family", "harness", "head", "self_review", "failed_review"}:
        receipt_path.write_text(json.dumps(receipt))
        binding["receipt_sha256"] = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
        binding["receipt_json"] = receipt_path.read_text()
    if fault == "bare_approval":
        binding["verdict_sha256"] = hashlib.sha256(verdict_path.read_bytes()).hexdigest()
        binding["verdict_body"] = verdict_path.read_text()
    write_yaml(tmp_path / dispositions.LEDGER_PATH, ledger)
    assert_load_fails(tmp_path)


def test_review_body_requires_both_row_digests(tmp_path):
    ledger, _, _ = make_authority(tmp_path)
    add_release(tmp_path, ledger, ledger["decisions"][0])
    binding = ledger["release_reviews"][0]
    path = tmp_path / binding["verdict_path"]
    path.write_text(path.read_text().replace("release-row-sha256:", "other-row-sha256:"))
    binding["verdict_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    binding["verdict_body"] = path.read_text()
    write_yaml(tmp_path / dispositions.LEDGER_PATH, ledger)
    assert_load_fails(tmp_path)


@pytest.mark.parametrize(
    "carrier", ["form_of", "related_slug", "target_slug", "alias_target", "canonical_slug", "aliases", "link_catalog"]
)
def test_route_carriers_fail_but_unlinked_citation_survives(carrier):
    slug = "held-route"
    value = {
        "entries": [
            {
                "lemma": "survivor",
                "url_slug": "survivor",
                "sections": {"synonyms": {"items": [slug], "synsets": [{"members": [{"lemma": slug}]}]}},
            }
        ]
    }
    dispositions.validate_route_references(value, {slug}, {slug})
    value["entries"][0][carrier] = {"url_slug": slug} if carrier in {"form_of", "aliases", "link_catalog"} else slug
    with pytest.raises(dispositions.DispositionError, match="route-bearing"):
        dispositions.validate_route_references(value, {slug}, {slug})
    value["entries"].append({"lemma": slug, "url_slug": slug})
    dispositions.validate_route_references(value, {slug}, {slug})


def test_path_escape_is_not_authority(tmp_path):
    with pytest.raises(dispositions.DispositionError):
        dispositions._path(tmp_path, "../outside")
    with pytest.raises(dispositions.DispositionError):
        dispositions._path(tmp_path, "/outside")
