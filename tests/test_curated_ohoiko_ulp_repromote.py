from __future__ import annotations

import inspect
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from scripts.lexicon import curated_ohoiko_ulp_repromote as ohoiko_repromote
from scripts.lexicon import curated_textbook_jsonl_repromote as textbook_repromote
from scripts.lexicon import ohoiko_paired_headword_split as paired_split

_MODULES = (ohoiko_repromote, textbook_repromote)
_ALL_GLOSS_FILL_MODULES = (*_MODULES, paired_split)


@pytest.mark.parametrize("module", _ALL_GLOSS_FILL_MODULES, ids=lambda m: m.__name__)
def test_module_never_reads_sum11_table(module) -> None:
    """#7453: СУМ-11 (Soviet-era) is banned on Atlas, including as inventory
    gloss fill. No curated gloss-fill script may query the offline ``sum11``
    SQL table anywhere in its source."""
    source = inspect.getsource(module)
    assert "sum11" not in source.lower()
    assert not hasattr(module, "_sum11_gloss")


@pytest.mark.parametrize("module", _MODULES, ids=lambda m: m.__name__)
def test_sum20_vts_gloss_prefers_sum20(monkeypatch, module) -> None:
    monkeypatch.setattr(
        module,
        "_sum20_definition_card",
        lambda lemma: {"definitions": ["Символ держави."]},
    )
    monkeypatch.setattr(
        module,
        "_vts_definition_card",
        lambda lemma: {"definitions": ["ВТС text that must not be used."]},
    )

    assert module._sum20_vts_gloss("прапор") == "Символ держави."


@pytest.mark.parametrize("module", _MODULES, ids=lambda m: m.__name__)
def test_sum20_vts_gloss_falls_back_to_vts_when_sum20_missing(monkeypatch, module) -> None:
    """СУМ-20 volumes 17-20 (С-Я) are unpublished — ВТС fills the gap. Never
    СУМ-11, even though it may have a matching headword."""
    monkeypatch.setattr(module, "_sum20_definition_card", lambda lemma: None)
    monkeypatch.setattr(
        module,
        "_vts_definition_card",
        lambda lemma: {"definitions": ["вишита сорочка"]},
    )

    assert module._sum20_vts_gloss("вишиванка") == "вишита сорочка"


@pytest.mark.parametrize("module", _MODULES, ids=lambda m: m.__name__)
def test_sum20_vts_gloss_none_when_neither_available(monkeypatch, module) -> None:
    """No СУМ-11 fallback: if neither modern dictionary has an entry, the
    gloss helper returns None rather than reaching for the Soviet-era source."""
    monkeypatch.setattr(module, "_sum20_definition_card", lambda lemma: None)
    monkeypatch.setattr(module, "_vts_definition_card", lambda lemma: None)

    assert module._sum20_vts_gloss("ґаджет") is None


@pytest.mark.parametrize("module", _MODULES, ids=lambda m: m.__name__)
def test_sum20_vts_gloss_truncates_long_definitions(monkeypatch, module) -> None:
    long_text = "а" * 200
    monkeypatch.setattr(module, "_sum20_definition_card", lambda lemma: {"definitions": [long_text]})
    monkeypatch.setattr(module, "_vts_definition_card", lambda lemma: None)

    gloss = module._sum20_vts_gloss("довге-слово")

    assert gloss is not None
    assert len(gloss) == 180
    assert gloss.endswith("...")


def test_collect_ulp_headwords_signature_has_no_sum_connection() -> None:
    """The ULP inventory builder no longer needs a sqlite connection now that
    gloss fill goes through _sum20_vts_gloss instead of a sum11 query."""
    params = inspect.signature(ohoiko_repromote.collect_ulp_headwords).parameters
    assert "sum_conn" not in params


def test_mine_headwords_signature_has_no_sum_connection() -> None:
    params = inspect.signature(textbook_repromote.mine_headwords).parameters
    assert "sum_conn" not in params


def test_resolve_leg_pos_gloss_signature_has_no_sum_connection() -> None:
    params = inspect.signature(paired_split.resolve_leg_pos_gloss).parameters
    assert "sum_conn" not in params


def test_resolve_leg_pos_gloss_falls_back_to_sum20_vts_gloss(monkeypatch) -> None:
    """A split leg with no parent gloss fills from СУМ-20/ВТС via the shared
    helper, never from СУМ-11 (#7453)."""
    monkeypatch.setattr(paired_split, "_vesum_pos", lambda lemma: "noun")
    monkeypatch.setattr(paired_split.promo, "_sum20_vts_gloss", lambda lemma: "офіційний символ")

    pos, gloss = paired_split.resolve_leg_pos_gloss({"lemma": "прапор"})

    assert pos == "noun"
    assert gloss == "офіційний символ"


