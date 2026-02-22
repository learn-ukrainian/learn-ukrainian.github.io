**Reviewed-By:** claude-opus-4-6

## Scores

| Dimension | Score | Evidence Summary |
|-----------|-------|-----------------|
| Lesson Quality | 8/10 | Clear PPP structure with good scenarios, but Grammar section is dense (6+ concepts before formal practice) and opening lacks explicit warmth for A1 |
| Factual Accuracy | 10/10 | All grammar rules correct, ALF cultural reference verified, double negation rule accurate |
| Ukrainian Language Quality | 7/10 | IPA dual stress on «за́вжди́» (line 172) is incorrect; vocabulary IPA `[ˈsʲkʲilʲkɪ]` for скільки has erroneous palatalized с; characterizing «шо» as "lazy pronunciation" (line 160) is sociolinguistically loaded |
| English Language Quality | 9/10 | Clear, accessible B1-level English throughout; warm tutoring voice in most sections; minor overuse of declarative motivational statements |
| Activities | 6/10 | Activities #5 "Скажіть «ні»" and #8 "Ввічливі запитання" are mechanically identical (all items have same answer, same distractors, same explanation) — no real decision-making. Good variety in types otherwise |
| Richness | 8/10 | Strong ALF cultural hook, practical café/social scenarios, good callout box variety (5 types). Missing "Investigative Journalist" roleplay from plan persona |
| LLM Fingerprint | 8/10 | No structural monotony, varied section openings, no Ukrainian AI clichés. Both [!warning] "Пастка з 'Do'" and [!myth-buster] "Міф про 'Do'" address the same concept thematically |
| Immersion Balance | 9/10 | 31.6% immersion is well within A1.1 target (20-40%). Good scaffolding with English explanations and Ukrainian examples |
| Humanity & Warmth | 7/10 | Meets minimum thresholds (≥15 direct address, ≥2 "don't worry", ≥2 "you can now") but just barely. Opening starts with «Чому це важливо?» rather than a warm welcome. Limited encouragement phrases (3 borderline) |

---

## Critical Issues Found

### Issue 1: IPA Dual Stress on «завжди» [CRITICAL — IPA Error]

**Location:** Content line 172, Vocabulary file line 50-51

**Content file (line 172):** «за́вжди́» has stress diacritics on BOTH the first and last syllable. Ukrainian words have a single primary stress. The standard pronunciation is завжди́ [zɑˈʋʒdɪ] (stress on final syllable).

**Vocabulary file (line 50):** `[ˈzɑˈʋʒdɪ]` — two primary stress marks in IPA. This is impossible transcription for a single word.

Additionally, «ніколи» (line 175) is missing its stress mark entirely while adjacent words «ча́сто» and «і́ноді» have them. Standard: ніко́ли [nʲiˈkɔlɪ].

**Fix:** Content line 172: change «за́вжди́» to «завжди́». Vocabulary file: change `[ˈzɑˈʋʒdɪ]` to `[zɑˈʋʒdɪ]`. Content line 175: change «ніколи» to «ніко́ли».

### Issue 2: Vocabulary IPA for скільки [IPA Error]

**Location:** Vocabulary file line 42

The vocabulary file has `[ˈsʲkʲilʲkɪ]` with palatalized с (sʲ). The «с» in «скільки» is not palatalized — it precedes «к», not a front vowel or soft sign. The content file correctly has `[ˈskʲilʲkɪ]` on line 140.

**Fix:** Vocabulary line 42: change `[ˈsʲkʲilʲkɪ]` to `[ˈskʲilʲkɪ]`.

### Issue 3: Activities #5 and #8 Are Mechanical Single-Answer Drills [Activity Quality]

