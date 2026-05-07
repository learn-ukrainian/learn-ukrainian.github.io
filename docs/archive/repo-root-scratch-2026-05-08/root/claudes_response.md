Adversarial review complete. The bot and simplify panel missed several critical edge cases where the new regexes and walkers will fail on valid syntax.

### CRITICAL

**1. `_BRACKETS_RE` destroys Markdown link text, blinding VESUM**
- **File/Line:** `scripts/build/linear_pipeline.py:97`
- **Issue:** `\[[^\]\n]*\]` matches the text portion of `[Українське слово](https://...)` and strips it. You lose valid words from the VESUM check. If a writer typos a word inside a markdown link, the gate will falsely pass because the word was hidden.
- **Fix:** Add a negative lookahead to protect markdown links: `r"\[[^\]\n]*\](?!\()"` or restrict to phonetic characters.

**2. `_JSX_BLOCK_RE` fails entirely if `<Capital>` appears anywhere inside**
- **File/Line:** `scripts/build/linear_pipeline.py:118`
- **Issue:** `(?:[^<]|<(?![A-Z/]))*?` stops matching if it hits `<` followed by a capital letter. If a prop string or comment contains a literal like `text="Press <Enter>"` or `{/* <Component> */}`, the `<(?![A-Z/])` lookahead fails. The non-greedy `*?` aborts, the whole JSX block match fails, and the block remains in the text, triggering the long-sentence false positive.
- **Fix:** Regex cannot robustly parse JSX. A safer heuristic is `r"<[A-Z].*?(?:/>|</[A-Z][A-Za-z0-9]*>)"` with `re.DOTALL` (though nested tags still break it). Alternatively, specifically strip `lines={[...]}` array blocks since that's the primary cause of long sentences.

**3. Immersion % heavily penalizes JSX schema keys**
- **File/Line:** `scripts/build/linear_pipeline.py:968`
- **Issue:** The token calculation runs on the raw `body` (*before* JSX strip). Every JSX prop key (`speaker`, `text`, `translation`) and English translation string inside a `DialogueBox` is counted as an English token. A standard dialogue block will severely dilute the Ukrainian percentage, likely dropping it below `min_pct` and causing false failures.
- **Fix:** Calculate the percentage on `body_for_sentences` (with JSX stripped) OR explicitly extract and count only the Ukrainian prose values from the JSX.

### IMPORTANT

**4. `_MORPHEME_FRAGMENT_RE` fails if surrounded by underscores**
- **File/Line:** `scripts/build/linear_pipeline.py:108`
- **Issue:** `\B` asserts no word boundary. In Python, `_` is a word character. If the writer uses underscores for markdown bold/italic (e.g., `__-шся__`), there *is* a word boundary between `_` and `-`. `\B` fails, the fragment is not stripped, and VESUM throws a false positive.
- **Fix:** Use an explicit lookbehind instead of `\B`: `r"(?<![А-ЯІЇЄҐа-яіїєґ'ʼa-zA-Z0-9_])-[А-Я...]"`.

**5. `_walk_artifact_strings` forgets dict context, breaking future schemas**
- **File/Line:** `scripts/build/linear_pipeline.py:813`
- **Issue:** `skip_error_field` checks `if parent_key == "error"`. If the schema evolves to allow nested dicts like `error: { "text": "typo" }`, the walker recurses, `parent_key` becomes `"text"`, and it fails to skip the typo, leaking it to VESUM.
- **Fix:** Filter at the dict level before recursing: `if skip_error_field and key == _ERROR_CORRECTION_INTENTIONAL_FIELD: continue`.

### NIT

**6. `@functools.cache` on whitelist lowercasing breaks test isolation**
- **File/Line:** `scripts/build/linear_pipeline.py:781`
- **Issue:** If a test dynamically patches `PROPER_NAME_WHITELIST` after the cache is primed, the new names won't be respected by other tests running in the same process.
- **Fix:** Tests mutating the whitelist should call `_proper_name_whitelist_lc.cache_clear()`.

**7. `_BRACES_RE` leaves trailing braces on nested structures**
- **File/Line:** `scripts/build/linear_pipeline.py:100`
- **Issue:** It matches up to the *first* `}`. On `{{ ... }}`, it leaves a trailing `}`. Harmless for VESUM, but leaves messy artifacts.
- **Fix:** Constrain to word characters for fill-ins: `r"\{[А-ЯІЇЄҐа-яіїєґ'ʼ]+\}"`.
