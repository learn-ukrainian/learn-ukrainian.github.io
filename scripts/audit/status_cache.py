"""
Status cache access layer — single source of truth for reading status JSON files.

ALL consumers of status/{slug}.json must use read_status() instead of direct json.loads.
Provides built-in staleness detection using relative mtime comparison (Solution B from #561).

Staleness logic:
    - Fresh: status file mtime >= max(source file mtimes)
    - Stale: any source file is newer than the status file
    - This works correctly after git clone (all mtimes reset to 'now')
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class StatusResult:
    """Wrapper around status JSON with freshness metadata.

    Consumers check .is_fresh before trusting .status as authoritative.
    Stale results still contain data (useful for display) but should not
    drive pass/fail decisions.
    """

    data: dict
    is_fresh: bool
    stale_sources: list[str] = field(default_factory=list)

    @property
    def status(self) -> str:
        """Overall pass/fail status string."""
        return self.data.get("overall", {}).get("status", "unknown")

    @property
    def gates(self) -> dict:
        """Gate-level detail dict."""
        return self.data.get("gates", {})

    @property
    def has_issues(self) -> bool:
        """True if the module has known failures (fresh and failing)."""
        return self.is_fresh and self.status == "fail"

    @property
    def module(self) -> str:
        """Module slug."""
        return self.data.get("module", "")

    @property
    def level(self) -> str:
        """Level code."""
        return self.data.get("level", "")

    def __bool__(self) -> bool:
        """True if data was loaded (file existed)."""
        return bool(self.data)

    def __repr__(self) -> str:
        freshness = "fresh" if self.is_fresh else f"stale({','.join(self.stale_sources)})"
        return f"StatusResult({self.module}@{self.level}, {self.status}, {freshness})"


def get_source_paths(track_dir: Path, slug: str) -> dict[str, Optional[Path]]:
    """Resolve all source file paths for a module.

    Args:
        track_dir: Path to the track directory (e.g., curriculum/l2-uk-en/a1)
        slug: Bare module slug (e.g., 'the-cyrillic-code-i')

    Returns:
        Dict with keys 'md', 'meta', 'activities', 'vocabulary', 'plan'.
        Values are Path objects (may not exist on disk).
    """
    plans_dir = track_dir.parent / "plans" / track_dir.name

    # Find the md file — could have a numeric prefix
    md_path = None
    direct = track_dir / f"{slug}.md"
    if direct.exists():
        md_path = direct
    else:
        matches = list(track_dir.glob(f"*-{slug}.md"))
        if matches:
            md_path = matches[0]
        else:
            md_path = direct  # Return expected path even if missing

    return {
        "md": md_path,
        "meta": track_dir / "meta" / f"{slug}.yaml",
        "activities": track_dir / "activities" / f"{slug}.yaml",
        "vocabulary": track_dir / "vocabulary" / f"{slug}.yaml",
        "plan": plans_dir / f"{slug}.yaml",
    }


def read_status(
    status_path: Path,
    source_paths: Optional[dict[str, Optional[Path]]] = None,
) -> Optional[StatusResult]:
    """Single access point for status cache. ALL consumers should use this.

    Freshness is determined by relative mtime comparison (Solution B from #561):
    the status file's own mtime must be >= every source file's mtime.
    This is stable across git clone/checkout because git resets all mtimes to 'now'.

    Args:
        status_path: Path to the status JSON file.
        source_paths: Optional dict of source file paths to check freshness against.
                      Keys: 'md', 'meta', 'activities', 'vocabulary', 'plan'.
                      If None, freshness check is skipped (result marked as fresh).

    Returns:
        StatusResult with is_fresh flag, or None if the status file doesn't exist.
    """
    if not status_path.exists():
        return None

    try:
        data = json.loads(status_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None

    # No source paths provided — skip freshness check
    if source_paths is None:
        return StatusResult(data=data, is_fresh=True, stale_sources=[])

    # Relative mtime comparison: status file must be newer than all source files
    try:
        status_mtime = status_path.stat().st_mtime
    except OSError:
        return StatusResult(data=data, is_fresh=False, stale_sources=["status_unreadable"])

    stale = []
    for key, path in source_paths.items():
        if path is None:
            continue
        if not path.exists():
            continue
        try:
            if path.stat().st_mtime > status_mtime:
                stale.append(key)
        except OSError:
            continue  # Can't stat source — don't mark as stale

    return StatusResult(data=data, is_fresh=len(stale) == 0, stale_sources=stale)
