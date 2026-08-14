"""Make `import ai_agent_bridge` deterministic for this test package.

These tests import the bridge as a top-level package (`from ai_agent_bridge
import …`), which requires `scripts/` on sys.path. In full runs that happened
only by import-order luck (an earlier module primed the path); Pytest fastlane
runs changed files alone and failed collection (#6800). Prime it here so any
subset of this package collects standalone.
"""

import sys
from pathlib import Path

_SCRIPTS = str(Path(__file__).resolve().parents[2] / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)
