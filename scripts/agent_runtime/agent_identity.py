"""Compatibility alias for canonical runtime identity."""
import sys

from learn_ukrainian_v4_runtime import agent_identity as _implementation

sys.modules[__name__] = _implementation
