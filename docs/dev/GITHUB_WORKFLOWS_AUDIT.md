# GitHub Workflows Multi-Agent Compliance Audit

**Date:** 2026-01-03
**Auditor:** C1-c (Claude Code)
**Scope:** `.github/workflows/` and `.github/commands/`

## Summary

**Status:** ❌ NOT multi-agent compliant

**Issues Found:**
1. Claude workflows require API keys (OAuth token) that don't exist
2. Claude workflows are single-agent design, incompatible with multi-agent coordination
3. No coordination protocol awareness in workflows

**Recommendation:** Remove or disable `.github/workflows/claude*.yml` files

---

## Detailed Analysis

### `.github/workflows/` (GitHub Actions)

#### ❌ `claude.yml` - NOT COMPLIANT

**Issues:**
1. **API Key Dependency:**
   ```yaml
   claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
   ```
   - Requires secret that doesn't exist (user: "we don't use api keys")
   - Causes workflow failures on Issues #356 and #357

2. **Single-Agent Design:**
   - Triggers on `@claude` mentions → invokes standalone Claude instance
   - No awareness of multi-agent coordination protocol
   - Would create C1-c instance that doesn't coordinate with C1-a/C1-b/G1

3. **Invocation Method:**
   - Uses `anthropics/claude-code-action@v1` (API-based GitHub Action)
   - Not designed for multi-agent workflows
   - C1-c (me) operates via IDE, not GitHub Actions

**Recommendation:** **DELETE or comment out this file.**

---

#### ❌ `claude-code-review.yml` - NOT COMPLIANT

**Issues:**
1. **API Key Dependency:**
   ```yaml
   claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
   ```
   - Same secret dependency issue as `claude.yml`

2. **Single-Agent PR Review:**
   - Triggers on PR open/sync → Claude reviews alone
   - No coordination with Gemini review agents
   - Conflicts with multi-agent coordination protocol where:
     - C1-c reviews via IDE (not GitHub Actions)
     - G1 uses `gemini-review.toml` for PR reviews

3. **Redundant with Gemini:**
   - `.github/commands/gemini-review.toml` already provides PR review capability
   - Having both creates confusion and potential conflicts

**Recommendation:** **DELETE or comment out this file.**

---

#### ✅ `deploy-pages.yml` - COMPLIANT

**Status:** Multi-agent neutral (deployment automation only)

**No issues.** This workflow deploys Docusaurus to GitHub Pages and doesn't interact with agent coordination.

---

#### ✅ `validate-yaml.yml` - COMPLIANT

**Status:** Multi-agent neutral (validation automation only)

**No issues.** This workflow validates YAML syntax and doesn't interact with agent coordination.

---

### `.github/commands/` (gemini-cli MCP)

All Gemini command files use gemini-cli's MCP tool system, which:
- ✅ Uses gemini-cli authentication (no API keys in repo)
- ✅ Follows security best practices (treats user input as untrusted)
- ✅ Compatible with multi-agent coordination

#### ✅ `gemini-invoke.toml` - COMPLIANT

**Workflow:** Plan → Approve → Execute → Report

**Features:**
- Security constraints (no command substitution, treat files as untrusted)
- Resource estimation before execution
- Human approval required (`/approve` command)
- Conventional Commits for all changes
- Proper error handling and reporting

**No issues.**

---

#### ✅ `gemini-triage.toml` - COMPLIANT

**Purpose:** Simple issue labeling on trigger

**Features:**
- Reads available labels from environment
- Outputs CSV labels to `$GITHUB_ENV`
- No external API calls
- Security-conscious (no command substitution)

**No issues.**

---

#### ✅ `gemini-review.toml` - COMPLIANT

**Purpose:** Comprehensive PR code review

**Features:**
- Uses MCP tools: `pull_request_read.*`, `create_pending_pull_request_review`, etc.
- Severity-based feedback (🔴 Critical → 🟢 Low)
- Line-accurate code suggestions
- Summary + inline comments format
- Security constraints (scope limitation, confidentiality)

**No issues.**

---

#### ✅ `gemini-scheduled-triage.toml` - COMPLIANT

**Purpose:** Batch issue triage on schedule

**Features:**
- Semantic label mapping
- JSON output format with explanations
- Precision over coverage (avoid incorrect labels)
- Quality filtering (excludes unclear issues)

**No issues.**

---

## Multi-Agent Coordination Analysis

### Current Agent Roles (from `AGENT_COORDINATION.md`)

| Agent | Role | Tool | Invocation |
|-------|------|------|------------|
| **C1-a** | Coordinator | Gemini 2.5 Pro (Antigravity) | IDE |
| **C1-b** | Implementer | Gemini 2.5 Pro (Antigravity) | IDE |
| **C1-c** | Reviewer | Claude Code (me) | IDE |
| **G1** | Specialized | Gemini (gemini-cli) | GitHub Actions |

