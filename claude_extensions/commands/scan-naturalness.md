# Naturalness Scan Skill

## Purpose
Scan activities for naturalness issues while maintaining vocabulary and grammar constraints.

## How Naturalness Evaluation Works

**You evaluate naturalness directly using your Ukrainian language knowledge.** No external tools or MCP servers are required.

As an LLM trained on extensive Ukrainian text, you can assess:
- Whether text flows naturally
- Appropriate use of discourse markers
- Register matching CEFR level
- Authentic vs robotic phrasing

**IMPORTANT:** Naturalness is NEVER "N/A" for any module with Ukrainian text. Even alphabet modules have Ukrainian instructions that must sound natural.

### What to Evaluate

1. **Activity instructions** (e.g., "З'єднайте відповідні елементи")
2. **Multi-sentence prose** (cloze, fill-in, unjumble passages)
3. **Quiz explanations** in Ukrainian
4. **Any other Ukrainian text** in activities

### After Evaluation

Update the module's meta file with your score:
```yaml
# curriculum/l2-uk-en/{level}/meta/{num}-{slug}.yaml
naturalness:
  score: 9  # Your evaluated score (1-10)
  status: PASS  # PASS if score >= 8, else FAIL
```

## Usage

```
/scan-naturalness <level> <start_module> <end_module>
```

**Examples:**
```bash
/scan-naturalness a2 1 11      # Scan A2 M01-M11 (first checkpoint)
/scan-naturalness a2 12 25     # Scan A2 M12-M25 (second batch)
/scan-naturalness b1 1 20      # Scan B1 M01-M20
```

## Parameters

- `<level>`: CEFR level (a1, a2, b1, b2, c1, c2)
- `<start_module>`: First module number (1-based)
- `<end_module>`: Last module number (inclusive)

## Instructions

When this skill is invoked, follow the protocol in `claude_extensions/protocols/a1-naturalness-scan.md` with these adaptations:

### 1. Load Level Context

```bash
# Read level plan for phases and scope
READ: curriculum/l2-uk-en/plans/{level}.yaml

# Read module plans for vocabulary/grammar scope
READ: curriculum/l2-uk-en/plans/{level}/*.yaml

# Read Ukrainian State Standard section for grammar progression
READ: docs/l2-uk-en/UKRAINIAN-STATE-STANDARD-2024.md (if exists)
```

### 2. Build Vocabulary Validation Tool

**For A1:**
```bash
# Use existing tool
TOOL: /tmp/query_a1_vocab.py
```

**For A2+:**
```python
# Create level-specific query tool
CREATE: /tmp/query_{level}_vocab.py

#!/usr/bin/env python3
import yaml
from pathlib import Path

vocab_dir = Path("curriculum/l2-uk-en/{level}/vocabulary")

def get_cumulative_vocab(up_to_module: int):
    """Get all vocabulary from M01 to M{up_to_module}."""
    words = set()
    for i in range(1, up_to_module + 1):
        yaml_files = list(vocab_dir.glob(f"{i:02d}-*.yaml"))
        if not yaml_files:
            continue
        with open(yaml_files[0], 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            if data and 'items' in data:
                for item in data['items']:
                    if 'lemma' in item:
                        words.add(item['lemma'])
    return sorted(words)

def check_word_module(word: str):
    """Find which module introduces a word."""
    for yaml_file in sorted(vocab_dir.glob("*.yaml")):
        with open(yaml_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            if data and 'items' in data:
                for item in data['items']:
                    if item.get('lemma') == word:
                        return data.get('module', 'unknown')
    return None

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python query_{level}_vocab.py <module_num>")
        print("   or: python query_{level}_vocab.py check <word>")
        sys.exit(1)

    if sys.argv[1] == "check":
        word = sys.argv[2]
        module = check_word_module(word)
        if module:
            print(f"'{word}' introduced in module: {module}")
        else:
            print(f"'{word}' not found in {level.upper()} vocabulary")
    else:
        module_num = int(sys.argv[1])
        vocab = get_cumulative_vocab(module_num)
        print(f"Cumulative vocabulary M01-M{module_num:02d}: {len(vocab)} words")
        print("\\n".join(vocab))
```

### 3. Scan Module Range

For each module in range `<start_module>` to `<end_module>`:

```bash
# Read activity file
READ: curriculum/l2-uk-en/{level}/activities/{num}-{slug}.yaml

# Read meta file to check current naturalness status
READ: curriculum/l2-uk-en/{level}/meta/{num}-{slug}.yaml

# Extract ALL Ukrainian text:
# - Activity instructions (always present)
# - Multi-sentence prose (cloze, fill-in, unjumble)
# - Quiz explanations in Ukrainian
# - Mark-the-words passages
EXTRACT: All Ukrainian text content

# Analyze naturalness using your Ukrainian language knowledge
ANALYZE:
  - Flow: Do sentences connect naturally?
  - Discourse markers: (а, але, потім, тому, спочатку, etc.)
  - Register: Matches CEFR level expectations?
  - Authenticity: Would a native speaker write this?
  - Instructions: Natural phrasing for activity context?

# Score 1-10
SCORE: Based on naturalness criteria (target: 8/10 for content, 7/10 for checkpoints)

# Update meta file with score
UPDATE: curriculum/l2-uk-en/{level}/meta/{num}-{slug}.yaml
  naturalness:
    score: {score}
    status: PASS  # if score >= 8, else FAIL

# If score < 8, validate vocabulary before proposing fix
VALIDATE: All words against M01-M{current} cumulative vocab
```

