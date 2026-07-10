#!/usr/bin/env python3
"""PreToolUse guard — block write tools from dirtying the primary checkout.

The branch-switch guard (``guard-branch-switch-in-main.py``) stops an agent from
*switching branches* in the primary checkout, but a direct write tool can dirty
tracked files from repo root without ever running a git command. That was the
observed Codex failure chain (issue #4448): the agent investigated from repo
root and then edited from the same cwd.

This hook closes that gap for providers whose PreToolUse hooks expose structured
write payloads. It reads the hook payload on stdin and blocks a write when its
target resolves to a protected file inside the primary checkout while that
checkout sits on a protected branch (``main`` / ``master``). Everything else —
writes into a ``.worktrees/**`` dispatch worktree, any other registered
worktree, gitignored local/runtime state, or paths outside the repo — is
allowed. Read-only commands (``git status``, ``git log``, ``rg``, ``cat`` …) are
never touched because they expose no write target.

Containment is **not** re-derived here: every decision defers to
``scripts.guardrails.worktree_containment`` (issue #4444), the single source of
truth shared with the monitor (#4449) and git shim (#4450). This hook only maps
each provider payload onto the target path(s) that module classifies.

Covered write surfaces
----------------------
* ``Write`` / ``Edit`` / ``MultiEdit`` — ``tool_input.file_path``.
* ``apply_patch`` and Codex ``Edit`` / ``Write`` aliases — file paths parsed from
  the ``*** Add/Update/Delete File:`` / ``*** Move to:`` headers of the patch
  body (issue #4447 verified Codex CLI fires PreToolUse for ``apply_patch``).
* ``Bash`` — write-capable redirection (``>``, ``>>``, ``&>``), ``tee``, and
  in-place editors (``sed -i`` / ``perl -i``). Quote-aware tokenization keeps a
  ``>`` inside a quoted string (e.g. a commit message) from reading as a
  redirect.

Coverage limitations (documented, by design)
--------------------------------------------
* Bash write detection is heuristic. Arbitrary write vectors — ``dd of=``,
  ``cp``/``mv`` destinations, ``python -c "open(...,'w')"``, ``$EDITOR`` — are
  **not** parsed. Those paths rely on physical worktree isolation plus the
  monitor tripwire (#4449) and git shim (#4450).
* Codex Desktop direct-edit interception is unverified (#4447). Where a provider
  does not emit a hookable write event, this hook cannot enforce that path; the
  enforcement layer is #4445/#4446/#4449 instead. See
  ``docs/runbooks/codex-hooks.md``.

The hook fails **open**: any parse/import/git error exits 0 (allow). It is a
safety net, not a chokepoint — physical isolation is the real guarantee.
"""
from __future__ import annotations

import json
import os
import shlex
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# shared containment predicate (issue #4444) — imported, never re-derived
# ---------------------------------------------------------------------------


def _load_containment():
    """Import ``scripts.guardrails.worktree_containment`` from any launch dir.

    The hook runs from a deployed copy (``<root>/.{claude,codex,agent}/hooks/``)
    or from source (``agents_extensions/shared/hooks/``); in both the repo root
    that owns ``scripts/`` is an ancestor. Walk upward for it and put it on
    ``sys.path``. Returns ``None`` if it cannot be found/imported so the caller
    fails open rather than blocking every write on an import error.
    """
    here = Path(__file__).resolve()
    for candidate in (here.parent, *here.parents):
        if (candidate / "scripts" / "guardrails" / "worktree_containment.py").exists():
            if str(candidate) not in sys.path:
                sys.path.insert(0, str(candidate))
            break
    try:
        from scripts.guardrails import worktree_containment as wc
    except Exception:  # pragma: no cover - defensive fail-open
        return None
    return wc


# ---------------------------------------------------------------------------
# payload plumbing
# ---------------------------------------------------------------------------


def _read_payload() -> dict:
    try:
        return json.loads(sys.stdin.read() or "{}")
    except (json.JSONDecodeError, ValueError):
        return {}


def _tool_name(payload: dict) -> str:
    return str(
        payload.get("tool_name") or payload.get("tool") or payload.get("name") or ""
    )


def _tool_input(payload: dict) -> dict:
    for key in ("tool_input", "arguments", "input", "params"):
        value = payload.get(key)
        if isinstance(value, dict):
            return value
    return {}


