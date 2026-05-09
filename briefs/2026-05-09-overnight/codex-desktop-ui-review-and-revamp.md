# Codex Desktop — Local API UI review + UX revamp

Hi Codex (Desktop) — this is a job for you. Same kind of work you did for kubedojo. The user picked you because you have the chrome browser plugin for visual feedback and the design judgment for this.

**If anything in this brief is unclear or you'd take a different approach, ASK FIRST before starting work.** Don't second-guess silently.

---

## What you're doing

Audit the local API's web UI (everything served at `http://localhost:8765/...`), report on UX/UI quality + working-state, and ship the revamp. The user's framing: *"review the local api ui for uiux experience and make sure it is working properly."* That's two passes — first a working-state audit, then a UX revamp. Both in scope.

The local API is `scripts/api/main.py` (FastAPI). Static pages live in `playgrounds/*.html`. Key UI surfaces today:

| Page | URL | Purpose |
|---|---|---|
| Dashboard / orient | `http://localhost:8765/orient.html` | Project home — git, issues, pipeline, runtime, delegate, wiki, health, session hints |
| Channels | `http://localhost:8765/channels.html` | Multi-agent channel viewer (`ab discuss`, `ab post` threads) |
| Comms | `http://localhost:8765/comms.html` | Inbox / message-broker viewer |
| Artifacts (new) | `http://localhost:8765/artifacts/...` | Static HTML/MD/asset serving for `audit/`, `docs/session-state/`, `docs/best-practices/`, etc. (just landed in commit `c17450a6c1`) |
| Other playgrounds | `http://localhost:8765/<other>.html` | List by `ls playgrounds/*.html` — there are ~18 |

Plus the JSON API at `/api/...` which feeds those pages. You can hit any endpoint via `curl localhost:8765/api/...` and see it in the browser too.

---

## Mandatory orientation (do this first)

Per the project's onboarding pattern, before touching anything:

1. Read this brief end-to-end. Note open questions; ASK before starting if unclear.
2. Read **`docs/best-practices/deterministic-over-hallucination.md`** — TOP PRIORITY cross-agent rule landed today (commit `653ffe39e9`). Every verifiable claim in your audit / PR / comments must be backed by a tool call. No "I think this is broken" — only "I ran X, got Y, here's the evidence."
3. Read the latest session handoff: **`docs/session-state/2026-05-09-late-night-gemini-tools-cwd-fix.html`** (open via `localhost:8765/artifacts/docs/session-state/2026-05-09-late-night-gemini-tools-cwd-fix.html` if API is up). Sets the recent context.
4. Read **`docs/MONITOR-API.md`** — the canonical API surface reference. Most of the UI is one-to-one with these endpoints.
5. Run `curl -s http://localhost:8765/api/health` to confirm the API is up. If 000, start it: `npm run api &` (it tees to `logs/api.log`). If you can't get it up, ASK before improvising.
6. Open the existing UI in your chrome plugin: orient.html, channels.html, comms.html, artifacts/. Take screenshots of each — they are evidence for your audit, attach them in the PR.

---

## Existing tracked UX issues (don't re-discover, build on these)

These were filed by the orchestrator (Claude) this morning. They are **inputs** to your work, not the full scope:

- **#1820** — `orient.html` has no awareness of active discussions; `channels.html` lacks `?channel=&thread=` deep-link params. Three sub-fixes: A) `GET /api/discussions/active` endpoint, B) dashboard widget on orient.html, C) URL deep-link in channels.html. Spec is in the issue body.
- **#1814** (umbrella) — HTML artifact serving + navigation UI on Monitor API. Sub-task A (`/artifacts/<path>` static serve) has shipped. Sub-tasks B (metadata listing endpoint) and C (browser UI) are still open. **The browse UI for /artifacts/ is part of your scope** — it's the missing piece between the route landing and a usable docs portal.
- **#1822** — no test coverage for the `/artifacts/` docs router. Spec lists 9 cases (traversal, symlink, ext allowlist, etc.).

**You can scope-creep into these issues if it makes the UX revamp coherent — but every additional sub-issue you absorb must be explicit in the PR body.** No silent expansion.

---

## What "review" means here (audit pass — first deliverable)

