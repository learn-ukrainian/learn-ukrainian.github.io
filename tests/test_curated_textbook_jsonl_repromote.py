"""Synthetic destination/readback proof; no corpus, dictionary or network calls."""

from __future__ import annotations

import json

import pytest
import yaml

from scripts.audit.source_inventory_review_decisions import source_inventory_key
from scripts.lexicon import curated_textbook_jsonl_repromote as textbook


@pytest.fixture
def pipeline(tmp_path, monkeypatch):
    chunks = tmp_path / "chunks"
    grade = chunks / "grade-1"
    grade.mkdir(parents=True)
    (grade / "synthetic.jsonl").write_text(
        json.dumps({"chunk_id": "fixture-1", "text": "synthetic mining input"}) + "\n",
        encoding="utf-8",
    )
    rows = [{"lemma": "fixture", "pos": "noun", "gloss": "synthetic gloss", "locator": "synthetic::fixture-1"}]

    def mine(texts, *, min_freq, max_lemmas):
        assert texts == [("synthetic", "fixture-1", "synthetic mining input")]
        assert (min_freq, max_lemmas) == (3, None)
        return rows

    monkeypatch.setattr(textbook, "mine_headwords", mine)
    monkeypatch.setattr(textbook, "build_skeleton_entry", lambda lemma: {"lemma": lemma})
    monkeypatch.setattr(textbook, "verify_word", lambda lemma: [{"pos": "noun"}])
    seen = {"planned": [], "applied": [], "published": []}
    plan = {"counts": {"proposed_additions": 1}, "fixture": "promotion plan", "production_outputs_updated": []}

    def build_plan(*, candidates_path, decision_files, manifest_path):
        # Read back real writers' outputs at the consumer boundary.
        payload = json.loads(candidates_path.read_bytes())
        entry = payload["auto_merge"][0]
        assert payload["generated_from"] == "curated_textbook_jsonl_repromote.v1"
        assert payload["counts"] == {"total_delta": 1, "processed": 1, "auto_merge": 1, "needs_review": 0}
        assert (entry["lemma"], entry["pos"], entry["gloss"]) == ("fixture", "noun", "synthetic gloss")
        assert "surface_admission" not in entry
        provenance = entry["source_provenance"][0]
        assert provenance["inventory_path"] == textbook.INV_REL
        assert provenance["source_locator"] == rows[0]["locator"]
        decisions = yaml.safe_load(decision_files[0].read_bytes())
        decision = decisions["decisions"][0]
        assert decision["source_inventory"] == {
            "key": source_inventory_key(lemma="fixture", inventory_path=textbook.INV_REL, locator=rows[0]["locator"]),
            "path": textbook.INV_REL,
            "locator": rows[0]["locator"],
            "source_id": textbook.SOURCE_ID,
            "source_family": "textbook",
        }
        assert decisions["production_outputs_updated"] == []
        assert json.loads(manifest_path.read_bytes()) == {"entries": []}
        seen["planned"].append(candidates_path)
        return plan

    def apply_plan(manifest, actual_plan):
        assert manifest == {"entries": []}
        assert actual_plan == plan
        seen["applied"].append(actual_plan)
        return {
            "counts": {"promoted": 1, "skipped_existing": 0},
            "promoted_entries": [{"lemma": "fixture"}],
        }

    def publish(manifest, result, *, manifest_path, fingerprint_path, self_check):
        assert manifest == {"entries": []}
        manifest_path.write_text(json.dumps({"entries": rows}), encoding="utf-8")
        fingerprint_path.write_bytes(b"synthetic fingerprint\n")
        assert self_check(manifest_path) == 0
        seen["published"].append((manifest_path, fingerprint_path))
        return {**result, "production_outputs_updated": ["manifest", "fingerprint"]}

    monkeypatch.setattr(textbook.planner, "build_promotion_plan", build_plan)
    monkeypatch.setattr(textbook.apply, "apply_promotion_plan", apply_plan)
    monkeypatch.setattr(textbook.apply, "write_manifest_if_changed", publish)
    monkeypatch.setattr(textbook.apply, "_validate_privacy_safe_provenance", lambda entry: None)
    inventory = tmp_path / "inventory.yaml"
    decisions = tmp_path / "decisions.yaml"
    manifest = tmp_path / "manifest.json"
    manifest.write_bytes(b'{"entries": []}\n')
    fingerprint = tmp_path / "fingerprint.json"
    fingerprint.write_bytes(b"original fingerprint\n")
    return {
        "argv": [
            "--chunks-root",
            str(chunks),
            "--inventory-out",
            str(inventory),
            "--decisions-out",
            str(decisions),
            "--manifest",
            str(manifest),
            "--fingerprint",
            str(fingerprint),
            "--apply",
            "--report",
        ],
        "inventory": inventory,
        "decisions": decisions,
        "manifest": manifest,
        "fingerprint": fingerprint,
        "rows": rows,
        "plan": plan,
        "seen": seen,
    }


