"""
Activity-related validation checks.

Validates activity sequencing, structure, variety, and level restrictions.
"""

import re
import sys
from pathlib import Path
from collections import Counter
from ..config import STAGE_ORDER, ACTIVITY_RESTRICTIONS, ACTIVITY_COMPLEXITY, VALID_ACTIVITY_TYPES, REQUIRED_ADVANCED_TYPES

# Add parent dir to path for imports
SCRIPT_DIR = Path(__file__).parent.parent.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.append(str(SCRIPT_DIR))
from yaml_activities import Activity

def check_activity_complexity(content: str, level_code: str, module_num: int = 1, yaml_activities: list[Activity] | None = None, module_focus: str | None = None) -> list[dict]:
    """
    Check if activities meet complexity requirements (word count, item count, structure).
    Strictly enforces rules from MODULE-RICHNESS-GUIDELINES-v2.md.

    A1 M01-M05 Exception: Less strict rules for very early modules (alphabet phase).
    Context-specific complexity: B2-history, B2-biography, B1-vocab, B1-cultural.
    """
    violations = []

    # Relax rules for A1 M01-M05 and B1 M01-M05 (bridge modules)
    is_a1_early = (level_code == 'A1' and module_num <= 5)
    is_b1_bridge = (level_code == 'B1' and module_num <= 5)
    
    # 1. Parse all activities (Unified: supports both legacy MD and new YAML)
    parsed_activities = []
    
    # Handle YAML activities (Preferred)
    if yaml_activities:
        for act in yaml_activities:
            parsed_activities.append({
                'type': act.type,
                'title': getattr(act, 'title', 'Untitled'),
                'body': '', # Not needed for YAML logic-based checks
                'source': 'yaml',
                'object': act
            })
    
    # Legacy Markdown activities support removed (Issue #394)
    
    for activity_data in parsed_activities:
        act_type = activity_data['type']
        title = activity_data['title']
        body = activity_data['body']
        act_obj = activity_data['object']
        
        # Skip checking unknown activity types
        if act_type not in ACTIVITY_COMPLEXITY:
            continue

        # Context-specific complexity lookup (e.g., B2-history, B1-vocab)
        context_key = f"{level_code}-{module_focus}" if module_focus else None
        rules = None

        # Try context-specific rules first (B2-history, B1-vocab, etc.)
        if context_key and context_key in ACTIVITY_COMPLEXITY[act_type]:
            rules = ACTIVITY_COMPLEXITY[act_type][context_key].copy()
        # Fall back to standard level rules
        elif level_code in ACTIVITY_COMPLEXITY[act_type]:
            rules = ACTIVITY_COMPLEXITY[act_type][level_code].copy()

        # If no specific rules for this level (e.g. anagram in A2), restrictions check handles it
        if not rules:
            continue

        # --- New Activity Type Structural Checks ---
        if act_type == 'essay-response':
            if not act_obj and '> [!model-answer]' not in body:
                violations.append({
                    'type': 'STRUCTURE_MISSING',
                    'issue': f"essay-response '{title}' missing mandatory > [!model-answer]",
                    'fix': "All essay responses must include a model answer."
                })
            if not act_obj and '> [!rubric]' not in body:
                violations.append({
                    'type': 'STRUCTURE_MISSING',
                    'issue': f"essay-response '{title}' missing mandatory > [!rubric]",
                    'fix': "All essay responses must include a rubric."
                })
        
        if act_type in ('critical-analysis', 'comparative-study', 'authorial-intent'):
             if not act_obj and '> [!model-answer]' not in body:
                violations.append({
                    'type': 'STRUCTURE_MISSING',
                    'issue': f"{act_type} '{title}' missing mandatory > [!model-answer]",
                    'fix': f"All {act_type} activities must include a model answer."
                })
            
        # Apply A1 Early Relaxations
        if is_a1_early:
            if act_type == 'quiz':
                rules['min_len'] = 2  # Very simple prompts
            elif act_type == 'match-up':
                rules['pairs_max'] = 15  # Allow more pairs for alphabet matching
            elif act_type == 'group-sort':
                rules['items_min'] = 6
                rules['items_max'] = 30
                rules['groups_min'] = 2
            elif act_type == 'fill-in':
                rules['min_items'] = 6

        # Apply B1 Bridge Relaxations (M01-M05 use A2 complexity exactly)
        if is_b1_bridge:
            if act_type == 'quiz':
                rules['min_len'] = 8
                rules['max_len'] = 15
            elif act_type == 'unjumble':
                rules['words_min'] = 8
                rules['words_max'] = 10
            elif act_type == 'match-up':
                rules['pairs_min'] = 10
                rules['pairs_max'] = 12
            elif act_type == 'fill-in':
                rules['sent_min'] = 6
                rules['sent_max'] = 8
            elif act_type == 'true-false':
                rules['min_len'] = 6
                rules['max_len'] = 12
            elif act_type == 'group-sort':
                rules['groups_min'] = 2
                rules['groups_max'] = 4
                rules['items_min'] = 10
            elif act_type == 'error-correction':
                rules['errors'] = 1
                rules['min_len'] = 6
                rules['max_len'] = 10
            elif act_type == 'cloze':
                rules['sentences'] = [3, 4, 5]
                rules['blanks'] = [3, 4]
            elif act_type == 'mark-the-words':
                rules['min_len'] = 8
                rules['max_len'] = 12
                rules['marks'] = [2, 3, 4]
            elif act_type == 'select':
                rules['min_len'] = 6
                rules['max_len'] = 10
                rules['options'] = [4, 5]
                rules['correct'] = [2, 3]
            elif act_type == 'translate':
                rules['min_len'] = 4
                rules['max_len'] = 8
        
        # --- Check Item Count ---
        items_count = count_items(body, act_obj)
        min_items = rules.get('min_items', 6)  # Default min 6 if not specified

        # Activity-specific item count checks
        if act_type == 'group-sort':
            group_count = 0
            if act_obj:
                group_count = len(act_obj.groups)
            else:
                group_headers = re.findall(r'^\s*###\s+([^\n]+)', body, re.MULTILINE)
                group_count = len([h for h in group_headers if not any(
                    skip in h.lower() for skip in ['note', 'explanation', 'hint', 'tip']
                )])
            
            min_groups = rules.get('groups_min', 2)
            max_groups = rules.get('groups_max', 4)
            
            if not (min_groups <= group_count <= max_groups):
                violations.append({
                    'type': 'COMPLEXITY',
                    'issue': f"group-sort '{title}' has {group_count} groups (target: {min_groups}-{max_groups})",
                    'fix': f"Adjust number of sorting categories to {min_groups}-{max_groups}."
                })
            
            min_sort_items = rules.get('items_min', 8)
            max_sort_items = rules.get('items_max', 20)
            if not (min_sort_items <= items_count <= max_sort_items):
                violations.append({
                    'type': 'COMPLEXITY',
                    'issue': f"group-sort '{title}' has {items_count} items (target: {min_sort_items}-{max_sort_items})",
                    'fix': f"Adjust number of items to sort to {min_sort_items}-{max_sort_items}."
                })
        
        elif act_type == 'match-up':
            min_pairs = rules.get('pairs_min', 8)
            max_pairs = rules.get('pairs_max', 18)
            
            if not (min_pairs <= items_count <= max_pairs):
                violations.append({
                    'type': 'COMPLEXITY',
                    'issue': f"match-up '{title}' has {items_count} pairs (target: {min_pairs}-{max_pairs})",
                    'fix': f"Adjust number of pairs to {min_pairs}-{max_pairs}."
                })

        elif items_count < min_items:
            violations.append({
                'type': 'COMPLEXITY',
                'issue': f"{act_type} '{title}' has {items_count} items (minimum: {min_items})",
                'fix': f"Add more items. {level_code} {act_type} requires at least {min_items} items."
            })

        # --- Check Content Complexity (Word Counts / Options) ---
        
        # Unjumble / Anagram Structure
        if act_type == 'unjumble':
            if not act_obj:
                slash_usage = len(re.findall(r'/', body))
                if slash_usage < items_count:
                     violations.append({
                        'type': 'FORMAT_ERROR',
                        'issue': f"unjumble '{title}' items must use slash '/' separator",
                        'fix': "Split words with slashes, e.g. 'Я / люблю / каву'."
                    })
            
            # Check word counts
            items_to_check = []
            if act_obj:
                for item in act_obj.items:
                    if hasattr(item, 'words') and isinstance(item.words, list):
                        items_to_check.append(' '.join(item.words))
                    elif hasattr(item, 'words'):
                        items_to_check.append(str(item.words))
            else:
                items_to_check = re.findall(r'\d+\.\s*([^\n>]+)', body)

            for i, item in enumerate(items_to_check, 1):
                words = len(re.findall(r'[\w\u0400-\u04FF]+', item))
                min_w = rules.get('words_min', 4)
                max_w = rules.get('words_max', 20)
                
                if words < min_w - 1 or words > max_w + 2:
                     violations.append({
                        'type': 'COMPLEXITY_WORD_COUNT',
                        'issue': f"unjumble '{title}' item {i} has {words} words (target: {min_w}-{max_w})",
                        'fix': f"Adjust sentence length to {min_w}-{max_w} words to match {level_code} complexity."
                    })

        # Anagram Structure
        elif act_type == 'anagram':
            if not act_obj:
                items_raw = re.findall(r'\d+\.\s*([^\n>]+)', body)
                for item in items_raw:
                    if '/' in item:
                        violations.append({
                            'type': 'FORMAT_ERROR',
                            'issue': f"anagram '{title}' item '{item.strip()}' must use SPACES separator, not slashes",
                            'fix': "Use spaces between letters: 'л і т е р а'."
                        })
                        break
        
        # Fill-in Structure
        elif act_type == 'fill-in':
            if not act_obj:
                if '___' not in body:
                     violations.append({
                        'type': 'FORMAT_ERROR',
                        'issue': f"fill-in '{title}' missing '___' placeholders",
                        'fix': "Use exactly '___' (three underscores) for blanks."
                    })
                if '[!options]' not in body:
                     violations.append({
                        'type': 'FORMAT_ERROR',
                        'issue': f"fill-in '{title}' missing mandatory [!options] block",
                        'fix': "All fill-in activities must provide [!options] for the user."
                    })
        
        # Quiz Options Check
        elif act_type == 'quiz':
            quiz_items = []
            if act_obj:
                quiz_items = act_obj.items
            else:
                # Basic parsing for legacy
                questions_raw = re.split(r'\n\d+\.', body)[1:]
                for q in questions_raw:
                    prompt = q.split('\n')[0]
                    opts = re.findall(r'-\s*\[', q)
                    from dataclasses import dataclass
                    @dataclass
                    class LegacyItem:
                        question: str
                        options: list
                    quiz_items.append(LegacyItem(question=prompt, options=opts))

            min_len = rules.get('min_len', 5)
            max_len = rules.get('max_len', 30)
            
            for i, q in enumerate(quiz_items, 1):
                prompt = getattr(q, 'question', '')
                prompt_words = len(re.findall(r'[\w\u0400-\u04FF]+', prompt))
                if prompt_words < min_len or prompt_words > max_len + 5:
                     violations.append({
                        'type': 'COMPLEXITY_WORD_COUNT',
                        'issue': f"quiz '{title}' Q{i} prompt length {prompt_words} (target: {min_len}-{max_len})",
                        'fix': f"Adjust prompt length to {min_len}-{max_len} words."
                    })
                
                options_count = len(q.options)
                target_opts = rules.get('options', [4])
                if isinstance(target_opts, int): target_opts = [target_opts]
                
                if options_count > 0 and options_count not in target_opts and options_count < min(target_opts):
                     violations.append({
                        'type': 'COMPLEXITY_OPTIONS',
                        'issue': f"quiz '{title}' Q{i} has {options_count} options (target: {target_opts})",
                        'fix': f"Provide {target_opts} options for {level_code} quizzes."
                    })

    return violations


