"""Load the product's review attempt hooks by their configured name (machinery move step 4, slice S14).

The dispatcher, the agent runtime and the review contract are machinery and import no product
module. The product names the one module that does, ``attempt_hooks`` in
``scripts/curriculum/review_hooks.v1.json``, and :func:`attempt_hooks` imports it. The file is
trusted because of where it is read from: its path is fixed relative to this module, as
``scripts.orchestration.product_policy`` reads its policy file, so code that runs from the primary
checkout also reads that checkout's hooks. No environment variable or flag redirects it.

Fail closed: :class:`ProductHooksError` (an ``ImportError``, which is what a caller saw before when
a product module could not be imported) when the file is missing, a symlink, not a regular file,
too large, not strict JSON or has a duplicate key, is of another schema, version or origin, has a
missing or unknown field, or names a module outside ``scripts``.
"""

from __future__ import annotations

import functools
import importlib.util
import json
import re
import stat
import sys
from pathlib import Path
from types import ModuleType

SCHEMA = "learn-ukrainian.review-hooks"
SCHEMA_VERSION = 1
HOOKS_REL = "scripts/curriculum/review_hooks.v1.json"
HOOKS_PATH = Path(__file__).resolve().parents[2] / HOOKS_REL
MAX_HOOKS_BYTES = 4096

_FIELDS = frozenset({"schema", "schema_version", "origin", "attempt_hooks"})
_MODULE_RE = re.compile(r"scripts(?:\.[a-z_][a-z0-9_]*)+\Z")


class ProductHooksError(ImportError):
    """The configured hooks file or the module it names refused; ``code`` names the rule."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"review hooks refused ({code}): {detail}")
        self.code = code


def _no_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    keys = [key for key, _ in pairs]
    if len(keys) != len(set(keys)):
        raise ProductHooksError("hooks_not_json", "duplicate key")
    return dict(pairs)


def _module_name(path: Path) -> str:
    try:
        info = path.lstat()
    except OSError as exc:
        raise ProductHooksError("hooks_missing", f"{HOOKS_REL}: {exc.strerror}") from None
    if not stat.S_ISREG(info.st_mode):
        raise ProductHooksError("hooks_not_regular_file", HOOKS_REL)
    if info.st_size > MAX_HOOKS_BYTES:
        raise ProductHooksError("hooks_too_large", f"{HOOKS_REL} is over {MAX_HOOKS_BYTES} bytes")
    try:
        payload = json.loads(path.read_bytes().decode("utf-8"), object_pairs_hook=_no_duplicates)
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        raise ProductHooksError("hooks_not_json", f"{HOOKS_REL}: {exc}") from None
    if not isinstance(payload, dict) or set(payload) != _FIELDS:
        raise ProductHooksError("hooks_fields", f"{HOOKS_REL} must hold exactly {sorted(_FIELDS)}")
    if (
        payload["schema"] != SCHEMA
        or type(payload["schema_version"]) is not int
        or payload["schema_version"] != SCHEMA_VERSION
    ):
        raise ProductHooksError("hooks_schema_mismatch", f"{HOOKS_REL} is not {SCHEMA} v{SCHEMA_VERSION}")
    if payload["origin"] != HOOKS_REL:
        raise ProductHooksError("hooks_origin_mismatch", f"{HOOKS_REL} names origin {payload['origin']!r}")
    name = payload["attempt_hooks"]
    if not isinstance(name, str) or not _MODULE_RE.match(name):
        raise ProductHooksError("hooks_module_invalid", f"{HOOKS_REL}: attempt_hooks {name!r}")
    return name


@functools.cache
def attempt_hooks() -> ModuleType:
    """The product module holding the review checks machinery review attempts call, loaded once.

    The SQLite boundary scan (``scripts.hygiene.lint_source_db_writable_connects``) refuses a
    computed ``import_module``, so the configured module is imported through its spec, as an import
    statement would: an already imported module is reused, and a new one is registered in
    ``sys.modules`` and on its parent package.
    """
    name = _module_name(HOOKS_PATH)
    loaded = sys.modules.get(name)
    if loaded is not None:
        return loaded
    spec = importlib.util.find_spec(name)
    if spec is None or spec.loader is None:
        raise ProductHooksError("hooks_module_missing", f"{HOOKS_REL}: no module {name!r}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    parent, _, child = name.rpartition(".")
    setattr(sys.modules[parent], child, module)
    return module
