#!/usr/bin/env python3
"""Compatibility entry point for ``orchestration/fleet_repos.py``, the implementation.

Run directly, this file runs the implementation as ``__main__``. Imported, it stays a
module of its own and forwards every attribute it does not define to the implementation.
Patch the implementation module, never this one: a value set here is not seen there.
"""

from __future__ import annotations

if __name__ == "__main__":
    import runpy
    from pathlib import Path

    runpy.run_path(str(Path(__file__).parent / "orchestration" / "fleet_repos.py"), run_name="__main__")
else:
    from typing import Any

    if __package__:
        from .orchestration import fleet_repos as _implementation
    else:  # imported as a top-level module, with this file's directory on sys.path
        from orchestration import fleet_repos as _implementation  # type: ignore[no-redef,attr-defined]

    def __getattr__(name: str) -> Any:
        return getattr(_implementation, name)

    def __dir__() -> list[str]:
        return sorted({*globals(), *dir(_implementation)})
