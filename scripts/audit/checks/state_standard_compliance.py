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


CASE_KEYWORDS: dict[str, set[str]] = {
    'dative': {'dative', 'давальн', 'мені', 'тобі', 'йому', 'їй', 'нам', 'вам', 'їм'},
    'instrumental': {'instrumental', 'орудн', 'мною', 'тобою', 'ним', 'нею', 'нами', 'вами', 'ними'},
    'genitive': {'genitive', 'родов', 'мене', 'тебе', 'його', 'її', 'нас', 'вас', 'їх'},
    'accusative': {'accusative', 'знахідн'},
    'locative': {'locative', 'місцев'},
    'vocative': {'vocative', 'кличн'},
    'nominative': {'nominative', 'називн'},
}


def _is_negative_evidence(text: str) -> bool:
    """Check if an evidence string indicates absence of evidence or is a negative note."""
    if not isinstance(text, str):
        return True
    cleaned = text.strip()
    if not cleaned:
        return True
    text_lower = cleaned.lower()

    if text_lower in {'none', 'no', 'n/a', 'na', 'false', 'nil', 'null'}:
        return True

    negative_patterns = [
        r'\bno\b.*\b(ulp|ukrainian lessons podcast|evidence|episode)\b',
        r'\bwithout\b.*\b(ulp|ukrainian lessons podcast|evidence)\b',
        r'\b(lacks?|missing)\b.*\b(ulp|ukrainian lessons podcast|evidence)\b',
        r'\b(not\s+covered|not\s+found|not\s+available|unavailable|unsupported)\b',
        r'\b(ulp|ukrainian lessons podcast|evidence)\b.*\b(not\s+found|not\s+available|not\s+covered|missing|none|unavailable|unsupported|does\s+not\b)',
        r'\bнемає\b',
        r'\bвідсутн\w*\b',
    ]
    return any(re.search(pat, text_lower) for pat in negative_patterns)


def _evidence_text_matches_move(text: str, item_key: str, item_id: str, item_name: str) -> bool:
    """Check if an evidence string specifically references the item/move and cites ULP."""
    if not isinstance(text, str):
        return False
    if _is_negative_evidence(text):
        return False
    text_lower = text.lower()
    if 'ulp' not in text_lower and 'ukrainian lessons podcast' not in text_lower:
        return False

    keywords: set[str] = set()
    clean_k = item_key.lower().strip() if item_key else ''
    if clean_k:
        keywords.add(clean_k)
        keywords.add(clean_k.replace('_', ' '))
        keywords.add(clean_k.replace('_', '-'))
        if clean_k in CASE_KEYWORDS:
            keywords.update(CASE_KEYWORDS[clean_k])

    if item_id:
        clean_id = item_id.lower().strip()
        if clean_id:
            keywords.add(clean_id)

    if item_name:
        clean_n = item_name.lower().strip()
        if clean_n:
            keywords.add(clean_n)

    clean_keywords = {kw for kw in keywords if kw}
    if not clean_keywords:
        return False

    return any(kw in text_lower for kw in clean_keywords)


