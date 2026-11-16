#!/usr/bin/env python3
"""Compatibility entry point for ``lu_machinery.research.research_quality``, the implementation.

Run directly, this file runs the implementation as ``__main__``. Imported, it stays a
module of its own and forwards every attribute it does not define to the implementation.
Patch the implementation module, never this one: a value set here is not seen there.
"""

from __future__ import annotations

if __name__ == "__main__":
    import runpy

    runpy.run_module("lu_machinery.research.research_quality", run_name="__main__", alter_sys=True)
else:
    from typing import Any

    from lu_machinery.research import research_quality as _implementation

    def __getattr__(name: str) -> Any:
        return getattr(_implementation, name)

    def __dir__() -> list[str]:
        return sorted({*globals(), *dir(_implementation)})
