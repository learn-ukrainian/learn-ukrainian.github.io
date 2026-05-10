"""Configuration for the local API server.

Imports project-wide paths from scripts.config and adds API-specific settings.
"""

import os
import sys
from pathlib import Path

# Add scripts/ to path if not already there (for standalone run)
_scripts_dir = str(Path(__file__).resolve().parent.parent)
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

from config import (
    BATCH_STATE_DIR,
    CURRICULUM_ROOT,
    DASHBOARDS_DIR,
    LOGS_DIR,
    PROJECT_ROOT,
    SOURCES_DB,
    TEXTBOOK_IMAGES_DIR,
    VESUM_DB,
    WIKI_DIR,
)

# ==================== API SPECIFIC ====================

# Message broker database
MESSAGE_DB = Path(
    os.environ.get(
        "AB_DB_PATH",
        str(PROJECT_ROOT / ".mcp" / "servers" / "message-broker" / "messages.db"),
    )
)

# Dispatcher log file
DISPATCHER_LOG = LOGS_DIR / "dispatcher.log"

# Levels configuration — keep in sync with:
#   assess_research.py (TRACKS), batch_dispatcher_config.py (TRACKS), manifest_utils.py (CORE_LEVELS/TRACKS)
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
    {"id": "hist", "name": "HIST - History Track", "path": "hist"},
    {"id": "istorio", "name": "ISTORIO - History Track", "path": "istorio"},
    {"id": "bio", "name": "BIO - Biography Track", "path": "bio"},
    {"id": "lit", "name": "LIT - Literature Track", "path": "lit"},
    {"id": "lit-essay", "name": "LIT-ESSAY - Essays", "path": "lit-essay"},
    {"id": "lit-hist-fic", "name": "LIT-HIST-FIC - Historical Fiction", "path": "lit-hist-fic"},
    {"id": "lit-fantastika", "name": "LIT-FANTASTIKA - Fantasy/Sci-Fi", "path": "lit-fantastika"},
    {"id": "lit-war", "name": "LIT-WAR - War Literature", "path": "lit-war"},
    {"id": "lit-humor", "name": "LIT-HUMOR - Humor", "path": "lit-humor"},
    {"id": "lit-youth", "name": "LIT-YOUTH - Youth & YA", "path": "lit-youth"},
    {"id": "lit-doc", "name": "LIT-DOC - Fact & Testimony", "path": "lit-doc"},
    {"id": "lit-drama", "name": "LIT-DRAMA - Modern Stage", "path": "lit-drama"},
    {"id": "lit-crimea", "name": "LIT-CRIMEA - Voices of Crimea", "path": "lit-crimea"},
    # Historical language tracks
    {"id": "oes", "name": "OES - Old East Slavic", "path": "oes"},
    {"id": "ruth", "name": "RUTH - Ruthenian", "path": "ruth"},
    # Specialized culture tracks
    {"id": "folk", "name": "FOLK - Folk Culture", "path": "folk"},
]

# Seminar tracks (require Phase 0 research)
SEMINAR_TRACK_IDS = {
    "hist", "istorio", "bio",
    "lit", "lit-essay", "lit-hist-fic", "lit-fantastika", "lit-war", "lit-humor", "lit-youth",
    "lit-doc", "lit-drama", "lit-crimea",
    "oes", "ruth", "folk",
}

# ==================== SERVER CONFIG ====================

API_HOST = os.environ.get("LU_API_HOST", "127.0.0.1")  # nosec B104 — bind to localhost only
API_PORT = int(os.environ.get("LU_API_PORT", 8765))
