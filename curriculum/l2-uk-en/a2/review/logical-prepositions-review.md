<!-- content-hash: 59529332f2c8 -->
**Reviewed-By:** claude-opus-4-6

---

## Scores

| # | Dimension | Score | Evidence Summary |
|---|-----------|-------|------------------|
| 1 | Plan Compliance | 8/10 | All H2 sections present. Activity count shortfalls: time quiz 8 items (plan: 10+), case quiz 8 items (plan: 12+), translate 6 items (plan: 10+). Group-sort activity missing Dative/Locative case groups despite the module teaching both. |
| 2 | Lesson Quality | 8/10 | Solid PPP arc with good WELCOME (blockquote at line 10) → PRESENT → PRACTICE → summary flow. However, Chess Grandmaster persona (per meta) is completely absent — zero chess metaphors or strategic framing. Dense Ukrainian intro paragraph (line 17-19) with no inline glossing may overwhelm A2 learners. Self-check questions at end are good but no "You can now..." celebration. |
| 3 | Language | 7/10 | Colonial framing: heading «Усунення росіянізмів» (line 135) + explicit Russian mention at line 149: "a direct calque (borrowing) from Russian." Research notes explicitly state "Do not compare them to Russian." Also: "красивий" Russianism used twice (lines 19, 103) — should be "гарний" per curriculum standards. Word order issue: «В українській сучасній культурі» (line 19) should be «В сучасній українській культурі». |
| 4 | Richness | 8/10 | Five engagement boxes with variety ([!culture], [!warning] x2, [!myth-buster], [!fact]). Two practical dialogues (pharmacy, trip planning). Formal letter analysis. Sentence transformation drill. However, Chess Grandmaster persona is unused — missed opportunity for strategic/game-theory metaphors that would elevate richness. Cultural hooks are good but rely heavily on "hospitality" trope. |
| 5 | Humanity & Warmth | 8/10 | Direct address count is adequate (~29 "you/your/ви/вам" matches). However: no warm greeting ("Привіт!" appears only in a dialogue at line 241, not as a module opening). No explicit encouragement phrases like "Great job!" or "Don't worry" in the instructional prose. No "You can now..." celebration at the end. The summary (line 255) lists what was learned but in a flat, report-like tone rather than celebratory. |
| 6 | LLM Fingerprint | 7/10 | Three LLM clichés found: (1) «архітектурний каркас складного мислення» (line 257) — classic "architecture of language" AI rhetoric; (2) "the Genitive case is the powerful engine that drives these logical substitutions" (line 220) — LLM-typical abstract metaphor; (3) «Вони діють як дуже надійний клей. Цей важливий клей міцно тримає складні довгі речення разом» (line 19) — overwrought metaphor with redundant adjective stacking. Additionally, "дуже" appears 15 times across the content, creating a padding effect — many instances are unnecessary filler (e.g., «дуже фундаментальною», «дуже надійний клей», «дуже багатшою та точнішою»). |
| 7 | Factual Accuracy | 9/10 | All grammar rules verified correct: через + Accusative, завдяки + Dative, для/без + Genitive, про + Accusative, від/з + Genitive, о/об + Locative. Callout box claims are accurate. The "піти по хліб" vs "піти за хлібом" distinction is prescriptivist but pedagogically appropriate for this curriculum's standards. One minor concern: «прийменник «по» + Accusative» claim at line 125 is correct for purpose-of-movement sense but oversimplifies «по»'s complex case governance. |
| 8 | Activity Quality | 7/10 | 12 activities total — good variety (match-up, group-sort, true-false, quiz x2, fill-in x2, cloze, error-correction, unjumble, mark-the-words, translate). **Critical gap**: group-sort activity (line 30-37) only has Genitive and Accusative groups but the module teaches Dative (завдяки, всупереч) and Locative (о/об) — these cases are completely absent from the sorting exercise. **IPA error**: vocabulary file has «всупереч» as [ˈʍsupɛrɛt͡ʃ] (line 71 of vocab) — stress should be on the last syllable [u̯supɛˈrɛt͡ʃ], and [ʍ] is not a Ukrainian phoneme. Activity item counts fall below plan minimums for time quiz (8 vs 10+), case quiz (8 vs 12+), and translate (6 vs 10+). |
| 9 | Immersion | 9/10 | Measured at 50.4%, within the 50-60% target for A2 M01-20. English appropriately used for grammar theory and explanations. Ukrainian used for all examples, dialogues, and practice. The balance is at the low end but acceptable. |