def check_activity_sequencing(content: str, pedagogy: str) -> list[dict]:
    """Check activity sequencing based on PPP or TTT methodology."""
    violations = []

    # Extract activity stages from headers
    activity_stages = []
    for match in re.finditer(
        r'##\s+\w+[^:]*:\s*[^\s]*\[stage:\s*([^\s]+)\]',
        content, re.IGNORECASE
    ):
        stage = match.group(1).strip().lower()
        activity_stages.append(stage)

    if not activity_stages:
        return violations

    # Determine expected order based on pedagogy field
    method = 'PPP'
    if pedagogy:
        pedagogy_upper = pedagogy.upper()
        if 'TTT' in pedagogy_upper:
            method = 'TTT'
        elif 'CLIL' in pedagogy_upper or 'NARRATIVE' in pedagogy_upper:
            method = 'CLIL'
    expected_order = STAGE_ORDER.get(method, STAGE_ORDER['PPP'])

    # Check if stages appear in valid order
    last_valid_idx = -1
    for stage in activity_stages:
        if stage in expected_order:
            current_idx = expected_order.index(stage)
            if current_idx < last_valid_idx:
                violations.append({
                    'type': 'SEQUENCING',
                    'issue': f"Activity stage '{stage}' appears after later stage (expected {method} order)",
                    'fix': f"Reorder activities: {' → '.join(expected_order)}"
                })
                break
            last_valid_idx = current_idx

    # Check for production before presentation
    stages_set = set(activity_stages)
    if 'free-production' in stages_set and 'presentation' not in content.lower():
        if method == 'PPP':
            violations.append({
                'type': 'SEQUENCING',
                'issue': "Free-production activity found but no Presentation section",
                'fix': "Add Presentation section before Practice activities (PPP methodology)"
            })

    return violations


