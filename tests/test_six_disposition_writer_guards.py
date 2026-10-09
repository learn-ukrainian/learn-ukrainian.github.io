"""Central writer boundaries block stale decisions and six regeneration paths."""

from __future__ import annotations

import copy
import json

import pytest

from scripts.audit import apply_source_inventory_promotion as applier
from scripts.audit import apply_source_inventory_provenance as overlay
from scripts.audit import plan_source_inventory_promotion as planner
from scripts.lexicon import build_data_manifest as builder
from scripts.lexicon import published_record_dispositions as dispositions
from scripts.lexicon import verify_manifest
from tests.test_published_record_dispositions import make_authority, write_yaml


def stale_decision(row):
    origin = row["origin"]
    return planner.ApprovedDecision(
        lemma=row["lemma"],
        approved_pos="opaque",
        approved_gloss="opaque",
        sense_note="fixture",
        source_inventory={"key": origin["key"], "source_family": origin["source_family"]},
        evidence_refs=(),
        review_queue_reasons=(),
        surface_admission={},
        batch_id="fixture",
        batch_label="fixture",
        decision_file="fixture.yaml",
    )


@pytest.mark.parametrize("index", range(1, 6))
def test_inventory_all_five_subset_approvals_cannot_regenerate(index, tmp_path):
    authority = dispositions.load_dispositions()
    row = authority.active_holds[index]
    ref = row["supersedes"][0]
    original = dispositions._read_yaml(authority.root / ref["ledger_path"])
    old = next(r for r in original["decisions"] if r["source_inventory"]["key"] == ref["source_key"])
    selected = tmp_path / "chosen-v1-only.yaml"
    write_yaml(selected, {"batch_id": original["batch_id"], "batch_label": original["batch_label"], "decisions": [old]})
    assert planner._decision_paths([selected]) == [selected]
    assert planner._approved_decisions([selected]) == []


@pytest.mark.parametrize("index", range(1, 6))
def test_stale_plan_and_stale_overlay_objects_fail_before_any_mutation(index):
    authority = dispositions.load_dispositions()
    record = authority.preservation["records"][index]
    row = authority.active_holds[index]
    entry = copy.deepcopy(record["entry"])
    manifest = {"entries": [{"lemma": "fixture-survivor", "url_slug": "fixture-survivor"}]}
    before = copy.deepcopy(manifest)
    plan = {
        "workflow": planner.WORKFLOW_ID,
        "proposed_manifest_additions": [
            {"lemma": "fixture-first", "manifest_entry": {"lemma": "fixture-first"}},
            {"source_inventory_key": row["origin"]["key"], "manifest_entry": entry},
        ],
        "production_outputs_updated": [],
    }
    with pytest.raises(dispositions.DispositionError, match="hold"):
        applier.apply_promotion_plan(manifest, plan)
    assert manifest == before
    decision = stale_decision(row)
    candidate = planner.CandidateMatch(entry, "needs_review", ())
    with pytest.raises(dispositions.DispositionError):
        overlay.apply_existing_provenance_overlay(manifest, {decision.source_key: candidate}, [decision])
    assert manifest == before


def test_saved_plan_held_skipped_row_is_also_refused():
    authority = dispositions.load_dispositions()
    key = authority.active_holds[1]["origin"]["key"]
    with pytest.raises(dispositions.DispositionError):
        applier.apply_promotion_plan(
            {"entries": []}, {"workflow": planner.WORKFLOW_ID, "skipped_existing": [{"source_inventory_key": key}]}
        )


def test_supplied_candidate_cannot_mask_held_origin_with_independent_key():
    authority = dispositions.load_dispositions()
    row = copy.deepcopy(authority.active_holds[1])
    row["origin"]["key"] = "independent-key"
    decision = stale_decision(row)
    candidate = planner.CandidateMatch(authority.preservation["records"][1]["entry"], "fixture", ())
    manifest = {"entries": []}
    with pytest.raises(dispositions.DispositionError):
        overlay.apply_existing_provenance_overlay(manifest, {decision.source_key: candidate}, [decision])
    assert manifest == {"entries": []}