def test_resolve_leg_pos_gloss_prefers_parent_gloss_over_dictionary(monkeypatch) -> None:
    monkeypatch.setattr(paired_split, "_vesum_pos", lambda lemma: "noun")
    monkeypatch.setattr(
        paired_split.promo,
        "_sum20_vts_gloss",
        lambda lemma: pytest.fail("must not be called when a parent gloss exists"),
    )

    _pos, gloss = paired_split.resolve_leg_pos_gloss({"lemma": "прапор", "gloss": "flag"})

    assert gloss == "flag"


def test_resolve_leg_pos_gloss_returns_honest_empty_string_not_lemma(monkeypatch) -> None:
    """#7458: when no parent gloss and no СУМ-20/ВТС hit, the gloss must be an
    honest empty string — never the bare Cyrillic lemma reused as a fake EN
    gloss, and never СУМ-11. Callers use the empty string to hold the leg out
    of promotion (never promote a skeleton)."""
    monkeypatch.setattr(paired_split, "_vesum_pos", lambda lemma: "noun")
    monkeypatch.setattr(paired_split.promo, "_sum20_vts_gloss", lambda lemma: None)

    pos, gloss = paired_split.resolve_leg_pos_gloss({"lemma": "ґаджет"})

    assert pos == "noun"
    assert gloss == ""


