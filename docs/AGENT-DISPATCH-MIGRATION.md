# Migrating from Agent Bridge to Direct CLI Dispatch

## Problem

The `ai_agent_bridge` ORCHESTRATED mode wraps every prompt with a restrictive system message:

```
ROLE: You are a TEXT GENERATOR executing a specific task.
DO NOT use MCP tools, or any communication tool.
DO NOT RUN SHELL COMMANDS.
```

This blocks MCP tool access even when the agent has tools configured. If your pipeline needs agents to verify data, query databases, or use any MCP server during generation or review — the bridge blocks it.

## Solution: Direct CLI Dispatch

Both Claude and Gemini CLIs support MCP tools natively in pipe/non-interactive mode. Bypass the bridge and call them directly.

### Claude with MCP Tools

```python
import subprocess

result = subprocess.run(
    [
        "claude", "-p",                          # pipe mode (non-interactive)
        "--model", "claude-opus-4-6",            # or sonnet, haiku
        "--output-format", "text",               # plain text output
        "--mcp-config", ".mcp.json",             # MCP server config
        "--allowedTools",                         # whitelist specific tools
        "mcp__rag__verify_word,"
        "mcp__rag__search_text,"
        "Read",                                  # can also allow built-in tools
    ],
    input=prompt,                                # prompt via stdin
    capture_output=True, text=True, timeout=600,
    cwd=str(PROJECT_ROOT),
)
ok = result.returncode == 0
output = result.stdout if ok else ""
```

**Key flags:**
- `-p` / `--print` — non-interactive, reads stdin, prints output, exits
- `--mcp-config` — path to `.mcp.json` with MCP server definitions
- `--allowedTools` — comma-separated whitelist (ONLY these tools available, no Edit/Write/Bash unless listed)
- `--output-format text` — plain text (also supports `json`, `stream-json`)
- `--model` — model override for this call

**Your `.mcp.json`:**
```json
{
  "mcpServers": {
    "rag": {
      "type": "sse",
      "url": "http://127.0.0.1:8766/sse"
    }
  }
}
```

### Gemini with MCP Tools

```python
import subprocess

result = subprocess.run(
    [
        "gemini",
        "-m", "gemini-3.1-pro-preview",         # model
        "-y",                                     # auto-approve tool use
        "--allowed-mcp-server-names", "rag",     # whitelist MCP servers
    ],
    input=prompt,                                # prompt via stdin
    capture_output=True, text=True, timeout=600,
    cwd=str(PROJECT_ROOT),
)
ok = result.returncode == 0
output = result.stdout if ok else ""
```

**Setup (one-time):**
```bash
# Add your MCP server to Gemini's project config
gemini mcp add rag http://127.0.0.1:8766/sse -t sse --trust
gemini mcp list  # verify: ✓ rag: ... (sse) - Connected
```

**Key flags:**
- `-y` — auto-approve all tool calls (like `--dangerously-skip-permissions` for Claude)
- `--allowed-mcp-server-names` — whitelist which MCP servers the agent can use
- `-m` — model selection

### When to Still Use the Agent Bridge

The bridge is still useful for:
- **Simple text generation** (no tools needed) — the ORCHESTRATED mode is fine
- **Message passing between agents** (Claude↔Gemini communication via broker)
- **GitHub issue posting** (bridge auto-posts to issues via `--task-id`)
- **Retry logic with model fallback** (bridge handles rate limits and flash→pro fallback)

### Migration Checklist

1. **Identify which agents need MCP tools** — writers and reviewers that verify data
2. **Replace `dispatch_gemini()` calls** with direct `subprocess.run(["gemini", ...])`
3. **Replace `subprocess.run(["claude", "-p", ...])` calls** — add `--mcp-config` and `--allowedTools`
4. **Add tool instructions to the prompt** — tell the agent what tools exist and when to use them
5. **Test** — verify the agent actually calls tools (check output for tool-use evidence)

### Tool Instruction Template

Append this to your prompt when the agent has MCP access:

```markdown
## Available Tools (MCP)

You have MCP tools for verification. Use them for quality:

- `{prefix}verify_words` — batch-verify words exist in dictionary
- `{prefix}search_style_guide` — check for calques/Russianisms
- `{prefix}query_cefr_level` — verify vocabulary level (A1-C1)
- `{prefix}search_definitions` — look up exact definitions

**When to use:** suspected Russianisms, unsure grammar forms,
vocabulary level checks. **When NOT to use:** basic words you're
confident about. Target 5-15 tool calls, not 50.
```

Where `{prefix}` is `mcp__rag__` for Claude or `rag_` for Gemini.

### Important: Tool Name Prefixes Differ

| CLI | MCP tool prefix | Example |
|-----|----------------|---------|
| Claude (`claude -p`) | `mcp__{server}__{tool}` | `mcp__rag__verify_word` |
| Gemini (`gemini`) | `{server}_{tool}` | `rag_verify_word` |

Your tool instructions must use the correct prefix for the target agent.

## Architecture Diagram

```
BEFORE (agent bridge blocks tools):
  prompt → ai_agent_bridge → "DO NOT use MCP" wrapper → gemini CLI → output
                                    ↑ blocks MCP access

AFTER (direct dispatch):
  prompt → gemini CLI --allowed-mcp-server-names rag → output
                           ↑ MCP tools available

  prompt → claude -p --mcp-config .mcp.json --allowedTools ... → output
                           ↑ MCP tools available
```
