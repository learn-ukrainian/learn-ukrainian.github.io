"""
Audit module for validating curriculum modules.

This package provides tools for auditing Ukrainian language curriculum modules,
checking grammar constraints, activity requirements, and pedagogical standards.
"""

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.append(str(SCRIPT_DIR))

from .checks.learner_state import check_learner_state
from .core import audit_module

__all__ = ['audit_module', 'check_learner_state']