Produce an HTML audit report at `audit/local-api-ui-review-2026-05-09/REPORT.html` (parchment template — copy from `docs/session-state/2026-05-09-late-night-gemini-tools-cwd-fix.html`). The audit must cover, per page:

1. **Working-state**: does the page render? Does every interactive element work? Does it survive an API restart? Are there console errors / 404s on assets / broken links?
2. **UX/UI quality**: information hierarchy, visual density, color usage, accessibility (keyboard nav, contrast, semantic HTML), responsive behavior on narrower viewports, discoverability.
3. **Consistency**: do the pages feel like one product? Same nav? Same color palette? Same typography?
4. **Performance**: cold-load time, time-to-interactive, network waterfall — `curl` timings + your chrome plugin's perf signal.
5. **Specific evidence**: per finding, a screenshot + the curl/console output that demonstrates it. **No claim without evidence per `#M-4`.**

Audit verdict per page: `OK | NEEDS-POLISH | BROKEN`. Aggregate verdict at the top.

---

## What "revamp" means here (implementation pass — second deliverable)

After the audit lands and you (or the user) signs off on the priority list:

1. **Active discussions on orient.html** (closes #1820 sub-tasks A + B): `GET /api/discussions/active` endpoint + a widget on orient.html surfacing in-flight `ab discuss` threads.
2. **Channels deep-link** (closes #1820 sub-task C): `?channel=<>&thread=<>` URL params on channels.html.
3. **Artifacts browse UI** (closes #1814 sub-tasks B + C): a usable browse experience for `/artifacts/...`. Today the route serves the file at the path; there's no index UI. Build one.
4. **Cross-page consistency pass**: shared nav header (so orient/channels/comms/artifacts feel like one product), unified palette + typography (recommend matching the parchment design from the session handoffs — but this is YOUR design call, justify in the audit report).
5. **Anything else surfaced by the audit** that's high-value and within reasonable scope.

Each revamp item is its own commit (or atomic group of commits) within the same PR — don't mix unrelated changes.

---

## Mandatory worktree setup

Per `.claude/rules/delegate-must-use-worktree.md` — work in a worktree, NOT the main checkout.

```bash
git worktree add -b codex/desktop-ui-review-revamp-2026-05-09 .worktrees/codex-desktop-ui-review-revamp
cd .worktrees/codex-desktop-ui-review-revamp
# do work, commit, push, gh pr create
```

The main checkout stays on `main`. After PR merges, the orchestrator (or you) cleans up:

```bash
git worktree remove .worktrees/codex-desktop-ui-review-revamp
git branch -d codex/desktop-ui-review-revamp-2026-05-09
```

---

## Workflow

1. **Orient** — read the docs above, take baseline screenshots, verify API is up.
2. **Ask if unclear** — anything in this brief, anything in the codebase, anything about scope. Channel: `ab post architecture --to claude "<question>"` or post in the GitHub issue thread (#1820 or #1814). The user prefers being asked over silent guessing.
3. **Audit** — produce the HTML report at `audit/local-api-ui-review-2026-05-09/REPORT.html`. Commit. (Optionally pause here and request user signoff on priorities before revamping — your call based on what you find.)
4. **Revamp** — ship the implementation against the audit's prioritized list.
5. **Test** — write tests for new code paths. Coverage is non-negotiable per `claude_extensions/rules/non-negotiable-rules.md`. The new tests should at least cover: each new endpoint (200 happy path + a negative path), each new UI behavior that has a measurable contract (URL deep-link sets state, dashboard widget renders the active count correctly).
6. **Pre-commit hygiene** — `.venv/bin/ruff check` clean for any Python touched; `npm test` if you touch frontend tests; bash syntax check (`bash -n`) for any scripts.
7. **Commit + push + PR** — conventional commit messages, one feature per commit. PR body includes: link to audit report, screenshot before/after for each UX change, test plan checked off, smoke evidence with raw output (per `#M-4`).
8. **Request review** — on the PR, tag the orchestrator + dispatch reviews:
   - `ab ask-claude --model claude-opus-4-7 --effort xhigh "Adversarial review of PR #N (UI review + revamp)"` — Claude as adversarial reviewer per project policy
   - `ab ask-gemini --model gemini-3.1-pro-preview "Cross-agent design review of PR #N (UI revamp)"` — Gemini as second design opinion
   - Comment on the PR with both review results before requesting human merge.
9. **NO auto-merge** — the orchestrator/user merges after CI is green AND both agent reviews pass. Per `MEMORY.md #M-0.5`: never admin-bypass a failing blocking check.

---

## Top-priority constraints (read these before doing anything)

### `#M-4` — deterministic over hallucination (TOP PRIORITY)

Every claim in your audit, PR body, commit messages, and review comments must be backed by a tool call. Examples:

- ❌ "The orient page loads slowly" → ✅ `curl -w '%{time_total}\n' -o /dev/null -s http://localhost:8765/orient.html` → "0.847s"
- ❌ "channels.html has a contrast issue" → ✅ chrome plugin's lighthouse report cited verbatim, contrast ratio numbers
- ❌ "I think the API endpoint returns X" → ✅ `curl /api/...` and quote the JSON response

Full rule: `docs/best-practices/deterministic-over-hallucination.md`. Skipping the tool = hallucinating with confidence. We have the tools; use them.

### `#M-2` — HTML for authored artifacts

Your audit report goes in HTML, parchment template. Copy from a recent handoff. Markdown is fine for the implementation README inside a code change, not for the audit deliverable.

### `#M-0.5` — no admin-bypass

When the PR has CI failures, STOP and report. Don't `gh pr merge --admin` or otherwise bypass. Pytest, ruff, frontend, schema-drift, gitleaks, radon, prompt-lint are all blocking. Only `Gemini Dispatch` (`review/review`) is advisory.

### `#0H` — but you're not the merger here

The orchestrator (Claude) merges after reviews land. You don't need to push for merge — push for clean review.

---

## Definition of done

- [ ] Audit HTML report committed at `audit/local-api-ui-review-2026-05-09/REPORT.html`. Parchment template. Per-page verdicts. Screenshots + curl evidence for every claim.
- [ ] Revamp commits land in the same PR (or a sibling PR if the user asks to split).
- [ ] All new code has tests; existing tests still pass; ruff clean.
- [ ] Smoke verification recorded in PR body:
  - `curl /api/health` → 200
  - `curl /api/discussions/active` → 200 with the expected shape (after sub-task A lands)
  - Visit `localhost:8765/orient.html` → see active-discussions widget render with at-least-one in-flight thread (after sub-task B lands)
  - Visit `localhost:8765/channels.html?channel=architecture&thread=33d8893f` → channel auto-selected, thread auto-filtered (after sub-task C lands)
  - Visit `localhost:8765/artifacts/` → see browse UI (after #1814 sub-task B/C lands)
- [ ] Reviews requested from Claude (Opus, xhigh) AND Gemini (3.1-pro). Both reviews posted as PR comments before requesting human merge.
- [ ] PR body explicitly lists every issue closed/touched (#1814, #1820, #1822 as applicable).

---

## Reference index

- **Top-priority rule (mandatory read):** `docs/best-practices/deterministic-over-hallucination.md`
- **Project critical rules:** `.claude/rules/critical-rules.md` (deployed) or `claude_extensions/rules/critical-rules.md` (source)
- **Non-negotiable rules:** `claude_extensions/rules/non-negotiable-rules.md`
- **Worktree mandatory rule:** `.claude/rules/delegate-must-use-worktree.md`
- **Latest session handoff:** `docs/session-state/2026-05-09-late-night-gemini-tools-cwd-fix.html`
- **Cross-agent reference:** `docs/best-practices/agent-cooperation.md` / `.html`
- **Open issues you'll touch:** #1814 (HTML artifact navigation umbrella), #1820 (orient widget + deep-link), #1822 (docs_router tests)
- **API source:** `scripts/api/main.py` + the routers it includes (`scripts/api/*_router.py`)
- **UI source:** `playgrounds/*.html`
- **Recent precedent (UI work that landed):** `c17450a6c1` (artifacts route + 9 HTML migrations), `dc0238c953` (8 more HTML migrations).

---

If you hit something this brief doesn't cover, **ask** — don't guess. Channel `architecture`, thread the orchestrator, or comment on a related issue. The user's preference is explicit: ask first if unclear.

Welcome aboard. Take your time with the audit; the revamp is more rewarding when the audit nailed the right priorities.

— Claude (orchestrator), 2026-05-09
