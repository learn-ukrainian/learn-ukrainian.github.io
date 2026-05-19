---
date: 2026-05-19
session: "Multi-agent routing audit shipped (REPORT.html, 788 lines) + #2148 γ landed (22% → 67% wiki coverage) + zizmor adopted (5 HIGH fixed) + CoT-architecture 3-agent consensus reached"
status: green
main_sha: be4c3c7afc
main_green: true
working_tree_dirty: false
report_shipped:
  - "audit/2026-05-19-multi-agent-routing-assessment/REPORT.html (788 lines, shareable, all citations verified)"
  - "Plus 19 raw artifacts in raw/ subdir (4-agent routing + 7-model writer bakeoff + DeepSeek introspection + CoT discussion thread)"
report_gaps_to_close:
  - "kimi-k2.5 bakeoff (NOT YET RUN — original plan called for it then we picked k2.6 instead per latest-only rule, but user wants both k2.5 and k2.6 in v2)"
  - "kimi-k2.6 bakeoff (BLOCKED by Hermes nvidia-provider config drift — see Section 1 below)"
  - "minimax-m2.7 bakeoff (BLOCKED — same Hermes issue)"
  - "B1+ register bakeoff (DEFERRED to v3 report per user direction — not yet validated)"
prs_merged_this_session:
  - "#2153 (γ implementation, render implementation_map contract into V7 writer prompt)"
direct_commits_to_main:
  - "e63df4593b security(ci): SHA-pin actions/checkout in 2 gemini-* workflows (#2152 closed)"
  - "40a0d5ab8f docs(dispatch-brief): task #5 deepseek+qwen V7 writer wiring (pre-staged)"
  - "7a8c9e2af6 security(ci): adopt zizmor + SHA-pin run-gemini-cli (5 HIGH fixed, #2154 filed for 21 MED)"
  - "8797642d0e docs(decisions): resolve #2148 γ — move out of pending/"
  - "6d9a0d362b audit(m20-build-8): preserve forensics — γ delivered 22% → 67% coverage (#2155 filed)"
  - "be4c3c7afc audit(routing): multi-agent routing assessment + 7-model writer bakeoff + CoT consensus"
active_dispatches: []
issues_filed: ["#2153 PR merged", "#2154 zizmor MED triage", "#2155 wiki_coverage_gate semantic bug (absence-required vs substance-required bans)"]
tasks_carried_over:
  - "#8 Fix wiki_coverage_gate semantics: distinguish substance-required vs absence-required bans (high-leverage — would push m20 from 67% → 83%)"
  - "#9 Fix m20 l2_exposure_floor + inject_activity_ids gate failures"
  - "#11 Tighten writer prompt: re-frame plan_reasoning as visible contract deliverable — SUPERSEDED by 3-agent CoT consensus, see Section 2"
  - "#12 delegate.py wrapper blocks minimax/* + moonshotai/* — REFRAMED: actual root cause is Hermes config drift, see Section 1"
---

# Handoff — Routing audit shipped + 3 recovery tasks for v2 report

## TL;DR for the next session

This session shipped a comprehensive 788-line HTML routing audit report at `audit/2026-05-19-multi-agent-routing-assessment/REPORT.html` covering pricing (corrected), 4-agent peer review, 7-model writer bakeoff, DeepSeek introspection, and 3-agent CoT consensus. User saw the report and approved the direction. **User's mandate for the next session:** recover the kimi-k2.5, kimi-k2.6, and minimax-m2.7 bakeoffs that failed due to a Hermes config drift, fold them into a v2 report at the same path, and validate B1+ readiness for a future v3.

## ⚠️ FIRST ITEM NEXT SESSION — pending email reply from the native-speaker reviewer

**User said at session close 2026-05-19:** they have a reply from one of the project's native-speaker reviewers (referenced privately in `memory/MEMORY.md` per the personal-name-audit convention — name not committed). User will share the content of the reply at the start of the next session.

**Action for next orchestrator:** Before starting Section 1 (Hermes fix), ASK the user to share the reviewer's reply. Do not proceed with the recovery plan until you've seen and discussed it — it may change priorities, redirect to a different concern, or surface a domain-expert review that affects routing/curriculum decisions. Treat this as a blocking prerequisite for the recovery work.

