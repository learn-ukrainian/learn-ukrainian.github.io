"""Fleet taxonomy resolver module.

Provides canonicalization and area resolution helpers based on
scripts/config/fleet_taxonomy.yaml.
"""

from __future__ import annotations

import functools
from dataclasses import dataclass
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TAXONOMY_PATH = PROJECT_ROOT / "scripts/config/fleet_taxonomy.yaml"


class FleetTaxonomyError(ValueError):
    """Base class for fleet taxonomy exceptions."""


class UnknownAreaError(FleetTaxonomyError):
    """Raised when an area name, alias, or epic number cannot be resolved."""


@dataclass(frozen=True, slots=True)
class EpicInfo:
    """Represents an epic in the fleet taxonomy."""

    number: int
    name: str


@dataclass(frozen=True, slots=True)
class ResolvedArea:
    """Represents a resolved area in the fleet taxonomy."""

    id: str
    aliases: tuple[str, ...]
    epics: tuple[EpicInfo, ...]


@dataclass(frozen=True, slots=True)
class TaxonomyRegistry:
    """Parsed and indexed fleet taxonomy data."""

    areas: dict[str, ResolvedArea]
    alias_to_area: dict[str, ResolvedArea]
    epic_to_area: dict[int, ResolvedArea]


@functools.lru_cache(maxsize=16)
def load_fleet_taxonomy(taxonomy_path: Path | None = None) -> TaxonomyRegistry:
    """Load and index fleet_taxonomy.yaml."""
    path = (taxonomy_path or DEFAULT_TAXONOMY_PATH).resolve()
    if not path.is_file():
        raise FleetTaxonomyError(f"Fleet taxonomy file not found: {path}")

    try:
        raw_data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise FleetTaxonomyError(f"Failed to parse YAML in {path}: {exc}") from exc

    if not isinstance(raw_data, dict) or "areas" not in raw_data:
        raise FleetTaxonomyError(f"Invalid taxonomy structure in {path}")

    areas_map: dict[str, ResolvedArea] = {}
    alias_to_area: dict[str, ResolvedArea] = {}
    epic_to_area: dict[int, ResolvedArea] = {}

    raw_areas = raw_data.get("areas", {})
    if isinstance(raw_areas, dict):
        for area_id, area_data in raw_areas.items():
            if not isinstance(area_data, dict):
                continue

            raw_aliases = area_data.get("aliases", [])
            aliases = tuple(str(a) for a in raw_aliases)

            epics_list: list[EpicInfo] = []
            for raw_epic in area_data.get("epics", []):
                if isinstance(raw_epic, dict) and "number" in raw_epic:
                    epics_list.append(
                        EpicInfo(
                            number=int(raw_epic["number"]),
                            name=str(raw_epic.get("name", "")),
                        )
                    )

            area = ResolvedArea(
                id=area_id,
                aliases=aliases,
                epics=tuple(epics_list),
            )
            areas_map[area_id] = area
            alias_to_area[area_id] = area

            for alias in aliases:
                if alias in alias_to_area and alias_to_area[alias].id != area_id:
                    raise FleetTaxonomyError(
                        f"Duplicate alias '{alias}' found across areas '{alias_to_area[alias].id}' and '{area_id}'"
                    )
                alias_to_area[alias] = area

            for epic in area.epics:
                if epic.number in epic_to_area and epic_to_area[epic.number].id != area_id:
                    raise FleetTaxonomyError(
                        f"Duplicate epic number {epic.number} found across areas '{epic_to_area[epic.number].id}' and '{area_id}'"
                    )
                epic_to_area[epic.number] = area

    return TaxonomyRegistry(
        areas=areas_map,
        alias_to_area=alias_to_area,
        epic_to_area=epic_to_area,
    )


def list_valid_names(*, taxonomy_path: Path | None = None) -> tuple[str, ...]:
    """Return all valid area IDs and aliases sorted alphabetically."""
    registry = load_fleet_taxonomy(taxonomy_path)
    return tuple(sorted(registry.alias_to_area.keys()))


def resolve_area(
    name: str | int,
    *,
    taxonomy_path: Path | None = None,
) -> ResolvedArea:
    """Resolve an area by its canonical ID, alias, or epic number.

    Raises UnknownAreaError if the input cannot be resolved.
    """
    registry = load_fleet_taxonomy(taxonomy_path)

    # 1. Direct integer epic lookup
    if isinstance(name, int):
        if name in registry.epic_to_area:
            return registry.epic_to_area[name]
        valid_epics = sorted(registry.epic_to_area.keys())
        raise UnknownAreaError(
            f"Unknown epic number {name}. Valid epics: {valid_epics}"
        )

    # 2. String lookup: canonical ID or alias
    s_name = str(name).strip()
    if s_name in registry.alias_to_area:
        return registry.alias_to_area[s_name]

    # 3. String numeric or epic:N lookup
    target_num: int | None = None
    if s_name.startswith("epic:"):
        raw_num = s_name[5:]
        if raw_num.isdigit():
            target_num = int(raw_num)
    elif s_name.isdigit():
        target_num = int(s_name)

    if target_num is not None and target_num in registry.epic_to_area:
        return registry.epic_to_area[target_num]

    valid_names = sorted(registry.alias_to_area.keys())
    raise UnknownAreaError(
        f"Unknown area name, alias, or epic '{name}'. Valid canonical names and aliases: {valid_names}"
    )


def resolve_area_by_epic(
    epic_number: int | str,
    *,
    taxonomy_path: Path | None = None,
) -> ResolvedArea:
    """Resolve an area specifically by epic number (e.g. 4707 or 'epic:4707' or '4707')."""
    if isinstance(epic_number, str):
        cleaned = epic_number.strip()
        if cleaned.startswith("epic:"):
            cleaned = cleaned[5:]
        if not cleaned.isdigit():
            raise UnknownAreaError(f"Invalid epic number format: '{epic_number}'")
        num = int(cleaned)
    else:
        num = int(epic_number)

    return resolve_area(num, taxonomy_path=taxonomy_path)
