# Task: Fix B1 Word Count Issues

**Issue:** 15 B1 modules fall slightly short of 1500-word minimum (1-66 words short)

**Your task:** Expand content in each module to meet word count requirement while maintaining quality.

---

## Modules to Fix

| Module | File Pattern | Current | Target | Needs |
|--------|--------------|---------|--------|-------|
| M44 | `curriculum/l2-uk-en/b1/44-*.md` | 1474 | 1500 | +26 words |
| M45 | `curriculum/l2-uk-en/b1/45-*.md` | 1473 | 1500 | +27 words |
| M47 | `curriculum/l2-uk-en/b1/47-*.md` | 1499 | 1500 | +1 word |
| M49 | `curriculum/l2-uk-en/b1/49-*.md` | 1434 | 1500 | +66 words |
| M52 | `curriculum/l2-uk-en/b1/52-*.md` | 1462 | 1500 | +38 words |
| M53 | `curriculum/l2-uk-en/b1/53-*.md` | 1453 | 1500 | +47 words |
| M55 | `curriculum/l2-uk-en/b1/55-*.md` | 1453 | 1500 | +47 words |
| M57 | `curriculum/l2-uk-en/b1/57-*.md` | 1454 | 1500 | +46 words |
| M60 | `curriculum/l2-uk-en/b1/60-*.md` | 1472 | 1500 | +28 words |
| M61 | `curriculum/l2-uk-en/b1/61-*.md` | 1450 | 1500 | +50 words |
| M66 | `curriculum/l2-uk-en/b1/66-*.md` | 1454 | 1500 | +46 words |
| M68 | `curriculum/l2-uk-en/b1/68-*.md` | 1445 | 1500 | +55 words |
| M69 | `curriculum/l2-uk-en/b1/69-*.md` | 1490 | 1500 | +10 words |
| M70 | `curriculum/l2-uk-en/b1/70-*.md` | 1452 | 1500 | +48 words |
| M79 | `curriculum/l2-uk-en/b1/79-*.md` | 1447 | 1500 | +53 words |

**Total:** 15 modules, 613 words to add

---

## Process for Each Module

### 1. Find Module File
```bash
# Example for M44
fd "^44-" curriculum/l2-uk-en/b1/
# Returns: curriculum/l2-uk-en/b1/44-active-participles-phrases.md
```

### 2. Read Module
Use Read tool to understand:
- Module topic and focus
- Existing content structure
- Where natural expansion points exist

### 3. Identify Expansion Points

**Good expansion areas:**
- Add more examples to grammar explanations
- Expand cultural context in engagement boxes (💡 Did You Know, 🌍 Real World)
- Add more detail to narrative sections
- Enrich existing explanations with additional nuance
- Add transitional sentences between sections

**DO NOT expand:**
- Vocabulary tables (fixed format)
- Activity instructions (must stay concise)
- Grammar rules (must stay precise)

### 4. Expand Content Naturally

**Example (M44 needs +26 words):**
```markdown
# BEFORE (too brief):
Active participles describe ongoing actions. They end in -учий/-ючий.

# AFTER (natural expansion):
Active participles describe ongoing actions performed by the subject of the sentence.
In Ukrainian, they are formed by adding the suffix -учий/-ючий to the verb stem,
creating adjective-like forms that can modify nouns while retaining verbal characteristics.
```

**B1 Immersion Requirement:**
- Body text must be 97%+ Ukrainian (only grammar terms in English if needed)
- Engagement boxes can have English explanations
- Add Ukrainian examples, not English filler

### 5. Verify Module Passes Audit

After editing each module:
```bash
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b1/44-*.md
```

**Check:**
- ✅ Word count ≥1500
- ✅ Immersion ≥97%
- ✅ All other gates pass (activities, pedagogy, richness)

### 6. Run Pipeline

After audit passes:
```bash
npm run pipeline l2-uk-en b1 44
```

**Pipeline validates:**
- Lint → Generate MDX → Validate MDX → Validate HTML

---

## Rules & Constraints

### ✅ DO
- Add natural narrative expansion
- Enrich examples and explanations
- Add cultural context and real-world connections
- Expand engagement boxes
- Maintain 100% Ukrainian in body text

### ❌ DO NOT
- Change vocabulary (must match curriculum plan)
- Modify grammar explanations (must stay accurate)
- Change activities (separate YAML files)
- Add English padding (immersion violation)
- Change module structure or pedagogy

---

## Workflow (Systematic Approach)

**Process modules in order: M44 → M45 → M47 → ... → M79**

For each module:
1. ✅ Find file
2. ✅ Read content
3. ✅ Edit (add needed words)
4. ✅ Audit (verify passes)
5. ✅ Pipeline (validate output)
6. ✅ Mark complete

**Track progress** - report after each batch of 5 modules.

---

## Quality Standards

**B1 Module Requirements:**
- Word count: 1500-2500 words
- Immersion: 97%+ (Ukrainian body text)
- Vocabulary: 20-35 items
- Activities: 12-14 total
- Richness: 95%+ (examples, engagement boxes, cultural depth)

**Your changes must maintain all quality standards while adding the missing words.**

---

## Deliverable

When complete, report:

1. **Summary table:**
   | Module | Words Added | Final Count | Audit | Pipeline |
   |--------|-------------|-------------|-------|----------|
   | M44 | +26 | 1500 | ✅ | ✅ |
   | ... | ... | ... | ... | ... |

2. **Expansion strategy summary:**
   - Where content was added (examples, narrative, engagement boxes)
   - Any patterns or challenges encountered

3. **Verification:**
   - All 15 modules audit passing
   - All 15 modules pipeline passing

---

## Context Files

**Read these first:**
- `/Users/krisztiankoos/projects/learn-ukrainian/CLAUDE.md` - Project instructions
- `/Users/krisztiankoos/projects/learn-ukrainian/docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md` - Quality standards

**Reference:**
- `claude_extensions/quick-ref/b1.md` - B1-specific requirements
- `docs/l2-uk-en/B1-CURRICULUM-PLAN.md` - B1 curriculum overview

---

## Issue Tracking

**GitHub Issue:** TBD (coordinator will create)
**Priority:** P1 - Quality enhancement (unblocked by #352)
**Agent:** Gemini 3-flash
**Estimated time:** 2-3 hours for all 15 modules

---

**Ready to begin?** Start with M44 and work systematically through all 15 modules.
