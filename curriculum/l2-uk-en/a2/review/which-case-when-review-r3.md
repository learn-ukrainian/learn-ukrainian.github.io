Now I have all the verification data I need. Let me compile the review.

## Linguistic Scan

**Russianisms:** None found. All Ukrainian vocabulary verified via VESUM (724/724 words confirmed, 8 not-found entries are proper nouns and morphological suffixes — all expected).

**Surzhyk:** None found.

**Calques:** None found. The module correctly teaches "дякувати комусь" (Dative) vs. incorrect "дякувати когось" — confirmed by Антоненко-Давидович (ad-124): "дієслово дякувати керує іменником чи займенником у давальному відмінку: дякую батькові, дякуємо тобі."

**Paronyms:** None found.

**Russian characters (ы, э, ё, ъ):** None found.

**Case forms verified:**
- "по місту", "по стадіону", "по лісу", "по небу", "по світу" — all confirmed as valid Locative forms via VESUM (e.g., `місту → noun:inanim:n:v_mis`, `стадіону → noun:inanim:m:v_mis`, `лісу → noun:inanim:m:v_mis`, `небу → noun:inanim:n:v_mis`, `світу → noun:inanim:m:v_mis`). The -у Locative is a legitimate parallel form in modern Ukrainian.
- "великого сусідського собаки" — "собака" confirmed as both m/f in VESUM; masculine adjective agreement with Gen. masc. = correct.

**One pedagogical inconsistency (not a linguistic error but a teaching accuracy issue):**
The Dative section states: "Чоловічий рід найчастіше отримує довгі закінчення «-ові» або «-еві»" — then immediately gives "Студент щиро дякує новому **вчителю**" with the short -ю ending, contradicting the rule just stated. VESUM confirms both "вчителю" (`v_dav`) and "вчителеві" (`v_dav`) are valid, but the example should match the stated rule to avoid confusing A2 learners.

## Exercise Check

Four `<!-- INJECT_ACTIVITY -->` markers found:

| # | Marker | Placement | Plan Match |
|---|--------|-----------|------------|
| 1 | `quiz` — correct case form by verb | After Section 1 (verbs) ✓ | Matches `activity_hints[0]`: quiz, 8 items ✓ |
| 2 | `group-sort` — prepositions by case | After Section 2 (prepositions) ✓ | Matches `activity_hints[1]`: group-sort, 8 items ✓ |
| 3 | `fill-in` — mixed cases (time, clothing, path) | After Section 3 (special cases) ✓ | Matches `activity_hints[2]`: fill-in, 8 items ✓ |
| 4 | `true-false` — judge case correctness | After Section 4 (algorithm) ✓ | Matches `activity_hints[3]`: true-false, 8 items ✓ |

All markers placed after the relevant teaching section. Even distribution across the module. All 4 plan activity hints are represented.

## Scores

| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | All 4 `content_outline` sections present and substantively covered. Section 1 covers Acc/Dat/Instr/Gen verbs + "думати про + Acc" as planned. Section 2 covers all 5 preposition pairs (на, у/в, по, з, за) with dual-case examples. Section 3 covers time expressions, clothing descriptions, and path with по. Section 4 presents the 3-step algorithm with common pitfalls. Minor gaps: plan examples "у четвер" and "Цю неділю я відпочиваю" are not in the text (covered conceptually but specific examples absent). Word count 2856 > 2000 target ✓. Individual section budgets all exceeded (good — targets are minimums). |
| 2. Linguistic accuracy | 10/10 | All 724 Ukrainian words verified in VESUM. No Russianisms, surzhyk, or calques. Case forms verified: "по місту/стадіону/лісу" confirmed as valid Locative (VESUM `v_mis`). "Дякувати + Dative" confirmed by Антоненко-Давидович. Correct animate/inanimate Accusative distinction taught. "Думати про + Acc" correctly identified. |
| 3. Pedagogical quality | 9/10 | Strong PPP flow: each case group introduced with concept → multiple examples → practice. 3+ examples per grammar point consistently (e.g., Acc verbs: бачити, знати, любити, читати, купити, шукати). Animate/inanimate distinction well-explained with examples. One issue: Dative section states -ові/-еві are "найчастіше" but second example uses -ю ("вчителю"), contradicting the stated rule — pedagogically confusing at A2. |
| 4. Vocabulary coverage | 10/10 | All 10 required vocab items used naturally in prose: відмінок (throughout), прийменник (throughout), дієслово (throughout), напрямок (§2: "це активна дія, яка має конкретну ціль" + §4: "Це напрямок"), місце (§2, §4), час (§3), характеристика (§3: "характеристика"), думати (§1), боятися (§1), користуватися (§1). Recommended: алгоритм (§4), керувати (§1), майбутнє (§1) all present. Only "контекст" (recommended) absent from prose — acceptable. |
| 5. Exercise quality | 9/10 | All 4 plan activity types present with correct focus. Markers well-placed after the relevant teaching content. Each exercise tests language skill (case selection), not content recall. Item counts match plan (8 each). |
| 6. Engagement & tone | 8/10 | Good: "граматичний компас" metaphor is concrete and carried through; "граматичний детектив" dialogue is engaging; self-check questions in Підсумок are practical. Deductions: Several generic filler phrases — "Ще один дуже цікавий прийменник — це «з»" (§2), "Час — це дуже важливий елемент у нашій мові" (§3), "Це дуже просте і важливе правило" (§2) — these tell rather than show. Some "Запам'ятайте" imperatives are textbook-formulaic. |
| 7. Structural integrity | 10/10 | Clean markdown. All 4 plan sections present as H2 headings in correct order, plus a natural Підсумок. No duplicate sections, no meta-commentary sections, no stray tags. Word count 2856 well within range (target 2000, minimum met). |
| 8. Cultural accuracy | 10/10 | Decolonized: Ukrainian presented on its own terms, never compared to Russian. Революція Гідності mentioned naturally ("У 2014 році в Україні відбулася Революція Гідності"). Examples use Ukrainian cities (Одеса, Київ), Ukrainian cultural details (подорожувати по Україні, українські села). No Russian-centric framing. |
| 9. Dialogue quality | 9/10 | Two dialogues with named speakers. Dialogue 1 (Вчитель/Олена): natural grammar detective game matching plan's `dialogue_situations` — reads a newspaper and identifies cases. Good back-and-forth. Dialogue 2 (Марк/Ірина): students discussing grammar questions — natural multi-turn exchange where confusion is resolved. Both culturally appropriate. Minor: Dialogue 2 speakers not from plan (plan specifies Вчитель/Студенти only), but adds pedagogical value. |

