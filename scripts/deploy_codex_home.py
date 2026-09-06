"""Deploy bounded Codex assets to an explicit home, with private recovery copies."""

from __future__ import annotations

import argparse
import contextlib
import copy
import json
import os
import re
import stat
import tempfile
import tomllib
import uuid
from pathlib import Path


class DeployError(Exception):
    """Sanitized deployment error."""


EXPECTED = {
    "model": "gpt-6-astra",
    "agents": {
        "default_subagent_model": "gpt-6-astra",
        "default_subagent_reasoning_effort": "low",
    },
}


def safe_path(path: Path) -> Path:
    if ".." in path.parts:
        raise DeployError("path traversal refused")
    path = path.absolute()
    for part in [*reversed(path.parents), path]:
        if part.is_symlink():
            raise DeployError("symlink path refused")
    return path


def parse(data: bytes) -> dict:
    try:
        return tomllib.loads(data.decode("utf-8"))
    except (UnicodeError, tomllib.TOMLDecodeError):
        raise DeployError("invalid TOML; repair source or target config") from None


def merge_config(data: bytes) -> bytes:
    original = parse(data)
    if not isinstance(original.get("agents", {}), dict):
        raise DeployError("unsupported agents shape; use a standard [agents] table")
    expected = copy.deepcopy(original)
    expected["model"] = EXPECTED["model"]
    expected.setdefault("agents", {}).update(EXPECTED["agents"])
    if original == expected:
        return data
    lines = data.decode().splitlines(keepends=True)
    section, found, insert_at = "", set(), None
    assignment = re.compile(
        r"""^(\s*)(model|default_subagent_model|default_subagent_reasoning_effort)(\s*=\s*)("(?:[^"\\\r\n]|\\.)*"|'[^'\r\n]*')([ \t]*(?:\#.*)?)(\r?\n)?$"""
    )
    for index, line in enumerate(lines):
        if line.lstrip().startswith("["):
            section = "agents" if re.fullmatch(r"\s*\[agents\]\s*(?:#.*)?", line.strip()) else "other"
            if section == "agents":
                insert_at = index + 1
        match = assignment.fullmatch(line)
        if not match:
            continue
        key = match[2]
        if (section == "" and key == "model") or (section == "agents" and key in EXPECTED["agents"]):
            value = EXPECTED["model"] if section == "" else EXPECTED["agents"][key]
            lines[index] = match[1] + key + match[3] + json.dumps(value) + match[5] + (match[6] or "")
            found.add((section, key))
    if "model" in original and ("", "model") not in found:
        raise DeployError("unsupported model assignment; use a single-line root string")
    missing = []
    for key, value in EXPECTED["agents"].items():
        if ("agents", key) not in found:
            if key in original.get("agents", {}):
                raise DeployError("unsupported agents assignment; use standard [agents] single-line strings")
            missing.append(f"{key} = {json.dumps(value)}\n")
    if missing:
        if insert_at is not None:
            if not lines[insert_at - 1].endswith("\n"):
                lines[insert_at - 1] += "\n"
            lines[insert_at:insert_at] = missing
        else:
            lines += ["\n[agents]\n", *missing]
    if ("", "model") not in found:
        lines.insert(0, f"model = {json.dumps(EXPECTED['model'])}\n")
    merged = "".join(lines).encode()
    try:
        valid = parse(merged) == expected
    except DeployError:
        valid = False
    if not valid:
        raise DeployError("unsupported config shape; use root model and a standard [agents] table")
    return merged


