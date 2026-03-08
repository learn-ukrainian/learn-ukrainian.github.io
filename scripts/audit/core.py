"""
Core audit orchestration module.

Contains the main audit_module function that coordinates all checks
and produces the final audit report.
"""

import os
import re
import sys
from pathlib import Path

import yaml

# Add project root to path for shared module imports
SCRIPT_DIR = Path(__file__).parent.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.append(str(SCRIPT_DIR))
# Import richness calculation
import sys
from pathlib import Path

from slug_utils import grammar_path as _grammar_path
from slug_utils import quality_path as _quality_path
from slug_utils import to_bare_slug
from yaml_activities import ActivityParser

from .checks import (
    check_activity_header_format,
    check_activity_ukrainian_content,
    check_content_quality,
    check_markdown_format,
    check_resources_placement,
    check_resources_required,
    check_section_order,
    check_unjumble_word_match,
    count_items,
    run_pedagogical_checks,
)
from .checks.activities import (
    check_advanced_activities_presence,
    check_cloze_syntax_errors,
    check_error_correction_format,
    check_error_correction_hints,
    check_forbidden_activity_types,
    check_hints_in_activities,
    check_malformed_cloze_activities,
    check_mark_the_words_format,
    check_yaml_activity_types,
)
from .checks.activity_validation import (
    check_english_hints_in_activities,
    check_fill_in_answer_in_options,
    check_mark_the_words_answers_in_text,
    check_morpheme_patterns,
    check_morpheme_pedagogy,
    check_quiz_single_correct,
    check_select_min_correct,
    check_seminar_reading_pairing,
    check_translate_single_correct,
    check_unjumble_empty_jumbled,
    check_unjumble_out_of_scope_dative,
    check_unjumble_runon_answer,
)
from .checks.colonial_framing import check_colonial_framing
from .checks.content_gaming import check_content_gaming
from .checks.content_purity import check_content_purity
from .checks.content_quality import (
    ACADEMIC_LATIN_ALLOWLIST,
    detect_track_from_path,
    is_academic_latin_context,
)
from .checks.content_recall_detection import (
    is_content_heavy_module,
    run_all_content_recall_checks,
)
from .checks.euphony import check_euphony_violations
from .checks.external_resource_validation import (
    check_external_resources,
    fix_external_resource_url,
)
from .checks.imperial_terminology import check_imperial_terminology
from .checks.meta_validator import check_activity_hints_valid, check_research_file, check_seminar_meta_requirements

# Vocabulary integrity checking removed - not needed (naturalness catches bad vocabulary)
from .checks.outline_compliance import (
    check_outline_compliance,
    print_section_summary,
)
from .checks.prose_quality import check_prose_quality
from .checks.review_gaming import check_review_gaming
from .checks.review_validation import check_review_validity
from .checks.russicism_detection import check_russicisms
from .checks.state_standard_compliance import (
    check_state_standard_compliance,
)
from .checks.vocabulary import (
    check_metalanguage_scaffolding,
    check_vocab_matches_plan,
    check_vocab_table_format,
    count_vocab_rows,
    extract_vocab_from_section,
    get_cumulative_vocab,
)
from .checks.vocabulary_integration import check_vocabulary_integration
from .checks.yaml_lint import lint_yaml_file
from .checks.yaml_schema_validation import (
    check_activity_yaml_schema,
)
from .cleaners import (
    calculate_immersion,
    clean_for_immersion,
    clean_for_stats,
    extract_core_content,
)
from .config import (
    ACTIVITY_COMPLEXITY,
    ACTIVITY_KEYWORDS,
    AI_CONTAMINATION_PATTERNS,
    EXCLUDE_KEYWORDS,
    LEVEL_CONFIG,
    REQUIRED_METADATA,
    VALID_ACTIVITY_TYPES,
    get_a1_immersion_range,
    get_a2_immersion_range,
    get_b1_immersion_range,
    get_level_config,
    get_word_target,
)
from .gates import (
    GateResult,
    compute_recommendation,
    evaluate_activity_count,
    evaluate_activity_quality,
    evaluate_audio,
    evaluate_content_heavy,
    evaluate_density,
    evaluate_engagement,
    evaluate_grammar,
    evaluate_immersion,
    evaluate_lint,
    evaluate_naturalness,
    evaluate_pedagogy,
    evaluate_persona,
    evaluate_priority_types,
    evaluate_research_alignment,
    evaluate_richness,
    evaluate_structure,
    evaluate_unique_types,
    evaluate_vocab,
    evaluate_word_count,
)

sys.path.insert(0, str(Path(__file__).parent.parent))
from calculate_richness import calculate_richness_score, detect_dryness_flags

from .report import (
    generate_report,
    print_gates,
    print_immersion_fix_hints,
    print_lint_errors,
    print_low_density_activities,
    print_pedagogical_violations,
    print_recommendation,
    print_template_violations,
    save_report,
    save_status_cache,
)

from dataclasses import dataclass, field


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
    missing = []
    for key, pattern in REQUIRED_METADATA:
        if not re.search(pattern, frontmatter_str):
            missing.append(key)
    return missing


def detect_level(file_path: str, frontmatter_str: str) -> tuple[str, int, str]:
    """Detect level code and module number from file path."""
    # Parse phase from frontmatter
    phase_match = re.search(r'phase:\s*([A-Za-z0-9\.]+)', frontmatter_str)
    phase = phase_match.group(1) if phase_match else "A1"

    # Detect level and track from file path
    level_from_path = None
    track_from_path = None  # Full track name for track-aware checks (e.g., BIO)
    # Match a1, a2, b1, b2, c1, c2 (case insensitive)
    # Also matches tracks like hist, bio, lit, oes, ruth
    path_match = re.search(r'/([abc][12])(-[a-z0-9]+)?/', file_path.lower())
    if path_match:
        base_level = path_match.group(1).upper()  # e.g., C1
        track_suffix = path_match.group(2)  # e.g., -bio or None
        level_from_path = base_level
        track_from_path = f"{base_level}{track_suffix.upper()}" if track_suffix else base_level
    else:
        # Try to match special tracks (lit, oes, ruth, bio, hist, istorio)
        special_match = re.search(r'/(lit|oes|ruth|bio|hist|istorio)/', file_path.lower())
        if special_match:
            track_name = special_match.group(1)
            # Map track slugs to their CEFR levels
            _TRACK_LEVEL_MAP = {
                'bio': 'C1', 'istorio': 'C1',
                'hist': 'B2',
                'lit': 'LIT', 'oes': 'OES', 'ruth': 'RUTH',
            }
            level_from_path = _TRACK_LEVEL_MAP.get(track_name, track_name.upper())
            track_from_path = track_name.upper()

    # Use path-detected level if available
    level_code = 'LIT' if phase == 'LIT' else level_from_path if level_from_path else phase.split('.')[0]

    if level_code not in LEVEL_CONFIG:
        if level_code.endswith('+'):
            level_code = level_code[:-1]
        if level_code not in LEVEL_CONFIG:
            level_code = 'A1'

    # Store track code for track-aware checks (will be used by check_markdown_format etc.)
    # If no track detected, use level_code as fallback
    track_code = track_from_path if track_from_path else level_code

    # Detect module number
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


def detect_focus(frontmatter_str: str, level_code: str, module_num: int, title: str = "", file_path: str = "") -> str | None:
    """Detect module focus (grammar, vocab, checkpoint, skills, cultural, history, etc.)."""
    # Detect track directories first (hist, bio, istorio, lit, oes, ruth)
    # These override all other detection methods
    if file_path:
        fp_lower = file_path.lower()
        # Top-level track directories (post-rename: no level prefix)
        if '/hist/' in fp_lower:
            return 'history'
        if '/bio/' in fp_lower:
            return 'biography'
        if '/istorio/' in fp_lower:
            return 'istorio'
        if '/lit/' in fp_lower:
            return 'literature'
        # Legacy level-prefixed tracks (b2-pro, c1-pro still use prefix)
        track_match = re.search(r'/([abc][12])-([a-z]+)/', fp_lower)
        if track_match:
            track_suffix = track_match.group(2)
            if track_suffix == 'pro':
                return 'professional'

    # Check frontmatter for explicit focus - recognize all valid config types
    # Including content-heavy types: history, literature, biography, folk-culture, fine-arts, synthesis
    focus_match = re.search(
        r'^focus:\s*["\']?(grammar|vocab|vocabulary|checkpoint|skills|culture|cultural|capstone|bridge|history|literature|biography|folk-culture|fine-arts|synthesis)["\']?$',
        frontmatter_str, re.MULTILINE | re.IGNORECASE
    )
    if focus_match:
        focus_val = focus_match.group(1).lower()
        # Normalize vocabulary -> vocab
        if focus_val == 'vocabulary':
            return 'vocab'
        # Normalize cultural -> culture
        if focus_val == 'cultural':
            return 'culture'
        return focus_val

    # Detect checkpoint from title or filename
    title_lower = title.lower() if title else ""
    if 'checkpoint' in title_lower:
        return 'checkpoint'

    # Auto-detect based on module number
    if level_code == 'B1':
        if module_num <= 5:
            return 'bridge'  # M01-05: Bridge modules (metalanguage)
        elif module_num <= 51:
            return 'grammar'  # M06-51: Grammar modules
        elif module_num <= 71:
            return 'vocab'  # M52-71: Vocabulary modules
        elif module_num <= 81:
            return 'culture'  # M72-81: Cultural modules
        else:
            return 'skills'  # M82-86: Integration/Skills modules
    elif level_code == 'B2':
        if module_num <= 40:
            return 'grammar'  # M01-40: Grammar modules
        elif module_num <= 70:
            return 'vocab'  # M41-70: Vocabulary modules
        elif module_num <= 131:
            return 'history'  # M71-131: Ukrainian History modules
        else:
            return 'skills'  # M132-145: Skills & Capstone

    return None


def parse_sections(body: str) -> dict[str, str]:
    """Parse body into sections."""
    # Split on both # and ## headers to properly separate activities from Summary/Vocabulary
    sections = re.split(r'\n#{1,2}\s+(.*?)\n', body)
    section_map = {}

    if sections[0].strip():
        section_map['Intro/Narrative'] = sections[0]

    for i in range(1, len(sections), 2):
        title = sections[i].strip()
        text = sections[i + 1] if i + 1 < len(sections) else ""
        section_map[title] = text

    return section_map



def check_typography(content: str) -> list[str]:
    """
    Check for incorrect typography usage (ASCII quotes).

    NOTE: This check is disabled because angular quotes («») are not compatible
    with YAML files. Since all modern modules use Clean MD architecture with
    activities in YAML sidecars, we don't enforce angular quotes in markdown
    to avoid compatibility issues when content is copied to YAML.
    """
    errors = []
    # Typography check disabled - angular quotes incompatible with YAML
    # See Issue #402 context
    return errors

def _lint_activity_structure(lines_raw: list[str]) -> list[str]:
    """Check activity section structure: type tracking, fill-in answers, anagram format, hints."""
    lint_errors = []
    in_activities = False
    current_activity_type = None
    fill_in_needs_answer = False

    for i, line in enumerate(lines_raw):
        line_num = i + 1
        stripped = line.strip()

        # Track Activities Section
        if re.match(r'^#{1,2}\s+(Activities|Вправи)', stripped, re.IGNORECASE):
            in_activities = True

        # Track Activity Type
        if in_activities and stripped.startswith('## '):
            if fill_in_needs_answer:
                lint_errors.append(f"Line {line_num}: Previous Fill-in item missing '> [!answer]'.")
                fill_in_needs_answer = False

            parts = stripped.split(':')
            if len(parts) > 1:
                header_type = parts[0].replace('##', '').strip().lower()
                current_activity_type = header_type
            else:
                current_activity_type = None

        # 1. Anagram Check
        if current_activity_type == 'anagram' and re.search(r'\w\s+/\s+\w\s+/', stripped):
            lint_errors.append(f"Line {line_num}: Invalid Anagram format. Use spaces (a b c), not slashes.")

        # 2. Activity YAML Check
        if in_activities and (stripped.startswith('type: ') or stripped.startswith('items:')):
            lint_errors.append(f"Line {line_num}: YAML detected in Activities. Use markdown.")

        # 4. Supported Activity Check
        if current_activity_type and current_activity_type not in VALID_ACTIVITY_TYPES:
            lint_errors.append(f"Line {line_num}: Invalid Activity Type '{current_activity_type}'. Supported: {', '.join(VALID_ACTIVITY_TYPES)}.")

        # 5. Fill-In Check
        if current_activity_type == 'fill-in':
            if re.match(r'^\d+\.', stripped):
                if fill_in_needs_answer:
                    lint_errors.append(f"Line {line_num}: Previous Fill-in item missing '> [!answer]'.")
                fill_in_needs_answer = True
                if '___' not in stripped:
                    lint_errors.append(f"Line {line_num}: Fill-in item missing '___' placeholder.")

            if '> [!answer]' in stripped:
                fill_in_needs_answer = False

        # 11. True/False Strict Check
        if current_activity_type == 'true-false' and '> [!explanation]' in stripped:
            lint_errors.append(f"Line {line_num}: T/F Activity contains '[!explanation]'. Remove all hints/solutions.")

        # 13. Hint Detection (only in Activities)
        if in_activities and (re.search(r'\[Hint:.*?\]', stripped, re.IGNORECASE) or re.search(r'\(Hint:.*?\)', stripped, re.IGNORECASE) or re.search(r'\bHint:', stripped, re.IGNORECASE)):
                lint_errors.append(f"Line {line_num}: Activity Hint detected. Policy: Remove all hints (e.g. [Hint: ...]) from activities.")

    return lint_errors