def check_answer_position_bias(content: str) -> list[dict]:
    """Check if correct answers are always in same position (bias)."""
    violations = []

    activities = re.findall(
        r'##\s+(quiz|select|translate)[^#]*?(?=\n##|\n#\s|\Z)',
        content, re.DOTALL | re.IGNORECASE
    )

    for activity in activities:
        if isinstance(activity, tuple):
            activity = activity[0]

        questions = re.split(r'\n\d+\.', activity)
        positions = []

        for q in questions:
            options = re.findall(r'-\s*\[([ xX])\]', q)
            for i, opt in enumerate(options):
                if opt.lower() == 'x':
                    positions.append(i + 1)
                    break

        if len(positions) >= 4:
            counts = Counter(positions)
            most_common_pos, most_common_count = counts.most_common(1)[0]
            bias_ratio = most_common_count / len(positions)

            if bias_ratio > 0.7:
                violations.append({
                    'type': 'ANSWER_BIAS',
                    'issue': f"Answer position bias detected: {most_common_count}/{len(positions)} ({bias_ratio:.0%}) answers in position {most_common_pos}",
                    'fix': "Randomize correct answer positions to prevent pattern guessing."
                })

    return violations


def check_activity_variety(content: str) -> list[dict]:
    """Check if same activity type is used too many times."""
    violations = []

    activity_types = re.findall(
        r'##\s*(quiz|match-up|fill-in|true-false|group-sort|unjumble|error-correction|anagram|cloze|select|translate|mark-the-words):',
        content, re.IGNORECASE
    )

    if not activity_types:
        return violations

    type_counts = Counter(t.lower() for t in activity_types)
    total = len(activity_types)

    for act_type, count in type_counts.items():
        if count >= 4 and count / total > 0.4:
            violations.append({
                'type': 'VARIETY',
                'issue': f"Activity type '{act_type}' overused: {count}/{total} activities ({count/total:.0%})",
                'fix': "Use more diverse activity types for better engagement."
            })

    return violations


def check_matchup_misuse(content: str) -> list[dict]:
    """Detect match-up activities that should be group-sort."""
    violations = []

    matchup_pattern = r'##\s*match-up:\s*([^\n]+)\n(.*?)(?=\n##|\n#\s|\Z)'
    matchups = re.findall(matchup_pattern, content, re.DOTALL | re.IGNORECASE)

    sorting_prompts = [
        r'which\s+(word|one|item)s?\s+(needs?|has|have|is|are|contains?)',
        r'sort\s+(by|into|the)',
        r'categoriz|classif|group\s+(the|these)',
        r'(with|without)\s+(soft sign|ь|apostrophe)',
        r'які\s+(слова|з них)',
        r'розсортуй|класифікуй|розділ',
    ]

    for title, body in matchups:
        full_text = title + ' ' + body[:200]

        for pattern in sorting_prompts:
            if re.search(pattern, full_text, re.IGNORECASE):
                violations.append({
                    'type': 'ACTIVITY_MISUSE',
                    'issue': f"match-up '{title.strip()}' appears to be a sorting task",
                    'fix': "Use group-sort instead. Match-up requires semantic pairs (Ukrainian↔English, Synonym↔Antonym). Sorting by category should be group-sort."
                })
                break

        # Check for symmetric pairs
        rows = re.findall(r'\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|', body)
        if len(rows) >= 4:
            symmetric_pairs = 0
            for left, right in rows:
                left_clean = re.sub(r'[^а-яіїєґА-ЯІЇЄҐ]', '', left)
                right_clean = re.sub(r'[^а-яіїєґА-ЯІЇЄҐ]', '', right)
                if len(left_clean) >= 3 and len(right_clean) >= 3:
                    if left_clean[:3].lower() == right_clean[:3].lower():
                        symmetric_pairs += 1

            if symmetric_pairs >= len(rows) * 0.5:
                already_flagged = any(
                    v['type'] == 'ACTIVITY_MISUSE' and title.strip() in v.get('issue', '')
                    for v in violations
                )
                if not already_flagged:
                    violations.append({
                        'type': 'ACTIVITY_MISUSE',
                        'issue': f"match-up '{title.strip()}' has symmetric pairs (X vs variant-of-X)",
                        'fix': "This pattern (same word with/without feature) should be group-sort. Match-up expects different concepts that pair logically."
                    })

    return violations


def check_activity_level_restrictions(content: str, level_code: str, module_num: int) -> list[dict]:
    """Check if activities are appropriate for the level."""
    violations = []

    activity_types = re.findall(
        r'##\s*(quiz|match-up|fill-in|true-false|group-sort|unjumble|error-correction|anagram|cloze|select|translate|mark-the-words):',
        content, re.IGNORECASE
    )
    activity_types = [t.lower() for t in activity_types]

    if not activity_types:
        return violations

    rules = ACTIVITY_RESTRICTIONS.get(level_code, {})

    # Check forbidden activities
    for forbidden in rules.get('forbidden', []):
        if forbidden in activity_types:
            violations.append({
                'type': 'LEVEL_RESTRICTION',
                'issue': f"Activity '{forbidden}' not allowed at {level_code}",
                'fix': f"Use level-appropriate activities. '{forbidden}' is introduced at A2+."
            })

    # Check anagram restrictions
    if 'anagram' in activity_types:
        if rules.get('anagram_forbidden'):
            violations.append({
                'type': 'LEVEL_RESTRICTION',
                'issue': f"Activity 'anagram' not allowed at {level_code}",
                'fix': "Anagram is only for A1 M01-M10 (Cyrillic scaffolding). Use unjumble instead."
            })
        elif level_code == 'A1' and module_num > rules.get('anagram_limit', 10):
            violations.append({
                'type': 'LEVEL_RESTRICTION',
                'issue': f"Activity 'anagram' should be phased out after A1 M10 (current: M{module_num:02d})",
                'fix': "Anagram is for Cyrillic scaffolding only. Use unjumble for word-ordering practice."
            })

    return violations


