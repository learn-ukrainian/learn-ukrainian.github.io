"""Regression and contract tests for the Foundry language-contact detector."""

from __future__ import annotations

import copy
import json
import sqlite3
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

import scripts.projects.open_model_data.language_contact_detector as detector

ROOT = Path(__file__).resolve().parents[1]
INPUT_ROOT = ROOT
TEST_INPUT_ROOT: Path | None = None
VESUM_MISS_FORMS = {
    "будет",
    "вєжліви",
    "вызвало",
    "врємя",
    "да",
    "делать",
    "звучит",
    "значіт",
    "мой",
    "нєй",
    "океаненяті",
    "они",
    "перекличка",
    "переклички",
    "перекличку",
    "перекличкою",
    "перекличці",
    "придєт",
    "разговаривают",
    "ростовъ",
    "с",
    "скліплює",
    "смуту",
    "цівілізація",
    "что",
    "шо",
}


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _test_input_root() -> Path:
    assert TEST_INPUT_ROOT is not None
    return TEST_INPUT_ROOT


def _seed_vesum(texts: list[str]) -> None:
    database = _test_input_root() / "data/vesum.db"
    forms = {
        token.normalized
        for text in texts
        for token in detector.tokenize_with_offsets(text)
        if token.normalized not in VESUM_MISS_FORMS
        and any("а" <= character <= "я" or character in "іїєґ" for character in token.normalized)
    }
    connection = sqlite3.connect(database)
    connection.executemany(
        "INSERT OR IGNORE INTO forms(word_form, lemma, pos, tags) VALUES (?, ?, 'fixture', 'fixture')",
        [(form, form) for form in sorted(forms)],
    )
    connection.commit()
    connection.close()


@pytest.fixture(scope="module")
def evidence_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    global TEST_INPUT_ROOT
    root = tmp_path_factory.mktemp("language-contact-evidence")
    data = root / "data"
    data.mkdir()
    vesum = sqlite3.connect(data / "vesum.db")
    vesum.execute(
        "CREATE TABLE forms(word_form TEXT NOT NULL, lemma TEXT NOT NULL, pos TEXT NOT NULL, tags TEXT NOT NULL, UNIQUE(word_form, lemma, pos, tags))"
    )
    vesum.commit()
    vesum.close()
    sources = sqlite3.connect(data / "sources.db")
    sources.execute("CREATE TABLE grinchenko(word TEXT NOT NULL)")
    sources.execute("CREATE TABLE esum_etymology_meta(lemma TEXT NOT NULL)")
    sources.execute("CREATE TABLE sum11(word TEXT NOT NULL)")
    sources.executemany("INSERT INTO grinchenko(word) VALUES (?)", [("шо",), ("да",)])
    sources.executemany("INSERT INTO sum11(word) VALUES (?)", [("мой",), ("перекличка",)])
    sources.commit()
    sources.close()
    TEST_INPUT_ROOT = root
    _seed_vesum(["очєнь"])
    return root


@pytest.fixture(scope="module")
def config(evidence_root: Path) -> dict:
    assert evidence_root.is_dir()
    return detector._load_and_validate_config(detector.DEFAULT_CONFIG_PATH)


@pytest.fixture(scope="module")
def runtime(config: dict, evidence_root: Path):
    active = detector.EvidenceRuntime(config, evidence_root)
    yield active
    active.close()


def _detect(
    text: str,
    *,
    config: dict,
    runtime: detector.EvidenceRuntime,
    period: str = "modern",
    register: str = "literary",
) -> list[dict]:
    _seed_vesum([text])
    tokens = detector.tokenize_with_offsets(text)
    vesum = runtime.vesum.lookup(token.normalized for token in tokens)
    return detector.run_detector_on_text(
        text=text,
        record_id="fixture-record",
        locator="sqlite:fixture.db#records/fixture-record",
        source_family="fixture",
        source_record_id="fixture:record",
        period=period,
        register=register,
        origin="project_authored_fixture",
        vesum_matches=vesum,
        config=config,
        runtime=runtime,
        input_root=_test_input_root(),
    )


