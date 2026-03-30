I found the actual Авраменко Grade 5 source. Now I have all the evidence I need. Let me compile the review.

---

## Linguistic Scan

**Russianisms:** None found. All vocabulary is standard Ukrainian.

**Surzhyk:** None found.

**Calques:** None found. `search_style_guide` for "любити подобатися", "мити посуд", "грати в ігри", "класична музика" returned no calque warnings for the phrases used in the module.

**Paronyms:** None found.

**Russian characters (ы, э, ё, ъ):** None found.

**Gender/case:** Verified — "Анно" is the correct vocative of Анна (VESUM confirmed: Анно → noun form of Анна). "Готуєш" correctly from готувати (VESUM confirmed). All 69 Ukrainian content words passed VESUM verification. The 6 "not found" are proper nouns (Анна, Анно, Віктор, Інна, Зоя, Авраменко) — all legitimate.

**Factual claim about infinitives:** The module states "Every Ukrainian infinitive ends in **-ти**." Заболотний Grade 7 (p.54) and Авраменко Grade 7 (p.55) both state the infinitive suffix is **-ти (-ть)**, noting -ть is colloquial ("має розмовний характер"). This is a pedagogical simplification acceptable at A1, and the plan's own Літвінова reference says "форма, що закінчується суфіксом -ти." No deduction.

**One pedagogically critical error found — see Findings #1 below.**

## Exercise Check

**Activity markers found:**
1. `<!-- INJECT_ACTIVITY: fill-in-infinitive-picture -->` — after Dialogues section ✅ (matches plan hint 1)
2. `<!-- INJECT_ACTIVITY: match-infinitives-meanings -->` — in "Я люблю" section ✅ (matches plan hint 3)
3. `<!-- INJECT_ACTIVITY: fill-in-infinitive-picture -->` — end of "Я люблю" section ⚠️ **DUPLICATE of marker 1**
4. `<!-- INJECT_ACTIVITY: quiz-structure-choice -->` — in "Мені подобається" section ✅ (matches plan hint 2)
5. `<!-- INJECT_ACTIVITY: fill-in-negative -->` — in "Мені подобається" section ✅ (matches plan hint 4)

**Issues:**
- Duplicate marker `fill-in-infinitive-picture` appears twice (after Dialogues and at end of "Я люблю"). This could cause the same activity to be injected twice during PUBLISH. The second occurrence should be removed.
- All 4 plan activity hints are represented by matching markers.
- Markers are reasonably distributed across sections (not clustered).
- Placement is correct — each marker appears AFTER the concept it tests.

## Scores

| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | All 4 content_outline sections present with correct headings. Both dialogue situations from plan are covered (hobby-sharing in Dialogue 1, подобається in Dialogue 2). All required vocabulary used in prose: любити, подобатися, читати, гуляти, готувати, слухати, дивитися, грати. All recommended vocab included: малювати, подорожувати, співати, музика, фільм, книга. Grammar points covered: infinitive -ти ending, люблю + infinitive, мені подобається as chunk, negation with не. One deduction: plan references "Літвінова Grade 7, p.26-27" not cited; instead unverifiable "Голуб, Grade 5" substituted (see Finding #2). |
| 2. Linguistic accuracy | 8/10 | All Ukrainian words VESUM-verified (69/69 + 6 proper nouns). No Russianisms, surzhyk, or calques found via `search_style_guide`. Case forms correct (Анно = vocative, готуєш = 2nd person). **Deduction:** The Зоя dialogue "мені не подобається гладити" uses подобається + infinitive, directly contradicting the module's own teaching that "Мені подобається + noun = I like something (a thing)." This is a factual/pedagogical error that teaches a wrong rule-example relationship (see Finding #1). |
| 3. Pedagogical quality | 8/10 | Strong PPP flow: dialogues present pattern naturally → explicit rules with 4+ examples per point → practice markers. Infinitive introduced through "люблю + verb" frame (matching Большакова Grade 1 pattern: "Я люблю малювати. Я не люблю грати в хокей." — confirmed in RAG). Good scaffolding: two-form distinction (люблю vs подобається) taught clearly with contrastive pairs. **Deduction:** The Авраменко Grade 5 Інна/Зоя dialogue is used out of context — its original textbook purpose is teaching lexical ambiguity (гладити = "to iron" vs "to pet"), not the люблю/подобається pattern. The truncation loses the pedagogical punchline. And worse, "мені не подобається гладити" breaks the rule just taught. |
| 4. Vocabulary coverage | 10/10 | All 8 required words used naturally in prose contexts (not as bare lists). All 5 recommended words included. New verbs introduced inside the "Я люблю..." frame — contextual, not listed. Additional useful vocabulary: борщ, вареники, кава, джаз, шахи, гітара — all VESUM-verified and level-appropriate (любити = A1 per PULS, подорожувати = A1 per PULS). |
| 5. Exercise quality | 8/10 | 4 distinct activity types matching all plan hints. Marker placement after teaching sections is correct. **Deduction:** Duplicate `fill-in-infinitive-picture` marker — same activity ID appears twice (after Dialogues and at end of "Я люблю"), risking double-injection during PUBLISH. |
| 6. Engagement & tone | 10/10 | No motivational openers, no meta-commentary, no gamified language. Opening sets a concrete scene ("cozy language café in Kyiv... two cups of tea steaming"). Dialogues feel natural — Анна and Віктор share hobbies organically, with culturally specific responses ("Борщ і вареники"). Transitions are teacher-like: "Did you spot the pattern?" rather than "Let us now explore..." Cultural detail: грати в шахи / грати на гітарі distinction explained naturally. |
| 7. Structural integrity | 10/10 | All 4 plan sections present as H2 headings in correct order (Діалоги, Я люблю, Мені подобається, Підсумок). Word count 1488 — above 1200 target. Clean markdown, no stray tags or formatting artifacts. No duplicate summary sections. |
| 8. Cultural accuracy | 10/10 | Ukrainian presented on its own terms — no "like Russian but..." framing. Culturally appropriate examples (борщ, вареники, Київ). The грати в/на distinction is a genuinely Ukrainian pattern taught correctly. No decolonization issues. |
| 9. Dialogue & conversation quality | 9/10 | Dialogue 1 is excellent — natural multi-turn exchange between named speakers, real hobby-sharing situation, culturally appropriate responses ("Смачно!"). Dialogue 2 also good — natural topic shift, varied responses. **Minor deduction:** The Інна/Зоя dialogue (Finding #1) is problematic in context, but as a standalone dialogue it reads naturally with named speakers and realistic household-chore conversation. |

## Findings

**[LINGUISTIC ACCURACY / PEDAGOGICAL QUALITY] [SEVERITY: critical]**
Location: "Мені подобається" section — the Інна/Зоя dialogue:
```
Інна: Я не люблю мити посуд. (I don't like to wash dishes.)
Зоя: А мені не подобається гладити. (And I don't like to iron.)
```
Issue: The module explicitly teaches "Мені подобається + noun = I like something (a thing)" — contrasted with "Я люблю + infinitive = I like doing something." Then this dialogue shows "мені не подобається гладити" — подобається + INFINITIVE, directly contradicting the rule just taught. A learner will be confused: "I was told подобається takes a noun, but this example uses it with a verb."

Additionally, this dialogue is from Авраменко Grade 5 §21 "Лексична помилка" (confirmed via RAG: `5-klas-ukrmova-avramenko-2022_s0055`), where its original purpose is teaching **lexical ambiguity** — the word "гладити" means both "to iron" and "to pet." The textbook continues with Інна's response: "Кого? Хіба гладити — це хатня робота? Для мене це розвага: гладжу кота — і тепло на душі стає…" — that's the whole point. The module truncated the dialogue, losing the punchline and misrepresenting the textbook's pedagogical intent.

Fix: Replace the dialogue with one that uses both patterns correctly — люблю + infinitive and подобається + noun — to reinforce (not contradict) the module's teaching. Keep the textbook attribution accurate.

**[PLAN ADHERENCE] [SEVERITY: major]**
Location: Підсумок section, final paragraph:
```
«Люблю гортати старі книги, бо від них віє спокоєм» — I like to leaf through old books because they breathe calmness (Голуб, Grade 5).
```
Issue: This quote attributed to "Голуб, Grade 5" is not verifiable in the textbook RAG collection. No "Голуб" textbook exists in the indexed corpus. The plan references "Літвінова Grade 7, p.26-27" and "ULP Season 1, Episode 14" — neither of which is cited in the module. An unverifiable textbook reference in an educational module is a trust issue.

Fix: Replace with a verifiable reference or remove the attribution entirely.

**[EXERCISE QUALITY] [SEVERITY: minor]**
Location: End of "Я люблю" section:
```
<!-- INJECT_ACTIVITY: fill-in-infinitive-picture -->
```
Issue: This is a duplicate of the same marker that already appears after the Dialogues section. The same activity ID injected twice would create a duplicate exercise during PUBLISH.

Fix: Remove the second occurrence.

## Verdict: REVISE

Two findings require fixes: one critical (Зоя dialogue contradicts the module's own rule and misuses a textbook source) and one major (unverifiable textbook reference). Both are fixable with targeted find/replace without rewriting the module.

<fixes>
- find: "Here is a real exchange from a Ukrainian textbook (Авраменко, Grade 5):\n\n<div class=\"dialogue\">\n\n<div class=\"dialogue-line\"><span class=\"speaker\">Інна:</span> Я не люблю мити посуд. *(I don't like to wash dishes.)*</div>\n\n<div class=\"dialogue-line\"><span class=\"speaker\">Зоя:</span> А мені не подобається гладити. *(And I don't like to iron.)*</div>\n\n</div>\n\nSee how natural that sounds? Two friends sharing what they *don't* enjoy — **не люблю** + infinitive and **мені не подобається** + infinitive, side by side. The word **не** always goes right before the verb."
  replace: "Here are a few more examples of what negation looks like with both structures:\n\n<div class=\"dialogue\">\n\n<div class=\"dialogue-line\"><span class=\"speaker\">Інна:</span> Я не люблю мити посуд. *(I don't like to wash dishes.)*</div>\n\n<div class=\"dialogue-line\"><span class=\"speaker\">Зоя:</span> А мені не подобається ця страва. *(And I don't like this dish.)*</div>\n\n</div>\n\nSee the pattern? Інна uses **не люблю** + infinitive (an activity she doesn't enjoy), and Зоя uses **мені не подобається** + noun (a thing she doesn't like). The word **не** always goes right before the verb."
- find: "As a Ukrainian textbook puts it: «Люблю гортати старі книги, бо від них віє спокоєм» — *I like to leaf through old books because they breathe calmness* (Голуб, Grade 5). That sentence uses the exact same pattern you just learned. You are ready."
  replace: "As Большакова's Grade 1 reading primer puts it: «Я люблю малювати. Я не люблю грати в хокей. Я люблю грати в шахи.» — even first-graders use the exact same pattern you just learned. You are ready."
- find: "<!-- INJECT_ACTIVITY: fill-in-infinitive-picture -->\n\n## Мені подобається"
  replace: "## Мені подобається"
</fixes>
