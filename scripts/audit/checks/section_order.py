"""
Section order validation for curriculum modules.

Ensures consistent section ordering across all modules and levels.
Supports both English and Ukrainian section headers.
"""

import re
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

# Section type aliases - maps various header names to canonical types
SECTION_ALIASES = {
    # Content sections (appear in order they're written)
    "introduction": ["# Introduction", "# Вступ", "# Intro", "## Introduction", "## Вступ"],
    "grammar": ["# Grammar", "# Граматика", "## Grammar", "## Граматика"],
    "examples": [
        "# Examples in Context",
        "# Examples",
        "# Приклади",
        "# Приклади в контексті",
        "## Examples in Context",
        "## Examples",
        "## Приклади",
        "## Приклади в контексті",
    ],
    "dialogues": ["# Dialogues", "# Діалоги", "# Dialogue", "## Dialogues", "## Діалоги"],
    "cultural": [
        "# Cultural Insight",
        "# Cultural Notes",
        "# Культурні нотатки",
        "## Cultural Insight",
        "## Cultural Notes",
        "## Культурні нотатки",
    ],
    "reading": ["# Reading Practice", "## Reading Practice"],  # A2 PPP format
    "warm_up": ["# Warm-up", "# Warm Up", "# Розминка", "## Warm-up", "## Warm Up", "## Розминка"],  # A2 PPP format
    "presentation": ["# Presentation", "# Презентація", "## Presentation", "## Презентація"],  # A2 PPP format
    "practice": ["# Practice", "# Практика", "## Practice", "## Практика"],  # A2 PPP format
    "review": ["# Review Sections", "# Review", "# Огляд", "## Review Sections", "## Review", "## Огляд"],
    "checklist": [
        "# A1 Can-Do Checklist",
        "# Can-Do Checklist",
        "# Контрольний список",
        "## Checklist",
        "## Контрольний список",
    ],
    # End sections (fixed order: Summary → Activities → Self-Assessment → External → Vocabulary)
    "summary": [
        "## Summary",
        "## Підсумок",
        "## Підсумок (Summary)",
        "## Резюме",
        "## Module Summary",
        "# Summary",
        "# Підсумок",
    ],
    "activities": [
        "## Activities",
        "## Вправи",
        "## Вправи (Activities)",
        "## Практичні вправи",
        "## Exercises",
        "# Activities",
        "# Вправи",
    ],
    "self_assessment": [
        "## Self-Assessment",
        "## Self-Assessment Rubric",
        "## Самооцінка",
        "## Самооцінка A1 (Final Self-Assessment)",
        "## Final Self-Assessment",
    ],
    "external": [
        "## External Resources",
        "## Зовнішні ресурси",
        "## Resources",
        "## Further Reading",
        "## Додаткові матеріали",
        "# External Resources",
        "# Зовнішні ресурси",
    ],
    "vocabulary": [
        "## Vocabulary",
        "## Словник",
        "## Vocab",
        "## Лексика",
        "## Word List",
        "# Vocabulary",
        "# Словник",
    ],
}

# Canonical order for end sections (must appear in this order at the end)
END_SECTION_ORDER = ["summary", "activities", "self_assessment", "external", "vocabulary"]

# These sections are optional
OPTIONAL_SECTIONS = {
    "self_assessment",
    "external",
    "introduction",
    "cultural",
    "reading",
    "warm_up",
    "presentation",
    "practice",
    "review",
    "checklist",
}


@dataclass
class Section:
    """Represents a section in a module file."""

    section_type: str  # Canonical type (e.g., 'vocabulary', 'activities')
    header: str  # Original header text (e.g., '# Vocabulary')
    line_num: int  # Line number where section starts
    content: str  # Full section content including header


def get_section_type(header: str) -> Optional[str]:
    """Map a header to its canonical section type.

    Uses exact match against known aliases to avoid false positives
    (e.g. '## Словник Шлунку' should NOT match '## Словник').
    """
    header_clean = header.strip()
    for section_type, aliases in SECTION_ALIASES.items():
        for alias in aliases:
            if header_clean == alias:
                return section_type
    return None


def is_title_section(header: str) -> bool:
    """Check if header is a module title (not a standard section)."""
    # Title sections are unique per module and don't match any alias pattern
    section_type = get_section_type(header)
    if section_type:
        return False
    # It's a title if it's an H1 that doesn't match known sections
    return header.strip().startswith("# ")


def parse_sections(content: str) -> list[Section]:
    """Parse module content into sections into sections."""
    sections = []
    lines = content.split("\n")

    current_header = None
    current_line_num = 0
    current_content_lines = []

    for i, line in enumerate(lines, 1):
        # Support both # and ## as section starts
        # But ignore ### and deeper for top-level sectioning
        if (line.startswith("# ") or line.startswith("## ")) and get_section_type(line):
            # Save previous section
            if current_header:
                section_type = get_section_type(current_header)
                if section_type:  # Only track known sections
                    sections.append(
                        Section(
                            section_type=section_type,
                            header=current_header,
                            line_num=current_line_num,
                            content="\n".join(current_content_lines),
                        )
                    )

            current_header = line
            current_line_num = i
            current_content_lines = [line]
        elif line.startswith("# ") and not current_header:
            # Handle the case where the very first H1 is the title and we want to start capturing
            # actually parse_sections currently only captures "known" sections.
            # If it's a title, we don't capture it as a "Section" object yet?
            # Looking at current code, it only tracks "known" sections.
            pass
        else:
            if current_header:
                current_content_lines.append(line)

    # Save last section
    if current_header:
        section_type = get_section_type(current_header)
        if section_type:
            sections.append(
                Section(
                    section_type=section_type,
                    header=current_header,
                    line_num=current_line_num,
                    content="\n".join(current_content_lines),
                )
            )

    return sections


