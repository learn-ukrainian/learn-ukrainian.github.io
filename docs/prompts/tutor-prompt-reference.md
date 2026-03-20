# Ukrainian Tutor Prompt — Reference for V6 Writing Prompt

**Source:** Tested prompt that catches errors other prompts miss (тактична/тактовна paronym, Russicisms, calques)
**Status:** Reference — adapt principles for V6 content writing prompt (#995)
**DO NOT copy verbatim — this is a personal tutor prompt. Extract the principles.**

## Why it works (analysis)

1. **"Admit uncertainty, never invent"** — LLM doesn't hallucinate when unsure
2. **Named reference hierarchy** — Горох, Словник.UA, Грінченко, Антоненко-Давидович
3. **Calque detection as separate skill** — not just "no Russicisms" but three distinct checks: Russianisms, surzhyk, calques
4. **Zero-tolerance with structure** — every error corrected, but methodically
5. **Ukrainian FIRST** — thinks in Ukrainian, translates to English after
6. **Stress marks only in vocabulary** — no contradiction possible
7. **Short and specific** — 5 principles, not 50 rules

## Principles to extract for V6

### Hard Rules (max 5 for writing prompt)
1. **Honesty over confidence:** If unsure about a word, stress, or form — flag it with `<!-- VERIFY -->`, don't invent.
2. **No Russianisms, no surzhyk, no calques:** Three separate checks. тактична≠тактовна is a calque/paronym, not a Russicism.
3. **Ukrainian authority hierarchy:** Горох (stress/morphology), VESUM (forms), Правопис 2019 (orthography), Антоненко-Давидович (style).
4. **Ukrainian first:** Write the Ukrainian, then explain in English. Not "here's an English explanation with Ukrainian examples."
5. **Stress marks only where specified:** In vocabulary sections and first occurrence in prose (handled by pipeline). Writer does not add them.

### Quality dimensions to add
- **Paronym detection:** Does the content use the RIGHT word, not just a similar-sounding one?
- **Calque detection:** Is a phrase translated literally from English instead of using the natural Ukrainian expression?
- **Register awareness:** Is the Ukrainian appropriate for the context (розмовний vs книжний vs офіційний)?

### Test scenarios (from real failures)
1. тактична vs тактовна — paronym (caught by this prompt, missed by default)
2. кон vs кін — Russicism (caught by Gemini adversarial review)
3. програміст "used for both" — outdated claim (програмістка exists)
4. Ї softens consonants — factual error (Ї never softens)
5. мяч without apostrophe — orthographic error (м'яч)
6. братú stress — Russian-influenced error (not брáти)
7. Па-пá regional attribution — factual error (western, not eastern)
8. метро stress — мéтро wrong, метрó correct

## Original prompt structure (for reference)

```
Role & Persona → Core Operating Principles (3) → Special Workflow
```

- Role: expert instructor, friendly but rigorous
- Principle 1: Zero-tolerance corrections, bilingual output (UA first)
- Principle 2: Linguistic standards (no Latin, no Russianisms, calque detection, stress rules)
- Principle 3: Source authority (admit uncertainty, reference hierarchy)
- Workflow: structured output format (intro → parallel text → vocabulary → exercises)
