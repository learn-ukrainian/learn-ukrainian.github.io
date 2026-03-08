"""
Parsing and detection utilities for module audits.

Contains data classes (AuditContext, AuditState), frontmatter parsing,
level/focus detection, and section parsing.
"""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from .config import LEVEL_CONFIG


@dataclass
class AuditContext:
    """Immutable module identity + parsed data for the audit."""
    file_path: str
    content: str
    body: str
    frontmatter_str: str
    meta_data: dict | None
    plan_data: dict | None
    vocab_data: list | None
    vocab_error: str | None
    level_code: str
    module_num: int
    track_code: str
    display_level: str
    module_focus: str | None
    module_title: str
    target: int
    config: dict
    section_map: dict
    core_content: str
    phase: str
    pedagogy: str
    skip_activities: bool
    skip_review: bool
    yaml_activities: list | None
    use_yaml_activities: bool
    yaml_file: Path = field(default_factory=lambda: Path('.'))


@dataclass
class AuditState:
    """Mutable accumulator passed through audit phases."""
    has_critical_failure: bool = False
    critical_failure_reasons: list = field(default_factory=list)
    results: dict = field(default_factory=dict)
    pedagogical_violations: list = field(default_factory=list)
    activity_count: int = 0
    found_activity_types: list = field(default_factory=list)
    valid_density_count: int = 0
    total_activities: int = 0
    low_density_activities: list = field(default_factory=list)
    activity_details: list = field(default_factory=list)
    table_rows: list = field(default_factory=list)
    vocab_blocking: list = field(default_factory=list)
    vocab_warnings: list = field(default_factory=list)
    template_violations: list = field(default_factory=list)
    total_words: int = 0
    raw_words: int = 0
    engagement_count: int = 0
    audio_count: int = 0
    lint_errors: list = field(default_factory=list)
    richness_data: dict = field(default_factory=dict)

    def fail(self, reason: str) -> None:
        self.has_critical_failure = True
        self.critical_failure_reasons.append(reason)


def parse_frontmatter(content: str) -> tuple[str, str]:
    """Extract frontmatter and body from content."""
    match = re.match(r'^---\n(.*?)\n---\n(.*)', content, re.DOTALL)
    if not match:
        return "", content
    return match.group(1), match.group(2)


def validate_required_metadata(frontmatter_str: str) -> list[str]:
    """Check for required metadata fields."""
    from .config import REQUIRED_METADATA
    missing = []
    for key, pattern in REQUIRED_METADATA:
        if not re.search(pattern, frontmatter_str):
            missing.append(key)
    return missing


def detect_level(file_path: str, frontmatter_str: str) -> tuple[str, int, str]:
    """Detect level code and module number from file path."""
    phase_match = re.search(r'phase:\s*([A-Za-z0-9\.]+)', frontmatter_str)
    phase = phase_match.group(1) if phase_match else "A1"

    level_from_path = None
    track_from_path = None
    path_match = re.search(r'/([abc][12])(-[a-z0-9]+)?/', file_path.lower())
    if path_match:
        base_level = path_match.group(1).upper()
        track_suffix = path_match.group(2)
        level_from_path = base_level
        track_from_path = f"{base_level}{track_suffix.upper()}" if track_suffix else base_level
    else:
        special_match = re.search(r'/(lit|oes|ruth|bio|hist|istorio)/', file_path.lower())
        if special_match:
            track_name = special_match.group(1)
            _TRACK_LEVEL_MAP = {
                'bio': 'C1', 'istorio': 'C1',
                'hist': 'B2',
                'lit': 'LIT', 'oes': 'OES', 'ruth': 'RUTH',
            }
            level_from_path = _TRACK_LEVEL_MAP.get(track_name, track_name.upper())
            track_from_path = track_name.upper()

    level_code = 'LIT' if phase == 'LIT' else level_from_path if level_from_path else phase.split('.')[0]

    if level_code not in LEVEL_CONFIG:
        if level_code.endswith('+'):
            level_code = level_code[:-1]
        if level_code not in LEVEL_CONFIG:
            level_code = 'A1'

    track_code = track_from_path if track_from_path else level_code

    module_num = 999
    try:
        basename = os.path.basename(file_path)
        m = re.search(r'module-(\d+)', basename)
        if m:
            module_num = int(m.group(1))
        else:
            m = re.match(r'^(\d+)-', basename)
            if m:
                module_num = int(m.group(1))
            else:
                m = re.search(r'module-LIT-(\d+)', basename)
                if m:
                    module_num = int(m.group(1))
    except (ValueError, AttributeError):
        pass

    return level_code, module_num, track_code


def detect_focus(frontmatter_str: str, level_code: str, module_num: int,
                 title: str = "", file_path: str = "") -> str | None:
    """Detect module focus (grammar, vocab, checkpoint, skills, cultural, history, etc.)."""
    if file_path:
        fp_lower = file_path.lower()
        if '/hist/' in fp_lower:
            return 'history'
        if '/bio/' in fp_lower:
            return 'biography'
        if '/istorio/' in fp_lower:
            return 'istorio'
        if '/lit/' in fp_lower:
            return 'literature'
        track_match = re.search(r'/([abc][12])-([a-z]+)/', fp_lower)
        if track_match:
            track_suffix = track_match.group(2)
            if track_suffix == 'pro':
                return 'professional'

    focus_match = re.search(
        r'^focus:\s*["\']?(grammar|vocab|vocabulary|checkpoint|skills|culture|cultural|capstone|bridge|history|literature|biography|folk-culture|fine-arts|synthesis)["\']?$',
        frontmatter_str, re.MULTILINE | re.IGNORECASE
    )
    if focus_match:
        focus_val = focus_match.group(1).lower()
        if focus_val == 'vocabulary':
            return 'vocab'
        if focus_val == 'cultural':
            return 'culture'
        return focus_val

    title_lower = title.lower() if title else ""
    if 'checkpoint' in title_lower:
        return 'checkpoint'

    if level_code == 'B1':
        if module_num <= 5:
            return 'bridge'
        elif module_num <= 51:
            return 'grammar'
        elif module_num <= 71:
            return 'vocab'
        elif module_num <= 81:
            return 'culture'
        else:
            return 'skills'
    elif level_code == 'B2':
        if module_num <= 40:
            return 'grammar'
        elif module_num <= 70:
            return 'vocab'
        elif module_num <= 131:
            return 'history'
        else:
            return 'skills'

    return None


def parse_sections(body: str) -> dict[str, str]:
    """Parse body into sections."""
    sections = re.split(r'\n#{1,2}\s+(.*?)\n', body)
    section_map = {}

    if sections[0].strip():
        section_map['Intro/Narrative'] = sections[0]

    for i in range(1, len(sections), 2):
        title = sections[i].strip()
        text = sections[i + 1] if i + 1 < len(sections) else ""
        section_map[title] = text

    return section_map
