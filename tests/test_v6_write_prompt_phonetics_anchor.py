from pathlib import Path

import pytest

PROMPT_PATH = Path("scripts/build/phases/v6-write.md")


@pytest.mark.unit
def test_v6_write_prompt_keeps_phonetics_anchor() -> None:
    prompt = PROMPT_PATH.read_text(encoding="utf-8")

    required_substrings = [
        "Phonetics canonical anchor: 33 letters vs 38 sounds",
        "Yotated vowel letters spell two sounds in some positions",
        "Many consonants come in hard / soft pairs that share one letter",
        "never write any of these as the explanation for 38 > 33",
    ]

    missing = [
        substring for substring in required_substrings if substring not in prompt
    ]
    assert not missing, f"Missing v6 write phonetics anchor canaries: {missing}"
