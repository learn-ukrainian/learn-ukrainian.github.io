"""
Outline Compliance Checker (Structural)

Validates that markdown content follows the content_outline structure from meta YAML.
Prevents semantic drift between planned structure and actual content.

LEVEL 1 (Structural - implemented here):
- Section headers in .md match content_outline sections
- Word count per section within reasonable tolerance (±30%)
- All outline sections are present

LEVEL 2 (Semantic - future enhancement):
- LLM-based analysis of content coverage
- Verification that content actually covers outlined points
- More expensive but catches true semantic drift

Issue: #440
"""

import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
import yaml


# =============================================================================
# SECTION EXTRACTION FROM MARKDOWN
# =============================================================================

def extract_markdown_sections(md_path: Path) -> Dict[str, Dict[str, any]]:
    """
    Extract section headers and word counts from markdown file.

    Returns dict mapping section name → {header, words, line_num}

    Example:
        {
            "Вступ": {"header": "Вступ", "words": 450, "line_num": 7},
            "Шлях до великого княжіння": {"header": "Шлях до...", "words": 680, "line_num": 31}
        }
    """
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    sections = {}
    current_section = None
    current_words = 0
    current_line = 0

    # Split into lines for processing
    lines = content.split('\n')

    # Skip frontmatter
    in_frontmatter = False
    skip_until = 0

    for idx, line in enumerate(lines):
        # Handle frontmatter
        if line.strip() == '---':
            if not in_frontmatter:
                in_frontmatter = True
                skip_until = idx
            else:
                in_frontmatter = False
                skip_until = idx + 1
                continue

        if idx < skip_until:
            continue

        # Detect ## headers (main sections)
        header_match = re.match(r'^##\s+(.+)$', line)
        if header_match:
            # Save previous section
            if current_section:
                sections[current_section] = {
                    'header': current_section,
                    'words': current_words,
                    'line_num': current_line
                }

            # Start new section
            current_section = header_match.group(1).strip()
            # Remove markdown formatting and emojis
            current_section = re.sub(r'\s*—.*$', '', current_section)  # Remove "— Subtitle"
            current_section = re.sub(r'[📚🎯💡🔍]', '', current_section).strip()
            current_words = 0
            current_line = idx + 1
        else:
            # Count words in non-header lines
            # Skip code blocks, blockquotes, and special markers
            if not line.strip().startswith('```') and \
               not line.strip().startswith('>') and \
               not line.strip().startswith('---') and \
               not line.strip().startswith('#'):
                # Count Ukrainian and English words
                words = re.findall(r'[а-яіїєґА-ЯІЇЄҐA-Za-z]+', line)
                current_words += len(words)

    # Save last section
    if current_section:
        sections[current_section] = {
            'header': current_section,
            'words': current_words,
            'line_num': current_line
        }

    return sections


# =============================================================================
# OUTLINE LOADING FROM META YAML
# =============================================================================

def load_content_outline(md_path: Path) -> Optional[List[Dict]]:
    """
    Load content_outline from meta YAML file.

    Returns list of sections or None if no outline exists.

    Example:
        [
            {"section": "Вступ", "words": 480, "points": [...]},
            {"section": "Шлях до великого княжіння", "words": 640, "points": [...]}
        ]
    """
    meta_dir = md_path.parent / 'meta'
    meta_file = meta_dir / f"{md_path.stem}.yaml"

    if not meta_file.exists():
        return None

    try:
        with open(meta_file, 'r', encoding='utf-8') as f:
            meta_data = yaml.safe_load(f)

        if not meta_data or 'content_outline' not in meta_data:
            return None

        return meta_data['content_outline']

    except Exception:
        return None


# =============================================================================
# SECTION NAME NORMALIZATION
# =============================================================================

def normalize_section_name(name: str) -> str:
    """
    Normalize section name for comparison.

    - Lowercase
    - Remove punctuation
    - Remove extra whitespace
    - Remove common Ukrainian filler words

    Example:
        "Вступ — Останній великий князь" → "вступ останній великий князь"
        "Шлях до великого княжіння" → "шлях великого княжіння"
    """
    name = name.lower().strip()

    # Remove em-dash subtitles
    name = re.sub(r'\s*[—–-]\s*.*$', '', name)

    # Remove punctuation
    name = re.sub(r'[^\wа-яіїєґ\s]', ' ', name)

    # Remove extra whitespace
    name = re.sub(r'\s+', ' ', name).strip()

    # Remove common filler words for better matching
    filler = {'та', 'і', 'й', 'або', 'чи'}
    words = [w for w in name.split() if w not in filler]

    return ' '.join(words)


