"""
Vocabulary integration and coverage checks.

Verifies that core vocabulary from the Curriculum Plan is actually utilized
within module lesson text and activities.
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Set

def get_plan_words(project_root: Path, level_code: str, module_num: int) -> List[str]:
    """Extract core vocabulary words for a module from its Curriculum Plan."""
    plan_file = project_root / "docs" / "l2-uk-en" / f"{level_code.upper()}-CURRICULUM-PLAN.md"
    if not plan_file.exists():
        return []
        
    content = plan_file.read_text(encoding='utf-8')
    # Support both "Module 01" and "Module 1"
    module_pattern = re.compile(rf'#### Module\s+0?{module_num}:')
    vocab_pattern = re.compile(r'**Vocabulary\s+\(\d+\s+words\):**\n(.*?)(?=\n\n|\n#|\Z)', re.DOTALL)
    
    parts = re.split(r'(?=#### Module)', content)
    for part in parts:
        if module_pattern.search(part):
            vocab_match = vocab_pattern.search(part)
            if vocab_match:
                raw_vocab = vocab_match.group(1).strip()
                clean_vocab = re.sub(r'\(.*?\)', '', raw_vocab)
                return [w.strip().lower() for w in clean_vocab.split(',') if w.strip()]
    return []

def check_vocabulary_integration(
    content: str, 
    level_code: str, 
    module_num: int, 
    yaml_activities: list = None
) -> Dict[str, Any]:
    """
    Calculate integration rates for core vocabulary.
    
    Returns a dict with lesson_rate, activity_rate, and missing_words.
    """
    project_root = Path(__file__).parent.parent.parent
    expected_words = get_plan_words(project_root, level_code, module_num)
    
    if not expected_words:
        return {'lesson_rate': 0, 'activity_rate': 0, 'missing': [], 'total': 0}
        
    md_text = content.lower()
    
    # Extract activity text from YAML if provided, or from markdown
    act_text = ""
    if yaml_activities:
        # Convert Activity objects to strings for searching
        for act in yaml_activities:
            act_text += str(act) + "\n"
    else:
        # Fallback to activity section in MD
        act_match = re.search(r'#\s*(Activities|Вправи)\s*\n(.*?)(?=#|\Z)', content, re.DOTALL | re.IGNORECASE)
        if act_match:
            act_text = act_match.group(2).lower()
            
    used_in_lesson = []
    used_in_activities = []
    
    for word in expected_words:
        # Cyrillic-aware word boundary check
        pattern = re.compile(rf'(?<![а-яіїєґ]){re.escape(word)}(?![а-яіїєґ])')
        
        if pattern.search(md_text):
            used_in_lesson.append(word)
        if act_text and pattern.search(act_text.lower()):
            used_in_activities.append(word)
            
    total = len(expected_words)
    lesson_rate = (len(used_in_lesson) / total) * 100 if total > 0 else 0
    act_rate = (len(used_in_activities) / total) * 100 if total > 0 else 0
    
    missing = [w for w in expected_words if w not in used_in_lesson and w not in used_in_activities]
    
    return {
        'lesson_rate': lesson_rate,
        'activity_rate': act_rate,
        'missing': missing,
        'total': total,
        'expected': expected_words
    }
