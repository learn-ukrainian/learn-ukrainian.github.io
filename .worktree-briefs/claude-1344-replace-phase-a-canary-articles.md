# Dispatch brief — #1344: replace Phase A canary wiki articles

**Agent**: Claude
**Effort**: xhigh
**Model**: claude-opus-4-7
**Gate**: **DO NOT FIRE until #1455 (wiki review per-dim MIN) is merged.**
The rebuild must exercise the new per-dim MIN aggregation; the old
weighted-average path would mask low-scoring dims that matter for
factual/cultural accuracy.

---

## Why this exists

Four wiki articles were compiled by the **pre-Phase 2 pipeline** (before
the dimensional review system shipped) and committed as "Phase A canary
output" in commit `4a0c77b55`. They live in the retired path layout
(`wiki/figures/`, `wiki/linguistics/oes/`, `wiki/literature/works/`,
`wiki/periods/`) and have never passed source-grounding / factual-accuracy
/ ukrainian-perspective / register dim review.

Kept on disk only to prevent dangling curriculum-plan references; carry
a deprecation banner.

Canonical architectural destination per `docs/wiki-rebuild-plan.md`:
`wiki/pedagogy/{track}/{slug}.md` + sibling `wiki/pedagogy/{track}/{slug}.sources.yaml`,
with `wiki/.reviews/pedagogy/{track}/{slug}.json` carrying the 4-dim
review result.

Ticket: https://github.com/<org>/<repo>/issues/1344

---

## Pre-flight gate checks

```bash
# #1455 must be merged — old path would corrupt the rebuild
gh pr list --state merged --search '1455 in:title' --limit 5
# expect: the #1455 PR visible, state MERGED

# sources.db must be populated locally
test -f data/sources.db && \
  sqlite3 data/sources.db "SELECT COUNT(*) FROM textbook_sections LIMIT 1;"
# expect: > 0

# The 4 old articles must still exist (you're replacing, not re-creating)
ls wiki/figures/knyahynia-olha.md \
   wiki/linguistics/oes/walls-speak-intro.md \
   wiki/literature/works/introduction-to-kotliarevsky.md \
   wiki/periods/trypillian-civilization.md
```

If any gate fails, halt.

---

## Worktree setup

```bash
git fetch origin main
git worktree add -b claude-1344-replace-canary-articles \
    .worktrees/claude-1344-replace-canary-articles origin/main
cd .worktrees/claude-1344-replace-canary-articles
git log --oneline HEAD..origin/main   # MUST be empty
```

---

## The work

### Step 1 — Rebuild each canary article through the new pipeline

Four articles, four tracks. Each goes through `scripts/wiki/rebuild.py`
or `scripts/wiki/compile.py` (whichever the current rebuild orchestrator
uses for per-slug compile — check `scripts/wiki/rebuild.py` CLI help
for current form). Each must land at the NEW path with dim-review report.

| Old path | New path | Track (phase per rebuild.py) |
|---|---|---|
| `wiki/figures/knyahynia-olha.md` | `wiki/pedagogy/bio/knyahynia-olha.md` | `bio` (phase 4) |
| `wiki/linguistics/oes/walls-speak-intro.md` | `wiki/pedagogy/oes/walls-speak-intro.md` | `oes` (phase 6) |
| `wiki/literature/works/introduction-to-kotliarevsky.md` | `wiki/pedagogy/lit/introduction-to-kotliarevsky.md` | `lit` (phase 5) |
| `wiki/periods/trypillian-civilization.md` | `wiki/pedagogy/hist/trypillian-civilization.md` | `hist` (phase 4) |

Per-slug compile (recommended, finer control):

```bash
# Check rebuild.py CLI for current per-slug invocation form
.venv/bin/python scripts/wiki/rebuild.py --help
.venv/bin/python scripts/wiki/compile.py --help  # fallback if rebuild.py is orchestrator-only

# Then for each slug (adjust flag form to match current CLI):
.venv/bin/python scripts/wiki/compile.py --track bio --slug knyahynia-olha --dim-review
.venv/bin/python scripts/wiki/compile.py --track oes --slug walls-speak-intro --dim-review
.venv/bin/python scripts/wiki/compile.py --track lit --slug introduction-to-kotliarevsky --dim-review
.venv/bin/python scripts/wiki/compile.py --track hist --slug trypillian-civilization --dim-review
```