def check_section_order(content: str, file_path: Path = None) -> list[dict]:
    """
    Check if sections are in the correct order.

    Returns list of issues found.
    """
    issues = []
    sections = parse_sections(content)

    if not sections:
        return issues

    # Extract end sections that are present
    end_sections_present = [s for s in sections if s.section_type in END_SECTION_ORDER]

    if not end_sections_present:
        return issues

    # Check order of end sections
    expected_order = [t for t in END_SECTION_ORDER if any(s.section_type == t for s in end_sections_present)]
    actual_order = [s.section_type for s in end_sections_present]

    if actual_order != expected_order:
        # Find specific violations
        for i, section in enumerate(end_sections_present):
            expected_idx = expected_order.index(section.section_type)
            actual_idx = actual_order.index(section.section_type)

            if expected_idx != actual_idx:
                # Find what should come before this
                if expected_idx > 0:
                    should_come_after = expected_order[expected_idx - 1]
                    issues.append(
                        {
                            "type": "section_order",
                            "severity": "warning",
                            "line": section.line_num,
                            "message": f"'{section.header.strip()}' should come after '{should_come_after}' section",
                            "section": section.section_type,
                            "expected_order": expected_order,
                            "actual_order": actual_order,
                        }
                    )
                    break  # Only report first violation

    # Check that end sections come after content sections
    if end_sections_present:
        first_end_section = end_sections_present[0]
        content_sections = [s for s in sections if s.section_type not in END_SECTION_ORDER]

        for content_section in content_sections:
            if content_section.line_num > first_end_section.line_num:
                issues.append(
                    {
                        "type": "section_order",
                        "severity": "warning",
                        "line": content_section.line_num,
                        "message": f"Content section '{content_section.header.strip()}' appears after end section '{first_end_section.header.strip()}'",
                        "section": content_section.section_type,
                    }
                )

    return issues


def fix_section_order(content: str) -> tuple[str, list[str]]:
    """
    Reorder sections to match canonical order.

    Returns (fixed_content, list_of_changes_made).
    """
    changes = []
    lines = content.split("\n")

    # Find frontmatter boundaries
    frontmatter_end = 0
    if lines and lines[0] == "---":
        for i, line in enumerate(lines[1:], 1):
            if line == "---":
                frontmatter_end = i + 1
                break

    # Split into: frontmatter, title+content, end sections
    frontmatter = lines[:frontmatter_end]
    rest = lines[frontmatter_end:]

    # Parse rest into sections
    section_starts = []
    for i, line in enumerate(rest):
        if line.startswith("# ") and not line.startswith("## "):
            section_type = get_section_type(line)
            section_starts.append(
                {
                    "line_idx": i,
                    "type": section_type,
                    "header": line,
                    "is_end_section": section_type in END_SECTION_ORDER if section_type else False,
                }
            )

    if len(section_starts) < 2:
        return content, []  # Nothing to reorder

    # Split content by sections
    sections_content = {}
    title_and_content = []

    for i, section in enumerate(section_starts):
        start = section["line_idx"]
        end = section_starts[i + 1]["line_idx"] if i + 1 < len(section_starts) else len(rest)
        section_lines = rest[start:end]

        if section["type"] is None:
            # This is the title section
            title_and_content = section_lines
        elif section["is_end_section"]:
            sections_content[section["type"]] = section_lines
        else:
            # Content section - append to title_and_content
            title_and_content.extend(section_lines)

    # Check if reordering is needed
    current_end_order = [s["type"] for s in section_starts if s["is_end_section"]]
    expected_end_order = [t for t in END_SECTION_ORDER if t in sections_content]

    if current_end_order == expected_end_order:
        return content, []  # Already in correct order

    # Rebuild content
    result_lines = frontmatter + title_and_content

    # Add end sections in canonical order
    for section_type in END_SECTION_ORDER:
        if section_type in sections_content:
            result_lines.extend(sections_content[section_type])

    changes.append(f"Reordered end sections: {current_end_order} → {expected_end_order}")

    return "\n".join(result_lines), changes


def get_section_order_summary(content: str) -> dict:
    """Get a summary of section order for reporting."""
    sections = parse_sections(content)
    return {
        "sections": [{"type": s.section_type, "header": s.header.strip(), "line": s.line_num} for s in sections],
        "end_section_order": [s.section_type for s in sections if s.section_type in END_SECTION_ORDER],
        "expected_order": END_SECTION_ORDER,
    }
