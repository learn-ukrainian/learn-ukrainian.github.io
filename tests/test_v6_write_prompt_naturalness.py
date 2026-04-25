from pathlib import Path

import pytest

PROMPT_PATH = Path("scripts/build/phases/v6-write.md")


@pytest.mark.unit
def test_v6_write_prompt_keeps_naturalness_bans() -> None:
    prompt = PROMPT_PATH.read_text(encoding="utf-8")

    required_substrings = [
        "Banned: `Українською:` meta-frame",
        "Banned: mixed-language clauses",
        "Banned: required-vocab token-drops",
        "The Glossarist:",
    ]

    missing = [
        substring for substring in required_substrings if substring not in prompt
    ]
    assert not missing, f"Missing v6 write naturalness canaries: {missing}"
