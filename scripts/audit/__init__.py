"""
Audit module for validating curriculum modules.

This package provides tools for auditing Ukrainian language curriculum modules,
checking grammar constraints, activity requirements, and pedagogical standards.
"""

import sys
from pathlib import Path

# Package imports need the repository root before checks resolve scripts.config.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

SCRIPT_DIR = Path(__file__).parent.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.append(str(SCRIPT_DIR))

__all__ = ["audit_module", "check_learner_state"]


def __getattr__(name: str):
    # Importing a standalone audit utility must not load curriculum checks.
    # Keep the public callable exports available to existing audit consumers.
    if name == "audit_module":
        from .core import audit_module

        return audit_module
    if name == "check_learner_state":
        from .checks.learner_state import check_learner_state

        return check_learner_state
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
