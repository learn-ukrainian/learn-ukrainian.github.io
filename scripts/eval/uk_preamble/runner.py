"""Plan candidate and judge tasks and execute them with safe resume.

Results directory layout (private, given on the command line)::

    manifest.json              frozen set/variant/template hashes, run tag
    prompts/<task_id>.md       exact prompt sent
    raw/<task_id>.json         attributed outcome and raw response
    raw/<task_id>.pending.json dispatched, outcome not collected yet
"""

from __future__ import annotations

import itertools
import sys
import threading
import time
from collections.abc import Callable, Iterable, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .common import (
    BASELINE_VARIANT,
    CANDIDATE_ORDER,
    HARNESS_VERSION,
    SEATS,
    HarnessError,
    Seat,
    judge_seats,
    read_json,
    sha256_text,
    write_private_json,
    write_private_text,
)
from .dataset import EvalSet, Variant
from .dispatch import Dispatcher, DispatchError, TaskOutcome
from .prompts import build_prompt, review_payload, template_fingerprint, validate_response, writing_payload

KINDS = ("review", "writing")
TASK_PREFIX = "uk9623"


@dataclass(frozen=True)
class Slot:
    """One candidate task's identity, without its prompt (scoring re-plans slots)."""

    task_id: str
    seat: Seat
    variant: str
    repeat: int
    kind: str
    item_ids: tuple[str, ...]


@dataclass(frozen=True)
class TaskSpec:
    task_id: str
    seat: Seat
    kind: str
    variant: str | None
    repeat: int
    item_ids: tuple[str, ...]
    prompt: str
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def prompt_sha256(self) -> str:
        return sha256_text(self.prompt)


def ordered_labels(labels: Iterable[str]) -> list[str]:
    """Baseline first, then the pre-registered candidates, then any others alphabetically."""
    labels = list(labels)
    head = [BASELINE_VARIANT] if BASELINE_VARIANT in labels else []
    head += [label for label in CANDIDATE_ORDER if label in labels]
    return head + sorted(label for label in labels if label not in head)


def _chunks(values: Sequence[Any], size: int) -> list[Sequence[Any]]:
    return [values[i : i + size] for i in range(0, len(values), size)]


def resolve_seats(seat_ids: Sequence[str] | None) -> list[Seat]:
    if not seat_ids:
        return list(SEATS.values())
    unknown = [seat for seat in seat_ids if seat not in SEATS]
    if unknown:
        raise HarnessError(f"unknown seat(s) {', '.join(unknown)}; known: {', '.join(SEATS)}")
    return [SEATS[seat] for seat in dict.fromkeys(seat_ids)]


def candidate_slots(
    eval_set: EvalSet,
    seats: Sequence[Seat],
    labels: Sequence[str],
    repeats: int,
    kinds: Sequence[str],
    chunk_size: int,
    run_tag: str,
) -> list[Slot]:
    """Every candidate task, interleaving seats and variants within each repeat."""
    groups = {
        "review": _chunks([item.id for item in eval_set.review], chunk_size),
        "writing": _chunks([task.id for task in eval_set.writing], chunk_size),
    }
    slots = []
    for repeat in range(1, repeats + 1):
        for kind in kinds:
            for index, ids in enumerate(groups[kind]):
                for label in ordered_labels(labels):
                    for seat in seats:
                        task_id = f"{TASK_PREFIX}-{run_tag}-{seat.code}-{label}-r{repeat}-{kind}-{index:02d}"
                        slots.append(Slot(task_id, seat, label, repeat, kind, tuple(ids)))
    return slots


def plan_candidate_tasks(
    eval_set: EvalSet,
    variants: Sequence[Variant],
    seats: Sequence[Seat],
    repeats: int,
    kinds: Sequence[str],
    chunk_size: int,
    run_tag: str,
) -> list[TaskSpec]:
    preambles = {variant.label: variant.preamble for variant in variants}
    reviews, writings = eval_set.review_by_id(), eval_set.writing_by_id()
    tasks = []
    for slot in candidate_slots(eval_set, seats, list(preambles), repeats, kinds, chunk_size, run_tag):
        if slot.kind == "review":
            payload = review_payload([reviews[item_id] for item_id in slot.item_ids])
        else:
            payload = writing_payload([writings[item_id] for item_id in slot.item_ids])
        prompt = build_prompt(slot.kind, payload, preambles[slot.variant])
        tasks.append(TaskSpec(slot.task_id, slot.seat, slot.kind, slot.variant, slot.repeat, slot.item_ids, prompt))
    return tasks


# --------------------------------------------------------------------------- manifest


def frozen_terms(eval_set: EvalSet, variants: Sequence[Variant], chunk_size: int, run_tag: str) -> dict[str, Any]:
    return {
        "harness": HARNESS_VERSION,
        "set_id": eval_set.set_id,
        "set_sha256": eval_set.sha256,
        "variants": {variant.label: variant.sha256 for variant in variants},
        "templates_sha256": template_fingerprint(),
        "chunk_size": chunk_size,
        "run_tag": run_tag,
    }


