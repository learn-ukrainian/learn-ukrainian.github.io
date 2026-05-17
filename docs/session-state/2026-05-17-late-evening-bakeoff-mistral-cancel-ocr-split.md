---
date: 2026-05-17
session: "Evening + late evening. Drove vibe + opencode + hermes CLI study, agent capability bakeoff (Mistral, DeepSeek v4 pro/flash), API /artifacts UI fix, OCR pipeline build attempt, Mistral subscription cancellation, full 4-way head-to-head (DeepSeek pro/flash vs Opus xhigh vs Codex gpt-5.5 xhigh). 14 commits, 1 PR-via-issue filed. Git tree clean at handoff."
status: green
main_sha: 96d9eeec2b
main_green: true
open_prs: [1873]  # dependabot only
open_issues_filed_this_session: [2106]  # ALLOWED_ROOTS whitelist drift
active_dispatches: 0
worktrees_open: 1  # main + clawpatch-trial (eval artifact, can clean later)

handoff_split:
  this_session_continues_on:
    - "Path 3 PR1 (deterministic skeleton seeder) — afternoon-handoff carry-over"
    - "m20 ship under Path 3"
    - "Phase 2b A1 batch (m01-m07) under Path 3"
    - "clawpatch tech-debt: #2099 HIGH, #2100/2101/2102 MEDIUM"
    - "evidence-layer 5 PRs (queued behind Path 3)"
    - "hermes_deepseek.py adapter build (~50 LOC clone of hermes_grok.py)"
    - "Gemma-local audit (define lane or remove from /api/orient)"
  parallel_agent_handles:
    - "OCR-ONLY: ESUM Phase 2 continuation via scripts/etymology/bulk_ocr_gemini.py (691 pages done; ~3000 pages remaining across 6 volumes)"
    - "Any new OCR work (e.g. textbook scans for curriculum citations)"
    - "Coordinator: this session. OCR agent reports findings back via channel or handoff."

p0_for_this_session:
  - "Read Path 3 Decision Card at docs/decisions/2026-05-17-path3-per-obligation-review-loop.md"
  - "Fire Path 3 PR1 dispatch (deterministic skeleton seeder) — Codex"
  - "After PR1 lands: PR2-PR4 sequential through Path 3 completion"
  - "m20 rebuild under Path 3 → ships as proof-of-pipeline module"
  - "Then Phase 2b A1 batch + clawpatch tech-debt drain"

p0_for_ocr_agent:
  - "Continue ESUM Phase 2 OCR via scripts/etymology/bulk_ocr_gemini.py"
  - "Current state: 691 ok / 130 errors / 647 valid .md of 3,691 target pages (per current.md)"
  - "Idempotent restart on QUOTA_HALT (rotate Gemini OAuth, re-run)"
  - "DO NOT touch agent routing, agent matrix, Path 3 work — those are this session's lane"
---

# Late-evening session — bakeoff + Mistral cancel + OCR-split handoff

## TL;DR (3 lines)

1. **Mistral subscription cancelled.** Bakeoff data showed DeepSeek-flash via
   hermes matched or beat Mistral medium-3.5 on every tested role; Mistral made
   a false-positive on content review. Roster now 6 families (Claude, Codex,
   Gemini, Grok, DeepSeek v4, Gemma-local TBD).
2. **Full 4-way capability matrix shipped** at `docs/agents/AGENT-CAPABILITY-MATRIX.md` —
   DeepSeek pro/flash via hermes vs Opus xhigh vs Codex gpt-5.5 xhigh × 7 roles
   + linguistic verification. Backups per role + drop recommendations. 65 raw
   probe outputs preserved at `audit/2026-05-17-agent-bakeoff-evening/`.
3. **OCR delegation:** parallel agent takes the OCR-only lane (ESUM Phase 2
   continuation via existing `scripts/etymology/bulk_ocr_gemini.py`); this
   session continues with Path 3 + clawpatch tech-debt + everything else.

## What landed today (14 commits this session)

