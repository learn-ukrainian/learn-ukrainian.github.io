"""Monitor entry for the Atlas job registry.

The Monitor's atlas-jobs, occupancy, and fleet-worker views call this module
instead of importing ``scripts.lexicon.runner.atlas_job``. Attribute lookup
is delegated on each call, so a test that patches the job module still sees
the same functions and constants.

This module stays separate from ``scripts.curriculum.monitor_surface``, which
is the curriculum monitor entry.
"""

from __future__ import annotations

from typing import Any

from scripts.lexicon.runner import atlas_job as _atlas_job


def __getattr__(name: str) -> Any:
    return getattr(_atlas_job, name)
