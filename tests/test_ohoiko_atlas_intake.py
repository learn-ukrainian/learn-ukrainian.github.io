from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.audit.source_inventory_intake import read_source_inventory
from scripts.audit.source_inventory_review_decisions import validate_decision_file
from scripts.lexicon import atlas_intake_core as core
from scripts.lexicon import ohoiko_atlas_intake as intake

SYNTHETIC_WORDS_BOOK = """How to Use Anki

1. Open Anki and create a new deck.
2. Anki uses a spaced repetition algorithm to show you cards.

Most Useful Ukrainian Words

1.    а                                               and, but
      Я люблю́ готува́ти, а ти?
2.    авто́бус                                        bus
      Сашко́ ї́здить в шко́лу авто́бусом.
3.    але́                                            but (contrast)
      Я хочу́, але́ не мо́жу.
Кросворд №1
1. бана́н
"""


SYNTHETIC_VERB_PAGE = """\f№1
аналізува́ти | проаналізува́ти   Present / Future Stems: аналізуй / проаналізуй
      Я аналізу́ю цей текст.
\f№2
будува́ти | побудува́ти   Present / Future Stems: будуй / побудуй
      Ми будує́мо дім.
Index of Ukrainian Verbs
"""


SYNTHETIC_NOTE = """# Module fixture

Мати тут. Кіт читає.
"""


def fake_vesum(forms: list[str]) -> dict[str, list[dict[str, str]]]:
    rows = {
        "а": [{"lemma": "а", "pos": "conjunction"}],
        "автобус": [{"lemma": "автобус", "pos": "noun"}],
        "але": [{"lemma": "але", "pos": "conjunction"}],
        "аналізувати": [{"lemma": "аналізувати", "pos": "verb"}],
        "будувати": [{"lemma": "будувати", "pos": "verb"}],
        "кіт": [{"lemma": "кіт", "pos": "noun"}],
        "мати": [
            {"lemma": "мати", "pos": "noun"},
            {"lemma": "мати", "pos": "verb"},
        ],
        "читає": [{"lemma": "читати", "pos": "verb"}],
        "тут": [{"lemma": "тут", "pos": "adv"}],
    }
    return {form: rows.get(form, []) for form in forms}


def clear_heritage(lemma: str) -> dict[str, object]:
    return {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True,
        "sovietization_risk": 0,
    }


def write_private_fixture(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "1000-Ukrainian-Words-2.0-Ukrainian-Lessons-PDF-4mwsom.txt").write_text(
        SYNTHETIC_WORDS_BOOK,
        encoding="utf-8",
    )
    (root / "500+ Ukrainian Verbs - Ukrainian Lessons - PDF.txt").write_text(
        SYNTHETIC_VERB_PAGE,
        encoding="utf-8",
    )
    (root / "ULP 1-00 Lesson Notes (all in one file) (2023).txt").write_text(
        "Lesson Notes № 1\n\nКіт спить.\n",
        encoding="utf-8",
    )
    notes = root / "ohoiko-june-a1-book" / "notes"
    notes.mkdir(parents=True)
    (notes / "fixture-note.md").write_text(SYNTHETIC_NOTE, encoding="utf-8")


def test_discovers_catalog_counts_without_private_paths(tmp_path: Path) -> None:
    private_root = tmp_path / "private"
    write_private_fixture(private_root)
    june_notes_root = private_root / "ohoiko-june-a1-book" / "notes"

    units = intake.discover_source_units(private_root=private_root, june_notes_root=june_notes_root)
    counts = intake.inventory_counts(units)

    assert counts == {
        "source_units_total": 9,
        "source_units_available": 4,
        "book_sources_total": 2,
        "book_sources_available": 2,
        "ulp_note_sources_total": 6,
        "ulp_note_sources_available": 1,
        "june_note_sources_total": 1,
        "june_note_sources_available": 1,
    }
    public_json = json.dumps([intake._public_source_unit(unit) for unit in units], ensure_ascii=False)
    assert "private" not in public_json
    assert "fixture-note" not in public_json
    assert "1000-Ukrainian-Words" not in public_json


