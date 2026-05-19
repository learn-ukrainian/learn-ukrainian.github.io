---
date: 2026-05-19
session: "Gap audit closure (6 of 10 specs shipped) + first qwen empirical signal (Russianism judge F1=69%, rank 5/5) + Codex 4-deliverable-docs PR landed clean in 20 min."
status: green
main_sha: cec462c37d
main_green: true
working_tree_dirty: false
shipped_this_session_to_disk:
  - "docs/decisions/pending/2026-05-18-wiki-obligation-emission-contract.md (#2148 DRAFT, 3 shapes, recommend γ)"
  - "docs/decisions/2026-05-18-deterministic-first-iteration.md (SYNTHESIS)"
  - "docs/north-star.md v3 → v3.1 (ULP-derived immersion)"
  - "docs/best-practices/agent-activity-matrix.md §8.11 (track-level routing stubs)"
  - "scripts/audit/qwen_judge_calibration.py (harness, 226 LOC)"
  - "audit/2026-05-19-qwen-3.6-judge-calibration/* (F1=69% rank 5/5)"
  - "docs/dispatch-briefs/2026-05-19-four-deliverable-docs-codex.md"
  - "docs/best-practices/pipeline/v7-build-preservation.md (P0 spec, 509 LOC)"
  - "docs/best-practices/pipeline/writer-bakeoff-methodology.md (P1, 432 LOC)"
  - "docs/architecture/v7-pipeline.md (P1, replaces legacy ARCHITECTURE.md, 685 LOC)"
  - "docs/plans/2026-06-15-claude-dispatch-sunset.md (P1, 419 LOC)"
prs_merged_this_session:
  - "#2149 docs(specs): close gap audit §1.1/§1.2/§1.8/§1.9"
active_dispatches: []
issues_filed: ["#2150 (closed inline)", "#2151 V7 preservation wrapper impl"]
---

# Handoff — Gap audit closure + first qwen empirical signal

## Restart context — 2.1.144 release notes (relevant items only)

User restarted with this session ending at `e5e16c9f2b`. New CLI is Claude Code 2.1.144. Items affecting our orchestration flow:

1. **MCP pagination fix** — *"MCP servers with paginated tools/list responses only returning the first page, silently dropping tools."* Our `mcp__sources__*` server registers ~40+ tools. Worth verifying with `claude mcp list` on first turn that the full tool catalog comes through. If the server uses pagination, prior sessions may have been operating with a subset.
2. **15s side-channel API timeout** (was 75s on `api.anthropic.com` unreachable). Affects cold-start when network is flaky / captive portals / VPN.
3. **Headless MCP startup ~2s faster** — every `delegate.py dispatch --agent claude` benefits. Also helps the Agent-tool subagents.
4. **Skill tool fixed in headless mode** (regression in 2.1.141). The `curriculum-writer` subagent uses skills; this regression may have been biting silent.
5. **`claude mcp list`** now surfaces `.mcp.json` config errors (was silent-empty). Useful debug surface — run on first turn if MCP behavior looks off.
6. **`/model` is now per-session; `/model d` sets default for new sessions.** Behavioral change. Default-setting requires a separate keypress now.
7. **MCP unsupported MIME (e.g. SVG)** — saved to disk + referenced instead of breaking the conversation. Affects `mcp__sources__search_images` if it ever returns non-JPEG/PNG.
8. **`/extra-usage` → `/usage-credits`** rename (old name still works as alias).
9. **MCP background side-queries on custom `ANTHROPIC_BASE_URL` / Bedrock Mantle** — now correctly fall back to Haiku. Relevant if the Hermes proxy ever gets pointed at by our base URL.
10. **`Edit`/`Write` no longer refuses with "background session hasn't isolated its changes yet"** right after detaching a session that was editing in place. Affects dispatch-worktree flows if we ever use `--bg`.

**Action recommended on first turn:** run `claude mcp list` to verify the `sources` MCP catalog is fully present post-pagination-fix; if any tool is missing that the matrix or rules reference, file an issue against the MCP server config.

### Kubedojo cross-perspective on 2.1.144

User shared kubedojo's analysis of the same release notes. Two items add real value over my own; two items are stale/N/A here. Verified findings:

