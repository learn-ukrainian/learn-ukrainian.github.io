"""Compatibility alias for the canonical Fleet schema shipped with V4."""
import sys

from learn_ukrainian_v4_runtime import pg_schema as _implementation

sys.modules[__name__] = _implementation
