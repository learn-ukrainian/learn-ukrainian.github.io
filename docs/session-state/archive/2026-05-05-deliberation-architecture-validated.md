# Session Handoff — 2026-05-05 (deliberation architecture validated + hardened)

> **Predecessor:** `2026-05-04-evening-multi-dispatch.md`
> **Successor scope:** Pick up from a load-bearing architectural shift. The pre-review multi-agent deliberation pattern (user's idea, originally framed as "have agents discuss before sending to expensive review") was empirically validated this session. ADR-008's per-gate correction-loop architecture is now a candidate for supersession by deliberation-as-pre-review. Several follow-on tasks queued.
> **Mode:** User online, executing aggressively, multiple sharp corrections on framing and scope.

---

## TL;DR — what shipped

8 commits to main. In dependency order:

1. `0ac2f3b827` — `_search_blog_dbs` UnboundLocalError regression fix (pre-existing on main, was blocking #1675 + #1678 CI)
2. `1be0c680a2` — Claude bridge adapter: prompt-positional after `--` separator (Commander.js end-of-options marker — unblocked `ab discuss` for prompts starting with `---`)
3. `dc77fea1c1` — new linguistic rule "Ukrainian is its own reference" + terminology hygiene (never "древнерусский", always "Old East Slavic / давньоруська")
4. `5f951d1f4b` — first attempt at Антоненко-Давидович placement (later corrected — overcorrected to "demoted")
5. `457f4b84e8` — reframed Антоненко-Давидович correctly as **canonical authority for Russianism work**, with both failure modes named (misuse as descriptive grammar / failure to use where Russianism work is needed)
6. `8ee92aa791` — promoted linguistic principles into `shared/context.md` (auto-prepends to every channel post), deduped from `content/context.md`
7. `872d8376b0` — deliberation protocol fix: round-1 cannot short-circuit + per-round directive split (round 1 = independent first-take, round 2+ = cross-agent comparison)
8. `cf8a5a7769` — Gemini × Антоненко-Давидович × собака hallucination autopsy in `docs/bug-autopsies/agent-hallucination.md`

Plus 3 PRs merged (`#1674`/`#1675`/`#1678` — VESUM `arch` tag, PyMorphy3, Грінченко rename) with conflict resolution in worktrees, parent issues `#1669/#1668/#1658` auto-closed, duplicate PR `#1681` closed.

---

## The architectural finding (load-bearing for the rest of the project)

**Multi-agent pre-review deliberation works as a quality mechanism — but only with two specific guards in place:**

1. **Channel-context-pinned linguistic rules.** `ab discuss --bare` agents do not auto-load `.claude/rules/`. The rules MUST be in the channel's pinned `context.md` (which the bridge auto-prepends to every post). Updates to `claude_extensions/rules/` reach interactive Claude Code sessions; updates to `docs/agent-channels/<channel>/context.md` reach `ab discuss` agents. Both paths are needed in parallel.

2. **Round 1 cannot short-circuit on `[AGREE]`.** Round 1 is a parallel fan-out — each agent answers the original question independently, having NOT seen any other agent's reply. `[AGREE]` in round 1 means "I'm done with my answer," not "I agree with the others." Pre-fix, the protocol short-circuited at round 1 unconditionally; cross-agent disagreement never surfaced. Post-fix (`872d8376b0`), round 2 is forced — agents read each other's first takes, can name fabrications, and `[AGREE]` becomes meaningful.

**Empirical proof (both runs in `content` channel):**

- **Vocative case deliberation** — pre-rule-pin (`c8f14a7c7a09`): both Claude + Gemini drifted to "Ukrainian preserved X / Russian innovated Y" framing. Post-rule-pin (`03fdad78b97d`): both caught the drift in round 1, signed `[DISAGREE]`, converged in round 2 with Ukrainian-internal framing + corrected `Антоненко-Давидович` placement.

- **Собака gender deliberation** — pre-protocol-fix (`482884ca054e`): all three agents `[AGREE]`'d in round 1, short-circuited; **Gemini hallucinated a verbatim Антоненко-Давидович citation that AD has no entry for**. Would have shipped. Post-protocol-fix (`7c6e401053bb`): same hallucination from Gemini in round 1, but round 2 forced — Claude + Codex independently caught it via MCP verification, refused `[AGREE]` until retraction was on record. Gemini conceded explicitly.

**Implication for ADR-008:** ADR-008 was about adding more correction cycles after the expensive strict reviewer fires. Pre-review deliberation reduces the number of times the expensive reviewer fires REVISE in the first place. If the deliberation pattern proves robust at scale, ADR-008's per-gate correction loop becomes a thin fallback for residual cases instead of the main correction story. ADR-008 still PROPOSED, awaits user signoff — could now be deprecated or substantially scoped down.

---

## What's actively in-progress (DO NOT TOUCH)

- **Issue #1683 — citation-provenance check before channel-message commit.** Filed this session, ACs documented, regression-test fixtures named (the verbatim Gemini fake quote from threads `482884ca054e` and `7c6e401053bb`). Not yet implemented. This is the next high-impact engineering task — the empirical case is strong.
- **Issue #1682 — `test_delegate.py::test_dispatch_creates_worktree_and_records_it` polluting from real `.worktrees/` on disk.** Filed, low priority.
- **Codex weekly cap cleared this session** (`gpt-5.5 — has headroom ✓`). Codex available for dispatches. The previous handoff queued `#1665 Holovashchuk «Словник-довідник з українського літературного слововживання» (2004) ingest` for Codex; not yet dispatched (deliberately held until the deliberation architecture was validated, which it now is).

## Open architectural items inherited from predecessor

- **ADR-008 still PROPOSED**, awaits user signoff — but as noted above, may be substantially scoped down or deprecated in favor of the deliberation-as-pre-review architecture validated this session. Decision: ask user whether ADR-008 should be (a) accepted as a fallback layer behind deliberation, (b) re-drafted as a thinner residual-correction policy, (c) deprecated entirely. Probably (b).

---

## Tier status (carried forward, with this session's deltas)

### Tier A — Critical infrastructure

| # | What | Status |
|---|---|---|
| #1631 | Wiki migration | DONE (PR #1635, merged 2026-05-02) |
| #1632 | ADR-008 implementation | **Re-evaluate** — likely superseded or scoped down by deliberation architecture |

### Tier B — Verification tools + prompt scaffolding

| # | What | Status |
|---|---|---|
| #1669 | VESUM `arch` tag | **DONE** (PR #1674 merged this session) |
| #1668 | PyMorphy3 wrapper | **DONE** (PR #1675 merged this session) |
| #1658 | Rename `search_etymology` | **DONE** (PR #1678 merged this session) |
| #1660 | Tool descriptions | DONE (commit 72135fa066) |
| #1673 | CoT scaffolding writer + reviewer | DONE (commit 3e08b3c77e) |

### Tier C — Content sources + license

| Item | Status |
|---|---|
| `query_slovnyk_me` multi-dictionary tool | DONE (commit 43ad83f269) |
| `query_sum20` repointed to slovnyk.me | DONE (commit 43ad83f269) |
| #1665 Holovashchuk ingest | **Codex-ready** — dispatch when bandwidth permits |
| #1663 Antonenko full ingest re-dispatch | Open, low priority; Антоненко already 279/600+ indexed and the gap was demonstrated this session (zero hits on собака despite expected coverage) |
| #1662 ЕСУМ vols 2-6 | Open, mechanical work for Codex |

### Tier D — Prompts use everything above

| # | What | Status |
|---|---|---|
| #1661 | V7 prompt diff for Tier-1 verification discipline | NOT YET — but partially overlapped by the channel-context rule pinning shipped this session |

### Tier E — Run A1/20

Still parked. Writer choice still undecided. The deliberation architecture validated here is orthogonal to A1/20 — A1/20 is about per-module build, deliberation is about pre-review consensus on architectural and linguistic decisions.

---

## New rules / docs landed this session

- **`claude_extensions/rules/ukrainian-linguistics.md`** — major rewrite, now leads with "Ukrainian is its own reference" + Antonenko-Davydovych canonical-for-Russianism placement + terminology hygiene. Deployed to `.claude/`, `.agent/`, `.gemini/` via `npm run claude:deploy`.

- **`docs/agent-channels/shared/context.md`** — promoted the linguistic principles to the auto-included channel context. The load-bearing change for `ab discuss` agent compliance.

- **`docs/agent-channels/content/context.md`** — deduped to content-channel-specific items only (textbook grounding, adult register, cultural authenticity, plan immutability), points at shared for the project-wide linguistic rules.

- **`docs/bug-autopsies/agent-hallucination.md`** — new category file in the autopsy index. First entry: Gemini × АД × собака. Pattern documented for future agents to recognize and refuse.

- **`scripts/agent_runtime/adapters/claude.py`** — Claude bridge: prompt positional now placed after `--` separator. Unblocks any prompt starting with `--` characters.

- **`scripts/ai_agent_bridge/_channels_cli.py`** — round-1 short-circuit blocked, per-round directive split. Inline comments name the empirical incident for future readers.

---

## Cold-start protocol for next session

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
source ./.envrc

# 1. Bootstrap from Monitor API (cached, condensed)
curl -s http://localhost:8765/api/state/manifest
curl -s http://localhost:8765/api/orient
curl -s 'http://localhost:8765/api/comms/inbox?agent=claude'

# 2. Verify clean main
git fetch origin main && git status -s && git log --oneline -5

# 3. Read THIS handoff + the predecessor:
#    docs/session-state/2026-05-05-deliberation-architecture-validated.md
#    docs/session-state/2026-05-04-evening-multi-dispatch.md

# 4. If ADR-008 status is the open question: surface to user.
#    Likely re-draft as thin residual-correction policy behind deliberation.
```

---

## Ranked next-session priorities

1. **Implement #1683 (citation-provenance check).** Highest leverage — every future deliberation gets the safety net automatically. Empirical case strong, ACs already documented on the issue.

2. **Surface ADR-008 supersession question to user.** Given the deliberation architecture is empirically validated, ADR-008's full per-gate correction loop is likely overkill. Ask whether to re-draft as residual-only fallback.

3. **Dispatch Codex on #1665 Holovashchuk ingest.** Mechanical work, fits Codex's strengths, Codex's weekly cap is now clear.

4. **Pin known-hallucination list** to `shared/context.md` (cross-reference `docs/bug-autopsies/agent-hallucination.md`) so the собака fabrication can't drift back even from training-data prior.

5. **Audit reviewer prompts** — feminine собака must NOT be flagged as Russianism. Adversarial-reviewer prompts likely need a "false-positive Russianism list" injection.

6. **Consider a HIST/OES seminar deliberation pilot.** The vocative-case transcript from this session is publishable curriculum content with light editing. Run a few more deliberations on seminar-tier topics; if the transcripts converge on usable pedagogical material, that's a parallel content-production stream we didn't have before.

---

## Workflow lessons captured this session

1. **Action bias is non-negotiable.** User repeatedly corrected me for offering "a/b veto windows" instead of executing. Pattern: pick the right thing, do it, report. Memory rules #0A, #0H, #0I all came up empirically again.

2. **"Place X to its place" ≠ "demote X."** First Антоненко-Давидович edit (5f951d1f4b) read as diminishment; user corrected, second edit (457f4b84e8) reframed as "canonical for Russianism work specifically." Lesson: when user says "place to its place," ask what role it should be PROMINENT IN, not what role it should be REMOVED FROM.

3. **Russian-comparison framing is the default reflex even while criticizing Russian.** Surfaced repeatedly: I produced "Ukrainian preserved X / Russian innovated Y" framings, then "compare to Polish/Czech/Slovenian" overcorrection, then finally landed on "Ukrainian is its own reference, no comparison frame." This is a stable training-data-prior issue, not a one-time slip. The rule must be re-asserted in every linguistic post (and now is, via shared/context.md).

4. **Single-completion-notification (Bash run_in_background) vs event-stream (Monitor).** I defaulted to Bash run_in_background for `ab discuss` runs three times this session. For multi-round deliberations the round-transition events ARE meaningful — Monitor is the right tool. Memory rule #0B exists for this reason. Self-correction committed to next session.

5. **Cross-agent disagreement is the value, not consensus.** Both deliberations this session that produced real signal did so via `[DISAGREE]` and surfaced fabrications. Deliberations that all-`[AGREE]`'d in round 1 produced false consensus and would have shipped bad rules. The protocol fix (`872d8376b0`) makes the disagreement-surfacing path the default.

---

## Cross-thread notes (still active)

- **Memory rule #0I** (don't stack micro-dilemmas) validated repeatedly this session.
- **Memory rule #0H** (Claude merges PRs) — merged 3 PRs without asking.
- **Memory rule #0B** (Monitor for event streams) — flagged by user; commit to applying next session.
- **slovnyk.me license posture** unchanged, per-query fair use.
- **Codex back online**, headroom confirmed, ready for dispatches.
- **Pyenv-rehash 60s lock** — fixed earlier, no recurrence.
- **`~/.bash_secrets`** still where `GITHUB_TOKEN` lives; source manually before `gh` calls.
