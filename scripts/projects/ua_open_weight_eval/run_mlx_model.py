#!/usr/bin/env python3
"""Run one already-downloaded MLX model over a source-only UA Eval packet.

The runner has no benchmark-gold dependency and performs no network access. It
keeps an append-only local checkpoint so a long 4,000-case run can resume
without regenerating completed items.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

REQUEST_SCHEMA = "ua_open_weight_eval_requests.v1"
RESPONSE_SCHEMA = "ua_open_weight_eval_responses.v1"
ALLOWED_ACTIONS = frozenset({"correct", "preserve", "abstain"})


class RunnerError(ValueError):
    """A source packet, model reply, or checkpoint is invalid."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_path(path: Path) -> str:
    _require(path.is_dir(), "model must be an existing local directory")
    digest = hashlib.sha256()
    files = sorted(item for item in path.rglob("*") if item.is_file() or item.is_symlink())
    _require(bool(files), "model directory contains no files")
    for item in files:
        _require(not item.is_symlink(), "model directory cannot contain symlinks")
        relative = item.relative_to(path).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        size = item.stat().st_size
        digest.update(size.to_bytes(8, "big"))
        with item.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
    return digest.hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RunnerError(message)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise RunnerError(f"cannot read JSONL {path}: {exc}") from exc
    rows: list[dict[str, Any]] = []
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RunnerError(f"invalid JSONL {path}:{number}: {exc}") from exc
        _require(isinstance(value, dict), f"expected object at {path}:{number}")
        rows.append(value)
    _require(bool(rows), f"empty JSONL: {path}")
    return rows


