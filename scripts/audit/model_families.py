"""Compatibility alias for canonical runtime identity."""
import sys

from learn_ukrainian_v4_runtime import model_families as _implementation

sys.modules[__name__] = _implementation