def _lint_line_patterns(lines_raw: list[str], module_num: int) -> list[str]:
    """Check per-line format patterns: callouts, checkboxes, audio, headers, transliteration."""
    lint_errors = []

    for i, line in enumerate(lines_raw):
        line_num = i + 1
        stripped = line.strip()

        # 3. Callout Check
        if "**Answer:**" in stripped or "**Option:**" in stripped:
            lint_errors.append(f"Line {line_num}: Old format detected. Use '> [!answer]'.")

        # 6. Explanation Check
        if '> [!explanation]' in stripped and '[!answer]' in stripped:
            lint_errors.append(f"Line {line_num}: Malformed Explanation. Contains '[!answer]' inside explanation block.")

        # 7. Checkbox Format Check
        if stripped.startswith('- [') and not re.match(r'- \[[ xX]\]', stripped):
            lint_errors.append(f"Line {line_num}: Invalid Checkbox format. Use '- [ ]' or '- [x]'.")

        # 9. Audio Artifact Check
        is_vocab_row = (stripped.startswith('|') and stripped.count('|') >= 3)
        if 'audio_' in stripped and not is_vocab_row:
            lint_errors.append(f"Line {line_num}: 'audio_' link detected outside Vocabulary Table. User Rule: Audio links only in Vocab.")

        # 10. Empty Header Check
        if re.match(r'^#+\s*$', stripped):
            lint_errors.append(f"Line {line_num}: Empty Header detected (Lonely '#'). Remove or add title.")

        # 12. Transliteration Column Check (M21+)
        # Note: Only flag "transliteration" or "translit", NOT "translation"
        if module_num >= 21 and '|' in stripped:
                lower_stripped = stripped.lower()
                # Check for transliteration columns but NOT translation or pronunciation (Вимова) columns
                if '| translit' in lower_stripped:
                    lint_errors.append(f"Line {line_num}: Transliteration Column detected in M{module_num} (Policy M21+: None). Remove column.")

    return lint_errors


def _lint_ai_contamination(content: str) -> list[str]:
    """Check for AI contamination patterns (thinking/self-correction artifacts)."""
    lint_errors = []
    lines_raw = content.split('\n')

    for i, line in enumerate(lines_raw):
        line_num = i + 1
        stripped = line.strip()

        for pat in AI_CONTAMINATION_PATTERNS:
            if re.search(pat, stripped, re.IGNORECASE):
                if "Wait" in pat and "**" in stripped:
                    continue
                if "Sorry" in pat and "**" in stripped:
                    continue
                if "error-correction" in stripped.lower():
                    continue
                lint_errors.append(f"Line {line_num}: AI Contamination detected ('{pat}'). Remove thinking/self-correction artifacts.")

    return lint_errors


def run_lint_checks(content: str, section_map: dict, module_num: int) -> list[str]:
    """Run markdown lint checks (orchestrator)."""
    lint_errors = []
    lines_raw = content.split('\n')

    # Typography Check
    lint_errors.extend(check_typography(content))

    # Activity structure checks (stateful: type tracking, fill-in, hints)
    lint_errors.extend(_lint_activity_structure(lines_raw))

    # Per-line pattern checks (stateless: callouts, checkboxes, audio, headers, translit)
    lint_errors.extend(_lint_line_patterns(lines_raw, module_num))

    # AI contamination checks
    lint_errors.extend(_lint_ai_contamination(content))

    return lint_errors


def validate_tone(content: str) -> list[str]:
    """Validate content for tone issues."""
    errors = []

    # Check for "The Ukraine"
    if re.search(r'\bThe\s+Ukraine\b', content, re.IGNORECASE):
        is_correction = re.search(
            r'(not|incorrect|offensive|never|avoid)\s+.*?\bThe\s+Ukraine\b',
            content, re.IGNORECASE
        ) or re.search(
            r'\bThe\s+Ukraine\b.*?\s+(is\s+incorrect|is\s+offensive)',
            content, re.IGNORECASE
        )
        if not is_correction:
            errors.append("Tone Error. Found 'The Ukraine'. Use 'Ukraine' (sovereign nation).")

    # Check for "Kiev"
    if re.search(r'\bKiev\b', content) and not re.search(r'not\s+Kiev', content, re.IGNORECASE) and not re.search(r'Russian', content, re.IGNORECASE):
        errors.append("Tone Error. Found 'Kiev'. Use 'Kyiv' (Ukrainian transliteration).")

    return errors


def validate_checkpoint_format(content: str) -> list[str]:
    """Validate checkpoint modules follow Skill-based format.

    Required structure (per checkpoint design guide):
    - H1: # Checkpoint - [Name] or # Контрольна точка
    - ## Skill N: [Name] or ## Навичка N: [Name] sections (at least 1)
    - Each skill has: ### Model:, ### Practice:, ### Self-Check
      (or Ukrainian equivalents: ### Модель:, ### Практика:, ### Самоперевірка:)

    Alternative structures (Діагностика/Аналіз/Поглиблення) are flagged as errors
    requiring rewrite to Skill-based format.

    See: docs/l2-uk-en/CHECKPOINT-DESIGN-GUIDE.md
    """
    errors = []

    # Check for alternative (incorrect) structure that needs rewrite
    has_diagnostika = bool(re.search(r'^## Діагностика', content, re.MULTILINE))
    has_analiz = bool(re.search(r'^## Аналіз', content, re.MULTILINE))
    has_pogliblennya = bool(re.search(r'^## Поглиблення', content, re.MULTILINE))

    alternative_structure = has_diagnostika or has_analiz or has_pogliblennya

    # Check for at least one Skill section (English or Ukrainian)
    # Matches: "## Skill N:", "## Skill:", "## Навичка N:", "## Навичка:"
    skill_pattern = r'^## (?:Skill|Навичка)\s*\d*:'
    skill_matches = re.findall(skill_pattern, content, re.MULTILINE)

    # Flag alternative structure as error if no Skill sections
    if alternative_structure and not skill_matches:
        alt_sections = []
        if has_diagnostika:
            alt_sections.append("Діагностика")
        if has_analiz:
            alt_sections.append("Аналіз")
        if has_pogliblennya:
            alt_sections.append("Поглиблення")
        errors.append(f"REWRITE REQUIRED: Checkpoint uses incorrect '{'/'.join(alt_sections)}' structure instead of Skill-based format (## Skill N: → ### Model: → ### Practice: → ### Self-Check)")
    elif not skill_matches:
        errors.append("Checkpoint missing '## Skill N:' or '## Навичка N:' sections (need at least 1)")

    # Check for bold-style headers (old format)
    bold_model = len(re.findall(r'^\*\*Model:', content, re.MULTILINE))
    bold_practice = len(re.findall(r'^\*\*Practice:', content, re.MULTILINE))

    if bold_model > 0 or bold_practice > 0:
        errors.append(f"Checkpoint uses **bold:** format ({bold_model} Model, {bold_practice} Practice) - convert to ### H3 headers")

    # Check each Skill section structure (H3 headers required)
    # Split by either English or Ukrainian skill headers
    skill_sections = re.split(skill_pattern, content, flags=re.MULTILINE)[1:]
    for i, section in enumerate(skill_sections, 1):
        section_end = re.search(r'^##\s', section, re.MULTILINE)
        section_text = section[:section_end.start()] if section_end else section

        # Accept English or Ukrainian headers
        has_model = re.search(r'^### (?:Model|Модель)', section_text, re.MULTILINE)
        has_practice = re.search(r'^### (?:Practice|Практика)', section_text, re.MULTILINE)
        has_selfcheck = re.search(r'^### (?:Self-Check|Самоперевірка)', section_text, re.MULTILINE)

        if not has_model:
            errors.append(f"Skill {i} missing '### Model:' or '### Модель:' H3 header")
        if not has_practice:
            errors.append(f"Skill {i} missing '### Practice:' or '### Практика:' H3 header")
        if not has_selfcheck:
            errors.append(f"Skill {i} missing '### Self-Check' or '### Самоперевірка' H3 header")

    return errors


def validate_checkpoint_coverage(content: str, frontmatter_str: str) -> list[str]:
    """Validate checkpoint covers expected skills from frontmatter grammar/objectives.

    Checks that:
    1. frontmatter has grammar or objectives list
    2. Each grammar/objective topic appears in content (Skill sections or body)

    This enables automated validation that checkpoints cover all required skills
    defined in the curriculum plan.
    """
    errors = []

    # Extract grammar list from frontmatter
    grammar_match = re.search(r'^grammar:\s*\n((?:\s+-\s+.*\n?)+)', frontmatter_str, re.MULTILINE)
    if grammar_match:
        grammar_items = re.findall(r'-\s+"?([^"\n]+)"?', grammar_match.group(1))

        # Check each grammar item appears somewhere in content
        for item in grammar_items:
            # Clean up the item for searching (take first few significant words)
            keywords = item.split('(')[0].strip()[:30].lower()
            if keywords and not re.search(re.escape(keywords[:15]), content.lower()):
                # Soft warning - might be covered under different wording
                pass  # Don't fail for now, just log for future

    # Extract objectives from frontmatter
    objectives_match = re.search(r'^objectives:\s*\n((?:\s+-\s+.*\n?)+)', frontmatter_str, re.MULTILINE)
    if objectives_match:
        objective_items = re.findall(r'-\s+"?([^"\n]+)"?', objectives_match.group(1))

        # Count how many objectives are reflected in Skill sections (English or Ukrainian)
        skill_pattern = r'^## (?:Skill|Навичка)\s*\d*:'
        skill_count = len(re.findall(skill_pattern, content, re.MULTILINE))
        objective_count = len(objective_items)

        # Warning if there are objectives but no corresponding skill sections
        if objective_count > 0 and skill_count < 1:
            errors.append(f"Checkpoint has {objective_count} objectives but no '## Skill N:' or '## Навичка N:' sections")

    return errors


def check_structure(content: str) -> dict[str, bool]:
    """Check for required structure elements.

    Returns a dictionary of boolean flags for each section.
    """
    lines = content.split('\n')
    has_summary = any(re.match(r'^#+\s+(Summary|Підсумок)', l.strip(), re.IGNORECASE) for l in lines)
    has_vocab = any(re.match(r'^#+\s+(Vocabulary|Словник)', l.strip(), re.IGNORECASE) for l in lines)
    has_activities = any(re.match(r'^#+\s+(Activities|Вправи)', l.strip(), re.IGNORECASE) for l in lines)
    has_resources = any(re.match(r'^#+\s+(External Resources|Зовнішні ресурси|Resources)', l.strip(), re.IGNORECASE) for l in lines)

    has_vocab_table = any('| Word |' in l or 'Слово' in l or 'Термін' in l or '| Ukrainian |' in l for l in lines)

    return {
        'summary': has_summary,
        'vocab_header': has_vocab,
        'vocab_table': has_vocab_table,
        'activities_header': has_activities,
        'resources_header': has_resources
    }



def load_yaml_meta(md_file_path: str) -> dict | None:
    """Load metadata from YAML sidecar if exists."""
    from pathlib import Path
    md_path = Path(md_file_path)
    bare = to_bare_slug(md_path.stem)
    yaml_path = md_path.parent / 'meta' / (bare + '.yaml')
    if not yaml_path.exists():
        # Fallback: try with raw stem (legacy files without numeric prefix)
        yaml_path = md_path.parent / 'meta' / (md_path.stem + '.yaml')
        if not yaml_path.exists():
            return None
    try:
        with open(yaml_path, encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"  ❌ YAML parse error in meta sidecar: {yaml_path}")
        print(f"     {e}")
        return None

def load_yaml_plan(md_file_path: str) -> dict | None:
    """Load plan data from plans directory if exists (Split Architecture)."""
    from pathlib import Path
    md_path = Path(md_file_path)

    # Determine level from path
    # e.g. curriculum/l2-uk-en/b1/01.md -> level=b1
    try:
        level_part = md_path.parent.name # e.g. 'b1' or 'c1' or 'lit'
        if level_part in ['a1', 'a2', 'b1', 'b2', 'c1', 'c2', 'lit', 'hist', 'bio', 'istorio']:
             level = level_part
        else:
             # Fallback: try to find level in path
             parts = md_path.parts
             if 'l2-uk-en' in parts:
                 idx = parts.index('l2-uk-en')
                 if idx + 1 < len(parts):
                     level = parts[idx+1]
                 else:
                     return None
             else:
                 return None
    except (ValueError, IndexError):
        return None

    # Construct plan path: curriculum/l2-uk-en/plans/{level}/{slug}.yaml
    # Base is curriculum/l2-uk-en
    base_dir = md_path.parent.parent
    slug = to_bare_slug(md_path.stem)
    plan_path = base_dir / 'plans' / level / (slug + '.yaml')

    if not plan_path.exists():
        # Fallback: try with stem directly (already bare after migration)
        plan_path = base_dir / 'plans' / level / (md_path.stem + '.yaml')
        if not plan_path.exists():
            return None

    try:
        with open(plan_path, encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"  ❌ YAML parse error in plan sidecar: {plan_path}")
        print(f"     {e}")
        return None

