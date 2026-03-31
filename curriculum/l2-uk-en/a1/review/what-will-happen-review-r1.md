Now I have enough data. Let me compile the full review.

---

## Linguistic Scan

**Russianisms:** None found. All vocabulary verified against VESUM (80/80 content words confirmed, 4 proper nouns correctly excluded).

**Surzhyk:** None found.

**Calques:** None found. Checked "звучати" and time expressions against Антоненко-Давидович — no issues.

**Paronyms:** None found.

**Russian characters (ы, э, ё, ъ):** None found.

**Gender agreement error found:**
The fortune teller dialogue labels the interlocutor as **«Клієнт»** (masculine noun) but the fortune teller says **«Будеш щаслива!»** (feminine adjective form). This is a gender agreement mismatch. If the client is male (Клієнт), the adjective must be **щасливий**; if female, the label should be **Клієнтка**. The plan explicitly shows both forms: "Будеш щасливий/щаслива!" — the module picked only the feminine form paired with a masculine speaker label.

**False completeness claim:**
The module states: *"Every person of **буду** appears in this dialogue — **буду**, **будеш**, **буде**, **будемо**, **будете**. Did you catch them all?"* — This lists only 5 of the 6 future forms of бути. The 3rd person plural **будуть** is absent from dialogue 2 (Андрій/Марина). The claim "every person" is factually wrong. A learner who trusts this statement will believe there are only 5 forms.

**Unverifiable attribution:**
The note states: *"The Litvinova Grade 7 textbook confirms both forms are equivalent."* RAG search of the Litvinova Grade 7 textbook (chunk `7-klas-ukrmova-litvinova-2024_s0054`/`s0055`) shows it presents both складена and складна future forms but does **not** use the word "equivalent" (еквівалентний). The Zabolotnyi Grade 7 textbook similarly presents all three future forms side by side. The claim is pedagogically reasonable but the specific attribution is fabricated. This reference is also not in the plan's `references` list.

## Exercise Check

**Marker inventory:**
1. `<!-- INJECT_ACTIVITY: match-buty-future-forms -->` — after Dialogues section ✓
2. `<!-- INJECT_ACTIVITY: fill-in-analytic-future -->` — after verb conjugation drill in Практика ✓
3. `<!-- INJECT_ACTIVITY: fill-in-tense-distinction -->` — after sentence-building practice in Практика ✓

**Placement:** All 3 markers placed immediately after the relevant teaching content. Match → after dialogues showcasing all forms; fill-in-analytic → after conjugation practice; fill-in-tense → after three-tense comparison sentences. Logical progression.

**Plan alignment:** Plan specifies 3 `activity_hints` (1 matching, 2 fill-in). Module has exactly 3 markers matching these types. ✓

**Spread:** Markers distributed across Dialogues (1) and Практика (2). Not clustered at the end. ✓

**No issues found with exercise markers.**

## Scores

| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | All 4 plan sections present in correct order (Dialogues, Майбутній час, Практика, Summary). Fortune teller dialogue present. Dialogue 2 (plans for tomorrow) covers the plan's script almost verbatim. Dialogue 3 (weekend plans) closely follows plan. Full conjugation table present. Three-tense comparison present. **Deductions:** (a) Plan specifies "Будеш щасливий/щаслива!" but module has only "щаслива"; (b) claim "every person" in dialogue 2 is false — будуть missing; (c) recommended vocab "план" and "звучати" absent from prose; (d) Litvinova reference not in plan's `references` list. |
| 2. Linguistic accuracy | 9/10 | All 80 VESUM-verified words confirmed. Conjugation table correct (verified against `verify_lemma` for бути: буду/будеш/буде/будемо/будете/будуть all confirmed as `verb:imperf:futr`). No Russianisms, surzhyk, or calques. **Deduction:** Gender agreement mismatch: "Клієнт" (m) + "щаслива" (f) in fortune teller dialogue. |
| 3. Pedagogical quality | 8/10 | Excellent PPP flow: situation (fortune teller + dialogues) → pattern (conjugation table + tense comparison) → practice (conjugation drills + sentence building). Multiple examples per grammar point. Clear three-tense comparison. Synthetic future correctly deferred to A2. **Deductions:** (a) False "every person" claim teaches wrong information — a learner counting forms will find only 5 and wonder what they missed; (b) Litvinova attribution unverifiable. |
| 4. Vocabulary coverage | 9/10 | All 8 required vocab items present naturally in prose: завтра ✓, буду/будеш/буде/будемо/будете/будуть ✓, робити ✓. Recommended: відпочивати ✓ (dialogue 3 + practice), наступний ✓ ("наступного тижня"), тиждень ✓, футбол ✓, зараз ✓. **Deduction:** "план" (plan) and "звучати" (to sound) from recommended list not used in prose — plan's dialogue 2 had "Звучить добре!" which was replaced with "Чудово!" |
| 5. Exercise quality | 9/10 | 3 markers match 3 plan hints exactly (matching, fill-in analytic, fill-in tense distinction). Good placement after relevant teaching. Cannot verify exercise YAML content (generated separately). No issues with marker logic or placement. Minor: no marker exercises the fortune teller dialogue specifically. |
| 6. Engagement & tone | 10/10 | Fortune teller opening is creative and immediately demonstrates the pattern. No LLM filler ("Numbers unlock the real Ukraine!"), no meta-commentary ("Let us now explore..."). Natural dialogues with distinct voices (playful teasing: "Ти завжди будеш дивитися футбол!"). Cultural details: «Чудово!» explicitly taught as a reaction. "Count the forms" engagement hook in dialogue 2. |
| 7. Structural integrity | 10/10 | All 4 H2 headings match plan sections. Clean markdown with proper dialogue div formatting. Word count 1221 ≥ 1200 target ✓. No duplicate summaries, no stray tags, no meta-commentary sections. :::note and :::tip used appropriately. |
| 8. Cultural accuracy | 10/10 | Ukrainian presented on its own terms. No "like Russian but..." framing. Synthetic future introduced with Ukrainian terminology (складений майбутній). Ukrainian cultural context (гуляти в парку, готувати вечерю) natural and appropriate. |
| 9. Dialogue quality | 9/10 | Three distinct dialogues with named speakers (Ворожка/Клієнт, Андрій/Марина, Оксана/Тарас). Natural situations: fortune telling, planning tomorrow, weekend plans between colleagues. Multi-turn with teasing ("Ти завжди будеш дивитися футбол!"). **Deduction:** Dialogue 2 claims to contain all 6 forms but only has 5 — will confuse engaged learners who actually try to count. |

