Now I have all the verification data I need. Here is my complete review:

---

## Linguistic Scan

**Two critical grammatical errors found in Section 1 (Instrumental endings recap):**

1. **Overgeneralized feminine rule:** "Жіночий рід **завжди** отримує закінчення -ою або -ею / -єю." This is factually wrong. III відміна feminines take -ю in instrumental: ніч→**ніччю**, сіль→**сіллю**, любов→**любов'ю**, радість→**радістю** (all verified via `verify_lemma`). The word "завжди" makes a universal claim that will teach learners an incorrect rule.

2. **Self-contradicting plural rule + example:** "У множині ми **завжди** використовуємо закінчення -ами або -ями. Наприклад, **двері** (doors) стають **дверима**." The example directly contradicts the rule — "дверима" ends in **-има**, not -ами/-ями. VESUM confirms: двері→**дверима** (v_oru). Other exceptions: люди→**людьми** (v_oru, verified via `verify_lemma`). A learner reading this will be confused — the example breaks the rule stated in the same sentence.

**No Russianisms, Surzhyk, calques, or Russian characters detected.** All 758 VESUM-verified words are confirmed valid. "Підвал", "тумбочка", "пухнастий" — all verified in VESUM. Style guide checks for potential calques returned no hits on any vocabulary used in this module.

## Exercise Check

Four `<!-- INJECT_ACTIVITY -->` markers present, matching all four `activity_hints` from the plan:

| # | Marker | After section | Plan match | Placement |
|---|--------|--------------|------------|-----------|
| 1 | `match-up` — spatial relationships | Section 1 | ✓ `match-up` | ✓ After teaching all 5 prepositions |
| 2 | `true-false` — room diagram | Section 2 | ✓ `true-false` | ✓ After room description practice |
| 3 | `quiz` — spatial vs temporal | Section 3 | ✓ `quiz` | ✓ After temporal meaning taught |
| 4 | `fill-in` — preposition + Instrumental | Section 4 | ✓ `fill-in` | ✓ After full practice section |

All markers correctly placed after relevant teaching content. Even spread across sections. Each matches the plan's activity_hints in type and focus. All item counts (8 each) match the plan. ✓

## Scores

| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | All four content_outline sections covered with correct focus. Required vocabulary all present: над, під, перед, за, між, стіл, будинок, ліжко, стіна, обід — all used naturally in prose. Recommended vocabulary (стеля, підлога, кут, розклад, сон) also present. Section word budgets roughly proportional. The `dialogue_situations` museum setting (Гід музею, Відвідувачі, камін, скульптура між вікнами) was **not implemented** — replaced with furniture-arranging (Section 2) and tourist-asking-directions (Section 4), which are adequate but don't follow the plan's specific cultural setting. An extra "Підсумок" section was added that isn't in the plan (minor). Word count 2810 exceeds 2000 target ✓. |
| 2. Linguistic accuracy | 7/10 | Two critical errors in Section 1 grammar recap: (1) "Жіночий рід **завжди** отримує закінчення -ою або -ею / -єю" — wrong for III відміна feminines (ніч→ніччю, любов→любов'ю). (2) "У множині ми **завжди** використовуємо закінчення -ами або -ями. Наприклад, двері стають дверима" — example directly contradicts the stated rule (дверима = -има, not -ами/-ями). These teach wrong grammar. All other Ukrainian text, case endings, gender assignments, and preposition usage verified correct. |
| 3. Pedagogical quality | 8/10 | Good PPP flow: presentation of each preposition with 3-5 examples, then room-description practice, then temporal extension, then mixed practice. Grammar points introduced with ample Ukrainian examples (5+ per preposition). Section 3 effectively contrasts spatial vs temporal meaning of перед/за. Section 4's Accusative vs Instrumental distinction is well-explained for A2. However, the opening grammar recap (Section 1) teaches two incorrect rules — the pedagogical damage of wrong grammar rules at the recap stage is significant. |
| 4. Vocabulary coverage | 9/10 | All 10 required vocabulary items used naturally in prose (not as bare lists). All 5 recommended items present: стеля (dialogue: "повісь лампу високо на стелі"), підлога (section 2: "на підлозі"), кут (section 2: "Постав її в кут між вікном і широкими дверима"), розклад ("за розкладом"), сон ("перед сном"). Additional room vocabulary introduced contextually: камін, полиця, дзеркало, умивальник, тумбочка. |
| 5. Exercise quality | 9/10 | All 4 plan activity_hints implemented with correct type and focus. Markers placed after relevant teaching. 8 items each as specified. Match-up tests spatial recognition; true-false tests room comprehension; quiz tests semantic distinction (spatial vs temporal); fill-in tests productive grammar. Good variety of exercise types testing different skills. |
| 6. Engagement & tone | 6/10 | Significant English meta-commentary that adds nothing: "These five prepositions are absolutely essential for describing the physical space around you" (generic motivation), "The preposition 'над' describes a vertical relationship where objects do not touch each other" (telling not showing), "This is a very important and beautiful distinction in Ukrainian grammar" (filler), "These prepositions perfectly capture the physical relationships between objects in space" (corporate-speak). Multiple instances of "Let's" meta-framing: "Let's quickly recap", "let's imagine". Section 4 has: "This is a very important and beautiful distinction" — a sentence that could apply to any language course unchanged. The Ukrainian prose itself is natural and engaging, but the English padding inflates without teaching. |
| 7. Structural integrity | 9/10 | Clean markdown, all plan sections present and ordered. H2 headings match plan sections (with minor title simplification on Section 2: "Описуємо кімнату" drops the English subtitle — acceptable). Extra "Підсумок" section added beyond plan — not harmful but not planned. Word count 2810 > 2000 target ✓. No stray tags or formatting artifacts. |
| 8. Cultural accuracy | 10/10 | Ukrainian presented entirely on its own terms. No "like Russian but..." comparisons. Case system explained using Ukrainian metalanguage (орудний відмінок, називний відмінок, знахідний відмінок). Cultural contexts appropriate — arranging a room, asking for directions in a Ukrainian city, daily routines. No decolonization issues. |
| 9. Dialogue & conversation quality | 9/10 | Two dialogues, both strong. Макс/Олена dialogue: natural situation (arranging furniture in a new room), named speakers, multi-turn, practical use of all prepositions, distinct voices. Турист/Місцевий dialogue: natural direction-asking scenario, appropriate register shift (formal "Перепрошую, ви не підкажете"), culturally correct closing ("Прошу, нехай щастить! Гарного вам дня!"). Both dialogues use prepositions organically. Minor: Турист/Місцевий uses role labels rather than names — acceptable for a stranger-interaction scenario. |

## Findings

```
[LINGUISTIC ACCURACY] [SEVERITY: critical]
Location: Section 1, paragraph 1 — "Жіночий рід завжди отримує закінчення -ою або -ею / -єю."
Issue: Factually wrong universal claim. III відміна feminines take -ю in Instrumental (ніч→ніччю, сіль→сіллю, любов→любов'ю, радість→радістю — all confirmed via VESUM verify_lemma). "Завжди" teaches an incorrect rule.
Fix: Scope the statement to I відміна feminines (іменники на -а/-я).
```

```
[LINGUISTIC ACCURACY] [SEVERITY: critical]
Location: Section 1, paragraph 1 — "У множині ми завжди використовуємо закінчення -ами або -ями. Наприклад, двері (doors) стають дверима."
Issue: Self-contradiction. The example "дверима" has ending -има, directly contradicting the "-ами або -ями" rule. VESUM confirms двері→дверима (v_oru). Other exceptions: люди→людьми. Teaching a rule and immediately breaking it with your own example will confuse learners.
Fix: Either change the example to a regular noun (вікна→вікнами), or add a note about exceptions.
```

```
[ENGAGEMENT & TONE] [SEVERITY: major]
Location: Throughout all sections — English meta-commentary
Issue: Multiple instances of generic English padding that doesn't teach anything:
  - "These five prepositions are absolutely essential for describing the physical space around you." (Section 1)
  - "The preposition 'над' describes a vertical relationship where objects do not touch each other." (Section 1)
  - "The preposition 'під' is used for objects that are underneath something else, often resting on the floor or covered." (Section 1)
  - "This preposition usually links two distinct objects to show that something is directly in the middle." (Section 1)
  - "This is a very important and beautiful distinction in Ukrainian grammar." (Section 4)
  - "These prepositions perfectly capture the physical relationships between objects in space." (Section 4)
Fix: Replace with specific, useful guidance or remove. The Ukrainian examples already demonstrate these concepts — the English restates what the Ukrainian already shows.
```

```
[ENGAGEMENT & TONE] [SEVERITY: minor]
Location: Section 2, paragraph 2 — "Для побудови правильної відповіді ми використовуємо іменник у називному відмінку. Потім ми додаємо відповідний прийменник і друге слово в орудному відмінку."
Issue: Overly procedural meta-explanation. This reads like assembly instructions, not language teaching. The Q&A examples that follow demonstrate the pattern perfectly — the meta-explanation is redundant.
Fix: No fix needed — minor polish item.
```

## Verdict: REVISE

Two critical linguistic errors (wrong grammar rules taught to learners) require fixing. The Instrumental endings recap in Section 1 makes two factually incorrect universal claims — one about feminine endings and one about plural endings — both immediately contradicted by VESUM-verified forms. These are the kind of errors that will confuse A2 learners and build incorrect mental models. The engagement score is also below standard due to excessive English meta-commentary, though this is secondary to the linguistic accuracy issues.

<fixes>
- find: "Жіночий рід завжди отримує закінчення **-ою** або **-ею** / **-єю**. Наприклад, **стіна** *(wall)* стає стіною."
  replace: "Іменники жіночого роду на **-а** / **-я** отримують закінчення **-ою** або **-ею** / **-єю**. Наприклад, **стіна** *(wall)* стає стіною."
- find: "У множині ми завжди використовуємо закінчення **-ами** або **-ями**. Наприклад, **двері** *(doors)* стають дверима."
  replace: "У множині ми зазвичай використовуємо закінчення **-ами** або **-ями**. Наприклад, **вікна** *(windows)* стають вікнами, а **гори** *(mountains)* стають горами. Деякі іменники мають особливі форми: **двері** *(doors)* стають дверима."
- find: "These five prepositions are absolutely essential for describing the physical space around you. Усі ці прийменники вимагають орудного відмінка, коли ми відповідаємо на питання «Де?»."
  replace: "Усі ці прийменники вимагають орудного відмінка, коли ми відповідаємо на питання «Де?»."
- find: "The preposition \"над\" describes a vertical relationship where objects do not touch each other. Дуже важливо не плутати його з прийменником «на»."
  replace: "Дуже важливо не плутати його з прийменником «на»."
- find: "The preposition \"під\" is used for objects that are underneath something else, often resting on the floor or covered. Мій пухнастий"
  replace: "Мій пухнастий"
- find: "This preposition usually links two distinct objects to show that something is directly in the middle. Коли ми використовуємо слово «між», ми зазвичай з'єднуємо два предмети сполучником «і»."
  replace: "Коли ми використовуємо слово «між», ми зазвичай з'єднуємо два предмети сполучником «і»."
- find: "This is a very important and beautiful distinction in Ukrainian grammar. When there is no movement and we describe a static, unmoving location, we use the Instrumental case with spatial prepositions like «під», «над», and «за»."
  replace: "When there is no movement and we describe a static location, we use the Instrumental case with spatial prepositions like «під», «над», and «за»."
- find: "These prepositions perfectly capture the physical relationships between objects in space. Наприклад: кіт лежить під ліжком."
  replace: "Наприклад: кіт лежить під ліжком."
</fixes>
