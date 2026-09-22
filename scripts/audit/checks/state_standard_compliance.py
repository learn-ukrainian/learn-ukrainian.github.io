"""
Ukrainian State Standard 2024 compliance checking.

Validates that modules and plans meet the official State Standard 2024 requirements
for grammar coverage, vocabulary targets, and pedagogical progression.

Policy (requirement R-32 of #8397):
- The State Standard defines the MINIMUM floor each level must cover.
- A plan may teach something the Standard lists at a higher level ONLY when the
  arc or plan records ULP evidence for that progression move.
- A plan may never drop a required Standard item for the level.
"""

import re
from pathlib import Path
from typing import Any

import yaml

LEVEL_ORDER = ['a1', 'a2', 'b1', 'b2', 'c1', 'c2']

ITEM_ALIASES: dict[str, str] = {
    'dative_case': 'dative',
    'instrumental_case': 'instrumental',
    'genitive_case': 'genitive',
    'accusative_case': 'accusative',
    'locative_case': 'locative',
    'vocative_case': 'vocative',
    'nominative_case': 'nominative',
    'imperative_3rd_person': 'imperative_complete',
    '3rd_person_imperative': 'imperative_complete',
    'reflexive': 'reflexive_verbs',
}


class StateStandardViolation:
    """Represents a State Standard 2024 compliance violation."""

    def __init__(self, code: str, message: str, reference: str, fix: str):
        self.code = code
        self.message = message
        self.reference = reference
        self.fix = fix

    def to_dict(self) -> dict[str, str]:
        return {
            'code': self.code,
            'message': self.message,
            'reference': self.reference,
            'fix': self.fix
        }


def load_compliance_mapping() -> dict[str, Any]:
    """Load the State Standard 2024 compliance mapping."""
    mapping_path = Path(__file__).parent.parent.parent.parent / 'docs' / 'l2-uk-en' / 'state-standard-2024-mapping.yaml'

    if not mapping_path.exists():
        return {}

    with open(mapping_path, encoding='utf-8') as f:
        return yaml.safe_load(f)


def find_item_standard_level(item_name: str, mapping: dict[str, Any]) -> str | None:
    """Find the earliest State Standard level where an item/topic is prescribed."""
    clean = item_name.lower().strip().replace('-', '_').replace(' ', '_')
    clean = ITEM_ALIASES.get(clean, clean)

    for lvl in LEVEL_ORDER:
        lvl_data = mapping.get(lvl, {})
        if not isinstance(lvl_data, dict):
            continue

        if clean in lvl_data:
            return lvl

        for section in ('cases', 'verbs', 'morphology', 'syntax', 'phonetics', 'word_formation', 'stylistics'):
            sec_dict = lvl_data.get(section, {})
            if isinstance(sec_dict, dict) and clean in sec_dict:
                return lvl

        for val in lvl_data.values():
            if isinstance(val, dict) and val.get('requirement_id', '').lower() == clean:
                return lvl

    return None


def _get_item_reference(item_name: str, level: str, mapping: dict[str, Any]) -> str:
    """Retrieve reference citation string for a standard item."""
    clean = item_name.lower().strip().replace('-', '_').replace(' ', '_')
    clean = ITEM_ALIASES.get(clean, clean)
    lvl_data = mapping.get(level, {})

    if clean in lvl_data and isinstance(lvl_data[clean], dict):
        return str(lvl_data[clean].get('reference', 'State Standard 2024'))

    for section in ('cases', 'verbs', 'morphology', 'syntax', 'phonetics', 'word_formation', 'stylistics'):
        sec_dict = lvl_data.get(section, {})
        if isinstance(sec_dict, dict) and clean in sec_dict:
            entry = sec_dict[clean]
            if isinstance(entry, dict):
                return str(entry.get('reference', 'State Standard 2024'))

    return 'State Standard 2024'


def check_reflexive_verbs_a1(
    module_num: int,
    content: str,
    mapping: dict,
    arc_position: int | None = None,
    requirement_id: str | None = None,
) -> list[StateStandardViolation]:
    """Check if module teaches reflexive verbs per §4.2.4.1."""
    violations = []

    req = mapping.get('a1', {}).get('reflexive_verbs')
    if not req:
        return violations

    target_modules = req.get('modules') or ([req['module']] if 'module' in req else [])
    target_pos = req.get('arc_position')
    target_req_id = req.get('requirement_id')

    matches = (
        (module_num in target_modules)
        or (arc_position is not None and arc_position == target_pos)
        or (requirement_id is not None and requirement_id == target_req_id)
    )
    if not matches:
        return violations

    # Check for required patterns
    for pattern in req.get('required_patterns', []):
        if pattern not in content:
            violations.append(StateStandardViolation(
                code='STATE_STANDARD_MISSING_REFLEXIVE',
                message=f"Module {module_num} must teach '{pattern}' ({req['reference']})",
                reference=req['reference'],
                fix=f"Add explanation and examples of reflexive verb '{pattern}'"
            ))

    # Check for -ся/-сь explanation
    req_explanation = req.get('required_explanation')
    if req_explanation and req_explanation not in content:
        violations.append(StateStandardViolation(
            code='STATE_STANDARD_MISSING_REFLEXIVE_EXPLANATION',
            message=f"Module {module_num} must explain reflexive suffix {req_explanation}",
            reference=req['reference'],
            fix=f"Add explanation of reflexive verb formation with {req_explanation}"
        ))

    return violations


