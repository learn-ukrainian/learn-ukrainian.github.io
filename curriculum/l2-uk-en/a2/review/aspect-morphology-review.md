<!-- content-hash: c2f954b44418 -->
**Reviewed-By:** claude-opus-4-6

---

## Scores

| # | Dimension | Score | Evidence Summary |
|---|-----------|-------|------------------|
| 1 | Plan Compliance | 7/10 | Missing виходити/вийти pair explicitly required by plan; all other sections present |
| 2 | Ukrainian Language | 8/10 | Generally strong; «сто відсотків фінальний» unnatural; «дуже чудову і цікаву» mildly overintensified |
| 3 | English Language | 8/10 | Clear and warm throughout but occasionally overwrought: "immense power", "glorious", "master key to unlocking", "grammatical architecture of true fluency" |
| 4 | Lesson Quality | 8/10 | Good structure with warm opening, clear examples, cultural grounding; but Підсумок lacks celebration/validation moment |
| 5 | Richness | 9/10 | Proverb, hospitality dialogue, morning narrative, evening narrative, cultural notes, good variety |
| 6 | Activity Quality | 7/10 | Critical factual error: quiz labels казати/сказати as suppletive when content correctly teaches it as regular prefix (Кафе Птах); mark-the-words has пішов appearing twice but listed once |
| 7 | Vocabulary Quality | 7/10 | IPA error: ʍ (voiceless labial-velar fricative, non-Ukrainian sound) used for вставати/встати instead of ʋ |
| 8 | Immersion Balance | 9/10 | 52.9% measured — squarely in the 50-60% target for A2 M01-20 |
| 9 | LLM Fingerprint | 7/10 | 4 consecutive prefix subsections all start "Префікс **X**..."; 6+ "Let's" pattern instances; no egregious AI clichés |
| 10 | Factual Accuracy | 8/10 | Grammar rules accurate; but activity mislabels a regular prefixal pair as suppletive, contradicting the content |
| 11 | Humanity & Warmth | 8/10 | Good opening with Привіт!, direct address throughout, encouragement present, but ending is informational rather than celebratory |
| 12 | Colonial Framing | 10/10 | No Russian comparisons detected. Ukrainian presented entirely on its own terms |

---

## Critical Issues Found

### Issue 1: Activity Factual Error — казати/сказати mislabeled as suppletive (CRITICAL)

**Location:** Activities YAML, lines 186-187

The quiz question asks «Як правильно утворити доконаний вид від дієслова 'казати'?» and the explanation states: «Слово 'казати' має суплетивну (нерегулярну) пару 'сказати'.»

This is **factually wrong** and directly contradicts the content itself. In Section «Творення префіксами та правило правопису», line 95, the content correctly presents казати → сказати as a regular prefixal formation per the Кафе Птах rule (с- before к). The pair казати/сказати shares the same root каз- and is formed with the regular prefix с-. It is NOT suppletive.

The suppletive pair involving "сказати" is говорити/сказати (different roots говор- and каз-), which the content correctly identifies in Section «Творення суфіксами та суплетивні пари» at line 208.

**Fix:** Change the explanation to: «За правилом 'Кафе Птах', перед літерою К префікс з- змінюється на с-, тому казати → сказати.» This aligns with the content's own teaching.

### Issue 2: Missing Plan-Required Suppletive Pair виходити/вийти

**Location:** Section «Творення суфіксами та суплетивні пари»

Both the plan and meta explicitly require the suppletive pair «виходити – вийти» as a high-frequency irregular pair from the State Standard. Grep confirms this pair is entirely absent from the content. The section covers говорити/сказати, шукати/знайти, брати/взяти, сідати/сісти, лягати/лягти, вставати/встати — but omits виходити/вийти.

**Fix:** Add виходити/вийти to the suppletive pairs list in Section «Творення суфіксами та суплетивні пари» with a contextual example sentence.

### Issue 3: IPA Error — ʍ in Vocabulary

**Location:** Vocabulary YAML, line 7

