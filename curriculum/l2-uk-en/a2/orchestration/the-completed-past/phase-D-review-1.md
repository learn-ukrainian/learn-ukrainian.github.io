**Reviewed-By:** claude-opus-4-6

# Phase D.1 Review — The Completed Past (a2-13)

**Module:** `the-completed-past` | **Level:** A2 | **Sequence:** 13
**Persona:** Encouraging Cultural Guide / Museum Archivist
**Word count:** 4798 / 3000 (159.9%) | **Immersion:** 50.0%

---

## Scores

| # | Dimension | Score | Justification |
|---|-----------|-------|---------------|
| 1 | Plan Compliance | 6/10 | All 5 H2 sections present, but 7 of 16 required vocabulary items (побачив, почув, взяв, дав, приїхав, почав, закінчив) missing from vocabulary file AND mostly absent from content prose. забув in vocab but never taught in content. |
| 2 | Lesson Quality | 8/10 | Warm welcome, encouraging tone, good dialogue, self-check questions at end. Opening blockquote is philosophical before learner knows terminology. Practice opportunities only via activities — no inline mini-exercises in prose. |
| 3 | Ukrainian Language Quality | 7/10 | Duplicate sentence on line 96. Misleading grammar instruction on line 80. Confusing referent «таку форму» on line 59. Otherwise solid grammar. |
| 4 | English Language Quality | 8/10 | Clear B1-level English throughout. Translations are helpful. Some English translations are embedded in nested parentheses (line 96 broken). |
| 5 | Activity Quality | 7/10 | 12 activities with good variety. Activity item on line 284 has a nonsensical sentence with ambiguous error target. Line 278 misleadingly labels correct Ukrainian «брав участь» under a "Russicism" heading. |
| 6 | Richness & Engagement | 8/10 | 6 callout boxes, extended dialogue, closing narrative story, cultural proverbs. Museum archivist persona well-maintained. |
| 7 | Immersion Balance | 8/10 | 50% Ukrainian — at the floor of the 50-60% target for A2 Band 1. English scaffolding well-placed for grammar theory. |
| 8 | Factual Accuracy | 8/10 | Grammar rules correct. Proverbs verified. Line 80 is pedagogically misleading (ties neuter suffix to semantic topic rather than grammatical gender). |
| 9 | LLM Fingerprint | 6/10 | «це не просто» × 2 (lines 12, 249). «двигун сюжету» (line 161) — LLM-typical metaphor. Uniform `* **Ukrainian.** (English.)` example formatting across 10+ subsections. 6+ subsections/paragraphs open with «Коли...» — structural monotony. |
| 10 | Humanity & Warmth | 8/10 | Direct address throughout, encouraging phrases in callout boxes. Could use more "don't worry" moments and explicit progress celebration markers. |

---

## Critical Issues Found

### CRITICAL 1: Duplicate sentence — copy-paste error (Line 96)

In section «Процес проти результату», line 96 contains a duplicated Ukrainian sentence with broken parenthetical structure:

> «Англійська мова використовує один час для процесів і результатів. (Англійська мова використовує один час для процесів і результатів. (English uses one tense for processes and results.))»

The pattern is `Ukrainian. (Ukrainian. (English.))` instead of the expected `Ukrainian. (English.)`. This is a generation artifact that a learner will find confusing.

**Fix:** Remove the duplicate Ukrainian sentence. Result should be: `Англійська мова використовує один час для процесів і результатів. (English uses one tense for processes and results.)`

---

### CRITICAL 2: Misleading grammar instruction (Line 80)

In section «Творення та граматична узгодженість», line 80:

> «Коли ви говорите про правила, додавайте суфікс **-ло**.»

This incorrectly ties the neuter suffix -ло to the semantic topic of "rules" rather than the grammatical gender of the subject. A learner reading this would think: "When I talk about rules, I use -ло." The actual rule is: when the SUBJECT is neuter gender, use -ло. The subject «правило» happens to be neuter, but the instruction as written is a false generalization.

**Fix:** Replace with something like: «Для підметів середнього роду завжди використовуйте суфікс **-ло**.» (For neuter subjects always use the suffix -ло.)

---

### CRITICAL 3: Confusing referent «таку форму» (Line 59)

In section «Творення та граматична узгодженість», line 59:

