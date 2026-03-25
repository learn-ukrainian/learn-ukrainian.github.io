## Linguistic Scan

**Russianisms:** None found.
**Surzhyk:** None found.
**Calques:** None found.
**Paronyms:** None found.
**Russian characters (ы, э, ё, ъ):** None found.
**Gender/case errors:** None found — all case forms verified against VESUM (дістатися, ідіть/іти, їдьте/їхати, автобусом/автобус, трамваєм/трамвай, хвилин/хвилина, розі/ріг, зупинку/зупинка, околиці/околиця, моєму/мій).

**VESUM false positives:** Анна (noun:prop:fname ✓) and Шевченка (noun:prop:lname, genitive of Шевченко ✓) are both in VESUM — pipeline batch check missed them due to capitalization.

**Minor inconsistency:** The module uses both **Ідіть** (standard imperative of іти, used throughout prose and most exercises) and **Йдіть** (imperative of йти, used once in fill-in exercise item 5). Both forms exist in VESUM, but mixing them in one A1 module may confuse learners. The plan itself uses both, so this is not a deviation — but pedagogically, consistency would be better.

No linguistic errors found.

## Exercise Check

| # | Type | Title | Items | Plan match | Logic |
|---|------|-------|-------|------------|-------|
| 1 | `:::fill-in` | "Give directions using прямо, направо, наліво" | 6 | ✓ Matches activity_hint #1 | ✓ All answers correct, blanks are directional adverbs taught in the section |
| 2 | `:::quiz` | "Де (locative) or Куди (accusative) in context" | 6 | ✓ Matches activity_hint #2 | ✓ All locative/accusative choices correct, distractors are the opposite case (plausible) |
| 3 | `:::fill-in` | "Describe route with transport (автобусом, пішки, на метро)" | 6 | ✓ Matches activity_hint #3 | ✓ Transport mode answers match context clues (далеко→на метро, близько→пішки) |
| 4 | `:::match-up` | "Match question to logical response for navigation" | 6 | ✓ Matches activity_hint #4 | ✓ All pairs are semantically correct, no cross-matching possible |

