# /validate-ukrainian

Real-time Ukrainian grammar validation using MCP Bridge and Gemini.

## Purpose

Validate Ukrainian grammar, detect Russianisms, calques, surzhyk, and pedagogical issues using the Ukrainian Validator MCP Server powered by Gemini.

**When to use:**
- Before committing B1+ module content
- When editing immersed Ukrainian modules (B1 M06+, B2, C1, C2)
- To verify error-correction activities have real errors
- To catch Russianisms and calques before pipeline

## Usage

```bash
/validate-ukrainian curriculum/l2-uk-en/b2/75-holodomor-mekhanizm.md
/validate-ukrainian b2/75                # Shorthand
/validate-ukrainian b2 75                # Alternative shorthand
```

---

## How It Works

1. **MCP Server** receives validation request from Claude Code
2. **Auto-selects model** based on CEFR level:
   - A1-B1: `gemini-3-flash-preview` (scaffolded content, faster)
   - B2+: `gemini-3-pro-preview` (immersed Ukrainian, better quality)
3. **Gemini validates** using Ukrainian Grammar Validator prompt
4. **Returns structured JSON** with violations and corrections

---

## Instructions

### Step 1: Validate File Path

Ensure the module file exists:
```bash
test -f {file_path} || echo "File not found"
```

**Accepted formats:**
- Full path: `curriculum/l2-uk-en/b2/75-holodomor-mekhanizm.md`
- Shorthand: `b2/75`, `b2 75`

### Step 2: Call MCP Tool

Use the `ukrainian-validator` MCP server to validate:

```
Call MCP tool: validate_ukrainian
Parameters:
  - file_path: <absolute path to .md file>
  - level: <a1|a2|b1|b2|c1|c2>
```

The MCP server will:
1. Read the module markdown file
2. Extract Ukrainian content (skip English translations in A1/A2)
3. Select appropriate Gemini model based on level
4. Validate grammar using Ukrainian tutor rules
5. Return structured JSON response

### Step 3: Parse Response

The MCP server returns JSON in this format:

```json
{
  "violations": [
    {
      "type": "RUSSIANISM|CALQUE|CASE_AGREEMENT|ASPECT|REGISTER|SURZHYK",
      "severity": "critical|high|medium|low",
      "line": 42,
      "text": "original text with error",
      "error": "specific error",
      "correction": "correct form",
      "explanation_uk": "Ukrainian explanation",
      "explanation_en": "English explanation",
      "confidence": 0.95
    }
  ],
  "summary": {
    "total": 3,
    "critical": 1,
    "high": 1,
    "medium": 1,
    "low": 0,
    "recommendation": "Fix critical Russianism before commit"
  }
}
```

### Step 4: Report Violations

Display violations to user in readable format:

```markdown
## Ukrainian Validation Report: M75

### Summary
- **Total violations:** 3
- **Critical:** 1
- **High:** 1
- **Medium:** 1

### Violations

#### 🔴 CRITICAL - RUSSIANISM (Line 42)
**Text:** "Він кушав хліб"
**Error:** кушав
**Correction:** їв
**Explanation:** «Кушати» — русизм. Правильно: «їсти» (НДВ) або «з'їсти» (ДВ).
**Confidence:** 1.0

#### 🟠 HIGH - CALQUE (Line 87)
**Text:** "Це робить сенс"
**Error:** робить сенс
**Correction:** має сенс
**Explanation:** Калька з англійської "make sense". По-українськи: «мати сенс».
**Confidence:** 0.95

#### 🟡 MEDIUM - CASE_AGREEMENT (Line 112)
**Text:** "Я допомагав мій брат"
**Error:** мій брат
**Correction:** моєму брату
**Explanation:** Після дієслова "допомагати" потрібен давальний відмінок (кому?).
**Confidence:** 0.9

### Recommendation
Fix critical Russianism before commit
```

### Step 5: User Action

Ask user if they want to:
1. **Fix violations** - Apply corrections directly
2. **Review manually** - Show locations for manual editing
3. **Skip** - Ignore violations (not recommended for critical errors)

---

## Violation Types

### RUSSIANISM (Critical)
Russian lexical borrowings not acceptable in Ukrainian:
- кушать → їсти
- ложить → класти
- кто/что → хто/що
- покуда → поки
- потом → потім

**Action:** Always fix

### CALQUE (High)
Loan translations from English:
- робити сенс → мати сенс
- приймати в увагу → брати до уваги
- мати справу з → мати діло з

**Action:** Fix before commit

### CASE_AGREEMENT (High)
Wrong grammatical case after verbs/prepositions:
- дати + dative (кому?)
- бачити + accusative (кого? що?)
- допомагати + dative (кому?)

**Action:** Fix before commit

### ASPECT (Medium)
Wrong aspect for context:
- Single completed action → perfective
- Repeated/ongoing → imperfective
- Negation → usually imperfective

**Action:** Review context, fix if confirmed

### REGISTER (Low)
Style/register inappropriateness:
- Too formal for conversational content
- Too colloquial for academic content

**Action:** Review context, optional fix

### SURZHYK (Critical)
Mixed Ukrainian-Russian grammar:
- Ukrainian words + Russian grammar
- Code-switching within sentences

**Action:** Always fix

---

## Severity Levels