The entry for вставати/встати has IPA `[ʍstɑˈʋɑtɪ / ˈʍstɑtɪ]`. The symbol ʍ is a voiceless labial-velar fricative (found in some English dialects of "which") and does NOT exist in Ukrainian phonology. The correct symbol for Ukrainian в is ʋ (labiodental approximant).

**Fix:** Replace ʍ with ʋ → `[ʋstɑˈʋɑtɪ / ˈʋstɑtɪ]`

---

## Additional Issues

### Issue 4: Unnatural Ukrainian — «сто відсотків фінальний»

**Location:** Section «Підсумок», line 341

The phrase «сто відсотків фінальний, успішний результат» uses "сто відсотків" as an adverb modifying an adjective, which is unnatural in Ukrainian. A native speaker would say «стовідсотковий результат» (compound adjective) or «повністю завершений результат».

**Fix:** Replace «сто відсотків фінальний, успішний результат» with «повністю завершений, успішний результат» or «стовідсотковий результат».

### Issue 5: Missing Celebration Ending

**Location:** Section «Підсумок», lines 337-353

The Підсумок section provides a solid factual summary and self-check questions — good pedagogically. However, it lacks a warm celebration moment. Grep for "Вітаємо", "You can now", "Congratulations", and "Чудова робота" returns no matches. For an A2 beginner module, the ending should have an explicit progress validation: "You can now identify and form aspectual pairs!" or "Вітаємо! Тепер ви знаєте, як утворюються видові пари!"

**Fix:** Add a warm closing paragraph before the self-check questions: "Вітаємо! You can now identify aspect from morphology, form perfective verbs with prefixes, and recognize suppletive pairs. This is a major milestone in your Ukrainian journey!"

### Issue 6: Structural Monotony in Prefix Subsections

**Location:** Section «Творення префіксами та правило правопису», lines 71, 102, 114, 133

Four consecutive H3 subsections all open with the identical pattern "Префікс **X** ...":
- Line 71: «Префікс **з-** є одним із найважливіших інструментів...»
- Line 102: «Префікс **на-** часто використовується...»
- Line 114: «Префікс **по-** неймовірно універсальний...»
- Line 133: «Префікс **про-** часто несе нюанс...»

While structurally logical for a catalogue of prefixes, 4/4 identical openings triggers the structural monotony gate.

**Fix:** Vary at least 2 of the 4 openings. For example, start one with a question: «А що робить **на-**?» or start with an example first, then name the prefix.

### Issue 7: "Let's" Pattern Repetition

**Location:** Throughout Sections «Творення префіксами та правило правопису», «Практика: Помилки та вибір аспекту», «Культурний контекст та діалоги»

Six or more instances of "Let's" as a section/paragraph opener: "Let's explore" (line 67), "Let's look at" (lines 73, 116, 292), "Let's use the pair" (lines 234, 240), "Let's try another one" (line 260), "Let's practice" (line 228). This creates a robotic cadence in the English scaffolding.

**Fix:** Replace at least 3 instances with varied structures: "Consider...", "Now watch what happens with...", "Here's how...", "Take a close look at...".

### Issue 8: Overwrought English Rhetoric

**Location:** Lines 12, 16, 56, 316, 323

The English scaffolding occasionally veers into hyperbolic territory inappropriate for calm A2 instruction:
- Line 12: «Mastering verb formation gives you the immense power to express precise results»
- Line 16: «reached its glorious, completed end»
- Line 56: «Ви почнете бачити математичну красу української морфології»
- Line 316: «You now have the master key to unlocking Ukrainian verbs»
- Line 323: «you are building the grammatical architecture of true fluency»

For A2 learners, the tone should be encouraging but grounded, not grandiose.

**Fix:** Tone down 2-3 of these: "immense power" → "the ability"; "glorious, completed end" → "completed end"; "master key to unlocking" → "a strong foundation for".

---

## Factual Verification

