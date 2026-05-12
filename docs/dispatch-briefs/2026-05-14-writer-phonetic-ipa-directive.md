# Codex dispatch brief — V7 writer phonetic-rule IPA directive + wiki-coverage gate hard-fail

> **Issue:** #1924
> **Mode:** danger
> **Worktree:** `.worktrees/dispatch/codex/writer-phonetic-ipa-2026-05-14/`
> **Base:** `origin/main` (currently `1d57748f6f`)
> **Hard timeout:** 5400s
> **Silence timeout:** 1800s
> **Effort:** high

---

## ⚠️ CRITICAL — fresh-shell behavior

Each bash block runs in a FRESH SHELL. CWD does NOT persist across blocks. Prefix every command with `cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/writer-phonetic-ipa-2026-05-14 && ...` or absolute path.

Inside the worktree, `.venv/` is gitignored. Use `/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python`.

---

## Goal

Close the **last** observed wiki-coverage gap from the 2026-05-12 first-ever V7 e2e build of `a1/my-morning`. The wiki-obligations-manifest restructure landed in #1920 drove text-contrast coverage from 0/6 → 4/6 (L2 errors) and 1/5 → 5/5 (sequence steps), but **phonetic_rules coverage stayed 0/3** because the writer emitted written forms (`-шся`, `-ться`) without their IPA spoken targets (`[с':а]`, `[ц':а]`). The wiki explicitly named the IPA as `критично важливо для англомовних учнів`. The writer just dropped it.

Two-part fix:

1. **Writer prompt** — add an explicit, hard directive that for every `phonetic_rules` obligation in the Wiki Obligations Manifest, the module MUST include the IPA spoken target verbatim (or an activity with both written and spoken forms in contrast).
2. **Deterministic gate** — `scripts/audit/wiki_coverage_gate.py` (shipped in #1920) should hard-fail when `spoken_present=false` on any phonetic obligation, even when other categories are in advisory mode. This converts "writer dropped the IPA" from a silent gap into a build halt the operator must address.

After this PR merges, the next V7 e2e rebuild of `a1/my-morning` should drive phonetic_rules coverage from 0/3 → 3/3 (and L2 errors err-2 and err-3 from missing → covered, since both are phonetic).

---

## #M-4 preamble — verifiable claims this work will produce

| Claim | Deterministic tool | Output format |
|---|---|---|
| "Writer prompt has explicit IPA-notation directive" | `grep -n -B1 -A4 -i 'IPA\|spoken target\|phonetic_rules\|\[с\|\[ц' scripts/build/phases/linear-write.md` shows new directive block | quote the new block verbatim |
| "Gate hard-fails on missing phonetic spoken target" | `grep -n -B1 -A6 -i 'phonetic\|spoken_present\|spoken_target' scripts/audit/wiki_coverage_gate.py` shows new failure path | quote the new condition |
| "Test covers the missing-IPA case" | new fixture test asserts: wiki manifest with `phonetic_rule.spoken_target='[с\':а]'`, module text WITHOUT that bracketed form → gate returns failure, with category=phonetic_rules in failure detail | quote the test + assertion |
| "Tests pass" | `.venv/bin/pytest tests/test_wiki_coverage* tests/test_*wiki* -x` | quote final summary line |
| "Lint clean" | `.venv/bin/ruff check scripts/build/phases scripts/audit/wiki_coverage_gate.py` | quote final line |

Inline "I checked X" claims without quoted raw output = hallucination per #M-4. Quote.

---

## Where to look

**Writer prompt:** `scripts/build/phases/linear-write.md`. Per #1920 the wiki manifest is now at the top of this prompt under `## Wiki Obligations Manifest` with `<implementation_map>` directives. The new IPA directive should slot in as a sub-section of the same block, NOT as a separate "rule" later in the file. Reference shape:

```md
### Phonetic rules — MUST emit IPA notation

For every entry under `phonetic_rules:` in the Wiki Obligations Manifest, the module
MUST include the spoken target verbatim in square brackets (e.g. `[с':а]`, `[ц':а]`)
alongside the written form (e.g. `-шся`, `-ться`). The IPA notation is what teaches
the pronunciation contrast for English-speaking learners — emitting only the written
form leaves the rule pedagogically useless.

Format requirements:
- Spoken target appears inside `[...]` brackets (single-character square brackets,
  not Unicode look-alikes).
- Pair the written and spoken form in close lexical proximity (same sentence or
  adjacent bullet), so the contrast is visible to the learner.
- If the wiki provides example word pairs (e.g. `сміється [с'м'ійец':а]`), copy at
  least one example verbatim into a vocabulary card or example sentence.

The deterministic wiki-coverage gate hard-fails when any phonetic_rule has
`spoken_present=false`. There is no advisory-mode escape for this category.
```

**Gate:** `scripts/audit/wiki_coverage_gate.py`. Per #1920 this gate consumes `wiki_manifest.json` and the assembled MDX. Find the per-category aggregation logic (likely `_check_phonetic_rules` or similar). Make `phonetic_rules` always HARD, even when `wiki_coverage_hard_fail` is False for other categories. The mode flag should still gate text-contrast etc., but phonetic must short-circuit to fail.

**Config:** `scripts/audit/config.py` and/or `scripts/config.py` SSOT — if there is a per-category enforcement flag (e.g. `WIKI_COVERAGE_PHONETIC_ALWAYS_HARD`), add one with default `True`. Otherwise inline the always-hard behavior. Pick whichever is cleaner.

**Test surface:** `tests/test_wiki_coverage_gate.py` (likely the home, created in #1920). Add fixtures for:
- Phonetic rule with spoken target present in module → pass.
- Phonetic rule with spoken target absent → fail, even when `hard_fail=False` for other categories.
- Phonetic rule with multiple example pairs from wiki, at least one present in module → pass.

---

## Fix shape — minimum viable

The fix is small in code surface (likely 20-40 LOC across prompt + gate + test). The bigger contract is **the right directive in the right place** so writers actually emit the IPA.

Prompt directive — emphasize:
- IPA is the contrast (written form alone is useless).
- Use square brackets `[...]` exactly.
- Pair within sentence-level proximity.

Gate hard-fail — short-circuit BEFORE the mode-dependent advisory branch.

Test — verify that `spoken_present=false` produces a failure regardless of the overall hard_fail flag.

---

## Numbered steps (mandatory checklist)

1. **Worktree setup:**
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian && \
   git worktree add -b codex/writer-phonetic-ipa-2026-05-14 .worktrees/dispatch/codex/writer-phonetic-ipa-2026-05-14 origin/main
   ```
2. **Read the relevant code:** `scripts/build/phases/linear-write.md`, `scripts/audit/wiki_coverage_gate.py`, `tests/test_wiki_coverage*.py`. Understand the current phonetic_rules handling before editing.
3. **Edit the prompt** — add the directive block at the right location inside the existing wiki-obligations section.
4. **Edit the gate** — short-circuit phonetic hard-fail.
5. **Add tests** — the 3 cases described above.
6. **Test suite:**
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/writer-phonetic-ipa-2026-05-14 && \
   /Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/pytest tests/test_wiki_coverage* tests/test_*wiki* -x
   ```
   Quote final summary line raw.
7. **Ruff:**
   ```bash
   /Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/ruff check scripts/build/phases scripts/audit/wiki_coverage_gate.py
   ```
   Quote final line raw.
8. **Regression check** — read `curriculum/l2-uk-en/a1/my-morning/wiki_manifest.json` from MAIN (read-only via absolute path) and confirm the 3 phonetic rules are present. State which 3 you found.
9. **Commit** — conventional message: `fix(writer+wiki-coverage): require IPA notation for phonetic_rules + hard-fail gate`. Reference `Closes #1924`.
10. **Push:** `git push -u origin codex/writer-phonetic-ipa-2026-05-14`.
11. **Open PR** via `gh pr create` with body containing: prompt-directive quote, gate-hard-fail quote, test summary, ruff summary, `Closes #1924`.
12. **DO NOT auto-merge.** Hand back for review.

---

## What blocks the merge

- Prompt directive in the wrong location (e.g. at end of file, where the writer's wiki-obligations consumption already happens to skip).
- Gate hard-fail can be silenced by `hard_fail=False` flag (must be unconditional for phonetic).
- Test coverage missing the `hard_fail=False` case.
- Tests failing.
- Ruff failing.

---

## Pre-submit checklist (per AGENTS.md:11-26)

- [ ] `.python-version` unchanged
- [ ] `.yamllint` / `.markdownlint.json` unchanged
- [ ] No `status/*.json` / `audit/*-review.md` files in diff
- [ ] No `sys.executable` — use `.venv/bin/python`
- [ ] No `@pytest.mark.skip` with empty `pass`
- [ ] Every changed file directly related to the directive + gate hard-fail
- [ ] Total files changed < 8

---

## Related

- Predecessor handoff: `docs/session-state/2026-05-13-night-wiki-obligations-e2e-brief.md`
- Wiki obligations manifest (just merged): #1920
- Companion in-flight bug fixes: #1925 (VESUM + fix-block, opens after this brief), #1926 (yaml_activities unjumble)
- Live wiki manifest for repro: `curriculum/l2-uk-en/a1/my-morning/wiki_manifest.json` (read-only reference)