def _payload_cwd(payload: dict) -> str:
    cwd = payload.get("cwd") or payload.get("working_directory")
    return str(cwd) if cwd else os.getcwd()


# ---------------------------------------------------------------------------
# target extraction — structured write tools
# ---------------------------------------------------------------------------

# Headers in an apply_patch body that name a file the patch writes to. The path
# is the remainder of the line. ``Move from`` is a delete of the old location,
# ``Move to`` a create of the new one — both dirty the tree, so both count.
_APPLY_PATCH_HEADERS = (
    "*** Add File:",
    "*** Update File:",
    "*** Delete File:",
    "*** Move to:",
    "*** Move from:",
)


def _apply_patch_targets(patch_text: str) -> list[str]:
    """File paths a ``*** Begin Patch`` body writes to, in order of appearance."""
    targets: list[str] = []
    for raw in patch_text.splitlines():
        line = raw.strip()
        for header in _APPLY_PATCH_HEADERS:
            if line.startswith(header):
                path = line[len(header):].strip()
                if path:
                    targets.append(path)
                break
    return targets


def _strings_in(value: object) -> list[str]:
    """Every string reachable inside a (possibly nested) tool_input value."""
    out: list[str] = []
    if isinstance(value, str):
        out.append(value)
    elif isinstance(value, dict):
        for item in value.values():
            out.extend(_strings_in(item))
    elif isinstance(value, (list, tuple)):
        for item in value:
            out.extend(_strings_in(item))
    return out


def write_tool_targets(tool_input: dict) -> list[str]:
    """Candidate target paths for a structured write tool.

    ``Write``/``Edit``/``MultiEdit`` expose ``file_path`` directly.
    ``apply_patch`` (and Codex ``Edit``/``Write`` aliases) carry the patch body
    somewhere in ``tool_input``; scan every string for apply_patch headers and,
    failing that, honor an explicit ``file_path``/``path`` key.
    """
    targets: list[str] = []

    # Direct single-file path keys used by Write/Edit/MultiEdit (and some
    # provider aliases). ``file_path`` is canonical; the rest are defensive.
    for key in ("file_path", "path", "filepath", "target_file", "notebook_path"):
        value = tool_input.get(key)
        if isinstance(value, str) and value:
            targets.append(value)

    # apply_patch / patch-style payloads: parse file headers from any string.
    for text in _strings_in(tool_input):
        if "*** Begin Patch" in text or any(h in text for h in _APPLY_PATCH_HEADERS):
            targets.extend(_apply_patch_targets(text))

    # De-dup while preserving order.
    seen: set[str] = set()
    ordered: list[str] = []
    for path in targets:
        if path not in seen:
            seen.add(path)
            ordered.append(path)
    return ordered


# ---------------------------------------------------------------------------
# target extraction — write-capable Bash
# ---------------------------------------------------------------------------

# Control operators that separate one logical command from the next.
_CONTROL_OPS = frozenset({"&&", "||", ";", "|", "&", "(", ")", "\n"})

# Redirection operators that create/append to a *file* (as opposed to ``>&``
# which duplicates a file descriptor). ``&>`` / ``&>>`` redirect both streams.
_FILE_REDIRECTS = frozenset({">", ">>", ">|", "&>", "&>>"})


def _strip_quotes_for_heredoc(token: str) -> str:
    if len(token) >= 2 and token[0] == token[-1] and token[0] in {"'", '"'}:
        return token[1:-1]
    return token


def _heredoc_delimiters(line: str) -> list[tuple[str, bool]]:
    try:
        lexer = shlex.shlex(line, posix=False, punctuation_chars=True)
        lexer.whitespace_split = True
        lexer.commenters = ""
        tokens = list(lexer)
    except ValueError:
        return []

    delimiters: list[tuple[str, bool]] = []
    i = 0
    while i < len(tokens):
        if tokens[i] != "<<":
            i += 1
            continue
        strip_tabs = False
        j = i + 1
        delim_tok = ""
        if j < len(tokens):
            nxt = tokens[j]
            if nxt == "-":  # spaced: << - DELIM
                strip_tabs = True
                j += 1
                if j < len(tokens):
                    delim_tok = tokens[j]
            elif nxt.startswith("-") and len(nxt) > 1:  # attached: <<-DELIM
                strip_tabs = True
                delim_tok = nxt[1:]
            else:
                delim_tok = nxt
        delimiter = _strip_quotes_for_heredoc(delim_tok)
        if delimiter:
            delimiters.append((delimiter, strip_tabs))
        i = j + 1
    return delimiters


