"""Hermetic canaries for the Phase 3 historical, non-correction layer."""

from __future__ import annotations

import copy

import pytest

from scripts.projects.open_model_data.phase3_historical_representation import (
    HistoricalRepresentationError,
    build_historical_representation,
    validate_historical_representation,
)
from scripts.projects.open_model_data.phase3_linguistic_representation import sha256_text

ORIGINAL = "Во имя Отца и С[ы]на и с[вя]т[о]го Д[у]ха. амин[ь]."
RESTORED = "Во имя Отца и Сына и святого Духа. аминь."
SOURCE_BLOCK = "\n".join(
    (
        "# newdoc = uk__shaxm_krym__zudech1413",
        "# lang = orv-uk",
        "# created = 1413",
        "# title = Зудечівська розгранична грамота 1413 року",
        "# sent_id = uk__shaxm_krym__zudech1413-4",
        f"# text = {ORIGINAL}",
    )
)
PERIODIZATION_EVIDENCE = (
    "Qualified Ukrainian secondary sources attribute overlapping historical stages "
    "to the periodization frameworks of Vasyl Nimchuk and George Shevelov."
)
# Exact acquired-file hashes from the Wave H and Wave G retrieval receipts.
SOURCE_DOCUMENT_SHA = "fc13f73dc71e5fac95938eba424b3d5236bfa8edd8ce7bd0e28db2d28a2f9680"
PERIODIZATION_DOCUMENT_SHA = "31a3c97bc512d72aeb0278b6683ee75215f073d0ded414ed09efd13b9659e9b6"


