Good — the vocabulary file exists and is well-populated (the prompt's "(file not found)" was stale). Now I have all the data. Here is my deep adversarial review.

---

## Phase 9 Final QA Review: the-living-verb-i (a1-06)

### Issues Found

**Issue 1 — MUST FIX: "книгу" in true-false activity breaks safe harbor**
- **File:** `activities/the-living-verb-i.yaml`, line 360
- **Text:** `statement: «Ми читає книгу» — це правильне речення.`
- **Problem:** The content prose at line 242 explicitly establishes a "safe harbor" pedagogical contract: *"If we used a feminine word like книга (book), it would change to книгу. But we aren't ready for that headache yet!"* This activity uses "книгу" (feminine accusative), violating that contract and exposing learners to an unexplained grammar form. The statement's error is the verb (читає with Ми), so the object is irrelevant to what's being tested.
- **Fix:** Replace "книгу" with "журнал" (masculine inanimate, Nom=Acc, safe harbor).

**Issue 2 — MUST FIX: "музику" in fill-in activity breaks safe harbor**
- **File:** `activities/the-living-verb-i.yaml`, line 391
- **Text:** `sentence: _____ слухає музику.`
- **Problem:** "Музику" is feminine accusative of "музика." Same safe harbor violation as Issue 1. The activity tests pronoun identification from verb endings — the object is just context. "Радіо" (neuter indeclinable, already used with "слухати" in the content) is the safe replacement and matches the module's own examples.
- **Fix:** Replace "музику" with "радіо".

**Issue 3 — SHOULD FIX: писати conjugation has no visual stress marking**
- **File:** `the-living-verb-i.md`, lines 313–318
- **Text:**
  ```
  *   **Я пишу.** (I write.) — *Note the stress shift!*
  *   **Ти пишеш.**
  *   **Він пише.**
  ```
- **Problem:** The text explicitly calls attention to a stress shift ("Note the stress shift!") but provides no visual indication of where the stress lands on any form. The stress pattern is: пишу́ (ending) vs пи́шеш, пи́ше, пи́шемо, пи́шете, пи́шуть (stem). A learner reading this has no way to know where stress falls. Adding acute accent marks (́) is the standard Ukrainian dictionary convention and trivial to add.
- **Fix:** Add stress marks to all conjugated forms.

**Issue 4 — INFO: відпочивати IPA voicing assimilation**
- **File:** `vocabulary/the-living-verb-i.yaml`, line 36
- **Text:** `ipa: '[ʋʲidpɔt͡ʃɪˈʋɑtɪ]'`
- **Problem:** In natural speech, the д before voiceless п undergoes regressive devoicing: [ʋʲitpɔt͡ʃɪˈʋɑtɪ]. The current transcription shows broad/phonemic [d], which is standard for dictionary entries but phonetically imprecise.
- **Severity:** Informational only. Broad transcription is acceptable for A1 vocabulary files. Not fixing.

**Issue 5 — INFO: працювати vocab note formatting**
- **File:** `vocabulary/the-living-verb-i.yaml`, line 13
- **Text:** `notes: type 1 (-ювати → -юю); imperfective`
- **Problem:** The notation "-юю" is non-standard shorthand for "first person singular form ends in -юю" (працюю). While not wrong, it could confuse someone reading the vocab data expecting standard conjugation class labels. A clearer note would be "type 1 (-ювати; stem truncation -вати)".
- **Severity:** Informational. Does not affect learners (vocab notes are metadata). Not fixing.

### Checks Passed

**IPA Accuracy:**
- All 23+ IPA transcriptions in the content verified correct
- Tie bars on affricates: t͡ʃ (Ч) ✓, t͡s (Ц in працювати) ✓
- В consistently rendered as ʋ (not w) ✓
- Ɦ for Ukrainian Г ✓ (книга [ˈknɪɦɑ], грати [ˈɦrɑtɪ])

**Russianisms:** CLEAN — no кушати, получати, приймати участь, слідуючий, or Russian characters (ы, э, ё, ъ) found.

**Conjugation accuracy:** All 3 full paradigms (читати, писати, працювати) verified correct. The с→ш alternation in писати and the -вати truncation in працювати are both correctly explained and demonstrated.

**Plan compliance:**
- All 4 content_outline sections present ✓
- All 8 required vocabulary items used in prose ✓
- All 4 recommended vocabulary items used in prose ✓
- 4/4 objectives map to self-check questions ✓
- Cultural content (Apostol 1574, proverb) matches plan ✓

**Activity correctness:**
- 10 activities, 82 items total
- All fill-in items produce grammatical sentences ✓
- All match-up pairs are correct ✓
- All true-false items have correct answers ✓
- All anagram scrambles contain exactly the right letters ✓
- Group-sort: all items correctly categorized as singular/plural ✓

**Factual accuracy:**
- Ivan Fedorovych / Apostol / Lviv / 1574: Correct ✓
- Proverb "Птицю пізнати по пір'ю, а людину по мові": Authentic Ukrainian proverb ✓
- Etymology of дієслово (дія + слово): Correct ✓

**LLM artifacts:** None detected. No purple prose, no "Це не просто X, а Y" patterns, no false statistics, no folk etymology as fact. Voice is distinctive and well-maintained.

**Vocabulary YAML:** File exists with 25 well-structured entries. All required and recommended vocabulary present. IPA transcriptions match content. Format is bare list at root ✓.

---

### Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/the-living-verb-i.yaml
---OLD---
    statement: «Ми читає книгу» — це правильне речення.
---NEW---
    statement: «Ми читає журнал» — це правильне речення.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/the-living-verb-i.yaml
---OLD---
    sentence: _____ слухає музику.
---NEW---
    sentence: _____ слухає радіо.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-living-verb-i.md
---OLD---
*   **Я пишу.** (I write.) — *Note the stress shift!*
*   **Ти пишеш.**
*   **Він пише.**
*   **Ми пишемо.**
*   **Ви пишете.**
*   **Вони пишуть.**
---NEW---
*   **Я пишу́.** (I write.) — *Stress on the ending!*
*   **Ти пи́шеш.** — *Stress jumps to the stem.*
*   **Він пи́ше.**
*   **Ми пи́шемо.**
*   **Ви пи́шете.**
*   **Вони пи́шуть.**
===FIX_END===

===VERDICT===
APPROVE
===END_VERDICT===