---
date: 2026-05-13
session: "Evening — immersion-gate reframe + writer-split-by-tab; 2 Decision Cards proposed; 2 PRs held; gate model fundamentally questioned"
status: ok
detail: 2026-05-13-evening-immersion-reframe-and-writer-split.html
main_sha: 55823800ce
main_green: true
open_prs: [1909, 1915]
active_dispatches: 0
merged_today: [1913]
filed_today: [1910, 1911, 1912, 1914]
closed_today: [1900, 1903, 1910, 1911, 1912]
in_flight: []
proposed_today: ["2026-05-13-immersion-gate-tab-aware-structural.md", "2026-05-13-writer-split-by-tab.md"]
blocked: ["a1/my-morning publication — held pending gate-redesign + writer-split decisions OR explicit override to ship under current gates"]
next_p0: "Decide on the two PROPOSED Decision Cards from this session: (1) immersion-gate-tab-aware-structural — replace global-% with 4 failure-mode-targeted gates; numbers in scripts/config.py SSOT; (2) writer-split-by-tab — per-tab specialized agents (Claude→Tab1, Codex→Tab2/3, Gemini→Tab4). Either can ship without the other; they compose well. Each has a cheap proof-of-concept defined. P0 alternative: revisit deployed A1 strategy — if deployed modules pass new gates on replay, V7 rebuild for A1 may not be needed; pivot to fill-in-missing + surgical-improvement strategy."
agents: [claude, codex, gemini]
worktrees_open: 2
ci_notes: |
  PR #1913 merged cleanly at `37d7881b6` (all blocking CI green; advisory Gemini-Dispatch fail per #M-0.5 ignored). PR #1909 has all blocking CI green but HELD per gate-redesign decision — "aim for middle of band" line in the prompt diff is misaligned with proposed structural gate model. PR #1915 (Track B research artifacts, VERDICT=YELLOW) HELD pending decisions on whether Pass-2 path remains viable.
incidents:
  - "Pattern caught mid-session: I forwarded multi-agent anchor-episode picks (Ep 1/10/20/30/40 from Gemini, 1/15/30/45 from Codex) without verifying that those ARE typical lessons in ULP. User flagged: every 10th in S1 is a Review episode. Confirmed on inspection: agents would have measured atypical formats. Cause: monitoring layer didn't gate `mcp__sources__*` claims. Both agents AND I let an ungrounded sample go to formal proposal stage."
  - "Pattern caught mid-session #2: I claimed deployed A1 'has no audio.' User flagged. On grep: YouTube links exist in `reading-ukrainian.md`, audio refs in `who-am-i.md`, `YouTubeVideo.tsx` component is deployed. The 'no audio' claim was ungrounded. #M-4 violation; surfaced + corrected in conversation."
  - "Pattern caught mid-session #3: I framed the V7 strategy as 'rebuild deployed A1.' User flagged: 'the old content is different, our new version has different structure different design, workbook, in-lesson activities, etc.' The old format is single-page MD; the NEW format is 4-tab (Урок/Словник/Вправи/Ресурси) with typed activity components, governed by `docs/lesson-contract.md`. I had been treating the deployed content as the target for V7 to recreate, when actually V7 is building toward a different artifact shape entirely."
---

# Brief — 2026-05-13 evening — immersion-gate reframe + writer-split-by-tab

> Machine-readable companion to `2026-05-13-evening-immersion-reframe-and-writer-split.html`.
> Predecessor: `2026-05-13-afternoon-bakeoff-and-twopass-brief.md`.

## TL;DR

