Good — I now have all the context needed. The known-good vocabulary files use bare lists with IPA fields and tie bars on affricates (e.g., `t͡s`). Let me compile the full adversarial review.

---

## Phase 9: Final QA Review — colors-and-clothing

### Issues Found

**ISSUE 1 — CRITICAL: Grammar error in model paragraph (line 363)**
The model paragraph (blockquote a student should follow) contains `зелена сорочка` (Nominative) after `ношу` which requires Accusative. This directly contradicts the rule taught on line 203 ("NOT 'червона сукня'"). A beginner copying this "correct" model learns the exact error the module warns against.

**ISSUE 2 — CRITICAL: IPA missing tie bars on ALL affricates (systemic)**
Ukrainian Ч = [t͡ʃ], Ц = [t͡s], Дж = [d͡ʒ]. The file consistently omits the tie bar, writing `tʃ`, `t s`, `dʒ` — which represent two separate phonemes in IPA, not affricates. The known-good vocab file (the-gender-code.yaml:6) correctly uses `t͡s`. Affected locations:
- Line 23: `[tʃerˈwɔnɪj]` — Ч missing tie bar
- Line 25: `[ˈtʃɔrnɪj]` — Ч missing tie bar
- Line 27: `[ˈbʲiɫɑ sɔˈrɔtʃkɑ]` — Ч missing tie bar
- Line 157: `[sɔˈrɔtʃkɑ]` — Ч missing tie bar
- Line 229: `[ˈdʒɪnsɪ]` — Дж missing tie bar
- Lines 244, 307, 341, 342: `[t sʲ i]`, `[t sʲ iˈnɑ]`, `[t s e ...]`, `[... t s e]` — Ц has spaces between phonemes AND missing tie bar

**ISSUE 3 — CRITICAL: Wrong phoneme `w` for Ukrainian В (line 23)**
`[tʃerˈwɔnɪj]` uses `w` (bilabial approximant) for В. Ukrainian В is a labiodental approximant [ʋ]. The file is inconsistent: lines 163, 169, 261 correctly use `ʋ` for В, while lines 23, 64, 341 use `v` or `w`.

**ISSUE 4 — MODERATE: Misplaced example under Structure 2 (line 294)**
`Я ношу старий светр.` is listed under "Structure 2: 'On him is...' (Locative)" but uses носити + Accusative (Structure 1). This confuses the pedagogical contrast between the two structures.

**ISSUE 5 — MODERATE: Pedagogically confusing case form (line 185)**
`Він не носить сорочки.` immediately follows Accusative teaching. The student just learned сорочка → сорочку in Accusative. Then they see `сорочки` (Genitive or plural) with zero explanation. Should be `сорочку` (Accusative) to reinforce the just-taught pattern.

**ISSUE 6 — MODERATE: Inconsistent `v`/`ʋ` for В in IPA (line 64, 341)**
Line 64: `vɪ` for ви. Line 341: `vɪɦlʲaˈdɑje` for виглядає. Both should use `ʋ` per Ukrainian phonology and per the file's own convention elsewhere.

**ISSUE 7 — MINOR: Scope comment typo (line 5)**
`Instrumental case (Instructional) → A2` — "(Instructional)" is garbled, should be "(Instrumental)" or removed.

**ISSUE 8 — MODERATE: Vocabulary YAML format (vocabulary file)**
Uses `items:` dictionary wrapper instead of the project-standard bare list. Compare with known-good files (this-is-i-am.yaml, the-gender-code.yaml) which all use bare lists. Also missing `ipa` fields, and includes 7 metalinguistic terms (дієслово, множина, займенник, відмінок, знахідний, рід, узгодження) that are grammar labels, not target vocabulary for a colors-and-clothing module. This needs a vocab enrichment pass — not fixable in a single FIX block.

**ISSUE 9 — MINOR: LLM repetition pattern**
"Це не просто X" used twice (line 17: `Колір — це не просто картинка`; line 258: `Одяг — це не просто тканина`). Borderline but flagged.

**ISSUE 10 — MINOR: Missing planned phrase "Це мені пасує"**
Meta line 49 specifies key phrase "Це мені пасує" (This fits me / This suits me) for the dialogue section. It does not appear anywhere in the module.

---

### Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/a1/colors-and-clothing.md
---OLD---
  - Instrumental case (Instructional) → A2
