# MCP Bridge for Ukrainian Validation - Complete

**Issue**: #401
**Status**: ✅ COMPLETE
**Date**: January 10, 2026

---

## Summary

Implemented and deployed a complete MCP (Model Context Protocol) bridge that connects Claude Code to Gemini for automated Ukrainian grammar validation. This enables real-time validation of curriculum content directly from the editor.

---

## What Was Implemented

### 1. MCP Server (Completed: Jan 9, 2026)

**File**: `.mcp/servers/ukrainian-validator/server.py` (235 lines)

**Features**:
- **Auto model selection** - flash for A1-B1, pro for B2+ based on CEFR level
- **gemini CLI integration** - Uses local gemini CLI with Google AI API
- **Structured JSON responses** - Violations categorized by type and severity
- **Ukrainian validator prompt** - Embedded from `scripts/audit/ukrainian_grammar_validator_prompt.md`

**Testing**: ✅ All tests passing (`.mcp/test_ukrainian_validator.py`)

Sample violations detected:
- RUSSIANISM: кушать → їсти
- CALQUE: робить сенс → має сенс
- CASE_AGREEMENT: мій брат → моєму брату

### 2. MCP Configuration (Completed: Jan 9, 2026)

**File**: `.mcp.json`

```json
{
  "mcpServers": {
    "ukrainian-validator": {
      "command": ".venv/bin/python",
      "args": [".mcp/servers/ukrainian-validator/server.py"],
      "env": {
        "PYTHONPATH": "."
      }
    }
  }
}
```

**File**: `.claude/settings.json` - MCP permissions

```json
{
  "permissions": {
    "mcp": {
      "mcp__ukrainian-validator__*": "allow"
    }
  }
}
```

### 3. Slash Command (Completed: Jan 10, 2026)

**File**: `claude_extensions/commands/validate-ukrainian.md`

**Usage**:
```bash
/validate-ukrainian curriculum/l2-uk-en/b2/75-holodomor-mekhanizm.md
/validate-ukrainian b2/75                # Shorthand
```

**Command features**:
- Full instructions for using MCP validator
- Violation type reference (RUSSIANISM, CALQUE, CASE_AGREEMENT, etc.)
- Severity levels (critical, high, medium, low)
- Model selection explanation
- Confidence threshold guidance
- Integration examples

**Deployed**: ✅ Deployed to `.claude/` and `.agent/` via `npm run claude:deploy`

---

## Architecture

```
User: /validate-ukrainian b2/75
    ↓
Claude Code
    ↓ (MCP Protocol)
Ukrainian Validator Server (.mcp/servers/ukrainian-validator/server.py)
    ↓ (subprocess)
gemini CLI
    ↓ (Google AI API)
Gemini Models (gemini-3-flash-preview / gemini-3-pro-preview)
    ↓
Structured JSON Response
    ↓
Claude Code (displays violations to user)
```

---

## Model Selection Strategy

The MCP server automatically selects the appropriate model:

### A1-B1 Modules (Scaffolded)
- **Model**: `gemini-3-flash-preview`
- **Reason**: Content is scaffolded with English translations
- **Speed**: < 5 seconds
- **Cost**: ~$0.0001 per validation

### B2-C2 Modules (Immersed)
- **Model**: `gemini-3-pro-preview`
- **Reason**: 100% immersed Ukrainian requiring higher quality
- **Speed**: 10-15 seconds
- **Cost**: ~$0.001 per validation

---

## Violation Types

The validator detects 6 violation types:

| Type | Example | Severity | Action |
|------|---------|----------|--------|
| RUSSIANISM | кушать → їсти | Critical | Must fix |
| CALQUE | робить сенс → має сенс | High | Should fix |
| CASE_AGREEMENT | мій брат → моєму брату | High | Should fix |
| ASPECT | Wrong aspect for context | Medium | Review |
| REGISTER | Style inappropriate for level | Low | Optional |
| SURZHYK | Mixed Ukrainian-Russian | Critical | Must fix |

---

## Response Format