def test_build_intake_classifies_book_and_running_text_candidates(tmp_path: Path) -> None:
    private_root = tmp_path / "private"
    write_private_fixture(private_root)
    june_notes_root = private_root / "ohoiko-june-a1-book" / "notes"

    result = intake.build_ohoiko_intake(
        private_root=private_root,
        june_notes_root=june_notes_root,
        project_root=tmp_path,
        manifest_lemma_keys={"кіт"},
        existing_ledger_keys=set(),
        committed_inventory_keys=set(),
        vesum_lookup=fake_vesum,
        heritage_lookup=clear_heritage,
        inventory_path="data/lexicon/source-inventory/fixture-ohoiko.json",
    )

    by_lemma = {candidate.lemma: candidate for candidate in result.candidates}
    assert by_lemma["автобус"].classification == "auto_approve"
    assert by_lemma["автобус"].gloss == "bus"
    assert by_lemma["кіт"].classification == "reject"
    assert by_lemma["кіт"].reasons == ("already_in_atlas",)
    assert by_lemma["мати"].classification == "review_queue"
    assert by_lemma["мати"].reasons == ("vesum_ambiguous_pos",)
    assert by_lemma["читати"].classification == "review_queue"
    assert by_lemma["читати"].reasons == ("missing_english_anchor",)
    assert all("::" in record.source_locator for candidate in result.candidates for record in candidate.records)
    assert all(record.source_path is None for candidate in result.candidates for record in candidate.records)


def test_rejects_committed_inventory_lemmas(tmp_path: Path) -> None:
    private_root = tmp_path / "private"
    write_private_fixture(private_root)
    inventory_dir = tmp_path / "registry" / "lexicon" / "source-inventory"
    inventory_dir.mkdir(parents=True)
    (inventory_dir / "ohoiko-abetka-keywords.yaml").write_text(
        "version: 1\n"
        "kind: atlas_source_inventory\n"
        "sources:\n"
        "  - id: ohoiko-fixture\n"
        "    source_family: ohoiko\n"
        "    extraction_mode: curated_headword\n"
        "    title: Fixture\n"
        "    headwords:\n"
        "      - lemma: автобус\n"
        "        pos: noun\n"
        "        gloss: bus\n",
        encoding="utf-8",
    )

    result = intake.build_ohoiko_intake(
        private_root=private_root,
        june_notes_root=private_root / "ohoiko-june-a1-book" / "notes",
        project_root=tmp_path,
        manifest_lemma_keys=set(),
        existing_ledger_keys=set(),
        vesum_lookup=fake_vesum,
        heritage_lookup=clear_heritage,
    )

    candidate = next(row for row in result.candidates if row.lemma == "автобус")
    assert candidate.classification == "reject"
    assert candidate.reasons == ("already_in_committed_source_inventory",)


def test_report_payload_omits_raw_corpus_text(tmp_path: Path) -> None:
    private_root = tmp_path / "private"
    write_private_fixture(private_root)
    result = intake.build_ohoiko_intake(
        private_root=private_root,
        june_notes_root=private_root / "ohoiko-june-a1-book" / "notes",
        project_root=tmp_path,
        manifest_lemma_keys=set(),
        existing_ledger_keys=set(),
        vesum_lookup=fake_vesum,
        heritage_lookup=clear_heritage,
    )
    serialized = json.dumps(result.report_payload(policy="fixture"), ensure_ascii=False)

    assert "Я люблю" not in serialized
    assert "Lesson Notes" not in serialized
    assert "private" not in serialized
    assert result.report_payload(policy="fixture")["surface_admission"]["daily_word"] == "unchanged"


def test_writes_parser_compatible_inventory_and_decision_ledger(tmp_path: Path) -> None:
    private_root = tmp_path / "private"
    write_private_fixture(private_root)
    inventory_path = "data/lexicon/source-inventory/fixture-ohoiko.json"
    inventory_out = tmp_path / inventory_path
    ledger_out = tmp_path / "fixture-ohoiko-ledger.yaml"

    result = intake.build_ohoiko_intake(
        private_root=private_root,
        june_notes_root=private_root / "ohoiko-june-a1-book" / "notes",
        project_root=tmp_path,
        manifest_lemma_keys=set(),
        existing_ledger_keys=set(),
        vesum_lookup=fake_vesum,
        heritage_lookup=clear_heritage,
        inventory_path=inventory_path,
    )
    core.assert_ledger_inventory_destination(inventory_out, inventory_path, project_root=tmp_path)
    core.write_flat_source_inventory(result.records, inventory_out)
    ledger = core.build_ledger_append_payload(
        result,
        batch_id="ohoiko-fixture-intake",
        batch_label="ohoiko fixture corpus intake",
        reviewed_at="2026-07-14",
        reviewer="ohoiko-intake-automation",
        sense_note=intake.OHOKO_LEDGER_SENSE_NOTE,
    )
    core.write_yaml_payload(ledger, ledger_out)

    records = read_source_inventory(inventory_out, project_root=tmp_path)
    source_index = {(record.lemma, record.inventory_path, record.source_locator): record for record in records}
    summary = validate_decision_file(ledger_out, source_index=source_index)

    assert summary["rows"] == len(result.candidates)
    assert ledger["production_outputs_updated"] == []
    auto_row = next(row for row in ledger["decisions"] if row["lemma"] == "автобус")
    assert auto_row["decision"] == "approve_for_publish"
    assert auto_row["approved_pos"] == "noun"
    assert auto_row["approved_gloss"] == "bus"


