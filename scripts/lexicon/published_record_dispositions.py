"""Mandatory, contribution-scoped holds and reviewed supersession for #10181.

Recovery data is immutable input. Review receipt validation here is structural;
root owns genuine completed CF, same-head CI and merge authorization.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from scripts.audit.source_inventory_intake import SourceInventoryError
from scripts.audit.source_inventory_review_decisions import source_inventory_key
from scripts.orchestration.integration_sweep import parse_marker

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LEDGER_PATH = Path("registry/lexicon/published-record-dispositions/10181-six.yaml")
PRESERVATION_PATH = LEDGER_PATH.with_suffix(".preserved.json")
ROW_IDS = tuple(f"10181-{n:02}" for n in range(1, 7))
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


class DispositionError(SourceInventoryError):
    """A disposition contract failed; callers must not publish or mutate."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def ordered_digest(entries: Sequence[Mapping[str, Any]]) -> str:
    digest = hashlib.sha256()
    for entry in entries:
        digest.update(canonical_bytes(entry) + b"\n")
    return digest.hexdigest()


def _require(condition: Any, message: str) -> None:
    if not condition:
        raise DispositionError(message)


def _path(root: Path, relative: str) -> Path:
    _require(
        isinstance(relative, str) and relative and not Path(relative).is_absolute(),
        "expected repository-relative authority path",
    )
    result = (root / relative).resolve()
    _require(result.is_relative_to(root.resolve()), "authority path escapes repository")
    return result


@lru_cache(maxsize=8)
def _parse_yaml(data: bytes) -> Any:
    """Cache parsing by exact bytes; every boundary still re-reads authority."""
    return yaml.load(data, Loader=yaml.CSafeLoader)


def _read_yaml(path: Path) -> dict[str, Any]:
    value = _parse_yaml(path.read_bytes())
    _require(isinstance(value, dict), f"{path.name}: expected mapping")
    return value


def _validate_origin(root: Path, origin: Mapping[str, Any], documents: dict[Path, Any]) -> None:
    """Verify a raw row, never its whole-file formatting or unrelated rows."""
    kind = origin.get("kind")
    _require(kind in {"source_inventory", "built_vocabulary"}, "unknown origin kind")
    logical = origin["path"]
    if kind == "source_inventory":
        _require(logical.startswith("data/lexicon/source-inventory/"), "invalid inventory path")
        registry_path = "registry/lexicon/source-inventory/" + logical.removeprefix("data/lexicon/source-inventory/")
        path = _path(root, registry_path)
        if not path.is_file():
            path = _path(root, logical)
        if path not in documents:
            documents[path] = _read_yaml(path)
        match = re.fullmatch(r"sources\[(\d+)\]\.headwords\[(\d+)\]", origin["structural_locator_one_based"])
        _require(match and all(int(x) > 0 for x in match.groups()), "invalid one-based structural locator")
        source_i, row_i = (int(x) - 1 for x in match.groups())
        source = documents[path]["sources"][source_i]
        raw = source["headwords"][row_i]
        _require(
            raw.get("lemma") == origin["lemma"] and raw.get("locator") == origin["source_locator"],
            "changed/moved inventory origin",
        )
        for field, raw_field in (
            ("source_id", "id"),
            ("source_family", "source_family"),
            ("extraction_mode", "extraction_mode"),
            ("source_title", "title"),
        ):
            _require(source.get(raw_field) == origin[field], f"changed inventory {field}")
        for field, path_field in (("key", "path"), ("historical_key", "historical_path")):
            expected = source_inventory_key(
                lemma=origin["lemma"], inventory_path=origin[path_field], locator=origin["source_locator"]
            )
            _require(origin[field] == expected, "inventory identity/key mismatch")
    else:
        path = _path(root, logical)
        _require(
            logical == f"curriculum/l2-uk-en/{origin['track']}/{origin['module_slug']}/vocabulary.yaml",
            "built origin path mismatch",
        )
        if path not in documents:
            documents[path] = _parse_yaml(path.read_bytes())
        index = origin["index_zero_based"]
        _require(type(index) is int and index >= 0 and origin["row_one_based"] == index + 1, "invalid built row index")
        raw = documents[path][index]
        _require(raw.get("lemma") == origin["lemma"], "changed/moved built origin")
    _require(canonical_sha256(raw) == origin["row_sha256"], "changed/moved raw origin digest")


