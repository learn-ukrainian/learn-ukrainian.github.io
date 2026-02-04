# /expand - Content Expansion Skill

<skill>
name: expand
description: Expand module content to meet word count target. Use when audit shows word count shortfall.
arguments: module_path - Path to the module file (e.g., curriculum/l2-uk-en/c1-bio/danylo-apostol.md)
</skill>

## Purpose

When a module fails audit due to insufficient word count, this skill guides proper content expansion. **NEVER change the word target - always expand the content.**

## Critical Rule

```
❌ FORBIDDEN: Changing word_target in meta file to match short content
✅ REQUIRED: Expand content to meet the existing target
```

Word targets exist because the content deserves that depth. Ukrainian historical figures, events, and literature are rich topics that warrant thorough treatment.

## Workflow

### Step 1: Assess the Gap

```bash
# Run audit to see current vs target
scripts/audit_module.sh {module_path}
```

Note:
- Current word count
- Target word count
- Gap (how many words needed)
- Which sections are under target

### Step 2: Read Research Notes

Check if research notes exist:
```
curriculum/l2-uk-en/{track}/audit/{slug}-research.md
```

If no research notes exist, run `/research {topic}` first.

### Step 3: Identify Expansion Opportunities

For each section under target, consider:

**Вступ (Introduction):**
- Add hook with compelling detail
- Expand historical significance
- Add "why this matters today" angle

**Життєпис (Biography):**
- Add more chronological detail
- Include specific dates and locations
- Add quotes from primary sources
- Describe key relationships/alliances
- Include lesser-known but significant events

**Історичний контекст (Historical Context):**
- Expand on era's political situation
- Add European/regional context
- Include economic/social factors
- Describe competing powers and interests

**Внесок (Contribution):**
- Detail specific achievements
- Add concrete examples
- Include lasting impacts
- Quote contemporaries' assessments

**Останні роки (Final Years):**
- Add circumstances of death/decline
- Include final works/acts
- Describe immediate aftermath

**Спадщина (Legacy):**
- Modern commemorations
- Scholarly reassessments
- Cultural representations
- Relevance to contemporary Ukraine

**Підсумок (Conclusion):**
- Synthesize significance
- Connect to broader themes
- End with memorable insight

### Step 4: Expand Content

When expanding, maintain:
- Natural Ukrainian prose (no calques)
- Appropriate C1 complexity
- Flow and coherence
- Callout variety ([!background], [!quote], [!myth-buster])

**Quality over filler:**
- Add substantive information, not padding
- Each sentence should add value
- Use research to add accurate details

### Step 5: Verify

After expansion:
```bash
scripts/audit_module.sh {module_path}
```

Continue expanding until word target is met (or exceeded - that's fine!).

## Example Usage

```
User: /expand curriculum/l2-uk-en/c1-bio/danylo-apostol.md

Claude:
1. Reading audit log...
   Current: 1465 words, Target: 4300 words, Gap: 2835 words

2. Checking research notes...
   Found: curriculum/l2-uk-en/c1-bio/audit/danylo-apostol-research.md

3. Section analysis:
   - Вступ: 150/600 words (-450)
   - Життєпис: 400/1600 words (-1200)
   - Історичний контекст: 200/600 words (-400)
   ...

4. Expanding sections using research...
   [Expands each section with substantive content]

5. Final audit:
   Words: 4523/4300 ✅
```

## Integration

This skill should be called:
- After `/module-fix` if word count is still under target
- When audit shows `Words ❌` failure
- As part of Stage 4 review loop

**From /module-fix:**
```
If audit shows word count failure:
  → Call /expand instead of changing meta
```

## Anti-Pattern Detection

If you find yourself wanting to:
- Change `word_target` in meta file → STOP, use /expand
- Add filler phrases → STOP, do more research
- Copy from English sources → STOP, use Ukrainian sources
- Skip sections → STOP, every section needs expansion

The mission is Ukrainian education. Quality and depth matter.