def check_imperative_complete_a2(
    module_num: int,
    content: str,
    mapping: dict,
    arc_position: int | None = None,
    requirement_id: str | None = None,
) -> list[StateStandardViolation]:
    """Check if module teaches complete imperative (3rd person) per §4.2.3.2."""
    violations = []

    req = mapping.get('a2', {}).get('imperative_complete')
    if not req:
        return violations

    target_modules = req.get('modules') or ([req['module']] if 'module' in req else [])
    target_pos = req.get('arc_position')
    target_req_id = req.get('requirement_id')

    matches = (
        (module_num in target_modules)
        or (arc_position is not None and arc_position == target_pos)
        or (requirement_id is not None and requirement_id == target_req_id)
    )
    if not matches:
        return violations

    # Check for required patterns
    for pattern in req.get('required_patterns', []):
        if pattern not in content:
            violations.append(StateStandardViolation(
                code='STATE_STANDARD_MISSING_IMPERATIVE',
                message=f"Module {module_num} must teach '{pattern}' ({req['reference']})",
                reference=req['reference'],
                fix=f"Add explanation and examples of 3rd person imperative with '{pattern}'"
            ))

    return violations


def check_immersion_compliance(level: str, module_num: int, immersion_pct: float, mapping: dict) -> list[StateStandardViolation]:
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
                    fix="Add more Ukrainian content to reach 90%+ immersion for full immersion modules"
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


def _has_ulp_evidence(item: Any, plan: dict[str, Any], arc: dict[str, Any] | None) -> bool:
    """Check whether ULP evidence is recorded for teaching an item earlier."""
    if isinstance(item, dict):
        if item.get('ulp_evidence'):
            return True
        evidence = item.get('evidence', [])
        if isinstance(evidence, list):
            for ev in evidence:
                if isinstance(ev, str) and 'ulp' in ev.lower():
                    return True
        elif isinstance(evidence, str) and 'ulp' in evidence.lower():
            return True

    if plan.get('ulp_evidence'):
        return True

    for key in ('arc', 'arc_ref'):
        arc_ref = plan.get(key)
        if isinstance(arc_ref, dict) and arc_ref.get('ulp_evidence'):
            return True

    if arc:
        if arc.get('ulp_evidence'):
            return True
        if isinstance(item, str) and arc.get(item, {}).get('ulp_evidence'):
            return True

    # Scan plan text / comments / points for ULP references
    for text_key in ('rationale', 'notes', 'review_notes', 'focus', 'subtitle'):
        val = plan.get(text_key)
        if isinstance(val, str) and re.search(r'\bULP\b', val, re.IGNORECASE):
            return True

    content_outline = plan.get('content_outline', [])
    if isinstance(content_outline, list):
        for sec in content_outline:
            if isinstance(sec, dict):
                for pt in sec.get('points', []):
                    if isinstance(pt, str) and re.search(r'\bULP\b', pt, re.IGNORECASE):
                        return True

    return False