def test_schema_and_config_conformance(config: dict) -> None:
    for path in (
        detector.CONFIG_SCHEMA_PATH,
        detector.CANDIDATE_SCHEMA_PATH,
        detector.RECEIPT_SCHEMA_PATH,
    ):
        Draft202012Validator.check_schema(_json(path))
    assert config["r2u_cache"]["network_during_run"] is False
    assert config["span"]["max_chars"] == 240


def test_frozen_denominator_and_source_adapters_match_profiler(config: dict) -> None:
    profile = _json(ROOT / "data/projects/open_model_data/profiles/public_external_full_corpus_v1.json")
    expected_rows = sum(source["expected"]["rows"] for source in config["sources"])
    expected_words = sum(source["expected"]["lexical_words"] for source in config["sources"])
    assert (expected_rows, expected_words) == (189150, 50298925)
    detector_sources = [
        (source["source_family"], source["inventory_asset_id"], source["adapter"], source["expected"])
        for source in config["sources"]
    ]
    profiler_sources = [
        (source["source_family"], source["inventory_asset_id"], source["adapter"], source["expected"])
        for source in profile["sources"]
    ]
    assert detector_sources == profiler_sources


def test_clean_long_ukrainian_emits_zero_and_never_leaks_full_text(config: dict, runtime) -> None:
    text = "Українська мова має багату історію та живу сучасну традицію. " * 200
    assert len(text) > 10000
    assert _detect(text, config=config, runtime=runtime) == []


def test_short_and_hyphen_fragments_do_not_become_morphology_rescues(config: dict, runtime) -> None:
    text = "Хто-небудь згадає ї та н у технічному покажчику."
    assert _detect(text, config=config, runtime=runtime) == []


def test_bounded_offsets_unicode_apostrophes_and_boundaries(config: dict, runtime) -> None:
    text = (
        "Перший абзац про м’яту й памʼять. " * 15
        + "\n\nЦя тема звучит у розмові.\n\n"
        + "Третій абзац лишається поза кандидатом. " * 15
    )
    candidates = _detect(text, config=config, runtime=runtime)
    assert len(candidates) == 1
    span = candidates[0]["span"]
    assert text[span["start_char"] : span["end_char"]] == span["original_text"]
    assert text[span["core_start_char"] : span["core_end_char"]] == "звучит"
    assert len(span["original_text"]) <= 240
    assert span["original_text"] != text
    assert "Третій абзац" not in span["original_text"]
    surfaces = ["м’ята", "мʼята", "м'ята", "м`ята"]
    assert {detector.normalize_form(surface) for surface in surfaces} == {"м'ята"}


def test_nested_imbalanced_quotes_and_dash_dialogue_have_exact_offsets() -> None:
    nested = "Автор записав: «Він перепитав “что значіт” і замовк»."
    spans = detector.segment_structure(nested)
    assert {span.boundary_kind for span in spans} >= {"paired_quote"}
    assert all(nested[span.start_char : span.end_char] == span.original_text for span in spans)
    imbalanced = "Початок «что вызвало без закриття.\n\nНовий абзац."
    imbalanced_spans = detector.segment_structure(imbalanced)
    target = next(span for span in imbalanced_spans if span.boundary_kind == "imbalanced_quote_paragraph")
    assert "Новий абзац" not in target.original_text
    dialogue = "— они что, не разговаривают? — запитав герой."
    dialogue_span = next(span for span in detector.segment_structure(dialogue) if span.discourse_role == "dialogue")
    assert dialogue[dialogue_span.start_char : dialogue_span.end_char] == dialogue_span.original_text
    assert "запитав" not in dialogue_span.original_text


def test_standard_russian_quotation_and_modern_narration_are_distinct(config: dict, runtime) -> None:
    quoted = _detect("Автор навів: «что вызвало смуту».", config=config, runtime=runtime)
    narration = _detect("Ця тема звучит у новинах.", config=config, runtime=runtime)
    assert quoted[0]["classification"]["category"] == "russian_quotation"
    assert quoted[0]["classification"]["downstream_disposition"] == "mask_from_modern_ukrainian_loss"
    assert quoted[0]["queue_route"] == "quoted_russian"
    assert narration[0]["classification"]["category"] == "modern_narration_interference"
    assert narration[0]["queue_route"] == "modern_interference_review"
    assert narration[0]["automatic_error_label"] is False