---NEW---
  - Instrumental case → A2
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/colors-and-clothing.md
---OLD---
**Червоний** [tʃerˈwɔnɪj] (red)
---NEW---
**Червоний** [t͡ʃerˈʋɔnɪj] (red)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/colors-and-clothing.md
---OLD---
**Чорний** [ˈtʃɔrnɪj] (black)
---NEW---
**Чорний** [ˈt͡ʃɔrnɪj] (black)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/colors-and-clothing.md
---OLD---
A **біла сорочка** [ˈbʲiɫɑ sɔˈrɔtʃkɑ] (white shirt)
---NEW---
A **біла сорочка** [ˈbʲiɫɑ sɔˈrɔt͡ʃkɑ] (white shirt)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/colors-and-clothing.md
---OLD---
**«Який колір ви любите?»** [jaˈkɪj ˈkɔlʲir vɪ ˈlʲubɪte]
---NEW---
**«Який колір ви любите?»** [jaˈkɪj ˈkɔlʲir ʋɪ ˈlʲubɪte]
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/colors-and-clothing.md
---OLD---
**Сорочка** [sɔˈrɔtʃkɑ] (shirt) is feminine.
---NEW---
**Сорочка** [sɔˈrɔt͡ʃkɑ] (shirt) is feminine.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/colors-and-clothing.md
---OLD---
*   **Він не носить сорочки.**
---NEW---
*   **Він не носить сорочку.**
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/colors-and-clothing.md
---OLD---
*   **Джинси** [ˈdʒɪnsɪ] (jeans)
---NEW---
*   **Джинси** [ˈd͡ʒɪnsɪ] (jeans)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/colors-and-clothing.md
---OLD---
**ці** [t sʲ i] (these)
---NEW---
**ці** [t͡sʲi] (these)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/colors-and-clothing.md
---OLD---
**Ціна** [t sʲ iˈnɑ] (price):
---NEW---
**Ціна** [t͡sʲiˈnɑ] (price):
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/colors-and-clothing.md
---OLD---
*   **На ній — гарна сорочка.** (On her is a beautiful shirt.)
*   **Я ношу старий светр.** (I wear an old sweater.)
---NEW---
*   **На ній — гарна сорочка.** (On her is a beautiful shirt.)
*   **На мені — старий светр.** (On me is an old sweater.)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/colors-and-clothing.md
---OLD---
*   **Це гарно виглядає.** [t s e ˈɦɑrnɔ vɪɦlʲaˈdɑje] — This looks good.
*   **Я беру це.** [ja beˈru t s e] — I'll take it.
---NEW---
*   **Це гарно виглядає.** [t͡se ˈɦɑrnɔ ʋɪɦlʲɑˈdɑje] — This looks good.
*   **Я беру це.** [ja beˈru t͡se] — I'll take it.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/colors-and-clothing.md
---OLD---
> Привіт! Мене звати Олена. Я люблю зелений колір. Я люблю зручний одяг. Сьогодні я ношу сині джинси і зелена сорочка. Я також ношу чорні окуляри. Мій стиль — простий і сучасний.
---NEW---
> Привіт! Мене звати Олена. Я люблю зелений колір. Я люблю зручний одяг. Сьогодні я ношу сині джинси і зелену сорочку. Я також ношу чорні окуляри. Мій стиль — простий і сучасний.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/colors-and-clothing.md
---OLD---
Одяг — це не просто тканина. Це наша культура.
---NEW---
Одяг — це частина культури.
===FIX_END===

### Unfixed findings (require separate pass):
- **Vocabulary YAML**: Needs bare-list reformat, IPA enrichment, and removal of 7 metalinguistic terms. Should be handled by `/module-vocab-enrich`.
- **Missing "Це мені пасує"**: Meta specifies this phrase in the dialogue section; not blocking but incomplete plan coverage.

===VERDICT===
NEEDS_WORK
===END_VERDICT===

**Rationale**: 13 fixes applied covering 1 critical grammar error in a model paragraph, 10 IPA corrections (missing tie bars on affricates, wrong phoneme for В), 1 misplaced pedagogical example, and 1 LLM repetition pattern. After these fixes the content prose is clean, activities are correct, and cultural claims are accurate. Remaining work is the vocabulary YAML (format + IPA enrichment) which doesn't block the audit but needs a vocab enrichment pass. Module passes audit otherwise — strong structure, good cultural depth, correct activities.