---

## Critical Issues Found

### Issue 1: Colonial Framing — "Усунення росіянізмів" Section (CRITICAL)

**Location:** Line 135 (heading), Line 149 (body text)

**Evidence:** The section heading «Усунення росіянізмів: «Із-за» проти «Через»» explicitly frames Ukrainian by contrast with Russian. Line 149 states: "Using «із-за» for cause is a direct calque (borrowing) from Russian, and it violates the internal logic of the Ukrainian prepositional system."

The research notes explicitly instruct: "Do not compare them to Russian. Present Ukrainian logical distinctions as independent positive features."

**Impact:** Defines Ukrainian preposition usage through Russian as a reference point, which is colonial framing per review rubric. Language score capped at ≤7.

**Fix:** Rename heading to «Типова помилка: «Із-за» проти «Через»». Rewrite line 149 to: "Using «із-за» for cause violates the internal logic of the Ukrainian prepositional system, where «із-за» is strictly a spatial preposition meaning 'from behind'. True Ukrainian relies on «через» for causation." — Remove all Russian references.

---

### Issue 2: "красивий" Russianism (×2)

**Location:** Line 19 and Line 103

**Evidence (line 19):** «З ними ваша українська мова стане дуже красивою і природною.»
**Evidence (line 103):** «Цей красивий подарунок від моєї старшої сестри.»

Per the auto-fail checklist, "красивий→гарний" is a flagged Russianism.

**Fix:** Line 19: replace «красивою» with «гарною». Line 103: replace «красивий» with «гарний».

---

### Issue 3: Group-Sort Activity Missing Two Case Groups

**Location:** Activities file, lines 30-37

**Evidence:** The group-sort activity only includes two groups:
- Родовий відмінок (Genitive): ["для", "без", "від", "крім", "замість"]
- Знахідний відмінок (Accusative): ["через", "про", "по"]

But the module teaches prepositions with **four** grammatical cases. Missing:
- Давальний відмінок (Dative): завдяки, всупереч
- Місцевий відмінок (Locative): о, об

Also missing from Genitive group: протягом, щодо, стосовно, внаслідок, заради

**Fix:** Add two additional groups to the group-sort activity:
- "Давальний відмінок (Dative)": ["завдяки", "всупереч"]
- "Місцевий відмінок (Locative)": ["о", "об"]
And add missing Genitive prepositions: "протягом", "щодо", "стосовно"

---

### Issue 4: IPA Error for «всупереч»

**Location:** Vocabulary file, line 71

**Evidence:** IPA listed as `[ˈʍsupɛrɛt͡ʃ]`. Two errors: (1) Stress is on the first syllable but should be on the last syllable (всупере́ч); (2) [ʍ] (voiceless labial-velar fricative, as in English "which") is not a Ukrainian phoneme — the initial cluster should be transcribed as [u̯s] or [fs].

**Fix:** Correct IPA to `[u̯supɛˈrɛt͡ʃ]`.

---

### Issue 5: LLM Clichés and "дуже" Padding

**Location:** Lines 19, 220, 257 (clichés); 15 occurrences of "дуже" throughout

