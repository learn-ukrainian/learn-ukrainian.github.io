"""
Content recall detection for content-heavy modules.

Detects activities that test content/historical recall rather than
Ukrainian language comprehension in B2 History and C1 Literature/Biography modules.

Issue: #359 - Content Modules Should Test Language, Not Content Recall
See: docs/dev/CONTENT_MODULE_ENHANCEMENT.md
"""

import re
from typing import List, Dict, Any, Tuple


# Patterns that indicate content recall (BAD - testing knowledge, not language)
FORBIDDEN_PATTERNS = {
    'date_recall': r'[Уу]\s*якому\s*роц[іi]',  # "У якому році..."
    'when_recall': r'[Кк]оли\s+(був|була|було|відбу)',  # "Коли був/відбувся..."
    'name_recall': r'[Хх]то\s*був',  # "Хто був..."
    'who_wrote': r'[Хх]то\s*написав',  # "Хто написав..."
    'count_recall': r'[Сс]кільки',  # "Скільки..."
    'what_symbolizes': r'[Щщ]о\s*символ[іi]зу[єе]',  # "Що символізує..." without context
    'where_born': r'[Дд]е\s*народи',  # "Де народився..."
    'where_studied': r'[Дд]е\s*навча',  # "Де навчався..."
}

# Patterns that indicate proper text reference (GOOD - testing comprehension)
REQUIRED_PATTERNS = {
    'text_reference': r'[Зз]гідно\s*з\s*текстом',  # "Згідно з текстом..."
    'author_describes': r'[Яя]к\s*автор\s*(описує|характеризує|пояснює|інтерпретує|тлумачить)',
    'module_text': r'[Уу]\s*тексті\s*модуля',  # "У тексті модуля..."
    'author_argument': r'[Яя]кий\s*аргумент\s*автор',  # "Який аргумент автор..."
    'author_highlights': r'[Яя]ку\s*(функцію|роль)\s*автор\s*(підкреслює|виділяє)',
    'in_text': r'[Уу]\s*тексті\s+(зазначено|автор)',  # "У тексті зазначено..."
    'according_to_analysis': r'[Зз]гідно\s*з\s*аналізом',  # "Згідно з аналізом..."
}


def check_content_recall_violations(
    content: str,
    level: str,
    module_type: str = "unknown"
) -> List[Dict[str, Any]]:
    """
    Check for content recall violations in quiz/true-false activities.
    
    Content-heavy modules (B2 history, C1 literature/biography/folk/arts) should
    test Ukrainian language comprehension, not factual recall.
    
    Args:
        content: Module content string
        level: Level code (e.g., 'B2', 'C1')
        module_type: Focus type (e.g., 'history', 'literature', 'biography')
        
    Returns:
        List of violation dicts with type, severity, message, suggestion
    """
    violations = []
    
    # Only check content-heavy modules
    content_heavy_types = ['history', 'literature', 'biography', 'folk-culture', 'fine-arts']
    if module_type not in content_heavy_types:
        return []
    
    # Extract quiz and true-false activities
    activity_pattern = r'##\s*(quiz|true-false)[:\s].*?(?=\n##\s|\n#\s|$)'
    activities = re.findall(activity_pattern, content, re.DOTALL | re.IGNORECASE)
    
    # Get full activity blocks for analysis
    activity_blocks = re.finditer(
        r'(##\s*(quiz|true-false)[:\s][^\n]*\n)(.*?)(?=\n##\s|\n#\s|$)',
        content,
        re.DOTALL | re.IGNORECASE
    )
    
    for match in activity_blocks:
        activity_header = match.group(1).strip()
        activity_type = match.group(2).lower()
        activity_content = match.group(3)
        
        # Check for forbidden patterns (content recall)
        for pattern_name, pattern in FORBIDDEN_PATTERNS.items():
            if re.search(pattern, activity_content, re.IGNORECASE):
                # Check if it's in a proper context (e.g., "Згідно з текстом, у якому році...")
                line_with_pattern = None
                for line in activity_content.split('\n'):
                    if re.search(pattern, line, re.IGNORECASE):
                        line_with_pattern = line.strip()[:80]
                        break
                
                # Allow if preceded by text reference pattern
                has_text_ref = any(
                    re.search(req_pattern, activity_content[:activity_content.find(line_with_pattern) if line_with_pattern else 0], re.IGNORECASE)
                    for req_pattern in REQUIRED_PATTERNS.values()
                )
                
                if not has_text_ref:
                    violations.append({
                        'type': 'CONTENT_RECALL',
                        'severity': 'warning',
                        'activity': activity_header[:50],
                        'pattern': pattern_name,
                        'message': f"Question appears to test content recall, not Ukrainian comprehension",
                        'suggestion': f"Rewrite to start with 'Згідно з текстом, як автор...'",
                        'example': line_with_pattern or "See activity content"
                    })
        
        # Check if quiz has any text reference patterns (for B2/C1)
        if level in ['B2', 'C1']:
            has_reference = any(
                re.search(pattern, activity_content, re.IGNORECASE)
                for pattern in REQUIRED_PATTERNS.values()
            )
            
            # Count questions in the activity
            questions = re.findall(r'^\d+\.', activity_content, re.MULTILINE)
            
            if not has_reference and len(questions) > 0:
                violations.append({
                    'type': 'MISSING_TEXT_REFERENCE',
                    'severity': 'warning',
                    'activity': activity_header[:50],
                    'message': f"Quiz should reference module text ('Згідно з текстом...')",
                    'suggestion': "Start questions with 'Згідно з текстом, як автор...'"
                })
    
    return violations


