# Codex dispatch brief — #1724 immersion gate dialogue-aware sentence splitter

> **Worktree:** `.worktrees/dispatch/codex/1724-immersion-splitter`
> **Branch:** `codex/1724-immersion-splitter`
> **Base:** `main` (after strand 1 + #1722 + #1723 land)
> **Mode:** danger
> **Effort:** medium
> **Hard timeout:** 3600s (60 min)
> **Reviewer:** Claude (cross-family adversarial via `ask-claude`)
> **No auto-merge.**

---

## Context

The 2026-05-06 bakeoff at `audit/bakeoff-2026-05-05/claude/python_qg.json` failed `immersion`:

```json
"immersion": {
  "passed": false,
  "pct": 23.28,
  "min_pct": 15,
  "max_pct": 35,
  "long_ukrainian_sentences": [...]
}
```

The Ukrainian percentage (23.28) is **within tolerance** (15-35). The gate fails because `long_ukrainian_sentences` contains 5 entries — but they're FALSE POSITIVES. The sentence splitter joins dialogue turns and table rows into mega-sentences:

```
'Що ти робиш потім?**\n— **Вмиваюся, одягаюся, снідаю.**\n— **А коли ти йдеш на роботу?**\n— **О восьмій'
```

That's 4 distinct dialogue turns concatenated by the splitter because line-leading em-dash (`—`) isn't being treated as a sentence boundary.

Conjugation tables are similarly merged: a markdown table with one verb form per row gets scanned as one continuous "sentence."

**This means writers cannot pass `immersion` for any module that uses dialogues (every A1 module per pedagogy) or conjugation tables (most A1 grammar modules). Self-defeating gate.**

---

## Worktree setup (mandatory)

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin main
git worktree add -b codex/1724-immersion-splitter .worktrees/dispatch/codex/1724-immersion-splitter origin/main
cd .worktrees/dispatch/codex/1724-immersion-splitter
git log --oneline HEAD..origin/main           # MUST be empty
```

---

## Goal

Make the immersion gate's sentence splitter recognize Ukrainian dialogue and table structure. Stop counting concatenated dialogue turns or table rows as one sentence.

---

## Investigation

1. Find the gate: `grep -rn "immersion\|long_ukrainian_sentences" scripts/build/ scripts/audit/`.
2. Find the sentence splitter — it's whatever the gate calls to break text into sentences before length-checking.
3. Reproduce the failure: run python_qg against `audit/bakeoff-2026-05-05/claude/module.md` (and `gpt55/module.md` and `gemini/module.md` for variety). Confirm the same false-positive long-sentences in each.

---

## Required fix

The splitter must recognize these as **hard sentence boundaries** in Ukrainian text:

1. **Line-leading em-dash** (`^\s*—\s+` or `^\s*[—–]\s*\*\*`) → dialogue speaker change. Each dialogue turn is its own sentence/line, regardless of trailing punctuation.
2. **Markdown table row separator** (`\n\|` after `\n\|---`) → each row is independent.
3. **Bullet/numbered list item start** (`^[*-] ` or `^\d+\. `) → each item is independent.
4. **Blockquote prefix** (`^>\s*`) when followed by another `^>` → each quoted line is a separate unit (especially for dialogue inside `> **Speaker:** ...`).
5. **Markdown headers** (`^#{1,6} `) → terminate the prior sentence.

After splitting, evaluate "long sentence" only on what's left — a single dialogue turn, a single table cell's text, a single bullet item.

### Optionally: drop content-inside-fences from the count entirely

Code fences (```` ``` ```` blocks) shouldn't contribute to immersion-gate length checks at all. They're code, not prose. If the current splitter doesn't strip them, do it.

---

## Files to touch

- `scripts/build/python_qg.py` (or wherever `immersion` lives) — gate function.
- The sentence splitter — find via grep.
- Possibly a new `scripts/build/sentence_split.py` if the splitter gets dedicated.
- `tests/test_immersion_splitter.py` (or extend existing).

---

## Tests

1. **`test_em_dash_line_start_is_sentence_boundary`** — input: `Що ти робиш?\n— Вмиваюся.\n— Снідаю.` → 3 sentences, none "long."
2. **`test_markdown_table_rows_split`** — input: a 4-row table → 4 sentences (or some number ≥ rows), no merged-table mega-sentence.
3. **`test_bullet_items_split`** — input: 3 bullets → 3 sentences.
4. **`test_blockquote_dialogue_split`** — input: `> **Ліна:** A.\n> **Настя:** B.` → 2 sentences.
5. **`test_code_fence_excluded_or_split`** — code fence content doesn't appear as a "long sentence."
6. **`test_real_long_sentence_still_caught`** — a 400-character continuous Ukrainian paragraph IS flagged as long. (Don't lose the gate's actual purpose.)
7. **`test_my_morning_immersion_passes`** — fixture: bakeoff `claude/module.md`. Gate passes (or fails for the right reasons — overall pct outside range, NOT phantom long sentences).

---

## Validation

```bash
.venv/bin/python -m pytest tests/test_immersion_splitter.py -v
.venv/bin/ruff check
git diff --check
```

Re-run python_qg on bakeoff outputs:

```bash
for w in claude gemini gpt55; do
  .venv/bin/python -c "
# pseudocode: run python_qg, print immersion result
"
done
```

Each writer's `immersion` should either pass or fail for legitimate reasons (e.g. genuinely too many English sentences) — not for splitter false positives.

---

## Get Claude adversarial review

```bash
git -C /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/1724-immersion-splitter \
  diff origin/main..HEAD > /tmp/1724-diff.txt

cd /Users/krisztiankoos/projects/learn-ukrainian
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-claude \
  "Adversarial review for #1724. Read /tmp/1724-diff.txt. Focus: (A) does the splitter handle three-em-dash variants — em-dash (—), en-dash (–), hyphen-as-dash (-) at line start? (B) what about Ukrainian quotation marks («») wrapping a dialogue line — does that interfere? (C) are the splitter's regex anchors correct (^ requires multiline flag)? (D) does the change preserve the gate's ability to flag REAL long sentences — confirm test #6 actually exercises that?" \
  --task-id 1724-review --model claude-opus-4-7
```

Apply feedback. Commit with `Reviewed-By: claude-opus-4-7 (1724-review)` trailer.

---

## Open PR

`fix(python_qg): immersion sentence splitter recognizes dialogue turns + table rows + bullets (#1724)`

NO auto-merge.

---

## Risks

1. **Over-splitting.** If the splitter becomes too aggressive, the immersion percentage calculation might also change (more sentences → different averaging). Verify the `pct` calculation isn't affected.
2. **Existing tests.** The splitter may be shared with other gates. Run the full pytest suite, not just immersion tests.
3. **Code-fence stripping (if implemented)** could affect other gates that also process the writer output. Coordinate by leaving the strip behavior gate-local.
