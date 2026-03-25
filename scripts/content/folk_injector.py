"""Folk Micro-Genres Injector.

Loads folk material (загадки, скоромовки, прислів'я, приказки, лічилки, мирилки)
from data/folk_micro_genres.yaml and filters by level + module themes.

Injected into content and activities prompts via {FOLK_MATERIAL} placeholder,
similar to how {LEXICAL_SANDBOX} works.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

DATA_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "folk_micro_genres.yaml"

# Map CEFR levels to allowed difficulty tags
LEVEL_DIFFICULTIES: dict[str, set[str]] = {
    "A1": {"A1"},
    "A2": {"A1", "A2"},
    "B1": {"A1", "A2", "B1"},
    "B2": {"A1", "A2", "B1"},
    "C1": {"A1", "A2", "B1"},
    "C2": {"A1", "A2", "B1"},
}

# Map module slug keywords to folk theme tags
SLUG_TO_THEMES: dict[str, list[str]] = {
    # Food & shopping
    "restaurant": ["їжа"],
    "shopping": ["їжа"],
    "market": ["їжа"],
    "cuisine": ["їжа"],
    "food": ["їжа"],
    # Nature & weather
    "weather": ["природа", "небо", "погода"],
    "nature": ["природа", "тварини", "рослини"],
    "season": ["природа"],
    # Animals
    "animal": ["тварини"],
    # Family & social
    "family": ["сім'я", "дружба"],
    "greeting": ["дружба", "почуття"],
    "politeness": ["дружба"],
    # School & education
    "school": ["школа", "навчання"],
    "education": ["навчання"],
    # Body & health
    "body": ["людина", "тіло"],
    "health": ["здоров'я", "тіло"],
    # Home & objects
    "object": ["побут", "дім"],
    "home": ["побут", "дім"],
    "house": ["побут", "дім"],
    "clothing": ["одяг"],
    "color": ["природа"],
    # Numbers
    "number": ["числа"],
    "count": ["числа"],
    # Work & daily life
    "work": ["праця"],
    "daily": ["праця", "побут"],
    "leisure": ["гра"],
    "hobby": ["гра"],
    # Language & communication
    "verb": ["слово", "мова"],
    "imperative": ["характер"],
    "negation": ["характер"],
    "question": ["слово"],
    # Emotions
    "emotion": ["почуття", "характер"],
    # Phonetics
    "phonetic": ["мова"],
    "stress": ["мова"],
    "syllable": ["мова"],
    "intonation": ["мова"],
    "cyrillic": ["мова", "навчання"],
    # Holiday & tradition
    "holiday": ["село"],
    "tradition": ["село"],
}

# Genre availability by level
GENRE_BY_LEVEL: dict[str, list[str]] = {
    "A1": ["прислів'я", "приказки", "лічилки", "мирилки"],  # No загадки — all use grammar beyond A1
    "A2": ["загадки", "прислів'я", "приказки", "лічилки", "мирилки", "скоромовки"],
    "B1": ["загадки", "прислів'я", "приказки", "лічилки", "мирилки", "скоромовки"],
    "B2": ["загадки", "скоромовки"],  # B2 has dedicated proverb modules
    "C1": ["загадки", "скоромовки"],
    "C2": ["загадки", "скоромовки"],
}


def _load_folk_data() -> dict[str, list[dict[str, Any]]]:
    """Load and cache folk micro-genres data."""
    if not DATA_FILE.exists():
        logger.warning("Folk data file not found: %s", DATA_FILE)
        return {}
    try:
        data = yaml.safe_load(DATA_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {}
        # Strip comment-only keys
        return {k: v for k, v in data.items() if isinstance(v, list)}
    except Exception as e:
        logger.warning("Failed to load folk data: %s", e)
        return {}


def _match_themes(slug: str) -> set[str]:
    """Extract folk themes from a module slug."""
    themes: set[str] = set()
    slug_lower = slug.lower().replace("-", " ")
    for keyword, theme_list in SLUG_TO_THEMES.items():
        if keyword in slug_lower:
            themes.update(theme_list)
    return themes


def _entry_matches_themes(entry: dict, themes: set[str]) -> bool:
    """Check if a folk entry matches any of the target themes."""
    if not themes:
        return True  # No theme filter = include all
    entry_themes = entry.get("themes", [])
    if isinstance(entry_themes, str):
        entry_themes = [entry_themes]
    # Also check "theme" (singular, used by прислів'я/приказки)
    if "theme" in entry:
        entry_themes = entry_themes + [entry["theme"]]
    return bool(themes & set(entry_themes))


def _entry_matches_level(entry: dict, allowed_difficulties: set[str]) -> bool:
    """Check if entry difficulty is appropriate for this level."""
    return entry.get("difficulty", "A1") in allowed_difficulties


def build_folk_material(
    track: str,
    slug: str,
    max_per_genre: int = 4,
) -> str:
    """Build folk material block for injection into prompts.

    Args:
        track: Level track (e.g., "a1", "a2-checkpoint", "b1-grammar")
        slug: Module slug (e.g., "shopping-and-market", "body-and-health")
        max_per_genre: Maximum items per genre to include

    Returns:
        Formatted markdown block, or empty string if no matches.
    """
    data = _load_folk_data()
    if not data:
        return ""

    # Determine level
    level = track.split("-")[0].upper()
    allowed_difficulties = LEVEL_DIFFICULTIES.get(level, {"A1", "A2", "B1"})
    allowed_genres = GENRE_BY_LEVEL.get(level, [])
    themes = _match_themes(slug)

    # Phonetics modules get ALL скоромовки regardless of theme
    slug_lower = slug.lower()
    is_phonetics = any(kw in slug_lower for kw in (
        "phonetic", "stress", "intonation", "syllable", "cyrillic",
    ))

    sections: list[str] = []

    genre_labels = {
        "загадки": ("Загадки (Riddles)", "🧩"),
        "скоромовки": ("Скоромовки (Tongue Twisters)", "🗣️"),
        "прислів'я": ("Прислів'я (Proverbs)", "📜"),
        "приказки": ("Приказки (Sayings)", "💬"),
        "лічилки": ("Лічилки (Counting Rhymes)", "🔢"),
        "мирилки": ("Мирилки (Making-Up Rhymes)", "🤝"),
    }

    for genre_key in allowed_genres:
        entries = data.get(genre_key, [])
        if not entries:
            continue

        label, emoji = genre_labels.get(genre_key, (genre_key, ""))

        # Phonetics modules get all скоромовки (their primary purpose)
        skip_theme_filter = is_phonetics and genre_key == "скоромовки"

        # Filter by level and theme
        if skip_theme_filter:
            matched = [
                e for e in entries
                if _entry_matches_level(e, allowed_difficulties)
            ]
        else:
            matched = [
                e for e in entries
                if _entry_matches_level(e, allowed_difficulties)
                and _entry_matches_themes(e, themes)
            ]

        # If no theme matches, include a few general ones
        if not matched and themes:
            matched = [
                e for e in entries
                if _entry_matches_level(e, allowed_difficulties)
            ][:2]  # Just 2 fallback items

        if not matched:
            continue

        # Limit per genre
        matched = matched[:max_per_genre]

        lines = [f"### {emoji} {label}"]
        for e in matched:
            text = e["text"]
            if genre_key == "загадки":
                answer = e.get("answer", "?")
                lines.append(f"- «{text}» → **{answer}**")
            elif genre_key == "скоромовки":
                sound = e.get("target_sound", "")
                lines.append(f"- «{text}» (звук: [{sound}])")
            else:
                lines.append(f"- «{text}»")
            lines.append(f"  *(джерело: {e.get('source', 'народна')})*")

        sections.append("\n".join(lines))

    if not sections:
        return ""

    header = (
        "## 🎭 Available Folk Material (USE in engagement boxes and activities)\n\n"
        "The following folk micro-genres are available for this module's theme. "
        "Use 1-2 items as `[!folk-wisdom]` engagement boxes in content, "
        "and incorporate into activities (quiz, match-up, fill-in, cloze).\n\n"
        "**How to use in content:**\n"
        "```markdown\n"
        "> [!folk-wisdom]\n"
        "> **Народна загадка**\n"
        "> «Сидить баба серед літа у сто сорочок одіта.» — Що це? (Капуста!)\n"
        "```\n\n"
        "**How to use in activities:** Create quiz items where learners match "
        "riddles to answers, fill in missing words in proverbs, or unscramble "
        "tongue twisters.\n"
    )

    return header + "\n\n".join(sections) + "\n"
