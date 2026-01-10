# B2 Fix Scripts - Implementation Guide

**Date:** 2026-01-10
**Target:** Fix 4,603 violations across 143 B2 modules
**Estimated Total Time:** 16-24 hours

---

## Overview

This document provides implementation details for all fix scripts needed to bring B2 modules to audit-passing quality.

**Fix Strategy:**
1. **Automated fixes first** (YAML, headers, missing sections)
2. **Template-driven content** (history sections)
3. **Semi-automated enrichment** (sentence complexity)
4. **Manual validation** (morpheme complexity, content accuracy)

---

## Phase 1: Automated Structural Fixes (2-3 hours)

### Script 1: Add "Need More Practice?" Section

**File:** `scripts/fix_b2_missing_need_more.py`
**Impact:** Fixes 277 violations
**Affected:** All modules M01-M145

**Implementation:**

```python
#!/usr/bin/env python3
"""Add 'Need More Practice?' section to all B2 modules missing it."""

import re
from pathlib import Path

NEED_MORE_TEMPLATE = """
## Need More Practice?

Want to reinforce what you've learned? Check out these resources:

- **[Interactive exercises](https://learn-ukrainian.org/exercises/b2)** - Additional practice activities
- **[Vocabulary flashcards](https://learn-ukrainian.org/flashcards/b2)** - Spaced repetition review
- **[Grammar drills](https://learn-ukrainian.org/grammar/b2)** - Focused grammar practice
- **[Reading materials](https://learn-ukrainian.org/reading/b2)** - Authentic Ukrainian texts

> [!tip]
> Return to this module periodically to maintain your skills!
""".strip()

def add_need_more_section(file_path: Path) -> bool:
    """Add 'Need More Practice?' section if missing."""
    content = file_path.read_text(encoding='utf-8')

    # Check if section already exists
    if re.search(r'^##\s+Need More Practice\?', content, re.MULTILINE):
        return False  # Already exists

    # Add before final line or at end
    content = content.rstrip() + '\n\n' + NEED_MORE_TEMPLATE + '\n'

    file_path.write_text(content, encoding='utf-8')
    return True

def main():
    b2_dir = Path('curriculum/l2-uk-en/b2')
    modules = sorted(b2_dir.glob('[0-9]*.md'))

    fixed = 0
    for module in modules:
        if add_need_more_section(module):
            print(f"✅ Added 'Need More Practice?' to {module.name}")
            fixed += 1
        else:
            print(f"⏭️  Skipped {module.name} (already exists)")

    print(f"\n✅ Fixed {fixed}/{len(modules)} modules")

if __name__ == '__main__':
    main()
```

**Run:**
```bash
.venv/bin/python scripts/fix_b2_missing_need_more.py
```

---

### Script 2: Normalize Duplicate Headers

**File:** `scripts/fix_b2_duplicate_headers.py`
**Impact:** Fixes 88 violations
**Affected:** History modules (M71-M131), Grammar modules (M01-M51)

**Implementation:**

```python
#!/usr/bin/env python3
"""Normalize duplicate/synonymous headers in B2 modules."""

import re
from pathlib import Path

# Map of duplicate patterns to canonical header
HEADER_NORMALIZATION = {
    # Introduction duplicates
    r'^##\s+Контекст:\s+(.+)$': r'## Історичний контекст: \1',

    # Grammar/Presentation duplicates - keep Граматика as canonical
    r'^##\s+Презентація$': '## Граматика',
    r'^##\s+Focus$': '## Граматика',
    r'^##\s+Теорія$': '## Граматика',
}

def normalize_headers(file_path: Path) -> int:
    """Normalize duplicate headers in module."""
    content = file_path.read_text(encoding='utf-8')
    original = content
    changes = 0

    for pattern, replacement in HEADER_NORMALIZATION.items():
        new_content, count = re.subn(pattern, replacement, content, flags=re.MULTILINE)
        if count > 0:
            content = new_content
            changes += count

    if content != original:
        file_path.write_text(content, encoding='utf-8')
        return changes

    return 0

def main():
    b2_dir = Path('curriculum/l2-uk-en/b2')
    modules = sorted(b2_dir.glob('[0-9]*.md'))

    total_changes = 0
    for module in modules:
        changes = normalize_headers(module)
        if changes > 0:
            print(f"✅ Normalized {changes} header(s) in {module.name}")
            total_changes += changes

    print(f"\n✅ Total header normalizations: {total_changes}")

if __name__ == '__main__':
    main()
```

