"""CLI entry point: python -m scripts.curriculum.validate <level> <slug>."""

import sys

from .validate import main

if __name__ == "__main__":
    sys.exit(main())
