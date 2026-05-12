"""Extract deterministic wiki obligations for V7 writer/reviewer prompts."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlparse

EXTERNAL_RESOURCE_ROLES = frozenset(
    {
        "textbook",
        "youtube",
        "video",
        "blog",
        "podcast",
        "audio",
        "article",
        "wiki",
    }
)

WIKI_MANIFEST_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": [
        "slug",
        "wiki_path",
        "sequence_steps",
        "l2_errors",
        "phonetic_rules",
        "decolonization_bans",
        "external_resources",
    ],
    "properties": {
        "slug": {"type": "string"},
        "wiki_path": {"type": "string"},
        "sequence_steps": {"type": "array"},
        "l2_errors": {"type": "array"},
        "phonetic_rules": {"type": "array"},
        "decolonization_bans": {"type": "array"},
        "external_resources": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["role", "title", "url", "author", "description"],
                "properties": {
                    "role": {"enum": sorted(EXTERNAL_RESOURCE_ROLES)},
                    "title": {"type": "string"},
                    "url": {"type": ["string", "null"]},
                    "author": {"type": ["string", "null"]},
                    "description": {"type": ["string", "null"]},
                },
            },
        },
    },
}


@dataclass(frozen=True, slots=True)
class L2Error:
    id: str
    incorrect: str
    correct: str
    why: str
    treatment: Literal["contrast_pair", "prose_explanation"]
    source_lines: str


@dataclass(frozen=True, slots=True)
class SequenceStep:
    id: str
    heading: str
    step_num: int
    required_claim: str
    source_lines: str


@dataclass(frozen=True, slots=True)
class PhoneticRule:
    id: str
    written: str
    spoken: str
    treatment: Literal["explicit_explanation"]
    source_lines: str


@dataclass(frozen=True, slots=True)
class DecolonizationBan:
    id: str
    rule: str
    source_lines: str


@dataclass(frozen=True, slots=True)
class ExternalResource:
    role: str
    title: str
    url: str | None
    author: str | None
    description: str | None


@dataclass(frozen=True, slots=True)
class WikiManifest:
    slug: str
    wiki_path: str
    sequence_steps: list[SequenceStep]
    l2_errors: list[L2Error]
    phonetic_rules: list[PhoneticRule]
    decolonization_bans: list[DecolonizationBan]
    external_resources: list[ExternalResource]


_SEQUENCE_HEADING_RE = re.compile(r"^##\s+Послідовність\s+(?:викладання|введення)\b", re.IGNORECASE)
_L2_HEADING_RE = re.compile(r"^##\s+Типові\s+помилки\s+L2\b", re.IGNORECASE)
_BAN_HEADING_RE = re.compile(r"^##\s+Деколонізаційні\s+застереження\b", re.IGNORECASE)
_EXTERNAL_RESOURCES_HEADING_RE = re.compile(
    r"^##\s+(?:Зовнішні\s+ресурси|External\s+Resources)\b",
    re.IGNORECASE,
)
_ANY_H2_RE = re.compile(r"^##\s+\S")
_STEP_RE = re.compile(r"^\s*(?:[-*]\s*)?(?:\*\*)?Крок\s+(?P<num>\d+)\s*[:.]\s*(?P<title>.+?)\s*$")
_META_SLUG_RE = re.compile(r"^\s*slug\s*:\s*(?P<slug>[-\w]+)\s*$", re.MULTILINE)
_IPA_RE = re.compile(r"\[(?![SС]\d)(?=[^\]\n]*(?:[:'ʼ’]|[A-Za-z]))[^\]\n]{1,60}\]")
_WRITTEN_RE = re.compile(r"(?<!\w)(-[\w'’ʼ-]{0,12}ся|-шся|-ться)(?!\w)", re.IGNORECASE)
_MD_LINK_RE = re.compile(r"\[(?P<title>[^\]]+)\]\((?P<url>[^)]+)\)")
_BULLET_RESOURCE_RE = re.compile(
    r"^\s*[-*]\s*(?:(?P<role>[A-Za-zА-ЯІЇЄҐа-яіїєґ-]+)\s*[:—-]\s*)?(?P<body>.+?)\s*$"
)


def extract_manifest(wiki_path: str | Path) -> dict[str, Any]:
    """Extract a JSON-serializable wiki obligations manifest."""
    path = Path(wiki_path)
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    slug = _extract_slug(text, path)

    manifest = WikiManifest(
        slug=slug,
        wiki_path=str(path),
        sequence_steps=_extract_sequence_steps(lines),
        l2_errors=_extract_l2_errors(lines),
        phonetic_rules=_extract_phonetic_rules(lines),
        decolonization_bans=_extract_decolonization_bans(lines),
        external_resources=_extract_external_resources(lines),
    )
    manifest_data = asdict(manifest)
    validate_manifest(manifest_data)
    return manifest_data


def validate_manifest(manifest: dict[str, Any]) -> None:
    """Validate the manifest shape that writer/reviewer prompts consume."""
    for key in WIKI_MANIFEST_SCHEMA["required"]:
        if key not in manifest:
            raise ValueError(f"wiki manifest missing required key: {key}")
    for index, resource in enumerate(manifest["external_resources"], start=1):
        if not isinstance(resource, dict):
            raise ValueError(f"external_resources[{index}] must be an object")
        for key in ("role", "title", "url", "author", "description"):
            if key not in resource:
                raise ValueError(f"external_resources[{index}] missing {key}")
        role = resource["role"]
        if role not in EXTERNAL_RESOURCE_ROLES:
            raise ValueError(f"external_resources[{index}] has invalid role: {role}")
        if not isinstance(resource["title"], str) or not resource["title"].strip():
            raise ValueError(f"external_resources[{index}] requires non-empty title")
        if role != "textbook" and not resource["url"]:
            raise ValueError(
                f"external_resources[{index}] role {role!r} requires url"
            )


def _extract_slug(text: str, path: Path) -> str:
    match = _META_SLUG_RE.search(text)
    return match.group("slug").strip() if match else path.stem


def _section_span(lines: list[str], heading_re: re.Pattern[str]) -> tuple[int, int] | None:
    start = None
    for index, line in enumerate(lines):
        if heading_re.search(line):
            start = index
            break
    if start is None:
        return None
    end = len(lines)
    for index in range(start + 1, len(lines)):
        if _ANY_H2_RE.search(lines[index]):
            end = index
            break
    return start, end


def _line_range(start_index: int, end_index: int) -> str:
    start = start_index + 1
    end = end_index + 1
    return str(start) if start == end else f"{start}-{end}"


def _clean_inline(text: str) -> str:
    text = text.replace("`", "")
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _clean_optional(text: str | None) -> str | None:
    if text is None:
        return None
    cleaned = _clean_inline(text)
    return cleaned or None


def _normalize_external_role(raw_role: str | None, *, url: str | None = None) -> str:
    role = _clean_inline(raw_role or "").casefold()
    aliases = {
        "book": "textbook",
        "books": "textbook",
        "підручник": "textbook",
        "textbook": "textbook",
        "youtube": "youtube",
        "ютуб": "youtube",
        "відео": "video",
        "video": "video",
        "blog": "blog",
        "блог": "blog",
        "podcast": "podcast",
        "подкаст": "podcast",
        "audio": "audio",
        "аудіо": "audio",
        "article": "article",
        "стаття": "article",
        "wiki": "wiki",
        "wikipedia": "wiki",
        "вікіпедія": "wiki",
    }
    if role in aliases:
        return aliases[role]
    if url:
        try:
            host = (urlparse(url).hostname or "").lower()
        except (ValueError, TypeError):
            host = ""
        if host == "youtube.com" or host.endswith(".youtube.com") or host == "youtu.be":
            return "youtube"
    return "article" if url else "textbook"


def _extract_markdown_link(value: str) -> tuple[str, str | None]:
    match = _MD_LINK_RE.search(value)
    if not match:
        return value, None
    return match.group("title"), match.group("url").strip() or None


def _external_resource_from_cells(
    row: dict[str, str],
    *,
    fallback_role: str | None = None,
) -> ExternalResource | None:
    title_raw = (
        row.get("title")
        or row.get("назва")
        or row.get("ресурс")
        or row.get("resource")
        or ""
    )
    title_from_link, link_url = _extract_markdown_link(title_raw)
    url = _clean_optional(row.get("url") or row.get("посилання") or link_url)
    role = _normalize_external_role(row.get("role") or row.get("роль") or fallback_role, url=url)
    title = _clean_inline(title_from_link)
    if not title:
        return None
    return ExternalResource(
        role=role,
        title=title,
        url=url,
        author=_clean_optional(row.get("author") or row.get("автор")),
        description=_clean_optional(
            row.get("description") or row.get("опис") or row.get("notes") or row.get("нотатки")
        ),
    )


def _extract_external_resources(lines: list[str]) -> list[ExternalResource]:
    span = _section_span(lines, _EXTERNAL_RESOURCES_HEADING_RE)
    if not span:
        return []
    start, end = span
    table_resources = _extract_external_resources_table(lines[start + 1 : end])
    if table_resources:
        return table_resources
    return _extract_external_resources_bullets(lines[start + 1 : end])


def _extract_external_resources_table(lines: list[str]) -> list[ExternalResource]:
    resources: list[ExternalResource] = []
    headers: list[str] = []
    table_started = False
    for line in lines:
        cells = _parse_table_row(line)
        if not cells:
            if table_started:
                break
            continue
        if _is_separator_row(cells):
            table_started = True
            continue
        lowered = [cell.casefold() for cell in cells]
        if not headers:
            if any(cell in {"title", "назва", "ресурс", "resource"} for cell in lowered):
                headers = lowered
                table_started = True
            continue
        table_started = True
        row = {headers[index]: cell for index, cell in enumerate(cells[: len(headers)])}
        resource = _external_resource_from_cells(row)
        if resource is not None:
            resources.append(resource)
    return resources


def _extract_external_resources_bullets(lines: list[str]) -> list[ExternalResource]:
    resources: list[ExternalResource] = []
    for line in lines:
        match = _BULLET_RESOURCE_RE.match(line)
        if not match:
            continue
        body = match.group("body")
        title_raw, url = _extract_markdown_link(body)
        parts = [part.strip() for part in re.split(r"\s+[—–-]\s+", body, maxsplit=2)]
        if url:
            author = parts[1] if len(parts) > 1 else None
            description = parts[2] if len(parts) > 2 else None
        else:
            title_raw = parts[0]
            author = parts[1] if len(parts) > 1 else None
            description = parts[2] if len(parts) > 2 else None
        resource = _external_resource_from_cells(
            {
                "role": match.group("role") or "",
                "title": title_raw,
                "url": url or "",
                "author": author or "",
                "description": description or "",
            }
        )
        if resource is not None:
            resources.append(resource)
    return resources


def _extract_sequence_steps(lines: list[str]) -> list[SequenceStep]:
    span = _section_span(lines, _SEQUENCE_HEADING_RE)
    if not span:
        return []
    start, end = span
    step_starts: list[tuple[int, re.Match[str]]] = []
    for index in range(start + 1, end):
        match = _STEP_RE.match(lines[index])
        if match:
            step_starts.append((index, match))

    steps: list[SequenceStep] = []
    for seq_index, (line_index, match) in enumerate(step_starts, start=1):
        next_line = step_starts[seq_index][0] if seq_index < len(step_starts) else end
        body = " ".join(line.strip() for line in lines[line_index:next_line] if line.strip())
        body = _clean_inline(body)
        step_num = int(match.group("num"))
        title = _clean_inline(match.group("title"))
        heading = f"Крок {step_num}: {title}"
        steps.append(
            SequenceStep(
                id=f"step-{step_num}",
                heading=heading,
                step_num=step_num,
                required_claim=body,
                source_lines=_line_range(line_index, max(line_index, next_line - 1)),
            )
        )
    return steps


def _parse_table_row(line: str) -> list[str]:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return []
    cells = [cell.strip() for cell in stripped.strip("|").split("|")]
    return [_clean_inline(cell) for cell in cells]


def _is_separator_row(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in cells)


def _extract_l2_errors(lines: list[str]) -> list[L2Error]:
    span = _section_span(lines, _L2_HEADING_RE)
    if not span:
        return []
    start, end = span
    errors: list[L2Error] = []
    table_started = False
    for index in range(start + 1, end):
        cells = _parse_table_row(lines[index])
        if not cells:
            if table_started:
                break
            continue
        if _is_separator_row(cells):
            table_started = True
            continue
        lowered = " ".join(cells).casefold()
        if "помилково" in lowered and "правильно" in lowered:
            table_started = True
            continue
        table_started = True
        if len(cells) < 3:
            continue
        errors.append(
            L2Error(
                id=f"err-{len(errors) + 1}",
                incorrect=cells[0],
                correct=cells[1],
                why=" | ".join(cells[2:]),
                treatment="contrast_pair",
                source_lines=_line_range(index, index),
            )
        )
    return errors


def _extract_phonetic_rules(lines: list[str]) -> list[PhoneticRule]:
    rules: list[PhoneticRule] = []
    seen: set[tuple[str, str]] = set()
    for index, line in enumerate(lines):
        clean = _clean_inline(line)
        if not clean or not _IPA_RE.search(clean):
            continue
        if "вимов" not in clean.casefold() and not _WRITTEN_RE.search(clean):
            continue
        written = _WRITTEN_RE.findall(clean)
        spoken = _IPA_RE.findall(clean)
        if not written or not spoken:
            continue
        for written_item, spoken_item in zip(written, spoken, strict=False):
            key = (written_item, spoken_item)
            if key in seen:
                continue
            seen.add(key)
            rules.append(
                PhoneticRule(
                    id=f"phon-{len(rules) + 1}",
                    written=written_item,
                    spoken=spoken_item,
                    treatment="explicit_explanation",
                    source_lines=_line_range(index, index),
                )
            )
    return rules


def _extract_decolonization_bans(lines: list[str]) -> list[DecolonizationBan]:
    span = _section_span(lines, _BAN_HEADING_RE)
    if not span:
        return []
    start, end = span
    bans: list[DecolonizationBan] = []
    paragraph_lines: list[str] = []
    paragraph_start = start + 1

    def flush(last_index: int) -> None:
        nonlocal paragraph_lines, paragraph_start
        if not paragraph_lines:
            return
        rule = _clean_inline(" ".join(paragraph_lines))
        if rule:
            bans.append(
                DecolonizationBan(
                    id=f"ban-{len(bans) + 1}",
                    rule=rule,
                    source_lines=_line_range(paragraph_start, last_index),
                )
            )
        paragraph_lines = []

    for index in range(start + 1, end):
        line = lines[index].strip()
        if not line:
            flush(index - 1)
            paragraph_start = index + 1
            continue
        if not paragraph_lines:
            paragraph_start = index
        paragraph_lines.append(line)
    flush(end - 1)
    return bans
