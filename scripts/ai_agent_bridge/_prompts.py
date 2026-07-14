"""Prompt building for Gemini and Claude interactions."""

from ._config import REPO_ROOT


def review_protocol_prefix(
    *,
    branch: str | None = None,
    pr_number: int | None = None,
    worktree_provisioned: bool = False,
) -> str:
    """Load the canonical review protocol and optional branch-target guard."""
    protocol = (REPO_ROOT / "docs" / "review-protocol.md").read_text("utf-8").rstrip()
    if branch is None:
        return protocol + "\n\n"

    pr_evidence = f" `gh pr diff {pr_number}` or" if pr_number is not None else ""
    fallback = (
        "BRANCH-TARGETED REVIEW — EVIDENCE BOUNDARY\n"
        f"The target is `origin/{branch}`. Your checkout may NOT be that branch; "
        "never infer branch contents from the primary checkout.\n"
    )
    if worktree_provisioned:
        fallback += (
            "A read-only detached worktree at that fetched branch head was provisioned "
            "for this invocation. Use it for branch file evidence. If it is unavailable, "
            "do not fall back to ordinary local file reads; use the no-worktree evidence "
            "forms below.\n"
        )
    else:
        fallback += "No branch worktree is provisioned for this invocation.\n"
    fallback += (
        "Without a provisioned worktree, the ONLY permitted file-evidence forms are"
        f"{pr_evidence} `git show origin/{branch}:<path>`. "
        "Do not read files from the current checkout.\n"
    )
    return f"{protocol}\n\n{fallback}\n"


def _prepend_review_protocol(
    prompt: str,
    review: bool,
    *,
    review_branch: str | None = None,
    review_pr_number: int | None = None,
    review_worktree_provisioned: bool = False,
) -> str:
    if not review:
        return prompt
    if review_branch is None and review_pr_number is None and not review_worktree_provisioned:
        return f"{review_protocol_prefix()}{prompt}"
    return (
        review_protocol_prefix(
            branch=review_branch,
            pr_number=review_pr_number,
            worktree_provisioned=review_worktree_provisioned,
        )
        + prompt
    )


def _load_gemini_context() -> str:
    """Load .gemini/docs/ context files and return as a single block.

    These files contain the linguistic rules, tool reference, and workflow
    that Gemini MUST know for every interaction.  GEMINI.md tells Gemini
    to "read these files" — we inject them directly so there's no chance
    of Gemini skipping or hallucinating their contents.
    """
    docs_dir = REPO_ROOT / ".gemini" / "docs"
    if not docs_dir.exists():
        return ""

    parts: list[str] = []
    for name in ("LINGUISTICS.md", "TOOLS.md", "WORKFLOW.md"):
        path = docs_dir / name
        if path.exists():
            parts.append(path.read_text("utf-8"))

    if not parts:
        return ""

    return (
        "# PROJECT CONTEXT — NON-NEGOTIABLE RULES\n\n"
        "The following rules, tools, and workflow govern ALL your output.\n"
        "Violating any rule = task failure.\n\n"
        + "\n\n---\n\n".join(parts)
        + "\n\n---\n\n"
    )


def build_gemini_prompt(msg: dict, stdout_only: bool, output_path: str | None,
                        allow_write: bool, delimiters: str | None,
                        review: bool = False) -> str:
    """Build the prompt string for a Gemini invocation.

    Selects one of three modes:
    - FULL-EXECUTION (allow_write): Gemini has bash + write access
    - ORCHESTRATED (stdout_only or output_path): Ultra-restrictive, text-only
    - STANDARD: Collaborative prompt for general communication
    """
    if allow_write:
        prompt = _build_full_execution_prompt(msg, delimiters)
    elif stdout_only or output_path:
        prompt = _build_orchestrated_prompt(msg, output_path)
    else:
        prompt = _build_standard_prompt(msg)
    return _prepend_review_protocol(prompt, review)


def _build_full_execution_prompt(msg: dict, delimiters: str | None) -> str:
    """Build FULL-EXECUTION prompt: Gemini has bash + write access."""
    if delimiters:
        tag_list = [t.strip() for t in delimiters.split(",")]
        delimiter_lines = "\n".join(
            f"  - ==={tag}_START=== ... ==={tag}_END===" for tag in tag_list
        )
        delimiter_instruction = f"Your ONLY text output must be between these exact delimiters:\n{delimiter_lines}"
    else:
        delimiter_instruction = "Your ONLY text output must be between the ===TAG_START=== / ===TAG_END=== delimiters defined in your task."

    context = _load_gemini_context()
    return f"""{context}ROLE: You are a SILENT EXECUTION AGENT with FULL read-write access.

TOOLS YOU MUST USE (not simulate):
- run_shell_command: scripts/audit_module.sh, .venv/bin/python scripts/*.py, grep, wc
- read_file / write_file: Read content, apply fixes directly

SILENCE PROTOCOL (CRITICAL):
- DO NOT narrate. DO NOT say "I will..." or "Let me..." or "First, I need to..."
- DO NOT describe what you are about to do. Just invoke the tool.
- Between tool calls, emit ZERO text. No commentary. No summaries. No reasoning.
- {delimiter_instruction}
- Every word you write that is NOT a tool call or the final delimited output is a WASTED TOKEN that risks timeout.

PRIVATE SCRATCHPAD (allowed):
- If you need to reason through complex logic (case endings, dates, IPA), use XML comments: <!-- thinking: your reasoning here -->
- Scratchpad comments do NOT count as narration — they are your private workspace.
- Keep scratchpad brief. Do NOT use it for narration or status updates.

RULES:
1. NO MESSAGES. Never use send_message, message broker, or any communication tool.
2. NO EXPLORATION. Do not check GitHub, inbox, or broker. Stay on task.
3. NO DELEGATION. Never say "Claude should..." or request skills/commands.
4. NO SIMULATION. You MUST run_shell_command for every check. Never "remember" file contents — always read from disk. If you skip a bash command and guess the result, the review is INVALID.
5. ALWAYS FINISH. Always produce output between the required delimiters, even on errors.

TASK:
{msg['content']}
"""


