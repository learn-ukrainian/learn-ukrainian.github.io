"""Compatibility alias for shared runtime contracts."""
import sys

from learn_ukrainian_v4_runtime import contracts as _implementation

sys.modules[__name__] = _implementation
