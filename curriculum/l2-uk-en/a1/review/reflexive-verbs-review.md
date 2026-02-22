<!-- content-hash: 10c1fce45519 -->
**Reviewed-By:** claude-opus-4-6

---

## Scores

| # | Dimension | Score | One-line justification |
|---|-----------|-------|----------------------|
| 1 | Lesson Quality | 8/10 | Warm tutor voice with strong arc, but inconsistent teaching undermines learner confidence |
| 2 | Factual Accuracy | 8/10 | Grammar rules are mostly accurate, but the -ся/-сь rule is taught then contradicted in examples |
| 3 | Immersion Balance | 9/10 | 22.3% immersion appropriate for A1.1, English scaffolding well-placed |
| 4 | Language Quality | 7/10 | Colonial framing at line 398; multiple instances where examples violate the module's own Golden Rule |
| 5 | Activity Quality | 8/10 | 10 varied activities with good coverage, but missing "знайомитися" practice from the plan |
| 6 | Richness | 8/10 | Good cultural hooks (Вибачаюсь debate, Maxim story), but the "Type 4" addition is unplanned scope creep |
| 7 | Vocabulary Accuracy | 8/10 | IPA errors for "вчитися" and "втомлюватися" using [ʍ] instead of [u̯] |
| 8 | LLM Fingerprint | 8/10 | Varied section openings and good narrative voice, but example formatting is fairly uniform (bold Ukr + English) across sections |
| 9 | Humanity & Warmth | 9/10 | Strong direct address, encouraging tone, good "Would I Continue?" performance |

---

## Critical Issues Found

### Issue 1 (CRITICAL — Colonial Framing): Line 398 defines Ukrainian pronunciation via Russian comparison

**Location:** Section «Культура: Секрети вимови», line 398

**Verbatim quote:** «This sound instantly distinguishes a native Ukrainian speaker. In Russian, the reflexive ending is hard and short. In Ukrainian, it is **soft** and **long**.»

**Problem:** This sentence defines the Ukrainian phonetic feature by contrast with Russian, which is colonial framing per review protocol. The Ukrainian [t͡sʲːa] sound should be presented on its own terms — as a distinct Ukrainian phonetic feature — not as "different from Russian."

**Fix:** Replace the Russian comparison with a standalone description. For example: "This sound is one of the defining phonetic fingerprints of the Ukrainian language. The -ться ending produces a long, soft [t͡sʲːa] — stretch the 'ts' out like a gentle buzz, and keep it soft by raising your tongue."

---

### Issue 2 (CRITICAL — Internal Inconsistency): -ся/-сь "Golden Rule" contradicted by the module's own examples

**Location:** Section «Теорія: Відмінювання та групи» teaches the rule at lines 125-126; contradicted in Sections «Теорія: Відмінювання та групи» and «Практика: Дія на себе чи на іншого?»

The module explicitly teaches:
- **Rule 1:** Use **-ся** after consonants (line 125)
- **Rule 2:** Use **-сь** after vowels (line 126)

But then the module uses -ся after vowels in its own examples:

| Line | Verbatim text | Stem ends in | Should be (per rule) |
|------|---------------|-------------|---------------------|
| 213 | «Ми сміємося з жарту.» | vowel "о" | Ми сміємось з жарту |
| 214 | «Ми сміємося з тебе.» | vowel "о" | Ми сміємось з тебе |
| 327 | «Я вчуся у школі.» | vowel "у" | Я вчусь у школі |
| 333 | «Я займаюся спортом.» | vowel "ю" | Я займаюсь спортом |
| 334 | «Я займаюся українською мовою.» | vowel "ю" | Я займаюсь українською мовою |

**Why this matters:** At A1 level, consistency is paramount. A learner who just memorized the Golden Rule will see these examples and think they made a mistake — or worse, that the rule is unreliable. The module itself notes (line 130) that -ся is "also allowed after vowels," but presents -сь as the primary rule. Examples must match the primary rule being taught.

**Fix:** Change all 5 examples to use -сь after vowels, matching the module's own conjugation tables (which correctly use -сь).

---

