"""AGY headless user-event envelope and terminal result extraction."""

import json
import math
import re

from scripts.common.jsonl import jsonl_lines
from scripts.dispatcher import agy_sandbox
from scripts.dispatcher.providers import read_only_refusal
from scripts.dispatcher.providers.stream_json import model_observer as _observe
from scripts.dispatcher.providers.stream_json import one_model
from scripts.dispatcher.types import Invocation, ParsedResult, TaskSpec
from scripts.dispatcher.watchdog import deadlines

MODEL_SOURCE = "agy-stream-json"

_BACKGROUND_TERMINATED_RE = re.compile(r"terminating (?P<count>\d+) background task\(s\)")
_PRINT_TIMEOUT_PARTIAL_RE = re.compile(r"print timeout after \S+ with turn in progress")
# One structured diagnostic line the CLI writes beside the terminal result.
# Status and code are the provider's own classification, the same role as
# Claude's api_error_status and Codex's terminal failure message.
_AGY_ERROR_PREFIX = "AGY_ERROR:"
_CAPACITY_STATUSES = frozenset({"RESOURCE_EXHAUSTED", "UNAVAILABLE"})
_CAPACITY_CODES = frozenset({429, 529})


def _stderr_capacity(stderr: str) -> bool:
    """True when stderr has exactly one AGY_ERROR naming a quota or capacity limit.

    A missing line, a malformed line, or more than one line is not that signal.
    Prose on stderr is never read: only this structured diagnostic classifies.
    """
    payloads = []
    # Newline only. str.splitlines() also breaks on U+2028/U+2029/U+0085, which
    # can sit inside the JSON this diagnostic parses (scripts JSONL guard).
    for line in stderr.split("\n"):
        if line.endswith("\r"):
            line = line[:-1]
        if not line.startswith(_AGY_ERROR_PREFIX):
            continue
        try:
            payload = json.loads(line[len(_AGY_ERROR_PREFIX) :].strip())
        except ValueError:
            return False
        if not isinstance(payload, dict):
            return False
        payloads.append(payload)
    if len(payloads) != 1:
        return False
    status, code = payloads[0].get("status"), payloads[0].get("error_code")
    # bool is an int. A true/false code is malformed even when the status name
    # is a capacity status, so it must not classify.
    if isinstance(code, bool):
        return False
    if isinstance(status, str) and status in _CAPACITY_STATUSES:
        return True
    return isinstance(code, int) and code in _CAPACITY_CODES


def transport_model(model: str) -> str:
    """The catalog's AGY wire id for a catalog model; any other request is unchanged.

    ``claude-sonnet-5-5`` is the catalog id and ``claude-sonnet-5-5-high`` is the id
    ``agy --model`` lists. They are not the same model. A request that is already the
    wire id stays that id.
    """
    from scripts.review.model_catalog import load_model_catalog

    text = model.strip()
    if not text:
        return model
    models = load_model_catalog()["models"]
    wires = {
        spec.get("routing_wire_ids", {}).get("agy")
        for spec in models.values()
        if isinstance(spec.get("routing_wire_ids", {}).get("agy"), str)
    }
    if text in wires:
        return text
    folded = text.casefold()
    for model_id, spec in models.items():
        names = (model_id, *spec.get("aliases", []))
        if any(isinstance(name, str) and name.casefold() == folded for name in names):
            wire = spec.get("routing_wire_ids", {}).get("agy")
            return wire if isinstance(wire, str) and wire else model
    return model


def _init_models(event: object) -> tuple[str, ...]:
    """Model strings an ``init`` event reports. No other event attests one."""
    if not isinstance(event, dict) or event.get("event") != "init":
        return ()
    reported = []
    nested = event.get("init")
    for metadata in (nested, event):
        if not isinstance(metadata, dict):
            continue
        model = metadata.get("model")
        if isinstance(model, str) and model.strip():
            reported.append(model)
    return tuple(reported)


def model_observer(stdout_path):
    """Attest the running task's model from complete init events, under ``parse``'s exactly-one rule."""
    return _observe(stdout_path, _init_models)


def identity_failure(requested: str, attested: str | None) -> str | None:
    """A typed failure naming both models, or None when the attested family is the requested one.

    No attested model, an unknown family, or a different family is never success under the
    requested name. The same known family, Claude or Gemini, is success and the record keeps
    both ids.
    """
    from scripts.dispatcher.checks import _model_families

    families = _model_families()
    requested_family = families.get(requested)
    attested_family = families.get(attested) if isinstance(attested, str) else None
    if isinstance(attested, str) and requested_family and attested_family == requested_family:
        return None
    shown = attested if isinstance(attested, str) else "none"
    return (
        "agy_model_identity_unverified: "
        f"requested {requested} ({requested_family or 'unknown'}), "
        f"attested {shown} ({attested_family or 'unknown'})"
    )


