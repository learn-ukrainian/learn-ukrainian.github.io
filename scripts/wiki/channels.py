"""Channel registry helpers for the external articles corpus."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .config import PROJECT_ROOT

CHANNELS_PATH = PROJECT_ROOT / "data" / "external_articles" / "channels.yaml"

REGISTER_TAGS = {"spoken", "scripted", "interview", "mixed"}
DECOLONIZATION_TAGS = {"strong", "moderate", "none", "neutral"}
LANGUAGE_PURITY_TAGS = {"vetted", "auto-captions", "unreviewed"}
QUALITY_TIER_WEIGHTS = {1: 1.0, 2: 0.6, 3: 0.2}

_REQUIRED_FIELDS = {
    "id",
    "name",
    "host",
    "url",
    "source_file",
    "register_tag",
    "decolonization_tag",
    "quality_tier",
    "language_purity",
    "track_affinity",
    "description",
}

_channels_cache: dict[str, dict[str, Any]] | None = None
TRACK_CHANNEL_AFFINITY: dict[str, dict[str, float]] = {}


def _validate_channel(raw: dict[str, Any]) -> dict[str, Any]:
    missing = sorted(_REQUIRED_FIELDS - set(raw))
    if missing:
        raise ValueError(f"Channel entry missing required fields: {', '.join(missing)}")

    register_tag = str(raw["register_tag"]).strip()
    if register_tag not in REGISTER_TAGS:
        raise ValueError(f"Invalid register_tag '{register_tag}'")

    decolonization_tag = str(raw["decolonization_tag"]).strip()
    if decolonization_tag not in DECOLONIZATION_TAGS:
        raise ValueError(f"Invalid decolonization_tag '{decolonization_tag}'")

    language_purity = str(raw["language_purity"]).strip()
    if language_purity not in LANGUAGE_PURITY_TAGS:
        raise ValueError(f"Invalid language_purity '{language_purity}'")

    quality_tier = raw["quality_tier"]
    if not isinstance(quality_tier, int) or quality_tier not in QUALITY_TIER_WEIGHTS:
        raise ValueError(f"Invalid quality_tier '{quality_tier}'")

    affinity = raw["track_affinity"]
    if not isinstance(affinity, dict):
        raise ValueError("track_affinity must be a mapping")

    normalized_affinity: dict[str, float] = {}
    for track, value in affinity.items():
        if not isinstance(track, str) or not track.strip():
            raise ValueError("track_affinity keys must be non-empty strings")
        if not isinstance(value, (int, float)):
            raise ValueError(f"track_affinity[{track!r}] must be numeric")
        if not 0.0 <= float(value) <= 1.0:
            raise ValueError(f"track_affinity[{track!r}] must be between 0.0 and 1.0")
        normalized_affinity[track.strip()] = float(value)

    normalized = dict(raw)
    normalized["register_tag"] = register_tag
    normalized["decolonization_tag"] = decolonization_tag
    normalized["language_purity"] = language_purity
    normalized["track_affinity"] = normalized_affinity
    return normalized


def load_channels(path: Path | None = None, *, reload: bool = False) -> dict[str, dict[str, Any]]:
    """Load and validate the channel registry keyed by source_file."""
    global _channels_cache

    registry_path = path or CHANNELS_PATH
    if registry_path == CHANNELS_PATH and _channels_cache is not None and not reload:
        return _channels_cache

    data = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
    raw_channels = data.get("channels")
    if not isinstance(raw_channels, list):
        raise ValueError("channels.yaml must contain a top-level 'channels' list")

    by_source_file: dict[str, dict[str, Any]] = {}
    seen_ids: set[str] = set()

    for raw in raw_channels:
        if not isinstance(raw, dict):
            raise ValueError("Each channel entry must be a mapping")
        channel = _validate_channel(raw)

        channel_id = str(channel["id"]).strip()
        source_file = str(channel["source_file"]).strip()
        if not channel_id:
            raise ValueError("Channel id must be non-empty")
        if not source_file:
            raise ValueError("source_file must be non-empty")
        if channel_id in seen_ids:
            raise ValueError(f"Duplicate channel id '{channel_id}'")
        if source_file in by_source_file:
            raise ValueError(f"Duplicate source_file '{source_file}'")

        seen_ids.add(channel_id)
        by_source_file[source_file] = channel

    if registry_path == CHANNELS_PATH:
        _channels_cache = by_source_file
        TRACK_CHANNEL_AFFINITY.clear()
        TRACK_CHANNEL_AFFINITY.update(
            {source_file: dict(channel["track_affinity"]) for source_file, channel in by_source_file.items()}
        )

    return by_source_file


def get_channel(source_file: str) -> dict[str, Any]:
    """Look up channel metadata by source_file."""
    return load_channels()[source_file]


def get_track_affinity(source_file: str, track: str) -> float:
    """Return 0.0-1.0 track affinity for a channel/source file."""
    channels = load_channels()
    channel = channels.get(source_file)
    if not channel:
        return 0.0
    return float(channel["track_affinity"].get(track, 0.0))


def quality_tier_weight(quality_tier: Any) -> float:
    """Return the ranking weight for a quality tier."""
    try:
        return QUALITY_TIER_WEIGHTS[int(quality_tier)]
    except (KeyError, TypeError, ValueError):
        return QUALITY_TIER_WEIGHTS[2]


def rank_external_hits(
    hits: list[dict[str, Any]],
    *,
    track: str | None = None,
    source_type_priority: dict[str, float] | None = None,
    apply_quality_without_track: bool = True,
) -> list[dict[str, Any]]:
    """Re-rank external hits using channel affinity and quality tiers.

    SQLite FTS5 BM25 ranks are negative numbers where more-negative is better,
    so weighted ranks continue to sort ascending.
    """
    ranked: list[dict[str, Any]] = []
    for hit in hits:
        rank = float(hit.get("rank", 0.0) or 0.0)
        source_type = str(hit.get("source_type", "")).strip()
        priority = 1.0
        if source_type_priority is not None:
            priority = float(source_type_priority.get(source_type, 1.0))

        tier_weight = quality_tier_weight(hit.get("quality_tier"))
        if track:
            channel_id = str(hit.get("channel_id", "")).strip()
            if channel_id:
                affinity = get_track_affinity(channel_id, track)
            else:
                affinity = 1.0
                if source_type_priority is not None:
                    tier_weight = 1.0
        else:
            affinity = 1.0
            if not apply_quality_without_track:
                tier_weight = 1.0

        adjusted_score = rank * priority * tier_weight * affinity
        ranked.append({**hit, "adjusted_score": adjusted_score})

    return sorted(
        ranked,
        key=lambda hit: (
            float(hit.get("adjusted_score", hit.get("rank", 0.0)) or 0.0),
            -int(hit.get("_kw_score", 0) or 0),
        ),
    )
