# Beginner Research + Meta Outline

> **You are Gemini, executing the research phase for a beginner-level module.**
> **Your task: Generate lightweight research notes AND a content_outline (meta YAML) in one pass.**

---

## Your Input

Read the plan file (SOURCE OF TRUTH):
```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/questions-and-negation.yaml
```

Read the level quick-ref for constraints:
```
/Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/quick-ref/A1.md
```

---

## Module Sequence Constraints

GRAMMAR CONSTRAINTS (A1.2 — Verbs & Sentences):
Present tense verbs are fully available. Simple sentences.

ALLOWED:
- Present tense (я читаю, він іде, вони мають)
- Basic imperatives (читай/читайте, слухай/слухайте, дивись/дивіться)
- Infinitives in simple contexts (можна читати, треба слухати)
- Simple questions and answers

BANNED (too complex for A1.2):
- Past tense, future tense, conditionals
- Participles, passive voice
- Complex subordinate clauses



---

## Textbook Context

## Textbook Excerpts (from real Ukrainian school textbooks)

Use these as authoritative reference for your research. Note how textbooks teach this topic: what exercises they use, what cultural examples they include, what common errors they address.

**Grade 7, avramenko — Сторінка 30**:
```
Б. Зробіть звуковий запис виділених слів.
```

**Grade 7, avramenko — Сторінка 65**:
```
62
Зауважте!
1. Щоб визначити основу інфінітива, відкидаємо суфікс -ти: чита-ти, 
зва-ти, грі-ти. 
2. Дієслова минулого часу за особами не змінюємо. На особу може вка-
зувати займенник: я знайшла, ти знайшла, вона знайшла.
2.	 Випишіть форми дієслів минулого часу.
Гримнула, проситися, знає, любила, зів’яне, очищу, аналізували, зві-
рятися, допоміг, плестиму, вагатися, іскрилася, брататися, оклигало, 
спитають, утечеш, лякався, протікати, уберіг, змагаєшся, спостеріг.
	
З перших букв виписаних сл
```

**Grade 6, avramenko — Сторінка 197**:
```
197
197
§ 99–100.  Написання  заперечних і  неозначених  займенників
7.	 Напишіть мінівисловлення-відмову від пропозиції, що загрожує вашому 
життю або здоров’ю, на тему «Ризик у казках і в реальності» (сім–дев’ять 
речень). Використайте  заперечні та неозначені займенники. 
8. Розгадайте кросворд. 
А.	Утворіть словотвірний ланцюжок слова-відгадки. 
Б.	Створіть запрошення вчителю / учительці, що перебуває на заслужено-
му відпочинку, на Свято останнього дзвоника. Розподіліть обов’язки між 
група
```

**Grade 6, avramenko — Сторінка 223**:
```
192
§ 99–100. Написання  заперечних  і  неозначених  займенників . . . 194
§ 101. Розвиток мовлення. Есе  світоглядного  змісту . . . . . . . . . . . . 198
§ 102. Наголошування  займенників  . . . . . . . . . . . . . . . . . . . . . . . . . 200
§ 103. Використання  займенників  для  зв’язку  речень  у  тексті . 202
§ 104. Повторення  та  узагальнення  вивченого  в  6 класі. Морфологія. Орфографія . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 204
§ 105. Повторення та узагаль
```

**Grade 5, zabolotnyi — Сторінка 242**:
```
239
	22. Наголос. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 90
	23. Вимова голосних. Позначення на письмі  
ненаголошених [е], [и] в коренях слів. . . . . . . . . . . . . . . 96
	24. Вимова приголосних звуків. Уподібнення  
приголосних. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 101
	25. Правопис префіксів з- (с-, зі-), роз- (розі-), без-. . . . . . . . 106
	26. Спрощення в групах приголосних. . . . . . . . . . . . . . . . . 109
	27. Чергування голо
```

**Grade 5, litvinova — Сторінка 4**:
```
4
Зміст
Підсумковий тест . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 100
Підсумовуємо й  узагальнюємо . . . . . . . . . . . . . . . . . . . . . . . . . . 102
ФОНЕТИКА. ГРАФІКА. ОРФОЕПІЯ. ОРФОГРАФІЯ . . . . . . . . . 103
Фонетика. Звуки мовлення . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 104
Транскрипція  . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 107
Голосні та приг
```

