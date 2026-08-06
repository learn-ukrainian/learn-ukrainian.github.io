#!/usr/bin/env python3
"""Private, deterministic capture bridge for cleared Phase 3 author packets.

The runner deliberately has no Ukrainian decision logic.  It prepares a single
attachment/prompt per packet, optionally calls the subscription-only AGY bridge,
and preserves untrusted output as bytes plus a mechanical parse record.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_rule_author_packets as packets

ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = "scripts/projects/open_model_data/phase3_rule_author_runner.py"
SCHEMA_PATH = ROOT / "data/projects/open_model_data/contracts/phase3_rule_author_run_manifest_v1.schema.json"
VERSION = "phase3_rule_author_runner_v1"
PRIVATE_MODE = 0o700
FILE_MODE = 0o600
CANONICAL_AGY_MODEL = "gemini-3.6-flash-high"


class RuleAuthorRunnerError(ValueError):
    """A private run cannot establish its source/binding boundary."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuleAuthorRunnerError(message)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuleAuthorRunnerError(f"cannot read JSON: {path}") from exc
    require(isinstance(value, dict), "JSON document must be an object")
    return value


def _no_alias(path: Path, label: str) -> Path:
    """Canonicalize safe ancestors while rejecting a symlink at the requested leaf."""
    require(not path.is_symlink(), f"{label} must not be a symlink")
    return path.resolve(strict=True)


def _private_root(path: Path, *, create: bool) -> Path:
    if create:
        path.mkdir(mode=PRIVATE_MODE, parents=True, exist_ok=True)
    root = _no_alias(path, "private directory")
    require(root.is_dir(), "private path is not a directory")
    require(stat.S_IMODE(root.stat().st_mode) == PRIVATE_MODE, "private directory must be mode 0700")
    return root


def _write_private(path: Path, value: bytes) -> None:
    if path.exists():
        require(not path.is_symlink() and path.resolve() == path.absolute(), "private output path is aliased")
    path.parent.mkdir(mode=PRIVATE_MODE, parents=True, exist_ok=True)
    os.chmod(path.parent, PRIVATE_MODE)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as handle:
            temporary = Path(handle.name)
            os.chmod(temporary, FILE_MODE)
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        os.chmod(path, FILE_MODE)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def _assert_private_file(root: Path, relative: str) -> Path:
    path = root / relative
    require(path.exists() and not path.is_symlink() and path.resolve() == path.absolute(), f"missing or aliased {relative}")
    require(path.is_file() and stat.S_IMODE(path.stat().st_mode) == FILE_MODE, f"private file must be 0600: {relative}")
    return path


