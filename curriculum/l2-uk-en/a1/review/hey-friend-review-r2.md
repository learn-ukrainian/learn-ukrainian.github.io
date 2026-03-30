Now I have comprehensive verification data. Let me compile the full review.

---

## Linguistic Scan

**Russianisms:** None found. All vocabulary is standard Ukrainian.
**Surzhyk:** None found.
**Calques:** None found. "Радий бачити" — style guide (Антоненко-Давидович) did not flag this expression.
**Paronyms:** None found.
**Russian characters (ы, э, ё, ъ):** None found.

**All vocative forms verified correct against VESUM:**
- друже ✓ (from друг), козаче ✓ (from козак), синку ✓ (from синок), дочко ✓ (from дочка), дідусю ✓ (from дідусь), бабусю ✓ (from бабуся), подруго ✓ (from подруга), сестро ✓ (from сестра), пане ✓ (from пан), вчителю ✓ (from вчитель), брате ✓ (from брат), мамо ✓ (from мама), тату ✓ (from тато, VESUM tag `v_kly`)
- All "NOT IN VESUM" items are proper nouns (Олена, Тарас, Андрій, etc.) — expected, VESUM excludes proper names.

**пані as невідмінюване:** Confirmed. VESUM shows all 14 forms as `пані` with `nv` (non-declinable) tag. Module's claim is correct.

**Factual errors found:**

1. **Wrong textbook attribution.** Module states: "As Litvinova's Grade 6 textbook notes, forms like **Насте** and **Катре** also exist." RAG search confirms this information comes from **Avramenko's** Grade 6 textbook (§54): "бабусю, Галю, АЛЕ: Насте, Катре." Litvinova's vocative section (§28) does not mention Насте/Катре in available chunks. The separate reference to "From Litvinova Grade 6: **пан Євген** → **пане Євгене**" IS correctly attributed (confirmed in Litvinova §28, s0148).

2. **тато → тату misclassified.** The module places тато → тату inside the "Masculine: soft consonant / -й → -ю" section and groups it with -ю endings in the summary table. But тато ends in -о (a vowel, not a soft consonant or -й), and its vocative тату has the ending **-у**, not **-ю**. VESUM confirms: `тату | noun:anim:m:v_kly`. This will confuse A1 learners who see the section heading says "-ю" but the example has "-у."

## Exercise Check

**Markers found (4):**
1. `<!-- INJECT_ACTIVITY: quiz-vocative -->` — after "Кличний відмінок" section ✅ (tests vocative recognition after explanation)
2. `<!-- INJECT_ACTIVITY: fill-in-vocative -->` — after "Закінчення кличного" section ✅ (tests pattern application after teaching endings)
3. `<!-- INJECT_ACTIVITY: group-sort-vocative -->` — after "Закінчення кличного" section ✅ (tests classification after all patterns taught)
4. `<!-- INJECT_ACTIVITY: quiz-choose-vocative -->` — at end of "Підсумок" section ✅ (final review)

**Plan has 4 activity_hints:** fill-in, quiz, group-sort, fill-in (dialogue). Module has 4 markers. Types map reasonably: quiz-vocative ↔ quiz, fill-in-vocative ↔ fill-in, group-sort-vocative ↔ group-sort. The 4th marker is `quiz-choose-vocative` but the plan's 4th hint is a fill-in (dialogue completion) — minor mismatch in type, but the ACTIVITIES step generates from plan hints, so this won't cause issues.

**Marker placement:** Well-distributed — one after section 2, two after section 3 (where all patterns are taught), one at the end. Not clustered. ✅

**Inline exercise:** The self-check at the end ("мама → ___, тато → ___...") with answers is a nice inline practice. Correct answers provided. ✅

## Scores

| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | All 4 content_outline sections present and ordered correctly. Both dialogue situations from plan covered (birthday party in Dialogue 1; family at home in Dialogue 2). All vocabulary_hints required words appear in prose: друг (друже), подруга (подруго), брат (брате), сестра (сестро), пан (пане), пані (explained as невідмінюване). All recommended words present: синку, дочко, козак (козаче), вчитель (вчителю), бабуся (бабусю), дідусь (дідусю). Grammar points from plan fully covered. Minor deduction: 4th activity marker type (quiz) doesn't match plan's 4th hint (fill-in dialogue). |
| 2. Linguistic accuracy | 9/10 | All vocative forms VESUM-verified correct. No Russianisms, Surzhyk, or calques. Gender/case usage correct throughout. One factual error: wrong textbook attribution — Насте/Катре forms attributed to "Litvinova's Grade 6" but confirmed from Avramenko §54. The separate Litvinova reference (пан Євген → пане Євгене) IS correct. |
| 3. Pedagogical quality | 8/10 | Strong PPP flow: dialogues present the pattern in context → explanation section builds conceptual understanding → endings section provides systematic rules → summary consolidates. Grade 4 helper word Кл.(!) referenced. 3+ examples per pattern. However, тато → тату is placed inside the "soft consonant / -й → -ю" section despite тато having neither a soft consonant nor -й ending. The module calls it "exceptional" but placing it IN this section suggests it belongs to the -ю pattern, which it doesn't (ending is -у). At A1, this classification error will confuse learners trying to apply the pattern. Should be a standalone exception or moved to a separate note. |
| 4. Vocabulary coverage | 10/10 | All 6 required vocabulary items from plan used naturally in prose within dialogues and explanations. All 6 recommended items present and contextualized. New words introduced through dialogue first, then systematized — не as bare lists. |
| 5. Exercise quality | 9/10 | 4 markers matching 4 plan hints. Good placement: quiz after concept introduction, fill-in and group-sort after pattern teaching, final quiz at summary. Self-check exercise at end is well-designed. Minor: 4th marker type mismatch with plan. |
| 6. Engagement & tone | 10/10 | No motivational openers, no meta-commentary, no filler. Cultural framing is specific: "the vocative is one of the ways Ukrainian encodes human connection directly into grammar" — this is concrete and unique to Ukrainian, not generic. Birthday party scenario is lively. Family scene is natural. The nominative-as-address analogy ("like saying 'Hey, him!'") is imperfect but pedagogically effective at A1. |
| 7. Structural integrity | 10/10 | All 4 H2 headings match plan sections. Clean markdown. Word count 1239 ≥ 1200 target. No stray tags, no formatting artifacts. Activity markers properly placed as HTML comments. |
| 8. Cultural accuracy | 10/10 | Ukrainian vocative presented as a living, vibrant feature ("You hear it everywhere"), not as archaic or formal. No "like Russian but..." framing. Vocative correctly described as mandatory in everyday speech. Cultural connection: "every time you address someone, the language itself changes shape to acknowledge that relationship." |
| 9. Dialogue quality | 10/10 | Dialogue 1: natural multi-turn greeting + introduction scenario with named speakers (Тарас, Олена, Андрій). Dialogue 2: realistic family scene with named speakers (Марко, Оля) — searching for phone, keys, saying goodbye. Both dialogues have culturally appropriate responses. Not transactional interrogation. Plan's speakers (Іменинник, Друзі) mapped to concrete characters. |