def check_activity_focus_alignment(content: str, level_code: str, module_num: int, frontmatter_str: str) -> list[dict]:
    """Check if activities align with grammar vs vocabulary focus (B1/B2).
    
    Checkpoints are exempt - they use quiz-heavy activity mix for comprehensive testing.
    """
    violations = []

    if level_code not in ['B1', 'B2']:
        return violations
    
    # Skip checkpoint modules - they legitimately use more quiz activities for assessment
    if 'checkpoint' in frontmatter_str.lower() or 'контрольна точка' in frontmatter_str.lower():
        return violations

    # Determine focus
    is_grammar = False
    is_vocab = False

    if level_code == 'B1':
        is_grammar = module_num <= 45
        is_vocab = module_num > 45
    elif level_code == 'B2':
        is_grammar = module_num <= 40
        is_vocab = module_num > 40

    if 'grammar' in frontmatter_str.lower():
        is_grammar = True
        is_vocab = False
    elif 'vocab' in frontmatter_str.lower() or 'vocabulary' in frontmatter_str.lower():
        is_vocab = True
        is_grammar = False

    # Extract activity types
    activity_types = re.findall(
        r'##\s*(quiz|match-up|fill-in|true-false|group-sort|unjumble|error-correction|anagram|cloze|select|translate|mark-the-words):',
        content, re.IGNORECASE
    )
    activity_types = [t.lower() for t in activity_types]

    if not activity_types:
        return violations

    type_counts = Counter(activity_types)

    grammar_priority = ['error-correction', 'fill-in', 'unjumble', 'cloze']
    vocab_priority = ['match-up', 'mark-the-words', 'translate', 'quiz']
    vocab_avoid = ['group-sort']

    if is_grammar:
        priority_count = sum(type_counts.get(t, 0) for t in grammar_priority)
        total = len(activity_types)

        if priority_count < total * 0.3:
            violations.append({
                'type': 'FOCUS_MISMATCH',
                'issue': f"{level_code} M{module_num:02d} is grammar-focused but lacks grammar-priority activities",
                'fix': f"Grammar modules should emphasize: {', '.join(grammar_priority)}. Currently only {priority_count}/{total} activities are grammar-focused."
            })

    elif is_vocab:
        avoid_count = sum(type_counts.get(t, 0) for t in vocab_avoid)
        if avoid_count >= 2:
            violations.append({
                'type': 'FOCUS_MISMATCH',
                'issue': f"{level_code} M{module_num:02d} is vocab-focused but uses group-sort ({avoid_count}x)",
                'fix': "Vocabulary modules should avoid group-sort (cognitive overload when learning new words). Use match-up, mark-the-words, or translate instead."
            })

    return violations


def count_items(text: str, activity: Activity | None = None) -> int:
    """Count items in an activity section (Markdown or YAML Activity object)."""
    if activity:
        # YAML Activity Object logic
        from yaml_activities import (
            QuizActivity, MatchUpActivity, GroupSortActivity, FillInActivity,
            ClozeActivity, UnjumbleActivity, ErrorCorrectionActivity,
            MarkTheWordsActivity, TranslateActivity, AnagramActivity, ReadingActivity,
            SelectActivity, TrueFalseActivity, EssayResponseActivity,
            CriticalAnalysisActivity, ComparativeStudyActivity, AuthorialIntentActivity
        )
        
        if isinstance(activity, (QuizActivity, FillInActivity, UnjumbleActivity, 
                                 ErrorCorrectionActivity, TranslateActivity, AnagramActivity, 
                                 SelectActivity, TrueFalseActivity)):
            return len(activity.items)
        elif isinstance(activity, MatchUpActivity):
            return len(activity.pairs)
        elif isinstance(activity, GroupSortActivity):
            # Count total items across all groups
            return sum(len(group.items) for group in activity.groups)
        elif isinstance(activity, ClozeActivity):
            # If passage is parsed into blanks, use blanks count
            if activity.blanks:
                return len(activity.blanks)
            # Fallback: parse passage string for {word|opt} patterns
            return len(re.findall(r'\{[^}|]+\|[^}]+\}', activity.passage))
        elif isinstance(activity, MarkTheWordsActivity):
            # If answers array is populated, use that
            if activity.answers:
                return len(activity.answers)
            # Otherwise count asterisks in text
            return len(re.findall(r'\*([^\*]+)\*', activity.text))
        elif isinstance(activity, ReadingActivity):
            # Seminar tracks use 'text' (primary source), others use 'tasks'
            count = 0
            if activity.text:
                count = 1
            if activity.tasks:
                count = max(count, len(activity.tasks))
            return count
        elif isinstance(activity, (EssayResponseActivity, CriticalAnalysisActivity, 
                                   ComparativeStudyActivity, AuthorialIntentActivity)):
            return 1
        return 0

    # Legacy Markdown parsing logic (text-based)
    # 1. Numbered Lists
    numbered = len(re.findall(r'^\s*\d+\.', text, re.MULTILINE))

    # 2. Table Rows (excluding headers and separators)
    table_lines = [
        line for line in text.split('\n')
        if line.strip().startswith('|') and '---' not in line
    ]
    table_count = max(0, len(table_lines) - 1) if table_lines else 0

    # 3. Checkboxes
    checkboxes = len(re.findall(r'^\s*-\s*\[[ xX]?\]', text, re.MULTILINE))

    # 4. Bullets (excluding checkboxes)
    bullets = len(re.findall(r'^\s*-\s+[^\s]', text, re.MULTILINE))

    # 5. Cloze Placeholders
    # Match {1} or {1:DROPDOWN...} or {1:TEXT...} (numbered format)
    # Also match {word|opt1|opt2...} (inline answer format)
    cloze_numbered = len(re.findall(r'\{\d+(?::[^}]+)?\}', text))
    cloze_inline = len(re.findall(r'\{[^}|]+\|[^}]+\}', text))  # {word|opt1|opt2}
    cloze_placeholders = cloze_numbered + cloze_inline

    # 6. Mark-the-words Brackets or Asterisks
    # Match [word] brackets (original format)
    mark_words_brackets = len([
        m for m in re.findall(r'\[([^\]]+)\]', text)
        if not m.startswith('!') and not re.match(r'[^\s]+\]\(', m)
    ])
    # Also match *word* asterisks (inline format)
    mark_words_asterisks = len(re.findall(r'\*[^\*]+\*', text))
    mark_words = mark_words_brackets + mark_words_asterisks

    # Priority Logic
    if numbered > 0:
        return numbered
    elif table_count > 0:
        return table_count
    elif cloze_placeholders > 0:
        return cloze_placeholders
    elif mark_words > 0:
        return mark_words
    elif checkboxes > 0:
        return checkboxes
    else:
        return bullets