def fuzzy_match_section(markdown_section: str, outline_sections: List[str]) -> Tuple[bool, str, float]:
    """
    Find best match for markdown section in outline sections.

    Returns: (matched, best_match, similarity_score)

    Uses normalized names and word overlap scoring.
    """
    from difflib import SequenceMatcher

    md_normalized = normalize_section_name(markdown_section)
    best_match = None
    best_score = 0.0

    for outline_sec in outline_sections:
        ol_normalized = normalize_section_name(outline_sec)

        # Use sequence matcher for similarity
        score = SequenceMatcher(None, md_normalized, ol_normalized).ratio()

        if score > best_score:
            best_score = score
            best_match = outline_sec

    # Threshold: 0.6 = 60% similarity
    if best_score >= 0.6:
        return (True, best_match, best_score)

    return (False, "", 0.0)


# =============================================================================
# COMPLIANCE CHECKING
# =============================================================================

def check_outline_compliance(
    file_path: str,
    level: str,
    module_num: int,
) -> List[Dict]:
    """
    Check structural compliance between markdown content and content_outline.

    This is the main entry point called by the audit system.

    Returns list of violation dicts with 'type', 'message', 'severity'.
    """
    violations = []
    md_path = Path(file_path)

    # Load outline from meta YAML
    outline = load_content_outline(md_path)

    if not outline:
        # No content_outline defined - skip check
        # This is expected for modules that don't use fractal generation
        return []

    # Extract sections from markdown
    md_sections = extract_markdown_sections(md_path)

    if not md_sections:
        violations.append({
            'type': 'NO_SECTIONS_FOUND',
            'message': (
                "No sections found in markdown, but content_outline exists in meta YAML.\n"
                "  Expected sections:\n" +
                "\n".join(f"    - {s['section']}" for s in outline)
            ),
            'severity': 'error',
        })
        return violations

    # Build outline section names for matching
    outline_section_names = [s['section'] for s in outline]
    matched_outline_sections = set()

    # Check each outline section exists in markdown
    for outline_sec in outline:
        section_name = outline_sec['section']
        expected_words = outline_sec['words']

        # Try to find matching section in markdown
        matched, md_match, score = fuzzy_match_section(section_name, list(md_sections.keys()))

        if not matched:
            violations.append({
                'type': 'MISSING_OUTLINE_SECTION',
                'message': (
                    f"Section '{section_name}' defined in outline but not found in markdown.\n"
                    f"  Expected word count: {expected_words}\n"
                    f"  Add section to markdown with ## header"
                ),
                'severity': 'error',
            })
            continue

        # Section found - check word count
        matched_outline_sections.add(md_match)
        actual_words = md_sections[md_match]['words']
        line_num = md_sections[md_match]['line_num']

        # Calculate deviation
        diff = actual_words - expected_words
        diff_pct = abs(diff) / expected_words if expected_words > 0 else 0

        # Only check if UNDER target (diff < 0)
        # Tolerance: -10% warning, -20% error
        if diff < 0 and diff_pct >= 0.10:
            severity = 'warning' if diff_pct < 0.20 else 'error'

            violations.append({
                'type': 'SECTION_LENGTH_MISMATCH',
                'message': (
                    f"Section '{section_name}' is under target word count.\n"
                    f"  Expected: ~{expected_words} words (minimum -10%)\n"
                    f"  Actual: {actual_words} words\n"
                    f"  Deviation: {diff:+d} words ({diff_pct*100:.0f}%)\n"
                    f"  Location: line {line_num} in markdown"
                ),
                'severity': severity,
            })

    # Check for extra sections in markdown not in outline
    for md_sec_name, md_sec_data in md_sections.items():
        if md_sec_name not in matched_outline_sections:
            # Check if it fuzzy-matches any outline section
            matched, _, score = fuzzy_match_section(md_sec_name, outline_section_names)
            if not matched:
                violations.append({
                    'type': 'EXTRA_SECTION_IN_MARKDOWN',
                    'message': (
                        f"Section '{md_sec_name}' found in markdown but not in outline.\n"
                        f"  Word count: {md_sec_data['words']}\n"
                        f"  Location: line {md_sec_data['line_num']}\n"
                        f"  Either add to content_outline in meta YAML or remove from markdown"
                    ),
                    'severity': 'warning',
                })

    return violations


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = ['check_outline_compliance']
