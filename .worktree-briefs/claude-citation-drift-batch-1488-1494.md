# Dispatch brief — batch-fix citation drift (#1488–#1494)

**Agent**: Claude
**Effort**: xhigh
**Model**: claude-opus-4-7
**Gate**: none — fire any time post-handoff. Orthogonal to ADR-007 /
colors pilot / wiki-pipeline work.

---

## Why this exists

PR #1497 shipped the citation-resolution invariant (#1460). On first
run against the existing `wiki/pedagogy/a1/` corpus, 7 articles had
unresolved `[S#]` citations — orphan inline refs (no registry entry)
or registry entries pointing at non-resolvable sources (dictionary
references, external articles).

To keep CI green while the invariant ships, the 7 violations were
captured in `tests/test_citation_resolution_invariant.py::KNOWN_DRIFT`
as xfail expectations + one GitHub issue per article (#1488–#1494).

This brief closes all 7 in one PR. After merge, the KNOWN_DRIFT dict
is empty and the invariant runs at strict for the entire A1 wiki
corpus.

---

## The 7 drifts

Per `tests/test_citation_resolution_invariant.py::KNOWN_DRIFT` and
issue bodies:

| Article | Issue | Drift class | Specific orphans |
|---|---|---|---|
| `wiki/pedagogy/a1/food-and-drink.md` | #1488 | external article unresolvable | `S12` → `ext-article-1` |
| `wiki/pedagogy/a1/hey-friend.md` | #1489 | orphan inline refs (no registry entry) | `S2447`, `S3165`, `S3336`, `S4715` |
| `wiki/pedagogy/a1/my-family.md` | #1490 | orphan inline refs | `S2435`, `S2452`, `S3129` |
| `wiki/pedagogy/a1/reading-ukrainian.md` | #1491 | external article unresolvable | `S12` → `ext-article-1` |
| `wiki/pedagogy/a1/stress-and-melody.md` | #1492 | orphan inline refs | `S606`, `S1503`, `S1548`, `S2298` |
| `wiki/pedagogy/a1/things-have-gender.md` | #1493 | malformed registry (`type: textbook-chunk` unsupported) + dictionary orphans `S7 (VESUM)`, `S8 (СУМ-11)` | see issue |
| `wiki/pedagogy/a1/who-am-i.md` | #1494 | dictionary orphans | `S8` (VESUM), `S9` (СУМ-11) |

---

## Pre-flight gate checks

```bash
# sources.db must be populated — citation resolution requires it
test -f data/sources.db && \
  sqlite3 data/sources.db "SELECT COUNT(*) FROM textbook_sections LIMIT 1;"
# expect: > 0

# The invariant test file and KNOWN_DRIFT dict must exist
test -f tests/test_citation_resolution_invariant.py && \
  grep -q 'KNOWN_DRIFT' tests/test_citation_resolution_invariant.py
# expect: exit 0

# Each article should still exist
for f in food-and-drink hey-friend my-family reading-ukrainian \
         stress-and-melody things-have-gender who-am-i; do
  test -f wiki/pedagogy/a1/$f.md || echo "MISSING: $f"
done
# expect: no MISSING lines
```

---

## Worktree setup

```bash
git fetch origin main
git worktree add -b claude-citation-drift-batch-1488-1494 \
    .worktrees/claude-citation-drift-batch-1488-1494 origin/main
cd .worktrees/claude-citation-drift-batch-1488-1494
git log --oneline HEAD..origin/main   # MUST be empty
```

---

## Per-article decision protocol

For each of the 7 articles, follow this decision tree:

### Step A — Read the article + its `.sources.yaml`

```bash
cat wiki/pedagogy/a1/<slug>.md
cat wiki/pedagogy/a1/<slug>.sources.yaml
```

Identify every inline `[S#]` reference and its surrounding sentence.
For each, answer: **does the prose actually need a citation here?**

### Step B — Classify each orphan

**Class 1: Prose needs a real citation.**
The factual claim or example is non-obvious and belongs under source
grounding.
- **Remediation**: search `sources.db` for a matching chunk using MCP
  tools (see §Authority hierarchy below). Register a new entry in
  `.sources.yaml` for the matching record. Update the `[S#]` inline
  ref if the registry numbering changes.

**Class 2: Prose does not need this citation.**
The claim is obvious from context or is a definition/heading that
doesn't cite anything specific. The `[S#]` was inserted mechanically
by the old pipeline.
- **Remediation**: remove the `[S#]` inline ref from the markdown
  entirely. If that leaves the `.sources.yaml` entry unreferenced,
  delete the registry entry too.

**Class 3: Prose needs a citation but no resolvable source exists.**
Dictionary references (VESUM, СУМ-11) currently don't resolve as
citations in this invariant because they aren't indexed in
`sources.db` the same way textbook_sections are. For now this is a
registry-layer problem, not an article-layer problem.
- **Remediation for #1493, #1494**: either (a) convert the dictionary
  cite to inline-text form ("per VESUM") and remove the `[S#]`, or
  (b) if we want structural dictionary citation support, open a new
  infra issue for adding dictionary-resolution to
  `wiki/source_attribution.resolve_chunk_attribution_any_corpus_with_conn`.
  **Recommendation**: remove per (a) for this batch; file the infra
  follow-up separately.

**Class 4 (only #1488, #1491): External article `ext-article-1`.**
This is a retired external-article reference. It likely points at a
source we no longer want to cite as authoritative.
- **Remediation**: remove the `[S#]` inline ref. If the prose claim
  needs grounding, find a textbook/literary/Wikipedia source to
  replace it. Otherwise drop.

**Class 5 (only #1493): Malformed registry.**
`type: textbook-chunk` is not a valid registry type; loader fails
before resolution can even attempt. Fix the registry schema first,
then classify remaining orphans per Step B normally.
- **Remediation**: change `type: textbook-chunk` to a supported type
  (check `wiki/sources_schema.py::load_sources_registry` for the
  permitted set — likely `textbook-section` or similar).

### Step C — Authority hierarchy for finding real sources

Per `claude_extensions/rules/mcp-sources-and-dictionaries.md`:

```
mcp__sources__search_sources  → start here; unified textbook + literary + wiki
mcp__sources__search_text     → textbook-only when you want scoped
mcp__sources__verify_word     → verify any Ukrainian word cited
mcp__sources__search_definitions → СУМ-11 (for definitions in prose)
mcp__sources__query_wikipedia → Ukrainian Wikipedia for cultural refs
```

For inline refs like `[S2447]` where `2447` is a textbook section ID
that no longer exists in the current `sources.db`, the `[S#]` is from
the old build's registry numbering — the prose needs either a new
current-DB lookup or removal.

### Step D — Edit the article + its `.sources.yaml`

Use the `Edit` tool per article. For each of the 7:

1. Read `wiki/pedagogy/a1/<slug>.md`
2. Read `wiki/pedagogy/a1/<slug>.sources.yaml`
3. Apply per Class 1–5 above.
4. **Re-read both files** after edits (per MEMORY code-editing-safety §2).
5. Sanity-check: every `[S#]` in the markdown now has a matching entry
   in `.sources.yaml`; every entry in `.sources.yaml` resolves.

---

## Step 2 — Remove KNOWN_DRIFT entries

Once an article's drifts are fixed, remove its entry from the dict.
Edit `tests/test_citation_resolution_invariant.py::KNOWN_DRIFT`:

```python
KNOWN_DRIFT = {
    # All 7 entries removed after fixing #1488–#1494.
}
```

If any article can NOT be fully fixed (e.g. dictionary orphans can't be
resolved without infra work), leave that article's entry but update the
fragments to reflect only the still-open drifts. Log why in the PR
body.

---

## Step 3 — Run the invariant locally

```bash
.venv/bin/pytest tests/test_citation_resolution_invariant.py -x -v
# expect: all tests pass (including the ex-KNOWN_DRIFT ones now
# running strict)
```

If any test fails: the article fix was incomplete. Re-read, re-edit,
re-test.

---

## Step 4 — Lint + broader test

```bash
.venv/bin/ruff check tests/test_citation_resolution_invariant.py
.venv/bin/ruff check scripts/ --fix

# Full pytest to confirm no unrelated regression
.venv/bin/pytest tests/ -x
```

---

## Step 5 — Close the 7 issues

In the commit message, reference all 7 issues with `Closes`. The
GitHub automation will close them when the PR merges.

---

## Commit + PR

```bash
git add -A
git status   # REVIEW

git commit -m "$(cat <<'EOF'
fix(wiki): resolve citation drift in 7 A1 articles (#1488–#1494)

Closes #1488, #1489, #1490, #1491, #1492, #1493, #1494.

The citation invariant (#1460/#1497) flagged 7 A1 wiki articles with
orphan inline [S#] refs or unresolvable registry entries. This PR
fixes each per the Class-1–5 remediation in the batch brief:

- food-and-drink.md: dropped S12 → retired ext-article-1
- hey-friend.md: removed 4 orphan inline refs (S2447 S3165 S3336 S4715)
- my-family.md: removed 3 orphan inline refs (S2435 S2452 S3129)
- reading-ukrainian.md: dropped S12 → retired ext-article-1
- stress-and-melody.md: removed 4 orphan inline refs (S606 S1503 S1548 S2298)
- things-have-gender.md: fixed malformed registry type + removed dictionary orphans
- who-am-i.md: removed dictionary orphans (S8 VESUM, S9 СУМ-11)

KNOWN_DRIFT dict emptied; invariant now runs strict for full A1 wiki
corpus.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"

git push -u origin claude-citation-drift-batch-1488-1494

gh pr create --title "fix(wiki): resolve citation drift in 7 A1 articles (#1488–#1494)" --body "$(cat <<'EOF'
## Summary

Closes #1488, #1489, #1490, #1491, #1492, #1493, #1494.

The citation invariant (#1460) flagged 7 A1 wiki articles. This PR
fixes each article's orphan / unresolvable citations and empties the
KNOWN_DRIFT xfail dict, flipping the invariant to strict for the full
A1 wiki corpus.

Per-article remediation is in the commit message. No prose-level
quality regression — each fix either replaced the orphan with a
resolvable source or removed the mechanically-inserted ref.

## Test plan

- [ ] `pytest tests/test_citation_resolution_invariant.py` green without xfails
- [ ] `git diff` on each of the 7 articles reviewed for prose sanity
- [ ] KNOWN_DRIFT dict empty (or shrunk with explicit PR-body justification for remaining entries)
- [ ] Full `pytest tests/` green

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

**DO NOT enable auto-merge.** User reviews and merges.

---

## Non-negotiables

- **Per-article judgement.** Do NOT just remove every orphan — that's
  the mechanical-fix pattern that caused the drift in the first place.
  For each `[S#]`, decide Class 1/2/3/4/5 based on the surrounding prose.
- **`<!-- VERIFY -->`** any Ukrainian word used in replacement citations
  per `ukrainian-linguistics.md` rule 1.
- **sources.db lookups for Class 1** use `mcp__sources__search_sources`
  first; do not invent records.
- **MEMORY code-editing-safety §2** — re-read each file after editing;
  max 3 edits per file without a full re-read.
- **Fetch-first + verify `HEAD..origin/main` empty** before starting.

Expected wall time: 3–4h xhigh (30m pre-flight + per-article reading,
20–30m per article × 7, 30m test + PR wait). Per-article time varies:
orphan removal is fast; replacement-with-real-source can take 20m of
MCP-search-and-verify work.