def check_anagram_min_letters(content: str) -> list[dict]:
    """Check that anagram items have at least 3 letters (1-2 letters are pointless)."""
    violations = []

    # Find all anagram activities
    anagram_pattern = r'##\s*anagram:\s*([^\n]+)\n(.*?)(?=\n##|\n#\s|\Z)'
    anagrams = re.findall(anagram_pattern, content, re.DOTALL | re.IGNORECASE)

    for title, body in anagrams:
        # Find numbered items: "1. а б в" or "1. а / б / в"
        items = re.findall(r'\d+\.\s*([^\n]+)', body)

        for i, item in enumerate(items, 1):
            # Extract letters (space or slash separated)
            letters = re.split(r'[\s/]+', item.strip())
            letters = [l.strip() for l in letters if l.strip() and not l.startswith('>')]

            if len(letters) <= 2:
                violations.append({
                    'type': 'ANAGRAM_TOO_SHORT',
                    'issue': f"Anagram '{title.strip()}' item {i} has only {len(letters)} letter(s): '{item.strip()}'",
                    'fix': "Anagram items must have at least 3 letters. Remove or replace with longer words."
                })

            # Check for uppercase letters
            if any(re.match(r'[А-ЯІЇЄҐ]', l) for l in letters):
                violations.append({
                    'type': 'ANAGRAM_UPPERCASE',
                    'issue': f"Anagram '{title.strip()}' item {i} uses uppercase: '{item.strip()}'",
                    'fix': "Use lowercase letters in anagram items."
                })

    return violations


def check_unjumble_word_match(content: str) -> list[dict]:
    """
    Check if unjumble jumbled words match answer words exactly.

    An unjumble activity is only solvable if the jumbled words are exactly
    the same words as in the answer (just reordered). This check catches:
    - Words in answer that aren't in the jumbled set
    - Words in jumbled set that aren't in the answer
    - Word count mismatches (e.g., "поняття" appearing twice in answer but once in jumbled)

    Punctuation (—, commas, periods, colons) is ignored since it's not part of the puzzle.
    """
    violations = []

    # Find all unjumble activities
    unjumble_pattern = r'##\s*unjumble:\s*([^\n]+)\n(.*?)(?=\n##\s|\n#\s|\Z)'
    unjumbles = re.findall(unjumble_pattern, content, re.DOTALL | re.IGNORECASE)

    for title, body in unjumbles:
        # Find numbered items with their answers
        # Pattern: "1. word / word / word" followed by "> [!answer] Answer sentence"
        item_pattern = r'(\d+)\.\s*([^\n>]+)\n\s*>\s*\[!answer\]\s*([^\n]+)'
        items = re.findall(item_pattern, body)

        for item_num, jumbled_text, answer_text in items:
            # Extract jumbled words (split by /)
            jumbled_words = [w.strip().lower() for w in jumbled_text.split('/') if w.strip()]

            # Extract answer words (split by whitespace, remove punctuation)
            # Keep apostrophes for words like "зв'язок", "пов'язаний"
            answer_clean = re.sub(r'[—\-,.:;!?()«»"]', ' ', answer_text)
            answer_words = [w.strip().lower() for w in answer_clean.split() if w.strip()]

            # Also clean jumbled words of any stray punctuation (but keep apostrophes)
            jumbled_words = [re.sub(r'[—\-,.:;!?()«»"]', '', w) for w in jumbled_words]
            jumbled_words = [w for w in jumbled_words if w]  # Remove empty strings

            # Compare as multisets
            jumbled_counter = Counter(jumbled_words)
            answer_counter = Counter(answer_words)

            # Find mismatches
            missing_from_jumbled = answer_counter - jumbled_counter  # Words in answer but not enough in jumbled
            extra_in_jumbled = jumbled_counter - answer_counter      # Words in jumbled but not enough in answer

            if missing_from_jumbled:
                missing_list = [f"{word}(×{count})" if count > 1 else word
                               for word, count in missing_from_jumbled.items()]
                violations.append({
                    'type': 'UNJUMBLE_WORD_MISMATCH',
                    'issue': f"Unjumble '{title.strip()}' item {item_num}: answer has words not in jumbled set: {', '.join(missing_list)}",
                    'fix': "Add missing words to the jumbled set, or fix the answer. Jumbled words must exactly match answer words."
                })

            if extra_in_jumbled:
                extra_list = [f"{word}(×{count})" if count > 1 else word
                             for word, count in extra_in_jumbled.items()]
                violations.append({
                    'type': 'UNJUMBLE_WORD_MISMATCH',
                    'issue': f"Unjumble '{title.strip()}' item {item_num}: jumbled set has extra words not in answer: {', '.join(extra_list)}",
                    'fix': "Remove extra words from jumbled set, or fix the answer. Jumbled words must exactly match answer words."
                })

    return violations


