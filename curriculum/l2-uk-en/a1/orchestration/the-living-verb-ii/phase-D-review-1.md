**Reviewed-By:** claude-opus-4-6

## Scores

| Dimension | Score | Evidence Summary |
|-----------|-------|-----------------|
| Plan Compliance | 8/10 | All 5 meta sections present. Missing the бачити/дивитися distinction from plan.yaml. |
| Lesson Quality | 9/10 | Warm, encouraging tutor voice. Good pacing overall, though Section «Презентація: Друга дієвідміна» packs 5 distinct concepts before practice. |
| Language Quality | 8/10 | Ukrainian grammar is correct throughout. Line 217 introduces a confusing exception (розуміти as Type 1) that could undermine pattern confidence at A1. |
| Activity Quality | 7/10 | 10 activities, 6 types. Activities 2 ("Я і моя дія") and 5 ("Знайди пару: Я роблю...") are near-identical match-ups testing the same skill with the same verbs. |
| Vocabulary Quality | 7/10 | 21 items covering all plan-required verbs. Two IPA errors: помилка has double stress mark, вчити uses wrong phonetic symbol (ʍ). |
| Immersion | 9/10 | 26.4% Ukrainian within A1.1 target range (20-40%). Good English scaffolding throughout. |
| Richness | 8/10 | 7 callout boxes (varied types), etymology hook, hospitality triad, dialogue. Herder quote attribution is unverifiable (see Factual Accuracy). |
| Humanity & Warmth | 9/10 | Strong warmth markers: "Вітаємо!" at open and close, inline encouragement, "You have doubled your verb power", progress celebration. |
| LLM Fingerprint | 9/10 | Section openings are varied. No "це не просто" patterns. Callout titles unique. Example formats vary (tables, bullets, dialogue). |
| Factual Accuracy | 7/10 | Grammar rules accurate. Herder quote (line 333) is unverifiable — likely a cultural paraphrase, not a documented translation from Herder's works. |

---

## Critical Issues Found

### Issue 1: Duplicate Match-Up Activities (Activity Quality — MAJOR)

**Location:** Activities file, activities 2 and 5

Activity 2 ("Я і моя дія", line 24-47) and Activity 5 ("Знайди пару: Я роблю...", line 228-252) are functionally identical match-up exercises. Both match infinitives to their "я" forms. The verb sets are the same 10 verbs in both. The only surface difference is that Activity 2 includes the pronoun "я" in the answer (e.g., "я говорю") while Activity 5 omits it (e.g., "говорю").

**Impact:** This is wasted exercise real estate. A learner who completes Activity 2 learns nothing new from Activity 5. Variety drops to 5 unique types out of 10 activities.

**Fix:** Replace Activity 5 with a different exercise type — e.g., a fill-in that tests other pronoun forms (ти, він, ми) instead of just "я", or a group-sort that separates mutation types (labial L vs consonant change vs no change). Actually, Activity 7 already covers mutation-type sorting, so a multi-pronoun conjugation drill would be more valuable.

### Issue 2: Vocabulary IPA Errors (Vocabulary Quality — MAJOR)

**Location:** Vocabulary file, lines 66 and 37

1. **помилка** (line 66): IPA is `` — contains TWO primary stress marks, which is phonetically impossible for a single word. Should be `` (stress on the second syllable only).

2. **вчити** (line 37): IPA is `` — the symbol **ʍ** represents a voiceless labial-velar fricative (the "wh" in some English dialects of "whistle"), which does not exist in Ukrainian phonology. Ukrainian **в** before a voiceless consonant is realized as a non-syllabic [u̯]. The correct IPA should be ``.

**Fix:** Correct both IPA transcriptions in the vocabulary file.

### Issue 3: Unverifiable Herder Quote (Factual Accuracy — MAJOR)

**Location:** Content file, line 333

The quote «Хто не любить своєї рідної мови? Той не заслуговує на ім'я людини.» is attributed to Йоганн Готфрід Гердер (Johann Gottfried Herder). While Herder did champion the connection between language and national identity in his German-language writings (notably *Abhandlung über den Ursprung der Sprache*, 1772), this specific Ukrainian-language quote does not appear to be a documented translation from any particular Herder passage. It reads like a Ukrainian cultural paraphrase that has been retroactively attributed to Herder — a common pattern in Ukrainian educational materials where inspirational quotes about language circulate with unreliable attributions.

This falls squarely into the "Named individuals and works — verify the attribution is correct" check for callout boxes. Presenting an unverified quote as a direct attribution in a `[!quote]` box is a factual accuracy risk.