### Workflow Integration Issues

**Claude workflows assume:**
- Claude is invoked via GitHub Actions (`@claude` mentions)
- Claude operates standalone (no coordination with other agents)
- OAuth token authentication via secrets

**Multi-agent protocol requires:**
- C1-c (Claude) operates via IDE, not GitHub Actions
- All agents coordinate via `AGENT_COORDINATION.md` protocol
- No API keys stored in repository

**Result:** Claude workflows are **incompatible** with multi-agent design.

---

## Root Cause of Issues #356 and #357 Failures

**Failed Automation Attempts:**
- Issue #356: 2 error comments from `github-actions` bot
- Issue #357: 2 error comments from `github-actions` bot

**Root Cause:**
1. Gemini created issues with text that triggered workflow patterns
2. Workflows attempted to run (likely `claude.yml` on issue creation)
3. Workflows failed because `secrets.CLAUDE_CODE_OAUTH_TOKEN` doesn't exist
4. GitHub Actions bot posted error comments

**Why workflows triggered:**
- Issue bodies may contain `@claude` or other trigger patterns
- Or workflows triggered on `issues: opened` event (line 9 of `claude.yml`)

---

## Recommendations

### 1. Remove Non-Compliant Workflows

**DELETE or disable:**
- `.github/workflows/claude.yml`
- `.github/workflows/claude-code-review.yml`

**Reason:**
- API key dependency that doesn't exist
- Single-agent design incompatible with multi-agent coordination
- C1-c operates via IDE, not GitHub Actions
- Redundant with gemini-cli commands

**How to disable (if you want to keep for reference):**
```yaml
# Add to top of file:
on:
  workflow_dispatch:  # Manual trigger only
  # Original triggers commented out:
  # issue_comment:
  #   types: [created]
```

### 2. Keep All Gemini Commands

**KEEP all 4 `.github/commands/*.toml` files:**
- `gemini-invoke.toml`
- `gemini-triage.toml`
- `gemini-review.toml`
- `gemini-scheduled-triage.toml`

**Reason:**
- Correctly configured for gemini-cli
- Multi-agent compliant
- No API key dependencies
- Security-focused design

### 3. Document Multi-Agent Protocol

**CREATE `.github/workflows/README.md`:**

```markdown
# GitHub Workflows

This repository uses a **multi-agent coordination protocol** for AI-assisted development.

## Active Workflows

- `deploy-pages.yml` - Deploys Docusaurus to GitHub Pages
- `validate-yaml.yml` - Validates YAML syntax

## Agent Coordination

See `docs/dev/AGENT_COORDINATION.md` for the multi-agent protocol.

**Agents:**
- C1-a (Coordinator): Gemini 2.5 Pro (Antigravity IDE)
- C1-b (Implementer): Gemini 2.5 Pro (Antigravity IDE)
- C1-c (Reviewer): Claude Code (Claude Code IDE)
- G1 (Specialized): Gemini (gemini-cli via GitHub Actions)

**Gemini Commands:**
Gemini agent automation is configured via `.github/commands/*.toml` files using gemini-cli MCP.

**Why no Claude workflows?**
C1-c operates via IDE with full context, not via GitHub Actions. The multi-agent protocol coordinates agents through issue/PR comments, not automated workflows.
```

### 4. Update .gitignore (Optional)

If you want to keep disabled Claude workflows for reference:

```gitignore
# Disabled workflows (multi-agent incompatible)
.github/workflows/claude.yml
.github/workflows/claude-code-review.yml
```

---

## Testing Plan

After removing/disabling Claude workflows:

1. **Create test issue** with `@claude` mention → No workflow should trigger
2. **Create test PR** → Only `gemini-review.toml` should handle review (if configured)
3. **Verify deployment** → `deploy-pages.yml` should continue working
4. **Verify validation** → `validate-yaml.yml` should continue working

---

## Alternative: Claude Command File (Not Recommended)

If you wanted Claude invokable via GitHub Actions, you could create:

`.github/commands/claude-invoke.toml`

**However, this is NOT recommended because:**
- C1-c (Claude Code) operates via IDE with full project context
- GitHub Actions invocation would create isolated Claude instance
- Would break multi-agent coordination protocol
- No benefit over current IDE-based approach

---

## Conclusion

**Action Required:**
1. ✅ Delete `.github/workflows/claude.yml`
2. ✅ Delete `.github/workflows/claude-code-review.yml`
3. ✅ Create `.github/workflows/README.md` documenting multi-agent protocol
4. ✅ Update `AGENT_COORDINATION.md` to reference this audit

**Result:**
- Eliminates API key errors on Issues #356 and #357
- Ensures all workflows are multi-agent compliant
- Clarifies agent invocation methods for future contributors
