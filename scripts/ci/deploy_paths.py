"""Fail-closed Pages auto-deploy decision over the product's deploy path policy (#5356, #8306).

Curriculum certification remains authoritative for learner-facing content. The
Pages workflow may redeploy a main revision automatically only when *every*
path since the last successful deployment is known site code. Which paths are
content and which are site code is product data,
``scripts/curriculum/deploy_paths.v1.json``; this module is the machinery that
reads it and applies the rule, and it imports nothing from the product.

The policy has three lists, each matched with ``str.startswith`` except the
exceptions, which match exactly:

- ``content_path_prefixes``: paths that can change published learner content,
  even under ``site/`` or ``data/``. A new content surface must be added here
  before an automatic deployment can cross it.
- ``site_code_path_exceptions``: exact release-pointer files under a content
  prefix. A pointer bump only retargets an already-published Release asset, so
  it is not content drift (#6733). An exception still needs a site-code prefix,
  so a typo'd entry cannot open a non-site path.
- ``site_code_path_prefixes``: the site tree and shared frontend packages. Any
  path outside them is unknown, and unknown is drift.

The content prefixes are evaluated before the site-code prefixes, so the
denylist wins. The file is product data at :data:`POLICY_REL`. The default
read is that path under the checkout that contains this module; pass
``product_root`` when the product checkout is not that directory. The
``path`` argument exists for tests. :func:`load_deploy_paths` raises
:class:`DeployPathsError` when the file is missing, not strict JSON, of another
schema or version (the version must be the integer 1, not ``true`` or ``1.0``),
missing a field, carrying an unknown one, or holding a list that is empty or
duplicated, or an entry outside the path grammar, so a broken policy stops the
eligibility step instead of deciding.

The path grammar is an allowlist: canonical repository-relative segments of
ASCII letters, digits, ``.``, ``_`` and ``-``, no ``.`` or ``..`` segment, and a
trailing ``/`` for a directory prefix. An entry that no Git path can match (a
NUL or other control character, a Unicode lookalike letter, whitespace) would
silently fall through to the broader site-code prefix, so it is refused.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

SCHEMA = "learn-ukrainian.deploy-paths"
SCHEMA_VERSION = 1
POLICY_REL = "scripts/curriculum/deploy_paths.v1.json"
_CHECKOUT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_POLICY_PATH = _CHECKOUT_ROOT / POLICY_REL
_LIST_FIELDS = ("content_path_prefixes", "site_code_path_exceptions", "site_code_path_prefixes")
_FIELDS = frozenset({"schema", "schema_version", *_LIST_FIELDS})
_PATH_RE = re.compile(r"[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*/?\Z")


class DeployPathsError(ValueError):
    """The deploy path policy is missing or malformed."""


@dataclass(frozen=True)
class DeployPaths:
    """A validated deploy path policy. Build one only through :func:`load_deploy_paths`."""

    content_path_prefixes: tuple[str, ...]
    site_code_path_exceptions: frozenset[str]
    site_code_path_prefixes: tuple[str, ...]


@dataclass(frozen=True)
class AutoDeployDecision:
    """A machine-readable result safe to write to ``GITHUB_OUTPUT``."""

    deploy: bool
    reason: str
    offending_paths: tuple[str, ...] = ()


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    keys = [key for key, _ in pairs]
    if len(keys) != len(set(keys)):
        raise DeployPathsError("deploy path policy has a duplicate key")
    return dict(pairs)


def _path_list(data: dict[str, object], field: str) -> tuple[str, ...]:
    values = data[field]
    if not isinstance(values, list) or not values:
        raise DeployPathsError(f"deploy path policy field {field} must be a non-empty list")
    for value in values:
        if not isinstance(value, str) or not value:
            raise DeployPathsError(f"deploy path policy field {field} holds a non-path entry")
        if not _PATH_RE.match(value) or {".", ".."} & set(value.rstrip("/").split("/")):
            raise DeployPathsError(f"deploy path policy field {field} holds a path outside the grammar: {value!r}")
    if len(values) != len(set(values)):
        raise DeployPathsError(f"deploy path policy field {field} holds a duplicate entry")
    return tuple(values)


def _policy_path(product_root: Path | None) -> Path:
    """``POLICY_REL`` under the product checkout, or this module's checkout when omitted."""
    if product_root is None:
        return DEFAULT_POLICY_PATH
    if not isinstance(product_root, Path) or not product_root.is_absolute():
        raise DeployPathsError(f"product root is not an absolute path: {product_root!r}")
    return product_root / POLICY_REL


@lru_cache(maxsize=4)
def load_deploy_paths(path: Path | None = None, *, product_root: Path | None = None) -> DeployPaths:
    """Read and validate the deploy path policy; raise :class:`DeployPathsError` on any defect.

    ``path`` names the file. When it is omitted, the file is :data:`POLICY_REL`
    under ``product_root``, an absolute product checkout. The default product
    checkout is the one that contains this module.
    """
    if path is not None and product_root is not None:
        raise DeployPathsError("pass path or product_root, not both")
    if path is None:
        path = _policy_path(product_root)
    try:
        data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicate_keys)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DeployPathsError(f"deploy path policy unreadable: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise DeployPathsError("deploy path policy must be a JSON object")
    version = data.get("schema_version")
    if data.get("schema") != SCHEMA or type(version) is not int or version != SCHEMA_VERSION:
        raise DeployPathsError(f"deploy path policy must be {SCHEMA} version {SCHEMA_VERSION}")
    if set(data) != _FIELDS:
        raise DeployPathsError(f"deploy path policy fields must be exactly {sorted(_FIELDS)}")
    return DeployPaths(
        content_path_prefixes=_path_list(data, "content_path_prefixes"),
        site_code_path_exceptions=frozenset(_path_list(data, "site_code_path_exceptions")),
        site_code_path_prefixes=_path_list(data, "site_code_path_prefixes"),
    )


def decide_auto_deploy(changed_paths: Iterable[str], policy: DeployPaths | None = None) -> AutoDeployDecision:
    """Classify a NUL-safe git path sequence with a deny-by-default policy."""
    paths = tuple(changed_paths)
    if not paths:
        return AutoDeployDecision(deploy=False, reason="no_changed_paths", offending_paths=())
    if policy is None:
        policy = load_deploy_paths()

    content_drift_paths: list[str] = []
    unknown_paths: list[str] = []

    for path in paths:
        if path in policy.site_code_path_exceptions:
            # Still require the site-code prefix so a typo'd exception cannot
            # open non-site paths.
            if not path.startswith(policy.site_code_path_prefixes):
                unknown_paths.append(path)
            continue
        if path.startswith(policy.content_path_prefixes):
            content_drift_paths.append(path)
            continue
        if not path.startswith(policy.site_code_path_prefixes):
            unknown_paths.append(path)
            continue

    if content_drift_paths:
        return AutoDeployDecision(
            deploy=False,
            reason="content_drift",
            offending_paths=tuple(content_drift_paths),
        )

    if unknown_paths:
        return AutoDeployDecision(
            deploy=False,
            reason="unknown_path",
            offending_paths=tuple(unknown_paths),
        )

    return AutoDeployDecision(deploy=True, reason="site_code_only", offending_paths=())
