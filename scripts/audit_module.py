#!/usr/bin/env python3
"""
Module Audit CLI

Audits curriculum module files for quality, grammar constraints,
activity requirements, and pedagogical standards.

Usage:
    python3 scripts/audit_module.py <file.md> [file2.md ...]
"""

import sys
from audit import audit_module

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/audit_module.py <file.md> [file2.md ...]")
        sys.exit(1)

    args = sys.argv[1:]

    if not args:
        print("Error: No module files specified")
        sys.exit(1)

    any_failure = False
    for file_path in args:
        print(f"\n{'='*40}")
        success = audit_module(file_path)
        if not success:
            any_failure = True

    if any_failure:
        sys.exit(1)
    else:
        sys.exit(0)
