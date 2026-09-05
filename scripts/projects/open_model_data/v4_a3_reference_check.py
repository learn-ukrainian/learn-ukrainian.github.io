"""Compatibility entrypoint for the canonical V4 runtime package."""

import sys

from learn_ukrainian_v4_runtime import v4_a3_reference_check as _implementation

if __name__ == "__main__":
    _implementation.main()
else:
    sys.modules[__name__] = _implementation
