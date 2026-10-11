#!/usr/bin/env python3
"""Content-free, frozen-sample context measurement. See the baseline runbook.

Record contract (fixed before metrics):
* Cold-start pre-action types: Claude every attachment, every system and the
  first user record before the first tool_use, measured as raw UTF-8 records.
  Codex session_meta, turn_context and response_item/message with role system
  or developer. A distinct system field is required for Codex:
  Codex session_meta.payload.base_instructions.text, turn_context.payload
  .system_prompt or .system_instructions, or a system-role message. No Codex
  field means unknown, even when pre-action records exist. Read calls never qualify.
* Compaction markers: Codex type=compacted; Claude type=system with
  subtype=compact_boundary. No occurrences means zero; never infer time gaps.
* Hook payload: attachment.content, then attachment.text, then attachment.stdout;
  otherwise the attachment object excluding its type. Claude absent payloads
  mean zero; Codex classes 2 and 8 remain unknown (field_absent).
* Claude assistant.message.content tool_use and user.message.content
  tool_result; Codex response_item.payload custom_tool_call/function_call and
  custom_tool_call_output/function_call_output. IDs join only within a session.
* Unknown record types increment other, without emitting their names. Bodies
  are discarded before reading the next line; only hashes, sizes, normalized
  hashed identities, model labels and numeric metadata survive. Oversized lines
  are drained in bounded chunks. Output labels have a closed allowlist.

Amendment 1 (normative; supersedes conflicting frozen sentences):
1. Aggregation: a harness or model aggregate is the SUM of the known per-session values, reported together with `coverage` = `{sessions_total, sessions_known, sessions_unknown, unknown_reasons: {reason: count}}`; mark the value `lower_bound: true` when any session is unknown. Only when NO session is known is the aggregate `unknown` with the dominant reason. Per-session values stay number-or-unknown exactly as before.
2. Class 3 / class 6 read identity: a read whose target cannot be recovered contributes nothing to class 3 or 6 and is counted in `read_identity_absent` (count and bytes); the class value stays a number and carries `partial: true` (a lower bound) when at least one such read exists. Do not set the class unknown for that reason.
3. Class 2 (`per_call_reinjection`) and class 8: for a harness whose transcripts record hook/attachment payloads (Claude), a session with none has value 0 (not unknown). For a harness that does not record them (Codex), the class stays `unknown` (`field_absent`).
4. Class 6: the marker types are defined per harness (Codex `compacted`; Claude `type=system` with `subtype=compact_boundary`). A session in which the marker type is defined for the harness but never occurs has `compactions: 0` and value 0. `unknown` (`no_marker`) is only for a harness with no defined marker type.
5. Class 1 for Claude (`cold_start`): the stored system prompt is not a distinct field, so the explicit pre-action list is: every `attachment` record, every `system` record and the first `user` record, occurring before the first `tool_use`. Document the list in the docstring and the runbook; the bytes are the UTF-8 length of those raw records. Codex keeps its existing definition.

Frozen definitions (normative except where amended above):
- Denominator: Codex `~/.codex/sessions/**/rollout-*.jsonl` and Claude `~/.claude/projects/**/*.jsonl` whose mtime is in `[run_start_utc − 7 days, run_start_utc)`, excluding paths that contain `subagents/` or a filename matching `agent-*.jsonl`, with at least 20 PAIRED tool calls (a tool call is paired when a call record and its result record join by the rule below). Grok, AGY, Gemini, Kimi and Cursor are reported `unavailable` with reason `no_documented_root`. Do not walk the home directory.
- Freeze: before any metric, write a mode-0600 manifest (under `batch_state/monitor-blocker-dedupe/`, never committed) that stores the full session path, harness, size, mtime, paired-tool-call count, and a 16-hex SHA-256 digest of the path; print the SHA-256 of the manifest file. `report` opens only paths listed in the manifest. If size or mtime differs from the manifest, skip that session as `stale_session`; never rescan. Stdout, the baseline JSON, error strings, tests and the runbook emit the 16-hex digest only, never the path or the raw session id.
- Join rule: Claude `tool_use.id` pairs with `tool_result.tool_use_id`; Codex `call_id` on `custom_tool_call` (and `function_call`, handled as a sibling) pairs with the matching output record. An unpaired result counts toward class 4 bytes with shape `other` and toward no other class.
- Hash and size basis: SHA-256 of the UTF-8 result body (canonical JSON with sorted keys when the body is an object); size is that body's byte length.
- Identity series (kept separate, never merged): (a) normalized path (collapse `.` and `..`, strip one trailing slash, do NOT resolve symlinks); (b) URL as scheme+host+path with query and fragment removed, then hashed; (c) allowlisted command shape (below). An identical path read through two different command shapes stays two series.
- Metric classes (per session, aggregated per harness, and per model where the model is recoverable from the transcript). Waste classes report BYTES only; classes are disjoint:
  1. `cold_start`: UTF-8 bytes of records whose type is on an explicit pre-action list (document the list in the module docstring), occurring before the first Claude `tool_use` or Codex `custom_tool_call`/`function_call`. If the system prompt is not a distinct stored field, the class is `unknown`. The first call's provider usage goes only into class 7 as `first_call_uncached_input`, `first_call_cache_creation`, `first_call_cache_read`. File reads belong to classes 3 and 6, never here.
  2. `per_call_reinjection`: `(occurrences − 1) × hashed size` of `hook_additional_context` payloads whose hash recurs on later model calls in the same session. These bytes are excluded from class 8.
  3. `repeated_reads`: for the same normalized path, or the same URL hash, read more than once with the same content hash: `(n − 1) × size`. A changed content hash is `changed_reread` and is excluded from waste (reported separately).
  4. `raw_tool_payload`: paired or unpaired tool results above 20,000 bytes: count, total bytes, share of all tool-result bytes, and the top five allowlisted command shapes by bytes.
  5. `unchanged_polls`: the same allowlisted command shape and normalized argument-free key repeated with an identical output hash, NON-READ commands only: `(n − 1) × output size`. (Reads are class 3; the same call is never counted twice.)
  6. `post_compaction_rehydration`: bytes of paired reads in the next 20 TOOL calls after a compaction marker that reuse a normalized path seen before that marker. Marker: Codex `type == compacted`, or a Claude `type`/`subtype` pair you name in the docstring BEFORE coding the metrics. With no such field the class is `unknown`. Never infer resume from a time gap.
  7. `totals`: wall time is the delta of event `timestamp` fields when both ends exist, otherwise `unknown`; paired-call count; model-call count; provider tokens, each category summed within itself and never across categories. Claude: each assistant `usage` is one request; sum `input_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens` and `output_tokens` separately. Codex: sum `last_token_usage` when present, otherwise delta `total_token_usage`, and on a negative delta (counter reset after `compacted`) add the new total as that event's increment. Copy a Codex key into a Claude category only when the key string is identical; otherwise that category is `unknown`. A bytes÷4 estimate may appear only in a separate field named `estimate`. Request-level cache counters are NOT assigned to any waste class (a repeated hook payload inside a stable cached prefix is far cheaper than the same payload in the uncached tail; this packet measures bytes, not cost).
  8. `reminder_attachments`: for the exact Claude attachment types `total_tokens_reminder`, `deferred_tools_record`, `silent_turn_reminder` and `queued_command`, waste is `(n − 1) × UTF-8 size` even when the text differs. Exclude `hook_success` and `hook_additional_context`. Codex is `unknown` until a named recurring type is written into the docstring. Any other type increments `other`.
- Every class value is a number or `unknown` plus a reason from a fixed enum (for example `field_absent`, `no_marker`, `unpaired`, `stale_session`, `no_documented_root`).
- Non-goals: no threshold or policy proposals; no edits to hooks, launchers, keeper, `current.md`, skills or rules; no session restarts; no worktree scanning or cleanup; no transcript text, commands, file contents or paths in any output, fixture or commit; no new message bus or service; no weakening of any gate.
- Independent held-out check (a later driver gate, not part of your completion): a different-family worker recomputes classes 2–5 and class 7 from these frozen sentences for six manifest digests chosen by a seed you never see, and compares wasted bytes and each class 7 category with `abs(a−b)/max(a,b)` (both zero is agreement; one `unknown` and one number is failure). Above 2% fails the packet; the implementation is then fixed to match THIS prompt, never the tolerance. You document exactly these rules in the module docstring and runbook and do not narrow them. Synthetic tests are necessary and are not evidence about real sessions.
- Stop terms: stop and report BLOCKED / ERROR / STILL WORKS / ASK if a transcript format cannot yield a class without guessing (report that class `unknown` for that harness). Two failed gate pushes with the same root cause: stop and report.

Operational interpretation: class 4 owns all oversized/unpaired results;
then class 6 owns eligible reads; then class 3/class 5 own repeats. All reads,
including large ones, update identity history, so their later small reads are
recognized. Each identity/content-hash series is counted separately;
A/B/A contains one changed reread and one repetition of A. Reminder waste sums each occurrence after the first,
using that occurrence's size. Hooks deduplicate within a model-call interval,
then count the same hash in later intervals. Poll keys are the shape only;
unknown commands (other) cannot safely be polls. Shell compound commands and
ambiguous read targets are other, never guessed. Relative paths normalize
against the stored cwd; symlinks are never resolved. Coverage counts sessions,
not model buckets or requests. Partial read values retain lower_bound in
aggregates, even when every session has a numeric value. Per-session model
buckets retain the original unknown propagation. Dominant-reason ties use
lexical order for deterministic output.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import posixpath
import re
import shlex
import sys
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

MAX_LINE = 8 * 1024 * 1024
REASONS = frozenset(
    {
        "field_absent",
        "no_marker",
        "unpaired",
        "stale_session",
        "no_documented_root",
        "no_eligible_session",
        "io_error",
        "invalid_manifest",
        "ambiguous_model",
    }
)
SHAPES = (
    "git-status",
    "git-diff",
    "git-log",
    "gh-pr-view",
    "gh-pr-diff",
    "file-read",
    "file-search",
    "pytest",
    "curl-local-api",
    "other",
)
CLASSES = (
    "cold_start",
    "per_call_reinjection",
    "repeated_reads",
    "raw_tool_payload",
    "unchanged_polls",
    "post_compaction_rehydration",
    "reminder_attachments",
)
TOKENS = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")
CODEX_TOKENS = (*TOKENS, "cached_input_tokens", "reasoning_output_tokens", "total_tokens")
REMINDERS = {"total_tokens_reminder", "deferred_tools_record", "silent_turn_reminder", "queued_command"}
KNOWN_RECORDS = {
    "session_meta",
    "turn_context",
    "event_msg",
    "response_item",
    "compacted",
    "world_state",
    "token_usage_record",
    "attachment",
    "assistant",
    "user",
    "system",
    "summary",
    "progress",
    "file-history-snapshot",
    "queue-operation",
    "last-prompt",
}
KNOWN_EVENTS = {
    "token_count",
    "task_started",
    "task_complete",
    "item_completed",
    "agent_message",
    "agent_reasoning",
    "user_message",
    "turn_aborted",
}
MODEL_RE = re.compile(r"^(?:gpt-|claude-|gemini-|grok-|o[134](?:-|$)|codex-)[a-zA-Z0-9.\[\]_-]{1,80}$")


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def body_bytes(body: Any) -> bytes:
    if isinstance(body, str):
        return body.encode("utf-8")
    return json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def unknown(reason: str) -> dict[str, Any]:
    assert reason in REASONS
    return {"value": "unknown", "reason": reason}


def value(number: int | float) -> dict[str, Any]:
    return {"value": number}


def obj(raw: Any) -> dict[str, Any]:
    return raw if isinstance(raw, dict) else {}


def records(path: Path, counters: Counter):
    """Yield one decoded record; drain oversized lines without retaining them."""
    with path.open("rb") as handle:
        while chunk := handle.readline(MAX_LINE + 1):
            length = len(chunk)
            if length > MAX_LINE:
                while not chunk.endswith(b"\n"):
                    chunk = handle.readline(MAX_LINE + 1)
                    length += len(chunk)
                    if not chunk:
                        break
                counters["oversized_line"] += 1
                del chunk
                yield {"_oversized": length}
                continue
            try:
                record = json.loads(chunk)
            except (ValueError, UnicodeError, RecursionError):
                counters["malformed_line"] += 1
                if not chunk.endswith(b"\n"):
                    counters["truncated_line"] += 1
                del chunk
                continue
            if isinstance(record, dict):
                labels = [record, obj(record.get("payload")), obj(record.get("attachment"))]
                if any("type" in item and not isinstance(item["type"], str) for item in labels):
                    counters["malformed_line"] += 1
                    del labels, record, chunk
                    continue
                record["_record_bytes"] = len(chunk.rstrip(b"\r\n"))
                yield record
                del labels, record
            else:
                counters["malformed_line"] += 1
                del record
            del chunk


def tools_in(record: dict, harness: str):
    """Emit call/result tuples without exposing any body outside the parser."""
    if harness == "codex":
        if record.get("type") != "response_item":
            return
        p = obj(record.get("payload"))
        kind = p.get("type")
        if kind in {"custom_tool_call", "function_call"} and isinstance(p.get("call_id"), str):
            yield "call", p["call_id"], p.get("name", ""), p.get("arguments", p.get("input", {}))
        elif kind in {"custom_tool_call_output", "function_call_output"} and isinstance(p.get("call_id"), str):
            yield "result", p["call_id"], "", p.get("output", "")
    else:
        message = obj(record.get("message"))
        content = message.get("content", [])
        if not isinstance(content, list):
            return
        for item in content:
            p = obj(item)
            if p.get("type") == "tool_use" and isinstance(p.get("id"), str):
                yield "call", p["id"], p.get("name", ""), p.get("input", {})
            elif p.get("type") == "tool_result" and isinstance(p.get("tool_use_id"), str):
                yield "result", p["tool_use_id"], "", p.get("content", "")


def paired_count(path: Path, harness: str) -> int:
    """Freeze selection only: join IDs without computing any metric."""
    calls: set[str] = set()
    results: set[str] = set()
    for record in records(path, Counter()):
        for kind, call_id, name, body in tools_in(record, harness):
            (calls if kind == "call" else results).add(digest(call_id))
            del name, body, call_id
        del record
    return len(calls & results)


def timestamp(raw: Any) -> datetime | None:
    if not isinstance(raw, str):
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return parsed.astimezone(UTC) if parsed.tzinfo else None
    except ValueError:
        return None


def normalize_path(raw: str, cwd: str) -> str:
    if not raw.startswith("/") and cwd:
        raw = posixpath.join(cwd, raw)
    return digest(posixpath.normpath(raw))


def url_identity(raw: str) -> str | None:
    try:
        u = urlsplit(raw)
        if u.scheme not in {"http", "https"} or not u.hostname:
            return None
        return digest(f"{u.scheme}://{u.netloc}{u.path}")
    except ValueError:
        return None


def command_shape(command: str, cwd: str) -> tuple[str, str | None, str | None]:
    """Return only fixed shape plus hashed read identity/kind, no argument text."""
    try:
        # Operators, substitutions and multiple commands cannot be safely attributed.
        words = shlex.split(command)
    except ValueError:
        return "other", None, None
    if not words or any(token in command for token in (";", "\n", "&&", "||", "|", "$(", "`", ">", "<")):
        return "other", None, None
    head = posixpath.basename(words[0])
    if head == "git":
        args = words[1:]
        directories = 0
        while args and args[0] in {"-C", "--git-dir", "--work-tree", "--no-pager", "--paginate"}:
            if args[0] in {"-C", "--git-dir", "--work-tree"}:
                directories += 1
                if directories > 1 or len(args) < 2 or args[1].startswith("-"):
                    return "other", None, None
                args = args[2:]
            else:
                args = args[1:]
        if args and args[0] in {"status", "diff", "log"}:
            return "git-" + args[0], None, None
    if head == "gh" and len(words) > 2 and words[1:3] in [["pr", "view"], ["pr", "diff"]]:
        return "gh-pr-" + words[2], None, None
    if head == "pytest" or (head in {"python", "python3"} and words[1:3] == ["-m", "pytest"]):
        return "pytest", None, None
    if head in {"cat", "head", "tail", "sed", "rg", "grep"}:
        shape = "file-search" if head in {"rg", "grep"} else "file-read"
        targets = []
        if head == "cat" and len(words) == 2 and not words[1].startswith("-"):
            targets = words[1:]
        elif head in {"head", "tail"}:
            args = words[1:]
            if len(args) == 1 and not args[0].startswith("-"):
                targets = args
            elif len(args) == 3 and args[0] in {"-n", "-c"} and args[1].isdigit():
                targets = args[2:]
        elif head == "sed" and len(words) == 4 and words[1] == "-n":
            targets = words[3:]
        elif head in {"rg", "grep"}:
            args = words[1:]
            if args and args[0] in {"-n", "-l", "-c"}:
                args = args[1:]
            if len(args) == 2 and all(not a.startswith("-") for a in args):
                targets = args[1:]
        if len(targets) == 1 and not any(c in targets[0] for c in "*?[]$"):
            return shape, normalize_path(targets[0], cwd), "path"
        return shape, None, "read_unknown"
    if head == "curl":
        urls = [w for w in words[1:] if w.startswith(("http://", "https://"))]
        if len(urls) == 1:
            identity = url_identity(urls[0])
            try:
                local = urlsplit(urls[0]).hostname in {"localhost", "127.0.0.1", "::1"}
            except ValueError:
                local = False
            return ("curl-local-api" if local else "other"), identity, "url"
    return "other", None, None


def call_shape(name: Any, arguments: Any, cwd: str) -> tuple[str, str | None, str | None]:
    if not isinstance(name, str):
        return "other", None, None
    name = name.rsplit(".", 1)[-1].lower()
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments)
        except (ValueError, RecursionError):
            # functions.exec has a JS body. Admit one literal cmd and no compounds.
            matches = re.findall(r'(?:"cmd"|\bcmd)\s*:\s*("(?:[^"\\]|\\.)*")', arguments)
            nested = re.findall(r"tools\.([A-Za-z0-9_]+)\s*\(", arguments)
            if name == "exec" and len(matches) == 1 and nested == ["exec_command"]:
                try:
                    return command_shape(json.loads(matches[0]), cwd)
                except ValueError:
                    pass
            return "other", None, None
    args = obj(arguments)
    if name in {"read", "read_file", "readfile", "glob", "grep"}:
        raw = args.get("file_path", args.get("path"))
        shape = "file-search" if name in {"glob", "grep"} else "file-read"
        return shape, normalize_path(raw, cwd) if isinstance(raw, str) else None, "path"
    if name in {"webfetch", "web_fetch", "fetch"}:
        raw = args.get("url")
        return "other", url_identity(raw) if isinstance(raw, str) else None, "url"
    cmd = args.get("command", args.get("cmd"))
    return command_shape(cmd, cwd) if isinstance(cmd, str) else ("other", None, None)


def fresh_metrics() -> dict[str, Any]:
    return {
        **{c: {"bytes": value(0)} for c in CLASSES},
        "raw_tool_payload": {"bytes": value(0), "count": value(0), "share": value(0), "top_shapes": []},
        "changed_reread": {"bytes": value(0), "count": value(0)},
        "read_identity_absent": {"bytes": value(0), "count": value(0)},
        "post_compaction_rehydration": {"bytes": value(0), "compactions": value(0)},
        "totals": {
            "paired_tool_calls": value(0),
            "model_calls": unknown("field_absent"),
            "wall_seconds": unknown("field_absent"),
            "provider_tokens": {k: unknown("field_absent") for k in CODEX_TOKENS},
            **{
                k: unknown("field_absent")
                for k in ("first_call_uncached_input", "first_call_cache_creation", "first_call_cache_read")
            },
        },
        "counters": {},
    }


def add_number(target: dict, key: str, amount: int | float) -> None:
    target[key] = value(target.get(key, {}).get("value", 0) + amount)


class Session:
    """Streaming attribution state. No result body or raw identity is retained."""

    def __init__(self, harness: str):
        self.harness = harness
        self.metrics: dict[str, dict] = {"unknown": fresh_metrics()}
        self.counters: Counter = Counter()
        self.model = "unknown"
        self.cwd = ""
        self.calls: dict[str, dict] = {}
        self.results: dict[str, dict] = {}
        self.paired: set[str] = set()
        self.reads: dict[tuple, set[str]] = {}
        self.paths: set[str] = set()
        self.pre_paths: set[str] = set()
        self.polls: dict[str, set[str]] = {}
        self.hooks: dict[str, int] = {}
        self.reminders: Counter = Counter()
        self.raw_shapes: dict[str, Counter] = {}
        self.result_bytes: Counter = Counter()
        self.bounds: dict[str, list[datetime]] = {}
        self.timestamps: list[datetime] = []
        self.tokens_previous: dict[str, int] = {}
        self.token_calls = 0
        self.tool_calls = 0
        self.compact_at: int | None = None
        self.has_system = False
        self.first_user_seen = False
        self.cold_bytes = 0
        self.first_usage: dict | None = None
        self.token_missing: dict[str, set[str]] = {}
        self.missing_read_identity: set[str] = set()

    def bucket(self, model: str | None = None) -> dict:
        key = model or self.model
        return self.metrics.setdefault(key, fresh_metrics())

    def usage(self, raw: dict) -> None:
        if not raw:
            return
        self.token_calls += 1
        t = self.bucket()["totals"]
        old = t["model_calls"]["value"]
        t["model_calls"] = value((0 if old == "unknown" else old) + 1)
        increments = {}
        for k in CODEX_TOKENS:
            n = raw.get(k)
            if isinstance(n, int) and not isinstance(n, bool) and n >= 0:
                increments[k] = n
                prior = t["provider_tokens"][k]["value"]
                t["provider_tokens"][k] = value((0 if prior == "unknown" else prior) + n)
            elif k in TOKENS:
                self.token_missing.setdefault(self.model, set()).add(k)
        if self.first_usage is None:
            self.first_usage = {k: increments.get(k) for k in TOKENS[:3]}
            for dest, source in zip(
                ("first_call_uncached_input", "first_call_cache_creation", "first_call_cache_read"),
                TOKENS[:3],
                strict=True,
            ):
                t[dest] = value(increments[source]) if source in increments else unknown("field_absent")

    def token_event(self, info: dict) -> None:
        last = obj(info.get("last_token_usage"))
        total = obj(info.get("total_token_usage"))
        if last:
            self.usage(last)
        elif total:
            increments = {}
            for k in CODEX_TOKENS:
                n = total.get(k)
                if isinstance(n, int) and not isinstance(n, bool) and n >= 0:
                    delta = n - self.tokens_previous.get(k, 0)
                    increments[k] = n if delta < 0 else delta
            self.usage(increments)
        for k in CODEX_TOKENS:
            n = total.get(k)
            if isinstance(n, int) and not isinstance(n, bool) and n >= 0:
                self.tokens_previous[k] = n

    def result(self, meta: dict, call: dict | None) -> None:
        model = call["model"] if call else meta["model"]
        m = self.bucket(model)
        size, hashed = meta["size"], meta["hash"]
        self.result_bytes[model] += size
        shape = call["shape"] if call else "other"
        large = size > 20_000 or call is None
        if large:
            add_number(m["raw_tool_payload"], "bytes", size)
            if size > 20_000:
                add_number(m["raw_tool_payload"], "count", 1)
            self.raw_shapes.setdefault(model, Counter())[shape] += size
        if call is None:
            self.counters["unpaired"] += 1
            return
        if call["kind"] is not None and call["identity"] is None:
            self.counters["read_identity_absent"] += 1
            self.counters["read_identity_absent_bytes"] += size
            add_number(m["read_identity_absent"], "count", 1)
            add_number(m["read_identity_absent"], "bytes", size)
            self.missing_read_identity.add(model)
        add_number(m["totals"], "paired_tool_calls", 1)
        identity, kind = call["identity"], call["kind"]
        if kind in {"path", "url"} and identity:
            key = (shape, kind, identity)
            seen = self.reads.setdefault(key, set())
            rehydrate = call["rehydrate"]
            if seen and hashed not in seen:
                add_number(m["changed_reread"], "bytes", size)
                add_number(m["changed_reread"], "count", 1)
            if not large:
                if rehydrate:
                    add_number(m["post_compaction_rehydration"], "bytes", size)
                elif hashed in seen:
                    add_number(m["repeated_reads"], "bytes", size)
            seen.add(hashed)
        elif kind is None and shape != "other":
            seen = self.polls.setdefault(shape, set())
            if not large and hashed in seen:
                add_number(m["unchanged_polls"], "bytes", size)
            seen.add(hashed)

    def consume(self, r: dict) -> None:
        record_size = r.pop("_record_bytes", None)
        if "_oversized" in r:
            self.result({"size": r["_oversized"], "hash": "", "model": self.model}, None)
            return
        typ = r.get("type")
        p = obj(r.get("payload"))
        msg = obj(r.get("message"))
        raw_model = p.get("model") if self.harness == "codex" else msg.get("model")
        if isinstance(raw_model, str) and MODEL_RE.fullmatch(raw_model):
            self.model = raw_model
        self.bucket()
        raw_cwd = p.get("cwd") if self.harness == "codex" else r.get("cwd")
        if isinstance(raw_cwd, str):
            self.cwd = raw_cwd
        dt = timestamp(r.get("timestamp"))
        if dt:
            # Keep only the first and latest timestamp, not an event history.
            for dates in (self.timestamps, self.bounds.setdefault(self.model, [])):
                if len(dates) < 2:
                    dates.append(dt)
                else:
                    dates[-1] = dt
        if typ not in KNOWN_RECORDS:
            self.counters["other"] += 1
        if typ == "event_msg" and p.get("type") not in KNOWN_EVENTS:
            self.counters["other"] += 1
        is_marker = (
            typ == "compacted"
            if self.harness == "codex"
            else typ == "system" and r.get("subtype") == "compact_boundary"
        )
        if is_marker:
            self.compact_at = self.tool_calls
            self.pre_paths = self.paths.copy()
            add_number(self.bucket()["post_compaction_rehydration"], "compactions", 1)
        if not self.tool_calls:
            pre = (
                self.harness == "codex"
                and (
                    typ in {"session_meta", "turn_context"}
                    or (
                        typ == "response_item"
                        and p.get("type") == "message"
                        and p.get("role") in {"system", "developer"}
                    )
                )
            ) or (
                self.harness == "claude"
                and (typ in {"attachment", "system"} or (typ == "user" and not self.first_user_seen))
            )
            if pre and (self.harness == "claude" or not is_marker):
                self.cold_bytes += record_size if record_size is not None else len(body_bytes(r))
            if typ == "user":
                self.first_user_seen = True
            system = (
                (typ == "session_meta" and isinstance(obj(p.get("base_instructions")).get("text"), str))
                or any(isinstance(p.get(k), str) for k in ("system_prompt", "system_instructions"))
                or (p.get("type") == "message" and p.get("role") == "system")
                or any(isinstance(r.get(k), str) for k in ("systemPrompt", "system_prompt"))
                or msg.get("role") == "system"
            )
            self.has_system |= system
        if self.harness == "claude" and typ == "assistant":
            self.usage(obj(msg.get("usage")))
        if self.harness == "codex" and typ == "event_msg" and p.get("type") == "token_count":
            self.token_event(obj(p.get("info")))
        if typ == "attachment":
            a = obj(r.get("attachment"))
            at = a.get("type")
            body = a.get("content", a.get("text", a.get("stdout", {k: v for k, v in a.items() if k != "type"})))
            b = body_bytes(body)
            if at == "hook_additional_context":
                hashed = hashlib.sha256(b).hexdigest()
                # Attachments before the next request belong to its call interval.
                if hashed in self.hooks and self.hooks[hashed] != self.token_calls:
                    add_number(self.bucket()["per_call_reinjection"], "bytes", len(b))
                self.hooks[hashed] = self.token_calls
            elif self.harness == "claude" and at in REMINDERS:
                if self.reminders[at]:
                    add_number(self.bucket()["reminder_attachments"], "bytes", len(b))
                self.reminders[at] += 1
            elif at != "hook_success":
                self.counters["other"] += 1
        for kind, raw_id, name, body in tools_in(r, self.harness):
            key = digest(raw_id)
            if kind == "call":
                if key in self.calls or key in self.paired:
                    self.counters["duplicate_call"] += 1
                    continue
                self.tool_calls += 1
                shape, identity, identity_kind = call_shape(name, body, self.cwd)
                rehydrate = (
                    self.compact_at is not None
                    and self.tool_calls - self.compact_at <= 20
                    and identity_kind == "path"
                    and identity in self.pre_paths
                )
                if identity_kind == "path" and identity:
                    self.paths.add(identity)
                call = {
                    "shape": shape,
                    "identity": identity,
                    "kind": identity_kind,
                    "model": self.model,
                    "rehydrate": rehydrate,
                }
                self.calls[key] = call
                if key in self.results:
                    self.result(self.results.pop(key), self.calls.pop(key))
                    self.paired.add(key)
            else:
                b = body_bytes(body)
                meta = {"size": len(b), "hash": hashlib.sha256(b).hexdigest(), "model": self.model}
                if key in self.paired or key in self.results:
                    self.counters["duplicate_result"] += 1
                    continue
                if key in self.calls:
                    self.result(meta, self.calls.pop(key))
                    self.paired.add(key)
                else:
                    self.results[key] = meta

    def finish(self) -> dict:
        for result in self.results.values():
            self.result(result, None)
        self.counters["unpaired_call"] += len(self.calls)
        # Cold records often precede model metadata; assign only for a single model.
        models = [k for k in self.metrics if k != "unknown"]
        cold_model = models[0] if len(models) == 1 else "unknown"
        for model, m in self.metrics.items():
            if model in self.missing_read_identity:
                for category in ("repeated_reads", "post_compaction_rehydration"):
                    m[category]["bytes"].update(partial=True, lower_bound=True)
            m["cold_start"]["bytes"] = (
                value(self.cold_bytes if model == cold_model else 0)
                if self.harness == "claude" or self.has_system
                else unknown("field_absent")
            )
            if self.harness not in {"codex", "claude"}:
                m["post_compaction_rehydration"]["bytes"] = unknown("no_marker")
            if self.harness == "codex":
                m["per_call_reinjection"]["bytes"] = unknown("field_absent")
                m["reminder_attachments"]["bytes"] = unknown("field_absent")
            for k in self.token_missing.get(model, set()):
                m["totals"]["provider_tokens"][k] = unknown("field_absent")
            dates = self.bounds.get(model, [])
            if len(dates) == 2:
                m["totals"]["wall_seconds"] = value((dates[-1] - dates[0]).total_seconds())
            total = self.result_bytes[model]
            m["raw_tool_payload"]["share"] = value(m["raw_tool_payload"]["bytes"]["value"] / total if total else 0)
            m["raw_tool_payload"]["top_shapes"] = [
                {"shape": k, "bytes": v} for k, v in self.raw_shapes.get(model, Counter()).most_common(5)
            ]
            m["totals"]["tool_result_bytes"] = value(total)
        # Do not invent an unknown-model request for metadata-only preamble lines.
        unattributed = self.metrics["unknown"]
        if (
            models
            and all(unattributed[c]["bytes"]["value"] in {0, "unknown"} for c in CLASSES)
            and not self.result_bytes["unknown"]
            and not unattributed["read_identity_absent"]["count"]["value"]
            and not unattributed["post_compaction_rehydration"]["compactions"]["value"]
            and unattributed["totals"]["model_calls"]["value"] == "unknown"
        ):
            del self.metrics["unknown"]
        session = aggregate(list(self.metrics.values()), session_coverage=False)
        dates = self.timestamps
        session["totals"]["wall_seconds"] = (
            value((dates[-1] - dates[0]).total_seconds()) if len(dates) == 2 else unknown("field_absent")
        )
        session["cold_start"]["bytes"] = (
            value(self.cold_bytes) if self.harness == "claude" or self.has_system else unknown("field_absent")
        )
        session["totals"]["model_calls"] = value(self.token_calls) if self.token_calls else unknown("field_absent")
        # A metadata-only unknown bucket must not turn known request totals unknown.
        used = [m for m in self.metrics.values() if m["totals"]["model_calls"]["value"] != "unknown"]
        if used:
            session["totals"]["provider_tokens"] = aggregate(
                [m["totals"]["provider_tokens"] for m in used], session_coverage=False
            )
            for k in ("first_call_uncached_input", "first_call_cache_creation", "first_call_cache_read"):
                present = [m["totals"][k] for m in used if m["totals"][k]["value"] != "unknown"]
                session["totals"][k] = present[0] if present else unknown("field_absent")
        session["counters"] = dict(self.counters)
        return {"metrics": session, "models": self.metrics}


def aggregate(items: list[dict], *, session_coverage: bool = True) -> dict:
    """Sum known session values with coverage; keep intra-session unknowns."""
    if not items:
        return {}
    if "value" in items[0]:
        known = [i for i in items if i["value"] != "unknown"]
        reasons = Counter(i["reason"] for i in items if i["value"] == "unknown")
        if reasons and not session_coverage:
            return next(i.copy() for i in items if i["value"] == "unknown")
        result = (
            value(sum(i["value"] for i in known))
            if known
            else unknown(min(reasons, key=lambda reason: (-reasons[reason], reason)))
        )
        if session_coverage:
            result["coverage"] = {
                "sessions_total": len(items),
                "sessions_known": len(known),
                "sessions_unknown": len(items) - len(known),
                "unknown_reasons": dict(sorted(reasons.items())),
            }
        if reasons or any(i.get("lower_bound") for i in known):
            result["lower_bound"] = True
        if any(i.get("partial") for i in known):
            result["partial"] = True
        return result
    out = {}
    for key in dict.fromkeys(k for i in items for k in i):
        parts = [i[key] for i in items if key in i]
        if key == "top_shapes":
            shapes: Counter = Counter()
            for part in parts:
                for row in part:
                    shapes[row["shape"]] += row["bytes"]
            out[key] = [{"shape": k, "bytes": n} for k, n in shapes.most_common(5)]
        elif all(isinstance(p, dict) for p in parts):
            out[key] = aggregate(parts, session_coverage=session_coverage)
        elif all(isinstance(p, (int, float)) for p in parts):
            out[key] = sum(parts)
    if "raw_tool_payload" in out:
        total = out["totals"].get("tool_result_bytes", value(0))["value"]
        out["raw_tool_payload"]["share"]["value"] = out["raw_tool_payload"]["bytes"]["value"] / total if total else 0
    return out


def parse_session(path: Path, harness: str) -> dict:
    session = Session(harness)
    for record in records(path, session.counters):
        session.consume(record)
        del record
    return session.finish()


def write_private(path: Path, payload: dict) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    # Refuse symlink targets, and tighten an existing file before writing.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as handle:
        os.fchmod(handle.fileno(), 0o600)
        handle.write(data)
    return hashlib.sha256(data).hexdigest()


def freeze(manifest: Path, *, roots: dict[str, Path] | None = None, run_start: datetime | None = None) -> dict:
    start = run_start or datetime.now(UTC)
    roots = (
        roots
        if roots is not None
        else {"codex": Path.home() / ".codex/sessions", "claude": Path.home() / ".claude/projects"}
    )
    sessions, errors = [], []
    excluded: Counter = Counter()
    availability = {}
    for harness in ("codex", "claude"):
        root = roots.get(harness)
        count = 0
        if root is not None and root.is_dir():
            pattern = "rollout-*.jsonl" if harness == "codex" else "*.jsonl"
            # No other roots, worktrees, or home-directory scan.
            for path in sorted(root.rglob(pattern)):
                if "subagents" in path.parts or path.match("agent-*.jsonl"):
                    continue
                sid = digest(str(path))[:16]
                try:
                    st = path.stat()
                    if not (start.timestamp() - timedelta(days=7).total_seconds() <= st.st_mtime < start.timestamp()):
                        continue
                    count += 1
                    paired = paired_count(path, harness)
                    after = path.stat()
                    if (st.st_size, st.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                        errors.append({"digest": sid, "reason": "stale_session"})
                        continue
                    if paired < 20:
                        excluded["below_paired_floor"] += 1
                        continue
                    sessions.append(
                        {
                            "path": str(path),
                            "digest": sid,
                            "harness": harness,
                            "size": st.st_size,
                            "mtime": st.st_mtime_ns,
                            "paired_tool_calls": paired,
                        }
                    )
                except OSError:
                    errors.append({"digest": sid, "reason": "io_error"})
        availability[harness] = {"candidates": count}
    payload = {
        "schema": "context-cost-manifest.v1",
        "run_start_utc": start.isoformat(),
        "sessions": sessions,
        "availability": availability,
        "errors": errors,
        "excluded": dict(excluded),
    }
    sha = write_private(manifest, payload)
    return {"manifest_sha256": sha, "sessions": len(sessions), "excluded": dict(excluded), "errors": errors}


def report(manifest: Path, *, tool_sha: str = "unknown") -> dict:
    if tool_sha != "unknown" and not re.fullmatch(r"[0-9a-f]{40}", tool_sha):
        raise ValueError("invalid_manifest")
    raw = manifest.read_bytes()
    frozen = json.loads(raw)
    if not isinstance(frozen, dict) or frozen.get("schema") != "context-cost-manifest.v1":
        raise ValueError("invalid_manifest")
    start = timestamp(frozen.get("run_start_utc"))
    if start is None or not isinstance(frozen.get("sessions"), list):
        raise ValueError("invalid_manifest")
    excluded = obj(frozen.get("excluded"))
    if any(k != "below_paired_floor" or not isinstance(v, int) or v < 0 for k, v in excluded.items()):
        raise ValueError("invalid_manifest")
    sessions, skipped = [], []
    for error in frozen.get("errors", []):
        sid = error.get("digest")
        reason = error.get("reason")
        if (
            not isinstance(sid, str)
            or not re.fullmatch(r"[0-9a-f]{16}", sid)
            or reason not in {"io_error", "stale_session"}
        ):
            raise ValueError("invalid_manifest")
        skipped.append({"digest": sid, "reason": reason})
    for entry in frozen["sessions"]:
        sid = entry["digest"]
        if not isinstance(sid, str) or not re.fullmatch(r"[0-9a-f]{16}", sid):
            raise ValueError("invalid_manifest")
        path = Path(entry["path"])
        if digest(str(path))[:16] != sid or entry["harness"] not in {"codex", "claude"}:
            raise ValueError("invalid_manifest")
        try:
            st = path.stat()
            if (st.st_size, st.st_mtime_ns) != (entry["size"], entry["mtime"]):
                skipped.append({"digest": sid, "reason": "stale_session"})
                continue
            result = parse_session(path, entry["harness"])
            st = path.stat()
            if (st.st_size, st.st_mtime_ns) != (entry["size"], entry["mtime"]):
                skipped.append({"digest": sid, "reason": "stale_session"})
                continue
            sessions.append({"digest": sid, "harness": entry["harness"], **result})
        except OSError:
            skipped.append({"digest": sid, "reason": "io_error"})
    harnesses = {}
    for harness in ("codex", "claude", "grok", "agy", "gemini", "kimi", "cursor"):
        group = [s for s in sessions if s["harness"] == harness]
        if not group:
            reason = "no_documented_root" if harness not in {"codex", "claude"} else "no_eligible_session"
            harnesses[harness] = {"status": "unavailable", "reason": reason}
            continue
        models = {}
        for s in group:
            for model, metrics in s["models"].items():
                models.setdefault(model, []).append(metrics)
        harnesses[harness] = {
            "status": "available",
            "sessions": len(group),
            "metrics": aggregate([s["metrics"] for s in group]),
            "models": {k: aggregate(v) for k, v in sorted(models.items())},
        }
    return {
        "schema": "context-cost-baseline.v1",
        "tool_sha": tool_sha,
        "manifest_sha256": hashlib.sha256(raw).hexdigest(),
        "run_start_utc": start.isoformat(),
        "sessions": sessions,
        "harnesses": harnesses,
        "skipped": skipped,
        "excluded": excluded,
    }


class PrivateParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.exit(2, "invalid_arguments\n")


def build_parser() -> argparse.ArgumentParser:
    description = (
        "Measure content-free context bytes and provider token categories from a frozen sample.\n"
        "Use for local baselines; never use to set thresholds or infer policy or cost."
    )
    epilog = """Examples:
  .venv/bin/python scripts/ops/context_cost_report.py freeze --manifest batch_state/monitor-blocker-dedupe/sample.json
  .venv/bin/python scripts/ops/context_cost_report.py report --manifest batch_state/monitor-blocker-dedupe/sample.json --text