def _strip_heredoc_bodies(command: str) -> str:
    """Drop heredoc BODY lines before tokenizing (#4538 / #4855).

    Content between ``<<'MARKER'`` and ``MARKER`` is document DATA, not shell
    syntax. Without this, body text like ``>15%`` or markdown backtick spans
    is tokenized as redirects and misread as write targets — the recurring
    false-positive class. Pattern shared with guard-secret-print.py.

    Fail-CLOSED on an unclosed heredoc (#4877): if a delimiter never appears
    before EOF, the buffered lines were NOT a real body — a crafted or
    malformed opener must not make trailing REAL writes vanish from the
    tokenized view. Those lines are kept; only a heredoc that actually
    closes has its body + closer dropped.
    """
    if "<<" not in command:
        return command

    lines = command.splitlines()
    kept: list[str] = []
    i = 0
    n = len(lines)
    while i < n:
        kept.append(lines[i])
        i += 1
        pending = _heredoc_delimiters(lines[i - 1])
        if not pending:
            continue
        body_start = i
        while i < n and pending:
            delimiter, strip_tabs = pending[0]
            candidate = lines[i].lstrip("\t") if strip_tabs else lines[i]
            if candidate == delimiter:
                pending.pop(0)
            i += 1
        if pending:
            kept.extend(lines[body_start:i])
    return "\n".join(kept)


def _tokenize(command: str) -> list[str]:
    """Quote-aware tokens with redirection/control operators kept separate.

    ``punctuation_chars`` makes shlex split ``();<>|&`` runs into their own
    tokens while still respecting quotes, so ``echo a>b`` yields
    ``['echo','a','>','b']`` but ``echo "a>b"`` keeps ``a>b`` intact — the whole
    reason this is Python and not a grep. Heredoc bodies are stripped first:
    document text carries no write targets (#4538).
    """
    try:
        lexer = shlex.shlex(
            _strip_heredoc_bodies(command), posix=True, punctuation_chars=True
        )
        lexer.whitespace_split = True
        return list(lexer)
    except ValueError:
        # Unbalanced quotes / un-tokenizable — fail open (the shell will reject
        # the malformed command itself).
        return []


def _segments(tokens: list[str]) -> list[list[str]]:
    """Split a token stream into per-command segments on control operators."""
    segments: list[list[str]] = []
    current: list[str] = []
    for tok in tokens:
        if tok in _CONTROL_OPS:
            if current:
                segments.append(current)
                current = []
        else:
            current.append(tok)
    if current:
        segments.append(current)
    return segments


def _redirect_targets(tokens: list[str]) -> list[str]:
    """Files named as the destination of a ``>``/``>>``/``&>`` redirection."""
    targets: list[str] = []
    for i, tok in enumerate(tokens):
        if tok in _FILE_REDIRECTS and i + 1 < len(tokens):
            dest = tokens[i + 1]
            # ``>&1`` / ``> &2`` duplicate a descriptor, and a bare number is a
            # descriptor too — neither is a file write.
            if dest.startswith("&") or dest.isdigit():
                continue
            targets.append(dest)
    return targets


def _command_word(segment: list[str]) -> tuple[str, int]:
    """First real command word of a segment and its index, skipping wrappers.

    Skips leading ``VAR=val`` assignments and common wrappers (``sudo``,
    ``env``, ``time``, ``nohup``, ``command``) so ``sudo tee x`` still reads as
    a ``tee``.
    """
    i = 0
    while i < len(segment):
        tok = segment[i]
        if "=" in tok and not tok.startswith("-") and tok.split("=", 1)[0].isidentifier():
            i += 1  # leading environment assignment
            continue
        if tok in {"sudo", "env", "time", "nohup", "command", "builtin", "exec"}:
            i += 1
            continue
        break
    if i >= len(segment):
        return "", i
    return Path(segment[i]).name, i


def _tee_targets(segment: list[str], cmd_index: int) -> list[str]:
    """Non-flag operands of a ``tee`` invocation (its output files)."""
    targets: list[str] = []
    for tok in segment[cmd_index + 1:]:
        if tok.startswith("-"):
            continue  # -a / --append / -i / -p
        targets.append(tok)
    return targets


