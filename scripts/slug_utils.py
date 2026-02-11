"""
Slug utilities — single source of truth for slug stripping and path construction.

All scripts should import from here instead of using inline re.sub or stem[3:].

Bare slug = filename stem with leading numeric prefix removed:
    "01-the-cyrillic-code-i"  → "the-cyrillic-code-i"
    "140-syntez-viyna"        → "syntez-viyna"
    "knyahynia-olha"          → "knyahynia-olha"  (no-op)
    "01-the-cyrillic-code-i.md" → "the-cyrillic-code-i"  (extension stripped)
"""

import re
from pathlib import Path

_NUMERIC_PREFIX_RE = re.compile(r"^\d+-")


def to_bare_slug(name: str) -> str:
    """Strip leading numeric prefix and extension from a filename or slug.

    Examples:
        "01-the-cyrillic-code-i.md"  → "the-cyrillic-code-i"
        "140-syntez-viyna.yaml"      → "syntez-viyna"
        "01-the-cyrillic-code-i"     → "the-cyrillic-code-i"
        "knyahynia-olha"             → "knyahynia-olha"
        "knyahynia-olha.yaml"        → "knyahynia-olha"
    """
    # Strip extension if present
    stem = Path(name).stem if "." in name else name
    return _NUMERIC_PREFIX_RE.sub("", stem)


def review_path(track_dir: Path, slug: str) -> Path:
    """Return canonical review file path: {track_dir}/review/{bare_slug}-review.md"""
    return track_dir / "review" / f"{to_bare_slug(slug)}-review.md"


def audit_report_path(track_dir: Path, slug: str) -> Path:
    """Return canonical audit report path: {track_dir}/audit/{bare_slug}-audit.md"""
    return track_dir / "audit" / f"{to_bare_slug(slug)}-audit.md"


def grammar_path(track_dir: Path, slug: str) -> Path:
    """Return canonical grammar file path: {track_dir}/audit/{bare_slug}-grammar.yaml"""
    return track_dir / "audit" / f"{to_bare_slug(slug)}-grammar.yaml"


def quality_path(track_dir: Path, slug: str) -> Path:
    """Return canonical quality file path: {track_dir}/audit/{bare_slug}-quality.md"""
    return track_dir / "audit" / f"{to_bare_slug(slug)}-quality.md"


def status_path(track_dir: Path, slug: str) -> Path:
    """Return status file path, checking bare slug first then numeric-prefixed.

    Canonical form is bare slug ({track_dir}/status/{bare_slug}.json).
    Falls back to numeric-prefixed form (e.g., 01-slug.json) for core tracks
    that haven't been migrated yet.
    """
    bare = to_bare_slug(slug)
    canonical = track_dir / "status" / f"{bare}.json"
    if canonical.exists():
        return canonical
    # Fallback: try numeric-prefixed (e.g., "01-the-cyrillic-code-i.json")
    status_dir = track_dir / "status"
    if status_dir.exists():
        matches = list(status_dir.glob(f"*-{bare}.json"))
        if matches:
            return matches[0]
    return canonical  # Return canonical even if missing (for creation)
