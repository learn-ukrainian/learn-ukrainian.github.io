"""Compatibility entrypoint for the canonical V4 runtime package."""

import sys

from learn_ukrainian_v4_runtime import v4_a9_evaluation_package as _implementation

if __name__ == "__main__":
    _implementation.main()
else:
    sys.modules[__name__] = _implementation
