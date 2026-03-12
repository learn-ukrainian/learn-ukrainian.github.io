# Beginner Research + Meta Outline

> **You are Gemini, executing the research phase for a beginner-level module.**
> **Your task: Generate lightweight research notes AND a content_outline (meta YAML) in one pass.**

---

## Your Input

Read the plan file (SOURCE OF TRUTH):
```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/checkpoint-communication.yaml
```

Read the level quick-ref for constraints:
```
/Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/quick-ref/A1.md
```

---

## Module Sequence Constraints

SEQUENCE CONSTRAINTS (A1.5 — Modals, Commands & Life):
All tenses available. Imperative mood is TAUGHT in this phase (M47).
Imperative forms are ALLOWED after M47 introduces them.

For M47 itself: Use imperative forms freely — читай/читайте, пиши/пишіть, скажи/скажіть, дай/дайте, іди/ідіть.
Both imperfective AND perfective verbs allowed for imperatives.



---

## Textbook Context

## Textbook Excerpts (from real Ukrainian school textbooks)

Use these as authoritative reference for your research. Note how textbooks teach this topic: what exercises they use, what cultural examples they include, what common errors they address.

**Grade 7, mishhenko — Сторінка 3**:
```
3
```

**Grade 7, litvinova — Сторінка 1**:
```
Підручник 
 
         видавництво "Ранок"
```

**Grade 6, shchupak — Сторінка 2**:
```
Український освітянський 
видавничий центр 
«Оріон»
```

**Grade 6, shchupak — Сторінка 260**:
```
Український освітянський 
видавничий центр 
«Оріон»
```

**Grade 5, avramenko — Сторінка 89**:
```
89
 § 38–39.  Наголос.  Орфоепічна  помилка
ІІ. Квартал, кілометр, корисний, курятина, листопад, навчання, на-
чинка, ненависть, новий, обіцянка, одинадцять, ознака, олень, підлітко-
вий, пізнання, подруга, поняття.
ІІІ. Посередині, проміжок, псевдонім, разом, сантиметр, середина, сли-
на, стрибати, текстовий, течія, тулуб, фартух, фаховий, фольга, чорнозем, 
чорнослив, шовковий. 
А. Запишіть неправильно наголошені слова й позначте в них наголос. 
Б. Вивчіть ці слова. 
3.	Випишіть слова, що мают
```

**Grade 5, avramenko — Сторінка 76**:
```
76
ФОНЕТИКА. ГРАФІКА. ОРФОЕПІЯ. ОРФОГРАФІЯ 
2.	Прочитайте речення та виконайте завдання.
1. Лань вискочила на широкий лан. 2. Стань, випрямся, глибоко дихай, 
аби твій фізичний стан був спокійним. 3. Син біля нічного моря спрямував 
свій погляд у далеку синь. 4. Хіба рись їсть рис? 5. Увесь берег покриває галь-
ка, а галка своїм забарвленням зливається із цими дрібними камінчиками 
(З інтернету).
А. Знайдіть і прочитайте слова, що розрізняються лише твердістю/ 
м’якістю одного з приголосних. 
Б.
```

---

## PART 1: Research

Research **Checkpoint: Communication** for the **A1** track.

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

# Дослідження: Checkpoint: Communication

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