### 4. Output Format

Generate report at `/tmp/{level}-naturalness-scan-m{start}-m{end}.md`:

```markdown
# {LEVEL} Naturalness Scan Report - M{start}-M{end}
**Date:** {date}
**Protocol:** claude_extensions/protocols/a1-naturalness-scan.md
**Scope:** M{start}-M{end} ({count} modules)

---

## Executive Summary

**Total modules:** {count}
**Prose activities found:** {count} modules
**Flagged for naturalness issues:** {count} modules
**Checkpoints deferred:** {count} modules

---

## Scan Results by Module

### M{num}: {Title} [✅ PASS | ⚠️ FLAGGED | ⏸️ DEFERRED]
**Status:** [details]
**Activities:** [list]
**Sample sentences:**
```
[if prose exists]
```
**Naturalness Analysis:**
- [issues if flagged]

**Score:** {score}/10

[If flagged:]
**Fix approach:** [strategy]
**Vocabulary constraint:** M01-M{num} = {word_count} words
**Grammar constraint:** {allowed constructs}

---

## Summary by Status

### ✅ PASS ({count} modules)
- M{num}: {title} (score {score}/10)

### ⚠️ FLAGGED ({count} modules)
- M{num}: {title} (score {score}/10)

### ⏸️ DEFERRED ({count} modules)
- M{num}: {title} (checkpoints - different standards)

---

## Recommended Actions

[For each flagged module, provide fix strategy]

---

## Next Steps

1. Review flagged modules
2. Create fixes for score < 8
3. Validate vocabulary constraints
4. Apply approved fixes
5. Commit with detailed message
```

### 5. Critical Constraints

**NEVER violate:**
- Vocabulary scope: Only words from M01-M{current}
- Grammar scope: Only constructs introduced by curriculum plan
- Pedagogical focus: Preserve grammar drill patterns
- CEFR level: Maintain appropriate complexity

**Checkpoint handling:**
- Score checkpoints separately
- Accept 6-7/10 for comprehensive assessments
- Mark as DEFERRED if unclear standards

### 6. Genre-Specific Naturalness Criteria

**Different genres have different naturalness expectations.** Do NOT penalize genre-appropriate style.

| Genre | Naturalness Markers | What NOT to penalize |
|-------|---------------------|---------------------|
| **Formal/business letters** | Formulaic structure, consistent register, polite forms | Fewer discourse markers, repetitive closings (З повагою, Щиро дякую) |
| **Narrative/dialogue** | Discourse markers (а, але, потім), varied sentence length, emotional range | Colloquial expressions at appropriate levels |
| **Historical/seminar (HIST/BIO)** | Literary quality, era-appropriate terminology, academic register | Formal tone, complex sentences, fewer informal markers |
| **Activity instructions** | Task-appropriate formality, clear imperatives | Repetitive patterns (Виберіть, Заповніть, З'єднайте) |
| **Checkpoint assessments** | Assessment register, consistent format | Lower variety (6-7/10 acceptable) |

**Examples:**

```yaml
# Formal letter - CORRECT (fewer discourse markers expected)
text: |
  Шановна пані Коваленко,

  Пишу, щоб запитати про можливість стажування.

  З повагою,
  Андрій
naturalness: 9/10  # Appropriate for formal letter

# Narrative - needs discourse markers
text: |
  Спочатку Марія пішла до крамниці. Потім вона купила хліб.
  А ввечері вона приготувала вечерю.
naturalness: 9/10  # Good flow with markers

# Historical module - literary register expected
text: |
  Козацька старшина зібралася на раду. Гетьман виступив з промовою,
  закликаючи до єдності перед спільним ворогом.
naturalness: 9/10  # Appropriate formal/historical register
```

**Key principle:** Evaluate naturalness WITHIN the genre's conventions, not against a universal standard.

### 7. Economical Scanning

To minimize token usage:
- Batch file reads (Read multiple activity files in parallel)
- For minimal-prose modules (alphabet, matching), focus on instruction text
- Group similar issues in report
- Read meta files in parallel with activity files

### 8. After Scan Complete

Present summary to user:
```
✅ Scan complete: {LEVEL} M{start}-M{end}
📊 {passed} passed, {flagged} flagged, {deferred} deferred
📝 Full report: /tmp/{level}-naturalness-scan-m{start}-m{end}.md

Next: Review flagged modules? Create fixes? Scan next batch?
```

## A2 Batch Recommendations

Scan A2 in checkpoint-based batches:
1. `/scan-naturalness a2 1 11` - Cases section
2. `/scan-naturalness a2 12 25` - Aspect section
3. `/scan-naturalness a2 26 35` - Mid-level section
4. `/scan-naturalness a2 36 44` - Word formation section
5. `/scan-naturalness a2 45 56` - Vocabulary section
6. `/scan-naturalness a2 57 58` - Final modules

## Notes

- Use parallel tool calls for efficiency
- Evaluate naturalness using your Ukrainian language knowledge (no MCP required)
- **Always update meta files** with score and status after evaluation
- Validate ALL vocabulary before proposing fixes
- Maintain strict grammar progression constraints
- Naturalness is NEVER "N/A" - every module with Ukrainian text needs a score
