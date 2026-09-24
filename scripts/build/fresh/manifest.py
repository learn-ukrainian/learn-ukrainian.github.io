"""Content-addressed, review-eligible fresh lesson attempt manifests.

The manifest names every file a reviewer receives, each with its sha256: the
plan, the evidence pack and word store (verified against their locks before they
are recorded), the built lesson and its activity data, the gate report, the style
card, the decisions record, the module digest, the materialized planned learner
state and the built lessons 1..N-1 (``upstream_lessons``).

The learner state has two forms. ``learner_state.sha256`` is its identity: the
canonical-JSON hash of ``planned_state(...).to_dict()``, independent of YAML
formatting. ``inputs.learner_state`` is the readable form the reviewer opens: a
deterministic YAML document written next to the manifest holding that same
``to_dict()`` under ``learner_state`` and the lesson's immersion rule (the
``lesson_immersion_payload`` result the writer received) under ``immersion``.
Both derive from one ``planned_state`` result.

A re-review (Contract 2) also names the previous attempt: its review file and its
receipt ledger (both hashed and refused when they no longer match) and the unified
diff between the lesson that attempt was shown and the current one. The previous
lesson's bytes come from the content-addressed snapshot every manifest write keeps
next to its history (``manifests/lesson-<n>/lesson.<sha256>.mdx``), so a rebuild
in place never loses them. ``previous_attempt`` and ``diff`` are both ``null`` on a
first review.
"""

from __future__ import annotations

import difflib
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from scripts.build.fresh.immersion import lesson_immersion_payload
from scripts.build.fresh.path_guard import checked_existing_path, checked_path
from scripts.curriculum.evidence import lock
from scripts.curriculum.learner_state.planned import planned_state
from scripts.review.digest.generator import GENERATOR_VERSION, build_digest, write_digest

ATTEMPT_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
SHA_RE = re.compile(r"[0-9a-f]{64}\Z")
EVIDENCE_ROOT = "curriculum/l2-uk-en/evidence"
SCHEMA = Path(__file__).resolve().parents[3] / "schemas" / "lesson-review-manifest-v1.schema.json"