| Their item | Our state |
|---|---|
| Drop `|| true` suppression around grep in pipeline scripts | **N/A for us.** Grepped `scripts/`, `.claude/`, `claude_extensions/`, `tests/` — only hit is `scripts/wt.sh:37 pgrep ... \|\| true`, which is process-grep, not the content-grep pattern the release fix targets. We don't have that anti-pattern. |
| Audit `mcp__rag__*` tool count | **Stale prefix** — our MCP retired `mcp__rag__*` → `mcp__sources__*` per `claude_extensions/rules/mcp-sources-and-dictionaries.md`. Audit still valid for `mcp__sources__*`. HTTP probe of `:8766/tools` returned "Not Found" — sources MCP is stdio, not HTTP. Concrete audit: next session run `claude mcp list` (2.1.144 surfaces config errors now) and compare visible tool count to `@server.tool()` declarations in the MCP server source. |
| `/resume` supports `--bg` sessions | Already in my notes. Pairs well with the `claude-i tmux wrapper` research (#2116) — `--bg` is no longer a one-way trip. |
| `/model` is per-session; `d` sets default | Already in my notes. |
| `/usage-credits` rename | Already in my notes. Aliases preserved. |

**Net adjustments to the muscle-memory layer:** none for grep (we're clean); add `claude mcp list` to the first-turn hygiene check; remember `d` in the model picker.

### Supply-chain audit — 2026-05 GitHub Actions `actions-cool/*` compromise

User flagged TheHackerNews report on `actions-cool/issues-helper` + `actions-cool/maintain-one-comment` (tags redirected to malicious imposter commits). Article's core protection: full-SHA pinning.

**Audit findings:**

1. **NOT exposed to the specific compromise** — we don't use any `actions-cool/*` action (grep `.github/` confirms zero hits).
2. **Real gap fixed inline:** `dorny/paths-filter@v4` (third-party, floating tag) at `ci.yml:46` — pinned to `fbd0ab8f3e69293af611ebaee6363fc25e6d187d`.
3. **Consistency gap fixed inline:** `actions/setup-node@v6` at `ci.yml:258` + `ci.yml:418` — pinned to `48b55a011bda9f5d6aeb4c2d9c7362e8dae4041e` (same vendor already SHA-pinned in other workflows; just consistency).
4. **Follow-up filed (#2152):** the `gemini-*` workflows have an inconsistent `ratchet:exclude` pattern — `actions/checkout@v6` is excluded in gemini-invoke.yml + gemini-plan-execute.yml but properly SHA-pinned in gemini-review.yml. `google-github-actions/run-gemini-cli@v0` is excluded everywhere (Google's release branch — intentional but worth documenting). Estimated 15 min cleanup.

**Inline fix committed at `fd4b89f18d`** (security-only, 3 lines, YAML parses, no behavior change).

**Where supply-chain hygiene was previously established:** 2026-03-25 handoff §"Supply chain hardening (SHA-pinned actions, requirements.lock, Dependabot)". Most actions are pinned with `ratchet:` comments — the 3 unpinned references in `ci.yml` were leftovers; #2152 covers the remaining `gemini-*` cleanup.

---

## TL;DR

Predecessor session (2026-05-19 morning) shipped the gap audit + 4 hygiene commits and left 8 items in the carry-over queue. This session drained items 2-4 inline, dispatched item 4 to Codex (landed in 20 min — 4× faster than the 1.5-3h estimate), updated item 7 (north-star), and earned the first empirical qwen signal in any role.

**1 PR merged (#2149) + 6 direct commits to main. 1 follow-up issue filed (#2151). 1 inline-closed issue (#2150). Main green at `cec462c37d`, tree clean, 0 active dispatches.**

The single most useful empirical signal: **qwen-3.6-plus as Russianism judge → F1 69%, P 90%, R 56%, case_acc 92%, rank 5/5.** Most-conservative judge in the field; high precision means qwen won't accuse innocent text, but recall=56% means it misses ~half the sev≥2 issues that real Russianism-heavy text contains. NOT primary; viable as cheap second-opinion screen where precision dominates recall.

## State at handoff

| Item | State |
|---|---|
| Main SHA | `cec462c37d` |
| Working tree | CLEAN |
| Active dispatches | 0 |
| Open PRs of mine | 0 |
| Open PRs (other) | only #1873 dependabot starlight (user-owned, leave) |
| Worktrees | only main + codex-interactive (none from this session) |
| Inbox | 0 unread for claude |
| MEMORY.md | 150/150 (at budget) |

## What shipped this session — by carry-over queue item

The 2026-05-19 morning handoff named 8 priorities. State now:

| Item | Status | Notes |
|---|---|---|
| 1. Commit grouping | ✅ pre-resolved before this session (predecessor committed 5 commits this morning) |
| 2. Verify §1.10 cascade | ✅ track-architecture.md + ROADMAP have ZERO writer-routing content; matrix §8.11 is canonical home, populated with stubs |
| 3. Reframe §1.5 synthesis | ✅ `docs/decisions/2026-05-18-deterministic-first-iteration.md` shipped (L1-L7 layered description of V7 correction pattern) |
| 4. Write 5+1 deliverable docs | ✅ 6 docs total — 2 shipped inline (synthesis + #2148 contract DRAFT), 4 dispatched to Codex (PR #2149 landed clean in 20 min) |
| 5. Wire deepseek-tools + qwen-tools as V7 writers | ⏸ task expanded — see "Tomorrow's queue" below |
| 6. A1 m20 bakeoff | ⏸ scope tightened — 3 writers (deepseek + qwen + gemini re-test), not 6 — blocked on task #5 |
| 7. Update north-star.md | ✅ v3 → v3.1 (compute_immersion_band() per ULP card) |
| 8. m20 ship work (#2148) | ⏸ DRAFT shipped — needs user signoff on γ-shape before implementation dispatch |

**Bonus tonight (not in morning queue):** qwen Russianism judge probe (~$2, ~6 min). User-requested mid-session ("when qwen?"). First qwen empirical signal in any role.

## Qwen empirical signal — single most useful finding

Per `audit/2026-05-19-qwen-3.6-judge-calibration/REPORT.md`:

| Metric | Value | Rank |
|---|---:|:---:|
| F1 (sev≥2) | 69.2% | **5/5** |
| Precision | 90.0% | ties Codex GPT-5.5 for best |
| Recall | 56.2% | lowest in field |
| Case accuracy | 91.7% | ties Gemini |

Wrong case: `cal_clean_with_lure` (false positive). Profile: high-precision conservative judge. Updated matrix §8.2a + §8.10. Marked recommended bakeoff #2 DONE.

## What changed about the bakeoff plan (user-driven mid-session)

User caught a wiring gap I'd missed: **`WRITER_CHOICES` at `scripts/build/linear_pipeline.py:65` is `("claude-tools", "gemini-tools", "codex-tools", "grok-tools")` — neither deepseek-tools nor qwen-tools is in there.** The "6-writer bakeoff" wasn't runnable until both are wired.

Then the user scoped down further: **don't re-bakeoff models we already have signal on.** Final scope for task #6:

- Drop: claude-tools (✅ A1 baseline validated 1224w/4 MCP/VESUM 159/159), codex-tools (A1 register gap empirical), grok-tools (#2039 weak)
- Keep: deepseek-tools (new), qwen-tools (new), gemini-tools (last bakeoff infra-crashed #1708 needs re-test)
- Result: **3-writer bakeoff at ~$6-10** (down from ~$10-15 for 6-writer)
- Caveat: if #2148 γ ships and changes prompt, add claude-tools re-baseline (4th writer, +$3-5)

User-stated models for the bakeoff: `qwen-3.6-plus`, `deepseek-v4-pro`, `gemini-3.1-pro-preview` (upper-tier production, not budget flash / not max-preview).

This is folded into task #5 + #6 descriptions and into the bakeoff-methodology.md doc (via the #2150 cross-link polish).

## Tomorrow's queue (user-locked sequence + new items)

Priority order:

1. **#2148 γ-shape signoff** — DRAFT decision card at `docs/decisions/pending/2026-05-18-wiki-obligation-emission-contract.md`. **BLOCKING** the m20 corrector dispatch + the 6-writer bakeoff baseline. Three shapes (α/β/γ). γ recommended (cheapest, reuses PR #2108 sidecar, ~1-2h Codex). User picks shape + bridge option (A/B/C/D).
2. **Task #5: Wire deepseek-v4-pro + qwen-3.6-plus as V7 writers** — single Codex PR, mirrors grok-tools wiring from PR #2033. Files: `scripts/build/linear_pipeline.py` WRITER_CHOICES + WRITER_DEFAULTS + `_runtime_tool_config`. Models: `deepseek-v4-pro` effort=high, `qwen/qwen3.6-plus` effort=high. Smoke test on a1/my-morning. ~half-day, ~$5-8.
3. **Task #6: A1 m20 3-writer bakeoff** — deepseek + qwen + gemini, deterministic rubric, ~$6-10. After #2 lands.
4. **#2151 V7 preservation wrapper implementation** — spec exists (`docs/best-practices/pipeline/v7-build-preservation.md`); implementation does not. ~half-day Codex dispatch. Touches `scripts/build/v7_build.py` wrapper layer.

Both #5 and #6 depend on user direction (do we fire codex on #5 autonomously, or wait for user). Per #M-0A I will surface this as a single decision card on next session start.

## Behavioral notes (for next session)

1. **The Codex 20-min docs dispatch was suspicious-fast** — my estimate was 1.5-3h. Codex actually shipped 2045 lines in 20 min with comprehensive #M-4 evidence and CI green. Lesson encoded: Codex on doc-writing tasks with locked source material is much faster than Codex on code-writing tasks. Update mental model: doc-write dispatches ~15-30 min, code-write ~30-180 min.
2. **The PR body's "Verification evidence" section was the right artifact.** Codex provided grep + cwd + raw-output triples for every cited file:line, every cited PR/issue number was verified with `gh pr view`. The brief's #M-4 preamble worked. Reuse the brief shape for future doc dispatches.
3. **One cross-link gap surfaced in PR review** — writer-bakeoff-methodology.md didn't link to #2148 contract DRAFT even though the methodology section warns about exactly that class of in-flight change. Closed inline as #2150. Lesson: when dispatching new docs alongside a pending decision card, explicitly enumerate the cross-links in the brief.
4. **Branch deletion vs worktree reaping** — `gh pr merge --delete-branch` left the local branch around because the dispatch worktree was using it. Cleanup: `git worktree remove .worktrees/dispatch/codex/...` first, then `git branch -D codex/...`.

## What the next session should do FIRST

**Cold-start sequence:**

1. Read this handoff
2. `curl -s http://localhost:8765/api/orient` — confirm tree state matches
3. `git status --short` — tree should be clean (only `docs/dispatch-briefs/2026-05-18-bulk-ocr-repetition-hallucination-filter.md` as the other-agent WIP untracked file, still flagged)
4. Check inbox + pending decisions:
   - `docs/decisions/pending/2026-05-18-wiki-obligation-emission-contract.md` (mine, BLOCKING m20)
   - `docs/decisions/pending/2026-05-14-agent-sdk-adoption.md` (older, RECONSIDER status per #M0 update)
5. Surface the #2148 γ-shape signoff to user as a one-card decision (3 shapes, recommend γ, decision needed to unblock m20)

**Priorities (user-locked sequence):**

1. User: pick #2148 shape (α/β/γ) + bridge option (A/B/C/D)
2. After γ signoff: dispatch Codex on implementation (1-2h, ~$3-5)
3. Concurrently or after: dispatch Codex on task #5 (deepseek + qwen V7 writer wiring, ~half-day, ~$5-8)
4. After #5 lands: fire task #6 (3-writer bakeoff, ~$6-10)
5. After m20 ships green: re-evaluate next batch (A1 m01-m07?)

## Critical findings / corrections — for next session

1. **Codex docs-dispatch is FAST** — recalibrate doc-dispatch ETA expectations (15-30 min, not 1.5-3h)
2. **Qwen-3.6-plus is conservative** — 90% precision, 56% recall as Russianism judge. Translates to: qwen won't false-accuse innocent text but will under-flag real issues. Implications for content reviewer role TBD (recommended bakeoff #3 in matrix §8.10 still open).
3. **WRITER_CHOICES is the gate for V7 writer wiring** at `scripts/build/linear_pipeline.py:65` — adding a writer needs a tuple entry + WRITER_DEFAULTS entry + `_runtime_tool_config` pattern.
4. **PR review pattern that works:** before merging a doc PR, grep for cross-links to in-flight decision cards. The cross-link audit caught #2150 in 30 seconds.

## Provenance

- Predecessor session: `docs/session-state/2026-05-19-handoff-gap-audit-and-qwen-integration.md`
- Audit driver: `audit/2026-05-18-docs-gaps-and-reorganization/REPORT.md`
- Decision cards landed: `2026-05-18-deterministic-first-iteration.md` (synthesis), `pending/2026-05-18-wiki-obligation-emission-contract.md` (#2148 DRAFT)
- Codex dispatch brief: `docs/dispatch-briefs/2026-05-19-four-deliverable-docs-codex.md`
- Qwen probe: `scripts/audit/qwen_judge_calibration.py` + `audit/2026-05-19-qwen-3.6-judge-calibration/REPORT.md`
- PR merged: #2149 (squashed at `6ff1b44b0a`); cross-link follow-up at `cec462c37d`
