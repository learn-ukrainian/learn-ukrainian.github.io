The critical failure is now fixed by creating the sidecar meta YAML file. The VESUM warnings for "сь" and "ть" are **false positives** — the word extractor regex captures 2-character Cyrillic fragments from pedagogical particle references like `-ть` and `-сь` where the hyphen is skipped by the regex start anchor. These are morphological particles being taught, not standalone words.

===REVIEW_START===

## Fix Summary

### 1. Critical: No YAML frontmatter found — FIXED
**Root cause:** Missing sidecar meta YAML file at `curriculum/l2-uk-en/a1/meta/my-daily-routine.yaml`.
**Fix:** Created sidecar meta file from plan data at `curriculum/l2-uk-en/plans/a1/my-daily-routine.yaml`. The audit's `load_yaml_meta()` function (in `scripts/audit/loaders.py`) checks `{module_dir}/meta/{slug}.yaml` for sidecar metadata.

### 2. Warning: VESUM not found — сь, ть — FALSE POSITIVES (no content fix needed)
**Root cause:** The word extraction regex in `scripts/rag/rag_batch_verify.py` line 64:
```
[а-яіїєґА-ЯІЇЄҐ][а-яіїєґА-ЯІЇЄҐ'ʼ-]+
```
This regex requires the **first** character to be Cyrillic, then matches 1+ continuation characters. When it encounters `-ть` or `-сь` (hyphenated particle references in the prose), it skips the leading hyphen and captures `ть` / `сь` as 2-character tokens. These then fail VESUM lookup because they are not standalone dictionary words.

**Why no content fix:** These are legitimate pedagogical references to Ukrainian reflexive particle morphology (e.g., "consonant -ть, so **-ся**" and "you use **-сь** after vowels"). Changing the content would degrade the pedagogical quality. The proper fix is in the word extraction tooling — either:
- Add `сь`, `ть`, `ся` to a morphological-particle allowlist, OR
- Require minimum 3 characters for standalone word extraction (current minimum is 2)

### No section content changes required.

===REVIEW_END===