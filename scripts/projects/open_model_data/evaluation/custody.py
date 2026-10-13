"""Dispatch-bound sealed reader with durable, content-free access receipts."""

from __future__ import annotations

import fcntl
import json
import os
import re
import time
import uuid
from contextlib import contextmanager, suppress
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

import yaml

from scripts.common.task_store_paths import tasks_dir
from scripts.orchestration.dispatch_isolation import scope_cgroup, scope_unit_matches
from scripts.orchestration.execution_safe_git import run_git
from scripts.orchestration.task_record_store import locate_task_record
from scripts.projects.open_model_data.review_build.contract import canonical, digest
from scripts.projects.open_model_data.review_build.errors import BuildError
from scripts.projects.open_model_data.review_build.output import OutputGuard
from scripts.review.model_catalog import CATALOG_PATH, canonical_model_id, load_model_catalog, validate_catalog

Purpose = Literal["custody_verify", "final_evaluation"]
STEWARD = re.compile(r"eval-steward-6321-[a-z0-9-]+\Z")
HEX = re.compile(r"[0-9a-f]{64}\Z")
COMMIT = re.compile(r"[0-9a-f]{40}\Z")
TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}\Z")
# Reserved lookup only. This task neither creates nor commits a real manifest.
MANIFEST_PATH = "docs/projects/open-model-data/sealed-rulers.json"
CATALOG_BLOB = "scripts/config/model_catalog.yaml"
REPOSITORY = Path(__file__).resolve().parents[4]
LOG = "access-log.jsonl"
LOCK = "access-log.lock"
SCHEMA = "omd-custody-access.v1"
LOCK_TIMEOUT = 1.0