def _has_ulp_evidence(item: Any, plan: dict[str, Any], arc: dict[str, Any] | None) -> bool:
    """Check whether ULP evidence is recorded specifically for teaching an item earlier."""
    item_name = ''
    item_id = ''

    if isinstance(item, dict):
        item_name = str(item.get('name') or item.get('point') or '')
        item_id = str(item.get('id') or '')

        # 1. Evidence directly on the item dictionary
        item_ulp = item.get('ulp_evidence')
        if not isinstance(item_ulp, bool):
            if isinstance(item_ulp, str):
                if not _is_negative_evidence(item_ulp) and ('ulp' in item_ulp.lower() or 'ukrainian lessons podcast' in item_ulp.lower()):
                    return True
            elif isinstance(item_ulp, list):
                for ev in item_ulp:
                    if isinstance(ev, str) and not _is_negative_evidence(ev) and ('ulp' in ev.lower() or 'ukrainian lessons podcast' in ev.lower()):
                        return True

        evidence = item.get('evidence', [])
        if isinstance(evidence, list):
            for ev in evidence:
                if isinstance(ev, str) and not _is_negative_evidence(ev) and ('ulp' in ev.lower() or 'ukrainian lessons podcast' in ev.lower()):
                    return True
        elif (
            isinstance(evidence, str)
            and not isinstance(evidence, bool)
            and not _is_negative_evidence(evidence)
            and ('ulp' in evidence.lower() or 'ukrainian lessons podcast' in evidence.lower())
        ):
            return True

    elif isinstance(item, str):
        item_name = item
        if item.startswith('G-'):
            item_id = item

    clean_key = item_name.lower().strip().replace('-', '_')
    clean_key = ITEM_ALIASES.get(clean_key, clean_key)

    # 2. Check plan-level ulp_evidence tied to this specific item/move
    plan_ulp = plan.get('ulp_evidence')
    if isinstance(plan_ulp, dict):
        entry = (
            (plan_ulp.get(clean_key) if clean_key else None)
            or (plan_ulp.get(item_name.lower()) if item_name else None)
            or (plan_ulp.get(item_id) if item_id else None)
        )
        if not isinstance(entry, bool):
            if isinstance(entry, str):
                if not _is_negative_evidence(entry) and ('ulp' in entry.lower() or 'ukrainian lessons podcast' in entry.lower()):
                    return True
            elif isinstance(entry, list):
                for ev in entry:
                    if isinstance(ev, str) and not _is_negative_evidence(ev) and ('ulp' in ev.lower() or 'ukrainian lessons podcast' in ev.lower()):
                        return True
    elif isinstance(plan_ulp, list):
        for ev in plan_ulp:
            if _evidence_text_matches_move(ev, clean_key, item_id, item_name):
                return True
    elif isinstance(plan_ulp, str) and not isinstance(plan_ulp, bool):
        if _evidence_text_matches_move(plan_ulp, clean_key, item_id, item_name):
            return True

    # 3. Check curriculum arc metadata tied to this move
    for arc_dict in (arc, plan.get('arc'), plan.get('arc_ref')):
        if not isinstance(arc_dict, dict):
            continue

        # Check arc moves or direct item entry
        moves = arc_dict.get('moves', {})
        move_entry = None
        if isinstance(moves, dict):
            move_entry = (moves.get(clean_key) if clean_key else None) or (moves.get(item_id) if item_id else None)
        if not move_entry:
            move_entry = (arc_dict.get(clean_key) if clean_key else None) or (arc_dict.get(item_id) if item_id else None)

        if isinstance(move_entry, dict):
            move_ulp = move_entry.get('ulp_evidence')
            if not isinstance(move_ulp, bool):
                if isinstance(move_ulp, str) and not _is_negative_evidence(move_ulp) and ('ulp' in move_ulp.lower() or 'ukrainian lessons podcast' in move_ulp.lower()):
                    return True
                if isinstance(move_ulp, list):
                    for ev in move_ulp:
                        if isinstance(ev, str) and not _is_negative_evidence(ev) and ('ulp' in ev.lower() or 'ukrainian lessons podcast' in ev.lower()):
                            return True
            move_ev = move_entry.get('evidence')
            if isinstance(move_ev, list):
                for ev in move_ev:
                    if isinstance(ev, str) and not _is_negative_evidence(ev) and ('ulp' in ev.lower() or 'ukrainian lessons podcast' in ev.lower()):
                        return True
            elif (
                isinstance(move_ev, str)
                and not isinstance(move_ev, bool)
                and not _is_negative_evidence(move_ev)
                and ('ulp' in move_ev.lower() or 'ukrainian lessons podcast' in move_ev.lower())
            ):
                return True
        elif isinstance(move_entry, str) and not isinstance(move_entry, bool):
            if not _is_negative_evidence(move_entry) and ('ulp' in move_entry.lower() or 'ukrainian lessons podcast' in move_entry.lower()):
                return True

        # Check arc['ulp_evidence'] mapping
        arc_ulp = arc_dict.get('ulp_evidence')
        if isinstance(arc_ulp, dict):
            ev_val = (arc_ulp.get(clean_key) if clean_key else None) or (arc_ulp.get(item_id) if item_id else None)
            if not isinstance(ev_val, bool):
                if isinstance(ev_val, str) and not _is_negative_evidence(ev_val) and ('ulp' in ev_val.lower() or 'ukrainian lessons podcast' in ev_val.lower()):
                    return True
                if isinstance(ev_val, list):
                    for ev in ev_val:
                        if isinstance(ev, str) and not _is_negative_evidence(ev) and ('ulp' in ev.lower() or 'ukrainian lessons podcast' in ev.lower()):
                            return True
        elif isinstance(arc_ulp, list):
            for ev in arc_ulp:
                if _evidence_text_matches_move(ev, clean_key, item_id, item_name):
                    return True
        elif isinstance(arc_ulp, str) and not isinstance(arc_ulp, bool):
            if _evidence_text_matches_move(arc_ulp, clean_key, item_id, item_name):
                return True

    return False


