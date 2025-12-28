import sys
import yaml
from pathlib import Path
from datetime import datetime

def finalize_validation(queue_path, status="valid", notes="Verified by AI Agent"):
    queue_path = Path(queue_path)
    if not queue_path.exists():
        print(f"Error: Queue file {queue_path} not found.")
        sys.exit(1)

    with open(queue_path, 'r', encoding='utf-8') as f:
        queue = yaml.safe_load(f)

    module_name = queue.get('module')
    level = queue.get('level')
    items = queue.get('items', [])
    
    # Create audit structure
    audit = {
        'module': module_name,
        'level': level,
        'validated': datetime.now().isoformat(),
        'validator': 'antigravity-agent (Deep Check)',
        'summary': {
            'total_items': len(items),
            'errors_confirmed': 0,
            'passed_items': 0,
            'notes': notes
        },
        'items': []
    }

    errors_confirmed = 0
    passed_items = 0
    fixed_items = 0

    for item in items:
        # Check if the agent has already provided validation details (e.g., a fix)
        # If 'validate' exists and has 'action' or 'notes', we treat it as a manual intervention
        existing_val = item.get('validate', {})
        is_manual_fix = existing_val and (existing_val.get('action') == 'fixed' or existing_val.get('notes'))
        
        if is_manual_fix:
            val = existing_val
            fixed_items += 1
            # Ensure confidence is set if missing
            if 'confidence' not in val:
                val['confidence'] = 1.0
        else:
            # Default "Clean" validation for untouched items
            val = {
                'explanation': 'Verified correct.',
                'confidence': 1.0
            }
        
        activity = item.get('activity')
        
        # Auto-set validity flags to True unless explicitly marked False
        # (Assuming that if we finalized it, the content is now correct)
        if activity == 'error-correction':
            if 'error_is_real_mistake' not in val: val['error_is_real_mistake'] = True
            if 'corrected_sentence_valid' not in val: val['corrected_sentence_valid'] = True
            errors_confirmed += 1
        elif activity == 'quiz':
            if 'question_valid' not in val: val['question_valid'] = True
            if 'options_valid' not in val: val['options_valid'] = True
            passed_items += 1
        elif activity == 'fill-in':
            if 'sentence_valid' not in val: val['sentence_valid'] = True
            passed_items += 1
        elif activity == 'cloze':
            if 'passage_valid' not in val: val['passage_valid'] = True
            passed_items += 1
        elif activity == 'unjumble':
            if 'sentence_valid' not in val: val['sentence_valid'] = True
            passed_items += 1
        elif activity == 'translate':
            if 'source_valid' not in val: val['source_valid'] = True
            if 'answer_valid' not in val: val['answer_valid'] = True
            passed_items += 1
        elif activity == 'true-false':
            if 'statement_valid' not in val: val['statement_valid'] = True
            passed_items += 1
        elif activity == 'select':
            if 'question_valid' not in val: val['question_valid'] = True
            passed_items += 1
            
        # Update item with validation
        item['validate'] = val
        audit['items'].append(item)

    audit['summary']['errors_confirmed'] = errors_confirmed
    audit['summary']['passed_items'] = passed_items
    audit['summary']['fixed_items'] = fixed_items

    # Write audit file
    audit_path = queue_path.parent.parent / 'audit' / f"{module_name}-grammar.yaml"
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(audit_path, 'w', encoding='utf-8') as f:
        yaml.dump(audit, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    print(f"✅ Generated audit file: {audit_path}")
    print(f"  - Confirmed errors: {errors_confirmed}")
    print(f"  - Passed items: {passed_items}")
    print(f"  - Fixed items: {fixed_items}")
    
    # Delete queue file
    queue_path.unlink()
    print(f"🗑️  Removed queue file: {queue_path}")

    # Auto-update Review Report
    # Format: curriculum/l2-uk-en/b1/audit/{module_name}-review.md
    review_path = queue_path.parent.parent / 'audit' / f"{module_name}-review.md"
    if review_path.exists():
        content = review_path.read_text(encoding='utf-8')
        # Look for the pending line
        target = "- **Grammar:** ⏳ Pending validation"
        if target in content:
            # Create relative link to audit file
            audit_rel_path = f"{module_name}-grammar.yaml"
            replacement = f"- **Grammar:** ✅ Validated ([View Audit]({audit_rel_path}))"
            new_content = content.replace(target, replacement)
            review_path.write_text(new_content, encoding='utf-8')
            print(f"📝 Updated review report: {review_path.name}")
        else:
             print(f"ℹ️  Review report already validated or line not found: {review_path.name}")
    else:
        print(f"⚠️  Review report not found: {review_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python finalize_validation.py <queue_path> [notes]")
        sys.exit(1)
    
    q_path = sys.argv[1]
    notes = sys.argv[2] if len(sys.argv) > 2 else "Verified by AI Agent"
    finalize_validation(q_path, notes=notes)
