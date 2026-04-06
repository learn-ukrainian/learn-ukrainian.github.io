# Wiki: Grammar Brief Compilation (A2–B2)

You are compiling a **grammar brief** for the Ukrainian language curriculum wiki. This brief will guide the content writer (a separate AI) when building modules that teach Ukrainian grammar to English-speaking teens and adults.

## Your Task

Compile a grammar brief on: **{topic}**
Domain: **{domain}**
Tracks served: **{tracks}**

## Source Material

The following source chunks come from Ukrainian textbooks (Заболотний Grades 5-9, Авраменко Grades 7-11, МійКлас) and grammar resources. **Every claim MUST cite a specific source** using `(Source N)` or `(Джерело: chunk_id)`. If no source supports a claim, mark it `<!-- VERIFY -->`.

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
- Show formation rules step-by-step: stem → suffix → ending

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
1. **Source citations in every section.** Woven into claims, not just in metadata.
2. **Complete paradigms in tables.** Don't summarize — show ALL forms.
3. **Minimum 12 natural examples.** Source-attributed. Grouped by pattern.
4. **Minimum 5 error pairs.** With explanations.
5. **Decolonization section present and substantive.**
6. **No Russianisms.** Not even as "also acceptable."
7. **Minimum 1,500 words.**

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

## Output

Return ONLY the markdown article. No preamble. Start with `# Title`.
