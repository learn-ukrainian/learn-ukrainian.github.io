"""Plan candidate and judge tasks, execute them with safe resume, and check paired conditions.

Results directory layout (private, outside every Git work tree, given on the command line)::

    manifest.json              the frozen plan (set, variants, templates, rules core, seats,
                               repeats, kinds, item ids, chunking, run tag, worker cwd, delegate's
                               composition frame, dispatch argument hashes, protocol shortfalls)
                               and, from the first ``score --judge``, the frozen judge terms
    prompts/<task_id>.md       exact prompt the worker received (rules core included)
    raw/<task_id>.json         attributed outcome, executed conditions and raw response
    raw/<task_id>.pending.json dispatched, outcome not collected yet (holds the dispatch-time
                               workspace and the expected composition)

A task is accepted only when its record attests the planned seat, the rendered
prompt, delegate's expected composition of it (effective prompt hash, prompt
blocks, cwd, worktree; see ``dispatch.py``) and the other frozen conditions, and
the worker checkout was the same at dispatch and at collection.
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

from scripts.lib import rules_core

from .common import (
    BASELINE_VARIANT,
    CANDIDATE_ORDER,
    HARNESS_VERSION,
    PROTOCOL_KINDS,
    PROTOCOL_REPEATS,
    SCORING_VERSION,
    SEATS,
    HarnessError,
    ResultsDir,
    Seat,
    judge_seats,
    read_json,
    sha256_text,
    word_count,
    write_private_json,
    write_private_text,
)
from .dataset import EvalSet, Variant, protocol_shortfalls
from .dispatch import PAIRED_FIELDS, Dispatcher, DispatchError, TaskOutcome, condition_problems, frame
from .prompts import build_prompt, review_payload, template_fingerprint, validate_response, writing_payload

KINDS = PROTOCOL_KINDS
TASK_PREFIX = "uk9623"
DEFAULT_LENGTH_RATIO = 0.8


def rules_block() -> str:
    """The rules core block delegate prepends for ``--rules-seat core``; the harness renders it into the prompt."""
    return rules_core.core_block("core")


def render(task_prompt: str, block: str) -> str:
    return f"{block}\n\n{task_prompt}"


@dataclass(frozen=True)
class Slot:
    """One candidate task's identity, without its prompt (scoring re-plans slots)."""

    task_id: str
    seat: Seat
    variant: str
    repeat: int
    kind: str
    chunk: int
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


# --------------------------------------------------------------------------- the frozen plan


def plan_shortfalls(eval_set: EvalSet, repeats: int, kinds: Sequence[str]) -> list[str]:
    """Why a plan cannot decide adoption (empty when it follows Protocol v2)."""
    problems = protocol_shortfalls(eval_set)
    if repeats < PROTOCOL_REPEATS:
        problems.append(f"{repeats} repeats < {PROTOCOL_REPEATS}")
    missing = [kind for kind in PROTOCOL_KINDS if kind not in kinds]
    if missing:
        problems.append(f"task kinds missing: {', '.join(missing)}")
    return problems


def frozen_plan(
    eval_set: EvalSet,
    variants: Sequence[Variant],
    seats: Sequence[Seat],
    repeats: int,
    kinds: Sequence[str],
    chunk_size: int,
    run_tag: str,
    worker_cwd: Path,
    block: str,
) -> dict[str, Any]:
    """Every term that defines the run and its denominator; frozen in the manifest, read by score and report.

    ``composition`` (delegate's frame around the prompts, see ``composition_frame``) and
    ``dispatch_args_sha256`` (see ``dispatch_args_frame``) are added once the candidate prompts are planned.
    """
    return {
        "harness": HARNESS_VERSION,
        "scoring": SCORING_VERSION,
        "set_id": eval_set.set_id,
        "set_sha256": eval_set.sha256,
        "variants": {variant.label: variant.sha256 for variant in variants},
        "templates_sha256": template_fingerprint(),
        "rules_core_sha256": sha256_text(block),
        "chunk_size": chunk_size,
        "run_tag": run_tag,
        "seats": [seat.seat_id for seat in seats],
        "repeats": repeats,
        "kinds": [kind for kind in KINDS if kind in kinds],
        "item_ids": {
            "review": [item.id for item in eval_set.review],
            "writing": [task.id for task in eval_set.writing],
        },
        "worker_cwd": str(worker_cwd),
        "protocol_shortfalls": plan_shortfalls(eval_set, repeats, kinds),
    }


