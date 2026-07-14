"""Stable, replay-grade QG run artifact serialization.

The offline bakeoff and production shadow capture deliberately share only this
artifact contract.  They retain separate execution and routing paths.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

RUN_SCHEMA_VERSION = "qg_bakeoff_run.v2"


def serialize_qg_run_v2(
    dispatch: Mapping[str, Any],
    payload: Mapping[str, Any],
    meta: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a qg_bakeoff_run.v2 artifact without mutating caller data.

    ``meta`` owns run-specific facts such as fixture/target identity, route,
    gate outcomes, scoring, and timing.  The shared fields are deliberately
    constrained to the captured dispatcher metadata and canonical reviewer
    payload so either runner can be replayed by :mod:`layerb_shadow`.
    """

    if "dispatch" in meta or "payload" in meta:
        raise ValueError("qg run metadata must not override dispatch or payload")
    schema_version = meta.get("schema_version", RUN_SCHEMA_VERSION)
    if schema_version != RUN_SCHEMA_VERSION:
        raise ValueError(f"qg run serializer requires {RUN_SCHEMA_VERSION}, got {schema_version!r}")
    return {
        **dict(meta),
        "schema_version": RUN_SCHEMA_VERSION,
        "dispatch": dict(dispatch),
        "payload": dict(payload),
    }
