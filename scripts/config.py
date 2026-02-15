"""
Learn Ukrainian Project - Central Configuration Brain

This file stores track-level constants, model mappings, and pedagogical floors.
It is the source of truth for the dispatcher, watcher, and audit scripts.
"""

from typing import Dict, Any

# =============================================================================
# TRACK CONFIGURATION
# =============================================================================

TRACK_CONFIG: Dict[str, Dict[str, Any]] = {
    # --- Core Tracks (Beginner/Intermediate) ---
    "a1": {
        "model": "gemini-3-flash-preview",
        "word_floor": 2000,
        "persona": "The Helpful Neighbor",
        "immersion_range": [0.10, 0.50],
    },
    "a2": {
        "model": "gemini-3-flash-preview",
        "word_floor": 2500,
        "persona": "The Cultural Guide",
        "immersion_range": [0.50, 0.90],
    },
    "b1": {
        "model": "gemini-3-flash-preview",
        "word_floor": 3000,
        "persona": "The Storyteller",
        "immersion_range": [0.85, 1.0],
    },
    "b2": {
        "model": "gemini-3-flash-preview",
        "word_floor": 3500,
        "persona": "The Urbanist",
        "immersion_range": [0.95, 1.0],
    },
    
    # --- Seminar Tracks (Advanced/Scholar) ---
    "b2-hist": {
        "model": "gemini-3-pro-preview",
        "word_floor": 4000,
        "persona": "The Decolonizer",
        "immersion_range": [0.95, 1.0],
    },
    "c1-hist": {
        "model": "gemini-3-pro-preview",
        "word_floor": 5000,
        "persona": "The Sensory Historian",
        "immersion_range": [1.0, 1.0],
    },
    "c1-bio": {
        "model": "gemini-3-pro-preview",
        "word_floor": 5000,
        "persona": "The Humanist Biographer",
        "immersion_range": [1.0, 1.0],
    },
    "lit": {
        "model": "gemini-3-pro-preview",
        "word_floor": 5000,
        "persona": "The Stylistic Critic",
        "immersion_range": [1.0, 1.0],
    },
    
    # --- Specialized Literature Tracks ---
    "lit-war": {
        "model": "gemini-3-pro-preview",
        "word_floor": 5000,
        "persona": "The Trauma Analyst",
        "immersion_range": [1.0, 1.0],
    },
    "lit-essay": {
        "model": "gemini-3-pro-preview",
        "word_floor": 5000,
        "persona": "The Intellectual Historian",
        "immersion_range": [1.0, 1.0],
    },
    "lit-fantastika": {
        "model": "gemini-3-pro-preview",
        "word_floor": 5000,
        "persona": "The World-Builder",
        "immersion_range": [1.0, 1.0],
    },
    "lit-hist-fic": {
        "model": "gemini-3-pro-preview",
        "word_floor": 5000,
        "persona": "The Historical Narratologist",
        "immersion_range": [1.0, 1.0],
    },
    "lit-humor": {
        "model": "gemini-3-pro-preview",
        "word_floor": 5000,
        "persona": "The Irony Analyst",
        "immersion_range": [1.0, 1.0],
    },
    "lit-juvenile": {
        "model": "gemini-3-pro-preview",
        "word_floor": 5000,
        "persona": "The Childhood Scholar",
        "immersion_range": [1.0, 1.0],
    },
    
    # --- Scholar Tracks (Ancient/Professional) ---
    "ruth": {
        "model": "gemini-3-pro-preview",
        "word_floor": 5000,
        "persona": "The Baroque Scholar",
        "immersion_range": [0.97, 1.0],
    },
    "oes": {
        "model": "gemini-3-pro-preview",
        "word_floor": 5000,
        "persona": "The Paleographer",
        "immersion_range": [0.97, 1.0],
    },
    "b2-pro": {
        "model": "gemini-3-pro-preview",
        "word_floor": 4000,
        "persona": "The Professional Coach",
        "immersion_range": [0.95, 1.0],
    },
    "c1-pro": {
        "model": "gemini-3-pro-preview",
        "word_floor": 5000,
        "persona": "The Corporate Strategist",
        "immersion_range": [1.0, 1.0],
    },
}

# =============================================================================
# GLOBAL CONSTRAINTS
# =============================================================================

OVERSHOOT_FACTOR = 1.5  # We write 1.5x the floor to ensure richness
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

def get_config(track: str) -> Dict[str, Any]:
    """Retrieves config for a specific track, falling back to default core config."""
    return TRACK_CONFIG.get(track, {
        "model": "gemini-3-flash-preview",
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
