# Codex dispatch brief — #1722 vesum_verified tokenizer fix (postfix-aware)

> **Worktree:** `.worktrees/dispatch/codex/1722-vesum-postfix`
> **Branch:** `codex/1722-vesum-postfix`
> **Base:** `main`
> **Mode:** danger
> **Effort:** medium
> **Hard timeout:** 3600s (60 min)
> **Reviewer:** Claude (cross-family adversarial — invoked from inside this dispatch via `ask-claude`, then again post-PR by orchestrator)
> **No auto-merge.** Orchestrator (Claude) reviews CI + body, then merges.

---

## Context

The 2026-05-06 bakeoff at `audit/bakeoff-2026-05-05/` killed all 3 writers at the `vesum_verified` gate of `python_qg`. For Claude's `my-morning.md` output, the gate flagged 8 'missing' tokens:

```
"missing": ["Білоуса", "Дмитра", "вмиваєть", "прокидаюс", "прокидаєть", "тся", "ться", "шся"]
```

`шся`, `тся`, `ться` are not Ukrainian words — they're suffix fragments. `вмиваєть`, `прокидаюс`, `прокидаєть` are reflexive-verb stems WITHOUT the `-ся`. The tokenizer is splitting reflexive verbs at the `-ся` / `-сь` boundary and checking the fragments against VESUM.

`-ся` / `-сь` is a Ukrainian **postfix** — it's part of the verb form, not a separable suffix. Splitting at it is incorrect at the language level.

Plus `Білоуса` (genitive of `Білоус`) and `Дмитра` (genitive of `Дмитро`) are valid Ukrainian proper-noun cases that may not be in VESUM as surface forms.

This issue is the **terminal failure** for Claude (`correction_terminal: gate: vesum_verified` in `python_qg.json`). It will recur for every reflexive-verb-focused module.

Full analysis: GH #1722.

---

## Worktree setup (mandatory)

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin main
git worktree add -b codex/1722-vesum-postfix .worktrees/dispatch/codex/1722-vesum-postfix origin/main
cd .worktrees/dispatch/codex/1722-vesum-postfix
git log --oneline HEAD..origin/main           # MUST be empty
.venv/bin/python -c "import scripts.build.python_qg" || echo "module path may differ — locate the gate runner"
```

---

## Goal

Make the `vesum_verified` gate stop splitting reflexive verbs and stop blocking on proper-noun case forms.

---

## Investigation FIRST (don't write code blind)

1. **Find the gate.** Run:
   ```bash
   grep -rn "vesum_verified" scripts/build/ scripts/audit/ 2>&1 | head -10
   ```
   Locate the function that runs this gate. Likely in `scripts/build/python_qg.py` or `scripts/build/linear_pipeline.py` (where `_apply_python_qg_correction` lives at line 2380 of `linear_pipeline.py`).
2. **Find the tokenizer.** The gate calls a word-extractor that splits the module text. Find that function. Read it. Understand exactly how it splits.
3. **Find VESUM access.** The gate calls into `mcp__sources__verify_words` or directly into `data/vesum.db`. Confirm which.
4. **Run the failing case locally** to reproduce:
   ```bash
   .venv/bin/python -c "
   from scripts.build.python_qg import run_python_qg  # or whatever the entry point is
   # Re-run the gate against audit/bakeoff-2026-05-05/claude/module.md
   # Confirm you reproduce the 8 missing-words list
   "
   ```
   If you can't reproduce, STOP — the fix can't be tested. Diagnose why first.

---

## Required fixes

### Fix 1 — Don't split reflexive verbs

The tokenizer must treat `-ся` / `-сь` as INSIDE the verb token, not as a separator. Whatever the current splitting regex/logic is:

- **Don't split on `-`** between alphabetic Ukrainian characters where the right side is `ся` or `сь` (potentially with following inflection).
- The simplest correct rule: split on whitespace + standard punctuation only. **Hyphens and em-dashes inside Cyrillic words are part of the word.** Em-dash (`—`, U+2014) is sentence punctuation in Ukrainian; never inside a word, so it CAN split. ASCII hyphen `-` between Cyrillic letters is part of compound words (`синьо-жовтий`) — do NOT split.
- After tokenization, every form ending in `ся` or `сь` should be passed to VESUM as-is. VESUM's 6.7M-form table has these surface forms (e.g. `вмиваюся` is in VESUM).

Verify by querying VESUM directly:
```bash
.venv/bin/python -c "
from mcp_server.tools.sources.verify import verify_words
print(verify_words(['вмиваюся', 'прокидаєшся', 'вмивається', 'вмиваємося', 'вмиваєтеся', 'вмиваються']))
"
```
All 6 should resolve. If not, the VESUM table is missing something — diagnose; this brief assumes they DO resolve (per spec).

### Fix 2 — Allow proper-noun case forms

`Білоуса` (gen. of `Білоус`) and `Дмитра` (gen. of `Дмитро`) are valid Ukrainian declensions. Three options, in order of preference:

1. **Best**: VESUM has these surface forms — verify and use them. If `verify_words(['Білоуса', 'Дмитра'])` returns matches, the tokenizer fix above auto-fixes this.
2. **If VESUM doesn't have them**: add proper-noun lemmatization — the gate should normalize via `pymorphy3` (which handles Ukrainian morphology) before checking VESUM, so `Білоуса` → `Білоус` lemma → check that.
3. **Last resort**: check the plan's `dialogue_situations[].speakers` and the plan's `vocabulary_hints` for proper nouns. If `Білоус` (the lemma) appears, whitelist all morphological variants.

Verify with:
```bash
.venv/bin/python -c "
import pymorphy3
m = pymorphy3.MorphAnalyzer(lang='uk')
for word in ['Білоуса', 'Дмитра', 'Білоус', 'Дмитро']:
    parses = m.parse(word)
    print(word, '→', [(p.normal_form, p.tag.POS) for p in parses[:3]])
