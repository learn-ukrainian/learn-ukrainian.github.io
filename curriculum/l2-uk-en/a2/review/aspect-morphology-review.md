<!-- content-hash: 22bc5dc2e22f -->
**Reviewed-By:** claude-opus-4-6

# Phase D.1 Review: aspect-morphology (A2-15)

**Module:** Aspect Morphology: Prefixes and Suffixes
**Level:** A2 | **Band:** 1 (M01-20) | **Target immersion:** 50-60%
**Word count:** 3722 / 3000 (124.1%) — above target ✅
**Activities:** 12 | **Vocabulary:** 28 | **Engagement boxes:** 5

---

## Pre-Screen Confirmation

### D.0 Finding 1: [RUSSIANISM] "давайте подивимося"
**CONFIRMED — 3 occurrences found:**
- Line 65: «Давайте уважно подивимося на **анато́мію сло́ва**»
- Line 153: «Давайте подивимося на критичні дієслова для ранкової рутини:»
- Line 325: «Давайте подивимося на ще одну історію, яка показує красу українських дієслів.»

**Analysis:** "подивимося" is the future indicative first-person plural form. After "давайте," Ukrainian requires the imperative form: **подивімося**. The construction "давайте + indicative" is a Russian calque ("давайте посмотрим"). Standard Ukrainian: "Подивімося" or "Давайте подивімося."

### D.0 Finding 2: [LLM_FILLER] "Let's explore" at ~line 62
**CONFIRMED** at line 67: «Let's explore the most frequent ones you must know.»
Generic LLM transition. Should be replaced with specific teaching content (e.g., "Here are the four most frequent prefixes you need for daily conversation.").

---

## Scores

| # | Dimension | Score | Key Evidence |
|---|-----------|-------|-------------|
| 1 | Plan Compliance | 7/10 | Missing виходити/вийти suppletive pair (required by plan). Missing vowel shift (-о-→-і-) detail. No IPA on any vocabulary. |
| 2 | Language Quality | 7/10 | "Давайте подивимося" Russianism x3. "сто відсотків фінальний" (line 336) is non-standard. Narrative/analysis verb mismatch (зачинив vs закрив). |
| 3 | Factual Accuracy | 8/10 | Grammar rules correctly taught. One activity explanation incorrectly labels казати→сказати as "suppletive" when the lesson teaches it as prefixal (Кафе Птах). |
| 4 | Activity Quality | 7/10 | Match-up: 12 pairs (plan: 15+). Fill-in: 8 items (plan: 12+). Quiz explanation error (казати/сказати). Overall variety excellent (11 unique types). |
| 5 | Richness | 6/10 | Zero grammar tables in a grammar module. Audit richness 64% (threshold 95%). Gaps: engagement 3/5, cultural 0/3, dialogues 0/4, tables 0/2. |
| 6 | LLM Fingerprint | 8/10 | One "Let's explore" filler. Section openings are varied. No structural monotony. No generic AI clichés. "Давайте подивимося" x3 is repetitive but is a Russianism issue not an LLM pattern. |
| 7 | Lesson Quality | 8/10 | "Would I Continue?" test: 4/5 Pass. Warm opening, clear scaffolding, good examples. Missing table-based visual aids for grammar patterns. Practice section slightly late (section 4 of 5). |
| 8 | Immersion | 9/10 | 52.6% — well within Band 1 target (50-60%). English used for theory, Ukrainian for examples and dialogues. Appropriate scaffolding. |
| 9 | Humanity & Warmth | 8/10 | Opens with "Приві́т!", uses proverb hook. Culture callout about hospitality is excellent. Could use 1-2 more encouragement moments ("You're making great progress!"). |
| 10 | Vocabulary Quality | 8/10 | All 14 required pairs + 5 recommended terms present. Vocabulary YAML correctly structured. відчиняти/відчинити used in dialogue (line 296-297) but not taught or in vocab — potential confusion. |

---

## Critical Issues Found

### Issue 1: RUSSIANISM — "давайте подивимося" (3 occurrences)
**Severity:** HIGH
**Lines:** 65, 153, 325
**Evidence:**
- Line 65: «Давайте уважно подивимося на **анато́мію сло́ва**»
- Line 153: «Давайте подивимося на критичні дієслова для ранкової рутини:»
- Line 325: «Давайте подивимося на ще одну історію, яка показує красу українських дієслів.»

**Fix:** Replace all three with "Подивімося" (imperative form) or "Давайте подивімося." A grammar module about verb morphology must not contain Russicisms in its own prose.

### Issue 2: Missing Plan-Required Content — виходити/вийти
**Severity:** HIGH
**Lines:** N/A (absent)
**Evidence:** The plan file (both meta and plan YAML) explicitly lists: `Irregular (Suppletive) Pairs: Presentation of high-frequency irregular roots from the State Standard, specifically 'виходити – вийти' and 'забувати – забути'.` The content in section «Творення суфіксами та суплетивні пари» at line 195 presents говорити/сказати, шукати/знайти, and брати/взяти as suppletive pairs — but виходити/вийти is completely absent.