def check_content_heavy_activity_count(
    activity_count: int,
    module_type: str
) -> List[Dict[str, Any]]:
    """
    Validate activity count for content-heavy modules.
    
    Content-heavy modules should have 10-12 activities, not 14+.
    
    Args:
        activity_count: Number of activities in module
        module_type: Focus type (e.g., 'history', 'literature')
        
    Returns:
        List of violation dicts
    """
    violations = []
    
    content_heavy_types = ['history', 'literature', 'biography', 'folk-culture', 'fine-arts']
    if module_type not in content_heavy_types:
        return []
    
    if activity_count > 12:
        violations.append({
            'type': 'TOO_MANY_ACTIVITIES',
            'severity': 'warning',
            'message': f"Content-heavy modules should have 10-12 activities, found {activity_count}",
            'suggestion': "Reduce to 10-12 high-quality language-focused activities"
        })
    
    if activity_count < 10:
        violations.append({
            'type': 'TOO_FEW_ACTIVITIES',
            'severity': 'warning',
            'message': f"Content-heavy modules should have 10-12 activities, found {activity_count}",
            'suggestion': "Add activities to reach 10-12 total"
        })
    
    return violations


def check_fill_in_year_answers(content: str, level: str, module_type: str) -> List[Dict[str, Any]]:
    """
    Check for fill-in activities where the answer is a year (4-digit number).

    Years as fill-in answers test factual recall, not language skills.

    Args:
        content: Module content string
        level: Level code (e.g., 'B2', 'C1')
        module_type: Focus type (e.g., 'history', 'literature')

    Returns:
        List of violation dicts
    """
    violations = []

    # Only check content-heavy modules
    content_heavy_types = ['history', 'literature', 'biography', 'folk-culture', 'fine-arts']
    if module_type not in content_heavy_types:
        return []

    # Find fill-in activity blocks
    fill_in_pattern = r'(##\s*fill-in[:\s][^\n]*\n)(.*?)(?=\n##\s|\n#\s|$)'
    fill_in_blocks = re.finditer(fill_in_pattern, content, re.DOTALL | re.IGNORECASE)

    for match in fill_in_blocks:
        activity_header = match.group(1).strip()
        activity_content = match.group(2)

        # Find answers that are years (4-digit numbers between 1000-2100)
        answer_pattern = r'>\s*\[!answer\]\s*(\d{4})\s*$'
        year_answers = re.findall(answer_pattern, activity_content, re.MULTILINE)

        for year in year_answers:
            year_int = int(year)
            if 1000 <= year_int <= 2100:
                # Find the sentence with this answer
                sentence_pattern = rf'\d+\.\s*([^\n]+)\n.*?>\s*\[!answer\]\s*{year}'
                sentence_match = re.search(sentence_pattern, activity_content, re.DOTALL)
                sentence = sentence_match.group(1)[:60] if sentence_match else "See activity"

                violations.append({
                    'type': 'FILL_IN_YEAR_ANSWER',
                    'severity': 'warning',
                    'activity': activity_header[:50],
                    'message': f"Fill-in answer is a year ({year}) - tests factual recall, not vocabulary",
                    'suggestion': "Replace with collocation or vocabulary test",
                    'example': sentence
                })

    return violations


def check_cloze_year_answers(content: str, level: str, module_type: str) -> List[Dict[str, Any]]:
    """
    Check for cloze activities where blanks are years.

    Args:
        content: Module content string
        level: Level code
        module_type: Focus type

    Returns:
        List of violation dicts
    """
    violations = []

    content_heavy_types = ['history', 'literature', 'biography', 'folk-culture', 'fine-arts']
    if module_type not in content_heavy_types:
        return []

    # Find cloze activity blocks
    cloze_pattern = r'(##\s*cloze[:\s][^\n]*\n)(.*?)(?=\n##\s|\n#\s|$)'
    cloze_blocks = re.finditer(cloze_pattern, content, re.DOTALL | re.IGNORECASE)

    for match in cloze_blocks:
        activity_header = match.group(1).strip()
        activity_content = match.group(2)

        # Find cloze blanks that have years as options: {1861|1865|1870}
        year_blank_pattern = r'\{(\d{4})\|[^}]*\}'
        year_blanks = re.findall(year_blank_pattern, activity_content)

        for year in year_blanks:
            year_int = int(year)
            if 1000 <= year_int <= 2100:
                violations.append({
                    'type': 'CLOZE_YEAR_BLANK',
                    'severity': 'warning',
                    'activity': activity_header[:50],
                    'message': f"Cloze blank is a year ({year}) - tests factual recall",
                    'suggestion': "Replace with vocabulary or collocation blanks"
                })
                break  # One warning per activity is enough

    return violations