def ensure_manifest(results: ResultsDir, frozen: dict[str, Any], set_path: Path) -> dict[str, Any]:
    """Create the manifest, or refuse when a resumed run changes any frozen term."""
    path = results.path("manifest.json")
    if path.exists():
        manifest = read_json(path)
        _require_scoring_version(path, manifest)
        changed = sorted(
            key for key in frozen.keys() | manifest["frozen"].keys() if frozen.get(key) != manifest["frozen"].get(key)
        )
        if changed:
            if "dispatch_args_sha256" in changed:
                raise HarnessError(
                    "results directory was frozen under different dispatch arguments "
                    f"({', '.join(changed)}). A new --run-tag is the path; argument sets are never mixed."
                )
            raise HarnessError(f"results directory was frozen with different terms: {', '.join(changed)}")
        return manifest
    manifest = {"frozen": frozen, "set_path": str(set_path), "created_at": datetime.now(UTC).isoformat()}
    write_private_json(path, manifest)
    return manifest


def _require_scoring_version(path: Path, manifest: dict[str, Any]) -> None:
    """Refuse a manifest frozen under another review-scoring contract; results never cross versions."""
    found = manifest.get("frozen", {}).get("scoring") or "uk-preamble-scoring/1 (unversioned)"
    if found != SCORING_VERSION:
        raise HarnessError(
            f"{path} was frozen under review-scoring version {found}, not {SCORING_VERSION}; results are never "
            "compared across scoring versions: start a new results directory"
        )


def load_manifest(results: ResultsDir) -> dict[str, Any]:
    path = results.path("manifest.json")
    if not path.is_file():
        raise HarnessError(f"{path} not found; run 'run' first")
    manifest = read_json(path)
    if manifest.get("frozen", {}).get("harness") != HARNESS_VERSION:
        raise HarnessError(f"{path} was written by another harness version; start a new results directory")
    _require_scoring_version(path, manifest)
    return manifest


def composition_frame(dispatcher: Dispatcher, tasks: Sequence[TaskSpec]) -> dict[str, Any]:
    """The frame delegate puts around every candidate prompt; refused unless it is the same for all of them.

    Delegate's worktree block depends on paths the prompt names (its sparse-checkout
    note), so a preamble or item naming such a path would frame its arm differently
    and the arms would differ in more than the preamble.
    """
    seen: dict[str, dict[str, Any]] = {}
    first: tuple[str, dict[str, Any]] | None = None
    for task in tasks:
        if task.prompt_sha256 not in seen:
            try:
                seen[task.prompt_sha256] = frame(dispatcher.compose(task.prompt))
            except DispatchError as exc:
                raise HarnessError(f"{task.task_id}: {exc}") from exc
        current = seen[task.prompt_sha256]
        if first is None:
            first = (task.task_id, current)
        elif current != first[1]:
            fields = ", ".join(sorted(key for key in current if current[key] != first[1][key]))
            raise HarnessError(
                f"delegate would frame {task.task_id} differently from {first[0]} ({fields}); "
                "the arms would differ in more than the preamble"
            )
    if first is None:
        raise HarnessError("the plan has no candidate tasks")
    return first[1]


