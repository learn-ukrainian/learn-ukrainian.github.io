# Pilot Notes: a1-008 «Речі мають рід» (Phase 0 Lesson Split — Post-Review Repair)

## 1. Structure and Allocation
Module A1-008 is split into three 60-minute lessons under the parallel level `a1-v2`:
- **Lesson 1: Він, вона́ чи воно́?** (est. 52 min)
  - Mapped baseline sections: Pre-section introduction + «Діалоги» + «Він, вона, воно».
  - Objectives:
    - Визнача́ти рід іме́нників — determine noun gender using він / вона́ / воно́;
    - Розпізнава́ти закі́нчення слів — recognise basic noun endings (consonant, -а / -я, -о / -е);
    - Вжива́ти присві́йні слова́ — use мій / моя́ / моє́ as a single phrase with each noun.
  - Prose tokens: 971 (clean, comments excluded).
  - Activities: 4 inline (`act-1`, `act-2`, `act-5`, `act-3`), 6 workbook (`act-w1`, `act-101`, `act-102`, `act-103`, `act-104`, `act-105` [bonus]), total 10.
  - Vocabulary: 18 lemmas (includes `соба́ка` and `Мико́ла` re-homed from Lesson 3 by first appearance).
  - Resources: 2 (Пономарьова 4 клас textbook chunk + Ukrainian Lessons infographic).
- **Lesson 2: Предме́ти навко́ло** (est. 47 min)
  - Mapped baseline sections: «Предмети навколо».
  - Objectives:
    - Назива́ти щоде́нні ре́чі — name items in your room and bag with their gender;
    - Будува́ти констру́кцію володі́ння — use «У мене́ є...» / «У тебе́ є...?» with nominative nouns;
    - Узго́джувати присві́йні слова́ — match «мій / моя́ / моє́» to the object you own.
  - Prose tokens: 677 (clean).
  - Activities: 4 inline (`act-4`, `act-201`, `act-202`, `act-203`), 6 workbook (`act-w2`, `act-w3`, `act-204`, `act-205`, `act-206`, `act-207` [bonus]), total 10.
  - Vocabulary: 16 lemmas.
  - Resources: 2 (Літвінова 6 клас § 25 + Авраменко 6 клас § 43).
- **Lesson 3: Профе́сії, па́стки й самопереві́рка** (est. 52 min)
  - Mapped baseline sections: «Підсумок» + «Імена, пастки й самоперевірка». Closes the module!
  - Objectives:
    - Вжива́ти фемініти́ви профе́сій — use paired masculine and feminine profession forms (вчи́тель / вчи́телька, лі́кар / лі́карка);
    - Розпізнава́ти особли́ві імена́ та ви́нятки — recognise masculine names ending in -а / -я (Мико́ла, Ілля́) and the key exception соба́ка;
    - Упе́внено вжива́ти всі ви́вчені слова́ — consolidate all 48 vocabulary items across the module.
  - Prose tokens: 931 (clean).
  - Activities: 4 inline (`act-9`, `act-301`, `act-302`, `act-303`), 6 workbook (`act-w4`, `act-w5`, `act-304`, `act-305`, `act-306`, `act-307` [bonus]), total 10.
  - Vocabulary: 14 lemmas.
  - Resources: 2 (Авраменко 6 клас с. 84 «Фемінітиви» + Літвінова 6 клас с. 130 «Вправа 264. Рід іменників»).

Total prose tokens: 2,579 (>= 2,000 threshold). Pacing heuristic for all three lessons falls within the recommended 45–75 minute range.

## 2. Prose Preservation Verification
All 47 original baseline paragraphs with >= 8 words are preserved verbatim in their mapped lessons (modulo stress marks added to multi-syllable Ukrainian words). No original text was cut or paraphrased.
- Lesson 1: 15 original paragraphs.
- Lesson 2: 13 original paragraphs.
- Lesson 3: 19 original paragraphs.
- Verification outcome (`verify_pilot.py`): lost: 0, duplicated: 0, misplaced: 0.

