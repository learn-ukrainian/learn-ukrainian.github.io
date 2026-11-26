"""Language-judgment entry points must agree with the installed skill."""

import hashlib
from importlib.metadata import distribution
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENTRY_POINTS = (
    "agents_extensions/shared/skills/content-review/SKILL.md",
    "agents_extensions/shared/skills/content-review/content-review-prompt.md",
    "agents_extensions/shared/skills/seminar-content-review/SKILL.md",
    "agents_extensions/shared/skills/seminar-content-review/seminar-content-review-prompt.md",
    "scripts/build/fresh/prompts/lesson-writer.md.j2",
    "scripts/build/fresh/prompts/lesson-recap-writer.md.j2",
    "scripts/build/fresh/prompts/requires-confirm.md.j2",
)


def test_language_judgment_entry_points_bind_the_installed_skill():
    """Catch a missing instruction or a pin to a different release's skill."""
    installed_skill = distribution("lu-machinery").locate_file(
        "agents_extensions/shared/skills/verify-ukrainian/SKILL.md"
    )
    digest = hashlib.sha256(installed_skill.read_bytes()).hexdigest()
    for path in ENTRY_POINTS:
        text = (ROOT / path).read_text(encoding="utf-8")
        assert "`verify-ukrainian` skill before" in text, path
        assert f"`{digest}`" in text, path
