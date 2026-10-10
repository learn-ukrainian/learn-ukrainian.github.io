"""All evidence readers apply exact-byte retirement before content access."""

import hashlib
from pathlib import Path

import pytest
import yaml

from scripts.curriculum.evidence import catalogue, pack, sources, verify, words
from scripts.curriculum.validate.loader import PlanError, load_plan, read_plan_text


@pytest.fixture
def retired(tmp_path):
    plans = tmp_path / "plans"
    plans.mkdir()
    plan = plans / "old.yaml"
    # Invalid UTF-8 and YAML establish that refusal precedes interpretation.
    plan.write_bytes(b"uses: [W-001]\ninvalid: [\xff")
    record = {
        "retirement_schema": 1,
        "plans": [{"slug": "old", "old_position": 1, "sha256": hashlib.sha256(plan.read_bytes()).hexdigest()}],
        "routes": [],
    }
    (plans / "_retired.yaml").write_text(yaml.safe_dump(record))
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    (evidence / "old.yaml").write_bytes(b"protected synthetic pack\xff")
    return plan, evidence


def snapshot(root):
    return {str(path.relative_to(root)): path.read_bytes() for path in root.rglob("*") if path.is_file()}


def operations(plan, evidence):
    return {
        "catalogue": lambda: catalogue.request_report(plan, evidence / "_words.yaml", None),
        "build": lambda: pack.build_pack(
            "a1", "old", evidence / "missing-request.yaml", plans_dir=plan.parent, evidence_dir=evidence
        ),
        "verify": lambda: verify.verify_pack("a1", "old", plans_dir=plan.parent, evidence_dir=evidence),
        "citations": lambda: words.find_plans_citing("W-001", plan.parent),
        "raw_text": lambda: read_plan_text(plan),
    }


@pytest.mark.parametrize("operation", ["catalogue", "build", "verify", "raw_text"])
@pytest.mark.parametrize("invalid_record", [False, True])
def test_refusal_precedes_all_other_content_reads(retired, operation, invalid_record, monkeypatch):
    plan, evidence = retired
    if invalid_record:
        (plan.parent / "_retired.yaml").write_text("plans: []\nplans: []\n")
    before = snapshot(plan.parent.parent)
    read_bytes, read_text = Path.read_bytes, Path.read_text

    def guarded_bytes(path, *args, **kwargs):
        assert path in {plan, plan.parent / "_retired.yaml"}, f"content read before refusal: {path.name}"
        return read_bytes(path, *args, **kwargs)

    def guarded_text(path, *args, **kwargs):
        assert path == plan.parent / "_retired.yaml", f"content decoded before refusal: {path.name}"
        return read_text(path, *args, **kwargs)

    with monkeypatch.context() as guard:
        guard.setattr(Path, "read_bytes", guarded_bytes)
        guard.setattr(Path, "read_text", guarded_text)
        with pytest.raises(PlanError, match="retirement_record_invalid" if invalid_record else "plan_retired"):
            operations(plan, evidence)[operation]()
    assert snapshot(plan.parent.parent) == before


def test_citations_exclude_retired_and_metadata_but_include_changed_replacement(retired):
    plan, evidence = retired
    (plan.parent / "_scope").mkdir()
    (plan.parent / "_scope/old.yaml").write_text("uses: [W-001]")
    (plan.parent / "_words.yaml").write_text("uses: [W-001]")
    (plan.parent / ".hidden.yaml").write_text("uses: [W-001]")
    (plan.parent / "active.yaml").write_text("uses: [W-001]")
    assert operations(plan, evidence)["citations"]() == ["active.yaml"]
    plan.write_text("plan_schema: 2\nslug: old\nlessons: []\nuses: [W-001]\n")
    assert words.find_plans_citing("W-001", plan.parent) == ["active.yaml", "old.yaml"]
    assert load_plan(plan)["slug"] == "old"
    (plan.parent / "_retired.yaml").write_text("invalid: true")
    with pytest.raises(PlanError, match="retirement_record_invalid"):
        words.find_plans_citing("W-001", plan.parent)


