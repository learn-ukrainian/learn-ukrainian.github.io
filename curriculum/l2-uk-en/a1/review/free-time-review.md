

Good — "Лєна" is confirmed in VESUM as a valid Ukrainian noun (proper name). Now let me compile the full review.

## Linguistic Scan

**Russianisms:** None found. All vocabulary is proper Ukrainian.

**Surzhyk:** None found.

**Calques:** None found. The phrase patterns (грати у футбол, грати на гітарі, ходити в кіно) are natural Ukrainian — Антоненко-Давидович does not flag them.

**Paronyms:** None found.

**Russian characters (ы, э, ё, ъ):** None found.

**Gender/case verification:**
- "кіно (cinema, n — indeclinable)" — correct
- "грати на гітарі" — locative of гітара, correct
- "грати на скрипці" — locative of скрипка, correct
- "слухати музику" — accusative of музика, correct
- "дивитися фільми" — accusative plural of фільм, correct

**Factual claims verified:**
- "іноді is more common" than інколи — GRAC confirms: іноді 44.45 ppm vs інколи 22.42 ppm ✓
- "ніколи requires не (double negation)" — correct Ukrainian grammar ✓
- снідаю is a valid form of снідати (verb:imperf:pres:s:1) — VESUM confirmed ✓
- All 97 content words confirmed in VESUM; 42 "not found" entries are stress-mark splitting artifacts (e.g., "Приві́т" → "Приві" + "т"), not real errors ✓

**No linguistic errors found.**

## Exercise Check

Three `<!-- INJECT_ACTIVITY -->` markers found:

1. `<!-- INJECT_ACTIVITY: match-hobby-verbs -->` — placed after the hobby verbs + грати у/на section. Matches plan's match-up activity hint. Correct placement ✓
2. `<!-- INJECT_ACTIVITY: fill-in-prepositions -->` — placed after the ходити в/на section. Matches plan's 3rd fill-in activity (prepositions). Correct placement ✓
3. `<!-- INJECT_ACTIVITY: fill-in-frequency -->` — placed after the frequency adverbs teaching section. Matches plan's 2nd fill-in activity (frequency). Correct placement ✓

Plan specifies 3 activity hints (1 match-up + 2 fill-in). Content has exactly 3 markers. All placed after the relevant teaching, evenly distributed across sections 2 and 3. ✓

No inline DSL exercises — all deferred to YAML injection. This is correct for core A1 modules.

## Scores

| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | All 4 content_outline sections present and well-covered. All 8 required vocab words used naturally in prose. All 7 recommended vocab words present (завжди, зазвичай, ніколи, театр, концерт, музей, давай, раз). Word count 1482 exceeds 1200 target ✓. **Deductions:** (a) Plan specifies speakers "Вітя" and "Оленка" in `dialogue_situations` but content uses "Вітя" and "Лєна" — the name was changed without justification. (b) **Давай!** is listed as a plan objective ("Invite someone to an activity using Ходімо! / Давай!") but is only mentioned in the summary list — never demonstrated in a dialogue or taught with examples. Ходімо is well-demonstrated in Dialogue 1; Давай deserves equal treatment. |
| 2. Linguistic accuracy | 10/10 | All Ukrainian verified against VESUM (97/97 real words confirmed). грати у + sport / грати на + instrument patterns correct. Frequency adverbs all verified. Double negation (ніколи не) correctly explained. No Russianisms, surzhyk, calques, or paronyms found (verified via style guide search). іноді vs інколи frequency claim verified via GRAC (44.45 vs 22.42 ppm). |
| 3. Pedagogical quality | 9/10 | Strong PPP flow: dialogues present patterns in context → explicit teaching sections extract rules → practice markers follow each section. Chunks approach (learn verb+object together, not separately) is excellent pedagogy. 3+ examples per grammar point throughout. Frequency scale visual (завжди → ніколи) is clear and memorable. Cross-references to prior modules (M15, M19, M24, M25) help learners build connections. Minor: the "грати у vs на" distinction could benefit from one more contrastive pair to reinforce the pattern. |
| 4. Vocabulary coverage | 9/10 | All 8 required words used naturally in prose. All 7 recommended words present. Additional vocabulary beyond plan (волейбол, скрипка, серіали, фотографувати) enriches the module appropriately. Words introduced in context (chunks), not as bare lists. Minor deduction: **давай** appears only in summary, not contextualized in a dialogue or example sentence. |
| 5. Exercise quality | 9/10 | 3 markers matching 3 plan activity hints exactly. Placement after relevant teaching sections is correct. Match-up covers verb-noun pairings (грати↔у футбол, слухати↔музику). Fill-in exercises cover both prepositions and frequency — the two core grammar points. Exercises test language skill, not content recall. No issues with marker placement or count. |
| 6. Engagement & tone | 10/10 | No motivational openers, no "let us explore" meta-commentary, no generic enthusiasm. Tone is direct and teacher-like: "Notice how Лєна uses Ходімо! to invite Вітя." Practical tips ("Don't choose the preposition — learn the whole phrase"). Two natural interactive prompts ("Your turn: pick two or three of your own hobbies…", "Try it yourself…"). Closing line in Ukrainian is encouraging without being patronizing. |
| 7. Structural integrity | 10/10 | All 4 H2 sections from plan present in correct order. Clean markdown with proper div classes for dialogues. No duplicate summaries, no meta-commentary sections, no stray tags. Word count 1482 is within range (1200 target, exceeded as expected). Caution and note callouts used appropriately. |
| 8. Cultural accuracy | 10/10 | Ukrainian presented on its own terms. No comparisons to Russian. The chunk-learning approach (ходити в кіно as a unit) respects how Ukrainian actually works rather than imposing English grammar categories. Community center setting is culturally natural. |
| 9. Dialogue & conversation quality | 9/10 | Two named speakers (Вітя, Лєна) with distinct voices. Dialogue 1 flows naturally: greeting → question → invitation → time negotiation → agreement. Dialogue 2 builds naturally from sports → frequency → additional hobbies → museum. Both are multi-turn (7-8 lines). Culturally appropriate responses. Minor deduction: both dialogues feature the same two speakers — adding a brief third exchange or using Давай! in context would strengthen variety. |

