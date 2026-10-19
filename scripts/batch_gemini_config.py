"""Re-export shim — actual module lives at scripts/batch/batch_gemini_config.py.

Historical context: this used to use importlib.util.spec_from_file_location
to dynamically load the real module under the import name `batch_gemini_config`.
That works at runtime but pyright cannot statically resolve any of the symbols,
producing a wall of false-positive 'unknown import symbol' errors across
v6_build.py, core.py, and ~20 other importers. The static `from ... import *`
re-export gives pyright something it CAN follow without changing runtime
semantics for the existing importers.
"""

# ruff: noqa: F401, F403, I001
# F401/I001: explicit re-imports below are intentional for pyright (star import alone is opaque).
# F403: star re-export is the runtime shim contract.
from typing import TYPE_CHECKING

from batch.batch_gemini_config import *  # re-export everything for pyright
from batch.batch_gemini_config import (
    CASCADE_PER_CALL_MAX_S,
    CLAUDE_MODEL_CORE_CONTENT,
    CURRICULUM_DIR,
    FALLBACK_MODEL,
    FLASH_LITE_MODEL,
    FLASH_MODEL,
    PHASES_DIR,
    PROJECT_ROOT,
    PRO_MODEL,
    PRO_TRACKS,
    SEMINAR_TRACKS,
    get_module_index,
    get_module_paths,
    get_track_config,
    num_for_slug,
    slug_for_num,
)

if TYPE_CHECKING:
    from batch.batch_gemini_config import VENV_PYTHON as VENV_PYTHON


def __getattr__(name: str) -> str:
    """Re-export ``VENV_PYTHON`` without resolving it at import.

    The implementation resolves the interpreter on first use. Binding it
    here would crash release snapshots and copied trees that import this
    shim only for model names.
    """
    if name != "VENV_PYTHON":
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from batch.batch_gemini_config import VENV_PYTHON

    globals()["VENV_PYTHON"] = VENV_PYTHON
    return VENV_PYTHON