def _build_kwargs() -> dict:
    source_locator = {
        "repository": "UniversalDependencies/UD_Old_East_Slavic-Ruthenian",
        "commit": "05a029e00ccf1a374c91a22d17fb6310e646d628",
        "path": "orv_ruthenian-ud-train.conllu",
        "newdoc": "uk__shaxm_krym__zudech1413",
        "sent_id": "uk__shaxm_krym__zudech1413-4",
    }
    source_evidence_id = "evidence:ud-source-record"
    metadata_evidence_id = "evidence:ud-source-metadata"
    periodization_evidence_id = "evidence:qualified-periodization"
    restoration_evidence_id = "evidence:bracket-restoration"
    public_source_rights = {
        "status": "admitted",
        "license": "CC BY-SA 4.0",
        "reuse_scope": "public_training",
        "attribution_required": True,
    }
    private_scholarship_rights = {
        "status": "private_inspection_only",
        "license": "copyright retained; repository open access",
        "reuse_scope": "private_inspection_only",
        "attribution_required": True,
    }
    return {
        "record_id": "historical:ud-orv-uk:zudech1413:4",
        "collection_identity": "UD_Old_East_Slavic-Ruthenian@05a029e00ccf",
        "document_or_edition_identity": "Зудечівська розгранична грамота 1413 року",
        "source_record_identity": "uk__shaxm_krym__zudech1413-4",
        "frozen_locator": source_locator,
        "source_document_bytes_sha256": SOURCE_DOCUMENT_SHA,
        "source_record_bytes_sha256": sha256_text(SOURCE_BLOCK),
        "historical_context": {
            "min_year": 1413,
            "max_year": 1413,
            "date_certainty": "exact",
            "region": "historical Ukrainian territory; source metadata does not encode a normalized region",
            "polity": None,
            "genre": "boundary charter",
            "manuscript_or_inscription_identity": "Зудечівська розгранична грамота 1413 року",
            "script": "Cyrillic transcription",
            "orthography": "historical source orthography with editorial bracket restorations",
        },
        "text_layers": [
            {
                "layer_id": "original_diplomatic",
                "text": ORIGINAL,
                "authority": "source_transcription",
                "evidence_ids": [source_evidence_id],
            },
            {
                "layer_id": "restored_reading",
                "text": RESTORED,
                "authority": "deterministic_derivation",
                "evidence_ids": [source_evidence_id, restoration_evidence_id],
            },
        ],
        "alignments": [
            {
                "alignment_id": "alignment:original-to-restored",
                "from_layer_id": "original_diplomatic",
                "to_layer_id": "restored_reading",
                "segments": [
                    {
                        "source_start": 0,
                        "source_end": len(ORIGINAL),
                        "target_start": 0,
                        "target_end": len(RESTORED),
                    }
                ],
                "authority": "deterministic_derivation",
                "evidence_ids": [source_evidence_id, restoration_evidence_id],
                "ambiguity": [],
            }
        ],
        "periodizations": [
            {
                "framework_id": "nimchuk-five-stage",
                "framework_label": "Five-stage synthesis attributed to Vasyl Nimchuk",
                "stage_id": "stage-iv-middle-ukrainian-rus",
                "stage_label": "Middle Ukrainian / Rus period",
                "start_year": 1300,
                "end_year": 1699,
                "status": "qualified_source_attributed",
                "attribution": "Vasyl Nimchuk framework as reproduced by qualified UzhNU scholarship",
                "evidence_ids": [periodization_evidence_id],
                "ambiguity": ["The published boundary is expressed as XIV/XV century, not one exact year."],
            },
            {
                "framework_id": "shevelov-detailed-periodization",
                "framework_label": "Detailed periodization attributed to George Shevelov",
                "stage_id": "early-middle-ukrainian",
                "stage_label": "Early Middle Ukrainian",
                "start_year": None,
                "end_year": None,
                "status": "qualified_source_attributed",
                "attribution": "George Shevelov framework as reproduced by qualified UzhNU scholarship",
                "evidence_ids": [periodization_evidence_id],
                "ambiguity": ["This canary preserves the attributed label without forcing exact numeric bounds."],
            },
        ],
        "language_labels": [
            {
                "label": "orv-uk",
                "label_kind": "corpus_annotation",
                "attribution": "UD Old East Slavic-Ruthenian treebank",
                "scope": "this explicitly tagged source document",
                "status": "attested",
                "evidence_ids": [metadata_evidence_id],
                "ambiguity": [],
            },
            {
                "label": "Old Ukrainian",
                "label_kind": "modern_scholarly",
                "attribution": "qualified Ukrainian historical-linguistic periodization",
                "scope": "historical stage interpretation, not a modern-language identity assertion",
                "status": "attributed",
                "evidence_ids": [periodization_evidence_id],
                "ambiguity": ["Historical umbrella labels vary across scholarly frameworks."],
            },
        ],
        "language_layers": [
            {
                "language_layer_id": "layer:primary-orv-uk",
                "label": "source-tagged Ukrainian Ruthenian record",
                "role": "primary",
                "status": "attested",
                "evidence_ids": [source_evidence_id, metadata_evidence_id],
                "ambiguity": ["The corpus-wide Ruthenian collection includes other regional language tags."],
            }
        ],
        "linguistic_features": [
            {
                "feature_id": "feature:editorial-bracket-restoration",
                "domain": "orthography",
                "claim": "Square brackets mark editorially supplied letters in the source transcription.",
                "layer_id": "original_diplomatic",
                "spans": [{"start": ORIGINAL.index("[ы]"), "end": ORIGINAL.index("[ы]") + 3}],
                "status": "attested",
                "attribution": "UD source transcription",
                "evidence_ids": [source_evidence_id, restoration_evidence_id],
                "ambiguity": [],
            }
        ],
        "interpretations": [
            {
                "interpretation_id": "interpretation:periodization-overlap",
                "claim": "The 1413 record is retained under multiple attributed historical frameworks.",
                "status": "qualified_source_attributed",
                "attribution": "qualified UzhNU historical-linguistic scholarship",
                "evidence_ids": [periodization_evidence_id],
                "alternatives": ["Middle Ukrainian / Rus period", "Early Middle Ukrainian"],
                "ambiguity": ["Framework names and boundaries are not collapsed into one chronology."],
            }
        ],
        "evidence": [
            {
                "evidence_id": source_evidence_id,
                "kind": "source_record",
                "locator": source_locator,
                "source_document_bytes_sha256": SOURCE_DOCUMENT_SHA,
                "evidence_text": SOURCE_BLOCK,
                "text_exposure": "verbatim",
                "authority": "source_transcription",
                "rights": public_source_rights,
            },
            {
                "evidence_id": metadata_evidence_id,
                "kind": "source_metadata",
                "locator": {**source_locator, "fields": ["lang", "created", "title"]},
                "source_document_bytes_sha256": SOURCE_DOCUMENT_SHA,
                "evidence_text": "lang=orv-uk; created=1413; title=Зудечівська розгранична грамота 1413 року",
                "text_exposure": "metadata_only",
                "authority": "source_transcription",
                "rights": public_source_rights,
            },
            {
                "evidence_id": periodization_evidence_id,
                "kind": "qualified_scholarship",
                "locator": {
                    "institutional_repository": "Uzhhorod National University",
                    "item_uuid": "04a0fdb3-1203-4855-8d8f-d6d3beb16a9b",
                    "bitstream_uuid": "8a86d15d-9534-441e-92c9-561fd8098a39",
                    "file": "uzhnu-historical-grammar-timko-ditko-yusyp-yakymovych-2017.pdf",
                    "evidence_pages": [28, 29, 30, 31],
                },
                "source_document_bytes_sha256": PERIODIZATION_DOCUMENT_SHA,
                "evidence_text": PERIODIZATION_EVIDENCE,
                "text_exposure": "paraphrase",
                "authority": "qualified_human",
                "rights": private_scholarship_rights,
            },
            {
                "evidence_id": restoration_evidence_id,
                "kind": "deterministic_derivation",
                "locator": {**source_locator, "derivation": "remove editorial square brackets, retain contents"},
                "source_document_bytes_sha256": SOURCE_DOCUMENT_SHA,
                "evidence_text": "The restored-reading fixture removes square brackets and retains bracket contents.",
                "text_exposure": "paraphrase",
                "authority": "deterministic_derivation",
                "rights": public_source_rights,
            },
        ],
        "rights": {
            "status": "admitted",
            "license": "CC BY-SA 4.0",
            "reuse_scope": "public_training",
            "attribution_required": True,
        },
        "derived_bundle_rights": [
            {"bundle_id": "historical_recognition", "rights": public_source_rights},
            {"bundle_id": "historical_alignment", "rights": public_source_rights},
            {"bundle_id": "periodization", "rights": private_scholarship_rights},
            {"bundle_id": "language_label_disambiguation", "rights": private_scholarship_rights},
        ],
        "primary_role_id": "historical_or_literary_excerpt",
        "claim_type": "attestation_only",
        "consumer_views": ("protection", "automatic"),
        "derived_bundles": (
            "historical_recognition",
            "historical_alignment",
            "periodization",
            "language_label_disambiguation",
        ),
        "evidence_grade": "source_record_plus_qualified_periodization",
        "linguistic_analyses": [
            {
                "analysis_id": "analysis:ud:1",
                "layer_id": "original_diplomatic",
                "source_token_id": "1",
                "source_surface": "Во",
                "token_ids": ["tok:000001"],
                "lemma": "во",
                "pos": "ADP",
                "morph": {},
                "head_analysis_id": "analysis:ud:2",
                "dependency": "case",
                "ambiguity": [],
            },
            {
                "analysis_id": "analysis:ud:2",
                "layer_id": "original_diplomatic",
                "source_token_id": "2",
                "source_surface": "имя",
                "token_ids": ["tok:000002"],
                "lemma": "имя",
                "pos": "NOUN",
                "morph": {"Case": "Acc", "Gender": "Neut", "Number": "Sing"},
                "head_analysis_id": None,
                "dependency": "root",
                "ambiguity": [],
            },
            {
                "analysis_id": "analysis:ud:3",
                "layer_id": "original_diplomatic",
                "source_token_id": "3",
                "source_surface": "Отца",
                "token_ids": ["tok:000003"],
                "lemma": "отецъ",
                "pos": "NOUN",
                "morph": {"Case": "Gen", "Gender": "Masc", "Number": "Sing"},
                "head_analysis_id": "analysis:ud:2",
                "dependency": "nmod",
                "ambiguity": [],
            },
            {
                "analysis_id": "analysis:ud:5",
                "layer_id": "original_diplomatic",
                "source_token_id": "5",
                "source_surface": "С[ы]на",
                "token_ids": ["tok:000005", "tok:000006", "tok:000007", "tok:000008", "tok:000009"],
                "lemma": "сынъ",
                "pos": "NOUN",
                "morph": {"Case": "Gen", "Gender": "Masc", "Number": "Sing"},
                "head_analysis_id": "analysis:ud:3",
                "dependency": "conj",
                "ambiguity": ["One UD token spans five deterministic tokens because editorial brackets are explicit."],
            },
        ],
        "analysis_provenance": {
            "status": "present",
            "resource_identity": "UD_Old_East_Slavic-Ruthenian",
            "resource_version": "05a029e00ccf1a374c91a22d17fb6310e646d628",
            "license": "CC BY-SA 4.0",
            "tokenization_alignment": "adapted",
        },
    }