> «Коли підмет жіночого роду, дієслово також має таку форму.»

«Таку форму» ("this/such form") backreferences the masculine -в form from the preceding subsection. The sentence literally says the feminine verb "also has this [masculine] form", which is the opposite of the intended meaning. The English translation "the verb also has this form" is equally misleading.

**Fix:** Replace with: «Коли підмет жіночого роду, дієслово змінює закінчення.» (When the subject is feminine, the verb changes its ending.)

---

### CRITICAL 4: Nonsensical activity sentence (Activities YAML, line 284)

In error-correction activity "Виправте русизми та помилки вибору виду":

> `sentence: "Я шукав свої ключі, і раптом я їх шукав у кишені!"`

This sentence is semantically absurd — "I was looking for my keys, and suddenly I was looking for them in my pocket!" The word «шукав» appears twice, making the error target ambiguous. The first «шукав» is correct (process of searching), only the second should be «знайшов».

**Fix:** Rewrite the sentence to: `"Я шукав свої ключі, і раптом їх шукав у кишені!"` → or better: make the sentence unambiguous by changing context, e.g. `"Я довго шукав свої ключі, і раптом я їх шукав у кишені!"` with the second `шукав` clearly being the error.

---

### MAJOR 5: Missing 7 required vocabulary items

The plan's `vocabulary_hints.required` lists 16 items. The vocabulary file contains only 12 items, missing:

| Missing from vocab file | Plan requirement |
|------------------------|------------------|
| побачив | noticed a detail, saw for the first time |
| почув | heard the news, caught a specific sound |
| взяв | took a seat, took the opportunity |
| дав | gave an answer, gave back |
| приїхав | arrived by transport/vehicle |
| почав | began / started a completed action |
| закінчив | reached the end of a task |

Of these, only «взяв» and «побачив» appear in the content prose (lines 178, 170). «Почув», «дав», «приїхав», «почав» are completely absent from both the vocabulary file and the lesson content. «Закінчив» appears only in the activities file (line 393 group-sort) but is never taught in the lesson.

**Fix:** Add all 7 missing items to the vocabulary YAML with IPA, translations, and example sentences. Integrate the verbs into the content prose, particularly in section «Процес проти результату» which has space for additional high-frequency verbs.

---

### MAJOR 6: забув in vocabulary but untaught in content

The vocabulary file includes «забув» (line 44-48) but this word never appears anywhere in the lesson content. A vocabulary item that isn't encountered in the lesson text provides no learning value.

**Fix:** Either add «забув» to a content example (e.g., in section «Процес проти результату» or the dialogue), or remove it from the vocabulary file and replace with a more relevant item.

---

### MAJOR 7: Activity misleadingly labels correct Ukrainian as error (Activities YAML, line 278)

In error-correction activity "Виправте русизми та помилки вибору виду":

> `sentence: "Студент брав участь у конференції та отримав диплом."`
> `error: "брав"` → `answer: "взяв"`

The activity title groups this under "русизми" (Russicisms), but «брати участь» is standard Ukrainian — it is NOT a Russicism. The actual Russicism would be «приймати участь» (from Russian «принимать участие»). While «взяв участь» is better for a completed event, labeling «брав участь» under a "Russicism" heading teaches the student incorrect metalinguistic knowledge.

**Fix:** Either (a) move this item to a separate aspect-only activity, or (b) rewrite the explanation to explicitly state this is about aspect choice, NOT a Russicism.

---

### MINOR 8: LLM structural monotony — «Коли...» sentence openers

Six subsections/major paragraphs open with «Коли...»:
- Line 48: «Коли підметом є чоловік...»
- Line 59: «Коли підмет жіночого роду...»
- Line 83: «Коли багато людей роблять дію...»
- Line 130: «Коли ви шукаєте щось...»
- Line 161: «Коли архіваріус розповідає історію...»
- Line 193: «Коли ви кажете **нарешті**...»

This creates a textbook-like cadence that marks LLM generation. The gender subsections (lines 48, 59, 73, 83) are particularly mechanical — all four follow the exact same template: "When [subject type], [suffix rule]."

**Fix:** Vary at least 3 of these openings. For example, line 59 could start with the tip box instead of the rule; line 83 could open with an example.

---

### MINOR 9: Uniform example formatting across all sections

