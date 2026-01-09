"""
Ukrainian State Standard 2024 compliance checking.

Validates that modules meet the official State Standard 2024 requirements
for grammar coverage, vocabulary targets, and pedagogical progression.
"""

from typing import List, Dict, Any, Optional
import yaml
from pathlib import Path


class StateStandardViolation:
    """Represents a State Standard 2024 compliance violation."""

    def __init__(self, code: str, message: str, reference: str, fix: str):
        self.code = code
        self.message = message
        self.reference = reference
        self.fix = fix

    def to_dict(self) -> Dict[str, str]:
        return {
            'code': self.code,
            'message': self.message,
            'reference': self.reference,
            'fix': self.fix
        }


def load_compliance_mapping() -> Dict[str, Any]:
    """Load the State Standard 2024 compliance mapping."""
    mapping_path = Path(__file__).parent.parent.parent.parent / 'docs' / 'l2-uk-en' / 'state-standard-2024-mapping.yaml'

    if not mapping_path.exists():
        return {}

    with open(mapping_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def check_reflexive_verbs_a1(module_num: int, content: str, mapping: Dict) -> List[StateStandardViolation]:
    """Check if M09 teaches reflexive verbs per §4.2.4.1."""
    violations = []

    req = mapping.get('a1', {}).get('reflexive_verbs')
    if not req or module_num != req['module']:
        return violations

    # Check for required patterns
    for pattern in req['required_patterns']:
        if pattern not in content:
            violations.append(StateStandardViolation(
                code='STATE_STANDARD_MISSING_REFLEXIVE',
                message=f"Module {module_num} must teach '{pattern}' ({req['reference']})",
                reference=req['reference'],
                fix=f"Add explanation and examples of reflexive verb '{pattern}'"
            ))

    # Check for -ся/-сь explanation
    if req['required_explanation'] not in content:
        violations.append(StateStandardViolation(
            code='STATE_STANDARD_MISSING_REFLEXIVE_EXPLANATION',
            message=f"Module {module_num} must explain reflexive suffix {req['required_explanation']}",
            reference=req['reference'],
            fix="Add explanation of reflexive verb formation with -ся/-сь"
        ))

    return violations


def check_imperative_complete_a2(module_num: int, content: str, mapping: Dict) -> List[StateStandardViolation]:
    """Check if M23 teaches complete imperative per §4.2.3.2."""
    violations = []

    req = mapping.get('a2', {}).get('imperative_complete')
    if not req or module_num != req['module']:
        return violations

    # Check for required patterns
    for pattern in req['required_patterns']:
        if pattern not in content:
            violations.append(StateStandardViolation(
                code='STATE_STANDARD_MISSING_IMPERATIVE',
                message=f"Module {module_num} must teach '{pattern}' ({req['reference']})",
                reference=req['reference'],
                fix=f"Add explanation and examples of 3rd person imperative with '{pattern}'"
            ))

    return violations


def check_immersion_compliance(level: str, module_num: int, immersion_pct: float, mapping: Dict) -> List[StateStandardViolation]:
    """Check if immersion percentage meets level requirements."""
    violations = []

    level_key = level.lower()
    immersion_req = mapping.get(level_key, {}).get('immersion')

    if not immersion_req:
        return violations

    # B1 special case: metalanguage bridge modules (M01-M05)
    if level_key == 'b1':
        if module_num in immersion_req.get('metalanguage_bridge', []):
            # Metalanguage modules have lower immersion - skip check
            return violations

        # M06+ should be 98%+
        if module_num >= immersion_req['full_immersion_start']:
            target = immersion_req['target_percentage']
            if immersion_pct < target:
                violations.append(StateStandardViolation(
                    code='STATE_STANDARD_LOW_IMMERSION',
                    message=f"Module {module_num} has {immersion_pct:.1f}% immersion (target: {target}%+)",
                    reference=immersion_req['reference'],
                    fix="Add more Ukrainian content to reach 98%+ immersion for full immersion modules"
                ))

    # B2, C1, C2: All modules should be 98%+
    elif level_key in ['b2', 'c1', 'c2']:
        target = immersion_req['target_percentage']
        if immersion_pct < target:
            violations.append(StateStandardViolation(
                code='STATE_STANDARD_LOW_IMMERSION',
                message=f"Module {module_num} has {immersion_pct:.1f}% immersion (target: {target}%+)",
                reference=immersion_req['reference'],
                fix=f"Add more Ukrainian content to reach {target}%+ immersion"
            ))

    return violations


def check_state_standard_compliance(
    level: str,
    module_num: int,
    content: str,
    immersion_pct: Optional[float] = None
) -> List[StateStandardViolation]:
    """
    Check if module meets Ukrainian State Standard 2024 requirements.

    Args:
        level: Module level (a1, a2, b1, b2, c1, c2)
        module_num: Module number
        content: Module content (markdown text)
        immersion_pct: Immersion percentage (optional)

    Returns:
        List of State Standard violations
    """
    mapping = load_compliance_mapping()

    if not mapping:
        return []

    violations = []
    level_key = level.lower()

    # Check level-specific requirements
    if level_key == 'a1':
        violations.extend(check_reflexive_verbs_a1(module_num, content, mapping))

    elif level_key == 'a2':
        violations.extend(check_imperative_complete_a2(module_num, content, mapping))

    # Check immersion compliance (B1+)
    if immersion_pct is not None and level_key in ['b1', 'b2', 'c1', 'c2']:
        violations.extend(check_immersion_compliance(level_key, module_num, immersion_pct, mapping))

    return violations