def source_assets(root: Path) -> dict[str, bytes]:
    agents = safe_path(root / "agents")
    if not agents.is_dir():
        raise DeployError("source agents directory missing")
    profiles = sorted(agents.glob("*.toml"))
    if not profiles:
        raise DeployError("source profiles missing")
    assets = {}
    for path in [root / "AGENTS.md", root / "config.toml", *profiles]:
        safe_path(path)
        if not path.is_file():
            raise DeployError("source asset missing or not a regular file")
        data = path.read_bytes()
        if path.suffix == ".toml":
            parsed = parse(data)
            if path == root / "config.toml":
                if parsed != EXPECTED:
                    raise DeployError("source config must contain exactly the three approved settings")
            else:
                if parsed.get("model") != EXPECTED["model"]:
                    raise DeployError("source profile must use the approved model")
                if parsed.get("name") != path.stem:
                    raise DeployError("source profile name must match its filename")
                for field in ("description", "developer_instructions"):
                    if not isinstance(parsed.get(field), str) or not parsed[field].strip():
                        raise DeployError(f"source profile requires nonempty {field}")
                if parsed.get("model_reasoning_effort") not in ("low", "medium", "high", "xhigh", "max", "ultra"):
                    raise DeployError("source profile requires a recognized explicit reasoning effort")
                if parsed.get("sandbox_mode") not in ("read-only", "workspace-write"):
                    raise DeployError("source profile requires read-only or workspace-write sandbox mode")
        elif not data.strip():
            raise DeployError("source AGENTS.md is empty")
        assets[path.relative_to(root).as_posix()] = data
    return assets


def atomic_write(path: Path, data: bytes, mode: int = 0o600) -> None:
    safe_path(path)
    fd, temporary = tempfile.mkstemp(prefix=".deploy-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            os.fchmod(stream.fileno(), mode)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        safe_path(path)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def deploy(source: Path, home: Path, *, dry_run: bool = False, check: bool = False) -> int:
    home = safe_path(home)
    assets = source_assets(safe_path(source))
    changes = []
    for relative, data in assets.items():
        target = safe_path(home / relative)
        for parent in target.parents:
            if parent.exists() and not parent.is_dir():
                raise DeployError("target parent is not a directory")
        if target.exists() and not target.is_file():
            raise DeployError("target asset is not a regular file")
        old = target.read_bytes() if target.exists() else None
        mode = stat.S_IMODE(target.stat().st_mode) if old is not None else 0o600
        if relative == "config.toml":
            data = merge_config(old or b"")
        if old != data:
            changes.append((relative, data, old, mode))
    backups = safe_path(home / ".deploy-backups")
    if backups.exists() and (not backups.is_dir() or stat.S_IMODE(backups.stat().st_mode) & 0o077):
        raise DeployError("backup directory must be private (mode 0700)")
    if dry_run or check or not changes:
        for relative, *_ in changes:
            print(f"{relative}: drift")
        if not changes:
            print("status: matched")
        return 1 if check and changes else 0
    home.mkdir(parents=True, exist_ok=True, mode=0o700)
    backups.mkdir(mode=0o700, exist_ok=True)
    run = backups / uuid.uuid4().hex
    run.mkdir(mode=0o700)
    receipt = {
        "status": "preparing",
        "changes": [
            {
                "path": rel,
                "backup": rel if old is not None else None,
                "original_mode": mode if old is not None else None,
                "status": "pending",
            }
            for rel, _, old, mode in changes
        ],
    }

    def save_receipt():
        atomic_write(run / "receipt.json", (json.dumps(receipt, indent=2) + "\n").encode())

    save_receipt()
    try:
        for relative, _, old, _ in changes:
            if old is not None:
                backup = run / relative
                backup.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                atomic_write(backup, old)
        receipt["status"] = "applying"
        save_receipt()
        for entry, (relative, data, old, mode) in zip(receipt["changes"], changes, strict=True):
            target = safe_path(home / relative)
            if (target.read_bytes() if target.exists() else None) != old:
                raise DeployError("target changed during deployment")
            target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            atomic_write(target, data, mode)
            entry["status"] = "applied"
            save_receipt()
            print(f"{relative}: changed")
        receipt["status"] = "complete"
        save_receipt()
    except (OSError, DeployError):
        receipt["status"] = "partial_failure"
        with contextlib.suppress(OSError, DeployError):
            save_receipt()
        raise DeployError(
            "deployment failed; inspect .deploy-backups originals and receipt; changes may be partial"
        ) from None
    print(f".deploy-backups/{run.name}/receipt.json: saved")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex-home", type=Path, required=True)
    parser.add_argument(
        "--source-root", type=Path, default=Path(__file__).resolve().parents[1] / "agents_extensions/codex-home"
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        return deploy(args.source_root, args.codex_home, dry_run=args.dry_run, check=args.check)
    except DeployError as error:
        print(f"status: error: {error}")
        return 2
    except OSError:
        print("status: error: filesystem operation failed; check access and .deploy-backups receipts")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