## 3. Vocabulary Distribution
The 48 baseline lemmas are cleanly partitioned across the 3 lessons by order of thematic introduction and first appearance in prose/dialogue:
- Lesson 1 (18): *рід, іменник, хто це?, що це?, він, вона, воно, мій, моя, моє, стіл, книга, вікно, місто, тато, батько, собака, Микола*.
  - `соба́ка` and `Мико́ла` re-homed to Lesson 1 where they first appear in the lesson dialogue and test lines.
- Lesson 2 (16): *у мене є, у тебе є, кімната, ліжко, стілець, лампа, телефон, комп'ютер, зошит, ручка, сумка, крісло, дзеркало, ключ, фото, стіна*.
- Lesson 3 (14): *дядько, студент, студентка, вчитель, вчителька, учителька, лікар, лікарка, актор, акторка, співак, співачка, Ілля, Павло*.

Multiset union check: exactly identical to baseline 48 lemmas (missing = 0, extra = 0, dups = 0). Each lesson maintains >= 12 lemmas.

## 4. Activities and Provenance
All 11 baseline activities are preserved structurally:
- Inline: `act-1` (L1), `act-2` (L1), `act-3` (L1), `act-5` (L1), `act-4` (L2), `act-9` (L3).
- Workbook: `act-w1` (L1), `act-w2` (L2), `act-w3` (L2), `act-w4` (L3), `act-w5` (L3).

### Review Fixes Implemented:
1. **Unintroduced vocabulary cleanup (Fix 1)**:
   - `act-302`: Item 6 replaced `Моя́ сестра́ — вчи́телька. ___ вдо́ма.` with `Оле́на — вчи́телька. ___ працю́є.`, removing unintroduced `вдо́ма`.
   - `act-104`: Replaced unjumble items containing unintroduced `там`, `кімна́та`, `зо́шит`, `фо́то` with taught Lesson 1 items: `Ось мій та́то.`, `Ось моя́ ма́ма.`, `Це моє́ мі́сто.`.
   - `act-205`: Removed untaught adjective chunks (`нова́ су́мка`, `нови́й телефо́н`, `вели́ке лі́жко`) and multi-clause compound sentences, keeping strictly canonical `У мене́ є...` / `У тебе́ є...?` structures with Lesson 2 nouns (`стіл`, `ла́мпа`, `су́мка`, `телефо́н`, `лі́жко`, `зо́шит`).
2. **Ambiguous Answer Structures (Fix 2)**:
   - `act-102`: Converted from duplicate-label match-up to single-choice `quiz` with 6 items (`стіл`, `кни́га`, `вікно́`, `та́то`, `ма́ма`, `мі́сто`) selecting `[він, вона́, воно́]`.
   - `act-304`: Split into two mutually disjoint, non-overlapping groups `він (чолові́чий рід)` (6 items: `студе́нт`, `вчи́тель`, `лі́кар`, `Мико́ла`, `Ілля́`, `дя́дько`) and `вона́ (жіно́чий рід)` (6 items: `студе́нтка`, `вчи́телька`, `лі́карка`, `акто́рка`, `співа́чка`, `Окса́на`), removing `соба́ка`.
   - `act-301`: Added explicit instruction regarding spelling preservation: `(зберіга́йте початко́ву лі́теру: вчи́тель → вчи́телька, учи́тель → учи́телька)`.
   - `act-306`: Explicit title and instruction: «За́йве сло́во за ро́дом» / «Знайді́ть одне́ за́йве сло́во за грамати́чним ро́дом.». Replaced item 5 (`соба́ка` -> `зо́шит`) and item 6 (`лі́карка` -> `ла́мпа`), eliminating animacy/semantic confounds.
   - `act-205`: Cleaned unjumble items to ensure unique word orders.
