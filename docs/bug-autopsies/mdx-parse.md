# MDX Parse Failures (2026-04-08)

## Symptom
Astro build fails: `Could not parse expression with acorn` / `Expected a closing tag for <TabItem>` / `Unexpected character !` across 39+ A2 MDX files and 1 B1 file.

## Root Causes (3 separate bugs)

### 1. `re.sub` backslash escape processing

**What:** `_inject_inline_activities()` used `re.sub(pattern, jsx_string, text)`. Python's `re.sub` interprets backslash sequences in string replacements — `\n` becomes a literal newline, `\t` becomes a tab, etc.

**Why it matters:** `json.dumps` correctly produces `\\n` (two chars: backslash + n) for newlines inside JSON strings. But `re.sub` converts `\n` back to `0x0a` (literal newline), creating unterminated string constants inside JSX props that break acorn's JS parser.

**Fix:** Use lambda replacement: `marker_pattern.sub(lambda _, r=jsx: r, text)`. Lambda replacements bypass backslash processing entirely.

**Reproducer:**
```python
import re, json
data = [{"sentence": "line1\nline2"}]
jsx = json.dumps(data)  # Produces: [{"sentence": "line1\\nline2"}]

# BAD: re.sub converts \\n → literal newline
result = re.sub(r"MARKER", jsx, "before MARKER after")
assert "\n" in result.split("MARKER")[0]  # BROKEN

# GOOD: lambda prevents backslash processing
result = re.sub(r"MARKER", lambda _: jsx, "before MARKER after")
assert "\\n" in result  # CORRECT
```

### 2. Missing blank lines around HTML blocks

**What:** `_format_dialogues()` in `enrich.py` emits `<div class="dialogue">` immediately after a prose paragraph with no blank line separator.

**Why it matters:** MDX requires blank lines before/after HTML block elements. Without them, `<div>` is parsed as an inline element within the preceding paragraph. This cascades: the parser can't find the closing `</TabItem>` because it thinks it's still inside a paragraph.

**Fix:** `_sanitize_mdx()` at publish time inserts blank lines before opening block tags and after closing block tags when adjacent to non-blank text.

### 3. LLM writer artifacts

**What:** Three types of LLM output artifacts break MDX:
- Stray code fences (unpaired ` ``` ` at end of content)
- HTML comments (`<!-- EXERCISE_N -->`) — MDX requires `{/* ... */}`
- Bare void elements (`<br>` instead of `<br />`)

**Fix:** `_sanitize_mdx()` handles all three: removes unpaired fences, strips orphaned exercise markers, converts HTML comments to MDX comments, self-closes void elements.

## Prevention

The `_sanitize_mdx()` function in `v6_build.py` runs at publish time on ALL future builds, catching these categories of LLM artifacts before they reach the MDX compiler. Categories covered:

1. Void element self-closing (`<br>`, `<hr>`)
2. Blank line enforcement around HTML blocks
3. Unpaired code fence removal
4. HTML comment conversion/removal
5. Triple+ blank line collapse

The `re.sub` lambda fix is in `_inject_inline_activities()` — the only place where `re.sub` is used with JSX replacement strings.

## Files Changed

- `scripts/build/v6_build.py` — lambda fix in `_inject_inline_activities` + new `_sanitize_mdx()`
- 40 A2 MDX files sanitized
- 1 B1 MDX file (`motion-flight-swim.mdx`) — `<br>` self-closed