"
```

Pick the option that works for the data you actually have.

---

## Files to touch

Likely candidates (verify by grep first):

- `scripts/build/python_qg.py` — the gate logic.
- `scripts/build/linear_pipeline.py` — where `run_python_qg` and `_apply_python_qg_correction` live (lines 2752 and 2380 respectively per the line numbers we have).
- A tokenizer module — find via `grep -rn "extract_words\|tokenize\|_split_words" scripts/`.

---

## Tests (mandatory)

Add a new test file `tests/test_vesum_verified_postfix.py` (or extend an existing one if there's a clear home):

1. **`test_reflexive_verb_not_split`** — `вмиваюся`, `прокидаєшся`, `вмивається`, `вмиваємося`, `вмиваєтеся`, `вмиваються` all tokenize as single tokens (no `шся`/`тся`/`ться` fragments).
2. **`test_compound_hyphen_word_not_split`** — `синьо-жовтий`, `англо-український` tokenize as single tokens.
3. **`test_em_dash_splits_sentences`** — `Привіт — як справи?` em-dash splits.
4. **`test_proper_noun_genitive_resolves`** — `Білоуса`, `Дмитра` either resolve via VESUM or via pymorphy3 lemma normalization (whichever path you implement).
5. **`test_my_morning_module_passes_vesum_gate`** — fixture: `audit/bakeoff-2026-05-05/claude/module.md`. Run the gate. `vesum_verified.passed = true`.

---

## Validation before opening PR

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/1722-vesum-postfix
.venv/bin/python -m pytest tests/test_vesum_verified_postfix.py -v
.venv/bin/ruff check scripts/build/python_qg.py scripts/build/linear_pipeline.py
git diff --check
```

Then re-run python_qg against the bakeoff output to verify:

```bash
.venv/bin/python scripts/build/python_qg.py \
  --module audit/bakeoff-2026-05-05/claude/module.md \
  --plan curriculum/l2-uk-en/plans/a1/my-morning.yaml \
  --out /tmp/python_qg_post_fix.json
.venv/bin/python -c "
import json
data = json.load(open('/tmp/python_qg_post_fix.json'))
g = data['gates']['vesum_verified']
print('passed:', g['passed'], 'missing:', g['missing'])
assert g['passed'], f'still failing: {g[\"missing\"]}'
print('OK')
"
```

