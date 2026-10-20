"""Rights inputs that set ``rights_class`` (design r3 §1, §6.1 "Rights").

A source's rights class is declared on its ``SourceSpec`` together with the
permissions-register rows that justify it. The transform digest hashes those
register rows, the owned-rights overlay and the display-rule state, so a
rights edit re-derives every affected L1 row instead of copying a stale class.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import yaml

from scripts.lexdata.canonical import sha256_canonical, sha256_file

PERMISSIONS_REGISTER = "docs/sources/permissions-register.yaml"
OWNED_RIGHTS = "registry/sources/owned-rights.yaml"
# §1: the public display rule for Ohoiko/ULP glosses and examples awaits
# operator confirmation; until then they are internal-only evidence.
DISPLAY_RULE_STATE = "ohoiko_ulp_gloss_example_internal_only_until_confirmed"


class RightsInputError(RuntimeError):
    """A declared register row is missing or the rights inputs are unreadable."""


def register_row_hashes(repo_root: Path, row_ids: Iterable[str]) -> dict[str, str]:
    wanted = sorted(set(row_ids))
    if not wanted:
        return {}
    path = repo_root / PERMISSIONS_REGISTER
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise RightsInputError(f"permissions register unreadable: {type(exc).__name__}") from exc
    rows = {row.get("id"): row for row in (payload or {}).get("sources", []) if isinstance(row, dict)}
    missing = [row_id for row_id in wanted if row_id not in rows]
    if missing:
        raise RightsInputError(f"permissions register has no row {missing}")
    return {row_id: sha256_canonical(rows[row_id]) for row_id in wanted}


def rights_contents(repo_root: Path, rights_class: str, register_ids: Iterable[str]) -> dict[str, object]:
    overlay = repo_root / OWNED_RIGHTS
    try:
        overlay_sha = sha256_file(overlay)
    except OSError as exc:
        raise RightsInputError(f"owned-rights overlay unreadable: {type(exc).__name__}") from exc
    return {
        "rights_class": rights_class,
        "register_rows": register_row_hashes(repo_root, register_ids),
        "owned_rights_sha256": overlay_sha,
        "display_rule_state": DISPLAY_RULE_STATE,
    }
