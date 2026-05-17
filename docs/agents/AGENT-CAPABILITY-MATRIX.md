# Agent Capability Matrix

> **Living document.** Last full pass: 2026-05-17 evening. Re-run the role probes
> whenever a new model variant lands. Raw evidence preserved at
> `audit/2026-05-17-agent-bakeoff-evening/`. Companion doc:
> `docs/best-practices/agent-cooperation.md` for protocols, this doc for routing.

## TL;DR

We run a roster of **7 agent families** across **9 roles**. Tonight's bakeoff added
empirical signal for the two newest (Mistral via `vibe`, DeepSeek v4 via `opencode`)
on 4 of those roles. Headline recommendations:

- **Drop `devstral-small`** (Mistral lighter) from the production roster. Failed UK
  Russianism judgment (Russian-pretraining contamination) and is unlikely to compete
  on coding/review against `gpt-5.5`, `deepseek-v4-flash`, or `claude-sonnet`.
  Keep `mistral-medium-3.5` as the Mistral entry.
- **Drop the planned `hermes_deepseek.py` adapter** — superseded by `opencode`
  (richer JSON telemetry, faster per-call). Hermes stays as the **Grok** harness.
- **Investigate `gemma-local`** — last surfaced in `runtime.agents` but I have not
  seen it used in months. Either resurrect with a defined lane or remove from
  `/api/orient` to stop suggesting it's in rotation.
- **Add 4 missing roles:** linguistic verification (split from generic review),
  OCR / vision, UI testing, bug hunter / static audit. All exist informally; none
  has a documented routing.

## Agent inventory

| # | Family | CLI | Production models | Surface where they live |
|---|---|---|---|---|
| 1 | **Claude** | `claude` (Code), `claude` (Desktop) | `claude-sonnet-4.6` (default), `claude-opus-4.7` (xhigh) | `delegate.py --agent claude` (until 2026-06-15 cutoff); `ab ask-claude`; inline orchestrator |
| 2 | **Codex** | `codex` (CLI), `codex` (Desktop) | `gpt-5.5` (xhigh) | `delegate.py --agent codex`; `ab ask-codex`; Codex Desktop UI |
| 3 | **Gemini** | `gemini` | `gemini-3.1-pro-preview` (deep), `gemini-3.0-flash-preview` (routine), Gemini Vision (OCR) | `delegate.py --agent gemini`; `ab ask-gemini --model gemini-3.0-flash-preview` for routine, `--model gemini-3.1-pro-preview` for deep |
| 4 | **Grok** | `hermes -m grok-4.3` | `grok-4.3` | `delegate.py --agent grok`; `ab ask-grok`; uses `hermes_grok.py` adapter |
| 5 | **Mistral** | `vibe -p` | `mistral-medium-3.5` (high-effort default) | NEW LANE — adapter `vibe_mistral.py` PENDING; `VIBE_ACTIVE_MODEL` env override |
| 6 | **DeepSeek v4** | `opencode run -m deepseek/...` | `deepseek-v4-pro` (max effort), `deepseek-v4-flash` (default) | NEW LANE — adapter `opencode_deepseek.py` PENDING; rich JSONL telemetry via `--format json` |
| 7 | **Gemma local** | unclear | `gemma-local` (?) | UNCLEAR — listed in `/api/orient` `runtime.agents` but no recent use; investigate before next pass |

### Light / orchestration-only surfaces (not full agents)

- **`Agent` subagent: Explore** (Haiku) — fast read-only search. Use for "find me X across files." `subagent_type: "Explore"`.
- **`Agent` subagent: Plan** (Sonnet) — software architecture plan-only. Use BEFORE non-trivial implementations.
- **`Agent` subagent: curriculum-orchestrator** — me, when spawned as a sub-orchestrator.
- **`Agent` subagent: curriculum-writer** — restricted-tool writer (`mcp__sources__*` only). Used inside V7 build phases.

### Dropped in this report

- **`devstral-small`** — see drop recommendation in §Drop candidates.
- **`hermes_deepseek.py` (was planned)** — never built; killed before adapter PR.

## Role definitions (NINE roles, +2 from user's list)

The user listed 7 roles (research, plan, architect, coding, reviewing, content
writing, content reviewing). Splitting + adding makes 9:

