Now I have everything I need. Let me perform the deep adversarial review.

---

## Deep Adversarial Review: yesterday-past-tense (a1-21)

### Issue Inventory

**Issue 1: Collocation — "Погода була добра" (md line 245)**
- **Text:** «Погода була добра.»
- **Problem:** "Добра погода" is not the standard collocation. "Добрий/добра" primarily means "kind" (about people). For weather quality, standard Ukrainian uses "гарна погода" or "хороша погода."
- **Severity:** Medium. Native speakers would notice this.
- **Fix:** → «Погода була гарна.»

**Issue 2: Collocation — "Актор був добрий?" (md line 278)**
- **Text:** «Актор був добрий?»
- **Problem:** Same as above. "Добрий актор" = "a kind actor." For professional quality: "хороший актор."
- **Severity:** Medium.
- **Fix:** → «Актор був хороший?»

**Issue 3: Linguistics jargon — "suppletion" / "suppletive root" (md lines 193-195)**
- **Text:** «It undergoes a complete change in the stem, a phenomenon called suppletion (like "go" becomes "went" in English). You cannot say «йтив». You must use the suppletive root **іш-**:»
- **Problem:** "Suppletion" and "suppletive root" are graduate-level linguistics terminology. An A1 learner has zero use for these terms. The English analogy ("go"→"went") already does the pedagogical work.
- **Severity:** Medium. Jargon overwhelm at A1.
- **Fix:** Remove jargon, keep the analogy.

**Issue 4: LLM purple prose — "endings dance" / "music of the story" (md line 221)**
- **Text:** «Do you see how the endings dance? *День був*, *музей працював*, *туристи ходили*. The rhythm of the past tense creates the music of the story.»
- **Problem:** Classic LLM metaphor overload. "Endings dance" and "music of the story" are meaningless fluff that confuses rather than clarifies.
- **Severity:** Medium (LLM fingerprint dimension).
- **Fix:** Replace with a clear pedagogical observation.

**Issue 5: LLM purple prose — "sound of masculine history" (md line 38)**
- **Text:** «Notice the sound at the end of these words? That deep, resonant **-в**? That is the sound of masculine history. If Ivan Fedorov were a woman, history would sound different.»
- **Problem:** "Deep, resonant" and "the sound of masculine history" are LLM anthropomorphizing. The second sentence is good pedagogy (foreshadowing feminine forms), but "the sound of masculine history" is empty rhetoric.
- **Severity:** Low-medium.
- **Fix:** Keep the pedagogical point, remove the purple prose.

**Issue 6: LLM purple prose in summary (md lines 312-314)**
- **Text:** «We learned that Ukrainian verbs in the past behave like mirrors—they reflect the person who is speaking. The masculine **-в** sounds solid and grounded. The feminine **-ла** flows and sings. The plural **-ли** unites everyone. We also honored Ivan Fedorov and his first book, reminding us that every grammatical past tense describes a piece of history, big or small. / You now have the tools to share your day. You are no longer just an observer of the present; you are a storyteller of your own life.»
- **Problem:** Multiple LLM artifacts: "mirrors," "-в sounds solid and grounded," "-ла flows and sings," "honored Ivan Fedorov," "storyteller of your own life." None of this helps an A1 learner.
- **Severity:** Medium.
- **Fix:** Rewrite summary to be concrete and useful.

**Issue 7: Style — "прийняла закон" (md line 225)**
- **Text:** «ЗУНР ... **прийняла** закон про українську мову.»
- **Problem:** In a legislative context, the standard Ukrainian term is "ухвалити закон" (to adopt/pass a law). "Прийняти закон" is colloquially used but is less precise for formal legislation.
- **Severity:** Low. Both forms are used, but "ухвалити" is better in a culture box about legislation.
- **Fix:** → «ухвалила»

**Issue 8: LLM opener — "unlock the ability" (md line 13)**
- **Text:** «Today, we unlock the ability to tell your story.»
- **Problem:** "Unlock" is signature LLM grandiose language.
- **Severity:** Low.
- **Fix:** Simplify.

**Issue 9: Activity instruction mismatch (activities YAML line 240)**
- **Text:** `instruction: "Select the correct form of 'їсти' (to eat) or 'йти' (to go)."`
- **Problem:** Items 3, 8 in this activity use forms of **ходити** (ходили), not йти. The instruction promises only їсти/йти but delivers ходити forms too.
- **Severity:** Low-medium. Instruction doesn't match content.
- **Fix:** Update instruction to include ходити.

### Items Verified — No Issues Found

