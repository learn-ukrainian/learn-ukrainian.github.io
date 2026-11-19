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
    PHASES_DIR,
    PROJECT_ROOT,
    PRO_TRACKS,
    SEMINAR_TRACKS,
    get_module_index,
    get_module_paths,
    get_track_config,
    num_for_slug,
    slug_for_num,
)

if TYPE_CHECKING:
    from batch.batch_gemini_config import (
        FLASH_LITE_MODEL as FLASH_LITE_MODEL,
        FLASH_MODEL as FLASH_MODEL,
        GEMINI_REVIEW_MODEL as GEMINI_REVIEW_MODEL,
        HYDROGEN_MODEL as HYDROGEN_MODEL,
        NEON_MODEL as NEON_MODEL,
        PRO_MODEL as PRO_MODEL,
        VENV_PYTHON as VENV_PYTHON,
    )

# Model seats resolve from the installed catalog on first access, so importing this shim never needs a seat.
_LAZY_NAMES = frozenset({
    "FLASH_LITE_MODEL", "FLASH_MODEL", "GEMINI_REVIEW_MODEL", "HYDROGEN_MODEL", "NEON_MODEL", "PRO_MODEL",
})


def __getattr__(name: str) -> str:
    """Re-export ``VENV_PYTHON`` and the model seats without resolving them at import.

    The implementation resolves the interpreter on first use. Binding it
    here would crash release snapshots and copied trees that import this
    shim only for model names.
    """
    if name != "VENV_PYTHON" and name not in _LAZY_NAMES:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    import batch.batch_gemini_config as real

    value = getattr(real, name)
    globals()[name] = value
    return value
