#!/usr/bin/env python3
"""Build a text-free manifest of Phase 3 units exposed in retired cycles."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
import tempfile
from pathlib import Path
from typing import Any

PRIVATE_DIR_MODE = 0o700
PRIVATE_FILE_MODE = 0o600
IDENTITY_FIELDS = {"unit_id", "unit_sha256"}


class PriorExposureError(ValueError):
    """A retired-cycle exposure source is malformed or unsafe."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise PriorExposureError(message)


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _regular_private(path: Path, label: str) -> None:
    try:
        result = path.lstat()
    except OSError as exc:
        raise PriorExposureError(f"missing {label}: {path}") from exc
    require(
        stat.S_ISREG(result.st_mode) and not path.is_symlink(),
        f"{label} must be a regular file",
    )
    require(
        stat.S_IMODE(result.st_mode) == PRIVATE_FILE_MODE,
        f"{label} permissions must be 0600",
    )


def _identity(value: Any, label: str) -> tuple[str, str]:
    require(isinstance(value, dict), f"{label} must be an object")
    require(set(value) >= IDENTITY_FIELDS, f"{label} lacks a unit identity")
    unit_id = value["unit_id"]
    unit_sha256 = value["unit_sha256"]
    require(isinstance(unit_id, str) and unit_id, f"{label} unit_id is invalid")
    require(
        isinstance(unit_sha256, str)
        and len(unit_sha256) == 64
        and all(char in "0123456789abcdef" for char in unit_sha256),
        f"{label} unit_sha256 is invalid",
    )
    return unit_id, unit_sha256


def _load_identity_list(path: Path) -> set[tuple[str, str]]:
    _regular_private(path, "identity list")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PriorExposureError(f"cannot read identity list: {path}") from exc
    require(isinstance(value, list), "identity list must be an array")
    identities = {_identity(item, f"{path.name} item") for item in value}
    require(len(identities) == len(value), f"duplicate identity inside {path.name}")
    return identities


def _load_packet_dir(path: Path) -> set[tuple[str, str]]:
    require(path.is_dir() and not path.is_symlink(), f"packet directory is invalid: {path}")
    require(
        stat.S_IMODE(path.stat().st_mode) == PRIVATE_DIR_MODE,
        f"packet directory permissions must be 0700: {path}",
    )
    packets = sorted(path.glob("packet-*.json"))
    require(packets, f"packet directory is empty: {path}")
    identities: set[tuple[str, str]] = set()
    for packet in packets:
        _regular_private(packet, "retired packet")
        try:
            value = json.loads(packet.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise PriorExposureError(f"cannot read retired packet: {packet}") from exc
        require(isinstance(value, dict), f"retired packet is not an object: {packet}")
        rows = value.get("rows")
        require(isinstance(rows, list) and rows, f"retired packet rows missing: {packet}")
        require(value.get("row_count") == len(rows), f"retired packet count drift: {packet}")
        packet_identities = {_identity(row, f"{packet.name} row") for row in rows}
        require(
            len(packet_identities) == len(rows),
            f"duplicate identity inside retired packet: {packet}",
        )
        require(
            not identities.intersection(packet_identities),
            f"duplicate identity across retired packets: {packet}",
        )
        identities.update(packet_identities)
    return identities


def _atomic_write(path: Path, payload: bytes) -> None:
    require(not path.is_symlink(), "output may not be a symlink")
    path.parent.mkdir(parents=True, exist_ok=True, mode=PRIVATE_DIR_MODE)
    require(not path.parent.is_symlink(), "output directory may not be a symlink")
    os.chmod(path.parent, PRIVATE_DIR_MODE)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            os.fchmod(handle.fileno(), PRIVATE_FILE_MODE)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        os.chmod(path, PRIVATE_FILE_MODE)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def build(
    *, identity_lists: list[Path], packet_dirs: list[Path], output: Path
) -> dict[str, Any]:
    require(identity_lists or packet_dirs, "at least one exposure source is required")
    output_resolved = output.resolve(strict=False)
    for path in identity_lists:
        require(
            output_resolved != path.resolve(),
            "output may not overwrite an exposure source",
        )
    for path in packet_dirs:
        try:
            output_resolved.relative_to(path.resolve())
        except ValueError:
            pass
        else:
            raise PriorExposureError("output may not be inside an exposure source")
    sources: list[dict[str, Any]] = []
    identities: set[tuple[str, str]] = set()
    for path in identity_lists:
        source_identities = _load_identity_list(path)
        identities.update(source_identities)
        sources.append(
            {
                "source_type": "identity_list",
                "raw_sha256": sha256_file(path),
                "identity_count": len(source_identities),
            }
        )
    for path in packet_dirs:
        source_identities = _load_packet_dir(path)
        identities.update(source_identities)
        packet_hashes = [sha256_file(item) for item in sorted(path.glob("packet-*.json"))]
        sources.append(
            {
                "source_type": "retired_packet_directory",
                "packet_count": len(packet_hashes),
                "ordered_packet_sha256s_sha256": hashlib.sha256(
                    canonical_bytes(packet_hashes)
                ).hexdigest(),
                "identity_count": len(source_identities),
            }
        )
    ordered = [
        {"unit_id": unit_id, "unit_sha256": unit_sha256}
        for unit_id, unit_sha256 in sorted(identities)
    ]
    payload = b"".join(canonical_bytes(row) for row in ordered)
    _atomic_write(output, payload)
    return {
        "schema_version": "phase3_prior_exposure_manifest_receipt_v1",
        "text_free": True,
        "source_bindings": sources,
        "unique_identity_count": len(ordered),
        "manifest_sha256": hashlib.sha256(payload).hexdigest(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--identity-list", action="append", default=[], type=Path)
    parser.add_argument("--packet-dir", action="append", default=[], type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        receipt = build(
            identity_lists=args.identity_list,
            packet_dirs=args.packet_dir,
            output=args.output,
        )
    except (OSError, PriorExposureError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