## Findings

**[PEDAGOGICAL QUALITY] [MAJOR]**
Location: Section 1 (Dative verbs), paragraph: "Зверніть особливу увагу на типові закінчення. Чоловічий рід найчастіше отримує довгі закінчення «-ові» або «-еві». Наприклад: [...] «Студент щиро дякує новому вчителю»"
Issue: The text states masculine Dative nouns "найчастіше" (most often) receive long endings -ові/-еві, but the second example "вчителю" uses the short -ю ending, directly contradicting the rule just taught. At A2 level, examples must reinforce the stated pattern — mixed forms without explanation create confusion. VESUM confirms both "вчителю" and "вчителеві" are valid Dative forms.
Fix: Change "вчителю" to "вчителеві" in the example to match the stated rule.

**[ENGAGEMENT & TONE] [MINOR]**
Location: Section 2, paragraph 1: "Запам'ятайте дуже просте і важливе правило: активний рух — це Знахідний відмінок, а статика — це Місцевий відмінок."
Issue: "дуже просте і важливе правило" is telling rather than showing — the examples already demonstrate the rule clearly.
Fix: Remove the evaluative filler, keep the rule statement direct.

**[ENGAGEMENT & TONE] [MINOR]**
Location: Section 2, paragraph 2 opener: "Ще один дуже цікавий прийменник — це «з»."
Issue: Generic "дуже цікавий" filler. The preposition is interesting because of its dual function, not because the author says so.
Fix: Replace with a direct functional statement.

**[ENGAGEMENT & TONE] [MINOR]**
Location: Section 3, paragraph 1 opener: "Час — це дуже важливий елемент у нашій мові."
Issue: Generic opener that could apply to any language. The section should dive directly into the time expression rules.
Fix: Replace with a more specific lead-in.

## Verdict: REVISE

One major finding (Dative pedagogical inconsistency) and three minor engagement fixes. No linguistic errors — all forms verified correct. The module is strong overall (all dimensions ≥ 8, most ≥ 9) but the Dative teaching inconsistency must be fixed before shipping because learners will memorize the wrong pattern association.

<fixes>
- find: "«Студент щиро дякує новому вчителю»"
  replace: "«Студент щиро дякує новому вчителеві»"
- find: "*(A student sincerely thanks a new teacher)*."
  replace: "*(A student sincerely thanks a new teacher)*. Також є коротке закінчення «-у»/«-ю»: «дякує вчителю», але довга форма звучить більш офіційно і вважається стилістично кращою."
- find: "Запам'ятайте дуже просте і важливе правило: активний рух — це Знахідний відмінок, а статика — це Місцевий відмінок."
  replace: "Отже, активний рух — це Знахідний відмінок, а статика — це Місцевий відмінок."
- find: "Ще один дуже цікавий прийменник — це «з»."
  replace: "Прийменник «з» також має дві абсолютно різні функції."
- find: "Час — це дуже важливий елемент у нашій мові."
  replace: "Час в українській мові має свої особливі правила для відмінків."
</fixes>