def _build_orchestrated_prompt(msg: dict, output_path: str | None) -> str:
    """Build ORCHESTRATED prompt: ultra-restrictive, text/file output only."""
    if output_path:
        output_instruction = f"""1. WRITE OUTPUT TO EXACTLY ONE FILE: {output_path}
   Write your COMPLETE output to this file. This is the ONLY file you may create or modify.
   Do NOT write to any other file. Do NOT edit any existing file."""
        success_instruction = f"""- Read the task content provided below
- Think about the content
- Write your COMPLETE output to: {output_path}
- That's it. Nothing else."""
    else:
        output_instruction = """1. OUTPUT ONLY TEXT. Your ONLY job is to read input files and produce text output between delimiters.
2. DO NOT WRITE OR EDIT ANY FILES. You must not use any tool that creates, modifies, or deletes files."""
        success_instruction = """- Read the task content provided below
- Think about the content
- Output your result as plain text between the delimiters specified in the task
- That's it. Nothing else. Just text output."""

    context = _load_gemini_context()
    prompt = f"""{context}ROLE: You are a TEXT GENERATOR executing a specific task. You produce text output. That's it.

ABSOLUTE RULES — VIOLATION OF ANY RULE MEANS TASK FAILURE:

{output_instruction}
3. DO NOT SEND MESSAGES. Do not use send_message, message broker, MCP tools, or any communication tool.
4. DO NOT RUN SHELL COMMANDS that modify state. You may read files (cat, head) but NEVER run commands that write, move, delete, or execute scripts (no sed -i, no python scripts, no git, no audit_module.sh).
5. DO NOT TAKE INITIATIVE. Do not explore the codebase beyond what the task requires. Do not check GitHub issues, status files, inbox, or broker messages. Do not make strategic decisions.
6. DO NOT DELEGATE. Do not say "Claude should...", "please run...", or request any skills/commands.

HOW TO SUCCEED:
{success_instruction}

IF YOU ARE TEMPTED TO DO ANYTHING OTHER THAN WHAT'S DESCRIBED ABOVE: DON'T. Complete the task and stop.

TASK:
{msg['content']}
"""
    if msg['data']:
        prompt += f"""
ATTACHED DATA:
{msg['data']}
"""
    return prompt


def _build_standard_prompt(msg: dict) -> str:
    """Build STANDARD collaborative prompt for general communication."""
    context = _load_gemini_context()
    prompt = f"""{context}You are Gemini, participating in a collaboration with Claude.
This is a message from Claude to you:

---
{msg['content']}
"""
    if msg['data']:
        prompt += f"""
---
Attached data:
{msg['data']}
"""
    prompt += """
---

Please respond appropriately. If this is a request, fulfill it.
If Claude asked for feedback, provide your honest assessment.
Format your response clearly.
"""
    return prompt


def build_claude_prompt(
    msg: dict,
    review: bool = False,
    review_branch: str | None = None,
    review_pr_number: int | None = None,
    review_worktree_provisioned: bool = False,
) -> str:
    """Build prompt for Claude invocation."""
    prompt = f"""You are Claude, receiving a message from {msg['from'].title()} via the message broker.

---
Task ID: {msg['task_id'] or 'none'}
Type: {msg['type']}
From: {msg['from']}

{msg['content']}
"""
    if msg['data']:
        prompt += f"""
---
Attached data:
{msg['data']}
"""
    prompt += """
---

Respond directly to this message. Be concise and helpful.
Your response will be automatically sent back to the sender via the message broker.
Do NOT use MCP tools to send your response - just output your response directly.
"""
    return _prepend_review_protocol(
        prompt,
        review,
        review_branch=review_branch,
        review_pr_number=review_pr_number,
        review_worktree_provisioned=review_worktree_provisioned,
    )


