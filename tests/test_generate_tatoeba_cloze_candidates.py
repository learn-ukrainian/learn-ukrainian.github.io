from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.audit.generate_practice_deck import JsonVesumVerifier, read_manifest
from scripts.audit.generate_tatoeba_cloze_candidates import (
    DEFAULT_LICENSE,
    SUPPORTED_CASE_RULE_SET,
    GeneratorConfig,
    build_yield_summary,
    format_yield_report_markdown,
    generate_tatoeba_cloze_candidates,
    main,
    read_cc0_sentence_ids,
    read_tatoeba_pairs,
    read_tatoeba_sentences,
)

FIXTURES = Path("tests/fixtures/tatoeba-cloze")
MANIFEST = FIXTURES / "atlas-manifest.json"
VESUM = FIXTURES / "vesum.json"
UK_SENTENCES = FIXTURES / "ukr_sentences.tsv"
EN_SENTENCES = FIXTURES / "eng_sentences.tsv"
LINKS = FIXTURES / "links.csv"


def _report(config: GeneratorConfig | None = None):
    entries = read_manifest(MANIFEST)
    pairs = read_tatoeba_pairs(UK_SENTENCES, EN_SENTENCES, LINKS)
    verifier = JsonVesumVerifier.from_path(VESUM)
    return generate_tatoeba_cloze_candidates(
        entries,
        pairs,
        verifier,
        config,
        russian_shadow_checker=lambda _token: False,
    )


def _candidate_sentence_ids(report) -> set[int]:
    return {candidate["provenance"]["sentenceId"] for candidate in report.candidates}


def test_tatoeba_manifest_fixture_uses_real_ukrainian_case_keys() -> None:
    entries = read_manifest(MANIFEST)
    cases = entries[0]["enrichment"]["morphology"]["paradigm"]["cases"]

    assert set(cases) == {"називний", "знахідний", "місцевий"}
    assert cases["знахідний"]["singular"] == "книгу"
    assert cases["місцевий"]["plural"] == "книгах"


def test_tatoeba_ingest_requires_en_pair_and_carries_authors_licenses() -> None:
    pairs = read_tatoeba_pairs(UK_SENTENCES, EN_SENTENCES, LINKS)
    pair_by_id = {pair.uk.sentence_id: pair for pair in pairs}

    assert 1013 not in pair_by_id
    assert pair_by_id[1001].uk.author == "olena_uk"
    assert pair_by_id[1001].uk.license == "CC-BY 2.0 FR"
    assert pair_by_id[1001].en.sentence_id == 2001
    assert pair_by_id[1001].en.author == "alice_en"
    assert pair_by_id[1002].uk.license == "CC0"
    assert pair_by_id[1003].en.sentence_id == 2003


def test_tatoeba_generator_emits_supported_case_rules_single_blank_and_sentence_cefr() -> None:
    report = _report()
    sentence_ids = _candidate_sentence_ids(report)

    assert {1001, 1002, 1003, 1012}.issubset(sentence_ids)
    assert all(candidate["caseRuleId"] in SUPPORTED_CASE_RULE_SET for candidate in report.candidates)
    assert {candidate["caseRuleId"] for candidate in report.candidates} == SUPPORTED_CASE_RULE_SET
    assert all(candidate["sentence"].count("___") == 1 for candidate in report.candidates)
    assert all(candidate.get("cefr") == "A1" for candidate in report.candidates)
    assert all(candidate["provenance"]["status"] == "tatoeba" for candidate in report.candidates)
    assert all(candidate["provenance"]["path"].startswith("tatoeba:") for candidate in report.candidates)
    assert all(candidate["provenance"].get("enAuthor") for candidate in report.candidates)


def test_tatoeba_prefilters_surface_not_equal_base_lemma_and_single_target() -> None:
    report = _report()
    sentence_ids = _candidate_sentence_ids(report)

    assert report.rejections["surface_equals_lemma"] > 0
    assert 1004 not in sentence_ids
    assert report.rejections["single_target_occurrence"] > 0
    assert 1006 not in sentence_ids


