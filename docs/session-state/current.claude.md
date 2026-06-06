# Current — Claude Thread Handoff (2026-06-06, deploy-fix + #2747 full v5/v6 cleanup + security queued)

> Read `docs/session-state/current.md` (router) first, then this file.
> origin/main at handoff: see Restart block (FF first). Long session: deploy fix → #2747 finished → **security investigation is the NEXT task (not started)**.

## ▶ NEXT TASK (not started) — SECURITY INVESTIGATION (user priority)
User queued this explicitly. Two parts:
1. **Study the "Miasma Worm" article:** `https://thehackernews.com/2026/06/miasma-worm-hits-73-microsoft-github.html`
   — ⚠️ **403 on WebFetch/curl** (thehackernews bot-protection). MUST read via Chrome tools:
   `ToolSearch select:mcp__claude-in-chrome__tabs_context_mcp` → `tabs_create_mcp` → `navigate` → `get_page_text`.
   Per #M-1: browser tools, not curl/WebFetch. Capture: the supply-chain vector (npm/postinstall? GitHub
   Actions? stolen PAT? self-propagation?), IOCs, ecosystems hit, mitigations.
2. **Audit OUR defense-in-depth vs. unexpected supply-chain attacks.** Concrete surfaces to assess:
   - Dependency pinning / lockfiles (uv.lock, package-lock.json, .dagger), `pip-audit`/`npm-audit` (advisory in CI — should they be blocking?), `gitleaks` (blocking ✓).
   - GitHub Actions hardening: token scope/permissions, `zizmor` (already in CI), pinned action SHAs vs tags, `pull_request_target` usage.
   - Agent-dispatch + MCP attack surface (delegate.py spawns CLIs with `--mode danger` in worktrees; MCP servers; `ANTHROPIC_API_KEY`/secrets handling — see MEMORY #M-5).
   - The local API server (localhost:8765) exposure.
   Deliverable: HTML report (ai→human per #M-2), filed under `audit/` or `docs/`, with prioritized findings + fixes.

## ✅ DONE THIS SESSION

### Deploy fix + main-worktree guard hardening (PR #2767, merged)
- Root cause: an in-session local `guard-main-worktree.sh` was written to the deploy TARGET `.claude/hooks/`
  (gitignored, untracked) + wired only in `.claude/settings.local.json` → rsync `--delete` aborted deploy.
- Removed the orphan; deploy clean (zero drift). Folded its useful protection (block `git branch -D/-M/-f` in
  main) into the tracked quote-aware `claude_extensions/hooks/guard-branch-switch-in-main.py` + 38-case test.
  `git reset --hard` intentionally left allowed (user choice: force-deletes only). Guard is live + verified.

### #2747 — legacy v5/v6 + dead-code cleanup FULLY COMPLETE (user: "fully finish that ticket")
All phases merged (or merging — see #2773 below). v5 AND v6 build paths are GONE from main.
- Slices 1–3 (#2764/#2765/#2770): extracted v6_build shared symbols (phase_constants, prompt_literals,
  content_cleanup) → no live import of v6_build.
- Phase 4 (#2771): deleted `v6_build.py` (~12K lines) + its test suite. **Codex dispatch TIMED OUT mid-run**
  (silence-timeout 1800s too tight for the full-suite run); I took over the worktree, **reverted 2 codex
  overreaches** (a V7 writer-prompt behavior change ported into `linear_pipeline`; a dead `step_honesty_annotate`
  ported into `honesty_annotator`), fixed the test, 8203 passed, API import 41/41 clean.
- Phase 5 (#2772, merged): deleted v5 entrypoints (`build_module_v5.py`, `pipeline_v5.py` 187KB, 2 root shims)
  + the dormant research-preseed chain (`assess_research.py`+stub, `assess_research_helpers.py`,
  `assess_research_queue.py`, `check_rag_coverage.py`, `preseed_runner.py`, `tools/test_pipeline.py`) +
  v5-coupled tests. De-v5'd `comms_router` (process-finder) + `test_plan_adherence` + `wt.sh`. Clean, no overreach.
- Phase 6+7 (#2773, MERGED): deleted `scripts/oneoff/` (225 one-offs, zero importers) + `scripts/build/_archive/`
  (v6 code archive). pytest collected 8139 clean. **#2747 is CLOSED (COMPLETED). v5+v6+dead-code cleanup DONE.**

## ⚠ KEPT (do NOT delete) — load-bearing, verified live
- `scripts/pipeline/` package (core/fixes/parsing/state/dispatch) — used by V7 `linear_pipeline`, audit, API.
- `scripts/pipeline_lib.py`; `scripts/research/research_quality.py` + `research_markdown_utils.py` (API research dep).
- Forensic `./archive/` (4.5M audits/evidence/memory) + `docs/archive/` (1.4M handoffs) — historical (#M-10),
  retained by default. User has NOT asked to remove these.

## 🔌 LOCAL API SERVER — protection map (user stressed: "our local api server is important")
API (`scripts/api/*`, localhost:8765) depends on cleanup-adjacent code ONLY via: `pipeline/` (state,
consultation) + `research_quality` (assess_research_compat/find_research_path/get_rubric) — ALL KEPT.
Verified at EVERY phase with a 41/41 `scripts/api/*` import smoke. No API import of v5/v6/queue/preseed.

## ⚠ GOTCHAS / LESSONS
- **Codex over-engineers "to keep tests passing"** — it ports dead functions into live modules instead of
  deleting the dead test. Phase-5 brief added a hard "NO porting / NO new functionality" rule → came back clean.
  ALWAYS review dispatched cleanup PRs for *added* `def`/`class`/`import` in live source.
- **Dispatch silence-timeout sizing:** full-suite runs go silent for minutes. Use `--silence-timeout 3000+`
  for cleanup/test-heavy dispatches (1800 killed phase 4 mid-run).
- 7 local pytest failures are PRE-EXISTING + local-env-only (`test_monitor_client_sdk` etag/httpx +
  `test_writer_prompt_render_size` ceiling) — they PASS in CI. Don't chase them.
- index.lock races from concurrent agents: `pgrep -fl "git "` (ignore fsmonitor daemon), `rm -f` stale lock, retry.

## Restart
```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin main && git merge --ff-only origin/main && git rev-parse --short HEAD
gh pr list --state open --json number,title  # confirm #2773 merged; #2601 = other lane
gh issue view 2747 --json state              # confirm CLOSED
# then: SECURITY INVESTIGATION (see top). Browser for the article; audit our supply-chain posture.
```
