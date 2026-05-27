---
date: 2026-05-27
session: "Part 8 of the multi-day m20 V7 anchor sprint. Continuation of 2026-05-26 Pt 4-7. THE BIG ONE: m20 V7 anchor SHIPPED in PR #2364 — first V7 A1 module under the post-reset 4-tab shape after 17 m20 build rounds across 4 sessions. Driven through 7 m20 rounds (#11-#17) + 8 PRs this session via codex-tools writer, with two surgical orchestrator fixes for activity-schema gaps. Round #15 was the load-bearing build (28/28 python_qg + 17/18 wiki gates by writer, then 18/18 after the slash-union parser fix in PR #2363, then 9.3 decolonization under the rubric recalibration in PR #2358)."
status: m20-v7-anchor-shipped
main_sha: 38f6348cd5 (post PR #2364)
main_green: clean
working_tree_dirty: 0 files (this handoff doc untracked until PR)
---

# 2026-05-27 — Part 8: m20 V7 anchor SHIPPED 🎉

**Read the TL;DR. Then skim the next-session opening sequence.** The juicy story is in the round-by-round section if you want it.

## TL;DR

**m20 (`a1/my-morning`) shipped as PR #2364 (`38f6348cd5`)** — first V7 A1 module under the post-reset 4-tab shape. 17 m20 build rounds across 4 sessions delivered this; 11 PRs in this session alone built and shipped it.

Across the day:
- **11 PRs merged** (#2350, #2352, #2354, #2355, #2356, #2357, #2358, #2359, #2360, #2363, #2364)
- **7 m20 build rounds fired** (#11 through #17, plus a resume-style empirical validation)
- **4 distinct V7 bugs root-caused and fixed** (writer prompt overshoot, wiki XML row parser, LLM-QG decolonization rubric, wiki gate slash-location parser)
- **Bio R1a pilot landed** (PR #2354) — 3 dossiers validating the 5-agent scale-up plan
- **Antigravity UI bridge built** (PR #2359)
- **Empirical writer comparison** at A1: codex-tools clearly wins on first attempt; gemini-tools needs adaptation work
- **4 issues filed** (#2351, #2353, #2361, #2362) for follow-up

Main went `6f2a440859` → `38f6348cd5` (10 squash commits).

## Next-session opening sequence

**Immediate (within 30 min of resume):**

1. **Write Pt 9 handoff or jump straight to bio scale-up.** The "juicy details" the user asked for are in this Pt 8 — read the round-by-round forensic section and the decisions-card-worthy findings, then plan accordingly.
2. **Update `docs/decisions/2026-05-06-writer-selection-codex-gpt55.md`** with the codex-tools-ships-A1 empirical record. The 17-round arc + the round #16b gemini-tools failure modes are the decision-card update content. **codex-tools as A1 writer should be the new default** based on this run.
3. **Bio scale-up unblock.** Per user direction 2026-05-27, scale-up was DELAYED until: (a) writer/review prompts resolved [✓ done], (b) agy bridge shipped [✓ done — PR #2359], (c) both gemini+codex have made A1 m20 [codex ✓ shipped; gemini still incomplete]. Strict reading: still blocked on gemini m20. Pragmatic reading: codex empirically dominant; user direction was about empirical comparison which we now have, even if gemini didn't pass. **Recommend asking the user** before firing scale-up.
4. **File the activity_schema gate divergence** as a follow-up issue (the python_qg `activity_schema` gate passed round #15's activities.yaml but the strict `ActivityParser` at MDX-assembly time rejected 2 of 10 activities — observe with dict examples, translate with `{prompt, answer}` shape). The 2 fixes are in PR #2364; the underlying gate-vs-parser divergence needs documentation + a tightening pass.

**Latent:**

- Update `docs/session-state/current.md` to point at this Pt 8 handoff (the file at HEAD is stale at Pt 5).
- Round-by-round m20 build worktrees still on disk under `~/.codex/worktrees/3a9a/learn-ukrainian/.worktrees/builds/`. Per #M-10 forensic-keep until promotion validated (it is) — they're safe to clean now if disk pressure exists, but no urgency.

## The juicy details — round-by-round forensic story

This is the chunk to read if you want the full story.

### Starting state (2026-05-26 Pt 7 close)

m20 round #12 (codex-tools) had cleared every pipeline gate except `llm_qg.decolonization` at **8.5 vs A1 floor 9.0** — terminal halt. The user's empirical question: "is this just about limits, not quality?"

### User direction 2026-05-27 morning (load-bearing principle)

> "we cannot always force anti-colonization. we are teaching a language, which was depressed, if we teach clean ukranian that is 10 anticolonization. do you agree?"

This is the load-bearing pedagogical principle. Teaching codified Ukrainian — сніданок (not завтрак), рушник (not полотенце), одягатися (not одіватися) — IS the substantive decolonization act. Forcing additional anti-colonial rhetoric on top of clean canonical teaching politicizes grammar lessons without pedagogical value.

This principle drove the entire arc that followed.

### Path: shift from writer-side to reviewer-side fix

My initial plan was to add `#R-DECOLONIZATION-DENSITY` to the writer prompt requiring 2-3 explicit decolonization touches per module — which would have forced exactly the kind of rhetoric the user said to avoid. The user's message redirected the fix to the REVIEWER side.

**PR #2358** recalibrated `linear-review-dim.md`'s `decolonization` rubric:
- **Anchor**: "teaching codified Ukrainian to learners of a historically depressed language IS the substantive decolonization act"
- **Topic-neutral modules** (grammar/vocab/phonetics): 9.0+ baseline if (a) Ukrainian-canonical vocab + (b) ≥1 bad-form contrast marker + (c) grammar on Ukrainian terms. Additional rhetoric is BONUS not required.
- **Topic-loaded modules** (history/bio/literature/war): higher bar — must explicitly name Russification / imperial framing / Soviet euphemisms.
- Defines REVISE and REJECT territories explicitly.

### Round #13: codex regressed on word_count after prompt edit

Fired round #13 expecting decolonization to clear under the new rubric. **Codex regressed on word_count** (gate=1022 vs floor 1104, wc=1228 — only 2.3% overshoot). The recalibrated rubric was never reached because python_qg halted first. Surprising — codex hit 1115/1134 in earlier rounds. Hypothesis: relay framing emphasized decolonization, codex deprioritized word budget.

### Round #14: word_count cleared, wiki failed on step-5

Sent a more emphatic relay on word count. Round #14: word_count 1128 ✓ but **wiki_coverage_gate 17/18 — step-5 missing the "Крок 5" section heading marker**. Each round, something different broke. This is the codex-thread-drift pattern: each round, attention focuses on what's emphasized in the relay; what's NOT emphasized regresses.

### Pivot: empirical test of the recalibrated rubric against round #12's actual artifacts

Rather than chase codex's drift across more rounds, wrote a small Python harness that called `invoke_reviewer_dim` directly against round #12's existing module.md/activities.yaml — testing whether the recalibrated rubric would now score it 9.0+.

**Result: 8.7** (up from 8.5 with the old rubric). Slight improvement, still 0.3 short.

Reviewer's specific finding: *"the absent explicit bad-form contrast pair — for an A1 routine module where learners are likely to encounter завтрак / полотенце / одіваться from L1-Russian carryover, one explicit marker pair would have lifted this cleanly to 9.0+."*

Verified across rounds #12/#13/#14: **ZERO** bad-form markers in any codex `module.md`. The existing `#R-BAD-FORM-MARKER` rule mandates the SYNTAX when used but doesn't REQUIRE the writer to include any.

### PR #2360: positive requirement for ≥1 bad-form contrast pair

Added to `linear-write.md`'s `#R-BAD-FORM-MARKER`: A1-A2 vocabulary modules covering L1-Russian-substitutable domains (food, household, clothing, daily routines, family, body, time, transportation, common verbs) MUST include AT LEAST ONE explicit bad-form contrast pair using `<!-- bad -->...<!-- /bad -->` syntax. Framed as pedagogical first (contrast pairs accelerate L2 acquisition), rubric-satisfying second. Not forcing extra rhetoric — just one concrete contrast.

### Round #15: bad-form marker present, only ban-4 substance missing

Fired round #15. Codex added the `<!-- bad -->завтрак<!-- /bad -->` marker. Results:
- python_qg: **28/28 PASS** (word_count 1115, wc=1343, chunk_context=2, tool_theatre=0, dialogue=35)
- Bad-form marker: ✓ present at module.md:29
- wiki_coverage 17/18: only `ban-4` failed `ban_substance_missing`

Investigation: round #15's module.md line 30 had a 4-sentence Ukrainian-prose rejection of all three Russified forms PLUS the age-construction calque. Substance was there. Why did the gate fail it?

### The wiki_coverage parser bug

Codex's `<row .../>` for ban-4 claimed `location="§Діалоги/§Підсумок"` (forward-slash-joined). The gate's `_location_text` parser treated the slash-joined string as ONE search key. Title-gap tiebreaker preferred §Підсумок (`|len("підсумок") - len("діалоги/§підсумок")|` = 8) over §Діалоги (gap 9). Gate evaluated substance against §Підсумок (no contrasts) → `ban_substance_missing`. The substance in §Діалоги was invisible to the gate.

### PR #2363: union-resolve multi-part locations

Added at the top of `_location_text`:
```python
parts = [p for p in re.split(r"\s*[/,;]\s*", location.strip()) if p.strip()]
if len(parts) > 1:
    chunks = [_location_text(text, p) for p in parts]
    # dedupe + join
    return "\n".join(deduped_chunks)
```

Slash/comma/semicolon-joined locations now union-resolve. 3 regression tests covering the round #15 envelope + comma variant + the "still fails when genuinely missing" case.

### The empirical validation that mattered

Wrote `/tmp/rerun_wiki_gate_round15.py`: rebased round #15's build worktree onto current main (post-#2363), called `check_wiki_coverage_paths` directly against the existing artifacts.

**Result: passed=True, coverage_pct=1.0, 18/18 obligations PASS.**

Then `/tmp/rerun_llm_qg_round15.py`: called `invoke_reviewer_dim` with claude-tools against round #15's actual module.md/activities.yaml/etc.

**Result: decolonization score 9.3, verdict PASS.** Above A1 floor 9.0. Aggregate terminal_verdict: PASS.

The reviewer's evidence quotes named all three bad-form markers + the сніданок-vs-завтрак stance line + the age-construction calque rejection. Reviewer noted "Not 9.5+ because Quote 3 reads slightly bolted-on (age calque is off-topic for morning routine) and the stance line 'Рішуче відкидай русизми…' is somewhat preachy register for an A1 reader." — pedagogically honest critique, but well above the floor.

### Round #17 was a regression (worth noting for next time)

Between round #15 and the validation run, I'd fired round #17 with codex via bridge asking for the missing ban-4 stance line. **Round #17 regressed catastrophically**: 0/18 wiki obligations (implementation_map_missing). Codex's session had ~36h of accumulated context across rounds #4-#17, and the conversation context degraded. Codex itself flagged "session is near compaction; please /exit and start fresh" in its final response.

This is the **codex-long-thread-drift** pattern. The pragmatic mitigation that worked: don't chase codex's drift with more rounds — use the existing good artifacts (round #15 had 17/18) and fix the gate to credit the substance that was already there.

### Surgical fixes for m20 anchor PR

Round #15's activities.yaml had two schema mismatches that the python_qg `activity_schema` gate didn't catch but the strict `ActivityParser` at MDX-assembly rejected:

1. **`act-3` observe**: `examples` was a list of `{spoken, written}` dicts. Schema requires `list[str]`. Converted to `"<written> → <spoken>"` strings.
2. **Last activity translate**: items had `{prompt, answer}` shape. Schema requires `{source, options[]}`. Pedagogically the right activity for free EN→UK translation is `match-up`. Converted to `pairs=[{left:<en>, right:<uk>}]`.

Both fixes are 1-line content changes; the underlying activity_schema vs ActivityParser divergence is a follow-up bug.

### m20 anchor PR #2364

Opened, CI cleared (only Gemini Dispatch advisory CANCELLED — explicit-advisory exception per MEMORY #M-0.5), merged. Main at `38f6348cd5`. **First V7 A1 module under the post-reset 4-tab shape is on main.**

## Empirical writer comparison — what we learned

Per the user's "we write both gemini and codex made a1 m20" direction, fired round #16 (agy-tools) + round #16b (gemini-tools direct) in parallel with codex rounds.

### codex-tools (the winner at A1)

| Round | python_qg | wiki | llm_qg decolonization | Outcome |
|---|---|---|---|---|
| #11 | 28/28 | parser bug (0/18) | not reached | wiki_coverage parser fix → #2355 |
| #12 | 28/28 | 18/18 | 8.5 (old rubric) | rubric recalibration → #2358 |
| #15 | 28/28 | 17/18 (loc-parser bug) | not reached | gate slash-union fix → #2363, then 9.3 |

Reliable Step B (chunk_context calls), reliable VESUM, occasional drift on word count / specific obligation locations.

### gemini-tools (round #16b) — first-attempt failure modes

| Metric | Result |
|---|---|
| Writer phase wall time | 17 min (codex: 5-10 min) |
| Word count | wc=1771 (47% overshoot — too much) |
| chunk_context_calls | **0** (Step B blind spot — same as claude-tools at A1) |
| tool_calls_total | 3 (codex: 11) |
| VESUM bad-form leak | "нуть" (Russian fragment) |
| Failed gate | long_uk_ceiling + VESUM (no English gloss for long UK passages) |

Gemini at first attempt: NOT publishable. Would need A1-specific writer-prompt iteration to address: Step B compliance, long_uk_ceiling adherence, VESUM strictness.

### agy-tools (round #16) — adapter bug

agy-tools writer dispatched but emitted ZERO sections COT and 2 tool calls, then exited without producing any artifacts. Filed as #2362.

**Conclusion**: codex-tools is the empirically validated A1 writer. The 2026-05-06 decision card should be updated to flip the default from claude-tools to codex-tools (or at minimum cite the empirical evidence and revisit "until next bakeoff signal indicates otherwise"). claude-tools's structural Step B blind spot at A1 (per issue #2351) + gemini-tools's first-attempt failure modes + codex-tools's 28/28 + 18/18 demonstrate the empirical pick.

## What's queued for next session

**Immediate:**

1. (Optional) Write Pt 9 handoff if this session ran further work; otherwise jump to #2.
2. **Update `docs/decisions/2026-05-06-writer-selection-codex-gpt55.md`** with the empirical record (rounds #11-#17, gemini comparison, claude blind spot). Flip A1 writer default to codex-tools.
3. **Update `docs/session-state/current.md`** to point at this Pt 8 handoff (current file is stale at Pt 5).
4. **Ask user: scale-up bio research?** Per 2026-05-27 user direction the gate was (a)+(b)+(c). Strictly (c) is "both gemini and codex have made A1 m20" — codex shipped, gemini hasn't cleanly. Pragmatically the empirical comparison was the point and we have it. User decides.

**Bio scale-up (if user OKs):**

5. Fire 5-agent split per Pt 6 plan (R1a-rest codex / R1b gemini-pro / R2 deepseek-pro / R3 gemini-pro / R5 gemini-pro; R4 needs F2-aligned brief). Batch 3 figures/dispatch.

**Latent:**

6. **File activity_schema vs ActivityParser divergence**: round #15's observe and translate activities passed python_qg's activity_schema gate but failed the strict ActivityParser at MDX assembly. Both gates should agree; the python_qg gate is missing strict schema validation for these activity types.
7. **Issue #2351 update**: claude-tools A1 Step B blind spot has more codex-tools contrast data now (every codex round made Step B calls).
8. **Update MEMORY.md** if appropriate — no urgent additions, the pattern of "codex thread drift over long sessions, use fresh thread for new work" might be worth a one-liner.
9. **Build worktrees on disk**: 9+ m20 build worktrees under `~/.codex/worktrees/.../.worktrees/builds/`. Per #M-10 keep for forensics; OK to clean now that m20 shipped — no urgency.

## PR stack reference (for the decision card update)

| PR | What it fixed | Lesson |
|---|---|---|
| #2305 | textbook_grounding Step B enforcement | Gate masking writer issues = bad signal |
| #2306 | Writer prompt deltas | Diglossia, INJECT_ACTIVITY, cite-honest |
| #2307 | шо reclassified surzhyk → register WARN | Don't penalize legitimate phonetic reductions |
| #2308 | note→notes typo fix | Schema-bound field names are load-bearing |
| #2339 | chunk_context list-shape parser | Codex's tool envelope shape differs from claude's |
| #2340 | Word target → minimum + overshoot guidance | "target" was read as "aim at" not "floor" |
| #2344 | A1-A2 dialogue floor + meta-narration ban | Concrete required counts beat abstract minimums |
| #2350 | Overshoot 10-15% → 18-20% with empirical data | The wc-w vs gate gap is structurally 15%, not 10% |
| #2355 | wiki_coverage XML `<row .../>` parser | Different writers emit different shapes; parsers must accept all reasonable ones |
| #2358 | llm_qg decolonization rubric recalibration | **Clean canonical Ukrainian IS substantive decolonization — don't force rhetoric** |
| #2360 | Writer prompt: ≥1 bad-form contrast pair required | The mandate-syntax rule didn't require inclusion; positive requirement added |
| #2363 | wiki gate slash/comma location union-resolve | Writers emit multi-part locations; gate must union-resolve |
| #2364 | **m20 V7 anchor — first V7 A1 module on main** | 17-round arc complete |

## Session totals

- **PRs merged**: 11 (this session) — #2350, #2352, #2354, #2355, #2356, #2357, #2358, #2359, #2360, #2363, #2364.
- **PRs opened**: 12 (incl. one merged via prior-session linkage).
- **m20 build rounds fired**: 7 (#11-#17 + one resume-style empirical validation).
- **Bio dossiers shipped**: 3 (R1a pilot, PR #2354).
- **Bugs root-caused + fixed**: 4 (writer overshoot framing, wiki XML parser, decolonization rubric calibration, wiki gate slash-location parser).
- **Issues filed**: 4 (#2351 claude Step B blind spot, #2353 Svidzinskyi cross-track gap, #2361 UI-store agy bridge, #2362 agy-tools writer protocol).
- **Main commits**: `6f2a440859` → `38f6348cd5` (10 squash commits).
- **The big one**: **m20 V7 anchor SHIPPED.** First V7 A1 module on main.

End of 2026-05-27 Pt 8. m20 done. Anchor in place. The shape works. Time to scale.