### Issue 3 (Significant — Pacing): Section «Теорія: Відмінювання та групи» introduces 13+ new verbs without practice breaks

**Location:** Lines 118-217

Section «Теорія: Відмінювання та групи» introduces the following verbs across Types 1-4: вмиватися, одягатися, зупинятися, зустрічатися, цілуватися, вітатися, називатися, подобатися, сміятися, навчатися, хвилюватися, боятися, надіятися. That's 13 new lexical verbs in one section, significantly exceeding the A1 guideline of ≤5-7 new words per section.

Additionally, "Type 4: Emotional States" (line 202) is not in the plan's content outline — neither the meta nor the .md frontmatter mention a fourth type. The plan specifies 3 types: True Reflexive, Reciprocal, and Lexicalized. This is scope creep that exacerbates the cognitive overload.

**Fix:** Either (a) move Types 3 and 4 to their own brief section or subsection with practice between groups, or (b) merge Type 4 into Type 3 (Lexicalized) since emotional verbs are also lexicalized reflexives, and trim to the plan's 3-type structure.

---

### Issue 4 (Significant — Plan Compliance): Missing "вмиватися" conjugation table

**Location:** Section «Теорія: Відмінювання та групи»

The plan (meta, line 19-20) requires: "Conjugation Table: Full present tense paradigm for 'дивитися' and 'вмиватися' (Standard alignment)." The content provides a full conjugation table for дивитися (lines 153-160) and a paradigm for сміятися (lines 134-141), but no conjugation table for вмиватися. Since вмиватися is a first-conjugation verb (-ати), providing its paradigm alongside the second-conjugation дивитися would show learners both patterns.

**Fix:** Add a short conjugation table for вмиватися (вмиваюсь, вмиваєшся, вмивається, вмиваємось, вмиваєтесь, вмиваються), or replace the сміятися table with вмиватися to match the plan.

---

### Issue 5 (Moderate — Plan Compliance): Missing "знайомитися" from content and activities

**Location:** Entire module

The plan (plans/a1/reflexive-verbs.yaml, line 77) lists "знайомитися (to get acquainted) — reciprocal interaction" under recommended vocabulary. The plan's practice section (line 54-55) also specifies: "Social Interaction: Using 'знайомитися' and 'вітатися' in short dialogues." The content uses вітатися in the story but never introduces знайомитися — not in the lesson text, not in the vocabulary file, and not in any activity.

**Fix:** Add знайомитися to the Reciprocal section (Type 2) with an example like «Ми знайомимось у кафе» and to the vocabulary file.

---

### Issue 6 (Moderate — IPA Error): Vocabulary file uses [ʍ] for initial "в" in consonant clusters

**Location:** Vocabulary file, lines 21 and 77

- Line 21: вчитися → `[ˈʍt͡ʃɪtɪsʲɑ]` — the [ʍ] (voiceless labiovelar fricative, as in English "which") is incorrect for Ukrainian. The initial "в" before a consonant is typically realized as [u̯] (non-syllabic u).
- Line 77: втомлюватися → `[ˈʍtɔmlʲuʋɑtɪsʲɑ]` — same issue.

**Fix:** Replace [ʍ] with [u̯] in both entries: `[u̯ˈt͡ʃɪtɪsʲɑ]` and `[u̯ˈtɔmlʲuʋɑtɪsʲɑ]`.

---

### Issue 7 (Minor — State Standard Alignment): Conjugation table uses shortened forms as primary

**Location:** Section «Теорія: Відмінювання та групи», lines 153-160

The State Standard (§4.2.4.1) lists the full forms as the primary paradigm: дивлюся, дивимося, дивитеся. The content table presents the shortened forms (дивлюсь, дивимось, дивитесь) as primary and only notes the full form as a "variant" for дивимось. For A1, teaching one consistent form is fine, but the module should acknowledge that the Standard uses the full forms, or at least not present them as mere "variants."

---

## Factual Verification

### Grammar Rules

