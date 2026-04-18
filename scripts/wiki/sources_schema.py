"""Schema helpers for sibling wiki source registries.

Registry format:

```yaml
# Source registry for wiki/<domain>/<slug>.md
# Referenced inline as [S1], [S2], ...
sources:
  - id: S1
    file: 11-klas-ukrmova-avramenko-2019_s0075
    type: textbook
```
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path

import yaml

SOURCE_TYPES = {
    "dictionary",
    "external",
    "literary",
    "pravopys",
    "textbook",
    "unknown",
    "wiki",
}
_ID_RE = re.compile(r"^S([1-9]\d*)$")
_SHORT_CITATION_BODY_RE = re.compile(r"\[([^\[\]]+)\]")
_SHORT_CITATION_ID_RE = re.compile(r"\bS([1-9]\d*)\b")
_TEXTBOOK_RE = re.compile(r"^\d+-?(?:klas|клас)-.+(?:_s\d+)?$", re.IGNORECASE)
_LITERARY_HASH_RE = re.compile(r"^[0-9a-f]{8}_c\d+$", re.IGNORECASE)


@dataclass(slots=True)
class WikiSourceEntry:
    id: str
    file: str
    type: str
    preserved_from_meta: bool = False

    def __post_init__(self) -> None:
        if not _ID_RE.fullmatch(self.id):
            raise ValueError(f"Invalid wiki source id: {self.id}")
        if not self.file:
            raise ValueError("Wiki source file must be non-empty")
        if self.type not in SOURCE_TYPES:
            raise ValueError(f"Unsupported wiki source type: {self.type}")

    @property
    def ordinal(self) -> int:
        return int(self.id[1:])

    def to_dict(self) -> dict:
        data = {
            "id": self.id,
            "file": self.file,
            "type": self.type,
        }
        if self.preserved_from_meta:
            data["preserved_from_meta"] = True
        return data


@dataclass(slots=True)
class WikiSourcesRegistry:
    sources: list[WikiSourceEntry]

    def by_id(self) -> dict[str, WikiSourceEntry]:
        return {entry.id: entry for entry in self.sources}

    def by_file(self) -> dict[str, WikiSourceEntry]:
        return {entry.file: entry for entry in self.sources}


def registry_path_for(article_path: Path) -> Path:
    """Return the sibling registry path for a wiki article."""
    if article_path.suffix != ".md":
        raise ValueError(f"Expected a markdown article path, got {article_path}")
    return article_path.with_suffix(".sources.yaml")


def load_sources_registry(path: Path) -> WikiSourcesRegistry:
    """Load a sibling sources registry.

    Missing files return an empty registry to simplify migration reruns.
    """
    if not path.exists():
        return WikiSourcesRegistry(sources=[])

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    raw_sources = data.get("sources") or []
    sources = [
        WikiSourceEntry(
            id=str(item["id"]),
            file=normalize_source_filename(str(item["file"])),
            type=str(item.get("type") or _infer_source_type(str(item["file"]))),
            preserved_from_meta=bool(item.get("preserved_from_meta", False)),
        )
        for item in raw_sources
    ]
    return WikiSourcesRegistry(sources=_sort_sources(sources))


def save_sources_registry(
    path: Path,
    registry: WikiSourcesRegistry,
    *,
    article_path: Path | None = None,
) -> None:
    """Write a sources registry with a short human-readable header."""
    article_target = article_path or path.with_suffix(".md")
    article_ref = article_target.as_posix()
    if "wiki" in article_target.parts:
        article_ref = Path(*article_target.parts[article_target.parts.index("wiki"):]).as_posix()
    payload = {"sources": [entry.to_dict() for entry in _sort_sources(registry.sources)]}
    body = yaml.safe_dump(
        payload,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    )
    header = (
        f"# Source registry for {article_ref}\n"
        "# Referenced inline as [S1], [S2], ...\n"
    )
    path.write_text(header + body, encoding="utf-8")


def assign_source_ids(
    filenames: list[str],
    *,
    existing: WikiSourcesRegistry | None = None,
    preserved_from_meta: set[str] | None = None,
) -> WikiSourcesRegistry:
    """Assign stable 1-indexed source ids, preserving existing ids on reruns."""
    existing = existing or WikiSourcesRegistry(sources=[])
    preserved_from_meta = {normalize_source_filename(name) for name in (preserved_from_meta or set())}

    normalized = [normalize_source_filename(name) for name in filenames if normalize_source_filename(name)]
    seen_now: set[str] = set()
    ordered_now: list[str] = []
    for name in normalized:
        if name in seen_now:
            continue
        seen_now.add(name)
        ordered_now.append(name)

    existing_by_file = existing.by_file()
    ordered: list[WikiSourceEntry] = []
    used_files: set[str] = set()
    for entry in _sort_sources(existing.sources):
        file_name = normalize_source_filename(entry.file)
        if file_name in used_files:
            continue
        if file_name in seen_now or entry.preserved_from_meta:
            ordered.append(
                WikiSourceEntry(
                    id=entry.id,
                    file=file_name,
                    type=entry.type or _infer_source_type(file_name),
                    preserved_from_meta=entry.preserved_from_meta or file_name in preserved_from_meta,
                )
            )
            used_files.add(file_name)

    next_id = max((entry.ordinal for entry in ordered), default=0) + 1
    for file_name in ordered_now:
        if file_name in used_files:
            # Refresh preserved flag if needed.
            continue
        existing_entry = existing_by_file.get(file_name)
        if existing_entry is not None:
            ordered.append(
                WikiSourceEntry(
                    id=existing_entry.id,
                    file=file_name,
                    type=existing_entry.type or _infer_source_type(file_name),
                    preserved_from_meta=existing_entry.preserved_from_meta or file_name in preserved_from_meta,
                )
            )
        else:
            ordered.append(
                WikiSourceEntry(
                    id=f"S{next_id}",
                    file=file_name,
                    type=_infer_source_type(file_name),
                    preserved_from_meta=file_name in preserved_from_meta,
                )
            )
            next_id += 1
        used_files.add(file_name)

    return WikiSourcesRegistry(sources=_sort_sources(ordered))


def extract_short_citation_ids(article_text: str) -> list[str]:
    """Return all short citation ids found in prose, preserving duplicates."""
    found: list[str] = []
    for body in _SHORT_CITATION_BODY_RE.findall(article_text):
        found.extend(f"S{match}" for match in _SHORT_CITATION_ID_RE.findall(body))
    return found


def validate_sources_registry(article_text: str, registry: WikiSourcesRegistry) -> list[str]:
    """Validate that short citations and registry entries agree."""
    issues: list[str] = []
    by_id: dict[str, WikiSourceEntry] = {}
    by_file: dict[str, WikiSourceEntry] = {}

    for entry in registry.sources:
        if entry.id in by_id:
            issues.append(f"Duplicate registry id: {entry.id}")
        if entry.file in by_file:
            issues.append(f"Duplicate registry file: {entry.file}")
        by_id[entry.id] = entry
        by_file[entry.file] = entry

    referenced_ids = extract_short_citation_ids(article_text)
    referenced_set = set(referenced_ids)
    for citation_id in referenced_ids:
        if citation_id not in by_id:
            issues.append(f"Missing registry entry for citation {citation_id}")

    for entry in registry.sources:
        if entry.id not in referenced_set and not entry.preserved_from_meta:
            issues.append(
                f"Unreferenced registry entry {entry.id} ({entry.file}) is not marked preserved_from_meta"
            )

    return issues


def normalize_source_filename(filename: str) -> str:
    """Normalize common wiki source-id glitches without changing semantics."""
    value = filename.strip().strip("`").strip('"').strip("'")
    if not value:
        return ""
    if value.startswith("Source "):
        return value
    value = re.sub(r"^(\d+)-клас-", r"\1-klas-", value, flags=re.IGNORECASE)
    return value


def _infer_source_type(filename: str) -> str:
    """Infer a registry source type from a filename-ish source identifier."""
    lower = normalize_source_filename(filename).lower()
    if not lower or lower == "unknown":
        return "unknown"
    if _TEXTBOOK_RE.match(lower):
        return "textbook"
    if lower.startswith(("ext-wikipedia-", "wikipedia-", "wiki-")) or "wikipedia" in lower:
        return "wiki"
    if any(token in lower for token in ("pravopys", "orthograph")):
        return "pravopys"
    if lower.startswith("ext-") or lower.startswith("http://") or lower.startswith("https://"):
        return "external"
    if any(
        token in lower
        for token in (
            "sum11",
            "grinchenko",
            "frazeoloh",
            "wiktionary",
            "ukrajinet",
            "balla",
            "dmklinger",
            "slovnyk",
            "dictionary",
        )
    ):
        return "dictionary"
    if _LITERARY_HASH_RE.match(lower) or lower.startswith(("ukrlib-", "wave", "fbf", "fc", "cf", "d7")):
        return "literary"
    return "unknown"


def _sort_sources(sources: list[WikiSourceEntry]) -> list[WikiSourceEntry]:
    return sorted(sources, key=lambda entry: entry.ordinal)