Every subsection presenting examples uses the identical format:
```
* **Ukrainian sentence.** (English translation.)
```

This appears in: Форми чоловічого роду, Форми жіночого роду, Форми середнього роду, Форми множини, зробити examples, сказати examples, знайти examples, зрозуміти examples, піти examples, прийти examples, спочатку examples, потім examples, нарешті examples — that's 13+ subsections with identical formatting.

**Fix:** Introduce format variation: use a table for the gender paradigm (section «Творення та граматична узгодженість»), inline examples for sequencing markers, dialogue snippets for high-frequency verbs.

---

## Factual Verification

| Claim | Location | Verdict |
|-------|----------|---------|
| «Діло майстра величає» is a Ukrainian proverb | Line 23 | ✅ Verified — real Ukrainian proverb |
| «Кінець — справі вінець» is a Ukrainian proverb | Line 23, 260 | ✅ Verified — real Ukrainian proverb |
| Perfective past uses suffixes -в, -ла, -ло, -ли | Lines 48-91 | ✅ Correct standard Ukrainian grammar |
| No auxiliary verb needed for perfective past | Lines 40-45 | ✅ Correct — «я зробив» not «я був зробив» |
| «Розумів» means process, «зрозумів» means result | Lines 142-143 | ✅ Correct aspectual distinction |
| State Standard §4.3.2 references aspectual pairs | Research notes line 4 | ✅ Cross-referenced with research |
| Gender agreement: -ло tied to "talking about rules" | Line 80 | ⚠️ Misleading — -ло is tied to neuter gender subjects, not the semantic topic |

---

## Verification Summary

| Check | Result |
|-------|--------|
| Colonial framing | ✅ PASS — No Russian comparisons found |
| Russicisms in content | ✅ PASS — No Russicisms detected in lesson prose |
| Russicisms in activities | ⚠️ Activity correctly catches «кушав» → «з'їв» (line 260). But mislabels «брав участь» as Russicism (line 278). |
| Grammar accuracy | ⚠️ PARTIAL — All rules correct, but line 80 gives a misleading generalization |
| IPA spot-check | ✅ PASS — Checked зробив, сказав, пішов — stress placement correct |
| Vocabulary scope | ❌ FAIL — 7 of 16 required vocabulary items absent |
| Activity item accuracy | ❌ FAIL — Nonsensical sentence on line 284, misleading error label on line 278 |
| "Would I Continue?" test | 3.5/5 — Warm opening, clear explanations, but dense philosophical opener before terminology is introduced; no inline practice before activities |
| LLM fingerprint | ⚠️ FLAGGED — «це не просто» × 2, «двигун сюжету», uniform example formatting, «Коли» monotony |

### Section Coverage
- Section «Вступ»: Cultural proverbs well-integrated; opening blockquote dense but effective
- Section «Творення та граматична узгодженість»: Gender paradigm thoroughly covered; issues on lines 59 and 80
- Section «Процес проти результату»: Strong contrast examples; duplicate sentence on line 96; missing several required high-frequency verbs
- Section «Наративна послідовність у музеї»: Excellent extended dialogue; sequencing markers well-taught; closing story is engaging
- Section «Практика та усунення помилок»: Good error correction patterns; slightly repetitive with earlier material

---

## Verdict

**FAIL — Requires D.2 repair cycle.**

The module has a strong pedagogical core: the Museum Archivist persona is engaging, the extended dialogue in section «Наративна послідовність у музеї» is genuinely good teaching, and the cultural hooks are authentic. However, several issues prevent a pass:

1. **Vocabulary scope gap** (7 of 16 required items missing) is the largest blocker — nearly half the plan's required verbs are untaught.
2. **Content errors** need fixing: duplicate sentence (line 96), misleading grammar instruction (line 80), confusing referent (line 59).
3. **Activity errors**: nonsensical sentence (line 284) and misleading Russicism label (line 278) would confuse learners.
4. **LLM fingerprint** is elevated due to uniform example formatting and structural monotony.

**Priority for D.2:**
1. Add missing vocabulary items and integrate into content prose
2. Fix the 3 content errors (lines 59, 80, 96)
3. Fix the 2 activity errors (lines 278, 284)
4. Vary example formatting and subsection openings to reduce LLM fingerprint