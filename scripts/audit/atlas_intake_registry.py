#!/usr/bin/env python3
"""Shared source-family registry for full-corpus Atlas intake."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

SOURCE_FAMILY_CURRICULUM = "curriculum"
SOURCE_FAMILY_TEACHER_LESSON = "teacher_lesson"
SOURCE_FAMILY_TEXTBOOK = "textbook"
SOURCE_FAMILY_OHOIKO = "ohoiko"

SourceFamilyId = Literal["curriculum", "teacher_lesson", "textbook", "ohoiko"]

REQUIRED_SOURCE_FAMILIES: tuple[SourceFamilyId, ...] = (
    SOURCE_FAMILY_CURRICULUM,
    SOURCE_FAMILY_TEACHER_LESSON,
    SOURCE_FAMILY_TEXTBOOK,
    SOURCE_FAMILY_OHOIKO,
)


@dataclass(frozen=True)
class SourceFamilyDefinition:
    """Policy for one safe Atlas-intake source family."""

    id: SourceFamilyId
    label: str
    raw_text_policy: str
    safe_locator_policy: str
    default_extraction_modes: tuple[str, ...]
    atlas_publish_policy: str
    surface_admission_policy: str


SOURCE_FAMILY_REGISTRY: dict[str, SourceFamilyDefinition] = {
    SOURCE_FAMILY_CURRICULUM: SourceFamilyDefinition(
        id=SOURCE_FAMILY_CURRICULUM,
        label="Owned curriculum/module content",
        raw_text_policy="owned source text may be inspected; intake census still emits derived metadata only",
        safe_locator_policy="repository-relative path plus section/key locator",
        default_extraction_modes=(
            "grammar_vocabulary_item",
            "module_markdown_token",
            "activity_token",
            "vocabulary_yaml_item",
        ),
        atlas_publish_policy="deterministic gate, review queue for ambiguous candidates, controlled Atlas publish",
        surface_admission_policy="Daily Word, Practice, and Cloze require explicit surface_admission",
    ),
    SOURCE_FAMILY_TEACHER_LESSON: SourceFamilyDefinition(
        id=SOURCE_FAMILY_TEACHER_LESSON,
        label="Private teacher lessons",
        raw_text_policy="never commit raw private lesson text, filenames, or private infrastructure details",
        safe_locator_policy="neutral lesson slug/source id plus table/paragraph locator",
        default_extraction_modes=(
            "curated_headword",
            "private_document_token",
        ),
        atlas_publish_policy="derived metadata only; external/non-Codex review before publish batches",
        surface_admission_policy="no learner-surface admission without explicit surface_admission policy",
    ),
    SOURCE_FAMILY_TEXTBOOK: SourceFamilyDefinition(
        id=SOURCE_FAMILY_TEXTBOOK,
        label="Ukrainian textbook corpus",
        raw_text_policy="never commit raw copyrighted textbook text or OCR chunks",
        safe_locator_policy="public/source slug plus page/chunk/row locator where rights-safe",
        default_extraction_modes=(
            "curated_headword",
            "headword_inventory",
            "ocr_candidate",
        ),
        atlas_publish_policy="strong noise/OCR filters plus review for source-thin candidates",
        surface_admission_policy="no learner-surface admission without explicit surface_admission policy",
    ),
    SOURCE_FAMILY_OHOIKO: SourceFamilyDefinition(
        id=SOURCE_FAMILY_OHOIKO,
        label="Anna Ohoiko corpus",
        raw_text_policy="never commit raw copyrighted book/content text",
        safe_locator_policy="corpus/source slug plus section/page/item locator",
        default_extraction_modes=(
            "curated_headword",
            "book_candidate",
            "content_token",
        ),
        atlas_publish_policy="dedupe against Atlas/ledgers, review queue for ambiguous candidates",
        surface_admission_policy="no learner-surface admission without explicit surface_admission policy",
    ),
}


def registered_source_families() -> tuple[str, ...]:
    """Return registered source-family identifiers in deterministic order."""
    return tuple(SOURCE_FAMILY_REGISTRY)


def is_registered_source_family(source_family: object) -> bool:
    """Return true when a source-family value is in the registry."""
    return isinstance(source_family, str) and source_family.casefold() in SOURCE_FAMILY_REGISTRY


def source_family_definition(source_family: str) -> SourceFamilyDefinition:
    """Return the registry definition for a source family."""
    family = source_family.casefold()
    try:
        return SOURCE_FAMILY_REGISTRY[family]
    except KeyError as exc:
        raise KeyError(f"unregistered Atlas source family: {source_family}") from exc


def registry_payload() -> dict[str, object]:
    """Return a JSON-ready registry summary safe for public reports."""
    return {
        "workflow": "atlas_intake_source_registry.v1",
        "required_source_families": list(REQUIRED_SOURCE_FAMILIES),
        "families": [
            {
                "id": definition.id,
                "label": definition.label,
                "raw_text_policy": definition.raw_text_policy,
                "safe_locator_policy": definition.safe_locator_policy,
                "default_extraction_modes": list(definition.default_extraction_modes),
                "atlas_publish_policy": definition.atlas_publish_policy,
                "surface_admission_policy": definition.surface_admission_policy,
            }
            for definition in SOURCE_FAMILY_REGISTRY.values()
        ],
    }
