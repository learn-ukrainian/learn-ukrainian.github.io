"""L2 stage contract for ``build_store`` (design r3 §5, §6 "L2 and L3 are fully
recomputed for each generation").

The resolver rules R0-R5 belong to slice (e). F owns the contract and the
generic steps around it: a stage inserts exactly one ``l2_link`` per
``l1_lex_item`` (copying the leaf's keys) plus the candidates it considered;
``build_store`` then fills ``candidate_set_sha256``, carries adjudications
forward (§5.4, §6.2) and verifies the result.

``PendingResolverStage`` is F's default: with no resolver installed every
refused leaf links as ``refused`` and every other leaf as ``unavailable``
(``resolver_not_installed``), so no leaf can carry a lexeme.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol, runtime_checkable

RESOLVER_NOT_INSTALLED = "resolver_not_installed"


@runtime_checkable
class L2Stage(Protocol):
    resolver_version: str
    stores: tuple[str, ...]

    def store_fingerprints(self, l0: Mapping[str, Any]) -> dict[str, str]:
        """Fingerprints of the identity stores this stage resolves against."""
        ...

    def link(self, conn: Any) -> None:
        """Insert one ``l2_link`` per leaf and its ``l2_candidate`` rows."""
        ...


class PendingResolverStage:
    resolver_version = "none"
    stores: tuple[str, ...] = ()

    def store_fingerprints(self, l0: Mapping[str, Any]) -> dict[str, str]:
        return {}

    def link(self, conn: Any) -> None:
        conn.execute(
            """
            INSERT INTO l2_link (item_id, key_stressed, key_unstressed, key_fold, status,
                                 unavailable_reason, resolver_version)
            SELECT item_id, key_stressed, key_unstressed, key_fold,
                   CASE WHEN refusal_code IS NULL THEN 'unavailable' ELSE 'refused' END,
                   CASE WHEN refusal_code IS NULL THEN ? END, ?
            FROM l1_lex_item ORDER BY item_id
            """,
            (RESOLVER_NOT_INSTALLED, self.resolver_version),
        )
