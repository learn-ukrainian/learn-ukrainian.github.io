
from scripts.build.linear_pipeline import _plan_reference_match_gate


def test_passes_when_all_textbook_resources_match_plan_chunk_ids():
    plan = {
        "references": [
            {"title": "Book 1", "notes": "chunk_id: 1-klas-bukvar_s0024"},
            {"title": "Book 2", "notes": "chunk_id: 1-klas-bukvar_s0052"},
        ]
    }
    resources = [
        {"role": "textbook", "source_ref": "Book 1", "packet_chunk_id": "1-klas-bukvar_s0024"},
        {"role": "textbook", "source_ref": "Book 2", "packet_chunk_id": "1-klas-bukvar_s0052"},
    ]

    result = _plan_reference_match_gate(resources, plan)
    assert result["passed"] is True


def test_rejects_resource_with_out_of_plan_chunk_id():
    plan = {
        "references": [
            {"title": "Захарійчук Grade 1", "notes": "chunk_id: 1-klas-bukvar-zaharijchuk-2025-1_s0024."},
            {"title": "Захарійчук Grade 1", "notes": "chunk_id: 1-klas-bukvar-zaharijchuk-2025-2_s0052."},
        ]
    }
    resources = [
        {
            "role": "textbook",
            "source_ref": "Захарійчук Grade 1, p.24",
            "packet_chunk_id": "1-klas-bukvar-zaharijchuk-2025-1_s0024",
        },
        {
            "role": "textbook",
            "source_ref": "Захарійчук Grade 1, p.52",
            "packet_chunk_id": "1-klas-bukvar-zaharijchuk-2025-2_s0052",
        },
        {"role": "textbook", "source_ref": "Захарійчук Grade 4", "packet_chunk_id": "4-klas-ukrmova-zaharijchuk_s1922"},
    ]

    result = _plan_reference_match_gate(resources, plan)
    assert result["passed"] is False
    assert result["severity"] == "HARD"
    assert result["reason"] == "resources_cite_chunk_ids_not_in_plan_references"
    assert set(result["plan_chunk_ids"]) == {
        "1-klas-bukvar-zaharijchuk-2025-1_s0024",
        "1-klas-bukvar-zaharijchuk-2025-2_s0052",
    }
    assert len(result["out_of_plan"]) == 1
    assert result["out_of_plan"][0]["source_ref"] == "Захарійчук Grade 4"
    assert result["out_of_plan"][0]["cited_chunk_id"] == "4-klas-ukrmova-zaharijchuk_s1922"
    assert result["rule_ids"] == ["#R-CITE-HONEST", "#R-TEXTBOOK-30W"]


def test_extracts_chunk_id_from_notes_when_packet_chunk_id_missing():
    plan = {
        "references": [
            {"title": "Захарійчук Grade 1", "notes": "chunk_id: 1-klas-bukvar-zaharijchuk-2025-1_s0024."},
        ]
    }
    resources = [
        {
            "role": "textbook",
            "source_ref": "Захарійчук, Українська мова та читання, Grade 4, p.150",
            "notes": "Knowledge Packet anchor S1 (chunk_id: 4-klas-ukrmova-zaharijchuk_s1922): some text here",
        }
    ]

    result = _plan_reference_match_gate(resources, plan)
    assert result["passed"] is False
    assert result["reason"] == "resources_cite_chunk_ids_not_in_plan_references"
    assert len(result["out_of_plan"]) == 1
    assert result["out_of_plan"][0]["cited_chunk_id"] == "4-klas-ukrmova-zaharijchuk_s1922"


def test_passes_when_plan_has_no_chunk_ids():
    plan = {
        "references": [
            {"title": "Some Book", "notes": "No chunk ID here"},
        ]
    }
    resources = [{"role": "textbook", "source_ref": "Some Book", "packet_chunk_id": "any-chunk-id"}]

    result = _plan_reference_match_gate(resources, plan)
    assert result["passed"] is True
    assert "warnings" in result
    assert result["warnings"] == ["plan_has_no_chunk_ids_skipping_membership_check"]


def test_ignores_non_textbook_roles():
    plan = {"references": [{"title": "Book 1", "notes": "chunk_id: known-chunk"}]}
    resources = [
        {"role": "youtube", "source_ref": "Vid 1", "packet_chunk_id": "unknown-1"},
        {"role": "wiki", "source_ref": "Article 1", "chunk_id": "unknown-2"},
    ]

    result = _plan_reference_match_gate(resources, plan)
    assert result["passed"] is True
