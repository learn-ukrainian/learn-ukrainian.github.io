# Codex dispatch brief — #1723 citations_resolve loads plan references

> **Worktree:** `.worktrees/dispatch/codex/1723-citations-from-plan`
> **Branch:** `codex/1723-citations-from-plan`
> **Base:** `main` (after strand 1 + #1722 merge)
> **Mode:** danger
> **Effort:** medium
> **Hard timeout:** 3600s (60 min)
> **Reviewer:** Claude (cross-family adversarial — invoked from inside this dispatch via `ask-claude`)
> **No auto-merge.**

---

## Context

The 2026-05-06 bakeoff at `audit/bakeoff-2026-05-05/claude/python_qg.json` failed `citations_resolve` with this output:

```json
"citations_resolve": {
  "passed": false,
  "unknown": [
    "Караман, Українська мова, 10 клас, с. 176",
    "Кравцова, Українська мова, 4 клас, с. 113",
    "Захарійчук, Українська мова, 4 клас, с. 162"
  ]
}
```

But the plan at `curriculum/l2-uk-en/plans/a1/my-morning.yaml` declares those exact references:

```yaml
plan_references:
  - title: Караман Grade 10, p.176
    notes: ...
  - title: Кравцова Grade 4, p.113
  - title: Захарійчук Grade 4, p.162
```

The resolver isn't loading the plan's references as the allowlist. Or it's doing string-exact matching: writer's full citation form (`Караман, Українська мова, 10 клас, с. 176`) doesn't equal the plan's compact form (`Караман Grade 10, p.176`).

This means **a writer cannot pass `citations_resolve` by quoting the exact textbook the plan told it to use.** Self-defeating gate.

---

## Worktree setup (mandatory)

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin main
git worktree add -b codex/1723-citations-from-plan .worktrees/dispatch/codex/1723-citations-from-plan origin/main
cd .worktrees/dispatch/codex/1723-citations-from-plan
git log --oneline HEAD..origin/main           # MUST be empty
```

---

## Goal

Make `citations_resolve` accept any citation that matches a `plan_references[]` entry by **author + grade + page** — tolerating Cyrillic/Latin punctuation, "Grade 10" vs "10 клас", "p.176" vs "с. 176", and presence/absence of the textbook subject ("Українська мова").

---

## Investigation FIRST

1. **Find the gate.** `grep -rn "citations_resolve" scripts/build/ scripts/audit/` — locate the function.
2. **Find the citation extractor.** It pulls quoted-citation strings out of `module.md`.
3. **Find the resolver.** It checks each citation against some source-of-truth — find what that source-of-truth currently IS (probably a static list or a pre-built corpus index).
4. **Reproduce the failure.** Run python_qg against `audit/bakeoff-2026-05-05/claude/module.md` with plan `curriculum/l2-uk-en/plans/a1/my-morning.yaml`. Confirm citations_resolve fails with the same 3 unknowns.

---

## Required fix

### 1. Load plan references as the allowlist

When citations_resolve runs, it must be passed the plan's `plan_references` (or `references` — verify the field name in plans like `curriculum/l2-uk-en/plans/a1/my-morning.yaml` and `b2/*.yaml`). Each entry has at minimum a `title`. Build a normalized matcher from each.

### 2. Normalized matching

Define a normalization function that extracts `(author, grade, page)` from any citation string in either of these surface forms:

- Plan-compact: `Караман Grade 10, p.176`
- Writer-expanded: `Караман, Українська мова, 10 клас, с. 176`
- Writer-Latin-mixed: `Karaman Ukrainian language, Grade 10, p.176`
- Writer-Cyrillic-only: `Караман, 10 клас, стор. 176`

Strategy:
- **Author**: first surname-shaped capitalized word (Cyrillic or Latin). `Караман` / `Karaman`.
- **Grade**: integer 1-11 followed by `clas`/`клас`/`Grade`/`grade` (in either order, either side of the integer).
- **Page**: integer following `p.`/`с.`/`стор.`/`page`/`сторінка`.

Match if author (case-insensitive, after Cyrillic-Latin fold) AND grade AND page all match an entry from `plan_references`.

Author folding: handle Cyrillic ↔ Latin transliteration only if both forms appear in the corpus. For the reference set (Караман, Кравцова, Захарійчук, Білоус, Заболотний, Авраменко, Вашуленко) just the Cyrillic forms suffice — but a future-proof matcher would handle Latin too.

### 3. Don't break absent-reference catching

If a writer cites `Tolstoy, War and Peace, p.500` and that's not in the plan, `citations_resolve.unknown` should still contain it. The fix expands what's accepted, not what's rejected.

---

## Files to touch

- `scripts/build/python_qg.py` (or `linear_pipeline.py` if the gate lives there) — gate function.
- A new helper module if the matcher gets >50 LOC: `scripts/build/citation_matcher.py`.
- `tests/test_citation_resolve.py` (or extend an existing test file).

---

## Tests

1. **`test_plan_compact_form_matches_writer_expanded`** — plan: `Караман Grade 10, p.176`; writer: `Караман, Українська мова, 10 клас, с. 176` → match.
2. **`test_grade_word_order_tolerated`** — `10 клас` vs `Grade 10` → match.
3. **`test_page_label_variants`** — `p.176` vs `с. 176` vs `стор. 176` → all match.
4. **`test_unknown_citation_still_rejected`** — citation absent from plan → still in `unknown`.
5. **`test_my_morning_module_passes_citations_resolve`** — fixture: `audit/bakeoff-2026-05-05/claude/module.md` + plan `my-morning.yaml`. Gate passes.
6. **`test_partial_match_does_not_pass`** — author matches but grade or page doesn't → rejected (don't accept partial matches; that's a security risk for fabricated citations).

---

## Validation

```bash
.venv/bin/python -m pytest tests/test_citation_resolve.py -v
.venv/bin/ruff check scripts/build/
git diff --check
```

Then re-run python_qg against bakeoff output to confirm the gate now passes. Same pattern as #1722 brief.

---

## Get Claude adversarial review

```bash
git -C /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/1723-citations-from-plan \
  diff origin/main..HEAD > /tmp/1723-diff.txt

cd /Users/krisztiankoos/projects/learn-ukrainian
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-claude \
  "Adversarial review for #1723. Read /tmp/1723-diff.txt. Focus: (A) is the normalization function tight enough to prevent fabricated-citation laundering — e.g. writer cites 'Караман Grade 10 p.999' when the plan only declares p.176? (B) does the matcher handle the Латинські lookalikes attack — Cyrillic 'К' vs Latin 'K'? (C) test coverage of the negative space — are unknown citations still surfaced? (D) does the change touch the source-of-truth corpus list, and if so does it break existing tests?" \
  --task-id 1723-review --model claude-opus-4-7
```

Apply feedback. Commit with `Reviewed-By: claude-opus-4-7 (1723-review)` trailer.

---

## Open PR

`fix(python_qg): citations_resolve loads plan_references as allowlist with author+grade+page matching (#1723)`

NO auto-merge. Orchestrator merges after CI green.

---

## Risks

1. **Fabricated citations.** Writer might cite a real author with a fake page number. The matcher rejects that — partial matches don't pass. Verify the test for this case.
2. **Corpus-list collision.** If there's an existing static corpus list (`scripts/build/corpus_authors.py` or similar), the new plan-loaded path must coexist with it. Don't replace; extend.
3. **Plan field name drift.** Some plans may have `references`, others `plan_references`. Handle both. Verify by `grep -l 'plan_references\|references:' curriculum/l2-uk-en/plans/`.