If `python_qg.py` doesn't have a CLI (likely — it's invoked from `linear_pipeline.py`), use whatever entry point exists. The point is: the prior `audit/bakeoff-2026-05-05/claude/python_qg.json` showed 8 missing tokens; the post-fix JSON should show 0 (or only legitimately-non-Ukrainian terms).

---

## Get Claude adversarial review

```bash
git -C /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/1722-vesum-postfix \
  diff origin/main..HEAD > /tmp/1722-diff.txt

cd /Users/krisztiankoos/projects/learn-ukrainian
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-claude \
  "Adversarial review for #1722. Read /tmp/1722-diff.txt. Focus: (A) is the tokenizer change correct for Ukrainian — what about the cases NOT covered (the verbs in -ться, -чся, -ться with consonant clusters)? (B) does the proper-noun fix add false positives — what if a writer cites a fictional name not in pymorphy3 / VESUM? (C) does the change touch any other gate or break existing tests? (D) coverage of the new tests — do they actually exercise the fix, or just assert the absence of the old bug?" \
  --task-id 1722-review \
  --model claude-opus-4-7
```

Apply feedback. Commit with `Reviewed-By: claude-opus-4-7 (1722-review)` trailer.

---

## Open PR

```bash
git push -u origin codex/1722-vesum-postfix

gh pr create \
  --title "fix(python_qg): vesum_verified treats -ся as postfix; allows proper-noun case forms (#1722)" \
  --body "$(cat <<'EOF'
## Summary

The `vesum_verified` gate of `python_qg` was splitting reflexive Ukrainian verbs at the `-ся` / `-сь` postfix and treating the suffix fragments (`шся`, `тся`, `ться`) as missing words. It also rejected proper-noun case forms (`Білоуса`, `Дмитра`).

This was the **terminal failure** for all 3 writers in the 2026-05-06 bakeoff (`audit/bakeoff-2026-05-05/{claude,gemini,gpt55}/python_qg.json`). Reflexive verbs are the central pedagogy of A1/20 (`my-morning`); the gate cannot block on them.

- Tokenizer no longer splits at `-ся` / `-сь` — these are postfixes, part of the verb form.
- Proper-noun case forms resolve via [VESUM surface lookup OR pymorphy3 lemma normalization — depending on what landed; note in PR body which].
- Compound hyphen-words (`синьо-жовтий`) preserved as single tokens.

## Test plan

- [ ] `pytest tests/test_vesum_verified_postfix.py -v` — 5 cases pass.
- [ ] Re-running python_qg on `audit/bakeoff-2026-05-05/claude/module.md` shows `vesum_verified: passed: true`.
- [ ] Existing `tests/test_python_qg*.py` (if any) still pass.

## Related

Closes #1722.
Companion to #1720 strand 1 — together these unblock the bakeoff.

Reviewed-By: claude-opus-4-7 (1722-review)
EOF
)"
```

DO NOT enable auto-merge.

---

## Risks

1. **VESUM might genuinely lack some forms.** If `verify_words(['вмиваюся'])` returns "missing", the issue is in the data, not the tokenizer. Diagnose first; don't paper over.
2. **pymorphy3 for Ukrainian is heuristic.** It's the standard tool but not perfect. If Fix 2 path 2 is taken, document that in code comments — surface novel false positives in the gate output.
3. **Other gates may use the same tokenizer.** If `russianisms_clean` / `surzhyk_clean` / `calques_clean` share the splitter, your fix may affect them — verify their tests still pass.

---

## Numbered checklist

1. `git worktree add ... origin/main`.
2. Verify `git log HEAD..origin/main` is empty.
3. Investigation phase — find gate, tokenizer, VESUM access, reproduce the 8 missing tokens.
4. Implement Fix 1 (postfix-aware tokenization).
5. Implement Fix 2 (proper-noun case forms — pick whichever path works for actual data).
6. Add 5 tests.
7. Run pytest + ruff + post-fix python_qg validation.
8. Get Claude adversarial review.
9. Apply review fixes.
10. `git push -u origin codex/1722-vesum-postfix`.
11. `gh pr create` (above body).
12. Do NOT enable auto-merge.
