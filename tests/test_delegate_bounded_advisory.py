"""#9275 envelope integrity and #10919 driver-brief admission and replay.

Outside #10919 recon/classification and bounded implementation, every ``gpt-6-luna``
dispatch needs an envelope issued by a finished ``gpt-6.1-sol`` advisory task and
bound to this dispatch's arguments. Gemini 3.8 Flash High does not (#12291).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from scripts.agent_runtime import bounded_advisory

# Delivery is proven against the driver-bound destination, never the worker's
# tracking refs (#10931); workers built by _bounded_worktree push to its origin.git.

# Lease directory names are the task ids. One module-wide id shares a lease
# across xdist workers (#9927). Each case gets its own worker id and advisor id.


# --- M1 -------------------------------------------------------------------


# --- M2 -------------------------------------------------------------------


# --- M3 -------------------------------------------------------------------


# --- M4 -------------------------------------------------------------------


# --- M5 -------------------------------------------------------------------


# --- M6 -------------------------------------------------------------------


# --- M7 -------------------------------------------------------------------


# --- M8 -------------------------------------------------------------------


# --- M9 -------------------------------------------------------------------


# --- M11 / M18: admitted Gemini Flash dispatches ---------------------------


# --- M13 / M14 --------------------------------------------------------------


# --- The advisor side --------------------------------------------------------


# --- M12 / M13 at finalize: the envelope ceilings ------------------------------


# The launch a worker admitted by ``_admitted_worker`` runs: what ``_start_worker`` passes.
_BOUND_LAUNCH_ARGS = (
    "effort", "hard_timeout", "silence_timeout", "initial_response_timeout", "max_budget_usd", "provider",
    "finalize_open_pr",
)  # fmt: skip


# --- Pure helpers --------------------------------------------------------------


def test_numstat_parser_and_test_path_classifier():
    entries = bounded_advisory.parse_numstat_z("3\t1\tsrc/a.py\x00-\t-\timg.png\x0010\t0\ttests/test_a.py\x00")
    assert entries == [(3, 1, "src/a.py"), (None, None, "img.png"), (10, 0, "tests/test_a.py")]
    verdict = bounded_advisory.ceiling_verdict(entries, max_changed_files=3, max_non_test_loc=4)
    assert (verdict["changed_files"], verdict["non_test_loc"], verdict["exceeded"]) == (3, 4, [])
    assert bounded_advisory.is_test_path("scripts/x/test_y.py")
    assert bounded_advisory.is_test_path("pkg/conftest.py")
    assert bounded_advisory.is_test_path("site/foo_test.ts")
    assert not bounded_advisory.is_test_path("scripts/testing_helpers.py")
    with pytest.raises(ValueError):
        bounded_advisory.parse_numstat_z("garbage\x00")


# --- M6: the binding covers the prompt text, not only the prompt path -------------


# --- Round 2 (review of record): B1 the worker backstop -------------------------


# --- Round 2: B2 classification of normalized owned paths ------------------------


# --- Round 2: B3 the finish-time seal --------------------------------------------


# --- Round 3: B3 the content-exemption completion gate ---------------------------


# --- Round 5: success only after every completion gate has durably passed ----------
#
# Fault injection for both gates, each with a passing, a failing and an
# unmeasurable tree. An interrupt (the worker's SIGTERM handler raises
# KeyboardInterrupt) lands during the measurement, between the measurement and
# its recording, or at the terminal write; the persisted record is what counts.

# An earlier run's passing measurement: it must never stand as this run's evidence.


# #9275 r7: one definition of the completion gates a record calls for, shared by
# the worker's terminal settle and the ask-* review wrapper.


# #10919: the driver brief is a second admission source, with the same replay boundary.