| SHA | What |
|---|---|
| `5ebf73875f` | Evening CLI study handoff (vibe Mistral + hermes DeepSeek) |
| `d9149cc732` | Correction: opencode for DeepSeek (later reversed) |
| `380f843469` | **Fix `/api/artifacts/html`** missed `docs/proposals` + `docs/poc` (48→52 artifacts) |
| `efbc1b56a3` | Capability matrix v1 |
| `2c65a59e08` | Opencode-for-Grok investigation (not natively supported, custom-provider extensible) |
| `c8260f0e01` | OCR pipeline (credential loader + Mistral client + 15 security tests + setup docs) |
| `f82fc315d9` | Failure telemetry persists to disk |
| `0090550869` | OCR JSON body shape corrected (`image_url.url` nesting) |
| `7dd3caef0e` | Extended bakeoff: Research / Content Writing / Content Review |
| `a0ad4095bc` | **Routing reversal: hermes for DeepSeek** (not opencode — 33% empty-output flake) |
| `0338a57900` | Mistral OCR client removed (subscription cancelled) |
| `31b338a639` | Doc updates after Mistral removal (matrix + SETUP) |
| `5367cbfacf` | Full 4-way bakeoff (DeepSeek/Opus/Codex × 7 roles) |
| `96d9eeec2b` | **Git hygiene** — gitignore + commit afternoon briefs + bulk lint patch |

Plus 1 GitHub issue filed: **#2106** — `/api/artifacts/html` ALLOWED_ROOTS whitelist drift (structural follow-up; user-blocking 4-artifact fix already shipped).

## Final agent roster + role winners

| Role | Primary | Backup | Tertiary |
|---|---|---|---|
| Plan | Codex gpt-5.5 xhigh | Opus xhigh (until 2026-06-15) | DeepSeek-pro hermes |
| Architect | **Codex** (novel artifact-store decoupling) | Opus xhigh | DeepSeek-pro hermes |
| Coding | Codex (`casefold` rigor) | Opus xhigh (idiomatic) | DeepSeek-pro hermes |
| Code Review | **DeepSeek-flash hermes** (A+, 15s, cheap) | Codex (A+ novel catches) | Opus xhigh |
| Research | Codex (with web search → primary sources) | Opus xhigh | Grok 4.3 hermes |
| Content Writing | Opus xhigh (until 2026-06-15) OR DeepSeek-pro hermes (MCP-verified) | DeepSeek-flash hermes | Gemini 3.1 pro |
| Content Review | **DeepSeek-pro hermes** (A+, MCP-backed verdict) | Opus xhigh | DeepSeek-flash hermes |
| Linguistic Verification | inline Claude w/ `mcp__sources__*` | DeepSeek-pro hermes | DeepSeek-flash hermes |
| OCR / Vision | **Gemini 2.5-flash** via `scripts/etymology/bulk_ocr_gemini.py` (691-page track record) | Apple Vision (untested) | Google Document AI (untested) |
| UI Testing | Claude inline + Chrome MCP | Codex Desktop `@browser-use` | Claude Desktop |
| Bug Hunter (clawpatch) | per-area rotation (Codex + DeepSeek + Claude + Gemini) | — | rotation IS the redundancy |

Full grades + raw probe outputs in `docs/agents/AGENT-CAPABILITY-MATRIX.md`.

## Two load-bearing technical findings

### 1. opencode flake = DeepSeek keep-alive empty-line streaming