@pytest.mark.parametrize("index", range(6))
def test_verifier_and_custom_self_check_writer_cannot_bypass_holds(index, tmp_path, capsys):
    authority = dispositions.load_dispositions()
    manifest = {"entries": [authority.preservation["records"][index]["entry"]]}
    path = tmp_path / "prospective.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False))
    original = path.read_bytes()
    assert verify_manifest.run(path, sample=0, baseline_path=None, run_conformance=False) == 2
    assert "DISPOSITION GATE" in capsys.readouterr().out
    with pytest.raises(dispositions.DispositionError):
        applier.write_manifest_if_changed(
            manifest,
            {"counts": {"promoted": 1}},
            manifest_path=path,
            fingerprint_path=tmp_path / "fingerprint.json",
            self_check=lambda _p: 0,
            fingerprint_writer=lambda _p: None,
        )
    assert path.read_bytes() == original
    assert not (tmp_path / "fingerprint.json").exists()


def test_missing_hold_blocks_verifier_even_with_conformance_disabled(tmp_path, monkeypatch):
    ledger, _, _ = make_authority(tmp_path)
    ledger["decisions"].pop()
    write_yaml(tmp_path / dispositions.LEDGER_PATH, ledger)
    monkeypatch.setattr(dispositions, "PROJECT_ROOT", tmp_path)
    path = tmp_path / "prospective.json"
    path.write_text('{"entries": []}')
    assert verify_manifest.run(path, sample=0, baseline_path=None) == 2
    with pytest.raises(dispositions.DispositionError):
        planner._approved_decisions([])


def test_real_built_origin_withheld_before_identity_loss():
    module = {"track": "b1", "slug": "society-and-media", "module_num": 73}
    raw = dispositions._parse_yaml((builder.CURRICULUM_ROOT / "b1/society-and-media/vocabulary.yaml").read_bytes())
    records = builder._load_built_vocab(module)
    assert len(records) == len(raw) - 1
    assert "достовірний" not in {r["lemma"] for r in records}
    assert all("_disposition_origin" in r for r in records)
    merged = {}
    builder._merge_lemma_records(merged, module, records)
    assert all("_disposition_origin" not in entry for entry in merged.values())


def test_raw_built_duplicate_and_changed_ingestion_refuse():
    authority = dispositions.load_dispositions()
    origin = authority.active_holds[0]["origin"]
    module = {"track": origin["track"], "slug": origin["module_slug"]}
    raw = dispositions._parse_yaml((authority.root / origin["path"]).read_bytes())[origin["index_zero_based"]]
    assert authority.withhold_built_row(module, origin["index_zero_based"], raw)
    with pytest.raises(dispositions.DispositionError):
        authority.withhold_built_row(module, 0, raw)
    with pytest.raises(dispositions.DispositionError):
        authority.withhold_built_row(module, origin["index_zero_based"], {**raw, "translation": "changed"})
    assert not authority.withhold_built_row({"track": "a1", "slug": "fixture"}, 0, raw)


@pytest.mark.parametrize("transformation", ["alias", "collision"])
def test_normalized_raw_origin_cannot_hide_inside_merging(transformation):
    authority = dispositions.load_dispositions()
    origin = authority.active_holds[0]["origin"]
    module = {"track": origin["track"], "slug": origin["module_slug"], "module_num": 73}
    record = {
        "lemma": "fixture-normalized" if transformation == "alias" else "fixture, normalized",
        "source": "built_vocabulary_normalized",
        "_disposition_origin": {
            "track": origin["track"],
            "module_slug": origin["module_slug"],
            "index_zero_based": origin["index_zero_based"],
        },
    }
    merged = {}
    with pytest.raises(dispositions.DispositionError, match="raw origin"):
        builder._merge_lemma_records(merged, module, [record])
    assert merged == {}


@pytest.mark.parametrize("index", range(6))
def test_independent_same_head_survives_but_opaque_or_mixed_payload_refuses(index):
    authority = dispositions.load_dispositions()
    hold = authority.active_holds[index]
    independent = {
        "lemma": hold["lemma"],
        "url_slug": hold["projection"]["url_slug"],
        "primary_source": "source_inventory_grow",
        "source_provenance": [
            {
                "source_id": "independent",
                "inventory_path": "data/lexicon/source-inventory/fixture.yaml",
                "source_locator": "fixture row",
            }
        ],
    }
    authority.validate_manifest({"entries": [independent]})
    with pytest.raises(dispositions.DispositionError, match="unknown"):
        authority.guard_entry({"lemma": hold["lemma"], "url_slug": hold["projection"]["url_slug"]})
    mixed = copy.deepcopy(independent)
    original = authority.preservation["records"][index]["entry"]
    if index:
        mixed["source_provenance"].extend(original["source_provenance"])
    else:
        mixed["course_usage"] = original["course_usage"]
    with pytest.raises(dispositions.DispositionError):
        authority.guard_entry(mixed)