**Fix:** Either (a) find and cite the specific Herder work this translates from, or (b) reattribute to a verified Ukrainian source about language and identity (e.g., Ivan Franko, who wrote extensively about мова), or (c) soften the attribution: "Ідею, яку приписують Гердеру..." (An idea attributed to Herder...).

### Issue 4: Confusing Exception in Practice Section (Language Quality — MODERATE)

**Location:** Content file, line 217

The text introduces розуміти as a confusing exception mid-exercise: «**розуміти** (to understand) → Ends in **-іти**. This is usually Type 1! **Я розумію**. (Language is full of surprises, but stick to the **-ати** vs **-ити** rule for now).»

At A1 level, learners are just building confidence in the -ати/-ити sorting rule. Introducing an exception in the practice section — the exact moment they should be reinforcing the pattern — undermines pedagogical safety. The parenthetical "Language is full of surprises" is dismissive rather than reassuring. Moreover, the phrasing "This is usually Type 1" is ambiguous: does it mean -іти verbs are usually Type 1 (incorrect — most are Type 2), or that розуміти specifically is Type 1?

**Fix:** Remove this example from the Section «Практика: Тренування форм» sorting drill. If the exception must be mentioned, move it to a `[!tip]` box in the Section «Презентація: Друга дієвідміна» with clear framing: "Most -іти verbs follow Type 2 (like сидіти). Розуміти is a rare exception — don't worry about it for now."

### Issue 5: Missing бачити/дивитися Distinction (Plan Compliance — MODERATE)

**Location:** Plan.yaml, section 2, point 5

The plan specifies: "Distinction between 'бачити' (to see - result/faculty) and 'дивитися' (to watch - process) to prevent semantic confusion in early sentence building." This distinction does not appear anywhere in the content. The word "дивитися" is entirely absent from the module.

The research notes (line 31) also flag this: "Ensure the distinction between *бачити*... and *дивитися*... is clear if *дивитися* is introduced."

**Fix:** Add a brief `[!tip]` box in the Section «Використання: Розповіді про дії» near the «Бачити — значить знати» culture note (line 279), contrasting: **бачити** = to see (result/ability), **дивитися** = to watch (process). A 2-3 sentence note with one example pair suffices.

### Issue 6: Untaught Verb Form in Dialogue (Language Quality — MINOR)

**Location:** Content file, line 294

The dialogue includes «Я йду (I am going) в кафе.» The verb **йти** (unidirectional motion) has not been taught in this module or its prerequisites (a1-06, a1-07). While the inline English translation "(I am going)" provides a crutch, A1 learners will wonder about the relationship between the taught **ходити** and the untaught **йду**. This could trigger confusion about when to use which form — a distinction that belongs to later modules.

**Fix:** Replace «Я йду» with a taught verb: «Я ходжу в кафе» (using the just-taught ходити form with its mutation), or simply restructure: «Я хочу каву.» to avoid motion verbs altogether in this dialogue.

---

## Factual Verification

### Grammar Rules (Core Track)

| Claim | Location | Verdict |
|-------|----------|---------|
| Type 2 uses vowel И/І in endings | Line 24, 60 | ✅ Correct |
| Labial L appears in я and вони forms | Line 128 | ✅ Correct (я роблю, вони роблять) |
| д→дж mutation in я form | Line 156-161 | ✅ Correct (сидіти→сиджу, ходити→ходжу) |
| їсти conjugation: я їм, ти їси, він їсть, ми їмо, ви їсте, вони їдять | Lines 189-194 | ✅ Correct |
| пити conjugation: я п'ю, ти п'єш, він п'є, ми п'ємо, ви п'єте, вони п'ють | Lines 180-185 | ✅ Correct |
| After hushing sounds (ч, ж, ш), write -ать not -ять | Line 86 | ✅ Correct (вони бачать) |
| спати behaves like Type 2 despite -ати ending | Line 126 | ✅ Correct (я сплю, ти спиш) |
| т→ч mutation: платити→плачу | Line 228 | ✅ Correct |
| с→ш mutation: просити→прошу | Line 229 | ✅ Correct |

### Callout Box Claims

