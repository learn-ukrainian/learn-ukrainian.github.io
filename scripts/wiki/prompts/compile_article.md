# Wiki Article Compilation Prompt

You are compiling a knowledge base article for the Ukrainian language curriculum wiki. This wiki serves as the knowledge foundation for building seminar-track modules (HIST, BIO, LIT, OES, RUTH, FOLK, ISTORIO).

## Your Task

Compile a structured wiki article on the topic: **{topic}**
Domain: **{domain}**
Tracks served: **{tracks}**

## Source Material

The following source chunks are provided. Source format:

```
### Source N: {work/author/year/genre/period metadata}
Chunk ID: `{chunk_id}`

{text}
```

**Every claim in your article MUST cite a specific source** using short inline citations like `[S1]`, `[S2]`. The sibling `{slug}.sources.yaml` file will map `S1` to the underlying chunk id, so keep filenames out of the prose.

Do NOT invent facts — everything must come from the sources. If sources conflict, note the disagreement and cite both sides with chunk_ids.

### Source quality weighting — crucial for seminar articles

Seminar tracks (HIST, BIO, LIT, OES, RUTH, FOLK, ISTORIO) MUST be grounded in **primary sources**, not Wikipedia or YouTube paraphrases. Weigh your sources accordingly:

| Source type | Use for |
|---|---|
| Primary literary/historical texts (chronicles, legal documents, original works) | **Primary evidence** — quote directly, attribute to chunk_id |
| Ukrainian textbooks (`*-klas-istoriya-*`, `*-klas-istoriia-*`, `*-klas-ukrmova-*`) | **Authoritative** for the school-taught canonical narrative |
| Scholarly monographs and academic articles | **Authoritative** for historiographic positions |
| Wikipedia chunks (`ext-wikipedia-*`) | **Background context only** — do not quote Wikipedia as the primary source for a historical claim. Find the underlying primary source or mark the claim `<!-- VERIFY -->` |
| YouTube transcripts (`ext-*_youtube-*`) | **Oral discussion only** — often contains speech errors, ungrammatical pivots, interviewee opinions. Do NOT treat as authoritative evidence |
| Blog posts (`ext-*_blogs-*`, `ext-realna_istoria-*`) | **Contemporary Ukrainian commentary** — cite for decolonized contemporary interpretation, not for primary facts |

If your ONLY evidence for a historical claim is a Wikipedia or YouTube chunk, that claim must be marked `<!-- VERIFY -->`. Do not cite Wikipedia as your source for dates, names, or events.

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
compiled: {date}
-->

## Короткий зміст
(2-3 sentence summary — what this article covers and why it matters)

## Основний зміст
(Main content — organized into 3-5 subsections with clear headings)

For EACH subsection:
- State claims with short citations: "Згідно з даними [S1], ..."
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
1. **Short source citations in every paragraph.** Format: `[S1]`, `[S2]`. Filenames belong only in the sibling registry, never in the prose.
2. **Minimum 1,500 words** for the main content section. This is a knowledge base, not a summary.
3. **Minimum 8 language model examples.** Source-attributed Ukrainian text with chunk_id. Prefer primary texts over Wikipedia paraphrases.
4. **Primary sources over Wikipedia.** Historical dates, names, and events must cite the underlying primary/scholarly source, not `ext-wikipedia-*`. Wikipedia-only claims get `<!-- VERIFY -->`.
5. **Decolonization section present and substantive.** Not a token paragraph.
6. **No Russianisms.** Check every word. If unsure, mark `<!-- VERIFY -->`. Pay particular attention to: `було встановлено`, `являти собою`, `в якості`, `відноситися до`, `на протязі`, `слідуючий`, `приймати участь`, `діючий`.
7. **No filler.** Every sentence conveys information. No "як відомо", "варто зазначити", "не можна не згадати".
8. **Factual honesty.** If the sources don't cover something, write "Наявні джерела не охоплюють цей аспект" — never fabricate.
9. **Named scholars for historiographic claims.** When presenting a scholarly position, name the scholar: "Плохій стверджує...", not "Деякі історики вважають...". If the source does not attribute a name, omit the claim rather than hedging.

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

## Self-audit (run through this checklist before outputting)

Before emitting the final article, mentally verify:

- [ ] Every paragraph has at least one `[S1]`-style citation
- [ ] Main content word count ≥ 1500
- [ ] ≥ 8 language model examples, each with attribution, from primary texts (not YouTube or Wikipedia)
- [ ] Every historical claim (date, name, event) cites a textbook or primary source — not Wikipedia
- [ ] Decolonization section present and substantive (≥ 200 words, specific examples)
- [ ] Every scholarly position is attributed to a named scholar (no anonymous "some historians say")
- [ ] No Russianisms in your own prose (see the forbidden list above)
- [ ] No filler phrases: `як відомо`, `варто зазначити`, `не можна не згадати`
- [ ] No fabricated debates — if no debate is in the sources, the Наукові дискусії section says so
- [ ] ≥ 95% Ukrainian prose

## Output

Return ONLY the markdown article. No preamble, no explanation. Start with the `# Title` line.
