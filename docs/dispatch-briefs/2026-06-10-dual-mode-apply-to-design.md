# Dispatch brief — Apply token authority to the design layer (tokens + Word Atlas POC dual-mode)

Authority/SSOT: `docs/best-practices/dual-mode-design-tokens.md` (read it if present; the canonical token
table is embedded below so this brief is self-contained). This step makes the **design layer** dual-mode.
**NO live page/route implementation in this dispatch** (that is the next one) — only the token definitions
+ the Word Atlas POC mockup.

## Task 1 — Define the semantic tokens in `starlight/src/css/custom.css`
Add to `:root` (light) and `[data-theme='dark']` (dark). Values are the authority:

| Token | Light | Dark |
|---|---|---|
| `--lu-bg` | `#ffffff` | `#0f0f1a` |
| `--lu-surface` | `#ffffff` | `#242526` |
| `--lu-surface-muted` | `#f8f9fa` | `#1a1a2e` |
| `--lu-border` | `#ebeced` | `#303846` |
| `--lu-text` | `#1c1e21` | `#e3e3e3` |
| `--lu-text-muted` | `#6b6b6b` | `#989898` |
| `--lu-primary` | `#0057B7` | `#5B9BD5` |
| `--lu-accent` | `#FFD700` | `#FFD700` |
| `--lu-on-accent` | `#1c1e21` | `#1c1e21` |
| `--lu-state-active` | `rgba(0,87,183,.08)` | `rgba(91,155,213,.22)` |
| `--lu-state-correct-bg` / `--lu-state-correct-fg` | `rgba(46,125,50,.08)` / `#2E7D32` | `rgba(46,160,70,.26)` / `#81C995` |
| `--lu-state-wrong-bg` / `--lu-state-wrong-fg` | `rgba(198,40,40,.08)` / `#C62828` | `rgba(210,70,70,.26)` / `#F28B82` |
| `--lu-state-missed` | `rgba(251,188,4,.15)` | `rgba(251,188,4,.22)` |
| `--lu-state-drag` | `rgba(106,27,154,.08)` | `rgba(167,130,224,.18)` |
| `--lu-match-right` | `rgba(230,81,0,.08)` | `rgba(230,145,56,.20)` |

Also: **extract** the per-section identity LIGHT hexes from the `.lu-hero` variants in
`starlight/src/styles/course.css` (core, lexicon, folk, lit, seminar, history) and **define a dark pair**
for each (desaturated/darkened so the hue stays legible on `--lu-bg`). Add as `--lu-id-<section>` light+dark.
**List every extracted-light + chosen-dark pair in the PR body for review** — do NOT invent the light values.

## Task 2 — Make `docs/poc/poc-word-atlas-design.html` DUAL-MODE
The POC currently shows light only. Make it show **both** themes (a `data-theme` toggle on the mockup, or
side-by-side light/dark frames) for all **3 views**, using the dark token values above. Specifically fix in
the dark frame: the **filter button** must use `--lu-on-accent` (dark text on the yellow `--lu-accent`) —
the current light-on-yellow is unreadable. UI labels in the mockup should be **Ukrainian** (e.g. `Фільтр`/
`Шукати`, not `Filter`).

## Task 3 — Verify
- Screenshot or render proof of the POC in **both** light and dark (both legible; WCAG-AA text contrast).
- `grep` the new tokens in `custom.css` (present in both `:root` and `[data-theme='dark']`).
- `npm run build:full --prefix starlight` final line raw (must stay green) + `npm test --prefix starlight`.
- Confirm NO live route/page was changed (only `custom.css` + the POC html + the authority doc).

## Numbered steps
1. Confirm `pwd` is the dispatch worktree.
2. Add the tokens to `custom.css`; extract+define section identities (list in PR).
3. Make the Word Atlas POC dual-mode (3 views, dark frame, `--lu-on-accent` filter button, Ukrainian labels).
4. Run the Task 3 verification (both-mode proof, build, tests).
5. `git add` incl. `docs/best-practices/dual-mode-design-tokens.md` if it is untracked on this branch
   (it is the SSOT — ensure it is committed).
6. `.venv/bin/ruff check` if any .py touched (none expected).
7. Commit (conventional + `X-Agent` trailer): `feat(design): dual-mode tokens + Word Atlas POC both-theme [token-authority]`.
8. `git push -u origin <branch>`; `gh pr create` with the section-identity table + both-mode screenshots. **DO NOT merge** — goes to review.
