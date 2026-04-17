import yaml

from scripts.build import v6_build


def test_style_review_advisory_flow(tmp_path, monkeypatch):
    """Test that failed style review records advice and continues (advisory)."""
    level = "a1"
    slug = "test-style-advisory"
    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    curriculum_root.mkdir(parents=True)
    (curriculum_root / level).mkdir(parents=True)

    # Setup mock contract
    contract_path = curriculum_root / level / "orchestration" / slug / "contract.yaml"
    contract_path.parent.mkdir(parents=True)
    contract_data = {
        "module": {"slug": slug},
        "banned_error_patterns": ["Pattern A"]
    }
    contract_path.write_text(yaml.dump(contract_data), "utf-8")

    content_path = curriculum_root / level / f"{slug}.md"
    content_path.write_text("Some content", "utf-8")

    # Mock step_review_style to fail
    monkeypatch.setattr(v6_build, "step_review_style",
        lambda *args, **kwargs: (False, 8.2, "Review text with issues")
    )
    # Mock extract issues
    monkeypatch.setattr(v6_build, "_extract_style_review_blocking_issues",
        lambda text: [{"type": "STYLE", "location": "Intro", "evidence": "Bad", "fix": "Good"}]
    )
    # Mock CURRICULUM_ROOT
    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)

    # Run the loop
    result = v6_build._run_style_review_heal_loop(
        content_path, level=level, module_num=1, slug=slug, writer="gemini", reviewer_override=None
    )

    # Assertions
    assert result.outcome == "pass"
    assert len(result.rounds) == 1
    assert result.rounds[0].passed is False
    assert result.rounds[0].score == 8.2

    # Check that contract was updated with advice
    updated_contract = yaml.safe_load(contract_path.read_text("utf-8"))
    assert "style_review_advice" in updated_contract
    assert len(updated_contract["style_review_advice"]) == 1
    assert updated_contract["style_review_advice"][0]["fix"] == "Good"

def test_contract_prompt_includes_style_advice():
    """Test that style advice is formatted into the contract prompt."""
    contract = {
        "module": {"slug": "test"},
        "style_review_advice": [
            {"type": "STYLE", "location": "Intro", "evidence": "X", "fix": "Y"}
        ]
    }
    excerpts = {}

    # Test mode="write"
    contract_literal, _ = v6_build._format_contract_prompt_artifacts(contract, excerpts, mode="write")
    assert "style_review_advice" in contract_literal
    assert "fix: Y" in contract_literal

    # Test mode="chunk" with matching location
    contract_literal, _ = v6_build._format_contract_prompt_artifacts(
        contract, excerpts, mode="chunk", section_title="Intro"
    )
    assert "style_review_advice" in contract_literal
    assert "fix: Y" in contract_literal

    # Test mode="chunk" with non-matching location
    contract_literal, _ = v6_build._format_contract_prompt_artifacts(
        contract, excerpts, mode="chunk", section_title="Other"
    )
    # It should be empty if location doesn't match and isn't global
    assert "style_review_advice: []" in contract_literal
