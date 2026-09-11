"""Retire byte-verified redundant Codex skill deploy copies; preserve unknown content."""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from reap_agent_mirrors import reap_entry


def legacy_files(root: Path) -> list[Path]:
    legacy = root / ".codex/skills"
    if legacy.is_symlink() or (root / ".codex").is_symlink():
        raise ValueError("Legacy Codex skill path must not be a symlink")
    if not legacy.exists():
        return []
    if not legacy.is_dir():
        raise ValueError("Legacy Codex skill path must be a directory")
    files = []
    for path in sorted(legacy.rglob("*")):
        if path.is_symlink():
            raise ValueError("Legacy Codex skills contain a symlink; preserve and reconcile")
        if path.is_dir():
            relative = path.relative_to(legacy)
            source = root / "agents_extensions/shared/skills" / relative
            if not source.is_dir() or source.is_symlink():
                raise ValueError("Unknown legacy Codex skill directory; preserve and reconcile")
            continue
        if not path.is_file():
            raise ValueError("Legacy Codex skills contain unsupported content")
        relative = path.relative_to(legacy)
        source = root / "agents_extensions/shared/skills" / relative
        payload = path.read_bytes()
        source_path = f"agents_extensions/shared/skills/{relative.as_posix()}"
        tracked = subprocess.run(
            ["git", "ls-files", "--error-unmatch", "--", source_path],
            cwd=root, capture_output=True, check=False,
        )
        if tracked.returncode == 0 and source.is_file() and not source.is_symlink() and payload == source.read_bytes():
            files.append(path)
            continue
        # After merge HEAD already contains new source bytes. Verify an older
        # deployment against regular-file blob IDs in this exact path's history.
        digest = subprocess.run(
            ["git", "hash-object", "--stdin"], input=payload,
            cwd=root, capture_output=True, check=False,
        )
        history = subprocess.run(
            ["git", "log", "--format=", "--raw", "--no-abbrev", "--", source_path],
            cwd=root, capture_output=True, check=False,
        )
        blob = digest.stdout.strip()
        verified = False
        if digest.returncode == 0 and history.returncode == 0:
            for line in history.stdout.splitlines():
                fields = line.split(b"\t", 1)[0].split()
                if len(fields) != 5 or not fields[0].startswith(b":"):
                    continue
                old_mode, new_mode, old_blob, new_blob, _ = fields
                verified |= old_mode[1:] in (b"100644", b"100755") and old_blob == blob
                verified |= new_mode in (b"100644", b"100755") and new_blob == blob
        if verified:
            files.append(path)
            continue
        raise ValueError(f"Unverified legacy Codex skill content: {relative}; preserve and reconcile")
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("verify", "apply"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    try:
        files = legacy_files(root)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1
    if args.mode == "apply":
        # Reuse the descriptor-bound reaper: a swapped parent can never redirect
        # deletion outside the checkout. Never recursively remove a directory.
        legacy = root / ".codex/skills"
        directories = sorted(
            (p for p in legacy.rglob("*") if p.is_dir()),
            key=lambda p: len(p.parts), reverse=True,
        ) if legacy.is_dir() else []
        entries = [("f", p) for p in files] + [("d", p) for p in directories]
        if legacy.is_dir():
            entries.append(("d", legacy))
        for kind, path in entries:
            removed, _ = reap_entry(str(root), kind, path.relative_to(root).as_posix())
            if not removed:
                print("ERROR: legacy Codex skill tree changed during retirement; preserve and reconcile")
                return 1
        print(f"Retired {len(files)} verified legacy Codex skill deploy files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
