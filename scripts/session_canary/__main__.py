"""python -m scripts.session_canary → grok_lane CLI (default)."""

from __future__ import annotations

import sys

from scripts.session_canary.grok_lane import main

if __name__ == "__main__":
    raise SystemExit(main())
