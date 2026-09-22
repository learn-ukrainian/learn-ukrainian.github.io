# Fresh lesson-based build — the build program (hand-over from design to the build orchestrator)

> Sub-epic #8397 (parent #7994). Written by the curriculum-upgrade design seat, 2026-09-22, as the
> hand-over of the design phase. Status: **design complete for A1 build start; two items need the
> operator (§6).** Everything below is a pointer to a frozen brief or an accepted document; this file
> adds the order, the dependencies, the routing constraints and the acceptance per package. It does
> not restate the contracts. Read the requirements, the plan schema and the two contracts first:
> [`fresh-build-requirements.md`](fresh-build-requirements.md), [`fresh-build-plan-schema.md`](fresh-build-plan-schema.md),
> the writer contract (#8431, body r3), the review contract (#8430, body r4).

## 1. What the build orchestrator inherits

| Layer | Artifact | State on `main` (verify with the tool) |
| --- | --- | --- |
| Requirements R-01…R-35 | `docs/epics/fresh-build-requirements.md` | accepted by the operator 2026-09-21 |
| Plan and evidence schema | `docs/epics/fresh-build-plan-schema.md` | revision 8 accepted; **revision 9** (this hand-over's docs PR) adds the fields the contracts need (§2 of this file) |
| Arcs A1, A2, B1, B2 | `docs/epics/fresh-build-{a1,a2,b1,b2}-arc.md` | all four accepted by the operator 2026-09-21; only A1 has its generated `_arc.yaml` |
| Writer contract + style card | issue #8431 body, r3 | two independent seats (AGY r1, Codex r2) folded in; **operator acceptance pending** |
| Review contracts (plan + lesson) | issue #8430 body, r4 | two independent seats (AGY r2, Codex r3) folded in; **operator acceptance pending** |
| Word-store primitives | `scripts/curriculum/evidence/{codes,sources,tags,lock,registry}.py` | merged (PR #8450, #8413 A1 part 1) |
| Arc loader + generator (a1) | `scripts/curriculum/arc/` | merged (#8411) |

Every other package is a **brief**: a frozen text on the issue it belongs to, with its sha256 in the comment that posts it, reviewed by at least one independent seat with tools before it was frozen. The orchestrator dispatches briefs; it does not redesign them. When a brief is wrong about the repository, the fix is a revision of the brief (a comment with a new sha256), not a silent deviation by the worker.

## 2. Work packages in dependency order

Legend — **lane**: `language` = a sanctioned language lane only (Claude, Codex, Gemini/AGY, Grok — LANGUAGE-LANES rule), `any` = any lane the live routing allows; **CF** = the cross-family review of record at the exact head; **gate** = the deterministic proof the PR must show.

| WP | Package | Brief (frozen text) | Depends on | Lane | Acceptance |
| --- | --- | --- | --- | --- | --- |
| 01 | Plan v2 schema + single-plan `plan-validate` (#8412 Brief A) | #8412 comment 5766341201 (Brief A) + the revision-8 change (comment 5769009637) + the revision-9 change (comment 5773059129) | — | any | fixtures per rule; CLI in a clean env |
| 02 | Cross-plan rules, grammar registry, scope sidecar, `--strict`, CI (#8412 Brief B) | #8412 comment 5766341454 | 01 | any | the `--all --strict` job green on a fixture level |
| 03 | Word store builder + `words-verify` (#8413 A1 part 2) | #8413 Brief A1 r3 (comment 5769198671, sha256 `8ea74268a01dd3d7`); dispatch header = #8413 comment 5773001736 and §4 of this file | — (part 1 merged) | language | dry run on five real A1 lemmas; determinism test |
| 04 | Module evidence pack + `pack-verify` (#8413 A2) | #8413 comment 5769383696 (r2, sha256 `5397f67b91acc40f`) | 03 | language | a quote whose chunk id moved passes; a changed quote fails |
| 05 | Arc generator modes a2/b1/b2 + band mapping (#8424) | #8424 comment 5773049943 (r3, sha256 `dcfb663fd4b2ce8c`) | plan schema r9 (the B1/B2 §7 tables) | any | `--check` green for four levels; `load_arc("a2")[0].band_key == "a2-bridge"` |
| 06 | Standard mapping corrections; compliance gate and plan-review treat the Standard as a floor (#8404) | #8404 body (the issue is the spec) | — | language | the AC list on the issue |
| 07 | Learner state at lesson grain, inventory gate, lesson immersion band (#8414) | #8414 comment 5773049472 (r3, sha256 `ccd38bb49cf4132d`) | 01, 03, 05, 08, plan schema r9 | language | config pin test; seven-knee band test |
| 08 | Token resolver: classification, narrowing, constrained questions, receipts (#8413 Brief B) | #8413 comment 5773128486 (r2, sha256 `dbd14390877cf7de`) | 03, 07 `planned` | language | the ULP lesson 10 replay numbers reproduced |
| 09 | Per-lesson evidence lock (#8413 Brief C) | #8413 comment 5773049727 (r3, sha256 `5e1c724051f34592`) | 01, 03, 04 | language | `--diff` names exactly the citing lessons |
| 10 | Base-layer request file `evidence/a1/_base.request.yaml` | #8414 r3 (comment 5773049472) §"The base layer" — the rule; the lane writes the file from it | 03 | language (writes planning data, reviewed cross-family like a plan) | built by `build-words`; every line has its closed-class note |
| 11 | Engine E1: draft schema, level-schema additions (`explanation`, `error_ref`), style cards | #8397 comment 5773128681 (E1–E3, r2, sha256 `1f8b3d84b0a527bd`) | plan schema r9 | any (E1 schemas); language (the cards) | a valid draft per level validates; cards' exemplars are sourced |
| 12 | Engine E2: prompt, rendered-prompt check, preflight, immersion payload, writer call | same brief | 11, 07 | language | preflight gap report; rendered prompt with hash |
| 13 | Engine E3: assembler, expanded document, check runner, state files, module build | same brief | 12, 08, 09 | language | check runner on a fixture module; `verify_shippable --astro-build` |
| 14 | Review R1: review schema, active validator, receipt ledger | #8430 comment 5773128901 (R1–R3, r2, sha256 `48d4e5762638f5fa`) | #8456 harness answer | any (ledger = harness work) | a fabricated receipt is rejected |
| 15 | Review R2: reviewer prompts, module digest, layer assignment, budgets, settle task | same brief | 14, 07, 13 | language | fix-loop report with a terminal transition |
| 16 | Review R3: seeded-defect planting, adjudication, scoring, runner | same brief | 15 | language (third-family planter and adjudicator) | a seed is deterministic-green or a gate test; report with intervals |
| 17 | Per-lesson practice deck generator + `practice` gate (#8407) | #8407 body | 03, 13 | any | deck consumed by the existing components |
| 18 | Atlas on-demand entry + `atlas-link` gate (#8409) — **Atlas lane** | #8409 body | #8400 identity | Atlas lane | the AC list on the issue |
| 19 | Practice Hub module feed (#8408) — **Atlas lane** | #8408 body | 17 | Atlas lane | the AC list on the issue |
| 20 | `/a1/` landing, module pages, lesson routes, archive link | #8397 comment 5773050121 (r3, sha256 `40923a7c7fef8caf`) | 13's frontmatter keys | any | `--check` green; Astro build with 0 and 1 built |
| 21 | Publication-right field on the source registry + `pack-verify` check (writer contract §1a) — **corpus lane** | writer contract #8431 r3 §1a (the requirement); a short brief is the corpus lane's to write from it | 04 | corpus lane | a `quote` from a source without the field is a gap |
| 22 | Position 1 pilot: pack, word store, plan, plan review, measurement, canary, lessons, recap, review (#8425) | §5 of this file (the runbook) | 01–16, 20, 21 | driver + language lanes | `/a1/sounds-letters-and-hello/` built, gates green, module verdict APPROVE, settle items counted |

Not packages — decisions and follow-ups: the R-19 activity redesign (§6.1), the `content-review` skill replacement (§6.2), Q10 "one wiki packet per module rendered from the pack" (R-25: a human-readable page may be rendered from the pack; not an input — a small brief for after the pilot), the grammar checker of writer contract §7 row 10 (an implementing brief after real drafts exist), lesson-level structural minimums (calibrated from the pilot, #8414), the arc's structured grammar/vocabulary columns (#8412 comment of 2026-09-21: option (b), after the first two or three plans).

## 3. Rules the orchestrator drives by (binding, from the design)
1. **Nothing typed.** Every Ukrainian string in evidence, a store, a lesson or a page is a tool copy or the writer's resolved text (R-35, #8413 rule "the builder copies; it never writes", #8431 principle 2). A worker that types a form, a stress or a gloss has broken the design; the fix is at the layer that let it happen.
2. **Language lanes only** for anything that judges or produces Ukrainian — including the resolver, the inventory gate, the engine's E2/E3, the reviewer prompts, the settle task, the seed planter and the base-layer request file. Never `--check-budget` substitution for language work (#8449). Reviewer seats must be dispatched in a mode where the `sources` MCP works (#8456).
3. **Cross-family review at the exact head before any PR**, then CI Gate green on that head, then enqueue; never `--auto`, never a draft PR during the fix loop; `merge_closeout <N> --apply` after MERGED (drive-epic §7, §7a).
4. **Briefs are frozen texts.** A worker quotes back every choice the brief left open; the orchestrator settles it by a brief revision (new sha256), not in chat. A material change to a contract (#8430, #8431, the plan schema) is a design change: it goes back to the design seat or the operator, with two independent seats, before implementation.
5. **Operator decisions are constants with dates**: the review measurement numbers (22 per dimension, 30 clean, 1 in 30, 1 in 10), the two-regeneration and 2N budgets, "an unsupported claim holds the module", "any form of an allowed lemma", the immersion numbers of R-30. They live in config with the date beside them; nobody re-tunes them in a PR.
6. **Pages deploys only on the operator's present-tense GO** (drive-epic §7-rollout). "Built and green in a worktree" is not done; the learner URL on `/a1/` after his GO is.
7. **Module acceptance gate during the pilot phase** (carried over from #8236, the operator's own method): the next module does not start until he has accepted the current one — two read-only reads of the whole module by two families, then his acceptance. This binds for the pilot and the first few modules; the review tooling (WP 14–16) is what makes it cheaper later.

## 4. Dispatch header for WP 03 (word store part 2)
The frozen prompt of the previous session (part 1 merged as PR #8450, `a33c5abb1c`) is Brief A1 r3 with this header: *Part 1 is on `main`; implement `words.py`, `verify.py`, the CLI and the remaining tests; monosyllables are gated before the oracle; CEFR exact match only; branch `<lane>/impl-8413a1-part2` by that exact name (the brief's own "Commit and push" names part 1's branch — this header overrides it); push `HEAD:refs/heads/<lane>/impl-8413a1-part2` explicitly if the remote is behind; no PR.* Routing note from the design seat's last attempt (2026-09-22): Codex weekly was at 13 %; Claude `claude-fable-5-1 --mode danger --worktree` was the cooler eligible seat; review of record then AGY or Codex. Reads: `fleet.usage show` before choosing.

## 5. Position 1 pilot — the runbook (WP 22, issue #8425)
In this order; each step's artifact is checked by the tool named before the next starts.
1. **Base layer and word store**: WP 10's request file → `build-words a1 --request …` → `words-verify a1` green; count the `pending` forms and the `unresolved` records; the operator's expectation is that ULIF-sourced stress is absent today (`homonym_checked = 0` everywhere) and the trie covers most A1 forms — quote the numbers.
2. **Evidence pack** for `sounds-letters-and-hello`: request from the arc data (`load_arc('a1')[0].letters`, the primer chunk ids listed on #8425) → `pack-verify` green → **provisional lock** (review contract, Contract 1 timing).
3. **Module plan** in the v2 format (about five lessons, the last a recap), written by a language lane from the pack and the arc, with the operator's decisions record; `plan-validate --strict` green (`--allow-missing-prior` is not needed at position 1).
4. **Plan review** (Contract 1) by a cross-family language seat with the full manifest; on APPROVE the pack lock is promoted into `evidence_ref`.
5. **Reviewer measurement** (WP 16): the first seeded set for the lesson reviewer seat — from *built* lessons, so this step interleaves with 7: the canary lesson and the contract fixtures are the first seed material; the operator sets the threshold after the first report; the held-out confirmation set is frozen before that.
6. **Canary**: lesson 1 written once (#8431 §8.3); passes checks 0–11 with at most one regeneration; reviewed under Contract 2 by a seat that has passed the measurement; on a second failure of the same check, stop and fix the layer.
7. **Lessons 2…N−1**, then the **recap** from the built lessons; module digest per lesson; reviews per lesson; the fix loop with its budgets; settle items counted and reported per module (the operator expects near zero).
8. **Module verdict** computed; two read-only reads (rule 7 of §3); the operator accepts.
9. **Landing** (WP 20) shows the module as `reviewed`; Pages only on his GO.
Calibration outputs of the pilot, recorded on #8425: `word_target` per lesson, lesson-level activity minimums, the share of tokens that needed a constrained question, the untaught-forms share per lesson, settle-item count.

## 6. What needs the operator (present-tense go)
1. **R-19 activity redesign** — the decision card is #8397 comment 5773129143 (r2, sha256 `39e3f785ebab4b8c`), after the cross-family discussion (design seat's r1 proposal; AGY's tooled critique, comment 5773123014). **Recommended: constrain and specialise `fill-in` and `true-false` in place** (`fill-in` with required 2–4 store-generated form options and an A1 orthography mode, no free typing inline at A1–A2; `true-false` only as a post-text check with a required, text-citing explanation; explanation register by level). Rejected: retire-and-replace with a new `choose-the-form` type. The position 1 pilot can run under the current allowlist; A1 plans at volume should not be written before this is decided.
2. **Replacing the `content-review` skill** for fresh-build lessons (#8430 deliverable (h)) — a change to the agent system.
3. **Acceptance of the two contracts** (#8430 r4, #8431 r3) as written, or corrections. The docs PR of this hand-over lands them in the plan-schema document marked "operator acceptance pending" so the build orchestrator has one place to read; his acceptance is a one-line status change.

## 7. Residual the design seat leaves, plainly
- No package has been implemented beyond #8413 A1 part 1; the numbers in the contracts that come from measurement (question rate, settle-item counts, reviewer recall) are unknown until the pilot.
- The grammar checker (writer contract §7 row 10) is undecided by design: it is decided from real drafts.
- The arc data carries structured inventory for letters only; grammar and vocabulary scope in rule 5 of the plan schema stay `not_checked` until the arc gains columns (after the first plans).
- Harness gap #8456 (Codex read-only cannot call the MCP) blocks Codex as a review seat until answered.
