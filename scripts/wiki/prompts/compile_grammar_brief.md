# Wiki: Grammar Brief Compilation (A2–B2)

You are compiling a **grammar brief** for the Ukrainian language curriculum wiki. This brief will guide the content writer (a separate AI) when building modules that teach Ukrainian grammar to English-speaking teens and adults.

## Your Task

Compile a grammar brief on: **{topic}**
Domain: **{domain}**
Tracks served: **{tracks}**

## Source Material

The following source chunks come from Ukrainian textbooks (Заболотний Grades 5-9, Авраменко Grades 7-11, МійКлас) and grammar resources. Synthesize them into a clear reference guide.

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
The Ukrainian textbook approach. What Grade introduces this? What sequence? What terminology do they use? Reference Заболотний, Авраменко, МійКлас where possible.

## Повна парадигма (Full Paradigm)
Tables showing all forms. Highlight patterns (which endings are predictable, which are exceptions). Group by declension/conjugation class.

## Частотність і пріоритети (Frequency & Priorities)
Which forms appear most in real Ukrainian? What should the learner master first? What can wait? Cite Горох frequency data if available.

## Типові помилки L2 (Common L2 Errors)
What English speakers get wrong with this grammar point. Structural transfer from English, false analogies, missing categories (aspect, gender agreement). How to prevent each error.

## Деколонізаційні застереження (Decolonization Notes)
Where Ukrainian grammar differs from Russian. Common teaching traps: assuming shared rules, using Russian examples, presenting Ukrainian forms as "exceptions to Russian norms."

## Природні приклади (Natural Examples)
10-15 natural Ukrainian sentences using this grammar point. NOT translated from English. Include situations from daily life, textbook dialogues, common phrases. Each example should demonstrate ONE specific form or usage.

## Зв'язки з іншими темами (Connections)
How this grammar point connects to what came before and what comes after. Prerequisites and what this enables.

## Пов'язані статті (Related Articles)
Cross-links to other wiki articles.
```

## Quality Standards
- **Complete paradigms.** Don't summarize — show ALL forms. The writer needs the full picture.
- **Frequency-driven.** Not every form is equally important. Highlight what matters most.
- **Natural examples only.** Every example sentence must sound like something a Ukrainian would actually say. Not "The boy gives the book to the girl."
- **Decolonized.** Ukrainian grammar is its own system. Never explain it as deviation from Russian.
- **Cite textbook approaches.** "Заболотний introduces the genitive through possession (у кого є що)" — specific, actionable.
- **Minimum 1,500 words.** Grammar needs detail.

## Output

Return ONLY the markdown article. No preamble. Start with `# Title`.