def dispatch_args_frame(dispatcher: Dispatcher, tasks: Sequence[TaskSpec], results: ResultsDir) -> dict[str, str]:
    """Argument hash of the first task of each kind and seat.

    Frozen on the manifest as ``dispatch_args_sha256``. The hash is delegate's hash of the
    arguments this harness builds, including ``--research-task-family``, so a manifest frozen
    under other arguments (or before tasks were classified) cannot be resumed. Task ids and
    prompt paths are stable for one plan, and the same kind classifies every seat.
    """
    found: dict[str, str] = {}
    for task in tasks:
        key = f"{task.kind}/{task.seat.seat_id}"
        if key in found:
            continue
        found[key] = dispatcher.expected_args_sha256(
            task.task_id, task.seat, task.kind, prompt_path(results, task.task_id)
        )
    return found


def candidate_slots(plan: dict[str, Any]) -> list[Slot]:
    """Every candidate task of the frozen plan, interleaving seats and variants within each repeat."""
    groups = {kind: _chunks(plan["item_ids"][kind], plan["chunk_size"]) for kind in KINDS}
    seats = [SEATS[seat_id] for seat_id in plan["seats"]]
    slots = []
    for repeat in range(1, plan["repeats"] + 1):
        for kind in plan["kinds"]:
            for index, ids in enumerate(groups[kind]):
                for label in ordered_labels(plan["variants"]):
                    for seat in seats:
                        task_id = f"{TASK_PREFIX}-{plan['run_tag']}-{seat.code}-{label}-r{repeat}-{kind}-{index:02d}"
                        slots.append(Slot(task_id, seat, label, repeat, kind, index, tuple(ids)))
    return slots


def plan_candidate_tasks(
    eval_set: EvalSet, variants: Sequence[Variant], plan: dict[str, Any], block: str
) -> list[TaskSpec]:
    preambles = {variant.label: variant.preamble for variant in variants}
    reviews, writings = eval_set.review_by_id(), eval_set.writing_by_id()
    tasks = []
    for slot in candidate_slots(plan):
        if slot.kind == "review":
            payload = review_payload([reviews[item_id] for item_id in slot.item_ids])
        else:
            payload = writing_payload([writings[item_id] for item_id in slot.item_ids])
        prompt = render(build_prompt(slot.kind, payload, preambles[slot.variant]), block)
        tasks.append(TaskSpec(slot.task_id, slot.seat, slot.kind, slot.variant, slot.repeat, slot.item_ids, prompt))
    return tasks


# --------------------------------------------------------------------------- execution


def raw_path(results: ResultsDir, task_id: str) -> Path:
    return results.path("raw", f"{task_id}.json")


def prompt_path(results: ResultsDir, task_id: str) -> Path:
    return results.path("prompts", f"{task_id}.md")


def _pending_path(results: ResultsDir, task_id: str) -> Path:
    return results.path("raw", f"{task_id}.pending.json")


