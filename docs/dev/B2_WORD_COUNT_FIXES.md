# Task: Fix B2 Word Count Issues

**Issue:** 8 B2 modules fall short of 1750-word minimum (8-97 words short)

**Your task:** Expand content to meet B2 word count requirement while maintaining quality.

---

## Modules to Fix

| Module | File Pattern | Current | Target | Needs |
|--------|--------------|---------|--------|-------|
| M116 | `curriculum/l2-uk-en/b2/116-*.md` | 1653 | 1750 | +97 words |
| M118 | `curriculum/l2-uk-en/b2/118-*.md` | 1706 | 1750 | +44 words |
| M119 | `curriculum/l2-uk-en/b2/119-*.md` | 1742 | 1750 | +8 words |
| M120 | `curriculum/l2-uk-en/b2/120-*.md` | 1724 | 1750 | +26 words |
| M123 | `curriculum/l2-uk-en/b2/123-*.md` | 1709 | 1750 | +41 words |
| M124 | `curriculum/l2-uk-en/b2/124-*.md` | 1676 | 1750 | +74 words |
| M127 | `curriculum/l2-uk-en/b2/127-*.md` | 1656 | 1750 | +94 words |
| M128 | `curriculum/l2-uk-en/b2/128-*.md` | 1720 | 1750 | +30 words |

**Total:** 8 modules, 413 words to add

---

## Process for Each Module

### 1. Find Module File
```bash
# Example for M116
fd "^116-" curriculum/l2-uk-en/b2/
# Returns: curriculum/l2-uk-en/b2/116-*.md
```

### 2. Read Module
Understand:
- Module topic (likely history or advanced grammar)
- Existing narrative structure
- Where expansion fits naturally

### 3. Identify Expansion Points

**B2-specific expansion areas:**
- **Historical modules:** Add historical context, primary source quotes, timeline details
- **Grammar modules:** Add advanced use cases, stylistic nuances, register variations
- **Cultural modules:** Add contemporary relevance, societal impact analysis
- Expand scholarly explanations with academic depth

**Good expansion strategies:**
- Add transitional paragraphs between major sections
- Expand cause-and-effect explanations in historical narratives
- Add comparative analysis (Ukrainian vs. other languages/cultures)
- Enrich critical thinking prompts in engagement boxes

### 4. Expand Content with B2 Depth

**Example (historical module needing +97 words):**
```markdown
# BEFORE:
Голодомор 1932-1933 став трагедією українського народу. Мільйони людей загинули від штучного голоду.

# AFTER:
Голодомор 1932-1933 років став однією з найтрагічніших сторінок в історії українського народу.
За різними оцінками, від штучно створеного радянською владою голоду загинуло від 3 до 7 мільйонів українців.
Ця трагедія була не природною катастрофою, а свідомою політикою тоталітарного режиму,
спрямованою на знищення українського селянства та придушення національної ідентичності.
Конфіскація зерна, заборона пересування селян та блокада постраждалих регіонів
свідчать про геноцидний характер цих подій.
```

**B2 Immersion Requirement:**
- Body text must be 98%+ Ukrainian (100% preferred)
- Only technical terms in parentheses if needed
- All examples, explanations, narratives in Ukrainian

### 5. Verify Module Passes Audit

After editing:
```bash
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b2/116-*.md
```

**Check:**
- ✅ Word count ≥1750 (B2 minimum)
- ✅ Immersion ≥98%
- ✅ All other gates pass (activities, pedagogy, richness)

### 6. Run Pipeline

```bash
npm run pipeline l2-uk-en b2 116
```

---

## Rules & Constraints

### ✅ DO
- Add scholarly depth and nuance
- Enrich historical context and analysis
- Expand critical thinking elements
- Add primary source references (for history modules)
- Maintain 100% Ukrainian in body text

### ❌ DO NOT
- Change vocabulary (must match curriculum plan)
- Modify grammar explanations (accuracy critical)
- Change activities (separate YAML files)
- Add English text (immersion violation)
- Change module structure or pedagogy

---

## B2-Specific Quality Standards

**B2 Module Requirements:**
- Word count: 1750-3000 words (strict minimum: 1750)
- Immersion: 98%+ (100% preferred)
- Vocabulary: 25-40 items
- Activities: 12-14 total
- Richness: 95%+ (deep examples, scholarly engagement)

**B2 Depth Characteristics:**
- Historical analysis (not just facts)
- Cause-and-effect reasoning
- Multiple perspectives
- Contemporary relevance
- Academic rigor

---

## Workflow

**Process modules in order: M116 → M118 → M119 → M120 → M123 → M124 → M127 → M128**

For each module:
1. ✅ Find file
2. ✅ Read content
3. ✅ Edit (add needed words with B2-appropriate depth)
4. ✅ Audit (verify passes)
5. ✅ Pipeline (validate output)
6. ✅ Mark complete

**Track progress** - report after each module.

---

## Module Context Hints

Based on module numbers, likely topics:

**M116-M120:** Likely early 20th century history (WWI, revolution era)
**M123-M124:** Likely Soviet period (1920s-1930s)
**M127-M128:** Likely mid-Soviet period or cultural topics

**For history modules:**
- Add chronological context
- Expand on key figures and their motivations
- Connect events to broader Ukrainian narrative
- Add impact analysis

**For grammar modules:**
- Add advanced use cases
- Show stylistic variations
- Provide register-specific examples
- Connect to literary usage

---

## Deliverable

When complete, report:

1. **Summary table:**
   | Module | Topic | Words Added | Final Count | Audit | Pipeline |
   |--------|-------|-------------|-------------|-------|----------|
   | M116 | [title] | +97 | 1750 | ✅ | ✅ |
   | ... | ... | ... | ... | ... | ... |

2. **Expansion strategy summary:**
   - Where content was added
   - Any patterns or challenges
   - Module-specific notes

3. **Verification:**
   - All 8 modules audit passing
   - All 8 modules pipeline passing

---

## Context Files

**Read these first:**
- `/Users/krisztiankoos/projects/learn-ukrainian/CLAUDE.md` - Project instructions
- `/Users/krisztiankoos/projects/learn-ukrainian/docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md` - Quality standards

**Reference:**
- `claude_extensions/quick-ref/b2.md` - B2-specific requirements (if exists)
- `docs/l2-uk-en/B2-CURRICULUM-PLAN.md` - B2 curriculum overview

---

## Issue Tracking

**GitHub Issue:** TBD (coordinator will create)
**Priority:** P1 - Quality enhancement (unblocked by #352)
**Agent:** C1-c (Claude)
**Estimated time:** 1-2 hours for all 8 modules

---

**Ready to begin?** Start with M116 and work systematically through all 8 modules.