def test_heritage_rejection_and_uncertainty_are_fail_closed() -> None:
    common = {
        "lemma": "тест",
        "pos": "noun",
        "gloss": "test",
        "metadata_reasons": (),
        "atlas_keys": set(),
        "ledger_keys": set(),
    }

    reject, reject_reasons, _ = core.classify_resolved_candidate(
        **common,
        heritage_lookup=lambda _: {"classification": "russianism", "is_russianism": True},
    )
    shadow, shadow_reasons, _ = core.classify_resolved_candidate(
        **common,
        heritage_lookup=lambda _: {"classification": "standard", "russian_shadow": True},
    )

    assert (reject, reject_reasons) == ("reject", ("heritage_russianism",))
    assert (shadow, shadow_reasons) == ("review_queue", ("heritage_russian_shadow",))


def test_cli_rejects_ledger_output_outside_source_inventory_directory(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("TMPDIR", raising=False)
    result = intake.main(
        [
            "--private-root",
            str(tmp_path / "missing-private"),
            "--ledger-out",
            str(tmp_path / "ledger.yaml"),
            "--batch-id",
            "fixture",
            "--batch-label",
            "fixture",
            "--reviewed-at",
            "2026-07-14",
            "--inventory-out",
            str(core.PROJECT_ROOT / "batch_state" / "cli-fixture-inventory.json"),
            "--report-out",
            str(tmp_path / "report.json"),
            "--inventory-path",
            "batch_state/cli-fixture-inventory.json",
        ]
    )

    assert result == 2
    assert "data/lexicon/source-inventory" in capsys.readouterr().err
    assert not (tmp_path / "report.json").exists()
    assert not (tmp_path / "ledger.yaml").exists()


def test_core_resolve_forms_capitalized_and_hyphenated_proper_nouns() -> None:
    def fake_cap_vesum(forms: list[str]) -> dict[str, list[dict[str, str]]]:
        data = {
            "Олена": [{"lemma": "Олена", "pos": "noun"}],
            "Івано-Франківськ": [{"lemma": "Івано-Франківськ", "pos": "noun"}],
        }
        return {form: data.get(form, []) for form in forms}

    resolutions = core.resolve_forms(["олена", "івано-франківськ", "невідоме"], vesum_lookup=fake_cap_vesum)
    assert resolutions["олена"].lemma == "Олена"
    assert resolutions["олена"].pos == "noun"
    assert resolutions["олена"].reason is None
    assert resolutions["івано-франківськ"].lemma == "Івано-Франківськ"
    assert resolutions["івано-франківськ"].pos == "noun"
    assert resolutions["івано-франківськ"].reason is None
    assert resolutions["невідоме"].lemma is None
    assert resolutions["невідоме"].reason == "vesum_unrecognized"


def empty_intake_cli_args(tmp_path: Path) -> list[str]:
    """Use synthetic empty inputs; never inspect a corpus or a live database."""
    source = tmp_path / "absent-private"
    return ["--private-root", str(source), "--june-notes-root", str(source / "notes")]


@pytest.mark.parametrize(
    "inventory_override,report_override", [(False, False), (True, False), (False, True), (True, True)]
)
def test_caller_scratch_defaults_and_override_readback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys,
    inventory_override: bool,
    report_override: bool,
) -> None:
    argv = empty_intake_cli_args(tmp_path)
    baseline_inventory, baseline_report = tmp_path / "baseline.json", tmp_path / "baseline-report.json"
    monkeypatch.delenv("TMPDIR", raising=False)
    assert intake.main([*argv, "--inventory-out", str(baseline_inventory), "--report-out", str(baseline_report)]) == 0
    expected_inventory, expected_report = baseline_inventory.read_bytes(), baseline_report.read_bytes()
    capsys.readouterr()
    # Reuse the imported API after the caller changes roots; prior outputs survive.
    for root_name in ("producer-consumer", "distinct-held-out-root"):
        root = tmp_path / root_name
        root.mkdir()
        monkeypatch.setenv("TMPDIR", str(root))
        inventory = tmp_path / f"{root_name}-inventory.json" if inventory_override else root / intake.INVENTORY_FILENAME
        report = tmp_path / f"{root_name}-report.json" if report_override else root / intake.REPORT_FILENAME
        overrides = ({"inventory_out": inventory} if inventory_override else {}) | (
            {"report_out": report} if report_override else {}
        )
        assert intake.resolve_output_paths(**overrides) == (inventory, report)
        call_args = argv.copy()
        for key, path in overrides.items():
            call_args.extend(["--" + key.replace("_", "-"), str(path)])
        assert intake.main(call_args) == 0
        output = capsys.readouterr().out
        assert f"inventory_out: {inventory}" in output and f"report_out: {report}" in output
        assert inventory.read_bytes() == expected_inventory == b"[\n\n]\n"
        assert report.read_bytes() == expected_report
        assert read_source_inventory(inventory) == []
        payload = json.loads(report.read_bytes())
        assert payload["production_outputs_updated"] == []
        assert set(payload["surface_admission"].values()) == {"unchanged"}
        assert payload["counts"]["deduped_candidates"] == 0
        assert str(tmp_path) not in report.read_text()
        assert intake.build_parser().parse_args(call_args).inventory_path == intake.DEFAULT_INVENTORY_PATH
        assert set(root.iterdir()) == ({inventory} if not inventory_override else set()) | (
            {report} if not report_override else set()
        )
    if not inventory_override:
        assert (tmp_path / "producer-consumer" / intake.INVENTORY_FILENAME).read_bytes() == expected_inventory
    if not report_override:
        assert (tmp_path / "producer-consumer" / intake.REPORT_FILENAME).read_bytes() == expected_report


