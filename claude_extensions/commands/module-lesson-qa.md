# /module-lesson-qa

Validate lesson content before locking.

## Usage

```
/module-lesson-qa {level} {module_num}
```

## Instructions

Parse arguments: $ARGUMENTS

### Step 1: Read Phase Instructions

Read: `claude_extensions/phases/module-lesson-qa.md`

### Step 2: Load Files

**For tracks (b2-hist, c1-bio, lit, c1-hist, b2-pro):**

1. Look up slug from manifest:
   ```bash
   yq ".levels.\"{level}\".modules[{module_num-1}]" curriculum/l2-uk-en/curriculum.yaml
   ```

2. Load meta file (LOCKED - reference only):
   ```
   curriculum/l2-uk-en/{level}/meta/{slug}.yaml
   ```

3. Load lesson file:
   ```
   curriculum/l2-uk-en/{level}/{slug}.md
   ```

**For core levels (a1, a2, b1, b2, c1, c2):**

1. Determine slug from module number

2. Load files:
   ```
   curriculum/l2-uk-en/{level}/meta/{slug}.yaml
   curriculum/l2-uk-en/{level}/{slug}.md
   ```

### Step 3: Run All Checks

Follow validation checklist from phase instructions:

1. File structure
2. Word count accuracy (CRITICAL)
3. Content outline coverage
4. Engagement boxes
5. Example sentences
6. Mini-dialogues (if applicable)
7. Required vocabulary
8. Forbidden content
9. Immersion percentage
10. YAML frontmatter match
11. Primary sources (if history module)
12. Ukrainian language quality (optional)

### Step 4: Output

**On PASS:**
```
LESSON-QA: PASS

✓ File structure complete
✓ Word count: {total}/{target} ({percentage}%)
  - {section}: {count}/{target} words
  ...
✓ Content outline: All {N} sections present
✓ Engagement boxes: {count} (min: {min})
✓ Example sentences: {count} (min: {min})
✓ [Other checks...]

LESSON LOCKED. Proceed to: /module-act {level} {module_num}
```

**On FAIL:**
```
LESSON-QA: FAIL

Violations:
1. [CHECK]: {issue}
2. [CHECK]: {issue}

Fix {slug}.md and re-run: /module-lesson-qa {level} {module_num}
```

**On PHASE REWIND:**
```
PHASE UNLOCK REQUIRED: {reason}

Meta.yaml needs adjustment.
Fix meta, re-run /module-meta-qa, then regenerate lesson.
```
