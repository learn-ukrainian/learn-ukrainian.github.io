# GitHub Workflows

This repository uses a **multi-agent coordination protocol** for AI-assisted development.

## Active Workflows

| Workflow | Purpose | Trigger | Status |
|----------|---------|---------|--------|
| `deploy-pages.yml` | Deploy Docusaurus to GitHub Pages | Push to main | ✅ Active |
| `validate-yaml.yml` | Validate YAML syntax | PR/Push | ✅ Active |

## Multi-Agent Coordination

See `docs/dev/AGENT_COORDINATION.md` for the complete multi-agent protocol.

### Agent Roles

| Agent | Role | Tool | Invocation |
|-------|------|------|------------|
| **C1-a** | Coordinator | Gemini 2.5 Pro | Antigravity IDE |
| **C1-b** | Implementer | Gemini 2.5 Pro | Antigravity IDE |
| **C1-c** | Reviewer | Claude Code | Claude Code IDE |
| **G1** | Specialized Tasks | Gemini | gemini-cli (GitHub Actions) |

### Gemini Automation (gemini-cli)

Gemini agent automation is configured via **`.github/commands/*.toml`** files:

- **`gemini-invoke.toml`** - Plan → Approve → Execute workflow for issue/PR tasks
- **`gemini-triage.toml`** - Automatic issue labeling on trigger
- **`gemini-review.toml`** - Comprehensive PR code review
- **`gemini-scheduled-triage.toml`** - Batch issue triage on schedule

These use gemini-cli's MCP tool system with built-in authentication (no API keys required in repo).

## Why No Claude Workflows?

**C1-c (Claude Code) operates via IDE, not GitHub Actions.**

The multi-agent protocol coordinates agents through:
- Issue/PR comments for task assignment
- `AGENT_COORDINATION.md` for role definitions
- Direct IDE access for full project context

GitHub Actions workflows would create **isolated Claude instances** that:
- ❌ Lack full project context
- ❌ Don't coordinate with C1-a/C1-b/G1
- ❌ Require API keys (`CLAUDE_CODE_OAUTH_TOKEN` secret)
- ❌ Break the multi-agent coordination protocol

Instead, C1-c is invoked manually via IDE when assigned review tasks by C1-a.

## Security

All workflows follow security best practices:
- No secrets stored in repository (gemini-cli uses external auth)
- User input treated as untrusted data
- No command substitution (`$(...)`, `<(...)`, `>(...)`)
- Conventional Commits for all automated changes

## References

- **Multi-Agent Protocol:** `docs/dev/AGENT_COORDINATION.md`
- **Workflow Audit:** `docs/dev/GITHUB_WORKFLOWS_AUDIT.md`
- **gemini-cli Documentation:** https://github.com/google/generative-ai-python
