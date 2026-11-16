"""Compatibility alias for canonical runtime identity."""
import sys

from lu_machinery import model_families as _implementation

sys.modules[__name__] = _implementation
