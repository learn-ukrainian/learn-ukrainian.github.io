# /module-lesson

Generate main lesson content from locked meta.yaml.

> **🤝 COLLABORATION RULE:** Write content yourself. Ask the other agent for help (research, facts, validation) when stuck. Never guess or hallucinate - collaboration is faster than guessing wrong.

## Usage

```
/module-lesson {level} {module_num}
```

## Instructions

Parse arguments: $ARGUMENTS

### Step 1: Read Phase Instructions

Read: `claude_extensions/phases/module-lesson.md`

### Step 2: Load Plan and Meta YAML

> **Architecture v2.0:** Plans are immutable source of truth. Meta is mutable build config.

**For tracks (b2-hist, c1-bio, lit, c1-hist, b2-pro):**

1. Look up slug from manifest:
   ```bash
   yq ".levels.\"{level}\".modules[{module_num-1}]" curriculum/l2-uk-en/curriculum.yaml
   ```

2. Load plan file (IMMUTABLE - content_outline, word_target, objectives):
   ```
   curriculum/l2-uk-en/plans/{level}/{slug}.yaml
   ```

3. Load meta file (MUTABLE - naturalness, version):
   ```
   curriculum/l2-uk-en/{level}/meta/{slug}.yaml
   ```

**For core levels (a1, a2, b1, b2, c1, c2):**

1. Determine slug from module number (usually zero-padded: 01, 02, etc.)

2. Load plan file (IMMUTABLE):
   ```
   curriculum/l2-uk-en/plans/{level}/{num}-{slug}.yaml
   ```

3. Load meta file (MUTABLE):
   ```
   curriculum/l2-uk-en/{level}/meta/{num}-{slug}.yaml
   ```

**Critical:** Content generation MUST follow the plan's `content_outline` exactly:
- Section names from plan
- Word targets from plan
- Points to cover from plan

### Step 3: Generate Content

> **OVERSHOOT RULE: Write to 1.5× the word_target on first draft.**
> For a 4000-word target, write 5500–6000 words. For 3000, write 4500.
> Trimming excess is trivial. Expanding later burns 30%+ of context in audit-fix cycles.
> This single rule eliminates the #1 workflow friction: iterative word count expansion.

> **PRE-PLAN CALLOUTS**: Before writing any prose, list the 6+ engagement callouts
> (myth-buster, decolonization, quote, etc.) with their target sections.

Follow the generation process from phase instructions:

1. Load meta.yaml and appropriate template
2. Generate SCOPE comment (NO frontmatter - metadata is in meta.yaml)
3. Pre-plan callout placement (section + type for each of 6+ callouts)
4. Generate title and introduction
5. **Generate content sections (section-by-section, targeting 1.5× word allocation per section)**
6. Generate summary
7. Verify total word count (should be ~150% of target)

### Step 4: Output

Write generated content to:
```
curriculum/l2-uk-en/{level}/{slug}.md
```

**On success:**
```
LESSON GENERATED: curriculum/l2-uk-en/{level}/{slug}.md

Word count breakdown:
- {section}: {count}/{target} words
...
- Total: {total}/{word_target} words ({percentage}%)

✓ Engagement boxes: {count} (min: {level_min})
✓ Example sentences: {count} (min: {level_min})

Next: Run /module-lesson-qa {level} {module_num}
```

**On error:**
```
LESSON GENERATION FAILED: {reason}

Check meta.yaml and try again.
```