DeepSeek's API sends empty lines as keep-alives during reasoning (per their
[FAQ](https://api-docs.deepseek.com/faq/)). opencode's stream parser likely
terminates on the first empty line, returning banner-only (we saw 3/9 = 33%
flake rate). Hermes correctly accumulates content past empty lines (5/5 success
rate on the same prompts). This validates the routing decision and explains
the mystery cleanly — not a model issue.

### 2. Hermes wires `sources` MCP into the DeepSeek session

When given content-writing or content-review tasks via `hermes -z`,
DeepSeek-pro **proactively calls** `mcp__sources__verify_words`,
`query_cefr_level`, `check_russian_shadow`, etc. before emitting content,
and includes a verification summary in the output. This is exactly the
writer-isolation behavior we've been engineering via prompts. opencode
doesn't wire MCP, so its content was both flake-prone AND unverified.

Implication: post-2026-06-15 cutoff (when Opus dispatches drop),
**DeepSeek-pro via hermes inherits the Content Writing + Content Review
gold-standard slot** — it's already the verification king.

## Mistral cancellation — bakeoff evidence

DeepSeek-flash via hermes matched or beat Mistral medium-3.5 on EVERY tested
role:

| Role | Mistral | DeepSeek-flash hermes |
|---|---|---|
| Plan | B (29.9s) | A- (~17s) |
| Architect | C+ (14.4s thin) | B+ (11.3s sharp) |
| Coding | B+ | A (with VESUM-backed bonus note) |
| Code Review | B− (missed sentinel) | A+ (caught magic-number) |
| Content Writing | B+ (no speaker labels) | A (labels + correct locative) |
| Content Review | **C (false positive on `-ся/-сь`)** | **A (zero false positives)** |
| Linguistic verification | ✅ correct | ✅ correct + polysemy detail |

The false-positive on `-ся/-сь` was the dealbreaker. Content review is the
worst place for unreliability. We kept the credential-loader pattern
(`scripts/ocr/_credentials.py` + 15 security tests + `docs/ocr/SETUP.md`) for
future API key needs; deleted the Mistral OCR client.

## What this session does NOT touch (OCR agent's lane)

- `scripts/etymology/bulk_ocr_gemini.py` — the production tool
- `data/raw/esum/jp2-staging/` (gitignored) — source images
- `data/raw/esum/gemini-ocr/` (gitignored) — per-page Gemini OCR outputs
- `data/raw/esum/*.txt` (gitignored as of `96d9eeec2b`) — concatenated volume OCRs
- Anything OCR-shape under `audit/etymology-ocr-feasibility/`

If the OCR agent finds bugs in the underlying ingester or sources DB,
they file an issue / dispatch brief and the orchestrator (this session) picks
it up — but the OCR work itself stays in their lane.

## P0 queue for this session

In order:

1. **Read Path 3 Decision Card** at
   `docs/decisions/2026-05-17-path3-per-obligation-review-loop.md` (or
   `pending/` if not yet moved). Internalize the 6-element architecture.
2. **Fire Path 3 PR1** — deterministic skeleton seeder. Per the afternoon
   handoff this is a Codex dispatch. Brief authoring + `delegate.py dispatch`.
3. **After PR1 lands:** PR2 (strict `<fixes>`-only reviewer per ADR-007),
   PR3 (batched-then-per-obligation correction staging), PR4 (Goodhart sentinel
   cross-family pass) — each Codex dispatch, sequential.
4. **m20 rebuild under Path 3** → ships as the first proof-of-pipeline module.
5. **Phase 2b A1 batch** (m01-m07) under Path 3 architecture.
6. **Tech debt** drain — #2099 HIGH (audit_level.py CI-trust killer) first,
   then #2100/#2101/#2102 MEDIUM. clawpatch lane per the adoption decision.
7. **Build `hermes_deepseek.py` adapter** — clone of `hermes_grok.py`. ~50 LOC.
   Adapter is what wires DeepSeek into `delegate.py dispatch` properly. Not
   urgent; can land anytime after Path 3 PR1.
8. **Gemma-local audit** — define a lane or remove from `/api/orient`. Low
   priority, do during a slow window.

Evidence-layer 5 PRs are queued behind Path 3 per the afternoon decisions.
Don't pre-empt that ordering.

## Open follow-ups (post-handoff to do at some point)

- **Mistral OCR vs Gemini Vision bakeoff** — NOW UNBLOCKED (Mistral cancelled,
  not worth pursuing). The credential-loader pattern remains valid for any
  future API key.
- **opencode custom-provider for Grok** — opencode's `opencode.jsonc`
  supports `provider: {xai: {api: "https://api.x.ai/v1", env: ["XAI_API_KEY"]}}`.
  Not urgent — hermes works fine for Grok today. Revisit only if we end up
  duplicating hermes logic.
- **`opencode_*` adapters** — formally drop the planned `opencode_deepseek.py`
  recommendation. Hermes wins on reliability + MCP wiring.

## Predecessor chain

1. `docs/session-state/2026-05-17-afternoon-path3-decision-card-handoff.md`
2. `docs/session-state/2026-05-17-evening-vibe-and-hermes-deepseek-cli-study.md`
3. THIS DOCUMENT (late evening — bakeoff + Mistral cancel + OCR split)

## Format note

MD per #M-2 (ai→ai handoff). HTML companion deferred; this is a routing /
queue handoff, not a build/audit result with rich human-read value.

## Tree state at handoff

- main: `96d9eeec2b`, green, ahead of origin 0
- Working tree: 0 dirty files outside exempt paths
- 0 active dispatches
- 1 worktree open: `.worktrees/clawpatch-trial` (eval artifact, deletable
  when convenient)
- MEMORY.md at 148/150 lines (approaching budget — trim before adding)
