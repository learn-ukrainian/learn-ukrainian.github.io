# DECISION REQUIRED — Should we split the V7 writer phase into per-tab specialized agents?

**Status:** PROPOSED (orchestrator-surfaced, awaiting user signoff)
**Surfaced:** 2026-05-13 evening, after the user proposed it in conversation: *"or we could give diff tabs to diff agents whichever is stronger in that?"*
**Source:** User-proposed direction; consistent with existing project patterns (wiki = always Gemini; reviewer = always non-writer; 3:3:3 dispatch by fit not quota)
**Scope:** V7 pipeline writer phase (`scripts/build/v7_build.py` + `linear_pipeline.py` writer dispatch). **Does NOT touch:** gate logic (separate proposal `2026-05-13-immersion-gate-tab-aware-structural.md`), reviewer phase, plan schema, MDX assembler

---

## What's being proposed

Replace V7's single-writer-produces-all-4-artifacts pattern with **per-tab specialized writers**, each agent picked by content-shape fit:

| Tab | Source artifact | Proposed writer | Rationale |
|---|---|---|---|
| Tab 1 — **Урок** (narrative + theory + dialogues) | `module.md` | **Claude** | Narrative voice, pedagogical care, decolonized framing, MCP verification calls. Today's bakeoff already confirmed Claude wins on content merit; this proposal scopes that win to its actual evidence (Tab 1 content) |
| Tab 2 — **Словник** (typed vocab YAML) | `vocabulary.yaml` | **Codex** | Strict YAML schema; VESUM-verified lemmas; per-entry structure; no creative bleed. Codex's mechanical schema correctness wins for structured data |
| Tab 3 — **Вправи** (typed activity YAML) | `activities.yaml` | **Codex** | 19 typed activity components, each with specific schema and per-level allowlist from `ACTIVITY_CONFIGS`. Mechanical generation against strict types matches Codex's strength |
| Tab 4 — **Ресурси** (citations + media YAML) | `resources.yaml` | **Gemini** | Already the wiki writer; comfortable with source attribution + URL handling; unmetered sub for routine work. Codex is the backup if Gemini quality is insufficient |

