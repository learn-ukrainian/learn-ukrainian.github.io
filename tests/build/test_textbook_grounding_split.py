from __future__ import annotations

import json
from pathlib import Path

import yaml

from scripts.build import linear_pipeline


def test_is_publishable_ref():
    # Grade 1 -> False
    assert linear_pipeline.is_publishable_ref({"title": "Bukvar Grade 1, p.10"}) is False
    assert linear_pipeline.is_publishable_ref({"notes": "chunk_id: 1-klas-bukvar-zaharijchuk-2025-1_s0024"}) is False

    # Grade 7 -> True
    assert linear_pipeline.is_publishable_ref({"title": "Karaman Grade 7, p.176"}) is True
    assert linear_pipeline.is_publishable_ref({"notes": "chunk_id: 7-klas-ukrainska-mova-karaman-2024_s0176"}) is True

    # literature -> True regardless of grade
    assert linear_pipeline.is_publishable_ref({"source_type": "literature", "title": "Grade 1 poetry"}) is True

    # style_guide -> True
    assert linear_pipeline.is_publishable_ref({"source_type": "style_guide"}) is True

    # curated author -> True
    assert linear_pipeline.is_publishable_ref({"author": "Антоненко-Давидович"}) is True
    assert linear_pipeline.is_publishable_ref({"title": "Як ми говоримо (Антоненко-Давидович)"}) is True
    assert linear_pipeline.is_publishable_ref({"title": "Словарь Грінченка"}) is True

    # No grade, no source_type, no author -> False
    assert linear_pipeline.is_publishable_ref({"title": "Random Book"}) is False

def test_chunk_context_for_all_refs_gate(tmp_path: Path):
    plan = {
        "references": [
            {"title": "Bukvar Grade 1, p.10", "notes": "chunk_id: grade-1-chunk"},
            {"title": "Karaman Grade 7, p.176", "notes": "chunk_id: grade-7-chunk"},
        ]
    }

    # All present
    tool_calls = [
        {"name": "mcp__sources__get_chunk_context", "arguments": {"chunk_id": "grade-1-chunk"}},
        {"name": "mcp__sources__get_chunk_context", "arguments": {"chunk_id": "grade-7-chunk"}},
    ]
    report = linear_pipeline._chunk_context_for_all_refs_gate(plan, tool_calls, tmp_path)
    assert report["passed"] is True

    # Missing one
    tool_calls = [
        {"name": "mcp__sources__get_chunk_context", "arguments": {"chunk_id": "grade-7-chunk"}},
    ]
    report = linear_pipeline._chunk_context_for_all_refs_gate(plan, tool_calls, tmp_path)
    assert report["passed"] is False
    assert report["reason"] == "missing_chunk_context_calls"
    assert any(v["chunk_id"] == "grade-1-chunk" for v in report["violations"])

def test_published_quote_for_publishable_refs_gate(tmp_path: Path):
    plan = {
        "level": "A1",
        "references": [
            {"title": "Bukvar Grade 1, p.10", "notes": "chunk_id: grade-1-chunk", "grade": 1},
            {"title": "Karaman Grade 7, p.176", "notes": "chunk_id: grade-7-chunk", "grade": 7},
        ]
    }
    # Mocking knowledge_packet.md so it doesn't think corpus is missing
    (tmp_path / "knowledge_packet.md").write_text("### Bukvar Grade 1, p.10\n### Karaman Grade 7, p.176\n", encoding="utf-8")

    quote_text = "Це дуже довгий текст українською мовою, який містить набагато більше тридцяти слів, щоб гарантовано пройти перевірку на мінімальну довжину цитати в цьому тесті для нових розподілених воріт, які ми щойно створили для нашого великого проекту."

    # Mock tool calls to provide "retrieved" text
    (tmp_path / "writer_tool_calls.json").write_text(json.dumps([
        {
            "name": "mcp__sources__get_chunk_context",
            "arguments": {"chunk_id": "grade-7-chunk"},
            "result": {
                "items": [
                    {
                        "source": "textbook",
                        "text": f"Karaman Grade 7, p.176\n{quote_text}"
                    }
                ]
            }
        }
    ]), encoding="utf-8")

    # Case 1: Only Grade 7 quoted
    module_text = f"""
> {quote_text}
*— Karaman, Grade 7, p.176*
"""
    report = linear_pipeline._published_quote_for_publishable_refs_gate(module_text, plan, tmp_path)
    assert report["passed"] is True
    assert "Karaman Grade 7, p.176" in report["matched"]

    # Case 2: Grade 7 NOT quoted (should fail)
    module_text = "No quotes here."
    report = linear_pipeline._published_quote_for_publishable_refs_gate(module_text, plan, tmp_path)
    assert report["passed"] is False

    # Case 3: Only Grade 1 in plan -> PASS even with no quotes
    plan_g1 = {"level": "A1", "references": [{"title": "Bukvar Grade 1, p.10", "notes": "chunk_id: g1", "grade": 1}]}
    (tmp_path / "knowledge_packet.md").write_text("### Bukvar Grade 1, p.10\n", encoding="utf-8")
    report = linear_pipeline._published_quote_for_publishable_refs_gate("No quotes", plan_g1, tmp_path)
    assert report["passed"] is True

def test_regression_m20_plan(tmp_path: Path):
    # Load real m20 plan
    plan_path = Path("curriculum/l2-uk-en/plans/a1/my-morning.yaml")
    plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))

    # Both refs in m20 are Grade 1
    # - title: Захарійчук Grade 1, p.24
    # - title: Захарійчук Grade 1, p.52

    # chunk_context_for_all_refs should fail if no calls
    report = linear_pipeline._chunk_context_for_all_refs_gate(plan, [], tmp_path)
    assert report["passed"] is False

    # chunk_context_for_all_refs should pass if both called
    tool_calls = [
        {"name": "mcp__sources__get_chunk_context", "arguments": {"chunk_id": "1-klas-bukvar-zaharijchuk-2025-1_s0024"}},
        {"name": "mcp__sources__get_chunk_context", "arguments": {"chunk_id": "1-klas-bukvar-zaharijchuk-2025-2_s0052"}},
    ]
    report = linear_pipeline._chunk_context_for_all_refs_gate(plan, tool_calls, tmp_path)
    assert report["passed"] is True

    # published_quote_for_publishable_refs should pass even with NO quotes because both are Grade 1
    # Mocking knowledge_packet.md so it doesn't think corpus is missing
    (tmp_path / "knowledge_packet.md").write_text("### Захарійчук Grade 1, p.24\n### Захарійчук Grade 1, p.52\n", encoding="utf-8")
    report = linear_pipeline._published_quote_for_publishable_refs_gate("No quotes here", plan, tmp_path)
    assert report["passed"] is True