**Fix:** Add виходити/вийти to the suppletive pairs list in section «Суплетивні пари» with example sentences, and add it to vocabulary YAML.

### Issue 3: Activity Factual Error — казати/сказати mislabeled as suppletive
**Severity:** HIGH
**Lines:** Activities YAML ~line 187
**Evidence:** Quiz explanation states: «Слово 'казати' має суплетивну (нерегулярну) пару 'сказати'.» This directly contradicts the lesson content at line 95 which correctly teaches казати→сказати as a **prefixal** formation following the Кафе Птах rule: `казати (to say) → **с**каза́ти (*від к*)`. The answer (сказати) is correct, but the explanation is wrong — it's a regular Кафе Птах prefix, not suppletive. A learner studying this quiz would receive contradictory information about the very morphological system the module teaches.

**Fix:** Change explanation to: «За правилом 'Кафе Птах', літера К — у фразі 'Кафе Птах', тому префікс з- змінюється на с-: казати → сказати.»

### Issue 4: Narrative/Analysis Inconsistency — зачинив vs закрив
**Severity:** MEDIUM
**Lines:** 305, 307
**Evidence:** The morning rhythm narrative at line 305 uses «**зачини́в** вхідні двері (*Результат*)» (from зачинити). But the analysis at line 307 says: «Notice how the perfective verbs (**встав**, **вми́вся**, **одягну́вся**, **закри́в**) act like the strong beats of a drum...» The analysis references **закри́в** (from закрити), which is a different verb than what appears in the narrative. A learner trying to match the analysis to the narrative would not find "закрив" anywhere.

**Fix:** Either change the narrative to use «закри́в» (matching the taught vocabulary pair закривати/закрити) or change the analysis to reference «зачини́в».

### Issue 5: No Grammar Tables in a Grammar Module
**Severity:** MEDIUM
**Lines:** N/A (absent throughout)
**Evidence:** The module teaches 4 prefixes (з-, на-, по-, про-), 2 suffix patterns (-ва-, -ува-), suppletive pairs, and future tense rules — all entirely as running prose with bullet-pointed examples. Zero comparison tables exist. For A2 grammar content, tables are critical visual aids (see Tier 1 rubric: "Visual Aids: Tables, charts for grammar" is A+ standard). The richness audit shows tables: 0/2.

**Fix:** Add at minimum: (1) a prefix summary table showing prefix → semantic hint → example pair, (2) a future tense formation table contrasting imperfective future (буду + inf.) vs perfective future (present-tense form of perfective verb).

### Issue 6: Missing IPA on First Occurrence
**Severity:** LOW-MEDIUM
**Lines:** Throughout
**Evidence:** The plan meta (line 37) states: «Ensure all new vocabulary includes IPA on the first occurrence only.» The research notes also state: «Ensure IPA is only used on the first occurrence of new words.» The content uses Unicode stress marks (e.g., видові́ па́ри, пре́фікс) — which is practical — but NO IPA transcription exists for any vocabulary item. The stress marks are a reasonable A2 approach, but this deviates from the explicit plan instruction.

**Fix:** Either add IPA for at least the grammatical metalanguage terms (префікс, суфікс, корінь, основа, утворення) on first occurrence, or document the decision to use stress marks instead.

---

## Grammar Rule Verification

| Rule | Correct? | Evidence |
|------|----------|---------|
| Perfective cannot be in present tense | ✅ | Line 59: correctly explained in [!observe] callout |
| Кафе Птах rule (з→с before к,п,т,ф,х) | ✅ | Lines 88-96: correctly taught with examples сформувати, спитати, сховати, сказати |
| буду + only imperfective | ✅ | Lines 245-258: correctly taught with error examples |
| Imperfective imperative = polite | ✅ | Lines 264-283: culturally accurate distinction |
| Suffix -ва-/-ува- creates imperfective | ✅ | Lines 149-177: correctly demonstrated |
| говорити/сказати = suppletive | ✅ | Line 203: different roots, correctly labeled |
| казати/сказати = prefixal | ✅ in content, ❌ in activity | Content line 95 correct; activity line 187 incorrectly calls it suppletive |

---

## Factual Verification

### Callout Box Verification

| Callout | Line | Claim | Verdict |
|---------|------|-------|---------|
| [!observe] | 58 | Perfective verbs cannot be used in present tense | ✅ Accurate |
| [!warning] | 97 | Common error: writing "зпитати" instead of "спитати" | ✅ Accurate — real learner error |
| [!fact] | 140 | роби́ти → зроби́ти, перероби́ти, зароби́ти | ✅ All real verbs with correct meanings |
| [!tip] | 218 | Write verb pairs together in notebook for faster learning | ✅ Sound pedagogical advice |
| [!culture] | 282 | Ukrainians use imperfective for hospitable invitations | ✅ Culturally accurate |

### Proverb Verification
- Line 16: «Кіне́ць — ді́лу віне́ць» — Real Ukrainian proverb. ✅

### Cultural Claims
- Hospitality dialogue (lines 293-298): Aspect usage in hosting context is accurate and natural. ✅
- Morning rhythm narrative (line 305): Aspect alternation between perfective (narrative beats) and imperfective (background) is accurately demonstrated. ✅