class CustodyRefused(Exception):
    """Closed-code diagnostics never include input, payload or locations."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class StewardDesignation:
    task_id: str
    run_nonce: str
    model: str
    launch_unit: str
    record_sha256: str


@dataclass(frozen=True)
class ArtifactRef:
    component: str
    split: Literal["final"]
    ruler_version: str


class SealedPayload:
    """Evaluator-only bytes; printing this object never prints its data."""

    __slots__ = ("__payload",)

    def __init__(self, payload: bytes):
        self.__payload = payload

    def data(self) -> bytes:
        return self.__payload

    def __repr__(self) -> str:
        return "<SealedPayload redacted>"

    __str__ = __repr__


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise CustodyRefused(code)


def _record(task_id: str, *, hot: bool) -> tuple[dict, str]:
    try:
        root = tasks_dir()
        path = locate_task_record(root, task_id)
        _require(path is not None and (not hot or path.parent == root), "record_unavailable")
        raw = path.read_bytes()
        record = json.loads(raw)
        _require(isinstance(record, dict), "record_unavailable")
        return record, digest(raw)
    except (OSError, ValueError, TypeError):
        raise CustodyRefused("record_unavailable") from None


def _model(model: object) -> str:
    try:
        catalog = load_model_catalog()
        expected = catalog["seats"]["openai_frontier"]["model_id"]
        resolved = canonical_model_id(model, catalog)
        _require(resolved == expected and catalog["models"][expected]["lifecycle"] == "active", "model_not_admitted")
        return resolved
    except (ValueError, KeyError, TypeError):
        raise CustodyRefused("model_not_admitted") from None


def resolve_designation() -> StewardDesignation:
    """Resolve only dispatch-owned environment, hot record, catalog and cgroup."""
    task_id = os.environ.get("LEARN_UKRAINIAN_DISPATCH_TASK_ID", "")
    nonce = os.environ.get("LU_RUNTIME_RUN_NONCE", "")
    _require(bool(task_id and nonce), "not_dispatched")
    _require(bool(STEWARD.fullmatch(task_id)), "not_steward_family")
    _require("LU_TASKS_DIR" not in os.environ, "tasks_dir_override")
    record, sha = _record(task_id, hot=True)
    _require(record.get("task_id") == task_id and record.get("run_nonce") == nonce, "run_mismatch")
    _require(record.get("status") == "running", "not_running")
    unit = record.get("launch_unit")
    _require(
        record.get("launch_mode") == "scope"
        and isinstance(unit, str)
        and scope_unit_matches(unit, task_id=task_id, run_nonce=nonce),
        "unbound_launch",
    )
    try:
        lines = Path("/proc/self/cgroup").read_text().splitlines()
        paths = [line[3:] for line in lines if line.startswith("0::")]
        _require(len(paths) == 1, "cgroup_unavailable")
    except (OSError, UnicodeError):
        raise CustodyRefused("cgroup_unavailable") from None
    expected = scope_cgroup(unit, uid=os.getuid())
    actual = paths[0]
    _require(
        actual == expected
        or (
            actual.startswith(expected + "/")
            and all(p not in {"", ".", ".."} for p in actual[len(expected) + 1 :].split("/"))
        ),
        "cgroup_mismatch",
    )
    return StewardDesignation(task_id, nonce, _model(record.get("model")), unit, sha)


def recheck(designation: StewardDesignation) -> None:
    """Repeat the full resolution; non-identity record fields may change."""
    current = resolve_designation()
    _require(
        (current.task_id, current.run_nonce, current.model, current.launch_unit)
        == (designation.task_id, designation.run_nonce, designation.model, designation.launch_unit),
        "designation_stale",
    )


def _ref(ref: ArtifactRef) -> dict:
    _require(
        isinstance(ref, ArtifactRef)
        and isinstance(ref.component, str)
        and bool(re.fullmatch(r"C(?:[1-79]|6[ab])", ref.component))
        and ref.split == "final"
        and isinstance(ref.ruler_version, str)
        and bool(TOKEN.fullmatch(ref.ruler_version)),
        "artifact_ref",
    )
    return asdict(ref)


def _artifact_name(ref: ArtifactRef) -> str:
    return digest(canonical(_ref(ref))) + ".sealed"


def _main_commit(code: str) -> str:
    result = run_git(
        ["rev-parse", "--verify", "refs/remotes/origin/main^{commit}"], cwd=REPOSITORY, capture_output=True
    )
    _require(result.returncode == 0, code)
    commit = result.stdout.decode("ascii").strip()
    _require(bool(COMMIT.fullmatch(commit)), code)
    return commit


def _catalog_blob(commit: str) -> bytes:
    result = run_git(["cat-file", "blob", f"{commit}:{CATALOG_BLOB}"], cwd=REPOSITORY, capture_output=True)
    _require(result.returncode == 0, "issuer_admission_unavailable")
    return result.stdout


def _admission_shape(value: object) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"schema", "model", "catalog_commit", "catalog_sha256"}
        and value["schema"] == "omd-issuer-admission.v1"
        and isinstance(value["model"], str)
        and bool(TOKEN.fullmatch(value["model"]))
        and isinstance(value["catalog_commit"], str)
        and bool(COMMIT.fullmatch(value["catalog_commit"]))
        and isinstance(value["catalog_sha256"], str)
        and bool(HEX.fullmatch(value["catalog_sha256"]))
    )


def _catalog_unchanged(raw: bytes) -> None:
    try:
        _require(CATALOG_PATH.read_bytes() == raw, "issuer_admission_invalid")
    except OSError:
        raise CustodyRefused("issuer_admission_unavailable") from None


def _sealing_admission(designation: StewardDesignation) -> tuple[dict, bytes]:
    try:
        commit = _main_commit("issuer_admission_unavailable")
        raw = _catalog_blob(commit)
        catalog = validate_catalog(yaml.safe_load(raw))
        model = canonical_model_id(designation.model, catalog)
        _require(
            model == catalog["seats"]["openai_frontier"]["model_id"]
            and catalog["models"][model]["lifecycle"] == "active",
            "model_not_admitted",
        )
        admission = {
            "schema": "omd-issuer-admission.v1",
            "model": model,
            "catalog_commit": commit,
            "catalog_sha256": digest(raw),
        }
        _require(_admission_shape(admission), "issuer_admission_invalid")
        _catalog_unchanged(raw)
        return admission, raw
    except OSError:
        raise CustodyRefused("issuer_admission_unavailable") from None
    except (ValueError, TypeError, KeyError, yaml.YAMLError):
        raise CustodyRefused("issuer_admission_invalid") from None


def _manifest(ref: ArtifactRef) -> tuple[dict, str]:
    wanted = _ref(ref)
    try:
        commit = _main_commit("manifest_unmerged")
        result = run_git(["cat-file", "blob", f"{commit}:{MANIFEST_PATH}"], cwd=REPOSITORY, capture_output=True)
        _require(result.returncode == 0, "manifest_unmerged")
        manifest = json.loads(result.stdout)
        _require(isinstance(manifest, dict) and manifest.get("schema") == "omd-sealed-rulers.v1", "manifest_invalid")
        entries = manifest.get("entries")
        _require(isinstance(entries, list) and all(isinstance(e, dict) for e in entries), "manifest_invalid")
        matches = [e for e in entries if all(e.get(k) == v for k, v in wanted.items())]
        _require(len(matches) == 1, "artifact_ref")
        entry = matches[0]
        _require(
            set(entry)
            in (
                {*wanted, "sha256", "bytes", "sealed_by_task_id", "custody_genesis_sha256"},
                {*wanted, "sha256", "bytes", "sealed_by_task_id", "custody_genesis_sha256", "sealed_event_sha256"},
            )
            and (
                "sealed_event_sha256" not in entry
                or (isinstance(entry["sealed_event_sha256"], str) and bool(HEX.fullmatch(entry["sealed_event_sha256"])))
            )
            and isinstance(entry["sha256"], str)
            and bool(HEX.fullmatch(entry["sha256"]))
            and type(entry["bytes"]) is int
            and entry["bytes"] >= 0
            and isinstance(entry["custody_genesis_sha256"], str)
            and bool(HEX.fullmatch(entry["custody_genesis_sha256"]))
            and isinstance(entry["sealed_by_task_id"], str)
            and bool(STEWARD.fullmatch(entry["sealed_by_task_id"])),
            "manifest_invalid",
        )
        return entry, commit
    except (OSError, ValueError, TypeError):
        raise CustodyRefused("manifest_unmerged") from None


def _identity() -> dict:
    """Untrusted claims are reduced to bounded ASCII labels and a nonce hash."""
    task = os.environ.get("LEARN_UKRAINIAN_DISPATCH_TASK_ID", "")
    return {
        "task_id": task if re.fullmatch(r"[a-z0-9-]{1,160}", task) else "unknown",
        "run_nonce_sha256": digest(os.environ.get("LU_RUNTIME_RUN_NONCE", "").encode()),
    }


def _append(out: OutputGuard, chain: list[dict], event: str, **fields) -> dict:
    entry = {
        "schema": SCHEMA,
        "seq": len(chain),
        "prev_sha256": digest(canonical(chain[-1])) if chain else "0" * 64,
        "event": event,
        "time": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **fields,
    }
    try:
        out.append(LOG, canonical(entry) + b"\n")
    except (BuildError, OSError, TypeError):
        raise CustodyRefused("access_log_unavailable") from None
    chain.append(entry)
    return entry


def _chain(out: OutputGuard) -> list[dict]:
    try:
        raw = out.read(LOG)
        _require(bool(raw) and raw.endswith(b"\n"), "access_log_corrupt")
        chain = []
        for line in raw.split(b"\n")[:-1]:
            entry = json.loads(line)
            _require(line == canonical(entry) and line.isascii(), "access_log_corrupt")
            chain.append(entry)
        previous = "0" * 64
        pending = set()
        for seq, entry in enumerate(chain):
            _require(isinstance(entry, dict) and canonical(entry).isascii(), "access_log_corrupt")
            common = {"schema", "seq", "prev_sha256", "event", "time"}
            event = entry.get("event")
            extras = {
                "genesis": {"custody_id"},
                "sealed": {"ref", "sha256", "bytes", "task_id", "run_nonce_sha256"},
                "attempt": {"attempt_id", "task_id", "run_nonce_sha256", "ref", "purpose"},
                "completed": {"attempt_id"},
                "refused": {"attempt_id", "code"},
                "open_failed": {"attempt_id", "code"},
                "interrupted": {"attempt_id", "reconciled_by"},
            }
            if event == "sealed" and "issuer_admission" in entry:
                extras[event] = extras[event] | {"issuer_admission"}
                _require(_admission_shape(entry["issuer_admission"]), "access_log_corrupt")
            _require(event in extras and set(entry) == common | extras[event], "access_log_corrupt")
            _require(
                entry["schema"] == SCHEMA
                and type(entry["seq"]) is int
                and entry["seq"] == seq
                and entry["prev_sha256"] == previous,
                "access_log_corrupt",
            )
            _require(
                isinstance(entry["time"], str)
                and bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", entry["time"])),
                "access_log_corrupt",
            )
            _require((event == "genesis") == (seq == 0), "access_log_corrupt")
            for key in extras[event] - {"ref", "bytes", "purpose", "issuer_admission"}:
                value = entry[key]
                pattern = (
                    r"[a-z0-9_-]{1,160}"
                    if key in {"task_id", "code"}
                    else r"[0-9a-f]{64}"
                    if key in {"sha256", "run_nonce_sha256"}
                    else r"[0-9a-f]{32}"
                )
                _require(isinstance(value, str) and bool(re.fullmatch(pattern, value)), "access_log_corrupt")
            if "ref" in entry and entry["ref"] is not None:
                _require(
                    isinstance(entry["ref"], dict) and _ref(ArtifactRef(**entry["ref"])) == entry["ref"],
                    "access_log_corrupt",
                )
            if "purpose" in entry:
                _require(entry["purpose"] in {"custody_verify", "final_evaluation", "invalid"}, "access_log_corrupt")
            if "bytes" in entry:
                _require(type(entry["bytes"]) is int and entry["bytes"] >= 0, "access_log_corrupt")
            if event == "attempt":
                _require(entry["attempt_id"] not in pending, "access_log_corrupt")
                pending.add(entry["attempt_id"])
            elif event in {"completed", "refused", "open_failed", "interrupted"}:
                _require(entry["attempt_id"] in pending, "access_log_corrupt")
                pending.remove(entry["attempt_id"])
            previous = digest(canonical(entry))
        return chain
    except BuildError:
        raise CustodyRefused("access_log_unavailable") from None
    except (ValueError, TypeError, KeyError, CustodyRefused):
        raise CustodyRefused("access_log_corrupt") from None


@contextmanager
def _locked(out: OutputGuard):
    fd = -1
    try:
        try:
            out.append(LOCK, b"")
            fd = os.open(LOCK, os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=out.fd)
            deadline = time.monotonic() + LOCK_TIMEOUT
            while True:
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    _require(time.monotonic() < deadline, "custody_busy")
                    time.sleep(0.01)
        except (BuildError, OSError):
            raise CustodyRefused("access_log_unavailable") from None
        yield
    finally:
        if fd >= 0:
            os.close(fd)


def _reconcile(out: OutputGuard, chain: list[dict], current: str) -> None:
    pending = set()
    for entry in chain:
        if entry["event"] == "attempt":
            pending.add(entry["attempt_id"])
        elif entry["event"] in {"completed", "refused", "open_failed", "interrupted"}:
            pending.remove(entry["attempt_id"])
    for attempt in sorted(pending):
        _append(out, chain, "interrupted", attempt_id=attempt, reconciled_by=current)


def _issuer(entry: dict, chain: list[dict], ref: ArtifactRef, manifest_commit: str) -> None:
    matches = [event for event in chain if event["event"] == "sealed" and event["ref"] == _ref(ref)]
    _require(len(matches) == 1, "issuer_invalid")
    event = matches[0]
    _require("issuer_admission" in event or "sealed_event_sha256" in entry, "issuer_admission_missing")
    _require(
        "issuer_admission" in event and entry.get("sealed_event_sha256") == digest(canonical(event)),
        "issuer_admission_invalid",
    )
    admission = event["issuer_admission"]
    try:
        result = run_git(
            ["merge-base", "--is-ancestor", admission["catalog_commit"], manifest_commit],
            cwd=REPOSITORY,
            capture_output=True,
        )
        _require(result.returncode in {0, 1}, "issuer_admission_unavailable")
        _require(result.returncode == 0, "issuer_admission_invalid")
        raw = _catalog_blob(admission["catalog_commit"])
        _require(digest(raw) == admission["catalog_sha256"], "issuer_admission_invalid")
        catalog = yaml.safe_load(raw)
        # Historical identity projection only: today's routing/freshness schema
        # must not revoke a seal's immutable admission witness.
        _require(
            isinstance(catalog, dict) and catalog.get("schema_version") in {"model-catalog.v1", "model-catalog.v1.1"},
            "issuer_admission_invalid",
        )
        models = catalog["models"]
        _require(isinstance(models, dict), "issuer_admission_invalid")
        for model_id, model in models.items():
            _require(
                isinstance(model_id, str)
                and isinstance(model, dict)
                and isinstance(model.get("aliases", []), list)
                and all(isinstance(alias, str) for alias in model.get("aliases", [])),
                "issuer_admission_invalid",
            )
        expected = catalog["seats"]["openai_frontier"]["model_id"]
        _require(
            expected == admission["model"] and models.get(expected, {}).get("lifecycle") == "active",
            "model_not_admitted",
        )
    except OSError:
        raise CustodyRefused("issuer_admission_unavailable") from None
    except (ValueError, KeyError, TypeError, yaml.YAMLError):
        raise CustodyRefused("issuer_admission_invalid") from None
    record, _ = _record(entry["sealed_by_task_id"], hot=False)
    _require(record.get("task_id") == entry["sealed_by_task_id"] and record.get("status") == "done", "issuer_invalid")
    _require(canonical_model_id(record.get("model"), catalog) == admission["model"], "model_not_admitted")
    nonce = record.get("run_nonce")
    _require(isinstance(nonce, str) and bool(nonce), "issuer_invalid")
    _require(
        event["task_id"] == entry["sealed_by_task_id"]
        and event["run_nonce_sha256"] == digest(nonce.encode())
        and event["ref"] == _ref(ref)
        and event["sha256"] == entry["sha256"]
        and event["bytes"] == entry["bytes"],
        "issuer_invalid",
    )


def read_sealed(ref: ArtifactRef, purpose: Purpose, *, custody_root: Path) -> SealedPayload | bool:
    """Return bytes only after the completed receipt has been durably appended."""
    try:
        out = OutputGuard(custody_root, (REPOSITORY,))
    except BuildError:
        raise CustodyRefused("access_log_unavailable") from None
    with out, _locked(out):
        chain = _chain(out)
        attempt = uuid.uuid4().hex
        _reconcile(out, chain, attempt)
        try:
            safe_ref = _ref(ref)
        except CustodyRefused:
            safe_ref = None
        _append(
            out,
            chain,
            "attempt",
            attempt_id=attempt,
            **_identity(),
            ref=safe_ref,
            purpose=purpose
            if isinstance(purpose, str) and purpose in {"custody_verify", "final_evaluation"}
            else "invalid",
        )
        terminal = False
        try:
            designation = resolve_designation()
            _require(isinstance(purpose, str) and purpose in {"custody_verify", "final_evaluation"}, "purpose_invalid")
            entry, manifest_commit = _manifest(ref)
            _require(digest(canonical(chain[0])) == entry["custody_genesis_sha256"], "custody_genesis")
            _issuer(entry, chain, ref, manifest_commit)
            try:
                payload = out.read(_artifact_name(ref))
            except (BuildError, OSError, TypeError):
                _append(out, chain, "open_failed", attempt_id=attempt, code="artifact_open")
                terminal = True
                raise CustodyRefused("artifact_open") from None
            if digest(payload) != entry["sha256"] or len(payload) != entry["bytes"]:
                del payload
                raise CustodyRefused("artifact_digest")
            try:
                recheck(designation)
            except CustodyRefused:
                del payload
                raise CustodyRefused("designation_stale") from None
            _append(out, chain, "completed", attempt_id=attempt)
            terminal = True
            return True if purpose == "custody_verify" else SealedPayload(payload)
        except CustodyRefused as exc:
            if not terminal and exc.code != "access_log_unavailable":
                _append(out, chain, "refused", attempt_id=attempt, code=exc.code)
                terminal = True
            raise
        finally:
            if not terminal:
                with suppress(CustodyRefused):
                    _append(out, chain, "interrupted", attempt_id=attempt, reconciled_by=attempt)


def seal(ref: ArtifactRef, payload: bytes, *, custody_root: Path) -> str:
    """Synthetic-only steward writer support. No real sealing is authorized here."""
    designation = resolve_designation()
    _ref(ref)
    _require(isinstance(payload, bytes), "payload_type")
    admission, catalog_raw = _sealing_admission(designation)
    try:
        with OutputGuard(custody_root, (REPOSITORY,)) as out, _locked(out):
            if LOG in os.listdir(out.fd):
                chain = _chain(out)
            else:
                chain = []
                _append(out, chain, "genesis", custody_id=uuid.uuid4().hex)
            _reconcile(out, chain, uuid.uuid4().hex)
            _require(not any(e["event"] == "sealed" and e["ref"] == _ref(ref) for e in chain), "already_sealed")
            recheck(designation)
            _catalog_unchanged(catalog_raw)
            _require(_artifact_name(ref) not in os.listdir(out.fd), "artifact_exists")
            out.append(_artifact_name(ref), payload)
            recheck(designation)
            _catalog_unchanged(catalog_raw)
            sha = digest(payload)
            _append(
                out,
                chain,
                "sealed",
                ref=_ref(ref),
                sha256=sha,
                bytes=len(payload),
                task_id=designation.task_id,
                run_nonce_sha256=digest(designation.run_nonce.encode()),
                issuer_admission=admission,
            )
            return sha
    except BuildError:
        raise CustodyRefused("artifact_open") from None
