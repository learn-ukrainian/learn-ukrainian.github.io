"""
Activity-related validation checks.

Validates activity sequencing, structure, variety, and level restrictions.
"""

import re
from collections import Counter
from ..config import STAGE_ORDER, ACTIVITY_RESTRICTIONS, ACTIVITY_COMPLEXITY, VALID_ACTIVITY_TYPES

def check_activity_complexity(content: str, level_code: str, module_num: int = 1) -> list[dict]:
    """
    Check if activities meet complexity requirements (word count, item count, structure).
    Strictly enforces rules from MODULE-RICHNESS-GUIDELINES-v2.md.
    
    A1 M01-M05 Exception: Less strict rules for very early modules (alphabet phase).
    """
    violations = []

    # Relax rules for A1 M01-M05 and B1 M01-M05 (bridge modules)
    is_a1_early = (level_code == 'A1' and module_num <= 5)
    is_b1_bridge = (level_code == 'B1' and module_num <= 5)
    
    # 1. Parse all activities
    activity_pattern = r'##\s*([a-z-]+):\s*([^\n]+)\n(.*?)(?=\n##\s|\n#\s|\Z)'
    activities = re.findall(activity_pattern, content, re.DOTALL | re.IGNORECASE)
    
    for act_type, title, body in activities:
        act_type = act_type.lower()
        
        # Skip checking unknown activity types
        if act_type not in ACTIVITY_COMPLEXITY:
            continue
            
        rules = ACTIVITY_COMPLEXITY[act_type].get(level_code).copy() if ACTIVITY_COMPLEXITY[act_type].get(level_code) else None
        
        # If no specific rules for this level (e.g. anagram in A2), restrictions check handles it
        if not rules:
            continue
            
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
        # True bridge: A2 difficulty for content, B1 topics (grammar terminology)
        if is_b1_bridge:
            if act_type == 'quiz':
                rules['min_len'] = 8
                rules['max_len'] = 15
            elif act_type == 'unjumble':
                rules['words_min'] = 8
                rules['words_max'] = 10  # A2 exact
            elif act_type == 'match-up':
                rules['pairs_min'] = 10
                rules['pairs_max'] = 12  # A2 exact
            elif act_type == 'fill-in':
                rules['sent_min'] = 6
                rules['sent_max'] = 8   # A2 exact
            elif act_type == 'true-false':
                rules['min_len'] = 6
                rules['max_len'] = 12   # A2 exact
            elif act_type == 'group-sort':
                rules['groups_min'] = 2
                rules['groups_max'] = 4
                rules['items_min'] = 10  # A2 exact
            elif act_type == 'error-correction':
                rules['errors'] = 1      # A2: 1 error per sentence
                rules['min_len'] = 6
                rules['max_len'] = 10   # A2 exact
            elif act_type == 'cloze':
                rules['sentences'] = [3, 4, 5]
                rules['blanks'] = [3, 4]  # A2 exact
            elif act_type == 'mark-the-words':
                rules['min_len'] = 8
                rules['max_len'] = 12
                rules['marks'] = [2, 3, 4]  # A2 exact
            elif act_type == 'dialogue-reorder':
                rules['lines'] = [4, 5, 6]  # A2 exact
            elif act_type == 'select':
                rules['min_len'] = 6
                rules['max_len'] = 10
                rules['options'] = [4, 5]
                rules['correct'] = [2, 3]  # A2 exact
            elif act_type == 'translate':
                rules['min_len'] = 4
                rules['max_len'] = 8   # A2 exact
        
        # --- Check Item Count ---
        
        items_count = count_items(body)
        min_items = rules.get('min_items', 6)  # Default min 6 if not specified

        
        # Activity-specific item count checks
        if act_type == 'group-sort':
            items_count = len(re.findall(r'^\s*-\s+[^\[]', body, re.MULTILINE))  # Count bullets only
            
            # Check group counts - look for H3 headers that are category names
            # Exclude common non-category H3s like "### Notes" or "### Explanation"
            group_headers = re.findall(r'^\s*###\s+([^\n]+)', body, re.MULTILINE)
            group_count = len([h for h in group_headers if not any(
                skip in h.lower() for skip in ['note', 'explanation', 'hint', 'tip']
            )])
            min_groups = rules.get('groups_min', 2)
            max_groups = rules.get('groups_max', 4)
            
            if not (min_groups <= group_count <= max_groups):
                violations.append({
                    'type': 'COMPLEXITY',
                    'issue': f"group-sort '{title.strip()}' has {group_count} groups (target: {min_groups}-{max_groups})",
                    'fix': f"Adjust number of sorting categories to {min_groups}-{max_groups}."
                })
            
            min_sort_items = rules.get('items_min', 8)
            max_sort_items = rules.get('items_max', 20)
            if not (min_sort_items <= items_count <= max_sort_items):
                violations.append({
                    'type': 'COMPLEXITY',
                    'issue': f"group-sort '{title.strip()}' has {items_count} items (target: {min_sort_items}-{max_sort_items})",
                    'fix': f"Adjust number of items to sort to {min_sort_items}-{max_sort_items}."
                })
        
        elif act_type == 'match-up':
            # Count pairs (lines with | ... |)
            table_rows = re.findall(r'^\s*\|\s*[^|]+\s*\|\s*[^|]+\s*\|', body, re.MULTILINE)
            # Subtract 1 for header, but ensure we don't go negative
            pair_count = max(0, len(table_rows) - 1) if table_rows else 0
            min_pairs = rules.get('pairs_min', 8)
            max_pairs = rules.get('pairs_max', 18)
            
            # If standard markdown table format
            if pair_count > 0:
                if not (min_pairs <= pair_count <= max_pairs):
                    violations.append({
                        'type': 'COMPLEXITY',
                        'issue': f"match-up '{title.strip()}' has {pair_count} pairs (target: {min_pairs}-{max_pairs})",
                        'fix': f"Adjust number of pairs to {min_pairs}-{max_pairs}."
                    })
            # Check for simple list format 1. A -> B
            else:
                pair_count = len(re.findall(r'->', body))
                if pair_count > 0 and not (min_pairs <= pair_count <= max_pairs):
                    violations.append({
                        'type': 'COMPLEXITY',
                        'issue': f"match-up '{title.strip()}' has {pair_count} pairs (target: {min_pairs}-{max_pairs})",
                        'fix': f"Adjust number of pairs to {min_pairs}-{max_pairs}."
                    })

        elif items_count < min_items:
            violations.append({
                'type': 'COMPLEXITY',
                'issue': f"{act_type} '{title.strip()}' has {items_count} items (minimum: {min_items})",
                'fix': f"Add more items. {level_code} {act_type} requires at least {min_items} items."
            })

        # --- Check Content Complexity (Word Counts / Options) ---
        
        # Unjumble / Anagram Structure
        if act_type == 'unjumble':
            # Check separator: Must use slash /
            slash_usage = len(re.findall(r'/', body))
            if slash_usage < items_count:
                 violations.append({
                    'type': 'FORMAT_ERROR',
                    'issue': f"unjumble '{title.strip()}' items must use slash '/' separator",
                    'fix': "Split words with slashes, e.g. 'Я / люблю / каву'."
                })
            
            # Check word counts
            items = re.findall(r'\d+\.\s*([^\n>]+)', body)
            for i, item in enumerate(items, 1):
                words = len(re.findall(r'[\w\u0400-\u04FF]+', item))
                min_w = rules.get('words_min', 4)
                max_w = rules.get('words_max', 20)
                
                # Allow slight variance (+-1) but flag extreme outliers
                if words < min_w - 1 or words > max_w + 2:
                     violations.append({
                        'type': 'COMPLEXITY_WORD_COUNT',
                        'issue': f"unjumble '{title.strip()}' item {i} has {words} words (target: {min_w}-{max_w})",
                        'fix': f"Adjust sentence length to {min_w}-{max_w} words to match {level_code} complexity."
                    })

        # Anagram Structure
        elif act_type == 'anagram':
            # Check separator: Must use spaces, NO slashes (only in item lines)
            items = re.findall(r'\d+\.\s*([^\n>]+)', body)
            for item in items:
                if '/' in item:
                    violations.append({
                        'type': 'FORMAT_ERROR',
                        'issue': f"anagram '{title.strip()}' item '{item.strip()}' must use SPACES separator, not slashes",
                        'fix': "Use spaces between letters: 'л і т е р а'."
                    })
                    break
        
        # Fill-in Structure
        elif act_type == 'fill-in':
            # Check placeholder: Must use ___
            if '___' not in body:
                 violations.append({
                    'type': 'FORMAT_ERROR',
                    'issue': f"fill-in '{title.strip()}' missing '___' placeholders",
                    'fix': "Use exactly '___' (three underscores) for blanks."
                })
            
            # Check missing options block
            if 'fill-in' in body and '[!options]' not in body:
                 violations.append({
                    'type': 'FORMAT_ERROR',
                    'issue': f"fill-in '{title.strip()}' missing mandatory [!options] block",
                    'fix': "All fill-in activities must provide [!options] for the user."
                })
        
        # Quiz Options Check
        elif act_type == 'quiz':
            # Check number of options per question (standard markdown list or [!options])
            questions = re.split(r'\n\d+\.', body)[1:] # Split by numbered list
            min_len = rules.get('min_len', 5)
            max_len = rules.get('max_len', 30)
            
            for i, q in enumerate(questions, 1):
                # Count prompt words
                prompt_line = q.split('\n')[0]
                prompt_words = len(re.findall(r'[\w\u0400-\u04FF]+', prompt_line))
                if prompt_words < min_len or prompt_words > max_len + 5: # Allow generous buffer
                     violations.append({
                        'type': 'COMPLEXITY_WORD_COUNT',
                        'issue': f"quiz '{title.strip()}' Q{i} prompt length {prompt_words} (target: {min_len}-{max_len})",
                        'fix': f"Adjust prompt length to {min_len}-{max_len} words."
                    })
                
                # Count options
                options_count = len(re.findall(r'-\s*\[', q))
                # Also check for [!options] block style
                if options_count == 0 and '[!options]' in q:
                    options_block = re.search(r'\[!options\](.*?)(?=\n>|\n\d|\Z)', q, re.DOTALL)
                    if options_block:
                        options_count = len(re.findall(r'\|', options_block.group(1))) + 1
                
                target_opts = rules.get('options', [4])
                if isinstance(target_opts, int): target_opts = [target_opts]
                
                # Skip check if no options found (might be parsing error)
                if options_count > 0 and options_count not in target_opts and options_count < min(target_opts):
                     violations.append({
                        'type': 'COMPLEXITY_OPTIONS',
                        'issue': f"quiz '{title.strip()}' Q{i} has {options_count} options (target: {target_opts})",
                        'fix': f"Provide {target_opts} options for {level_code} quizzes."
                    })

    return violations


