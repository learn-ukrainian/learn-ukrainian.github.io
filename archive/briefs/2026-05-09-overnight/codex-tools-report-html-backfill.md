# Backfill `audit/codex-tools-review-2026-05-08/REPORT.md` to HTML

**Goal:** Convert the markdown report at `audit/codex-tools-review-2026-05-08/REPORT.md` into an HTML artifact at `audit/codex-tools-review-2026-05-08/REPORT.html`, using the parchment design language established in `docs/session-state/2026-05-09-overnight-codex-tools-and-html-migration.html`.

**Why:** Per `MEMORY.md #M-2` (HTML for authored artifacts) and #1814 (HTML migration). The codex-tools report is referenced from the latest handoff and listed as Phase 3 ("opportunistic backfill"). This is a 1-file conversion — high signal, bounded scope, perfect Gemini job (content writing, unmetered).

## Worktree instructions (mandatory)

```bash
git worktree add -b gemini/codex-tools-report-html-backfill .worktrees/gemini-codex-tools-report-html-backfill
cd .worktrees/gemini-codex-tools-report-html-backfill
```

## Acceptance criteria

1. **Read the source markdown:** `audit/codex-tools-review-2026-05-08/REPORT.md` (307 lines).

2. **Read the design reference:** `docs/session-state/2026-05-09-overnight-codex-tools-and-html-migration.html`. Mirror its CSS variables (parchment surfaces, oxblood/ochre/sober-green/brick-red palette, Charter/Source-Serif body, system mono code), its component vocabulary (verdict bar, KPI grid, threads table, timeline, callouts, lessons grid, details disclosures, footer), and its meta-tag header convention. Do NOT copy paste the entire `<style>` block verbatim — keep it self-contained but consistent.

3. **Translate the markdown to HTML structure:**
   - Hero header: title `codex-tools deep review — joint Claude + Codex report`, status pill `CONVERGED`, date `2026-05-08`, agents `claude,codex`.
   - Verdict bar: `Root cause: identified` (ok), `Fix: shipped via #1813` (ok), `Convergence: claude+codex` (info).
   - KPIs (4 tiles): root-cause field count, evidence sections (E1-E4 = 4), tool calls observed at runtime (39-59 exec_command), MCP calls observed (0 — the smoking gun).
   - Per-thread / per-layer table from the executive summary (Layer / Status / Owner with pills for ok/warn/fail).
   - Evidence section: E1, E2, E3, E4 each as an `<h2>` with its own table or `<details>` block — keep the verbatim quoted shell output in `<pre><code>`.
   - "Root cause" callout (accent border) summarizing the fix.
   - "Recommended fix" section with the code patch in `<pre><code>` (the same `_codex_sanitize_server_config` helper).
   - Timeline of the investigation (drawn from the markdown's structure — discovery cascade).
   - Footer: generated date, author `claude+codex`, link to predecessor handoff.

4. **Preserve all evidence verbatim.** The shell-output quotes, file paths, line numbers, JSONL excerpts — every concrete artifact must appear in the HTML byte-identical to the markdown. The HTML's job is structure + styling + readability, not editorial revision.

5. **Add the meta-tag header convention** (same as the handoff):
   ```
   <meta name="report-class" content="audit" />
   <meta name="report-date" content="2026-05-08" />
   <meta name="report-status" content="ok" />
   <meta name="report-title" content="codex-tools deep review — joint Claude + Codex report" />
   <meta name="report-kpi-summary" content="root cause identified · fix shipped via #1813 · joint claude+codex convergence" />
   <meta name="report-related-issues" content="1809,1811,1812,1815" />
   <meta name="report-related-prs" content="1813" />
   <meta name="report-agents" content="claude,codex" />
   <meta name="report-author" content="claude,codex" />
   <meta name="report-template-version" content="0.1" />
   ```

6. **Validation:**
   - File parses as valid HTML5 (test: `python3 -c "from html.parser import HTMLParser; HTMLParser().feed(open('REPORT.html').read())"` — no exceptions).
   - Visual sanity check: open in a browser (or use `lightpanda fetch --dump semantic_tree_text` if available) — every section header from the markdown must be findable in the rendered output.
   - Verbatim preservation check: `grep -c "type=\"streamable-http\""` ≥ 1, `grep -c "exec_command"` ≥ 3, `grep -c "rollout-2026-05-08"` ≥ 2 in the HTML.

7. **Commit + push + PR:**
   - `git add audit/codex-tools-review-2026-05-08/REPORT.html`
   - Commit: `docs(audit): backfill codex-tools review to HTML — #M-2 phase 3 (#1814)`
   - Push to `origin gemini/codex-tools-report-html-backfill`
   - `gh pr create --title "docs(audit): backfill codex-tools review HTML (#1814)" --body "First Phase 3 opportunistic backfill per MEMORY #M-2. Source REPORT.md preserved unchanged."`

8. **Do NOT delete the markdown.** Both files coexist (`.md` is the source-of-investigation, `.html` is the read-friendly artifact). Future links from session-state docs should prefer `.html`, but tools that already point to `.md` keep working.

## What to NOT do

- Do NOT edit `audit/codex-tools-review-2026-05-08/REPORT.md`. Read-only.
- Do NOT add Phase 4 interactivity (sliders, copy-as-prompt buttons, "re-dispatch" controls). That's a separate ticket.
- Do NOT add JavaScript. The artifact is static; if a section needs collapsibility, use native `<details>` (the handoff demonstrates this).
- Do NOT inline external fonts or fetch from CDNs. Use system font stacks only — same constraint as the handoff.
- Do NOT use placeholder content. Every section must reflect the actual markdown content; do not omit, summarize, or paraphrase the evidence.

## Reference

- Source markdown: `audit/codex-tools-review-2026-05-08/REPORT.md` (307 lines)
- Design reference: `docs/session-state/2026-05-09-overnight-codex-tools-and-html-migration.html`
- Meta-tag convention: documented in the handoff's "Show the meta-tag convention this file uses" `<details>`
- Article that justified the policy: `docs/references/external/2026-05-08-thariq-html-effectiveness.html`
- Umbrella issue: #1814 (HTML migration + nav UI)

Model: default Gemini sub. Effort: high (this is content writing — Gemini's strength).