def ensure_manifest(results: Path, frozen: dict[str, Any], set_path: Path) -> dict[str, Any]:
    """Create the manifest, or refuse when a resumed run changes any frozen term."""
    path = results / "manifest.json"
    if path.exists():
        manifest = read_json(path)
        changed = sorted(
            key for key in frozen.keys() | manifest["frozen"].keys() if frozen.get(key) != manifest["frozen"].get(key)
        )
        if changed:
            raise HarnessError(f"results directory was frozen with different terms: {', '.join(changed)}")
        return manifest
    manifest = {"frozen": frozen, "set_path": str(set_path), "created_at": datetime.now(UTC).isoformat()}
    write_private_json(path, manifest)
    return manifest


def load_manifest(results: Path) -> dict[str, Any]:
    path = results / "manifest.json"
    if not path.is_file():
        raise HarnessError(f"{path} not found; run 'run' first")
    return read_json(path)


# --------------------------------------------------------------------------- execution


def raw_path(results: Path, task_id: str) -> Path:
    return results / "raw" / f"{task_id}.json"


def _pending_path(results: Path, task_id: str) -> Path:
    return results / "raw" / f"{task_id}.pending.json"


def load_raw(results: Path, task_id: str) -> dict[str, Any] | None:
    path = raw_path(results, task_id)
    return read_json(path) if path.is_file() else None


@dataclass
class RunSummary:
    accepted: int = 0
    skipped_accepted: int = 0
    failed: list[str] = field(default_factory=list)
    not_run: list[str] = field(default_factory=list)
    preflighted: int = 0

    @property
    def complete(self) -> bool:
        return not self.failed and not self.not_run


