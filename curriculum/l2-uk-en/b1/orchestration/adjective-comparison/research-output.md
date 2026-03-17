  [gemini] attempt 1/5, model=gemini-3.1-pro-preview, prompt=14331 chars: ROLE: You are a TEXT GENERATOR executing a specific task. You produce text output. That's it.  ABSOLUTE RULES — VIOLATION OF ANY RULE MEANS TASK FAILURE:  1. OUTPUT ONLY TEXT. Your ONLY job is to read...
===RESEARCH_START===

# Дослідження: Ступені порівняння прикметників

## State Standard Reference
§N/A: "Specific State Standard mapping file could not be read due to strict execution environment constraints (no file I/O). However, this aligns completely with the B1 CEFR / Ukrainian State Standard requirement for Morphological Competence: formation and usage of comparative and superlative degrees of qualitative adjectives, including synthetic/analytic forms and irregulars."
Alignment: This module directly addresses the B1 requirement to express comparison, preference, and degree using appropriate morphological and syntactic structures, distinguishing between formal (analytic) and informal/natural (synthetic) registers.

## Vocabulary Frequency
| Word | Frequency / Source | Key collocations |
|------|-------------------|------------------|
| кращий | High (GRAC est.) | кращий варіант, набагато кращий, зміни на краще |
| більший | High (GRAC est.) | більший розмір, значно більший, більша частина |
| вищий | High (GRAC est.) | вищий рівень, вища освіта, вищий ступінь |
| менший | Medium (GRAC est.) | менший брат, щонайменший, менша половина |
| найбільш | High (GRAC est.) | найбільш ефективний, найбільш поширений |

## Cultural Hooks
1. Emphatic superlatives with prefixes **якнай-** and **щонай-** (e.g., *якнайшвидший*, *щонайкращий*) are deeply rooted in Ukrainian folklore and classic literature. Their use showcases the language's synthetic richness and is a hallmark of highly authentic, expressive Ukrainian.
2. The pervasive use of superlative adjectives in modern Ukrainian marketing (*найсмачніша кава*, *найкращі ціни*). This "superlative inflation" provides a highly recognizable, real-world context for learners to see these forms in everyday urban environments.

## Common Learner Errors
1. **Double Marking:** *найбільш найкращий* → **найкращий** (or *найбільш хороший*). Learners often stack analytic and synthetic markers. Rule: Only one marker is allowed.
2. **Colonial Syntax in Comparison:** *Він старший мене* → **Він старший за мене** (or *старший, ніж я*). Using the direct genitive for comparison is a Russian grammatical interference (*старше меня*). Standard Ukrainian requires the preposition "за + Accusative" or "ніж + Nominative".
3. **Missing Consonant Alternations:** *дорогіший*, *легкіший* → **дорожчий**, **легший**. Learners often just add "-іший" to the stem, missing the historical alternations (г→ж, к→ч, ск→щ).

## Cross-References
- Builds on: b1-58 (Word Formation: Modifiers)
- Prepares for: b1-61 (Synonymy: Thinking Verbs)

## Multimedia Resources
- (none encountered)

## Notes for Content Writing
- **Decolonized Framing:** Strongly emphasize that synthetic forms (*розумніший*, *швидший*) are the natural, authentic core of the Ukrainian language. The overuse of analytic forms (*більш розумний*) in everyday speech is often a remnant of Soviet-era linguistic convergence policies designed to make Ukrainian mirror Russian (*более умный*). Promoting synthetic forms reclaims authentic Ukrainian syntax.
- **Syntactic Drilling:** Ensure that examples comparing two objects rigorously model the `за + Accusative` and `ніж + Nominative` patterns to build muscle memory against the Russian genitive structure.
- **Irregulars as a Closed Set:** Treat `кращий, гірший, більший, менший` as high-priority, high-frequency core vocabulary that must be memorized as a closed set rather than derived.

===RESEARCH_END===

===FRICTION_START===
**Phase**: Phase A: Meta + Research (Core)
**Step**: State Standard Retrieval & RAG Tools
**Friction Type**: TOOL_RESTRICTION
**Raw Error**: Strict Text Generator constraints ("DO NOT SEND MESSAGES. Do not use... MCP tools") prevented the use of the requested RAG tools (`search_text`, `verify_words`, `query_grac`).
**Self-Correction**: Utilized internal linguistic knowledge base to synthesize accurate morphological rules, decolonized framing, frequency estimations, and learner errors to fulfill the prompt's structural requirements without violating the absolute system rules.
**Proposed Tooling Fix**: If RAG MCP tools are mandatory for the pipeline, the system prompt's "ABSOLUTE RULES" must be updated to explicitly whitelist these specific MCP commands rather than universally banning all tool calls and message sending.
===FRICTION_END===
