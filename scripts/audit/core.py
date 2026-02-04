"""
Core audit orchestration module.

Contains the main audit_module function that coordinates all checks
and produces the final audit report.
"""

import os
import re
import sys
import yaml
from pathlib import Path

# Add project root to path for shared module imports
SCRIPT_DIR = Path(__file__).parent.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.append(str(SCRIPT_DIR))
from yaml_activities import ActivityParser, Activity

from .config import (
    LEVEL_CONFIG,
    ACTIVITY_KEYWORDS,
    CORE_KEYWORDS,
    EXCLUDE_KEYWORDS,
    VALID_ACTIVITY_TYPES,
    AI_CONTAMINATION_PATTERNS,
    REQUIRED_METADATA,
    ACTIVITY_COMPLEXITY,
    get_a1_immersion_range,
    get_a2_immersion_range,
    get_b1_immersion_range,
    get_level_config,
    get_word_target,
)
from .cleaners import (
    clean_for_stats,
    clean_for_immersion,
    extract_core_content,
    calculate_immersion,
)
from .checks import (
    run_pedagogical_checks,
    count_items,
    check_markdown_format,
    check_section_order,
    check_section_order,
    check_activity_ukrainian_content,
    check_resources_placement,
    check_resources_required,
    check_unjumble_word_match,
    check_content_quality,
    check_activity_header_format,
)
from .checks.content_purity import check_content_purity
from .checks.outline_compliance import print_section_summary
from .checks.activities import check_mark_the_words_format, check_hints_in_activities, check_error_correction_hints, check_malformed_cloze_activities, check_cloze_syntax_errors, check_error_correction_format, check_yaml_activity_types, check_advanced_activities_presence, check_forbidden_activity_types
from .checks.vocabulary_integration import check_vocabulary_integration
from .checks.activity_validation import (
    check_morpheme_patterns,
    check_morpheme_pedagogy,
    check_english_hints_in_activities,
    check_unjumble_empty_jumbled,
    check_mdx_unjumble_rendering,
    check_seminar_reading_pairing,
)
from .checks.external_resource_validation import (
    check_external_resources,
    fix_external_resource_url,
)
from .checks.meta_validator import check_seminar_meta_requirements, check_activity_hints_valid
from .checks.yaml_schema_validation import (
    check_activity_yaml_schema,
)
from .checks.yaml_lint import lint_yaml_file
from .checks.state_standard_compliance import (
    check_state_standard_compliance,
)
# Vocabulary integrity checking removed - not needed (naturalness catches bad vocabulary)
from .checks.outline_compliance import (
    check_outline_compliance,
)
from .checks.vocabulary import (
    count_vocab_rows,
    extract_vocab_items,
    extract_vocab_from_section,
    check_vocab_matches_plan,
    check_metalanguage_scaffolding,
    check_vocab_table_format,
    get_cumulative_vocab,
)
from .gates import (
    GateResult,
    evaluate_word_count,
    evaluate_activity_count,
    evaluate_density,
    evaluate_unique_types,
    evaluate_priority_types,
    evaluate_engagement,
    evaluate_audio,
    evaluate_vocab,
    evaluate_structure,
    evaluate_lint,
    evaluate_pedagogy,
    evaluate_immersion,
    evaluate_richness,
    evaluate_grammar,
    evaluate_activity_quality,
    evaluate_content_heavy,
    evaluate_naturalness,
    compute_recommendation,
)
from .checks.content_recall_detection import (
    is_content_heavy_module,
    run_all_content_recall_checks,
)

# Import richness calculation
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from calculate_richness import calculate_richness_score, detect_dryness_flags
from .report import (
    generate_report,
    save_report,
    save_status_cache,
    print_gates,
    print_lint_errors,
    print_pedagogical_violations,
    print_template_violations,
    print_recommendation,
    print_immersion_fix_hints,
    print_low_density_activities,
)


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
    track_from_path = None  # Full track name for track-aware checks (e.g., C1-BIO)
    # Match a1, a2, b1, b2, c1, c2 (case insensitive)
    # Also matches tracks like b2-hist, c1-bio, lit, oes, ruth
    path_match = re.search(r'/([abc][12])(-[a-z0-9]+)?/', file_path.lower())
    if path_match:
        base_level = path_match.group(1).upper()  # e.g., C1
        track_suffix = path_match.group(2)  # e.g., -bio or None
        level_from_path = base_level
        track_from_path = f"{base_level}{track_suffix.upper()}" if track_suffix else base_level
    else:
        # Try to match special tracks (lit, oes, ruth)
        special_match = re.search(r'/(lit|oes|ruth)/', file_path.lower())
        if special_match:
            level_from_path = special_match.group(1).upper()
            track_from_path = level_from_path

    # Use path-detected level if available
    if phase == 'LIT':
        level_code = 'LIT'
    else:
        level_code = level_from_path if level_from_path else phase.split('.')[0]

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
    except:
        pass

    return level_code, module_num, track_code


def detect_focus(frontmatter_str: str, level_code: str, module_num: int, title: str = "", file_path: str = "") -> str | None:
    """Detect module focus (grammar, vocab, checkpoint, skills, cultural, history, etc.)."""
    # Detect track directories first (b2-hist, c1-bio, c1-hist, lit)
    # These override all other detection methods
    if file_path:
        track_match = re.search(r'/([abc][12])-([a-z]+)/', file_path.lower())
        if track_match:
            track_suffix = track_match.group(2)
            if track_suffix == 'hist':
                return 'history'
            elif track_suffix == 'bio':
                return 'biography'
            elif track_suffix == 'pro':
                return 'professional'
        # LIT track
        if '/lit/' in file_path.lower():
            return 'literature'

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