def _packet(**overrides):
    kwargs = _build_kwargs()
    kwargs.update(overrides)
    return build_historical_representation(**kwargs)


def _private_bundle_rights():
    rights = {
        "status": "private_inspection_only",
        "license": "copyright retained",
        "reuse_scope": "private_inspection_only",
        "attribution_required": True,
    }
    return [{"bundle_id": bundle_id, "rights": rights} for bundle_id in _build_kwargs()["derived_bundles"]]


def test_source_grounded_canary_round_trips_all_text_offsets():
    packet = _packet()

    assert packet["text_layers"][0]["text"] == ORIGINAL
    assert packet["text_layers"][1]["text"] == RESTORED
    assert "[ы]" in [token["text"] for token in packet["text_layers"][0]["tokens"]] or any(
        token["text"] == "ы" for token in packet["text_layers"][0]["tokens"]
    )
    for layer in packet["text_layers"]:
        for token in layer["tokens"]:
            assert layer["text"][token["start"] : token["end"]] == token["text"]
    bracketed_analysis = next(
        item for item in packet["linguistic_analyses"] if item["source_token_id"] == "5"
    )
    assert bracketed_analysis["token_ids"] == [
        "tok:000005",
        "tok:000006",
        "tok:000007",
        "tok:000008",
        "tok:000009",
    ]
    assert validate_historical_representation(packet) == packet