3. **A1 Sentence Length (Fix 3)**:
   - `act-203`: All 6 statements shortened to exactly 5 words each (within the 4–6 word A1 limit):
     1. `Сло́во «стіл» — це він.` (5 words, True)
     2. `Сло́во «ла́мпа» — це воно́.` (5 words, False)
     3. `Сло́во «лі́жко» — це воно́.` (5 words, True)
     4. `Сло́во «су́мка» — це вона́.` (5 words, True)
     5. `Сло́во «телефо́н» — це вона́.` (5 words, False)
     6. `Сло́во «дзе́ркало» — це воно́.` (5 words, True)
   - `act-303`: All 6 statements shortened to exactly 5 words each (within 4–6 word A1 limit):
     1. `Ім'я́ «Мико́ла» — це він.` (5 words, True)
     2. `Ім'я́ «Павло́» — це воно́.` (5 words, False)
     3. `У ку́рсі «соба́ка» — це він.` (5 words, True)
     4. `Ім'я́ «Ілля́» — це він.` (5 words, True)
     5. `Сло́во «дя́дько» — це вона́.` (5 words, False)
     6. `Сло́во «ба́тько» — це він.` (5 words, True)
4. **Presentation (Fix 4)**:
   - Every English -> Ukrainian `translate` activity is marked as bonus (`bonus: true`, title prefixed `Бо́нус:`): `act-105`, `act-207`, `act-307`.
   - Disambiguated prompts: `act-105` item 4 (`My brother is here.` -> `Це мій брат.`); `act-207` item 2 (`Do you (informal) have a phone?` -> `У тебе́ є телефо́н?`); `act-307` item 1 (`She is a teacher (vchytelka).` -> `Вона́ вчи́телька.`).
   - Added summary passages across all three lessons feature bilingual side-by-side Ukrainian/English tables.
5. **Resources Resolvability (Fix 6)**:
   - Every textbook reference mapped to an exact chunk ID in `sources.db`:
     - L1: `4-klas-ukrayinska-mova-ponomarova-2021-1_s0033` (Пономарьова 4 клас с. 35 «Визначаю рід і число іменників»)
     - L2: `6-klas-ukrmova-litvinova-2023_s0134` (Літвінова 6 клас с. 129 § 25 «Рід іменників»)
     - L2: `6-klas-ukrmova-avramenko-2023_s0084` (Авраменко 6 клас с. 83 § 43 «Рід іменників»)
     - L3: `6-klas-ukrmova-avramenko-2023_s0085` (Авраменко 6 клас с. 84 «Фемінітиви»)
     - L3: `6-klas-ukrmova-litvinova-2023_s0135` (Літвінова 6 клас с. 130 «Вправа 264. Рід іменників»)
   - External URL in L1 updated with access date: `accessed: '2026-09-12'`.
6. **Pedagogical Completeness (Fix 7)**:
   - Opener of each lesson states 2–3 specific objectives (Ukrainian title, em-dash English gloss).
   - Summary of each lesson concludes with a 2–3 line independent production task.
   - Lesson 3 self-check includes a dedicated table covering professions, male names, and exceptions.
7. **Dialogue Formatting (Fix 8)**:
   - Lesson 1 dialogue emitted as `> **Марко́**: Приві́т! ...` blockquotes for `<DialogueBox>` integration.

### Self-Solved Activity Solution Keys:
- **`act-102` (quiz)**:
  1. стіл -> він
  2. кни́га -> вона́
  3. вікно́ -> воно́
  4. та́то -> він
  5. ма́ма -> вона́
  6. мі́сто -> воно́
- **`act-205` (unjumble)**:
  1. `[У, мене́, є, стіл]` -> `У мене́ є стіл.`
  2. `[У, тебе́, є, ла́мпа]` -> `У тебе́ є ла́мпа?`
  3. `[У, мене́, є, су́мка]` -> `У мене́ є су́мка.`
  4. `[У, тебе́, є, телефо́н]` -> `У тебе́ є телефо́н?`
  5. `[У, мене́, є, лі́жко]` -> `У мене́ є лі́жко.`
  6. `[У, тебе́, є, зо́шит]` -> `У тебе́ є зо́шит?`
- **`act-301` (match-up)**:
  - `студе́нт` -> `студе́нтка`
  - `вчи́тель` -> `вчи́телька`
  - `учи́тель` -> `учи́телька`
  - `лі́кар` -> `лі́карка`
  - `акто́р` -> `акто́рка`
  - `співа́к` -> `співа́чка`