Outputs: freeze writes a private mode-0600 manifest; report prints content-free JSON or a short table.
Exit codes: 0 success (including explicit unknowns); 1 IO/manifest error; 2 invalid arguments.
Related: docs/runbooks/context-cost-baseline.md; #10421."""
    parser = PrivateParser(description=description, epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True, help="freeze the sample or report its metrics")
    for name in ("freeze", "report"):
        child = commands.add_parser(
            name,
            description=description,
            epilog=epilog,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            help="write the frozen manifest" if name == "freeze" else "measure only frozen sessions",
        )
        child.add_argument(
            "--manifest",
            type=Path,
            required=True,
            help="Private manifest file, e.g. batch_state/monitor-blocker-dedupe/sample.json (required; no default)",
        )
        if name == "report":
            child.add_argument(
                "--tool-sha",
                default="unknown",
                help="Verified tool commit SHA, e.g. the 40-hex result of git rev-parse HEAD (default: unknown; parser spawns no process)",
            )
            child.add_argument(
                "--text", action="store_true", help="Print a short aggregate table instead of JSON (default: false)"
            )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = freeze(args.manifest) if args.command == "freeze" else report(args.manifest, tool_sha=args.tool_sha)
    except OSError:
        print(json.dumps({"error": "io_error", "digest": digest(str(args.manifest))[:16]}), file=sys.stderr)
        return 1
    except (ValueError, KeyError, TypeError, RecursionError):
        print(json.dumps({"error": "invalid_manifest", "digest": digest(str(args.manifest))[:16]}), file=sys.stderr)
        return 1
    if getattr(args, "text", False):
        print("harness sessions " + " ".join(CLASSES))
        for harness, row in result["harnesses"].items():
            if row["status"] == "unavailable":
                print(f"{harness} unavailable {row['reason']}")
            else:
                cells = []
                for c in CLASSES:
                    measure = row["metrics"][c]["bytes"]
                    cell = str(measure["value"]) if measure["value"] != "unknown" else f"unknown({measure['reason']})"
                    coverage = measure["coverage"]
                    flags = [f"coverage={coverage['sessions_known']}/{coverage['sessions_total']}"]
                    flags += [f"{key}=true" for key in ("lower_bound", "partial") if measure.get(key)]
                    cells.append(cell + "[" + ";".join(flags) + "]")
                print(f"{harness} {row['sessions']} " + " ".join(cells))
    else:
        print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