### Grammar Rules Verified:
- **Кафе Птах rule** (з- → с- before к, п, т, ф, х): Correctly explained and exemplified. Examples спитати, сформувати, сховати, сказати all correct. ✅
- **Perfective cannot be present tense**: Correctly stated in the [!observe] box, line 59. ✅
- **Буду + imperfective only**: Correctly explained in Section «Практика: Помилки та вибір аспекту», lines 250-258. Error examples are accurate. ✅
- **Imperative aspect nuance**: Correctly presented. Imperfective for polite invitation, perfective for direct order — culturally accurate. ✅
- **Suffixes -ва-, -ува-**: Correctly explained as creating imperfective forms. Examples (відкрити→відкривати, забути→забувати) are accurate. ✅
- **Suppletive pairs**: говорити/сказати, шукати/знайти, брати/взяти — all genuine suppletive pairs. ✅

### Callout Box Verification:
- **[!observe]** (line 58): Perfective verbs cannot be present tense — factually accurate. ✅
- **[!warning]** (line 97): Common error "зпитати"/"зформувати" — accurate, relevant. ✅
- **[!fact]** (line 140): Multiple perfective meanings from one root (зробити, переробити, заробити) — factually accurate, all real verbs. ✅
- **[!tip]** (line 223): Write pairs together in notebook — sound pedagogical advice. ✅
- **[!culture]** (line 287): Imperfective for hospitality invitations (Сідайте!, Беріть!, Їжте!) — culturally accurate. Perfective forms would indeed sound harsh. ✅

### Proverb Verification:
- «Кіне́ць — ді́лу віне́ць» (line 16): This is a real Ukrainian proverb. ✅

### Flagged Factual Issue:
- Activity quiz (line 187): labels казати/сказати as "суплетивну (нерегулярну) пару" — **INCORRECT**. This is regular prefixal formation. See Critical Issue 1 above.

---

## Verification Summary

| Check | Status | Notes |
|-------|--------|-------|
| Plan sections present | PARTIAL | All 5 H2 sections present; missing виходити/вийти pair |
| Vocabulary coverage | PASS | All 14 required pairs present in vocab YAML |
| Recommended vocab | PASS | All 5 recommended terms (префікс, суфікс, корінь, основа, утворення) present |
| Colonial framing | PASS | No Russian comparisons found |
| Russianisms | PASS | No кушать/красивий/прекрасне/приймати участь detected |
| LLM fingerprints | PARTIAL | No AI clichés, but structural monotony in prefix subsections and "Let's" repetition |
| Immersion target | PASS | 52.9% within 50-60% range |
| Activity count | PASS | 12 activities (target met) |
| Engagement boxes | PASS | 5 callout boxes (exceeds minimum) |
| IPA accuracy | FAIL | ʍ symbol in vocab is non-Ukrainian |
| Activity accuracy | FAIL | Factual error in quiz explanation (казати/сказати ≠ suppletive) |
| Would-I-Continue test | 4/5 | Warm opening ✅, clear instructions ✅, quick wins ✅, Ukrainian not scary ✅, but ending lacks celebration |
| Emotional safety arc | PARTIAL | Welcome ✅, curiosity ✅, quick wins ✅, encouragement ✅ in body — but no progress marker at end |

---

## Verdict

**REVISE** — 3 critical issues require targeted repair:

1. **Activity fix** (Critical): Correct the quiz explanation for казати/сказати from "suppletive" to Кафе Птах prefixal rule. This is a factual contradiction with the lesson content that would confuse learners.
2. **Plan compliance** (Critical): Add виходити/вийти suppletive pair to Section «Творення суфіксами та суплетивні пари» with example sentences.
3. **IPA fix** (Critical): Replace ʍ with ʋ in вставати/встати vocabulary entry.

Additionally recommended (non-blocking):
4. Fix «сто відсотків фінальний» → natural Ukrainian equivalent in Підсумок.
5. Add celebration closing before self-check questions.
6. Vary 2+ of the 4 prefix subsection openings to break structural monotony.
7. Reduce 3+ "Let's" instances to varied alternatives.

The module's core pedagogy is solid — the aspect family analogy works well, the Кафе Птах mnemonic is excellent, the hospitality dialogue and morning narrative are culturally rich and pedagogically effective. The critical issues are isolated and surgically fixable. After repair, this module should pass cleanly.