| # | Role | Definition | Typical work |
|---|---|---|---|
| 1 | **Research** | Open-ended investigation, retrieval + synthesis | "How does X compare to Y," "summarize state of the art for Z," web/corpus exploration |
| 2 | **Plan** | Multi-step task decomposition, dependency ordering | Migration plans, build sequences, decision-card option enumeration |
| 3 | **Architect** | Design proposals, contract definition, trade-off analysis | ADRs, decoupling proposals, system boundary design |
| 4 | **Coding** | Write new code to a spec | Implement a function, write a script, port a library |
| 5 | **Code Review** | Judge an existing diff for correctness / quality | PR review, audit of a function, lint-level findings |
| 6 | **Content Writing** | Write Ukrainian curriculum modules | A1-C2 module text, dialogues, vocabulary, activities |
| 7 | **Content Review** | Judge curriculum content for pedagogy + linguistic quality | Plan review, post-build module review, friction triage |
| 8 | **Linguistic Verification** *(NEW, split from #5/#7)* | Single-shot Ukrainian word/phrase verification using sources MCP | Russianism check, VESUM lookup, stress verification, calque detection |
| 9 | **OCR / Vision** *(NEW, user-requested)* | Extract text / parse images | Ukrainian textbook OCR, layout extraction, scanned book ingestion |

Plus 2 cross-cutting capabilities the user didn't list but that we already use:

| # | Capability | Notes |
|---|---|---|
| A | **UI Testing / Browser Automation** | Currently Claude inline (chrome MCP) + Codex Desktop (`@browser-use`). Worth its own column. |
| B | **Bug Hunter / Static Audit** | clawpatch lane (per ADR-2026-05-17). Multi-agent rotation per code-area. |

## Empirical bakeoff results (2026-05-17 evening)

Seven probes designed across all 7 user-listed roles + the linguistic
verification we ran earlier. Probes are small but discriminating — see
`audit/2026-05-17-agent-bakeoff-evening/probe*.txt` for exact prompts. Grades
are mine after reading raw outputs; raw outputs are preserved in the audit dir.

| Role | mistral-medium-3.5 (vibe) | deepseek-v4-pro --variant max (opencode) | deepseek-v4-flash (opencode) |
|---|---|---|---|
| **Plan** | B (29.9s) — 4 steps + risks; step 4 has SQLite syntax slip (`ALTER COLUMN SET NOT NULL` invalid in SQLite) | A retry / **EMPTY first attempt** (24.7s banner-only; 55.3s on retry produced clean 4-step plan with sharp risks) | A- (11.6s) — accurate SQLite knowledge (WAL checkpoint, FTS `rebuild` exclusive lock), sleep-based batching |
| **Architect** | C+ (14.4s) — minimal "scanner + serving" split; weak trade-off | A (44.0s) — used Grep to inspect repo first, proposed `SCAN_ROOTS` + `SERVE_ROOTS` + **reconciler** for pending entries | A- (11.7s) — same split, sharper trade-off ("scanner finds, serving 404s = different invisibility") |
| **Coding** | B+ (29.9s) — correct + walrus operator; compact but readable | A (74.6s) — correct + adds word-boundary checks (`isalpha()` adjacency) not in spec — defensive engineering | B (11.8s) — wrote file `/Users/krisztiankoos/agent.py` (outside workdir, **hygiene violation**) and ran it; function works but prompt-following weak |
| **Code Review** | B- (12.0s) — 3 findings, MISSED sentinel ambiguity (highest-priority issue) | A (19.0s) — 3 findings, sentinel ambiguity articulated correctly | A+ (8.1s) — 3 findings, sentinel + caught magic-number `5` (both Mistral and pro missed it) |
| **Research** (Україна etymology) | A- (116.8s) — correct Vasmer + Pivtorak citations + accurate Hypatian Codex 1187 attestation | A (34.2s) — Vasmer + Rudnyckyj 1962-82 + critically evaluates the Hrushevsky counterhypothesis | **EMPTY OUTPUT** (13.2s banner-only) |
| **Content Writing** (A1 Ukrainian dialogue) | B+ (27.1s) — 4 turns, vocative correct, no Russianisms, no speaker labels (style miss) | **EMPTY OUTPUT** (35.3s) | A (19.9s) — speaker labels, café reference, correct locative case, comprehension question well-formatted |
| **Content Review** (planted `на протязі` Russianism + other issues) | **C** (18.1s) — caught the calque BUT **false positive** asserting `зустрінемось` is misspelled (both `-сь`/`-ся` are valid per VESUM) | B+ (71.4s) — caught calque + sharp pedagogical critique on past-tense complexity, but **over-prescriptive** on `звичайно→звісно` (звичайно is native UK, not Russian influence) | A (30.4s) — caught calque + Time-Place-Manner word-order critique + completeness critique; **no false positives** |

### Empty-output flake rate (significant)

Across 9 opencode + DeepSeek probes, **3 returned banner-only with no content**:
pro-max PLAN (attempt 1 — retry succeeded), pro-max WRITING, flash RESEARCH.
**~33% flake rate.** Probably an opencode/streaming edge case where the final
`text` event doesn't get emitted, not a model-level failure (the model spent
real wall-clock time in every case). If we use opencode + DeepSeek for any
production lane, the adapter MUST retry on empty output. Filed as follow-up
in §Open follow-ups.

