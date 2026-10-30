"""AGY headless user-event envelope and terminal result extraction."""

import json
import re

from scripts.common.jsonl import jsonl_lines
from scripts.dispatcher import agy_sandbox
from scripts.dispatcher.providers import read_only_refusal
from scripts.dispatcher.providers.stream_json import model_observer as _observe
from scripts.dispatcher.providers.stream_json import one_model
from scripts.dispatcher.types import Invocation, ParsedResult, TaskSpec

MODEL_SOURCE = "agy-stream-json"

_BACKGROUND_TERMINATED_RE = re.compile(r"terminating (?P<count>\d+) background task\(s\)")
_PRINT_TIMEOUT_PARTIAL_RE = re.compile(r"print timeout after \S+ with turn in progress")


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


def build(spec: TaskSpec, env: dict[str, str]) -> Invocation:
    argv = ["agy", "--mode", "auto", "--input-format", "stream-json", "--output-format", "stream-json"]
    argv += ["--model", transport_model(spec.model)]
    argv += ["--dangerously-skip-permissions", "--print-timeout", "120m"]
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
    terminal_seen = False
    for line in jsonl_lines(stdout):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except ValueError:
            error = error or "agy: invalid JSON stream"
            continue
        if not isinstance(event, dict):
            error = error or "agy: invalid event"
            continue
        models.update(_init_models(event))
        if event.get("event") == "result":
            if terminal_seen:
                error = error or "agy: duplicate terminal result"
                continue
            terminal_seen = True
            terminal = event.get("result")
            if not isinstance(terminal, dict):
                error = error or "agy: invalid terminal result"
                continue
            result = terminal
            if result.get("status") != "SUCCESS" or result.get("error"):
                error = error or "agy: terminal result unsuccessful"
        elif event.get("event") == "error":
            error = error or "agy: terminal error"
    text = result.get("response")
    text = text if isinstance(text, str) and text.strip() else None
    usage = result.get("usage")
    if _PRINT_TIMEOUT_PARTIAL_RE.search(stderr) or any(
        int(match["count"]) > 0 for match in _BACKGROUND_TERMINATED_RE.finditer(stderr)
    ):
        error = error or "agy: incomplete run"
    if returncode:
        error = f"agy: exited with status {returncode}"
    return ParsedResult(
        text, usage if isinstance(usage, dict) else None, error or (None if text else "agy: missing final text"),
        one_model(models),
    )
