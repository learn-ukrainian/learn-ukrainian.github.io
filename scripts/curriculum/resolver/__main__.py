"""CLI: python -m scripts.curriculum.resolver {resolve,questions,apply,check} <level> <slug> <n>."""

import sys

from .stream import main

if __name__ == "__main__":
    sys.exit(main())