## Findings

**[Dim 2: Linguistic accuracy] [SEVERITY: major]**
Location: Section "Закінчення кличного", paragraph "Feminine exceptions: soft and mixed groups" — "As Litvinova's Grade 6 textbook notes, forms like **Насте** and **Катре** also exist"
Issue: Wrong textbook attribution. RAG search confirms Насте/Катре forms come from Avramenko's Grade 6 textbook (§54: "бабусю, Галю, АЛЕ: Насте, Катре"), not Litvinova's. The separate Litvinova reference for пан Євген → пане Євгене is correct.
Fix: Change "Litvinova's" to "Avramenko's" in this specific sentence.

**[Dim 3: Pedagogical quality] [SEVERITY: major]**
Location: Section "Закінчення кличного", subsection "Masculine: soft consonant / -й → -ю" — "One exception to memorize: **тато** → **тату** — an exceptional **-у** ending, listed alongside **сину** and **діду** in textbooks."
Issue: тато → тату is placed inside the "soft consonant / -й → -ю" section, but тато ends in -о (a vowel), not a soft consonant or -й. The vocative ending is -у, not -ю. Placing this exception inside the -ю section implies it follows that pattern. At A1, learners will be confused about WHY тато is here and may incorrectly conclude тато has a soft stem.
Fix: Move тато → тату out of the -ю section. Place it as a standalone note after the consonant alternation paragraph (end of the Закінчення section), clearly labeled as an exception.

**[Dim 3: Pedagogical quality] [SEVERITY: major]**
Location: Section "Підсумок — Summary", table row "Masculine **-й**/soft | + **-ю** | **Андрій** → **Андрію**, **вчитель** → **вчителю**, **тато** → **тату**"
Issue: тато → тату grouped with -ю endings in the summary table, but тату has ending -у, not -ю. This contradicts the column header "+ **-ю**" and will confuse learners referencing this table.
Fix: Remove тато → тату from the -ю row. Add a separate "Exceptions" row: **тато** → **тату** (memorize).

## Verdict: REVISE

Two major findings require fixes: the wrong textbook attribution (factual error) and the тато → тату misclassification (pedagogical confusion at A1). Neither is critical (no wrong Ukrainian forms are taught), but both fall below the quality standard. All fixes are surgical — no rebuild needed.

<fixes>
- find: "As Litvinova's Grade 6 textbook notes, forms like **Насте** and **Катре** also exist, but **бабусю** and **Настусю** are the standard affectionate forms you will use most."
  replace: "As Avramenko's Grade 6 textbook notes, forms like **Насте** and **Катре** also exist, but **бабусю** and **Настусю** are the standard affectionate forms you will use most."
- find: "One exception to memorize: **тато** → **тату** — an exceptional **-у** ending, listed alongside **сину** and **діду** in textbooks.\nTwo consonant alternations"
  replace: "Two consonant alternations"
- find: "These follow standard Ukrainian phonetic patterns — the back consonant softens before **-е**."
  replace: "These follow standard Ukrainian phonetic patterns — the back consonant softens before **-е**.\nOne more form to memorize: **тато** → **тату**. This is an exception — тато doesn't fit neatly into either the -е or -ю pattern. The vocative ending is **-у**, and it simply needs to be learned as a special case alongside **син** → **сину** and **дід** → **діду**."
- find: "| Masculine **-й**/soft | + **-ю** | **Андрій** → **Андрію**, **вчитель** → **вчителю**, **тато** → **тату** |"
  replace: "| Masculine **-й**/soft | + **-ю** | **Андрій** → **Андрію**, **вчитель** → **вчителю** |\n| Exceptions | memorize | **тато** → **тату**, **син** → **сину**, **дід** → **діду** |"
</fixes>
