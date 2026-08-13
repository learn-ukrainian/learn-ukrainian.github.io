#!/usr/bin/env python3
"""Restore Atlas definition cards chopped by the retired 900-char cap (#6736).

Pre-#6437 ``_definition_body`` hard-capped dictionary card text at 900 chars,
amputating multi-sense ВТС/СУМ-20 articles mid-word (e.g. подаватися sense 8
ends «Става…»). The cap is gone, but the published manifest still carries the
chopped payloads: the translation-delta merge is additive-only by contract and
never overwrites a non-empty ``definition_cards`` field, so re-enrichment alone
cannot heal them.

This script rebuilds ONLY provably-chopped ``vts``/``sum20`` cards from the
attested local slovnyk.me cache (schema-current rows, read-only). It never
fetches from the network, never invents text, and is fail-closed: a card is
replaced only when the rebuilt body is strictly longer and the chopped body is
a prefix of it modulo whitespace (cross-reference-resolved cards fail this
check and are reported, not touched).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "site" / "src" / "data" / "lexicon-manifest.json"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lexicon import enrich_manifest
from scripts.lexicon.manifest_io import load_manifest
from scripts.lexicon.publish_manifest import (
    DEFAULT_GZIP,
    DEFAULT_POINTER,
    build_pointer_payload,
    evaluate_manifest_pointer_write_gate,
    gzip_manifest,
    write_pointer,
)

# Signature of the pre-#6437 cap: ``_truncate_text(body, 900)`` emitted
# ``cleaned[:899].rstrip() + "…"``, so a chopped body is exactly 899 or 900
# chars long and ends with the ellipsis the cutter appended. Legitimate
# dictionary prose never lands on this exact length + ellipsis pair.
CHOP_SIGNATURE_LENGTHS = (899, 900)
ELLIPSIS = "…"

# Manifest card id → slovnyk.me cache slug. Only slovnyk-backed cards can be
# restored from the local cache; grinchenko cards come from sources.db and are
# out of scope here (none are chopped at 900 in practice).
_CARD_ID_TO_SLOVNYK_SLUG = {"vts": "vts", "sum20": "newsum"}


def _is_chopped(text: object) -> bool:
    return isinstance(text, str) and len(text) in CHOP_SIGNATURE_LENGTHS and text.endswith(ELLIPSIS)


def find_chopped_cards(manifest: dict[str, Any]) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    """Return ``(entry, card)`` pairs whose single definition carries the chop signature."""
    hits: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for entry in manifest.get("entries") or []:
        if not isinstance(entry, dict):
            continue
        enrichment = entry.get("enrichment")
        if not isinstance(enrichment, dict):
            continue
        cards = enrichment.get("definition_cards")
        if not isinstance(cards, list):
            continue
        for card in cards:
            if not isinstance(card, dict):
                continue
            if card.get("id") not in _CARD_ID_TO_SLOVNYK_SLUG:
                continue
            definitions = card.get("definitions")
            if isinstance(definitions, list) and len(definitions) == 1 and _is_chopped(definitions[0]):
                hits.append((entry, card))
    return hits


def _cached_slovnyk_row(lemma: str, slug: str) -> dict[str, Any] | None:
    """Read the lemma's (or its unambiguous base's) cached slovnyk row.

    Read-only: uses the no-fetch cache reader so a cache miss is a residual,
    never a network call or a cache write.
    """
    cache = enrich_manifest._read_cached_slovnyk_rows(lemma)
    row = enrich_manifest._cache_lookup(cache, slug)
    if row:
        return row
    base = enrich_manifest._vesum_base_lemma(lemma)
    if base:
        base_cache = enrich_manifest._read_cached_slovnyk_rows(base)
        return enrich_manifest._cache_lookup(base_cache, slug)
    return None


_WHITESPACE_RE = re.compile(r"\s+")


def _squash(text: str) -> str:
    """Whitespace-free form for the prefix guard.

    Cache rows re-normalized by newer fetch code (#6465 empty-string join) can
    differ from the published chopped body only in inline-tag spacing
    («невідм. ,» vs «невідм.,»). The underlying attested article is the same,
    so the guard compares with whitespace squashed.
    """
    return _WHITESPACE_RE.sub("", text)


def rebuild_card_body(lemma: str, card_id: str, chopped: str) -> str | None:
    """Rebuild one chopped card body from the local slovnyk cache.

    Returns the full body, or ``None`` when no attested local source exists or
    the rebuilt body fails the prefix guard (fail-closed).
    """
    slug = _CARD_ID_TO_SLOVNYK_SLUG.get(card_id)
    if slug is None:
        return None
    row = _cached_slovnyk_row(lemma, slug)
    if not row:
        return None
    lookup_word = enrich_manifest._slovnyk_lookup_word(lemma)
    body = enrich_manifest._definition_body(
        row.get("text"),
        headword=str(row.get("word") or lookup_word),
        strip_leading_headword=True,
    )
    if not body:
        return None
    # Prefix guard: the chopped body was produced by cutting the same article,
    # so it must be a verbatim prefix (minus the appended ellipsis), allowing
    # only whitespace drift from fetch-side re-normalization — including the
    # retired letter-spaced join (#6465), which also means raw character length
    # cannot gate the swap (the clean body can be shorter in chars while
    # carrying strictly more content). Compare squashed forms and require the
    # rebuilt body to continue past the chop point. A real mismatch means the
    # published card came from a different resolution path (e.g. a «див.»
    # cross-reference) — leave it untouched.
    chopped_prefix = _squash(chopped[: -len(ELLIPSIS)])
    body_squashed = _squash(body)
    if len(body_squashed) <= len(chopped_prefix):
        return None
    if not body_squashed.startswith(chopped_prefix):
        return None
    return body


def repair_truncated_cards(
    manifest: dict[str, Any],
    *,
    limit: int | None = None,
) -> dict[str, Any]:
    """Restore chopped vts/sum20 cards in place from the local slovnyk cache."""
    hits = find_chopped_cards(manifest)
    if limit is not None:
        hits = hits[:limit]
    repaired = 0
    residual_no_cache: list[str] = []
    residual_guard: list[str] = []
    for entry, card in hits:
        lemma = str(entry.get("lemma") or "")
        chopped = card["definitions"][0]
        body = rebuild_card_body(lemma, str(card.get("id")), chopped)
        if body is None:
            row = _cached_slovnyk_row(lemma, _CARD_ID_TO_SLOVNYK_SLUG[str(card.get("id"))])
            (residual_no_cache if row is None else residual_guard).append(f"{lemma}:{card.get('id')}")
            continue
        card["definitions"] = [body]
        repaired += 1
    return {
        "chopped_cards": len(hits),
        "repaired": repaired,
        "residual_no_cache": residual_no_cache,
        "residual_guard_mismatch": residual_guard,
    }


def _refresh_manifest_fingerprint(manifest: dict[str, Any]) -> None:
    fingerprint_payload = enrich_manifest.write_fingerprint(enrich_manifest.DEFAULT_FINGERPRINT, root=ROOT)
    manifest["manifest_fingerprint"] = {
        "schema_version": fingerprint_payload["schema_version"],
        "fingerprint": fingerprint_payload["fingerprint"],
    }


def _write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_default_release_pointer(
    manifest_path: Path,
    *,
    bootstrap_no_baseline: bool = False,
    allow_richness_regression_reason: str | None = None,
) -> dict[str, Any] | None:
    if manifest_path.resolve() != DEFAULT_MANIFEST.resolve():
        return None
    richness_gate = evaluate_manifest_pointer_write_gate(
        manifest_path,
        bootstrap_no_baseline=bootstrap_no_baseline,
        allow_richness_regression_reason=allow_richness_regression_reason,
    )
    gzip_manifest(manifest_path, DEFAULT_GZIP)
    pointer = build_pointer_payload(
        manifest_path=manifest_path,
        gzip_path=DEFAULT_GZIP,
        richness_gate=richness_gate,
    )
    write_pointer(DEFAULT_POINTER, pointer)
    return pointer


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Restore 900-char-chopped Atlas definition cards from the local slovnyk cache (#6736)."
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument(
        "--local",
        action="store_true",
        help="Read manifest path directly instead of hydrating the canonical release asset.",
    )
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--write", action="store_true")
    parser.add_argument(
        "--allow-richness-regression",
        metavar="REASON",
        help="Record an operator decision to permit a richness regression while writing the pointer.",
    )
    parser.add_argument(
        "--bootstrap-no-baseline",
        action="store_true",
        help="Write only an initial pointer when no canonical release asset exists; records bootstrap=true.",
    )
    args = parser.parse_args()

    manifest_path = args.manifest if args.manifest.is_absolute() else ROOT / args.manifest
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if args.local else load_manifest(manifest_path)

    summary = repair_truncated_cards(manifest, limit=args.limit)
    printable = {
        **summary,
        "residual_no_cache_count": len(summary["residual_no_cache"]),
        "residual_guard_mismatch_count": len(summary["residual_guard_mismatch"]),
    }
    print(json.dumps(printable, ensure_ascii=False, indent=2))

    if args.write:
        if summary["repaired"]:
            _refresh_manifest_fingerprint(manifest)
            _write_manifest(manifest_path, manifest)
            pointer = _write_default_release_pointer(
                manifest_path,
                bootstrap_no_baseline=args.bootstrap_no_baseline,
                allow_richness_regression_reason=args.allow_richness_regression,
            )
            if pointer:
                print(
                    f"Updated local atlas-manifest pointer {pointer['manifest_fingerprint']} {pointer['json_sha256']}"
                )
        else:
            print("Nothing repaired; manifest left untouched.")
    else:
        print("Dry run only; pass --write to update the manifest.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
