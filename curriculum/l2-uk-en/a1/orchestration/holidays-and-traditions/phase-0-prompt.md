# Phase 0: Lightweight Research (Core Track)

> **You are Gemini, executing Phase 0 of an orchestrated rebuild.**
> **Your ONLY task: Lightweight research for a core-track module.**

## Your Input

Read the plan file:

```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/holidays-and-traditions.yaml
```

Read the meta file:

```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/meta/holidays-and-traditions.yaml
```

Read the level quick-ref for constraints:

```
/Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/quick-ref/A1.md
```

Read the State Standard compliance mapping (small file — read this FIRST):

```
docs/l2-uk-en/state-standard-2024-mapping.yaml
```

The full State Standard 2024 is at `docs/l2-uk-en/UKRAINIAN-STATE-STANDARD-2024.txt` (431KB, ~6000 lines). **Do NOT read the entire file.** Instead:
1. Check the mapping file for the relevant `A1` section — find the grammar topic that matches your module
2. Use the `lines: [start, end]` coordinates to read ONLY that section from the full Standard (e.g., `read_file` with offset=start, limit=end-start+10)
3. If the mapping has no entry for this specific topic, search the Standard by §number or topic keyword as fallback
4. If you still can't find a relevant section, say so honestly — do NOT fabricate a §reference

## Your Task

Research **Holidays & Traditions** for the **A1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

You have web search available — use it for vocabulary frequency, cultural facts, and teaching resources. Do NOT rely only on training data when you can verify with real sources.

### Research Requirements

1. **State Standard Reference**: Look up the §section in the mapping file (`state-standard-2024-mapping.yaml`), then read ONLY that section from the full State Standard (`UKRAINIAN-STATE-STANDARD-2024.txt`). Quote the relevant requirement.
2. **Vocabulary Frequency**: For key vocabulary items in the plan, search for frequency data and collocations. Use web search or corpus tools if available. Note high-frequency collocations.
3. **Cultural Hook**: Find 1-2 verified cultural facts to anchor the lesson. Use web search to verify — do NOT rely on memory alone for dates, quotes, or historical claims.
4. **Cross-References**: Note which modules this builds on and prepares for (check the plan's `connects_to` field).
5. **Common Errors**: Identify 2-3 common learner mistakes for this grammar point/topic (from teaching resources, not guesses).

### Additional for Core B (B1.6+, B2, C1, C2, PRO)

- Domain-specific vocabulary collocations from professional glossaries (PRO tracks)
- Stylistic/dialectal features from academic sources (C2)
- Register distinctions (formal vs. informal usage)

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded by the extraction pipeline.

Return your research as structured markdown:

```
===RESEARCH_START===

# Дослідження: Holidays & Traditions

## State Standard Reference
§{section_number}: "{quoted requirement from UKRAINIAN-STATE-STANDARD-2024.txt}"
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
- {Any additional observations for the content phase}

===RESEARCH_END===
```

## Friction Report (MANDATORY)

After your research output, include:

```
===FRICTION_START===
**Phase**: Phase 0: Research (Core)
**Step**: {what you were doing when friction occurred, or "Full research"}
**Friction Type**: NONE | TOKEN_LIMIT_TRUNCATION | TOOL_REDUNDANCY | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if a script/design issue, or "N/A"}
===FRICTION_END===
```

## Boundaries

- Do NOT write lesson content — only research notes
- Do NOT generate activities or vocabulary
- Do NOT fabricate State Standard references — if you can't find the exact §, say so
- Do NOT request skills, delegate to Claude, or skip this phase
