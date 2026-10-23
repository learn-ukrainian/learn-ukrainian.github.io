"""Invariants for ``scripts/audit/config.LEVEL_CONFIG`` and the
audit ↔ pipeline reconciliation introduced in #1550 unit 4.

These invariants capture the outcome of the audit/pipeline config sweep:

1. Activity counts are MINIMUMS. Every level has a non-zero
   ``min_activities`` floor (real failures should be detectable, not
   silently swallowed by ``0``).
2. Type-diversity is enforced. Every level has ``min_types_unique >= 2``.
3. The forbidden / required / allowed / priority sets within audit are
   self-consistent (forbidden cannot also be priority/required/allowed).
4. Audit's ``priority_types`` are a subset of the union of the pipeline's
   inline + workbook allowed types — i.e. the writer can actually emit
   what the audit says it prefers.

Run: ``.venv/bin/pytest tests/audit/test_config_invariants.py -v``
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.reads_content

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from audit.config import LEVEL_CONFIG


def test_folk_resolves_to_seminar_thresholds_not_a1() -> None:
    from audit.config import get_level_config
    from audit.parsing import detect_focus, detect_level

    fm = "level: FOLK\nphase: FOLK.B\n"
    fp = "curriculum/l2-uk-en/folk/kalendarna-obriadovist-zvychai/module.md"
    level_code, module_num, _ = detect_level(fp, fm)
    module_focus = detect_focus(fm, level_code, module_num, "", fp)

    cfg = get_level_config(level_code, module_focus)
    a1 = LEVEL_CONFIG["A1"]
    assert cfg is not a1, (
        "folk audited against the A1 default config — the FOLK seminar "
        "thresholds are not being applied."
    )
    assert cfg["min_vocab"] == LEVEL_CONFIG["FOLK"]["min_vocab"] == 24
    assert cfg["target_words"] == 4000
    assert cfg["min_types_unique"] == 4
