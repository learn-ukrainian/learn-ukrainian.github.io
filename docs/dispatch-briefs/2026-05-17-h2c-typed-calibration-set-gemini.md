# Dispatch brief: H2c — typed Russianism calibration set (Stage 1: authoring)

**Agent:** Gemini headless (`gemini-3.1-pro-preview`)
**Mode:** `--mode danger` (worktree-isolated)
**Base branch:** `main`
**Task ID:** `h2c-typed-calibration-authoring-2026-05-17-v3`

> **REVISION (v3):** v1 cancelled (only style_guide attestation). v2 cancelled (added Antonenko prose, but UA-GEC corpus was overlooked — that's ~6.5K human-annotated F/Calque + F/Style + F/Collocation triples from Grammarly Ukraine's MIT corpus, the largest single Russianism evidence source on our disk). v3 corrects step 5 to require attestation across ALL THREE channels: structured + prose + UA-GEC. The H2 dispatch (PR #2049, `audit/2026-05-17-judge-calibration-h2/COMPARISON.md`) confirmed UA-GEC F/Calque hits become cited evidence on sev≥2 flags (1-2 citations per cell). For H2c authoring, UA-GEC is the densest attestation source — many phraseological calques only appear there.

## Why this work — root cause from H1

The 2026-05-17 H1 calibration A/B (PR #2046, `audit/2026-05-17-judge-calibration-h1/COMPARISON.md`) revealed that the **calibration set itself is the bottleneck**, not the judge prompt or the model. On the existing 12-case set (`eval/russianism/calibration-cases.jsonl` at `origin/pr-2006`):

- 5 of 6 models converged on identical F1 scores under the H1 strict-evidence rule (F1=0.118, P=1.0, R=0.0625)
- Only 2 of 12 cases had ANY evidence anchor under the strict rule
- The set is dominated by lexical/phraseological/register calques — which the morphology-and-style-guide evidence channels can't anchor

Per user analysis (2026-05-17): "the calibration set itself is the bottleneck — we can't optimize the prompt without knowing what we're optimizing against. The current 12 cases over-represent lexical/register calques (because that's what Antonenko documents), which means H1 looks terrible on this set even though it likely wins on morphological russianisms."

**H2c hypothesis:** build a 30-50 case set spanning all 4 russianism types in balanced proportions. Re-run baseline + H1 against the new set. Predict: H1 wins on morphological cells, loses on phraseological/register cells, and the per-channel coverage metrics reveal which evidence channel each type needs.

## Deterministic claims this work will produce (#M-4)

| Claim | Required evidence |
|---|---|
| "40 cases authored in correct schema" | `wc -l eval/russianism/calibration-cases-h2c.jsonl` returns 40 (one JSON per line) |
# venv symlinked into worktree by delegate.py
| "Schema validation passes" | `.venv/bin/python -c "import json; [json.loads(l) for l in open('eval/russianism/calibration-cases-h2c.jsonl')]; print('OK')"` prints OK |
| "10 cases per russianism type" | `jq -r '.gold.expected_flags[].type' eval/russianism/calibration-cases-h2c.jsonl \| sort \| uniq -c` shows ≥10 per type bucket |
| "Each flag has cited source" | `jq -r 'select(.gold.expected_clean==false) \| .gold.source' eval/russianism/calibration-cases-h2c.jsonl \| sort -u` lists ≥5 distinct sources, all containing "Antonenko" or "Pravopys" or "Karavansky" or "ESUM" |
| "Tests pass" | raw `pytest tests/audit/` summary line |
| "PR opened" | raw `gh pr view --json url` URL line |

## Numbered execution steps

### 1. Worktree
Dispatch system creates `.worktrees/dispatch/gemini/h2c-typed-calibration-authoring-2026-05-17/` from main.

### 2. Data symlinks (sparse worktree)

```
[ -L data/sources.db ] || { rm -f data/sources.db; ln -s /Users/krisztiankoos/projects/learn-ukrainian/data/sources.db data/sources.db; }
[ -L data/vesum.db ]   || { rm -f data/vesum.db;   ln -s /Users/krisztiankoos/projects/learn-ukrainian/data/vesum.db   data/vesum.db; }
[ -L data/ua-gec ]     || { rm -f data/ua-gec;     ln -s /Users/krisztiankoos/projects/learn-ukrainian/data/ua-gec     data/ua-gec; }
```

### 3. Read the existing 12-case set as exemplar

```
git fetch origin 'refs/pull/2006/head:refs/remotes/origin/pr-2006'
mkdir -p eval/russianism
git show origin/pr-2006:eval/russianism/calibration-cases.jsonl > /tmp/existing-12-cases.jsonl
cat /tmp/existing-12-cases.jsonl | jq -r '.prompt_id + " | type=" + (.gold.expected_flags[0].type // "clean") + " | " + .output_text'
```

Study the format carefully. Note the field shape:
```json
{
  "prompt_id": "cal_<bucket>_<short_id>",
  "model": "GOLD",
  "status": "ok",
  "output_text": "<2-4 sentences of realistic Ukrainian prose>",
  "gold": {
    "expected_clean": true|false,
    "expected_flags": [
      {
        "phrase": "<exact substring of output_text>",
        "correct": "<canonical Ukrainian alternative>",
        "severity": 1|2|3,
        "type": "<one of the 4 types — see spec below>"
      }
    ],
    "rationale": "<1-2 sentences explaining the call>",
    "source": "<Antonenko / Pravopys §N / Karavansky chapter X / ESUM vol Y / etc.>"
  }
}
```

### 4. Author the 40-case H2c set

**Output file:** `eval/russianism/calibration-cases-h2c.jsonl` (NEW; do not modify `calibration-cases.jsonl`).

**Bucket structure (40 cases total):**

| Bucket | Dirty cases | Clean lure cases | Notes |
|---|---:|---:|---|
| Morphological | 8 | 2 | Case agreement, preposition government, declension, verbal aspect surface |
| Lexical | 8 | 2 | Single-word Russian loans that are morphologically valid Ukrainian (e.g. `забір`, `прийом`, `слідуючий`) |
| Phraseological | 8 | 2 | Multi-word fixed expressions that are literal calques (`повістка дня`, `у вкладенні`, `велика компанія`) |
| Register/stylistic | 8 | 2 | Grammatically correct but Russian-flavored register (`викликати занепокоєння`, overuse of `повинен`) |

**Total: 32 dirty + 8 clean lures = 40 cases.**

**Type definitions — be strict:**

- **morphological**: the surface FORM is wrong — case ending, preposition choice, participle form, verb aspect. Example: `на наступному тижні` (locative-after-`на`) → `наступного тижня` (genitive). Detectable by morphological analysis; VESUM-unknown candidate possible.
- **lexical**: SINGLE TOKEN is a Russian loan that's morphologically valid Ukrainian on the surface, but the WORD is wrong. Example: `забір крові` → `взяття крові` (забір = fence in Ukrainian, not "drawing"). Antonenko entry or attested lexical contrast.
- **phraseological**: MULTI-WORD fixed expression that's a literal Russian calque. Example: `повістка дня` → `порядок денний` (1-to-1 calque of `повестка дня`). Not detectable from any single token — needs phrase-level recognition.
- **register/stylistic**: grammatically correct, lexically valid, but the COMBINATION sounds Russian-translated rather than native Ukrainian. Example: `викликають занепокоєння` → `непокоять / турбують` (the verb-noun collocation is a calque of `вызывают беспокойство`). Stylistic preference, often sev 1-2.

**Clean lure cases** (2 per bucket): use the CORRECT form that contrasts with the dirty cases in the same bucket. E.g. lexical-clean lure: a sentence using `взяття крові` correctly. This catches over-eager judges.

### 5. Source attestation — REQUIRED per dirty case

Each dirty case MUST have a `source` that you VERIFIED via the THREE available evidence channels before writing. Per the H2 finding (PR #2049 COMPARISON.md), UA-GEC produces 1-2 of the most-cited anchors per cell on sev≥2 flags — for phraseological calques it's often the ONLY documented source.

```python
# For each dirty case, before adding to JSONL:
# 1. Identify the russianism phrase
# 2. Look up the canonical correction across ALL THREE channels:

# (a) Structured Antonenko entries (342 keyed headwords):
mcp__sources__search_style_guide(query="<russianism keyword>", limit=5)

# (b) Antonenko PROSE corpus (169 page chunks — different content from (a)):
mcp__sources__search_text(
    query="<russianism keyword>",
    source_file="antonenko-davydovych-yak-my-hovorymo",
    limit=5,
)

# (c) UA-GEC F/Calque + F/Collocation + G/Case + G/Gender annotations
#     (~5K human-annotated error pairs from Grammarly UA):
#     Parse data/ua-gec/data/{gec-fluency,gec-only}/{train,test}/annotated/*.ann
#     for the inline {ORIGINAL=>CORRECTED:::error_type=F/Calque} markers.
#     If your dispatch worktree doesn't symlink data/ua-gec, add the symlink
#     in step 2 BEFORE running this lookup:
#         [ -L data/ua-gec ] || ln -s /Users/krisztiankoos/projects/learn-ukrainian/data/ua-gec data/ua-gec
#
#     Quick parser snippet (use in a Bash one-liner or python):
#         grep -ohE '\{[^{}]+=>[^{}]*:::error_type=F/(Calque|Collocation)\}' data/ua-gec/data/**/annotated/*.ann | \\
#             grep -i "<keyword>"
#     OR cleaner: use PR #2049's _ua_gec_calque_search if those scripts are on
#     the branch your worktree is based on — but they may not be on main yet.

# (d) Fallback if (a) (b) (c) all empty:
mcp__sources__query_pravopys(query="<grammar rule keyword>")
# OR ESUM volume for etymology arguments
# OR (separate decision) Karavansky — NOT yet ingested per issue #2048

# 3. The `source` field MUST contain a real entry id, prose chunk_id,
#    UA-GEC ann file path, or section number — NOT a generic citation. Examples:
#    "Antonenko style_guide entry 'наступний'"                       (from (a))
#    "Antonenko prose chunk_id 26159 — 'наступних виданнях'"          (from (b))
#    "UA-GEC F/Calque: 'повістку дня → порядок денний' (0921.a2.ann)" (from (c))
#    "Pravopys 2019 §123 (case after на)"                             (from (d))

# 4. PREFER UA-GEC for phraseological calques (the H2 finding shows
#    style_guide + prose miss most phraseological flags; UA-GEC is the
#    densest source for the phraseological bucket).
#    PREFER style_guide for headword-level lexical russianisms.
#    PREFER prose for register/stylistic rules with discussion.
```

If a phrase CANNOT be attested in any of these sources, do NOT include it as a dirty case. Use a different example. This is critical — fake sources poison the calibration set.

**Why three channels matter for H2c specifically:** the H1 finding (COMPARISON.md, PR #2046) proved 14 of 16 calibration flags lacked structured-table anchors. H2 (COMPARISON.md, PR #2049) recovered ~3.5× by adding prose + UA-GEC, but `antonenko_prose` earned 0 citations across all 6 cells while UA-GEC earned 1-2 per cell — so for H2c source-distribution, **UA-GEC F/Calque is the densest attestation channel**, structured headwords second, prose third. Author the 40 cases knowing which channel WILL anchor each flag in production.

### 6. Quality criteria

- **Realistic register**: each case should sound like real workplace/personal Ukrainian text. Not pedagogical-constructed; not contrived. A native speaker reading it should think "I've seen this in actual emails/conversations."
- **Single-cause cases**: each dirty case should have 1-3 expected_flags max. Don't pile every kind of russianism into one sentence.
- **Spaced flag types**: across the 8 dirty cases per bucket, vary the severity (mix of sev 1, 2, 3) and the surface (different prepositions, different lexical pairs, etc.).
- **Proper-noun safety**: do NOT use proper nouns whose form contrasts with common nouns (e.g. avoid `Львова` vs `львова`). If you must use a place name, choose unambiguous nominative forms.
- **No archaisms / dialectisms**: stay in modern standard Ukrainian. The calibration tests RUSSIANISM detection, not heritage-defense edge cases.

### 7. Write the JSONL

Output exactly 40 lines, one JSON object per line, NO trailing newline after last line, NO blank lines, NO comments.

After writing, validate:

```
wc -l eval/russianism/calibration-cases-h2c.jsonl   # expect 40
# venv symlinked into worktree by delegate.py
.venv/bin/python -c "import json; lines = open('eval/russianism/calibration-cases-h2c.jsonl').readlines(); assert len(lines) == 40; [json.loads(l) for l in lines]; print('40 lines, valid JSON each')"
jq -r '.gold.expected_flags[]?.type' eval/russianism/calibration-cases-h2c.jsonl | sort | uniq -c
# expect approximately:
#  ≥8 morphological
#  ≥8 lexical
#  ≥8 phraseological
#  ≥8 register
```

### 8. Add a README

Write `eval/russianism/calibration-cases-h2c.README.md`:

```markdown
# H2c Typed Russianism Calibration Set

40 cases (32 dirty + 8 clean lures) spanning 4 russianism types:
morphological / lexical / phraseological / register.

Authored 2026-05-17 in response to H1 falsification finding
(audit/2026-05-17-judge-calibration-h1/COMPARISON.md): the existing
12-case set (origin/pr-2006:eval/russianism/calibration-cases.jsonl) is
dominated by lexical/phraseological cases that the morphology + style-guide
evidence channels structurally can't anchor.

H2c balances the type buckets to reveal per-channel coverage gaps:
which evidence channel each russianism type actually needs.

## Schema

(reproduce the JSONL schema from the dispatch brief here)

## Per-type test plan

After this lands, run baseline + H1 prompts against this set:

    # venv symlinked into worktree by delegate.py
    .venv/bin/python scripts/audit/judge_calibration_matrix.py \\
      --out-dir audit/2026-05-17-judge-calibration-h2c-baseline \\
      --families anthropic,openai,google,xai \\
      --models claude-opus-4-7,gpt-5.5,gemini-3.1-pro-preview,grok-4.3 \\
      --harnesses native_cli \\
      --efforts high \\
      --mcp-states with_mcp \\
      --cases-file eval/russianism/calibration-cases-h2c.jsonl  # NEW flag

(The --cases-file flag does not exist yet; follow-up issue to add it
goes in the PR body.)
```

### 9. Tests + lint

```
# venv symlinked into worktree by delegate.py
.venv/bin/python -m pytest tests/audit/ -q
.venv/bin/ruff check
```

No new code is shipping, but pytest catches schema-drift assertions if any test references calibration cases by id/count.

### 10. Commit

```
git add eval/russianism/calibration-cases-h2c.jsonl eval/russianism/calibration-cases-h2c.README.md
git commit -m "$(cat <<'EOF'
feat(eval): H2c typed Russianism calibration set (40 cases, 4 type buckets)

Authored in response to the H1 calibration A/B finding
(audit/2026-05-17-judge-calibration-h1/COMPARISON.md) that the existing
12-case set is dominated by lexical/phraseological calques the morphology
+ style-guide evidence channels can't anchor. 5 of 6 models converged on
identical F1=0.118 under the H1 strict-evidence rule, proving the
calibration set is the bottleneck, not model intelligence.

H2c balances 4 russianism types (10 cases each):
- morphological: case/preposition/declension surface errors
- lexical: single-word Russian loans valid as Ukrainian morphology
- phraseological: multi-word fixed-expression calques
- register/stylistic: native-Ukrainian-flavor preferences

Each dirty case cites a real source (Antonenko entry id, Pravopys
section, Karavansky chapter, or ESUM volume), verified against MCP
sources at authoring time. 8 clean lure cases (2 per bucket) catch
over-eager judges.

Next: stage 2 = Codex adversarial review of each case + per-channel
coverage labeling. Stage 3 = run baseline + H1 against the new set,
compare deltas.

Co-Authored-By: Gemini 3.1 Pro <noreply@google.com>
EOF
)"
```

### 11. Push + open PR (no auto-merge)

```
git push -u origin <branch>
gh pr create --title "feat(eval): H2c typed Russianism calibration set (40 cases)" --body "$(cat <<'EOF'
## Summary

Authored 40-case typed calibration set in response to H1 finding (PR #2046)
that the existing 12-case set is structurally biased toward
lexical/phraseological calques the evidence catalog can't anchor.

H2c balances 4 russianism types (10 cases each):
- morphological / lexical / phraseological / register

Each dirty case has a verified source. 8 clean lure cases per bucket.

## Type bucket counts

\`\`\`
$(jq -r '.gold.expected_flags[]?.type' eval/russianism/calibration-cases-h2c.jsonl | sort | uniq -c)
\`\`\`

## Source distribution

\`\`\`
$(jq -r 'select(.gold.expected_clean==false) | .gold.source' eval/russianism/calibration-cases-h2c.jsonl | sort | uniq -c)
\`\`\`

## Next steps after this lands

- Stage 2 (Codex adversarial review): verify each cited source resolves, flag false-positive russianisms, validate JSONL schema
- Stage 3: run baseline + H1 prompts against this set, compare per-type per-channel deltas
- Follow-up: add \`--cases-file\` flag to \`scripts/audit/judge_calibration_matrix.py\` to enable running matrices against different calibration sets

## Test plan

- [ ] pytest tests/audit/ — pass
- [ ] ruff check — clean
- [ ] manual: review 5 random cases for register realism + source accuracy
- [ ] manual: confirm each clean lure uses the correct form of a dirty case's russianism

🤖 Generated with [Gemini 3.1 Pro] via dispatch
EOF
)" --base main
```

**Do NOT auto-merge.** User reads + adversarial review (stage 2) runs first.

## Hard rules

- Do NOT modify `eval/russianism/calibration-cases.jsonl` (existing 12-case set on `origin/pr-2006` — that's the baseline)
- Do NOT cite a `source` you didn't verify via `mcp__sources__search_style_guide` / `query_pravopys` / etc. Fake sources poison the set.
- Do NOT use proper nouns whose form contrasts with common nouns (proper-noun-safety per H1 finding)
- Do NOT add new code (this is content-only — no Python, no schema changes)
- Stay under 75 min wall-time. If at 60 min with cases incomplete, STOP, commit what's done, document the gap.

## What you do NOT do

- Do NOT touch `scripts/audit/_judge_eval_lib.py` or `judge_calibration_matrix.py`
- Do NOT run the matrix (that's stage 3, separate dispatch)
- Do NOT auto-merge
- Do NOT add archaisms / dialectisms (stay in modern standard UA — that's a separate heritage-defense calibration concern)
- Do NOT pile multiple types into one case (single-cause cases; max 3 flags)

## Reference materials

- Existing 12-case set: `git show origin/pr-2006:eval/russianism/calibration-cases.jsonl`
- H1 COMPARISON.md (root-cause analysis): `audit/2026-05-17-judge-calibration-h1/COMPARISON.md` (in PR #2046)
- MCP tools: `mcp__sources__search_style_guide` (342 structured) + `mcp__sources__search_text(source_file='antonenko-davydovych-yak-my-hovorymo')` (169 prose chunks) + UA-GEC annotation lookup via `data/ua-gec/data/**/*.ann` parsing (~5K F/Calque + F/Collocation + G/Case + G/Gender triples) — all three MUST BE QUERIED per step 5 above
- Supplementary: `mcp__sources__query_pravopys`, `mcp__sources__search_grinchenko_1907`, `mcp__sources__verify_word`, `mcp__sources__search_heritage`
- Karavansky reference: NOT yet ingested (issue #2048). Use Antonenko + UA-GEC + Pravopys + ESUM for the 4 buckets; skip Karavansky as a source for now.
