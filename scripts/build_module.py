#!/usr/bin/env python3
"""Backward-compatible shim — use pipeline_lib directly.

All shared utilities have moved to pipeline_lib.py (#671).
This file exists only so that any stale imports like
``from build_module import dispatch_gemini`` continue to work.
"""
from pipeline_lib import *  # noqa: F401,F403

# External scripts historically imported the *raw* dispatch (no rate-limit
# fallback).  Re-export it under the original name so old call-sites work.
from pipeline_lib import dispatch_gemini_raw as dispatch_gemini  # noqa: F811


def main() -> None:
    import sys
    print(
        "build_module.py is now a backward-compat shim.\n"
        "Use build_module_v3.py for the active pipeline.\n"
        "Shared utilities live in pipeline_lib.py.",
        file=sys.stderr,
    )
    sys.exit(1)


if __name__ == "__main__":
    main()