_CODEX_STANDING_RULES = """\
# NON-NEGOTIABLE RULES FOR CODEX (apply to EVERY task from this bridge)

## Git branch safety — HARD CONSTRAINT
You are invoked from the caller's current working directory, which is normally on `main`.
You MUST NOT leave `main` under any circumstances:

- FORBIDDEN commands: `git checkout <branch>`, `git switch <branch>`, `git reset --hard`,
  `git branch -D`, `git checkout .`, `git restore .`, `git clean -f`, `git rebase`,
  `git merge`, `git pull` with rebase, `git push --force`.
- If you need isolation for experimental work, create a dedicated worktree:
    `git worktree add ../codex-wt-<task-id> -b codex/<task-id>`
  then `cd` into that worktree and work there. Never modify the caller's branch state.
- When you finish a worktree task, leave the worktree in place — the human will clean it up.
- If a task seems to require switching the caller's branch, STOP and reply explaining
  the conflict. Do not improvise.

Violating this rule destroys the caller's work in progress. There is no exception.

## Scope discipline
- Stay strictly within the files the task names. Do not "clean up" unrelated code.
- Do not run destructive operations (`rm -rf`, `git push --force`) without explicit approval in the task.
- Reference the GH issue number in every commit message: `fix: X (#NNNN)`.

## Reporting
- If you hit a `usage limit reached` or rate-limit error, STOP and reply with the exact error
  so the caller can reschedule. Do not retry silently.
- Be concise. Report what you did, what you verified, and what remains.

## Runtime / architecture tasks
- If the task involves `scripts/agent_runtime/`, READ `docs/agent-runtime-guide.md` FIRST.
  The guide is the single source of truth for the runtime design; violating its rules
  (session resume policy, mode vocabulary, adapter protocol shape) causes silent bugs.
"""


OPERATOR_CONTRACT_DIGEST = """Operator contract (binding; full text: agents_extensions/shared/rules/operator-expectations.md):
quality over shortcuts - root-cause fixes - tool-backed claims only (Ukrainian word/stress/
morphology facts VESUM/`sources`-verified, never guessed) - max UA immersion EXCEPT A1 (its
English scaffolding is by design; from A2 never raise English) - reviews need an independent
cross-family reviewer (discussion does not satisfy the gate) - note any lane substitution."""


def build_agy_prompt(
    msg: dict,
    review: bool = False,
    review_branch: str | None = None,
    review_pr_number: int | None = None,
    review_worktree_provisioned: bool = False,
) -> str:
    """Build prompt for Agy (Antigravity CLI) invocation.

    Mirrors the codex prompt shape — minimal context, directive framing,
    no investigation side-paths. Agy has shown a tendency in 2026-05-21
    probes to grep through scripts/, query sqlite directly, and write
    throwaway scripts when asked introspection-style questions. Bridge Q&A
    may read the precise repository files needed to answer, but must not
    broaden that into an exploratory or write-capable task.
    """
    prompt = f"""You are Agy (Antigravity CLI, Gemini-3.5-Flash-High), receiving a message from {msg['from'].title()} via the message broker.

{OPERATOR_CONTRACT_DIGEST}

---
Task ID: {msg['task_id'] or 'none'}
Type: {msg['type']}
From: {msg['from']}

{msg['content']}
"""
    if msg['data']:
        prompt += f"""
---
Attached data:
{msg['data']}
"""
    prompt += """

---

Standing rules for bridge Q&A:
- Respond directly. Be concise. This bridge is for quick questioning
  and short coordination, not long-running task execution.
- You MAY read the specific repository file(s) needed to answer the
  caller's question. Do not broaden this into codebase exploration (no
  `grep` across scripts/, no `sqlite3` against data/, no throwaway Python
  scripts).
- This is read-only Q&A. Do NOT create, modify, move, or delete files, and
  do NOT run commands that change repository or system state.
- Do NOT use broker or MCP messaging tools to send your response —
  output your response directly.
- If the message references MCP tools (mcp_sources_*), prefer calling
  them via your native plugin surface; only fall back to run_command +
  curl if the plugin isn't loaded.
"""
    return _prepend_review_protocol(
        prompt,
        review,
        review_branch=review_branch,
        review_pr_number=review_pr_number,
        review_worktree_provisioned=review_worktree_provisioned,
    )


def build_codex_prompt(
    msg: dict,
    review: bool = False,
    review_branch: str | None = None,
    review_pr_number: int | None = None,
    review_worktree_provisioned: bool = False,
) -> str:
    """Build prompt for Codex invocation."""
    prompt = f"""You are Codex, receiving a message from {msg['from'].title()} via the message broker.

{_CODEX_STANDING_RULES}
---
Task ID: {msg['task_id'] or 'none'}
Type: {msg['type']}
From: {msg['from']}

{msg['content']}
"""
    if msg['data']:
        prompt += f"""
---
Attached data:
{msg['data']}
"""
    prompt += """

---

Respond directly to this message. Be concise and helpful.
This bridge is for quick questioning and short coordination, not long-running task execution.
Do NOT use broker or MCP messaging tools to send your response - just output your response directly.
"""
    return _prepend_review_protocol(
        prompt,
        review,
        review_branch=review_branch,
        review_pr_number=review_pr_number,
        review_worktree_provisioned=review_worktree_provisioned,
    )