def _validate_release_review(
    _root: Path, row: Mapping[str, Any], hold_digest: str, bindings: Sequence[Mapping[str, Any]]
) -> None:
    """Adapt existing code-review receipt + recorder verdict; no online trust claim."""
    row_digest = canonical_sha256(row)
    matches = [
        b for b in bindings if b.get("row_sha256") == row_digest and b.get("superseded_row_sha256") == hold_digest
    ]
    _require(len(matches) == 1, "missing/competing release review row binding")
    binding = matches[0]
    receipt_bytes = binding["receipt_json"].encode("utf-8")
    body_bytes = binding["verdict_body"].encode("utf-8")
    _require(hashlib.sha256(receipt_bytes).hexdigest() == binding["receipt_sha256"], "release receipt digest mismatch")
    _require(hashlib.sha256(body_bytes).hexdigest() == binding["verdict_sha256"], "release verdict digest mismatch")
    receipt = json.loads(receipt_bytes)
    _require(
        receipt.get("schema_version") == "code-review-receipt.v1"
        and receipt.get("exit_code") == 0
        and receipt.get("final_disposition") == "clean"
        and not receipt.get("error"),
        "release requires completed clean code-review receipt",
    )
    author, reviewer, target = receipt["author"], receipt["reviewer"], receipt["target"]
    for identity in (author, reviewer):
        _require(
            all(isinstance(identity.get(k), str) and identity[k].strip() for k in ("model", "family", "harness")),
            "missing release native model/family/harness provenance",
        )
    _require(author["family"] != reviewer["family"], "release self-review refused")
    body = body_bytes.decode("utf-8")
    marker = parse_marker(body)
    _require(
        marker and marker.get("verdict") == "APPROVED" and marker.get("review_mode", "cross_family") == "cross_family",
        "release requires recorder cross-family APPROVED verdict",
    )
    _require(
        marker["sha"] == target["head_sha"]
        and marker["model"] == reviewer["model"]
        and marker["family"] == reviewer["family"],
        "release native head/model/family mismatch",
    )
    _require(
        f"release-row-sha256: {row_digest}" in body and f"superseded-hold-row-sha256: {hold_digest}" in body,
        "release verdict missing exact row digest binding",
    )


@dataclass(frozen=True)
class Dispositions:
    root: Path
    ledger: Mapping[str, Any]
    preservation: Mapping[str, Any]
    active_holds: tuple[Mapping[str, Any], ...]
    released_ids: frozenset[str]

    def holds_source_key(self, key: str) -> bool:
        return any(
            r["origin"]["kind"] == "source_inventory" and key in (r["origin"]["key"], r["origin"]["historical_key"])
            for r in self.active_holds
        )

    def guard_plan_rows(self, rows: Sequence[Mapping[str, Any]]) -> None:
        for row in rows:
            key = row.get("source_inventory_key") or (row.get("source_inventory") or {}).get("key")
            _require(not self.holds_source_key(str(key)), "active hold defeats saved plan/approval")
            entry = row.get("manifest_entry")
            if isinstance(entry, Mapping):
                self.guard_entry(entry)

    def withhold_built_row(self, module: Mapping[str, Any], index: int, raw: Mapping[str, Any]) -> bool:
        for row in self.active_holds:
            origin = row["origin"]
            if origin["kind"] != "built_vocabulary" or (module["track"], module["slug"]) != (
                origin["track"],
                origin["module_slug"],
            ):
                continue
            if index == origin["index_zero_based"]:
                _require(canonical_sha256(raw) == origin["row_sha256"], "changed/moved built row at ingestion")
                return True
            _require(raw.get("lemma") != origin["lemma"], "moved/duplicated built origin")
        return False

    def guard_built_record(self, module: Mapping[str, Any], record: Mapping[str, Any]) -> None:
        origin = record.get("_disposition_origin")
        if origin is None:
            # Old callers may supply projected records directly. Their public
            # course usage and normalization names remain checked below.
            self.guard_entry({**record, "course_usage": [{"track": module["track"], "slug": module["slug"]}]})
            return
        for row in self.active_holds:
            held = row["origin"]
            if held["kind"] == "built_vocabulary" and (
                origin["track"],
                origin["module_slug"],
                origin["index_zero_based"],
            ) == (held["track"], held["module_slug"], held["index_zero_based"]):
                raise DispositionError("held raw origin survived normalization/merging")

    def guard_entry(self, entry: Mapping[str, Any]) -> None:
        """Recognize exact origins even under normalization and slug collision.

        Same-head contributions with disjoint explicit provenance survive. A
        mixed payload cannot be unmerged here and must be refused by the caller.
        """
        provenance = entry.get("source_provenance") or []
        usages = entry.get("course_usage") or []
        _require(isinstance(provenance, list) and isinstance(usages, list), "invalid contribution provenance")
        for row in self.active_holds:
            origin, projection = row["origin"], row["projection"]
            if origin["kind"] == "source_inventory":
                for item in provenance:
                    same_source = (
                        item.get("source_id") == origin["source_id"]
                        and item.get("source_locator") == origin["source_locator"]
                    )
                    explicit_key = item.get("source_inventory_key") or item.get("key")
                    origin_names = [entry.get("lemma"), *entry.get("slug_variants", [])]
                    origin_names += [n.get("source_lemma") for n in entry.get("atlas_normalizations", [])]
                    same_head = origin["lemma"] in origin_names or entry.get("url_slug") == projection["url_slug"]
                    if (same_source and same_head) or explicit_key in (origin["key"], origin["historical_key"]):
                        raise DispositionError("active held inventory contribution present (or retargeted)")
            else:
                for usage in usages:
                    if (usage.get("track"), usage.get("slug")) == (origin["track"], origin["module_slug"]):
                        names = [entry.get("lemma"), *entry.get("slug_variants", [])]
                        names += [n.get("source_lemma") for n in entry.get("atlas_normalizations", [])]
                        _require(origin["lemma"] not in names, "active held built contribution present")
            same_projection = (
                entry.get("lemma") == row["lemma"]
                or entry.get("url_slug") == projection["url_slug"]
                or row["lemma"] in entry.get("slug_variants", [])
            )
            if same_projection:
                _require(canonical_sha256(entry) != projection["payload_sha256"], "preserved held projection present")
                _require(
                    provenance or usages or entry.get("primary_source") in {"surzhyk_to_avoid", "heritage_status_seed"},
                    "inseparable/unknown same-head contribution",
                )
                if origin["kind"] == "source_inventory":
                    for item in provenance:
                        _require(
                            not (
                                item.get("inventory_path") in (origin["path"], origin["historical_path"])
                                and item.get("source_locator") == origin["source_locator"]
                            ),
                            "held inventory contribution missing/changed source ID",
                        )

    def validate_manifest(self, manifest: Mapping[str, Any]) -> None:
        entries = manifest.get("entries")
        _require(
            isinstance(entries, list) and all(isinstance(e, dict) for e in entries), "manifest entries must be mappings"
        )
        for entry in entries:
            self.guard_entry(entry)
        validate_route_references(
            manifest, {r["projection"]["url_slug"] for r in self.active_holds}, {r["lemma"] for r in self.active_holds}
        )


