# Codex dispatch brief — #1828 strip dark-theme CSS from playground HTMLs (post-#1839)

**Background:** PR #1839 fixed `playgrounds/index.html` by replacing inline dark CSS with the shared `/monitor.css` parchment palette. Three other files still carry the legacy pattern and rely on `!important` overrides in `monitor.css`. This is a maintenance trap. See full issue body via `gh issue view 1828`.

**Files to fix (mirror the index.html pattern from PR #1839):**
- `playgrounds/orient.html`
- `playgrounds/channels.html`
- `playgrounds/comms.html`

## Worktree

You start in `.worktrees/dispatch/codex/1828-css-dark-theme-cleanup/` on branch `codex/1828-css-dark-theme-cleanup`. Do NOT `cd` out.

## Reference implementation

Read `playgrounds/index.html` on `main` (post-#1839). Specifically look at:
- The `<head>` block — `<link rel="stylesheet" href="/monitor.css">` is loaded; inline `:root { --bg: #0d1117; ... }` is gone.
- The `<style>` block kept ONLY layout/component-specific CSS, NOT theme variables.
- The top-bar / monitor-nav structure.

Apply the same shape to the three target files. Each will need:
1. Remove the inline `:root { --bg, --bg2, --bg3, --border, --text, --text2, --text3, --green, --blue, --red, --yellow, --gray, --purple, --orange, --cyan }` definitions — those come from `/monitor.css` now.
2. Add `<link rel="stylesheet" href="/monitor.css">` if not already present.
3. Replace any `var(--blue)` → `var(--accent)` (and similar) where the file currently uses dark-theme accent colors.
4. Strip ANY `!important` declaration that was a workaround for dark-theme inline styles. After the cleanup, the parchment styles should win on specificity alone.
5. Keep file-specific layout/component CSS (e.g., grid templates, transitions) — those are NOT dark-theme.

## Test plan

Existing test: `tests/test_monitor_ui_contracts.py` already has assertions for `index.html`. Add equivalent contract tests for `orient.html`, `channels.html`, `comms.html`:

- `<link rel="stylesheet" href="/monitor.css">` present
- `#0d1117` NOT present (the dark-theme regression guard)
- Whatever monitor-nav structure each file needs

Pattern to mirror: the existing `test_index_page_uses_shared_parchment_monitor_design` test. Add three more parametrized over the three filenames.

## Numbered steps

1. Verify worktree branch.
2. Read `playgrounds/index.html` (current main) for the reference pattern.
3. For each of the three target files:
   - Read current state.
   - Strip dark-theme `:root` block + any `!important` workarounds.
   - Confirm `monitor.css` link present.
   - Replace dark accent colors with parchment equivalents.
   - Visually verify (lightpanda or similar) — files render with parchment palette.
4. Add 3 new contract tests (parametrize, or 3 separate functions — match the file's style).
5. Run: `.venv/bin/pytest tests/test_monitor_ui_contracts.py -v` → all pass.
6. Ruff: `.venv/bin/ruff check tests/`.
7. Commit (single conventional):
   ```
   fix(ui): strip dark-theme CSS from orient/channels/comms playgrounds (#1828)

   Mirrors the index.html cleanup from #1839 across the remaining three
   playground HTMLs. Removes inline :root dark-theme color vars and any
   !important workarounds — monitor.css parchment palette wins on
   specificity now.

   Adds contract tests asserting #0d1117 stays out of each file.

   Closes #1828
   Refs #1839 (the index.html fix that established this pattern)
   ```
8. `git push -u origin codex/1828-css-dark-theme-cleanup`.
9. `gh pr create --title "..." --body "..."`. Reference this brief + #1839. Do NOT auto-merge.

## What NOT to do

- Do NOT touch `playgrounds/monitor.css` itself — the goal is for inline styles to NOT need !important overrides; the global stylesheet stays as-is.
- Do NOT change behavior — these are pure styling cleanups.
- Do NOT add new HTML structure (top-bar, hero, etc.) unless it's required for parchment-theme parity. Match what the file currently has, just retheme it.
- Do NOT enable auto-merge.

## Acceptance criteria

- [ ] `playgrounds/orient.html` — dark-theme `:root` removed, `monitor.css` linked, no `!important` workarounds, visual parchment.
- [ ] Same for `playgrounds/channels.html`.
- [ ] Same for `playgrounds/comms.html`.
- [ ] Three new contract tests in `tests/test_monitor_ui_contracts.py`.
- [ ] All existing tests still pass.
- [ ] Ruff clean.
