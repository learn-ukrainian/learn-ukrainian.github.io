"""CLI entry point: python -m scripts.review.validate."""

import sys

from .validate import main

if __name__ == "__main__":
    sys.exit(main())