def load_yaml_vocab(md_file_path: str) -> tuple[list[dict] | None, str | None]:
    """Load vocabulary from YAML sidecar if exists.

    Returns (data, error_msg):
    - (list, None) on success
    - (None, None) if file not found
    - (None, error_string) on parse error
    """
    from pathlib import Path
    md_path = Path(md_file_path)
    yaml_path = md_path.parent / 'vocabulary' / (md_path.stem + '.yaml')
    if not yaml_path.exists():
        return None, None
    try:
        with open(yaml_path, encoding='utf-8') as f:
            data = yaml.safe_load(f)
            # Support both 'items' (legacy?) and 'vocabulary' (standard) keys
            if isinstance(data, list):
                 return data, None
            return data.get('vocabulary', data.get('items', [])), None
    except Exception as e:
        print(f"  ❌ YAML parse error in vocabulary sidecar: {yaml_path}")
        print(f"     {e}")
        return None, f"YAML parse error in {yaml_path.name}: {e}"

def get_module_number_from_curriculum(file_path: str, level_code: str) -> int | None:
    """
    Look up module number from curriculum.yaml manifest.

    Returns module number (1-based) or None if not found.
    """
    from pathlib import Path

    # Get module slug from filename
    module_slug = Path(file_path).stem

    # Remove numeric prefix if exists (e.g., "01-passive-voice" -> "passive-voice")
    # But keep it for lookup first
    bare = to_bare_slug(module_slug)
    slug_variants = [module_slug] if bare == module_slug else [module_slug, bare]

    # Find curriculum.yaml
    curriculum_yaml_path = Path(file_path).parent.parent / 'curriculum.yaml'
    if not curriculum_yaml_path.exists():
        return None

    try:
        with open(curriculum_yaml_path, encoding='utf-8') as f:
            curriculum = yaml.safe_load(f)

        # Determine which level key to look under
        # Map level codes to curriculum.yaml keys
        level_key_map = {
            'A1': 'a1',
            'A2': 'a2',
            'B1': 'b1',
            'B2': 'b2',
            'C1': 'c1',
            'C2': 'c2',
        }

        # Check if file is in a track directory (hist, bio, etc.)
        track_match = re.search(r'/([abc][12]-[a-z]+)/', file_path)
        level_key = track_match.group(1) if track_match else level_key_map.get(level_code, level_code.lower())

        # Get modules list for this level
        level_data = curriculum.get('levels', {}).get(level_key)
        if not level_data or 'modules' not in level_data:
            return None

        modules = level_data['modules']

        # Find module number by slug
        for idx, module_entry in enumerate(modules, start=1):
            # Module entry might be a string "slug-name" or "slug-name # [N]"
            module_slug_in_yaml = module_entry.split('#')[0].strip()

            # Check if any slug variant matches
            if module_slug_in_yaml in slug_variants:
                return idx

            # Also check if the original has a numeric prefix and matches
            if module_slug.startswith(f"{idx:02d}-") and module_slug[3:] == module_slug_in_yaml:
                return idx

        return None

    except Exception:
        return None

def _load_and_resolve(file_path: str, skip_activities: bool, skip_review: bool) -> tuple[AuditContext, AuditState]:
    """Load files, parse frontmatter, detect level/config, build AuditContext.

    Contains sys.exit() calls for fatal early aborts (missing file, missing frontmatter,
    missing required metadata).
    """
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.")
        sys.exit(1)

    with open(file_path, encoding='utf-8') as f:
        content = f.read()

    state = AuditState()

    # Try loading YAML sidecars
    meta_data = load_yaml_meta(file_path)
    plan_data = load_yaml_plan(file_path)

    # Merge Plan data into Meta data (Split Architecture Support)
    # This allows existing checks to work seamlessly whether data is in meta.yaml or plans/*.yaml
    if meta_data and plan_data:
        print(f"  📋 Loaded Plan from: plans/{plan_data.get('level', '').lower()}/{os.path.basename(file_path).replace('.md', '.yaml')}")
        # Copy plan fields to meta_data if not present (or overwrite if plan is authority)
        # Plan is AUTHORITY for these fields
        PLAN_FIELDS_TO_MERGE = [
            'title', 'subtitle', 'content_outline', 'word_target',
            'vocabulary_hints', 'activity_hints', 'focus', 'pedagogy',
            'prerequisites', 'connects_to', 'objectives', 'learning_outcomes',
            'grammar', 'module_type', 'sources', 'immersion', 'register', 'phase'
        ]
        for fld in PLAN_FIELDS_TO_MERGE:
            if fld in plan_data and fld not in meta_data:
                    meta_data[fld] = plan_data[fld]

    vocab_data, vocab_error = load_yaml_vocab(file_path)

    # Parse frontmatter
    if meta_data:
        # Reconstruct frontmatter string for validation functions that expect it
        frontmatter_str = yaml.dump(meta_data, sort_keys=False, allow_unicode=True)
        # Content is the body (file is stripped) - No frontmatter in MD, whole file is body
        body = content
        print("  📋 Loaded Metadata from YAML sidecar")
    else:
        frontmatter_str, body = parse_frontmatter(content)

    if not frontmatter_str:
        print("Error: No YAML frontmatter found (checked embedded and sidecar).")
        state.fail("No YAML frontmatter found")
        print("\nCritical Failures:")
        for reason in state.critical_failure_reasons:
            print(f"  • {reason}")
        sys.exit(1)

    # Detect Metadata
    level_code, module_num, track_code = detect_level(file_path, frontmatter_str)

    # Detect full track identifier for display (e.g., "BIO" instead of "C1")
    display_level = level_code
    track_match = re.search(r'/([abc][12]-[a-z]+)/', file_path.lower())
    if track_match:
        display_level = track_match.group(1).upper()  # e.g., "BIO", "HIST"
    elif re.search(r'/lit/', file_path.lower()):
        display_level = 'LIT'

    # If module number not detected (999), try curriculum.yaml lookup
    if module_num == 999:
        curriculum_module_num = get_module_number_from_curriculum(file_path, level_code)
        if curriculum_module_num is not None:
            module_num = curriculum_module_num

    module_focus = detect_focus(frontmatter_str, level_code, module_num, meta_data.get('title') if meta_data else "", file_path)

    # Parse phase (for report - defaults to level_code if not specified)
    phase_match = re.search(r'phase:\s*([A-Za-z0-9\.]+)', frontmatter_str)
    phase = phase_match.group(1) if phase_match else level_code

    # Parse title for display
    title_match = re.search(r"title:\s*['\"]?([^'\"\n]+)['\"]?", frontmatter_str)
    module_title = title_match.group(1).strip() if title_match else os.path.basename(file_path)

    print(f"\n📋 Auditing: {display_level} M{module_num:02d} — {module_title}")

    # Check word target — config is source of truth, but meta.yaml can override
    target = get_word_target(level_code, module_num, module_focus)
    if meta_data and 'word_target' in meta_data:
        target = int(meta_data['word_target'])
    elif plan_data and 'word_target' in plan_data:
        target = int(plan_data['word_target'])

    print(f"   File: {file_path} | Target: {target} words")

    # Required Metadata Check
    # For A1/A2 legacy, check frontmatter string. For B1+, assume YAML sidecar handles it (schema validated elsewhere)
    if not meta_data: # Only validate embedded frontmatter if no sidecar
        missing_meta = validate_required_metadata(frontmatter_str)
        if missing_meta:
            print(f"❌ AUDIT FAILED: Missing Frontmatter Fields: {', '.join(missing_meta)}")
            print("  -> These fields are REQUIRED for 'npm run generate'")
            state.fail(f"Missing Frontmatter Fields: {', '.join(missing_meta)}")
            print("\nCritical Failures:")
            for reason in state.critical_failure_reasons:
                print(f"  • {reason}")
            sys.exit(1)

    # Get config
    config = get_level_config(level_code, module_focus)

    # Override required_types with meta.yaml activity_hints if available
    # This ensures the audit checks against what the meta specifies, not hardcoded defaults
    if meta_data and meta_data.get('activity_hints'):
        meta_required_types = set()
        for hint in meta_data['activity_hints']:
            if isinstance(hint, dict) and 'type' in hint:
                meta_required_types.add(hint['type'])
        if meta_required_types:
            config = dict(config)  # Make a copy to avoid modifying global config
            config['required_types'] = meta_required_types
            print(f"  📋 Required activity types from meta: {', '.join(sorted(meta_required_types))}")

    # Extract pedagogy
    pedagogy = "Not Specified"
    pedagogy_match = re.search(r'^pedagogy:\s*(.+)$', frontmatter_str, re.MULTILINE)
    if pedagogy_match:
        pedagogy = pedagogy_match.group(1).strip()

    # Parse sections
    section_map = parse_sections(body)

    # Extract core content
    core_content = extract_core_content(body)

    # Load YAML activities
    yaml_activities = None
    yaml_file = Path(file_path).parent / 'activities' / (Path(file_path).stem + '.yaml')

    if skip_activities:
        print("  ⏳ Content-only audit: activities/vocab gates DEFERRED")
        use_yaml_activities = False
    else:
        # Check both new and legacy paths
        if not yaml_file.exists():
            yaml_file = Path(file_path).with_suffix('.activities.yaml')

        if yaml_file.exists():
            parser = ActivityParser()
            try:
                yaml_activities = parser.parse(yaml_file)
            except Exception as e:
                print(f"  ❌ Error parsing YAML activities: {e}")

        use_yaml_activities = yaml_activities is not None

    ctx = AuditContext(
        file_path=file_path,
        content=content,
        body=body,
        frontmatter_str=frontmatter_str,
        meta_data=meta_data,
        plan_data=plan_data,
        vocab_data=vocab_data,
        vocab_error=vocab_error,
        level_code=level_code,
        module_num=module_num,
        track_code=track_code,
        display_level=display_level,
        module_focus=module_focus,
        module_title=module_title,
        target=target,
        config=config,
        section_map=section_map,
        core_content=core_content,
        phase=phase,
        pedagogy=pedagogy,
        skip_activities=skip_activities,
        skip_review=skip_review,
        yaml_activities=yaml_activities,
        use_yaml_activities=use_yaml_activities,
        yaml_file=yaml_file,
    )

    return ctx, state


def _check_template_compliance(ctx: AuditContext, state: AuditState) -> None:
    """Check template compliance (Issue #398, #389) - Gradual rollout level-by-level."""
    TEMPLATE_COMPLIANCE_ENABLED_LEVELS = ['A1', 'A2', 'B1', 'B2', 'C1']  # All Clean MD migrated levels

    if ctx.level_code not in TEMPLATE_COMPLIANCE_ENABLED_LEVELS:
        return

    try:
        # Import template modules - use relative imports for package context
        from . import template_parser
        from .checks import template_compliance as tc_module

        # Construct module ID for template mapping
        # Extract full level including track suffix (hist, bio, lit)
        module_slug = Path(ctx.file_path).stem
        track_match = re.search(r'/([abc][12](?:-[a-z0-9]+)?|lit)/', ctx.file_path.lower())
        full_level = track_match.group(1) if track_match else ctx.level_code.lower()
        module_id_for_mapping = f"{full_level}-{module_slug}"

        # Resolve which template this module should follow
        meta_for_template = ctx.meta_data if ctx.meta_data else {}
        template_path = template_parser.resolve_template(module_id_for_mapping, meta_for_template)
        template_structure = template_parser.parse_template(template_path)

        if template_structure is None:
            print(f"  ℹ️  No template mapping for {module_id_for_mapping} (skipping template compliance)")
        else:
            print(f"  📋 Template: {template_path} (pedagogy: {template_structure.pedagogy})")

            # Run compliance checks
            state.template_violations = tc_module.check_template_compliance(
                content=ctx.content,
                meta=meta_for_template,
                template=template_structure
            )

        if state.template_violations:
            critical_count = sum(1 for v in state.template_violations if v['severity'] == 'CRITICAL')
            warning_count = sum(1 for v in state.template_violations if v['severity'] == 'WARNING')
            info_count = sum(1 for v in state.template_violations if v['severity'] == 'INFO')

            print(f"  ⚠️  Template violations: {critical_count} critical, {warning_count} warnings, {info_count} info")

            # Show first 3 violations
            for violation in state.template_violations[:3]:
                severity_icon = "🔴" if violation['severity'] == 'CRITICAL' else "⚠️" if violation['severity'] == 'WARNING' else "ℹ️"
                print(f"     {severity_icon} [{violation['type']}] {violation['issue']}")

            if critical_count > 0:
                state.fail(f"{critical_count} Critical Template Violations")

    except ImportError as e:
        print(f"  ⚠️  Template compliance not available: {e}")
    except Exception as e:
        print(f"  ⚠️  Template resolution error: {e}")


