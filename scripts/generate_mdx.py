#!/usr/bin/env python3
"""MDX Generator for Site — thin wrapper.

This file delegates to the generate_mdx package (scripts/generate_mdx/).
Kept for backward compatibility with direct invocation:
    python scripts/generate_mdx.py [lang_pair] [level] [module_num] [--validate]

Running a file puts ``scripts/`` on ``sys.path`` instead of the repository root,
so the package's ``scripts.*`` imports do not resolve. Re-execute the package
from the repository root so the direct and module entry points behave alike:

    python -m scripts.generate_mdx [lang_pair] [level] [module_num] [--validate]
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    os.chdir(REPO_ROOT)
    os.execv(
        sys.executable,
        [sys.executable, "-m", "scripts.generate_mdx", *sys.argv[1:]],
    )


if __name__ == '__main__':
    main()
