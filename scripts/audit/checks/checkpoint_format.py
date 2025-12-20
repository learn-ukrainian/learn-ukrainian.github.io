"""
Checkpoint Format Validation

Validates that checkpoint modules use the correct Skill-based structure:
- ## Skill X: [Name]
- ### Model:
- ### Practice:
- ### Self-Check

Checkpoints with alternative structures (Діагностика/Аналіз/Поглиблення)
are flagged for rewrite.
"""

import re
from pathlib import Path


def check_checkpoint_format(content: str, frontmatter: dict, level: str, module_num: int) -> list[dict]:
    """
    Validate checkpoint modules have correct Skill-based structure.
    
    Returns list of violations if checkpoint format is incorrect.
    """
    violations = []
    
    # Only check checkpoint modules
    focus = frontmatter.get('focus', '').lower()
    if focus != 'checkpoint':
        return violations
    
    # Count Skill-based structure elements
    skill_count = len(re.findall(r'^## Skill\s*\d*:', content, re.MULTILINE))
    model_count = len(re.findall(r'^### Model:', content, re.MULTILINE))
    practice_count = len(re.findall(r'^### Practice:', content, re.MULTILINE))
    self_check_count = len(re.findall(r'^### Self-Check', content, re.MULTILINE))
    
    # Check for alternative (incorrect) structure
    has_diagnostika = bool(re.search(r'^## Діагностика', content, re.MULTILINE))
    has_analiz = bool(re.search(r'^## Аналіз', content, re.MULTILINE))
    has_pogliblennya = bool(re.search(r'^## Поглиблення', content, re.MULTILINE))
    
    alternative_structure = has_diagnostika or has_analiz or has_pogliblennya
    
    # Checkpoint should have Skill sections
    if skill_count == 0 and alternative_structure:
        violations.append({
            'type': 'checkpoint_format',
            'severity': 'error',
            'issue': f"{level.upper()} M{module_num:02d} checkpoint uses incorrect Діагностика/Аналіз structure",
            'fix': "Rewrite to Skill-based format: ## Skill X: [name] → ### Model: → ### Practice: → ### Self-Check",
            'details': {
                'has_diagnostika': has_diagnostika,
                'has_analiz': has_analiz,
                'has_pogliblennya': has_pogliblennya,
                'skill_count': skill_count,
            }
        })
    elif skill_count == 0:
        violations.append({
            'type': 'checkpoint_format',
            'severity': 'warning',
            'issue': f"{level.upper()} M{module_num:02d} checkpoint missing Skill sections",
            'fix': "Add ## Skill X: sections with ### Model:, ### Practice:, ### Self-Check subsections",
            'details': {
                'skill_count': skill_count,
                'model_count': model_count,
                'practice_count': practice_count,
            }
        })
    
    # If has Skills but missing subsections
    if skill_count > 0:
        if model_count == 0:
            violations.append({
                'type': 'checkpoint_format',
                'severity': 'warning',
                'issue': f"{level.upper()} M{module_num:02d} checkpoint has Skills but missing ### Model: sections",
                'fix': "Add ### Model: section under each Skill with annotated examples",
                'details': {'skill_count': skill_count, 'model_count': model_count}
            })
        
        if practice_count == 0:
            violations.append({
                'type': 'checkpoint_format',
                'severity': 'warning',
                'issue': f"{level.upper()} M{module_num:02d} checkpoint has Skills but missing ### Practice: sections",
                'fix': "Add ### Practice: section under each Skill with exercises",
                'details': {'skill_count': skill_count, 'practice_count': practice_count}
            })
    
    # Check for bold-style headers (old format)
    bold_model = len(re.findall(r'^\*\*Model:', content, re.MULTILINE))
    bold_practice = len(re.findall(r'^\*\*Practice:', content, re.MULTILINE))
    
    if bold_model > 0 or bold_practice > 0:
        violations.append({
            'type': 'checkpoint_format',
            'severity': 'error',
            'issue': f"{level.upper()} M{module_num:02d} checkpoint uses **bold:** format instead of ### H3 headers",
            'fix': "Convert **Model:** → ### Model: and **Practice:** → ### Practice:",
            'details': {'bold_model': bold_model, 'bold_practice': bold_practice}
        })
    
    return violations


def get_checkpoint_structure_summary(content: str) -> dict:
    """
    Get a summary of checkpoint structure for reporting.
    """
    return {
        'skill_count': len(re.findall(r'^## Skill\s*\d*:', content, re.MULTILINE)),
        'model_count': len(re.findall(r'^### Model:', content, re.MULTILINE)),
        'practice_count': len(re.findall(r'^### Practice:', content, re.MULTILINE)),
        'self_check_count': len(re.findall(r'^### Self-Check', content, re.MULTILINE)),
        'has_diagnostika': bool(re.search(r'^## Діагностика', content, re.MULTILINE)),
        'has_analiz': bool(re.search(r'^## Аналіз', content, re.MULTILINE)),
        'uses_bold_headers': bool(re.search(r'^\*\*(Model|Practice):', content, re.MULTILINE)),
    }