## Findings

```
[1. Plan adherence] [MAJOR]
Location: Dialogue sections — "Лєна:" appears as speaker throughout
Issue: Plan's dialogue_situations specifies speakers "Вітя" and "Оленка", but content uses "Вітя" and "Лєна". The name change is unjustified. Plan is source of truth.
Fix: Replace "Лєна" with "Оленка" throughout both dialogues and the explanatory text.
```

```
[1. Plan adherence] [MAJOR]
Location: Summary section — "Ходімо! Давай! (Let's go! Let's!)"
Issue: Plan objective #2 says "Invite someone to an activity using Ходімо! / Давай!" — but Давай! is only mentioned in the summary list. It is never demonstrated in a dialogue, never taught with example sentences, and never practiced. Ходімо gets full dialogue demonstration; Давай deserves equal treatment.
Fix: Add a brief exchange using Давай! in Dialogue 1 (naturally fits the invitation context) and add 2-3 example sentences in the summary showing Давай! in use.
```

## Verdict: REVISE

Two major findings: (1) speaker name deviates from plan source of truth, (2) Давай! is a plan objective that's barely covered. No linguistic errors — the Ukrainian is clean. The module is strong overall but needs these two targeted fixes.

<fixes>
- find: "Вітя and Лєна are standing by a bulletin board at the community center, scanning sign-up sheets for weekend activities."
  replace: "Вітя and Оленка are standing by a bulletin board at the community center, scanning sign-up sheets for weekend activities."
- find: "<div class=\"dialogue-line\"><span class=\"speaker\">Лєна:</span> Приві́т, Вітю! Що ти ро́биш у вихідні́? *(Hi, Vitya! What are you doing on the weekend?)*</div>"
  replace: "<div class=\"dialogue-line\"><span class=\"speaker\">Оленка:</span> Приві́т, Вітю! Що ти ро́биш у вихідні́? *(Hi, Vitya! What are you doing on the weekend?)*</div>"
- find: "<div class=\"dialogue-line\"><span class=\"speaker\">Лєна:</span> А в субо́ту? Ході́мо в кіно́! *(And on Saturday? Let's go to the cinema!)*</div>"
  replace: "<div class=\"dialogue-line\"><span class=\"speaker\">Оленка:</span> А в субо́ту? Ході́мо в кіно́! *(And on Saturday? Let's go to the cinema!)*</div>"
- find: "<div class=\"dialogue-line\"><span class=\"speaker\">Лєна:</span> О п'я́тій. *(At five.)*</div>"
  replace: "<div class=\"dialogue-line\"><span class=\"speaker\">Оленка:</span> О п'я́тій. *(At five.)*</div>"