def test_phonetic_reconstruction_requires_context_morphology_and_r2u(config: dict, runtime) -> None:
    assert _detect("У примітці є форма очєнь.", config=config, runtime=runtime) == []
    candidates = _detect("Вона сказала: «очєнь вєжліви с нєй».", config=config, runtime=runtime)
    assert candidates[0]["classification"]["category"] == "ukrainian_phonetic_russian"
    reconstructions = candidates[0]["evidence"]["reconstruction_candidates"]
    assert {item["original_surface"] for item in reconstructions} >= {"очєнь", "вєжліви", "нєй"}
    assert all(item["validated"] is True for item in reconstructions)
    assert all(item["ru_morph"]["confidence"] >= 0.7 for item in reconstructions)
    assert all(item["r2u_cache"]["status"] == "hit" for item in reconstructions)
    assert all(item["transformation_path"][0].startswith("configured:") for item in reconstructions)


@pytest.mark.parametrize(
    "surface",
    ["перекличка", "переклички", "перекличку", "перекличці", "перекличкою"],
)
def test_pereklychka_inflections_are_rescued_by_actual_sum_evidence(
    surface: str,
    config: dict,
    runtime,
) -> None:
    candidates = _detect(f"Перед уроком згадали {surface} учнів.", config=config, runtime=runtime)
    assert candidates[0]["classification"]["category"] == "protected_authentic_ukrainian"
    heritage = candidates[0]["evidence"]["heritage"]
    assert heritage["status"] == "used"
    assert any(
        hit["dictionary_identity"] == "СУМ-11" and hit["matched_headword"] == "перекличка"
        for lookup in heritage["lookups"]
        for hit in lookup["hits"]
    )
    assert candidates[0]["queue_route"] == "protected_rescue"


@pytest.mark.parametrize(
    ("text", "surface", "dictionary_identity"),
    [
        ("Він пояснив, шо саме сталося.", "шо", "Грінченко"),
        ("Вона да й рушила далі.", "да", "Грінченко"),
        ("Він гукнув мой до хлопців.", "мой", "СУМ-11"),
    ],
)
def test_short_russian_morphology_hits_with_heritage_evidence_are_protected(
    text: str,
    surface: str,
    dictionary_identity: str,
    config: dict,
    runtime,
) -> None:
    candidates = _detect(text, config=config, runtime=runtime)
    assert [item["classification"]["category"] for item in candidates] == [
        "protected_authentic_ukrainian"
    ]
    heritage = candidates[0]["evidence"]["heritage"]
    assert any(
        hit["dictionary_identity"] == dictionary_identity
        for lookup in heritage["lookups"]
        if lookup["surface"] == surface
        for hit in lookup["hits"]
    )


@pytest.mark.parametrize(
    "text",
    [
        "Оповідач згадав океаненяті та скліплює.",
        "Автор записав: «будет делать».",
    ],
)
def test_adjacent_russian_morphology_without_anchor_or_r2u_is_uncertain(
    text: str,
    config: dict,
    runtime,
) -> None:
    candidates = _detect(text, config=config, runtime=runtime)
    assert [item["classification"]["category"] for item in candidates] == ["uncertain"]
    assert candidates[0]["classification"]["language_identity"] == "uncertain"
    assert candidates[0]["classification"]["downstream_disposition"] == "human_review_required"
    assert candidates[0]["automatic_error_label"] is False


def test_vesum_present_ochen_is_not_accepted_without_russian_context(config: dict, runtime) -> None:
    tokens = detector.tokenize_with_offsets("очєнь")
    vesum = runtime.vesum.lookup(token.normalized for token in tokens)
    assert vesum["очєнь"]
    assert _detect("У покажчику подано очєнь як форму.", config=config, runtime=runtime) == []