- **Two PROPOSED Decision Cards filed** — both independent, both with cheap proof-of-concept paths:
  - `2026-05-13-immersion-gate-tab-aware-structural.md` — replace global-% gate with 4 failure-mode-targeted gates (exposure floor / long-UK ceiling / component-aware density / progressive challenge). Tab-aware. Numbers in `scripts/config.py:IMMERSION_POLICIES` (SSOT, NOT in card). Multi-agent convergence channel `immersion-reframe-2026-05-13` (Codex + Gemini round 2, both `[AGREE]`).
  - `2026-05-13-writer-split-by-tab.md` — per-tab specialized writers (Claude→Tab 1, Codex→Tab 2/3, Gemini→Tab 4) replacing monolithic V7 writer. User-proposed direction at session close.
- **Pipeline gate trio shipped** (PR #1913 merged at `37d7881b6`) — vesum sentence-exclusion (#1910), textbook_grounding parser (#1911), immersion display fix (#1912) all closed.
- **PR #1909 (writer-prompt-tune)** held — 3/4 parts survive any gate redesign (citation parity, budget discipline, long-sentence rule); 1 part dies ("aim for middle of band" predicated on rejected gate model).
- **Track B verdict YELLOW** (PR #1915 held) — anchor preservation contract WORKS; immersion failed; partly measurement artifact of misshapen gate.
- **Major strategic insight, surfaced by user:** the V7 rebuild strategy may be solving the wrong problem. Deployed A1 modules (5 read this session) follow the right structural pattern (bilingual headers, pure-UK dialogues with parenthetical gloss, EN-dominant teaching prose). They fail current gates because gates are misshapen, not because content is bad. Replay against new gates would settle empirically.
- **Empirical grounding done this session:** all 6 ULP seasons cataloged (240 episodes), 6 anchor episodes read across seasons, structural-transformation series mapped (metalanguage flip at S1→S2; translation-density flip at S3→S4); 5 deployed A1 modules read and characterized.

## What's in the Decision Cards (summary)

### Card 1 — Immersion gate tab-aware structural

Four gates replace `_immersion_gate()` pass/fail at `linear_pipeline.py:4582-4624`:

| Gate | Catches | Where the numbers live |
|---|---|---|
| L2 Exposure Floor | Pure-EN failure (essay about Ukrainian) | `IMMERSION_POLICIES[level][band].min_uk_dialogue_lines / min_vocab_entries / min_uk_example_sentences / min_uk_tab3_activities` |
| Long-UK-Without-Gloss Ceiling | Wall-of-UK failure | `IMMERSION_POLICIES[level][band].max_unsupported_uk_words` + `.support_proximity` |
| Component-Aware Language Density | Wrong-language-for-wrong-purpose | `IMMERSION_POLICIES[level][band].required_components` + per-component rules |
| Progressive Challenge | Floor-gaming with dull padding | `IMMERSION_POLICIES[level][band].min_target_grammar_coverage_pct / min_target_vocab_coverage_pct` (requires `plan.targets` field; may ship later) |

Global `pct` demoted to advisory telemetry (NOT removed; Codex's "Option A as destination, Option C as migration path"). B1+ Latin-character-ratio gate unchanged.

Phases: A (gate code split + config schema extend) → B (empirical calibration via replay against deployed A1 — NO LLM cost) → C (writer prompt rewrite) → D (one validation bakeoff) → E (Lesson Contract §4.6 amendment).

### Card 2 — Writer split by tab

Replace V7's single-writer-produces-all-4-artifacts with per-tab specialized writers:

| Tab | Artifact | Proposed agent | Why |
|---|---|---|---|
| Tab 1 Урок | `module.md` | Claude | Narrative voice + decolonized framing + MCP verification; today's bakeoff already shows Claude wins on content merit |
| Tab 2 Словник | `vocabulary.yaml` | Codex | Strict YAML schema, VESUM-verified lemmas, no creative bleed |
| Tab 3 Вправи | `activities.yaml` | Codex | 19 typed activity components, mechanical schema correctness |
| Tab 4 Ресурси | `resources.yaml` | Gemini | Already the wiki writer; URL/source handling; unmetered sub |

Consistent with existing patterns (wiki=Gemini, reviewer=non-writer, 3:3:3 dispatch by fit). Recommended implementation: sequential Path A (Tab 1 → Tab 2 → Tab 3 → Tab 4) for proof-of-concept on `a1/my-morning`, ~4 LLM calls + analysis.

## What the convergence-channel said (ai→ai)

Round 1 Codex: `[DISAGREE]` — accept reframe, but Option C (advisory pct stays) not pure Option A. Plan schema doesn't encode section_type today; markdown heuristics are OK for prototype. Hard-fail conditions named: `too_few_uk_sentences`, `too_few_vocab_lemmas`, `long_uk_without_gloss`, missing required components. Missed-failure-mode: floor-gaming.

Round 1 Gemini: `[DISAGREE]` — strongly support reframe (Option A). Section-typed density is the right model. Prior art: Coffee Break S1 ~90% English; Language Transfer ~100% English explanation. **Missed-failure-mode named: Gloss Proximity** — block-by-block translation is still a wall to A1 readers; sentence-by-sentence support required at A1 early. Anchor episodes Ep 1/10/20/30/40.

Round 2 Codex: `[AGREE]` — "Option A as destination, Option C as migration path." Specific implementation citations: `IMMERSION_POLICIES` at `scripts/config.py:147-218`; `_immersion_gate` at `scripts/build/linear_pipeline.py:4582-4624`; `_long_ukrainian_sentences()` at `:4640`. Anchor episodes Ep 1/15/30/45.

Round 2 Gemini: `[AGREE]` — minimum-viable measurement (5 anchors instead of full corpus), markdown-heuristic gate implementation.

**Convergence**: replace global % with structural gates; tab-aware; markdown-heuristic detection; advisory pct stays until replay proves new gates.

## What the user reframed mid-session (post-convergence)

After both agents converged, user pushed deeper: **"pedagogy is more important than immersion. I feel that in the beginning of a1 immersion level is misleading. We need to figure out how to do this."** This wasn't just "fix the gate" — it was "the framing of 'gate the immersion ratio' is wrong; gate the pedagogy."

Followed by:
- **Anchor-sampling correction**: agents' anchor episode picks were wrong because they didn't verify ULP review-episode locations; ALL 6 seasons should be checked, anchors should be REGULAR lessons not reviews/specials/interviews.
- **Audio correction**: "we have lots of YT content, audio in first 1-3 for letter learning, reference videos of other creators for the rest." My "no audio" claim was wrong.
- **Format correction**: "the old content is different, our new version has different structure different design, workbook, in-lesson activities, etc." The deployed A1 I'd been reading is OLD format (single-page MD); the new format is 4-tab structured.
- **SSOT correction**: "config.py is the single source of truth for quality gates" — Decision Card describes gate logic, numbers live in code.
- **Bakeoff reframe**: "or we could give diff tabs to diff agents whichever is stronger in that?" → Card 2.

Each correction caught me proceeding on ungrounded assumptions. Encoded patterns in the autopsy section (below).

## Empirical work this session

### ULP 6-season scan (all on disk after copying S5/S6 from `~/Downloads/`)

| Season | Episodes | Format pattern | Typical episode for anchor |
|---|---|---|---|
| S1 | 1-40 | EN-titled didactic lesson; reviews at 10/20/30; pronunciation trainer 5/15/25/35; interviews 36-39; Q&A 40 | Ep 12 (Ordering food) |
| S2 | 41-80 | UK-titled didactic lesson; reviews every ~5; Курс з історії 71-79; Anna's metalanguage flips to UK | Ep 47 (Genitive food festivals) |
| S3 | 81-120 | UK didactic + Голосове повідомлення recaps every 5; Khrystyna+Lesia recurring | Ep 88 (Higher education) |
| S4 | 121-160 | Topical deep dive; less didactic, more cultural content; line-by-line translation drops to sidebar glosses | Ep 138 (Surviving winter) |
| S5 | 161-200 | Interview-heavy + topical monologues; lesson format dissolves | Ep 180 (Про борщ) |
| S6 | 201-240 | Thematic content (poetry, war, history); near-native expectation | Ep 213 (Милозвучність) |

**Two hard structural boundaries:**
1. **S1→S2**: metalanguage flip. Anna stops speaking English to the learner; UK becomes teacher voice.
2. **S3→S4**: translation-density flip. Parallel-column line-by-line translation dies; sidebar vocabulary glosses survive only.

**S4 Ep 138 contained the gold:** Anna explicitly self-labels the CEFR mapping in Ukrainian — "Перший і другий сезон — для початківців, третій сезон — для середнього рівня, і зараз триває четвертий сезон — для високого середнього чи високого рівня." Authoritative season→CEFR map.

### Deployed A1 modules read (5)

1. `sounds-letters-and-hello` (m1, foundational) — dense (3-4 topics in one module), Bolshakova-cited, English-dominant phonetics theory + UK examples
2. `hey-friend` (vocative case) — bilingual headers, pure-UK dialogues with parenthetical gloss, EN grammar prose
3. `who-am-i` (introductions) — 3 dialogues, бути omission, pronouns, professions, з-construction. 160 lines.
4. `when-and-where` (m45 complex sentences) — subordinate conjunctions що/де/коли + 3 verbs. 193 lines.
5. `checkpoint-actions` (consolidation format) — self-check + reading + grammar table + connected dialogue

All 5 follow the same structural pattern: bilingual headers + pure-UK dialogues with parenthetical gloss + EN-dominant teaching prose + bilingual vocab tables + activity injection markers + cross-module references + decolonized framing + Ukrainian textbook citations + MDX callouts. The failure modes the immersion gate was designed to catch do NOT appear in deployed content.

**Implication:** if deployed A1 passes new gates on replay, the V7 rebuild strategy for A1 needs reframing. Likely candidates:
- (a) Keep deployed mostly as-is; surgical fixes (density splits, audio expansion)
- (b) Use V7 only for modules that don't exist yet (A2 has 0 deployed; A1 has only my-morning in new format)
- (c) Reframe V7 as "fill-in" tool

Decision deferred pending Phase B replay results.

## What's in flight / blocked

- **PR #1909 (writer-prompt-tune)** — all blocking CI green; HELD pending Card 1 decision. 3 of 4 prompt edits survive any redesign (citation parity, section budget, long-sentence rule). "Aim for middle of band" line dies under structural gate model. Either trim-then-merge OR revert when redesign lands.
- **PR #1915 (Track B research artifacts)** — VERDICT=YELLOW. Anchor preservation contract works (74/74 byte-identical); immersion failed (32.03% vs cap 24%). Was partly measurement artifact of misshapen gate. HELD; #1914 (Codex follow-up "tune Pass-2 scaffold") needs reframing under new gate model.
- **#1914 (Codex follow-up)** — premise predicated on wrong gate. Needs explicit re-scope or close after gate redesign lands.

## Carry-over queue (priority-ordered)

| # | Item | State |
|---|---|---|
| 1 | **Decide Card 1: immersion-gate-tab-aware-structural** | 📋 P0 — PROPOSED, cheap proof-of-concept defined |
| 2 | **Decide Card 2: writer-split-by-tab** | 📋 P0 — PROPOSED, ~1 hour proof-of-concept defined |
| 3 | If Card 1 accepted: Phase A dispatch (Codex, ~half-day, gate code split + config schema extension) | 📋 |
| 4 | If Card 1 accepted: Phase B replay (Codex, ~half-day, NO LLM cost, empirical calibration against deployed A1) | 📋 — answers "is V7 rebuild needed for A1" empirically |
| 5 | If Card 2 accepted: cheap proof-of-concept on a1/my-morning (~4 LLM calls, sequential Path A) | 📋 |
| 6 | After both Phase B + Card 2 PoC: revisit A1 strategy (keep deployed / surgical fix / V7 fill-in only) | 📋 — major strategic decision |
| 7 | PR #1909 disposition (trim-then-merge OR revert) | 📋 — depends on Card 1 |
| 8 | PR #1915 + #1914 disposition (close, reframe, OR re-test under new gate model) | 📋 — depends on Card 1 |
| 9 | Density / pacing improvement on deployed A1 (e.g. split `sounds-letters-and-hello` into 3-4 narrower modules) | 📋 — surfaced this session; deferred |
| 10 | **#1908** Layered-harness audit (push advisory rules to hooks) — EPIC #1865 structural | 📋 |
| 11 | **#1905** Pipeline replay-mode regression suite — EPIC #1865 structural | 📋 |
| 12 | **#1896** Secret-leak prevention follow-ups (autopsy backlog) | 📋 |
| 13 | Pending Decision Cards from prior sessions (`2026-05-12-autonomous-codex-dispatch-narrow-class.md`, `2026-05-09-decision-graph-view.md`, `2026-05-06-multi-ui-channel-participation.md`) | 📋 |

## Pending Decision Cards

| File | Status |
|---|---|
| `2026-05-13-immersion-gate-tab-aware-structural.md` | PROPOSED (this session) |
| `2026-05-13-writer-split-by-tab.md` | PROPOSED (this session) |
| `2026-05-12-autonomous-codex-dispatch-narrow-class.md` | PROPOSED |
| `2026-05-09-decision-graph-view.md` | PROPOSED |
| `2026-05-06-multi-ui-channel-participation.md` | PROPOSED |

## Autopsy — pattern of ungrounded claims this session

User caught 4 ungrounded-claim instances within ~3 hours of conversation:

1. "No audio in deployed A1" → wrong; YouTubeVideo component + Anna's video refs exist
2. "Anchor episodes Ep 1/10/20/30/40 are representative" → wrong; every 10th in S1 is Review
3. "Deployed A1 is the target V7 is rebuilding" → wrong; new format is 4-tab structured, different from old single-page deployed
4. "Gate numbers can live in spec doc" → wrong; SSOT is `config.py`

Each was a #M-4 violation. Each was caught by the user, not by me. Encoded pattern:

> **Before forwarding ANY agent-proposed evidence or sample selection**, run the deterministic verification: open the file, check the structure, confirm the assumption. The agents (and I) don't get a free pass on grounding because they're "smart" — they confabulate as readily as inline-Claude does.

Reinforces MEMORY #M-4 (Deterministic Over Hallucination) in a new context: **multi-agent convergence is NOT a substitute for tool-backed verification**. Both agents agreeing on Ep 1/10/20/30/40 doesn't make Ep 10/20/30 not-reviews. Convergence is high-confidence FRAMING; the underlying evidence still needs deterministic verification.

## Handoff economics

MEMORY #2 thresholds (revised 2026-05-13 midday): 500K+ = handoff zone. This session is being handed off because the user requested it after task 5 completed — natural topic break + 2 Decision Cards filed + cross-session reference needed for the cards. Not budget-triggered.

## Predecessor brief

`docs/session-state/2026-05-13-afternoon-bakeoff-and-twopass-brief.md` — sets up the two-pass workflow discussion, fair-env bakeoff verdict, MEMORY #2 threshold change. This evening's session opened by firing that two-pass discussion (which converged at round 2 on staged option C), then pivoted toward immersion-gate reframe after user pushback on the immersion framing, then again to writer-split after user proposed per-tab agent specialization.

---

*Format spec: `claude_extensions/rules/workflow.md` § "Two-tier handoffs". Companion HTML: `2026-05-13-evening-immersion-reframe-and-writer-split.html`. Decision Cards committed at `55823800ce`. Opening action for next session: read both Decision Cards in `docs/decisions/pending/2026-05-13-*.md` and surface user signoff path.*
