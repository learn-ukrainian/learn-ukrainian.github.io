# Phase 0: Deep Research (Seminar Track)

> **You are Gemini, executing Phase 0 of an orchestrated rebuild.**
> **Your ONLY task: Research the topic and produce structured notes.**

## Your Input

Read the plan file to understand what this module covers:

```
{PLAN_PATH}
```

Read the current meta file for content_outline structure:

```
{META_PATH}
```

## Your Task

Research **{TOPIC_TITLE}** for the **{TRACK}** track. Produce structured research notes that will drive content writing in later phases.

### Research Requirements

1. **Sources**: Find 3+ Ukrainian-language academic sources (esu.com.ua, history.org.ua, uk.wikipedia.org, litopys.org.ua). Russian-language sources are PROHIBITED.
2. **Timeline**: Build a chronological timeline with 5+ dated events/milestones.
3. **Primary Quotes**: Find 2+ quotable primary source excerpts (original Ukrainian text preferred).
4. **Engagement Hooks**: Identify 6+ engagement hooks mapped to specific content sections:
   - `[!myth-buster]` — Decolonization: correct imperial/Soviet myths
   - `[!history-bite]` — Surprising or lesser-known facts
   - `[!context]` — Broader historical/cultural context
   - `[!quote]` — Primary source citations
   - `[!decolonization]` — Ukraine-centric reframing
   - `[!culture]` — Cultural significance
5. **Decolonization Angle**: Identify how this topic has been distorted by imperial/Soviet historiography and what the Ukrainian-centric framing should be.
6. **Section-Mapped Content**: Structure notes with headings that match the `content_outline` sections from the meta file. This makes content writing mechanical.

### Contested Terms (if applicable)

If this topic involves contested narratives (Ukrainian vs. Russian/Soviet/Polish historiography), create a Contested Terms Table:

```markdown
## Contested Terms

| Concept | Enemy/Imperial framing | Ukrainian (decolonized) framing |
|---------|----------------------|-------------------------------|
| ...     | ...                  | ...                           |
```

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded by the extraction pipeline.

Return your research as structured markdown. Use these exact section headers:

```
===RESEARCH_START===

# Дослідження: {TOPIC_TITLE}

## Використані джерела
1. [Source name](URL) — brief description
2. ...
3. ...

## Хронологія
- {date}: {event}
- ...

## Ключові факти та цитати
- ...

## Engagement Hooks (mapped to sections)
- Section "{section_name}": [!hook_type] — description
- ...

## Деколонізаційний контекст
- Imperial/Soviet myth: ...
- Ukrainian reality: ...

## Contested Terms (if applicable)
| Concept | Imperial framing | Ukrainian framing |
|---------|-----------------|-------------------|
| ...     | ...             | ...               |

## Section-Mapped Research Notes

### {Section 1 from content_outline}
Key facts, dates, sources for this section...

### {Section 2 from content_outline}
...

===RESEARCH_END===
```

## Boundaries

- Do NOT write lesson content — only research notes
- Do NOT generate activities or vocabulary
- Do NOT skip any section from the content_outline
- Do NOT use Russian-language sources
- Do NOT fabricate quotes or dates — if unsure, mark as "[needs verification]"
- Do NOT request skills, delegate to Claude, or skip this phase