def _check_outline_compliance(ctx: AuditContext, state: AuditState) -> None:
    """Check outline compliance and tone validation."""
    # Check outline compliance (Issue #440: structural validation)
    outline_violations = check_outline_compliance(ctx.file_path, ctx.level_code, ctx.module_num)
    if outline_violations:
        error_count = sum(1 for v in outline_violations if v['severity'] == 'error')
        warning_count = sum(1 for v in outline_violations if v['severity'] == 'warning')
        print(f"  ⚠️  Outline compliance: {error_count} errors, {warning_count} warnings")
        for v in outline_violations[:3]:  # Show first 3
            severity_icon = "❌" if v['severity'] == 'error' else "⚠️"
            print(f"     {severity_icon} [{v['type']}] {v['message'].split(chr(10))[0]}")  # First line only

        if error_count > 0:
            state.fail(f"{error_count} Outline Compliance Errors")

    # Show section word summary for hydration guidance
    print_section_summary(ctx.file_path, word_target=ctx.target)

    # Tone validation
    tone_errors = validate_tone(ctx.content)
    if tone_errors:
        for err in tone_errors:
            print(f"❌ Tone violation: {err}")
            state.fail(err)


def _evaluate_structure_gate(ctx: AuditContext) -> GateResult:
    """Detect sidecar data presence and evaluate structure gate."""
    struct_flags = check_structure(ctx.content)
    has_summary = struct_flags['summary']
    has_vocab_header = struct_flags['vocab_header']
    has_vocab_table = struct_flags['vocab_table']
    has_activities_header = struct_flags['activities_header']
    has_resources_header = struct_flags['resources_header']

    # Sidecar Data Presence
    has_vocab_data = ctx.vocab_data is not None

    # Check for activities YAML
    activities_yaml_path = Path(ctx.file_path).parent / 'activities' / (Path(ctx.file_path).stem + '.yaml')
    if not activities_yaml_path.exists():
        activities_yaml_path = Path(ctx.file_path).with_suffix('.activities.yaml')
    has_activities_data = activities_yaml_path.exists()

    # Check for external resources in centralized YAML
    has_resources_data = False
    resources_path = Path('docs/resources/external_resources.yaml')
    if resources_path.exists():
        with resources_path.open('r', encoding='utf-8') as f:
            try:
                resources_data = yaml.safe_load(f)
                all_resources = resources_data.get('resources', {})
                module_slug = Path(ctx.file_path).stem
                has_resources_data = module_slug in all_resources or f"{ctx.level_code.lower()}-{module_slug}" in all_resources
            except Exception:
                pass

    # Metadata sidecar overrides for summary
    if ctx.meta_data and (ctx.meta_data.get('summary') or ctx.meta_data.get('description')):
        has_summary = True

    # Final structure evaluation (Clean MD Standard)
    is_clean_md_standard = ctx.level_code in ('A1', 'A2', 'B1', 'B2', 'C1', 'C2', 'LIT', 'OES', 'RUTH')

    return evaluate_structure(
        has_summary=has_summary,
        has_vocab=has_vocab_header or has_vocab_data or ctx.skip_activities,
        has_vocab_table=has_vocab_table or has_vocab_data or ctx.skip_activities,
        has_activities=has_activities_header or has_activities_data or ctx.skip_activities,
        has_resources=has_resources_header or has_resources_data,
        is_a2_plus=is_clean_md_standard,
        vocab_error=ctx.vocab_error,
    )


def _check_structure_gates(ctx: AuditContext, state: AuditState) -> GateResult:
    """Check structure headers, vocab, checkpoint format, fill-in options.

    Returns the structure_gate result for use in later gate evaluation.
    """
    structure_gate = _evaluate_structure_gate(ctx)

    if structure_gate.status == 'FAIL':
        print(f"❌ Structure check failed: {structure_gate.msg}")
        state.fail(f"Structure: {structure_gate.msg}")

    # Duplicate vocabulary check (B1+ should have YAML-only, not both)
    if ctx.vocab_data and ctx.level_code in ('B1', 'B2', 'C1', 'C2', 'LIT'):
        # Check if markdown also has embedded vocab table
        has_embedded_vocab = bool(re.search(r'^#\s*(Словник|Vocabulary)', ctx.content, re.MULTILINE))
        if has_embedded_vocab:
            # Check if there's actually a table after the header
            vocab_section_match = re.search(r'^#\s*(Словник|Vocabulary)\s*\n(.*?)(?=^#|\Z)', ctx.content, re.MULTILINE | re.DOTALL)
            if vocab_section_match:
                vocab_section = vocab_section_match.group(2)
                has_embedded_table = '|' in vocab_section and re.search(r'\|.*\|.*\|', vocab_section)
                if has_embedded_table:
                    print("⚠️  DUPLICATE VOCABULARY: Both YAML sidecar and embedded markdown table exist.")
                    print(f"   → For {ctx.level_code}+ modules, vocabulary should be YAML-only.")
                    print("   → Remove the '# Словник' section from the markdown file.")


    # Checkpoint format validation
    if ctx.module_focus == 'checkpoint':
        checkpoint_errors = validate_checkpoint_format(ctx.content)
        coverage_errors = validate_checkpoint_coverage(ctx.content, ctx.frontmatter_str)
        checkpoint_errors.extend(coverage_errors)
        if checkpoint_errors:
            print("❌ CHECKPOINT FORMAT ERRORS:")
            for err in checkpoint_errors:
                print(f"  → {err}")
            print("  See: docs/l2-uk-en/CHECKPOINT-DESIGN-GUIDE.md")
            state.fail("Checkpoint Format Errors")

    # Fill-in options check
    for title, text in ctx.section_map.items():
        if title.lower().startswith('fill-in'):
            if '> [!options]' not in text:
                print(f"❌ AUDIT FAILED: Activity '{title}' missing mandatory > [!options] block.")
                print("  -> ALL fill-in activities require explicit options/choices.")
                sys.exit(1)
            if not re.search(r'^\s*\d+\.', text, re.MULTILINE):
                print(f"❌ AUDIT FAILED: Activity '{title}' missing numbered items (1. ...).")
                print("  -> Parser requires fill-in items to be a numbered list to function.")
                sys.exit(1)

    return structure_gate


def _check_outline_and_structure(ctx: AuditContext, state: AuditState) -> GateResult:
    """Check outline compliance, structure, tone, checkpoints, fill-in options.

    Returns the structure_gate result for use in later gate evaluation.
    """
    _check_outline_compliance(ctx, state)
    return _check_structure_gates(ctx, state)


def _count_words_and_engagement(ctx: AuditContext, state: AuditState) -> None:
    """Count words, engagement boxes, and audio links."""
    # Word count
    state.raw_words = len(ctx.body.split())
    core_lines = [line for line in ctx.core_content.split('\n') if not line.strip().startswith('|')]
    core_no_tables = '\n'.join(core_lines)
    core_cleaned = clean_for_stats(core_no_tables)
    state.total_words = len(core_cleaned.split())

    # Engagement pattern - includes B2+ history/cultural callouts
    engagement_pattern = re.compile(
        r'(>\s*[💡⚡🎬🎭📜⚔️🔗🌍🎁🗣️🏠🧭🚌🚇🎟️📱🕵️🌤️🌦️🎱🔮🇺🇦🕰️❓🛠️💂🥪🍺🛍️🏫🏥💊👵🔬🎨🔄📅🍃❄️🚂⏳📚🍲🥣🥗🥙🥚🥛🧩⚠️🛑🎯🎮🎓🔍])|'
        r'(>\s*\[!(note|tip|warning|caution|important|cultural|history-bite|myth-buster|quote|context|analysis|source|legacy|reflection|fact|culture|military|perspective|biography)\])'
    )
    state.engagement_count = len(engagement_pattern.findall(ctx.content))

    # Audio count
    audio_pattern = re.compile(r'\[🔊\]\(.*?\)')
    state.audio_count = len(audio_pattern.findall(ctx.content))


def _validate_yaml_activities(ctx: AuditContext, state: AuditState) -> tuple[list, list, list, list, list, list, list, list, list]:
    """Run all YAML activity validation checks.

    Returns tuples of violation lists needed by later phases:
    (yaml_schema_violations, mark_words_violations, hint_violations,
     error_correction_hint_violations, malformed_cloze_violations,
     cloze_syntax_violations, error_correction_violations,
     invalid_type_violations, forbidden_type_violations)
    """
    yaml_schema_violations = []
    mark_words_violations = []
    hint_violations = []
    error_correction_hint_violations = []
    malformed_cloze_violations = []
    cloze_syntax_violations = []
    error_correction_violations = []
    invalid_type_violations = []
    forbidden_type_violations = []

    yaml_file = ctx.yaml_file

    if not ctx.skip_activities:
        # Pre-parse Linting (Issue #403)
        if yaml_file.exists():
            lint_errors = lint_yaml_file(str(yaml_file))
            if lint_errors:
                print(f"  ❌ YAML syntax violations: {len(lint_errors)}")
                for v in lint_errors:
                    print(f"     ❌ [LINT] line {v['line']}: {v['message']}")
                    print(f"        Fix: {v['fix']}")

                # Critical lint errors stop audit to avoid parser explosions
                if any(v['severity'] == 'critical' for v in lint_errors):
                    sys.exit(1)

        if yaml_file.exists():
            yaml_schema_violations = check_activity_yaml_schema(ctx.file_path, ctx.level_code, ctx.module_num)
            if yaml_schema_violations:
                print(f"  ❌ YAML schema violations: {len(yaml_schema_violations)}")
                for v in yaml_schema_violations:
                    severity_icon = "❌" if v['severity'] == 'error' else "⚠️"
                    print(f"     {severity_icon} [{v['type']}] {v['message']}")

        # Vocabulary integrity checking removed - naturalness gate catches bad vocabulary
    # Check mark-the-words format (Issue #361: prevent (correct)/(wrong) annotations)
    if ctx.yaml_activities:
        mark_words_violations = check_mark_the_words_format(ctx.yaml_activities)
        if mark_words_violations:
            print(f"  ⚠️  mark-the-words format violations: {len(mark_words_violations)}")
            for v in mark_words_violations:
                print(f"     → {v['issue']}")

    # Check for hints in activities (all should be removed)
    if ctx.yaml_activities:
        hint_violations = check_hints_in_activities(ctx.yaml_activities)
        if hint_violations:
            print(f"  ⚠️  hint violations: {len(hint_violations)}")
            for v in hint_violations:
                print(f"     → {v['issue']}")

    # Check for error-correction activities with highlighted error words
    if ctx.yaml_activities:
        error_correction_hint_violations = check_error_correction_hints(ctx.yaml_activities)
        if error_correction_hint_violations:
            print(f"  ❌  error-correction hint violations: {len(error_correction_hint_violations)}")
            for v in error_correction_hint_violations:
                print(f"     → {v['issue']}")
                print(f"     Fix: {v['fix']}")

    # Check for malformed cloze activities (dialogue lines as blanks)
    if ctx.yaml_activities:
        malformed_cloze_violations = check_malformed_cloze_activities(ctx.yaml_activities)
        if malformed_cloze_violations:
            print(f"  ⚠️  malformed cloze violations: {len(malformed_cloze_violations)}")
            for v in malformed_cloze_violations:
                print(f"     → {v['issue']}")

    # Check for cloze syntax errors (colons inside blanks)
    if ctx.yaml_activities:
        cloze_syntax_violations = check_cloze_syntax_errors(ctx.yaml_activities)
        if cloze_syntax_violations:
            print(f"  ⚠️  cloze syntax violations: {len(cloze_syntax_violations)}")
            for v in cloze_syntax_violations:
                print(f"     → {v['issue']}")

    # Check for malformed error-correction activities (placeholder syntax)
    if ctx.yaml_activities:
        error_correction_violations = check_error_correction_format(ctx.yaml_activities)
        if error_correction_violations:
            print(f"  ⚠️  malformed error-correction violations: {len(error_correction_violations)}")
            for v in error_correction_violations:
                print(f"     → {v['issue']}")

    # Check for invalid activity types in YAML
    if ctx.yaml_activities:
        invalid_type_violations = check_yaml_activity_types(ctx.yaml_activities)
        if invalid_type_violations:
            print(f"  ⚠️  invalid activity types in YAML: {len(invalid_type_violations)}")
            for v in invalid_type_violations:
                print(f"     → {v['issue']}")

    # Check for forbidden activity types (seminar tracks)
    if ctx.yaml_activities:
        forbidden_type_violations = check_forbidden_activity_types(ctx.yaml_activities, ctx.level_code, ctx.module_focus)
        if forbidden_type_violations:
            print(f"  🔴 FORBIDDEN activity types in seminar track: {len(forbidden_type_violations)}")
            for v in forbidden_type_violations:
                print(f"     → {v['issue']}")
                print(f"        Fix: {v['fix']}")
            state.fail(f"{len(forbidden_type_violations)} forbidden activity types (use --fix to remove)")

    return (yaml_schema_violations, mark_words_violations, hint_violations,
            error_correction_hint_violations, malformed_cloze_violations,
            cloze_syntax_violations, error_correction_violations,
            invalid_type_violations, forbidden_type_violations)


