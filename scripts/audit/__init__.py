"""
Audit module for validating curriculum modules.

This package provides tools for auditing Ukrainian language curriculum modules,
checking grammar constraints, activity requirements, and pedagogical standards.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).parent.parent

__all__ = ["audit_module", "check_learner_state"]


def __getattr__(name: str):
    # Importing a standalone audit utility must not load curriculum checks.
    # Keep the public callable exports available to existing audit consumers.
    if name not in __all__:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    # Full curriculum audits still perform scripts-level imports at call time.
    # Keep their legacy bootstrap behind explicit export access; standalone
    # helpers importing this package never need or execute it.
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    if str(SCRIPT_DIR) not in sys.path:
        sys.path.append(str(SCRIPT_DIR))
    if name == "audit_module":
        from .core import audit_module

        return audit_module
    from .checks.learner_state import check_learner_state

    return check_learner_state
