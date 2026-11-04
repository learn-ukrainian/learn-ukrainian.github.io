#!/usr/bin/env python3
"""Pre-commit: regenerate the Atlas lexicon code-fingerprint.

Root-cause fix for the recurring "Atlas Manifest Freshness" CI failure (#3649).

The committed sidecar ``site/src/data/lexicon-manifest.fingerprint.json`` hashes
``scripts/lexicon/*.py`` (see ``scripts/lexicon/manifest_fingerprint.py``). It
must be regenerated whenever that code changes, but humans and agents kept
forgetting — every such miss turns the gate red on every PR that touches the
trigger paths (#3603 -> #3629, #3626 -> #3628, #3646 -> #3649). This hook
regenerates the sidecar deterministically at commit time; the companion
``.pre-commit-config.yaml`` entry then runs ``git diff --exit-code`` on the
sidecar, so a drifted fingerprint blocks the commit until the refreshed file is
staged. After that, drift cannot reach ``main``.

Deliberately lives in ``scripts/pre_commit/`` rather than ``scripts/lexicon/``:
the latter is the hashed glob, so a maintainer script there would churn the very
fingerprint it maintains.

This machinery wrapper does not import the product fingerprint code: the
product names ``manifest_fingerprint.main --write`` in
``scripts/build/pre_commit_entry_points.v1.json`` and
``scripts.pre_commit.product_entry`` runs it. That entry point writes the
sidecar and prints the confirmation line.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.pre_commit.product_entry import run_entry_point

HOOK_ID = "atlas-lexicon-fingerprint-drift"


def main() -> int:
    return run_entry_point(HOOK_ID)


if __name__ == "__main__":
    raise SystemExit(main())