class ManifestInputError(ValueError):
    def __init__(self, path: Path, reason: str, root: Path):
        resolved = path.resolve()
        try:
            self.path = resolved.relative_to(root.resolve()).as_posix()
        except ValueError:
            self.path = resolved.as_posix()
        super().__init__(f"{reason}: {self.path}")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def learner_state_sha256(state: Any) -> str:
    """Canonical JSON identity, independent of YAML formatting and key order."""
    data = json.dumps(state.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def current_paths(state_dir: Path, n: int) -> tuple[Path, Path, Path]:
    base = state_dir / f"lesson-{n}.manifest.yaml"
    return base, state_dir / f"lesson-{n}.manifest.sha256", state_dir / f"lesson-{n}.manifest-error.yaml"


def unlink_current(state_dir: Path, n: int) -> None:
    for path in current_paths(state_dir, n):
        path.unlink(missing_ok=True)


def _input(path: Path, repo_root: Path) -> dict[str, str]:
    relative = path.relative_to(repo_root.resolve())
    allowed = Path(*relative.parts[:3]) if relative.parts[:2] == ("curriculum", "l2-uk-en") else relative.parts[0]
    path = checked_existing_path(repo_root, path, allowed)
    if not path.is_file():
        raise FileNotFoundError(str(path))
    relative = path.resolve().relative_to(repo_root.resolve()).as_posix()
    return {"path": relative, "sha256": sha256(path)}


def _locked_input(path: Path, repo_root: Path) -> dict[str, str]:
    """A file input whose bytes must agree with its lock sidecar; fails naming the path."""
    entry = _input(path, repo_root)
    if not lock.check(path):
        raise ManifestInputError(path, "lock mismatch", repo_root)
    return entry


def learner_state_document(state: Any, immersion: Any | None = None) -> dict[str, Any]:
    """The readable learner-state document; the identity hash covers only ``learner_state``."""
    document: dict[str, Any] = {"learner_state": state.to_dict()}
    if immersion is not None:
        document["immersion"] = immersion.to_dict()
    return document


def materialize_learner_state(path: Path, document: dict[str, Any], repo_root: Path) -> dict[str, str]:
    """Write the document as deterministic YAML with its lock sidecar; return the manifest input entry."""
    root = repo_root.resolve()
    target = checked_path(root, path.resolve().relative_to(root), "curriculum/l2-uk-en/evidence")
    lock.write(target, lock.yaml_bytes(document))
    return _input(target, root)


def lesson_snapshot_path(state_dir: Path, n: int, digest: str) -> Path:
    return state_dir / "manifests" / f"lesson-{n}" / f"lesson.{digest}.mdx"


def _keep_lesson_snapshot(root: Path, state_dir: Path, n: int, page: Path, entry: dict[str, str]) -> None:
    """Keep the exact bytes of the lesson this manifest records, addressed by their sha256."""
    data = page.read_bytes()
    if hashlib.sha256(data).hexdigest() != entry["sha256"]:
        raise ManifestInputError(page, "lesson changed while the manifest was written", root)
    target = checked_existing_path(root, lesson_snapshot_path(state_dir, n, entry["sha256"]), EVIDENCE_ROOT)
    if target.exists() and target.read_bytes() != data:
        raise ManifestInputError(target, "lesson snapshot collision", root)
    if not target.exists():
        lock.atomic_write(target, data)


def _pinned_file(root: Path, recorded: Any, expected: Path, what: str) -> tuple[Path, bytes]:
    """A previous-attempt file: at the path the layout dictates, bytes equal to the recorded sha256."""
    if not isinstance(recorded, dict) or set(recorded) != {"path", "sha256"}:
        raise ManifestInputError(expected, f"previous {what} must be {{path, sha256}}", root)
    path = checked_existing_path(root, expected, _allowed(root, expected))
    if recorded["path"] != path.relative_to(root).as_posix():
        raise ManifestInputError(path, f"previous {what} is not at its expected path", root)
    if not path.is_file():
        raise ManifestInputError(path, f"previous {what} missing", root)
    data = path.read_bytes()
    if not isinstance(recorded["sha256"], str) or hashlib.sha256(data).hexdigest() != recorded["sha256"]:
        raise ManifestInputError(path, f"previous {what} changed since it was recorded", root)
    return path, data


def _allowed(root: Path, path: Path) -> str:
    parts = path.relative_to(root).parts
    return EVIDENCE_ROOT if parts[:2] == ("curriculum", "l2-uk-en") else parts[0] + "/review-receipts"


def _previous_attempt_inputs(
    previous: dict[str, Any], *, level: str, slug: str, n: int, state_dir: Path, root: Path, page: Path
) -> tuple[dict[str, Any], bytes]:
    """The manifest's ``previous_attempt`` object and the unified diff bytes for a re-review.

    Every input is verified before it is recorded: the review and ledger files
    against their recorded hashes and expected paths, the review's attempt block
    against the attempt id, the previous manifest against its content address, and
    the previous lesson snapshot against the hash that manifest recorded.
    """
    attempt_id = previous.get("attempt_id") if isinstance(previous, dict) else None
    if not isinstance(attempt_id, str) or not ATTEMPT_TOKEN.fullmatch(attempt_id):
        raise ManifestInputError(state_dir, "previous attempt id invalid", root)
    if set(previous) != {"attempt_id", "review", "ledger"}:
        raise ManifestInputError(state_dir, "previous attempt must be {attempt_id, review, ledger}", root)
    review_path, review_bytes = _pinned_file(
        root, previous["review"], state_dir / f"lesson-{n}.review.{attempt_id}.yaml", "review"
    )
    try:
        review = yaml.safe_load(review_bytes)
        attempt = review["attempt"]
        review_id, manifest_sha = attempt["review_id"], attempt["manifest_sha256"]
    except (yaml.YAMLError, KeyError, TypeError) as err:
        raise ManifestInputError(review_path, "previous review carries no attempt block", root) from err
    if (
        review.get("kind") != "lesson"
        or attempt.get("attempt_id") != attempt_id
        or not isinstance(review_id, str)
        or not ATTEMPT_TOKEN.fullmatch(review_id)
        or not isinstance(manifest_sha, str)
        or not SHA_RE.fullmatch(manifest_sha)
    ):
        raise ManifestInputError(review_path, "previous review is not a lesson review of that attempt", root)
    ledger_path, _ = _pinned_file(
        root, previous["ledger"], root / "batch_state" / "review-receipts" / review_id / f"{attempt_id}.jsonl", "ledger"
    )
    history = checked_existing_path(
        root, state_dir / "manifests" / f"lesson-{n}" / f"{manifest_sha}.yaml", EVIDENCE_ROOT
    )
    if not history.is_file() or sha256(history) != manifest_sha:
        raise ManifestInputError(history, "previous attempt manifest missing or not at its content address", root)
    earlier = yaml.safe_load(history.read_bytes())
    if (earlier.get("level"), earlier.get("slug"), earlier.get("lesson")) != (level, slug, n):
        raise ManifestInputError(history, "previous attempt manifest is for another lesson", root)
    old = earlier["inputs"]["lesson"]
    snapshot = checked_existing_path(root, lesson_snapshot_path(state_dir, n, old["sha256"]), EVIDENCE_ROOT)
    if not snapshot.is_file() or sha256(snapshot) != old["sha256"]:
        raise ManifestInputError(snapshot, "previous lesson snapshot missing or altered", root)
    lines = difflib.unified_diff(
        snapshot.read_text(encoding="utf-8").splitlines(keepends=True),
        page.read_text(encoding="utf-8").splitlines(keepends=True),
        fromfile=f"a/{old['path']}@{old['sha256'][:12]}",
        tofile=f"b/{page.resolve().relative_to(root).as_posix()}",
    )
    entry = {
        "attempt_id": attempt_id,
        "review": {"path": review_path.relative_to(root).as_posix(), "sha256": previous["review"]["sha256"]},
        "ledger": {"path": ledger_path.relative_to(root).as_posix(), "sha256": previous["ledger"]["sha256"]},
    }
    return entry, "".join(lines).encode("utf-8")


def _activity_imports(mdx_path: Path, repo_root: Path) -> list[Path]:
    text = mdx_path.read_text(encoding="utf-8")
    imports = re.findall(r"(?m)^\s*import\s+(?:[^\n]*?\s+from\s+)?[\"']([^\"']+)[\"']", text)
    paths: set[Path] = set()
    for value in imports:
        if value.startswith("./") or value.startswith("../"):
            target = mdx_path.parent / value
        elif value.startswith("@site/"):
            target = repo_root / "site" / value.removeprefix("@site/")
        elif value.startswith("/src/"):
            target = repo_root / "site" / value.lstrip("/")
        else:
            continue
        target = checked_existing_path(repo_root, target, "site")
        if target.suffix.lower() in {".json", ".yaml", ".yml", ".csv"} or "data" in target.parts:
            paths.add(target)
    return sorted(paths)


def write_manifest(
    level: str,
    slug: str,
    n: int,
    *,
    lesson_kind: str,
    state_dir: Path,
    repo_root: Path,
    plans_dir: Path,
    evidence_dir: Path,
    position: int,
    site_dir: Path | None = None,
    previous_attempt: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], str]:
    root = repo_root.resolve()
    page_dir = site_dir or root / "site/src/content/docs" / level / slug
    expected_paths = (
        (plans_dir, root / "curriculum/l2-uk-en/lesson-plans" / level),
        (evidence_dir, root / "curriculum/l2-uk-en/evidence" / level),
        (state_dir, root / "curriculum/l2-uk-en/evidence" / level / "_state" / slug),
        (page_dir, root / "site/src/content/docs" / level / slug),
    )
    for path, expected in expected_paths:
        if path.resolve() != expected.resolve():
            raise ManifestInputError(path, "digest_path_mismatch", root)
    digest_doc = build_digest(level, slug, n, repo_root=root)
    digest_path, _ = write_digest(digest_doc, repo_root=root)
    page = page_dir / f"{n}.mdx"
    plan_path = plans_dir / f"{slug}.yaml"
    pack_path = evidence_dir / f"{slug}.yaml"
    words_path = evidence_dir / "_words.yaml"
    lock_path = state_dir / "lessons.lock.yaml"
    gate_path = state_dir / f"lesson-{n}.gates.yaml"
    from scripts.build.fresh.prompt import BAND_CARD_MAP

    card_name = BAND_CARD_MAP.get(level.lower().split("-")[0], "b1plus")
    card_path = checked_existing_path(root, root / "docs/style-cards" / f"{card_name}.md", "docs/style-cards")
    sidecar_path = checked_existing_path(root, root / "docs/style-cards" / f"{card_name}.sha256", "docs/style-cards")
    if not sidecar_path.is_file():
        raise ManifestInputError(sidecar_path, "style card sidecar missing", root)
    expected = sidecar_path.read_text(encoding="utf-8").strip().split()
    if not card_path.is_file() or not expected or expected[0] != sha256(card_path):
        raise ManifestInputError(sidecar_path, "style card sidecar mismatch", root)
    lock_path = checked_existing_path(root, lock_path, "curriculum/l2-uk-en/evidence")
    lock_doc = yaml.safe_load(lock_path.read_text(encoding="utf-8"))
    entry = next((item for item in lock_doc["lessons"] if item["n"] == n), None)
    if not entry or not entry.get("entry_sha256"):
        raise ValueError(f"missing lesson lock entry {n}: {lock_path}")
    upstream = [{"n": k, **_input(page.parent / f"{k}.mdx", root)} for k in range(1, n)]
    state = planned_state(level, position, n, allow_missing_prior=True, plans_dir=plans_dir, evidence_dir=evidence_dir)
    state_path = state_dir / f"lesson-{n}.learner-state.yaml"
    try:
        immersion = lesson_immersion_payload(level, position, n, state)
    except Exception as err:
        raise ManifestInputError(state_path, f"immersion rule unavailable ({err})", root) from err
    state_input = materialize_learner_state(state_path, learner_state_document(state, immersion), root)
    lesson_input = _input(page, root)
    previous_doc: dict[str, Any] | None = None
    diff_input: dict[str, str] | None = None
    if previous_attempt is not None:
        previous_doc, diff_bytes = _previous_attempt_inputs(
            previous_attempt, level=level, slug=slug, n=n, state_dir=state_dir, root=root, page=page
        )
        diff_path = checked_existing_path(
            root, state_dir / f"lesson-{n}.diff.{previous_doc['attempt_id']}.patch", EVIDENCE_ROOT
        )
        lock.atomic_write(diff_path, diff_bytes)
        diff_input = _input(diff_path, root)
    _keep_lesson_snapshot(root, state_dir, n, page, lesson_input)
    doc = {
        "manifest_schema": 1,
        "kind": "lesson",
        "level": level,
        "slug": slug,
        "lesson": n,
        "lesson_kind": lesson_kind,
        "recap": lesson_kind == "recap",
        "review_eligible": True,
        "blocked_by": [],
        "inputs": {
            "plan": _input(plan_path, root),
            "pack": _locked_input(pack_path, root),
            "pack_lock": _input(Path(f"{pack_path}.lock"), root),
            "words": _locked_input(words_path, root),
            "words_lock": _input(Path(f"{words_path}.lock"), root),
            "learner_state": state_input,
            "lessons_lock": _input(lock_path, root),
            "lesson": lesson_input,
            "activity_data": [_input(path, root) for path in _activity_imports(page, root)],
            "gate_report": _input(gate_path, root),
            "style_card": _input(card_path, root),
            "decisions": _input(plans_dir / "_decisions.yaml", root),
        },
        "lesson_lock_entry": {
            "path": lock_path.resolve().relative_to(root).as_posix(),
            "lesson": n,
            "entry_sha256": entry["entry_sha256"],
        },
        "learner_state": {"sha256": learner_state_sha256(state), "source": "planned_state"},
        "module_digest": _input(digest_path, root),
        "digest_generator_version": GENERATOR_VERSION,
        "upstream_lessons": upstream,
        "previous_attempt": previous_doc,
        "diff": diff_input,
    }
    Draft202012Validator(
        json.loads(checked_existing_path(SCHEMA.parents[1], SCHEMA, "schemas").read_text(encoding="utf-8"))
    ).validate(doc)
    content = lock.yaml_bytes(doc)
    digest = hashlib.sha256(content).hexdigest()
    history = checked_existing_path(
        root, state_dir / "manifests" / f"lesson-{n}" / f"{digest}.yaml", "curriculum/l2-uk-en/evidence"
    )
    if history.exists():
        if history.read_bytes() != content:
            raise ValueError(f"content-addressed manifest collision: {history}")
    else:
        lock.atomic_write(history, content)
    current, sidecar, error = current_paths(state_dir, n)
    current = checked_existing_path(root, current, "curriculum/l2-uk-en/evidence")
    sidecar = checked_existing_path(root, sidecar, "curriculum/l2-uk-en/evidence")
    error = checked_existing_path(root, error, "curriculum/l2-uk-en/evidence")
    lock.atomic_write(current, content)
    lock.atomic_write(sidecar, f"{digest}\n".encode("ascii"))
    error.unlink(missing_ok=True)
    return doc, digest


def write_manifest_error(state_dir: Path, n: int, reason: str, path: str, at: str) -> dict[str, Any]:
    current, sidecar, error = current_paths(state_dir, n)
    current.unlink(missing_ok=True)
    sidecar.unlink(missing_ok=True)
    doc = {"check": 12, "reason": reason, "path": path, "layer": "engine", "at": at}
    lock.atomic_write(error, lock.yaml_bytes(doc))
    return doc