def check_activity_ukrainian_content(content: str, level_code: str = 'A1', module_num: int = 1) -> list[dict]:
    """
    Check if activities contain Ukrainian content (not just English).
    
    Activities that are 100% English (like quizzes asking about English sentences)
    are pedagogically useless for a Ukrainian language course.
    
    Thresholds:
    - A1 M01-M02: EXEMPT (alphabet learning - letters themselves are the content)
    - A1 M03-M10: Allow up to 80% English (Cyrillic learning phase)
    - A1 M11+, A2: Require at least 20% Cyrillic
    - B1+: Require at least 30% Cyrillic
    """
    violations = []
    
    # EXEMPT A1 M01-M02 (alphabet modules - letters themselves are the content)
    if level_code == 'A1' and module_num <= 2:
        return violations
    
    
    # Find all activity sections
    activity_pattern = r'##\s*([a-z-]+):\s*([^\n]+)\n(.*?)(?=\n##\s|\n#\s|\Z)'
    activities = re.findall(activity_pattern, content, re.DOTALL | re.IGNORECASE)
    
    # Determine threshold based on level
    min_cyrillic_ratio = 0.10  # Default: 10% Cyrillic minimum
    if level_code in ['B1', 'B2', 'C1', 'C2']:
        min_cyrillic_ratio = 0.20  # Higher levels need more Ukrainian
    
    for act_type, title, body in activities:
        act_type_lower = act_type.lower()

        # Skip non-activity sections (content sections with colon in title)
        if act_type_lower not in VALID_ACTIVITY_TYPES:
            continue

        # Skip anagram activities (they're supposed to be letters only)
        if act_type_lower == 'anagram':
            continue
            
        # Count Cyrillic vs total characters (excluding markdown/punctuation)
        text = title + ' ' + body
        
        # Extract just text content (remove markdown syntax)
        clean_text = re.sub(r'\[[ xX]?\]', '', text)  # Remove checkboxes
        clean_text = re.sub(r'\|', '', clean_text)     # Remove table pipes
        clean_text = re.sub(r'[#*_>`~\-]', '', clean_text)  # Remove markdown
        clean_text = re.sub(r'\{[^}]+\}', '', clean_text)  # Remove cloze placeholders
        
        # Count characters
        cyrillic_chars = len(re.findall(r'[а-яіїєґА-ЯІЇЄҐ]', clean_text))
        latin_chars = len(re.findall(r'[a-zA-Z]', clean_text))
        total_text_chars = cyrillic_chars + latin_chars
        
        if total_text_chars < 20:
            # Too short to evaluate
            continue
            
        cyrillic_ratio = cyrillic_chars / total_text_chars if total_text_chars > 0 else 0
        
        if cyrillic_ratio < min_cyrillic_ratio:
            violations.append({
                'type': 'NO_UKRAINIAN_CONTENT',
                'issue': f"Activity '{act_type}: {title.strip()}' has only {cyrillic_ratio:.0%} Ukrainian content ({cyrillic_chars}/{total_text_chars} chars)",
                'fix': "Activities must contain Ukrainian examples/sentences/words. Rewrite with Ukrainian content."
            })
    
    return violations


def check_resources_placement(content: str) -> list[dict]:
    """
    DEPRECATED - Resources are now managed in YAML (Issue #354, Jan 2026).

    Resources are stored in docs/resources/external_resources.yaml and injected
    at build time, not stored in markdown files.

    This check is disabled - [!resources] sections should NOT appear in markdown.
    If found, they are stale and will be ignored (replaced by YAML at build time).
    """
    # No longer check for resources in markdown
    return []


def check_resources_required(content: str) -> list[dict]:
    """
    DEPRECATED - Resources are now managed in YAML (Issue #354, Jan 2026).

    Resources are stored in docs/resources/external_resources.yaml and injected
    at build time, not stored in markdown files.

    This check is disabled - modules should NOT have [!resources] in markdown.
    To add resources, edit docs/resources/external_resources.yaml instead.
    """
    # No longer require resources in markdown
    return []


def check_activity_header_format(content: str) -> list[dict]:
    """
    Check if activity headers use the required format: ## activity-type: Title

    The MDX generator requires the colon+title format. Headers like "## quiz"
    (without colon) will be silently ignored during generation, causing missing
    activities in the output.

    Correct: ## quiz: Визначення виду
    Wrong:   ## quiz
    """
    violations = []

    # Find all potential activity headers (with or without colon)
    # Pattern: ## followed by known activity type, optionally followed by colon
    activity_types_pattern = '|'.join(VALID_ACTIVITY_TYPES)

    # Find headers WITHOUT colon (malformed)
    malformed_pattern = rf'^##\s*({activity_types_pattern})\s*$' # Removed : from pattern
    malformed_matches = re.findall(malformed_pattern, content, re.MULTILINE | re.IGNORECASE)

    for act_type in malformed_matches:
        violations.append({
            'type': 'MALFORMED_ACTIVITY_HEADER',
            'issue': f"Activity header '## {act_type}' missing required ': Title' suffix",
            'fix': f"Change to '## {act_type}: Descriptive Title' format. Without the colon and title, the MDX generator will skip this activity entirely."
        })

    # Also check for headers with colon but no title
    empty_title_pattern = rf'^##\s*({activity_types_pattern}):\s*$' # Added : to pattern
    empty_title_matches = re.findall(empty_title_pattern, content, re.MULTILINE | re.IGNORECASE)

    for act_type in empty_title_matches:
        violations.append({
            'type': 'MALFORMED_ACTIVITY_HEADER',
            'issue': f"Activity header '## {act_type}:' has empty title",
            'fix': f"Add a descriptive Ukrainian title after the colon: '## {act_type}: Назва вправи'"
        })

    return violations


def check_mark_the_words_format(activities: list) -> list[dict]:
    """Check for malformed mark-the-words activities in YAML."""
    violations = []
    
    if not activities or not isinstance(activities, list):
        return violations
    
    for activity in activities:
        act_type = activity.type if hasattr(activity, 'type') else activity.get('type')
        if act_type != 'mark-the-words':
            continue
            
        title = getattr(activity, 'title', 'Untitled')
        if not title and isinstance(activity, dict):
            title = activity.get('title', 'Untitled')
            
        # Handle both dict (YAML) and object (parsed) representations
        # Schema-compliant: passage/correct_words (in YAML dict)
        # Object attributes: text/answers (in parsed object)
        passage = ''
        correct_words = []
        
        if isinstance(activity, dict):
            # YAML dict - check for schema-compliant fields first
            passage = activity.get('passage', '')
            correct_words = activity.get('correct_words', [])
            
            # Fallback to old field names for backwards compatibility
            if not passage:
                passage = activity.get('text', '')
            if not correct_words:
                correct_words = activity.get('answers', [])
        else:
            # Parsed object - uses text/answers attributes
            passage = getattr(activity, 'text', '')
            correct_words = getattr(activity, 'answers', [])

        if not passage:
             violations.append({
                'type': 'MISSING_FIELD',
                'severity': 'critical',
                'issue': f"mark-the-words '{title}' is missing 'passage' field",
                'fix': "Add 'passage' field with the content"
            })
            
        if not correct_words and '*' not in passage:
             violations.append({
                'type': 'MISSING_FIELD',
                'severity': 'critical',
                'issue': f"mark-the-words '{title}' is missing 'correct_words' array",
                'fix': "Add 'correct_words' array with correct words"
            })
        
        if '(correct)' in passage or '(wrong)' in passage:
            violations.append({
                'type': 'MALFORMED_MARK_THE_WORDS',
                'severity': 'critical',
                'issue': f"mark-the-words '{title}' contains (correct)/(wrong) annotations",
                'fix': "Remove (correct)/(wrong) annotations and use 'correct_words' array"
            })
            
        # Verify correct_words are in passage
        for idx, ans in enumerate(correct_words):
            if ans not in passage:
                violations.append({
                    'type': 'INVALID_ANSWER',
                    'severity': 'critical',
                    'issue': f"mark-the-words '{title}' answer '{ans}' not found in passage",
                    'fix': f"Ensure '{ans}' is exactly present in the passage field"
                })

    return violations


