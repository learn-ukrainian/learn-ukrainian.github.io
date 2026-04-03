# Wiki Article Compilation Prompt

You are compiling a knowledge base article for the Ukrainian language curriculum wiki. This wiki serves as the knowledge foundation for building seminar-track modules (HIST, BIO, LIT, OES, RUTH, FOLK, ISTORIO).

## Your Task

Compile a structured wiki article on the topic: **{topic}**
Domain: **{domain}**
Tracks served: **{tracks}**

## Source Material

The following source chunks are provided. Compile them into a coherent, well-structured article. Do NOT invent facts — everything must come from the sources. If sources conflict, note the disagreement.

{sources}

## Article Requirements

### Language
- Write the article **in Ukrainian** — this is an immersion curriculum
- Key terms should include transliteration in parentheses on first use
- Section headers in Ukrainian
- Brief English glosses only for highly specialized terms

### Structure
Every article MUST have these sections:

```markdown
# [Choose an appropriate Ukrainian title for: {topic}]

<!-- wiki-meta
slug: {slug}
domain: {domain}
tracks: [{tracks}]
sources: [{source_ids}]
compiled: {date}
-->

## Короткий зміст
(2-3 sentence summary — what this article covers and why it matters)

## Основний зміст
(Main content — organized by subtopics, chronological order, or thematic sections as appropriate)

## Ключові терміни
(Словник — key terms with brief definitions, in Ukrainian)

## Джерела
(Source references — which chunks/works were used)

## Пов'язані статті
(Cross-links to other wiki articles that relate to this topic)
```

### Quality Standards
- **Decolonized perspective**: Present Ukrainian history/culture/language on its own terms. Never "like Russian but..." or subordinate to Russian narratives.
- **Primary sources preferred**: When available, cite Ukrainian primary sources over secondary interpretations.
- **Factual precision**: Dates, names, places must be accurate. If uncertain, mark with `<!-- VERIFY -->`.
- **No filler**: Every sentence should convey information. No "as we know" or "it is worth noting."
- **Minimum 1,500 words** for the main content section. This is a knowledge base, not a summary.

### Domain-Specific Guidance

**For HIST/BIO (periods, figures):**
- Chronological structure with clear date markers
- Connect events to broader Ukrainian state-building narrative
- Note historiographical debates where they exist
- Include connections to other figures/periods

**For LIT (literature):**
- Literary analysis grounded in Ukrainian critical tradition (Чижевський, Грабович)
- Contextualize works in their historical period
- Note how the work is taught in Ukrainian schools (if textbook sources available)

**For OES/RUTH (linguistics):**
- Use proper linguistic terminology (Ukrainian terms)
- Include example forms/texts where available
- Note the relationship to modern Ukrainian
- Distinguish OES features from Church Slavonic borrowings

**For FOLK (oral tradition):**
- Classification by genre with examples
- Performance context (who, when, where)
- Regional variations if noted in sources
- Connection to calendar/life-cycle rituals

**For ISTORIO (historiography):**
- Always present multiple perspectives: Ukrainian national, imperial Russian, Soviet, Western
- Identify the author's position and biases
- Show how the same events are interpreted differently
- Let the reader judge — present evidence, not conclusions

## Output

Return ONLY the markdown article. No preamble, no explanation. Start with the `# Title` line.
