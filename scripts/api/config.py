"""Configuration for the playground API."""

from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Curriculum paths
CURRICULUM_ROOT = PROJECT_ROOT / "curriculum" / "l2-uk-en"

# Message broker database
MESSAGE_DB = PROJECT_ROOT / ".mcp" / "servers" / "message-broker" / "messages.db"

# Playgrounds directory (for static file serving)
PLAYGROUNDS_DIR = PROJECT_ROOT / "playgrounds"

# Levels configuration
LEVELS = [
    # Core levels
    {"id": "a1", "name": "A1 - Beginner", "path": "a1"},
    {"id": "a2", "name": "A2 - Elementary", "path": "a2"},
    {"id": "b1", "name": "B1 - Intermediate", "path": "b1"},
    {"id": "b2", "name": "B2 - Upper Intermediate", "path": "b2"},
    {"id": "b2-pro", "name": "B2-PRO - Professional", "path": "b2-pro"},
    {"id": "c1", "name": "C1 - Advanced", "path": "c1"},
    {"id": "c1-pro", "name": "C1-PRO - Professional", "path": "c1-pro"},
    {"id": "c2", "name": "C2 - Mastery", "path": "c2"},
    # Seminar tracks
    {"id": "b2-hist", "name": "B2-HIST - History Track", "path": "b2-hist"},
    {"id": "c1-hist", "name": "C1-HIST - History Track", "path": "c1-hist"},
    {"id": "c1-bio", "name": "C1-BIO - Biography Track", "path": "c1-bio"},
    {"id": "lit", "name": "LIT - Literature Track", "path": "lit"},
    # Historical language tracks
    {"id": "oes", "name": "OES - Old East Slavic", "path": "oes"},
    {"id": "ruth", "name": "RUTH - Ruthenian", "path": "ruth"},
]

# Server settings
API_HOST = "0.0.0.0"
API_PORT = 8765