Each invocation must produce three artifacts:
- `wiki/pedagogy/{track}/{slug}.md`
- `wiki/pedagogy/{track}/{slug}.sources.yaml`
- `wiki/.reviews/pedagogy/{track}/{slug}.json` with all 4 dims showing
  `status: pass` (source_grounding, factual_accuracy, ukrainian_perspective,
  register)

**If any dim fails**: diagnose, do not publish. This is the whole point
of rebuilding through the new pipeline — if the new articles also fail
a dim, the old articles were worse and we learned something. Open a
sub-issue, leave the old article in place (banner still prevents
accidental consumption), halt this dispatch.

### Step 2 — Migrate curriculum plan references

Every curriculum plan that cites an old path must be updated.

```bash
# Find every reference to every old path prefix
grep -RnE 'wiki/figures/knyahynia-olha|wiki/linguistics/oes/walls-speak-intro|wiki/literature/works/introduction-to-kotliarevsky|wiki/periods/trypillian-civilization' \
    curriculum/ docs/ README.md
```

Update each match to the new `wiki/pedagogy/{track}/{slug}.md` path.
Per MEMORY code-editing-safety §4: grep is not an AST — run separate
searches for:
1. Direct path references
2. `slug` fields (e.g. `slug: knyahynia-olha`) — these reference slug
   without the track prefix; confirm the track field also changed
3. String literals in YAML values, comments in markdown, cross-refs in
   seminar frontmatter
4. `oes_mapping.yaml` specifically (mentioned in the issue)
5. `wiki/index.md` if it lists these articles

After updates, re-grep for the OLD paths — must return zero matches.

### Step 3 — Delete deprecated files

Once AC1 + AC2 complete, delete:

```bash
git rm wiki/figures/knyahynia-olha.md
git rm wiki/linguistics/oes/walls-speak-intro.md
git rm wiki/literature/works/introduction-to-kotliarevsky.md
git rm wiki/periods/trypillian-civilization.md

# Also delete the 6 companion review files from 4a0c77b55 under
# wiki/.reviews/{linguistics,literature,periods}/** (issue AC3)
git rm wiki/.reviews/linguistics/oes/walls-speak-intro.json 2>/dev/null || true
git rm wiki/.reviews/literature/works/introduction-to-kotliarevsky.json 2>/dev/null || true
git rm wiki/.reviews/periods/trypillian-civilization.json 2>/dev/null || true
git rm wiki/.reviews/figures/knyahynia-olha.json 2>/dev/null || true
# (Exact list of 6: check `git show 4a0c77b55 --stat | grep '\.reviews/'`)

# Also delete any sibling .sources.yaml for the old articles
git rm wiki/figures/knyahynia-olha.sources.yaml 2>/dev/null || true
git rm wiki/linguistics/oes/walls-speak-intro.sources.yaml 2>/dev/null || true
git rm wiki/literature/works/introduction-to-kotliarevsky.sources.yaml 2>/dev/null || true
git rm wiki/periods/trypillian-civilization.sources.yaml 2>/dev/null || true

# If any of the parent directories (wiki/figures/, wiki/periods/, etc.)
# are now empty AND the directory itself is deprecated by the
# architectural migration, remove them too. If they still contain
# other articles, leave them.
find wiki/figures wiki/linguistics/oes wiki/literature/works wiki/periods \
    -type d -empty -delete 2>/dev/null || true
```

### Step 4 — Regression check

For each of the 4 slugs, run the plan-level validation:

```bash
# If there are modules that consume these wikis, build-verify them:
# (Only necessary if the curriculum has modules pointing at these slugs
# as part of their plan.yaml source list.)
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/plans/bio/knyahynia-olha.yaml 2>&1
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/plans/oes/walls-speak-intro.yaml 2>&1
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/plans/lit/introduction-to-kotliarevsky.yaml 2>&1
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/plans/hist/trypillian-civilization.yaml 2>&1
# If audit_module.py does not accept a plan yaml as input, skip — the
# grep-based ref check in Step 2 is the equivalent.
```

### Step 5 — Lint + test

```bash
# Ruff on any script you modified (Step 2 may touch .py helpers)
.venv/bin/ruff check scripts/ --fix

# Citation invariant — if the new articles cite sources, they must
# resolve. This test is the real guard:
.venv/bin/pytest tests/test_citation_resolution_invariant.py -x -v
```

### Step 6 — Update `wiki/index.md` if it lists any of the 4

```bash
grep -n 'knyahynia-olha\|walls-speak-intro\|introduction-to-kotliarevsky\|trypillian-civilization' \
    wiki/index.md 2>&1
# If any match: update each listing to the new path + track.
```

---

## Commit + PR

```bash
git add -A  # OK here because all changes are curriculum/wiki content
git status  # REVIEW before committing; do not commit stray .pyc or .ruff_cache

git commit -m "$(cat <<'EOF'
feat(wiki): replace Phase A canary articles via dim-reviewed pipeline (#1344)

Closes #1344. Rebuilds four Phase-A-canary wiki articles through the
new per-dim-MIN review pipeline (post-#1455) and migrates them to the
`wiki/pedagogy/{track}/` path layout per `docs/wiki-rebuild-plan.md`.

Articles:
- knyahynia-olha (bio)
- walls-speak-intro (oes)
- introduction-to-kotliarevsky (lit)
- trypillian-civilization (hist)

Each new article has a passing 4-dim review
(`wiki/.reviews/pedagogy/{track}/{slug}.json`), migrated curriculum-plan
refs, deleted deprecated source files + companion review files.

Citation invariant (#1460) passes; no new KNOWN_DRIFT entries.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"

git push -u origin claude-1344-replace-canary-articles

gh pr create --title "feat(wiki): replace Phase A canary articles via dim-reviewed pipeline (#1344)" --body "$(cat <<'EOF'
## Summary

Closes #1344.

Rebuilds the 4 pre-Phase-2-canary wiki articles through the post-#1455
per-dim-MIN review pipeline and migrates them to the
`wiki/pedagogy/{track}/` layout.

- `knyahynia-olha` → `wiki/pedagogy/bio/`
- `walls-speak-intro` → `wiki/pedagogy/oes/`
- `introduction-to-kotliarevsky` → `wiki/pedagogy/lit/`
- `trypillian-civilization` → `wiki/pedagogy/hist/`

Each new article carries a passing 4-dim review. All curriculum-plan
refs migrated. Old files + companion review files deleted. Citation
invariant still clean.

## Test plan

- [ ] All 4 new articles at `wiki/pedagogy/{track}/{slug}.md`
- [ ] All 4 dim-review reports show all-4-pass
- [ ] `grep -R wiki/figures\|wiki/linguistics/oes\|wiki/literature/works\|wiki/periods curriculum/ docs/` — zero matches
- [ ] `pytest tests/test_citation_resolution_invariant.py` green
- [ ] `wiki/index.md` updated if it listed any of the 4

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

**DO NOT enable auto-merge.** User reviews and merges.

---

## Non-negotiables

- **#1455 MUST be merged first.** If not, halt.
- **Dim review must pass.** If a new article's dim review fails, open a
  sub-issue and halt — do not publish a failing article just to close
  #1344.
- **Grep for old paths after migration must return zero.** This is the
  AC2 invariant.
- **Delete the old files.** AC3 is explicit: keeping them around perpetuates
  the dead path.
- **Fetch-first + verify `HEAD..origin/main` empty** before starting.

Expected wall time: 2–3h xhigh (1h compile time across 4 articles, 30m
for grep + migration + file deletes, 30m for audit + test, 30m PR + CI
wait).
