I now have all the evidence needed. Let me compile the full review.

---

## Linguistic Scan

**1. Intonation contradiction — "як" omitted from question words, then used with wrong intonation:**

The module teaches: "Words like **хто** (who), **що** (what), **де** (where), **коли́** (when) carry the interrogative meaning themselves — they signal 'this is a question' without any rise in your voice." However, **як** (how) is omitted from this list — Grade 2 textbook (Кравцова, p.108) explicitly lists як among question words: "Коли? Де? Як? Скільки? Чому?"

The module then violates its own rule twice:
- Reading Aloud dialogue: "Як спра́ви? ↗" — marked rising, but як is a question word → should fall ↘
- Summary: "Як тебе звати? ↗ — a question with rising intonation" — same violation

**2. Factual error — "the second а" in фотографія:**

The word фотографія contains exactly ONE letter а (ф-о-т-о-г-р-**а**-ф-і-я). The module says "stress on the third syllable, the second а" (Section 1) and "stress on the second **а**" (Section 3). There is no "second а" — this is a factual error that will confuse learners trying to find a vowel that doesn't exist.

**3. No Russianisms, surzhyk, calques, or Russian characters found.** All Ukrainian words verified against VESUM (74/74 confirmed; the 52 "not found" entries are fragments from stress-marked words split by the tokenizer — e.g., "Інтона" from "Інтона́ція", proper nouns like "Кирилко", "Соломійка", "Тарас"). No issues.

## Exercise Check

Four activity markers present:
1. `<!-- INJECT_ACTIVITY: quiz-stress-syllable -->` — after Наголос section ✓ (matches plan hint 1: quiz, stress syllable)
2. `<!-- INJECT_ACTIVITY: match-stress-pairs -->` — after Наголос section ✓ (matches plan hint 2: match-up, stress pairs)
3. `<!-- INJECT_ACTIVITY: quiz-sentence-type -->` — after Інтонація section ✓ (matches plan hint 3: quiz, sentence type)
4. `<!-- INJECT_ACTIVITY: fill-in-punctuation -->` — after Інтонація section ✓ (matches plan hint 4: fill-in, punctuation)

All 4 markers match plan's `activity_hints` in type and focus. Placement is correct — each follows its teaching section. Spread is even (2 after Section 1, 2 after Section 2). No exercises appear before concepts are taught.

## Scores

| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | All 4 content_outline sections present with correct ordering. All plan points covered: stress pairs (замок, мука, атлас), intonation patterns (↘ ↗ ↘↘), sentence types (розповідні, питальні, спонукальні + окличні as separate dimension), 3-step reading method, self-check questions. Both textbook references cited (Заболотний p.73 — confirmed via RAG; Авраменко p.19 intonation content confirmed). ULP reference not cited (minor). Word count 1782 vs 1200 target — well above minimum. Deduction: фотографія description ("the second а") deviates from plan's "third а" (plan also wrong, but module made it worse by saying "second"). |
| 2. Linguistic accuracy | 7/10 | Two factual errors. (1) "Як справи? ↗" and "Як тебе звати? ↗" contradict the module's own rule that question-word questions use falling intonation. "Як" is a standard question word (confirmed: Grade 2 Кравцова p.108 lists як among питальні слова). This teaches learners contradictory rules. (2) "the second а" in фотографія — the word has only one а. Both errors are in phonetics content that learners will memorize. All other Ukrainian is correct: grammar terminology verified (розповідні, питальні, спонукальні, окличні all confirmed VESUM), stress pairs are legitimate, sentence type classification matches textbooks. |
| 3. Pedagogical quality | 9/10 | Strong PPP flow: situation (say "наголос" aloud → feel the stress) → pattern (stress is free, changes meaning) → practice (read aloud with 3-step method). Multiple examples per concept: 5 first-syllable words, 5 last-syllable words, 3 stress pairs, 3 intonation patterns. Textbook pedagogy followed: syllable-breaking method matches Grade 1 approach. The 3-step reading method (поділ → наголос → читай разом) is well-structured. Deduction only for the intonation contradiction which undermines the pedagogy of that specific rule. |
| 4. Vocabulary coverage | 10/10 | All required vocab: наголос ✓ (metalanguage, explained in opening), замок castle ✓, замок lock ✓, кава ✓, вода ✓, столиця ✓ ("Київ — столиця України" in Reading Aloud). All recommended vocab: мука ✓ (stress pair), ранок ✓, метро ✓ (in dialogue), фотографія ✓. All introduced in context, not as lists. столиця confirmed A1 by PULS CEFR. |
| 5. Exercise quality | 9/10 | All 4 plan activity_hints have corresponding markers. Placement is pedagogically correct (after teaching, not before). Types match exactly (quiz, match-up, quiz, fill-in). Cannot fully evaluate exercise content since YAML is generated separately, but marker IDs clearly map to plan focus areas. |
| 6. Engagement & tone | 9/10 | No motivational openers or generic enthusiasm. The Білоус riddle about замок is a nice cultural touch. The identity paragraph about Київ stress is powerful and specific ("Getting stress right is not just grammar — it is an act of respect"). Practical tip about tapping the table while reading is concrete and actionable. Named speakers in dialogues (Кирилко, Соломійка, Оленка, Тарас). The :::tip block is well-placed. Minor: the identity paragraph could be seen as slightly lecturing, but it's specific enough to earn its place. |
| 7. Structural integrity | 10/10 | All H2 headings from plan present and correctly ordered: Наголос → Інтонація → Читаємо вголос → Підсумок. Clean markdown throughout. Word count 1782 above 1200 target. No duplicate sections, no meta-commentary, no stray tags. |
| 8. Cultural accuracy | 10/10 | Decolonized throughout — Ukrainian presented on its own terms. The Київ/українська stress paragraph frames stress as identity without reference to Russian as a baseline. No "like Russian but..." framing anywhere. Factually correct: Ukrainian stress is free (confirmed Golub Grade 5 p.70, Zaболотний p.73, Litvinova p.166). Sentence classification matches all three textbooks consulted. |
| 9. Dialogue & conversation quality | 9/10 | Two dialogues with named speakers. The Кирилко/Соломійка metro dialogue is natural — two friends near a station, one asks directions, short and functional. Models all three intonation patterns organically. The Оленка/Тарас greeting dialogue recycles M01 greetings with intonation overlay — good spiral pedagogy. Deduction: "Як справи? ↗" is marked wrong per the module's own rules (critical issue scored under linguistic accuracy, but it slightly hurts dialogue quality too since the dialogue is meant to MODEL correct intonation). |