def get_required_items_for_plan(plan: dict[str, Any], plan_level: str, mapping: dict[str, Any]) -> list[str]:
    """Derive minimum required State Standard items for a plan from the Standard mapping."""
    lvl_data = mapping.get(plan_level, {})
    if not isinstance(lvl_data, dict):
        return []

    required_items: list[str] = []

    # 1. Module / position-specific presence requirements from mapping
    plan_module = plan.get('module') or plan.get('module_num') or plan.get('sequence')
    if isinstance(plan_module, str) and plan_module.isdigit():
        plan_module = int(plan_module)
    plan_pos = plan.get('arc_position')
    plan_req_id = plan.get('requirement_id')

    for key, val in lvl_data.items():
        if isinstance(val, dict):
            target_modules = val.get('modules') or ([val['module']] if 'module' in val else [])
            target_pos = val.get('arc_position')
            target_req_id = val.get('requirement_id')
            if (
                (plan_module is not None and plan_module in target_modules)
                or (plan_pos is not None and plan_pos == target_pos)
                or (plan_req_id is not None and plan_req_id == target_req_id)
            ):
                required_items.append(key)

    # Check case first_module mappings
    cases_dict = lvl_data.get('cases', {})
    if isinstance(cases_dict, dict) and plan_module is not None:
        for case_name, case_data in cases_dict.items():
            if isinstance(case_data, dict) and case_data.get('first_module') == plan_module and case_name not in required_items:
                required_items.append(case_name)

    # 2. Check if plan is a level-level plan (or empty plan with no taught items)
    is_level_plan = plan.get('is_level_plan') is True
    has_no_taught = not (
        plan.get('grammar') or plan.get('taught_items') or plan.get('covered_items')
        or plan.get('inventory', {}).get('grammar')
        or any(isinstance(l, dict) and (l.get('grammar') or l.get('inventory', {}).get('grammar')) for l in plan.get('lessons', []))
    )

    if is_level_plan or has_no_taught:
        # Collect items with required: true in the mapping for this level
        for section in ('cases', 'verbs', 'morphology', 'syntax'):
            sec_dict = lvl_data.get(section, {})
            if isinstance(sec_dict, dict):
                for item_name, item_data in sec_dict.items():
                    if isinstance(item_data, dict) and item_data.get('required') is True and item_name not in required_items:
                        required_items.append(item_name)

    # 3. Include any required_items explicitly declared by the plan
    declared = plan.get('required_items', [])
    if isinstance(declared, list):
        for item in declared:
            if isinstance(item, str) and item not in required_items:
                required_items.append(item)

    return required_items


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

    required_items = get_required_items_for_plan(plan, plan_level, mapping)
    if required_items:
        taught_set: set[str] = set()
        for key in ('covered_items', 'taught_items', 'grammar'):
            vals = plan.get(key, [])
            if isinstance(vals, list):
                for v in vals:
                    if isinstance(v, str):
                        clean = v.lower().strip().replace('-', '_')
                        taught_set.add(clean)
                        taught_set.add(ITEM_ALIASES.get(clean, clean))
                    elif isinstance(v, dict):
                        if 'name' in v:
                            clean = str(v['name']).lower().strip().replace('-', '_')
                            taught_set.add(clean)
                            taught_set.add(ITEM_ALIASES.get(clean, clean))
                        if 'id' in v:
                            clean = str(v['id']).lower().strip().replace('-', '_')
                            taught_set.add(clean)

        inv_grammar = plan.get('inventory', {}).get('grammar', [])
        if isinstance(inv_grammar, list):
            for v in inv_grammar:
                if isinstance(v, str):
                    clean = v.lower().strip().replace('-', '_')
                    taught_set.add(clean)
                    taught_set.add(ITEM_ALIASES.get(clean, clean))
                elif isinstance(v, dict):
                    if 'name' in v:
                        clean = str(v['name']).lower().strip().replace('-', '_')
                        taught_set.add(clean)
                        taught_set.add(ITEM_ALIASES.get(clean, clean))
                    if 'id' in v:
                        clean = str(v['id']).lower().strip().replace('-', '_')
                        taught_set.add(clean)

        for lesson in plan.get('lessons', []):
            if isinstance(lesson, dict):
                for lk in ('grammar', 'inventory'):
                    l_val = lesson.get(lk, [])
                    if lk == 'inventory' and isinstance(l_val, dict):
                        l_val = l_val.get('grammar', [])
                    if isinstance(l_val, list):
                        for v in l_val:
                            if isinstance(v, str):
                                clean = v.lower().strip().replace('-', '_')
                                taught_set.add(clean)
                                taught_set.add(ITEM_ALIASES.get(clean, clean))
                            elif isinstance(v, dict):
                                if 'name' in v:
                                    clean = str(v['name']).lower().strip().replace('-', '_')
                                    taught_set.add(clean)
                                    taught_set.add(ITEM_ALIASES.get(clean, clean))
                                if 'id' in v:
                                    clean = str(v['id']).lower().strip().replace('-', '_')
                                    taught_set.add(clean)

        for req_item in required_items:
            clean_req = req_item.lower().strip().replace('-', '_')
            clean_req = ITEM_ALIASES.get(clean_req, clean_req)
            if clean_req not in taught_set and req_item.lower().strip().replace('-', '_') not in taught_set:
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

    # Extract grammar items from v2 inventory
    inventory_grammar = plan.get('inventory', {}).get('grammar', [])
    if isinstance(inventory_grammar, list):
        taught_candidates.extend(inventory_grammar)

    # Extract grammar items from v2 lessons[].inventory.grammar and lessons[].grammar
    lessons = plan.get('lessons', [])
    if isinstance(lessons, list):
        for lesson in lessons:
            if isinstance(lesson, dict):
                lesson_inv = lesson.get('inventory', {})
                if isinstance(lesson_inv, dict):
                    l_inv_grammar = lesson_inv.get('grammar', [])
                    if isinstance(l_inv_grammar, list):
                        taught_candidates.extend(l_inv_grammar)
                l_grammar = lesson.get('grammar', [])
                if isinstance(l_grammar, list):
                    taught_candidates.extend(l_grammar)

    for item in taught_candidates:
        item_level: str | None = None
        item_name = ''

        if isinstance(item, dict):
            item_name = str(item.get('name') or item.get('point') or item.get('id') or '')
            # Authority of the Standard mapping: mapping level wins over caller-supplied level
            std_level = find_item_standard_level(item_name, mapping) if item_name else None
            if std_level:
                item_level = std_level
            elif 'id' in item and str(item['id']).startswith('G-'):
                parts = str(item['id']).split('-')
                if len(parts) >= 2 and parts[1].lower() in LEVEL_ORDER:
                    item_level = parts[1].lower()
            elif 'level' in item:
                item_level = str(item['level']).lower()
        elif isinstance(item, str):
            item_name = item
            std_level = find_item_standard_level(item, mapping)
            if std_level:
                item_level = std_level
            elif item.startswith('G-'):
                parts = item.split('-')
                if len(parts) >= 2 and parts[1].lower() in LEVEL_ORDER:
                    item_level = parts[1].lower()

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

    # If plan is not provided, try to extract frontmatter from content as plan
    if plan is None and immersion_pct is None and content and content.startswith('---'):
        try:
            match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
            if match:
                parsed = yaml.safe_load(match.group(1))
                if isinstance(parsed, dict):
                    plan = parsed
        except Exception:
            pass

    # If plan is provided (or extracted from content), check plan compliance first
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
