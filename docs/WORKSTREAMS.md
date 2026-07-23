# Workstreams — V7 Pipeline Era

> **Living document.** Tiers + contents rotate. The *framework* (tier
> definitions, operating rhythm, KPI) is stable; the *contents* (which
> issues are in which tier) refresh whenever an issue closes, a bug is
> filed, or a build surfaces a new gap. Update on every session-handoff
> + on every PR that closes a Tier-1 item. **Stale tier rows are worse
> than missing ones — when in doubt, delete and let `gh issue list`
> be the source of truth.**

| Field | Value |
|---|---|
| **Last refreshed** | 2026-05-19 (post-B1-bakeoff, Hermes MCP fix + DeepSeek-pro xhigh validated) |
| **Refresh trigger** | Every session handoff, every Tier-1 issue close, every new build-surfaced bug |
| **KPI** | Curriculum modules passing audit per week |
| **Mission** | Full Ukrainian curriculum with decolonized pedagogy, real textbook grounding, RAG-verified vocabulary, adversarial review. Quality non-negotiable. |
| **Pipeline** | V7 (`scripts/build/v7_build.py` → `linear_pipeline.py`). V5/V6 obsolete, do not extend. |

---

## Streams = GitHub Epics (#4708 — supersedes hand-maintained tier rows for scheduling)

Scheduling now lives in GitHub stream epics; this doc keeps the framework and pillars.
The registry `scripts/config/issue_streams.yaml` is the single source of truth (auditor:
`scripts/orchestration/issue_stream_audit.py`; live view: `GET /api/issues/streams`).

| Stream | Epic(s) | Scope |
|---|---|---|
| atlas-practice | #4387 → #4700 | Word Atlas + Practice Hub product & UX |
| atlas-intake | #4220, #4378 | Full-corpus intake into the Atlas |
| corpus-channels | #4706 | Acquisition & ingestion (textbooks · ZNO · Ohoiko-media · press · academic) |
| infra-harness | #4707 | Infra, DevOps & fleet reliability (hooks, deps, dispatch, routing) |
| eval-harness | #4913 | UA eval harness: QG grounding/entailment gates, grammar-lexical gate, annotation, bakeoffs, cutovers |
| benchmark-2156 | #4639 | UA LLM factuality benchmark community release |
| core-quality | #4274 | Deterministic track audits + remediation (A1–B2) |
| seminars-folk | #2836 | FOLK re-research + rebuild |
| seminars-bio | #4431, #4215 | BIO readiness + builds |
| seminars-cross | #3120, #3079 | Cross-seminar gates |
| hramatka | #4542 | Teacher lesson service (user-gated) |

Rules for every orchestrator (Claude, Codex UI, agy, cursor): work from your stream epic;
link new issues to a stream at creation; orphans get flagged at every cold start.

---

## Three Quality Pillars

Every shipped module must pass all three:

| Pillar | What | How |
|---|---|---|
| **Structural** | Word count, activities, vocab, formatting, MDX render | Deterministic audit gates (`scripts/audit_module.py`, `python_qg.json`, `wiki_coverage_gate.py`) |
| **Linguistic** | VESUM-verified words, Russianisms/Surzhyk/calques/paronyms clean, citations resolve | MCP `sources` server (`mcp__sources__*` / `mcp_sources_*`) — verify_words, check_russian_shadow, verify_source_attribution, search_style_guide |
| **Pedagogical** | Tone, immersion balance, register, decolonization, sequence | Cross-agent reviewer (Codex per `pipeline.md`; DeepSeek-pro hermes for VESUM-backed content review per #M0) |

The reviewer-as-fixer rule (ADR-007): reviewer emits `<fixes>` find/replace pairs; pipeline applies deterministically. No LLM regeneration during review. Self-review forbidden (`SELF_REVIEW_DETECTED` gate enforces).

---

## Priority tiers (the operational framework)

Tier definitions are stable. Tier *membership* rotates — refresh per the rules above.

### Tier 1 — Unblocks lesson throughput (drive first)

Things that, when fixed, increase the number of modules passing audit per week. These get the orchestrator's foreground attention.

| Issue | Why it blocks throughput |
|---|---|
| Writer-MCP-invocation gap | If Hermes-routed writers (deepseek/qwen) don't actually invoke MCP at writer-time, the post-2026-06-15 routing has a quality hole. Investigation in flight; the m20+A2+B1 builds running 2026-05-19 will tell us. |
| **#2151** V7 preservation wrapper | Spec exists, impl missing — without it, parallel module builds don't archive consistently. Codex dispatch, ~2-3h. |
| **#1969** `resources_search_attempted=0` regression | Multimedia obligations not getting fulfilled — direct lesson-quality hit. ~1-2h. |
| **#1918** immersion gate tab-aware | Pedagogical accuracy on a load-bearing gate. Investigation first. |

### Tier 2 — Improves lesson quality (next)

These improve the QUALITY of modules passing audit, not the rate. Pick up when Tier 1 is empty or a Tier 1 dispatch is mid-flight.

- **#1940** `pedagogical_deviations_from_standard:` plan field (curriculum metadata)
- **#1916** Gate 4 Progressive Challenge needs `plan.targets` schema
- **#1914** Pass-2 scaffold tune for YELLOW contract test
- **#2039** grok-tools under-target (only matters if grok stays in routing rotation)

### Tier 3 — Data acquisition (parallel content track)

Don't block builds but cap content depth. Dispatch as background work when capacity exists. Gemini's lane (unmetered, "running existing pipelines").

- **#2054** paronyms NBU 1986 PDF OCR — needs OCR pipeline (currently used on ESUM)
- **#2053** Holovashchuk PDF 404 — needs alternate source
- **#2052** Karavansky scraper landing
- **#2048** R2U difficult-lexis (~5K rows) — script ready, data load pending
- **#1960** wiki external article placeholders → real URLs

### Tier 4 — Infra/CI noise reduction (when budget permits)

Doesn't ship lessons but reduces friction. Address opportunistically.

- **#2154** zizmor MEDIUM triage (DeepSeek-pro code dispatch in flight at time of writing)
- **#2126** review/review broken-env (saves 1 advisory-fail per PR going forward)
- **#2159** codex CLI silent-crash via runner — low priority; codex isn't the B1+ writer post-sunset routing anyway
- **#2134** codex silent-exit pattern — related to #2159
- **#2071** codex hangs with response_chars=0 — related to #2159
- **#1908** layered-harness audit
- **#1905** pipeline replay-mode regression suite
- **#1896** secret-leak prevention follow-ups (#M-5 recurrence backlog)
- **#2023** bridge claude --bare auth

### Tier 5 — Epics / meta (separate workstreams, don't compete for tactical time)

Long-running initiatives. Track in their own decision-card / RFC threads.

- **#1865** [EPIC] Context budget optimization (subscription-tier quota burn)
- **#2156** Project: UA calque + grammar eval harness (UNLP 2027 target)
- **#2132** [promote-protocol] Round 1 results — agent capability expansion
- **#2116** [research] claude-i tmux wrapper — post-2026-06-15 Claude lane
- **#2072** [follow-up] Grok integration — extend dispatch capabilities
- **#1933** [harness-engineering] /goal driver improvements
- **#2036** [hermes/auth] anthropic provider logout — Claude-via-Hermes empty stdout

---

## Operating rhythm

Per session (1-3h block):

1. **Cold-start** — orient via Monitor API + latest handoff (existing protocol, `claude_extensions/rules/workflow.md`).
2. **Pick a Tier-1 item + dispatch it** (Codex for mechanical-with-design-judgment, DeepSeek-pro for code+content quality, Gemini for routine pipeline runs per #M0).
3. **Build at least one curriculum module in parallel** (`v7_build.py --writer deepseek-tools --effort xhigh --worktree`) — validates pipeline AND adds to throughput.
4. **Sweep open PRs** — review + merge clean PRs (per #0H). Advisory CI fails (review/review per #2126, Gemini-Dispatch) don't block.
5. **Inline orchestration** while dispatches run — write briefs, file follow-up issues, autopsies, decision cards. Never sit idle waiting on watchers.
6. **Handoff at natural break** with full queue state — let the next session start oriented.

Weekly cadence:

- Modules built that pass audit (the KPI)
- Modules with reviewer-approved content
- Tier-1 issues closed
- New bugs surfaced + filed (signal, not noise — bugs found mean the pipeline is exercising itself)

---

## V7 Pipeline Architecture (current)

```
Plan (DRAFT→REVIEWED→LOCKED) →
  Knowledge packet (RAG sources via MCP) →
  Implementation map (seeded contract from wiki obligations) →
  Writer (claude-tools pre-sunset / deepseek-tools xhigh post-sunset) →
  Audit gates (python_qg) →
  Reviewer (cross-agent, no self-review) →
  Fix loop (deterministic find/replace from reviewer <fixes>) →
  MDX assembly
```

- **Writer policy**: claude-tools (Opus 4.7 xhigh) is current default. Post-2026-06-15 sunset → deepseek-tools effort=xhigh uniformly across A1/A2/B1+ per `scripts/config/agent_fallback_substitutions.yaml`. No tier splits, no "budget option" routing — quality non-negotiable.
- **Reviewer policy**: Codex primary per `claude_extensions/rules/pipeline.md`; DeepSeek-pro hermes for VESUM-backed content review (#M0). Cross-agent only (SELF_REVIEW_DETECTED enforces).
- **Wiki writer**: Gemini always (`scripts/wiki/compile.py --writer gemini`).
- **MCP source-of-truth**: `mcp__sources__*` (Claude/Codex convention) ↔ `mcp_sources_*` (Hermes/Gemini convention). Pipeline tolerates both (commits `0fc0f0d427` + `3aa830fa4f`).

---

## Content Status

Source of truth: `curl http://localhost:8765/api/orient | jq '.pipeline.summary'`. Numbers below are a periodic snapshot — refresh from API, do not edit inline.

Snapshot 2026-05-19:

| Track | Total | Research done | Content done | Audit passing |
|---|---:|---:|---:|---:|
| A1 | 55 | 0 | 0 | 0 |
| A2 | 69 | 0 | 0 | 0 |
| B1 | 94 | 0 | 0 | 0 |
| B2 | 93 | 0 | 0 | 0 |
| C1 | 132 | 0 | 0 | 0 |
| C2 | 110 | 0 | 0 | 0 |
| folk | 27 | 27 | 1 | 0 |
| (seminar tracks) | 1318 | 0 | 0 | 0 |

Wiki compilation: ~99% across most tracks (manifest in `curl /api/orient | jq '.wiki'`).

Active work this session: 3 V7 builds with deepseek-pro xhigh — a1/my-morning, a2/aspect-concept, b1/genitive-nuances. Results determine whether deepseek-pro xhigh + Hermes MCP fix gives audit-green modules end-to-end.

---

## Tracks (architecture)

- **l2-uk-en** (main): A1→C2 + seminar tracks (HIST, BIO, ISTORIO, LIT, OES, RUTH, lit-* subtracks, folk). Ukrainian for English speakers.
- **l2-uk-direct**: L1-agnostic Ukrainian (A1→B2). Separate schemas, no English. See `docs/l2-uk-direct/`.

Per-track architecture details: `docs/best-practices/track-architecture.md`.

---

## Deferred / parking lot

Labeled `priority:later` in issues. Will revisit after CORE A1-B2 tracks have shipped quantity. Do NOT mix into Tier 1-5 above without explicit re-prioritization.

- Seminar tracks beyond the existing manifest
- STEM domain tracks (#859 epic + children: IT, MED, BUS, LAW, etc.)
- PRO tracks activity framework (#429)
- Vocabulary progression audit (#705)
- Monolingual toggle for C1+ (#676)
- ZNO exam dataset (#715)
- RAG source expansion (#854)
- Monolingual lexicon builder (#634)

---

## When to refresh this document

| Trigger | Action |
|---|---|
| A Tier-1 issue closes | Move it out + promote next-most-important Tier-2 in |
| New bug surfaces a Tier-1-level blocker | Add it to Tier 1 immediately |
| A pipeline architecture change lands | Update §V7 Pipeline Architecture section |
| Routing config changes | Cross-reference `agent_fallback_substitutions.yaml` change in §V7 Pipeline Architecture |
| Quarterly | Audit Tier 5 — initiatives that have stalled get moved to deferred or closed |

The framework rows (tier definitions, operating rhythm, KPI, pillars) almost never change. The contents under each tier change every few sessions. **Don't be precious about edits — staleness is the actual failure mode.**
