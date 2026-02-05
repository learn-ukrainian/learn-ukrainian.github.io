# Gemini CLI Best Practices & Setup Guide

This guide outlines the recommended configuration and workflow for using `gemini-cli` within the `learn-ukrainian` project. It ensures consistent behavior, effective context management, and seamless integration with our existing tools.

## 1. Project Root Initialization

Always run `gemini-cli` from the root of the project repository. This ensures relative paths for configuration, context files, and output directories are resolved correctly.

```bash
cd /path/to/learn-ukrainian
gemini-cli
```

## 2. Configuration (`.gemini/config.yaml`)

Store project-specific settings in `.gemini/config.yaml`. This file defines how the agent behaves and interacts with the system.

**Key Settings:**
- **`model`**: Specify the preferred Gemini model (e.g., `gemini-2.0-flash-exp`).
- **`temperature`**: Set according to task (lower for code/docs, higher for creative writing).
- **`tools`**: Enable necessary toolsets (File System, Shell, Web Search).

## 3. Context Management

Define critical context sources to ground the agent in the project's reality. Configure `context_files` in your setup to auto-load these references.

**Essential Context Files:**
- `GEMINI.md`: The primary memory file containing project status, conventions, and user preferences.
- `CLAUDE.md`: Workflow references (shared with Claude agents).
- `docs/MARKDOWN-FORMAT.md`: Structural rules for content generation.
- `package.json` / `pyproject.toml`: Dependency and script awareness.

## 4. Memory & Persistence

Utilize `.gemini/memory.json` (or `GEMINI.md` as a persistent markdown memory) to maintain state across sessions.

- **Ephemeral Memory**: The agent remembers the current session context automatically.
- **Long-term Memory**: Use the `save_memory` tool or update `GEMINI.md` manually to persist architectural decisions, completed milestones, or style preferences.

## 5. Hooks & Validation

Integrate with existing pre-commit hooks to ensure quality *before* finalizing changes.

- **Pre-Commit**: The agent should respect and fix issues flagged by hooks (e.g., `validate-issue-fields.py`).
- **Validation Scripts**: Regularly invoke scripts like `scripts/validate_content_quality.py` or `scripts/validate_mdx.py` to verify generated content.

## 6. Workflow Integration

Leverage the "Shared Core" architecture by loading workflows dynamically from `claude_extensions/`.

- **Source of Truth**: `claude_extensions/` contains the prompts and stage definitions.
- **Loading**: Use the `read_file` tool to ingest specific workflow instructions (e.g., `claude_extensions/phases/stage-2-content.md`) when executing complex tasks.
- **Do not fork**: Do not create separate `.gemini/workflows/` unless absolutely necessary.

## 7. CLI Arguments & Execution

Pass specific file paths or module identifiers as arguments to focus the agent's attention.

**Example:**
```bash
# Focus on a specific module
gemini-cli "Refactor the vocabulary table in curriculum/l2-uk-en/b1/module-10.md"
```

## 8. Output & Logging

Redirect verbose logs to a temporary location to keep the console clean while retaining debug information.

- **Log Path**: `/tmp/gemini.log` (or project temp dir).
- **Console Output**: Keep interaction concise. Use tools for heavy lifting and provide short summaries to the user.

## 9. Version Control

Treat the agent as a collaborator.

- **Git Status**: The agent should check `git status` before starting work to avoid overwriting unstaged changes.
- **Commits**: Changes should be atomic. The agent can propose commit messages based on the work done.
- **Branching**: Always work on feature branches (e.g., `gemini/feature-name`), never directly on `main` or `claude-coder-work` unless instructed.

## 10. CI/CD Integration

Automate setup in pipelines (e.g., GitHub Actions) for tasks like automated code review or documentation generation.

- **Environment Variables**: specific API keys and configuration paths via environment variables in the CI runner.
- **Headless Mode**: Run the CLI in non-interactive mode for automated tasks.