def test_competing_periodization_frameworks_are_preserved_without_collapse():
    packet = _packet()

    assert [(item["framework_id"], item["stage_label"]) for item in packet["periodizations"]] == [
        ("nimchuk-five-stage", "Middle Ukrainian / Rus period"),
        ("shevelov-detailed-periodization", "Early Middle Ukrainian"),
    ]


def test_each_derived_bundle_has_rights_bounded_by_its_evidence():
    packet = _packet()
    bundle_rights = {
        item["bundle_id"]: item["rights"]["reuse_scope"]
        for item in packet["classification"]["derived_bundle_rights"]
    }

    assert bundle_rights == {
        "historical_recognition": "public_training",
        "historical_alignment": "public_training",
        "periodization": "private_inspection_only",
        "language_label_disambiguation": "private_inspection_only",
    }


def test_historical_record_is_mechanically_excluded_from_modern_correction_gold():
    packet = _packet()

    assert packet["safeguards"] == {
        "historical_forms_protected": True,
        "modern_correction_eligible": False,
        "russkyi_auto_mapped_to_modern_russian": False,
        "old_east_slavic_is_modern_russian": False,
        "scalar_language_age_claim_allowed": False,
    }
    assert "protection" in packet["classification"]["consumer_views"]
    assert "supervised_pair" not in packet["classification"]["consumer_views"]


def test_unresolved_language_annotation_remains_unresolved_without_inference():
    language_labels = copy.deepcopy(_build_kwargs()["language_labels"])
    language_labels[0] = {
        "label": "unresolved",
        "label_kind": "corpus_annotation",
        "attribution": "missing source metadata",
        "scope": "one untagged adjacent document",
        "status": "unresolved",
        "evidence_ids": ["evidence:ud-source-metadata"],
        "ambiguity": ["No language tag is present; regional identity must not be inferred."],
    }

    packet = _packet(language_labels=language_labels)

    assert packet["language_labels"][0]["label"] == "unresolved"
    assert packet["language_labels"][0]["status"] == "unresolved"


def test_rejects_stale_text_hash():
    packet = _packet()
    packet["text_layers"][0]["text_sha256"] = "0" * 64

    with pytest.raises(HistoricalRepresentationError, match="stale text hash"):
        validate_historical_representation(packet)


def test_rejects_source_record_hash_not_bound_to_exact_evidence_bytes():
    packet = _packet()
    packet["source"]["source_record_bytes_sha256"] = "0" * 64

    with pytest.raises(HistoricalRepresentationError, match="not bound to source-record evidence"):
        validate_historical_representation(packet)


def test_rejects_missing_original_diplomatic_layer():
    packet = _packet()
    packet["text_layers"] = [item for item in packet["text_layers"] if item["layer_id"] != "original_diplomatic"]

    with pytest.raises(HistoricalRepresentationError, match="original diplomatic"):
        validate_historical_representation(packet)


def test_rejects_stale_alignment_offsets():
    packet = _packet()
    packet["alignments"][0]["segments"][0]["source_text"] = "stale"

    with pytest.raises(HistoricalRepresentationError, match="stale source alignment"):
        validate_historical_representation(packet)


def test_rejects_derived_layer_without_path_from_original():
    packet = _packet()
    packet["alignments"] = []

    with pytest.raises(HistoricalRepresentationError, match="not aligned to original"):
        validate_historical_representation(packet)