### Mistral content-review false-positive risk

Mistral medium-3.5 produced a confident false positive on `зустрінемось` →
`зустрінемося`. Both forms are valid Ukrainian; the loader confidently
"corrects" the original to a non-existent rule. **This is more damaging than
missing a real finding** — false positives in content review erode trust in
real findings. Caveat: 1 false positive across 7 probes is not a pattern
yet, but the content-review lane is the one where this kind of mistake
costs the most. Recommendation: pair Mistral with a verifier (`mcp__sources__verify_word`)
for any `-ся` / `-сь` / orthography-detail finding before surfacing it to learners.

**Linguistic verification** (from earlier this session, `на протязі` Russianism probe):

| Model | Verdict | Latency | Notes |
|---|---|---|---|
| `mistral-medium-3.5` | ✅ correct | 7.7s | Terse fix suggestion |
| `devstral-small` | ❌ WRONG | 3.2s | **Russian-contamination failure** |
| `deepseek-v4-pro` (hermes) | ✅ correct | 37.5s | + etymology |
| `deepseek-v4-flash` (hermes) | ✅ correct | 26.8s | + polysemy disambiguation (best output) |
| `deepseek-v4-pro --variant max` (opencode) | ✅ correct | 11.3s | + grammar detail (instrumental case) |

**OCR / Vision** — NOT TESTED this session. `MISTRAL_API_KEY` not in shell scope. Once exported,
the test plan is: render a Ukrainian textbook page (Zaharіychuk Grade 1 p.52 — known clean
ground truth from our corpus) → call `mistral-ocr-latest` + `gemini-pro-vision` on the same
image → compare WER + diacritic accuracy + table-extraction correctness.

## Role → Agent routing (recommended)

Numbers in parens are confidence: **(E)mpirical from this session**, **(H)istorical from
prior audits**, **(I)nferred from architecture**.