| Claim | Accurate? | Notes |
|-------|-----------|-------|
| -ся is historically from "себе" | ✅ Yes | Well-established etymology |
| -ся after consonants, -сь after vowels | ✅ Yes | Correct rule, but both forms accepted after vowels |
| -ться pronounced as [t͡sʲːa] | ✅ Yes | Correct Ukrainian pronunciation |
| "подобатися — there is no standalone подобати" | ⚠️ Approximate | "подобати" exists in dialectal/archaic use, but is absent from modern standard Ukrainian; claim is acceptable for A1 simplification |
| "сміятися з" as the standard preposition | ✅ Yes | Correct; "над" exists in literary register but "з" is standard |
| "Вибачаюсь" literally means "I excuse myself" | ✅ Yes | This is the standard linguistic analysis |

### Callout Box Verification

| Box | Type | Claim | Verified? |
|-----|------|-------|-----------|
| Line 101 | [!warning] | "Don't double up" -ся + себе | ✅ Correct |
| Line 162 | [!tip] | -ся is strictly a suffix in Ukrainian | ✅ Correct |
| Line 197 | [!observe] | дивитися conjugation examples | ✅ Correct forms |
| Line 246 | [!myth-buster] | Can use transitive and reflexive in one sentence | ✅ Correct, natural Ukrainian |
| Line 415 | [!culture] | "Вибачте" / "Пробачте" as gold standard | ✅ Correct |

No fabricated claims found in callout boxes.

---

## Verification Summary

| Check | Result | Details |
|-------|--------|---------|
| Colonial framing | ❌ FOUND | Line 398: Russian comparison for -ться pronunciation |
| Russianisms | ✅ Clear | No Russianisms detected in Ukrainian text |
| Calques | ✅ Clear | No calques detected |
| Grammar scope violations | ⚠️ Minor | Imperative "хвилюйся" (line 295) is technically out of scope (module targets present tense) |
| LLM clichés | ✅ Clear | No "це не просто", no generic AI rhetoric detected |
| Structural monotony | ✅ Clear | Section openings are varied |
| Example plausibility | ✅ Clear | All Ukrainian example sentences are natural and plausible |
| Factual accuracy | ✅ Clear | Grammar explanations are accurate |
| Plan compliance | ⚠️ Gaps | Missing вмиватися conjugation table, missing знайомитися, unauthorized "Type 4" section |
| Internal consistency | ❌ FAIL | Module violates its own Golden Rule in 5+ examples |
| "Would I Continue?" test | 4/5 | Warm welcome ✅, Clear instructions ✅, Quick wins ✅, Ukrainian not scary ✅, but inconsistent rules would confuse me ⚠️ |

### Section Coverage

- Section «Розминка: Що таке зворотні дієслова?» — Strong mirror analogy, good etymology, clear redundancy warning. Well-scaffolded for A1.
- Section «Теорія: Відмінювання та групи» — Comprehensive but overloaded (13+ new verbs, unauthorized Type 4). Core conjugation teaching is solid. Internal -ся/-сь inconsistency is the main problem.
- Section «Практика: Дія на себе чи на іншого?» — Excellent Maxim story and gym dialogue. The transitive vs. reflexive contrast table is clear and effective. More -ся/-сь inconsistencies here.
- Section «Культура: Секрети вимови» — Good pronunciation guidance and Вибачаюсь debate. Colonial framing issue at line 398 needs fixing.

---

## Verdict

**REVISE** — 3 critical issues must be fixed before this module can pass:

1. **Remove colonial framing** at line 398 (present Ukrainian -ться pronunciation on its own terms)
2. **Fix -ся/-сь inconsistency** across 5+ examples (lines 213, 214, 327, 333, 334) to match the taught Golden Rule
3. **Trim "Type 4" scope creep** or integrate it into the plan's 3-type structure to reduce cognitive overload in Section «Теорія: Відмінювання та групи»

Additionally recommended:
- Add missing вмиватися conjugation table per plan
- Add знайомитися to content and vocabulary per plan
- Fix IPA [ʍ] → [u̯] in vocabulary file for вчитися and втомлюватися

The module has a genuinely warm, encouraging voice and strong pedagogical arc (mirror analogy → conjugation → practice story → pronunciation). The Maxim morning story and gym dialogue are excellent practice vehicles. The core content is sound — the fixes are primarily about consistency and plan compliance, not about rewriting.