def _validate_activity_answers(ctx: AuditContext, state: AuditState) -> None:
    """Check structural correctness of activity answers and external URLs."""
    if not ctx.yaml_activities:
        return

    # Check morpheme patterns (Issue #363: validate *morpheme*word patterns)
    morpheme_violations = check_morpheme_patterns(ctx.yaml_activities)
    if morpheme_violations:
        print(f"  ⚠️  morpheme pattern violations: {len(morpheme_violations)}")
        for v in morpheme_violations:
            print(f"     → {v['activity']}: {v['message']}")

    # Check morpheme pedagogy (detect vague/weak morpheme activities)
    morpheme_pedagogy_violations = check_morpheme_pedagogy(ctx.yaml_activities)
    if morpheme_pedagogy_violations:
        print(f"  ⚠️  pedagogically weak morpheme activities: {len(morpheme_pedagogy_violations)}")
        for v in morpheme_pedagogy_violations:
            severity = "🔴" if v['severity'] == 'critical' else "⚠️"
            print(f"     {severity} [{v['type']}] {v['activity']}")
            print(f"        Issue: {v['message']}")
            print(f"        Fix: {v['suggestion']}")
            if 'pedagogical_issue' in v:
                print(f"        Why: {v['pedagogical_issue']}")

    # Check for inappropriate English hints in A2+ activities
    english_hint_violations = check_english_hints_in_activities(ctx.yaml_activities, ctx.level_code, ctx.module_num)
    if english_hint_violations:
        print(f"  ⚠️  English hints in A2+ activities: {len(english_hint_violations)}")
        for v in english_hint_violations:
            severity = "🔴" if v['severity'] == 'critical' else "⚠️"
            print(f"     {severity} [{v['type']}] {v['activity']} ({v['activity_type']})")
            print(f"        Issue: {v['message']}")
            print(f"        Fix: {v['suggestion']}")
            if 'pedagogical_issue' in v:
                print(f"        Why: {v['pedagogical_issue']}")

    # Check for empty jumbled fields in unjumble activities (Issue #362)
    unjumble_violations = check_unjumble_empty_jumbled(ctx.yaml_activities)
    if unjumble_violations:
        print(f"  ⚠️  unjumble activities with empty jumbled fields: {len(unjumble_violations)}")
        for v in unjumble_violations:
            severity = "🔴" if v['severity'] == 'critical' else "⚠️"
            print(f"     {severity} [{v['type']}] {v['activity']}")
            print(f"        Issue: {v['message']}")
            print(f"        Fix: {v['suggestion']}")

    # Check for reading-analysis pairing in seminar tracks (Issue #425)
    seminar_pairing_violations = check_seminar_reading_pairing(ctx.yaml_activities, ctx.level_code)
    if seminar_pairing_violations:
        print(f"  📚 Seminar reading-analysis pairing issues: {len(seminar_pairing_violations)}")
        for v in seminar_pairing_violations:
            severity = "🔴" if v['severity'] == 'critical' else "⚠️"
            print(f"     {severity} [{v['type']}] {v['activity']}")
            print(f"        Issue: {v['message']}")
            print(f"        Fix: {v['suggestion']}")
        # Critical pairing violations fail the audit (Issue #425)
        critical_pairing = [v for v in seminar_pairing_violations if v['severity'] == 'critical']
        if critical_pairing:
            state.has_critical_failure = True

    # Check structural correctness of activity answers (Issue #xxx)
    # These catch bugs the YAML schema cannot: min_correct mismatches, answer-not-in-options, etc.
    answer_correctness_violations = []
    answer_correctness_violations.extend(check_select_min_correct(ctx.yaml_activities))
    answer_correctness_violations.extend(check_quiz_single_correct(ctx.yaml_activities))
    answer_correctness_violations.extend(check_fill_in_answer_in_options(ctx.yaml_activities))
    answer_correctness_violations.extend(check_translate_single_correct(ctx.yaml_activities))
    answer_correctness_violations.extend(check_mark_the_words_answers_in_text(ctx.yaml_activities))
    answer_correctness_violations.extend(check_unjumble_runon_answer(ctx.yaml_activities))
    answer_correctness_violations.extend(check_unjumble_out_of_scope_dative(ctx.yaml_activities))
    if answer_correctness_violations:
        print(f"  🔴 Activity answer correctness issues: {len(answer_correctness_violations)}")
        for v in answer_correctness_violations:
            severity = "🔴" if v['severity'] == 'critical' else "⚠️"
            print(f"     {severity} [{v['type']}] {v.get('activity', 'Unknown')}")
            print(f"        Issue: {v['message']}")
            print(f"        Fix: {v['suggestion']}")
        critical_answer = [v for v in answer_correctness_violations if v['severity'] == 'critical']
        if critical_answer:
            state.has_critical_failure = True

    # Check external resource URLs in reading activities (Issue #430)
    if ctx.level_code.lower() in ['lit', 'hist', 'istorio', 'bio']:
        external_url_violations = check_external_resources(ctx.yaml_activities, ctx.module_title)
        if external_url_violations:
            print(f"  🔗 External URL validation issues: {len(external_url_violations)}")
            for v in external_url_violations:
                severity = "🔴" if v['severity'] == 'critical' else "⚠️"
                print(f"     {severity} [{v['type']}] {v['activity']}")
                print(f"        URL: {v.get('url', 'N/A')}")
                print(f"        Issue: {v['message']}")
                if v.get('suggested_url'):
                    print(f"        ✅ Suggested fix: {v['suggested_url']}")
                    # Auto-fix if we have a suggestion
                    if ctx.yaml_file and v.get('suggested_url'):
                        if fix_external_resource_url(ctx.yaml_file, v['url'], v['suggested_url']):
                            print(f"        ✓ AUTO-FIXED: URL updated in {ctx.yaml_file.name}")
                        else:
                            print(f"        Fix: {v['suggestion']}")
                else:
                    print(f"        Fix: {v['suggestion']}")
            # External URL mismatches are critical
            state.has_critical_failure = True


def _process_activity_sections(ctx: AuditContext, state: AuditState) -> None:
    """Process YAML and embedded markdown activities, build activity details and table rows."""
    # LLM review files removed (Issue #430 superseded)
    # Validation happens during /review-content, not via separate files

    if ctx.use_yaml_activities:
        print(f"  📋 Found YAML activities file ({len(ctx.yaml_activities)} activities)")
        # Process YAML activities
        for activity in ctx.yaml_activities:
            act_type = activity.type.lower()
            if act_type in VALID_ACTIVITY_TYPES or act_type.replace('-', '') in [t.replace('-', '') for t in VALID_ACTIVITY_TYPES]:
                state.activity_count += 1
                state.total_activities += 1
                state.found_activity_types.append(act_type)

                # Use shared count_items (Issue #394)
                items = count_items('', activity)
                density_target = ctx.config['min_items_per_activity']
                if act_type in ACTIVITY_COMPLEXITY:
                    # Try specific key first (e.g. history)
                    specific_key = f"{ctx.level_code}-{ctx.module_focus}" if ctx.module_focus else ctx.level_code
                    complexity_rules = ACTIVITY_COMPLEXITY[act_type].get(specific_key)

                    # Fallback to base level key (e.g. B2)
                    if not complexity_rules:
                        complexity_rules = ACTIVITY_COMPLEXITY[act_type].get(ctx.level_code, {})

                    if 'min_items' in complexity_rules:
                        density_target = complexity_rules['min_items']

                # Track ALL activity details for report
                state.activity_details.append({
                    'title': getattr(activity, 'title', act_type),
                    'type': act_type,
                    'items': items,
                    'target': density_target,
                    'status': '✅' if items >= density_target else '❌'
                })

                if items >= density_target:
                    state.valid_density_count += 1
                else:
                    state.low_density_activities.append({
                        'title': getattr(activity, 'title', act_type),
                        'type': act_type,
                        'items': items,
                        'target': density_target
                    })

                print(f"  > {getattr(activity, 'title', act_type)}: {items} items (min {density_target})")

    for title, text in ctx.section_map.items():
        title_lower = title.lower()

        is_core = False
        is_excluded = False
        is_activity = False

        # Activity Check
        matched_act_type = None
        for act in ACTIVITY_KEYWORDS:
            if act in title_lower:
                is_activity = True
                matched_act_type = act
        if is_activity:
            state.found_activity_types.append(matched_act_type)

        if not is_activity:
            for exc in EXCLUDE_KEYWORDS:
                if exc in title_lower:
                    is_excluded = True
                    break

            # NEW LOGIC: If not activity and not explicitly excluded, it IS core content.
            # This enables creative/thematic H2 headers.
            if not is_excluded:
                is_core = True

        cleaned_stats = clean_for_stats(text)
        count = len(cleaned_stats.split())

        status_icon = "⚪️"
        note = "Skipped"

        if is_activity and not ctx.use_yaml_activities:
            # Only count embedded MD activities if no YAML file
            state.activity_count += 1
            state.total_activities += 1

            items = count_items(text)
            # Use activity-specific minimum from complexity config if available
            density_target = ctx.config['min_items_per_activity']
            if matched_act_type in ACTIVITY_COMPLEXITY:
                 complexity_rules = ACTIVITY_COMPLEXITY[matched_act_type].get(ctx.level_code, {})
                 if 'min_items' in complexity_rules:
                     density_target = complexity_rules['min_items']

            # Track ALL activity details for report
            state.activity_details.append({
                'title': title,
                'type': matched_act_type,
                'items': items,
                'target': density_target,
                'status': '✅' if items >= density_target else '❌'
            })

            if items >= density_target:
                state.valid_density_count += 1
            else:
                # Track low density activities for reporting
                state.low_density_activities.append({
                    'title': title,
                    'type': matched_act_type,
                    'items': items,
                    'target': density_target
                })

            status_icon = "🎮"
            note = f"Activity ({items} items, min {density_target})"
            print(f"  > {title}: {items} items (min {density_target})")
            display_count = items

        elif is_activity and ctx.use_yaml_activities:
            # Skip embedded activities when using YAML
            status_icon = "⚪️"
            note = "Skipped (using YAML)"
            display_count = 0

        elif is_core and not is_excluded:
            status_icon = "✅"
            note = "Included in Core"
            display_count = count
        elif is_excluded:
            status_icon = "➖"
            note = "Excluded Type"
            display_count = count
        else:
            display_count = count

        state.table_rows.append(f"| **{title}** | {status_icon} | {display_count} | {note} |")