def _manifest_validator() -> Draft202012Validator:
    schema = _read_json(SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _validate_manifest(manifest: Mapping[str, Any]) -> None:
    errors = sorted(_manifest_validator().iter_errors(manifest), key=lambda error: list(error.path))
    require(not errors, f"run manifest schema violation: {errors[0].message if errors else ''}")


def _validate_receipt(receipt: Mapping[str, Any]) -> None:
    schema = _read_json(SCHEMA_PATH)
    wrapper = {"$schema": schema["$schema"], "$defs": schema["$defs"], "$ref": "#/$defs/publicReceipt"}
    errors = sorted(Draft202012Validator(wrapper).iter_errors(receipt), key=lambda error: list(error.path))
    require(not errors, f"public receipt schema violation: {errors[0].message if errors else ''}")
    require(receipt.get("no_leakage") is True, "public receipt leakage invariant is false")


def _receipt_has_no_leakage(receipt: Mapping[str, Any]) -> bool:
    forbidden = {"packet_id", "source_item_id", "locator", "fingerprint", "source_text", "corrected_text", "raw_response", "response"}

    def walk(value: Any) -> bool:
        if isinstance(value, Mapping):
            return all(not any(word in str(key).lower() for word in forbidden) and walk(child) for key, child in value.items())
        return all(walk(child) for child in value) if isinstance(value, list) else True

    return walk(receipt)


def _author(role_path: Path, exact_model: str) -> dict[str, str]:
    require(exact_model == CANONICAL_AGY_MODEL, "exact model is not the canonical AGY Gemini model")
    role = packets.read_json(role_path)
    actor = packets._derive_role_actor(role, "rule_author_extractor")
    return {**actor, "provider": "google", "model_family": "gemini", "harness": "agy", "exact_model": exact_model}


def _validate_bundle(path: Path) -> dict[str, Any]:
    bundle = packets.read_json(path)
    schema = packets._local_schema(packets.read_json(packets.SCHEMA_PATH))
    errors = sorted(Draft202012Validator(schema).iter_errors(bundle), key=lambda error: list(error.path))
    require(not errors, f"packet bundle schema violation: {errors[0].message if errors else ''}")
    require(bundle.get("compiler", {}).get("implementation_version") == packets.IMPLEMENTATION_VERSION, "packet compiler binding drift")
    require(
        bundle["compiler"].get("script_sha256") == sha256_file(ROOT / packets.SCRIPT_PATH),
        "packet compiler script binding drift",
    )
    require(
        bundle["compiler"].get("query_plan_sha256") == packets._query_plan_sha256(),
        "packet compiler query-plan binding drift",
    )
    require(
        bundle.get("phase3_v2_contract_sha256") == packets.PHASE3_V2_CONTRACT_SHA256
        and bundle["compiler"].get("phase3_v2_contract_sha256") == packets.PHASE3_V2_CONTRACT_SHA256,
        "packet bundle Phase 3 v2 contract binding drift",
    )
    return bundle


def _prompt(author: Mapping[str, str], packet_sha: str, prompt_sha_placeholder: str = "computed after serialization") -> str:
    # No output self-hash is requested: the runner adds only mechanical capture
    # fields after preserving the model's exact raw bytes.
    return "\n".join((
        "You are the assigned Phase 3 rule-author extractor, not a reviewer or scorer.",
        f"Binding: role={author['role_id']}; controller={author['controller_identity_id']}; task={author['task_id']}.",
        "The attached private packet is the complete and only evidence. Do not use model memory as authority.",
        "Do not access, infer, mention, or reconstruct heldout, UA-Eval, or public-canary material.",
        "Propose only source-supported candidates from attached source_item_id values; abstain when the source is insufficient.",
        "Return one JSON object only with keys proposals, abstentions, limitations, parse_state.",
        "Each proposal must satisfy the Phase 3 typed matcher/output schema; matcher.kind must equal the proposal's mechanism value (for example, both literal).",
        "Every proposal source_item_id and evidence_refs must reference attached source_item_id values, and source_span must match that item.",
        "This is a non-authoritative proposal; do not claim Ukrainian review, acceptance, publication, or completion.",
        f"Mechanical packet SHA-256: {packet_sha}.",
        f"Prompt hash note: {prompt_sha_placeholder}.",
        "",
    ))


def _expected_paths(manifest: Mapping[str, Any]) -> set[str]:
    paths = {"manifest.json"}
    for entry in manifest["packets"]:
        paths.update((entry["attachment"], entry["prompt"], entry["raw"], entry["record"]))
    return paths


def _assert_tree(root: Path, manifest: Mapping[str, Any], *, permit_empty_results: bool) -> None:
    expected = _expected_paths(manifest)
    actual: set[str] = set()
    for path in root.rglob("*"):
        relative = path.relative_to(root).as_posix()
        require(not path.is_symlink(), f"symlink forbidden in private run: {relative}")
        if path.is_dir():
            require(stat.S_IMODE(path.stat().st_mode) == PRIVATE_MODE, f"private directory must be 0700: {relative}")
        elif path.is_file():
            require(stat.S_IMODE(path.stat().st_mode) == FILE_MODE, f"private file must be 0600: {relative}")
            actual.add(relative)
    require(actual <= expected, "unexpected private run file")
    require({"manifest.json"} | {entry["attachment"] for entry in manifest["packets"]} | {entry["prompt"] for entry in manifest["packets"]} <= actual, "prepared private files are incomplete")
    require(actual <= expected and (permit_empty_results or actual == expected), "private run tree is incomplete")
    for entry in manifest["packets"]:
        raw, record = root / entry["raw"], root / entry["record"]
        require(raw.exists() == record.exists(), "raw response and parse record must be paired")


def prepare(*, bundle_path: Path, role_path: Path, private_dir: Path, exact_model: str) -> dict[str, Any]:
    """Prepare canonical private attachments/prompts, idempotently on exact identity."""
    bundle_path, role_path = _no_alias(bundle_path, "bundle"), _no_alias(role_path, "role contract")
    bundle, author = _validate_bundle(bundle_path), _author(role_path, exact_model)
    require(bundle["role_contract_sha256"] == sha256_file(role_path), "packet bundle role-contract binding drift")
    root = _private_root(private_dir, create=True)
    entries: list[dict[str, Any]] = []
    for packet in bundle["packets"]:
        ordinal = packet["ordinal"]
        attachment = canonical_json(packet).encode("utf-8") + b"\n"
        packet_sha = sha256_bytes(attachment)
        prompt = _prompt(author, packet_sha).encode("utf-8")
        entries.append({
            "ordinal": ordinal, "packet_id": packet["packet_id"], "packet_sha256": packet_sha,
            "attachment": f"attachments/{ordinal}.json", "attachment_sha256": sha256_bytes(attachment),
            "prompt": f"prompts/{ordinal}.txt", "prompt_sha256": sha256_bytes(prompt),
            "raw": f"raw/{ordinal}.raw", "record": f"records/{ordinal}.json",
        })
    manifest = {
        "schema_version": "phase3_rule_author_run_manifest_v1", "bundle_sha256": sha256_file(bundle_path),
        "role_contract_sha256": sha256_file(role_path),
        "bindings": {
            "evaluation_contract_sha256": bundle["evaluation_contract_sha256"],
            "phase3_v2_contract_sha256": bundle["phase3_v2_contract_sha256"],
            "coverage_contract_sha256": bundle["coverage_contract_sha256"],
            "near_duplicate_policy_sha256": bundle["near_duplicate_policy_fingerprint_sha256"],
            "query_plan_sha256": bundle["compiler"]["query_plan_sha256"],
            "packet_schema_sha256": sha256_file(packets.SCHEMA_PATH),
            "compiler": bundle["compiler"],
        },
        "runner": {"implementation_version": VERSION, "script_sha256": sha256_file(ROOT / SCRIPT_PATH), "schema_sha256": sha256_file(SCHEMA_PATH)},
        "author": author, "packets": entries,
    }
    _validate_manifest(manifest)
    existing = root / "manifest.json"
    if existing.exists():
        old = _read_json(_assert_private_file(root, "manifest.json"))
        require(old == manifest, "resume binding or hash drift")
        _assert_tree(root, old, permit_empty_results=True)
        for entry in entries:
            require(sha256_file(_assert_private_file(root, entry["attachment"])) == entry["attachment_sha256"], "attachment hash drift")
            require(sha256_file(_assert_private_file(root, entry["prompt"])) == entry["prompt_sha256"], "prompt hash drift")
            if (root / entry["record"]).exists():
                _validate_record(entry, old, root)
        return old
    require(not any(root.iterdir()), "private run directory contains unexpected files")
    _write_private(root / "manifest.json", (canonical_json(manifest) + "\n").encode("utf-8"))
    for entry, packet in zip(entries, bundle["packets"], strict=True):
        _write_private(root / entry["attachment"], canonical_json(packet).encode("utf-8") + b"\n")
        _write_private(root / entry["prompt"], _prompt(author, entry["packet_sha256"]).encode("utf-8"))
    _assert_tree(root, manifest, permit_empty_results=True)
    return manifest


def command_for(entry: Mapping[str, Any], manifest: Mapping[str, Any], root: Path) -> list[str]:
    """Return the fixed subscription bridge command; prompt bytes go on stdin."""
    return [str(ROOT / ".venv/bin/python"), str(ROOT / "scripts/ai_agent_bridge/__main__.py"), "ask-agy", "-", "--task-id", manifest["author"]["task_id"], "--to-model", manifest["author"]["exact_model"], "--data", str(root / entry["attachment"]), "--output-path", str(root / entry["raw"])]


def _record(entry: Mapping[str, Any], manifest: Mapping[str, Any], root: Path, *, execution_error: str | None = None) -> dict[str, Any]:
    raw = _assert_private_file(root, entry["raw"]).read_bytes()
    attachment_path = _assert_private_file(root, entry["attachment"])
    require(sha256_file(attachment_path) == entry["attachment_sha256"], "attachment hash drift")
    packet = _read_json(attachment_path)
    packets.validate(packet, "packet", "attached packet")
    base: dict[str, Any] = {"packet_sha256": entry["packet_sha256"], "prompt_sha256": entry["prompt_sha256"], "raw_response_sha256": sha256_bytes(raw), "author": manifest["author"]}
    try:
        untrusted = json.loads(raw.decode("utf-8"))
        require(isinstance(untrusted, dict), "raw response JSON is not an object")
        allowed = {"proposals", "abstentions", "limitations", "parse_state"}
        require(set(untrusted) == allowed, "raw response has forbidden or missing fields")
        response = {"schema_version": "phase3_rule_author_response_v1", "authority_state": "non_authoritative_model_proposal", **base, **untrusted}
        packets.validate(response, "ruleAuthorResponse", "rule-author response")
        item_spans = {item["source_item_id"]: item["source_span"] for item in packet["items"]}
        for proposal in response["proposals"]:
            require(proposal["source_item_id"] in item_spans and proposal["source_span"] == item_spans[proposal["source_item_id"]], "proposal source binding drift")
            require(proposal["evidence_refs"] and set(proposal["evidence_refs"]) <= {proposal["source_item_id"]}, "proposal evidence is not source-only")
        record = {"state": "parsed", "response": response, "execution_error": execution_error}
    except (UnicodeDecodeError, json.JSONDecodeError, RuleAuthorRunnerError, packets.PacketCompilerError) as exc:
        record = {"state": "unparsed", "packet_sha256": entry["packet_sha256"], "prompt_sha256": entry["prompt_sha256"], "raw_response_sha256": sha256_bytes(raw), "technical_error": str(exc), "execution_error": execution_error}
    return {**record, "record_sha256": sha256_bytes(canonical_json(record).encode("utf-8"))}


def _validate_record(entry: Mapping[str, Any], manifest: Mapping[str, Any], root: Path) -> dict[str, Any]:
    record = _read_json(_assert_private_file(root, entry["record"]))
    stored_hash = record.get("record_sha256")
    unsigned = {key: value for key, value in record.items() if key != "record_sha256"}
    require(
        isinstance(stored_hash, str) and stored_hash == sha256_bytes(canonical_json(unsigned).encode("utf-8")),
        "record self-integrity hash drift",
    )
    expected = _record(entry, manifest, root, execution_error=record.get("execution_error"))
    require(record == expected, "resume record hash, schema, or binding drift")
    return record


def _receipt(manifest: Mapping[str, Any], root: Path) -> dict[str, Any]:
    records = []
    for entry in manifest["packets"]:
        path = root / entry["record"]
        if path.exists():
            records.append(_validate_record(entry, manifest, root))
    parsed = [record for record in records if record["state"] == "parsed"]
    fully_attempted = len(records) == len(manifest["packets"])
    failed_count = sum(bool(record.get("execution_error")) for record in records)
    complete = fully_attempted and len(parsed) == len(records) and failed_count == 0
    canary_succeeded = not fully_attempted and bool(records) and len(parsed) == len(records) and failed_count == 0
    prompt_set_sha = sha256_bytes(canonical_json([entry["prompt_sha256"] for entry in manifest["packets"]]).encode("utf-8"))
    receipt = {"schema_version": "phase3_rule_author_public_receipt_v1", "text_free": True, "execution_mode": "sequential", "planned_count": len(manifest["packets"]), "attempted_count": len(records), "parsed_count": len(parsed), "unparsed_count": sum(record["state"] == "unparsed" for record in records), "failed_count": failed_count, "proposal_count": sum(len(record.get("response", {}).get("proposals", [])) for record in parsed), "abstention_count": sum(len(record.get("response", {}).get("abstentions", [])) for record in parsed), "bundle_sha256": manifest["bundle_sha256"], "phase3_v2_contract_sha256": manifest["bindings"]["phase3_v2_contract_sha256"], "role_contract_sha256": manifest["role_contract_sha256"], "evaluation_contract_sha256": manifest["bindings"]["evaluation_contract_sha256"], "coverage_contract_sha256": manifest["bindings"]["coverage_contract_sha256"], "near_duplicate_policy_sha256": manifest["bindings"]["near_duplicate_policy_sha256"], "query_plan_sha256": manifest["bindings"]["query_plan_sha256"], "packet_schema_sha256": manifest["bindings"]["packet_schema_sha256"], "compiler": manifest["bindings"]["compiler"], "runner": manifest["runner"], "prompt_set_sha256": prompt_set_sha, "model": {key: manifest["author"][key] for key in ("provider", "model_family", "harness", "exact_model")}, "complete": complete, "canary": not fully_attempted, "canary_succeeded": canary_succeeded}
    receipt["no_leakage"] = _receipt_has_no_leakage(receipt)
    _validate_receipt(receipt)
    return receipt


def run(
    *,
    bundle_path: Path,
    role_path: Path,
    private_dir: Path,
    receipt_path: Path,
    exact_model: str,
    max_packets: int | None = None,
    executor: Callable[[list[str], bytes], Any] | None = None,
) -> dict[str, Any]:
    """Execute a bounded set with the subscription bridge, then capture safely."""
    require(max_packets is None or max_packets >= 1, "max packets must be positive")
    manifest = prepare(bundle_path=bundle_path, role_path=role_path, private_dir=private_dir, exact_model=exact_model)
    root = _private_root(private_dir, create=False)
    safe_receipt_path = _safe_receipt_path(
        receipt_path,
        bundle_path=bundle_path,
        role_path=role_path,
        private_dir=root,
        manifest=manifest,
    )
    selected_entries = manifest["packets"][:max_packets] if max_packets else manifest["packets"]
    invoke = executor or (lambda command, stdin: subprocess.run(command, input=stdin, check=False, capture_output=True))
    for entry in selected_entries:
        record_path = root / entry["record"]
        if record_path.exists():
            _assert_private_file(root, entry["record"])
            continue
        raw_path = root / entry["raw"]
        raw_path.parent.mkdir(mode=PRIVATE_MODE, parents=True, exist_ok=True)
        os.chmod(raw_path.parent, PRIVATE_MODE)
        execution_error = None
        try:
            prompt = _assert_private_file(root, entry["prompt"]).read_bytes()
            require(sha256_bytes(prompt) == entry["prompt_sha256"], "prompt hash drift")
            result = invoke(command_for(entry, manifest, root), prompt)
            if getattr(result, "returncode", 0) != 0:
                execution_error = f"bridge_exit_{getattr(result, 'returncode', 1)}"
        except OSError as exc:
            execution_error = f"bridge_oserror:{exc.__class__.__name__}"
        if not raw_path.exists():
            _write_private(raw_path, b"")
            execution_error = execution_error or "bridge_did_not_write_output"
        else:
            require(not raw_path.is_symlink() and raw_path.resolve() == raw_path.absolute(), "bridge output path is aliased")
            os.chmod(raw_path, FILE_MODE)
        _write_private(record_path, (canonical_json(_record(entry, manifest, root, execution_error=execution_error)) + "\n").encode("utf-8"))
    if max_packets is None:
        _assert_tree(root, manifest, permit_empty_results=False)
    receipt = _receipt(manifest, root)
    _write_public_receipt(safe_receipt_path, (canonical_json(receipt) + "\n").encode("utf-8"))
    return receipt


def _safe_receipt_path(
    path: Path,
    *,
    bundle_path: Path,
    role_path: Path,
    private_dir: Path,
    manifest: Mapping[str, Any],
) -> Path:
    parent = _no_alias(path.parent, "receipt parent")
    candidate = parent / path.name
    require(not candidate.exists() or not candidate.is_symlink(), "receipt path is aliased")
    try:
        candidate.absolute().relative_to(private_dir.absolute())
    except ValueError:
        pass
    else:
        raise RuleAuthorRunnerError("public receipt must be outside the private run directory")
    protected = [bundle_path, role_path, SCHEMA_PATH, ROOT / SCRIPT_PATH]
    protected.extend(private_dir / relative for relative in _expected_paths(manifest))
    for target in protected:
        target = target.absolute()
        if candidate.absolute() == target or (candidate.exists() and target.exists() and os.path.samefile(candidate, target)):
            raise RuleAuthorRunnerError("receipt destination aliases a protected input or private file")
    return candidate


def _write_public_receipt(path: Path, value: bytes) -> None:
    """Atomically write a public-safe receipt without changing parent permissions."""
    parent = _no_alias(path.parent, "receipt parent")
    require(parent.is_dir(), "receipt parent is not a directory")
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=parent, prefix=f".{path.name}.", delete=False) as handle:
            temporary = Path(handle.name)
            os.chmod(temporary, FILE_MODE)
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        os.chmod(path, FILE_MODE)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def verify(*, bundle_path: Path, role_path: Path, private_dir: Path, exact_model: str) -> dict[str, Any]:
    manifest = prepare(bundle_path=bundle_path, role_path=role_path, private_dir=private_dir, exact_model=exact_model)
    root = _private_root(private_dir, create=False)
    _assert_tree(root, manifest, permit_empty_results=False)
    for entry in manifest["packets"]:
        if (root / entry["record"]).exists():
            _validate_record(entry, manifest, root)
        else:
            require(not (root / entry["raw"]).exists(), "raw response without parse record")
    return {"ok": True, "packets": len(manifest["packets"])}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare/capture private Phase 3 AGY rule-author runs.")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("prepare", "verify", "run"):
        child = commands.add_parser(name)
        child.add_argument("--bundle", required=True, type=Path)
        child.add_argument("--role-contract", required=True, type=Path)
        child.add_argument("--private-dir", required=True, type=Path)
        child.add_argument("--exact-model", required=True)
        if name == "run":
            child.add_argument("--receipt", required=True, type=Path)
            child.add_argument("--max-packets", type=int)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.command == "prepare":
            result = prepare(
                bundle_path=args.bundle,
                role_path=args.role_contract,
                private_dir=args.private_dir,
                exact_model=args.exact_model,
            )
        elif args.command == "verify":
            result = verify(
                bundle_path=args.bundle,
                role_path=args.role_contract,
                private_dir=args.private_dir,
                exact_model=args.exact_model,
            )
        else:
            result = run(
                bundle_path=args.bundle,
                role_path=args.role_contract,
                private_dir=args.private_dir,
                receipt_path=args.receipt,
                exact_model=args.exact_model,
                max_packets=args.max_packets,
            )
        public_result = result if args.command == "run" else {"packets": result.get("packets")}
        print(canonical_json({"ok": True, "result": public_result}))
    except RuleAuthorRunnerError as exc:
        print(canonical_json({"ok": False, "error": str(exc)}))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
