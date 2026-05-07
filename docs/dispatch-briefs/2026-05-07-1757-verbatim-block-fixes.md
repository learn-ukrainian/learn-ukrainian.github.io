# Codex dispatch brief — PR #1757 BLOCK fixes (6 findings)

> **Worktree:** `.worktrees/dispatch/codex/1757-verbatim-fixes` (NEW — branch from `codex/1725-verbatim-quoting` head)
> **Branch:** `codex/1725-verbatim-quoting` (CONTINUE — push to existing branch, PR #1757 will update)
> **Base:** `main`
> **Mode:** danger
> **Effort:** medium
> **Hard timeout:** 7200s (2h)
> **Silence timeout:** 1800s

## Worktree setup

```bash
git fetch origin codex/1725-verbatim-quoting
git worktree add .worktrees/dispatch/codex/1757-verbatim-fixes codex/1725-verbatim-quoting
cd .worktrees/dispatch/codex/1757-verbatim-fixes
git rebase origin/main  # rebase on latest main first
```

Commit and push to the same branch — PR #1757 will pick up the new commits automatically.

## Why

PR #1757 received 6 BLOCK findings from Claude Opus adversarial review (`audit/reviews/1757-verbatim-review.result` — also posted as comment on the PR). Each is gameable in production OR introduces a permablock. List below.

## Files in scope

The textbook-grounding gate is in `scripts/build/linear_pipeline.py` (search for `_contains_textbook_quote`, `_reference_matches_search_call`, `_search_textbook_hits`, A1 fallback). Tests in `tests/test_textbook_grounding_gate.py`. Fixtures in `tests/fixtures/textbook_grounding/`. Read the existing diff at `gh pr diff 1757` first.

## BLOCK findings (must fix)

### BLOCK 1: Reference-binding via query-text loophole

**Problem:** `_reference_matches_search_call` does substring match against `query_text + result_text` combined. Putting the reference title in the query satisfies the gate even if the search returned content from a different textbook.

**Fix:** Match against `result_text` ONLY (or against `result.source` / `result.metadata` if those carry the textbook identifier). Never count a match that comes purely from the query text.

**Test:** `test_query_only_reference_match_rejected` — feed a tool-call where `query_text="Караман Grade 10"` and `result_text` is from Захарійчук. Assert no match.

### BLOCK 2: No source_type filter at gate time

**Problem:** Gate counts blockquotes matched against wiki/literary search results equally. The packet-build time filter doesn't help here.

**Fix:** When extracting matched results in the gate, require `result.source_type == "textbook"` (or whatever the equivalent type field is — inspect `mcp__sources__search_text` schema). Non-textbook results don't count.

**Test:** `test_wiki_result_does_not_satisfy_gate` — feed a tool-call returning a wiki chunk with verbatim text. Assert no match.

### BLOCK 3: A1 fallback gameability

**Problem:** A1 fallback accepts ANY blockquote matching ANY search call regardless of reference, attributes to `references[0]`. Reported `matched` field misleading.

**Fix:** Two options — pick (b):
  (a) Remove the A1 fallback entirely.
  (b) Keep the fallback but make attribution truthful: report which reference the quote actually matched (or "unattributed" if it matched none). Don't lie about `references[0]`.

**Test:** `test_a1_fallback_attributes_to_actual_match` — quote matches `references[1]`'s search result; assert reported attribution is `references[1]`, not `references[0]`.

### BLOCK 4: No topical-relevance check

**Problem:** A 30-token excerpt about Soviet-era farming passes a module on зворотні дієслова as long as it's verbatim from a cited textbook.

**Fix:** Compare quote against the module's section title or the writer's `<plan_reasoning>` topic. Use a simple keyword overlap (Jaccard / cosine over lemma tokens). Threshold: at least 1 content word from quote must appear in section_title OR plan_reasoning. Document the threshold; reviewers can tune it.

NOT a full semantic-similarity model — too heavy. Lemma-overlap is good enough to catch the cross-topic gaming case.

**Test:** `test_off_topic_quote_rejected` — verbatim quote from a real textbook chunk on Soviet farming; section_title is "Reflexive Verbs". Assert rejection with reason "topical_mismatch".

### BLOCK 5: Permablock for missing corpus

**Problem:** If the cited textbook isn't in `sources_db`, packet emits "*No textbook excerpt found*", writer can't verbatim-quote, gate REJECTs forever. B1+ permablocked.

**Fix:** Add a corpus-availability check at packet-build time. If a reference's textbook isn't in `sources_db`, mark the reference with `corpus_missing: true`. At gate time, if a reference has `corpus_missing: true`, downgrade its requirement (count it as satisfied with a WARN flag). Module audit logs the downgrade so it's visible — not silently bypassed.

Alternative: add `verbatim_required: false` on individual `references[i]` entries; gate respects that flag. Use whichever fits the existing schema cleaner.

**Test:** `test_missing_corpus_does_not_permablock` — cited textbook absent from sources_db; assert gate passes with WARN, not REJECT.

### BLOCK 6: Stress-mark tokenization mismatch

**Problem:** Token regex `[0-9A-Za-zА-Яа-яҐґЄєІіЇї'ʼ'-]+` doesn't include combining diacritics (U+0301 etc.). Module-corpus stress drift causes false negatives.

**Fix:** Normalize both module text and search-result text via `unicodedata.normalize('NFD', text)` then strip combining marks (or use `NFKC` if you want to preserve them but treat them transparently). Apply the SAME normalization to both sides before tokenization. Do not include combining marks in the regex character class — strip them first.

**Test:** `test_stress_marks_do_not_break_matching` — module has `при́клад`, corpus has `приклад`. After normalization, 30-token windows match.

## NIT findings (worth fixing in same PR)

- Per-section trace overwrite: `module_dir/writer_tool_calls.json` is overwritten on each `invoke_writer`. Append per-section, not overwrite. Test for it.
- Apostrophe normalization: `’` → `'` and `ʼ` → `'` before tokenization. Test for it.
- Empty references = pass: add a hard rule "B1+ plans must declare ≥1 reference" — fail the gate (or fail an earlier plan-validation step) if missing.

## QUESTION finding (defer to follow-up issue if intentional)

`required = len(references)` for B1+. If the user designed this as a cliff, leave it. If untested, file a follow-up issue with a `min_required_per_level` config proposal.

## Validation before push

```bash
.venv/bin/pytest tests/test_textbook_grounding_gate.py -v  # all existing + new tests pass
.venv/bin/pytest tests/test_writer_correction_no_op_diagnostic.py tests/test_prompt_template_render.py tests/test_prompt_cot_tier1_scaffolding.py tests/test_no_rewrite_contract.py -v  # regression
.venv/bin/ruff check scripts/build/linear_pipeline.py
git diff --check
```

Confirm `git log --oneline origin/main..HEAD` shows reasonable commit count (≥1 per BLOCK fix is fine — separate commits help review).

## After push

PR #1757 will update with the new commits. Comment on the PR with:
- Mapping: which commit fixes which BLOCK finding
- Confirmation each new test exists and passes
- A note on the QUESTION finding (kept as-is OR follow-up issued)

NO auto-merge. Orchestrator (Claude) reviews + merges after a second adversarial pass.