---

## Section-by-Section Evidence

### Section «Вступ: Концепція видових пар» (lines 14-60)
**Plan target:** 450 words | **Points covered:** Family analogy ✅, Visual icons (⏳/✅) ✅, писати-написати example ✅
**Issues:** None significant. Warm opening with proverb. Good scaffolding from English to Ukrainian.

### Section «Творення префіксами та правило правопису» (lines 61-141)
**Plan target:** 750 words | **Points covered:** з-/с- rule ✅, Кафе Птах ✅, робити-зробити ✅, писати-написати ✅, ділити-поділити ✅, semantic hints for prefixes ✅
**Issues:** LLM filler "Let's explore" at line 67. Russianism "Давайте уважно подивимося" at line 65.

### Section «Творення суфіксами та суплетивні пари» (lines 143-219)
**Plan target:** 750 words | **Points covered:** -ва-/-ува- suffixes ✅, morning routine hook ✅, stem changes (вибирати/вибрати partial) ⚠️, забувати/забути ✅
**Issues:** 
- виходити/вийти suppletive pair **MISSING** (plan-required)
- Internal vowel shifts (-о-→-і-) mentioned briefly at line 188 for вибирати but not taught as a systematic pattern
- Russianism "Давайте подивимося" at line 153

### Section «Практика: Помилки та вибір аспекту» (lines 221-283)
**Plan target:** 600 words | **Points covered:** Process vs Result drill ✅, Future tense mismatch ✅, Imperative nuance ✅
**Issues:** No significant issues. Well-structured with error examples.

### Section «Культурний контекст та діалоги» (lines 285-348)
**Plan target:** 450 words | **Points covered:** Hospitality dialogue ✅, Morning rhythm narrative ✅, Grammatical summary ✅
**Issues:**
- Narrative (line 305) uses "зачини́в" but analysis (line 307) references "закри́в" — verb mismatch
- Russianism "Давайте подивимося" at line 325
- Additional story «Вечір у Києві» (lines 323-329) not in plan — adds good content but significantly extends the section beyond its 450-word allocation
- Line 336: «сто відсотків фінальний» — non-standard colloquialism; should be «стовідсотково завершений» or simply «повністю завершений»

---

## Richness Gap Fix Plan

Current richness: 64% | Target: 95%

| Gap | Current | Target | Fix |
|-----|---------|--------|-----|
| Engagement boxes | 3/5 | 5/5 | Add 2 more callout boxes (e.g., [!did-you-know] about aspect in poetry, [!myth-buster] about "all prefixes add meaning") |
| Cultural callouts | 0/3 | 3/3 | Add [!culture] boxes about aspect in folk songs, aspect in SMS/messaging, aspect in restaurant ordering |
| Dialogues | 0/4 | 4/4 | Add 3-4 short dialogues: pharmacy purchase (aspect contrast), phone call ending (perfective sequence), morning planning (future tense forms) |
| Tables | 0/2 | 2/2 | Add (1) prefix summary table, (2) future tense formation comparison table |

---

## Verification Summary

| Check | Result | Notes |
|-------|--------|-------|
| All H2 sections from plan present | ✅ | 5/5 sections match plan |
| Vocabulary matches plan hints | ✅ | 14/14 required + 5/5 recommended present |
| No colonial framing | ✅ | No Russian comparisons found |
| No LLM generic clichés | ✅ | No діамант, двигун прогресу, etc. |
| Russicisms | ❌ | "подивимося" x3 (confirmed calque) |
| Grammar accuracy | ⚠️ | Content correct; activity explanation wrong (казати/сказати) |
| Plan-required suppletive pairs | ❌ | виходити/вийти missing |
| IPA on first occurrence | ❌ | Stress marks used instead; no IPA |
| Immersion target | ✅ | 52.6% within 50-60% band |
| Callout factual accuracy | ✅ | All 5 callouts verified |
| Activity-content alignment | ⚠️ | Quiz explanation contradicts lesson content |
| Narrative consistency | ❌ | зачинив (narrative) ≠ закрив (analysis) |
| Section structural monotony | ✅ | Varied section openings |
| Tables for grammar | ❌ | Zero tables in grammar module |

---

## Verdict

**FAIL — 6 issues requiring fixes before pass**

**Critical (must fix):**
1. Replace "Давайте подивимося" → "Подивімося" at lines 65, 153, 325 (Russianism)
2. Add виходити/вийти suppletive pair with examples to section «Творення суфіксами та суплетивні пари» and to vocabulary YAML
3. Fix activity quiz explanation: казати→сказати is prefixal (Кафе Птах), not suppletive

**Medium (should fix):**
4. Fix narrative/analysis mismatch: align зачинив/закрив at lines 305/307
5. Add 2 grammar tables: prefix summary + future tense formation
6. Close richness gaps: add dialogues, cultural callouts, and engagement boxes per fix plan above

**Low (recommended):**
7. Replace "Let's explore" (line 67) with concrete teaching content
8. Replace "сто відсотків фінальний" (line 336) with standard "повністю завершений"
9. Consider adding IPA for metalanguage terms (префікс, суфікс, etc.) per plan instruction