def _inplace_edit_targets(segment: list[str], cmd_index: int) -> list[str]:
    """File operands of an in-place ``sed -i`` / ``perl -i`` invocation.

    Only fires when an in-place flag is present. The editor's *script* is
    excluded so it is never mistaken for a file path: with an explicit
    ``-e``/``-f`` script every positional is a file; otherwise the first
    positional is the script and the rest are files.
    """
    args = segment[cmd_index + 1:]
    has_inplace = False
    has_explicit_script = False
    files: list[str] = []
    skip_next = False
    first_positional_seen = False

    for tok in args:
        if skip_next:
            skip_next = False
            has_explicit_script = True  # value of -e/-f was the script, not a file
            continue
        if tok.startswith("--"):
            long = tok[2:]
            if long.startswith("in-place"):  # --in-place / --in-place=.bak
                has_inplace = True
            if long in ("expression", "file"):
                skip_next = True
            continue
        if tok.startswith("-") and len(tok) > 1:
            # Short-flag cluster (``-i``, ``-i.bak``, ``-Ei``, perl ``-pi``).
            # Among sed/perl short switches only ``-i`` carries an ``i``.
            if "i" in tok[1:]:
                has_inplace = True
            if tok in ("-e", "-f"):
                skip_next = True
            continue
        # Positional token.
        if not has_explicit_script and not first_positional_seen:
            first_positional_seen = True  # inline script (no -e); never a file
            continue
        files.append(tok)

    return files if has_inplace else []


def bash_write_targets(command: str) -> list[str]:
    """Best-effort list of files a Bash command would create/modify.

    Covers redirection, ``tee``, and ``sed -i``/``perl -i``. Other write
    vectors are intentionally out of scope (see module docstring); they rely on
    physical worktree isolation and the monitor/git-shim layers.
    """
    targets: list[str] = []
    for segment in _segments(_tokenize(command)):
        if not segment:
            continue
        targets.extend(_redirect_targets(segment))
        cmd, idx = _command_word(segment)
        if cmd == "tee":
            targets.extend(_tee_targets(segment, idx))
        elif cmd in ("sed", "perl"):
            targets.extend(_inplace_edit_targets(segment, idx))
    return targets


# ---------------------------------------------------------------------------
# decision
# ---------------------------------------------------------------------------


def _resolve(path_str: str, cwd: str) -> Path:
    """Resolve a possibly-relative target against the payload cwd."""
    path = Path(path_str).expanduser()
    if not path.is_absolute():
        path = Path(cwd) / path
    return path


def main() -> int:
    payload = _read_payload()
    tool_name = _tool_name(payload)
    if not tool_name:
        return 0

    wc = _load_containment()
    if wc is None:
        return 0  # can't classify without the shared predicate → allow

    tool_input = _tool_input(payload)
    cwd = _payload_cwd(payload)

    if tool_name == "Bash":
        command = str(tool_input.get("command") or "")
        if not command.strip():
            return 0
        raw_targets = bash_write_targets(command)
    else:
        raw_targets = write_tool_targets(tool_input)

    if not raw_targets:
        return 0

    # Enforce only while the primary checkout sits on a protected branch. If the
    # human has deliberately checked the primary tree onto a feature branch, git
    # can't resolve it, or any classification errors, this hook stays out of the
    # way (fail open) — physical worktree isolation is the real guarantee.
    try:
        main_root = wc.resolve_main_root(cwd)
        if not wc.is_protected_branch(main_root):
            return 0
        decisions = [
            (raw, wc.evaluate_write(_resolve(raw, cwd), cwd=cwd)) for raw in raw_targets
        ]
    except Exception:  # pragma: no cover - defensive fail-open
        return 0

    for raw, decision in decisions:
        if not decision.allowed:
            sys.stderr.write(
                f"BLOCKED by guard-primary-checkout-write: {tool_name} would write "
                f"'{raw}' inside the protected primary checkout ({main_root}) "
                f"[{decision.reason}].\n\n"
                "The primary checkout must stay clean on `main`. Do all write "
                "work in a dispatch worktree instead:\n\n"
                "  git worktree add .worktrees/dispatch/<agent>/<task> "
                "-b <agent>/<task>\n"
                "  cd .worktrees/dispatch/<agent>/<task>\n"
                "  # ...edits, commits, push, PR...\n\n"
                f"{decision.message}\n"
                "Hook source: agents_extensions/shared/hooks/"
                "guard-primary-checkout-write.py\n"
            )
            return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