def check_activity_sequencing(content: str, pedagogy: str) -> list[dict]:
    """Check activity sequencing based on PPP or TTT methodology."""
    violations = []

    # Extract activity stages from headers
    activity_stages = []
    for match in re.finditer(
        r'##\s+\w+[^:]*:\s*[^\[]*\[stage:\s*([^\]]+)\]',
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
        r'##\s*(quiz|match-up|fill-in|true-false|group-sort|unjumble|error-correction|anagram|cloze|select|translate|dialogue-reorder|mark-the-words):',
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
        r'##\s*(quiz|match-up|fill-in|true-false|group-sort|unjumble|error-correction|anagram|cloze|select|translate|dialogue-reorder|mark-the-words):',
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
        r'##\s*(quiz|match-up|fill-in|true-false|group-sort|unjumble|error-correction|anagram|cloze|select|translate|dialogue-reorder|mark-the-words):',
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


def count_items(text: str) -> int:
    """Count items in an activity section."""
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
    bullets = len(re.findall(r'^\s*-\s+[^\[]', text, re.MULTILINE))

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
        if not m.startswith('!') and not re.match(r'[^\]]+\]\(', m)
    ])
    # Also match *word* asterisks (inline format)
    mark_words_asterisks = len(re.findall(r'\*[^*]+\*', text))
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
    malformed_pattern = rf'^##\s*({activity_types_pattern})\s*$'
    malformed_matches = re.findall(malformed_pattern, content, re.MULTILINE | re.IGNORECASE)

    for act_type in malformed_matches:
        violations.append({
            'type': 'MALFORMED_ACTIVITY_HEADER',
            'issue': f"Activity header '## {act_type}' missing required ': Title' suffix",
            'fix': f"Change to '## {act_type}: Descriptive Title' format. Without the colon and title, the MDX generator will skip this activity entirely."
        })

    # Also check for headers with colon but no title
    empty_title_pattern = rf'^##\s*({activity_types_pattern}):\s*$'
    empty_title_matches = re.findall(empty_title_pattern, content, re.MULTILINE | re.IGNORECASE)

    for act_type in empty_title_matches:
        violations.append({
            'type': 'MALFORMED_ACTIVITY_HEADER',
            'issue': f"Activity header '## {act_type}:' has empty title",
            'fix': f"Add a descriptive Ukrainian title after the colon: '## {act_type}: Назва вправи'"
        })

    return violations


def check_mark_the_words_format(activities: list[dict]) -> list[dict]:
    """Check for malformed mark-the-words activities in YAML.
    
    The md_to_yaml conversion script incorrectly copied markdown annotations
    (correct)/(wrong) into YAML. These should have been stripped.
    
    Wrong:  '*слово*(correct)'
    Correct: '*слово*'
    
    Args:
        activities: List of activity dicts from YAML
        
    Returns:
        List of violations
    """
    violations = []
    
    if not activities or not isinstance(activities, list):
        return violations
    
    for activity in activities:
        if not isinstance(activity, dict):
            continue
            
        if activity.get('type') != 'mark-the-words':
            continue
            
        text = activity.get('text', '')
        title = activity.get('title', 'Untitled')
        
        if '(correct)' in text or '(wrong)' in text:
            violations.append({
                'type': 'MALFORMED_MARK_THE_WORDS',
                'severity': 'critical',
                'issue': f"mark-the-words '{title}' contains (correct)/(wrong) annotations",
                'fix': "Run: .venv/bin/python scripts/fix_mark_the_words.py"
            })
    
    return violations
