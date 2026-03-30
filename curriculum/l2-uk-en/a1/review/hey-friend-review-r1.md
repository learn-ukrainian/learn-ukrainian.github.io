Now I have all the evidence I need. The Litvinova attribution for Насте/Катре is **confirmed correct** (Litvinova Grade 6, p. 151: "Але: Насте, Катре"). Let me compile the full review.

---

## Linguistic Scan

**Russianisms:** None found.
**Surzhyk:** None found.
**Calques:** None found. "Радий бачити" checked against Антоненко-Давидович — no flag.
**Paronyms:** None found.
**Russian characters (ы, э, ё, ъ):** None found.

**All vocative forms verified against VESUM:**
- друже (v_kly of друг) ✅, козаче (v_kly of козак) ✅, тату (v_kly of тато) ✅, дочко (v_kly of дочка) ✅, синку (v_kly of синок) ✅, мамо, сестро, подруго, пане, брате, вчителю, дідусю, бабусю — all confirmed ✅

**Textbook claims verified:**
- "Але: Насте, Катре" attributed to Litvinova Grade 6 — **confirmed** (p. 151) ✅
- "пан Євген → пане Євгене, Іван Вікторович → Іване Вікторовичу" from Litvinova — **confirmed** (p. 141) ✅
- "тату, сину, діду" as exceptions — **confirmed** in Litvinova (p. 159) ✅
- Patronymics in -ович take -у — **confirmed** in both Litvinova and Avramenko ✅

**One factual issue found:**

The module says: "One exception to memorize: **тато** → **тату** — an exceptional **-у** ending, listed alongside **сину** and **діду** in textbooks."

Litvinova (p. 159) actually lists these as: "Але: тату, сину, діду" — under "Тверда група" of II відміна. The module implies тато → тату is the sole exception ("One exception"), but тату/сину/діду are a group of three exceptions. Minor imprecision — it does mention "listed alongside сину and діду" which partially corrects this.

**Dialogue 2 — factual/logic issue:**

