"""Learner-facing dictionary attribution for the Word Atlas (#5163).

Maps mirror-aggregator provenance (slovnyk.me, goroh.pp.ua, sum.in.ua) to
academic dictionary labels and official electronic-edition URLs per
docs/best-practices/atlas-source-presentation.md. Mirror URLs are kept only in
internal ``mirror_source_url`` / ``mirror_source_urls`` fields.
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote, unquote, urlparse

MIRROR_HOSTS = frozenset({"slovnyk.me", "goroh.pp.ua", "sum.in.ua", "www.slovnyk.me", "www.goroh.pp.ua", "www.sum.in.ua"})
MIRROR_HOST_PATTERN = re.compile(
    r"(?:^|[\s/+])(slovnyk\.me|goroh\.pp\.ua|sum\.in\.ua)(?:[/:\s]|$)",
    re.IGNORECASE,
)
MIRROR_URL_PATTERN = re.compile(
    r"https?://(?:www\.)?(?:slovnyk\.me|goroh\.pp\.ua|sum\.in\.ua)(?:/[^\s\"'<>]*)?",
    re.IGNORECASE,
)
SLOVNYK_DICT_PATH_RE = re.compile(
    r"https?://(?:www\.)?slovnyk\.me/dict/(?P<slug>[^/]+)/(?P<word>[^/?#]+)",
    re.IGNORECASE,
)
SLOVNYK_SOURCE_PREFIX_RE = re.compile(r"^slovnyk\.me:\s*", re.IGNORECASE)

SUM20_ACADEMIC_LABEL = (
    "Словник української мови у 20 томах (УМІФ НАН України, Ін-т мовознавства ім. О. О. Потебні)"
)
SUM20_SHORT_LABEL = "СУМ-20"
VTS_ACADEMIC_LABEL = "Великий тлумачний словник сучасної української мови"
VTS_SHORT_LABEL = "ВТС"
KARAVANSKY_LABEL = "Словник синонімів С. Караванського"
SYNONYMS_LABEL = "Словник синонімів української мови"
PHRASEOLOGY_LABEL = "Фразеологічний словник української мови"
BALLA_LABEL = "Українсько-англійський словник (М. Балла)"
BALLA_SHORT_LABEL = "Українсько-англійський словник"
DAVYDOV_LABEL = "«Як ми говоримо» Антоненка-Давидовича"
VOLOSHCHAK_LABEL = "Неправильно-правильно"
SHTEPA_LABEL = "Словник чужослів Павла Штепи"
CORRECTION_DICTIONARIES_LABEL = "Словники мовних поправок"

SUM20_OFFICIAL_HOME = "https://sum20ua.com"
ULIF_EXPL_HOME = "https://services.ulif.org.ua/expl"
ULIF_HOME = "https://www.ulif.org.ua"

SLUG_ACADEMIC_LABELS: dict[str, str] = {
    "newsum": SUM20_ACADEMIC_LABEL,
    "vts": VTS_ACADEMIC_LABEL,
    "synonyms_karavansky": KARAVANSKY_LABEL,
    "synonyms": SYNONYMS_LABEL,
    "phraseology": PHRASEOLOGY_LABEL,
    "ukreng": BALLA_LABEL,
    "davydov": DAVYDOV_LABEL,
    "voloschak": VOLOSHCHAK_LABEL,
    "foreign_shtepa": SHTEPA_LABEL,
}

LEGACY_LABEL_ALIASES: dict[str, str] = {
    "Словник синонімів Караванського": KARAVANSKY_LABEL,
    "Словник синонімів української мови": SYNONYMS_LABEL,
    "Фразеологічний словник української мови": PHRASEOLOGY_LABEL,
    "Українсько-англійський словник": BALLA_LABEL,
    "Словник української мови у 20 томах (СУМ-20)": SUM20_ACADEMIC_LABEL,
    SUM20_SHORT_LABEL: SUM20_ACADEMIC_LABEL,
    VTS_SHORT_LABEL: VTS_ACADEMIC_LABEL,
}


def is_mirror_host(host: str) -> bool:
    normalized = host.casefold().removeprefix("www.")
    return normalized in {item.removeprefix("www.") for item in MIRROR_HOSTS}


def is_mirror_url(url: object) -> bool:
    if not isinstance(url, str) or not url.strip():
        return False
    try:
        host = urlparse(url.strip()).hostname or ""
    except ValueError:
        return False
    return is_mirror_host(host)


def contains_mirror_provenance(value: object) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    if MIRROR_URL_PATTERN.search(value):
        return True
    return bool(MIRROR_HOST_PATTERN.search(value))


def _decode_path_word(raw: str) -> str:
    return unquote(raw).strip()


def parse_slovnyk_mirror_url(url: str) -> tuple[str, str] | None:
    match = SLOVNYK_DICT_PATH_RE.match(url.strip())
    if not match:
        return None
    return match.group("slug"), _decode_path_word(match.group("word"))


def official_url_for_slug(slug: str, word: str = "") -> str | None:
    slug = slug.strip().casefold()
    lookup_word = _decode_path_word(word)
    if slug == "newsum" and lookup_word:
        return f"{ULIF_EXPL_HOME}/#/word/{quote(lookup_word, safe='')}"
    if slug == "newsum":
        return SUM20_OFFICIAL_HOME
    if slug == "vts":
        return ULIF_HOME
    return None


def official_url_from_mirror(url: str) -> str | None:
    parsed = parse_slovnyk_mirror_url(url)
    if parsed:
        slug, word = parsed
        return official_url_for_slug(slug, word)
    if "goroh.pp.ua" in url.casefold():
        return None
    if "sum.in.ua" in url.casefold():
        return None
    return None


def academic_label_for_slug(slug: str) -> str | None:
    return SLUG_ACADEMIC_LABELS.get(slug.strip().casefold())


def normalize_academic_label(label: str) -> str:
    cleaned = SLOVNYK_SOURCE_PREFIX_RE.sub("", label.strip())
    if not cleaned:
        return cleaned
    if cleaned.casefold().startswith("slovnyk.me correction"):
        return CORRECTION_DICTIONARIES_LABEL
    return LEGACY_LABEL_ALIASES.get(cleaned, cleaned)


def join_academic_source_labels(labels: list[str]) -> str:
    normalized: list[str] = []
    seen: set[str] = set()
    for raw in labels:
        label = normalize_academic_label(str(raw or "").strip())
        if not label or label in seen:
            continue
        seen.add(label)
        normalized.append(label)
    return " + ".join(normalized)


def remap_mirror_source_string(source: str) -> str:
    if not source.strip():
        return source
    parts = [normalize_academic_label(part.strip()) for part in source.split(" + ") if part.strip()]
    deduped: list[str] = []
    seen: set[str] = set()
    for part in parts:
        if part and part not in seen:
            seen.add(part)
            deduped.append(part)
    return " + ".join(deduped)


def attach_official_url(
    block: dict[str, Any],
    *,
    mirror_url: str | None,
    slug: str | None = None,
    word: str = "",
) -> None:
    """Set learner-facing ``source_url`` and internal ``mirror_source_url``."""
    mirror = str(mirror_url or block.pop("mirror_source_url", "") or "").strip()
    if mirror and is_mirror_url(mirror):
        block.setdefault("mirror_source_url", mirror)
    elif mirror and "mirror_source_url" not in block:
        block["source_url"] = mirror
        return

    parsed = parse_slovnyk_mirror_url(mirror) if mirror else None
    resolved_slug = slug or (parsed[0] if parsed else "")
    resolved_word = word or (parsed[1] if parsed else "")
    official = official_url_for_slug(resolved_slug, resolved_word) if resolved_slug else None
    if official:
        block["source_url"] = official
    else:
        block.pop("source_url", None)


def remap_url_list(urls: list[str]) -> tuple[list[str], list[str]]:
    official: list[str] = []
    mirrors: list[str] = []
    seen_official: set[str] = set()
    seen_mirror: set[str] = set()
    for raw in urls:
        url = str(raw or "").strip()
        if not url:
            continue
        if is_mirror_url(url):
            if url not in seen_mirror:
                seen_mirror.add(url)
                mirrors.append(url)
            mapped = official_url_from_mirror(url)
            if mapped and mapped not in seen_official:
                seen_official.add(mapped)
                official.append(mapped)
            continue
        if url not in seen_official:
            seen_official.add(url)
            official.append(url)
    return official, mirrors


def apply_section_attribution(section: dict[str, Any]) -> bool:
    changed = False
    source = str(section.get("source") or "")
    remapped = remap_mirror_source_string(source)
    if remapped != source:
        section["source"] = remapped
        changed = True

    raw_urls = [str(url) for url in section.get("source_urls", []) if str(url).strip()]
    if raw_urls:
        official, mirrors = remap_url_list(raw_urls)
        if official != raw_urls:
            if official:
                section["source_urls"] = official
            else:
                section.pop("source_urls", None)
            changed = True
        if mirrors:
            existing = [str(url) for url in section.get("mirror_source_urls", []) if str(url).strip()]
            merged = list(dict.fromkeys([*existing, *mirrors]))
            if merged != existing:
                section["mirror_source_urls"] = merged
                changed = True

    for item in section.get("items", []):
        if not isinstance(item, dict):
            continue
        item_source = str(item.get("source") or "")
        item_remapped = normalize_academic_label(item_source)
        if item_remapped != item_source:
            item["source"] = item_remapped
            changed = True
        item_url = str(item.get("source_url") or "")
        if is_mirror_url(item_url):
            block = dict(item)
            attach_official_url(block, mirror_url=item_url)
            for key in ("source_url", "mirror_source_url"):
                if key in block:
                    item[key] = block[key]
                elif key in item:
                    del item[key]
            changed = True
    return changed


def apply_definition_card_attribution(card: dict[str, Any], *, lemma: str = "") -> bool:
    changed = False
    card_id = str(card.get("id") or "")
    source = str(card.get("source") or "")
    if card_id == "sum20" and source == SUM20_SHORT_LABEL:
        card["source"] = SUM20_ACADEMIC_LABEL
        changed = True
    elif card_id == "vts" and source == VTS_SHORT_LABEL:
        card["source"] = VTS_ACADEMIC_LABEL
        changed = True

    mirror_url = str(card.get("source_url") or "")
    if is_mirror_url(mirror_url):
        slug = "newsum" if card_id == "sum20" else "vts" if card_id == "vts" else None
        parsed = parse_slovnyk_mirror_url(mirror_url)
        block = dict(card)
        attach_official_url(
            block,
            mirror_url=mirror_url,
            slug=slug or (parsed[0] if parsed else ""),
            word=(parsed[1] if parsed else lemma),
        )
        for key in ("source_url", "mirror_source_url"):
            if key in block:
                card[key] = block[key]
            elif key in card and key not in block:
                del card[key]
        changed = True
    return changed


def apply_translation_attribution(translation: dict[str, Any], *, lemma: str = "") -> bool:
    changed = False
    source = str(translation.get("source") or "")
    remapped = remap_mirror_source_string(source)
    if remapped != source:
        translation["source"] = remapped or BALLA_LABEL
        changed = True
    mirror_url = str(translation.get("source_url") or "")
    if is_mirror_url(mirror_url):
        parsed = parse_slovnyk_mirror_url(mirror_url)
        block = dict(translation)
        attach_official_url(
            block,
            mirror_url=mirror_url,
            slug="ukreng",
            word=(parsed[1] if parsed else lemma),
        )
        for key in ("source_url", "mirror_source_url"):
            if key in block:
                translation[key] = block[key]
            elif key in translation and key not in block:
                del translation[key]
        changed = True
    return changed


def apply_entry_attribution(entry: dict[str, Any]) -> bool:
    changed = False
    lemma = str(entry.get("lemma") or "")
    enrichment = entry.get("enrichment")
    if isinstance(enrichment, dict):
        translation = enrichment.get("translation")
        if isinstance(translation, dict) and apply_translation_attribution(translation, lemma=lemma):
            changed = True
        for card in enrichment.get("definition_cards") or []:
            if isinstance(card, dict) and apply_definition_card_attribution(card, lemma=lemma):
                changed = True
    sections = entry.get("sections")
    if isinstance(sections, dict):
        for section in sections.values():
            if isinstance(section, dict) and apply_section_attribution(section):
                changed = True
    return changed


def learner_facing_mirror_violations(entry: dict[str, Any]) -> list[str]:
    """Return human-readable violations when mirror provenance leaks to learners."""
    lemma = str(entry.get("lemma") or "")
    violations: list[str] = []

    def check(value: object, path: str) -> None:
        if contains_mirror_provenance(value):
            violations.append(f"{path}={value!r}")

    enrichment = entry.get("enrichment")
    if isinstance(enrichment, dict):
        translation = enrichment.get("translation")
        if isinstance(translation, dict):
            check(translation.get("source"), "enrichment.translation.source")
            check(translation.get("source_url"), "enrichment.translation.source_url")
        for index, card in enumerate(enrichment.get("definition_cards") or []):
            if not isinstance(card, dict):
                continue
            check(card.get("source"), f"enrichment.definition_cards[{index}].source")
            check(card.get("source_url"), f"enrichment.definition_cards[{index}].source_url")

    sections = entry.get("sections")
    if isinstance(sections, dict):
        for name, section in sections.items():
            if not isinstance(section, dict):
                continue
            check(section.get("source"), f"sections.{name}.source")
            for index, url in enumerate(section.get("source_urls") or []):
                check(url, f"sections.{name}.source_urls[{index}]")
            for index, item in enumerate(section.get("items") or []):
                if not isinstance(item, dict):
                    continue
                check(item.get("source"), f"sections.{name}.items[{index}].source")
                check(item.get("source_url"), f"sections.{name}.items[{index}].source_url")

    if violations:
        return [f"{lemma}: {detail}" for detail in violations]
    return []