def test_proper_name_other_language_and_ocr_require_positive_suspicion(config: dict, runtime) -> None:
    assert _detect("Тарас Шевченко відвідав Київ.", config=config, runtime=runtime) == []
    proper = _detect("У документі згадано Ростовъ як назву.", config=config, runtime=runtime)
    assert proper[0]["classification"]["category"] == "proper_name"
    assert _detect("Платформа OpenAI допомагає дослідникам.", config=config, runtime=runtime) == []
    other = _detect("Подано термін language contact theory.", config=config, runtime=runtime)
    assert other[0]["classification"]["category"] == "other_language"
    ocr = _detect("Фрагмент містить дефект\u0000 кодування.", config=config, runtime=runtime)
    assert ocr[0]["classification"]["category"] == "ocr_or_encoding_candidate"


def test_quoted_capitalized_russian_orthography_cannot_self_corroborate(config: dict, runtime) -> None:
    candidates = _detect("Автор згадав назву «Ростовъ» у примітці.", config=config, runtime=runtime)
    assert [item["classification"]["category"] for item in candidates] == ["uncertain"]
    assert candidates[0]["classification"]["language_identity"] == "uncertain"
    assert candidates[0]["classification"]["downstream_disposition"] == "human_review_required"
    assert candidates[0]["automatic_error_label"] is False


def test_vetted_valid_word_route_is_candidate_only(config: dict, runtime) -> None:
    candidates = _detect("Він хотів прийняти участь у події.", config=config, runtime=runtime)
    candidate = candidates[0]
    assert candidate["classification"]["category"] == "valid_word_contact_candidate"
    assert candidate["evidence"]["valid_word_routes"][0]["evidence_key"].startswith("PHRASAL_CALQUES:")
    assert candidate["automatic_error_label"] is False
    assert candidate["review_state"] == "unresolved"
    assert candidate["queue_route"] == "valid_word_review"


def test_evidence_identities_and_pending_states_are_truthful(config: dict, runtime) -> None:
    quote = _detect("Автор навів: «что вызвало смуту».", config=config, runtime=runtime)[0]
    evidence = quote["evidence"]
    assert evidence["vesum"]["adapter_id"] == "scripts.verification.vesum.verify_words"
    assert evidence["russian_morphology"]["adapter_id"].endswith("get_ru_confidence")
    assert evidence["r2u"]["status"] == "used"
    assert evidence["r2u"]["lookups"][0]["status"] == "miss"
    assert evidence["external_pending"] == [
        {
            "adapter_id": "scripts.rag.source_query.ulif_lookup",
            "dictionary_identity": "ULIF DictUA underlying module pending",
            "status": "not_queried",
        },
        {
            "adapter_id": "scripts.rag.source_query.slovnyk_me_lookup",
            "dictionary_identity": "underlying slovnyk.me dictionary not selected",
            "status": "not_queried",
        },
    ]
    assert evidence["network_performed"] is False