def check_plan_compliance(
    plan: dict[str, Any],
    mapping: dict[str, Any] | None = None,
    arc: dict[str, Any] | None = None,
) -> list[StateStandardViolation]:
    """
    Validate that a plan meets the Ukrainian State Standard 2024 as a minimum floor.

    Policy (requirement R-32):
    - The State Standard is the MINIMUM a level must cover (a floor, not a ceiling).
    - A plan may teach something the Standard lists at a higher level ONLY when the
      arc or plan records ULP evidence for that progression move.
    - A plan may never drop or omit a required Standard item for the level.

    Args:
        plan: Plan dictionary (e.g. from plan YAML)
        mapping: Optional State Standard compliance mapping (loaded if None)
        arc: Optional curriculum arc dictionary with progression metadata

    Returns:
        List of StateStandardViolation instances (empty if compliant)
    """
    if mapping is None:
        mapping = load_compliance_mapping()
    if not mapping:
        return []

    violations = []
    plan_level = str(plan.get('level', 'a1')).lower()

    if plan_level not in LEVEL_ORDER:
        return []

    plan_level_idx = LEVEL_ORDER.index(plan_level)

    # 1. Check for omitted / dropped required items (Standard floor violation)
    omitted = plan.get('omitted_items') or plan.get('dropped_items') or plan.get('omits') or []
    if isinstance(omitted, list):
        for item in omitted:
            item_name = item if isinstance(item, str) else str(item.get('name', item))
            ref = _get_item_reference(item_name, plan_level, mapping)
            violations.append(StateStandardViolation(
                code='STATE_STANDARD_OMITTED_ITEM',
                message=f"Plan omits required State Standard item '{item_name}' for level {plan_level.upper()}",
                reference=ref,
                fix=f"Include coverage of required State Standard item '{item_name}' to satisfy the minimum floor"
            ))

    required_items = plan.get('required_items', [])
    if isinstance(required_items, list) and required_items:
        taught_set: set[str] = set()
        for key in ('covered_items', 'taught_items', 'grammar', 'topics'):
            vals = plan.get(key, [])
            if isinstance(vals, list):
                for v in vals:
                    if isinstance(v, str):
                        taught_set.add(v.lower().strip().replace('-', '_'))
                    elif isinstance(v, dict):
                        if 'name' in v:
                            taught_set.add(str(v['name']).lower().strip().replace('-', '_'))
                        if 'id' in v:
                            taught_set.add(str(v['id']).lower().strip().replace('-', '_'))

        for req_item in required_items:
            clean_req = req_item.lower().strip().replace('-', '_')
            if clean_req not in taught_set:
                ref = _get_item_reference(req_item, plan_level, mapping)
                violations.append(StateStandardViolation(
                    code='STATE_STANDARD_OMITTED_ITEM',
                    message=f"Plan omits required State Standard item '{req_item}' for level {plan_level.upper()}",
                    reference=ref,
                    fix=f"Include coverage of required State Standard item '{req_item}' in plan"
                ))

    # 2. Check taught items against floor / ceiling policy (R-32)
    taught_candidates: list[Any] = []
    for key in ('grammar', 'taught_items', 'topics', 'covered_items'):
        vals = plan.get(key, [])
        if isinstance(vals, list):
            taught_candidates.extend(vals)

    # Also extract grammar items from v2 inventory
    inventory_grammar = plan.get('inventory', {}).get('grammar', [])
    if isinstance(inventory_grammar, list):
        taught_candidates.extend(inventory_grammar)

    for item in taught_candidates:
        item_level: str | None = None
        item_name = ''

        if isinstance(item, dict):
            item_name = str(item.get('name') or item.get('id') or item.get('point') or '')
            if 'level' in item:
                item_level = str(item['level']).lower()
            elif 'id' in item and str(item['id']).startswith('G-'):
                parts = str(item['id']).split('-')
                if len(parts) >= 2 and parts[1].lower() in LEVEL_ORDER:
                    item_level = parts[1].lower()
            if not item_level and item_name:
                item_level = find_item_standard_level(item_name, mapping)
        elif isinstance(item, str):
            item_name = item
            if item.startswith('G-'):
                parts = item.split('-')
                if len(parts) >= 2 and parts[1].lower() in LEVEL_ORDER:
                    item_level = parts[1].lower()
            if not item_level:
                item_level = find_item_standard_level(item, mapping)

        if not item_level or item_level not in LEVEL_ORDER:
            continue

        item_level_idx = LEVEL_ORDER.index(item_level)

        # If taught item is from a higher level than the plan:
        if item_level_idx > plan_level_idx:
            # Standard is a floor: teaching earlier is allowed if and only if ULP evidence is recorded
            has_ulp = _has_ulp_evidence(item, plan, arc)
            if not has_ulp:
                violations.append(StateStandardViolation(
                    code='STATE_STANDARD_EARLY_WITHOUT_ULP',
                    message=(
                        f"Plan at level {plan_level.upper()} teaches item '{item_name}' "
                        f"from higher level {item_level.upper()} without recorded ULP evidence (requirement R-32)"
                    ),
                    reference='R-32',
                    fix=f"Record ULP evidence justifying early introduction of '{item_name}' at {plan_level.upper()}, or defer to {item_level.upper()}"
                ))

    return violations


def check_state_standard_compliance(
    level: str,
    module_num: int,
    content: str,
    immersion_pct: float | None = None,
    plan: dict[str, Any] | None = None,
    arc_position: int | None = None,
    requirement_id: str | None = None,
) -> list[StateStandardViolation]:
    """
    Check if module meets Ukrainian State Standard 2024 requirements.

    Args:
        level: Module level (a1, a2, b1, b2, c1, c2)
        module_num: Module number
        content: Module content (markdown text)
        immersion_pct: Immersion percentage (optional)
        plan: Optional plan dictionary to check against Standard floor
        arc_position: Optional arc position
        requirement_id: Optional requirement ID

    Returns:
        List of State Standard violations
    """
    mapping = load_compliance_mapping()

    if not mapping:
        return []

    violations = []
    level_key = level.lower()

    # If plan is provided, check plan compliance first
    if plan is not None:
        violations.extend(check_plan_compliance(plan, mapping=mapping))

    # Check level-specific content requirements
    if level_key == 'a1':
        violations.extend(check_reflexive_verbs_a1(
            module_num, content, mapping, arc_position=arc_position, requirement_id=requirement_id
        ))

    elif level_key == 'a2':
        violations.extend(check_imperative_complete_a2(
            module_num, content, mapping, arc_position=arc_position, requirement_id=requirement_id
        ))

    # Check immersion compliance (B1+)
    if immersion_pct is not None and level_key in ['b1', 'b2', 'c1', 'c2']:
        violations.extend(check_immersion_compliance(level_key, module_num, immersion_pct, mapping))

    return violations