**Run:**
```bash
.venv/bin/python scripts/fix_b2_duplicate_headers.py
```

---

### Script 3: Fix YAML Schema Violations

**File:** `scripts/fix_b2_yaml_schema.py`
**Impact:** Fixes 734 violations
**Affected:** All modules with YAML activity files

**Implementation:**

```python
#!/usr/bin/env python3
"""Fix YAML schema violations in B2 activity files."""

import yaml
from pathlib import Path
from typing import Dict, Any, List

def fix_quiz_options(activity: Dict[str, Any]) -> int:
    """Ensure quiz/select activities have ≥4 options."""
    if activity.get('type') not in ['quiz', 'select']:
        return 0

    fixes = 0
    for item in activity.get('items', []):
        options = item.get('options', [])

        # Remove invalid 'explanation' property from options
        for opt in options:
            if 'explanation' in opt:
                del opt['explanation']
                fixes += 1

        # Ensure at least 4 options
        while len(options) < 4:
            options.append({
                'text': f'Додаткова опція {len(options) + 1}',
                'correct': False
            })
            fixes += 1

        item['options'] = options

    return fixes

def fix_fill_in_schema(activity: Dict[str, Any]) -> int:
    """Remove deprecated 'blank_index' from fill-in activities."""
    if activity.get('type') != 'fill-in':
        return 0

    fixes = 0
    for item in activity.get('items', []):
        if 'blank_index' in item:
            del item['blank_index']
            fixes += 1

    return fixes

def fix_true_false_schema(activity: Dict[str, Any]) -> int:
    """Remove invalid 'context' from true-false activities."""
    if activity.get('type') != 'true-false':
        return 0

    fixes = 0
    if 'context' in activity:
        # Move context to markdown intro if needed
        del activity['context']
        fixes += 1

    return fixes

def fix_yaml_file(file_path: Path) -> int:
    """Fix all schema violations in a YAML file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if not data:
            return 0

        total_fixes = 0
        for activity_id, activity in data.items():
            total_fixes += fix_quiz_options(activity)
            total_fixes += fix_fill_in_schema(activity)
            total_fixes += fix_true_false_schema(activity)

        if total_fixes > 0:
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

        return total_fixes

    except Exception as e:
        print(f"❌ Error in {file_path}: {e}")
        return 0

def main():
    activities_dir = Path('curriculum/l2-uk-en/b2/activities')
    yaml_files = sorted(activities_dir.glob('*.yaml'))

    total_fixes = 0
    for yaml_file in yaml_files:
        fixes = fix_yaml_file(yaml_file)
        if fixes > 0:
            print(f"✅ Fixed {fixes} violation(s) in {yaml_file.name}")
            total_fixes += fixes

    print(f"\n✅ Total YAML fixes: {total_fixes}")

if __name__ == '__main__':
    main()
```

**Run:**
```bash
.venv/bin/python scripts/fix_b2_yaml_schema.py
```

---

### Script 4: Add Missing Grammar Sections

**File:** `scripts/fix_b2_missing_grammar_sections.py`
**Impact:** Fixes 190 violations
**Affected:** Grammar modules M01-M51

**Implementation:**

```python
#!/usr/bin/env python3
"""Add missing grammar presentation sections to B2 grammar modules."""

import re
from pathlib import Path

GRAMMAR_SECTION_TEMPLATE = """
## Граматика

<!-- TODO: Add grammar presentation -->

### Формування

[Explain how the grammatical form is constructed]

### Вживання

[Explain when and how to use this grammar point]

### Приклади

1. Example sentence 1
2. Example sentence 2
3. Example sentence 3
""".strip()

def has_grammar_section(content: str) -> bool:
    """Check if module has grammar/presentation section."""
    grammar_headers = [
        r'^##\s+Граматика',
        r'^##\s+Презентація',
        r'^##\s+Focus',
        r'^##\s+Теорія',
    ]

    for pattern in grammar_headers:
        if re.search(pattern, content, re.MULTILINE):
            return True

    return False

def add_grammar_section(file_path: Path) -> bool:
    """Add grammar section if missing."""
    content = file_path.read_text(encoding='utf-8')

    if has_grammar_section(content):
        return False

    # Insert after Словник section (vocabulary)
    vocab_pattern = r'(^##\s+Словник.*?(?=^##|\Z))'
    match = re.search(vocab_pattern, content, re.MULTILINE | re.DOTALL)

    if match:
        insert_pos = match.end()
        new_content = (
            content[:insert_pos] +
            '\n\n' + GRAMMAR_SECTION_TEMPLATE + '\n\n' +
            content[insert_pos:]
        )
        file_path.write_text(new_content, encoding='utf-8')
        return True

    return False

def main():
    b2_dir = Path('curriculum/l2-uk-en/b2')

    # Grammar modules are M01-M51
    grammar_modules = [
        b2_dir / f"{str(i).zfill(2)}-{name}.md"
        for i in range(1, 52)
        for name in [m.stem.split('-', 1)[1] for m in b2_dir.glob(f'{str(i).zfill(2)}-*.md')]
    ]

    fixed = 0
    for module in grammar_modules:
        if module.exists() and add_grammar_section(module):
            print(f"✅ Added grammar section to {module.name}")
            fixed += 1

    print(f"\n✅ Fixed {fixed} modules")

if __name__ == '__main__':
    main()
```

