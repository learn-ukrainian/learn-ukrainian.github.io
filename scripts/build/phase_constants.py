"""Canonical V6 pipeline phase order + human-friendly labels.

Extracted from the retired ``scripts/build/v6_build.py`` (#2747 / #1863) so
that out-of-process consumers could read the phase list and labels without
importing the build entrypoint.

The data lives in ``scripts/curriculum/phase_labels.v1.json``, which the
Monitor API (machinery) reads directly; this module loads the same file, so
there is one source of truth (machinery move step 4, slice S2, #12504). A
missing or malformed file raises at import.

Pure data only — this module must never import build/runtime code (keeping it
dependency-free is what lets callers import it cheaply).
"""

import json
from pathlib import Path

_PHASE_LABELS_PATH = Path(__file__).resolve().parents[1] / "curriculum" / "phase_labels.v1.json"
_SCHEMA = "learn-ukrainian.monitor-phase-labels"


def _load() -> tuple[list[str], dict[str, str]]:
    document = json.loads(_PHASE_LABELS_PATH.read_text(encoding="utf-8"))
    if (
        not isinstance(document, dict)
        or set(document) != {"schema", "schema_version", "phases", "phase_labels"}
        or document["schema"] != _SCHEMA
        or type(document["schema_version"]) is not int
        or document["schema_version"] != 1
    ):
        raise ValueError(f"{_PHASE_LABELS_PATH.name}: expected {_SCHEMA} version 1")
    phases, labels = document["phases"], document["phase_labels"]
    if not (isinstance(phases, list) and phases and all(isinstance(phase, str) for phase in phases)):
        raise ValueError(f"{_PHASE_LABELS_PATH.name}: phases must be a non-empty list of strings")
    if not (isinstance(labels, dict) and all(isinstance(label, str) for label in labels.values())):
        raise ValueError(f"{_PHASE_LABELS_PATH.name}: phase_labels must map phase ids to strings")
    return phases, labels


# All phases in pipeline order (used by --resume and by API state reconciliation).
# ``PHASES`` is the stable public alias; ``ALL_PHASES`` is the underlying list.
# They are the same object on purpose.
#
# ``PHASE_LABELS`` keys are phase ids; any phase without an explicit label
# falls back to its kebab-case id via ``PHASE_LABELS.get(name, name)``.
ALL_PHASES, PHASE_LABELS = _load()
PHASES = ALL_PHASES