def load_raw(results: ResultsDir, task_id: str) -> dict[str, Any] | None:
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
        results: ResultsDir,
        *,
        worker_cwd: Path,
        workspace: Callable[[], dict[str, Any]],
        frame: dict[str, Any] | None = None,
        max_parallel: int = 3,
        spawn_interval: float = 10.0,
        retry_failed: bool = False,
        log: Callable[[str], None] | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.dispatcher = dispatcher
        self.results = results
        self.worker_cwd = worker_cwd
        self.workspace = workspace
        self.frame = frame
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

    def _expected(self, task: TaskSpec) -> dict[str, Any]:
        """Delegate's composition of the task's prompt; refused when it departs from the frozen frame."""
        expected = self.dispatcher.compose(task.prompt)
        if self.frame is not None and frame(expected) != self.frame:
            fields = ", ".join(sorted(key for key in self.frame if self.frame[key] != expected.get(key)))
            raise DispatchError(f"delegate would frame the prompt differently from the frozen plan ({fields})")
        return expected

    def _record(
        self,
        task: TaskSpec,
        outcome: TaskOutcome,
        workspace: dict[str, Any] | None,
        expected: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        workspace_after = self.workspace()
        problems = []
        if expected is None:  # no pending marker: recompute (the task is refused below anyway)
            try:
                expected = self._expected(task)
            except DispatchError as exc:
                problems.append(str(exc))
        if expected is not None:
            problems += condition_problems(
                outcome.conditions,
                expected=expected,
                args_sha256=self.dispatcher.expected_args_sha256(
                    task.task_id, task.seat, task.kind, prompt_path(self.results, task.task_id)
                ),
            )
        if workspace is None:
            problems.append("worker checkout at dispatch is unknown (no pending marker)")
        elif workspace != workspace_after:
            problems.append("worker checkout changed while the task ran")
        identity = outcome.identity_problem(task.seat, task.prompt_sha256)
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
            "conditions": outcome.conditions,
            "composition": expected,
            "workspace": workspace,
            "workspace_after": workspace_after,
            "identity_problem": identity,
            "condition_problem": "; ".join(problems) or None,
            "accepted": outcome.status == "done" and identity is None and not problems,
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
        workspace: dict[str, Any] | None = None
        expected: dict[str, Any] | None = None
        try:
            if pending.is_file() and existing is None:
                stored = read_json(pending)
                if stored.get("prompt_sha256") != task.prompt_sha256:
                    raise HarnessError(f"{task.task_id}: pending prompt hash differs from the re-planned prompt")
                nonce, workspace, expected = stored.get("run_nonce"), stored.get("workspace"), stored.get("expected")
                self.log(f"resume-wait {task.task_id}")
            elif existing is None and self.dispatcher.known(task.task_id):
                self.log(f"resume-wait {task.task_id} (record exists, no pending marker)")
            else:
                expected = self._expected(task)
                path = prompt_path(self.results, task.task_id)
                write_private_text(path, task.prompt)
                self._stagger()
                workspace = self.workspace()
                nonce = self.dispatcher.dispatch(
                    task.task_id, task.seat, task.kind, path, force_new=existing is not None
                )
                write_private_json(
                    pending,
                    {
                        "run_nonce": nonce,
                        "prompt_sha256": task.prompt_sha256,
                        "workspace": workspace,
                        "expected": expected,
                    },
                )
                self.log(f"dispatched {task.task_id}")
            outcome = self.dispatcher.wait(task.task_id, nonce)
        except DispatchError as exc:
            self.log(f"not-run {task.task_id}: {exc}")
            with self._summary_lock:
                summary.not_run.append(task.task_id)
            return
        raw = self._record(task, outcome, workspace, expected)
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

        Each prompt's composition is computed and checked against the frozen frame first. The dry run
        uses a distinct ``-preflight`` task id so it never collides with the real task. That id itself
        is reused when a dry run is repeated; the dispatcher passes ``--force-new`` so delegate can
        archive its own terminal ``dry_run`` record. A real dispatch does not.
        """
        summary = RunSummary()
        for task in tasks:
            path = prompt_path(self.results, task.task_id)
            write_private_text(path, task.prompt)
            try:
                self._expected(task)
                self.dispatcher.preflight(f"{task.task_id}-preflight", task.seat, task.kind, path)
                summary.preflighted += 1
            except DispatchError as exc:
                self.log(f"preflight-refused {task.task_id}: {exc}")
                summary.not_run.append(task.task_id)
        return summary


# --------------------------------------------------------------------------- paired conditions


def _split_prompt(prompt: str) -> tuple[str, str] | None:
    """(rules core block, the rest) of a rendered prompt, or None when it does not start with a block."""
    close = prompt.find(rules_core.BLOCK_CLOSE)
    if not prompt.startswith(rules_core.BLOCK_OPEN) or close < 0:
        return None
    cut = close + len(rules_core.BLOCK_CLOSE)
    if prompt[cut : cut + 2] != "\n\n":
        return None
    return prompt[:cut], prompt[cut + 2 :]


def _stored_prompt(results: ResultsDir, raw: dict[str, Any]) -> str | None:
    path = prompt_path(results, raw["task_id"])
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    return text if sha256_text(text) == raw["prompt_sha256"] else None


def pair_problem(
    results: ResultsDir, plan: dict[str, Any], label: str, base: dict[str, Any], cand: dict[str, Any]
) -> str | None:
    """Why two accepted arms of one cell differ in anything but the preamble (None when they do not)."""
    differing = [f for f in PAIRED_FIELDS if base["conditions"].get(f) != cand["conditions"].get(f)]
    for key in ("agent", "model"):
        if base.get(key) != cand.get(key):
            differing.append(key)
    if base.get("workspace") != cand.get("workspace"):
        differing.append("worker checkout")
    if differing:
        return "arms ran under different conditions: " + ", ".join(differing)
    frames = [frame(raw.get("composition") or {}) for raw in (base, cand)]
    if frames[0] != frames[1] or frames[0] != plan.get("composition"):
        return "delegate framed the arms differently or not as frozen"
    base_prompt, cand_prompt = _stored_prompt(results, base), _stored_prompt(results, cand)
    if base_prompt is None or cand_prompt is None:
        return "stored prompt missing or not the attested prompt"
    base_parts, cand_parts = _split_prompt(base_prompt), _split_prompt(cand_prompt)
    if base_parts is None or cand_parts is None:
        return "prompt does not start with the rules core block"
    if base_parts[0] != cand_parts[0] or sha256_text(base_parts[0]) != plan["rules_core_sha256"]:
        return "rules core differs between arms or from the frozen plan"
    rest_base, rest_cand = base_parts[1], cand_parts[1]
    suffix = "\n\n" + rest_base
    if not rest_cand.endswith(suffix) or sha256_text(rest_cand[: -len(suffix)]) != plan["variants"][label]:
        return "prompts differ in more than the frozen preamble"
    return None


def pair_checks(results: ResultsDir, plan: dict[str, Any], slots: Sequence[Slot]) -> list[dict[str, Any]]:
    """Every variant-vs-baseline cell of the plan, with the reason it is not a valid pair (or None)."""
    baseline = {(s.seat.seat_id, s.repeat, s.kind, s.chunk): s for s in slots if s.variant == BASELINE_VARIANT}
    pairs = []
    for slot in slots:
        if slot.variant == BASELINE_VARIANT:
            continue
        base_slot = baseline[(slot.seat.seat_id, slot.repeat, slot.kind, slot.chunk)]
        base, cand = load_raw(results, base_slot.task_id), load_raw(results, slot.task_id)
        if base is None or cand is None or not base.get("accepted") or not cand.get("accepted"):
            problem = "an arm was not run or not accepted"
        else:
            problem = pair_problem(results, plan, slot.variant, base, cand)
        pairs.append(
            {
                "seat": slot.seat.seat_id,
                "variant": slot.variant,
                "repeat": slot.repeat,
                "kind": slot.kind,
                "chunk": slot.chunk,
                "baseline_task": base_slot.task_id,
                "variant_task": slot.task_id,
                "problem": problem,
            }
        )
    return pairs


# --------------------------------------------------------------------------- judge planning


def valid_entries(raw: dict[str, Any] | None, kind: str) -> dict[str, dict[str, Any]]:
    """Validated item entries of an accepted raw record (empty when not accepted)."""
    if not raw or not raw.get("accepted"):
        return {}
    results = validate_response(kind, raw.get("response_text"), raw["item_ids"])
    return {result.item_id: result.entry for result in results if result.entry is not None}


def writing_texts(results: ResultsDir, slots: Sequence[Slot]) -> dict[tuple[str, str, int, str], str]:
    texts = {}
    for slot in slots:
        if slot.kind != "writing":
            continue
        for item_id, entry in valid_entries(load_raw(results, slot.task_id), "writing").items():
            texts[(slot.seat.seat_id, slot.variant, slot.repeat, item_id)] = entry["text"]
    return texts


def _swap(seed: int, *parts: object) -> bool:
    return int(sha256_text("|".join(str(part) for part in (seed, *parts)))[:8], 16) & 1 == 1


def length_ratio(words_a: int, words_b: int) -> float:
    """Shorter over longer word count (1.0 for two empty texts)."""
    longer = max(words_a, words_b)
    return 1.0 if longer == 0 else min(words_a, words_b) / longer


def plan_judge_tasks(
    eval_set: EvalSet,
    results: ResultsDir,
    plan: dict[str, Any],
    terms: dict[str, Any],
    block: str,
) -> tuple[list[TaskSpec], list[dict[str, Any]]]:
    """Blind pairwise judgements by the two other families, A/B order randomised per judge and comparison.

    Length control (pre-registered "length controlled"): a pair is judged only when the
    shorter text has at least ``terms["length_ratio_min"]`` of the longer text's words;
    pairs outside the bound, and pairs missing a text, are not sent to judges and are
    returned as exclusions with their word counts.
    """
    slots = candidate_slots(plan)
    texts = writing_texts(results, slots)
    seats = [SEATS[seat_id] for seat_id in plan["seats"]]
    tasks, exclusions = [], []
    if "writing" not in plan["kinds"]:
        return tasks, exclusions
    labels = ordered_labels(plan["variants"])
    for candidate, repeat, (va, vb) in itertools.product(
        seats, range(1, plan["repeats"] + 1), itertools.combinations(labels, 2)
    ):
        judged = []
        for task in eval_set.writing:
            text_a = texts.get((candidate.seat_id, va, repeat, task.id))
            text_b = texts.get((candidate.seat_id, vb, repeat, task.id))
            where = {"candidate_seat": candidate.seat_id, "pair": [va, vb], "repeat": repeat, "item_id": task.id}
            if text_a is None or text_b is None:
                exclusions.append({**where, "reason": "missing text", "words": None})
                continue
            words = {va: word_count(text_a), vb: word_count(text_b)}
            ratio = length_ratio(words[va], words[vb])
            if ratio < terms["length_ratio_min"]:
                exclusions.append(
                    {**where, "reason": f"length ratio {ratio:.2f} < {terms['length_ratio_min']}", "words": words}
                )
                continue
            judged.append((task, {va: text_a, vb: text_b}, words))
        for judge in judge_seats(candidate.seat_id):
            payload, order, lengths = [], {}, {}
            for task, lookup, words in judged:
                swap = _swap(terms["seed"], judge.seat_id, candidate.seat_id, repeat, va, vb, task.id)
                first, second = (vb, va) if swap else (va, vb)
                entry = writing_payload([task])[0]
                entry.update({"A": lookup[first], "B": lookup[second]})
                payload.append(entry)
                order[task.id] = {"A": first, "B": second}
                lengths[task.id] = words
            for index, chunk in enumerate(_chunks(payload, terms["chunk_size"])):
                prompt = render(build_prompt("judge", list(chunk)), block)
                ids = tuple(entry["id"] for entry in chunk)
                task_id = (
                    f"{TASK_PREFIX}-{plan['run_tag']}-judge-{judge.code}-{candidate.code}-{va}-vs-{vb}"
                    f"-r{repeat}-{index:02d}-{sha256_text(prompt)[:8]}"
                )
                meta = {
                    "candidate_seat": candidate.seat_id,
                    "pair": [va, vb],
                    "order": {i: order[i] for i in ids},
                    "words": {i: lengths[i] for i in ids},
                }
                tasks.append(TaskSpec(task_id, judge, "judge", None, repeat, ids, prompt, meta))
    return tasks, exclusions
