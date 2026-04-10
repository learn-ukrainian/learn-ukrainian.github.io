# Wiki: Grammar Brief Compilation (A2–B2)

You are compiling a **grammar brief** for the Ukrainian language curriculum wiki. This brief will guide the content writer (a separate AI) when building modules that teach Ukrainian grammar to English-speaking teens and adults.

## Your Task

Compile a grammar brief on: **{topic}**
Domain: **{domain}**
Tracks served: **{tracks}**

## Source Material

The following source chunks come from Ukrainian textbooks (Заболотний Grades 5-9, Авраменко Grades 7-11, Літвінова Grade 7, Глазова Grade 11, Карман Grade 10, МійКлас) and grammar resources. Source format:

```
### Source N: {work/grade metadata}
Chunk ID: `{chunk_id}`

{text}
```

**Every claim in your article MUST cite a specific source** using the format `(Source N: {chunk_id})` — **BOTH** the ordinal AND the chunk_id are required. `(Source 5)` alone or `(Джерело: ...)` alone is insufficient. The chunk_id makes the claim traceable back to the exact textbook passage and lets the reviewer verify it.

If no source supports a claim, mark it `<!-- VERIFY -->`. Do NOT invent support.

### Source quality weighting

Textbook chunks and МійКлас are **primary sources** — cite them freely. Wikipedia (`ext-wikipedia-*`) and YouTube transcripts (`ext-*_youtube-*`) are **background context only** — YouTube transcripts often contain speech errors and spoken-language pivots, so never quote them as examples of standard written grammar. If your only support for a claim is a Wikipedia or YouTube chunk, mark it `<!-- VERIFY -->`.

{sources}

## What a Grammar Brief IS

This is NOT a lesson. It's a **reference guide for the writer** covering:
- HOW Ukrainian schools teach this grammar point (progression, examples, exercises)
- The COMPLETE paradigm (all forms, with patterns highlighted)
- WHICH forms are most useful at this level (frequency-driven)
- Common L2 errors and how to address them
- Natural Ukrainian examples (not translated-from-English sentences)

## Article Structure

```markdown
# {topic}

<!-- wiki-meta
slug: {slug}
domain: {domain}
tracks: [{tracks}]
sources: [{source_ids}]
compiled: {date}
-->

## Як це пояснюють у школі (How Schools Teach This)
The Ukrainian textbook approach. What Grade introduces this? What sequence? What terminology do they use? **Cite specific textbooks:** "Заболотний (Source N) вводить цю тему в 6 класі через..."

## Повна парадигма (Full Paradigm)
Tables showing all forms. Highlight patterns (which endings are predictable, which are exceptions). Group by declension/conjugation class.
- Use TABLES — not prose — for paradigms
- Mark irregular forms in **bold**
- Show formation rules **as an explicit transformation chain**: `{infinitive} → {stem} → {+suffix} → {final form}`. Example: `посивіти → посиві- → +ідl- → посивілий`. Prose like "add -л-" is insufficient — show the mechanical step.
- **State ALL restrictions explicitly**, not just formation rules. Examples: "active past participles form only from INTRANSITIVE perfective verbs — `*прочиталий книгу` is impossible" (cite the source that establishes the restriction). Missing a restriction is a failure mode that has historically tanked review scores.

## Частотність і пріоритети (Frequency & Priorities)
Which forms appear most in real Ukrainian? What should the learner master first? What can wait? Cite frequency data if available.

## Типові помилки L2 (Common L2 Errors)
What English speakers get wrong with this grammar point. For EACH error:

| ❌ Помилково | ✅ Правильно | Чому |
Show structural transfer from English, false analogies, missing categories (aspect, gender agreement).
**Minimum: 5 error pairs.**

## Деколонізаційні застереження (Decolonization Notes)
**MANDATORY — never omit.** Where Ukrainian grammar differs from Russian:
- Specific Ukrainian forms that differ from Russian equivalents
- Common teaching traps: assuming shared rules, using Russian examples
- Never present Ukrainian forms as "exceptions to Russian norms" — Ukrainian is the default

## Природні приклади (Natural Examples)
**Minimum 12 natural Ukrainian sentences** using this grammar point. Requirements:
- NOT translated from English — must sound like something a Ukrainian would say
- Source-attributed where possible: "(Авраменко, Grade 9)" or "(Source N)"
- Include: daily life situations, textbook dialogues, common phrases, literary citations
- Each example demonstrates ONE specific form or usage pattern
- Group examples by pattern (2-3 examples per group, 4-5 groups)

## Рекомендації для вправ (Activity Concepts)
Specific exercise types and teaching sequences the writer should use:
- Phase 1 → Phase 2 → Phase 3 progression
- Exact drill formats (fill-in, transformation, choice, etc.)
- Which forms to drill first (frequency-based)

## Зв'язки з іншими темами (Connections)
How this grammar point connects to what came before and what comes after. Prerequisites and what this enables.

## Пов'язані статті (Related Articles)
Cross-links to other wiki articles.
```

