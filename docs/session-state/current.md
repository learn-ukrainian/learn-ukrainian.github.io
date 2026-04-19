# Session Handoff — 2026-04-19 late afternoon (#1345 closed · L1-UK pivot question refined · #1338 ready)

You're resuming (or starting cold). Boot via the API, not the filesystem:

```bash
curl -s http://localhost:8765/api/state/manifest
curl -s http://localhost:8765/api/orient
curl -s 'http://localhost:8765/api/comms/inbox?agent=claude'
```

## TL;DR

Three things happened since the morning handoff:

1. **#1345 bakeoff closed** (8-task Codex chain, zero OOM after initial parallel-dispatch correction). Verdict: `BAAI/bge-m3` for #1338 T1-T2; metadata-first locked for #1341 T3-T4. Qwen3 parked in #1346.

2. **You proposed a "crazy idea" on your bike ride**: build the canonical wiki in Ukrainian, publish dual tracks (English-scaffolded A1/A2 + Ukrainian-only immersion for B1+). Tri-agent discussion revealed the idea is **narrower than it seemed** — see "L1-UK pivot status" below.

3. **#1338 prompt is still ready to dispatch** at `/tmp/codex-1338-prompt-DRAFT.md`. Retrieval rebuild is orthogonal to the L1-UK question.

## L1-UK pivot status (read this — key reframe)

Tri-agent discussion (`architecture` channel, thread `90555b6ee066`, full text at `orchestration/discussions/2026-04-19-l1-uk-wiki-pivot.md`) ended with Gemini + Codex both [AGREE], Claude's responses failed due to a bridge bug (no actual disagreement). Codex's main correction:

> **"The wiki compile layer already emits Ukrainian articles, not English briefs."**

Evidence: `scripts/wiki/prompts/compile_article.md:45`, `compile_pedagogy_brief.md:41`, `compile_grammar_brief.md:41`, `compile_academic.md:79` — all require Ukrainian output today.

**So "build wiki in Ukrainian" is NOT a pivot. It's already the case.**

The real variable under test is the **A1/A2 writer layer** (`scripts/build/phases/v6-write.md`). It currently consumes Ukrainian wiki briefs and produces English-scaffolded MDX modules. The genuine question is whether changing the writer's **prompt framing** (e.g. "paraphrase this Ukrainian brief into English scaffolding preserving Ukrainian metalanguage where pedagogically appropriate") produces measurably better modules than current behavior.

This is a **prompt engineering + audit question**, not an architecture rebuild.

### What NOT to do

- **Don't create `l1-uk/`** as a new publish root. The repo already has `l2-uk-direct` architecture (`docs/architecture/ARCHITECTURE.md:167`, `scripts/build/build_module_direct.py`) for the no-English case. If we want a published immersion track later, that's the proper home — a separate migration, not coupled to this experiment.
- **Don't couple the writer A/B to any publish/routing changes.** `l2-uk-en` is hardcoded in 4+ places (`scripts/build/v6_build.py:428`, `scripts/manifest_utils.py:36`, `scripts/generate_landing_pages.py:20`, `scripts/paths.py:18`). Changing roots is a separate project.
- **Don't rebuild what's already built.** A2.9 Metalanguage Bridge (6 modules, sequence 61–66) is already designed and grounded in Заболотний + Литвінова. Don't re-design it.

### Adjusted A/B test (8 articles, from the discussion)

Expand your original 6 to 8 per Gemini's + Codex's push:

| # | Module | Why |
|---|---|---|
| 1 | A1/M01 | early literacy, concrete |
| 2 | A1/M02 | early literacy |
| 3 | A1/M03 | early literacy |
| 4 | A1 mid — case intro (accusative or nominative) | morphology |
| 5 | A1 late — verb aspect intro | abstract |
| 6 | A1 or A2 — one vocabulary module (daily routines, shopping) | lexical, Gemini's add |
| 7 | A2 grammar-heavy (conditional mood or instrumental) | syntax/morphology |
| 8 | One A2.9 metalanguage module (pick from metalanguage-phonetics, metalanguage-morphology, etc.) | immersion handoff stress test, Codex's add |

Protocol:
- **Identical retrieval** between A arm and B arm (same wiki sources, same query construction)
- **Blinded review** — reviewer does not know which arm
- Compare on the 4-dim scores used for wiki review, OR design a consistent module reviewer (wiki review is 4-dim; learner module review is 9-dim — measurement gap to resolve before the A/B)
- **Two-batch confirmation** — if canary wins twice, discuss architecture. Until then, no published-tree changes.

### Key risk the A/B must test for

Codex flagged: A1/A2 writer could "over-shift into Ukrainian technical prose" when primed with Ukrainian briefs, violating the English-scaffolding contracts in `scripts/config.py:215, 231, 311, 391`. This is the failure mode the test design must surface.

## Chain status