- find: "<div class=\"dialogue-line\"><span class=\"speaker\">Лєна:</span> Так, звича́йно! *(Yes, of course!)*</div>"
  replace: "<div class=\"dialogue-line\"><span class=\"speaker\">Оленка:</span> Так, звича́йно! *(Yes, of course!)*</div>"
- find: "Notice how Лєна uses **Ходімо!** (Let's go!) to invite Вітя. This is the natural Ukrainian invitation — **Ходімо** + activity + day + time. She names the activity (**в кіно**), the day is already clear (**в суботу**), and when Вітя asks **О котрій?** (At what time?), she gives a time from M25: **О п'ятій** (At five)."
  replace: "Notice how Оленка uses **Ходімо!** (Let's go!) to invite Вітя. This is the natural Ukrainian invitation — **Ходімо** + activity + day + time. She names the activity (**в кіно**), the day is already clear (**в суботу**), and when Вітя asks **О котрій?** (At what time?), she gives a time from M25: **О п'ятій** (At five). There's a second invitation word: **Давай!** (Let's! — informal). While **Ходімо** suggests going somewhere together, **Давай** is broader — it works for any shared activity: **Давай пограємо у теніс!** (Let's play tennis!), **Давай послухаємо музику!** (Let's listen to music!)."
- find: "<div class=\"dialogue-line\"><span class=\"speaker\">Лєна:</span> Так, я гра́ю у футбо́л. *(Yes, I play football.)*</div>"
  replace: "<div class=\"dialogue-line\"><span class=\"speaker\">Оленка:</span> Так, я гра́ю у футбо́л. *(Yes, I play football.)*</div>"
- find: "<div class=\"dialogue-line\"><span class=\"speaker\">Лєна:</span> Дві́чі на ти́ждень, у вівто́рок і четве́р. *(Twice a week, on Tuesday and Thursday.)*</div>"
  replace: "<div class=\"dialogue-line\"><span class=\"speaker\">Оленка:</span> Дві́чі на ти́ждень, у вівто́рок і четве́р. *(Twice a week, on Tuesday and Thursday.)*</div>"
- find: "<div class=\"dialogue-line\"><span class=\"speaker\">Лєна:</span> І́ноді слу́хаю му́зику і малю́ю. *(Sometimes I listen to music and draw.)*</div>"
  replace: "<div class=\"dialogue-line\"><span class=\"speaker\">Оленка:</span> І́ноді слу́хаю му́зику і малю́ю. *(Sometimes I listen to music and draw.)*</div>"
- find: "<div class=\"dialogue-line\"><span class=\"speaker\">Лєна:</span> Рі́дко. Раз на мі́сяць. *(Rarely. Once a month.)*</div>"
  replace: "<div class=\"dialogue-line\"><span class=\"speaker\">Оленка:</span> Рі́дко. Раз на мі́сяць. *(Rarely. Once a month.)*</div>"
- find: "The key question here is **Як часто?** (How often?) — it opens the door to frequency adverbs like **іноді** (sometimes) and **рідко** (rarely), plus numeric expressions like **двічі на тиждень** (twice a week). Лєна answers naturally, combining hobby verbs with how often she does each one."
  replace: "The key question here is **Як часто?** (How often?) — it opens the door to frequency adverbs like **іноді** (sometimes) and **рідко** (rarely), plus numeric expressions like **двічі на тиждень** (twice a week). Оленка answers naturally, combining hobby verbs with how often she does each one."
- find: "Two communicative tools from these dialogues: **Ходімо!** (Let's go!) for invitations, and **Як часто?** (How often?) for asking about frequency."
  replace: "Three communicative tools from these dialogues: **Ходімо!** (Let's go!) for going somewhere together, **Давай!** (Let's!) for any shared activity, and **Як часто?** (How often?) for asking about frequency."
- find: "2. **Invitation patterns** — **Ходімо!** (Let's go!) + activity + time + day. This is the native Ukrainian way to invite someone, using the 1st person plural imperative. Combine with days from M24 and times from M25 for a complete invitation."
  replace: "2. **Invitation patterns** — **Ходімо!** (Let's go!) + destination + time + day for going somewhere together. **Давай!** + verb for any shared activity: **Давай пограємо!** (Let's play!), **Давай подивимося фільм!** (Let's watch a film!). Both are natural Ukrainian invitations — combine with days from M24 and times from M25 for a complete invitation."
- find: "- How do you say \"let's go to the cinema\"? → **Ходімо в кіно!**"
  replace: "- How do you say \"let's go to the cinema\"? → **Ходімо в кіно!**\n- How do you say \"let's play tennis\"? → **Давай пограємо у теніс!**"
</fixes>