| Claim | Location | Verdict |
|-------|----------|---------|
| «любити» may share PIE root with «люди» | Line 314 | ✅ Hedged appropriately ("Some linguists note it may share..."). The connection via PIE *lewbh-/*h₁lewdh- is debated but legitimate. |
| -ити ending comes from Proto-Slavic *-iti | Line 322 | ✅ Correct — well-established historical linguistics. |
| «їсти» preserves 1000-year-old forms from Kyivan Rus' | Line 201 | ✅ Correct — Old East Slavic їсти paradigm is largely preserved. |
| Herder quote on language and humanity | Line 333 | ⚠️ UNVERIFIABLE — see Issue 3. |
| Hospitality triad: їсти, пити, говорити | Line 328 | ✅ Culturally accurate, supported by research notes. |

---

## Section-by-Section Analysis

### Section «Вступ: Родина -ити» (lines 16-49)

Strong opening with «Вітаємо у світі дії!» — warm and orienting. Good bridge to previous module (First Conjugation). The five "star verbs" are introduced clearly. The `[!context]` box on «Подумайте про «Дію»» effectively explains that Ukrainian doesn't need helper verbs. Minor observation: the opening blockquote (lines 12-14) uses Ukrainian that's slightly above A1 level (e.g., «Вони будують ваш світ»), but the mix with bolded vocabulary makes it accessible.

### Section «Презентація: Друга дієвідміна» (lines 51-201)

The comparison table (lines 64-71) is excellent — clear visual distinction between Type 1 and Type 2. The `[!tip]` box «Секрет множини» (line 78) is pedagogically smart, giving a memorable rule of thumb. The `[!warning]` box «Не плутайте групи!» (line 102) addresses the #1 learner error with clear ✅/❌ examples.

However, this section is dense: it covers (1) side-by-side comparison, (2) full говорити conjugation, (3) labial L phenomenon, (4) д→дж mutation, and (5) two irregular verbs (їсти, пити). That's 5 distinct concepts spanning 150 lines before any practice. At A1, chunking to ≤2 concepts before practice is ideal. The content itself is well-written, but the cognitive load is high.

### Section «Практика: Тренування форм» (lines 203-245)

Good progression from sorting → mutation practice → sentence building. The sorting exercise (lines 209-218) provides quick wins. The mutation drill (lines 222-229) targets the trickiest aspect of the lesson. The sentence-building examples (lines 233-245) are clear and scaffold well.

The розуміти exception (line 217) is the weak point — see Issue 4.

### Section «Використання: Розповіді про дії» (lines 247-306)

The collocations section (lines 270-277) is practical and well-chosen. The dialogue (lines 289-305) is natural and uses appropriate verb forms — except for «Я йду» (see Issue 6). The dialogue effectively demonstrates multiple taught verbs in a real conversation context.

One strength: the dialogue ending «Так, із задоволенням!» on line 303 teaches a useful social phrase naturally.

### Section «Культурний контекст: Глибина слова» (lines 308-338)

The etymology of «любити» (lines 312-318) is well-hedged and engaging. The historical note about -ити (lines 320-324) gives learners a sense of connection to history. The hospitality triad (lines 326-328) is culturally authentic and ties the three core verbs together beautifully.

The Herder quote (line 333) is the section's weakness — see Issue 3.

---

## Verification Summary

| Check | Result |
|-------|--------|
| Russianisms | ✅ None found |
| Calques | ✅ None found |
| Colonial framing | ✅ None found — Ukrainian presented on its own terms |
| Grammar scope violations | ✅ No grammar from later modules introduced |
| Activity grammar accuracy | ✅ All 10 activities have correct answers and explanations |
| Activity duplicate detection | ❌ Activities 2 and 5 are near-identical |
| IPA accuracy (vocabulary) | ❌ 2 errors: помилка double stress, вчити wrong symbol |
| LLM fingerprint patterns | ✅ No structural monotony, no AI clichés |
| Plan section coverage | ⚠️ Missing бачити/дивитися distinction |
| Factual claims | ⚠️ 1 unverifiable attribution (Herder quote) |
| "Would I Continue?" test | ✅ 5/5 pass — encouraging, manageable, rewarding |

---

## Verdict

**PASS WITH REPAIRS**

This is a well-structured A1 module with strong pedagogical design, accurate grammar teaching, and warm tutor voice. The core content — conjugation tables, labial L explanation, mutation rules, and irregular verbs — is taught clearly and correctly. The cultural section adds genuine depth without overwhelming beginners.

**Required repairs before approval:**

1. **Replace Activity 5** with a non-duplicate exercise (e.g., multi-pronoun conjugation fill-in)
2. **Fix 2 vocabulary IPA errors** (помилка, вчити)
3. **Resolve Herder quote attribution** (verify, reattribute, or soften)
4. **Remove or relocate розуміти exception** from the Practice section
5. **Replace «Я йду» in dialogue** with a taught verb form
6. **Add brief бачити/дивитися note** to address plan gap

None of these repairs require structural rewriting. The module's foundation is solid.