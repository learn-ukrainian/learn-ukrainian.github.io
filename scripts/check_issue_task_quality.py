#!/usr/bin/env python3
"""Compatibility entry point for ``ci/check_issue_task_quality.py``, the implementation.

Run directly, this file runs the implementation as ``__main__``. Imported, it stays a
module of its own and forwards every attribute it does not define to the implementation.
Patch the implementation module, never this one: a value set here is not seen there.
"""

from __future__ import annotations

if __name__ == "__main__":
    import runpy
    from pathlib import Path

    runpy.run_path(str(Path(__file__).parent / "ci" / "check_issue_task_quality.py"), run_name="__main__")
else:
    from typing import Any

    if __package__:
        from .ci import check_issue_task_quality as _implementation
    else:  # imported as a top-level module, with this file's directory on sys.path
        import sys
        from pathlib import Path

        # The implementation imports the package absolutely and puts the checkout on
        # sys.path only when it is itself top-level; as ``ci.<module>`` it is not, so do it here.
        _checkout = str(Path(__file__).resolve().parents[1])
        if _checkout not in sys.path:
            sys.path.insert(0, _checkout)
        from ci import check_issue_task_quality as _implementation  # type: ignore[no-redef]

    def __getattr__(name: str) -> Any:
        return getattr(_implementation, name)

    def __dir__() -> list[str]:
        return sorted({*globals(), *dir(_implementation)})
