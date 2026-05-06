# Gemini dispatch brief — CodeQL cleanup, real fixes vs false-positive dismissals

> **Branch base:** `origin/main` (this dispatch fires AFTER #1711 merges so the gemini-cli adapter is fixed)
> **Worktree:** `.worktrees/dispatch/gemini/codeql-cleanup-2026-05-05/`
> **Branch name:** `gemini/codeql-cleanup-2026-05-05`
> **Mode:** danger
> **Hard timeout:** 5400s (90 min)

## Goal

Clear the 12 open CodeQL alerts. **Some are real bugs that need code fixes. Others are false positives** (scraped third-party podcast HTML treated as JS source, localhost-only dev tools flagged as if internet-facing, etc.) that should be dismissed via `gh api` with a clear rationale, not "fixed" by editing scraped artifacts.

You decide which is which per-alert. Don't suppress something that's actually a bug; don't waste effort fixing scraped HTML.

## Inventory (as of 2026-05-05 20:48 CEST)

| Alert | Severity | Rule | File | Line |
|---|---|---|---|---|
| #167 | error | `py/clear-text-storage-sensitive-data` | `scripts/build/linear_pipeline.py` | 2637 |
| #166 | error | `py/clear-text-storage-sensitive-data` | `scripts/generate_mdx/core.py` | 574 |
| #114 | error | `py/path-injection` | `scripts/tools/image_review_server.py` | 239 |
| #113 | error | `py/path-injection` | `scripts/tools/image_review_server.py` | 234 |
| #23  | warning | `js/functionality-from-untrusted-source` | `docs/resources/podcasts/raw/episode_021.html` | 1848 |
| #22  | warning | `js/functionality-from-untrusted-source` | `docs/resources/podcasts/raw/episode_022.html` | 1848 |
| #21  | warning | `js/functionality-from-untrusted-source` | `docs/resources/podcasts/raw/episode_022.html` | 3318 |
| #20  | warning | `js/functionality-from-untrusted-source` | `docs/resources/podcasts/raw/episode_021.html` | 3318 |
| #19  | warning | `js/unvalidated-dynamic-method-call` | `playgrounds/admin.html` | 219 |
| #18  | warning | `js/xss-through-dom` | `playgrounds/image-explorer.html` | 705 |
| #17  | warning | `js/xss-through-dom` | `docs/resources/podcasts/raw/episode_022.html` | 4498 |
| #16  | warning | `js/xss-through-dom` | `docs/resources/podcasts/raw/episode_021.html` | 4498 |

## Categorization framework

For each alert, decide: **REAL** (fix in code) or **FALSE POSITIVE** (dismiss via `gh api`).

### Heuristics

- **Scraped third-party HTML in `docs/resources/podcasts/raw/`** = archived research artifact, NOT deployed code. Adding SRI hashes to scraped HTML or escaping its DOM doesn't make sense — we don't own that markup. **Dismiss.** Likely candidates: #16, #17, #20, #21, #22, #23 (all in `docs/resources/podcasts/raw/`).

- **`scripts/tools/image_review_server.py` path-injection** = check first whether this is a localhost-only dev tool. If `app.run(host='127.0.0.1', ...)` and there's no production deployment of this server, the path-injection risk is bounded to local users (i.e., the developer themselves). May still be worth fixing for hygiene — your call. Document the reasoning either way.

- **`playgrounds/*.html`** = also localhost-only (per `docs/best-practices/agent-bridge.md`, the dashboard at `:8765` is localhost-binding). XSS in localhost-only tools has bounded risk but is still cleanable. Check the context. Lean toward fixing (small JS edits) unless the fix is disproportionate.

- **Python clear-text-storage in `linear_pipeline.py` and `generate_mdx/core.py`** = read line context before deciding. If the "private" data is something like an API token written to a log, that's real. If it's a benign string that CodeQL pattern-matched as sensitive, it's a false positive. Investigate.

### Decision rules

- **REAL:** fix in code; add a regression test where applicable
- **FALSE POSITIVE in deployed code:** add inline CodeQL suppression with `// lgtm[<rule-id>]` (JS) or `# lgtm[<rule-id>]` (Python) AND a comment explaining why
- **FALSE POSITIVE in scraped/research artifact:** dismiss the alert via `gh api` (see commands below). Don't edit the scraped file.

### Dismissing an alert via gh api

```bash
gh api -X PATCH \
    -H "Accept: application/vnd.github+json" \
    /repos/learn-ukrainian/learn-ukrainian.github.io/code-scanning/alerts/<ALERT_NUMBER> \
    -f state=dismissed \
    -f dismissed_reason="false positive" \
    -f dismissed_comment="Scraped third-party podcast HTML archived as research artifact under docs/resources/podcasts/raw/. Not user-facing deployed code; we don't own this markup. CodeQL flagged the original podcast site's CDN script tags. Not actionable on our side."
```

Valid `dismissed_reason` values: `false positive`, `won't fix`, `used in tests`. Pick the most accurate one per-alert.

## Numbered execution steps

1. Verify worktree base clean: `git log --oneline HEAD..origin/main` empty.
2. Pull the latest CodeQL alerts list:
   ```bash
   gh api -H "Accept: application/vnd.github+json" \
       /repos/learn-ukrainian/learn-ukrainian.github.io/code-scanning/alerts \
       --paginate -q '.[] | select(.state=="open")'
   ```
   Verify the inventory above is still current. If new alerts appeared, include them in scope.

3. For each alert: open the file at the cited line, read 30 lines of surrounding context, decide REAL or FALSE POSITIVE. Document your reasoning in a working notes file (commit it as `docs/audits/codeql-2026-05-05-triage.md`).

4. **For REAL alerts:** make the code fix. If the fix is non-trivial (>20 LOC), prefer a defensive minimum-viable patch over a sweeping refactor. Log each fix in the triage notes.

5. **For FALSE POSITIVE alerts:** dismiss via `gh api` (command above). Use a precise `dismissed_comment` that explains the project context (NOT generic "false positive" — specifically why THIS alert is wrong for THIS file).

6. Run tests + lint on touched files:
   ```bash
   .venv/bin/ruff check scripts/
   .venv/bin/pytest tests/ -x  # only if you touched code that has tests
   ```

7. Get cross-family review from Claude (you're Gemini; cross-family = Claude):
   ```bash
   git add -A
   git diff --cached > /tmp/codeql-cleanup-diff.txt
   .venv/bin/python scripts/ai_agent_bridge/__main__.py ask-claude \
       "Adversarial review for CodeQL cleanup dispatch. Read /tmp/codeql-cleanup-diff.txt and docs/audits/codeql-2026-05-05-triage.md. For each REAL fix: is the patch sufficient? For each dismissal: is the reasoning sound, or is this actually a real bug being papered over? Cite specific alert numbers." \
       --task-id codeql-cleanup-review
   ```

8. Apply review feedback or argue back in writing in the triage notes file.

9. After review CLEAN: commit with `Reviewed-By: claude-opus-4-7 (codeql-cleanup-review)` trailer. Conventional commit message:
   ```
   chore(codeql): triage 12 alerts — N fixed, M dismissed
   ```

10. Push and open PR. Body MUST include:
    - The full triage table (alert # / file / verdict / one-line rationale)
    - Per-fix: brief description + test added (if any)
    - Per-dismissal: link to the dismissed alert page + the rationale used
    - DO NOT enable auto-merge.

## Constraints

- **Do NOT edit `docs/resources/podcasts/raw/*.html`** — those are archived scraped research artifacts. Only dismissals are appropriate for their alerts.
- **Do NOT mass-dismiss without per-alert reasoning.** Each `dismissed_comment` should be specific to the alert.
- **Do NOT introduce new failure modes.** If you fix a path-injection by adding validation, test that the validation doesn't break legitimate use cases.
- **Cross-family review is mandatory** before commit. Claude is your reviewer (Codex is also OK as a fallback, but Claude is preferred since it's adjacent to the project's daily orchestration).
- **One PR for the whole batch.** Don't split per-alert; the triage is a coherent unit of work.
- **Don't touch any of the open in-flight PRs:** #1696, #1688, #1711.

## Out of scope

- Adding a CodeQL config that excludes `docs/resources/podcasts/raw/` from scanning (could be a follow-up PR if mass-dismissing 7 alerts feels excessive)
- Refactoring `image_review_server.py` beyond the minimum needed to fix the path-injection
- Rewriting the playground HTML files
- Investigating CodeQL alerts that are CLOSED (dismissed previously) — only OPEN ones are in scope

## Failure modes

- **Dismissing alert fails with 403:** you don't have repo write permission on alerts. Stop and report — this is a permissions issue, not a triage issue.
- **A "false positive" turns out to be real on closer reading:** that's fine, switch to fixing it. Update the triage notes file.
- **A fix breaks tests:** roll back the fix, document the failure mode in triage notes, leave the alert open with a comment explaining what blocked the fix.