class Executor:
    """Dispatch, wait and record tasks; already-accepted tasks are never re-run."""

    def __init__(
        self,
        dispatcher: Dispatcher,
        results: Path,
        *,
        max_parallel: int = 3,
        spawn_interval: float = 10.0,
        retry_failed: bool = False,
        log: Callable[[str], None] | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.dispatcher = dispatcher
        self.results = results
        self.max_parallel = max(1, max_parallel)
        self.spawn_interval = spawn_interval
        self.retry_failed = retry_failed
        self.log = log or (lambda message: print(message, file=sys.stderr, flush=True))
        self.sleep = sleep
        self._spawn_lock = threading.Lock()
        self._last_spawn: float | None = None
        self._summary_lock = threading.Lock()

    def _stagger(self) -> None:
        with self._spawn_lock:
            now = time.monotonic()
            if self._last_spawn is not None:
                wait = self.spawn_interval - (now - self._last_spawn)
                if wait > 0:
                    self.sleep(wait)
            self._last_spawn = time.monotonic()

    def _record(self, task: TaskSpec, outcome: TaskOutcome) -> dict[str, Any]:
        problem = outcome.identity_problem(task.seat, task.prompt_sha256)
        raw = {
            "task_id": task.task_id,
            "kind": task.kind,
            "seat": task.seat.seat_id,
            "variant": task.variant,
            "repeat": task.repeat,
            "item_ids": list(task.item_ids),
            "meta": task.meta,
            "prompt_sha256": task.prompt_sha256,
            "status": outcome.status,
            "agent": outcome.agent,
            "model": outcome.model,
            "substitution": outcome.substitution,
            "identity_problem": problem,
            "accepted": outcome.status == "done" and problem is None,
            "response_text": outcome.response_text,
            "result_sha256": outcome.result_sha256,
            "run_nonce": outcome.run_nonce,
            "detail": outcome.detail,
            "collected_at": datetime.now(UTC).isoformat(),
        }
        write_private_json(raw_path(self.results, task.task_id), raw)
        _pending_path(self.results, task.task_id).unlink(missing_ok=True)
        return raw

    def _execute(self, task: TaskSpec, summary: RunSummary) -> None:
        existing = load_raw(self.results, task.task_id)
        if existing is not None and existing.get("prompt_sha256") != task.prompt_sha256:
            raise HarnessError(f"{task.task_id}: stored prompt hash differs from the re-planned prompt")
        if existing is not None and (existing.get("accepted") or not self.retry_failed):
            with self._summary_lock:
                if existing.get("accepted"):
                    summary.skipped_accepted += 1
                else:
                    summary.failed.append(task.task_id)
            return
        pending = _pending_path(self.results, task.task_id)
        nonce: str | None = None
        try:
            if pending.is_file() and existing is None:
                stored = read_json(pending)
                if stored.get("prompt_sha256") != task.prompt_sha256:
                    raise HarnessError(f"{task.task_id}: pending prompt hash differs from the re-planned prompt")
                nonce = stored.get("run_nonce")
                self.log(f"resume-wait {task.task_id}")
            elif existing is None and self.dispatcher.known(task.task_id):
                self.log(f"resume-wait {task.task_id} (record exists, no pending marker)")
            else:
                prompt_path = self.results / "prompts" / f"{task.task_id}.md"
                write_private_text(prompt_path, task.prompt)
                self._stagger()
                nonce = self.dispatcher.dispatch(
                    task.task_id, task.seat, task.kind, prompt_path, force_new=existing is not None
                )
                write_private_json(pending, {"run_nonce": nonce, "prompt_sha256": task.prompt_sha256})
                self.log(f"dispatched {task.task_id}")
            outcome = self.dispatcher.wait(task.task_id, nonce)
        except DispatchError as exc:
            self.log(f"not-run {task.task_id}: {exc}")
            with self._summary_lock:
                summary.not_run.append(task.task_id)
            return
        raw = self._record(task, outcome)
        with self._summary_lock:
            if raw["accepted"]:
                summary.accepted += 1
            else:
                summary.failed.append(task.task_id)
        self.log(f"collected {task.task_id}: {outcome.status}{'' if raw['accepted'] else ' (not accepted)'}")

    def run(self, tasks: Sequence[TaskSpec]) -> RunSummary:
        summary = RunSummary()
        with ThreadPoolExecutor(max_workers=self.max_parallel) as pool:
            for future in [pool.submit(self._execute, task, summary) for task in tasks]:
                future.result()
        return summary

    def preflight(self, tasks: Sequence[TaskSpec]) -> RunSummary:
        """Write prompts and validate each dispatch with the delegate's dry run; nothing is spawned.

        The dry run leaves a terminal ``dry_run`` record, so it uses a distinct ``-preflight``
        task id that never collides with the real task the next run resumes.
        """
        summary = RunSummary()
        for task in tasks:
            prompt_path = self.results / "prompts" / f"{task.task_id}.md"
            write_private_text(prompt_path, task.prompt)
            try:
                self.dispatcher.preflight(f"{task.task_id}-preflight", task.seat, task.kind, prompt_path)
                summary.preflighted += 1
            except DispatchError as exc:
                self.log(f"preflight-refused {task.task_id}: {exc}")
                summary.not_run.append(task.task_id)
        return summary


# --------------------------------------------------------------------------- judge planning


def valid_entries(raw: dict[str, Any] | None, kind: str) -> dict[str, dict[str, Any]]:
    """Validated item entries of an accepted raw record (empty when not accepted)."""
    if not raw or not raw.get("accepted"):
        return {}
    results = validate_response(kind, raw.get("response_text"), raw["item_ids"])
    return {result.item_id: result.entry for result in results if result.entry is not None}


def writing_texts(results: Path, slots: Sequence[Slot]) -> dict[tuple[str, str, int, str], str]:
    texts = {}
    for slot in slots:
        if slot.kind != "writing":
            continue
        for item_id, entry in valid_entries(load_raw(results, slot.task_id), "writing").items():
            texts[(slot.seat.seat_id, slot.variant, slot.repeat, item_id)] = entry["text"]
    return texts


def _swap(seed: int, *parts: object) -> bool:
    return int(sha256_text("|".join(str(part) for part in (seed, *parts)))[:8], 16) & 1 == 1


def plan_judge_tasks(
    eval_set: EvalSet,
    results: Path,
    slots: Sequence[Slot],
    seats: Sequence[Seat],
    labels: Sequence[str],
    repeats: int,
    chunk_size: int,
    seed: int,
    run_tag: str,
) -> list[TaskSpec]:
    """Blind pairwise judgements by the two other families, A/B order randomised per judge and comparison."""
    texts = writing_texts(results, slots)
    tasks = []
    for candidate, repeat, (va, vb) in itertools.product(
        seats, range(1, repeats + 1), itertools.combinations(ordered_labels(labels), 2)
    ):
        for judge in judge_seats(candidate.seat_id):
            payload, order = [], {}
            for task in eval_set.writing:
                text_a = texts.get((candidate.seat_id, va, repeat, task.id))
                text_b = texts.get((candidate.seat_id, vb, repeat, task.id))
                if text_a is None or text_b is None:
                    continue
                first, second = (
                    (vb, va) if _swap(seed, judge.seat_id, candidate.seat_id, repeat, va, vb, task.id) else (va, vb)
                )
                lookup = {va: text_a, vb: text_b}
                entry = writing_payload([task])[0]
                entry.update({"A": lookup[first], "B": lookup[second]})
                payload.append(entry)
                order[task.id] = {"A": first, "B": second}
            for index, chunk in enumerate(_chunks(payload, chunk_size)):
                prompt = build_prompt("judge", list(chunk))
                ids = tuple(entry["id"] for entry in chunk)
                task_id = (
                    f"{TASK_PREFIX}-{run_tag}-judge-{judge.code}-{candidate.code}-{va}-vs-{vb}"
                    f"-r{repeat}-{index:02d}-{sha256_text(prompt)[:8]}"
                )
                meta = {"candidate_seat": candidate.seat_id, "pair": [va, vb], "order": {i: order[i] for i in ids}}
                tasks.append(TaskSpec(task_id, judge, "judge", None, repeat, ids, prompt, meta))
    return tasks
