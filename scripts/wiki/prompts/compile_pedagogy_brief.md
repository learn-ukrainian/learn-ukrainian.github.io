# Wiki: Pedagogical Brief Compilation (A1)

You are compiling a **pedagogical brief** for the Ukrainian language curriculum wiki. This brief will guide the content writer (a separate AI) when building A1 modules for English-speaking teens and adults learning Ukrainian from zero.

## Your Task

Compile a pedagogical brief on: **{topic}**
Domain: **{domain}**
Tracks served: **{tracks}**

## Source Material

The following source chunks come from Ukrainian textbooks (Большакова, Вашуленко Grades 1-2) and pedagogy resources. Source format:

```
### Source N: {work/grade metadata}
Chunk ID: `{chunk_id}`

{text}
```

**Every claim MUST cite a specific source** using short inline citations like `[S1]`, `[S2]`. The sibling `{slug}.sources.yaml` file will map those ids to the underlying chunk ids.

If no source supports a claim, mark it `<!-- VERIFY -->`. Do NOT invent support.

### Source quality weighting

Textbook chunks (Вашуленко, Большакова, Заболотний Grade 5) are **primary** — cite freely. Wikipedia and YouTube chunks are **background only**; A1 pedagogy should be driven by the school textbook progression, not by general-purpose sources.

{sources}

## What a Pedagogical Brief IS

This is NOT a lesson. It's a **methodology guide for the writer**. It tells the writer:
- HOW Ukrainian teachers teach this concept (the native approach)
- WHAT order to introduce elements (letter sequences, vocabulary progression)
- WHAT mistakes English-speaking learners make (and how to prevent them)
- WHAT to avoid (Russian-influenced phonetics, English phonetic analogies)
- WHAT vocabulary and examples are appropriate at this stage

## Article Structure

```markdown
# {topic}

<!-- wiki-meta
slug: {slug}
domain: {domain}
tracks: [{tracks}]
compiled: {date}
-->

## Методичний підхід (Methodological Approach)
How Ukrainian Grade 1-2 teachers introduce this concept. What sequence, what exercises, what examples. **Cite specific textbooks:** "Большакова починає з голосних: А, О, У... [S2]"

## Послідовність введення (Introduction Sequence)
Exact order of elements. For letters: which letters first, which clusters. For grammar: which forms before which. For vocabulary: which words are appropriate.
- Number each step (Step 1 → Step 2 → Step 3...)
- Explain WHY this order (not arbitrary — based on frequency, phonetic simplicity, or pedagogy)

## Типові помилки L2 (Common L2 Errors)
What English speakers get wrong. For EACH error:

| ❌ Помилково | ✅ Правильно | Чому |
Phonetic interference, false cognates, structural transfer from English. How to prevent each error.
**Minimum: 5 error pairs.**

## Деколонізаційні застереження (Decolonization Notes)
**MANDATORY — never omit.** Where Russian-influenced teaching creeps in:
- Common traps: using Russian phonetic comparisons, teaching Ukrainian letters as "like Russian X but..."
- Presenting shared vocabulary as "borrowed from Russian" (when it's Common Slavic or Ukrainian-origin)
- The learner must build Ukrainian phonetic categories from scratch, not through Russian

## Словниковий мінімум (Vocabulary Boundaries)
What words/phrases are appropriate at this stage. What to avoid introducing too early.
- Organize by part of speech: іменники, дієслова, прикметники, прислівники
- Mark frequency: ★★★ = essential, ★★ = useful, ★ = can wait
- Maximum complexity level for this A1 stage

## Приклади з підручників (Textbook Examples)
**Minimum 4 specific exercises/activities** from the source textbooks:
- Show the exact exercise format (fill-in, match, listen-and-repeat, etc.)
- Include Ukrainian prompts as they appear in the textbook
- These are the gold standard — the writer should follow these patterns

## Пов'язані статті (Related Articles)
Cross-links to other wiki articles that complement this one.
```

## Quality Standards

### ABSOLUTE REQUIREMENTS:
1. **Short source citations in every section.** Format: `[S1]`, `[S2]`.
2. **Minimum 5 error pairs.** ❌ → ✅ format with explanations.
3. **Minimum 4 textbook exercise examples.** Specific, not vague. Cite the textbook + chunk_id + grade for each.
4. **Grade-level attribution.** When describing "how schools teach this," specify the exact grade and textbook author from the sources (e.g., "Вашуленко Grade 1 introduces А, О, У first [S3].").
5. **Decolonization section present and substantive.**
6. **No Russianisms.** Not even in "also acceptable" framing.
7. **Minimum 1,000 words.**

### STRONG PREFERENCES:
- Practical, not theoretical. The writer needs actionable guidance, not linguistics lectures.
- English-speaker focused. Frame advice through what an English speaker expects vs what Ukrainian actually does.
- Decolonized from day 1. Ukrainian is taught on its own terms. Never "like Russian X."
- Vocabulary must be age-appropriate for teens AND adults (no baby talk, but simple).

## Anti-patterns (what NOT to do)

1. ❌ "Teach the letters" (generic) → ✅ "Start with А, О, У (Большакова), then М, Н, Т (high-frequency consonants)"
2. ❌ English phonetic approximations ("И sounds like the i in bit") → ✅ Ukrainian phonetic description with audio guidance
3. ❌ Mixing Cyrillic script systems (Ukrainian vs Russian И/І) → ✅ Only Ukrainian alphabet
4. ❌ Vocabulary beyond A1 level → ✅ Stick to frequency-ranked A1 vocabulary
5. ❌ Theoretical phonology → ✅ Practical pronunciation guidance the writer can use

## Self-audit (run through this checklist before outputting)

- [ ] Every paragraph has at least one `[S1]`-style citation
- [ ] Total word count ≥ 1000
- [ ] ≥ 5 L2 error pairs in ❌/✅ format
- [ ] ≥ 4 specific textbook exercise examples (grade + author + chunk_id)
- [ ] Decolonization section present and substantive — not a token paragraph
- [ ] No claim supported only by Wikipedia or YouTube (those get `<!-- VERIFY -->`)
- [ ] No Russianisms in the teaching recommendations (no phonetic comparisons to Russian, no "like Russian X but…")

## Output

Return ONLY the markdown article. No preamble. Start with `# Title`.
