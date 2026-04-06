# Wiki Article Compilation Prompt

You are compiling a knowledge base article for the Ukrainian language curriculum wiki. This wiki serves as the knowledge foundation for building seminar-track modules (HIST, BIO, LIT, OES, RUTH, FOLK, ISTORIO).

## Your Task

Compile a structured wiki article on the topic: **{topic}**
Domain: **{domain}**
Tracks served: **{tracks}**

## Source Material

The following source chunks are provided. **Every claim in your article MUST cite a specific source** using the format `(Source N)` or `(Джерело: chunk_id)`. Do NOT invent facts — everything must come from the sources. If sources conflict, note the disagreement and cite both sides.

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
(Main content — organized into 3-5 subsections with clear headings)

For EACH subsection:
- State claims with source citations: "Згідно з (Source N), ..."
- Include relevant Ukrainian quotations from primary sources
- Use tables for dates, names, and systematic comparisons
- Break prose every 200-300 words with a subheading or example block

## Ключові терміни
(10-15 key terms with brief definitions, in Ukrainian. Format as a table:)

| Термін | Визначення |
|--------|-----------|

## Мовні зразки (Language Models)
**Minimum 8 examples** of advanced Ukrainian prose relevant to the topic:
- Direct quotations from primary sources (with attribution)
- Key phrases and collocations the module writer should use
- Register-appropriate academic or literary language
This section helps the module writer match the correct Ukrainian register.

## Деколонізаційна перспектива (Decolonization Perspective)
**MANDATORY — never omit.**
- How this topic has been distorted by imperial/Soviet/Russian narratives
- What the Ukrainian sources actually say (with citations)
- Common myths and their refutations
- Frame: the Ukrainian perspective is the default, not the "alternative"

## Джерела
(Source references — which chunks/works were used. List by Source N.)

## Пов'язані статті
(Cross-links to other wiki articles that relate to this topic)
```

### Quality Standards

#### ABSOLUTE REQUIREMENTS:
1. **Source citations in every paragraph.** Not just listed at the end — woven into claims.
2. **Minimum 1,500 words** for the main content section. This is a knowledge base, not a summary.
3. **Minimum 8 language model examples.** Source-attributed Ukrainian text.
4. **Decolonization section present and substantive.** Not a token paragraph.
5. **No Russianisms.** Check every word. If unsure, mark `<!-- VERIFY -->`.
6. **No filler.** Every sentence conveys information. No "як відомо", "варто зазначити", "не можна не згадати".
7. **Factual honesty.** If the sources don't cover something, write "Наявні джерела не охоплюють цей аспект" — never fabricate.

#### STRONG PREFERENCES:
- Primary sources over secondary interpretations
- Tables for dates, names, comparisons (not prose lists)
- Break dense prose with quotation blocks and examples
- Decolonized perspective throughout, not just in the dedicated section

### Domain-Specific Guidance

**For HIST/BIO (periods, figures):**
- Chronological structure with clear date markers
- Connect events to broader Ukrainian state-building narrative
- Note historiographical debates with source citations
- Include connections to other figures/periods

**For LIT (literature):**
- Literary analysis grounded in Ukrainian critical tradition (Чижевський, Грабович)
- Contextualize works in their historical period
- Note how the work is taught in Ukrainian schools (if textbook sources available)
- Include key quotations from the literary work itself

**For OES/RUTH (linguistics):**
- Use proper linguistic terminology (Ukrainian terms with transliteration)
- Include example forms/texts with morphological analysis
- Note the relationship to modern Ukrainian
- Distinguish OES features from Church Slavonic borrowings

**For FOLK (oral tradition):**
- Classification by genre with examples
- Performance context (who, when, where)
- Regional variations if noted in sources
- Connection to calendar/life-cycle rituals
- Include full text examples of songs/riddles/proverbs

**For ISTORIO (historiography):**
- Always present multiple perspectives: Ukrainian national, imperial Russian, Soviet, Western
- Identify each author's position and biases with source citations
- Show how the same events are interpreted differently
- Let the reader judge — present evidence, not predetermined conclusions
- **But be clear:** Ukrainian primary sources take precedence over imperial interpretations

## Anti-patterns (what NOT to do)

1. ❌ "Як відомо, це важлива тема..." → ✅ Start with concrete facts
2. ❌ Unsourced claims about dates or events → ✅ "(Source N) датує цю подію..."
3. ❌ Presenting Russian imperial narratives as "balanced" → ✅ Label them: "Російська імперська інтерпретація стверджує..."
4. ❌ Prose lists of dates and names → ✅ Use chronological tables
5. ❌ Generic summaries that could describe any topic → ✅ Specific details unique to THIS topic
6. ❌ Missing quotations from primary sources → ✅ Direct quotes with attribution

## Output

Return ONLY the markdown article. No preamble, no explanation. Start with the `# Title` line.
