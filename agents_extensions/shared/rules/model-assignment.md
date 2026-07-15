# Per-Task Model Assignment (HARD RULE)

<critical>

Match the EXACT command — not a principle. Memory does not enforce; the dispatch tool does. Established 2026-05-06 after repeated drift on cost discipline.

| Task | Tool + model |
|---|---|
| Inline code edit ≤5 LOC, fixing a CI failure I just caused | Me, current model |
| Claude-side ROUTINE work — formulaic reviews, config/fixture edits, monitoring-only sessions, wiki fixes, mechanical PR babysitting | **Sonnet 5** (user 2026-07-07: "use Sonnet more often for routine work") — dispatch `--model sonnet` / Sonnet session. Reserve the frontier Claude tier (Opus 4.8 / whatever frontier model is active) for judgment work: architecture, adversarial review, pedagogy, hard bugs. **Route by TIER-FIT, not model name — the Claude lane rotates** (Fable 5 was temporary). **Motive = SAVE THE FRONTIER WINDOW** (user-confirmed 2026-07-07): if Sonnet is busy, QUEUE routine work or reroute to agy/codex — do not burn the frontier window on it. |
| Code change >5 LOC, mechanical / pattern-applying / fixtures | `delegate.py dispatch --agent codex --mode danger --worktree --base origin/main` (no `--model`) |
| Code Review (PR diff) — cheap second opinion | `delegate.py dispatch --agent deepseek --model deepseek-v4-flash --mode read-only` (default first-party DeepSeek; opt-in `--provider openrouter` for pinned US path per #4358). (hermes; PR #2107 adapter). Empirical winner 2026-05-17 bakeoff (A+ at 15s). ⚠️ ALWAYS pass `--silence-timeout` — the lane can silent-stall with zero stdout and failover does NOT trigger on silence (#4672, stalled 2/2 on PR #4667). On stall: reroute **grok** (validated adversarial reviewer 2026-07-07 — live worktree verification, 81s, caught-nothing-false) |
| Content Review with VESUM verification (load-bearing) | `delegate.py dispatch --agent deepseek --model deepseek-v4-pro` (first-party DeepSeek default per #4358; hermes/MCP-backed: proactively calls `sources` `verify_words`, `query_cefr_level`, `check_russian_shadow`). Validated by PR #2112 write-mode dispatch on artifacts-MD feature |
| Wiki / content writing · content / pedagogy / factual **review** | agy — `delegate.py dispatch --agent agy` (write) or `ab ask-agy --to-model gemini-3.1-pro-high` (review). **Use agy actively here** (user 2026-06-24): the §7/factual-fabrication fence is LIFTED (cleared 2026-06-13 — it grounds in the `sources` MCP and abstains "NO SOURCE"), and its pedagogy/CEFR review is strong — it LED the 2026-06-24 practice-hub panel. **Metered** → be cost-aware, but do NOT under-use it where it's strong. NOT for cross-file architecture / security-concurrency / auth-heavy git / mass-mechanical (→ codex/claude). Caveat: agy `--data` truncates large/binary attachments → paste trimmed content or use codex `--data`. |
| Ukrainian CONTENT (authoring · russicism/quality review) — **we AUTHOR UK content, we do NOT translate EN→UK** | Written in Ukrainian, immersion-first, grounded in VESUM/`sources` MCP. **Per-profile authoring — BAKEOFF-BACKED (2026-07-04, `audit/2026-07-04-uk-writing-probe/`, deterministic VESUM + russian-shadow, 5 candidates):** all of codex (gpt-5.6-terra default; 5.5 retained for pinned workflows)/agy/claude/deepseek/cursor wrote **0-russicism, 95-100%-VESUM** content on all 3 profiles → **gpt-5.5 is not uniquely best; it can and should delegate.** A1-A2 English-support → **agy** (best immersion teaching-voice) ≈ **codex**; B1-C2 pure → **codex ≈ agy ≈ claude**. **Seminars — FACT-CHECKED (2026-07-04, `audit/2026-07-04-uk-writing-probe/SEMINAR-SCORECARD.md`; tool-backed vs uk.wikipedia + VESUM, cross-verified by an independent 3-family review codex/agy/deepseek):** the probe can't rank seminar content (all clean), so the «Веснянки» sample was fact-verified. **Writers → codex + claude + agy** (all factually clean, mutually cross-family). **deepseek + cursor are NOT seminar writers:** deepseek made 1 hard error (царинні conflated with юр'ївські cattle-drive songs — confident scholarly specificity that was wrong; it conceded on review), cursor made 2 (веснянки «від хати до хати» = over-generalised риндзівки/волочебні; «мелодії легкі, м'які, співочі» = inverted musicology). **Seminar review → deepseek (+ agy)** for **non-folk** seminars, **always paired with a source-enforced fact-check gate** (`seminar-content-review` skill + `sources` MCP) — never a bare LLM pass. ⚠️ **FOLK carve-out (hard): NO deepseek for folk** (see the module-content panel note + `docs/folk-epic/folk-review-rubric.md`) — the царинні slip is fresh proof. **Lesson: "sounds scholarly" ≠ "is accurate" — verify confident specificity, don't trust it.** **Review (russicism/surzhyk/CEFR):** deepseek-v4-pro + `sources` MCP (`verify_words`, `check_russian_shadow`, `query_cefr_level`); agy also strong. ⚠️ **cursor**: usable UK but emits non-canonical apostrophes (U+2019) + had a text-dependent russicism («перекатні») on harder text → keep a VESUM + apostrophe-normalization gate; not the first pick. **Never pool/glm for UK content** (code models — glm anglicizes, pool worse). |
| Adversarial review of design / ADR / architecture / code — the **Claude reviewer seat** | **Prefer IN-SESSION INLINE for cost** — the interactive orchestrator reads the artifact, verifies claims, writes the verdict + fix notes on the main quota (cheapest path; economics below). Dispatching Claude (`claude -p` / `--agent claude` / `review-deep` / an `Agent` review subagent) **is permitted when it adds value or inline isn't feasible** — the `-p` sunset was cancelled (user 2026-06-22). For routine reviews still prefer inline or a non-Claude lane; reserve dispatched Claude for catches that need it. Context heavy → DEFER to the next interactive session, or dispatch if it must clear now. |
| Q&A or single-shot review without commit | `ab ask-codex` / `ab ask-agy --to-model gemini-3.5-flash-high` for routine, `--to-model gemini-3.1-pro-high` only for deep (gemini-cli retired → agy) |
| Live web fact-check (current version / pricing / URL & citation currency, "is this API still live") | **opencode + lightpanda-MCP HARNESS capability — any opencode-hosted model browses** (kubedojo-verified incl. deepseek); it is NOT model-specific. Route by fit: `ab ask-pool` (poolside.ai, **free**) · `ab ask-glm` (⚠️ LOCAL-ONLY, China-egress) · or an opencode-hosted deepseek. |
| Search / grep / "find me X" across files | `Agent` tool with `subagent_type: Explore`, `model: "haiku"` |
| Status check on running dispatches | Monitor API curl, never inline file scans |

If I'm about to write code inline and it doesn't match row 1, STOP and dispatch instead. Tooling enforces (worktree + commits) — memory does not.

**Use agy more (user 2026-06-24):** route content / wiki / pedagogy / factual **review** + bounded scripts / fixtures / migrations / docs-near-code to **agy** by default — its §7-fabrication fence is lifted (cleared 2026-06-13) and its pedagogy/CEFR review is strong (it led the 2026-06-24 practice-hub panel). It is **metered**, so be cost-aware, not absent — don't under-use it where it's strong. Keep cross-file architecture / security-concurrency / auth-heavy git / mass-mechanical on codex/claude. Confirm its model via `ab check-model` / `--help` (changes often; the bridge labels it Gemini-3.5-Flash-High, panels route `--to-model gemini-3.1-pro-high`).

**Writer routing refinement (user-confirmed 2026-07-07):** general content writing runs on **codex + agy** (agy = the standout A1-A2 immersion teaching voice per the 2026-07-04 bakeoff — do not forget it exists); the Claude window is SAVED for judgment work (architecture, adversarial review, hard bugs — codex is the primary coder, not Claude). The **V7 PIPELINE writer seat is separate**: it stays `claude-tools` because that seat is in-harness TOOL-CALLING fit, not prose (codex-tools emitted `tool_calls=0`); after any Claude-model rotation, spot-check ONE module before the next batch.

**CodexBar / routing-budget (live 2026-07-07):** `/api/state/routing-budget` + `delegate --check-budget` = the never-trip window check for SUBSCRIPTION lanes (claude/codex/gemini/cursor/**grok**) — consult before big fanouts. **grok is a SUBSCRIPTION lane (xAI sub, user-corrected 2026-07-07), NOT API-billed** — it appears in the CodexBar snapshot (5h window) and `grok-build` (native CLI) is the seat to use for coding + adversarial review; grok-4.5 is the only live Grok model. (xAI catalog rotation 2026-07-15; grok-4.5 re-won the bakeoff, #5197) API-billed lanes (deepseek/openrouter) are absent from CodexBar BY DESIGN (the user tracks dollar spend himself): **absence from the snapshot ≠ unavailable** — route them freely by quality fit. Any ranked-headroom view must treat absent lanes as unmetered (constraint pinned on #4640). **Deficit routing (pace > 1× of the weekly window): shed work from the over-pace lanes to the FULL relief roster — agy / grok-build / cursor (coding dispatches) · deepseek (dirt-cheap API: execution via hermes + the default review seat) · glm (idle Zhipu sub — standing slice of off-seat deep/security review, LOCAL-ONLY guard unchanged) · gemma (cheap surface review). Don't forget the cheap lanes exist (user reminder 2026-07-07).**

## Fleet topology — orchestrator · advisor · workers (user directive 2026-07-11)

Standing role assignment for orchestrated sessions (names rotate; route by the role, not the label):

- **Orchestrator = the interactive Claude seat (`claude-infra`).** Owns the loop: prioritize, delegate,
  decide, review in-the-loop, merge in-lane. Drive the high-judgment work in-context, but do **not** run
  worker-level implementation on the orchestrator seat — delegate it (>50 LOC non-test, mechanical,
  fixtures, or anything parallelizable → a worker). "Make good use of them" (user).
- **Advisor = `gpt-5.6-sol` @ `xhigh` (on-demand, NOT a standing worker).** Convene for the hard,
  high-judgment calls only: architecture, high-stakes design/spec/ADR review, difficult debugging, final
  synthesis. Consult BEFORE committing a substantive design; do not use for routine work.
- **Workers = every other lane** — `gpt-5.6-terra` + `gpt-5.6-luna` (make active use of BOTH), `agy`,
  `cursor`, `grok-build`, `deepseek`, `pool`, `gemma`, `glm` (LOCAL-ONLY). They do the build /
  implementation / mechanical / review work. Keep lanes busy; queue rather than idle.

This names who orchestrates vs advises vs works. The cross-family review gate, the per-task routing rows
above, and the GPT-5.6 Sol/Terra/Luna row below are unchanged — this is the standing topology over them.

### Worker priority ladder — first pick per work type (user standing order 2026-07-11: stop re-deriving this)

Route by FIT, then shed from HOT lanes — consult **CodexBar** `/api/state/routing-budget` (+ `delegate --check-budget`) before any fanout. Live 2026-07-11: **claude 82% HOT (~1d to reset) → push load off the orchestrator seat to codex (89% free) + the cheap lanes.** Each lane's full strengths/caveats live in the per-task table + panel notes; this is the consolidated ranking.

| Work type | 1st pick | 2nd | 3rd | gate / never |
|---|---|---|---|---|
| **Coding / impl / fixtures** | **codex** — `terra` default · `luna` = fast-bounded | **agy** — bounded scripts, docs-near-code | cursor · grok-build | claude seat = only ≤5-LOC CI-fix-I-caused; luna never sole authority |
| **Code review** (cross-family = outside author's family) | **deepseek-v4-flash** — cheap, A+ fast (ALWAYS `--silence-timeout`) | **grok-build** — sharpest gate + deepseek stall-failover | pool (FREE) · glm (LOCAL: security + big-context coherence) | codex = same family as Sol/terra/luna; claude seat = prefer inline |
| **UK content authoring** (author immersion-first, never translate) | **agy** (A1–A2 voice) ≈ **codex** | **claude** (B1–C2, sparingly — save the window) | — | NO deepseek for FOLK; cursor apostrophe/russicism gate; never pool/glm/gemma-sole |
| **Content / factual / CEFR review** (VESUM-gated) | **deepseek-v4-pro** (+ `sources` MCP) | **agy** (pedagogy/CEFR) | **gemma** (cheap surface: russicism/calque/Latin-leak/decolonization) | NO deepseek for FOLK; gemma not sole factual/seminar reviewer |
| **Research / recon / triage** | **luna** (fast bounded) | Explore-haiku (grep/find) | terra (deeper) | luna never sole authority on consequential calls |
| **Live web fact-check** (pricing/URL/citation currency) | any opencode model — pool (FREE) · glm (LOCAL) · deepseek | — | — | browsing = harness property, not a model trait |

**Advisor (on-demand, HARD calls only): `gpt-5.6-sol @ high–max`** — architecture, high-stakes design/ADR review, difficult debugging, final synthesis. Convene BEFORE committing a substantive design; never for routine. **Excluded:** qwen (cost). **LOCAL-ONLY:** glm (China-egress, never CI). **Cross-family review gate holds:** the reviewer must be outside the author's model family.

## Fleet discussion panels — actively involve ≥1 other agent before committing (user order 2026-06-23)

Drive high-judgment work (design, architecture, in-the-loop review, brief authoring) YOURSELF in-context — the frontier Claude lane does not brain-rot in-session (canary-verified on Opus 4.8; Fable 5 improvised 10/10 @ ~500K/1M 2026-07-07; a NEWLY rotated model must mint its own canary at cold-start per workflow.md — rot evidence is per-model, names rotate). But for any SUBSTANTIVE design / decision, **actively DISCUSS + cross-verify with the fleet BEFORE committing** — not solo dispatch-and-merge. Default to ≥1 other agent per substantive task; solo only for trivial work. Convene by lane:

- **Module-content panel** (writers, content review): **agy** (gemini-pro) · **gpt-5.5** (codex, `--effort xhigh`) · **cursor** (composer-2.5). Prefer a bake-off + cross-family verification. Folk content review stays **cross-family (GPT↔Claude)** per `docs/folk-epic/folk-review-rubric.md` — **NO DeepSeek for folk culture** (lacks intrinsic Ukrainian-culture knowledge).
- **Infra panel** (code, gates, pipeline, tooling, schemas, Atlas/lexicon): **agy** · **gpt-5.5** (codex) · **cursor** (auto) · **grok-build** · **deepseek-v4-pro** (code review) · **pool** (poolside.ai `laguna-m.1`, **free** — cross-family code review + live web fact-check, `ask-pool`) · **glm** (Zhipu `glm-5.2` — deep security/bug review + large-context cross-file coherence audits, `ask-glm`; ⚠️ China-hosted → **LOCAL-ONLY, never CI**) · **gemma** (Google Gemma 4 via **`google-ais/gemma-4-31b-it` — $0 default**, user key + order 2026-07-07: AIS-direct, Gemma has NO paid SKU on the Gemini API (triple-verified: pricing page · opencode cost:0 · guard) — runs TOOLLESS (`chat` agent); PAID OR `-it` ~$0.12/$0.35 per M tok via explicit `--model` fallback (OR `:free` is pool-starved, avoid); guard refuses `google-ais/` non-gemma ids (postpay project — Gemini WOULD bill) — cheap surface review + source-constrained wiki drafting, `ask-gemma`; ⚠️ **NOT a sole seminar writer or factual reviewer** — gate seminar/factual work behind a non-Gemma check; Google-family so not a clean reviewer of agy/Gemini work).

Invocation (`scripts/ai_agent_bridge/__main__.py`): `ask-codex` · `ask-agy --to-model gemini-3.1-pro-high` · `ask-cursor --model auto` (or `--model composer-2.5`) · `ask-grok-build` · `ask-pool [--variant high|max]` · `ask-glm` (LOCAL-ONLY) · `ask-gemma` (cheap; ⚠️ not a sole seminar writer / factual reviewer) · `discuss <channel> "<topic>" --with <a,b,c>` for a bounded multi-round. **deepseek has NO `ask-*`** — route it via `delegate.py dispatch --agent deepseek --model deepseek-v4-pro` (first-party by default; `--provider openrouter` for opt-in per #4358). Bridge `ask-*` replies arrive as INBOX MESSAGES (`ab read <id>`), not stdout.

**opencode-routed cross-family reviewers (pool · glm · gemma):** opencode is a multi-provider ROUTER — the fleet member is the MODEL, not "opencode" (`ask-opencode <model>` is the generic escape hatch; `ask-pool`/`ask-glm`/`ask-gemma` are the named members). **Live web fact-checking is a HARNESS property (opencode + lightpanda MCP), NOT a model trait — any opencode-hosted model browses** (kubedojo-verified incl. deepseek); don't treat it as unique to pool/glm. Since the coding floor is uniformly high across the fleet, route by the DIFFERENTIATOR (kubedojo 5-agent scorecard 2026-07-04): **pool** = **free** cross-family code review + web-verify *volume*; **glm** = deep security/bug review + **large-context cross-file coherence audits**; grok-build = sharpest final code-review gate; deepseek = cheap all-rounder (+ browses when opencode-hosted); **gemma** (Google Gemma 4 via **`google-ais/gemma-4-31b-it`, $0 DEFAULT** — AIS-direct with the user's key, no paid SKU exists for Gemma on the Gemini API; TOOLLESS `chat` agent; paid OR `-it` via `--model` fallback only, note the spend; OR `:free` pool-starved, avoid) = a metered-lane OFFLOAD for **(a) cheap SURFACE review** — reliably flags russicisms/calques, Latin-letter leakage, imperial/decolonization framing — and **(b) SOURCE-CONSTRAINED wiki drafting** — with a full source packet it cites every factual sentence and invents no sources (user probes 2026-07-05, `docs/projects/ua-eval-harness/model-evidence.md`). ⚠️ it is **NOT a sole seminar writer** (adds unsupported details beyond the source packet) and **NOT a sole factual reviewer** (not trustworthy on accuracy yet) — gate seminar/factual work behind a **non-Gemma** source/factual check; Google-family → not a clean reviewer of agy/Gemini work. **pool and glm are NOT for Ukrainian content / prose / pedagogy** — both are code models (glm anglicizes/code-switches, pool is worse); for UK content see the "Ukrainian CONTENT" row above (we author, not translate; cursor is NOT russicism-safe on long UK text). **pool** = poolside.ai `laguna-m.1`, **free** (watch weekly limits on bursts). ⚠️ **glm** = Zhipu `glm-5.2`, **China-hosted (Zhipu/z.ai) → prompt data egresses to China → LOCAL-ONLY: never in CI / automated pipelines or with sensitive data** (`ask-glm` refuses under any CI env var as a backstop); prefer a Western-lab reviewer for top-stakes. Bridge (consult/review) only today — no `delegate.py --agent pool|glm|gemma` dispatch adapter yet, and no V7 `--writer gemma-tools` yet (the opencode→delegate adapter + tool-calling writer harness are scoped follow-ups; a plain OpenRouter chat model has no `sources`-MCP harness).

## Harness vs model — route by BOTH (added 2026-07-05; user order: fleet utilization is paramount)

A fleet member = MODEL × HARNESS. The same model behaves differently in different harnesses, and
several models are reachable through more than one. Know both axes before routing:

| Harness | What it adds to ANY model it hosts | Models reachable through it | Entry points¹ |
|---|---|---|---|
| **hermes** (v0.18.x — full agent platform, NOT a thin wrapper) | SOUL.md project persona · `sources` MCP (30+ UK tools) auto-attached · 16 built-in toolsets (web, browser, terminal, code-exec, files, delegation, cron, session-search…) · session store w/ FTS5 search · agent loop up to 90 turns | deepseek (API key) · gpt-5.5 (codex OAuth) · grok (xai OAuth) · zai/GLM (API key — ⚠️ same China-egress LOCAL-ONLY rule as opencode glm) · OpenRouter catalog (qwen², gemma, …) — probe `hermes auth list` | `ab ask-hermes --model <m>` (one-shot Q&A/review) · `delegate.py dispatch --agent deepseek\|grok\|qwen² --mode danger --worktree` (execution — worktree MANDATORY per delegate-must-use-worktree) · V7 `--writer/--reviewer grok-tools\|deepseek-tools\|qwen-tools` (all hermes-backed) |
| **opencode** (multi-provider router) | lightpanda MCP configured (`~/.config/opencode/opencode.jsonc`) → **live web browsing/fact-check is a HARNESS property here**, available to tool-capable hosted models (kubedojo-verified for pool·glm·deepseek routes; verify before relying on a new route) | pool (poolside laguna-m.1, free) · glm (⚠️ LOCAL-ONLY) · gemma · deepseek-direct (first-party `api.deepseek.com`; #4358/#4626 QG bakeoff default) · OpenRouter deepseek/gemma baselines · any OpenRouter model | `ab ask-pool` / `ask-glm` / `ask-gemma` (named) · `ab ask-opencode <model>` (generic) |
| **native CLIs** (codex, cursor, agy, grok-build, claude) | each CLI's own tool loop + repo context; capabilities differ per CLI. grok-build = the NATIVE grok CLI lane; plain `--agent grok` routes via hermes (row above) | one primary family each | `ab ask-codex` / `ask-cursor` / `ask-agy` / `ask-grok-build` / `ask-claude` · `delegate.py dispatch --agent <a> --mode danger --worktree` |

¹ `ab` = the user's shell alias for `.venv/bin/python scripts/ai_agent_bridge/__main__.py`.
In scripts, docs meant for copy-paste, and anything automated, ALWAYS write the full path —
bare `ab` resolves to ApacheBench (`/usr/sbin/ab`) outside the user's shell (AGENTS.md rule).
There is NO `ask-deepseek`: one-shot deepseek = `ask-hermes --model <deepseek-model>` (first-party
as attributed on 2026-07-07) or `ask-opencode deepseek-direct/<deepseek-model>`; execution =
`delegate.py dispatch --agent deepseek`. `openrouter/deepseek/*` is **guard-REFUSED** (user order
2026-07-07 — the OR account was drained by deepseek bakeoff cells; deepseek runs FIRST-PARTY only.
The user's OR BYOK now bills deepseek underneath, so transport-comparison runs (#4321/#4358) are
billing-safe behind `LU_ROUTING_GUARD_OVERRIDE=1` — deliberate, user-authorized only).
² qwen is reachable but EXCLUDED from routine routing (cost, user 2026-05-29) — reachable ≠ routable.

Consequences:
- **A model "lacking" a capability may just be in the wrong harness** — deepseek can't browse
  natively but browses via opencode; any hermes-hosted model gets VESUM/`sources` tools for free.
- **Limits are per-harness-credential, not per-model**: when a lane quotas out, the same model is
  often reachable through another harness (e.g. gpt-5.5 native codex CLI ↔ hermes codex-OAuth;
  deepseek via delegate-hermes ↔ opencode). Check `hermes auth list` + `/api/orient` headroom.
  For Claude/Codex budget buckets at `near_cap`, substitute per
  `scripts/config/agent_fallback_substitutions.yaml` (that file is the budget-bucket map, not a
  general outage map). ALWAYS note a substitution in the artifact — silent rerouting hides
  review-independence, cost, and egress changes.
- **Hermes is also an automation platform** (cron, kanban, insights, session FTS, gateway,
  openai-compat proxy) — study + adoption plan: `docs/references/private/hermes-usage.md`
  § Automation adoption plan (gitignored machine-local doc — operator OPSEC policy 2026-07-05;
  tracked stub at `docs/best-practices/hermes-usage.md`). Prefer harness-level automation over
  hand-rolled polling where it fits.

**Model names here are current-as-of-2026-06-23 EXAMPLES, not constants** — grok-build, cursor, agy, hermes change CLIs/flags/models often. Confirm current capability via this file, `docs/best-practices/agent-activity-matrix.md`, `ab check-model`, the agent's `--help`, or `docs/agent-runtime-guide.md` before relying on a specific string. Worked example: the 2026-06-23 Atlas warning-taxonomy plan — a 3-agent panel (codex, agy-pro, cursor) caught real defects no single seat saw.

## GPT-5.6 family (Sol · Terra · Luna) — onboarded 2026-07-09 (user directive)

All three tiers: **372K context (~353K effectively usable** before the context-management margin), text+image input. Tier choice = capability/cost routing, NEVER context. Effort levels apply on every tier.

| Tier | Model id | Use for | Effort policy |
| --- | --- | --- | --- |
| Sol | `gpt-5.6-sol` | Frontier lead: hard architecture, high-stakes advisory/review, difficult debugging, final synthesis | **FLOOR = `high`** (user 2026-07-09: never dispatch Sol below high); `high`–`max` |
| Terra | `gpt-5.6-terra` | Balanced default: normal implementation, scoped planning, investigations, standard reviews (≈5.5-level quality, cheaper) | default `high`; `xhigh` for the hardest cells |
| Luna | `gpt-5.6-luna` | Fast bounded worker: recon, test/log triage, mechanical checks, draft summaries. **NEVER sole authority** on consequential decisions or release approval | `medium` default |

Policy: **prefer 5.6 for NEW work**; retain 5.5/5.4 only for pinned workflows (qg_bakeoff arms, the V7 pipeline reviewer seat until spot-checked post-reset), proven compatibility, or quota pressure. Codex dispatch + `ask-codex` defaults = `gpt-5.6-terra`.

Probe evidence (2026-07-09): `luna@medium` QG 69-item triage PASS (69/69 processed, 5/5 spot-verified verdicts, 160s); `sol@xhigh` (Layer B design) + `terra@high` (#4824 fix) probes ran same day; Sonnet-5-vs-Terra and Haiku-4.5-vs-Luna matched pairs queued for the 07-13 claude reset.

Anthropic tier mapping for cross-family routing: Sol ≈ Fable 5 / Opus 4.8 · Terra ≈ Sonnet 5 · Luna ≈ Haiku 4.5. Claude lanes keep the 1M-context edge — route giant-context work (cross-file coherence audits, corpus reads) to Claude/gemini, not 5.6.

## Claude reviewer-seat economics (2026-06-12)

There is ONE Claude Code quota. A dispatched / headless / subagent Claude competes with the interactive
orchestrator's own seat, AND a subagent starts a fresh context that **reloads the full project (~2–3M tokens,
~1000:1 overhead per the global `code-editing-safety` §7 rule)** to return a verdict that inline costs
~15–25k. A subagent therefore *duplicates a session boot you pay for anyway* → ~50–150× the tokens for the
identical verdict. So **prefer** fulfilling the Claude reviewer seat IN-SESSION (dispatching Claude is
permitted — the `-p` sunset was cancelled, user 2026-06-22 — but it costs the multiple above, so route by need):

1. **Default: review INLINE, early in the session** while context is light — cheapest, full faculties, and you
   reuse the read to write the fix.
2. **Context heavy + a Claude review is still needed: DEFER** to the next MANUAL interactive session's start
   (record a top-of-handoff `Claude review PENDING: <artifact>` so cold-start picks it up first). That
   artifact's merge waits one session. Prefer this over cramming it into a depleted session or spawning a
   subagent (cost) — though dispatch IS available when the review must clear now.
3. **Inline-now despite heavy context** only when latency is unacceptable (the review must clear THIS session
   to unblock something).

Non-Claude reviewers are UNAFFECTED — keep routing the bulk of reviews to them: DeepSeek (rows above) for PR
diffs + VESUM content review, Codex for novel-architecture catches. The *Claude* seat is **preferred** in-session for cost.
(The headless `--agent claude` / `claude -p` lane is AVAILABLE again — the mid-June 2026 sunset / "native binary not
installed" fiasco was cancelled, user 2026-06-22; Claude may be used for ANY task, incl. dispatched review, when needed.
The cost economics above stand regardless: dispatched Claude is far pricier than inline, so route by need, not by ban.)

The same table lives in `memory/MEMORY.md` rule #M0; this file is the deploy-rule mirror so it loads via `npm run agents:deploy` into `.claude/rules/`.

</critical>
