**Reviewed-By:** claude-opus-4-6

---

## Scores

| # | Dimension | Score | Short Justification |
|---|-----------|-------|---------------------|
| 1 | **Lesson Quality** | 8/10 | Strong structure following PPP arc; good cultural hooks (обід, домашній одяг, сирники); dialogues are natural and well-annotated. However, opening lacks warmth (no greeting, no "Привіт!"), and some redundant sentences reduce flow. The lark/owl hook is engaging but buried after two dense paragraphs. |
| 2 | **Immersion Balance** | 8/10 | 40.9% Ukrainian within the audit target of 35-55%. Ukrainian is well-scaffolded with English translations throughout. However, for an A1.3 consolidation module (sequence 25 of ~30), the immersion is on the lower end — could push closer to 50% by converting some redundant English explanations into Ukrainian with glosses. |
| 3 | **Language Quality** | 7/10 | Ukrainian sentences are mostly grammatically correct and natural. However, «приймати душ» (line 126) is a calque from Russian «принимать душ» — standard Ukrainian prefers «брати душ» or «митися під душем». Line 82 has redundant near-identical sentences. Overall solid but these issues prevent a higher score. |
| 4 | **Richness** | 8/10 | Good cultural hooks: Ukrainian breakfast (сирники, каша, млинці), домашній одяг custom, обід as main meal. The lark/owl personality hook is engaging. The contrast table (workday vs weekend) is excellent visual organization. Missing: no named Ukrainian city references or contemporary media examples that could ground the routine further. |
| 5 | **Activity Quality** | 7/10 | 9 activities with 73 items — good volume and variety (quiz, fill-in, match-up, unjumble, group-sort). However, activity line 357 tests «запізнюється» which is not taught in the content (content uses «спізнююся» at line 212). Multiple vocabulary items tested in activities are missing from the vocabulary YAML. Activity types don't match plan hints well (plan asks for 20-item quizzes, activities have 8-item quizzes). |
| 6 | **Vocabulary Completeness** | 6/10 | Critical gap: «дивитися» — which gets a full grammar spotlight in the content (lines 157-170) and is explicitly required in plan vocabulary_hints — is MISSING from the vocabulary YAML. Also missing: «іноді», «нарешті», «після цього», «обідня перерва», «щодня». The metalinguistic term «дієслово» is included but key target vocabulary is not. |
| 7 | **IPA Accuracy** | 5/10 | Two IPA errors in vocabulary YAML: (1) «вставати» has IPA `` — the symbol `ʍ` (voiceless labial-velar fricative, an English phoneme) does not exist in Ukrainian; should be ``. (2) «завжди» has IPA `` — two primary stress marks, which is invalid IPA. A word can only have one primary stress. |
| 8 | **Factual Accuracy** | 9/10 | Cultural claims are accurate: обід as main meal (13:00-14:00, first+second course) matches research notes. «Сніданок з'їж сам» is a genuine proverb. Домашній одяг cultural practice is authentic. Grammar explanations are correct. Minor: the "wrong" example «Я встаю сьома» (line 39) is a slightly contrived error illustration — real learners more likely to say *«Я встаю в сім»*. |
| 9 | **LLM Fingerprint** | 8/10 | The verb introduction pattern in section «Ранок, день та вечір» is repetitive (Bold verb → English → explanation → examples), but this is pedagogically justified for A1 predictability. No "це не просто" patterns, no stacked abstract nouns, no generic AI clichés. The fragmented Ukrainian sentences in the intro (line 18: «Це послідовність дій. Ви робите їх щодня. Від ранку до сну.») feel slightly mechanical but not detectably AI-generated. |
| 10 | **Humanity & Warmth** | 7/10 | Direct address ("you/ви") is present throughout. The lark/owl question is warm. Cultural hooks add personality. However: no opening greeting ("Привіт!"), no "Don't worry" moments, encouragement is sparse (mainly at the very end). The closing «Розкажіть комусь про свій день — сьогодні!» (line 289) is encouraging but comes only at the end. Missing: "Great job!" or "You've got this!" style beats throughout the lesson body. |

---