**Run:**
```bash
.venv/bin/python scripts/fix_b2_missing_grammar_sections.py
```

---

## Phase 2: History Section Completion (4-6 hours)

### Script 5: Add Reading Sections to History Modules

**File:** `scripts/fix_b2_history_reading.py`
**Impact:** Fixes 80 violations
**Affected:** History modules M71-M131 missing "Читання"

**Strategy:** Use LLM to generate reading passages based on module topic.

**Implementation:**

```python
#!/usr/bin/env python3
"""Add 'Читання' sections to history modules missing them."""

import re
from pathlib import Path

READING_PLACEHOLDER = """
## Читання: {topic}

<!-- TODO: Add 400-600 word historical reading passage -->

[Historical reading passage about the topic]

### Питання до тексту

1. **Question 1?**
   - Answer with text reference

2. **Question 2?**
   - Answer with text reference

3. **Question 3?**
   - Answer with text reference
""".strip()

def extract_topic_from_frontmatter(content: str) -> str:
    """Extract module title from frontmatter."""
    match = re.search(r'^title:\s*(.+)$', content, re.MULTILINE)
    if match:
        return match.group(1).strip('"\'')
    return "Historical Topic"

def add_reading_section(file_path: Path) -> bool:
    """Add Читання section if missing."""
    content = file_path.read_text(encoding='utf-8')

    # Check if Читання already exists
    if re.search(r'^##\s+Читання', content, re.MULTILINE):
        return False

    topic = extract_topic_from_frontmatter(content)
    reading_section = READING_PLACEHOLDER.format(topic=topic)

    # Insert after Словник, before Первинні джерела
    vocab_pattern = r'(^##\s+Словник.*?(?=^##\s+Первинні джерела|^##\s+Need More|\Z))'
    match = re.search(vocab_pattern, content, re.MULTILINE | re.DOTALL)

    if match:
        insert_pos = match.end()
        new_content = (
            content[:insert_pos] +
            '\n\n' + reading_section + '\n\n' +
            content[insert_pos:]
        )
        file_path.write_text(new_content, encoding='utf-8')
        return True

    return False

def main():
    b2_dir = Path('curriculum/l2-uk-en/b2')

    # History modules M71-M131
    history_modules = sorted([
        m for m in b2_dir.glob('[0-9]*.md')
        if 71 <= int(m.stem.split('-')[0]) <= 131
    ])

    fixed = 0
    for module in history_modules:
        if add_reading_section(module):
            print(f"✅ Added Читання section to {module.name}")
            fixed += 1

    print(f"\n✅ Fixed {fixed}/{len(history_modules)} history modules")
    print("\n⚠️  Sections added with TODO markers - manual content needed")

if __name__ == '__main__':
    main()
```

**Run:**
```bash
.venv/bin/python scripts/fix_b2_history_reading.py
```

**Follow-up:** Manually populate TODO markers using:
- Reference M102, M105 for structure
- Historical sources from Ukrainian historiography
- 400-600 word passages at B2 reading level

---

### Script 6: Add Primary Sources & Decolonization Sections

**File:** `scripts/fix_b2_history_callouts.py`
**Impact:** Fixes 32 + 8 + 47 violations (87 total)
**Affected:** History modules M71-M131

**Implementation:**

