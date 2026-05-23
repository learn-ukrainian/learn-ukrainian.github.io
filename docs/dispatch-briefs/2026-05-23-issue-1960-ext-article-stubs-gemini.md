# Gemini dispatch — strip unreferenced `ext-article-N` stubs from wiki source registries (Option A of #1960, scoped-safe)

## Mission

Issue #1960 reports placeholder `ext-article-N` source entries (no `title`, no `url`) cluttering `wiki/pedagogy/**/*.sources.yaml` files. The issue offers three fix paths (A: strip / B: backfill / C: rebuild). Execute **Option A — but ONLY for stubs whose ID is NOT cited in the corresponding wiki text body.** Stubs that ARE cited would create dangling citations if stripped; those are out of scope for this PR (file a sibling issue for Option B if found). **Quality bar: every claim about an action taken is grounded in a tool result** (MEMORY #M-4).

## #M-4 deterministic preamble

| Claim in your output | Tool to ground it |
|---|---|
| "Stub X exists in file Y" | `grep -n 'ext-article-' wiki/pedagogy/<file>.sources.yaml` |
| "ID Sn IS referenced in wiki body" | `grep -F '[Sn]' wiki/pedagogy/<module>.md` and `grep -F 'Sn' wiki/pedagogy/<module>.md` |
| "Stub is SAFE to strip" | Both: (a) `title: ext-article-N` with no real title, (b) zero references in body |
| "Validator passes" | run the wiki manifest validator if one exists (look for `scripts/wiki/validate_*.py`) |
| "Tests pass" | `.venv/bin/python -m pytest tests/wiki tests/audit -q -k 'wiki or pedagogy or source'` final summary raw |

## Steps

1. Worktree already provided.
2. Enumerate affected files:
   ```
   grep -rln 'ext-article-' wiki/pedagogy/
   ```
   Paste the file list into your PR body.
3. For each affected file, identify which stub IDs are present:
   ```
   grep -nB1 -A3 'ext-article-' wiki/pedagogy/<file>.sources.yaml
   ```
   Note the `id:` field for each stub block (e.g. `S5`, `S6`, `S7`).
4. For each (file, id) pair, check whether the id is cited in the corresponding wiki body. The body file is the `.md` sibling of the `.sources.yaml` (e.g. `wiki/pedagogy/a1/my-morning.md` for `my-morning.sources.yaml`):
   ```
   grep -nF '[S5]' wiki/pedagogy/a1/my-morning.md
   grep -nF '[S6]' wiki/pedagogy/a1/my-morning.md
   ...
   ```
   Also check for `(S5)`, `S5,`, `S5.`, `S5 ` to catch alternate citation forms. Use a single regex if cleaner: `grep -nE '[\[\( ](S5|S6|S7)[\]\),. ]' wiki/pedagogy/<module>.md`.
5. Bucket each stub into TWO sets:
   - **SAFE-TO-STRIP**: stub ID has ZERO references in the wiki body. Strip it.
   - **UNSAFE**: stub ID HAS references. LEAVE IT in the YAML; record it for the followup issue (Option B scope).
6. For each SAFE stub, remove its block from the YAML (the 3-4 line entry starting `- id: Sn`). Preserve YAML formatting (trailing newlines, indentation).
7. After all edits, re-run the enumeration to confirm only UNSAFE stubs remain:
   ```
   grep -rln 'ext-article-' wiki/pedagogy/
   ```
   Paste before/after counts into the PR body.
8. Run targeted tests: `.venv/bin/python -m pytest tests/wiki/ tests/audit/ -q -k 'wiki or pedagogy or source' --timeout 60`. Paste the final summary line.
9. `.venv/bin/ruff check .` — should be clean (no python touched, hook may run).
10. `git add wiki/pedagogy/` (specific files, not -A)
11. `git commit -m "fix(wiki/pedagogy): strip unreferenced ext-article-N stubs (Option A of #1960)"`
12. `git push -u origin <your-branch>`
13. `gh pr create --title "fix(wiki/pedagogy): strip unreferenced ext-article-N stubs (Option A of #1960)" --body "<summary + before/after grep counts + unsafe-stubs list>"`
14. **NO auto-merge.** Orchestrator reviews.
15. If you found UNSAFE stubs (still-cited in body), file ONE followup issue titled `[wiki-ingestion] Option B followup — N ext-article-N stubs are cited in wiki body and need backfill` listing the (file, id, citation-line-numbers) tuples. Reference #1960. NO code in that issue — it's a tracking ticket.

## Hard scope limits

- ONLY `wiki/pedagogy/**/*.sources.yaml` edits + the followup issue (if needed).
- Do NOT touch the ingestion script. That's Option C scope.
- Do NOT edit any wiki `.md` body file to remove citations. That's a separate decision.
- Do NOT add real titles/URLs to remaining stubs. That's Option B scope and requires source-of-truth manifest data we may not have.

## Acceptance criteria

- ext-article-N stubs that have ZERO body references are removed.
- ext-article-N stubs that DO have body references are preserved with a followup issue tracking them.
- Test suite green.
- PR body has: before/after grep counts; list of files touched; list of UNSAFE stubs deferred (or "0 unsafe found" if none); link to followup issue if any.