## Critical Issues Found

### Issue 1: CRITICAL — Vocabulary YAML Missing «дивитися» (Plan-Required Verb)

**Location:** vocabulary/my-daily-routine.yaml (entire file)
**Evidence:** The plan (vocabulary_hints.required) explicitly lists «дивитися (to watch/look) — §4.2.4.1 core conjugation: дивлюся, дивишся, дивиться; focus on reflexive particle». The content devotes an entire grammar subsection to it (lines 157-170 of content). Yet the vocabulary YAML has no entry for «дивитися». Meanwhile, the metalinguistic term «дієслово» (line 122-126 of vocab YAML) IS included. A target verb required by the State Standard §4.2.4.1 must appear in the vocabulary file.

**Fix:** Add a vocabulary entry for «дивитися» with IPA, conjugation note about Class II stem change (дивлюся, дивишся), and usage example.

### Issue 2: CRITICAL — IPA Errors in Vocabulary YAML

**Location:** vocabulary/my-daily-routine.yaml, lines 9 and 107

**Evidence (1):** «вставати» has IPA ``. The symbol `ʍ` represents a voiceless labial-velar fricative (found in some English dialects for "wh-"). This phoneme does not exist in Ukrainian. The initial /в/ before a consonant cluster in Ukrainian is realized as [ʋ] (labiodental approximant) or sometimes [u̯]. Correct IPA: ``.

**Evidence (2):** «завжди» has IPA ``. This contains two primary stress marks, which violates IPA conventions — a word can only bear one primary stress. Ukrainian «завжди» has variable stress (záвжди or завждú are both accepted), but either way, only ONE stress mark is valid.

**Fix:** Correct both IPA transcriptions. For вставати: ``. For завжди: `` or `` (choose one standard variant).

### Issue 3: MAJOR — Activity Tests Untaught Vocabulary («запізнюватися»)

**Location:** activities/my-daily-routine.yaml, line 357
**Evidence:** The fill-in activity includes «Він ___ не запізнюється, він дуже пунктуальний.» (answer: ніколи). The verb «запізнюватися» is never introduced in the content. The content teaches «спізнюватися» at line 212: «Я ніколи не спізнююся.» These are related but distinct verbs (запізнюватися vs спізнюватися). At A1, testing a verb form the learner hasn't seen undermines the safe learning environment.

**Fix:** Either (a) change the activity to use «спізнюється» to match the content, or (b) add «запізнюватися» to the content and vocabulary as a synonym. Option (a) is simpler and maintains scope.

### Issue 4: MAJOR — «приймати душ» Potential Calque

**Location:** content line 125-127
**Evidence:** The content teaches «Приймати душ» (to take a shower) as a standard phrase. This parallels Russian «принимать душ» and is considered a calque by many Ukrainian language standardizers. The Ukrainian verb «приймати» means "to receive/accept" (приймати гостей, приймати рішення). Standard Ukrainian alternatives: «брати душ» or «митися під душем». While «приймати душ» appears in modern dictionaries and is widely used in colloquial speech, for a curriculum teaching standard Ukrainian, the native expression should be preferred.

**Fix:** Replace «приймати душ» with «брати душ» in the content and update the heading/conjugation examples accordingly.

### Issue 5: MODERATE — Multiple Vocabulary Items Taught But Not in YAML

**Location:** vocabulary/my-daily-routine.yaml
**Evidence:** The following items are actively taught with definitions and examples in the content but absent from the vocabulary YAML:
- «іноді» (sometimes) — taught at content line 202-204
- «нарешті» (finally) — taught at content line 187-189, recommended in plan
- «після цього» (after that) — taught at content line 183-185
- «обідня перерва» (lunch break) — used at content line 95, recommended in plan
- «щодня» (every day) — used at content line 18, recommended in plan

**Fix:** Add these items to the vocabulary YAML with IPA, translation, and usage examples. At minimum, «іноді» and «нарешті» should be added since they are actively taught alongside their sibling adverbs that ARE in the YAML.

### Issue 6: MINOR — Redundant Sentences at Line 82