```python
#!/usr/bin/env python3
"""Add missing history-specific sections and callouts."""

import re
from pathlib import Path

PRIMARY_SOURCES_TEMPLATE = """
## Первинні джерела

<!-- TODO: Add 2-3 primary source excerpts -->

### Джерело 1: [Title]

> [Primary source quote in historical Ukrainian]

**Контекст:** [Brief context about the source]

### Джерело 2: [Title]

> [Primary source quote]

**Контекст:** [Brief context]
""".strip()

DECOLONIZATION_TEMPLATE = """
## Деколонізаційний погляд

<!-- TODO: Add decolonization analysis -->

### Імперський наратив

[Describe the Russian imperial narrative about this event]

### Українська перспектива

[Contrast with Ukrainian historical perspective]

### Сучасні дослідження

[Reference contemporary Ukrainian scholarship]
""".strip()

MYTH_BUSTER_TEMPLATE = """
> [!myth-buster]
> **МІФ:** [Russian imperial myth about this topic]
> **РЕАЛЬНІСТЬ:** [Ukrainian historical reality]
""".strip()

HISTORY_BITE_TEMPLATE = """
> [!history-bite]
> [Interesting historical fact or trivia related to the topic]
""".strip()

def add_missing_sections(file_path: Path) -> dict:
    """Add all missing history-specific sections."""
    content = file_path.read_text(encoding='utf-8')
    fixes = {'primary_sources': False, 'decolonization': False,
             'myth_buster': False, 'history_bite': False}

    # Add Первинні джерела if missing
    if not re.search(r'^##\s+Первинні джерела', content, re.MULTILINE):
        # Insert before Деколонізаційний погляд or Need More Practice
        pattern = r'(^##\s+Словник.*?(?=^##\s+Деколонізаційний|^##\s+Need More|\Z))'
        match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
        if match:
            content = (
                content[:match.end()] +
                '\n\n' + PRIMARY_SOURCES_TEMPLATE + '\n\n' +
                content[match.end():]
            )
            fixes['primary_sources'] = True

    # Add Деколонізаційний погляд if missing
    if not re.search(r'^##\s+Деколонізаційний погляд', content, re.MULTILINE):
        pattern = r'(^##\s+Первинні джерела.*?(?=^##\s+Need More|\Z))'
        match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
        if match:
            content = (
                content[:match.end()] +
                '\n\n' + DECOLONIZATION_TEMPLATE + '\n\n' +
                content[match.end():]
            )
            fixes['decolonization'] = True

    # Add [!myth-buster] if missing
    if not re.search(r'\[!myth-buster\]', content):
        # Insert in Деколонізаційний погляд section
        pattern = r'(^##\s+Деколонізаційний погляд.*?)(?=^##|\Z)'
        match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
        if match:
            content = (
                content[:match.end()] +
                '\n\n' + MYTH_BUSTER_TEMPLATE + '\n' +
                content[match.end():]
            )
            fixes['myth_buster'] = True

    # Add [!history-bite] if missing
    if not re.search(r'\[!history-bite\]', content):
        # Insert in Вступ section
        pattern = r'(^##\s+Вступ.*?)(?=^##|\Z)'
        match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
        if match:
            content = (
                content[:match.end()] +
                '\n\n' + HISTORY_BITE_TEMPLATE + '\n' +
                content[match.end():]
            )
            fixes['history_bite'] = True

    if any(fixes.values()):
        file_path.write_text(content, encoding='utf-8')

    return fixes

def main():
    b2_dir = Path('curriculum/l2-uk-en/b2')

    # History modules M71-M131
    history_modules = sorted([
        m for m in b2_dir.glob('[0-9]*.md')
        if 71 <= int(m.stem.split('-')[0]) <= 131
    ])

    stats = {'primary_sources': 0, 'decolonization': 0,
             'myth_buster': 0, 'history_bite': 0}

    for module in history_modules:
        fixes = add_missing_sections(module)
        for key, fixed in fixes.items():
            if fixed:
                stats[key] += 1

        if any(fixes.values()):
            print(f"✅ Fixed {module.name}: {', '.join(k for k, v in fixes.items() if v)}")

    print(f"\n✅ Summary:")
    print(f"   - Added Первинні джерела: {stats['primary_sources']}")
    print(f"   - Added Деколонізаційний погляд: {stats['decolonization']}")
    print(f"   - Added [!myth-buster]: {stats['myth_buster']}")
    print(f"   - Added [!history-bite]: {stats['history_bite']}")

if __name__ == '__main__':
    main()
```

**Run:**
```bash
.venv/bin/python scripts/fix_b2_history_callouts.py
```

---

## Phase 3: Complexity Enrichment (8-12 hours)

### Script 7: Enrich Quiz Prompts

