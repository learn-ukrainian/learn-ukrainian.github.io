"""
Batch Dispatcher Configuration.

Defines all 20 curriculum tracks with their priority order, dependencies,
module counts, and scoring weights for autonomous batch processing.

Track priority order is user-specified (not computed). Dependencies define
prerequisite pass rates before a track becomes eligible.
"""

# ---------------------------------------------------------------------------
# Track definitions — ordered by user-specified priority
# ---------------------------------------------------------------------------

TRACKS = [
    # (priority, track_name, expected_modules, type, dependencies)
    # Dependencies: list of (track, min_pass_rate) tuples
    (1,  "a1",             44,  "core",    []),
    (2,  "a2",             70,  "core",    [("a1", 0.80)]),
    (3,  "b1",             92,  "core",    [("a2", 0.80)]),
    (4,  "b2",             94,  "core",    [("b1", 0.80)]),
    (5,  "c1",            106,  "core",    [("b2", 0.80)]),
    (6,  "b2-hist",       140,  "seminar", [("b1", 0.80)]),
    (7,  "c1-bio",        128,  "seminar", [("b2", 0.80)]),
    (8,  "c1-hist",        98,  "seminar", [("b2-hist", 0.80), ("c1", 0.30)]),
    (9,  "lit",            30,  "seminar", [("b2", 0.80)]),
    (10, "lit-essay",      58,  "seminar", [("lit", 0.80)]),
    (11, "lit-hist-fic",   19,  "seminar", [("lit", 0.80)]),
    (12, "lit-fantastika", 31,  "seminar", [("lit", 0.80)]),
    (13, "lit-war",        20,  "seminar", [("lit", 0.80)]),
    (14, "lit-humor",      13,  "seminar", [("lit", 0.80)]),
    (15, "lit-juvenile",   30,  "seminar", [("lit", 0.80)]),
    (16, "oes",           102,  "seminar", [("c1", 0.80)]),
    (17, "ruth",           79,  "seminar", [("c1", 0.80)]),
    (18, "b2-pro",         15,  "core",    [("b1", 0.80)]),
    (19, "c1-pro",         48,  "core",    [("c1", 0.80)]),
    (20, "c2",            100,  "core",    [("c1", 0.80)]),
]

# Lookup by track name
TRACK_BY_NAME = {t[1]: t for t in TRACKS}
TRACK_NAMES = [t[1] for t in TRACKS]

# ---------------------------------------------------------------------------
# Priority scoring weights (for tiebreaking within same tier)
# ---------------------------------------------------------------------------

SCORING_WEIGHTS = {
    "quick_win":    0.30,   # 10 * (pass/total)^2 — finish near-complete tracks
    "impact":       0.25,   # min(10, failing/10) — big tracks matter more
    "success_rate": 0.20,   # Historical pass rate from batch_state
    "dependency":   0.15,   # Boost if downstream tracks are waiting
    "cost_penalty": -0.10,  # Seminar=7, core_build=4, core_fix=2
}

# Cost estimates by strategy
COST_ESTIMATES = {
    "seminar_build": 7,
    "core_build": 4,
    "core_fix": 2,
    "seminar_fix": 5,
}

# ---------------------------------------------------------------------------
# Timing and retry constants
# ---------------------------------------------------------------------------

COOLDOWN_SECONDS = 30 * 60          # 30 minutes on quota hit
SUBPROCESS_TIMEOUT_SECONDS = 2 * 3600  # 2 hours hard timeout per dispatch
INTER_DISPATCH_PAUSE = 5            # Seconds between dispatches
MAX_STALL_COUNT = 2                 # Zero-progress dispatches before STALLED
STALLED_REVISIT_AFTER_ROTATION = True  # Re-enable STALLED after full rotation

# Max consecutive failures before batch runner self-aborts
RUNNER_MAX_CONSECUTIVE_FAILURES = 5
RUNNER_MAX_FAILURE_RATE = 0.7       # More lenient for dispatcher (runner has own abort)

# ---------------------------------------------------------------------------
# State machine
# ---------------------------------------------------------------------------

class TrackState:
    PENDING   = "PENDING"     # Not yet checked
    ELIGIBLE  = "ELIGIBLE"    # Dependencies met, ready to run
    RUNNING   = "RUNNING"     # Currently dispatched
    COOLDOWN  = "COOLDOWN"    # Quota hit, waiting
    STALLED   = "STALLED"     # 2x zero-progress, revisit later
    DONE      = "DONE"        # 100% pass rate or all modules processed
    BLOCKED   = "BLOCKED"     # Dependencies not met

# ---------------------------------------------------------------------------
# Default state file location
# ---------------------------------------------------------------------------

DISPATCHER_STATE_FILE = "batch_state/dispatcher_state.json"