| Severity | Icon | Meaning | Action |
|----------|------|---------|--------|
| Critical | 🔴 | Unacceptable error (Russianism, surzhyk) | Must fix |
| High | 🟠 | Important error (calque, case) | Should fix |
| Medium | 🟡 | Context-dependent | Review |
| Low | 🔵 | Style preference | Optional |

---

## Model Selection

The MCP server automatically selects the appropriate Gemini model:

### A1-B1 Modules (Scaffolded)
**Model:** `gemini-3-flash-preview`
- Faster validation (< 5 seconds)
- Lower cost
- Sufficient for scaffolded content with English translations
- Focuses on glaring errors only

### B2-C1-C2 Modules (Immersed)
**Model:** `gemini-3-pro-preview`
- Better linguistic quality
- Detects subtle Russianisms and calques
- More nuanced aspect/register validation
- Longer processing (10-15 seconds)
- Higher confidence scores

**Why different models?**
- A1-A2 content is scaffolded with English - grammar errors less critical
- B1 M01-M05 is metalanguage bridge - transitional
- B1 M06+ is fully immersed - high quality required
- B2+ is advanced immersed content - native-like accuracy expected

---

## Confidence Thresholds

The MCP server assigns confidence scores:

| Score | Meaning | Action |
|-------|---------|--------|
| 1.0 | Absolute certainty (кушать is a Russianism) | Auto-fix safe |
| 0.9-0.95 | Very confident (clear grammar rules) | Fix with review |
| 0.8-0.85 | Confident (context-dependent but clear) | Review context |
| 0.7-0.75 | Somewhat confident (could be style) | Flag for human review |
| < 0.7 | Uncertain | Do not auto-fix |

**Recommendation:** Only apply corrections with confidence ≥ 0.9 automatically.

---

## Examples

### Example 1: Clean Module (No Violations)

```bash
/validate-ukrainian b2/74

✅ Ukrainian Validation Report: M74

No violations detected.
Module is ready for commit.
```

### Example 2: Module with Violations

```bash
/validate-ukrainian b2/75

⚠️ Ukrainian Validation Report: M75

Summary: 3 violations (1 critical, 1 high, 1 medium)

🔴 CRITICAL - RUSSIANISM (Line 42)
Text: "Він кушав хліб"
Fix: їв

🟠 HIGH - CALQUE (Line 87)
Text: "Це робить сенс"
Fix: має сенс

🟡 MEDIUM - CASE_AGREEMENT (Line 112)
Text: "Я допомагав мій брат"
Fix: моєму брату

Recommendation: Fix critical and high violations before commit
```

---

## Integration with Audit Pipeline

The MCP validator can be integrated with the audit system:

```bash
# Run audit with Ukrainian validation
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b2/75-holodomor-mekhanizm.md --validate-ukrainian
```

This will:
1. Run structural/pedagogical audit
2. Call MCP Ukrainian validator
3. Merge violations into audit report
4. Generate combined audit file

---

## Limitations

- **A1-A2 modules:** Not recommended (scaffolded with English)
- **B1 M01-M05:** Limited (metalanguage bridge with grammar terms)
- **B1 M06+, B2, C1, C2:** Ideal (fully immersed Ukrainian)
- **Context window:** Validates ~8000 tokens (~2000 words) per request
- **Timeout:** 60 seconds per validation
- **No caching:** Each validation re-processes entire file

---

## Troubleshooting

### Error: "MCP server not responding"
**Cause:** Ukrainian Validator MCP server not running
**Fix:** Restart Claude Code to reload MCP configuration

### Error: "gemini command not found"
**Cause:** gemini CLI not installed or not in PATH
**Fix:** Install gemini CLI: `brew install gemini-cli`

### Error: "GEMINI_API_KEY not set"
**Cause:** No Gemini API key configured
**Fix:** Set in `.gemini/config.yaml` or environment variable

### Error: "Timeout waiting for response"
**Cause:** Module too large or Gemini API slow
**Fix:**
- Validate smaller sections of the module
- Increase timeout in `.mcp/servers/ukrainian-validator/server.py`

---

## Cost Analysis

**Zero Anthropic API costs** - Uses local gemini CLI with Google AI API directly.

**Gemini API costs:**
- Flash: ~$0.0001 per validation (2000 words)
- Pro: ~$0.001 per validation (2000 words)

**Estimated monthly cost for B2 development:**
- 14 modules remaining × 2 validations per module = 28 validations
- 28 × $0.001 = $0.028/month

**Negligible cost compared to manual review time.**

---

## Checklist

Before marking validation complete:

- [ ] MCP server returned valid JSON response
- [ ] All violations reviewed
- [ ] Critical violations fixed
- [ ] High violations fixed or justified
- [ ] Medium violations reviewed
- [ ] Confidence scores checked (≥ 0.9 for fixes)
- [ ] Files modified and saved
- [ ] MDX regenerated: `npm run generate l2-uk-en {level} {module}`

---

## References

- **MCP Server:** `.mcp/servers/ukrainian-validator/server.py`
- **Validator Prompt:** `scripts/audit/ukrainian_grammar_validator_prompt.md`
- **MCP Protocol:** https://modelcontextprotocol.io/docs/concepts/tools
- **Issue #401:** MCP Bridge for Ukrainian Validation