| Role | Primary | Backup | Pick / Avoid signal |
|---|---|---|---|
| **Research** | Grok 4.3 (H) OR DeepSeek-pro-max (E) | Gemini 3.1 pro (H), Mistral medium-3.5 (E) | Pro-max wins on speed (34s vs Mistral's 117s) + adds critical evaluation of counterhypotheses. Mistral correct but slow. Flash UNUSABLE here (returned empty). Grok still strong for X.com / web access tasks. |
| **Plan** | DeepSeek-flash (E) OR Codex (H) | Claude-Opus-xhigh (H) | Flash is 2.5× faster than Mistral and avoids pro's flakiness. Codex remains the production planner. |
| **Architect** | Claude-Opus-xhigh (H) | DeepSeek-pro-max (E) | Opus xhigh for ADRs/decision cards (post-2026-06-15: Opus dispatches dropped → DeepSeek-pro-max takes lead). Pro's grep-then-design pattern is encouraging. |
| **Coding** | Codex gpt-5.5 (H) | DeepSeek-pro-max (E) | Codex remains incumbent — production-shipped 20+ PRs this month. DeepSeek-pro-max competitive on small tasks; needs validation on cross-file work. |
| **Code Review** | Codex (H) + DeepSeek-flash (E) | Gemini-3.1-pro (H) | DeepSeek-flash had the highest signal density tonight. Use it as cheap second-opinion alongside Codex on PR reviews. |
| **Content Writing** | Claude (until 2026-06-15) / Gemini (after) | DeepSeek-flash (E), Mistral medium-3.5 (E) | Per ADR `2026-05-06-writer-selection-codex-gpt55.md` REVISED → claude-tools. Post-June-15: Gemini default. Flash beat Mistral on format compliance + speaker labels in the A1 dialogue test. Pro-max UNUSABLE here (returned empty). NOT yet tested on full V7-module-scale output. |
| **Content Review** | Claude-Opus-xhigh (H) + Codex (H, green-team) | Gemini-3.1-pro (H), DeepSeek-flash (E) | xhigh-effort review on Opus is gold standard. **DeepSeek-flash is the strongest new entrant — caught the planted Russianism + sharp pedagogical critique + zero false positives.** Mistral medium-3.5 NOT trustworthy for content review without a verifier (produced false positive on `-ся/-сь`). |
| **Linguistic Verification** | inline Claude with `mcp__sources__*` | DeepSeek-pro / DeepSeek-flash (E) | Sources MCP must run in-process (Claude Code). For OUT-OF-PROCESS verification: DeepSeek (either variant) — both passed `на протязі`. **NEVER devstral-small** (contamination). |
| **OCR / Vision** | Gemini Vision (H, used for bulk ESUM re-OCR) | Mistral OCR (UNTESTED) | Pending Mistral bakeoff. User reports anecdotally that Mistral is strong. |

Cross-cutting:

| Capability | Primary | Notes |
|---|---|---|
| **UI Testing** | Claude inline + Chrome MCP | Codex Desktop has `@browser-use` for parallel testing. Mistral + DeepSeek not relevant here. |
| **Bug Hunter (clawpatch)** | per-area: Codex ↔ DeepSeek for `scripts/audit/`, `tests/`, `.mcp/`; Claude ↔ Mistral for `scripts/build/`, starlight | See afternoon handoff `2026-05-17-afternoon-path3-decision-card-handoff.md` for the full per-area table; one update: DeepSeek (via opencode) replaces hermes-deepseek throughout. |

## Drop candidates (the user-requested call)

### 1. DROP: `devstral-small`

**Evidence:** Failed Russianism judgment (returned "correct UK" for the classic
calque `на протязі`). Russian-pretraining contamination is a structural limit, not
a fixable prompt issue — devstral was likely trained on a lot of Russian repo READMEs
and Russian-speaking Slavic-language content. The "lighter" Mistral variant is
strictly worse than `mistral-medium-3.5` for any task that touches UK content, AND
unlikely to beat `deepseek-v4-flash` for code-only tasks (untested but flash already
wins on latency).

**Recommendation:** Remove `devstral-small` from any production routing. If we
want a "cheap Mistral" lane, retest after a major Mistral release. Don't ship it
to clawpatch lanes that walk over `curriculum/` or `scripts/wiki/`.

### 2. DROP (already): planned `hermes_deepseek.py` adapter

**Evidence:** Hermes `-z` mode gives us `tool_calls_total=None` (per
`hermes_grok.py` docstring). Opencode `--format json` gives us
`tokens: {total, input, output, reasoning, cache.{read,write}}` + `cost` per call —
clean parity with claude/codex/gemini adapters.

**Recommendation:** Build `opencode_deepseek.py` instead. Hermes stays scoped to
**Grok only**, where it's the canonical adapter and we have no opencode-equivalent.

#### Aside: can we use opencode for Grok too?

Probed 2026-05-17. **Not natively today, but extensible if we want it.**

- `opencode models` lists only `github-copilot/grok-code-fast-1` — Grok routed via
  GitHub Copilot's API, not native xAI. PONG returns `Forbidden: unauthorized: not
  licensed to use Copilot`. Path dead without a paid Copilot tier, and it's
  `grok-code-fast-1` not `grok-4.3` — different capability profile (faster +
  code-tuned, weaker on the research/reasoning where Grok wins for us).
- opencode DOES support custom OpenAI-compatible providers via
  `~/.config/opencode/opencode.jsonc`. xAI exposes `https://api.x.ai/v1`. Adding
  10-15 lines of config + `XAI_API_KEY` env var would unlock `opencode_grok.py`.

**Recommendation: KEEP hermes for Grok 4.3 until consolidation pays off.** The
existing `hermes_grok.py` works, MCP is wired, and migration cost (config +
adapter rewrite + retest) outweighs current pain. Revisit IF the DeepSeek +
Mistral adapters land AND we find ourselves duplicating hermes logic. Then
consolidate to opencode for all OpenAI-compatible API agents (Mistral via vibe
stays separate as its own CLI surface).

### 3. INVESTIGATE: `gemma-local`

**Evidence:** `runtime.agents` list at `/api/orient` includes `gemma-local`. No
session-state mention of it being used in the last ~30 days. Status unclear.

**Recommendation:** Either define a lane (probably: cheap on-machine summarization
when API budget hot, no network needed) and resurrect, OR remove from
`/api/orient` to stop signalling availability that isn't real. Defer this call
until user weighs in — needs ~5 min `gemma-local` probe + a routing decision.

## What I'd update in the afternoon-handoff routing table

The afternoon handoff (`2026-05-17-afternoon-path3-decision-card-handoff.md`)
proposed per-area routing for clawpatch scanning. Tonight's data changes one row:

| Area | Afternoon proposal | Tonight's update |
|---|---|---|
| Frontend `starlight/` | Claude ↔ Mistral | Claude ↔ `mistral-medium-3.5` (NOT devstral-small — even though it's "code-only" frontend, our Lit-essay/seminar copy will eventually touch this surface) |
| scripts/audit/ | Codex ↔ DeepSeek | Codex ↔ `opencode --model deepseek/deepseek-v4-pro --variant max` |
| scripts/build/ | Claude headless ↔ Mistral | Claude ↔ `mistral-medium-3.5` |
| (Everything else) | per afternoon handoff | unchanged |

## How to invoke each agent (cheat sheet)

```bash
# Claude (Sonnet inline / Opus xhigh dispatch)
# Inline: just chat. Dispatch (pre-2026-06-15):
scripts/delegate.py dispatch --agent claude --model claude-opus-4-7 --effort xhigh \
  --brief docs/dispatch-briefs/foo.md

# Codex
scripts/delegate.py dispatch --agent codex --model gpt-5.5 --effort xhigh \
  --brief docs/dispatch-briefs/foo.md

# Gemini (default flash for routine; pro for deep)
scripts/ai_agent_bridge/__main__.py ask-gemini --model gemini-3.0-flash-preview "QUESTION"
scripts/ai_agent_bridge/__main__.py ask-gemini --model gemini-3.1-pro-preview  "DEEP QUESTION"
scripts/delegate.py dispatch --agent gemini --brief docs/dispatch-briefs/foo.md

# Grok (via hermes)
hermes -z "QUESTION" -m grok-4.3
scripts/delegate.py dispatch --agent grok --brief docs/dispatch-briefs/foo.md

# Mistral (via vibe; NEW lane — adapter PR pending)
VIBE_ACTIVE_MODEL=mistral-medium-3.5 vibe -p "QUESTION" --output text --trust
# For longer work pass --max-turns N --max-price 0.50

# DeepSeek v4 (via opencode; NEW lane — adapter PR pending)
opencode run --model deepseek/deepseek-v4-pro --variant max \
  --dangerously-skip-permissions "QUESTION"
opencode run --model deepseek/deepseek-v4-flash \
  --dangerously-skip-permissions --format json "QUESTION"
# JSON envelope gives token + cost telemetry per call.
```

## Open follow-ups

1. **Mistral OCR bakeoff** — pending `MISTRAL_API_KEY` exported into orchestrator
   shell. Test target: render Zaharіychuk Grade 1 p.52 (known clean source); compare
   `mistral-ocr-latest` to `gemini-pro-vision`. WER + diacritic accuracy + table
   extraction.
2. **`opencode_deepseek.py` adapter** — implementation PR. Modeled on
   claude/codex (rich JSON), NOT on `hermes_grok.py`. Routes both pro and flash.
3. **`vibe_mistral.py` adapter** — implementation PR. Env-based model override
   (no `-m`), manual worktree (`--workdir` + `git worktree add`), 5-LOC adapter.
4. **DeepSeek empty-output flake — 33% rate across 9 probes** (confirmed this
   session): pro-max PLAN attempt 1, pro-max WRITING, flash RESEARCH all
   returned banner-only with real wall-clock time consumed. Recommendation:
   the `opencode_deepseek.py` adapter MUST retry on empty output, max 2
   retries, before treating as failure. File as tracking issue when the
   adapter PR lands. Hypothesis: opencode streaming edge case where final
   `text` event isn't emitted; model produced text but the harness lost it.
5. **Content writing bakeoff at module scale** — tonight's A1-dialogue probe
   was a smoke test (4 turns). The real test is a full V7-shape module:
   plan_sections, vocabulary YAML, activities, all 22 gates. Roadmapped
   behind Path 3 PR1. Tonight's small-scale signal: DeepSeek-flash and
   Mistral medium-3.5 are both viable candidates; pro-max is RISKY due
   to the empty-output flake.
6. **`gemma-local` audit** — define a lane or remove from `/api/orient`.

## Format note

MD per #M-2 (ai→ai reference doc). HTML companion deferred — this is a routing
spec that agents load, not a human-only artifact.
