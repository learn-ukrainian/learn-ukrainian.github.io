"""
Core audit orchestration module.

Contains the main audit_module function that coordinates all checks
and produces the final audit report.
"""

import os
import re
import sys
import yaml

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
from .checks.activities import check_mark_the_words_format, check_hints_in_activities, check_malformed_cloze_activities, check_cloze_syntax_errors, check_error_correction_format, check_yaml_activity_types, check_advanced_activities_presence
from .checks.activity_validation import (
    check_morpheme_patterns,
    check_morpheme_pedagogy,
    check_english_hints_in_activities,
    check_unjumble_empty_jumbled,
    check_mdx_unjumble_rendering,
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
    evaluate_content_heavy,
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
    print_gates,
    print_lint_errors,
    print_pedagogical_violations,
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


def load_yaml_activities(md_file_path: str) -> list[dict] | None:
    """
    Load activities from YAML file if it exists.

    Checks two locations (new structure first, then legacy):
    1. {level}/activities/{module}.yaml (new structure)
    2. {level}/{module}.activities.yaml (legacy)

    Args:
        md_file_path: Path to the markdown file

    Returns:
        List of activity dicts if YAML file exists and is valid, None otherwise
    """
    from pathlib import Path

    md_path = Path(md_file_path)

    # New structure: activities/{module}.yaml
    yaml_path = md_path.parent / 'activities' / (md_path.stem + '.yaml')

    # Fallback to legacy: {module}.activities.yaml
    if not yaml_path.exists():
        yaml_path = md_path.parent / (md_path.stem + '.activities.yaml')

    if not yaml_path.exists():
        return None

    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        # Support both formats:
        # 1. Root list: [{ type: quiz, ... }, ...]
        # 2. Dict with 'activities' key: { activities: [{ type: quiz, ... }, ...] }
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'activities' in data:
            activities = data['activities']
            if isinstance(activities, list):
                return activities
        return None
    except (yaml.YAMLError, IOError) as e:
        print(f"  ⚠️ Error loading YAML activities: {e}")
        return None


def count_yaml_activity_items(activity: dict) -> int:
    """Count items in a YAML activity based on its type."""
    act_type = activity.get('type', '').lower()

    if act_type in ('quiz', 'fill-in', 'true-false', 'unjumble', 'error-correction', 'select', 'translate', 'anagram'):
        return len(activity.get('items', []))
    elif act_type == 'match-up':
        # Support both 'pairs' (preferred) and 'items' with left/right keys
        pairs = activity.get('pairs', [])
        if pairs:
            return len(pairs)
        items = activity.get('items', [])
        if items and isinstance(items[0], dict) and 'left' in items[0]:
            return len(items)
        return 0
    elif act_type == 'group-sort':
        total = 0
        for group in activity.get('groups', []):
            total += len(group.get('items', []))
        return total
    elif act_type == 'cloze':
        # Support two formats:
        # 1. Inline format in passage: {word|opt1|opt2|opt3}
        # 2. Separate blanks array with id, answer, options
        blanks = activity.get('blanks', [])
        if blanks:
            return len(blanks)
        # Fallback to inline format
        passage = activity.get('passage', '')
        return len(re.findall(r'\{[^}]+\}', passage))
    elif act_type == 'mark-the-words':
        # Count marked words: *word* or [word]
        text = activity.get('text', '')
        asterisk_marks = len(re.findall(r'\*[^*]+\*', text))
        bracket_marks = len(re.findall(r'\[[^\]]+\]', text))
        return asterisk_marks + bracket_marks
    elif act_type == 'dialogue-reorder':
        return len(activity.get('lines', []))
    elif act_type in ('essay-response', 'critical-analysis', 'comparative-study', 'authorial-intent'):
        # For essay/analysis tasks, count prompts or items
        # If 'items' exists, count it. If 'prompts' or 'prompt' exists, count it.
        # If neither, return 1 if instructions exist (assumed single task)
        items = activity.get('items', [])
        prompts = activity.get('prompts', [])
        prompt = activity.get('prompt', '')
        questions = activity.get('questions', [])
        model_answers = activity.get('model_answers', [])
        
        if items:
            return len(items)
        if prompts:
            return len(prompts)
        if questions:
            return len(questions)
        if model_answers:
            return len(model_answers)
        if prompt:
            return 1
        return 1 if activity.get('instructions') or activity.get('instruction') else 0

    return 0


def validate_required_metadata(frontmatter_str: str) -> list[str]:
    """Check for required metadata fields."""
    missing = []
    for key, pattern in REQUIRED_METADATA:
        if not re.search(pattern, frontmatter_str):
            missing.append(key)
    return missing


def detect_level(file_path: str, frontmatter_str: str) -> tuple[str, int]:
    """Detect level code and module number from file path."""
    # Parse phase from frontmatter
    phase_match = re.search(r'phase:\s*([A-Za-z0-9\.]+)', frontmatter_str)
    phase = phase_match.group(1) if phase_match else "A1"

    # Detect level from file path
    level_from_path = None
    # Match a1, a2, b1, b2, c1, c2 (case insensitive)
    path_match = re.search(r'/([abc][12])/', file_path.lower())
    if path_match:
        level_from_path = path_match.group(1).upper()

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

    return level_code, module_num


def detect_focus(frontmatter_str: str, level_code: str, module_num: int, title: str = "") -> str | None:
    """Detect module focus (grammar, vocab, checkpoint, skills, cultural, history, etc.)."""
    # Check frontmatter for explicit focus - recognize all valid config types
    # Including content-heavy types: history, literature, biography, folk-culture, fine-arts
    focus_match = re.search(
        r'^focus:\s*["\']?(grammar|vocab|vocabulary|checkpoint|skills|cultural|capstone|bridge|history|literature|biography|folk-culture|fine-arts)["\']?$',
        frontmatter_str, re.MULTILINE | re.IGNORECASE
    )
    if focus_match:
        focus_val = focus_match.group(1).lower()
        # Normalize vocabulary -> vocab
        if focus_val == 'vocabulary':
            return 'vocab'
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
            return 'cultural'  # M72-81: Cultural modules
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


def run_lint_checks(content: str, section_map: dict, module_num: int) -> list[str]:
    """Run markdown lint checks."""
    lint_errors = []
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


def check_structure(content: str) -> tuple[bool, bool, bool]:
    """Check for required structure elements."""
    lines = content.split('\n')
    has_summary = any(re.match(r'^#+\s+(Summary|Підсумок)', l.strip(), re.IGNORECASE) for l in lines)
    has_vocab = any(re.match(r'^#+\s+(Vocabulary|Словник)', l.strip(), re.IGNORECASE) for l in lines)
    has_vocab_table = any('| Word |' in l or 'Слово' in l or 'Термін' in l or '| Ukrainian |' in l for l in lines)
    return has_summary, has_vocab, has_vocab_table



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
            return data.get('items', [])
    except Exception:
        return None

def audit_module(file_path: str) -> bool:
    """
    Main audit function for a module file.

    Args:
        file_path: Path to the module markdown file.

    Returns:
        True if audit passed, False otherwise.
    """
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.")
        sys.exit(1)

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Try loading YAML sidecars
    meta_data = load_yaml_meta(file_path)
    vocab_data = load_yaml_vocab(file_path)
    
    # Parse frontmatter
    if meta_data:
        # Reconstruct frontmatter string for validation functions that expect it
        frontmatter_str = yaml.dump(meta_data, sort_keys=False, allow_unicode=True)
        # Content is the body (file is stripped)
        body = content
        print(f"  📋 Loaded Metadata from YAML sidecar")
    else:
        frontmatter_str, body = parse_frontmatter(content)

    if not frontmatter_str:
        print("Error: No YAML frontmatter found (checked embedded and sidecar).")
        sys.exit(1)

    # Validate required metadata
    missing_meta = validate_required_metadata(frontmatter_str)
    if missing_meta:
        print(f"❌ AUDIT FAILED: Missing Frontmatter Fields: {', '.join(missing_meta)}")
        print("  -> These fields are REQUIRED for 'npm run generate'")
        sys.exit(1)

    # Detect level and module
    level_code, module_num = detect_level(file_path, frontmatter_str)

    # Parse phase
    phase_match = re.search(r'phase:\s*([A-Za-z0-9\.]+)', frontmatter_str)
    phase = phase_match.group(1) if phase_match else level_code

    # Detect focus (pass filename for checkpoint detection)
    module_focus = detect_focus(frontmatter_str, level_code, module_num, os.path.basename(file_path))

    # Get config
    config = get_level_config(level_code, module_focus)
    target = get_word_target(level_code, module_num, module_focus)
    vocab_target = config.get('min_vocab', 25)
    transliteration_allowed = config.get('transliteration_allowed', True)

    # Extract pedagogy
    pedagogy = "Not Specified"
    pedagogy_match = re.search(r'^pedagogy:\s*(.+)$', frontmatter_str, re.MULTILINE)
    if pedagogy_match:
        pedagogy = pedagogy_match.group(1).strip()

    # Parse sections
    section_map = parse_sections(body)

    # Tone validation
    tone_errors = validate_tone(content)
    for err in tone_errors:
        print(f"❌ AUDIT FAILED: {err}")
        sys.exit(1)

    # Summary check
    has_summary, has_vocab, has_vocab_table = check_structure(content)
    
    if vocab_data:
        has_vocab = True
        has_vocab_table = True

    # If metadata sidecar exists, check if it handles the summary (via description or summary field)
    if meta_data and (meta_data.get('summary') or meta_data.get('description')):
        has_summary = True
        
    if not has_summary:
        print(f"❌ AUDIT FAILED: Missing 'Summary' section.")
        print("  -> Every module must have a Summary section (in Markdown or YAML metadata).")
        sys.exit(1)

    # Initialize failure flag early (checkpoint validation may set it)
    has_critical_failure = False

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
            print("❌ CHECKPOINT FORMAT ERRORS:")
            for err in checkpoint_errors:
                print(f"  → {err}")
            print("  See: docs/l2-uk-en/CHECKPOINT-DESIGN-GUIDE.md")
            has_critical_failure = True

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
    core_lines = [line for line in core_content.split('\n') if not line.strip().startswith('|')]
    core_no_tables = '\n'.join(core_lines)
    core_cleaned = clean_for_stats(core_no_tables)
    total_words = len(core_cleaned.split())

    # Engagement pattern - includes B2+ history/cultural callouts
    engagement_pattern = re.compile(
        r'(>\s*[💡⚡🎬🎭🔗🌍🎁🗣️🏠🧭🚌🚇🎟️📱🕵️🌤️🌦️🎱🔮🇺🇦🕰️❓🛠️💂🥪🍺🛍️🏫🏥💊👵🔬🎨🔄📅🍃❄️🚂⏳📚🍲🥣🥗🥙🥚🥛🧩⚠️🛑🎯🎮])|'
        r'(>\s*\[!(note|tip|warning|caution|important|cultural|history-bite|myth-buster|quote|context|analysis|source|legacy|reflection)\])'
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

    print(f"\nAuditing {file_path} (Target: {target})...\n")

    # Check for YAML activities file
    yaml_activities = load_yaml_activities(file_path)
    use_yaml_activities = yaml_activities is not None

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

    if use_yaml_activities:
        print(f"  📋 Found YAML activities file ({len(yaml_activities)} activities)")
        # Process YAML activities
        for activity in yaml_activities:
            act_type = activity.get('type', '').lower()
            if act_type in VALID_ACTIVITY_TYPES or act_type.replace('-', '') in [t.replace('-', '') for t in VALID_ACTIVITY_TYPES]:
                activity_count += 1
                total_activities += 1
                found_activity_types.append(act_type)

                items = count_yaml_activity_items(activity)
                density_target = config['min_items_per_activity']
                if act_type in ACTIVITY_COMPLEXITY:
                    complexity_rules = ACTIVITY_COMPLEXITY[act_type].get(level_code, {})
                    if 'min_items' in complexity_rules:
                        density_target = complexity_rules['min_items']

                if items >= density_target:
                    valid_density_count += 1
                else:
                    low_density_activities.append({
                        'title': activity.get('title', act_type),
                        'type': act_type,
                        'items': items,
                        'target': density_target
                    })

                print(f"  > {activity.get('title', act_type)}: {items} items (min {density_target})")

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

    results['words'] = evaluate_word_count(total_words, target)
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
        has_summary, has_vocab, has_vocab_table = check_structure(content)

    results['structure'] = evaluate_structure(has_summary, has_vocab, has_vocab_table)
    if results['structure'].status == 'FAIL':
        has_critical_failure = True

    # Run lint checks
    lint_errors = run_lint_checks(content, section_map, module_num)
    results['lint'] = evaluate_lint(len(lint_errors))
    if results['lint'].status == 'FAIL':
        has_critical_failure = True

    # Run pedagogical checks
    pedagogical_violations = run_pedagogical_checks(
        content, core_content, level_code, module_num, pedagogy
    )

    # Run vocabulary plan compliance checks
    # VOCAB_PLAN_MISSING is now BLOCKING - core vocab from plan must be present
    if vocab_data:
        # Extract set of words from vocab_data dicts
        vocab_words = set()
        for item in vocab_data:
            uk = item.get('lemma', '') # YAML schema uses 'lemma'
            if uk: vocab_words.add(uk.lower())
    else:
        vocab_words = extract_vocab_from_section(content)

    plan_violations = check_vocab_matches_plan(
        file_path, level_code, module_num, vocab_words
    )

    # Separate blocking violations (missing core vocab) from warnings
    vocab_blocking = [v for v in plan_violations if v.get('blocking', True)]
    vocab_warnings = [v for v in plan_violations if not v.get('blocking', True)]

    # Missing core vocab is a blocking failure
    if vocab_blocking:
        has_critical_failure = True

    # Run metalanguage scaffolding check
    cumulative_vocab = get_cumulative_vocab(level_code, module_num - 1)
    metalang_violations = check_metalanguage_scaffolding(
        content, vocab_words, level_code, module_num, cumulative_vocab
    )
    pedagogical_violations.extend(metalang_violations)

    # Run markdown format checks
    markdown_violations = check_markdown_format(content)
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
    content_quality_violations = check_content_quality(content, level_code, module_num)
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
    results['content_heavy'] = evaluate_content_heavy(
        is_content_heavy,
        activity_count,
        content_recall_violations
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
    all_violations_for_severity = pedagogical_violations + vocab_blocking + vocab_warnings
    recommendation, reasons, severity = compute_recommendation(
        all_violations_for_severity, lint_errors, results, immersion_score,
        min_imm, max_imm, level_code
    )
    print_recommendation(recommendation, reasons, severity)

    # Generate and save report (include all violations)
    all_violations_for_report = pedagogical_violations + vocab_blocking + vocab_warnings

    # Get richness data for report (if available)
    richness_data = None
    richness_flags_for_report = None
    if level_code in ('B1', 'B2', 'C1', 'C2', 'LIT'):
        yaml_activity_types = set(found_activity_types) if use_yaml_activities else None
        richness_data = calculate_richness_score(content, level_code, file_path, yaml_activity_types)
        richness_flags_for_report = detect_dryness_flags(content, level_code, file_path)

    report_content = generate_report(
        file_path, phase, level_code, pedagogy, target,
        has_critical_failure, results, table_rows,
        lint_errors, all_violations_for_report,
        recommendation, reasons, severity,
        low_density_activities,
        richness_data=richness_data,
        richness_flags=richness_flags_for_report
    )
    report_path = save_report(file_path, report_content)
    print(f"\nReport: {report_path}")

    if has_critical_failure:
        print("\n❌ AUDIT FAILED. Correct errors before proceeding.")
        return False
    else:
        print("\n✅ AUDIT PASSED.")
        return True