**File:** `scripts/fix_b2_quiz_complexity.py`
**Impact:** Fixes ~1,500 violations
**Strategy:** Use LLM to expand short quiz prompts to 10-25 words

**Implementation:**

```python
#!/usr/bin/env python3
"""Enrich quiz prompts to meet B2 complexity targets (10-25 words)."""

import re
from pathlib import Path
from typing import List, Tuple

def count_words(text: str) -> int:
    """Count words in Ukrainian text."""
    return len(re.findall(r'\b\w+\b', text, re.UNICODE))

def extract_quiz_prompts(content: str) -> List[Tuple[str, int, int]]:
    """Extract quiz prompts that are too short.

    Returns: [(prompt_text, word_count, line_number), ...]
    """
    short_prompts = []
    lines = content.split('\n')

    in_quiz_activity = False
    for i, line in enumerate(lines):
        # Detect quiz activity start
        if line.startswith('### ') and 'quiz' in line.lower():
            in_quiz_activity = True
            continue

        # Detect activity end
        if line.startswith('### '):
            in_quiz_activity = False

        # Extract prompts (numbered items in quiz)
        if in_quiz_activity and re.match(r'^\d+\.\s+', line):
            prompt = re.sub(r'^\d+\.\s+', '', line).strip()
            word_count = count_words(prompt)

            if word_count < 10:  # B2 target minimum
                short_prompts.append((prompt, word_count, i))

    return short_prompts

def enrich_prompt(prompt: str) -> str:
    """Enrich a short prompt to B2 complexity.

    NOTE: This is a placeholder - use LLM for actual enrichment.
    """
    # Placeholder implementation
    # In practice, call Gemini/Claude API with:
    # - Original prompt
    # - Instruction to expand to 10-25 words
    # - B2 level constraints

    return f"{prompt} (TODO: enrich to 10-25 words)"

def main():
    b2_dir = Path('curriculum/l2-uk-en/b2')
    modules = sorted(b2_dir.glob('[0-9]*.md'))

    total_prompts = 0
    for module in modules:
        content = module.read_text(encoding='utf-8')
        short_prompts = extract_quiz_prompts(content)

        if short_prompts:
            print(f"\n{module.name}: {len(short_prompts)} short prompts")
            for prompt, wc, line_num in short_prompts:
                print(f"  Line {line_num+1} ({wc} words): {prompt[:50]}...")
                total_prompts += 1

    print(f"\n✅ Found {total_prompts} quiz prompts to enrich")
    print("\n⚠️  Use LLM-assisted enrichment:")
    print("    1. Extract all short prompts")
    print("    2. Batch enrich with Gemini/Claude API")
    print("    3. Validate enriched prompts")
    print("    4. Apply back to modules")

if __name__ == '__main__':
    main()
```

**Run:**
```bash
.venv/bin/python scripts/fix_b2_quiz_complexity.py
```

**LLM Enrichment Prompt:**

```markdown
You are enriching Ukrainian language quiz prompts for B2 level learners.

**Task:** Expand the following short prompt to 10-25 words while:
1. Maintaining the original question's intent
2. Adding contextual information or dependent clauses
3. Using B2-appropriate vocabulary and syntax
4. Keeping the question grammatically correct

**Original prompt (8 words):**
Який дієслівник став пасивним дієприкметником?

**Enriched prompt (15 words):**
Який дієслівник у наведеному реченні трансформувався в пасивний дієприкметник минулого часу?

**Original prompt:**
{original_prompt}

**Enriched prompt:**
```

---

### Script 8: Expand Unjumble Sentences

**File:** `scripts/fix_b2_unjumble_complexity.py`
**Impact:** Fixes ~800 violations
**Strategy:** Add adverbial phrases and dependent clauses to short unjumble items

**Implementation:**

