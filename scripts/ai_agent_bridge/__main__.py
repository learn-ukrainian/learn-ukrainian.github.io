"""AI Agent Bridge command runner.

Common commands:
  ask-codex, process-codex
  ask-grok / ask-grok-build, process-grok / process-grok-build
  ask-claude, process-claude
  ask-gemini, process

Run as script or package:
  python scripts/ai_agent_bridge/__main__.py <command>
"""

import sys
from pathlib import Path

# When run directly as a script, add scripts/ to path so the package is importable
if __name__ == "__main__":
    scripts_dir = str(Path(__file__).resolve().parent.parent)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from ai_agent_bridge._cli import main
    main()
else:
    # Imported, not run (``python -m`` runs the branch above): expose the entry point only.
    from ._cli import main