## Quality Standards

### ABSOLUTE REQUIREMENTS:
1. **Chunk-ID citations in every section.** Format: `(Source N: chunk_id)`. Not `(Source N)` alone, not `(Джерело 5)` alone. The chunk_id is mandatory and makes the claim traceable.
2. **Complete paradigms in tables.** Don't summarize — show ALL forms.
3. **Formation as transformation chain**: `{infinitive} → {stem} → {+suffix} → {final}`, not just "add suffix X".
4. **ALL restrictions stated explicitly** (intransitive-only, perfective-only, etc.) with the source that establishes each.
5. **Minimum 12 natural examples.** Source-attributed with chunk_id. Grouped by pattern. Textbook chunks only — not YouTube transcripts.
6. **Minimum 5 error pairs.** With explanations.
7. **Decolonization section present and substantive.**
8. **No Russianisms.** Not even as "also acceptable."
9. **Minimum 1,500 words.**

### STRONG PREFERENCES:
- Frequency-driven: not every form is equally important. Highlight what matters most.
- Actionable: a writer should be able to extract exact drills and sequences without reinvention.
- Cite textbook approaches specifically: "Заболотний introduces the genitive through possession (у кого є що)" — not vague advice.

## Anti-patterns (what NOT to do)

1. ❌ Inventing grammar rules not in the sources → ✅ Mark unsourced claims `<!-- VERIFY -->`
2. ❌ Missing the key constraint (e.g., "past active participles form only from intransitive verbs") → ✅ State ALL formation rules, especially restrictions
3. ❌ Meta-commentary in examples ("це пасивний... -> Краще") → ✅ Clean examples only
4. ❌ Strikethrough corrections in example sections → ✅ Put corrections in the L2 Errors section
5. ❌ Presenting every paradigm cell as equally important → ✅ Frequency-rank the forms
6. ❌ "Like in Russian..." as explanation → ✅ Explain from Ukrainian internal logic

## Self-audit (run through this checklist before outputting)

Before emitting the final article, mentally verify:

- [ ] Every paragraph has at least one `(Source N: chunk_id)` citation (both ordinal AND chunk_id)
- [ ] Total word count ≥ 1500
- [ ] Formation rules shown as transformation chains, not bare prose
- [ ] ALL restrictions stated explicitly with source attribution
- [ ] ≥ 12 natural examples, grouped by pattern, textbook-sourced
- [ ] ≥ 5 error pairs in ❌/✅ table format
- [ ] Decolonization section present and substantive
- [ ] No claim endorsed solely by a Wikipedia or YouTube chunk (all such claims marked `<!-- VERIFY -->`)
- [ ] No Russianisms endorsed in your own prose (включно з: `було встановлено`, `являти собою`, `в якості`, `відноситися до`, `на протязі`, `слідуючий`, `приймати участь`, `діючий`)

## Output

Return ONLY the markdown article. No preamble. Start with `# Title`.