def validate_route_references(manifest: Mapping[str, Any], slugs: set[str], lemmas: set[str]) -> None:
    """Inspect explicit route carriers, leaving unlinked cited text opaque."""
    present_slugs = {e.get("url_slug") for e in manifest["entries"]}
    present_lemmas = {e.get("lemma") for e in manifest["entries"]}
    blocked_slugs, blocked_lemmas = slugs - present_slugs, lemmas - present_lemmas

    def walk(value: Any, carrier: str = "") -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if key in {"related_slug", "target_slug", "alias_target", "canonical_slug"} or (
                    carrier in {"form_of", "aliases", "link_catalog"} and key in {"url_slug", "slug", "target", "lemma"}
                ):
                    _require(
                        not isinstance(child, str) or child not in blocked_slugs | blocked_lemmas,
                        f"unresolved route-bearing reference: {key}",
                    )
                walk(child, key if key in {"form_of", "aliases", "link_catalog"} else carrier)
        elif isinstance(value, list):
            for child in value:
                walk(child, carrier)

    walk(manifest)


def load_dispositions(root: Path | None = None) -> Dispositions:
    """Read mandatory canonical pair and resolve an explicit, nonforking graph."""
    root = root or PROJECT_ROOT
    try:
        return _load_dispositions(root)
    except (OSError, ValueError, TypeError, KeyError, IndexError, yaml.YAMLError) as exc:
        raise DispositionError(f"disposition authority invalid: {exc}") from exc