def run_lint_checks(content: str, section_map: dict, module_num: int) -> list[str]:
    """Run markdown lint checks."""
    lint_errors = []
    
    # Typography Check
    lint_errors.extend(check_typography(content))
    
    lines_raw = content.split('\n')

    in_activities = False
    current_activity_type = None
    fill_in_needs_answer = False
    fill_in_has_options = False
    fill_in_item_line = 0

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
        if current_activity_type == 'anagram':
            if re.search(r'\w\s+/\s+\w\s+/', stripped):
                lint_errors.append(f"Line {line_num}: Invalid Anagram format. Use spaces (a b c), not slashes.")

        # 2. Activity YAML Check
        if in_activities:
            if stripped.startswith('type: ') or stripped.startswith('items:'):
                lint_errors.append(f"Line {line_num}: YAML detected in Activities. Use markdown.")

        # 3. Callout Check
        if "**Answer:**" in stripped or "**Option:**" in stripped:
            lint_errors.append(f"Line {line_num}: Old format detected. Use '> [!answer]'.")

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

        # 6. Explanation Check
        if '> [!explanation]' in stripped and '[!answer]' in stripped:
            lint_errors.append(f"Line {line_num}: Malformed Explanation. Contains '[!answer]' inside explanation block.")

        # 7. Checkbox Format Check
        if stripped.startswith('- ['):
            if not re.match(r'- \[[ xX]\]', stripped):
                lint_errors.append(f"Line {line_num}: Invalid Checkbox format. Use '- [ ]' or '- [x]'.")

        # 8. AI Contamination Check
        for pat in AI_CONTAMINATION_PATTERNS:
            if re.search(pat, stripped, re.IGNORECASE):
                if "Wait" in pat and "**" in stripped:
                    continue
                if "Sorry" in pat and "**" in stripped:
                    continue
                if "error-correction" in stripped.lower():
                    continue
                lint_errors.append(f"Line {line_num}: AI Contamination detected ('{pat}'). Remove thinking/self-correction artifacts.")

        # 9. Audio Artifact Check
        is_vocab_row = (stripped.startswith('|') and stripped.count('|') >= 3)
        if 'audio_' in stripped and not is_vocab_row:
            lint_errors.append(f"Line {line_num}: 'audio_' link detected outside Vocabulary Table. User Rule: Audio links only in Vocab.")

        # 10. Empty Header Check
        if re.match(r'^#+\s*$', stripped):
            lint_errors.append(f"Line {line_num}: Empty Header detected (Lonely '#'). Remove or add title.")

        # 11. True/False Strict Check
        if current_activity_type == 'true-false':
            if '> [!explanation]' in stripped:
                lint_errors.append(f"Line {line_num}: T/F Activity contains '[!explanation]'. Remove all hints/solutions.")

        # 12. Transliteration Column Check (M21+)
        # Note: Only flag "transliteration" or "translit", NOT "translation"
        if module_num >= 21:
            if '|' in stripped:
                lower_stripped = stripped.lower()
                # Check for transliteration columns but NOT translation or pronunciation (Вимова) columns
                if '| translit' in lower_stripped:
                    lint_errors.append(f"Line {line_num}: Transliteration Column detected in M{module_num} (Policy M21+: None). Remove column.")

        # 13. Hint Detection (only in Activities)
        if in_activities:
            if re.search(r'\[Hint:.*?\]', stripped, re.IGNORECASE) or re.search(r'\(Hint:.*?\)', stripped, re.IGNORECASE) or re.search(r'\bHint:', stripped, re.IGNORECASE):
                lint_errors.append(f"Line {line_num}: Activity Hint detected. Policy: Remove all hints (e.g. [Hint: ...]) from activities.")

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
    yaml_path = md_path.parent / 'meta' / (md_path.stem + '.yaml')
    if not yaml_path.exists():
        return None
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception:
        return None

