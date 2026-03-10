#!/usr/bin/env python3
"""MDX Generator for Starlight — thin wrapper.

This file delegates to the generate_mdx package (scripts/generate_mdx/).
Kept for backward compatibility with direct invocation:
    python scripts/generate_mdx.py [lang_pair] [level] [module_num] [--validate]

All logic lives in the generate_mdx/ package submodules.
"""

from generate_mdx import main

if __name__ == '__main__':
    main()