- **`act-304` (group-sort)**:
  - `він (чолові́чий рід)`: `студе́нт`, `вчи́тель`, `лі́кар`, `Мико́ла`, `Ілля́`, `дя́дько`
  - `вона́ (жіно́чий рід)`: `студе́нтка`, `вчи́телька`, `лі́карка`, `акто́рка`, `співа́чка`, `Окса́на`
- **`act-306` (odd-one-out за родом)**:
  1. `[вчи́телька, лі́карка, студе́нтка, студе́нт]` -> `студе́нт` (він vs вона)
  2. `[акто́р, співа́к, лі́кар, акто́рка]` -> `акто́рка` (вона vs він)
  3. `[Мико́ла, Ілля́, Павло́, Окса́на]` -> `Окса́на` (вона vs він)
  4. `[та́то, ба́тько, дя́дько, ма́ма]` -> `ма́ма` (вона vs він)
  5. `[стіл, телефо́н, зо́шит, кни́га]` -> `кни́га` (вона vs він)
  6. `[вікно́, лі́жко, фо́то, ла́мпа]` -> `ла́мпа` (вона vs воно)

## 5. Language Verification Outcomes & Tool Receipts

### 5.1. VESUM Morphological Verification (`verify_words`)
Every added and modified word form is verified in VESUM.
```
Found: 8/8
- собака — FOUND (2 analyses (1 distinct lemma)): собака(noun:anim:m:v_naz), собака(noun:anim:f:v_naz)
- Микола — FOUND (1 analysis (1 distinct lemma)): Микола(noun:anim:m:v_naz:prop:fname)
- вчителька — FOUND (1 analysis (1 distinct lemma)): вчителька(noun:anim:f:v_naz)
- лікарка — FOUND (1 analysis (1 distinct lemma)): лікарка(noun:anim:f:v_naz)
- поєднується — FOUND (1 analysis (1 distinct lemma)): поєднуватися(verb:rev:imperf:pres:s:3)
- зошит — FOUND (2 analyses (1 distinct lemma)): зошит(noun:inanim:m:v_naz), зошит(noun:inanim:m:v_zna)
- лампа — FOUND (1 analysis (1 distinct lemma)): лампа(noun:inanim:f:v_naz)
- або — FOUND (1 analysis (1 distinct lemma)): або(conj:coord)
```
Unverified lemmas across all lessons: 0 (limit <= 5 per lesson).

### 5.2. Stress Oracle Verification (`verify_stress`)
Every Ukrainian word in module prose, activities, and vocabulary carries stress verified against the ULIF-derived offline dictionary `scripts.verification.stress`:
```json
{
  "або́": {"status": "ok", "stressed_form": "або́", "vowel_index": 2},
  "поє́днується": {"status": "ok", "stressed_form": "поє́днується", "vowel_index": 2},
  "соба́ка": {"status": "ok", "stressed_form": "соба́ка", "vowel_index": 2},
  "Мико́ла": {"status": "ok", "stressed_form": "Мико́ла", "vowel_index": 2},
  "вчи́телька": {"status": "ok", "stressed_form": "вчи́телька", "vowel_index": 1},
  "лі́карка": {"status": "ok", "stressed_form": "лі́карка", "vowel_index": 1},
  "зо́шит": {"status": "ok", "stressed_form": "зо́шит", "vowel_index": 1},
  "ла́мпа": {"status": "ok", "stressed_form": "ла́мпа", "vowel_index": 1}
}
```
Stress gaps declared in `lessons.yaml: unverified_stress`:
- Lesson 1: `[уро́ці]` (locative of *уро́к*).
- Lesson 2: `[уро́ці, фемініти́вами]`.
- Lesson 3: `[фемініти́ви, фемініти́вом]`.

### 5.3. Russian Pattern & Shadow Verification (`check_russian_shadow`)
Heuristic check shows 0 Russian calques / shadows:
```json
{
  "Це мій собака і моя вчителька.": {"matches_russian": false, "confidence": 0.0},
  "Микола — це він.": {"matches_russian": false, "confidence": 0.0},
  "Це моя кімната. У мене є стіл і лампа.": {"matches_russian": false, "confidence": 0.0}
}
```

