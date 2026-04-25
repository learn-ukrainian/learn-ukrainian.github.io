from pathlib import Path

PROMPT_PATH = Path("scripts/build/phases/v6-write.md")

REQUIRED_BLOCKS = (
    "phonetic-notation",
    "no-meta-language",
    "speaker-labels",
    "dialogue-not-lecture",
    "no-stress-marks",
)


def test_v6_write_prompt_contains_quality_rule_blocks():
    prompt = PROMPT_PATH.read_text(encoding="utf-8")

    for block in REQUIRED_BLOCKS:
        assert prompt.count(f"<{block}>") == 1
        assert prompt.count(f"</{block}>") == 1