def _mini_config(tmp_path: Path, config: dict, texts: list[str]) -> Path:
    _seed_vesum(texts)
    database = tmp_path / "mini.db"
    connection = sqlite3.connect(database)
    connection.execute("CREATE TABLE records(id INTEGER PRIMARY KEY, text TEXT NOT NULL)")
    connection.executemany("INSERT INTO records(id, text) VALUES (?, ?)", enumerate(texts, 1))
    connection.commit()
    connection.close()
    word_count = sum(len(detector.tokenize_with_offsets(text)) for text in texts)
    payload = copy.deepcopy(config)
    payload["vesum"]["database"] = str(_test_input_root() / "data/vesum.db")
    payload["heritage"]["database"] = str(_test_input_root() / "data/sources.db")
    payload["sources"] = [
        {
            "source_family": "fixture",
            "inventory_asset_id": "fixture.records",
            "adapter": {
                "kind": "sqlite_query_v1",
                "database": str(database),
                "table": "records",
                "id_column": "id",
                "text_column": "text",
                "locator_column": "id",
                "dimensions": {
                    "period": {"constant": "modern"},
                    "genre": {"constant": "fixture"},
                    "register": {"constant": "literary"},
                    "origin": {"constant": "project_authored_fixture"},
                },
            },
            "evidence": {
                "provenance_status": "complete",
                "rights_status": "granted",
                "origin_status": "verified_human_authorship",
                "contamination_status": "cleared",
                "permitted_use": "private_reference",
            },
            "expected": {"rows": len(texts), "lexical_words": word_count},
        }
    ]
    path = tmp_path / "config.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def test_receipt_arithmetic_derives_from_rows_and_bytes_are_deterministic(
    tmp_path: Path,
    config: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    texts = [
        "Українська мова має живу традицію.",
        "Автор навів: «что вызвало смуту».",
        "Перед уроком відбулася перекличка.",
        "Ця тема звучит у новинах.",
        "Він хотів прийняти участь у події.",
    ]
    config_path = _mini_config(tmp_path, config, texts)
    candidate_schema_loads = 0
    original_load_json = detector._load_json

    def counted_load_json(path: Path) -> dict:
        nonlocal candidate_schema_loads
        if path == detector.CANDIDATE_SCHEMA_PATH:
            candidate_schema_loads += 1
        return original_load_json(path)

    monkeypatch.setattr(detector, "_load_json", counted_load_json)
    outputs = []
    for suffix in ("one", "two"):
        candidates = tmp_path / f"candidates-{suffix}.jsonl"
        receipt = tmp_path / f"receipt-{suffix}.json"
        result = detector.stream_detector(
            config_path=config_path,
            input_root=tmp_path,
            summary_output=receipt,
            candidates_output=candidates,
        )
        outputs.append((result, candidates, receipt))
    first, second = outputs
    assert candidate_schema_loads == 2
    assert first[1].read_bytes() == second[1].read_bytes()
    assert first[2].read_bytes() == second[2].read_bytes()
    summary = first[0].summary
    arithmetic = summary["candidate_arithmetic"]
    assert arithmetic == {
        "total_candidates": 4,
        "unresolved_review_queue": 1,
        "protected_rescues": 1,
        "quoted_russian": 1,
        "modern_interference_candidates": 1,
        "other_routes": 0,
        "queue_route_counts": {
            "modern_interference_review": 1,
            "protected_rescue": 1,
            "quoted_russian": 1,
            "valid_word_review": 1,
        },
    }
    assert summary["coverage"]["dropped_rows"] == 0
    assert summary["coverage"]["dropped_lexical_words"] == 0
    assert summary["outputs"]["review_candidates"]["records"] == 4
    assert sum(arithmetic["queue_route_counts"].values()) == arithmetic["total_candidates"]
    assert (
        arithmetic["unresolved_review_queue"]
        + arithmetic["protected_rescues"]
        + arithmetic["quoted_russian"]
        + arithmetic["modern_interference_candidates"]
        + arithmetic["other_routes"]
        == arithmetic["total_candidates"]
    )
    for field in (
        "yields_by_category",
        "yields_by_source_family",
        "yields_by_period",
        "yields_by_register",
    ):
        assert sum(summary[field].values()) == arithmetic["total_candidates"]
    assert sum(summary["prefilter"].values()) == summary["coverage"]["processed_rows"]
    assert summary["claims"] == {
        "correction_gold_created": False,
        "precision_or_recall_claimed": False,
        "source_admission_changed": False,
        "training_or_publication_performed": False,
    }


def test_dimension_reads_aliased_sqlite_columns_instead_of_row_values() -> None:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    try:
        row = connection.execute(
            "SELECT 'middle_ukrainian' AS __period, 'dialectal' AS __register"
        ).fetchone()
    finally:
        connection.close()
    assert row is not None
    source = {
        "adapter": {
            "dimensions": {
                "period": {"column": "language_period"},
                "register": {"column": "register_tag"},
            }
        }
    }
    assert detector._dimension(row, source, "period") == "middle_ukrainian"
    assert detector._dimension(row, source, "register") == "dialectal"
    assert detector._dimension(row, source, "origin") == "unknown"