Once you've read the reply: triage it against the carry-over tasks below, decide whether anything in it supersedes the v2-report plan, then proceed.

**Main is at `be4c3c7afc`, tree clean, 0 active dispatches, 0 open PRs of mine** (only dependabot's remain).

## Section 1 — The Hermes nvidia-provider config drift (P0 to fix)

### The bug

Three bakeoff dispatches failed identically:

```
RuntimeError: Provider 'nvidia' is set in config.yaml but no API key was found.
Set the NVIDIA_API_KEY environment variable, or switch to a different provider with `hermes model`.
```

Affected: `moonshotai/kimi-k2.6`, `minimax/minimax-m2.7`, and likely `moonshotai/kimi-k2.5` (untested but same routing path).

Both DELEGATE.PY dispatch (`--agent qwen --model moonshotai/kimi-k2.6`) AND DIRECT `hermes -z PROMPT -m moonshotai/kimi-k2.6` produce the same error. User verified that hermes ROUTES correctly to `minimax/minimax-m2.7` in interactive mode and confirmed "in kubedojo project those models work" — so the bug is project-specific.

### What we know about the config

`grep` of `~/.hermes/config.yaml` shows top-level:

```yaml
default: qwen/qwen3.6-plus
provider: openrouter
base_url: https://openrouter.ai/api/v1
providers: {}
fallback_providers: []
```

…BUT also has 7+ per-section entries with:

```yaml
provider: auto
base_url: ''
```

The `provider: auto` setting evidently routes `moonshotai/*` and `minimax/*` to NVIDIA (which is set somewhere in a config layer we haven't located yet). The auto-routing for `qwen/*`, `deepseek/*`, `inclusionai/*`, and `mistralai/*` correctly goes to OpenRouter — confirmed by the successful bakeoffs in this session.

### What the next session should do (in order)

1. **Read `~/.hermes/config.yaml` in full.** Find the section(s) that have `provider: auto` and the upstream Hermes routing rule that maps `moonshotai/*` to NVIDIA.

2. **Compare with kubedojo's Hermes config** if accessible. User confirmed these models work in that project — the diff is the fix.

3. **Two possible fixes:**
   - (a) Add an explicit per-vendor override forcing `provider: openrouter` for `moonshotai/*` and `minimax/*` in the config.
   - (b) Set `provider: openrouter` as the global fallback so `auto` defaults there when no explicit rule matches.

4. **Verify the fix** by running a quick smoke probe: `hermes -z "test" -m moonshotai/kimi-k2.6` should return a response, not the nvidia-key error.

5. **Once Hermes works for these vendors, re-fire the bakeoffs** (see Section 3).

### Closes task #12 with corrected scope

Task #12's original framing was "delegate.py wrapper blocks moonshotai/minimax." The actual root cause is Hermes provider drift; the delegate.py wrapper is a passthrough. Update the task description (already done in the task list mid-session) and resolve once the config fix lands.

---

## Section 2 — The CoT-removal opportunity (P0 implementation)

### What the 3-agent discussion concluded

Unanimous: visible chain-of-thought in V7 writer is **vestigial**. Empirical evidence: DeepSeek-v4-pro dropped all `<plan_reasoning>` + audit lines and produced the **highest-quality Ukrainian content** of any challenger in the writer bakeoff. The "CoT contract" was a tax on output budget that the downstream gates never parsed.

Specific verdicts (folded across Codex + Gemini + DeepSeek):

| Task | CoT verdict |
|---|---|
| V7 writer | REMOVE (prose fields); keep `implementation_map_audit` ONLY if a gate actually parses it |
| V7 module reviewer | OPTIONAL (cited findings only, no raw CoT) |
| Code review (PR diff) | REMOVE (2/3) |
| Content review w/ VESUM | REMOVE (deterministic checks suffice) |
| Q&A / one-shot | OPTIONAL (only when teaching a derivation) |
| Search / grep | REMOVE |
| **Adversarial ADR review** | **REQUIRED — unanimous** (the rationale IS the deliverable) |

Research citations all 3 agents independently surfaced (Wei 2022, Kojima 2022, Wang 2022, Lightman 2023, Turpin 2023, Lanham 2023, Nye 2021) are linked in the v1 report.

### Implementation task for next session

Edit `scripts/build/phases/linear-write.md`:

1. **Remove** the mandatory `<plan_reasoning>` requirement (the entire "Mandatory visible verification block" section at the top of the prompt). This drops the 6-field per-section requirement (word_budget, plan_vocab, register, teaching_sequence, verification_plan, verification_trace).
2. **Remove** the `<verification_trace>` requirement entirely — telemetry (`writer_tool_calls.json`) replaces it; the prompt's reference to it is already noted as tool-theatre risk at `linear_pipeline.py:2051`.
3. **Verify** whether `implementation_map_audit` is parsed by a gate. If yes, **keep** it. If not, **remove**.
4. **Verify** whether `bad_form_audit` is parsed by a gate. Same disposition rule.
5. **Add** the two prompt-clarity directives DeepSeek's introspection identified as universal failures across all writers tested:
   - "Emit fences as ```` ```module.md ````, NOT ```` ```markdown file=module.md ````."
   - "Use YAML in `activities.yaml`, `vocabulary.yaml`, `resources.yaml` blocks — never JSON. The pipeline's YAML parser will reject JSON content."
6. **Re-run m20 build #9** with the tightened prompt against `claude-tools` (baseline) and `deepseek-v4-pro` (challenger). If deepseek-v4-pro passes the gates AND keeps its content quality, promote it to V7 writer primary candidate **before the 2026-05-31 DeepSeek discount cliff** (would save $4-12K of curriculum-wide writer cost).

This supersedes task #11 (which was the narrower "tighten CoT framing" idea); the consensus is REMOVE not TIGHTEN.

### Dispatch target

Codex GPT-5.5 xhigh, ~1-2h. The brief should mirror PR #2153's shape: numbered execution steps + #M-4 evidence preamble + worktree + no auto-merge.

---

## Section 3 — Re-run the 3 failed bakeoffs (the v2 report's body)

### Models to test

After the Hermes fix in Section 1 lands:

| Model | Why include |
|---|---|
| **moonshotai/kimi-k2.5** | User explicitly wants the older Kimi variant alongside k2.6 — tests Kimi's generation gap within family, parallel to qwen3.6-plus vs qwen3-max test we already ran |
| **moonshotai/kimi-k2.6** | Latest Kimi; user-named in the kubedojo lineup as the "non-correlated errors vs Qwen" candidate |
| **minimax/minimax-m2.7** | Latest MiniMax mainstream; gives us a third non-Qwen Chinese vendor data point |

Cost estimate: ~$0.10 + $0.15 + $0.06 = ~$0.30 total. ETA ~10-15 min once Hermes works.

### Bakeoff procedure (same as v1 — DO NOT re-invent)

Use the existing prompt at `audit/2026-05-19-qwen-writer-bakeoff/writer_prompt.md` (the real m20 V7 writer prompt, 60K tokens). Same grading rubric as v1 §5:
- Output size (KB)
- `<plan_reasoning>` blocks count (target 4)
- Audit lines count (target 2)
- Fence syntax (will likely be wrong-syntax like every other challenger)
- YAML in `.yaml` blocks (will likely be JSON-in-YAML)
- Content quality assessment (immersion discipline, Ukrainian pedagogy, activity-id injection)

Save raw outputs to `audit/2026-05-19-multi-agent-routing-assessment/raw/` (the same dir the v1 report already references in its appendix). The artifact URLs in v1's appendix will automatically pick up the new files.

### How to expand the report

Open `audit/2026-05-19-multi-agent-routing-assessment/REPORT.html`:

1. **§5 Writer bakeoff table** — replace the 3 "BLOCKED by Hermes config issue" rows with the actual bakeoff verdicts. Use the same column structure (Output size, plan_reasoning, audit, fence, YAML, content quality, cost).
2. **§5 The "two universal failures" block** — re-verify with the new data; if kimi/minimax also have wrong-fence + JSON-in-YAML, the prompt-clarity bug is confirmed universal (currently 7 of 7 challengers). If they diverge, note the model-specific behavior.
3. **§9 Limitations table** — remove the "INFRA-BLOCKED" rows for kimi-k2.6 and minimax-m2.7 (replaced by real verdicts). Keep glm-5.1 latency-DQ as-is.
4. **§1 Executive summary findings** — update finding #4 (family diversity beats variant diversity) with kimi as additional cross-family evidence.
5. **§10 Appendix raw artifacts** — add the 3 new result file links (artifact API URLs).
6. **Header meta** — bump report date to next-session date; add "v2 — adds kimi/minimax recovery + Hermes fix" subtitle line.
7. **DO NOT** re-run the qwen/deepseek/ring/mistral/gemini/codex bakeoffs — they're complete and the data is on disk. The v1 report's verdicts for those rows stand.
8. **DO NOT** re-write sections 2 (Methodology), 3 (Pricing), 4 (Routing), 6 (DeepSeek introspection), 7 (CoT consensus). They're complete and load-bearing.

The v2 report is a TARGETED EXPANSION, not a rewrite.

---

## Section 4 — B1+ register readiness check (for v3)

### Current state

B1 plans EXIST on disk (`curriculum/l2-uk-en/plans/b1/*.yaml`, well-formed). Sample plan inspection (`adjectives-comparative.yaml`):
- `level: B1`
- `slug: adjectives-comparative`
- `sequence: 44`
- `word_target: 4000` (vs A1's 1200 — **3× larger output budget**)
- `phase: B1.4 [Порівняння та словотворення]`
- Has `content_outline`, `dialogue_situations`, `objectives`, `pedagogy`, `references`, `register`, `grammar` — same schema as A1 plans

### What's untested (the gating items for v3)

1. **Wiki manifest for B1 modules** — A1 modules have a wiki_manifest.json seeded by `build_wiki_manifest_data()`. Whether B1 plans have matching wiki content + a manifest path that resolves is UNKNOWN.
2. **Knowledge packet generation for B1** — V7 pipeline assembles a knowledge packet from textbook chunks. B1-level Ukrainian textbook coverage in `data/sources.db` is unverified for the modules we'd want to bakeoff.
3. **Implementation map seeding for B1** — Path 3 γ contract (`implementation_map.json`) is wired for A1. B1 modules using the same code path should work but hasn't been measured.
4. **Output budget at 4000 words** — 60K-token A1 prompts produced 25-70KB outputs in v1 bakeoffs. A 4000-word B1 module is ~10K tokens of OUTPUT alone, plus larger knowledge packet → easily 100-200K combined budget. Some models may hit context or output limits.

### v3 readiness validation (~30 min next-session work)

1. Render the writer prompt for ONE B1 module (e.g. `b1-baseline-past-present`):
   ```python
   from scripts.build.linear_pipeline import render_writer_prompt, build_wiki_manifest_data
   plan = yaml.safe_load(open('curriculum/l2-uk-en/plans/b1/...'))
   manifest_data = build_wiki_manifest_data(level='b1', slug=plan['slug'], plan=plan)
   # Confirm manifest data is non-empty + has obligations
   prompt = render_writer_prompt(plan=plan, plan_content=..., knowledge_packet=..., wiki_manifest=manifest_data)
   ```
2. If the prompt renders cleanly → fire a B1 bakeoff with the top 3 A1 performers (claude-tools baseline + deepseek-v4-pro + qwen-3.6-plus). ~$1-3 cost, ~15 min wall.
3. If it doesn't render → document the missing infrastructure in the v3 readiness section and defer to a future date.

### What the v2 report SAYS about B1+

Per user direction: state explicitly that **B1+ register (full Ukrainian) will be covered in a later report (v3)** with rationale: A1 register-precision findings do not transfer to B1+ register-relaxed automatically. The codex high-Ukrainian bias that hurt at A1 may BECOME a feature at B1+. Same for qwen / deepseek-pro register tuning. Per-level bakeoff is required; this audit covers A1 only.

Add to v2 report (suggested location: between §8 Recommendations and §9 Limitations, as a new "§8.5 B1+ register: deferred to v3" subsection).

---

## Section 5 — Carry-over task list

The user explicitly requested tasks carry over. The task IDs below are from the previous orchestrator session; numbers will change when the next session creates new tasks, but the WORK should be preserved.

| # | Status | Subject | Notes |
|---|---|---|---|
| 8 | pending | Fix wiki_coverage_gate semantics: distinguish substance-required vs absence-required bans (#2155) | Highest-leverage code fix in queue: would push m20 from 67% → 83% wiki coverage at no other cost. ~2-3h Codex dispatch. |
| 9 | pending | Fix m20 l2_exposure_floor + inject_activity_ids gate failures | Pre-existing m20 ship blockers, unrelated to γ. Decide writer-prompt fix vs plan revision. |
| 11 | SUPERSEDED | Tighten writer prompt CoT framing | Replaced by Section 2 above (REMOVE CoT, not TIGHTEN). The 3-agent consensus is decisive. |
| 12 | reframed | Hermes nvidia-provider config drift blocks moonshotai/minimax | See Section 1 above. Root cause is config, not delegate.py wrapper. |
| NEW | pending | Re-run kimi-k2.5 + kimi-k2.6 + minimax-m2.7 writer bakeoffs after Hermes fix | Section 3 above. ~$0.30 + ~15 min wall. |
| NEW | pending | Expand REPORT.html v1 → v2 with kimi/minimax data + Hermes-bug postmortem | Section 3.How-to. TARGETED EXPANSION not rewrite. |
| NEW | pending | Validate B1+ readiness (render B1 writer prompt, check manifest path) | Section 4 above. ~30 min. Gates v3 report. |
| NEW | pending | Implement P0 CoT removal in linear-write.md (3-agent consensus) | Section 2 above. ~1-2h Codex dispatch. Should land BEFORE 2026-05-31 DeepSeek discount cliff to unlock the writer rerouting. |

---

## Section 6 — Cold-start protocol for the next session

1. Read this handoff (you're doing it now).
2. **ASK USER FOR THE NATIVE-SPEAKER REVIEWER'S EMAIL REPLY** (see ⚠️ block at top — pending content blocks the recovery plan).
3. Orient via Monitor API:
   ```
   curl -s http://localhost:8765/api/state/manifest
   curl -s http://localhost:8765/api/orient
   curl -s 'http://localhost:8765/api/comms/inbox?agent=claude'
   ```
4. Read the v1 REPORT.html for context on what's already shipped: `audit/2026-05-19-multi-agent-routing-assessment/REPORT.html`. Browseable at http://localhost:8765/artifacts/audit/2026-05-19-multi-agent-routing-assessment/REPORT.html.
5. Check the open follow-up issues (#2154 zizmor MED triage, #2155 gate semantics bug).
6. AFTER triaging the reviewer's reply: begin with Section 1 (Hermes fix) — that unblocks Section 3 (kimi/minimax bakeoffs).
7. Section 2 (CoT removal) can dispatch in parallel — independent of Hermes.
8. Section 4 (B1+ readiness) is a one-shot inline check; do it whenever convenient.

---

## Provenance + cross-links

- v1 report shipped this session: `audit/2026-05-19-multi-agent-routing-assessment/REPORT.html`
- All raw artifacts: `audit/2026-05-19-multi-agent-routing-assessment/raw/` (15+ files: 4 routing + 8 writer bakeoffs + DeepSeek introspection + CoT discussion thread)
- The m20 writer prompt used for bakeoffs (real 60K-token prompt from build #8): `audit/2026-05-19-qwen-writer-bakeoff/writer_prompt.md`
- The claude-tools baseline output (for content quality comparison): `audit/2026-05-19-qwen-writer-bakeoff/claude-tools-baseline.raw.md`
- Predecessor session handoff: `docs/session-state/2026-05-19-night-gap-audit-closure-and-qwen-judge-brief.md`
- Open issues to track: #2154 (zizmor MED), #2155 (wiki_coverage_gate semantics)
- Resolved this session: #2148 γ shape (decision card moved to `docs/decisions/2026-05-18-wiki-obligation-emission-contract.md`), PR #2153 merged
