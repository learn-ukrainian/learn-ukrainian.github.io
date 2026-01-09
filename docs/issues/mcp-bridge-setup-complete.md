# MCP Bridge Setup Complete

**Status**: ✅ READY
**Issue**: #401
**Completion Date**: 2026-01-09

## What Was Built

A Model Context Protocol (MCP) bridge that connects Claude Code ↔ gemini CLI for automated Ukrainian grammar validation.

## Architecture

```
Claude Code
    ↓ (MCP Protocol)
Ukrainian Validator Server (.mcp/servers/ukrainian-validator/server.py)
    ↓ (subprocess)
gemini CLI
    ↓ (Google AI API)
Gemini Models (gemini-3-flash-preview / gemini-3-pro-preview)
```

## Model Selection Strategy

The MCP server automatically selects the appropriate model based on CEFR level:

- **A1-B1**: `gemini-3-flash-preview` (scaffolded content, faster/cheaper)
- **B2+**: `gemini-3-pro-preview` (immersed Ukrainian, better linguistic quality)

## How It Works

1. MCP server receives validation request from Claude Code
2. Server selects appropriate model based on level
3. Server updates `.gemini/config.yaml` with selected model
4. Server calls `gemini -y` (reads model from config.yaml)
5. Gemini validates Ukrainian text using the validator prompt
6. Server parses response and returns structured JSON

## Test Results

✅ All tests passing:

```bash
.venv/bin/python .mcp/test_ukrainian_validator.py
```

Sample violations detected (B2 level):
- **Russianism**: кушать → їсти
- **Calque**: робить сенс → має сенс
- **Case Agreement**: мій брат → моєму брату

## Files Created/Modified

1. **`.mcp/servers/ukrainian-validator/server.py`** - MCP server implementation (235 lines)
2. **`.mcp.json`** - MCP server registration
3. **`.claude/settings.json`** - Wildcard permissions for MCP
4. **`.mcp/test_ukrainian_validator.py`** - Test harness

## Configuration

### `.mcp.json`
```json
{
  "mcpServers": {
    "ukrainian-validator": {
      "command": ".venv/bin/python",
      "args": [".mcp/servers/ukrainian-validator/server.py"],
      "env": {
        "PYTHONPATH": "."
      },
      "description": "Ukrainian grammar validator using gemini CLI"
    }
  }
}
```

### `.claude/settings.json`
```json
{
  "permissions": {
    "mcp": {
      "mcp__ukrainian-validator__*": "allow"
    }
  }
}
```

## Usage (After Claude Code Restart)

### Manual Validation
```
/validate-ukrainian curriculum/l2-uk-en/b2/75-holodomor-mekhanizm.md
```

### Automated Validation (Future)
Agent hooks will trigger validation when editing B1+ modules.

## Validation Response Format

```json
{
  "violations": [
    {
      "type": "RUSSIANISM|CALQUE|CASE_AGREEMENT|ASPECT|REGISTER",
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
    "recommendation": "Fix critical Russianism before commit"
  }
}
```

## Cost Analysis

**Zero API costs** - Uses local gemini CLI (no Anthropic API or direct Google AI API billing)

## Next Steps

1. **Restart Claude Code** to load MCP configuration
2. **Test live validation** with a real B2 module
3. **Create custom slash command** `/validate-ukrainian [file]`
4. **Add agent hooks** for automatic validation on B1+ edits
5. **Integrate with audit pipeline** to parse JSON violations

## Known Limitations

- Modifies `.gemini/config.yaml` on each validation (toggles between flash/pro)
- No caching (validates full content each time)
- 60-second timeout for LLM response

## References

- **Issue #401**: Native Ukrainian Validation via MCP Bridge
- **Ukrainian Validator Prompt**: `scripts/audit/ukrainian_grammar_validator_prompt.md`
- **MCP Protocol**: https://modelcontextprotocol.io/docs/concepts/tools
