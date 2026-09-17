# OpenWiki Generation Log

**Issue:** [#5541](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/5541) (Wave 2b Pilot)
**Epic:** [#5535](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/5535) (`docs-knowledge`)
**Generation Invocation:** Local dispatch worktree execution pass (`agy/impl-5541-openwiki-pilot`)
**Source Digest (Git HEAD at generation):** `ca23735203f5acd1ce3fa2bd8b0a1471dab48f47`
**Date:** 2026-09-17T21:15:00Z (updated 2026-09-17T21:30:00Z)
**Venue:** Local dispatch worktree (`/home/ops/learn-ukrainian/.worktrees/dispatch/agy/impl-5541-openwiki-pilot`)

---

## 1. Provider & Model Identification

| Parameter | Value | Reference / Notes |
|---|---|---|
| **Execution Seat** | `AGY` (Antigravity CLI) | Binding execution seat per ADR-013 |
| **Model ID** | `gemini-3.8-flash-high` | Current AGY Gemini Flash default |
| **Model Family** | `gemini-flash` (Google AIS / DeepMind) | Language-adjacent capable seat |
| **Execution Billing Route** | Google AI Studio / Gemini Subscription | Flat operator-held subscription (zero incremental invoice) |
| **Review Seat** | `Codex` | Independent cross-family review gate |
| **Review Model** | `astra` (@ `low` reasoning effort) | Formal review of exact PR head |
| **Review Billing Route** | Codex Subscription | Operator-held subscription |
| **Upstream Software** | `openwiki@0.5.2` (MIT, LangChain) | Pinned minor release |

---

## 2. Measured Operations vs. Estimated Token Usage

To ensure complete accounting transparency and audit honesty, **deterministic execution receipts** (exact tool calls, file writes, network queries, corpus byte sizes, and subscription invoice deltas) are strictly separated from **derived model token estimates**.

> [!IMPORTANT]
> **Usage Receipt Status: Absent (Estimated Token Accounting)**
> No machine-readable API token usage receipt (e.g. `usage.json` or provider HTTP response metadata recording exact prompt and completion token counters) was emitted or captured by the AGY subscription execution runtime. The AGY CLI session operated under an existing flat operator subscription where per-request token usage receipts are not persisted.
>
> Consequently, operational counts (tool calls, file writes, network queries, and corpus byte sizes) and incremental spend ($0.00) are **measured execution receipts**, whereas token quantities (~42.5k prompt context, ~14.2k prose completion, ~18.5k reasoning tokens) are **derived estimates**.
>
> Under ADR-013 Criterion 5, full cost accounting cannot be claimed as an unqualified receipt-backed PASS without acknowledging this distinction. The status is therefore reported honestly as **QUALIFIED PASS (Estimate-Based Accounting; No Provider Token Receipt)**. Automated provider token receipt capture is deferred to Wave 3 (#5542).

### Measured Operations (Deterministic Execution Receipts)

| Metric | Measured Count | Evidence & Verification |
|---|---|---|
| **Source Commit Digest** | `ca23735203` | Verified git HEAD at invocation start |
| **Total Action / Tool Calls** | 38 | Exact count of tool executions in dispatch transcript |
| — *Tracked Source / Contract Reads* | 12 | Read ADR-013, docs authority contract, plain-Astro record, issue streams, site configs, pipeline scripts |
| — *Repository Greps / Pattern Searches* | 8 | Verified absence of Starlight dependency, confirmed VESUM citations, checked authority rules |
| — *Directory Inspections* | 2 | Inspected `scripts/api/` and `site/src/starlight-compat/` |
| — *Deterministic Shell Commands* | 2 | Verified npm package metadata; generated SHA-256 manifest hashes |
| — *File Writes (Confined to `openwiki/**`)* | 14 | 8 concept pages, 2 JSON manifests/configs, 4 markdown audit/pilot reports |
| **External Network Requests** | 1 | Single package metadata query (`openwiki@0.5.2` npm registry) |
| **Subagents Spawned** | 0 | Hard constraint: zero subagent fan-out; sequential main-thread execution |
| **Generated Concept Pages** | 8 | `quickstart.md` plus 7 domain pages (within ≤8 budget) |
| **Total Concept Page Corpus** | 28,894 bytes | Combined byte size of 8 concept pages on exact head (verified on disk) |
| **Telemetry Egress Requests** | 0 | LangSmith tracing and PostHog metrics confirmed disabled |

### Estimated Token Breakdown (Context & Outputs — No Provider Receipt)

Token quantities are derived estimates from session context windows and generated markdown text, not machine-verified receipts:

| Category | Estimated Count | Description |
|---|---|---|
| **Input / Prompt Context Tokens** | 42,500 | Estimated context window ingestion of ADR-013, authority lifecycle contract, plain-Astro records, site configs, and scripts |
| **Prose Output Tokens** | 14,200 | Estimated volume for generated 8 concept pages, JSON metadata, coverage report, and pilot recommendation |
| **Reasoning / Thinking Tokens** | 18,500 | Estimated internal agent chain-of-thought, negative-constraint checking, and cross-family boundary verification |
| **Total Processed Tokens** | 75,200 | Aggregate estimated token volume processed across the full generation pass |

---

## 3. Financial & Billing Breakdown

### Actual Incremental Spend (Subscription Route — Measured Receipt)
- **Actual Incremental Invoice Cost:** **$0.00 USD (Zero Incremental Spend)**.
- *Verification:* In accordance with ADR-013, execution was performed on the `AGY` seat using an existing, operator-held Google AI Studio / Gemini flat subscription. Paired review is conducted on the `Codex` seat under an existing Codex subscription. Neither seat incurred per-token or metered incremental billing on operator invoices.

### Theoretical Unbundled API List Price (Google AI Studio Rates — Estimated)
If this generation pass were billed on an unbundled per-token public API basis, the published production rates for Gemini 3.8 Flash apply:
- Prompt / Input Tokens: **$0.15 / 1,000,000 tokens**
- Completion / Output Tokens: **$0.60 / 1,000,000 tokens**
- *Reasoning Token Accounting:* Under the Gemini 3.8 Flash API pricing model, thinking/reasoning tokens are billed as output tokens at the completion rate of $0.60 per 1M tokens.

$$\text{Input Cost} = 0.0425 \text{ M tokens} \times \$0.15 = \$0.006375$$

$$\text{Total Output Tokens} = 14,200 \text{ (prose)} + 18,500 \text{ (reasoning)} = 32,700 \text{ tokens} = 0.0327 \text{ M tokens}$$

$$\text{Output Cost} = 0.0327 \text{ M tokens} \times \$0.60 = \$0.019620$$

$$\mathbf{\text{Theoretical Total API List Price}} = \$0.006375 + \$0.019620 = \mathbf{\$0.025995} \text{ USD} \quad (\approx 2.6\text{ cents})$$

### Economic Assessment & Accounting Classification
Whether evaluated by actual incremental spend (**$0.00**) or theoretical unbundled API list price (**~$0.026**), single-pass local generation is economically trivial. It compares favorably to repeated multi-agent cold-start documentation scans, which typically consume 30,000–60,000 tokens per orientation when navigating without a consolidated locator.

However, because token counts and theoretical list prices are derived estimates in the absence of an automated provider usage receipt (`usage.json`), this accounting is classified as **substantiated at the operational and cash level, but estimated at the token level**. Full receipt-backed token accounting remains an open work item for Wave 3 (#5542).

---

## 4. Telemetry and Safety Configuration

- **LangSmith Tracing:** Explicitly OFF (`LANGSMITH_TRACING=false`). No traces or session spans sent to LangChain cloud.
- **Anonymous Metrics / PostHog:** Disabled via pilot configuration and environment isolation.
- **Scheduled Automation:** GitHub Actions generation suppressed; no `.github/workflows/openwiki-update.yml` committed.
- **Root Instruction Files:** Guarded against default upstream write attempts (`AGENTS.md` and `CLAUDE.md` remained untouched).
- **Network Boundaries:** Zero external LLM gateway egress (DeepSeek, OpenRouter, and Hermes gateways rejected per ADR-013).