def is_content_heavy_module(
    level: str,
    module_num: int,
    focus: str = ""
) -> bool:
    """
    Determine if a module is content-heavy based on level, number, or focus.

    Content-heavy modules:
    - B2 History: M71-131
    - C1 Literature: M146-160
    - C1 Biography: M36-100
    - C1 Folk Culture: M121-145
    - C1 Fine Arts: various

    Args:
        level: Level code (e.g., 'B2', 'C1')
        module_num: Module number
        focus: Focus field value if available

    Returns:
        True if module is content-heavy
    """
    content_heavy_focuses = ['history', 'literature', 'biography', 'folk-culture', 'fine-arts']

    # Check by explicit focus
    if focus.lower() in content_heavy_focuses:
        return True

    # Check by level and module number
    if level == 'B2' and 71 <= module_num <= 131:
        return True  # B2 History range

    if level == 'C1':
        if 146 <= module_num <= 160:
            return True  # C1 Literature
        if 36 <= module_num <= 100:
            return True  # C1 Biography
        if 121 <= module_num <= 145:
            return True  # C1 Folk Culture

    return False


def check_yaml_cloze_year_blanks(
    activities: list,
    level: str,
    module_type: str = "unknown"
) -> List[Dict[str, Any]]:
    """
    Check YAML cloze activities for year-based blanks.
    """
    violations = []

    content_heavy_types = ['history', 'literature', 'biography', 'folk-culture', 'fine-arts']
    if module_type not in content_heavy_types:
        return []

    for activity in activities:
        act_type = getattr(activity, 'type', '') or activity.get('type', '').lower()
        if act_type != 'cloze':
            continue

        title = getattr(activity, 'title', 'Cloze')
        passage = getattr(activity, 'passage', '')
        if not passage and isinstance(activity, dict):
            passage = activity.get('passage', '')

        # Find cloze blanks that have years as the first option: {1861|1865|1870}
        year_blank_pattern = r'\{(\d{4})\|[^}]*\}'
        year_blanks = re.findall(year_blank_pattern, passage)

        year_count = 0
        for year in year_blanks:
            year_int = int(year)
            if 1000 <= year_int <= 2100:
                year_count += 1

        if year_count > 0:
            violations.append({
                'type': 'CLOZE_YEAR_BLANK',
                'severity': 'warning',
                'activity': str(title)[:50],
                'message': f"Cloze has {year_count} year-based blank(s) - tests factual recall, not language",
                'suggestion': "Replace year blanks with vocabulary/collocation blanks"
            })

    return violations


def check_yaml_fill_in_year_answers(
    activities: list,
    level: str,
    module_type: str = "unknown"
) -> List[Dict[str, Any]]:
    """
    Check YAML fill-in activities for year-based answers.
    """
    violations = []

    content_heavy_types = ['history', 'literature', 'biography', 'folk-culture', 'fine-arts']
    if module_type not in content_heavy_types:
        return []

    for activity in activities:
        act_type = getattr(activity, 'type', '') or activity.get('type', '').lower()
        if act_type != 'fill-in':
            continue

        title = getattr(activity, 'title', 'Fill-in')
        items = getattr(activity, 'items', [])
        if not items and isinstance(activity, dict):
            items = activity.get('items', [])

        year_count = 0
        for item in items:
            answer = str(getattr(item, 'answer', '')) or str(item.get('answer', ''))
            if answer.isdigit() and len(answer) == 4:
                year_int = int(answer)
                if 1000 <= year_int <= 2100:
                    year_count += 1

        if year_count > 0:
            violations.append({
                'type': 'FILL_IN_YEAR_ANSWER',
                'severity': 'warning',
                'activity': str(title)[:50],
                'message': f"Fill-in has {year_count} year-based answer(s) - tests factual recall, not vocabulary",
                'suggestion': "Replace year answers with vocabulary/collocation answers"
            })

    return violations


def run_all_content_recall_checks(
    content: str,
    level: str,
    module_type: str = "unknown",
    yaml_activities: list = None
) -> List[Dict[str, Any]]:
    """
    Run all content recall detection checks.
    """
    all_violations = []

    # Markdown-based activity checks removed (Issue #394)

    # Run YAML-based checks if activities provided (Now the primary source)
    if yaml_activities:
        all_violations.extend(check_yaml_cloze_year_blanks(yaml_activities, level, module_type))
        all_violations.extend(check_yaml_fill_in_year_answers(yaml_activities, level, module_type))

    return all_violations