```json
{
  "violations": [
    {
      "type": "RUSSIANISM",
      "severity": "critical",
      "line": 42,
      "text": "Він кушав хліб",
      "error": "кушав",
      "correction": "їв",
      "explanation_uk": "«Кушати» — русизм. Правильно: «їсти» (НДВ) або «з'їсти» (ДВ).",
      "explanation_en": "«Кушати» is a Russianism. Correct: «їсти» (imperfective) or «з'їсти» (perfective).",
      "confidence": 1.0
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

---

## Cost Analysis

**Zero Anthropic API costs** - Uses local gemini CLI with Google AI API directly.

**Gemini API costs**:
- Flash: ~$0.0001 per validation (2000 words)
- Pro: ~$0.001 per validation (2000 words)

**Estimated monthly cost for B2 development:**
- 14 modules remaining × 2 validations per module = 28 validations
- 28 × $0.001 = $0.028/month

**Negligible cost compared to manual review time.**

---

## Files Created/Modified

### Created
1. `.mcp/servers/ukrainian-validator/server.py` - MCP server (235 lines)
2. `.mcp/test_ukrainian_validator.py` - Test harness
3. `claude_extensions/commands/validate-ukrainian.md` - Slash command documentation
4. `docs/issues/mcp-bridge-setup-complete.md` - Initial setup documentation
5. `docs/issues/401-mcp-bridge-complete.md` - This completion document

### Modified
1. `.mcp.json` - Registered ukrainian-validator MCP server
2. `.claude/settings.json` - Added MCP wildcard permissions

### Deployed
1. `.claude/commands/validate-ukrainian.md` - Deployed from claude_extensions
2. `.agent/commands/validate-ukrainian.md` - Deployed from claude_extensions
3. `.agent/workflows/validate-ukrainian.md` - Deployed from claude_extensions

---

## Usage Example

### Clean Module (No Violations)

```bash
/validate-ukrainian b2/74

✅ Ukrainian Validation Report: M74

No violations detected.
Module is ready for commit.
```

### Module with Violations

```bash
/validate-ukrainian b2/75

⚠️ Ukrainian Validation Report: M75

Summary: 3 violations (1 critical, 1 high, 1 medium)

🔴 CRITICAL - RUSSIANISM (Line 42)
Text: "Він кушав хліб"
Error: кушав
Correction: їв
Explanation: «Кушати» — русизм. Правильно: «їсти»
Confidence: 1.0

🟠 HIGH - CALQUE (Line 87)
Text: "Це робить сенс"
Error: робить сенс
Correction: має сенс
Explanation: Калька з англійської "make sense"
Confidence: 0.95

🟡 MEDIUM - CASE_AGREEMENT (Line 112)
Text: "Я допомагав мій брат"
Error: мій брат
Correction: моєму брату
Explanation: Давальний відмінок після "допомагати"
Confidence: 0.9