def load_yaml_plan(md_file_path: str) -> dict | None:
    """Load plan data from plans directory if exists (Split Architecture)."""
    from pathlib import Path
    md_path = Path(md_file_path)
    
    # Determine level from path
    # e.g. curriculum/l2-uk-en/b1/01.md -> level=b1
    try:
        level_part = md_path.parent.name # e.g. 'b1' or 'c1' or 'lit'
        if level_part in ['a1', 'a2', 'b1', 'b2', 'c1', 'c2', 'lit', 'b2-hist', 'c1-bio', 'c1-hist']:
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
    except:
        return None

    # Construct plan path: curriculum/l2-uk-en/plans/{level}/{slug}.yaml
    # We assume 'plans' is a sibling of 'a1', 'b1', etc. if structure is standard
    # OR 'plans' is at curriculum/l2-uk-en/plans
    
    # Base is curriculum/l2-uk-en
    base_dir = md_path.parent.parent 
    plan_path = base_dir / 'plans' / level / (md_path.stem + '.yaml')
    
    if not plan_path.exists():
        return None
        
    try:
        with open(plan_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception:
        return None

def load_yaml_vocab(md_file_path: str) -> list[dict] | None:
    """Load vocabulary from YAML sidecar if exists."""
    from pathlib import Path
    md_path = Path(md_file_path)
    yaml_path = md_path.parent / 'vocabulary' / (md_path.stem + '.yaml')
    if not yaml_path.exists():
        return None
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            # Support both 'items' (legacy?) and 'vocabulary' (standard) keys
            if isinstance(data, list):
                 return data
            return data.get('vocabulary', data.get('items', []))
    except Exception:
        return None

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
    slug_variants = [module_slug]
    if re.match(r'^\d{2,3}-', module_slug):
        slug_variants.append(re.sub(r'^\d{2,3}-', '', module_slug))

    # Find curriculum.yaml
    curriculum_yaml_path = Path(file_path).parent.parent / 'curriculum.yaml'
    if not curriculum_yaml_path.exists():
        return None

    try:
        with open(curriculum_yaml_path, 'r', encoding='utf-8') as f:
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

        # Check if file is in a track directory (b2-hist, c1-bio, etc.)
        track_match = re.search(r'/([abc][12]-[a-z]+)/', file_path)
        if track_match:
            level_key = track_match.group(1)  # e.g., 'b2-hist'
        else:
            level_key = level_key_map.get(level_code, level_code.lower())

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

def audit_module(file_path: str) -> bool:
    """
    Orchestrates the audit process for a single module file.
    Returns True on success, False on failure.
    """
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.")
        sys.exit(1)

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Initialize failure tracking early (used throughout audit)
    has_critical_failure = False
    critical_failure_reasons = []

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
        for field in PLAN_FIELDS_TO_MERGE:
            if field in plan_data:
                # Allow Meta to override Plan (e.g. for refined activity_hints)
                if field not in meta_data:
                    meta_data[field] = plan_data[field]

    vocab_data = load_yaml_vocab(file_path)
    
    # Parse frontmatter
    if meta_data:
        # Reconstruct frontmatter string for validation functions that expect it
        frontmatter_str = yaml.dump(meta_data, sort_keys=False, allow_unicode=True)
        # Content is the body (file is stripped) - No frontmatter in MD, whole file is body
        body = content
        print(f"  📋 Loaded Metadata from YAML sidecar")
    else:
        frontmatter_str, body = parse_frontmatter(content)

    if not frontmatter_str:
        print("Error: No YAML frontmatter found (checked embedded and sidecar).")
        critical_failure_reasons.append("No YAML frontmatter found")
        print("\nCritical Failures:")
        for reason in critical_failure_reasons:
            print(f"  • {reason}")
        sys.exit(1)

    # Detect Metadata
    level_code, module_num, track_code = detect_level(file_path, frontmatter_str)

    # Detect full track identifier for display (e.g., "C1-BIO" instead of "C1")
    display_level = level_code
    track_match = re.search(r'/([abc][12]-[a-z]+)/', file_path.lower())
    if track_match:
        display_level = track_match.group(1).upper()  # e.g., "C1-BIO", "B2-HIST"
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
    
    # Check word target
    target = get_word_target(level_code, module_num, module_focus)
    if meta_data and meta_data.get('word_target'):
        target = meta_data['word_target']
    print(f"   File: {file_path} | Target: {target} words")

    # Required Metadata Check
    # For A1/A2 legacy, check frontmatter string. For B1+, assume YAML sidecar handles it (schema validated elsewhere)
    if not meta_data: # Only validate embedded frontmatter if no sidecar
        missing_meta = validate_required_metadata(frontmatter_str)
        if missing_meta:
            print(f"❌ AUDIT FAILED: Missing Frontmatter Fields: {', '.join(missing_meta)}")
            print("  -> These fields are REQUIRED for 'npm run generate'")
            critical_failure_reasons.append(f"Missing Frontmatter Fields: {', '.join(missing_meta)}")
            print("\nCritical Failures:")
            for reason in critical_failure_reasons:
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

    vocab_target = config.get('min_vocab', 25)
    transliteration_allowed = config.get('transliteration_allowed', True)

    # Template Compliance (Issue #398, #389) - Gradual rollout level-by-level
    TEMPLATE_COMPLIANCE_ENABLED_LEVELS = ['A1', 'A2', 'B1', 'B2', 'C1']  # All Clean MD migrated levels
    
    template_structure = None
    template_violations = []
    
    if level_code in TEMPLATE_COMPLIANCE_ENABLED_LEVELS:
        try:
            # Import template modules - use relative imports for package context
            from . import template_parser
            from .checks import template_compliance as tc_module
            
            # Construct module ID for template mapping
            # Extract full level including track suffix (b2-hist, c1-bio, lit)
            module_slug = Path(file_path).stem
            track_match = re.search(r'/([abc][12](?:-[a-z0-9]+)?|lit)/', file_path.lower())
            full_level = track_match.group(1) if track_match else level_code.lower()
            module_id_for_mapping = f"{full_level}-{module_slug}"
            
            # Resolve which template this module should follow
            meta_for_template = meta_data if meta_data else {}
            template_path = template_parser.resolve_template(module_id_for_mapping, meta_for_template)
            template_structure = template_parser.parse_template(template_path)
            
            print(f"  📋 Template: {template_path} (pedagogy: {template_structure.pedagogy})")
            
            # Run compliance checks
            template_violations = tc_module.check_template_compliance(
                content=content,
                meta=meta_for_template,
                template=template_structure
            )
            
            if template_violations:
                critical_count = sum(1 for v in template_violations if v['severity'] == 'CRITICAL')
                warning_count = sum(1 for v in template_violations if v['severity'] == 'WARNING')
                info_count = sum(1 for v in template_violations if v['severity'] == 'INFO')
                
                print(f"  ⚠️  Template violations: {critical_count} critical, {warning_count} warnings, {info_count} info")
                
                # Show first 3 violations
                for violation in template_violations[:3]:
                    severity_icon = "🔴" if violation['severity'] == 'CRITICAL' else "⚠️" if violation['severity'] == 'WARNING' else "ℹ️"
                    print(f"     {severity_icon} [{violation['type']}] {violation['issue']}")

                if critical_count > 0:
                    has_critical_failure = True
                    critical_failure_reasons.append(f"{critical_count} Critical Template Violations")
                    
        except ImportError as e:
            print(f"  ⚠️  Template compliance not available: {e}")
        except Exception as e:
            print(f"  ⚠️  Template resolution error: {e}")

    # Check outline compliance (Issue #440: structural validation)
    outline_violations = check_outline_compliance(file_path, level_code, module_num)
    if outline_violations:
        error_count = sum(1 for v in outline_violations if v['severity'] == 'error')
        warning_count = sum(1 for v in outline_violations if v['severity'] == 'warning')
        print(f"  ⚠️  Outline compliance: {error_count} errors, {warning_count} warnings")
        for v in outline_violations[:3]:  # Show first 3
            severity_icon = "❌" if v['severity'] == 'error' else "⚠️"
            print(f"     {severity_icon} [{v['type']}] {v['message'].split(chr(10))[0]}")  # First line only

        if error_count > 0:
            has_critical_failure = True
            critical_failure_reasons.append(f"{error_count} Outline Compliance Errors")

    # Show section word summary for hydration guidance
    print_section_summary(file_path, word_target=target)

    # Extract pedagogy
    pedagogy = "Not Specified"
    pedagogy_match = re.search(r'^pedagogy:\s*(.+)$', frontmatter_str, re.MULTILINE)
    if pedagogy_match:
        pedagogy = pedagogy_match.group(1).strip()

    # Parse sections
    section_map = parse_sections(body)

    # Tone validation
    tone_errors = validate_tone(content)
    if tone_errors:
        has_critical_failure = True
        for err in tone_errors:
            print(f"❌ Tone violation: {err}")
            critical_failure_reasons.append(err)

    # Summary check
    struct_flags = check_structure(content)
    has_summary = struct_flags['summary']
    has_vocab_header = struct_flags['vocab_header']
    has_vocab_table = struct_flags['vocab_table']
    has_activities_header = struct_flags['activities_header']
    has_resources_header = struct_flags['resources_header']
    
    # Sidecar Data Presence
    has_vocab_data = vocab_data is not None
    
    # Check for activities YAML
    activities_yaml_path = Path(file_path).parent / 'activities' / (Path(file_path).stem + '.yaml')
    if not activities_yaml_path.exists():
        activities_yaml_path = Path(file_path).with_suffix('.activities.yaml')
    has_activities_data = activities_yaml_path.exists()
    
    # Check for external resources in centralized YAML
    has_resources_data = False
    resources_path = Path('docs/resources/external_resources.yaml')
    if resources_path.exists():
        with resources_path.open('r', encoding='utf-8') as f:
            try:
                resources_data = yaml.safe_load(f)
                all_resources = resources_data.get('resources', {})
                module_slug = Path(file_path).stem
                has_resources_data = module_slug in all_resources or f"{level_code.lower()}-{module_slug}" in all_resources
            except Exception:
                pass

    # Metadata sidecar overrides for summary
    if meta_data and (meta_data.get('summary') or meta_data.get('description')):
        has_summary = True
        
    # Final structure evaluation (Clean MD Standard)
    # Applied to all production-ready levels that use sidecars
    is_clean_md_standard = level_code in ('A1', 'A2', 'B1', 'B2', 'C1', 'C2', 'LIT', 'OES', 'RUTH')
    
    # Clean MD Logic: headers are optional IF data exists in sidecars.
    # However, Summary (# Підсумок) is ALWAYS required in Markdown.
    
    structure_gate = evaluate_structure(
        has_summary=has_summary,
        has_vocab=has_vocab_header or has_vocab_data,
        has_vocab_table=has_vocab_table or has_vocab_data,
        has_activities=has_activities_header or has_activities_data,
        has_resources=has_resources_header or has_resources_data,
        is_a2_plus=is_clean_md_standard
    )

    if structure_gate.status == 'FAIL':
        has_critical_failure = True
        print(f"❌ Structure check failed: {structure_gate.msg}")
        critical_failure_reasons.append(f"Structure: {structure_gate.msg}")

    # Duplicate vocabulary check (B1+ should have YAML-only, not both)
    if vocab_data and level_code in ('B1', 'B2', 'C1', 'C2', 'LIT'):
        # Check if markdown also has embedded vocab table
        has_embedded_vocab = bool(re.search(r'^#\s*(Словник|Vocabulary)', content, re.MULTILINE))
        if has_embedded_vocab:
            # Check if there's actually a table after the header
            vocab_section_match = re.search(r'^#\s*(Словник|Vocabulary)\s*\n(.*?)(?=^#|\Z)', content, re.MULTILINE | re.DOTALL)
            if vocab_section_match:
                vocab_section = vocab_section_match.group(2)
                has_embedded_table = '|' in vocab_section and re.search(r'\|.*\|.*\|', vocab_section)
                if has_embedded_table:
                    print(f"⚠️  DUPLICATE VOCABULARY: Both YAML sidecar and embedded markdown table exist.")
                    print(f"   → For {level_code}+ modules, vocabulary should be YAML-only.")
                    print(f"   → Remove the '# Словник' section from the markdown file.")


    # Checkpoint format validation
    if module_focus == 'checkpoint':
        checkpoint_errors = validate_checkpoint_format(content)
        coverage_errors = validate_checkpoint_coverage(content, frontmatter_str)
        checkpoint_errors.extend(coverage_errors)
        if checkpoint_errors:
            has_critical_failure = True
            print("❌ CHECKPOINT FORMAT ERRORS:")
            for err in checkpoint_errors:
                print(f"  → {err}")
            print("  See: docs/l2-uk-en/CHECKPOINT-DESIGN-GUIDE.md")
            critical_failure_reasons.append("Checkpoint Format Errors")

    # Fill-in options check
    for title, text in section_map.items():
        if title.lower().startswith('fill-in'):
            if '> [!options]' not in text:
                print(f"❌ AUDIT FAILED: Activity '{title}' missing mandatory > [!options] block.")
                print("  -> ALL fill-in activities require explicit options/choices.")
                sys.exit(1)
            if not re.search(r'^\s*\d+\.', text, re.MULTILINE):
                print(f"❌ AUDIT FAILED: Activity '{title}' missing numbered items (1. ...).")
                print("  -> Parser requires fill-in items to be a numbered list to function.")
                sys.exit(1)

    # Extract core content
    core_content = extract_core_content(body)

    # Word count
    raw_words = len(body.split())
    core_lines = [line for line in core_content.split('\n') if not line.strip().startswith('|')]
    core_no_tables = '\n'.join(core_lines)
    core_cleaned = clean_for_stats(core_no_tables)
    total_words = len(core_cleaned.split())

    # Engagement pattern - includes B2+ history/cultural callouts
    engagement_pattern = re.compile(
        r'(>\s*[💡⚡🎬🎭📜⚔️🔗🌍🎁🗣️🏠🧭🚌🚇🎟️📱🕵️🌤️🌦️🎱🔮🇺🇦🕰️❓🛠️💂🥪🍺🛍️🏫🏥💊👵🔬🎨🔄📅🍃❄️🚂⏳📚🍲🥣🥗🥙🥚🥛🧩⚠️🛑🎯🎮🎓🔍])|'
        r'(>\s*\[!(note|tip|warning|caution|important|cultural|history-bite|myth-buster|quote|context|analysis|source|legacy|reflection|fact|culture|military|perspective|biography)\])'
    )
    engagement_count = len(engagement_pattern.findall(content))

    # Audio count
    audio_pattern = re.compile(r'\[🔊\]\(.*?\)')
    audio_count = len(audio_pattern.findall(content))

    # Process sections
    activity_count = 0
    found_activity_types = []
    valid_density_count = 0
    total_activities = 0
    table_rows = []
    low_density_activities = []  # Track activities with insufficient items
    activity_details = []  # Track ALL activities for detailed report

    print(f"\n📋 Auditing: {display_level} M{module_num:02d} — {module_title}")
    print(f"   File: {file_path} | Target: {target} words\n")

    # Check for YAML activities file using shared parser (Issue #394)
    yaml_activities = None
    # Check both new and legacy paths
    yaml_file = Path(file_path).parent / 'activities' / (Path(file_path).stem + '.yaml')
    if not yaml_file.exists():
        yaml_file = Path(file_path).with_suffix('.activities.yaml')
        
    if yaml_file.exists():
        parser = ActivityParser()
        try:
            yaml_activities = parser.parse(yaml_file)
        except Exception as e:
            print(f"  ❌ Error parsing YAML activities: {e}")
            
    use_yaml_activities = yaml_activities is not None

    # Check YAML schema compliance (Issue #397: validate all activity types)
    yaml_schema_violations = []
    
    # Pre-parse Linting (Issue #403)
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
        yaml_schema_violations = check_activity_yaml_schema(file_path, level_code, module_num)
        if yaml_schema_violations:
            print(f"  ❌ YAML schema violations: {len(yaml_schema_violations)}")
            for v in yaml_schema_violations:
                severity_icon = "❌" if v['severity'] == 'error' else "⚠️"
                print(f"     {severity_icon} [{v['type']}] {v['message']}")

        # Vocabulary integrity checking removed - naturalness gate catches bad vocabulary
    # Check mark-the-words format (Issue #361: prevent (correct)/(wrong) annotations)
    mark_words_violations = []
    if yaml_activities:
        mark_words_violations = check_mark_the_words_format(yaml_activities)
        if mark_words_violations:
            print(f"  ⚠️  mark-the-words format violations: {len(mark_words_violations)}")
            for v in mark_words_violations:
                print(f"     → {v['issue']}")

    # Check for hints in activities (all should be removed)
    hint_violations = []
    if yaml_activities:
        hint_violations = check_hints_in_activities(yaml_activities)
        if hint_violations:
            print(f"  ⚠️  hint violations: {len(hint_violations)}")
            for v in hint_violations:
                print(f"     → {v['issue']}")

    # Check for error-correction activities with highlighted error words
    error_correction_hint_violations = []
    if yaml_activities:
        error_correction_hint_violations = check_error_correction_hints(yaml_activities)
        if error_correction_hint_violations:
            print(f"  ❌  error-correction hint violations: {len(error_correction_hint_violations)}")
            for v in error_correction_hint_violations:
                print(f"     → {v['issue']}")
                print(f"     Fix: {v['fix']}")

    # Check for malformed cloze activities (dialogue lines as blanks)
    malformed_cloze_violations = []
    if yaml_activities:
        malformed_cloze_violations = check_malformed_cloze_activities(yaml_activities)
        if malformed_cloze_violations:
            print(f"  ⚠️  malformed cloze violations: {len(malformed_cloze_violations)}")
            for v in malformed_cloze_violations:
                print(f"     → {v['issue']}")

    # Check for cloze syntax errors (colons inside blanks)
    cloze_syntax_violations = []
    if yaml_activities:
        cloze_syntax_violations = check_cloze_syntax_errors(yaml_activities)
        if cloze_syntax_violations:
            print(f"  ⚠️  cloze syntax violations: {len(cloze_syntax_violations)}")
            for v in cloze_syntax_violations:
                print(f"     → {v['issue']}")

    # Check for malformed error-correction activities (placeholder syntax)
    error_correction_violations = []
    if yaml_activities:
        error_correction_violations = check_error_correction_format(yaml_activities)
        if error_correction_violations:
            print(f"  ⚠️  malformed error-correction violations: {len(error_correction_violations)}")
            for v in error_correction_violations:
                print(f"     → {v['issue']}")

    # Check for invalid activity types in YAML
    invalid_type_violations = []
    if yaml_activities:
        invalid_type_violations = check_yaml_activity_types(yaml_activities)
        if invalid_type_violations:
            print(f"  ⚠️  invalid activity types in YAML: {len(invalid_type_violations)}")
            for v in invalid_type_violations:
                print(f"     → {v['issue']}")

    # Check for forbidden activity types (seminar tracks)
    forbidden_type_violations = []
    if yaml_activities:
        forbidden_type_violations = check_forbidden_activity_types(yaml_activities, level_code, module_focus)
        if forbidden_type_violations:
            print(f"  🔴 FORBIDDEN activity types in seminar track: {len(forbidden_type_violations)}")
            for v in forbidden_type_violations:
                print(f"     → {v['issue']}")
                print(f"        Fix: {v['fix']}")
            has_critical_failure = True
            critical_failure_reasons.append(f"{len(forbidden_type_violations)} forbidden activity types (use --fix to remove)")

    # Check morpheme patterns (Issue #363: validate *morpheme*word patterns)
    morpheme_violations = []
    if yaml_activities:
        morpheme_violations = check_morpheme_patterns(yaml_activities)
        if morpheme_violations:
            print(f"  ⚠️  morpheme pattern violations: {len(morpheme_violations)}")
            for v in morpheme_violations:
                print(f"     → {v['activity']}: {v['message']}")

    # Check morpheme pedagogy (detect vague/weak morpheme activities)
    morpheme_pedagogy_violations = []
    if yaml_activities:
        morpheme_pedagogy_violations = check_morpheme_pedagogy(yaml_activities)
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
    english_hint_violations = []
    if yaml_activities:
        english_hint_violations = check_english_hints_in_activities(yaml_activities, level_code, module_num)
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
    unjumble_violations = []
    if yaml_activities:
        unjumble_violations = check_unjumble_empty_jumbled(yaml_activities)
        if unjumble_violations:
            print(f"  ⚠️  unjumble activities with empty jumbled fields: {len(unjumble_violations)}")
            for v in unjumble_violations:
                severity = "🔴" if v['severity'] == 'critical' else "⚠️"
                print(f"     {severity} [{v['type']}] {v['activity']}")
                print(f"        Issue: {v['message']}")
                print(f"        Fix: {v['suggestion']}")

    # Check for reading-analysis pairing in seminar tracks (Issue #425)
    seminar_pairing_violations = []
    if yaml_activities:
        seminar_pairing_violations = check_seminar_reading_pairing(yaml_activities, level_code)
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
                has_critical_failure = True

    # Check external resource URLs in reading activities (Issue #430)
    external_url_violations = []
    if yaml_activities and level_code.lower() in ['lit', 'b2-hist', 'c1-hist', 'c1-bio']:
        external_url_violations = check_external_resources(yaml_activities, module_title)
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
                    if yaml_file and v.get('suggested_url'):
                        if fix_external_resource_url(yaml_file, v['url'], v['suggested_url']):
                            print(f"        ✓ AUTO-FIXED: URL updated in {yaml_file.name}")
                        else:
                            print(f"        Fix: {v['suggestion']}")
                else:
                    print(f"        Fix: {v['suggestion']}")
            # External URL mismatches are critical
            has_critical_failure = True

    # LLM review files removed (Issue #430 superseded)
    # Validation happens during /review-content, not via separate files

    if use_yaml_activities:
        print(f"  📋 Found YAML activities file ({len(yaml_activities)} activities)")
        # Process YAML activities
        for activity in yaml_activities:
            act_type = activity.type.lower()
            if act_type in VALID_ACTIVITY_TYPES or act_type.replace('-', '') in [t.replace('-', '') for t in VALID_ACTIVITY_TYPES]:
                activity_count += 1
                total_activities += 1
                found_activity_types.append(act_type)

                # Use shared count_items (Issue #394)
                items = count_items('', activity)
                density_target = config['min_items_per_activity']
                if act_type in ACTIVITY_COMPLEXITY:
                    # Try specific key first (e.g. B2-history)
                    specific_key = f"{level_code}-{module_focus}" if module_focus else level_code
                    complexity_rules = ACTIVITY_COMPLEXITY[act_type].get(specific_key)

                    # Fallback to base level key (e.g. B2)
                    if not complexity_rules:
                        complexity_rules = ACTIVITY_COMPLEXITY[act_type].get(level_code, {})

                    if 'min_items' in complexity_rules:
                        density_target = complexity_rules['min_items']

                # Track ALL activity details for report
                activity_details.append({
                    'title': getattr(activity, 'title', act_type),
                    'type': act_type,
                    'items': items,
                    'target': density_target,
                    'status': '✅' if items >= density_target else '❌'
                })

                if items >= density_target:
                    valid_density_count += 1
                else:
                    low_density_activities.append({
                        'title': getattr(activity, 'title', act_type),
                        'type': act_type,
                        'items': items,
                        'target': density_target
                    })

                print(f"  > {getattr(activity, 'title', act_type)}: {items} items (min {density_target})")

    for title, text in section_map.items():
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
            found_activity_types.append(matched_act_type)

        if not is_activity:
            for exc in EXCLUDE_KEYWORDS:
                if exc in title_lower:
                    is_excluded = True
                    break

            if not is_excluded:
                for core in CORE_KEYWORDS:
                    if core in title_lower:
                        is_core = True
                        break
                if title == 'Intro/Narrative':
                    is_core = True

        cleaned_stats = clean_for_stats(text)
        count = len(cleaned_stats.split())

        status_icon = "⚪️"
        note = "Skipped"

        if is_activity and not use_yaml_activities:
            # Only count embedded MD activities if no YAML file
            activity_count += 1
            total_activities += 1

            items = count_items(text)
            # Use activity-specific minimum from complexity config if available
            density_target = config['min_items_per_activity']
            if matched_act_type in ACTIVITY_COMPLEXITY:
                 complexity_rules = ACTIVITY_COMPLEXITY[matched_act_type].get(level_code, {})
                 if 'min_items' in complexity_rules:
                     density_target = complexity_rules['min_items']

            # Track ALL activity details for report
            activity_details.append({
                'title': title,
                'type': matched_act_type,
                'items': items,
                'target': density_target,
                'status': '✅' if items >= density_target else '❌'
            })

            if items >= density_target:
                valid_density_count += 1
            else:
                # Track low density activities for reporting
                low_density_activities.append({
                    'title': title,
                    'type': matched_act_type,
                    'items': items,
                    'target': density_target
                })

            status_icon = "🎮"
            note = f"Activity ({items} items, min {density_target})"
            print(f"  > {title}: {items} items (min {density_target})")
            display_count = items

        elif is_activity and use_yaml_activities:
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

        table_rows.append(f"| **{title}** | {status_icon} | {display_count} | {note} |")

    # Evaluate gates
    results = {}

    results['words'] = evaluate_word_count(total_words, target, raw_words)
    if results['words'].status == 'FAIL':
        has_critical_failure = True

    act_target = config['min_activities']
    results['activities'] = evaluate_activity_count(activity_count, act_target)
    if results['activities'].status == 'FAIL':
        has_critical_failure = True

    failed_density = total_activities - valid_density_count
    dens_threshold = config['min_items_per_activity']
    results['density'] = evaluate_density(failed_density, total_activities, dens_threshold, act_target)
    if results['density'].status == 'FAIL' and act_target > 0:
        has_critical_failure = True
        # Print which activities need more items
        print_low_density_activities(low_density_activities)

    unique_types = set(found_activity_types)
    type_target = config['min_types_unique']
    results['unique_types'] = evaluate_unique_types(len(unique_types), type_target)
    if results['unique_types'].status == 'FAIL':
        has_critical_failure = True

    results['priority'] = evaluate_priority_types(unique_types, config['priority_types'])
    if results['priority'].status == 'FAIL':
        has_critical_failure = True

    # Check required_types (from meta.yaml activity_hints)
    required_types = config.get('required_types', set())
    if required_types:
        missing_required = required_types - unique_types
        if missing_required:
            has_critical_failure = True
            critical_failure_reasons.append(
                f"Missing required activity types: {', '.join(sorted(missing_required))}"
            )
            print(f"  ❌ Missing required activity types from meta.yaml: {', '.join(sorted(missing_required))}")

    eng_target = config.get('min_engagement', 3)
    results['engagement'] = evaluate_engagement(engagement_count, eng_target)
    if results['engagement'].status == 'FAIL':
        has_critical_failure = True

    results['audio'] = evaluate_audio(audio_count)

    results['audio'] = evaluate_audio(audio_count)

    if vocab_data:
        vocab_count = len(vocab_data)
    else:
        vocab_count = count_vocab_rows(content)
        
    results['vocab'] = evaluate_vocab(vocab_count, vocab_target)
    # Note: vocab_count is a soft target (Issue #340) - don't fail audit

    # If using YAML sidecar for vocab, we assume "table format" is "handled by schema",
    # but we still want to check if the Markdown *links* or *displays* it... 
    # Actually, the Markdown file doesn't display it anymore. generate_mdx injects it.
    # So we pass structure check if vocab_data exists.
    if vocab_data:
        has_vocab = True
        has_vocab_table = True
    else:
        # Use flags already calculated above
        has_vocab = has_vocab_header
        has_vocab_table = has_vocab_table

    results['structure'] = structure_gate
    if results['structure'].status == 'FAIL':
        has_critical_failure = True

    # Run lint checks
    lint_errors = run_lint_checks(content, section_map, module_num)
    results['lint'] = evaluate_lint(len(lint_errors))
    if results['lint'].status == 'FAIL':
        has_critical_failure = True

    # Run Meta YAML requirements check (Seminar modules)
    meta_violations = check_seminar_meta_requirements(meta_data, level_code, pedagogy)

    # Run activity type validation for ALL modules with meta.yaml
    activity_type_violations = check_activity_hints_valid(meta_data)
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
            has_critical_failure = True

    # Run pedagogical checks (with context-specific complexity)
    pedagogical_violations = run_pedagogical_checks(
        content, core_content, level_code, module_num, pedagogy, yaml_activities, module_focus
    )
    
    # Add meta violations to pedagogical violations for reporting
    for v in meta_violations:
        pedagogical_violations.append({
            'type': v['type'],
            'severity': 'error' if v['severity'] == 'critical' else 'warning',
            'issue': v['message'],
            'fix': v.get('fix', '')
        })

    # Run State Standard 2024 compliance checks
    # Note: immersion_score calculated later in the audit, so pass None here
    # Immersion compliance will be checked separately after immersion calculation
    state_standard_violations = check_state_standard_compliance(
        level_code, module_num, content, immersion_pct=None
    )
    for violation in state_standard_violations:
        pedagogical_violations.append({
            'type': violation.code,
            'severity': 'blocking',
            'issue': violation.message,
            'fix': violation.fix
        })

    # Run vocabulary integration checks (Issue #395)
    integration_data = check_vocabulary_integration(content, level_code, module_num, yaml_activities)
    if integration_data['total'] > 0:
        print(f"  📊 Vocabulary Integration: Lesson {integration_data['lesson_rate']:.1f}%, Activities {integration_data['activity_rate']:.1f}%")
        
        # Add violations if below thresholds
        if integration_data['lesson_rate'] < 50:
            pedagogical_violations.append({
                'type': 'LOW_LESSON_INTEGRATION',
                'severity': 'warning',
                'issue': f"Only {integration_data['lesson_rate']:.1f}% of core vocabulary used in lesson text.",
                'fix': f"Use more core words in the prose: {', '.join(integration_data['missing'][:5])}..."
            })
        if integration_data['activity_rate'] < 80:
            pedagogical_violations.append({
                'type': 'LOW_ACTIVITY_INTEGRATION',
                'severity': 'warning',
                'issue': f"Only {integration_data['activity_rate']:.1f}% of core vocabulary used in activities.",
                'fix': f"Add activities using: {', '.join(integration_data['missing'][:5])}..."
            })

    # Run vocabulary plan compliance checks
    # VOCAB_PLAN_MISSING is NON-BLOCKING (Issue #387) - shown as warning only
    if vocab_data:
        # Extract set of words from vocab_data dicts
        vocab_words = set()
        for item in vocab_data:
            uk = item.get('lemma', '') # YAML schema uses 'lemma'
            if uk: vocab_words.add(uk.lower())
    else:
        vocab_words = extract_vocab_from_section(content)

    # Only check vocab plan for A1/A2 - B1+ uses separate vocabulary YAML files
    if level_code.upper() in ('A1', 'A2'):
        plan_violations = check_vocab_matches_plan(
            file_path, level_code, module_num, vocab_words
        )

        # Separate blocking violations (missing core vocab) from warnings
        vocab_blocking = [v for v in plan_violations if v.get('blocking', True)]
        vocab_warnings = [v for v in plan_violations if not v.get('blocking', True)]

        # Missing core vocab is a blocking failure
        if vocab_blocking:
            has_critical_failure = True
    else:
        vocab_blocking = []
        vocab_warnings = []

    # Run metalanguage scaffolding check
    cumulative_vocab = get_cumulative_vocab(level_code, module_num - 1)
    metalang_violations = check_metalanguage_scaffolding(
        content, vocab_words, level_code, module_num, cumulative_vocab
    )
    pedagogical_violations.extend(metalang_violations)

    # Run markdown format checks (pass track_code for track-aware checks like heading levels)
    markdown_violations = check_markdown_format(content, track_code)
    pedagogical_violations.extend(markdown_violations)

    # Run vocabulary table format checks
    if not vocab_data:
        vocab_format_violations = check_vocab_table_format(content, level_code)
        pedagogical_violations.extend(vocab_format_violations)

    # Run section order checks
    section_order_violations = check_section_order(content)
    for v in section_order_violations:
        pedagogical_violations.append({
            'type': v['type'].upper(),
            'severity': v['severity'],
            'issue': v['message'],
            'fix': f"Reorder sections to: Summary → Activities → Self-Assessment → External → Vocabulary",
            'line': v.get('line', 0)
        })
    
    # Run content quality checks (LLM-based + deterministic purity checks)
    content_quality_violations = check_content_quality(content, level_code, module_num, file_path)
    
    # Run content purity checks (Redundancy, Roboticness, Mirroring)
    yaml_content_str = ""
    if yaml_file.exists():
        yaml_content_str = yaml_file.read_text(encoding='utf-8')
    purity_violations = check_content_purity(content, yaml_content_str)
    
    if purity_violations:
        print(f"  ✨ Purity violations found: {len(purity_violations)}")
        for v in purity_violations:
            print(f"     ❌ [{v['type']}] {v['issue']}")
            
        content_quality_violations.extend(purity_violations)
            
    
            
    # Convert purity violations to standard pedagogical violations for reporting
    for v in content_quality_violations:
        pedagogical_violations.append({
            'type': v['type'],
            'severity': v['severity'],
            'issue': v['issue'],
            'fix': v['fix']
        })

    # Run activity content checks (Issue #235)
    # 1. Check if activities contain Ukrainian content (not just English)
    ukrainian_content_violations = check_activity_ukrainian_content(content, level_code)
    for v in ukrainian_content_violations:
        pedagogical_violations.append({
            'type': v['type'],
            'severity': 'error',
            'issue': v['issue'],
            'fix': v['fix']
        })
    
    # 2. Check if [!resources] callout appears before Activities section
    resources_violations = check_resources_placement(content)
    for v in resources_violations:
        pedagogical_violations.append({
            'type': v['type'],
            'severity': 'warning',
            'issue': v['issue'],
            'fix': v['fix']
        })
    
    # 3. Check if [!resources] callout exists at all
    missing_resources_violations = check_resources_required(content)
    for v in missing_resources_violations:
        pedagogical_violations.append({
            'type': v['type'],
            'severity': 'warning',
            'issue': v['issue'],
            'fix': v['fix']
        })

    # 4. Check if unjumble activities have matching words (jumbled words = answer words)
    unjumble_violations = check_unjumble_word_match(content)
    for v in unjumble_violations:
        pedagogical_violations.append({
            'type': v['type'],
            'severity': 'error',  # Blocking - unsolvable activities are critical
            'issue': v['issue'],
            'fix': v['fix']
        })

    # 5. Check activity header format (must use "## type: Title" format for MDX generation)
    header_violations = check_activity_header_format(content)
    for v in header_violations:
        pedagogical_violations.append({
            'type': v['type'],
            'severity': 'error',  # Blocking - activities will be silently skipped
            'issue': v['issue'],
            'fix': v['fix']
        })

    # 6. Check mark-the-words format (Issue #361: malformed (correct)/(wrong) annotations)
    for v in mark_words_violations:
        pedagogical_violations.append({
            'type': v['type'],
            'severity': v['severity'],
            'issue': v['issue'],
            'fix': v['fix']
        })

    # 7. Check for hints in activities (all should be removed)
    for v in hint_violations:
        pedagogical_violations.append({
            'type': v['type'],
            'severity': v['severity'],
            'issue': v['issue'],
            'fix': v['fix']
        })

    # 7b. Check for error-correction activities with highlighted error words
    for v in error_correction_hint_violations:
        pedagogical_violations.append({
            'type': v['type'],
            'severity': v['severity'],
            'issue': v['issue'],
            'fix': v['fix']
        })

    # 8. Check for malformed cloze activities (dialogue lines as blanks)
    for v in malformed_cloze_violations:
        pedagogical_violations.append({
            'type': v['type'],
            'severity': v['severity'],
            'issue': v['issue'],
            'fix': v['fix']
        })

    # 9. Check for cloze syntax errors (colons inside blanks)
    for v in cloze_syntax_violations:
        pedagogical_violations.append({
            'type': v['type'],
            'severity': v['severity'],
            'issue': v['issue'],
            'fix': v['fix']
        })

    # 10. Check for malformed error-correction activities (placeholder syntax)
    for v in error_correction_violations:
        pedagogical_violations.append({
            'type': v['type'],
            'severity': v['severity'],
            'issue': v['issue'],
            'fix': v['fix']
        })

    # 11. Check for invalid activity types in YAML
    for v in invalid_type_violations:
        pedagogical_violations.append({
            'type': v['type'],
            'severity': v['severity'],
            'issue': v['issue'],
            'fix': v['fix']
        })

    # 12. Check for YAML schema violations (Issue #397)
    for v in yaml_schema_violations:
        pedagogical_violations.append({
            'type': v['type'],
            'severity': v['severity'],
            'issue': v['message'],
            'fix': 'Fix the activity YAML to match the schema in schemas/activities-base.schema.json',
            'blocking': True  # Schema violations are blocking errors
        })

    # 12. Check for missing advanced activities in C1/C2
    advanced_presence_violations = check_advanced_activities_presence(found_activity_types, level_code, module_focus)
    for v in advanced_presence_violations:
        pedagogical_violations.append({
            'type': v['type'],
            'severity': v['severity'],
            'blocking': v.get('blocking', True),
            'issue': v['issue'],
            'fix': v['fix']
        })

    blocking_pedagogy = [v for v in pedagogical_violations if v.get('blocking', True)]
    results['pedagogy'] = evaluate_pedagogy(len(blocking_pedagogy))
    if results['pedagogy'].status == 'FAIL':
        has_critical_failure = True

    # Immersion (includes Activities + Summary - full learner experience)
    full_immersion_text = clean_for_immersion(body)
    immersion_score = calculate_immersion(full_immersion_text)

    # Immersion targets (phase-based for A1, A2, and B1 - check level directly)
    # CHECKPOINTS: No immersion gate - immersion should come naturally from practice
    if module_focus == 'checkpoint':
        min_imm, max_imm = 0, 100  # Skip gate - just report the value
        phase_label = " (checkpoint - no gate)"
    elif level_code == 'A1':
        min_imm, max_imm = get_a1_immersion_range(module_num)
        phase_label = f" (M{module_num:02d})"
    elif level_code == 'A2':
        min_imm, max_imm = get_a2_immersion_range(module_num)
        # Label the phase for clarity
        if module_num <= 20:
            phase_label = " (A2.1)"
        elif module_num <= 40:
            phase_label = " (A2.2)"
        else:
            phase_label = " (A2.3)"
    elif level_code == 'B1':
        min_imm, max_imm = get_b1_immersion_range(module_num)
        # Label the phase for clarity
        if module_num <= 10:
            phase_label = " (B1.1 Aspect)"
        elif module_num <= 20:
            phase_label = " (B1.2 Motion)"
        elif module_num <= 45:
            phase_label = " (B1.3-4 Complex)"
        elif module_num <= 65:
            phase_label = " (B1.5-6 Vocab)"
        else:
            phase_label = " (B1.7-8 Ukraine)"
    else:
        # B2, C1, C2 use type-based immersion from config
        min_imm = config.get('min_immersion', 0)
        max_imm = config.get('max_immersion', 100)
        phase_label = f" ({module_focus})" if module_focus else ""

    results['immersion'] = evaluate_immersion(immersion_score, min_imm, max_imm, phase_label)
    if results['immersion'].status == 'FAIL':
        has_critical_failure = True
        print_immersion_fix_hints(immersion_score, min_imm, max_imm, level_code, module_focus)

    # Run State Standard 2024 immersion compliance (B1+)
    if level_code in ['B1', 'B2', 'C1', 'C2']:
        immersion_violations = check_state_standard_compliance(
            level_code, module_num, content, immersion_pct=immersion_score
        )
        for violation in immersion_violations:
            pedagogical_violations.append({
                'type': violation.code,
                'severity': 'warning',
                'issue': violation.message,
                'fix': violation.fix
            })

    # Hard failure for very low immersion
    if immersion_score < 10.0 and module_num > 5:
        has_critical_failure = True

    # Richness evaluation (B1+ only)
    if level_code in ('B1', 'B2', 'C1', 'C2', 'LIT'):
        # Pass YAML activity types for checkpoints so richness can count them
        yaml_activity_types = set(found_activity_types) if use_yaml_activities else None
        richness_result = calculate_richness_score(content, level_code, file_path, yaml_activity_types)
        richness_flags = detect_dryness_flags(content, level_code, file_path)
        results['richness'] = evaluate_richness(
            richness_result['score'],
            richness_result['threshold'],
            richness_result.get('module_type', 'grammar'),
            richness_flags,
        )
        if results['richness'].status == 'FAIL':
            # Richness is a HARD gate - fail the audit
            has_critical_failure = True
            print(f"\n⚠️  Richness below threshold ({richness_result['score']}% < {richness_result['threshold']}% min)")
            if richness_flags:
                print("   Dryness flags:")
                for flag in richness_flags:
                    print(f"     - {flag}")

    # Grammar validation check - look for -grammar.yaml in audit folder
    file_dir = os.path.dirname(os.path.abspath(file_path))
    file_name = os.path.basename(file_path)
    base_name = os.path.splitext(file_name)[0]
    audit_dir = os.path.join(file_dir, 'audit')
    grammar_file = os.path.join(audit_dir, f"{base_name}-grammar.yaml")

    grammar_summary = None
    if os.path.exists(grammar_file):
        try:
            with open(grammar_file, 'r', encoding='utf-8') as f:
                grammar_data = yaml.safe_load(f)
                grammar_summary = grammar_data.get('summary', {})
        except Exception:
            pass

    results['grammar'] = evaluate_grammar(os.path.exists(grammar_file), grammar_summary)

    # Naturalness validation (Issue #415)
    nat_score = 0
    nat_status = "PENDING"

    # Check if naturalness already evaluated in meta.yaml
    if meta_data and 'naturalness' in meta_data:
        nat_score = meta_data['naturalness'].get('score', 0)
        nat_status = meta_data['naturalness'].get('status', 'PENDING')

    # Auto-check naturalness via Gemini if PENDING and --naturalness flag provided
    # Or if environment variable AUDIT_AUTO_NATURALNESS=1
    auto_naturalness = os.environ.get('AUDIT_AUTO_NATURALNESS', '0') == '1'
    if nat_status == "PENDING" and auto_naturalness:
        try:
            from .naturalness_check import check_naturalness
            nat_score, nat_status = check_naturalness(file_path, update_meta=True)
        except Exception as e:
            print(f"  ⚠️ Auto naturalness check failed: {e}")

    results['naturalness'] = evaluate_naturalness(nat_score, nat_status)
    if results['naturalness'].status == 'FAIL':
        has_critical_failure = True

    # Activity quality validation check - look for -quality.md in audit folder
    quality_file = os.path.join(audit_dir, f"{base_name}-quality.md")
    quality_result = None
    quality_failed_gates = 0

    if os.path.exists(quality_file):
        try:
            with open(quality_file, 'r', encoding='utf-8') as f:
                quality_content = f.read()
                # Parse result from report (look for "**Result:** ✅ PASS" or "**Result:** ❌ FAIL")
                if '**Result:** ✅ PASS' in quality_content:
                    quality_result = 'PASS'
                elif '**Result:** ❌ FAIL' in quality_content:
                    quality_result = 'FAIL'
                    # Count failed gates from "### Failed Gates" section
                    # Each failed gate is listed as "- **dimension:**"
                    failed_gates_section = re.search(r'### Failed Gates\n\n(.*?)\n\n', quality_content, re.DOTALL)
                    if failed_gates_section:
                        # Count bullet points in the failed gates section
                        quality_failed_gates = len(re.findall(r'^- \*\*', failed_gates_section.group(1), re.MULTILINE))
        except Exception:
            pass

    results['activity_quality'] = evaluate_activity_quality(
        os.path.exists(quality_file),
        quality_result,
        quality_failed_gates,
        level_code
    )

    # Content-heavy module check (B2 history, C1 literature/biography/folk/arts)
    is_content_heavy = is_content_heavy_module(level_code, module_num, module_focus or "")
    content_recall_violations = []
    if is_content_heavy:
        # Run all content recall checks (quiz patterns, fill-in years, cloze years)
        # Pass YAML activities if available for YAML-based detection
        content_recall_violations = run_all_content_recall_checks(
            content, level_code, module_focus or "",
            yaml_activities=yaml_activities
        )
    
    # Calculate limits for content-heavy gate
    min_act = config.get('min_activities', 10)
    # Use max_activities from config if available (e.g. LIT: 6), otherwise default buffer
    max_act = config.get('max_activities', min_act + 4)

    results['content_heavy'] = evaluate_content_heavy(
        is_content_heavy,
        activity_count,
        content_recall_violations,
        min_act=min_act,
        max_act=max_act
    )

    # Transliteration policy
    if not transliteration_allowed:
        if not re.search(r'transliteration:\s*["\']?none["\']?', frontmatter_str):
            print(f"❌ AUDIT FAILED: Level {level_code} forbids transliteration. Set 'transliteration: none' in frontmatter.")
            has_critical_failure = True

        for line in content.split('\n'):
            if '___' in line or '[___:' in line:
                continue
            if re.search(r'\((Dat|Acc|Gen|Loc|Ins|Nom|Voc)\)', line):
                continue
            translit_pattern = re.search(r'[\u0400-\u04ff]+\s*\([A-Za-z]+\)', line)
            if translit_pattern:
                print(f"❌ AUDIT FAILED: Transliteration detected: '{translit_pattern.group()}'. Remove Latin in parentheses.")
                has_critical_failure = True
                break

    # Output
    print_gates(results, level_code)
    print_lint_errors(lint_errors)
    print_pedagogical_violations(pedagogical_violations)
    print_template_violations(template_violations)

    # Print vocab blocking errors (these fail the audit)
    if vocab_blocking:
        print("\n❌ MISSING CORE VOCABULARY (blocking):")
        for v in vocab_blocking:
            print(f"  [{v['type']}] {v['issue']}")
            print(f"     → FIX: {v['fix']}")

    # Print vocab warnings (informational only)
    if vocab_warnings:
        print("\n⚠️  VOCABULARY WARNINGS (informational):")
        for v in vocab_warnings:
            print(f"  [{v['type']}] {v['issue']}")
            print(f"     → FIX: {v['fix']}")

    # Recommendation - include all vocab issues in severity
    all_violations_for_severity = pedagogical_violations + vocab_blocking + vocab_warnings + template_violations
    recommendation, reasons, severity = compute_recommendation(
        all_violations_for_severity, lint_errors, results, immersion_score,
        min_imm, max_imm, level_code
    )
    print_recommendation(recommendation, reasons, severity)

    # Generate and save report (pedagogical, vocab, and template separated)
    all_violations_for_report = pedagogical_violations + vocab_blocking + vocab_warnings

    # Get richness data for report (if available)
    richness_data = None
    richness_flags_for_report = None
    if level_code in ('B1', 'B2', 'C1', 'C2', 'LIT'):
        yaml_activity_types = set(found_activity_types) if use_yaml_activities else None
        richness_data = calculate_richness_score(content, level_code, file_path, yaml_activity_types)
        richness_flags_for_report = detect_dryness_flags(content, level_code, file_path)

    # Get naturalness data from metadata
    naturalness_data = meta_data.get('naturalness') if meta_data else None

    report_content = generate_report(
        file_path, phase, level_code, pedagogy, target,
        has_critical_failure, results, table_rows,
        lint_errors, all_violations_for_report,
        recommendation, reasons, severity,
        low_density_activities,
        richness_data=richness_data,
        richness_flags=richness_flags_for_report,
        template_violations=template_violations,
        naturalness=naturalness_data,
        module_num=module_num,
        config=config,
        activity_details=activity_details,
        unique_types=unique_types,
        module_focus=module_focus,
        display_level=display_level
    )
    report_path = save_report(file_path, report_content)
    print(f"\nReport: {report_path}")

    # Save Status Cache (V2 Architecture)
    try:
        module_slug = Path(file_path).stem
        plan_ver = meta_data.get('version', '2.0') if meta_data else '2.0'
        cache_path = save_status_cache(
            file_path, 
            level_code, 
            module_slug, 
            results, 
            has_critical_failure, 
            critical_failure_reasons,
            plan_version=plan_ver
        )
        print(f"Status: {cache_path}")
    except Exception as e:
        print(f"⚠️ Failed to save status cache: {e}")

    if has_critical_failure:
        print("\n❌ AUDIT FAILED. Correct errors before proceeding.")
        if critical_failure_reasons:
            print("\nCritical Failures:")
            for reason in critical_failure_reasons:
                print(f"  • {reason}")
        return False
    else:
        print("\n✅ AUDIT PASSED.")
        return True
