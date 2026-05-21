# Dispatch brief — fix text-pdf parser column-flow / lemma extraction bugs

**Agent**: codex (gpt-5.5, xhigh)
**Mode**: danger
**Worktree**: `.worktrees/dispatch/codex/esum-textpdf-column-flow-2026-05-21` (REQUIRED)
**Task ID**: `esum-textpdf-column-flow-2026-05-21`
**Created**: 2026-05-21 night

## Why

User goal: link vocabulary words in V7 lesson MDX → corresponding `/etymology/<slug>/` page. Coverage probe on current corpus (after PRs #2195 + #2196 + commit `583fa3d698`) found only 20-40% of vocab words have an extractable etymology slug — and the gap is largely **lemma-extraction bugs in the text-pdf parser**, not missing source data.

The smoking gun: `субота` ("Saturday") is one of the most common Ukrainian words. It IS in the source text:

```
data/raw/esum/ia-text-pdf/vol5-text.txt:98288: субота, ісобітна «вогнище на Ку-
```

But it does NOT appear as a lemma in `data/processed/esum_vol5.jsonl`. Direct `grep "lemma\": \"субота\"" data/processed/esum_vol*.jsonl` returns nothing.

Other common words with the same problem on spot-check: `кава` (yes, it IS there), but examples like `рік`, `дім`, `день`, `день`, etc. need verification.

## Two root causes

### Root cause #1: blank-line-as-continuation in text-pdf mode

`scripts/ingest/esum_ingest.py::_clean_lines` lines ~233-241:

```python
if not line:
    if source_format == "text-pdf":
        continue  # <-- blank lines SKIPPED, carry continues
    if carry:
        cleaned.append((current_page, carry.strip()))
        carry = ""
    cleaned.append((current_page, ""))
    continue
```

In text-pdf mode, blank lines do NOT terminate the carry. So a paragraph like:

```
спорідненого
                ← blank
субота, ісобітна «вогнище на Ку-
                ← blank
пала» Куз, ...
```

gets merged into one carry `спорідненого субота, ісобітна «вогнище на Ку- пала» ...`, and `_extract_headword` picks `спорідненого` as the lemma (it's the leading token before `,`). `спорідненого` is a participle continuation from the previous entry — not a real headword.

### Root cause #2: column-break artifacts → mashed and fragmented lemmas

`pdftotext` (without `-layout`) walks two-column ESUM print in reading order: column 1 top-to-bottom, then column 2 top-to-bottom. At column transitions:

- **Word-fragment artifacts**: hyphenated words at end of column 1 get split — `ка`, `рай`, `тин`, `від`, `ем`, `мов`, `не`, `мак` (real samples from `data/processed/esum_vol5.jsonl`). These short tokens look like lemmas because `_extract_headword` cuts at the first `,` / `;` / `(` / `—` / `«`.
- **Mashed lemmas**: end of column 1 + start of column 2 join without a separator → `дорізькийізйре`, `гневразнийодраза`, `дорізнийчіткий` (real samples). The parser treats the concatenated string as a single headword.

PR #2195's `_is_sane_lemma` doesn't catch these because (a) they're pure Cyrillic (no Latin/digit triggers) and (b) the min-length is 1 (too lenient for text-pdf).

## What

### Investigation phase (do this first; ~30 min)

1. Run a coverage probe on the current corpus: how many common A1 vocabulary words (sample list below) extract correctly?

   Sample words to verify: `субота, кава, рік, дім, день, мати, батько, ранок, вечір, ніч, зима, літо, осінь, весна, хліб, вода, око, рука, нога, голова, дитина, чоловік, жінка, родина, друг, школа, місто, село, річка, ліс, поле, сонце, місяць, вітер, дощ, сніг, вогонь, дерево, квітка, трава`.

   Expected: most should resolve to a clean lemma in the JSONL. Document which are missing, which have garbage lemmas, which are correctly extracted.

2. For each missing word, find it in `data/raw/esum/ia-text-pdf/vol{N}-text.txt` and document which root cause hits: blank-line concat (#1), column-fragment (#2), or other.

### Implementation phase

Fix the parser in `scripts/ingest/esum_ingest.py`:

#### Fix A — entry-start break across blank-line carries

In text-pdf mode, if the current line starts with a strong entry-start pattern (Cyrillic word + `,` + Cyrillic continuation, OR `[` + Cyrillic + `]` bracketed-headword form), emit the current carry first and start a new paragraph WITH this line. Don't merge it into the previous carry.

Concretely, add to `_clean_lines` text-pdf branch:

```python
def _looks_like_strong_entry_start_textpdf(line: str) -> bool:
    """Cyrillic headword + comma + Cyrillic continuation; or [bracketed]."""
    # plain headword pattern
    m = re.match(r"^([а-яґіїєА-ЯҐІЇЄ'’]{2,20}[1-9!?-]?)\s*[,;]\s*[а-яґіїєА-ЯҐІЇЄ\[«]", line)
    if m: return True
    # bracketed headword pattern (text-pdf converts | → [ in ESUM)
    m = re.match(r"^\[[а-яґіїєА-ЯҐІЇЄ'’]{2,20}\]?\s*[«,]", line)
    return bool(m)
```

Wire it into the blank-line block so blank+strong-entry-start emits the carry:

```python
if not line:
    if source_format == "text-pdf":
        # peek-ahead: if next non-blank line is a strong entry start, treat
        # blank as a paragraph break here.
        continue  # keep behavior, but defer the real decision to the
                  # strong-entry-start check on the NEXT non-blank line
    ...
```

Actually the cleaner formulation: in the non-blank branch, BEFORE adding to carry, check if `_looks_like_strong_entry_start_textpdf(line)`. If yes AND we have a non-empty carry that doesn't end with a hyphenated split, flush the carry first.

#### Fix B — tighten short-lemma rejection

In `_is_sane_lemma`:
- Reject lemmas of length 2-3 unless they're in a small allowlist of real ESUM short headwords. Build the allowlist empirically: scan vol1-6 raw text for entries that legitimately have 2-3 char lemmas — `ох`, `ой`, `аж`, `ой`, `ну`, `ще`, `як`, `що`, `він`, `вон`, `ого`, `ага`, `ан`, `ах`, `ой`, `гей`, `ой`, `ой`, etc. (Limit to ~30 entries. Cross-check with VESUM short-form lemmas.)
- Reject lemmas that fail VESUM lemma lookup AND aren't in the allowlist AND aren't a recognizable Slavic root pattern. This is conservative — many real ESUM lemmas are archaisms/dialectisms NOT in VESUM, so the filter should be: short + not-in-VESUM + not-in-allowlist.

#### Fix C — detect mashed lemmas at column breaks

When a candidate lemma has length > 12 chars (anomalously long for a single Ukrainian root) AND contains a recognizable VESUM lemma as a prefix, split at the prefix boundary:

```
дорізькийізйре → split at дорізький (VESUM lemma) → reject the suffix as separate token; if the suffix is also a VESUM lemma, emit two entries.
гневразнийодраза → split at гневразний → suffix одраза is another VESUM lemma → maybe emit both.
```

Practically: try greedy-longest-prefix VESUM match; if the residue is also a VESUM lemma, the original was a column-mash and we drop it (emit nothing for that candidate — the real entries appear elsewhere).

#### Don't

- Don't change the djvutxt branch — its semantics are settled and the deployed djvutxt source files have been deleted (only re-downloadable from IA).
- Don't widen the entry-start regex to catch single-word headwords without punctuation context — too many false positives on continuation participles.
- Don't apply Fix C to short candidate lemmas — it's a fix for the anomalously-long mash case, not for normal entries.

### Acceptance gates

1. **Investigation report in PR body**: which of the 40 sample words extract correctly, before vs after. Target: ≥ 35/40 correctly extracted after fix.
2. **`субота` specifically**: must appear as a lemma in `data/processed/esum_vol5.jsonl` (or wherever it lives) after the fix, with correct etymology body.
3. **Column-fragment lemmas removed**: `ка`, `рай`, `тин`, `від`, `ем`, `мов`, `не`, `мак` no longer appear as lemmas in vol5.
4. **Mashed lemmas removed**: `дорізькийізйре`, `гневразнийодраза`, `дорізнийчіткий` no longer appear as lemmas.
5. **No legitimate-entry regressions**: existing tests + the noise-filter tests in `tests/ingest/test_esum_noise_filters.py` + the ABBYY + djvutxt regression tests all pass.
6. **Total entry count delta**: corpus should be within ±15% of current 34,197 (the fix mostly REJECTS noise and FIXES boundary-misses; net could be slight up or down).
7. **Pytest + ruff green.**

DO NOT regenerate `data/processed/*.jsonl` or `data/sources.db` as part of this dispatch — leave the full corpus reload to a Claude follow-up commit.

### Verification before commit

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian && .venv/bin/ruff check scripts/ingest/ tests/
cd /Users/krisztiankoos/projects/learn-ukrainian && .venv/bin/python -m pytest tests/ -k esum -v --tb=short
# Smoke run all 6 vols:
for vol in 1 2 3 4 5 6; do
  cd /Users/krisztiankoos/projects/learn-ukrainian && .venv/bin/python scripts/ingest/esum_ingest.py --input data/raw/esum/ia-text-pdf/vol${vol}-text.txt --output /tmp/esum_vol${vol}_fixed.jsonl --vol ${vol} --source-format text-pdf 2>&1 | tail -1
done
wc -l /tmp/esum_vol{1..6}_fixed.jsonl
# Verify the 40 common words from the investigation phase appear correctly:
cd /Users/krisztiankoos/projects/learn-ukrainian && .venv/bin/python -c "
import json
TARGETS = ['субота', 'кава', 'рік', 'дім', 'день', 'мати', 'батько', 'ранок', 'вечір', 'ніч', 'зима', 'літо', 'осінь', 'весна', 'хліб', 'вода', 'око', 'рука', 'нога', 'голова', 'дитина', 'чоловік', 'жінка', 'родина', 'друг', 'школа', 'місто', 'село', 'річка', 'ліс', 'поле', 'сонце', 'місяць', 'вітер', 'дощ', 'сніг', 'вогонь', 'дерево', 'квітка', 'трава']
found = set()
for vol in range(1, 7):
    with open(f'/tmp/esum_vol{vol}_fixed.jsonl') as f:
        for line in f:
            d = json.loads(line)
            l = d['lemma'].rstrip('123456789!?-')
            if l in TARGETS: found.add(l)
print(f'found: {len(found)}/40 ({100*len(found)/40:.0f}%)')
print('missing:', sorted(set(TARGETS) - found))
"
```

## Commit + PR shape

- **Branch**: `feat/esum-textpdf-column-flow-fix-2026-05-21`
- **One commit**.
- **PR title**: `fix(esum): text-pdf column-flow boundary detection + short-lemma + mashed-lemma filter`
- **PR body**: investigation report (40 sample words before/after), per-vol entry count delta, sample of newly-correctly-extracted lemmas, sample of removed garbage.
- **Do NOT auto-merge.**

## Steps (mandatory)

1. `git worktree add -B feat/esum-textpdf-column-flow-fix-2026-05-21 .worktrees/dispatch/codex/esum-textpdf-column-flow-2026-05-21 origin/main`
2. Investigation: 40-word probe + raw-text inspection for missing ones; document root cause per case.
3. Implement Fix A (entry-start break across blanks).
4. Implement Fix B (short-lemma + VESUM-aware filter).
5. Implement Fix C (mashed-lemma detection) — optional if Fix A+B already get ≥35/40 acceptance.
6. Add unit tests for each fix.
7. Run verification commands.
8. Single conventional commit.
9. `git push -u origin feat/esum-textpdf-column-flow-fix-2026-05-21`
10. `gh pr create --title ... --body ...` (NO auto-merge).
11. Report task done with the 40-word coverage number quoted verbatim from the smoke-run.

## Anti-fabrication (per #M-4)

Every "tests pass" / "ruff clean" / "субота correctly extracted" / "40-word coverage = N/40" claim MUST be backed by literal command output (cmd + cwd + raw last lines). Quote `grep` raw output for the test lemmas, pytest summary line, ruff "All checks passed!", and the actual 40-word coverage script output. Don't paraphrase.