- **IPA transcriptions:** All checked and correct. for вчора is accurate (в→[u̯] before voiceless [t͡ʃ]). Stress on була/було/були correctly on second syllable. Affricates have proper tie bars throughout. [ɦ] used correctly for Г.
- **Historical claims:** February 15, 1574 (Fedorov's Apostol in Lviv) — confirmed as the completion date. February 15, 1919 (ZUNR language law) — confirmed. Both dates accurate.
- **No Russianisms** detected. No Russian characters (ы, э, ё, ъ).
- **Unjumble activities:** All 6 items verified — every word in `words` array appears in the `answer`, and answers are grammatical sentences.
- **Fill-in activities:** All 32 items produce grammatical sentences when the answer is inserted. Gender agreement correct throughout.
- **Plan compliance:** All 3 meta sections present. All meta outline points covered. All required vocabulary used in prose. All 4 objectives map to self-check questions.
- **Vocabulary file:** Exists with 19 entries. All plan-required vocabulary present.
- **No forward references** to untaught grammar. Aspect distinction is explicitly marked as "intro only" in the SCOPE comment.
- **Quiz, true-false, group-sort, match-up activities:** All answers verified correct.

### Notes (Not Fixing)

- **"Ми не їли суп"** (line 147) — Genitive of negation ("супу") would be more traditional, but Accusative is increasingly acceptable in colloquial Ukrainian. At A1, introducing Genitive of negation here would overload the lesson. Acceptable.
- **"робити каву"** (line 256) — Slightly less natural than "варити каву," but explicitly authorized by the plan's vocabulary_hints. Acceptable.
- **Negation section** not in meta outline but is a natural, proportionate addition to a past tense grammar lesson. Acceptable.
- **"прокидатися"** used in the final fill-in activity while the building blocks list uses "вставати" — minor vocabulary inconsistency but both verbs are in the vocabulary file and both are A1-appropriate.

---

## Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/a1/yesterday-past-tense.md
---OLD---
> Up until now, we have lived entirely in the present moment. But life is made of memories and stories. To share who you are, where you came from, and what you did, you need the past tense. Today, we unlock the ability to tell your story.
---NEW---
> Up until now, we have lived entirely in the present moment. But life is made of memories and stories. To share who you are, where you came from, and what you did, you need the past tense. Today, we learn how to talk about what happened yesterday.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/yesterday-past-tense.md
---OLD---
Notice the sound at the end of these words? That deep, resonant **-в**? That is the sound of masculine history. If Ivan Fedorov were a woman, history would sound different. But we will get to that in a moment. For now, remember: history is action in the past.
---NEW---
Notice the sound at the end of these words? The **-в** ending? That ending tells us the subject is masculine. If Ivan Fedorov were a woman, the ending would be different. But we will get to that in a moment. For now, remember: history is action in the past.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/yesterday-past-tense.md
---OLD---
The verb **йти** [i̯tɪ] (to go/walk) is the trickiest one. It undergoes a complete change in the stem, a phenomenon called suppletion (like "go" becomes "went" in English).

You cannot say «йтив». You must use the suppletive root **іш-**:
---NEW---
The verb **йти** [i̯tɪ] (to go/walk) is the trickiest one. Its stem changes completely in the past — just like "go" becomes "went" in English.

You cannot say «йтив». You must use the special past stem **іш-**:
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/yesterday-past-tense.md
---OLD---
Do you see how the endings dance? *День був*, *музей працював*, *туристи ходили*. The rhythm of the past tense creates the music of the story.
---NEW---
Notice how the endings change to match the subject: *день був* (masculine), *музей працював* (masculine), *туристи ходили* (plural). The ending always tells you who did the action.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/yesterday-past-tense.md
---OLD---
ЗУНР (Західноукраїнська Народна Республіка) **прийняла** закон про українську мову.
> *   Республіка (жіночий рід) → **прийняла** (минулий час, вона).
---NEW---
ЗУНР (Західноукраїнська Народна Республіка) **ухвалила** закон про українську мову.
> *   Республіка (жіночий рід) → **ухвалила** (минулий час, вона).
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/yesterday-past-tense.md
---OLD---
Погода була добра.
---NEW---
Погода була гарна.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/yesterday-past-tense.md
---OLD---
**Олена:** Це добре! Актор був добрий?
---NEW---
**Олена:** Це добре! Актор був хороший?
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/yesterday-past-tense.md
---OLD---
We learned that Ukrainian verbs in the past behave like mirrors—they reflect the person who is speaking. The masculine **-в** sounds solid and grounded. The feminine **-ла** flows and sings. The plural **-ли** unites everyone. We also honored Ivan Fedorov and his first book, reminding us that every grammatical past tense describes a piece of history, big or small.

You now have the tools to share your day. You are no longer just an observer of the present; you are a storyteller of your own life.
---NEW---
We learned that Ukrainian past tense verbs change their ending to match the subject's gender: **-в** for masculine, **-ла** for feminine, **-ло** for neuter, and **-ли** for plural. We also saw how Ivan Fedorov and his first book gave us real examples of past tense in action.

You now have the tools to describe your day, ask others about theirs, and share simple stories about the past.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/yesterday-past-tense.yaml
---OLD---
  instruction: "Select the correct form of 'їсти' (to eat) or 'йти' (to go)."
---NEW---
  instruction: "Select the correct form of 'їсти' (to eat), 'йти' (to go), or 'ходити' (to go regularly)."
===FIX_END===

---

## Review Summary

| Check | Result |
|-------|--------|
| IPA accuracy | PASS — all transcriptions correct, tie bars present, [ɦ] not [g], [ʋ] not [v] in appropriate positions |
| Russianisms | PASS — none found |
| Russian characters | PASS — none found |
| Gender/case agreement | PASS — all verified |
| Historical accuracy | PASS — both Feb 15 dates confirmed |
| Plan compliance | PASS — all sections, vocab, objectives covered |
| Activity correctness | PASS — all answers grammatical, unjumbles complete |
| Vocabulary scope | PASS — no out-of-scope vocabulary in activities |
| LLM artifacts | 5 instances fixed (purple prose, jargon, grandiose opener) |
| Collocation issues | 2 fixed (добра→гарна, добрий→хороший) |
| Legislative style | 1 fixed (прийняла→ухвалила) |

**Content lines read:** 324 (md) + 340 (yaml) + 82 (vocab yaml)
**Activity items verified:** 87
**Ukrainian sentences checked:** ~65
**IPA transcriptions verified:** 23
**Issues found:** 9 (all fixed above)

===VERDICT===
APPROVE
===END_VERDICT===