## Findings

**[LINGUISTIC ACCURACY] [CRITICAL]**
Location: Section "Інтонація" — question word list, then Section "Читаємо вголос" dialogue, then "Підсумок"
Issue: The module teaches that question words (хто, що, де, коли) use falling intonation, but omits **як** from the list. It then marks "Як справи? ↗" (Reading Aloud dialogue) and "Як тебе звати? ↗" (Summary) with rising intonation — directly contradicting the rule. Grade 2 textbook (Кравцова p.108) lists як as a standard question word. A learner following this module would learn the rule, then see it violated in practice examples, causing confusion.
Fix: (1) Add як to the question word list. (2) Change both "Як справи?" and "Як тебе звати?" to falling intonation ↘. (3) Update the Summary explanation.

**[LINGUISTIC ACCURACY] [CRITICAL]**
Location: Section "Наголос" paragraph 1 — "stress on the third syllable, the second а"; Section "Читаємо вголос" — "stress on the second **а**"
Issue: The word фотографія (ф-о-т-о-г-р-а-ф-і-я) contains exactly one letter "а". Saying "the second а" is factually wrong — there is no second а to find. A learner scanning the word for "the second а" will be confused.
Fix: Change both occurrences to refer to "the а" without a numeral.

**[PLAN ADHERENCE] [MINOR]**
Location: Section "Наголос" paragraph 4 — "One more powerful pair from Авраменко's Grade 5 textbook: ніколи vs ніколи"
Issue: The plan's Авраменко reference (p.19) covers sentence intonation types, not stress pairs. The ніколи/ніколи stress pair is real and well-attested, but its attribution to Авраменко Grade 5 could not be verified via textbook RAG search. [NEEDS VERIFICATION]
Fix: No fix required if attribution is correct. If unverifiable, soften to "A well-known pair in Ukrainian:" without the Авраменко attribution.

## Verdict: REVISE

Two critical findings: (1) the intonation contradiction where "як" is omitted from question words and then two examples violate the module's own rule, and (2) the "second а" error in фотографія that references a letter that doesn't exist. Both are phonetics errors that learners will memorize as truth. Fixes below are targeted — no rewrite needed.

<fixes>
- find: "Words like **хто** (who), **що** (what), **де** (where), **коли́** (when) carry the interrogative meaning themselves"
  replace: "Words like **хто** (who), **що** (what), **де** (where), **як** (how), **коли́** (when) carry the interrogative meaning themselves"

- find: "**Що це?** ↘ — falling intonation. The word **що** already tells the listener you are asking about identity. **Де метро?** ↘ — falling. The word **де** signals a question about location. **Коли авто́бус?** ↘ — falling again."
  replace: "**Що це?** ↘ — falling intonation. The word **що** already tells the listener you are asking about identity. **Де метро?** ↘ — falling. The word **де** signals a question about location. **Як справи?** ↘ — falling. The word **як** signals a question about manner. **Коли авто́бус?** ↘ — falling again."

- find: "**Фотогра́фія** (photograph) — stress on the third syllable, the second а."
  replace: "**Фотогра́фія** (photograph) — stress on the third syllable, on the а."

- find: "— **Тара́с:** Привіт! Як спра́ви? ↗ *(Hi! How are you?)*"
  replace: "— **Тара́с:** Привіт! Як спра́ви? ↘ *(Hi! How are you?)*"

- find: "— **Оленка:** До́бре! А у тебе́? ↗ *(Good! And you?)*"
  replace: "— **Оле́нка:** До́бре! А у те́бе? ↗ *(Good! And you?)*"

- find: "- **фо-то-гра-фі-я** (photograph) — stress on the second **а**. Slow: фо... то... гра... фі... я. Now together: **фотографія**."
  replace: "- **фо-то-гра-фі-я** (photograph) — stress on the **а** (third syllable). Slow: фо... то... гра... фі... я. Now together: **фотогра́фія**."

- find: "**Як тебе звати?** ↗ — a question with rising intonation."
  replace: "**Як тебе звати?** ↘ — a question with falling intonation (the question word **як** signals the question)."
</fixes>
