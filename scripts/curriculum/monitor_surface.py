"""Product calls the Monitor API makes (machinery move step 4, slice S2, #12504).

The Monitor routers under ``scripts/api`` are machinery. They do not import the
pipeline or audit modules below. ``scripts/api/state_helpers.py`` loads this
module once, by the name in ``scripts/curriculum/monitor_paths.v1.json``
(field ``monitor_surface``), and the routers call it.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# ``pipeline.*`` uses bare imports (``from pipeline.core import log``), so
# scripts/ must be importable. These are the module objects the Monitor used
# before this wrapper existed.
_SCRIPTS_DIR = str(Path(__file__).resolve().parents[1])
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from pipeline.consultation import TemplateChange
from pipeline.consultation import apply_template_patch as _apply_template_patch
from pipeline.state import is_complete as phase_is_complete
from pipeline.state import load_state as load_pipeline_state
from scripts.audit.llm_qg_store import (
    current_payload_for_module,
    llm_qg_file_is_current_for_module,
)

__all__ = [
    "apply_template_patch",
    "current_payload_for_module",
    "llm_qg_file_is_current_for_module",
    "load_pipeline_state",
    "phase_is_complete",
]


def apply_template_patch(
    template_path: Path,
    changes: list[dict[str, Any]],
    output_path: Path,
) -> tuple[bool, int]:
    """Apply a consultation proposal's change mappings to one template copy.

    Each mapping is one ``proposed_changes`` entry (``find``, ``replace``,
    ``file``, ``rationale``). Returns ``(success, num_applied)`` from
    ``pipeline.consultation.apply_template_patch``.
    """
    template_changes = [
        TemplateChange(
            find=change.get("find", ""),
            replace=change.get("replace", ""),
            file=change.get("file", ""),
            rationale=change.get("rationale", ""),
        )
        for change in changes
    ]
    result: tuple[bool, int] = _apply_template_patch(template_path, template_changes, output_path)
    return result