**Evidence:**
- Line 257: «Ці логічні прийменники — це архітектурний каркас складного мислення в українській мові.» — "architectural framework of complex thinking" is LLM-typical abstract rhetoric.
- Line 220: "the Genitive case is the powerful engine that drives these logical substitutions" — Another LLM-favored metaphor.
- Line 19: «Вони діють як дуже надійний клей. Цей важливий клей міцно тримає складні довгі речення разом.» — Overwrought glue metaphor with redundant adjective stacking.
- "Дуже" appears 15 times. Many are unnecessary filler: «дуже фундаментальною» (line 24), «дуже надійний клей» (line 19), «значно багатшою та точнішою» is fine but the preceding line has «дуже».

**Fix:** Replace line 257 metaphor with a concrete statement about what the learner can now do. Remove "powerful engine" at line 220. Simplify the glue metaphor at line 19. Audit all 15 "дуже" instances and remove at least 8 unnecessary ones.

---

### Issue 6: Missing Chess Grandmaster Persona

**Location:** Entire content file (absence)

**Evidence:** The meta file specifies `persona.role: Chess Grandmaster`, but zero chess, strategy, or game-theory metaphors appear anywhere in the content. The content reads as a generic Ukrainian tutor, not a grandmaster guiding a student through strategic language moves.

**Fix:** Incorporate 2-3 chess metaphors. Example: Introduce preposition selection as "strategic moves" on a grammatical chessboard. The через/завдяки distinction could be framed as choosing between attacking and defensive positions. Subtlety is key — don't force it, but the persona should be recognizable.

---

### Issue 7: Word Order Error

**Location:** Line 19

**Evidence:** «В українській сучасній культурі дуже цінується чітке та логічне висловлення думок.» — The adjective order "українській сучасній" is unnatural. In Ukrainian, temporal adjectives typically precede nationality/origin adjectives.

**Fix:** Replace with «В сучасній українській культурі...»

---

## Verification Summary

| Check | Result | Details |
|-------|--------|---------|
| Russianisms | FAIL | "красивий" ×2 (lines 19, 103) |
| Colonial framing | FAIL | "Усунення росіянізмів" heading (line 135) + Russian reference (line 149) |
| Grammar scope | PASS | All prepositions within A2 scope |
| Calques | PASS | No calques in the module's own language (the module correctly identifies calques as errors to avoid) |
| Factual accuracy (callouts) | PASS | All 5 callout boxes verified accurate |
| Grammar rules | PASS | All case governance rules verified correct |
| IPA | FAIL | "всупереч" IPA has wrong stress and non-Ukrainian phoneme |
| Activity errors | FAIL | Group-sort missing 2 case groups; item counts below plan minimums |
| LLM fingerprint | FAIL | 3 cliché patterns + "дуже" overuse (15×) |
| Persona compliance | FAIL | Chess Grandmaster persona completely absent |
| Beginner safety | PASS | Content is accessible at A2 level, clear instructions |
| Section coverage | PASS | All 5 plan sections present as H2 headers |

**Sections referenced:** Section «Вступ» (lines 14-38), Section «Презентація: Причина та Мета» (lines 40-119), Section «Культурний контекст та логічні пастки» (lines 121-160), Section «Практика: Час та Відносини» (lines 162-219), Section «Діалоги та підсумок» (lines 222-265).

---

## Verdict

**REVISE** — The module has a solid pedagogical foundation with good structure, accurate grammar rules, and practical dialogues. However, it has multiple issues that require targeted fixes:

1. **Colonial framing** (Critical) — must remove Russian references and reframe the "із-за" error correction on Ukrainian's own terms
2. **"красивий" Russianism** (Critical) — straightforward lexical fix
3. **Group-sort activity gap** — must add Dative and Locative case groups
4. **IPA error** — "всупереч" needs correct stress and phoneme transcription
5. **LLM fingerprint** — remove cliché metaphors and reduce "дуже" padding
6. **Missing persona** — add Chess Grandmaster framing (2-3 touches)
7. **Word order** — minor fix at line 19

None of these require a full rewrite. A targeted D.2 repair pass addressing these 7 issues should bring the module to passing quality.