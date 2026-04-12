"""Re-export shim — actual module lives at scripts/batch/batch_gemini_config.py.

Historical context: this used to use importlib.util.spec_from_file_location
to dynamically load the real module under the import name `batch_gemini_config`.
That works at runtime but pyright cannot statically resolve any of the symbols,
producing a wall of false-positive 'unknown import symbol' errors across
v6_build.py, core.py, and ~20 other importers. The static `from ... import *`
re-export gives pyright something it CAN follow without changing runtime
semantics for the existing importers.
"""

# ruff: noqa: F403, I001
from batch.batch_gemini_config import *  # re-export everything for pyright
from batch.batch_gemini_config import (
    CASCADE_PER_CALL_MAX_S,
    CLAUDE_MODEL_CORE_ACTIVITIES,
    CLAUDE_MODEL_CORE_CONTENT,
    CLAUDE_MODEL_CORE_RESEARCH,
    CLAUDE_MODEL_FINAL_REVIEW,
    CURRICULUM_DIR,
    FALLBACK_MODEL,
    FLASH_LITE_MODEL,
    FLASH_MODEL,
    GEMINI_REVIEW_MODEL,
    PHASES_DIR,
    PROJECT_ROOT,
    PRO_MODEL,
    PRO_TRACKS,
    SEMINAR_TRACKS,
    TIMEOUT_ACTIVITIES,
    TIMEOUT_ANNOTATE,
    TIMEOUT_PRE_VERIFY,
    TIMEOUT_PUBLISH,
    TIMEOUT_REVIEW_CLAUDE,
    TIMEOUT_REVIEW_GEMINI_PROBE,
    TIMEOUT_SKELETON,
    TIMEOUT_VOCAB,
    TIMEOUT_WRITE,
    TIMEOUT_WRITE_NO_TOOLS,
    VENV_PYTHON,
    get_module_index,
    get_module_paths,
    get_track_config,
    num_for_slug,
    slug_for_num,
)