def test_alias_and_slug_collision_variants_preserve_held_origin_provenance():
    authority = dispositions.load_dispositions()
    inventory = copy.deepcopy(authority.preservation["records"][1]["entry"])
    inventory.update(
        lemma="fixture-alias", url_slug="fixture-alias", atlas_normalizations=[{"source_lemma": inventory["lemma"]}]
    )
    with pytest.raises(dispositions.DispositionError):
        authority.guard_entry(inventory)
    built = {
        "lemma": "fixture",
        "url_slug": "fixture",
        "course_usage": [{"track": "b1", "slug": "society-and-media"}],
        "atlas_normalizations": [{"source_lemma": "достовірний"}],
    }
    with pytest.raises(dispositions.DispositionError):
        authority.guard_entry(built)
    built.pop("atlas_normalizations")
    built["slug_variants"] = ["достовірний"]
    with pytest.raises(dispositions.DispositionError):
        authority.guard_entry(built)


def test_changed_inventory_path_or_missing_id_is_not_independence():
    authority = dispositions.load_dispositions()
    entry = copy.deepcopy(authority.preservation["records"][1]["entry"])
    entry["source_provenance"][0]["inventory_path"] = "data/lexicon/source-inventory/moved.yaml"
    with pytest.raises(dispositions.DispositionError):
        authority.guard_entry(entry)
    entry["source_provenance"][0]["inventory_path"] = authority.active_holds[1]["origin"]["historical_path"]
    entry["source_provenance"][0].pop("source_id")
    with pytest.raises(dispositions.DispositionError):
        authority.guard_entry(entry)
    entry["source_provenance"][0]["source_inventory_key"] = authority.active_holds[1]["origin"]["key"]
    entry["lemma"] = "fixture-other"
    with pytest.raises(dispositions.DispositionError):
        authority.guard_entry(entry)


def test_final_build_check_runs_after_seed_and_collision_boundaries(monkeypatch):
    authority = dispositions.load_dispositions()
    held = copy.deepcopy(authority.preservation["records"][1]["entry"])
    monkeypatch.setattr(builder, "_vocabulary_modules", lambda: [])
    monkeypatch.setattr(builder, "_merge_seed_records", lambda rows: rows.update({"held": held}))
    monkeypatch.setattr(builder, "_merge_heritage_seed_records", lambda rows: None)
    with pytest.raises(dispositions.DispositionError):
        builder.build_manifest()


def test_all_four_producers_reach_the_guarded_central_boundaries():
    # Their full existing behavioral tests are also selected in the affected run.
    from scripts.lexicon import (
        curated_ohoiko_ulp_repromote,
        curated_textbook_jsonl_repromote,
        promote_atlas_6370_named_multiword_residual,
        promote_teacher_lesson_intake,
    )

    for producer in (
        curated_ohoiko_ulp_repromote,
        curated_textbook_jsonl_repromote,
        promote_atlas_6370_named_multiword_residual,
        promote_teacher_lesson_intake,
    ):
        assert producer.planner is planner
        assert producer.apply is applier