**Location:** content line 82
**Evidence:** «Середина дня — це час для роботи. День — це час для активної роботи.» — These two sentences say essentially the same thing back-to-back. The second adds only the word "активної" which doesn't meaningfully extend the thought. This is filler that a careful editor would cut.

**Fix:** Remove the second sentence or combine: «Середина дня — це час для активної роботи.»

---

## Factual Verification

| Claim | Location | Verdict |
|-------|----------|---------|
| «Сніданок з'їж сам» is a popular proverb | Content line 79 | **Correct** — genuine Eastern European proverb (full: «Сніданок з'їж сам, обід поділи з другом, а вечерю віддай ворогу») |
| Обід is the main meal, 13:00-14:00, with first+second course | Content line 101, research line 20 | **Correct** — matches research notes and cultural reality |
| Домашній одяг custom: changing immediately upon returning home | Content line 113 | **Correct** — matches research notes and authentic cultural practice |
| Сирники, каша, млинці as traditional breakfast items | Content line 79 | **Correct** — these are standard traditional Ukrainian breakfast foods |
| Double negative rule: «ніколи не» | Content line 211 | **Correct** — Ukrainian requires double negation |
| Дивитися conjugation: дивлюся, дивишся, дивиться, дивимося, дивитеся, дивляться | Content lines 161-166 | **Correct** — matches §4.2.4.1 and research notes line 6 |
| -ся after consonants, -сь after vowels | Content line 138-139 | **Correct** — standard rule, with appropriate note that -ся is "always safe" at A1 |
| Вмиватися vs мити distinction | Content lines 152-155 | **Correct** — accurately distinguishes reflexive face-washing from transitive hand-washing |

No factual errors found in the content prose. All cultural claims verified against research notes.

---

## Verification Summary

| Check | Result |
|-------|--------|
| Colonial framing | **PASS** — No "Unlike Russian..." or similar comparisons found |
| Russianisms | **FLAG** — «приймати душ» (line 126) is a potential calque of Russian «принимать душ»; prefer «брати душ» |
| Plan compliance — sections | **PASS** — All 4 planned H2 sections present: «Вступ: Ваш розпорядок дня», «Ранок, день та вечір», «Практика: Робочий день і вихідні», «Підсумок: Мій ідеальний день» |
| Plan compliance — vocabulary | **PARTIAL FAIL** — «дивитися» (plan-required) missing from vocab YAML; 5 additional recommended items missing |
| Plan compliance — grammar | **PASS** — Reflexive verbs, дивитися conjugation (§4.2.4.1), sequence adverbs, frequency adverbs all covered |
| Plan compliance — objectives | **PASS** — All 4 objectives addressed (reflexive conjugation, daily routine description, sequence words, habits) |
| Word count | **PASS** — 2802/2000 (140.1%), well above minimum |
| Activity errors | **FLAG** — Activity tests «запізнюватися» not taught in content |
| IPA accuracy | **FAIL** — 2 errors: ʍ in вставати, double stress in завжди |
| Factual accuracy | **PASS** — All cultural/linguistic claims verified |
| LLM fingerprint | **PASS** — No structural monotony beyond pedagogically justified verb patterns |
| Warmth/humanity | **MARGINAL** — Needs more encouragement beats throughout body, warm opening greeting |

---

## Verdict

**REVISE** — The module has strong pedagogical content, accurate cultural hooks, and well-structured progression through daily routine vocabulary. The dialogues are natural, the contrast table is excellent, and grammar explanations are clear. However, three issues prevent approval:

1. **IPA errors** (vocabulary YAML) — invalid phoneme [ʍ] and double stress marks must be corrected
2. **Vocabulary YAML gaps** — «дивитися» (plan-required, State Standard §4.2.4.1) and 5 other taught items missing from vocabulary file
3. **Activity-content mismatch** — «запізнюватися» tested but not taught

Secondary fixes needed: replace «приймати душ» with «брати душ», remove redundant sentence at line 82, add warmth markers to opening and body sections.

Estimated repair scope: D.2 targeted fix (vocabulary YAML additions, IPA corrections, one activity line edit, one content line edit). No structural rewrite needed.