@pytest.mark.parametrize("write", [False, True], ids=["plan-only", "publish"])
@pytest.mark.parametrize(
    "overrides",
    [(), ("candidates",), ("plan",), ("candidates", "plan")],
    ids=["caller-defaults", "candidate-override", "plan-override", "explicit-outputs"],
)
def test_main_producer_consumer_destinations_and_publication_gate(tmp_path, monkeypatch, pipeline, write, overrides):
    scratch = tmp_path / "caller scratch"
    scratch.mkdir()
    monkeypatch.setenv("TMPDIR", str(scratch))  # Module was already imported.
    candidates = scratch / textbook.CANDIDATES_FILENAME
    plan_out = scratch / textbook.PLAN_FILENAME
    argv = list(pipeline["argv"])
    if "candidates" in overrides:
        candidates = tmp_path / "explicit" / "candidates.json"
        argv += ["--candidates-out", str(candidates)]
    if "plan" in overrides:
        plan_out = tmp_path / "explicit" / "plan.json"
        argv += ["--plan-out", str(plan_out)]
    if write:
        argv.append("--write")

    assert textbook.main(argv) == 0
    assert pipeline["seen"]["planned"] == [candidates]
    # Caller-owned artifacts remain after return for an independent readback.
    payload = json.loads(candidates.read_bytes())
    assert candidates.read_bytes() == (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    assert plan_out.read_bytes() == (
        json.dumps(pipeline["plan"], ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    assert json.loads(plan_out.read_bytes()) == pipeline["plan"]
    assert set(scratch.iterdir()) == {path for path in (candidates, plan_out) if path.parent == scratch}
    if write:
        assert pipeline["seen"]["applied"] == [pipeline["plan"]]
        assert pipeline["seen"]["published"] == [(pipeline["manifest"], pipeline["fingerprint"])]
        assert pipeline["fingerprint"].read_bytes() == b"synthetic fingerprint\n"
    else:
        assert pipeline["seen"]["applied"] == []
        assert pipeline["seen"]["published"] == []
        assert pipeline["manifest"].read_bytes() == b'{"entries": []}\n'
        assert pipeline["fingerprint"].read_bytes() == b"original fingerprint\n"


@pytest.mark.parametrize("explicit", [False, True])
def test_direct_apply_plan_retains_default_or_explicit_plan(tmp_path, monkeypatch, pipeline, explicit):
    scratch = tmp_path / "task scratch"
    scratch.mkdir()
    monkeypatch.setenv("TMPDIR", str(scratch))
    textbook.write_inventory(pipeline["rows"], pipeline["inventory"])
    textbook.write_decisions(pipeline["rows"], pipeline["decisions"])
    candidates = tmp_path / "direct-candidates.json"
    textbook.build_candidates(pipeline["inventory"], candidates)
    plan_out = tmp_path / "direct-plan.json" if explicit else scratch / textbook.PLAN_FILENAME
    kwargs = {"plan_out": plan_out} if explicit else {}
    assert textbook.apply_plan(
        candidates=candidates,
        decisions=pipeline["decisions"],
        manifest=pipeline["manifest"],
        fingerprint=pipeline["fingerprint"],
        write=False,
        **kwargs,
    ) == {"plan": pipeline["plan"]["counts"], "wrote": False}
    assert json.loads(plan_out.read_bytes()) == pipeline["plan"]
    assert candidates.is_file()
    assert pipeline["seen"]["published"] == []


def test_default_and_explicit_outputs_preserve_bytes_and_ledger_identities(tmp_path, monkeypatch, pipeline):
    scratch = tmp_path / "managed task"
    scratch.mkdir()
    monkeypatch.setenv("TMPDIR", str(scratch))
    explicit_candidates = tmp_path / "overrides" / "candidates.json"
    explicit_plan = tmp_path / "overrides" / "plan.json"
    assert (
        textbook.main(
            [
                *pipeline["argv"],
                "--candidates-out",
                str(explicit_candidates),
                "--plan-out",
                str(explicit_plan),
            ]
        )
        == 0
    )
    ledger_bytes = {name: pipeline[name].read_bytes() for name in ("inventory", "decisions")}
    assert textbook.main(pipeline["argv"]) == 0
    assert (scratch / textbook.CANDIDATES_FILENAME).read_bytes() == explicit_candidates.read_bytes()
    assert (scratch / textbook.PLAN_FILENAME).read_bytes() == explicit_plan.read_bytes()
    assert {name: pipeline[name].read_bytes() for name in ledger_bytes} == ledger_bytes
    assert pipeline["manifest"].read_bytes() == b'{"entries": []}\n'
    assert pipeline["fingerprint"].read_bytes() == b"original fingerprint\n"


def test_default_resolution_follows_each_caller_root_and_system_fallback(tmp_path, monkeypatch):
    fallback = tmp_path / "fallback"
    monkeypatch.setattr(textbook.tempfile, "gettempdir", lambda: str(fallback))
    for root in (tmp_path / "first", tmp_path / "second"):
        monkeypatch.setenv("TMPDIR", str(root))
        assert textbook._scratch_output(textbook.CANDIDATES_FILENAME) == root / textbook.CANDIDATES_FILENAME
        assert textbook._scratch_output(textbook.PLAN_FILENAME) == root / textbook.PLAN_FILENAME
        assert not root.exists()
    monkeypatch.delenv("TMPDIR")
    assert textbook._scratch_output(textbook.PLAN_FILENAME) == fallback / textbook.PLAN_FILENAME


def test_plan_override_keeps_repository_output_refusal(tmp_path, monkeypatch, pipeline):
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    with pytest.raises(ValueError, match="repository"):
        textbook.main([*pipeline["argv"], "--plan-out", str(textbook.PROJECT_ROOT / "forbidden-plan.json")])
    assert pipeline["seen"]["applied"] == []
    assert pipeline["manifest"].read_bytes() == b'{"entries": []}\n'


def test_help_documents_scratch_lifetime_and_overrides(capsys):
    with pytest.raises(SystemExit) as exc:
        textbook.main(["--help"])
    assert exc.value.code == 0
    help_text = capsys.readouterr().out
    for text in ("--candidates-out", "--plan-out", "TMPDIR", "caller owns cleanup", "--apply --write", "Exit codes:"):
        assert text in help_text


def test_write_without_apply_does_not_create_scratch_or_publish(tmp_path, monkeypatch, pipeline):
    scratch = tmp_path / "caller scratch"
    scratch.mkdir()
    monkeypatch.setenv("TMPDIR", str(scratch))
    argv = [arg for arg in pipeline["argv"] if arg != "--apply"]

    assert textbook.main([*argv, "--write"]) == 0
    assert list(scratch.iterdir()) == []
    assert not pipeline["inventory"].exists()
    assert not pipeline["decisions"].exists()
    assert pipeline["seen"] == {"planned": [], "applied": [], "published": []}
    assert pipeline["manifest"].read_bytes() == b'{"entries": []}\n'
    assert pipeline["fingerprint"].read_bytes() == b"original fingerprint\n"