**Total exercises:** 4 (matches plan's 4 `activity_hints`). All exercises placed after the relevant teaching section. All test language skills, not content recall.

**Placement:** Exercise 1 after Dialogues ✓, Exercise 2 after Де/Куди section ✓, Exercise 3 after Мій район ✓, Exercise 4 in Summary ✓.

No exercise issues found.

## Scores

| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | All 4 sections present with matching H2 headings. Both dialogues follow plan scripts exactly (Турист/Перехожий for D1, Анна/Максим for D2). Preposition synthesis table matches plan. All vocabulary_hints (required: пішки, хвилина, район, центр, вибачте; recommended: дістатися, ідіть, їдьте, поруч, навпроти, між) appear in prose. All 4 activity_hints implemented. Word count 1321 vs 1200 target ✓. Minor: plan blanks show multi-blank items (e.g., "Ідіть {прямо}, потім {направо}") but exercises use single blanks — acceptable simplification for A1. |
| 2. Linguistic accuracy | 10/10 | All 108 Ukrainian words verified against VESUM. Case endings correct: "бібліотеки" (Gen after до), "автобусом" (Instr), "у парку" (Loc), "в магазин" (Acc), "на вулиці" (Loc), "на роботу" (Acc). Imperative forms "ідіть" (іти) and "їдьте" (їхати) correct. No Russianisms, Surzhyk, calques, or paronyms found. |
| 3. Pedagogical quality | 9/10 | Clear PPP structure: Dialogues present real conversation → explanation of forms → practice exercises. Grammar scope appropriate for A1.5 — synthesizes M28-M32 without introducing new grammar. Imperative forms (ідіть, їдьте) correctly framed as "preview" per plan. між + Instrumental acknowledged but wisely limited to indeclinable nouns ("For now, you can safely use it with foreign loan words that never change their endings"). Genitive after до explained with concrete examples (бібліотека→бібліотеки, центр→центру). |
| 4. Vocabulary coverage | 10/10 | All 5 required words used naturally in prose: пішки ("іду пішки п'ять хвилин"), хвилина ("п'ять хвилин"), район ("У моєму районі є кафе"), центр ("до центру"), вибачте ("Вибачте, як дістатися"). All 6 recommended words present: дістатися (dialogue + explanation), ідіть/їдьте (dialogue + explanation), поруч ("Зупинка поруч"), навпроти ("Кафе навпроти парку"), між ("Магазин між метро і кіно"). Words introduced in context through dialogues and example sentences, not as isolated lists. |
| 5. Exercise quality | 9/10 | All 4 exercises match plan activity_hints in type, focus, and item count (6 each). Quiz exercise tests де/куди distinction with case-form distractors — forces learner to choose correct case, not just vocabulary. Fill-in exercises test directional adverbs and transport modes contextually. Match-up pairs are unambiguous (no cross-matching). All exercises test language skills taught in the preceding section. |
| 6. Engagement & tone | 8/10 | Generally warm and authoritative. Good cultural hooks: Ukrainian neighborhood identity ("people strongly identify with their район"), politeness norms ("Вибачте"), formal/informal register awareness. However, several LLM filler phrases: "one of the most rewarding milestones in language learning" (§1, sentence 1), "It is incredibly versatile" (§1, after Dialogue 1), "You now possess a complete urban communication toolkit" (Summary, sentence 1). These feel generic rather than teacher-like. |
| 7. Structural integrity | 10/10 | All 4 H2 headings match plan exactly: "Діалоги (Dialogues)", "Де і куди разом (Where and Where To Together)", "Мій район (My Neighborhood)", "Підсумок — Summary". Word count 1321 ≥ 1200 target. No duplicate sections. No meta-commentary. Clean markdown with proper dialogue div blocks. |
| 8. Cultural accuracy | 10/10 | Ukrainian presented entirely on its own terms. No "like Russian but…" comparisons. Street names are Ukrainian cultural figures (Франка, Шевченка). Ukrainian social norms respected (Вибачте for strangers, formal imperative for unknown adults). No factually incorrect claims about Ukrainian language or culture. |
| 9. Dialogue quality | 9/10 | Dialogue 1 (tourist asking for directions) is natural and realistic — appropriate use of Вибачте, contrast between walking and metro. Dialogue 2 (describing daily commute) flows naturally with sequence words (спочатку, потім). Speaker roles clear (Турист/Перехожий, Анна/Максим). Both dialogues follow plan scripts faithfully. Situations are genuinely useful for someone navigating a Ukrainian city. |

## Findings

```
[ENGAGEMENT] [MINOR]
Location: Section "Діалоги", paragraph 1, sentence 1
Issue: LLM filler — "Navigating a new city is one of the most rewarding milestones in language learning."
Fix: Replace with a direct, teacher-like opening that sets up the practical context.
```

```
[ENGAGEMENT] [MINOR]
Location: Section "Діалоги", paragraph after Dialogue 1, sentence 2
Issue: LLM filler — "It is incredibly versatile because it does not specify whether you are walking or driving."
Fix: Trim the superlative; state the functional fact directly.
```

```
[ENGAGEMENT] [MINOR]
Location: Section "Підсумок", paragraph 1, sentence 1
Issue: LLM filler — "You now possess a complete urban communication toolkit."
Fix: Replace with a direct summary opener.
```

## Verdict: PASS

Zero critical findings, zero major findings. Three minor engagement issues (LLM filler phrases) that do not affect linguistic accuracy, pedagogical quality, or exercise correctness. The module faithfully implements the plan, all Ukrainian forms are VESUM-verified, exercises are well-constructed and correctly placed, and dialogues are natural. Word count (1321) exceeds the 1200 target. All required and recommended vocabulary is used in context. The module is shippable.
