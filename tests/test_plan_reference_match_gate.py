
from scripts.build.linear_pipeline import _plan_reference_match_gate, _resource_coverage_gate


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


def test_resource_coverage_requires_a1_m1_m7_plan_references():
    plan = {
        "level": "A1",
        "sequence": 2,
        "references": [
            {"title": "Большакова, буквар 1 клас, стор. 25"},
            {"title": "Wiki: pedagogy/a1/reading-ukrainian"},
        ],
    }
    resources = [{"role": "textbook", "title": "Захарійчук, буквар 1 клас, p. 13"}]

    result = _resource_coverage_gate(resources, plan, {"external_resources": []})

    assert result["passed"] is False
    assert result["severity"] == "HARD"
    assert result["missing_plan_references"][0]["title"] == "Большакова, буквар 1 клас, стор. 25"
    assert result["skipped_internal_references"] == ["Wiki: pedagogy/a1/reading-ukrainian"]


def test_resource_coverage_accepts_title_page_match_and_pronunciation_urls():
    plan = {
        "level": "A1",
        "sequence": 1,
        "references": [
            {"title": "Большакова, буквар 1 клас, стор. 24"},
            {"title": "ULP Season 1, Episode 1", "url": "https://www.ukrainianlessons.com/episode1/"},
        ],
        "pronunciation_videos": {
            "overview": "https://www.youtube.com/watch?v=overview",
            "vowels": {"А": "https://www.youtube.com/watch?v=a"},
            "consonants": {"М": "https://www.youtube.com/watch?v=m"},
            "special": {"Ї": "https://www.youtube.com/watch?v=yi"},
        },
    }
    resources = [
        {"role": "textbook", "title": "Большакова, буквар 1 клас, p. 24"},
        {"role": "podcast", "title": "ULP Episode 1", "url": "https://www.ukrainianlessons.com/episode1/"},
        {"role": "youtube", "title": "Overview", "url": "https://www.youtube.com/watch?v=overview"},
        {"role": "youtube", "title": "А", "url": "https://www.youtube.com/watch?v=a"},
        {"role": "youtube", "title": "М", "url": "https://www.youtube.com/watch?v=m"},
        {"role": "youtube", "title": "Ї", "url": "https://www.youtube.com/watch?v=yi"},
    ]

    result = _resource_coverage_gate(resources, plan, {"external_resources": []})

    assert result["passed"] is True
    assert result["missing_plan_references"] == []
    assert result["missing_pronunciation_videos"] == []


def test_resource_coverage_requires_wiki_external_resource_urls():
    plan = {"level": "A1", "sequence": 1, "references": []}
    resources = []
    manifest = {
        "external_resources": [
            {
                "role": "youtube",
                "title": "Video",
                "url": "https://www.youtube.com/watch?v=abc",
            }
        ]
    }

    result = _resource_coverage_gate(resources, plan, manifest)

    assert result["passed"] is False
    assert result["missing_wiki_external_resources"] == [
        {
            "title": "Video",
            "role": "youtube",
            "url": "https://www.youtube.com/watch?v=abc",
        }
    ]


def test_resource_coverage_skips_other_archetypes():
    plan = {"level": "A1", "sequence": 8, "references": [{"title": "Missing"}]}

    result = _resource_coverage_gate([], plan, {"external_resources": []})

    assert result == {"passed": True, "skipped": "not_a1_m1_m7_archetype"}