def test_rejects_unknown_evidence_reference():
    packet = _packet()
    packet["language_labels"][0]["evidence_ids"] = ["evidence:missing"]

    with pytest.raises(HistoricalRepresentationError, match="unknown evidence"):
        validate_historical_representation(packet)


def test_rejects_model_output_as_evidence_authority():
    packet = _packet()
    packet["evidence"][0]["authority"] = "model_output"

    with pytest.raises(HistoricalRepresentationError, match="schema violation"):
        validate_historical_representation(packet)


def test_rejects_verbatim_exposure_from_non_public_evidence():
    evidence = copy.deepcopy(_build_kwargs()["evidence"])
    evidence[2]["text_exposure"] = "verbatim"

    with pytest.raises(HistoricalRepresentationError, match="cannot expose verbatim"):
        _packet(evidence=evidence)


def test_rejects_derived_bundle_that_exceeds_evidence_rights():
    bundle_rights = copy.deepcopy(_build_kwargs()["derived_bundle_rights"])
    bundle_rights[2]["rights"] = {
        "status": "admitted",
        "license": "CC BY 4.0",
        "reuse_scope": "public_training",
        "attribution_required": True,
    }

    with pytest.raises(HistoricalRepresentationError, match="exceeds evidence rights"):
        _packet(derived_bundle_rights=bundle_rights)


def test_rejects_correction_claim_for_historical_record():
    with pytest.raises(HistoricalRepresentationError, match="correction claim"):
        _packet(claim_type="human_correction_pair")


def test_rejects_non_public_record_in_learning_view():
    rights = {
        "status": "private_inspection_only",
        "license": "copyright retained",
        "reuse_scope": "private_inspection_only",
        "attribution_required": True,
    }

    with pytest.raises(HistoricalRepresentationError, match="cannot enter learning views"):
        _packet(
            rights=rights,
            derived_bundle_rights=_private_bundle_rights(),
            consumer_views=("protection", "research_only", "automatic"),
        )


def test_accepts_private_inspection_record_only_in_protected_research_view():
    rights = {
        "status": "private_inspection_only",
        "license": "copyright retained",
        "reuse_scope": "private_inspection_only",
        "attribution_required": True,
    }

    packet = _packet(
        rights=rights,
        derived_bundle_rights=_private_bundle_rights(),
        consumer_views=("protection", "research_only"),
    )

    assert packet["rights"]["reuse_scope"] == "private_inspection_only"


def test_rejects_public_training_without_resolved_license():
    rights = {
        "status": "admitted",
        "license": "unknown",
        "reuse_scope": "public_training",
        "attribution_required": False,
    }

    with pytest.raises(HistoricalRepresentationError, match="requires a license"):
        _packet(rights=rights)


def test_rejects_analysis_for_unknown_token():
    analyses = copy.deepcopy(_build_kwargs()["linguistic_analyses"])
    analyses[0]["token_ids"] = ["tok:999999"]

    with pytest.raises(HistoricalRepresentationError, match="unknown token"):
        _packet(linguistic_analyses=analyses)


def test_rejects_analysis_head_for_unknown_source_analysis():
    analyses = copy.deepcopy(_build_kwargs()["linguistic_analyses"])
    analyses[0]["head_analysis_id"] = "analysis:ud:missing"

    with pytest.raises(HistoricalRepresentationError, match="unknown analysis"):
        _packet(linguistic_analyses=analyses)


def test_rejects_analysis_with_noncontiguous_token_mapping():
    analyses = copy.deepcopy(_build_kwargs()["linguistic_analyses"])
    analyses[3]["token_ids"] = ["tok:000005", "tok:000007", "tok:000009"]

    with pytest.raises(HistoricalRepresentationError, match="contiguous and source ordered"):
        _packet(linguistic_analyses=analyses)


def test_rejects_analysis_surface_that_does_not_round_trip_offsets():
    analyses = copy.deepcopy(_build_kwargs()["linguistic_analyses"])
    analyses[3]["source_surface"] = "Сына"

    with pytest.raises(HistoricalRepresentationError, match="source surface"):
        _packet(linguistic_analyses=analyses)


def test_schema_rejects_untracked_fields():
    packet = _packet()
    packet["historical_context"]["modernized_guess"] = "forbidden"

    with pytest.raises(HistoricalRepresentationError, match="schema violation"):
        validate_historical_representation(packet)