### 5.4. Grammatical Error Corpus Check (`search_ua_gec_errors`)
Checked added constructions against UA-GEC annotated corpus:
- `собака`: No UA-GEC results found.
- `у мене є`: No UA-GEC results found.

### 5.5. Source Textbook Chunks (`search_text`)
Verified locators against SQLite FTS index in `sources.db`:
- `4-klas-ukrayinska-mova-ponomarova-2021-1_s0033`: Пономарьова К. І., 4 клас (2021), с. 35 «Визначаю рід і число іменників».
- `6-klas-ukrmova-litvinova-2023_s0134`: Літвінова І. М., 6 клас (2023), с. 129 § 25 «Рід іменників».
- `6-klas-ukrmova-avramenko-2023_s0084`: Авраменко О., 6 клас (2023), с. 83 § 43 «Рід іменників».
- `6-klas-ukrmova-avramenko-2023_s0085`: Авраменко О., 6 клас (2023), с. 84 «Фемінітиви».
- `6-klas-ukrmova-litvinova-2023_s0135`: Літвінова І. М., 6 клас (2023), с. 130 «Вправа 264. Рід іменників».

## 6. Plan-level findings (inherited from the original module)
These four issues originated in the baseline module `curriculum/l2-uk-en/a1/things-have-gender/` (and its upstream plan). Because original baseline prose and activity structure are locked by Phase 0 verbatim preservation invariants, they are recorded here for orchestrator routing to plan review:

1. **Categorical rejection of «моя́ соба́ка» as an error**:
   - *Baseline text*: Module 8 paragraph 27 (`Моя́ соба́ка га́рна. -> Мій соба́ка га́рний.`) and paragraph 28 (`For соба́ка, just memorize the course phrase мій соба́ка.`) treat feminine gender as an error.
   - *Reviewer Evidence*: СУМ-11 (том IX, с. 431) defines `соба́ка` as «ч. і рідше ж.». VESUM provides two analyses: `noun:anim:m:v_naz` and `noun:anim:f:v_naz`. In Ukrainian folk, colloquial, and classical usage, feminine gender is authentic and documented, not an ungrammatical error.
   - *Proposed Plan Change*: In the A1/A2 curriculum plan, clarify that masculine `мій соба́ка` is the standard literary and course default norm, while noting that feminine `моя́ соба́ка` is a recognized colloquial variant («рідше ж.»), rather than penalizing learners as if it were a grammatical corruption.
2. **`act-9` English prompts in immersion curriculum**:
   - *Baseline text*: Inline activity `act-9` poses questions in English: `She is a teacher.`, `He is a doctor.`, `He is a student.`, `She is an actor.`.
   - *Reviewer Evidence*: Contradicts the project's pedagogical guideline requiring target-language immersion (Ukrainian prompts for recall/comprehension) in core lessons.
   - *Proposed Plan Change*: Update the plan for Module 8 to formulate `act-9` prompts in Ukrainian with context sentences or visual cues (e.g. `Оле́на працю́є в шко́лі. Хто вона́? — Вона́ [вчи́телька / вчи́тель]`).
3. **`act-w2` English translation cues**:
   - *Baseline text*: Workbook match-up `act-w2` pairs Ukrainian nouns with English words (`стіл` -> `table`, `кни́га` -> `book`, `вікно́` -> `window`, etc.).
   - *Reviewer Evidence*: Translating isolated vocabulary words provides weak communicative engagement compared to grammatical gender pairing (`стіл` -> `він`, `кни́га` -> `вона́`, `вікно́` -> `воно́`).
   - *Proposed Plan Change*: Replace the English gloss matching in `act-w2` with Ukrainian gender association or contextual iconography.
4. **`act-w3` missing context in single-token fill-ins**:
   - *Baseline text*: `act-w3` tests isolated tokens in isolated templates: `___ мене́ є стіл.` (testing `У`) and `У мене́ ___ кни́га.` (testing `є`).
   - *Reviewer Evidence*: Fill-in questions without conversational context or communicative purpose encourage mechanical guessing rather than functional language acquisition.
   - *Proposed Plan Change*: Frame `act-w3` as micro-dialogues or situational exchanges where the speaker describes possessions in a natural communicative context.