@pytest.mark.parametrize("write", [False, True], ids=["plan-only", "apply"])
@pytest.mark.parametrize(
    "candidate_override,plan_override,has_tmpdir",
    [(False, False, True), (True, False, True), (False, True, True), (True, True, True), (True, True, False)],
)
def test_temp_artifacts_destination_readback_and_lifetime(
    monkeypatch,
    tmp_path: Path,
    write: bool,
    candidate_override: bool,
    plan_override: bool,
    has_tmpdir: bool,
) -> None:
    """Synthetic producer→planner→application proof; caller retains both JSON artifacts."""
    task_root = tmp_path / "task"
    task_root.mkdir()
    if has_tmpdir:
        monkeypatch.setenv("TMPDIR", str(task_root))
    else:
        monkeypatch.delenv("TMPDIR", raising=False)
    candidates = (
        (tmp_path / "explicit-candidates.json")
        if candidate_override
        else task_root / ohoiko_repromote.CANDIDATES_FILENAME
    )
    plan_out = (tmp_path / "explicit-plan.json") if plan_override else task_root / ohoiko_repromote.PLAN_FILENAME
    inventory, decisions = tmp_path / "inventory.yaml", tmp_path / "decisions.yaml"
    manifest, fingerprint = tmp_path / "manifest.json", tmp_path / "fingerprint.json"
    manifest.write_text('{"entries": []}', encoding="utf-8")
    fingerprint.write_text("unchanged", encoding="utf-8")
    row = {"lemma": "synthetic-token", "pos": "noun", "gloss": "synthetic gloss", "source_family": "ohoiko"}
    monkeypatch.setattr(ohoiko_repromote, "collect_book_headwords", lambda: [row])
    monkeypatch.setattr(ohoiko_repromote, "collect_ulp_headwords", lambda **kwargs: [])

    def write_inventory(rows, path):
        assert path == inventory
        path.write_text(yaml.safe_dump(list(rows)), encoding="utf-8")

    def write_decisions(rows, path, *, inventory_rel):
        assert path == decisions
        assert inventory_rel == ohoiko_repromote.INV_REL
        path.write_text(yaml.safe_dump(list(rows)), encoding="utf-8")

    monkeypatch.setattr(ohoiko_repromote, "write_inventory", write_inventory)
    monkeypatch.setattr(ohoiko_repromote, "write_decisions", write_decisions)
    monkeypatch.setattr(ohoiko_repromote, "read_source_inventory", lambda path, **kwargs: [row])
    monkeypatch.setattr(
        ohoiko_repromote, "source_inventory_candidates", lambda records: [SimpleNamespace(**row, source_provenance=[])]
    )
    monkeypatch.setattr(ohoiko_repromote, "build_skeleton_entry", lambda lemma: {"lemma": lemma})
    monkeypatch.setattr(ohoiko_repromote, "verify_word", lambda lemma: [])
    # Freeze variable payload metadata; exercise the actual candidate serializer.
    monkeypatch.setattr(ohoiko_repromote, "build_payload", lambda **kwargs: {"auto_merge": kwargs["auto_merge"]})
    entry = {
        "lemma": row["lemma"],
        "pos": row["pos"],
        "gloss": row["gloss"],
        "primary_source": "source_inventory_grow",
        "source_provenance": [],
        "heritage_status": {
            "classification": "unknown",
            "attestations": [],
            "is_russianism": False,
            "russian_shadow": False,
            "vesum_attested": False,
            "calque_warning": None,
            "warning_severity": "none",
        },
    }
    payload = {"auto_merge": [entry], "generated_from": "curated_ohoiko_ulp_repromote.v1"}
    expected_candidate_bytes = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode()
    plan = {"counts": {"proposed_additions": 1}, "proposed_manifest_additions": [entry]}
    calls = []

    def build_plan(*, candidates_path, decision_files, manifest_path):
        assert candidates_path == candidates
        assert candidates_path.read_bytes() == expected_candidate_bytes
        assert yaml.safe_load(inventory.read_text()) == [row]
        assert decision_files == [decisions]
        assert yaml.safe_load(decisions.read_text()) == [row]
        assert manifest_path == manifest
        calls.append("plan")
        return plan

    def apply_plan(manifest_payload, actual_plan):
        assert actual_plan == plan
        assert json.loads(plan_out.read_text()) == plan
        calls.append("apply")
        return {"promoted_entries": [entry], "counts": {"promoted": 1, "skipped_existing": 0}}

    def write_manifest(manifest_payload, result, *, manifest_path, fingerprint_path, self_check):
        assert manifest_path == manifest and fingerprint_path == fingerprint
        manifest_path.write_text(json.dumps({"entries": [entry]}), encoding="utf-8")
        assert self_check(manifest_path) == 0
        fingerprint_path.write_text("updated", encoding="utf-8")
        calls.append("write")
        return result

    monkeypatch.setattr(ohoiko_repromote.planner, "build_promotion_plan", build_plan)
    monkeypatch.setattr(ohoiko_repromote.apply, "apply_promotion_plan", apply_plan)
    monkeypatch.setattr(ohoiko_repromote.apply, "write_manifest_if_changed", write_manifest)
    checked = []
    monkeypatch.setattr(ohoiko_repromote.apply, "_validate_privacy_safe_provenance", checked.append)
    argv = [
        "--apply",
        "--report",
        "--inventory-out",
        str(inventory),
        "--decisions-out",
        str(decisions),
        "--manifest",
        str(manifest),
        "--fingerprint",
        str(fingerprint),
    ]
    if candidate_override:
        argv += ["--candidates-out", str(candidates)]
    if plan_override:
        argv += ["--plan-out", str(plan_out)]
    if write:
        argv.append("--write")
    assert ohoiko_repromote.main(argv) == 0
    assert calls == (["plan", "apply", "write"] if write else ["plan"])
    assert checked == ([entry] if write else [])
    assert candidates.read_bytes() == expected_candidate_bytes
    assert plan_out.read_bytes() == (json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    assert json.loads(manifest.read_text()) == {"entries": [entry] if write else []}
    assert fingerprint.read_text() == ("updated" if write else "unchanged")
    assert set(task_root.iterdir()) == ({candidates} if not candidate_override else set()) | (
        {plan_out} if not plan_override else set()
    )


def test_apply_plan_resolves_default_at_call_time(monkeypatch, tmp_path: Path) -> None:
    plan = {"counts": {"proposed_additions": 0}}
    monkeypatch.setattr(ohoiko_repromote.planner, "build_promotion_plan", lambda **kwargs: plan)
    for name in ("first", "second"):
        root = tmp_path / name
        root.mkdir()
        monkeypatch.setenv("TMPDIR", str(root))
        assert ohoiko_repromote.apply_plan(
            candidates=tmp_path / "candidates",
            decisions=tmp_path / "decisions",
            manifest=tmp_path / "manifest",
            fingerprint=tmp_path / "fingerprint",
            write=False,
        ) == {
            "plan": plan["counts"],
            "wrote": False,
        }
        assert json.loads((root / ohoiko_repromote.PLAN_FILENAME).read_text()) == plan
    assert (tmp_path / "first" / ohoiko_repromote.PLAN_FILENAME).is_file()


@pytest.mark.parametrize("tmpdir", [None, "relative", "missing"])
def test_invalid_temp_root_stops_before_collection(monkeypatch, tmp_path: Path, capsys, tmpdir) -> None:
    if tmpdir is None:
        monkeypatch.delenv("TMPDIR", raising=False)
    else:
        monkeypatch.setenv("TMPDIR", str(tmp_path / "missing") if tmpdir == "missing" else tmpdir)
    monkeypatch.setattr(ohoiko_repromote, "collect_book_headwords", lambda: pytest.fail("must resolve scratch first"))
    with pytest.raises(SystemExit) as exc:
        ohoiko_repromote.main(["--apply"])
    assert exc.value.code == 2
    assert "TMPDIR" in capsys.readouterr().err


def test_parser_preserves_committed_defaults_and_help_without_tmpdir(monkeypatch, capsys) -> None:
    monkeypatch.delenv("TMPDIR", raising=False)
    args = ohoiko_repromote.build_parser().parse_args([])
    assert args.inventory_out == ohoiko_repromote.DEFAULT_INVENTORY
    assert args.decisions_out == ohoiko_repromote.DEFAULT_DECISIONS
    assert args.manifest == ohoiko_repromote.DEFAULT_MANIFEST
    assert args.fingerprint == ohoiko_repromote.DEFAULT_FINGERPRINT
    with pytest.raises(SystemExit) as exc:
        ohoiko_repromote.main(["--help"])
    assert exc.value.code == 0
    help_text = capsys.readouterr().out
    assert "--plan-out" in help_text and "$TMPDIR" in help_text and "caller" in help_text


def test_explicit_plan_needs_no_temp_root_and_keeps_publication_guard(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("TMPDIR", raising=False)
    plan = {"counts": {"proposed_additions": 0}}
    monkeypatch.setattr(ohoiko_repromote.planner, "build_promotion_plan", lambda **kwargs: plan)
    kwargs = {
        "candidates": tmp_path / "candidates",
        "decisions": tmp_path / "decisions",
        "manifest": tmp_path / "manifest",
        "fingerprint": tmp_path / "fingerprint",
        "write": False,
    }
    out = tmp_path / "plan.json"
    ohoiko_repromote.apply_plan(**kwargs, plan_out=out)
    assert json.loads(out.read_text()) == plan
    with pytest.raises(ohoiko_repromote.planner.SourceInventoryError):
        ohoiko_repromote.apply_plan(**kwargs, plan_out=ohoiko_repromote.DEFAULT_MANIFEST)


@pytest.mark.parametrize("plan_override", [False, True], ids=["default", "explicit"])
def test_failed_publication_gate_retains_plan_without_durable_writes(monkeypatch, tmp_path: Path, plan_override) -> None:
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    candidates = tmp_path / "candidates.json"
    candidates.write_text('{"auto_merge": []}', encoding="utf-8")
    manifest, fingerprint = tmp_path / "manifest.json", tmp_path / "fingerprint.json"
    manifest.write_text('{"entries": []}', encoding="utf-8")
    fingerprint.write_text("unchanged", encoding="utf-8")
    before = {path: path.read_bytes() for path in (candidates, manifest, fingerprint)}
    entry = {"lemma": "synthetic-token", "pos": "noun", "gloss": "", "source_provenance": []}
    plan = {"counts": {"proposed_additions": 1}, "proposed_manifest_additions": [entry]}
    monkeypatch.setattr(ohoiko_repromote.planner, "build_promotion_plan", lambda **kwargs: plan)

    def apply_plan(payload, actual_plan):
        assert actual_plan == plan
        payload["entries"].append(entry)
        return {"promoted_entries": [entry], "counts": {"promoted": 1, "skipped_existing": 0}}

    monkeypatch.setattr(ohoiko_repromote.apply, "apply_promotion_plan", apply_plan)
    monkeypatch.setattr(
        ohoiko_repromote.apply,
        "_write_fingerprint_sidecar",
        lambda path: pytest.fail("failed validation must not publish the fingerprint"),
    )
    plan_out = tmp_path / ("explicit-plan.json" if plan_override else ohoiko_repromote.PLAN_FILENAME)
    with pytest.raises(ohoiko_repromote.apply.promote.SelfCheckError):
        ohoiko_repromote.apply_plan(
            candidates=candidates,
            decisions=tmp_path / "decisions.yaml",
            manifest=manifest,
            fingerprint=fingerprint,
            write=True,
            plan_out=plan_out if plan_override else None,
        )
    assert json.loads(plan_out.read_text()) == plan
    assert all(path.read_bytes() == content for path, content in before.items())