def _load_dispositions(root: Path) -> Dispositions:
    ledger = copy.deepcopy(_read_yaml(root / LEDGER_PATH))
    _require(
        ledger.get("kind") == "atlas_published_record_dispositions"
        and type(ledger.get("version")) is int
        and ledger["version"] == 1,
        "invalid disposition kind/version",
    )
    preservation_ref = ledger["preservation"]
    _require(preservation_ref["path"] == PRESERVATION_PATH.as_posix(), "noncanonical preservation path")
    data = _path(root, preservation_ref["path"]).read_bytes()
    _require(hashlib.sha256(data).hexdigest() == preservation_ref["sha256"], "preservation file digest mismatch")
    preservation = json.loads(data)
    _require(
        preservation.get("kind") == "atlas_published_record_preservation"
        and type(preservation.get("version")) is int
        and preservation["version"] == 1
        and preservation["batch_id"] == ledger["batch_id"],
        "invalid preservation kind/version/batch",
    )
    records = preservation["records"]
    _require(
        isinstance(records, list) and tuple(r["row_id"] for r in records) == ROW_IDS,
        "preservation must cover all six fixed IDs",
    )
    positions = [r["original_index_zero_based"] for r in records]
    _require(
        all(type(i) is int and i >= 0 for i in positions) and positions == sorted(set(positions)),
        "invalid preserved positions",
    )
    for record in records:
        _require(canonical_sha256(record["entry"]) == record["payload_sha256"], "preserved payload digest mismatch")
    order = preservation["original_top_level_order"]
    _require(
        len(order) == len(set(order)) and set(order) == set(preservation["original_manifest_envelope"]) | {"entries"},
        "preserved envelope/order mismatch",
    )
    tx = preservation["transaction"]
    _require(
        all(_SHA256.fullmatch(tx[k]) for k in ("before_sha256", "after_sha256", "ordered_survivor_sha256")),
        "invalid transaction digests",
    )
    _require(
        tx["before_entries"] - tx["after_entries"] == 6 and positions[-1] < tx["before_entries"],
        "invalid transaction denominator",
    )
    rows = ledger["decisions"]
    _require(isinstance(rows, list), "dispositions must be a list")
    by_id = {r["row_id"]: r for r in rows}
    _require(len(by_id) == len(rows), "duplicate disposition row IDs")
    holds, released = [], set()
    documents: dict[Path, Any] = {}
    used_ids: set[str] = set()
    for record in records:
        row_id = record["row_id"]
        base = by_id.get(row_id)
        _require(
            base and base.get("decision") == "needs_more_evidence" and base.get("effect") == "withhold_projection",
            "missing/omitted original hold",
        )
        _require(
            base["lemma"] == record["entry"]["lemma"]
            and base["projection"]
            == {
                "url_slug": record["entry"]["url_slug"],
                "index_zero_based": record["original_index_zero_based"],
                "payload_sha256": record["payload_sha256"],
            },
            "hold/preservation projection mismatch",
        )
        _validate_origin(root, base["origin"], documents)
        _require(
            base["origin"]["lemma"] == base["lemma"] and base.get("evidence_refs") and base.get("rationale"),
            "missing hold evidence/identity",
        )
        predecessors = base["supersedes"]
        _require(
            isinstance(predecessors, list)
            and len(predecessors) == (1 if base["origin"]["kind"] == "source_inventory" else 0),
            "invalid hold predecessors",
        )
        for reference in predecessors:
            path = _path(root, reference["ledger_path"])
            if path not in documents:
                documents[path] = _read_yaml(path)
            old = documents[path]
            matches = [
                r
                for r in old["decisions"]
                if (r.get("source_inventory") or {}).get("key") == reference["source_key"]
                and r.get("decision") == reference["decision"]
            ]
            _require(
                old["batch_id"] == reference["batch_id"]
                and len(matches) == 1
                and canonical_sha256(matches[0]) == reference["row_sha256"]
                and reference["source_key"] == base["origin"]["key"]
                and reference["decision"] == "approve_for_publish",
                "missing/changed predecessor row",
            )
        tip = base
        seen: set[str] = set()
        while True:
            _require(tip["row_id"] not in seen, "disposition cycle")
            seen.add(tip["row_id"])
            used_ids.add(tip["row_id"])
            digest = canonical_sha256(tip)
            children = [r for r in rows if any(ref.get("row_id") == tip["row_id"] for ref in r.get("supersedes", []))]
            _require(len(children) <= 1, "disposition fork/competing tips")
            if not children:
                break
            child = children[0]
            _require(
                child.get("decision") == "approve_for_publish"
                and child.get("effect") == "restore_projection"
                and tip["decision"] == "needs_more_evidence",
                "invalid release/cyclic supersession",
            )
            _require(
                child["origin"] == base["origin"]
                and child["projection"] == base["projection"]
                and child["lemma"] == base["lemma"],
                "release retargets origin/projection",
            )
            _require(
                child["supersedes"]
                == [
                    {
                        "ledger_path": LEDGER_PATH.as_posix(),
                        "batch_id": ledger["batch_id"],
                        "row_id": tip["row_id"],
                        "decision": tip["decision"],
                        "row_sha256": digest,
                    }
                ],
                "release supersession identity mismatch",
            )
            _validate_release_review(root, child, digest, ledger.get("release_reviews", []))
            tip = child
        if tip["decision"] == "needs_more_evidence":
            holds.append(base)
        else:
            released.add(row_id)
    _require(used_ids == set(by_id), "orphan/missing/cyclic disposition chain")
    return Dispositions(root, ledger, preservation, tuple(holds), frozenset(released))