def _evaluate_core_gates(ctx: AuditContext, state: AuditState, structure_gate: GateResult) -> set:
    """Evaluate word count, activity, engagement, vocab, structure, persona, lint gates.

    Returns the unique_types set for use in later phases.
    """
    config = ctx.config
    vocab_target = config.get('min_vocab', 25)

    state.results['words'] = evaluate_word_count(state.total_words, ctx.target, state.raw_words)
    if state.results['words'].status == 'FAIL':
        state.has_critical_failure = True

    # Activity gates (deferred in content-only mode)
    if ctx.skip_activities:
        deferred = GateResult('INFO', '⏳', "Deferred (content-only audit)")
        state.results['activities'] = deferred
        state.results['density'] = deferred
        state.results['unique_types'] = deferred
        state.results['priority'] = deferred
        unique_types = set()
    else:
        act_target = config['min_activities']
        state.results['activities'] = evaluate_activity_count(state.activity_count, act_target)
        if state.results['activities'].status == 'FAIL':
            state.has_critical_failure = True

        failed_density = state.total_activities - state.valid_density_count
        dens_threshold = config['min_items_per_activity']
        state.results['density'] = evaluate_density(failed_density, state.total_activities, dens_threshold, act_target)
        if state.results['density'].status == 'FAIL' and act_target > 0:
            state.has_critical_failure = True
            # Print which activities need more items
            print_low_density_activities(state.low_density_activities)

        unique_types = set(state.found_activity_types)
        type_target = config['min_types_unique']
        state.results['unique_types'] = evaluate_unique_types(len(unique_types), type_target)
        if state.results['unique_types'].status == 'FAIL':
            state.has_critical_failure = True

        state.results['priority'] = evaluate_priority_types(unique_types, config['priority_types'])
        if state.results['priority'].status == 'FAIL':
            state.has_critical_failure = True

        # Check required_types (from meta.yaml activity_hints)
        required_types = config.get('required_types', set())
        if required_types:
            missing_required = required_types - unique_types
            if missing_required:
                state.fail(
                    f"Missing required activity types: {', '.join(sorted(missing_required))}"
                )
                print(f"  ❌ Missing required activity types from meta.yaml: {', '.join(sorted(missing_required))}")

    eng_target = config.get('min_engagement', 3)
    state.results['engagement'] = evaluate_engagement(state.engagement_count, eng_target)
    if state.results['engagement'].status == 'FAIL':
        state.has_critical_failure = True

    state.results['audio'] = evaluate_audio(state.audio_count)

    state.results['audio'] = evaluate_audio(state.audio_count)

    if ctx.skip_activities:
        state.results['vocab'] = GateResult('INFO', '⏳', "Deferred (content-only audit)")
    else:
        vocab_count = len(ctx.vocab_data) if ctx.vocab_data else count_vocab_rows(ctx.content)

        state.results['vocab'] = evaluate_vocab(vocab_count, vocab_target)
        # Note: vocab_count is a soft target (Issue #340) - don't fail audit

    state.results['structure'] = structure_gate
    if state.results['structure'].status == 'FAIL':
        state.has_critical_failure = True

    # Persona Gate (Deterministic Curriculum Standard v2.2)
    has_persona = ctx.plan_data is not None and 'persona' in ctx.plan_data
    has_voice = has_persona and 'voice' in ctx.plan_data['persona']
    has_role = has_persona and 'role' in ctx.plan_data['persona']
    state.results['persona'] = evaluate_persona(has_persona, has_voice, has_role)
    if state.results['persona'].status == 'FAIL':
        state.has_critical_failure = True

    # Run lint checks
    state.lint_errors = run_lint_checks(ctx.content, ctx.section_map, ctx.module_num)
    state.results['lint'] = evaluate_lint(len(state.lint_errors))
    if state.results['lint'].status == 'FAIL':
        state.has_critical_failure = True

    # Run Meta YAML requirements check (Seminar modules)
    meta_violations = check_seminar_meta_requirements(ctx.meta_data, ctx.level_code, ctx.pedagogy)

    # Check for research file (seminar tracks only)
    research_violations = check_research_file(ctx.file_path)
    meta_violations.extend(research_violations)

    # Research alignment gate — checks if content reflects current research
    try:
        from research_quality import assess_research_compat, find_research_path
        _md_path = Path(ctx.file_path)
        _bare_slug = to_bare_slug(_md_path.stem)
        _research_path = find_research_path(_md_path.parent, _bare_slug)
        _research_info = None
        if _research_path:
            _research_info = assess_research_compat(_research_path, ctx.track_code.lower(), _md_path)
        state.results['research'] = evaluate_research_alignment(_research_info, _md_path.exists())
    except ImportError:
        state.results['research'] = GateResult('INFO', 'ℹ️', "N/A (research_quality not available)")

    # Run activity type validation for ALL modules with meta.yaml
    activity_type_violations = check_activity_hints_valid(ctx.meta_data)
    meta_violations.extend(activity_type_violations)

    if meta_violations:
        print(f"  📜 Meta YAML Validation: {len(meta_violations)} issues")
        for v in meta_violations:
             severity_icon = "❌" if v['severity'] == 'critical' else "⚠️"
             print(f"     {severity_icon} [{v['type']}] {v['message']}")
             if v.get('fix'):
                 print(f"        Fix: {v['fix']}")

        # Add to main violations list but mark critical ones as blocking
        if any(v['severity'] == 'critical' for v in meta_violations):
            state.has_critical_failure = True

    # Add meta violations to pedagogical violations for reporting
    for v in meta_violations:
        state.pedagogical_violations.append({
            'type': v['type'],
            'severity': 'error' if v['severity'] == 'critical' else 'warning',
            'issue': v['message'],
            'fix': v.get('fix', '')
        })

    return unique_types


def _run_vocab_and_format_checks(ctx: AuditContext, state: AuditState) -> None:
    """Run vocabulary plan compliance, metalanguage scaffolding, markdown format, and section order checks."""
    # Run vocabulary plan compliance checks
    # VOCAB_PLAN_MISSING is NON-BLOCKING (Issue #387) - shown as warning only
    if ctx.vocab_data:
        # Extract set of words from vocab_data dicts
        vocab_words = set()
        for item in ctx.vocab_data:
            uk = item.get('lemma', '') # YAML schema uses 'lemma'
            if uk:
                vocab_words.add(uk.lower())
    else:
        vocab_words = extract_vocab_from_section(ctx.content)

    # Only check vocab plan for A1/A2 - B1+ uses separate vocabulary YAML files
    if ctx.level_code.upper() in ('A1', 'A2'):
        plan_violations = check_vocab_matches_plan(
            ctx.file_path, ctx.level_code, ctx.module_num, vocab_words
        )

        # Separate blocking violations (missing core vocab) from warnings
        state.vocab_blocking = [v for v in plan_violations if v.get('blocking', True)]
        state.vocab_warnings = [v for v in plan_violations if not v.get('blocking', True)]

        # Missing core vocab is a blocking failure
        if state.vocab_blocking:
            state.has_critical_failure = True

    # Run metalanguage scaffolding check
    cumulative_vocab = get_cumulative_vocab(ctx.level_code, ctx.module_num - 1)
    metalang_violations = check_metalanguage_scaffolding(
        ctx.content, vocab_words, ctx.level_code, ctx.module_num, cumulative_vocab
    )
    state.pedagogical_violations.extend(metalang_violations)

    # Run markdown format checks (pass track_code for track-aware checks like heading levels)
    markdown_violations = check_markdown_format(ctx.content, ctx.track_code)
    state.pedagogical_violations.extend(markdown_violations)

    # Run vocabulary table format checks
    if not ctx.vocab_data:
        vocab_format_violations = check_vocab_table_format(ctx.content, ctx.level_code)
        state.pedagogical_violations.extend(vocab_format_violations)

    # Run section order checks
    section_order_violations = check_section_order(ctx.content)
    for v in section_order_violations:
        state.pedagogical_violations.append({
            'type': v['type'].upper(),
            'severity': v['severity'],
            'issue': v['message'],
            'fix': "Reorder sections to: Summary → Activities → Self-Assessment → External → Vocabulary",
            'line': v.get('line', 0)
        })


def _run_content_detectors(ctx: AuditContext, state: AuditState) -> None:
    """Run content quality detectors: purity, imperial, russicism, colonial, euphony, prose, gaming."""
    # Run content quality checks (LLM-based + deterministic purity checks)
    content_quality_violations = check_content_quality(ctx.content, ctx.level_code, ctx.module_num, ctx.file_path)

    # Run content purity checks (Redundancy, Roboticness, Mirroring)
    yaml_content_str = ""
    if ctx.yaml_file.exists():
        yaml_content_str = ctx.yaml_file.read_text(encoding='utf-8')
    purity_violations = check_content_purity(ctx.content, yaml_content_str)

    if purity_violations:
        print(f"  ✨ Purity violations found: {len(purity_violations)}")
        for v in purity_violations:
            print(f"     ❌ [{v['type']}] {v['issue']}")

        content_quality_violations.extend(purity_violations)

    # Run imperial terminology checks (Russian/Soviet framing)
    imperial_violations = check_imperial_terminology(ctx.content, ctx.file_path)
    if imperial_violations:
        errors = [v for v in imperial_violations if v["severity"] == "error"]
        warnings = [v for v in imperial_violations if v["severity"] == "warning"]
        if errors:
            print(f"  🚩 Imperial framing violations: {len(errors)} error(s), {len(warnings)} warning(s)")
        else:
            print(f"  ⚠️  Imperial framing warnings: {len(warnings)}")
        for v in imperial_violations:
            icon = "❌" if v["severity"] == "error" else "⚠️ "
            print(f"     {icon} [{v['type']}] {v['issue']}")
        content_quality_violations.extend(imperial_violations)

    # Run Russicism detection (lexical calques from Russian)
    russicism_violations = check_russicisms(ctx.content, ctx.file_path)
    if russicism_violations:
        for v in russicism_violations:
            sev_icon = "❌" if v['severity'] == 'critical' else "⚠️"
            print(f"     {sev_icon} [{v['type']}] {v['issue']}")
        content_quality_violations.extend(russicism_violations)

    # Run colonial framing checks (Russian-as-baseline)
    colonial_violations = check_colonial_framing(ctx.content, ctx.file_path)
    if colonial_violations:
        print(f"  🏛️  Colonial framing warnings: {len(colonial_violations)}")
        for v in colonial_violations:
            print(f"     ⚠️  [{v['type']}] {v['issue']}")
        content_quality_violations.extend(colonial_violations)

    # Run euphony checks (і/й, у/в, з/із/зі, conjunction variety)
    euphony_violations = check_euphony_violations(ctx.content, ctx.file_path)
    if euphony_violations:
        print(f"  🎵 Euphony violations: {len(euphony_violations)}")
        for v in euphony_violations:
            print(f"     ⚠️  [{v['type']}] {v['issue']}")
        content_quality_violations.extend(euphony_violations)

    # Run prose quality checks (Drill blocks, Glossary lists, LLM fingerprints, Inline English)
    prose_violations = check_prose_quality(ctx.content)

    if prose_violations:
        print(f"  ✨ Prose quality violations found: {len(prose_violations)}")
        for v in prose_violations:
            print(f"     ❌ [{v['type']}] {v['issue']}")

        content_quality_violations.extend(prose_violations)

    # Run content gaming detection (Issue #610)
    gaming_violations = check_content_gaming(ctx.content, ctx.file_path)

    if gaming_violations:
        print(f"  🎭 Content gaming violations found: {len(gaming_violations)}")
        for v in gaming_violations:
            sev_icon = "❌" if v['severity'] == 'critical' else "⚠️"
            print(f"     {sev_icon} [{v['type']}] {v['issue']}")

        content_quality_violations.extend(gaming_violations)

    # Convert to standard pedagogical violations for reporting
    # Only critical-severity violations block the audit; warnings are informational
    for v in content_quality_violations:
        state.pedagogical_violations.append({
            'type': v['type'],
            'severity': v['severity'],
            'blocking': v['severity'] == 'critical',
            'issue': v['issue'],
            'fix': v['fix']
        })


def _run_content_quality_checks(ctx: AuditContext, state: AuditState) -> None:
    """Run content quality, purity, imperial, russicism, colonial, euphony, prose checks."""
    # Run pedagogical checks (with context-specific complexity)
    ped_violations = run_pedagogical_checks(
        ctx.content, ctx.core_content, ctx.level_code, ctx.module_num, ctx.pedagogy, ctx.yaml_activities, ctx.module_focus
    )
    state.pedagogical_violations.extend(ped_violations)

    # Run State Standard 2024 compliance checks
    state_standard_violations = check_state_standard_compliance(
        ctx.level_code, ctx.module_num, ctx.content, immersion_pct=None
    )
    for violation in state_standard_violations:
        state.pedagogical_violations.append({
            'type': violation.code,
            'severity': 'blocking',
            'issue': violation.message,
            'fix': violation.fix
        })

    # Run vocabulary integration checks (Issue #395)
    integration_data = check_vocabulary_integration(ctx.content, ctx.level_code, ctx.module_num, ctx.yaml_activities)
    if integration_data['total'] > 0:
        print(f"  📊 Vocabulary Integration: Lesson {integration_data['lesson_rate']:.1f}%, Activities {integration_data['activity_rate']:.1f}%")

        # Add violations if below thresholds
        if integration_data['lesson_rate'] < 50:
            state.pedagogical_violations.append({
                'type': 'LOW_LESSON_INTEGRATION',
                'severity': 'warning',
                'issue': f"Only {integration_data['lesson_rate']:.1f}% of core vocabulary used in lesson text.",
                'fix': f"Use more core words in the prose: {', '.join(integration_data['missing'][:5])}..."
            })
        if integration_data['activity_rate'] < 80:
            state.pedagogical_violations.append({
                'type': 'LOW_ACTIVITY_INTEGRATION',
                'severity': 'warning',
                'issue': f"Only {integration_data['activity_rate']:.1f}% of core vocabulary used in activities.",
                'fix': f"Add activities using: {', '.join(integration_data['missing'][:5])}..."
            })

    # Vocab/format checks
    _run_vocab_and_format_checks(ctx, state)

    # Content quality detectors
    _run_content_detectors(ctx, state)