Марко asks "Тату, а де ключі?" but Тато responds "У кишені, дочко" addressing the daughter, not Марко. The aside "— he's talking to Марко's sister" is raw English text inside the dialogue `<div>`, breaking the established format of `*(translation)*`. This creates both a naturalness problem (why is тато answering someone else's question?) and a formatting inconsistency.

## Exercise Check

**Markers found (4):**
1. `<!-- INJECT_ACTIVITY: quiz-vocative -->` — after Section 2 (Кличний відмінок) ✅
2. `<!-- INJECT_ACTIVITY: fill-in-vocative -->` — after Section 3 (Закінчення кличного) ✅
3. `<!-- INJECT_ACTIVITY: quiz-choose-vocative -->` — in Section 4 (Підсумок)
4. `<!-- INJECT_ACTIVITY: group-sort-vocative -->` — in Section 4 (Підсумок)

**Plan activity_hints (4):** fill-in, quiz, group-sort, fill-in (dialogue). Count matches (4 markers for 4 hints) ✅

**Issue:** Markers 3 and 4 are both in the summary section, creating a cluster. The plan's 4th activity (fill-in dialogue completion) maps to no specific marker — the `quiz-choose-vocative` marker is a quiz, not a fill-in dialogue. The marker names don't perfectly map to the plan's hint types, but this is minor since the ACTIVITIES step generates from the plan's YAML.

**Marker placement after teaching:** Each marker appears after the relevant content is taught ✅

## Scores

| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | All 4 content_outline sections present with correct topics. Dialogues match plan scenarios. **Deduction:** Required vocabulary **пані** (Mrs./Ms.) is completely absent from prose — plan lists it as required. The plan's dialogue_situations specify "Іменинник (birthday person)" but the module uses this setting well. Section word budgets roughly balanced. Litvinova and Grade 4 textbook references are integrated naturally. |
| 2. Linguistic accuracy | 10/10 | Every vocative form verified against VESUM. All 13 vocative forms batch-verified ✅. Consonant alternation rules (г→ж, к→ч) confirmed by VESUM (друже, козаче). Textbook references verified against Litvinova Grade 6 (pp. 141, 151, 159) and Avramenko Grade 6 (§54). No Russianisms, no Surzhyk, no calques, no paronyms. Gender and case correct throughout. |
| 3. Pedagogical quality | 9/10 | Excellent PPP flow: dialogues first (situation), then explicit rule explanation (pattern), then practice markers. The nominative-vs-vocative contrast ("Олена прийшла" vs "Олено, ходи сюди!") is an effective pedagogical device — matches how Grade 4 textbooks present it (cf. Varzatska p. 38: "Оксанка каже..." vs "Оксанко, скажи..."). 3+ examples per pattern. The "Hey, him!" analogy is approximate but effective for A1 learners. |
| 4. Vocabulary coverage | 8/10 | All required vocab present EXCEPT **пані** — a required word that is never used or explained. This matters pedagogically: пані is невідмінюване (invariable), so its vocative = називний, which is a useful contrast to teach. All 6 recommended words (синку, дочко, козак, вчитель, бабуся, дідусь) are naturally used in context. New words introduced through dialogues, not lists. |
| 5. Exercise quality | 9/10 | 4 markers for 4 plan hints — correct count. Types roughly match plan (quiz, fill-in, group-sort). Markers placed after relevant teaching content. **Minor deduction:** 2 of 4 markers clustered in the summary section rather than distributed. No dialogue-completion fill-in marker explicitly matching the plan's 4th activity hint. |
| 6. Engagement & tone | 9/10 | No motivational openers, no "Let us explore...", no gamified language. The birthday party setting is concrete and engaging. Good cultural framing: "the vocative is one of the ways Ukrainian encodes human connection directly into grammar." The self-check at the end ("Can you call your own family?") is genuine engagement. **Minor deduction:** The sentence "This is not a formal or old-fashioned feature" slightly tells rather than shows. |
| 7. Structural integrity | 9/10 | All 4 H2 headings from plan present and correctly ordered. Clean markdown. Word count 1204 meets 1200 target. **Deduction:** The raw English aside in Dialogue 2 ("— he's talking to Марко's sister") breaks the established `*(translation)*` formatting pattern and sits inside the dialogue div as unformatted text. |
| 8. Cultural accuracy | 10/10 | Fully decolonized — Ukrainian presented on its own terms. No "like Russian but..." comparisons. The description of vocative as "alive and vibrant in modern Ukrainian" is accurate and culturally respectful. Grade 4 textbook references ground the teaching in Ukrainian pedagogy. |
| 9. Dialogue & conversation quality | 8/10 | Dialogue 1 is excellent — natural multi-turn, named speakers, realistic party setting, each vocative form used organically. **Dialogue 2 has a logic problem:** Марко asks "Тату, а де ключі?" but Тато responds "У кишені, дочко" — addressing the daughter instead of the person who asked. The English aside "he's talking to Марко's sister" patches the confusion rather than fixing the flow. The dialogue would be natural if Оля asked the question, making Тато's "дочко" response logical. |

## Findings

**[VOCABULARY COVERAGE] [MAJOR]**
Location: Entire module — пані never appears
Issue: Plan lists **пані (Mrs./Ms., f)** as required vocabulary, but the word never appears in the prose. пані is невідмінюване (vocative = називний), which is a pedagogically important contrast to teach alongside words that change.
Fix: Add пані to the vocative endings section, noting it doesn't change. Natural insertion point: after the masculine -е pattern where пан → пане is taught.

**[DIALOGUE QUALITY] [MAJOR]**
Location: Dialogue 2, lines 3-4:
`Марко: Тату, а де ключі?` / `Тато: У кишені, дочко. — he's talking to Марко's sister`
Issue: Марко asks about keys but Тато addresses дочко (the daughter), creating an illogical exchange. The English aside breaks dialogue formatting and patches rather than fixes the confusion.
Fix: Have Оля ask this question instead of Марко, making тато's "дочко" response natural. Remove the English aside.

**[STRUCTURAL INTEGRITY] [MINOR]**
Location: Same Dialogue 2 line — `— he's talking to Марко's sister`
Issue: Raw English text outside the `*(translation)*` format pattern established by all other dialogue lines.
Fix: Resolved by the Dialogue 2 restructure above.

**[EXERCISE QUALITY] [MINOR]**
Location: Section 4 (Підсумок) — markers 3 and 4 clustered
Issue: `quiz-choose-vocative` and `group-sort-vocative` both in the summary. Ideally one would be earlier for better pacing.
Fix: Move `group-sort-vocative` marker to after the feminine endings subsection in Section 3, where learners have enough knowledge to sort -о vs -е vs -ю.

## Verdict: REVISE

Two major findings (missing required vocabulary пані, unnatural dialogue flow) prevent PASS. All fixes are targeted patches — no rewrite needed. Linguistic accuracy is excellent; the core teaching is strong.

<fixes>
- find: "Full name address follows the same pattern. From Litvinova Grade 6: **пан Євген** → **пане Євгене**, **Іван Вікторович** → **Іване Вікторовичу**. Masculine patronymics in **-ович** take **-у**: **Іванович** → **Івановичу**."
  replace: "Full name address follows the same pattern. From Litvinova Grade 6: **пан Євген** → **пане Євгене**, **Іван Вікторович** → **Іване Вікторовичу**. Masculine patronymics in **-ович** take **-у**: **Іванович** → **Івановичу**. Note: **пані** (Mrs./Ms.) is невідмінюване — it does not change in any case, including vocative. You simply say **пані Оксано!** where **пані** stays the same and only the name takes the vocative ending."
- find: "<div class=\"dialogue-line\"><span class=\"speaker\">Марко:</span> Тату, а де ключі? *(Dad, and where are the keys?)*</div>\n\n<div class=\"dialogue-line\"><span class=\"speaker\">Тато:</span> У кишені, дочко. *(In the pocket, daughter.)* — he's talking to Марко's sister</div>"
  replace: "<div class=\"dialogue-line\"><span class=\"speaker\">Оля:</span> Тату, а де ключі? *(Dad, where are the keys?)*</div>\n\n<div class=\"dialogue-line\"><span class=\"speaker\">Тато:</span> У кишені, дочко. *(In the pocket, daughter.)*</div>"
- find: "<!-- INJECT_ACTIVITY: fill-in-vocative -->\n\n## Підсумок — Summary"
  replace: "<!-- INJECT_ACTIVITY: fill-in-vocative -->\n\n<!-- INJECT_ACTIVITY: group-sort-vocative -->\n\n## Підсумок — Summary"
- find: "<!-- INJECT_ACTIVITY: quiz-choose-vocative -->\n\n<!-- INJECT_ACTIVITY: group-sort-vocative -->"
  replace: "<!-- INJECT_ACTIVITY: quiz-choose-vocative -->"
</fixes>
