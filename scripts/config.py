"""
Learn Ukrainian Project - Central Configuration Brain

This file stores track-level constants, model mappings, and pedagogical floors.
It is the source of truth for the dispatcher, watcher, and audit scripts.
"""

from typing import Any

from batch_gemini_config import FLASH_MODEL, PRO_MODEL

# =============================================================================
# TRACK CONFIGURATION
# =============================================================================

TRACK_CONFIG: dict[str, dict[str, Any]] = {
    # --- Core Tracks (Beginner/Intermediate) ---
    "a1": {
        "model": FLASH_MODEL,
        "word_floor": 2000,
        "persona": "The Helpful Neighbor",
        "immersion_range": [0.10, 0.50],
    },
    "a2": {
        "model": FLASH_MODEL,
        "word_floor": 2500,
        "persona": "The Cultural Guide",
        "immersion_range": [0.50, 0.90],
    },
    "b1": {
        "model": FLASH_MODEL,
        "word_floor": 3000,
        "persona": "The Storyteller",
        "immersion_range": [0.85, 1.0],
    },
    "b2": {
        "model": FLASH_MODEL,
        "word_floor": 3500,
        "persona": "The Urbanist",
        "immersion_range": [0.95, 1.0],
    },
    "c1": {
        "model": PRO_MODEL,
        "word_floor": 4000,
        "persona": "The Analyst",
        "immersion_range": [1.0, 1.0],
    },
    "c2": {
        "model": PRO_MODEL,
        "word_floor": 5000,
        "persona": "The Connoisseur",
        "immersion_range": [1.0, 1.0],
    },

    # --- Seminar Tracks (Advanced/Scholar) ---
    "hist": {
        "model": PRO_MODEL,
        "word_floor": 4000,
        "persona": "The Decolonizer",
        "immersion_range": [0.95, 1.0],
    },
    "istorio": {
        "model": PRO_MODEL,
        "word_floor": 5000,
        "persona": "The Sensory Historian",
        "immersion_range": [1.0, 1.0],
    },
    "bio": {
        "model": PRO_MODEL,
        "word_floor": 5000,
        "persona": "The Humanist Biographer",
        "immersion_range": [1.0, 1.0],
    },
    "lit": {
        "model": PRO_MODEL,
        "word_floor": 5000,
        "persona": "The Stylistic Critic",
        "immersion_range": [1.0, 1.0],
    },

    # --- Specialized Literature Tracks ---
    "lit-war": {
        "model": PRO_MODEL,
        "word_floor": 5000,
        "persona": "The Trauma Analyst",
        "immersion_range": [1.0, 1.0],
    },
    "lit-essay": {
        "model": PRO_MODEL,
        "word_floor": 5000,
        "persona": "The Intellectual Historian",
        "immersion_range": [1.0, 1.0],
    },
    "lit-fantastika": {
        "model": PRO_MODEL,
        "word_floor": 5000,
        "persona": "The World-Builder",
        "immersion_range": [1.0, 1.0],
    },
    "lit-hist-fic": {
        "model": PRO_MODEL,
        "word_floor": 5000,
        "persona": "The Historical Narratologist",
        "immersion_range": [1.0, 1.0],
    },
    "lit-humor": {
        "model": PRO_MODEL,
        "word_floor": 5000,
        "persona": "The Irony Analyst",
        "immersion_range": [1.0, 1.0],
    },
    "lit-youth": {
        "model": PRO_MODEL,
        "word_floor": 5000,
        "persona": "The Childhood Scholar",
        "immersion_range": [1.0, 1.0],
    },
    "lit-doc": {
        "model": PRO_MODEL,
        "word_floor": 5000,
        "persona": "The Witness Documentarian",
        "immersion_range": [1.0, 1.0],
    },
    "lit-drama": {
        "model": PRO_MODEL,
        "word_floor": 5000,
        "persona": "The Avant-Garde Playwright",
        "immersion_range": [1.0, 1.0],
    },
    "lit-crimea": {
        "model": PRO_MODEL,
        "word_floor": 5000,
        "persona": "The Crimean Narratologist",
        "immersion_range": [1.0, 1.0],
    },

    # --- Scholar Tracks (Ancient/Professional) ---
    "ruth": {
        "model": PRO_MODEL,
        "word_floor": 5000,
        "persona": "The Baroque Scholar",
        "immersion_range": [0.97, 1.0],
    },
    "oes": {
        "model": PRO_MODEL,
        "word_floor": 5000,
        "persona": "The Paleographer",
        "immersion_range": [0.97, 1.0],
    },
    "b2-pro": {
        "model": PRO_MODEL,
        "word_floor": 4000,
        "persona": "The Professional Coach",
        "immersion_range": [0.95, 1.0],
    },
    "c1-pro": {
        "model": PRO_MODEL,
        "word_floor": 5000,
        "persona": "The Corporate Strategist",
        "immersion_range": [1.0, 1.0],
    },
}

# =============================================================================
# GLOBAL CONSTRAINTS
# =============================================================================

OVERSHOOT_FACTOR = 1.5  # Default for B1+; A1/A2 use 1.0 (no overshoot)


def get_overshoot_factor(level: str) -> float:
    """A1/A2 should hit the target, not overshoot. B1+ benefits from 1.5x."""
    base = level.split('-')[0].upper() if level else ''
    if base in ('A1', 'A2'):
        return 1.0
    return OVERSHOOT_FACTOR
MAX_SENTENCE_LENGTH = 25  # Words
MANDATORY_CALLOUT_DENSITY = 6 # Callouts per module

# =============================================================================
# TURN SEQUENCE LOGIC
# =============================================================================

TURN_SEQUENCE = [1, 2, 3, 3.1, 3.5, 4, 5]

def get_next_turn(current_turn: float) -> float:
    """Returns the next turn in the sequence, or None if finished."""
    try:
        idx = TURN_SEQUENCE.index(current_turn)
        if idx + 1 < len(TURN_SEQUENCE):
            return TURN_SEQUENCE[idx + 1]
    except ValueError:
        pass
    return None

def get_config(track: str) -> dict[str, Any]:
    """Retrieves config for a specific track, falling back to default core config."""
    return TRACK_CONFIG.get(track, {
        "model": FLASH_MODEL,
        "word_floor": 2500,
        "persona": "The Helpful Neighbor",
        "immersion_range": [0.5, 1.0],
    })

if __name__ == "__main__":
    # Simple CLI test
    import sys
    if len(sys.argv) > 1:
        print(get_config(sys.argv[1]))
    else:
        print("Usage: python scripts/config.py <track_name>")