| # | Title | State | Next step |
|---|---|---|---|
| **#1338** | T1-T2 retrieval pipeline | ⏸️ waiting | **Dispatch next** — split into 6 sub-tasks per the plan agreed pre-bike. Prompt draft at `/tmp/codex-1338-prompt-DRAFT.md`. BGE-M3 locked. |
| #1340 | Re-validate #1330 | ⏸️ gated on #1338 | — |
| #1341 | T3-T4 archaic retrieval | ⏸️ **deferred** | User's call: close as "deferred until better archaic retrieval tech (sovereign UK LLM, historical-Slavic fine-tunes). Revisit 2026 Q3 or earlier if candidate emerges." Don't ship weak T3-T4 to lock in mediocrity. |
| #1342 | Doc updates | ⏸️ last | — |
| #1344 | Replace Phase A canary | ⏸️ gated on #1338 | Plan audit posted to issue |
| **#1345** | Bakeoff + rerankers | ✅ **closed** | BGE-M3 wins, metadata-first confirmed |
| #1346 | Qwen3 CPU/smaller-batch parked | open | Conditional reopen only |
| #1335 | EPIC tracker | open | Closes when #1338/#1340/#1342 all done |

### The writer A/B — open question

New work item implied by today's discussion. Consider filing as its own GH issue:

> **Issue title**: "A/B test: writer prompt framing for Ukrainian-brief → English-scaffolded A1/A2 output"
> Scope: 8-article canary per the table above. Measurement: consistent reviewer (pick 4-dim wiki-style OR 9-dim module-style, not both). Blinded. Identical retrieval. Two-batch confirmation rule.
> Blocked on: #1338 (so the retrieval feeding both arms is actually working).

I recommend filing it but holding dispatch until #1338 + #1340 are green (so the baseline "current pipeline works end-to-end" exists).

## Codex chain summary — what shipped today

| SHA | Task | What |
|---|---|---|
| `c7d429d07` | #1345-A | Sequential lockfile + reranker harness skeleton + HF_TOKEN wiring |
| `8f5d753c8` | #1345-B | jina-v3 full 1000-sample — smoke didn't hold, archaic collapsed |
| `87d7a454f` | #1345-F | BGE-reranker-v2-m3 full — lifts modern FTS5 +0.33 R@10, no archaic help |
| `0101ce36e` | #1345-G | jina-reranker-v2 — essentially ties BGE-reranker |
| `b32033f46` | #1345-C | e5-large-instruct — 512-tok cap, 2020/3048 passages truncated |
| `3f57300dc` | #1345-D | gte-multilingual-base — fastest (246s), weakest on archaic |
| `2e7bda11e` | #1345-E | EmbeddingGemma-300M — shockingly weak on Ukrainian (0.03 R@10 modern) |
| `089e6e459` | #1345-H | Survey doc refresh + verdict + #1345 closed |

## Plus my own commits today

| SHA | What |
|---|---|
| `d110b741d` | rebuild orchestrator + plan doc |
| `a613f9b82` | dim-review taxonomy + A1 char cap + registry invariant |
| `5e0b0bd47` | autocompact 650k → 750k |
| `0ce8d5b7e` | Phase A canary deprecated (#1344) |
| `c9707dc00` | statusline context % |
| `249ab34fe` | statusline subscription-oriented (dropped $cost) |
| `549cefacb` | Gemini rebuild-plan review encoded |
| `74ab96e3b`, `6deab3faf` | earlier handoffs (this supersedes) |

## Issues updated

| # | Action |
|---|---|
| #1336, #1337, #1339 | closed earlier |
| #1343 | closed (Codex claimed closure but hadn't) |
| #1332 | closed (superseded by ADR-006) |
| #1345 | **closed with full verdict** |
| #1344 | curriculum-plan audit posted as comment |
| #1346 | newly opened (Qwen3 parked follow-up) |

**Today's total on main: 36 commits** (34 + this handoff + discussion archive).

## Env / infra recap

- HF_TOKEN ✅ in `~/.bash_secrets`, sourced by bash login shells
- Autocompact 750k (picked up on fresh session launch)
- `CLAUDE_CODE_MAX_OUTPUT_TOKENS=64000`, `CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS=32000` confirmed correct
- Statusline works; shows `[ctx: N%]` with color coding + `[5h/7d: N%]` when elevated
- Bridge bug noticed: `ab discuss` fails for claude because pinned context gets passed as CLI flags. File as a small issue if not already known; Gemini + Codex work fine.

## Git dirty state (unchanged — do not touch)

```
?? wiki/.reviews/pedagogy/a1/sounds-letters-and-hello.json
?? wiki/pedagogy/a1/   (sounds-letters-and-hello.md + .sources.yaml)
```

Phase 0 smoke artifacts — known-REJECT under old retrieval. Wait for #1338 → #1340 → clean Phase 0 re-run.

## Gemini reviews archived today

- `review-wiki-rebuild-plan` (msg #391) — 3 findings encoded in `549cefacb`
- `review-1338-prompt` (msg #393) — 4 findings encoded in draft prompt
- Tri-agent discussion archived at `orchestration/discussions/2026-04-19-l1-uk-wiki-pivot.md`

## What to do first on resume

1. **Read this handoff + `orchestration/discussions/2026-04-19-l1-uk-wiki-pivot.md`** (has the full discussion text — 134 lines)
2. Decide: dispatch #1338 now? Or also file the writer-A/B issue first so it's on the tracker?
3. Consider closing #1341 as "deferred pending better archaic retrieval" if you agree with that call
4. Re-arm Monitor watcher when you dispatch #1338 (snippet in previous handoffs)

## Monitor state

Monitor watcher already stopped (chain done). Re-arm per snippet in previous handoff when dispatching #1338 sub-tasks.