def _run_activity_pedagogical_checks(ctx: AuditContext, state: AuditState,
                                      yaml_schema_violations: list,
                                      mark_words_violations: list,
                                      hint_violations: list,
                                      error_correction_hint_violations: list,
                                      malformed_cloze_violations: list,
                                      cloze_syntax_violations: list,
                                      error_correction_violations: list,
                                      invalid_type_violations: list) -> None:
    """Run activity-specific pedagogical checks (Ukrainian content, resources, unjumble, headers, advanced presence)."""
    # Run activity content checks (Issue #235)
    # 1. Check if activities contain Ukrainian content (not just English)
    ukrainian_content_violations = check_activity_ukrainian_content(ctx.content, ctx.level_code)
    for v in ukrainian_content_violations:
        state.pedagogical_violations.append({
            'type': v['type'],
            'severity': 'error',
            'issue': v['issue'],
            'fix': v['fix']
        })

    # 2. Check if [!resources] callout appears before Activities section
    resources_violations = check_resources_placement(ctx.content)
    for v in resources_violations:
        state.pedagogical_violations.append({
            'type': v['type'],
            'severity': 'warning',
            'issue': v['issue'],
            'fix': v['fix']
        })

    # 3. Check if [!resources] callout exists at all
    missing_resources_violations = check_resources_required(ctx.content)
    for v in missing_resources_violations:
        state.pedagogical_violations.append({
            'type': v['type'],
            'severity': 'warning',
            'issue': v['issue'],
            'fix': v['fix']
        })

    # 4. Check if unjumble activities have matching words (jumbled words = answer words)
    unjumble_violations = check_unjumble_word_match(ctx.content)
    for v in unjumble_violations:
        state.pedagogical_violations.append({
            'type': v['type'],
            'severity': 'error',  # Blocking - unsolvable activities are critical
            'issue': v['issue'],
            'fix': v['fix']
        })

    # 5. Check activity header format (must use "## type: Title" format for MDX generation)
    header_violations = check_activity_header_format(ctx.content)
    for v in header_violations:
        state.pedagogical_violations.append({
            'type': v['type'],
            'severity': 'error',  # Blocking - activities will be silently skipped
            'issue': v['issue'],
            'fix': v['fix']
        })

    # 6. Check mark-the-words format (Issue #361: malformed (correct)/(wrong) annotations)
    for v in mark_words_violations:
        state.pedagogical_violations.append({
            'type': v['type'],
            'severity': v['severity'],
            'issue': v['issue'],
            'fix': v['fix']
        })

    # 7. Check for hints in activities (all should be removed)
    for v in hint_violations:
        state.pedagogical_violations.append({
            'type': v['type'],
            'severity': v['severity'],
            'issue': v['issue'],
            'fix': v['fix']
        })

    # 7b. Check for error-correction activities with highlighted error words
    for v in error_correction_hint_violations:
        state.pedagogical_violations.append({
            'type': v['type'],
            'severity': v['severity'],
            'issue': v['issue'],
            'fix': v['fix']
        })

    # 8. Check for malformed cloze activities (dialogue lines as blanks)
    for v in malformed_cloze_violations:
        state.pedagogical_violations.append({
            'type': v['type'],
            'severity': v['severity'],
            'issue': v['issue'],
            'fix': v['fix']
        })

    # 9. Check for cloze syntax errors (colons inside blanks)
    for v in cloze_syntax_violations:
        state.pedagogical_violations.append({
            'type': v['type'],
            'severity': v['severity'],
            'issue': v['issue'],
            'fix': v['fix']
        })

    # 10. Check for malformed error-correction activities (placeholder syntax)
    for v in error_correction_violations:
        state.pedagogical_violations.append({
            'type': v['type'],
            'severity': v['severity'],
            'issue': v['issue'],
            'fix': v['fix']
        })

    # 11. Check for invalid activity types in YAML
    for v in invalid_type_violations:
        state.pedagogical_violations.append({
            'type': v['type'],
            'severity': v['severity'],
            'issue': v['issue'],
            'fix': v['fix']
        })

    # 12. Check for YAML schema violations (Issue #397)
    for v in yaml_schema_violations:
        state.pedagogical_violations.append({
            'type': v['type'],
            'severity': v['severity'],
            'issue': v['message'],
            'fix': 'Fix the activity YAML to match the schema in schemas/activities-base.schema.json',
            'blocking': True  # Schema violations are blocking errors
        })

    # 12. Check for missing advanced activities in C1/C2
    if not ctx.skip_activities:
        advanced_presence_violations = check_advanced_activities_presence(state.found_activity_types, ctx.level_code, ctx.module_focus)
    else:
        advanced_presence_violations = []
    for v in advanced_presence_violations:
        state.pedagogical_violations.append({
            'type': v['type'],
            'severity': v['severity'],
            'blocking': v.get('blocking', True),
            'issue': v['issue'],
            'fix': v['fix']
        })


def _run_pedagogical_and_content_checks(ctx: AuditContext, state: AuditState,
                                         yaml_schema_violations: list,
                                         mark_words_violations: list,
                                         hint_violations: list,
                                         error_correction_hint_violations: list,
                                         malformed_cloze_violations: list,
                                         cloze_syntax_violations: list,
                                         error_correction_violations: list,
                                         invalid_type_violations: list) -> None:
    """Run pedagogical checks, content quality, vocabulary plan compliance, and activity violation aggregation."""
    _run_content_quality_checks(ctx, state)
    _run_activity_pedagogical_checks(
        ctx, state,
        yaml_schema_violations, mark_words_violations, hint_violations,
        error_correction_hint_violations, malformed_cloze_violations,
        cloze_syntax_violations, error_correction_violations,
        invalid_type_violations,
    )

    blocking_pedagogy = [v for v in state.pedagogical_violations if v.get('blocking', True)]
    state.results['pedagogy'] = evaluate_pedagogy(len(blocking_pedagogy))
    if state.results['pedagogy'].status == 'FAIL':
        state.has_critical_failure = True


def _evaluate_immersion(ctx: AuditContext, state: AuditState) -> tuple[float, int, int]:
    """Evaluate immersion gate and return (immersion_score, min_imm, max_imm)."""
    # Immersion (includes Activities + Summary - full learner experience)
    full_immersion_text = clean_for_immersion(ctx.body)
    immersion_score = calculate_immersion(full_immersion_text)

    # Immersion targets (phase-based for A1, A2, and B1 - check level directly)
    # CHECKPOINTS: No immersion gate - immersion should come naturally from practice
    if ctx.module_focus == 'checkpoint':
        min_imm, max_imm = 0, 100  # Skip gate - just report the value
        phase_label = " (checkpoint - no gate)"
    elif ctx.level_code == 'A1':
        min_imm, max_imm = get_a1_immersion_range(ctx.module_num)
        phase_label = f" (M{ctx.module_num:02d})"
    elif ctx.level_code == 'A2':
        min_imm, max_imm = get_a2_immersion_range(ctx.module_num)
        # Label the phase for clarity
        if ctx.module_num <= 20:
            phase_label = " (A2.1)"
        elif ctx.module_num <= 40:
            phase_label = " (A2.2)"
        else:
            phase_label = " (A2.3)"
    elif ctx.level_code == 'B1':
        min_imm, max_imm = get_b1_immersion_range(ctx.module_num)
        # Label the phase for clarity
        if ctx.module_num <= 5:
            phase_label = " (B1.0 Bridge)"
        elif ctx.module_num <= 10:
            phase_label = " (B1.1 Aspect)"
        elif ctx.module_num <= 20:
            phase_label = " (B1.2 Motion)"
        elif ctx.module_num <= 45:
            phase_label = " (B1.3-4 Complex)"
        elif ctx.module_num <= 65:
            phase_label = " (B1.5-6 Vocab)"
        else:
            phase_label = " (B1.7-8 Ukraine)"
    else:
        # B2, C1, C2 use type-based immersion from config
        min_imm = ctx.config.get('min_immersion', 0)
        max_imm = ctx.config.get('max_immersion', 100)
        phase_label = f" ({ctx.module_focus})" if ctx.module_focus else ""

    state.results['immersion'] = evaluate_immersion(immersion_score, min_imm, max_imm, phase_label)
    if state.results['immersion'].status == 'FAIL':
        state.has_critical_failure = True
        print_immersion_fix_hints(immersion_score, min_imm, max_imm, ctx.level_code, ctx.module_focus)

    # Run State Standard 2024 immersion compliance (B1+)
    if ctx.level_code in ['B1', 'B2', 'C1', 'C2']:
        immersion_violations = check_state_standard_compliance(
            ctx.level_code, ctx.module_num, ctx.content, immersion_pct=immersion_score
        )
        for violation in immersion_violations:
            state.pedagogical_violations.append({
                'type': violation.code,
                'severity': 'warning',
                'issue': violation.message,
                'fix': violation.fix
            })

    # Hard failure for very low immersion
    if immersion_score < 10.0 and ctx.module_num > 5:
        state.has_critical_failure = True

    return immersion_score, min_imm, max_imm


def _evaluate_grammar_and_naturalness(ctx: AuditContext, state: AuditState) -> None:
    """Evaluate grammar validation + naturalness check."""
    # Richness evaluation (B1+ only)
    if ctx.level_code in ('B1', 'B2', 'C1', 'C2', 'LIT'):
        # Pass YAML activity types for checkpoints so richness can count them
        yaml_activity_types = set(state.found_activity_types) if ctx.use_yaml_activities else None
        richness_result = calculate_richness_score(ctx.content, ctx.level_code, ctx.file_path, yaml_activity_types)
        richness_flags = detect_dryness_flags(ctx.content, ctx.level_code, ctx.file_path)
        state.results['richness'] = evaluate_richness(
            richness_result['score'],
            richness_result['threshold'],
            richness_result.get('module_type', 'grammar'),
            richness_flags,
        )
        if state.results['richness'].status == 'FAIL':
            # Richness is a HARD gate - fail the audit
            state.has_critical_failure = True
            print(f"\n⚠️  Richness below threshold ({richness_result['score']}% < {richness_result['threshold']}% min)")
            if richness_flags:
                print("   Dryness flags:")
                for flag in richness_flags:
                    print(f"     - {flag}")

    # Grammar validation check - look for -grammar.yaml in audit folder
    md_abs = Path(os.path.abspath(ctx.file_path))
    grammar_file = str(_grammar_path(md_abs.parent, md_abs.stem))
    # Also check legacy path (numbered stem) during transition
    if not os.path.exists(grammar_file):
        legacy_grammar = os.path.join(str(md_abs.parent), 'audit', f"{md_abs.stem}-grammar.yaml")
        if os.path.exists(legacy_grammar):
            grammar_file = legacy_grammar

    grammar_summary = None
    if os.path.exists(grammar_file):
        try:
            with open(grammar_file, encoding='utf-8') as f:
                grammar_data = yaml.safe_load(f)
                grammar_summary = grammar_data.get('summary', {})
        except Exception:
            pass

    state.results['grammar'] = evaluate_grammar(os.path.exists(grammar_file), grammar_summary)

    # Naturalness validation (Issue #415)
    # DECOMMISSIONED: Automated LLM check during audit is redundant and wastes resources.
    # Naturalness is now verified during the Phase 5 Review (review-content-v4).
    nat_score = 0
    nat_status = "PENDING"

    # Check if naturalness already evaluated in meta.yaml
    if ctx.meta_data and 'naturalness' in ctx.meta_data:
        nat_val = ctx.meta_data['naturalness']
        if isinstance(nat_val, dict):
            nat_score = nat_val.get('score', 0) or 0
            nat_status = nat_val.get('status', 'PENDING') or 'PENDING'
        elif isinstance(nat_val, (int, float)):
            nat_score = int(nat_val)
            nat_status = 'PASS' if nat_score >= 7 else 'FAIL'

    # Auto-check naturalness logic REMOVED.
    # We no longer trigger external LLM calls for naturalness during the structural audit.

    state.results['naturalness'] = evaluate_naturalness(nat_score, nat_status)
    if state.results['naturalness'].status == 'FAIL':
        state.has_critical_failure = True


def _evaluate_activity_quality_gate(ctx: AuditContext, state: AuditState) -> None:
    """Evaluate activity quality gate from quality report file."""
    md_abs = Path(os.path.abspath(ctx.file_path))
    if ctx.skip_activities:
        state.results['activity_quality'] = GateResult('INFO', '⏳', "Deferred (content-only audit)")
        return

    quality_file = str(_quality_path(md_abs.parent, md_abs.stem))
    # Also check legacy path during transition
    if not os.path.exists(quality_file):
        legacy_quality = os.path.join(str(md_abs.parent), 'audit', f"{md_abs.stem}-quality.md")
        if os.path.exists(legacy_quality):
            quality_file = legacy_quality
    quality_result = None
    quality_failed_gates = 0

    if os.path.exists(quality_file):
        try:
            with open(quality_file, encoding='utf-8') as f:
                quality_content = f.read()
                if '**Result:** ✅ PASS' in quality_content:
                    quality_result = 'PASS'
                elif '**Result:** ❌ FAIL' in quality_content:
                    quality_result = 'FAIL'
                    failed_gates_section = re.search(r'### Failed Gates\n\n(.*?)\n\n', quality_content, re.DOTALL)
                    if failed_gates_section:
                        quality_failed_gates = len(re.findall(r'^- \*\*', failed_gates_section.group(1), re.MULTILINE))
        except Exception:
            pass

    state.results['activity_quality'] = evaluate_activity_quality(
        os.path.exists(quality_file),
        quality_result,
        quality_failed_gates,
        ctx.level_code
    )