This is consistent with existing project patterns: the **wiki writer is always Gemini** (MEMORY policy, codified in `scripts/wiki/compile.py`); the **reviewer is always non-writer** (no self-review per `SELF_REVIEW_DETECTED` audit gate); the **3:3:3 dispatch split** assumes per-task fit, not one-agent-fits-all (MEMORY #0). Per-tab specialization is the same principle applied at module granularity.

---

## Why this might be worth doing

1. **Each agent works at peak strength.** Claude's content-merit win in today's bakeoff is evidence about Tab 1 narrative, not about whole-module dominance. Splitting the question into "best Tab 1 writer," "best Tab 3 writer," etc. lets each agent be evaluated on its actual strength.
2. **Smaller per-tab prompts.** Today's V7 writer prompt is ~127KB. Each per-tab prompt becomes ~25-40% the size — focused on one artifact type, one schema, one set of guidance. Lower cognitive load on the LLM = higher adherence.
3. **Failures isolate per tab.** If Tab 3 activities are weak, you retry Tab 3 only — not regenerate the whole module. Cheaper recovery, finer-grained gates.
4. **The empirical signal is already there.** Today's bakeoff showed Claude produces a meticulous, citation-careful Tab 1; Codex's Tab 1 truncated `равцова` for `Кравцова`. Codex's strength on structured data isn't shown in that test because monolithic writing doesn't isolate it. Per-tab dispatch would.
5. **Composes with the gate-redesign proposal.** Tab-aware gates align naturally with per-tab writers — each agent's output is gated against its tab's own structural requirements, no "global %" temptation.
6. **The Track B (two-pass workflow) idea was a special case of this.** Pass 1 = "Ukrainian-content tab" vs Pass 2 = "EN-scaffolding tab" was one specific cut; tab-split is the general pattern. Today's Track B YELLOW verdict (anchor preservation works; immersion off; activities schema broke) becomes meaningful evidence under the more general pattern.
7. **Aligns with existing reviewer architecture.** Cross-agent review is already the norm. Cross-agent WRITING is the same architectural principle extended.

## Why this might NOT be worth doing

1. **Cross-tab coherence is a real risk.** Tab 2 vocab MUST align with Tab 1 prose vocab. Tab 3 activities MUST exercise Tab 1 grammar targets. Tab 4 citations MUST support Tab 1 claims. With one writer, alignment is implicit. With four writers, it requires either sequential dispatch (later tabs read earlier output) OR an explicit coherence-check gate.
2. **Pipeline rewrite required.** Today's `v7_build.py` writer phase is single-dispatch (~lines 280-323). Per-tab dispatch is multi-dispatch. Sequential = simpler but slower; parallel = faster but coherence-fragile. Either way it's a structural change, not a tweak. Estimated ~1-2 days of focused work.
3. **More dispatches in flight.** 4 dispatches per module instead of 1. Concurrency cap (`2 Claude + 2 Codex + 2 Gemini`) becomes more relevant. Module throughput depends on queue depth.
4. **Reviewer phase may need to split too.** Today's reviewer reviews the whole artifact. Per-tab writers may want per-tab reviewers, OR a unified reviewer that specifically checks cross-tab coherence. Either way, more changes downstream of writer split.
5. **Cost multiplier (uncertain direction).** 4 LLM calls vs 1 per module. But each call is smaller (smaller prompt = fewer input tokens). Net cost may be lower OR higher; needs empirical measurement.
6. **Writer-choice evidence is partial.** Today's bakeoff showed Claude winning Tab 1 specifically. Whether Codex is genuinely the right Tab 2/Tab 3 writer is not yet evidenced — it's a reasonable inference from Codex's mechanical schema correctness elsewhere, but a tab-split bakeoff would settle it.
7. **Could be a lateral move at A1/A2 cost.** If deployed A1 modules already pass new gates (per the gate-redesign Phase B), the bigger question is whether we need V7 rebuild for A1 at all. If the answer is "no for most A1," the writer-split investment is amortized only over A2 + future levels.

---

## Implementation paths

### Path A — sequential dispatch (recommended for first experiment)

Order: Tab 1 → Tab 2 → Tab 3 → Tab 4. Later tabs receive earlier tabs' output as additional context.

```
1. Claude writes Tab 1 (module.md) — input: plan + Tab-1 spec
2. Codex writes Tab 2 (vocabulary.yaml) — input: plan + Tab 1 output + Tab-2 spec
3. Codex writes Tab 3 (activities.yaml) — input: plan + Tab 1 output + Tab-3 spec + ACTIVITY_CONFIGS allowlist
4. Gemini writes Tab 4 (resources.yaml) — input: plan + Tab 1 references[] + Tab-4 spec
```

**Pros:** simple orchestration; Tab 1 anchors the module so later tabs cohere naturally; reviewer phase unchanged
**Cons:** total wall-clock = sum of per-tab durations; failure mid-chain requires partial retry

### Path B — parallel dispatch with coherence check

All four tabs dispatched simultaneously with shared plan + cross-tab-coherence reviewer at the end.

**Pros:** faster wall-clock
**Cons:** cross-tab coherence is fragile (Tab 2 vocab might not match Tab 1's actual vocab); requires explicit coherence gate; partial-failure handling is more complex

### Path C — hybrid (Tab 1 first, then parallel 2-3-4)

Tab 1 ships first; Tabs 2-3-4 dispatch in parallel reading Tab 1.

**Pros:** Tab 1 anchors everything; parallel speed on the structured tabs
**Cons:** still needs coherence verification between Tab 2 and Tab 3 (both reference UK grammar; they might diverge)

Recommend **Path A** for the proof-of-concept experiment; revisit B/C if A proves the pattern works and wall-clock becomes a bottleneck.

---

## What this DOES NOT change

- **Writer choice per tab is empirical, not theoretical.** Today's bakeoff evidence supports Claude→Tab 1. Codex→Tab 2/Tab 3 is a reasonable inference. Gemini→Tab 4 is consistent with existing wiki-writer policy. All choices are revisitable via per-tab bakeoff if signal warrants.
- **Reviewer phase remains.** Either unchanged (reviewer sees full module after assembly) or split per-tab (deferred to a follow-up decision).
- **Plan schema, gate logic, MDX assembler.** All orthogonal to this proposal.
- **The current claude-tools win for "V7 writer."** That decision was monolithic. Under tab-split, the win becomes "Tab 1 writer," which is what the evidence actually supports. The decision card `2026-05-06-writer-selection-codex-gpt55.md` (REVISED-AGAIN) should be amended to reflect tab-scoped writer choices once this proposal accepts.

## Open questions for the decider

1. **Sequential (Path A) or parallel (Path B/C)?** Recommend A for proof-of-concept; revisit if wall-clock is bottleneck.
2. **Should the experiment use `a1/my-morning` (today's bakeoff target) for direct comparison, or pick a fresh module?** Recommend `a1/my-morning` — direct comparison to today's monolithic claude bakeoff is the cleanest evidence.
3. **Does Tab 4 (Ресурси) go to Gemini or Codex?** Gemini is the policy-aligned default; Codex is the backup. Could bakeoff Tab 4 specifically.
4. **Does this proposal depend on the gate-redesign accepting first, or can they ship independently?** They can ship independently. Each is independently valuable. If both ship, they compose well.
5. **Reviewer split — deferred to follow-up, or addressed now?** Recommend defer. Get writer-split working; reviewer-split is a separate architectural decision.

## Recommended path forward

1. **Accept this Decision Card** — promotes to ACCEPTED in `docs/decisions/2026-05-13-writer-split-by-tab.md`
2. **Cheap proof-of-concept experiment first** (~1 hour wall-clock, ~4 LLM calls):
   - One module: `a1/my-morning`
   - Sequential Path A: Claude → Codex → Codex → Gemini
   - Capture each writer's output, the full module after assembly, and a side-by-side comparison with today's monolithic claude bakeoff
   - Verdict: does the tab-split output (a) cohere, (b) pass gates (new or old — either signal helps), (c) feel pedagogically right
3. **If proof-of-concept passes** → invest in `v7_build.py` orchestration changes (~1-2 days Codex dispatch)
4. **If proof-of-concept fails** → either tune the per-tab prompts and retry, OR fall back to monolithic writer (sunk cost = 4 LLM calls + a couple of hours analysis)

Total commitment for accepting today: ~1 hour of LLM-call budget + analysis time for the proof-of-concept; no code change until the experiment validates.

## Related

- Companion proposal: `2026-05-13-immersion-gate-tab-aware-structural.md` (independent decision; either can ship without the other but they compose well)
- Predecessor architectural precedents:
  - `docs/decisions/2026-04-26-reboot-agent-responsibilities.md` §1 (wiki = Gemini policy)
  - `docs/decisions/2026-05-06-writer-selection-codex-gpt55.md` REVISED-AGAIN (current claude-tools-for-V7 monolithic choice)
  - MEMORY #0 — 3:3:3 dispatch split by fit
- Empirical context:
  - Today's bakeoff (`audit/bakeoff-2026-05-13-midday/`) — monolithic comparison
  - Track B YELLOW verdict (`audit/twopass-pass2-only-2026-05-13/REPORT.md`) — special-case evidence of tab-shape-mattering
  - Held PR #1915 (Track B research artifacts)
- Lesson Contract authority: `docs/lesson-contract.md` §1 (source artifacts), §3 (per-tab component inventory)
- Activity allowlist: `docs/best-practices/activity-pedagogy.md` + `scripts/pipeline/config_tables.py:ACTIVITY_CONFIGS`