def check_hints_in_activities(activities: list) -> list[dict]:
    """Check for hint fields in activities (all should be removed)."""
    violations = []

    if not activities or not isinstance(activities, list):
        return violations

    for activity in activities:
        act_type = activity.type if hasattr(activity, 'type') else activity.get('type', 'unknown')
        title = getattr(activity, 'title', 'Untitled')
        if not title and isinstance(activity, dict):
            title = activity.get('title', 'Untitled')

        # Check activity-level hint
        if (hasattr(activity, 'hint') and activity.hint) or (isinstance(activity, dict) and 'hint' in activity):
            violations.append({
                'type': 'HINT_IN_ACTIVITY',
                'severity': 'critical',
                'issue': f"{act_type} activity '{title}' has activity-level hint field",
                'fix': "Remove all 'hint' fields from activities (they break activities and provide no real pedagogical value)"
            })
            continue

        # Check item-level hints
        items = getattr(activity, 'items', [])
        if not items and isinstance(activity, dict):
            items = activity.get('items', [])
            
        for idx, item in enumerate(items):
            if hasattr(item, 'hint') and item.hint:
                violations.append({
                    'type': 'HINT_IN_ACTIVITY',
                    'severity': 'critical',
                    'issue': f"{act_type} activity '{title}' has item-level hint in item {idx + 1}",
                    'fix': "Remove all 'hint' fields from activity items (they break activities and provide no real pedagogical value)"
                })
                break
            elif isinstance(item, dict) and 'hint' in item:
                violations.append({
                    'type': 'HINT_IN_ACTIVITY',
                    'severity': 'critical',
                    'issue': f"{act_type} activity '{title}' has item-level hint in item {idx + 1}",
                    'fix': "Remove all 'hint' fields from activity items (they break activities and provide no real pedagogical value)"
                })
                break

    return violations


def check_error_correction_hints(activities: list) -> list[dict]:
    """
    Check for error-correction activities where the error word is highlighted in the sentence.

    This is a critical pedagogical issue: highlighting the error word (with bold, italics, or other
    formatting) ruins the activity by giving away the answer. Students should find the error themselves.

    Example of violation:
      sentence: "Вона має дивне **почуття** у пальцях."
      error: "почуття"

    The error word is highlighted with ** which acts as a hint.
    """
    violations = []

    if not activities or not isinstance(activities, list):
        return violations

    for activity in activities:
        act_type = activity.type if hasattr(activity, 'type') else activity.get('type')
        if act_type != 'error-correction':
            continue

        title = getattr(activity, 'title', 'Untitled')
        if not title and isinstance(activity, dict):
            title = activity.get('title', 'Untitled')

        items = getattr(activity, 'items', [])
        if not items and isinstance(activity, dict):
            items = activity.get('items', [])

        for idx, item in enumerate(items):
            # Get sentence and error fields
            sentence = None
            error = None

            if hasattr(item, 'sentence'):
                sentence = item.sentence
            elif isinstance(item, dict):
                sentence = item.get('sentence', '')

            if hasattr(item, 'error'):
                error = item.error
            elif isinstance(item, dict):
                error = item.get('error', '')

            if not sentence or not error:
                continue

            # Check if error word is highlighted in sentence
            # Check for: **word**, *word*, __word__, _word_
            error_str = str(error).strip()
            sentence_str = str(sentence)

            # Build regex patterns for different markdown formatting
            patterns = [
                rf'\*\*{re.escape(error_str)}\*\*',  # **word**
                rf'\*{re.escape(error_str)}\*',      # *word*
                rf'__{re.escape(error_str)}__',      # __word__
                rf'_{re.escape(error_str)}_',        # _word_
            ]

            for pattern in patterns:
                if re.search(pattern, sentence_str, re.IGNORECASE):
                    violations.append({
                        'type': 'ERROR_WORD_HIGHLIGHTED',
                        'severity': 'critical',
                        'issue': f"error-correction activity '{title}' item {idx + 1}: error word '{error_str}' is highlighted in sentence (ruins activity)",
                        'fix': f"Remove formatting from '{error_str}' in sentence. Error-correction activities should NOT highlight the error word - students must find it themselves."
                    })
                    break  # Only report once per item

    return violations


def check_malformed_cloze_activities(activities: list) -> list[dict]:
    """Check for cloze activities with complete sentences as blanks."""
    violations = []

    if not activities or not isinstance(activities, list):
        return violations

    for activity in activities:
        act_type = activity.type if hasattr(activity, 'type') else activity.get('type')
        if act_type != 'cloze':
            continue

        title = getattr(activity, 'title', 'Untitled')
        if not title and isinstance(activity, dict):
            title = activity.get('title', 'Untitled')
            
        passage = getattr(activity, 'passage', '')
        if not passage and isinstance(activity, dict):
            passage = activity.get('passage', '')

        if not passage:
            continue

        # Extract all blanks from passage: {option1|option2|option3}
        blank_pattern = r'\{([^}]+)\}'
        blanks = re.findall(blank_pattern, passage)

        if not blanks:
            continue

        # Check if this looks like a malformed dialogue-line cloze
        dialogue_line_count = 0
        complete_sentence_count = 0

        for blank in blanks:
            options = [opt.strip() for opt in blank.split('|')]

            # Check each option in this blank
            for opt in options:
                # Check if it's a complete sentence (5+ words)
                word_count = len(opt.split())

                # Check if it contains dialogue markers or ends with sentence punctuation
                has_dialogue_marker = '—' in opt or '«' in opt or '»' in opt
                ends_with_punctuation = opt.endswith(('.', '?', '!'))

                if word_count >= 5 and (has_dialogue_marker or ends_with_punctuation):
                    dialogue_line_count += 1
                    break  # One option is enough to flag this blank

                if word_count >= 5:
                    complete_sentence_count += 1
                    break

        # If most blanks look like complete dialogue lines, flag it
        total_blanks = len(blanks)
        if dialogue_line_count >= total_blanks * 0.5:  # 50% or more
            violations.append({
                'type': 'MALFORMED_CLOZE',
                'severity': 'critical',
                'issue': f"Cloze activity '{title}' has dialogue lines as blanks (should be word/phrase blanks)",
                'fix': f"Convert to proper cloze format with word/phrase blanks, or use a different activity type. Found {dialogue_line_count}/{total_blanks} blanks with complete dialogue lines."
            })

    return violations