def test_citation_read_errors_are_not_swallowed(tmp_path, monkeypatch):
    (tmp_path / "active.yaml").write_text("uses: [W-001]")
    read = Path.read_bytes

    def inaccessible(path, *args, **kwargs):
        if path.name == "active.yaml":
            raise PermissionError("synthetic read failure")
        return read(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_bytes", inaccessible)
    with pytest.raises(PermissionError, match="synthetic read failure"):
        words.find_plans_citing("W-001", tmp_path)


@pytest.mark.parametrize("operation", ["catalogue", "build", "verify"])
def test_invalid_record_without_plan_still_refuses(retired, operation):
    plan, evidence = retired
    plan.rename(plan.with_suffix(".preserved"))
    (plan.parent / "_retired.yaml").write_text("invalid: true")
    with pytest.raises(PlanError, match="retirement_record_invalid"):
        operations(plan, evidence)[operation]()


@pytest.mark.parametrize("entrypoint", [pack.main, verify.main_pack])
@pytest.mark.parametrize("invalid_record", [False, True])
def test_production_clis_report_typed_refusal_and_never_overwrite(retired, entrypoint, invalid_record, capsys):
    plan, evidence = retired
    if invalid_record:
        (plan.parent / "_retired.yaml").write_text("invalid: true")
    before = snapshot(plan.parent.parent)
    args = ["a1", "old", "--plans-dir", str(plan.parent), "--evidence-dir", str(evidence), "--json"]
    if entrypoint is pack.main:
        args += ["--request", str(evidence / "missing-request.yaml")]
    assert entrypoint(args) == 1
    assert ("retirement_record_invalid" if invalid_record else "plan_retired") in capsys.readouterr().out
    assert snapshot(plan.parent.parent) == before


def test_changed_replacement_builds_and_integrity_publication_still_gate(
    retired, synthetic_sources, synthetic_vesum, synthetic_standard
):
    plan, evidence = retired
    plan.write_text("plan_schema: 2\nslug: old\nlessons: []\n")
    # Preserve the original protected pack; a separate output tests ordinary builds.
    output = evidence / "replacement"
    request = evidence / "request.yaml"
    request.write_text("request_schema: 1\nmodule: a1/old\n")
    with sources.Sources(
        sources_db=synthetic_sources, vesum_db=synthetic_vesum, standard_path=synthetic_standard
    ) as source:
        result = pack.build_pack(
            "a1", "old", request, plans_dir=plan.parent, evidence_dir=output, sources_instance=source, offline=True
        )
        assert result["catalogue"]["status"] == "ok"
        assert (
            verify.verify_pack(
                "a1", "old", plans_dir=plan.parent, evidence_dir=output, sources_instance=source, offline=True
            )["status"]
            == "ok"
        )
        # Valid changed bytes must still fail publication resolution and lock integrity.
        plan.write_text("[]\n")
        (output / "old.yaml").write_bytes((output / "old.yaml").read_bytes() + b"\n")
        result = verify.verify_pack(
            "a1", "old", plans_dir=plan.parent, evidence_dir=output, sources_instance=source, offline=True
        )
        assert any("publication_plan_unresolved" in error for error in result["errors"])
        assert any("lock_mismatch" in error for error in result["errors"])
    assert (evidence / "old.yaml").read_bytes() == b"protected synthetic pack\xff"


def test_raw_text_missing_and_nonretired_invalid_encoding_are_named(tmp_path):
    with pytest.raises(PlanError, match="plan_not_found"):
        read_plan_text(tmp_path / "absent.yaml")
    path = tmp_path / "bad.yaml"
    path.write_bytes(b"\xff")
    with pytest.raises(PlanError, match="plan_yaml_invalid"):
        read_plan_text(path)


def test_word_builder_and_verifier_ignore_only_retired_citations(retired, synthetic_sources, synthetic_vesum):
    plan, evidence = retired
    request = evidence / "words.request.yaml"
    request.write_text("request_schema: 1\nlevel: a1\nwords: [{lemma: synthetic, pos: noun, want: new}]\n")
    with sources.Sources(sources_db=synthetic_sources, vesum_db=synthetic_vesum) as source:
        words.build_words("a1", request, plans_dir=plan.parent, evidence_dir=evidence, sources_instance=source)
        result = verify.verify_words_store("a1", plans_dir=plan.parent, evidence_dir=evidence, sources_instance=source)
        assert result["status"] == "ok"
        assert result["unresolved_uncited_count"] == 1
        request.write_text(
            "request_schema: 1\nlevel: a1\nwords: [{lemma: synthetic, pos: noun, want: W-001, note: changed}]\n"
        )
        result = words.build_words(
            "a1", request, plans_dir=plan.parent, evidence_dir=evidence, sources_instance=source, dry_run=True
        )
        assert result["changed_ids"] == ["W-001"]
        assert result["affected_plans"] == {}
        plan.write_text("uses: [W-001]\n")
        result = words.build_words(
            "a1", request, plans_dir=plan.parent, evidence_dir=evidence, sources_instance=source, dry_run=True
        )
        assert result["affected_plans"] == {"W-001": ["old.yaml"]}
        result = verify.verify_words_store("a1", plans_dir=plan.parent, evidence_dir=evidence, sources_instance=source)
        assert result["status"] == "failed"
        assert any("unresolved_cited" in error for error in result["errors"])
        (plan.parent / "_retired.yaml").write_text("invalid: true")
        for operation in (
            lambda: words.build_words(
                "a1", request, plans_dir=plan.parent, evidence_dir=evidence, sources_instance=source, dry_run=True
            ),
            lambda: verify.verify_words_store(
                "a1", plans_dir=plan.parent, evidence_dir=evidence, sources_instance=source
            ),
        ):
            with pytest.raises(PlanError, match="retirement_record_invalid"):
                operation()


@pytest.mark.parametrize("entrypoint", [words.build_words, verify.verify_words_store])
def test_word_entrypoints_validate_inventory_before_requests_or_store_reads(retired, entrypoint, monkeypatch):
    plan, evidence = retired
    (plan.parent / "_retired.yaml").write_text("invalid: true")
    before = snapshot(plan.parent.parent)
    original = Path.read_text

    def guarded(path, *args, **kwargs):
        assert path == plan.parent / "_retired.yaml", f"content read before invalid record: {path.name}"
        return original(path, *args, **kwargs)

    with monkeypatch.context() as guard:
        guard.setattr(Path, "read_text", guarded)
        args = ("a1", evidence / "missing-request.yaml") if entrypoint is words.build_words else ("a1",)
        with pytest.raises(PlanError, match="retirement_record_invalid"):
            entrypoint(*args, plans_dir=plan.parent, evidence_dir=evidence)
    assert snapshot(plan.parent.parent) == before