@pytest.mark.parametrize("root_kind", ["unset", "empty", "relative", "missing", "file"])
@pytest.mark.parametrize("inventory_override,report_override", [(False, False), (True, False), (False, True)])
def test_invalid_caller_root_refuses_before_intake(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys,
    root_kind: str,
    inventory_override: bool,
    report_override: bool,
) -> None:
    if root_kind == "unset":
        monkeypatch.delenv("TMPDIR", raising=False)
    else:
        file = tmp_path / "file"
        file.write_text("sentinel", encoding="utf-8")
        value = {"empty": "", "relative": "relative", "missing": str(tmp_path / "missing"), "file": str(file)}[
            root_kind
        ]
        monkeypatch.setenv("TMPDIR", value)
    monkeypatch.setattr(intake, "build_ohoiko_intake", lambda **kwargs: pytest.fail("must refuse before intake"))
    overrides = ({"inventory_out": tmp_path / "override-inventory.json"} if inventory_override else {}) | (
        {"report_out": tmp_path / "override-report.json"} if report_override else {}
    )
    with pytest.raises(ValueError, match="TMPDIR"):
        intake.resolve_output_paths(**overrides)
    argv = []
    for key, path in overrides.items():
        argv.extend(["--" + key.replace("_", "-"), str(path)])
    assert intake.main(argv) == 2
    assert "TMPDIR" in capsys.readouterr().err
    assert not (tmp_path / "missing").exists()
    assert not any(path.exists() for path in overrides.values())


def test_help_and_argument_errors_need_no_caller_root(monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    monkeypatch.delenv("TMPDIR", raising=False)
    args = intake.build_parser().parse_args([])
    assert args.inventory_out is None and args.report_out is None
    assert args.inventory_path == intake.DEFAULT_INVENTORY_PATH
    with pytest.raises(SystemExit) as exc:
        intake.main(["--help"])
    assert exc.value.code == 0
    help_text = capsys.readouterr().out
    for required in ("$TMPDIR", "caller", "Outputs:", "Exit codes:", "Related:"):
        assert required in help_text
    with pytest.raises(SystemExit) as exc:
        intake.main(["--ledger-out", "ledger.yaml"])
    assert exc.value.code == 2
    assert "--batch-id" in capsys.readouterr().err