def check_cloze_syntax_errors(activities: list) -> list[dict]:
    """Check for cloze activities with invalid syntax in blanks."""
    violations = []

    if not activities or not isinstance(activities, list):
        return violations

    for activity in activities:
        act_type = activity.type if hasattr(activity, 'type') else activity.get('type')
        if act_type != 'cloze':
            continue

        title = getattr(activity, 'title', 'Untitled')
        if not title and isinstance(activity, dict):
            title = activity.get('title', 'Untitled')
            
        passage = getattr(activity, 'passage', '')
        if not passage and isinstance(activity, dict):
            passage = activity.get('passage', '')

        if not passage:
            continue

        # Extract all blanks from passage: {option1|option2|option3}
        blank_pattern = r'\{([^}]+)\}'
        blanks = re.findall(blank_pattern, passage)

        if not blanks:
            continue

        # Check for invalid colon syntax inside blanks
        invalid_blanks = []
        for blank in blanks:
            # Check if blank contains a colon (invalid syntax)
            if ':' in blank:
                # Extract a sample for error message
                sample = blank[:50] + '...' if len(blank) > 50 else blank
                invalid_blanks.append(sample)

        if invalid_blanks:
            violations.append({
                'type': 'CLOZE_SYNTAX_ERROR',
                'severity': 'critical',
                'issue': f"Cloze activity '{title}' has invalid syntax with colons inside blanks",
                'fix': f"Remove colons from blanks. Use format {{option1|option2|option3}} not {{option1|word: option2}}. Found {len(invalid_blanks)} invalid blanks."
            })

    return violations


def check_error_correction_format(activities: list) -> list[dict]:
    """Check for malformed error-correction activities."""
    violations = []

    if not activities or not isinstance(activities, list):
        return violations

    for activity in activities:
        act_type = activity.type if hasattr(activity, 'type') else activity.get('type')
        if act_type != 'error-correction':
            continue

        title = getattr(activity, 'title', 'Untitled')
        if not title and isinstance(activity, dict):
            title = activity.get('title') or activity.get('question') or 'Untitled'
            
        items = getattr(activity, 'items', [])
        if not items and isinstance(activity, dict):
            items = activity.get('items', [])

        placeholder_count = 0

        for idx, item in enumerate(items):
            sentence = getattr(item, 'sentence', '')
            error = getattr(item, 'error', '')
            answer = getattr(item, 'answer', '')
            
            if not sentence and isinstance(item, dict):
                sentence = item.get('sentence', '')
                error = item.get('error', '')
                answer = item.get('answer', '')

            # Check if using placeholder syntax
            if error == '___' or (isinstance(error, str) and error.strip() == ''):
                placeholder_count += 1
            # Check if sentence contains → ___ pattern (transformation exercise, not error-correction)
            elif sentence and '→' in sentence and '___' in sentence:
                placeholder_count += 1
            # Allow 'none' or 'correct' as valid values for "no error" sentences
            elif isinstance(error, str) and error.lower() in ('none', 'correct'):
                continue
            # Allow sentence transformation format
            elif not sentence and error and answer and len(str(error).split()) >= 3 and len(str(answer).split()) >= 3:
                continue
            # Check if error word is not in sentence (case-insensitive, quote-normalized)
            elif error and sentence:
                def normalize_quotes(s):
                    return s.replace('«', '"').replace('»', '"').replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
                if normalize_quotes(str(error).lower()) not in normalize_quotes(str(sentence).lower()):
                    placeholder_count += 1

        # If items use placeholders, flag it
        if placeholder_count > 0:
            violations.append({
                'type': 'MALFORMED_ERROR_CORRECTION',
                'severity': 'critical',
                'issue': f"Error-correction activity '{title}' uses placeholder syntax instead of real errors",
                'fix': f"Convert to proper error-correction format with real error words in sentences, or change to fill-in activity. Found {placeholder_count}/{len(items)} items with placeholders/missing errors."
            })

    return violations


def check_advanced_activities_presence(found_types: list[str], level_code: str, module_focus: str = None) -> list[dict]:
    """Check if advanced levels have required advanced activity types."""
    violations = []
    
    # Only enforce for non-checkpoint modules
    if module_focus == 'checkpoint':
        return []
        
    # Required for B2+ 
    if level_code in ('B2', 'C1', 'C2', 'LIT'):
        # Get required types for this specific focus
        # Default to 'default' requirements if focus not found or None
        req_key = module_focus if module_focus in REQUIRED_ADVANCED_TYPES else 'default'
        required_types = REQUIRED_ADVANCED_TYPES.get(req_key, [])
        
        for req_type in required_types:
            if req_type not in found_types:
                violations.append({
                    'type': 'MISSING_ADVANCED_ACTIVITY',
                    'severity': 'warning',
                    'issue': f"B2+ module (focus: {module_focus}) missing advanced activity type: {req_type}",
                    'fix': f"Add a {req_type} activity to meet advanced richness standards."
                })
                
    return violations


def check_yaml_activity_types(activities: list) -> list[dict]:
    """Check if all activity types in YAML are valid.

    Args:
        activities: List of activity dicts from YAML

    Returns:
        List of violations for invalid activity types
    """
    violations = []

    if not activities or not isinstance(activities, list):
        return violations

    for i, activity in enumerate(activities):
        if not isinstance(activity, dict):
            continue

        act_type = activity.get('type', '').lower()
        if not act_type:
            violations.append({
                'type': 'INVALID_ACTIVITY_TYPE',
                'severity': 'error',
                'issue': f"Activity #{i+1} missing 'type' field",
                'fix': "Add 'type' field to activity"
            })
            continue

        if act_type not in VALID_ACTIVITY_TYPES:
            violations.append({
                'type': 'INVALID_ACTIVITY_TYPE',
                'severity': 'error',
                'issue': f"Invalid activity type '{act_type}' in YAML",
                'fix': f"Use supported type: {', '.join(sorted(VALID_ACTIVITY_TYPES))}"
            })

    return violations