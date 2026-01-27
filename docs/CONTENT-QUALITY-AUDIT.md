# Content Quality Audit

The content quality audit uses LLM evaluation to check if module lesson content is educational, coherent, and actually teaches what it claims to teach.

## What It Checks

The audit evaluates the **lesson content** (everything before the Activities section) for:

1. **Coherence**: Is the content logically organized and easy to follow?
2. **Relevance**: Does it actually teach what the title/topic claims?
3. **Educational Value**: Are there clear explanations and useful examples?
4. **Language Quality**: Is it well-written, not repetitive or confusing?
5. **Word Salad Detection**: Does it contain meaningless filler or repetitive patterns?

## Scoring System

Each criterion is scored 1-5:
- **5**: Excellent
- **4**: Good
- **3**: Acceptable (triggers warning)
- **2**: Poor (triggers error)
- **1**: Very poor (triggers error)

## Enabling Content Quality Audit

The content quality check is **disabled by default** because it requires API calls to LLM services.

### Option 1: Gemini API (Recommended)

```bash
export GEMINI_API_KEY="your-api-key-here"
export AUDIT_CONTENT_QUALITY="true"

# Install dependency
pip install google-generativeai

# Run audit
python3 scripts/audit_module.py curriculum/l2-uk-en/a1/01-the-cyrillic-code-i.md
```

Get your Gemini API key at: https://aistudio.google.com/app/apikey

### Option 2: Claude API (Anthropic)

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
export AUDIT_CONTENT_QUALITY="true"

# Install dependency
pip install anthropic

# Run audit
python3 scripts/audit_module.py curriculum/l2-uk-en/a1/01-the-cyrillic-code-i.md
```

Get your Anthropic API key at: https://console.anthropic.com/

## Example Output

When enabled, the audit will show content quality violations:

```
## PEDAGOGICAL VIOLATIONS
- **[CONTENT_QUALITY]** Low quality score: 2/5
  - FIX: Issues: Repetitive examples, unclear explanation of cases, missing context

- **[CONTENT_QUALITY]** Low Coherence score: 2/5
  - FIX: Improve coherence

- **[CONTENT_QUALITY]** Content appears to be word salad or meaningless filler
  - FIX: Rewrite with clear educational structure and meaningful examples
```

## Severity Levels

- **Error** (blocks module): Overall score < 3, word salad detected, or rewrite recommended
- **Warning**: Overall score = 3, needs improvement, or individual metric < 3
- **Info**: API key not configured

## Integration with Pipeline

To run content quality checks as part of the full pipeline:

```bash
# Set API key and enable
export GEMINI_API_KEY="your-key"
export AUDIT_CONTENT_QUALITY="true"

# Run pipeline with content quality checks
npm run pipeline l2-uk-en a1 1
```

## Cost Considerations

- **Gemini 2.0 Flash**: Free tier available, very low cost for production
- **Claude Sonnet**: Pay-per-use, moderate cost

Each module evaluation costs approximately:
- Gemini Flash: ~$0.0001 USD (free tier)
- Claude Sonnet: ~$0.003 USD

For 400+ modules: ~$0.04 (Gemini) or ~$1.20 (Claude)

## Disabling Content Quality Checks

To disable (default behavior):

```bash
unset AUDIT_CONTENT_QUALITY
# OR
export AUDIT_CONTENT_QUALITY="false"
```

## What Content Is Evaluated

The check extracts:
- Everything **before** the `## Activities` section
- Or everything before `## Vocabulary` if no Activities section
- Excluding frontmatter metadata

This focuses the evaluation on the actual teaching content, not the practice activities.

## Recommendation Logic

Based on the LLM evaluation, the audit returns:

- **PASS**: Overall score ≥ 4, no critical issues
- **NEEDS_IMPROVEMENT**: Overall score = 3, minor issues
- **REWRITE**: Overall score < 3, word salad detected, or fundamental issues

## Fallback Behavior

If LLM evaluation fails:
1. Tries Gemini API first
2. Falls back to Claude API
3. If both unavailable, returns info message (not a blocking error)

## Example Use Cases

### Check single module

```bash
export GEMINI_API_KEY="your-key"
export AUDIT_CONTENT_QUALITY="true"
python3 scripts/audit_module.py curriculum/l2-uk-en/a2/19-the-best-the-worst.md
```

### Check all A1 modules

```bash
export GEMINI_API_KEY="your-key"
export AUDIT_CONTENT_QUALITY="true"

for f in curriculum/l2-uk-en/a1/*.md; do
  echo "=== $(basename $f) ==="
  python3 scripts/audit_module.py "$f" | grep -A 5 "CONTENT_QUALITY"
done
```

### Batch check with summary

```bash
export GEMINI_API_KEY="your-key"
export AUDIT_CONTENT_QUALITY="true"

for i in {1..34}; do
  python3 scripts/audit_module.py curriculum/l2-uk-en/a1/$i-*.md 2>&1 | \
    grep -q "CONTENT_QUALITY.*error" && echo "Module $i: FAIL" || echo "Module $i: PASS"
done
```

## Technical Details

### Architecture

- **Location**: `scripts/audit/checks/content_quality.py`
- **Called from**: `scripts/audit/checks/pedagogy.py` (check #16)
- **Model**: Gemini 2.0 Flash (primary) or Claude Sonnet 4 (fallback)
- **Prompt**: Structured evaluation with JSON response format

### Response Format

The LLM returns JSON with:
```json
{
  "coherence_score": 1-5,
  "relevance_score": 1-5,
  "educational_score": 1-5,
  "language_score": 1-5,
  "overall_score": 1-5,
  "is_word_salad": true/false,
  "issues": ["issue 1", "issue 2"],
  "strengths": ["strength 1", "strength 2"],
  "recommendation": "PASS" | "NEEDS_IMPROVEMENT" | "REWRITE"
}
```

### Error Handling

- Missing API key: Returns info violation (non-blocking)
- API failure: Tries fallback, then returns info violation
- JSON parse error: Returns info violation
- Short content (<500 chars): Returns warning

## Best Practices

1. **Use Gemini for batch checks**: Free tier + fast
2. **Use Claude for deep review**: More detailed feedback
3. **Review violations manually**: LLM can have false positives
4. **Run after content changes**: Not needed for every audit
5. **Check high-risk modules**: Newly created or significantly modified

## Limitations

- Cannot evaluate cultural appropriateness deeply
- May miss subtle linguistic errors
- Limited to first 4000 characters of lesson content
- Requires internet connection and valid API key
- May have occasional false positives/negatives

## Future Enhancements

Potential improvements:
- [ ] Cache evaluations to avoid re-checking unchanged content
- [ ] Add configurable scoring thresholds
- [ ] Support local LLM models (Ollama)
- [ ] Generate detailed improvement suggestions
- [ ] Compare modules for consistency
- [ ] Track quality trends over time