Recommendation: Fix critical and high violations before commit
```

---

## Integration Points

### 1. Manual Validation (Available Now)

Use the `/validate-ukrainian` command directly:

```bash
/validate-ukrainian curriculum/l2-uk-en/b2/75-holodomor-mekhanizm.md
```

### 2. Audit Pipeline (Existing)

The audit pipeline already has `--validate-grammar` option:

```bash
.venv/bin/python scripts/audit_module.py {file.md} --validate-grammar
```

This uses direct Gemini API calls (same validator prompt, different infrastructure).

**Note**: MCP bridge is for interactive Claude Code usage. Audit pipeline uses direct API for CI/CD compatibility.

### 3. Agent Hooks (Future Enhancement)

Not implemented yet. Would auto-trigger validation when editing B1+ modules.

**Why not implemented:**
- Requires hooks directory setup
- Need to define trigger patterns (file edit, file save, etc.)
- Need to handle validation failures gracefully
- Can be added later if needed

---

## Known Limitations

1. **A1-A2 modules**: Not recommended (scaffolded with English)
2. **B1 M01-M05**: Limited (metalanguage bridge with grammar terms)
3. **Context window**: Validates ~8000 tokens (~2000 words) per request
4. **Timeout**: 60 seconds per validation
5. **No caching**: Each validation re-processes entire file
6. **Config file modification**: Updates `.gemini/config.yaml` on each validation

---

## Future Enhancements (Not Implemented)

### 1. Agent Hooks
Auto-trigger validation when editing B1+ modules.

**Implementation**:
- Create `.claude/hooks/` directory
- Add file edit trigger for `curriculum/l2-uk-en/{b1,b2,c1,c2}/*.md`
- Call MCP validator on edit
- Display violations in editor

**Status**: Deferred (not critical for current workflow)

### 2. Caching
Cache validation results to avoid re-validating unchanged content.

**Implementation**:
- Hash file content
- Store validation results with content hash
- Return cached results if content unchanged

**Status**: Deferred (cost already negligible)

### 3. Batch Validation
Validate multiple modules in one request.

**Implementation**:
- Accept array of file paths
- Validate each file
- Return aggregated results

**Status**: Deferred (current single-file validation sufficient)

### 4. Audit Pipeline Integration
Parse MCP JSON violations in audit reports.

**Implementation**:
- Modify `scripts/audit_module.py` to optionally call MCP server
- Parse JSON response
- Integrate violations into audit report

**Status**: Deferred (audit already has `--validate-grammar` using direct API)

---

## Testing

### Manual Test

```bash
.venv/bin/python .mcp/test_ukrainian_validator.py
```

**Expected output**:

```
================================================================================
Ukrainian Validator MCP Server Test
================================================================================

1. Checking Ukrainian validator prompt...
   ✅ Found: scripts/audit/ukrainian_grammar_validator_prompt.md

2. Checking gemini CLI availability...
   ✅ gemini found at: /opt/homebrew/bin/gemini

3. Testing MCP server tools/list...
   ✅ Server responded with 1 tool(s)

4. Testing Ukrainian validation with sample content...
   ✅ Validation completed
      Response structure:
      - violations: 3 found
      - summary: total, recommendation

================================================================================
✅ MCP Server Setup Complete!
================================================================================
```

### Live Validation Test

After restarting Claude Code:

```bash
/validate-ukrainian curriculum/l2-uk-en/b2/75-holodomor-mekhanizm.md
```

Expected: Structured violation report or "No violations detected"

---

## Dependencies

### Required
- **gemini CLI**: `brew install gemini-cli` (or equivalent)
- **Google AI API key**: Configured in `.gemini/config.yaml` or `GEMINI_API_KEY` env var
- **Python venv**: `.venv/` with dependencies

### Optional
- **Claude Code**: For `/validate-ukrainian` command
- **Antigravity**: Also supported (shares `.agent/` deployment)

---

## Completion Checklist

- [x] MCP server implemented (`.mcp/servers/ukrainian-validator/server.py`)
- [x] MCP configuration created (`.mcp.json`)
- [x] Permissions configured (`.claude/settings.json`)
- [x] Tests passing (`.mcp/test_ukrainian_validator.py`)
- [x] Slash command created (`claude_extensions/commands/validate-ukrainian.md`)
- [x] Command deployed (`.claude/`, `.agent/`, `.agent/workflows/`)
- [x] Documentation complete (`docs/issues/401-mcp-bridge-complete.md`)
- [x] Model selection logic implemented (flash vs pro based on level)
- [x] Violation types documented
- [x] Cost analysis provided
- [ ] Agent hooks (deferred - future enhancement)
- [ ] Audit pipeline integration (deferred - audit already has `--validate-grammar`)

---

## Commit Message

```bash
git add .mcp/ claude_extensions/commands/validate-ukrainian.md docs/issues/401-mcp-bridge-complete.md
git commit -m "feat(mcp): complete MCP bridge for Ukrainian validation

Completed MCP Bridge implementation for issue #401:

1. **MCP Server** (Jan 9, 2026)
   - Ukrainian validator at .mcp/servers/ukrainian-validator/server.py
   - Auto model selection (flash for A1-B1, pro for B2+)
   - Structured JSON responses with violations
   - ✅ All tests passing

2. **Slash Command** (Jan 10, 2026)
   - Created /validate-ukrainian command
   - Full documentation with examples
   - Deployed to .claude/ and .agent/

3. **Features**
   - Detects Russianisms, calques, case errors, aspect issues
   - Severity levels (critical, high, medium, low)
   - Confidence scores (0.0-1.0)
   - Zero Anthropic API costs (uses gemini CLI)

4. **Deferred**
   - Agent hooks (not critical for current workflow)
   - Audit pipeline integration (audit has --validate-grammar)

Usage: /validate-ukrainian curriculum/l2-uk-en/b2/75-holodomor-mekhanizm.md

Closes #401"
```

---

## Status

**✅ COMPLETE** - Core functionality implemented and tested.

**Future Enhancements** (deferred, not blocking):
- Agent hooks for auto-validation
- Caching for performance
- Batch validation

**Next Issue**: #299 - Vocabulary Deduplication

---

## References

- **Issue #401**: MCP Bridge for Ukrainian Validation
- **MCP Protocol**: https://modelcontextprotocol.io/docs/concepts/tools
- **Ukrainian Validator Prompt**: `scripts/audit/ukrainian_grammar_validator_prompt.md`
- **Setup Documentation**: `docs/issues/mcp-bridge-setup-complete.md`
