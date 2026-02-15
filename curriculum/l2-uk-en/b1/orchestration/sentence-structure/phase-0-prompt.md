# Phase 0: Lightweight Research (Core Track)

> **You are Gemini, executing Phase 0 of an orchestrated rebuild.**
> **Your ONLY task: Lightweight research for a core-track module.**

## Your Input

Read the plan file:

```
curriculum/l2-uk-en/plans/b1/sentence-structure.yaml
```

Read the level quick-ref for constraints:

```
claude_extensions/quick-ref/B1.md
```

Read the State Standard compliance mapping (small file — read this FIRST):

```
docs/l2-uk-en/state-standard-2024-mapping.yaml
```

The full State Standard 2024 is at `docs/l2-uk-en/UKRAINIAN-STATE-STANDARD-2024.txt` (431KB, ~6000 lines). **Do NOT read the entire file.** Instead:
1. Check the mapping file for the relevant B1 section — find the syntax topic that matches this module
2. Use the `lines: [start, end]` coordinates to read ONLY that section from the full Standard (e.g., `read_file` with offset=start, limit=end-start+10)
3. The B1 syntax sections are at §4.4 lines 2344-2431 (declarative, interrogative, complex simple, complex sentence)
4. If you still can't find a relevant section, say so honestly — do NOT fabricate a §reference

## Your Task

Research **Структура речення (Sentence analysis terminology)** for the **B1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

This is B1 Module 04, a **bridge module** (metalanguage phase B1.0, 85% Ukrainian immersion). Students are learning Ukrainian grammar terminology — how Ukrainians talk about sentence structure in school. Key concepts: підмет, присудок, додаток, означення, обставина, головне речення, підрядне речення, просте/складне речення.

You have web search available — use it for vocabulary frequency, cultural facts, and teaching resources. Do NOT rely only on training data when you can verify with real sources.

### Research Requirements

1. **State Standard Reference**: Look up §4.4 in the mapping file (B1 syntax), then read ONLY lines 2344-2431 from the full State Standard (`UKRAINIAN-STATE-STANDARD-2024.txt`). Quote the relevant requirement for sentence structure terminology.
2. **Vocabulary Frequency**: For key vocabulary items (підмет, присудок, додаток, означення, обставина, сполучник, кома, крапка, просте речення, складне речення), search for frequency data and collocations. Note which terms are most common in school textbooks.
3. **Cultural Hook**: Find 1-2 verified cultural facts to anchor the lesson — e.g., how Ukrainian schoolchildren learn to diagram sentences (розбір речення), famous quotes about Ukrainian language/syntax.
4. **Cross-References**: This builds on b1-01 (basic grammar terminology), b1-02 (verb terminology), b1-03 (reading grammar rules). It prepares for b1-05 (metalanguage checkpoint), b1-26 (relative clauses), b1-35 (concessive clauses).
5. **Common Errors**: Identify 2-3 common learner mistakes when analyzing Ukrainian sentences — e.g., confusing додаток and означення, misidentifying sentence types, word order assumptions from English.

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded by the extraction pipeline.

Return your research as structured markdown:

```
===RESEARCH_START===

# Дослідження: Структура речення

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
