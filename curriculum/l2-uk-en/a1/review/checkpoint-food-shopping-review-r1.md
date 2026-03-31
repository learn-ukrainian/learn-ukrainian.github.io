

Good — all proper nouns (Анна, Дмитро, Олена) are confirmed in VESUM. The "замовляти" usage is correct per Антоненко-Давидович (not "заказати"). Now let me compile the full review.

## Linguistic Scan

**Russianisms:** None found. "Звичайно" is correct Ukrainian (not Russian "конечно"). "Замовляє" is correct (not "заказує").

**Surzhyk:** None found.

**Calques:** None found. Phrases like "Мені борщ, будь ласка" and "Рахунок, будь ласка" are natural Ukrainian café/market language.

**Paronyms:** None found.

**Russian characters (ы, э, ё, ъ):** None found.

**Gender/case errors:** All accusative forms are correct:
- Masculine inanimate: борщ → борщ, хліб → хліб, сік → сік ✓
- Feminine -а → -у: кава → каву, вода → воду, піца → піцу ✓
- Masculine animate = genitive: брат → брата, лікар → лікаря ✓
- Feminine animate: Олена → Олену, мама → маму ✓

**Vocative forms:** Олено ✓ (VESUM: `v_kly`), Анно ✓ (VESUM: `v_kly`), Дмитре ✓ (VESUM: `v_kly`), Михайле ✓.

**Factual claims:** Currency paradigm "одна гривня / дві гривні / п'ять гривень" is correct. All three forms verified in VESUM.

**One narrative logic error (not linguistic):** In the Діалог section, **Дмитро** says "Ти знаєш мого **брата** Дмитра?" — Дмитро is introducing his brother who is also named Дмитро. This is narratively absurd. In the Reading section, it's correctly done: Анна introduces "мого брата Михайла" (a different person). The dialogue should have **Наталя** introducing her brother, not Дмитро introducing a brother with his own name.

**One dialogue logic error:** The офіціант says "Все було дуже смачно!" — this is a customer's phrase complimenting the food, not something a waiter says. The plan's activity quiz correctly frames it as something YOU say. The waiter should just say "Звичайно" and the customer should say the compliment, or it should be removed from the waiter's line.

**One truncated sentence:** In "Що ми знаємо?", the text reads: "Can you recall ten foods and five drinks without looking? If yes, " — the sentence is cut off mid-thought. Missing completion.

No other linguistic errors found.

## Exercise Check

**Activity markers inventory:**
1. `<!-- INJECT_ACTIVITY: quiz-accusative-check -->` — after Читання section ✓ (matches plan hint 1: quiz on accusative forms)
2. `<!-- INJECT_ACTIVITY: fill-in-cafe-market -->` — after Граматика section ✓ (matches plan hint 2: fill-in café/market dialogue)
3. `<!-- INJECT_ACTIVITY: group-sort-accusative -->` — after Граматика section ✓ (matches plan hint 3: group-sort inanimate vs animate)
4. `<!-- INJECT_ACTIVITY: quiz-situations -->` — after Діалог section ✓ (matches plan hint 4: situation-matching quiz)

**4 markers for 4 plan activity hints** — correct count.

**Placement:** Markers are distributed across sections (after reading, after grammar x2, after dialogue). Not clustered. ✓

**Logic of plan activities (checking hints):**
- Quiz 1 (accusative): correct answers are all valid accusative forms. Distractors are nominative/genitive — plausible. ✓
- Fill-in: correct answers match the dialogue context. ✓
- Group-sort: inanimate vs animate categories are correct. All animate forms are genitive=accusative masculine. ✓
- Quiz 2 (situations): phrases match situations correctly. ✓

No exercise issues found.

## Scores

| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | All 5 content_outline sections present with correct headings. Self-check covers M36-M40 as specified. Reading follows plan's Anna scenario (market → café → meets friend → introduces brother). Grammar summary covers all 6 patterns from plan. Dialogue covers breakfast → market → café as planned. Summary mentions A1.7 next step. Minor: truncated sentence in section 1 ("If yes, ") leaves one plan point (the vocabulary self-test prompt) incomplete. |
| 2. Linguistic accuracy | 10/10 | All Ukrainian forms verified against VESUM. Accusative paradigm correctly presented for all four subcategories. Vocatives correct (Олено, Анно, Дмитре, Михайле). No Russianisms, surzhyk, calques, or paronyms. "Замовляти" confirmed correct per Антоненко-Давидович (not "заказувати"). Currency forms гривня/гривні/гривень all VESUM-verified. |
| 3. Pedagogical quality | 9/10 | Strong PPP flow: self-check → reading → grammar summary → connected dialogue → summary. Grammar presented with examples, not bare lists (e.g., Pattern 2 shows борщ→борщ, кава→каву with full example sentences). Accusative table is clear. Each pattern has 2-3 examples. Checkpoint structure appropriate — reviews M36-M40 without introducing new material. Minor deduction: the self-check section could have been more interactive (just checkmarks + vocabulary list). |
| 4. Vocabulary coverage | 10/10 | All plan vocabulary present: їжа, напої, meals (сніданок, обід, вечеря), accusative forms, café phrases (Мені..., Рахунок, Можна карткою?), market phrases (Скільки коштує/коштують, Дайте кілограм), з+noun chunks (кава з молоком, борщ зі сметаною, хліб із сиром). Food items comprehensive: борщ, вареники, салат, хліб, сир, піца, каша, яєчня, суп, котлета. Drinks: кава, чай, вода, сік, молоко. |
| 5. Exercise quality | 10/10 | 4 activity markers matching all 4 plan activity_hints. Markers placed after relevant teaching sections. Plan activities have varied correct-answer positions (not all index 0). Distractors are plausible (салата vs салат, борща vs борщ — genitive forms that a learner might confuse). Group-sort has balanced 5:5 split. Situation quiz tests functional language, not content recall. |
| 6. Engagement & tone | 9/10 | No motivational openers or meta-commentary. Direct, teacher-like tone: "Go through each checkpoint honestly — if something feels shaky, that's useful information." Reading section is a realistic scenario (Anna's day). No gamified language. The truncated sentence ("If yes, ") and one awkward waiter line slightly reduce polish. Final line "Ukrainian is becoming your language" is borderline motivational but earned after 41 modules. |
| 7. Structural integrity | 8/10 | All H2 headings present and ordered correctly. Word count 1265 vs 1000 target ✓. Clean markdown structure with dialogue divs. **Deductions:** (1) Truncated sentence "If yes, " is a structural defect. (2) The reading section mixes blockquote markers (`>`) with `<div class="dialogue">` blocks in a way that may cause rendering issues — blockquotes containing divs is fragile HTML/MDX. |
| 8. Cultural accuracy | 10/10 | Ukrainian presented on its own terms. No "like Russian" comparisons. Market and café scenarios are culturally authentic Ukrainian settings. Гривня as currency. Борщ зі сметаною, вареники, каша — authentic Ukrainian food culture. No decolonization issues. |
| 9. Dialogue & conversation quality | 7/10 | Reading section dialogue is natural with named speakers. **But the Connected Dialogue has two significant logic errors:** (1) Дмитро says "Ти знаєш мого брата Дмитра?" — introducing a brother with his own name is absurd/confusing. (2) The офіціант says "Все було дуже смачно!" — a customer phrase, not a waiter phrase. The three-scene structure (breakfast, market, café) is well-conceived and the market haggling ("Дорого!") feels natural. Named speakers throughout ✓. But the logic errors undermine the dialogue's credibility. |

## Findings

```
[STRUCTURAL INTEGRITY] [SEVERITY: major]
Location: "Що ми знаємо?" section, paragraph 3
Issue: Truncated sentence — "Can you recall ten foods and five drinks without looking? If yes, " cuts off mid-thought.
Fix: Complete the sentence, e.g., "If yes, you're ready to continue."
```

```
[DIALOGUE & CONVERSATION QUALITY] [SEVERITY: critical]
Location: "Діалог — У кафе" scene
Issue: Дмитро says "Ти знаєш мого брата Дмитра?" — a character introducing a brother with his own name is narratively absurd. The Reading section correctly has Анна introducing "мого брата Михайла" (different person). The dialogue should have Наталя introducing her brother, using a different name.
Fix: Change so that Наталя introduces the brother (e.g., "мого брата Андрія"), and Олена responds with the matching vocative.
```

```
[DIALOGUE & CONVERSATION QUALITY] [SEVERITY: major]
Location: "Діалог — У кафе" scene, last line
Issue: Офіціант says "Все було дуже смачно!" — this is a customer's phrase, not a waiter's. Waiters don't tell customers "everything was very tasty." The plan's own situation quiz correctly frames this as something the customer says.
Fix: Move the compliment to Наталя's line, or have the waiter say something appropriate like "Дякуємо!"
```

## Verdict: REVISE

Three findings require fixes: one critical (nonsensical brother introduction), one major (waiter dialogue logic), one major (truncated sentence). The linguistic accuracy is excellent — all Ukrainian forms are correct, no Russianisms or calques. The module is very close to PASS; these are targeted fixes.

<fixes>
- find: "Can you recall ten foods and five drinks without looking? If yes, "
  replace: "Can you recall ten foods and five drinks without looking? If yes, you remember A1.6 vocabulary well."
- find: "<div class=\"dialogue-line\"><span class=\"speaker\">Дмитро:</span> Ти знаєш мого брата Дмитра? *(Do you know my brother Dmytro?)*</div>\n\n<div class=\"dialogue-line\"><span class=\"speaker\">Олена:</span> Ні, не знаю. Дуже приємно, Дмитре! *(No, I don't. Nice to meet you, Dmytro!)*</div>"
  replace: "<div class=\"dialogue-line\"><span class=\"speaker\">Наталя:</span> Ти знаєш мого брата Андрія? *(Do you know my brother Andriy?)*</div>\n\n<div class=\"dialogue-line\"><span class=\"speaker\">Олена:</span> Ні, не знаю. Дуже приємно, Андрію! *(No, I don't. Nice to meet you, Andriy!)*</div>"
- find: "<div class=\"dialogue-line\"><span class=\"speaker\">Офіціант:</span> Звичайно. Все було дуже смачно! *(Of course. Everything was very tasty!)*</div>"
  replace: "<div class=\"dialogue-line\"><span class=\"speaker\">Офіціант:</span> Звичайно! *(Of course!)*</div>\n\n<div class=\"dialogue-line\"><span class=\"speaker\">Наталя:</span> Дякую! Все було дуже смачно! *(Thank you! Everything was very tasty!)*</div>"
- find: "Accusative animate: **Олену**, **брата Дмитра** — the people they see and introduce."
  replace: "Accusative animate: **Олену**, **брата Андрія** — the people they see and introduce."
</fixes>
