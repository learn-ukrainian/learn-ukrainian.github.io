# Phase 0: Lightweight Research (Core Track)

> **You are Gemini, executing Phase 0 of an orchestrated rebuild.**
> **Your ONLY task: Lightweight research for a core-track module.**

## Your Input

Read the plan file:

```
{PLAN_PATH}
```

Read the meta file:

```
{META_PATH}
```

Read the level quick-ref for constraints:

```
{QUICK_REF_PATH}
```

## Your Task

Research **{TOPIC_TITLE}** for the **{LEVEL}** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

### Research Requirements

1. **State Standard Reference**: Find the §section in the Ukrainian State Standard 2024 that covers this grammar point or topic area. Quote the relevant requirement.
2. **Vocabulary Frequency**: For key vocabulary items in the plan, verify frequency on lcorp.ulif.org.ua or similar corpus. Note high-frequency collocations.
3. **Cultural Hook**: Find 1-2 verified cultural facts (NOT from memory) to anchor the lesson. These should be authentic, not generic.
4. **Cross-References**: Note which modules this builds on and prepares for (check the plan's `connects_to` field).
5. **Common Errors**: Identify 2-3 common learner mistakes for this grammar point/topic (from teaching resources, not guesses).

### Additional for Core B (B1.6+, B2, C1, C2, PRO)

- Domain-specific vocabulary collocations from professional glossaries (PRO tracks)
- Stylistic/dialectal features from academic sources (C2)
- Register distinctions (formal vs. informal usage)

## Output Format

Return your research as structured markdown:

```
===RESEARCH_START===

# Дослідження: {TOPIC_TITLE}

## State Standard Reference
§{section_number}: "{quoted requirement}"
Alignment: {how this module addresses the standard}

## Vocabulary Frequency
| Word | Frequency rank | Key collocations |
|------|---------------|------------------|
| ...  | ...           | ...              |

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

## Boundaries

- Do NOT write lesson content — only research notes
- Do NOT generate activities or vocabulary
- Do NOT fabricate State Standard references — if you can't find the exact §, say so
- Do NOT request skills, delegate to Claude, or skip this phase
