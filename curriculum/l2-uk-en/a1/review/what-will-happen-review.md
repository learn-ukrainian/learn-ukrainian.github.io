All linguistic checks are clean. Now let me compile the full review.

---

## Linguistic Scan

**Russianisms:** None found. All vocabulary is standard Ukrainian.

**Surzhyk:** None found.

**Calques:** None found. "Звучить добре" checked — not flagged by Антоненко-Давидович. "Справді" confirmed as natural Ukrainian (Антоненко-Давидович lists it as a proper Ukrainian word alongside "дійсно").

**Paronyms:** None found.

**Russian characters (ы, э, ё, ъ):** None found.

**Gender/case errors:** None found. "дев'ятої", "п'ятої" confirmed as valid genitive forms. "у дворі" — "дворі" confirmed as valid locative of "двір" (VESUM: `noun:inanim:m:v_mis`). "нових друзів" — correct genitive plural of "друг".

**Factual claims about Ukrainian grammar:** The module claims Ukrainian has "two futures" and teaches only the analytic one (буду + infinitive). Textbook evidence (Grade 4, Varzatska p.132) confirms three forms: prefixed perfective (що зроблю?), analytic (що буду робити?), and synthetic imperfective (що робитиму?). The module simplifies to "two futures" — this is a reasonable pedagogical simplification at A1 since the prefixed perfective future is actually the synthetic future of perfective verbs. Ukrainian grammars typically distinguish складений (analytic) vs. простий (synthetic) future. The claim is acceptable for A1.

**VESUM verification:** All 85 checked content words confirmed. The 4 "not found" items (Андрій, Оксана, Олена, Тарас) are proper nouns — expected VESUM gaps.

**Note on "Звучить добре!"** in Dialogue 2 (plan): This phrase appears in the plan but was replaced by "Чудово!" in the actual content. Acceptable — "Чудово" is confirmed natural Ukrainian by Антоненко-Давидович (synonym of "гарний, красивий, хороший").

No linguistic errors found.

## Exercise Check

Three activity markers found:
1. `<!-- INJECT_ACTIVITY: match-buty-future-forms -->` — placed after Dialogues section, before grammar explanation. Tests matching pronoun→бути form. **Placement is correct** — the dialogues already present all 6 forms, so learners have been exposed to the pattern.
2. `<!-- INJECT_ACTIVITY: fill-in-analytic-future -->` — placed in Практика section after the verb conjugation lists. Tests choosing the correct бути form. **Placement is correct** — tests what was just drilled.
3. `<!-- INJECT_ACTIVITY: fill-in-tense-distinction -->` — placed in Практика section after the full-sentence examples. Tests past/present/future distinction. **Placement is correct** — requires knowledge from both the grammar section and practice.

**Plan's activity_hints specify 3 activities:** 1 matching + 2 fill-in. The module has exactly 3 markers matching these types. ✅

**Marker IDs:** `match-buty-future-forms` maps to plan hint 1 (matching: pronoun→бути), `fill-in-analytic-future` maps to plan hint 2 (fill-in: analytic future), `fill-in-tense-distinction` maps to plan hint 3 (fill-in: tense distinction). All accounted for.

**Distribution:** Markers are spread across the module — one in Dialogues, two in Практика. Not clustered. ✅

**Logic check (from plan hints):**
- Matching: pairs are correct (я→буду, ти→будеш, він/вона→буде, ми→будемо, ви→будете, вони→будуть). Verified against VESUM conjugation of "бути". ✅
- Fill-in #1: all items have correct answers as first option (буду, будеш, буде, будемо, будете, будуть) with plausible distractors from other persons. ✅
- Fill-in #2: time markers signal the correct tense (зараз→present, учора→past, завтра→future, минулого тижня→past). ✅

No exercise issues found.

## Scores

| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 10/10 | All 4 content_outline sections present (Dialogues, Майбутній час, Практика, Summary). Fortune-teller dialogue from plan's `dialogue_situations` implemented faithfully. Dialogue 1 (plans for tomorrow) matches plan exactly: "Що ти будеш робити завтра?" → all 6 persons covered. Dialogue 2 (weekend plans) matches plan. All content_outline points covered: full бути conjugation table, three-tense comparison (минулий/теперішній/майбутній), 6 core verbs in practice, time expressions (завтра, наступного тижня, у суботу, ввечері). Synthetic future note (читатиму/робитиму) mentioned as A2 material per plan. References to Grade 3-4 textbooks integrated. Word count 1262 ≥ 1200 target. ✅ |
| 2. Linguistic accuracy | 10/10 | All Ukrainian verified against VESUM (85/85 content words confirmed). бути conjugation matches VESUM exactly (буду/будеш/буде/будемо/будете/будуть — all tagged `verb:imperf:futr`). No Russianisms, Surzhyk, calques, or paronyms found. Gender/case endings correct throughout (нових друзів — gen.pl of друг; дев'ятої/п'ятої — gen.f of ordinals). Fortune-teller scene uses correct forms: "щасливий" (m) / "щаслива" (f) distinction. |
| 3. Pedagogical quality | 10/10 | Follows PPP flow as specified. Presentation: fortune-teller dialogue introduces pattern naturally (будеш + infinitive repeated), then Dialogue 1 exposes all 6 forms in context. Pattern: grammar section provides explicit table + three-tense comparison with same verb (читати). Practice: 6 verbs drilled across all persons, then full sentences with time markers. Matches Grade 3-4 textbook approach (Vashulenko: "Дієслова майбутнього часу називають дію, яка відбудеться після того, як про неї говоримо"; Kravtsova: "змінюється тільки допоміжне дієслово бути"). The note box about synthetic future is pedagogically appropriate — acknowledges existence without teaching it. |
| 4. Vocabulary coverage | 10/10 | All required vocabulary from plan present in prose: завтра (multiple uses), буду/будеш/буде/будемо/будете/будуть (all in dialogues + table + practice), робити (in "Що ти будеш робити?"). Recommended vocab: відпочивати (Dialogue 2: "будемо відпочивати"), наступний (Practice: "наступного тижня"), тиждень ("наступного тижня"), звучати (replaced by "Чудово!" — acceptable), футбол (Dialogue 2: "дивитися футбол"), зараз (grammar section: "Я читаю книжку зараз"). Plan ("план") not explicitly used as a noun, but "plans" is the topic. All words introduced in context, not as bare lists. |
| 5. Exercise quality | 9/10 | Three exercises match plan's activity_hints exactly in type and focus. Matching exercise covers all 6 бути forms. Fill-in exercises have plausible distractors (other person forms of бути). Tense-distinction exercise uses time markers as signals — tests language skill, not content recall. Minor: all correct answers in fill-in #1 are in first position {correct|distractor1|distractor2} — if the pipeline preserves this order, learners could game it. However, the pipeline typically randomizes option order, so this is informational only. |
| 6. Engagement & tone | 9/10 | Strong opening with fortune-teller scene — creative, culturally plausible, immediately demonstrates the pattern. No motivational openers, no meta-commentary, no "Let us explore..." Dialogues are natural: weekend planning, teasing about football ("Ти завжди будеш дивитися футбол!"). Good use of "Чудово!" as a reaction. The prose explaining grammar is clear and direct. Minor deduction: the Практика section's verb conjugation lists (6 verbs × 6 forms = 36 forms) are somewhat dry — functional but not engaging. The sentence-building section that follows compensates well. |
| 7. Structural integrity | 10/10 | All H2 headings match plan sections: Dialogues, Майбутній час, Практика, Summary. No duplicate sections, no meta-commentary blocks, no stray tags. Clean markdown with proper table formatting. Word count 1262 is within target range (1200 minimum). :::note and :::tip blocks are well-placed and content-appropriate. |
| 8. Cultural accuracy | 10/10 | Ukrainian presented on its own terms. The grammar explanation uses Ukrainian terminology (майбутній час, складений майбутній, минулий/теперішній/майбутній). No "like Russian but..." framing. The note about synthetic future (читатиму) is factual and neutral. Fortune-teller scene is culturally appropriate — ворожка at a fair is a recognizable cultural setting. |
| 9. Dialogue & conversation quality | 10/10 | Three distinct dialogues with named speakers (Ворожка/Клієнт, Андрій/Марина, Оксана/Тарас). Fortune-teller scene is creative and memorable. Андрій/Марина dialogue is natural multi-turn conversation about daily plans with a progression (tomorrow → evening → Олена → walking together → kids). Оксана/Тарас dialogue includes playful teasing ("Ти завжди будеш дивитися футбол!"). No interrogation patterns. Culturally appropriate (weekend planning, family activities). |

## Findings

[EXERCISE QUALITY] [MINOR]
Location: Plan activity_hints, fill-in exercise #1 — all items: `{буду|буде|будемо}`, `{будеш|буду|будете}`, `{буде|будуть|будемо}`, etc.
Issue: All correct answers are in the first position in the plan's activity_hints. If the pipeline does not randomize option order, this creates a pattern learners could exploit.
Fix: This is a pipeline/activity-generation concern, not a content issue. The activity YAML generator should randomize option positions. No content fix needed — informational only.

## Verdict: PASS

All dimensions score ≥9. No linguistic errors found — all Ukrainian verified against VESUM and style guides. Grammar explanations are factually correct and match Grade 3-4 textbook approach. Three well-placed exercises match plan exactly. Dialogues are natural and engaging. Word count (1262) meets the 1200 target. The module is a clean, well-structured introduction to the analytic future tense.