def _check_transliteration_policy(ctx: AuditContext, state: AuditState) -> None:
    """Check transliteration policy compliance."""
    transliteration_allowed = ctx.config.get('transliteration_allowed', True)
    if not transliteration_allowed:
        translit_ok = False
        if ctx.meta_data:
            if 'transliteration' not in ctx.meta_data:
                translit_ok = True
            else:
                val = ctx.meta_data['transliteration']
                translit_ok = (val is None or str(val).lower() == 'none')
        if not translit_ok:
            translit_ok = bool(re.search(r'transliteration:\s*["\']?none["\']?', ctx.frontmatter_str))
        if not translit_ok:
            print(f"❌ AUDIT FAILED: Level {ctx.level_code} forbids transliteration. Set 'transliteration: none' in frontmatter.")
            state.has_critical_failure = True

        track_for_translit = detect_track_from_path(ctx.file_path)
        is_bridge_module = (ctx.level_code == 'B1' and ctx.module_num <= 5)
        content_lines = ctx.content.split('\n')
        for line_idx, line in enumerate(content_lines):
            if '___' in line or '[___:' in line:
                continue
            if re.search(r'\((Dat|Acc|Gen|Loc|Ins|Nom|Voc)\)', line):
                continue
            translit_pattern = re.search(r'[\u0400-\u04ff]+\s*\(([A-Za-z]+)\)', line)
            if translit_pattern:
                latin_part = translit_pattern.group(1)
                if latin_part.upper() in ACADEMIC_LATIN_ALLOWLIST:
                    continue
                if is_academic_latin_context(line, content_lines, line_idx, track_for_translit):
                    continue
                if is_bridge_module:
                    continue
                print(f"❌ AUDIT FAILED: Transliteration detected: '{translit_pattern.group()}'. Remove Latin in parentheses.")
                state.has_critical_failure = True
                break


def _evaluate_richness_and_quality(ctx: AuditContext, state: AuditState) -> None:
    """Evaluate activity quality, content-heavy, and transliteration gates."""
    _evaluate_activity_quality_gate(ctx, state)

    # Content-heavy module check (B2 history, C1 literature/biography/folk/arts)
    if ctx.skip_activities:
        state.results['content_heavy'] = GateResult('INFO', '⏳', "Deferred (content-only audit)")
    else:
        is_content_heavy = is_content_heavy_module(ctx.level_code, ctx.module_num, ctx.module_focus or "")
        content_recall_violations = []
        if is_content_heavy:
            content_recall_violations = run_all_content_recall_checks(
                ctx.content, ctx.level_code, ctx.module_focus or "",
                yaml_activities=ctx.yaml_activities
            )

        min_act = ctx.config.get('min_activities', 10)
        max_act = ctx.config.get('max_activities', min_act + 4)

        state.results['content_heavy'] = evaluate_content_heavy(
            is_content_heavy,
            state.activity_count,
            content_recall_violations,
            min_act=min_act,
            max_act=max_act
        )

    # Transliteration policy
    _check_transliteration_policy(ctx, state)


def _evaluate_advanced_gates(ctx: AuditContext, state: AuditState) -> None:
    """Evaluate richness, grammar, naturalness, activity quality, content-heavy, transliteration gates."""
    _evaluate_grammar_and_naturalness(ctx, state)
    _evaluate_richness_and_quality(ctx, state)


def _print_and_save_report(ctx: AuditContext, state: AuditState,
                            immersion_score: float, min_imm: int, max_imm: int,
                            unique_types: set) -> None:
    """Print gates, violations, generate report, and save."""
    # Output
    print_gates(state.results, ctx.level_code)
    print_lint_errors(state.lint_errors)
    print_pedagogical_violations(state.pedagogical_violations)
    print_template_violations(state.template_violations)

    # Print vocab blocking errors (these fail the audit)
    if state.vocab_blocking:
        print("\n❌ MISSING CORE VOCABULARY (blocking):")
        for v in state.vocab_blocking:
            print(f"  [{v['type']}] {v['issue']}")
            print(f"     → FIX: {v['fix']}")

    # Print vocab warnings (informational only)
    if state.vocab_warnings:
        print("\n⚠️  VOCABULARY WARNINGS (informational):")
        for v in state.vocab_warnings:
            print(f"  [{v['type']}] {v['issue']}")
            print(f"     → FIX: {v['fix']}")

    # Recommendation - include all vocab issues in severity
    all_violations_for_severity = state.pedagogical_violations + state.vocab_blocking + state.vocab_warnings + state.template_violations
    recommendation, reasons, severity = compute_recommendation(
        all_violations_for_severity, state.lint_errors, state.results, immersion_score,
        min_imm, max_imm, ctx.level_code
    )
    print_recommendation(recommendation, reasons, severity)

    # Generate and save report (pedagogical, vocab, and template separated)
    all_violations_for_report = state.pedagogical_violations + state.vocab_blocking + state.vocab_warnings

    # Get richness data for report (if available)
    richness_data = None
    richness_flags_for_report = None
    if ctx.level_code in ('B1', 'B2', 'C1', 'C2', 'LIT'):
        yaml_activity_types = set(state.found_activity_types) if ctx.use_yaml_activities else None
        richness_data = calculate_richness_score(ctx.content, ctx.level_code, ctx.file_path, yaml_activity_types)
        richness_flags_for_report = detect_dryness_flags(ctx.content, ctx.level_code, ctx.file_path)

    # Get naturalness data from metadata
    naturalness_data = ctx.meta_data.get('naturalness') if ctx.meta_data else None

    report_content = generate_report(
        ctx.file_path, ctx.phase, ctx.level_code, ctx.pedagogy, ctx.target,
        state.has_critical_failure, state.results, state.table_rows,
        state.lint_errors, all_violations_for_report,
        recommendation, reasons, severity,
        state.low_density_activities,
        richness_data=richness_data,
        richness_flags=richness_flags_for_report,
        template_violations=state.template_violations,
        naturalness=naturalness_data,
        module_num=ctx.module_num,
        config=ctx.config,
        activity_details=state.activity_details,
        unique_types=unique_types,
        module_focus=ctx.module_focus,
        display_level=ctx.display_level
    )
    report_path = save_report(ctx.file_path, report_content)
    print(f"\nReport: {report_path}")


def _check_review_gaming(ctx: AuditContext, state: AuditState,
                          module_slug: str, review_violations: list,
                          review_gate_status: str) -> tuple[list, str]:
    """Run review gaming detection on the review file. Returns (updated violations, updated gate status)."""
    from slug_utils import review_path as _review_path_fn
    _review_base = Path(ctx.file_path).parent
    _review_canonical = _review_path_fn(_review_base, module_slug)
    _review_file_path = None
    if _review_canonical.exists():
        _review_file_path = _review_canonical
    else:
        _bare = to_bare_slug(module_slug)
        _legacy = _review_base / 'audit' / f'{_bare}-review.md'
        if _legacy.exists():
            _review_file_path = _legacy

    if _review_file_path:
        try:
            _review_text = _review_file_path.read_text(encoding='utf-8')
            gaming_review_violations = check_review_gaming(
                _review_text, ctx.content, ctx.file_path, ctx.level_code, module_slug
            )
            if gaming_review_violations:
                g_crits = [v for v in gaming_review_violations if v['severity'] == 'critical']
                g_warns = [v for v in gaming_review_violations if v['severity'] == 'warning']
                print(f"  🎭 Review Gaming: {len(g_crits)} critical, {len(g_warns)} warnings")
                for v in g_crits:
                    print(f"     ❌ [{v['type']}] {v['message']}")
                    state.critical_failure_reasons.append(v['message'])
                for v in g_warns:
                    print(f"     ⚠️  [{v['type']}] {v['message']}")
                review_violations.extend(gaming_review_violations)
                if g_crits and review_gate_status == "pass":
                    review_gate_status = "fail"
                    state.has_critical_failure = True
        except OSError:
            pass  # Can't read review file — skip gaming checks

    return review_violations, review_gate_status


def _validate_review_and_finalize(ctx: AuditContext, state: AuditState) -> bool:
    """Run review validation, gaming detection, save status cache, return final verdict."""
    # Review Validation (final gate — only checked if all content gates pass)
    # Skipped in content-only mode (skip_activities) because Phase D creates the review
    review_violations = []
    review_gate_status = "skipped"
    if ctx.skip_activities or ctx.skip_review:
        review_gate_status = "deferred"
    elif not state.has_critical_failure:
        module_slug_for_review = Path(ctx.file_path).stem
        review_violations = check_review_validity(ctx.file_path, ctx.level_code, module_slug_for_review)
        if review_violations:
            criticals = [v for v in review_violations if v['severity'] == 'critical']
            warnings = [v for v in review_violations if v['severity'] == 'warning']
            print(f"  🕵️  Review Validation: {len(criticals)} critical, {len(warnings)} warnings")
            for v in criticals:
                print(f"     ❌ [{v['type']}] {v['message']}")
                state.critical_failure_reasons.append(v['message'])
            for v in warnings:
                print(f"     ⚠️  [{v['type']}] {v['message']}")
            if criticals:
                review_gate_status = "fail"
                state.has_critical_failure = True
            else:
                review_gate_status = "pass"
        else:
            review_gate_status = "pass"  # No violations

        # Review Gaming Detection (Issue #610)
        review_violations, review_gate_status = _check_review_gaming(
            ctx, state, module_slug_for_review, review_violations, review_gate_status
        )
    else:
        review_gate_status = "skipped"  # Content gates failed, review not checked

    # Save Status Cache (V2 Architecture)
    try:
        module_slug = Path(ctx.file_path).stem
        plan_ver = ctx.meta_data.get('version', '2.0') if ctx.meta_data else '2.0'
        cache_path = save_status_cache(
            ctx.file_path,
            ctx.level_code,
            module_slug,
            state.results,
            state.has_critical_failure,
            state.critical_failure_reasons,
            plan_version=plan_ver,
            review_violations=review_violations,
            review_gate_status=review_gate_status,
        )
        print(f"Status: {cache_path}")
    except Exception as e:
        print(f"⚠️ Failed to save status cache: {e}")

    if state.has_critical_failure:
        print("\n❌ AUDIT FAILED. Correct errors before proceeding.")
        if state.critical_failure_reasons:
            print("\nCritical Failures:")
            for reason in state.critical_failure_reasons:
                print(f"  • {reason}")
        return False
    else:
        print("\n✅ AUDIT PASSED.")
        return True


def _generate_output_and_report(ctx: AuditContext, state: AuditState,
                                 immersion_score: float, min_imm: int, max_imm: int,
                                 unique_types: set) -> bool:
    """Print gates, generate report, run review validation, save status cache. Returns audit result."""
    _print_and_save_report(ctx, state, immersion_score, min_imm, max_imm, unique_types)
    return _validate_review_and_finalize(ctx, state)


def audit_module(file_path: str, skip_activities: bool = False,
                 skip_review: bool = False) -> bool:
    """
    Orchestrates the audit process for a single module file.
    Returns True on success, False on failure.

    Args:
        skip_activities: When True, defer activity/vocab gates (content-only audit
                         for the otaman content sprint). Deferred gates return INFO
                         status and do NOT cause critical failures.
        skip_review: When True, defer review gate only (#606). Used by the v3 audit
                     phase to validate content + activities but not the review file
                     (which Phase D creates later).
    """
    # Phase 1: Load files, parse frontmatter, detect level/config
    ctx, state = _load_and_resolve(file_path, skip_activities, skip_review)

    # Phase 2: Template compliance
    _check_template_compliance(ctx, state)

    # Phase 3: Outline, structure, tone, checkpoint validation
    structure_gate = _check_outline_and_structure(ctx, state)

    # Phase 4: Word count and engagement metrics
    _count_words_and_engagement(ctx, state)

    # Phase 5: Validate YAML activity files (schema, lint, format checks)
    (yaml_schema_violations, mark_words_violations, hint_violations,
     error_correction_hint_violations, malformed_cloze_violations,
     cloze_syntax_violations, error_correction_violations,
     invalid_type_violations, forbidden_type_violations) = _validate_yaml_activities(ctx, state)

    # Phase 6: Activity answer correctness and external URL validation
    _validate_activity_answers(ctx, state)

    # Phase 7: Process activity sections (YAML + embedded markdown)
    _process_activity_sections(ctx, state)

    # Phase 8: Evaluate core gates (words, activities, engagement, vocab, structure, persona, lint)
    unique_types = _evaluate_core_gates(ctx, state, structure_gate)

    # Phase 9: Pedagogical checks, content quality, vocabulary plan compliance
    _run_pedagogical_and_content_checks(
        ctx, state,
        yaml_schema_violations, mark_words_violations, hint_violations,
        error_correction_hint_violations, malformed_cloze_violations,
        cloze_syntax_violations, error_correction_violations,
        invalid_type_violations,
    )

    # Phase 10: Immersion evaluation
    immersion_score, min_imm, max_imm = _evaluate_immersion(ctx, state)

    # Phase 11: Advanced gates (richness, grammar, naturalness, activity quality, content-heavy, transliteration)
    _evaluate_advanced_gates(ctx, state)

    # Phase 12: Output, report generation, review validation, status cache
    return _generate_output_and_report(ctx, state, immersion_score, min_imm, max_imm, unique_types)
