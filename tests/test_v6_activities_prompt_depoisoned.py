from pathlib import Path

import pytest

PROMPT_PATH = Path("scripts/build/phases/v6-activities.md")


@pytest.mark.unit
def test_v6_activities_prompt_depoisoned_examples() -> None:
    prompt = PROMPT_PATH.read_text(encoding="utf-8")

    assert "<no-example-words>" in prompt
    assert "<UKR_1>" in prompt

    poisoned_examples = ['"кіт"', '"пес"', '"молоко"', '"книга"', '"яблуко"']
    present = [example for example in poisoned_examples if example in prompt]
    assert not present, f"Concrete Ukrainian example words remain: {present}"