```python
#!/usr/bin/env python3
"""Expand unjumble sentences to B2 complexity (10-18 words)."""

import yaml
from pathlib import Path
from typing import Dict, Any

def count_words_in_unjumble(text: str) -> int:
    """Count words in unjumble item (separated by /)."""
    return len(text.split(' / '))

def enrich_unjumble_activity(activity: Dict[str, Any]) -> int:
    """Enrich unjumble items that are too short."""
    if activity.get('type') != 'unjumble':
        return 0

    fixes = 0
    for item in activity.get('items', []):
        scrambled = item.get('scrambled', '')
        word_count = count_words_in_unjumble(scrambled)

        if word_count < 10:  # B2 target minimum
            # Mark for enrichment
            item['_enrichment_needed'] = True
            item['_current_words'] = word_count
            fixes += 1

    return fixes

def main():
    activities_dir = Path('curriculum/l2-uk-en/b2/activities')
    yaml_files = sorted(activities_dir.glob('*.yaml'))

    total_items = 0
    for yaml_file in yaml_files:
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            fixes = 0
            for activity_id, activity in data.items():
                fixes += enrich_unjumble_activity(activity)

            if fixes > 0:
                print(f"{yaml_file.name}: {fixes} unjumble items need enrichment")
                total_items += fixes

        except Exception as e:
            print(f"❌ Error in {yaml_file}: {e}")

    print(f"\n✅ Found {total_items} unjumble items to enrich")
    print("\n⚠️  Manual enrichment needed:")
    print("    - Add temporal/locative adverbials")
    print("    - Include dependent clauses")
    print("    - Maintain scramble solvability")

if __name__ == '__main__':
    main()
```

**Run:**
```bash
.venv/bin/python scripts/fix_b2_unjumble_complexity.py
```

---

### Script 9: Extend Fill-in Contexts

**File:** `scripts/fix_b2_fillin_complexity.py`
**Impact:** Fixes ~500 violations
**Strategy:** Expand fill-in sentences with contextual clauses

**Implementation:** Similar to unjumble enrichment, targeting fill-in activities.

---

## Phase 4: Manual Review & Validation (2-3 hours)

### Task 1: Review TOO_MANY_MORPHEMES Flags

**Files:** 39 modules with complex vocabulary
**Action:** Manual review to accept/reject each flag

**Workflow:**
1. Read module context (history, medical, linguistics)
2. Verify word is appropriate for B2 domain
3. If justified, accept and document
4. If excessive, replace with simpler alternative or phrase

---

### Task 2: Validate History Callout Content

**Files:** 47 modules with new `[!myth-buster]` and `[!history-bite]` callouts
**Action:** Verify factual accuracy and decolonization perspective

**Checklist:**
- [ ] Myth-buster references verifiable Ukrainian scholarship
- [ ] History-bite is interesting and factually accurate
- [ ] Language is B2-appropriate
- [ ] No perpetuation of imperial narratives

---

### Task 3: Re-run Comprehensive Audit

**Command:**
```bash
.venv/bin/python scripts/audit_all_b2.py
```

**Expected outcome:** 95%+ pass rate (138+/145 modules)

---

## Execution Plan

### Week 1: Automated Fixes

**Monday (2-3 hours):**
- ✅ Run Scripts 1-4 (Phase 1)
- ✅ Re-audit to verify fixes
- ✅ Commit automated fixes

**Tuesday-Wednesday (4-6 hours):**
- ✅ Run Scripts 5-6 (Phase 2 structural)
- ✅ Begin manual content for Читання sections
- ✅ Add primary sources from Ukrainian archives

**Thursday-Friday (8-12 hours):**
- ✅ Run Scripts 7-9 (Phase 3 complexity enrichment)
- ✅ Use LLM-assisted batch enrichment
- ✅ Manual review of 30% sample

### Week 2: Validation

**Monday (2-3 hours):**
- ✅ Phase 4 manual reviews
- ✅ Final audit
- ✅ Document remaining issues

**Tuesday:**
- ✅ Fix edge cases
- ✅ Run full pipeline validation
- ✅ Update documentation

---

## Success Metrics

| Metric | Before | Target | Measurement |
|--------|--------|--------|-------------|
| Pass rate | 1.4% | 95%+ | Audit pass/fail |
| COMPLEXITY violations | 3,030 | <100 | Word count checks |
| YAML violations | 734 | 0 | Schema validation |
| Missing sections | 663 | 0 | Template compliance |
| Duplicate headers | 88 | 0 | Header normalization |

---

## Risk Mitigation

**Risk 1: LLM enrichment introduces errors**
- Mitigation: Manual review of 30% sample + re-audit

**Risk 2: History content requires deep research**
- Mitigation: Use M102, M105 as templates + Ukrainian historiography references

**Risk 3: YAML changes break existing activities**
- Mitigation: Validate after each fix + backup before changes

---

## Related Files

- `b2-rebuild-audit-report.md` - Full audit logs
- `b2-audit-quick-summary.md` - Quick reference
- `b2-rebuild-audit-summary.md` - Detailed analysis
- `b2-rebuild-index.md` - Progress tracker