## Findings

```
[LINGUISTIC ACCURACY] [CRITICAL]
Location: Fortune teller dialogue — "Будеш щаслива! *(You will be happy!)*"
Issue: Gender agreement mismatch. The speaker label is "Клієнт" (masculine noun), but the predicate adjective is "щаслива" (feminine). Either the label or the adjective must change. The plan specifies "Будеш щасливий/щаслива!" showing both forms.
Fix: Change to "щасливий" to match "Клієнт" (m), and add a parenthetical note showing the feminine alternative, matching the plan's intent to demonstrate gender agreement with буду + adjective.
```

```
[PEDAGOGICAL QUALITY] [CRITICAL]
Location: After dialogue 2 — "*Every person of **буду** appears in this dialogue — **буду**, **будеш**, **буде**, **будемо**, **будете**. Did you catch them all?*"
Issue: Claims "every person" but lists only 5 of 6 forms. The 3rd person plural "будуть" is missing from the dialogue and from the list. An A1 learner trusting this statement will believe there are only 5 future forms of бути. This directly contradicts the conjugation table presented later, which correctly shows 6 forms.
Fix: Add a dialogue exchange using "будуть" to dialogue 2 and include it in the list.
```

```
[PEDAGOGICAL QUALITY] [MINOR]
Location: :::note block — "The Litvinova Grade 7 textbook confirms both forms are equivalent."
Issue: RAG search of Litvinova Grade 7 (chunk 7-klas-ukrmova-litvinova-2024_s0054/s0055) shows the textbook presents both future forms but does not use the word "equivalent." The attribution is an extrapolation. This reference is also not listed in the plan's references.
Fix: Replace with a general attribution to Ukrainian textbooks.
```

```
[VOCABULARY COVERAGE] [MINOR]
Location: Dialogue 3 (Оксана/Тарас)
Issue: Plan's dialogue 2 script included "Звучить добре!" which would introduce the recommended vocab word "звучати." The module replaced this with "Чудово!" — a fine word but misses the vocab opportunity.
Fix: Not fixing — "Чудово!" is natural and "звучати" is only recommended, not required. Informational only.
```

## Verdict: REVISE

Two critical findings: (1) gender agreement error teaching wrong Ukrainian (Клієнт + щаслива), and (2) false completeness claim about all persons of буду in dialogue. Both are factual/linguistic errors that will mislead A1 learners. Three targeted fixes below resolve all issues.

<fixes>
- find: "<div class=\"dialogue-line\"><span class=\"speaker\">Ворожка:</span> Будеш щаслива! *(You will be happy!)*</div>"
  replace: "<div class=\"dialogue-line\"><span class=\"speaker\">Ворожка:</span> Будеш щасливий! Будеш щаслива! *(You will be happy! [m/f])*</div>"
- find: "<div class=\"dialogue-line\"><span class=\"speaker\">Марина:</span> Так, ми будемо гуляти в парку! *(Yes, we will walk in the park!)*</div>\n\n</div>\n\n*Every person of **буду** appears in this dialogue — **буду**, **будеш**, **буде**, **будемо**, **будете**. Did you catch them all?*"
  replace: "<div class=\"dialogue-line\"><span class=\"speaker\">Марина:</span> Так, ми будемо гуляти в парку! *(Yes, we will walk in the park!)*</div>\n\n<div class=\"dialogue-line\"><span class=\"speaker\">Андрій:</span> А діти? *(And the kids?)*</div>\n\n<div class=\"dialogue-line\"><span class=\"speaker\">Марина:</span> Вони будуть грати у дворі. *(They will play in the yard.)*</div>\n\n</div>\n\n*All six forms of **буду** appear in this dialogue — **буду**, **будеш**, **буде**, **будемо**, **будете**, **будуть**. Did you catch them all?*"
- find: "The Litvinova Grade 7 textbook confirms both forms are equivalent."
  replace: "Ukrainian textbooks present both forms as standard ways to express the future."
</fixes>