def test_overlay_cli_checks_mandatory_authority_before_writing(tmp_path, monkeypatch, capsys):
    from tests.test_apply_source_inventory_provenance import decision, match

    approved = decision("fixture-survivor")
    candidate = match("fixture-survivor")
    path, candidates, fingerprint = (
        tmp_path / "manifest.json",
        tmp_path / "candidates.json",
        tmp_path / "fingerprint.json",
    )
    candidates.write_text(json.dumps({"auto_merge": [candidate.entry], "needs_review": []}))
    manifest = {"entries": [{"lemma": approved.lemma, "primary_source": "built_vocabulary"}]}
    path.write_text(json.dumps(manifest))
    monkeypatch.setattr(planner, "_approved_decisions", lambda _paths: [approved])
    monkeypatch.setattr(overlay.promote, "verify_prospective_manifest", lambda _path: 0)
    monkeypatch.setattr(overlay.promote, "_embed_manifest_fingerprint", lambda value: None)
    monkeypatch.setattr(overlay, "write_fingerprint", lambda dest: dest.write_text("{}"))
    generated = []
    monkeypatch.setattr(overlay.review, "generate_review_candidates", lambda **kwargs: generated.append(kwargs))
    argv = ["--manifest", str(path), "--candidates", str(candidates), "--fingerprint", str(fingerprint)]
    original = path.read_bytes()
    assert overlay.main([*argv, "--generate-candidates", "--report"]) == 0
    assert generated and path.read_bytes() == original and not fingerprint.exists()
    assert overlay.main([*argv, "--write"]) == 0
    assert json.loads(path.read_bytes())["entries"][0]["source_provenance"] == candidate.entry["source_provenance"]
    assert fingerprint.read_text() == "{}"
    held = dispositions.load_dispositions().preservation["records"][1]["entry"]
    path.write_text(json.dumps({"entries": [manifest["entries"][0], held]}, ensure_ascii=False))
    original = path.read_bytes()
    assert overlay.main([*argv, "--write"]) == 2
    assert path.read_bytes() == original
    assert "error:" in capsys.readouterr().out


def test_independent_head_sharing_book_locator_is_conserved():
    authority = dispositions.load_dispositions()
    hold = authority.active_holds[2]
    origin = hold["origin"]
    entry = {
        "lemma": "нагорі",
        "url_slug": "нагорі",
        "primary_source": "source_inventory_grow",
        "source_provenance": [
            {
                "source_id": origin["source_id"],
                "inventory_path": origin["historical_path"],
                "source_locator": origin["source_locator"],
                "inventory_locator": "sources[1].headwords[934]",
            }
        ],
    }
    authority.validate_manifest({"entries": [entry]})
    entry["atlas_normalizations"] = [{"source_lemma": hold["lemma"]}]
    with pytest.raises(dispositions.DispositionError):
        authority.guard_entry(entry)


def test_loader_skips_nonrecords_and_missing_unrelated_file(tmp_path, monkeypatch):
    monkeypatch.setattr(builder, "CURRICULUM_ROOT", tmp_path)
    module = {"track": "fixture", "slug": "fixture", "module_num": 1}
    assert builder._load_built_vocab(module) == []
    path = tmp_path / "fixture/fixture/vocabulary.yaml"
    path.parent.mkdir(parents=True)
    path.write_text("- not a mapping\n- {}\n- lemma: fixture-head\n  translation: opaque\n")
    assert [r["lemma"] for r in builder._load_built_vocab(module)] == ["fixture-head"]


def test_overlay_missing_candidate_and_target_are_explicit_residuals():
    from tests.test_apply_source_inventory_provenance import decision, match

    approved = decision("fixture-head")
    manifest = {"entries": [{"lemma": approved.lemma}]}
    result = overlay.apply_existing_provenance_overlay(manifest, {}, [approved])
    assert result["counts"]["missing_candidates"] == 1 and "source_provenance" not in manifest["entries"][0]
    result = overlay.apply_existing_provenance_overlay(
        {"entries": [None, {}]}, {approved.source_key: match(approved.lemma)}, [approved]
    )
    assert result["counts"]["missing_manifest_entries"] == 1
    with pytest.raises(dispositions.DispositionError.__bases__[0]):
        overlay.apply_existing_provenance_overlay({"entries": None}, {}, [])


def test_unchanged_writer_leaves_files_and_callbacks_untouched(tmp_path):
    path = tmp_path / "manifest.json"
    path.write_text('{"entries": []}')
    result = {"counts": {"promoted": 0}}

    def unexpected_callback(_path):
        pytest.fail("no-op invoked writer/verification callback")

    assert (
        applier.write_manifest_if_changed(
            {"entries": []},
            result,
            manifest_path=path,
            fingerprint_path=tmp_path / "fingerprint.json",
            self_check=unexpected_callback,
            fingerprint_writer=unexpected_callback,
        )
        == result
    )
    assert path.read_text() == '{"entries": []}'
    assert not (tmp_path / "fingerprint.json").exists()
