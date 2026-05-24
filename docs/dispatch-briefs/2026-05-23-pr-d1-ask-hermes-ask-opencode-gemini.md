# Dispatch brief — PR-D1: `ab ask-hermes` + `ab ask-opencode` bridge subcommands

**Agent:** gemini (mechanical mirror of existing ask-codex/ask-gemini patterns; codex busy on PR-C + #2239)
**Task ID:** `pr-d1-ask-hermes-ask-opencode-2026-05-23`
**Worktree:** auto via `--worktree`
**Mode:** `danger`
**Base SHA:** `c363726b44` or newer
**Authority:** user direction 2026-05-23 — "would like both hermes and opencode support for everything"

## #M-4 preamble

Every verifiable claim MUST be tool-backed with command + cwd + raw output triple. Required evidence:

| Claim | Evidence |
|---|---|
| Bridge subcommands registered | `.venv/bin/python scripts/ai_agent_bridge/__main__.py --help` raw output showing `ask-hermes` + `ask-opencode` in subcommand list |
| Tests pass | `.venv/bin/python -m pytest tests/test_ask_hermes.py tests/test_ask_opencode.py -v` + raw final line |
| Lint clean | `.venv/bin/ruff check scripts/ai_agent_bridge/_hermes.py scripts/ai_agent_bridge/_opencode.py scripts/ai_agent_bridge/_cli.py tests/test_ask_hermes.py tests/test_ask_opencode.py` + raw final line |
| Smoke test (hermes) | `echo "say hello in 5 words" \| .venv/bin/python scripts/ai_agent_bridge/__main__.py ask-hermes - --task-id smoke-hermes --model qwen/qwen3.6-plus` + raw output (must include hermes response) |
| Smoke test (opencode) | `echo "say hello in 5 words" \| .venv/bin/python scripts/ai_agent_bridge/__main__.py ask-opencode - --task-id smoke-opencode --model openrouter/qwen/qwen3.7-max` + raw output (must include opencode response) |
| Commit landed | `git log -1 --oneline` raw |
| PR opened | `gh pr view --json url --jq .url` raw URL |

## Context

The `ai_agent_bridge` CLI already has `ask-codex` (`scripts/ai_agent_bridge/_codex.py`), `ask-gemini` (`scripts/ai_agent_bridge/_gemini.py`), `ask-claude` (`scripts/ai_agent_bridge/_claude.py`), `ask-agy` (`scripts/ai_agent_bridge/_agy.py`). Each subcommand:

1. Parses CLI args (content, --task-id, --type, --data, --model, --from, --from-model, --to-model)
2. Calls `send_message(content, task_id, msg_type, data, from_llm=..., to_llm="<agent>", ...)` from `scripts/ai_agent_bridge/_messaging.py` to record the message in the broker SQLite
3. Invokes a `process_for_<agent>(message_id, ...)` function that:
   a. Loads the message from the broker
   b. Runs the underlying CLI (`codex exec`, `gemini`, `claude`, etc.) capturing stdout
   c. Posts the response back to the broker as a reply message (to_llm = original from_llm)

Hermes is currently invoked from `scripts/agent_runtime/adapters/hermes_grok.py`, `hermes_deepseek.py`, `hermes_qwen.py` via `hermes -z PROMPT -m MODEL`. Opencode is a new CLI: `opencode run --model PROVIDER/MODEL --file ATTACH "CONTENT"`. Neither has a bridge `ask-*` subcommand yet — PR-D1 adds them.

**Out of scope for PR-D1:** delegate.py `--agent opencode` / `--agent hermes` integration. That's PR-D2 (filed as follow-up).

## Steps — execute in order

### 1. Worktree setup (auto)

Cwd will be `.worktrees/dispatch/gemini/pr-d1-ask-hermes-ask-opencode-2026-05-23/`.

```bash
git status --short
git log -1 --oneline  # expect c363726b44 or newer
```

### 2. Create `scripts/ai_agent_bridge/_hermes.py` (new)

Mirror `scripts/ai_agent_bridge/_codex.py`. Replace codex CLI invocation with hermes:

```python
"""Hermes adapter for ai_agent_bridge ask-hermes subcommand.

Mirrors ask-codex / ask-gemini pattern. Hermes is the underlying runtime for
several already-supported model adapters (hermes_grok, hermes_deepseek,
hermes_qwen). This bridge subcommand exposes ad-hoc one-shot Hermes calls
with arbitrary models so cross-model adversarial reviews can route through
hermes the same way they route through codex/gemini.

Invocation pattern:
    # venv symlinked
    .venv/bin/python scripts/ai_agent_bridge/__main__.py ask-hermes <content> \\
      --task-id <task> --model qwen/qwen3.6-plus

Under the hood: hermes -z "<content>" -m <model>
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from ._messaging import send_message, write_reply

HERMES_DEFAULT_MODEL = "qwen/qwen3.6-plus"
HERMES_DEFAULT_TIMEOUT_S = 900  # 15 min — adversarial reviews can be long


def ask_hermes(
    content: str,
    task_id: str,
    msg_type: str = "query",
    data: str | None = None,
    model: str | None = None,
    from_llm: str = "claude",
    from_model: str | None = None,
    to_model: str | None = None,
    no_timeout: bool = False,
) -> int:
    """Send message to Hermes AND invoke Hermes one-shot to process it."""
    effective_model = model or HERMES_DEFAULT_MODEL
    msg_id = send_message(
        content,
        task_id,
        msg_type,
        data,
        from_llm=from_llm,
        to_llm="hermes",
        from_model=from_model,
        to_model=to_model or effective_model,
    )
    print(f"\n🚀 Invoking Hermes ({effective_model}) to process message #{msg_id}...")
    response = _invoke_hermes(content, effective_model, data=data, no_timeout=no_timeout)
    write_reply(msg_id, "hermes", from_llm, response, to_model=from_model)
    return msg_id


def _invoke_hermes(
    content: str,
    model: str,
    *,
    data: str | None = None,
    no_timeout: bool = False,
) -> str:
    """Run hermes -z PROMPT -m MODEL; return captured stdout."""
    hermes_bin = shutil.which("hermes")
    if not hermes_bin:
        raise SystemExit("ask-hermes: hermes CLI not found in PATH")

    # If data file attached, prepend its content to the prompt under a fenced block.
    prompt = content
    if data:
        data_path = Path(data)
        if not data_path.exists():
            raise SystemExit(f"ask-hermes: --data file does not exist: {data}")
        attached = data_path.read_text(encoding="utf-8", errors="replace")
        prompt = f"{content}\n\n## Attached data: {data_path.name}\n\n```\n{attached}\n```"

    timeout = None if no_timeout else HERMES_DEFAULT_TIMEOUT_S
    try:
        result = subprocess.run(
            [hermes_bin, "-z", prompt, "-m", model],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise SystemExit(f"ask-hermes: hermes timed out after {timeout}s") from exc

    if result.returncode != 0:
        raise SystemExit(
            f"ask-hermes: hermes exited {result.returncode}\n"
            f"stderr: {result.stderr[-2000:]}"
        )

    return result.stdout.strip()
```

If `write_reply` doesn't exist in `_messaging.py` under that exact name, look for the equivalent (e.g. `send_response`, `send_reply`, `send_message` with msg_type="response" + to_llm=original-from). Match the pattern from `_codex.py`.

### 3. Create `scripts/ai_agent_bridge/_opencode.py` (new)

Mirror the hermes pattern. Replace with opencode invocation:

```python
"""Opencode adapter for ai_agent_bridge ask-opencode subcommand.

Exposes ad-hoc one-shot opencode calls with arbitrary openrouter models.
Useful for cross-model adversarial reviews where the target model isn't
in the hermes proxy (e.g. openrouter/qwen/qwen3.7-max as demonstrated in
the 2026-05-23 strip-plan review).

Invocation pattern:
    # venv symlinked
    .venv/bin/python scripts/ai_agent_bridge/__main__.py ask-opencode <content> \\
      --task-id <task> --model openrouter/qwen/qwen3.7-max [--data FILE]

Under the hood: opencode run --model PROVIDER/MODEL [--file FILE] "CONTENT"
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from ._messaging import send_message, write_reply

OPENCODE_DEFAULT_MODEL = "openrouter/qwen/qwen3.7-max"
OPENCODE_DEFAULT_TIMEOUT_S = 900


def ask_opencode(
    content: str,
    task_id: str,
    msg_type: str = "query",
    data: str | None = None,
    model: str | None = None,
    from_llm: str = "claude",
    from_model: str | None = None,
    to_model: str | None = None,
    no_timeout: bool = False,
) -> int:
    effective_model = model or OPENCODE_DEFAULT_MODEL
    msg_id = send_message(
        content,
        task_id,
        msg_type,
        data,
        from_llm=from_llm,
        to_llm="opencode",
        from_model=from_model,
        to_model=to_model or effective_model,
    )
    print(f"\n🚀 Invoking opencode ({effective_model}) to process message #{msg_id}...")
    response = _invoke_opencode(content, effective_model, data=data, no_timeout=no_timeout)
    write_reply(msg_id, "opencode", from_llm, response, to_model=from_model)
    return msg_id


def _invoke_opencode(
    content: str,
    model: str,
    *,
    data: str | None = None,
    no_timeout: bool = False,
) -> str:
    opencode_bin = shutil.which("opencode")
    if not opencode_bin:
        raise SystemExit("ask-opencode: opencode CLI not found in PATH")

    argv = [opencode_bin, "run", "--model", model, "--format", "default"]
    if data:
        data_path = Path(data)
        if not data_path.exists():
            raise SystemExit(f"ask-opencode: --data file does not exist: {data}")
        argv.extend(["--file", str(data_path.resolve())])
    argv.append(content)

    timeout = None if no_timeout else OPENCODE_DEFAULT_TIMEOUT_S
    try:
        result = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise SystemExit(f"ask-opencode: opencode timed out after {timeout}s") from exc

    if result.returncode != 0:
        raise SystemExit(
            f"ask-opencode: opencode exited {result.returncode}\n"
            f"stderr: {result.stderr[-2000:]}"
        )

    # opencode run prints ANSI control codes and a banner before the response.
    # Strip leading ANSI sequences and the "build · model" line.
    output = result.stdout
    # Crude strip: lines that are escape sequences or the banner.
    # If a more robust ANSI stripper exists in the project (e.g. _ANSI_RE in
    # hermes adapters), reuse it.
    return output.strip()
```

### 4. Wire into `scripts/ai_agent_bridge/_cli.py`

Add imports at the existing import-block area:

```python
from ._hermes import ask_hermes, HERMES_DEFAULT_MODEL
from ._opencode import ask_opencode, OPENCODE_DEFAULT_MODEL
```

Add argparse subparsers (mirror ask-codex/ask-gemini patterns; look at lines 463-540 of current _cli.py for the exact shape):

```python
# ask-hermes
ask_hermes_parser = subparsers.add_parser(
    "ask-hermes",
    help="Send message AND invoke Hermes one-shot (use '-' to read from stdin)",
)
ask_hermes_parser.add_argument("content", help="Message content (use '-' to read from stdin)")
ask_hermes_parser.add_argument("--task-id", required=True, help="Task ID")
ask_hermes_parser.add_argument("--type", default="query", help="Message type")
ask_hermes_parser.add_argument("--data", help="Path to data file to attach")
ask_hermes_parser.add_argument(
    "--model",
    default=HERMES_DEFAULT_MODEL,
    help=f"Hermes model (default {HERMES_DEFAULT_MODEL})",
)
ask_hermes_parser.add_argument("--from", dest="from_llm", help="Sender agent family")
ask_hermes_parser.add_argument("--from-model", dest="from_model", help="Exact sender model")
ask_hermes_parser.add_argument("--to-model", dest="to_model", help="Target model ID")
ask_hermes_parser.add_argument("--no-timeout", dest="no_timeout", action="store_true")

# ask-opencode
ask_opencode_parser = subparsers.add_parser(
    "ask-opencode",
    help="Send message AND invoke opencode one-shot (use '-' to read from stdin)",
)
ask_opencode_parser.add_argument("content", help="Message content (use '-' to read from stdin)")
ask_opencode_parser.add_argument("--task-id", required=True, help="Task ID")
ask_opencode_parser.add_argument("--type", default="query", help="Message type")
ask_opencode_parser.add_argument("--data", help="Path to data file to attach")
ask_opencode_parser.add_argument(
    "--model",
    default=OPENCODE_DEFAULT_MODEL,
    help=f"Opencode model (default {OPENCODE_DEFAULT_MODEL})",
)
ask_opencode_parser.add_argument("--from", dest="from_llm", help="Sender agent family")
ask_opencode_parser.add_argument("--from-model", dest="from_model", help="Exact sender model")
ask_opencode_parser.add_argument("--to-model", dest="to_model", help="Target model ID")
ask_opencode_parser.add_argument("--no-timeout", dest="no_timeout", action="store_true")
```

Add the dispatch handlers near where `ask-codex` / `ask-gemini` are handled (search for `elif args.command == "ask-codex"`):

```python
elif args.command == "ask-hermes":
    _handle_ask_hermes(args)
elif args.command == "ask-opencode":
    _handle_ask_opencode(args)
```

```python
def _handle_ask_hermes(args):
    content = _read_content_stdin_or_arg(args.content)
    ask_hermes(
        content,
        args.task_id,
        msg_type=args.type,
        data=args.data,
        model=args.model,
        from_llm=args.from_llm or _default_from_llm(),
        from_model=args.from_model,
        to_model=args.to_model,
        no_timeout=args.no_timeout,
    )


def _handle_ask_opencode(args):
    content = _read_content_stdin_or_arg(args.content)
    ask_opencode(
        content,
        args.task_id,
        msg_type=args.type,
        data=args.data,
        model=args.model,
        from_llm=args.from_llm or _default_from_llm(),
        from_model=args.from_model,
        to_model=args.to_model,
        no_timeout=args.no_timeout,
    )
```

(Match the existing helper functions `_read_content_stdin_or_arg` and `_default_from_llm` from `_cli.py`; if names differ, use the actual names.)

### 5. Tests

**`tests/test_ask_hermes.py`** (new):

```python
"""Tests for ab ask-hermes bridge subcommand (PR-D1)."""

import subprocess
from unittest.mock import patch, MagicMock

import pytest

from scripts.ai_agent_bridge._hermes import _invoke_hermes, HERMES_DEFAULT_MODEL


def test_hermes_default_model_is_qwen_plus():
    assert HERMES_DEFAULT_MODEL == "qwen/qwen3.6-plus"


def test_invoke_hermes_constructs_correct_argv(tmp_path):
    """Hermes subprocess is invoked with -z PROMPT -m MODEL."""
    with patch("scripts.ai_agent_bridge._hermes.shutil.which", return_value="/fake/hermes"):
        with patch("scripts.ai_agent_bridge._hermes.subprocess.run") as run_mock:
            run_mock.return_value = MagicMock(returncode=0, stdout="response body", stderr="")
            _invoke_hermes("hello", "qwen/qwen3.6-plus")
            argv = run_mock.call_args[0][0]
            assert argv[0] == "/fake/hermes"
            assert "-z" in argv
            assert "hello" in argv
            assert "-m" in argv
            assert "qwen/qwen3.6-plus" in argv


def test_invoke_hermes_attaches_data_file(tmp_path):
    data_file = tmp_path / "context.md"
    data_file.write_text("# Context\nSome content.")
    with patch("scripts.ai_agent_bridge._hermes.shutil.which", return_value="/fake/hermes"):
        with patch("scripts.ai_agent_bridge._hermes.subprocess.run") as run_mock:
            run_mock.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
            _invoke_hermes("review this", "qwen/qwen3.6-plus", data=str(data_file))
            argv = run_mock.call_args[0][0]
            # data should be in the prompt, not as a separate flag
            prompt_arg = argv[argv.index("-z") + 1]
            assert "Some content." in prompt_arg
            assert "review this" in prompt_arg


def test_invoke_hermes_raises_when_binary_missing():
    with patch("scripts.ai_agent_bridge._hermes.shutil.which", return_value=None):
        with pytest.raises(SystemExit, match="hermes CLI not found"):
            _invoke_hermes("hello", "qwen/qwen3.6-plus")


def test_invoke_hermes_raises_on_nonzero_exit():
    with patch("scripts.ai_agent_bridge._hermes.shutil.which", return_value="/fake/hermes"):
        with patch("scripts.ai_agent_bridge._hermes.subprocess.run") as run_mock:
            run_mock.return_value = MagicMock(returncode=1, stdout="", stderr="auth failed")
            with pytest.raises(SystemExit, match="hermes exited 1"):
                _invoke_hermes("hello", "qwen/qwen3.6-plus")
```

**`tests/test_ask_opencode.py`** (new):

```python
"""Tests for ab ask-opencode bridge subcommand (PR-D1)."""

from unittest.mock import patch, MagicMock

import pytest

from scripts.ai_agent_bridge._opencode import _invoke_opencode, OPENCODE_DEFAULT_MODEL


def test_opencode_default_model_is_qwen_max():
    assert OPENCODE_DEFAULT_MODEL == "openrouter/qwen/qwen3.7-max"


def test_invoke_opencode_constructs_correct_argv():
    with patch("scripts.ai_agent_bridge._opencode.shutil.which", return_value="/fake/opencode"):
        with patch("scripts.ai_agent_bridge._opencode.subprocess.run") as run_mock:
            run_mock.return_value = MagicMock(returncode=0, stdout="response", stderr="")
            _invoke_opencode("hello", "openrouter/qwen/qwen3.7-max")
            argv = run_mock.call_args[0][0]
            assert argv[0] == "/fake/opencode"
            assert argv[1] == "run"
            assert "--model" in argv
            assert "openrouter/qwen/qwen3.7-max" in argv
            assert "hello" in argv


def test_invoke_opencode_attaches_file(tmp_path):
    data_file = tmp_path / "report.html"
    data_file.write_text("<html><body>data</body></html>")
    with patch("scripts.ai_agent_bridge._opencode.shutil.which", return_value="/fake/opencode"):
        with patch("scripts.ai_agent_bridge._opencode.subprocess.run") as run_mock:
            run_mock.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
            _invoke_opencode("review", "openrouter/qwen/qwen3.7-max", data=str(data_file))
            argv = run_mock.call_args[0][0]
            assert "--file" in argv
            # file path is in argv right after --file
            file_idx = argv.index("--file")
            assert str(data_file.resolve()) == argv[file_idx + 1]


def test_invoke_opencode_raises_when_binary_missing():
    with patch("scripts.ai_agent_bridge._opencode.shutil.which", return_value=None):
        with pytest.raises(SystemExit, match="opencode CLI not found"):
            _invoke_opencode("hello", "openrouter/qwen/qwen3.7-max")
```

### 6. Run focused tests

```bash
# venv symlinked
.venv/bin/python -m pytest tests/test_ask_hermes.py tests/test_ask_opencode.py -v
```

Expect: all green (8-10 tests).

### 7. Smoke tests (live)

```bash
# venv symlinked
echo "say hello in 5 words" | .venv/bin/python scripts/ai_agent_bridge/__main__.py ask-hermes - --task-id smoke-hermes-pr-d1 --model qwen/qwen3.6-plus 2>&1 | tail -20
echo "say hello in 5 words" | .venv/bin/python scripts/ai_agent_bridge/__main__.py ask-opencode - --task-id smoke-opencode-pr-d1 --model openrouter/qwen/qwen3.7-max 2>&1 | tail -20
```

Both should print a 5-word hello-style response. If either fails, surface in PR body.

### 8. Regression test

```bash
# venv symlinked
.venv/bin/python -m pytest tests/ --timeout=120 -q 2>&1 | tail -30
```

Specifically watch tests in `tests/test_ai_*` and `tests/test_messaging*` — they might assert agent enumerations.

### 9. Lint

```bash
.venv/bin/ruff check scripts/ai_agent_bridge/_hermes.py scripts/ai_agent_bridge/_opencode.py scripts/ai_agent_bridge/_cli.py tests/test_ask_hermes.py tests/test_ask_opencode.py
```

### 10. Commit + push + PR

```bash
git add scripts/ai_agent_bridge/_hermes.py scripts/ai_agent_bridge/_opencode.py scripts/ai_agent_bridge/_cli.py tests/test_ask_hermes.py tests/test_ask_opencode.py
git commit -m "$(cat <<'EOF'
feat(bridge): ab ask-hermes + ab ask-opencode subcommands (PR-D1)

Adds first-class bridge support for two more agents:

- ask-hermes: one-shot hermes -z PROMPT -m MODEL via the hermes CLI. Default
  model qwen/qwen3.6-plus (matches the hermes_qwen adapter default at
  scripts/agent_runtime/adapters/hermes_qwen.py). Useful for ad-hoc cross-
  model reviews via hermes proxy.

- ask-opencode: one-shot opencode run --model PROVIDER/MODEL via opencode
  CLI. Default model openrouter/qwen/qwen3.7-max (demonstrated as effective
  adversarial reviewer in the 2026-05-23 strip-plan review). Useful for
  routing models not in hermes proxy (any openrouter model).

Both subcommands mirror the existing ask-codex / ask-gemini pattern:
broker send → CLI invoke → broker reply. Optional --data flag attaches
file content to the prompt for context.

Out of scope: delegate.py --agent hermes / --agent opencode for dispatched
commits-and-PR work. That's PR-D2 (filed as follow-up).

Per user direction 2026-05-23: "would like both hermes and opencode
support for everything."

Co-Authored-By: Gemini CLI <noreply@anthropic.com>
EOF
)"

git push -u origin HEAD
gh pr create --title "feat(bridge): ab ask-hermes + ab ask-opencode subcommands (PR-D1)" --body "..."
```

Use the commit message body for the PR description.

### 11. Do NOT auto-merge

Surface PR URL. Orchestrator merges on CI green.

## Acceptance criteria

- `ab --help` shows `ask-hermes` and `ask-opencode` in subcommand list
- 8-10 unit tests pass
- Both smoke tests return a real model response
- Ruff clean
- PR URL surfaced

## Stay in scope

DO NOT modify:
- `scripts/agent_runtime/` (PR-D2 territory)
- `scripts/delegate.py` (PR-D2)
- Any agent's existing `ask-*` subcommand (codex / gemini / claude / agy)
- The broker schema (`_messaging.py`, `_db.py`)

If `write_reply` doesn't exist under that exact name in `_messaging.py`: use the equivalent that ask-codex uses (look at how `process_for_codex` sends its response back to the broker — copy that exact pattern).

If the broker has a hard-coded agent enumeration (e.g. `VALID_AGENTS = {"claude", "codex", "gemini", "agy"}`), add `"hermes"` and `"opencode"` to it. Search:

```bash
grep -rn 'VALID_AGENTS\|valid_agents\|ALLOWED_AGENTS\|AGENT_LIST' scripts/ai_agent_bridge/
```

## Failure recovery

- If `opencode run` returns non-zero on the smoke test: check `opencode providers` shows OpenRouter configured. If not, the smoke test can be marked skip-when-not-configured rather than failing the PR — but document in PR body.
- If `hermes -z` is unfamiliar to you: `hermes --help` shows the surface; `-z PROMPT -m MODEL` is the one-shot mode.
- If existing `ask-codex` / `ask-gemini` use a different broker function than `send_message + write_reply`: mirror whatever they do, don't invent.
