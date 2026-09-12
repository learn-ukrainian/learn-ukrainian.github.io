# Pilot Notes: a1-008 «Речі мають рід» (Phase 0 Lesson Split)

## 1. Structure and Allocation
Module A1-008 is split into three 60-minute lessons under the parallel level `a1-v2`:
- **Lesson 1: Він, вона́ чи воно́?** (60 min)
  - Mapped baseline sections: Pre-section introduction + «Діалоги» + «Він, вона, воно».
  - Content: Concept of grammatical gender, question words *Хто це?* / *Що це?*, the *він / вона́ / воно́* test, noun endings (consonant, -а/-я, -о/-е), first possessives *мій / моя́ / моє́*.
  - Prose tokens: ~890 (clean, comments excluded).
  - Activities: 4 inline (`act-1`, `act-2`, `act-5`, `act-3`), 6 workbook (`act-w1`, `act-101`, `act-102`, `act-103`, `act-104`, `act-105`), total 10.
  - Vocabulary: 16 lemmas.
- **Lesson 2: Предме́ти навко́ло** (60 min)
  - Mapped baseline sections: «Предмети навколо».
  - Content: Everyday items in the room and bag, construction *У ме́не є...* / *У те́бе є...?*, noun gender governing pronoun replacement (*Де стіл? Він тут*).
  - Prose tokens: ~590 (clean).
  - Activities: 4 inline (`act-4`, `act-201`, `act-202`, `act-203`), 6 workbook (`act-w2`, `act-w3`, `act-204`, `act-205`, `act-206`, `act-207`), total 10.
  - Vocabulary: 16 lemmas.
- **Lesson 3: Профе́сії, па́стки й самопереві́рка** (60 min)
  - Mapped baseline sections: «Підсумок» + «Імена, пастки й самоперевірка». Closes the module!
  - Content: Feminitive profession forms as default for women (*вчи́телька, лі́карка*), male names and family words ending in -а/-о (*Мико́ла, Ілля́, Павло́, та́то, дя́дько*), high-value exception *соба́ка*, 5-point gender diagnostic (*біль, степ, ро́зпис, лі́топис, путь*), and module self-check.
  - Prose tokens: ~730 (clean).
  - Activities: 4 inline (`act-9`, `act-301`, `act-302`, `act-303`), 6 workbook (`act-w4`, `act-w5`, `act-304`, `act-305`, `act-306`, `act-307`), total 10.
  - Vocabulary: 16 lemmas.

Total prose tokens: ~2,210 (>= 2,000 threshold).

## 2. Prose Preservation Verification
All 47 original baseline paragraphs with >= 8 words are preserved verbatim in their mapped lessons (modulo stress marks added to multi-syllable Ukrainian words). No original text was cut or paraphrased.
- Lesson 1: 15 original paragraphs.
- Lesson 2: 13 original paragraphs.
- Lesson 3: 19 original paragraphs.
Total = 47 original paragraphs preserved.

## 3. Vocabulary Distribution
The 48 baseline lemmas are cleanly partitioned across the 3 lessons (16 entries each) by order of thematic introduction. The module union is identical to the baseline 48 lemmas with zero additions or deletions.
- Lesson 1 (16): *рід, іменник, хто це?, що це?, він, вона, воно, мій, моя, моє, стіл, книга, вікно, місто, тато, батько*.
- Lesson 2 (16): *у мене є, у тебе є, кімната, ліжко, стілець, лампа, телефон, комп'ютер, зошит, ручка, сумка, крісло, дзеркало, ключ, фото, стіна*.
- Lesson 3 (16): *дядько, собака, студент, студентка, вчитель, вчителька, учителька, лікар, лікарка, актор, акторка, співак, співачка, Микола, Ілля, Павло*.

## 4. Activities and Provenance
All 11 baseline activities are preserved structurally:
- Inline: `act-1` (L1), `act-2` (L1), `act-3` (L1), `act-5` (L1), `act-4` (L2), `act-9` (L3).
- Workbook: `act-w1` (L1), `act-w2` (L2), `act-w3` (L2), `act-w4` (L3), `act-w5` (L3).
All new activities adhere to the A1 allowlist and presentation standards:
- Ukrainian-only prompts and options for comprehension/recall.
- English -> Ukrainian translation included strictly in workbook as bonus.
- All activities carry >= 6 items, with exactly two allowed exemptions:
  - `act-9`: 4 items (profession-form quiz from baseline).
  - `act-w5`: 5 items (gender diagnostic from baseline / plan).

## 5. Language Verification Outcomes
1. **VESUM Word Verification (`verify_word`)**:
   - Every lemma and inflected Ukrainian token is verified in VESUM.
   - Unverified lemmas: 0 (limit <= 5 per lesson).
2. **Stress Verification (`verify_stress`)**:
   - Every multi-syllable Ukrainian form in prose, activities, and vocabulary carries a combining acute accent (U+0301).
   - Orchestrator batch re-verification (2026-09-12, `scripts.verification.stress`) found and corrected 29 forms the writer had marked wrongly (e.g. *ме́не → мене́*, *диви́мося → ди́вимося*, *Лі́топис → літо́пис*, *твер́дження → тве́рдження*). Writer-side stress claims were not tool-backed; the checker now re-verifies every stressed form.
   - Not in the stress dictionary (listed per lesson in `lessons.yaml: unverified_stress`, left as written): *уро́ці* (loc. of *уро́к*), *фемініти́ви / фемініти́вом / фемініти́вами* (*фемініти́в*, stress per Правопис/СУМ-20 usage).
3. **Russian Shadow & Morphology (`is_russian_pattern`)**:
   - All standard vocabulary clear of Russian shadow.
   - Proper nouns (`Микола`, `Ілля`, `Павло`, `Оксана`) from baseline curriculum are whitelisted as standard Ukrainian personal names.
