# Phase A: Meta + Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module_v3).**
> **This is a combined Phase 0 + Phase 1. Your ONLY task: Lightweight research AND meta outline in one pass.**

---

## Your Input

Read the plan file (SOURCE OF TRUTH):

```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/b1/aspect-integration-practice.yaml
```

Read the meta file (for reference — you will replace the content_outline):

```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/meta/aspect-integration-practice.yaml
```

Read the level quick-ref for constraints:

```
/Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/quick-ref/B1.md
```

Read the State Standard compliance mapping (small file — read this FIRST):

```
docs/l2-uk-en/state-standard-2024-mapping.yaml
```

The full State Standard 2024 is at `docs/l2-uk-en/UKRAINIAN-STATE-STANDARD-2024.txt` (431KB, ~6000 lines). **Do NOT read the entire file.** Instead:
1. Check the mapping file for the relevant `B1` section — find the grammar topic that matches your module
2. Use the `lines: [start, end]` coordinates to read ONLY that section from the full Standard
3. If no mapping entry exists for this topic, search by §number or keyword as fallback
4. If still no match, say so honestly — do NOT fabricate a §reference

---

## PART 1: Lightweight Research

Research **Інтеграція виду: практика** for the **B1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

### Research Requirements

1. **State Standard Reference**: Look up the §section in `state-standard-2024-mapping.yaml`, then read ONLY that section from `UKRAINIAN-STATE-STANDARD-2024.txt`. Quote the relevant requirement.
2. **Vocabulary Frequency**: For key vocabulary items in the plan, note frequency data and collocations. Use web search if available — do NOT rely on memory alone.
3. **Cultural Hook**: Find 1-2 verified cultural facts to anchor the lesson.
4. **Cross-References**: Note which modules this builds on and prepares for (check the plan's `connects_to` field).
5. **Common Errors**: Identify 2-3 common learner mistakes for this grammar point/topic.

### Decolonized Framing

When researching, frame Ukrainian independently — **never as a derivative or variant of Russian:**
- Describe Ukrainian features positively ("Ukrainian has...", "Ukrainian uses...")
- Do NOT use Russian as the baseline for comparisons ("Unlike Russian...", "Different from Russian...")
- If comparing language systems is useful, use non-Russian languages (Polish, Portuguese, etc.)
- Note how topics have been historically misframed by Russian/Soviet sources and provide the Ukrainian-centric perspective

### Research Output Cap
Keep research notes under **1500 words**. Focus on density: facts, dates, quotes, tables — not prose.

### Additional for Core B (B1.6+, B2, C1, C2, PRO)

- Domain-specific vocabulary collocations from professional glossaries (PRO tracks)
- Stylistic/dialectal features from academic sources (C2)
- Register distinctions (formal vs. informal usage)

## Downstream Audit Gates (Phase B content will be checked for)

Plan your outline knowing that Phase B content must pass these gates:
- **Word count**: minimum **4000** words — allocate outline sections accordingly
- **Colonial framing**: plan decolonized framing NOW so Phase B doesn't default to Russian comparisons
- **Russianisms**: ensure vocabulary_hints and examples avoid banned words (кушати→їсти, получати→отримувати)
- **IPA vowels**: Ukrainian о = [ɔ] always, е = [ɛ] always, ч = [t͡ʃ] with tie-bar
- **Duplicate headers**: ensure outline section names don't share keywords

---

## PART 2: Meta Outline

After completing research, rebuild the `content_outline` using:
- The plan's section structure as skeleton
- Research findings to inform depth and word allocation

### Rules for Meta Outline

- **Do NOT copy the old meta's outline** — rebuild from the plan's section structure
- Allocations must sum to approximately **4000** words (±10% acceptable)
- Minimum section allocation: 200 words (merge smaller sections)
- Each section must have `section`, `words`, and `points` fields
- Section names must be in Ukrainian (these become H2 headings in the lesson)
- **Section names must match plan exactly** — use exact names from plan's `content_outline` (or very close Ukrainian equivalents)
- Points are specific and actionable — not vague ("cover grammar" → bad; "Each case form gets its own H3 with definition, 2+ examples, usage note" → good)
- **Bridge modules (immersion < 90%):** Note the plan's `immersion` field. The intro section should explicitly list English scaffolding requirements.

---

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded by the extraction pipeline.

### Output Block 1: Research Notes

```
===RESEARCH_START===

# Дослідження: Інтеграція виду: практика

## State Standard Reference
§{section_number}: "{quoted requirement}"
Alignment: {how this module addresses the standard}

## Vocabulary Frequency
| Word | Frequency / Source | Key collocations |
|------|-------------------|------------------|
| ...  | ...               | ...              |

## Cultural Hooks
1. {Verified fact with source}
2. {Verified fact with source}

## Common Learner Errors
1. {Error pattern} → {Correct form} — {Why it happens}
2. ...

## Cross-References
- Builds on: {module slugs}
- Prepares for: {module slugs}

## Notes for Content Writing
- {Any additional observations for Phase B}

===RESEARCH_END===
```

### Output Block 2: Meta Outline

```
===META_OUTLINE_START===
content_outline:
  - section: "{Section 1 name in Ukrainian}"
    words: {allocation}
    points:
      - "{key point 1}"
      - "{key point 2}"
  - section: "{Section 2 name}"
    words: {allocation}
    points:
      - "..."
  # ... all sections
  # Total: ~4000 words
===META_OUTLINE_END===
```

### Validation checklist (complete before outputting meta):

- [ ] All section names are Ukrainian
- [ ] Section names match plan structure
- [ ] Each section has `words` and `points`
- [ ] Sum of all `words` ≈ 4000
- [ ] No section has fewer than 200 words
- [ ] Points are actionable and specific

---

## Friction Report (MANDATORY)

After both output blocks, include:

```
===FRICTION_START===
**Phase**: Phase A: Meta + Research (Core)
**Step**: {what you were doing when friction occurred, or "Full Phase A"}
**Friction Type**: NONE | TOKEN_LIMIT_TRUNCATION | TOOL_REDUNDANCY | STATE_STANDARD_NOT_FOUND | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if a script/design issue, or "N/A"}
===FRICTION_END===
```

---

## Boundaries

- Do NOT write lesson content — only research notes and meta outline
- Do NOT generate activities or vocabulary
- Do NOT fabricate State Standard references — if you can't find the exact §, say so
- Do NOT reference persona names or voice instructions — persona is assigned at content generation time
- Do NOT request skills, delegate to Claude, or skip this phase