def test_tatoeba_prefilters_vesum_length_duplicates_register_russianism_and_cefr_unknown() -> None:
    report = _report()
    sentence_ids = _candidate_sentence_ids(report)

    assert report.rejections["sentence_length"] > 0
    assert report.rejections["vesum_ambiguous"] > 0
    assert report.rejections["near_duplicate"] > 0
    assert report.rejections["exact_duplicate"] > 0
    assert report.rejections["blocked_register"] > 0
    assert report.rejections["russianism_prescreen"] > 0
    assert report.rejections["sentence_cefr_unknown"] > 0
    assert {1005, 1007, 1008, 1009, 1010, 1011, 1014}.isdisjoint(sentence_ids)


def test_tatoeba_caps_per_lemma_and_case_rule() -> None:
    lemma_report = _report(GeneratorConfig(max_per_lemma=0))
    case_rule_report = _report(GeneratorConfig(max_per_case_rule=0))

    assert lemma_report.candidates == []
    assert lemma_report.rejections["cap_lemma"] > 0
    assert case_rule_report.candidates == []
    assert case_rule_report.rejections["cap_case_rule"] > 0


def test_tatoeba_cli_writes_review_candidate_file(tmp_path: Path) -> None:
    out = tmp_path / "review-candidates.json"
    yield_report = tmp_path / "yield-report.json"

    exit_code = main(
        [
            "--manifest",
            str(MANIFEST),
            "--uk-sentences",
            str(UK_SENTENCES),
            "--en-sentences",
            str(EN_SENTENCES),
            "--links",
            str(LINKS),
            "--vesum-json",
            str(VESUM),
            "--out",
            str(out),
            "--yield-report",
            str(yield_report),
            "--progress-every",
            "1",
        ],
        russian_shadow_checker=lambda _token: False,
    )

    rows = json.loads(out.read_text(encoding="utf-8"))
    summary = json.loads(yield_report.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert rows
    assert all(row["provenance"]["status"] == "tatoeba" for row in rows)
    assert summary["candidates"] == len(rows)
    assert summary["pairs_processed"] > 0
    assert summary["target_form_keys"] > 0
    assert "rejections" in summary


def test_tatoeba_cli_fails_loudly_on_missing_inputs(tmp_path: Path) -> None:
    missing = tmp_path / "missing-manifest.json"
    with pytest.raises(FileNotFoundError, match="missing Atlas manifest"):
        main(
            [
                "--manifest",
                str(missing),
                "--uk-sentences",
                str(UK_SENTENCES),
                "--en-sentences",
                str(EN_SENTENCES),
                "--links",
                str(LINKS),
                "--vesum-json",
                str(VESUM),
                "--out",
                str(tmp_path / "out.json"),
            ],
            russian_shadow_checker=lambda _token: False,
        )


def test_tatoeba_detailed_export_license_defaults_and_cc0_ids(tmp_path: Path) -> None:
    detailed = tmp_path / "ukr_detailed.tsv"
    detailed.write_text(
        "1001\tukr\tЯ бачу цю книгу.\tolena_uk\t2020-01-01 00:00:00\t2020-01-02 00:00:00\n"
        "1002\tukr\tЯ живу у місті тепер.\ttaras_uk\t2020-01-01 00:00:00\t2020-01-02 00:00:00\n",
        encoding="utf-8",
    )
    cc0 = tmp_path / "sentences_CC0.csv"
    cc0.write_text("1002\tukr\tignored\t2020-01-01\n", encoding="utf-8")

    with pytest.raises(ValueError, match="missing per-row license"):
        read_tatoeba_sentences(detailed, "ukr")

    rows = read_tatoeba_sentences(
        detailed,
        "ukr",
        default_license=DEFAULT_LICENSE,
        cc0_ids=read_cc0_sentence_ids(cc0),
    )
    assert rows[1001].license == DEFAULT_LICENSE
    assert rows[1002].license == "CC0"
    assert rows[1001].author == "olena_uk"


def test_tatoeba_yield_summary_and_markdown_cover_counts() -> None:
    report = _report()
    summary = build_yield_summary(report)
    markdown = format_yield_report_markdown(summary, run_date="2026-07-19")

    assert summary["candidates"] == len(report.candidates)
    assert summary["pairs_processed"] > 0
    assert set(summary["by_case_rule"]) <= SUPPORTED_CASE_RULE_SET
    assert "Candidates emitted" in markdown
    assert "accusative_direct_object" in markdown or "locative_static" in markdown