def test_prefilter_arithmetic_includes_records_without_lexical_tokens(
    tmp_path: Path,
    config: dict,
) -> None:
    config_path = _mini_config(tmp_path, config, ["", "Українська мова."])
    result = detector.stream_detector(
        config_path=config_path,
        input_root=tmp_path,
        summary_output=tmp_path / "receipt.json",
        candidates_output=tmp_path / "candidates.jsonl",
    )
    prefilter = result.summary["prefilter"]
    assert result.summary["coverage"]["processed_rows"] == 2
    assert prefilter["rows_with_signal"] + prefilter["rows_without_signal"] == 2


def test_receipt_promotion_failure_restores_prior_detector_artifacts(
    tmp_path: Path,
    config: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = _mini_config(tmp_path, config, ["Ця тема звучит у новинах."])
    candidates = tmp_path / "candidates.jsonl"
    receipt = tmp_path / "receipt.json"
    candidates.write_bytes(b"prior candidates\n")
    receipt.write_bytes(b"prior receipt\n")
    original_replace = detector.os.replace
    failed = False
    reserved_backups = 0

    def fail_receipt_promotion(source: Path, destination: Path) -> None:
        nonlocal failed, reserved_backups
        if Path(destination).name.endswith(".rollback"):
            assert Path(destination).is_file()
            reserved_backups += 1
        if Path(destination) == receipt and not failed:
            failed = True
            raise OSError("forced receipt promotion failure")
        original_replace(source, destination)

    monkeypatch.setattr(detector.os, "replace", fail_receipt_promotion)
    with pytest.raises(OSError, match="forced receipt promotion failure"):
        detector.stream_detector(
            config_path=config_path,
            input_root=tmp_path,
            summary_output=receipt,
            candidates_output=candidates,
        )

    assert candidates.read_bytes() == b"prior candidates\n"
    assert receipt.read_bytes() == b"prior receipt\n"
    assert reserved_backups == 2
    assert not list(tmp_path.glob("*.rollback"))


def test_missing_evidence_adapters_fail_closed(tmp_path: Path, config: dict) -> None:
    broken_vesum = copy.deepcopy(config)
    broken_vesum["vesum"]["database"] = "missing-vesum.db"
    with pytest.raises(FileNotFoundError, match="VESUM database inaccessible"):
        detector.EvidenceRuntime(broken_vesum, tmp_path)

    broken_r2u = copy.deepcopy(config)
    broken_r2u["vesum"]["database"] = str(_test_input_root() / "data/vesum.db")
    broken_r2u["r2u_cache"]["file"] = str(tmp_path / "missing-r2u.json")
    with pytest.raises(ValueError, match="cannot read JSON"):
        detector.EvidenceRuntime(broken_r2u, tmp_path)

    no_heritage = copy.deepcopy(config)
    no_heritage["vesum"]["database"] = str(_test_input_root() / "data/vesum.db")
    no_heritage["heritage"]["database"] = "missing-sources.db"
    active = detector.EvidenceRuntime(no_heritage, tmp_path)
    try:
        tokens = detector.tokenize_with_offsets("Перед уроком відбулася перекличка.")
        vesum = active.vesum.lookup(token.normalized for token in tokens)
        assert detector.run_detector_on_text(
            text="Перед уроком відбулася перекличка.",
            record_id="missing",
            locator="sqlite:fixture.db#records/missing",
            source_family="fixture",
            source_record_id="fixture:missing",
            period="modern",
            register="literary",
            origin="project_authored_fixture",
            vesum_matches=vesum,
            config=no_heritage,
            runtime=active,
            input_root=tmp_path,
        ) == []
    finally:
        active.close()


def test_frozen_regression_fixture_uses_real_local_adapters(config: dict) -> None:
    fixture = _json(detector.DEFAULT_REGRESSION_FIXTURE)
    _seed_vesum([case["text"] for case in fixture["cases"]])
    detector.run_regression_tests(
        detector.DEFAULT_REGRESSION_FIXTURE,
        input_root=_test_input_root(),
    )
