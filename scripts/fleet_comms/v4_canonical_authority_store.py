"""Compatibility alias for the canonical V4 runtime."""
import sys

from learn_ukrainian_v4_runtime import v4_canonical_authority_store as _implementation

sys.modules[__name__] = _implementation