def terminal_result_observer(stdout_path):
    """Observe complete terminal envelopes incrementally, without granting success."""
    offset, pending = 0, b""

    def observed():
        nonlocal offset, pending
        with stdout_path.open("rb") as stream:
            stream.seek(offset)
            chunk = stream.read()
            offset = stream.tell()
        lines = (pending + chunk).split(b"\n")
        pending = lines.pop()
        for line in lines:
            try:
                event = json.loads(line)
            except (ValueError, UnicodeDecodeError):
                continue
            if isinstance(event, dict) and event.get("event") == "result" and isinstance(event.get("result"), dict):
                return True
        return False

    return observed


# AGY moves any command still running after its ``WaitMsBeforeAsync`` (at most 10 s) to a background task, and
# a headless run waits for background tasks only until its ``--print-timeout`` deadline, counted from launch.
# There agy 1.4.11 exits 0 with the interim reply as a SUCCESS result, no ``finished_reason`` and nothing on
# stderr, so a worker waiting on a task it dispatched ended mid-chain (#12156). The deadline is therefore the
# task's own hard timeout plus this margin: the supervisor's deadline, which settles a cut run as ``timeout``,
# always comes first, and a task with no hard timeout leaves AGY unbounded too.
PRINT_TIMEOUT_MARGIN_S = 60


def _print_timeout(spec: TaskSpec) -> str:
    hard_timeout = deadlines(spec.options)[0]
    return f"{math.ceil(hard_timeout) + PRINT_TIMEOUT_MARGIN_S}s" if hard_timeout > 0 else "0s"


def build(spec: TaskSpec, env: dict[str, str]) -> Invocation:
    argv = ["agy", "--mode", "auto", "--input-format", "stream-json", "--output-format", "stream-json"]
    argv += ["--model", transport_model(spec.model)]
    argv += ["--dangerously-skip-permissions", "--print-timeout", _print_timeout(spec)]
    if spec.mode == "workspace-write":
        argv += ["--log-file", str(spec.final_file.with_suffix(".log"))]
    elif spec.mode == "read-only":
        # AGY has no write lock of its own: read-only runs only inside the dispatcher's bubblewrap
        # boundary, which is the argv returned here, so no caller can launch it unwrapped (C-3027).
        if refusal := read_only_refusal("agy"):
            raise ValueError(refusal)
        argv += ["--add-dir", str(spec.worktree), "--log-file", str(agy_sandbox.log_file(spec.task_id))]
        argv = agy_sandbox.launcher(spec, argv)
    else:
        raise ValueError(f"agy: unsupported mode {spec.mode!r}")
    message = {"role": "user", "content": [{"type": "text", "text": spec.prompt_file.read_bytes().decode("utf-8")}]}
    stdin = (json.dumps({"event": "user", "message": message}) + "\n").encode("utf-8")
    return Invocation(argv, stdin, env, None)


def parse(stdout: str, stderr: str, returncode: int, final_text: str | None) -> ParsedResult:
    result, error, models = {}, None, set()
    terminal_seen, stream_clean = False, True
    for line in jsonl_lines(stdout):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except ValueError:
            error = error or "agy: invalid JSON stream"
            stream_clean = False
            continue
        if not isinstance(event, dict):
            error = error or "agy: invalid event"
            stream_clean = False
            continue
        if terminal_seen:
            # Anything after the terminal result makes a capacity classification untrustworthy.
            stream_clean = False
        models.update(_init_models(event))
        if event.get("event") == "result":
            if terminal_seen:
                error = error or "agy: duplicate terminal result"
                continue
            terminal_seen = True
            terminal = event.get("result")
            if not isinstance(terminal, dict):
                error = error or "agy: invalid terminal result"
                stream_clean = False
                continue
            result = terminal
            if result.get("status") != "SUCCESS" or result.get("error"):
                error = error or "agy: terminal result unsuccessful"
        elif event.get("event") == "error":
            error = error or "agy: terminal error"
            stream_clean = False
    text = result.get("response")
    text = text if isinstance(text, str) and text.strip() else None
    usage = result.get("usage")
    incomplete = bool(
        _PRINT_TIMEOUT_PARTIAL_RE.search(stderr)
        or any(int(match["count"]) > 0 for match in _BACKGROUND_TERMINATED_RE.finditer(stderr))
    )
    if incomplete:
        error = error or "agy: incomplete run"
    quota_message = result.get("error")
    if (
        stream_clean
        and terminal_seen
        and not incomplete
        and result.get("status") != "SUCCESS"
        and error == "agy: terminal result unsuccessful"
        and isinstance(quota_message, str)
        and quota_message.strip()
        and _stderr_capacity(stderr)
    ):
        # Before the exit-status overwrite, as Claude and Codex do. The terminal
        # error is the provider's reset hint; the AGY_ERROR line is the classification.
        return ParsedResult(
            None,
            usage if isinstance(usage, dict) else None,
            f"agy: {quota_message}",
            one_model(models),
            rate_limited=True,
        )
    if returncode:
        error = f"agy: exited with status {returncode}"
    return ParsedResult(
        text,
        usage if isinstance(usage, dict) else None,
        error or (None if text else "agy: missing final text"),
        one_model(models),
    )