def load_requests(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    rows = read_jsonl(path)
    header, requests = rows[0], rows[1:]
    _require(header.get("type") == "request_run", "request packet header is missing")
    _require(header.get("schema_version") == REQUEST_SCHEMA, "request schema drift")
    _require(header.get("gold_fields_supplied") == [], "request packet exposes gold fields")
    _require(
        header.get("input_fields") == ["item_id", "source", "source_sha256", "instruction_sha256"],
        "request input field contract drift",
    )
    _require(header.get("case_count") == len(requests), "request count drift")
    _require(len(requests) == 4000, "the frozen release requires exactly 4,000 requests")
    instruction_sha256 = header.get("instruction_sha256")
    _require(
        isinstance(instruction_sha256, str) and instruction_sha256 == sha256_text(str(header.get("instruction", ""))),
        "instruction hash drift",
    )
    seen: set[str] = set()
    for row in requests:
        _require(row.get("type") == "request", "non-request row in packet")
        item_id = row.get("item_id")
        source = row.get("source")
        _require(isinstance(item_id, str) and item_id and item_id not in seen, "invalid or duplicate item_id")
        _require(isinstance(source, str) and source, f"missing source for {item_id}")
        _require(row.get("source_sha256") == sha256_text(source), f"source hash drift for {item_id}")
        _require(row.get("instruction_sha256") == instruction_sha256, f"instruction drift for {item_id}")
        payload = {
            "item_id": item_id,
            "source": source,
            "source_sha256": row["source_sha256"],
            "instruction_sha256": instruction_sha256,
        }
        _require(row.get("request_sha256") == sha256_text(canonical_json(payload)), f"request hash drift for {item_id}")
        _require(
            not {"expected", "target", "targets", "reference", "references", "edit", "edits"}.intersection(row),
            f"gold field in {item_id}",
        )
        seen.add(item_id)
    return header, requests


def format_prompt(source: str) -> str:
    source_json = json.dumps(source, ensure_ascii=False)
    return (
        "You are evaluating Ukrainian correction versus faithful preservation. "
        "Return exactly one JSON object and no markdown or explanation. "
        'The object must have the keys "action" and "output_text". '
        '"action" must be "correct", "preserve", or "abstain". '
        "Correct only a clearly warranted Ukrainian error. Preserve quotations, proper names, "
        "historical or regional language, deliberate register, and genuinely acceptable text. "
        "Use abstain when the evidence is insufficient. For preserve or abstain, copy the source "
        f"exactly as output_text. Source JSON string: {source_json}"
    )


def parse_model_reply(reply: str) -> dict[str, str]:
    decoder = json.JSONDecoder()
    candidates: list[Mapping[str, Any]] = []
    for index, character in enumerate(reply):
        if character != "{":
            continue
        try:
            value, _ = decoder.raw_decode(reply[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            candidates.append(value)
    _require(len(candidates) == 1, "model reply must contain exactly one JSON object")
    value = candidates[0]
    _require(set(value) == {"action", "output_text"}, "model reply field set drift")
    action = value.get("action")
    output_text = value.get("output_text")
    _require(action in ALLOWED_ACTIONS, "model reply has an invalid action")
    _require(isinstance(output_text, str) and output_text, "model reply has no output_text")
    return {"action": str(action), "output_text": output_text}


def load_checkpoint(path: Path, run_header: Mapping[str, Any]) -> list[dict[str, Any]]:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(canonical_json(dict(run_header)) + "\n", encoding="utf-8")
        return []
    rows = read_jsonl(path)
    _require(rows[0] == run_header, "checkpoint run header drift")
    records = rows[1:]
    seen: set[str] = set()
    for record in records:
        _require(set(record) == {"item_id", "request_sha256", "raw_generation", "response"}, "checkpoint field drift")
        item_id = record.get("item_id")
        response = record.get("response")
        _require(isinstance(item_id, str) and item_id not in seen, "invalid or duplicate checkpoint item")
        _require(isinstance(record.get("raw_generation"), str), f"missing raw generation for {item_id}")
        _require(isinstance(response, dict), f"missing checkpoint response for {item_id}")
        parse_model_reply(canonical_json(response))
        seen.add(item_id)
    return records


def append_checkpoint(path: Path, record: Mapping[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(canonical_json(dict(record)) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def write_responses(path: Path, header: Mapping[str, Any], records: Sequence[Mapping[str, Any]]) -> None:
    rows = [dict(header)]
    rows.extend({"item_id": record["item_id"], **record["response"]} for record in records)
    temporary = path.with_name(f".{path.name}.tmp")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary.write_text("".join(canonical_json(row) + "\n" for row in rows), encoding="utf-8")
    temporary.replace(path)


def load_mlx_generator(model_path: Path, max_tokens: int) -> Callable[[str], str]:
    try:
        import mlx.core as mx
        from mlx_lm import generate, load
        from mlx_lm.sample_utils import make_sampler
    except ImportError as exc:
        raise RunnerError("mlx-lm is not installed in the active .venv") from exc

    model, tokenizer = load(str(model_path), lazy=False)
    sampler = make_sampler(temp=0.0)

    def generate_one(prompt: str) -> str:
        messages = [{"role": "user", "content": prompt}]
        rendered = tokenizer.apply_chat_template(messages, add_generation_prompt=True, tokenize=False)
        _require(isinstance(rendered, str), "tokenizer did not render a chat prompt")
        mx.random.seed(0)
        return generate(model, tokenizer, prompt=rendered, max_tokens=max_tokens, sampler=sampler, verbose=False)

    return generate_one


def run(args: argparse.Namespace, generator: Callable[[str], str] | None = None) -> dict[str, Any]:
    model_path = args.model.expanduser().resolve()
    _require(model_path.is_dir(), "model must be an existing local directory")
    _require(
        len(args.model_sha256) == 64 and all(character in "0123456789abcdef" for character in args.model_sha256),
        "model_sha256 must be lowercase SHA-256",
    )
    _require(sha256_path(model_path) == args.model_sha256, "model path hash mismatch")
    request_header, requests = load_requests(args.requests)
    run_header = {
        "type": "checkpoint_run",
        "schema_version": "ua_open_weight_eval_mlx_checkpoint.v1",
        "release_id": request_header["release_id"],
        "requests_sha256": hashlib.sha256(args.requests.read_bytes()).hexdigest(),
        "model": args.model_id,
        "model_revision": args.model_revision,
        "model_sha256": args.model_sha256,
        "backend": "mlx-lm",
        "decoding": {"temperature": 0.0, "max_tokens": args.max_tokens, "seed": 0},
        "network_allowed": False,
    }
    records = load_checkpoint(args.state, run_header)
    by_id = {str(record["item_id"]): record for record in records}
    expected_prefix = [row["item_id"] for row in requests[: len(records)]]
    _require(list(by_id) == expected_prefix, "checkpoint is not an exact request-order prefix")
    for request, record in zip(requests, records, strict=False):
        _require(record["request_sha256"] == request["request_sha256"], "checkpoint request hash drift")
        _require(
            parse_model_reply(record["raw_generation"]) == record["response"],
            "checkpoint response does not match raw generation",
        )
    if generator is None:
        generator = load_mlx_generator(model_path, args.max_tokens)

    for position, request in enumerate(requests[len(records) :], len(records) + 1):
        prompt = format_prompt(request["source"])
        last_error = ""
        for attempt in range(args.parse_retries + 1):
            retry_prompt = prompt
            if attempt:
                retry_prompt += f" Previous reply was invalid ({last_error}); return only the required JSON object."
            raw_generation = generator(retry_prompt)
            try:
                response = parse_model_reply(raw_generation)
            except RunnerError as exc:
                last_error = str(exc)
                continue
            record = {
                "item_id": request["item_id"],
                "request_sha256": request["request_sha256"],
                "raw_generation": raw_generation,
                "response": response,
            }
            append_checkpoint(args.state, record)
            records.append(record)
            break
        else:
            raise RunnerError(f"cannot parse model reply for {request['item_id']}: {last_error}")
        if position % args.progress_every == 0 or position == len(requests):
            print(f"mlx-runner: completed {position}/{len(requests)}", file=sys.stderr, flush=True)

    response_header = {
        "type": "run",
        "schema_version": RESPONSE_SCHEMA,
        "release_id": request_header["release_id"],
        "model": args.model_id,
        "model_revision": args.model_revision,
        "model_sha256": args.model_sha256,
        "backend": "mlx-lm",
        "decoding": run_header["decoding"],
        "network_allowed": False,
        "closed_api_used": False,
    }
    write_responses(args.responses, response_header, records)
    return {"status": "passed", "responses": len(records), "path": str(args.responses)}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--requests", type=Path, required=True)
    parser.add_argument("--responses", type=Path, required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--model-revision", required=True)
    parser.add_argument("--model-sha256", required=True)
    parser.add_argument("--max-tokens", type=int, default=160)
    parser.add_argument("--parse-retries", type=int, default=2)
    parser.add_argument("--progress-every", type=int, default=25)
    args = parser.parse_args(argv)
    _require(args.max_tokens > 0, "max_tokens must be positive")
    _require(args.parse_retries >= 0, "parse_retries cannot be negative")
    _require(args.progress_every > 0, "progress_every must be positive")
    return args


def main(argv: Sequence[str] | None = None) -> int:
    try:
        result = run(parse_args(argv))
    except (OSError, RunnerError) as exc:
        print(f"mlx-runner: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