**Location:** Activities file lines 161-196 (Activity #5 "Скажіть «ні»") and lines 240-275 (Activity #8 "Ввічливі запитання")

**Activity #5:** All 8 items have the identical answer "не", identical distractors ["не", "ні", "так", "чи"], and nearly identical explanations (6 of 8 say «Заперечна частка «не» ставиться перед дієсловом.»). A learner can pattern-match "не" every time without engaging any understanding.

**Activity #8:** All 8 items have the identical answer "Чи", identical distractors ["Чи", "Не", "Ні", "Так"], and identical explanations (all say «Ввічливе запитання часто починається з частки «Чи».»). Same mechanical problem.

The key learning point — distinguishing «не» from «ні» — is never actually tested. A better design would MIX «не» and «ні» answers within a single activity, requiring the learner to think about which is appropriate in each context.

**Fix:** Redesign Activity #5 to mix «не» (negation particle) and «ні» (answer "no") items. Redesign Activity #8 to mix «чи» with question words or intonation-only questions, requiring actual decision-making.

### Issue 4: "Шо" Characterized as "Lazy Pronunciation" [Language/Pedagogy]

**Location:** Content line 160

The text reads: **Шо** = Very casual, spoken, sometimes considered "Surzhyk" (mixed language) or just lazy pronunciation.

Calling «шо» "lazy pronunciation" is sociolinguistically loaded and inaccurate. «Шо» is a well-established dialectal variant with deep roots in Ukrainian dialectology (particularly central/eastern dialects). While some prescriptivists frown upon it, framing it as "lazy" rather than "dialectal" perpetuates linguistic prejudice. At A1, introducing loaded sociolinguistic labels is pedagogically risky.

**Fix:** Replace "or just lazy pronunciation" with "or a dialectal variant" or "or informal pronunciation." The learner should learn standard «що» as the target form without being taught to judge speakers who use «шо».

---

## Additional Issues

### Issue 5: Grammar Section Density [Pacing]

**Location:** Section «Граматика: Як будувати питання» (lines 60-200)

This section introduces: (1) «чи» questions, (2) intonation questions, (3) answers «так»/«ні», (4) nine question words, (5) «що» vs «шо» distinction, (6) frequency adverbs. That's 6 distinct concepts spanning ~140 lines before the formal Practice section begins. The rubric flags >3 concepts before any exercise.

The section does include inline examples throughout, which partially mitigates the density. But for an A1.1 learner, this is a heavy block of new material.

**Fix:** Consider splitting the frequency adverbs (section «Слова частоти: Відповіді на "Коли?"», lines 169-200) into the Practice section, or adding a mini-exercise after the question words list.

### Issue 6: Opening Lacks Explicit Warmth [Warmth]

**Location:** Content lines 11-18

The module opens with «Чому це важливо?» followed by "Conversation requires questions, not just statements." This is functional but not warm. For an A1.1 beginner who may be nervous, a warm greeting ("Great job getting this far!") or encouragement before diving into content would improve the emotional arc.

### Issue 7: Missing "Investigative Journalist" Roleplay [Plan Compliance]

**Location:** Plan persona specifies `role: Investigative Journalist` and the plan's production section calls for "Roleplay: 'The Investigative Journalist' (Persona)." The content in section «Застосування: Розмова в реальному житті» has café and social scenarios but no explicit "Investigative Journalist" activity.

### Issue 8: Thematic Duplication in Callout Boxes

Both [!warning] «Пастка з "Do"» (line 27) and [!myth-buster] «Міф про "Do"» (line 185) address the same concept (English speakers trying to translate "do"). The myth-buster box adds the step-by-step breakdown which is genuinely useful, but the warning box's content is already covered in the preceding prose (lines 23-25). Consider whether the [!warning] box is necessary given the prose already covers the point.

---

## Factual Verification

| Claim | Source | Verdict |
|-------|--------|---------|
| No auxiliary "do/does" in Ukrainian questions | Standard Ukrainian grammar | **Correct** |
| «Не» placement before the negated word | Standard Ukrainian grammar §4.3.1 | **Correct** |
| Double negation with «ніколи»: «Я ніколи не читаю.» (line 183) | Standard Ukrainian grammar — required, not optional | **Correct** |
| Animals use «хто» not «що»: «В українській граматиці тварини є "істотами".» (line 239) | Animacy category in Ukrainian grammar | **Correct** |
| ALF Ukrainian dub from 1990s: «У 1990-х роках американський серіал "ALF" переклали українською.» (line 345) | Cultural reference — ALF US run 1986-1990, Ukrainian dub in 1990s | **Correct** |
| «Цей дубляж — це шедевр перекладу! Він сформував почуття гумору цілого покоління.» (line 345-346) | Strong superlative claim, but widely attested in Ukrainian popular culture | **Plausible** (not fabricated, but "шедевр" and "ціле покоління" is hyperbolic; acceptable for cultural engagement) |
| ALF quote: «Ти не любиш котів? Ти просто не вмієш їх готувати!» (line 349) | Confirmed in research notes | **Correct** |
| «Так» can mean "so" in other contexts (line 125) | Standard Ukrainian — «так» as intensifier/connector | **Correct** |
| Verb "to be" omitted in present tense: «Хто це?» literally "Who this?" (line 154) | Standard Ukrainian present-tense copula deletion | **Correct** |

No factual errors found. All grammar explanations are accurate per Ukrainian State Standard §4.3.1.

---

## Verification Summary

### Plan Compliance
- **Sections:** All 5 content_outline sections present as H2 headers. Section «Вступ: Мистецтво ставити питання» matches meta (not the older plan.yaml section name). **PASS**
- **Vocabulary scope:** All required items (чи, що, хто, де, коли, не, так, ні) present. All recommended items (куди, звідки, чому, як, скільки, завжди, ніколи) present plus extras. **PASS**
- **Grammar scope:** No scope creep. Stays within yes/no questions, question words, negation with «не». Does not introduce genitive negation (a1-11) or complex questions (a1-14). **PASS**
- **Objectives:** All 4 objectives addressed. **PASS**
- **Persona:** "Patient Supportive Tutor" voice present. "Investigative Journalist" role MISSING. **PARTIAL**

### Colonial Framing Check
No Russian comparisons found. All L1 comparisons are with English (appropriate for L2 English→Ukrainian). **PASS**

### LLM Fingerprint Check
- Structural monotony: **PASS** — each H2 section opens differently
- Example batching: **PASS** — mix of bullets, dialogues, drills, tables
- "Це не просто" pattern: **PASS** — not found
- Abstract noun stacking: **PASS** — not found
- Generic AI clichés: **PASS** — none found
- Callout monotony: **MINOR** — two callouts about "Do" trap, different box types but same theme

### Section Coverage Verification
- Section «Вступ: Мистецтво ставити питання» — reviewed for opening warmth, IPA issues, "Do" trap coverage
- Section «Граматика: Як будувати питання» — reviewed for density/pacing, question word coverage, IPA accuracy
- Section «Практика: Інтонація та конструктор» — reviewed for drill quality, animacy practice, visualization
- Section «Застосування: Розмова в реальному житті» — reviewed for scenario quality, missing Investigative Journalist roleplay
- Section «Культурний контекст: Ввічливість і гумор» — reviewed for register explanation, ALF cultural hook accuracy, softening «ні»

### "Would I Continue?" Test (Beginner)
| Question | Result |
|----------|--------|
| Did I feel overwhelmed? | Partial — Grammar section is dense (6+ concepts before practice) |
| Were instructions clear? | **Pass** — always knew what to do |
| Did I get quick wins? | **Pass** — early examples, manageable chunks |
| Was Ukrainian scary? | **Pass** — introduced gently with translations |
| Would I come back tomorrow? | **Pass** — ALF hook is engaging, overall encouraging |

4/5 Pass → Lesson Quality baseline 9, adjusted to 8 due to density and warmth concerns.

---

## Verdict

**CONDITIONAL PASS** — The module delivers solid pedagogical content with accurate grammar explanations, a strong cultural hook (ALF), and appropriate immersion balance. However, three issues require repair before approval:

1. **IPA errors** (dual stress on завжди in content + vocabulary, incorrect palatalization on скільки in vocabulary, missing stress on ніколи) — these directly misinform learners about pronunciation
2. **Two mechanical activities** (#5 and #8) with identical single-answer pattern — these fail to test the key learning distinction (не vs ні) and inflate activity count without adding pedagogical value
3. **"Lazy pronunciation" characterization** of «шо» — should be reframed as dialectal/informal

Secondary improvements (warmth, Grammar section pacing, missing Investigative Journalist roleplay) would elevate the module but are not blocking.