---

## PART 1: Research

Research **Questions & Negation** for the **A1** track.

Beginner research is focused and practical — no literary analysis, no decolonization framing. **Use the textbook excerpts above** as your primary reference for how this topic is taught.

### What to research:

1. **State Standard**: Briefly check `docs/l2-uk-en/state-standard-2024-mapping.yaml` for the relevant A1 entry. Quote the §reference if one exists. If no mapping applies (e.g., letter-introduction modules), write "No specific § — foundational literacy prerequisite."
2. **Vocabulary**: For key vocabulary items in the plan's `vocabulary_hints`, list them in a table with brief notes (frequency, collocations, or cognate status). Minimum 5 rows.
3. **Common errors**: 3-4 mistakes English speakers make with this topic (numbered list). Reference textbook exercises above — what errors do the exercises target?
4. **Cultural hooks**: 2-3 verified cultural connections (загадки, скоромовки, proverbs, songs, folk sayings, real-life situations from Ukrainian daily life). Look at the textbook excerpts for examples. Keep it concrete — a specific riddle or saying is better than a vague "Ukrainians value politeness."
5. **Cross-references**: Which modules this builds on and prepares for (check plan's `connects_to`)
6. **Teaching strategy**: How should this concept be introduced to a learner? Describe a concrete discovery exercise — a scenario, dialogue, or set of examples that lets the learner notice the pattern BEFORE you explain the rule. What real-life context makes this grammar point feel natural (classroom, café, market, directions)? What contrastive pairs would help disambiguation? **Cite specific textbook exercises from the excerpts above as models.**
7. **Notes**: Any observations useful for the content writer

### What NOT to research:

- Decolonization framing (irrelevant for alphabet and basic vocabulary)
- Literary or historical sources
- Deep frequency analysis (a brief table is enough)

---

## PART 2: Meta Outline

Generate a `content_outline` for this module. The outline defines H2/H3 structure with word budgets.

**Target**: 1200 total words across all sections.

### Outline rules:

1. Section word budgets must sum to approximately 1200 (±10%)
2. Each section needs a clear teaching purpose (introduce, practice, reinforce)
3. Structure should build progressively: introduce concept → show examples → practice → summarize
4. Include a summary section with 3-4 self-check questions

---

## Output Format

```
===RESEARCH_START===

# Дослідження: Questions & Negation

## State Standard Reference
§{section_number}: "{quoted requirement}" (or "No specific § — foundational literacy prerequisite" for alphabet modules)
Alignment: {how this module addresses the standard}

## Vocabulary Frequency
| Word | Notes | Key collocations |
|------|-------|------------------|
| ...  | ...   | ...              |

## Cultural Hooks
1. {Verified fact or загадка/скоромовка/saying — concrete and specific}
2. {Another hook — different type from #1}
3. {Optional third hook}

## Common Learner Errors
1. {Error pattern} → {Correct form} — {Why it happens}
2. {Another error}
3. {Third error — reference textbook exercise if possible}

## Cross-References
- Builds on: {module slugs or "first module"}
- Prepares for: {module slugs}

## Teaching Strategy
- **Discovery exercise**: {Concrete scenario/dialogue that introduces the pattern before explaining the rule}
- **Best context**: {Real-life situation where this grammar appears naturally}
- **Contrastive pairs**: {Examples that highlight the key distinction learners need to grasp}

## Notes for Content Writing
- {Any observations for the content writer}

===RESEARCH_END===
```

**Research word cap**: 400-800 words. Keep it dense: facts, tables, examples — not prose.

```
===META_OUTLINE_START===
content_outline:
  - title: "Section Title"
    slug: section-slug
    words: 300
    points:
      - "Teaching point 1"
      - "Teaching point 2"
  - title: "Another Section"
    slug: another-section
    words: 250
    points:
      - "Teaching point"
===META_OUTLINE_END===
```

## Boundaries

- Do NOT write lesson content — only research notes and meta outline
- Do NOT invent vocabulary outside the plan's vocabulary_hints
- Do NOT fabricate cultural facts — if unsure, omit
- Keep research focused — beginner modules need structured research, not lengthy prose
