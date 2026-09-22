"""Per-lesson evidence lock generator, checker, and diff engine (issue #8413, Brief C).

Each lesson's evidence lock covers exactly the records cited by that lesson's plan
entry plus shared module provenance. Two builds of the same
lesson from the same cited records yield identical lock entries, isolating touched
records from unaffected lessons.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

from scripts.curriculum.validate import codes as val_codes
from scripts.curriculum.validate.validate import _pack_ids_in_plan, _word_ids_in_plan

from . import codes, lock, pack, registry, words

REPO_ROOT = Path(__file__).resolve().parents[3]

# Source identities from built_with that can change lesson compilation/verification
# outputs without changing pack record bytes (morphology, stress, and rules engines).
SHARED_SOURCE_IDENTITY_KEYS = (
    "vesum",
    "trie",
    "ulif_forms",
    "overrides_sha256",
    "russian_patterns",
)


def read_git_file(
    ref: str,
    repo_rel_path: str,
    cwd: Path = REPO_ROOT,
    timeout: float = 10.0,
) -> bytes | None:
    """Read file content from git ref using git show without shell, explicit timeout."""
    try:
        proc = subprocess.run(
            ["git", "show", f"{ref}:{repo_rel_path}"],
            cwd=cwd,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        if proc.returncode == 0:
            return proc.stdout
    except Exception:
        pass
    return None


def check_git_ref(ref: str, cwd: Path = REPO_ROOT, timeout: float = 10.0) -> bool:
    """Verify that ref exists in git repository."""
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--verify", f"{ref}^{{commit}}"],
            cwd=cwd,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        return proc.returncode == 0
    except Exception:
        return False


def resolve_paths(
    level: str,
    slug: str,
    *,
    evidence_dir: Path | None = None,
    plans_dir: Path | None = None,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Path]:
    """Resolve plan, pack, word store, registry, and lock paths."""
    ev_root = evidence_dir if evidence_dir is not None else repo_root / f"curriculum/l2-uk-en/evidence/{level}"
    pl_dir = plans_dir if plans_dir is not None else repo_root / f"curriculum/l2-uk-en/lesson-plans/{level}"

    plan_path = pl_dir / f"{slug}.yaml"
    pack_path = ev_root / f"{slug}.yaml"
    words_path = ev_root / "_words.yaml"
    registry_path = ev_root / "_words.registry.yaml"
    lock_path = ev_root / f"_state/{slug}/lessons.lock.yaml"

    return {
        "plan": plan_path,
        "pack": pack_path,
        "words": words_path,
        "registry": registry_path,
        "lock": lock_path,
        "state_dir": ev_root / "_state",
    }


def compute_lesson_lock(
    level: str,
    slug: str,
    *,
    plan_dict: dict[str, Any] | None = None,
    pack_dict: dict[str, Any] | None = None,
    words_dict: dict[str, Any] | None = None,
    registry_records: list[dict[str, Any]] | None = None,
    evidence_dir: Path | None = None,
    plans_dir: Path | None = None,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    """Compute the deterministic lessons lock document for a module."""
    paths = resolve_paths(level, slug, evidence_dir=evidence_dir, plans_dir=plans_dir, repo_root=repo_root)

    # 1. Load plan
    if plan_dict is None:
        if not paths["plan"].is_file():
            raise FileNotFoundError(f"{val_codes.PLAN_NOT_FOUND}: plan file {paths['plan']} does not exist")
        plan_dict = yaml.safe_load(paths["plan"].read_text(encoding="utf-8"))

    # 2. Load pack
    if pack_dict is None:
        if not paths["pack"].is_file():
            raise FileNotFoundError(f"{val_codes.PACK_NOT_FOUND}: pack file {paths['pack']} does not exist")
        lock.require(paths["pack"])
        pack_dict = yaml.safe_load(paths["pack"].read_text(encoding="utf-8"))

    # 3. Load words
    if words_dict is None:
        if not paths["words"].is_file():
            raise FileNotFoundError(f"{val_codes.WORDS_NOT_FOUND}: word store {paths['words']} does not exist")
        lock.require(paths["words"])
        words_dict = yaml.safe_load(paths["words"].read_text(encoding="utf-8"))

    # 4. Load registry
    retired_ids: set[str] = set()
    if registry_records is None:
        if paths["registry"].is_file():
            lock.require(paths["registry"])
            registry_records = registry.load(paths["registry"])
        else:
            registry_records = []
    for r in registry_records:
        if r.get("retired") is True:
            retired_ids.add(r["id"])

    # 5. Extract cited ids per lesson
    all_pack_citations = _pack_ids_in_plan(plan_dict)
    all_word_citations = _word_ids_in_plan(plan_dict)

    lessons_in_plan = plan_dict.get("lessons", [])
    lesson_numbers = [l["n"] for l in lessons_in_plan]

    # Pre-index pack and word store
    pack_record_map: dict[str, dict[str, Any]] = {}
    for lst_name in pack.PACK_RECORD_LISTS:
        for rec in pack_dict.get(lst_name) or []:
            if isinstance(rec, dict) and "id" in rec:
                pack_record_map[rec["id"]] = rec

    word_record_map: dict[str, dict[str, Any]] = {}
    for rec in words_dict.get("words") or []:
        if isinstance(rec, dict) and "id" in rec:
            word_record_map[rec["id"]] = rec

    # 6. Shared calculation
    built_with = pack_dict.get("built_with") or {}
    shared_built_with = {k: built_with[k] for k in SHARED_SOURCE_IDENTITY_KEYS if k in built_with}

    built_with_sha256 = hashlib.sha256(lock.yaml_bytes(shared_built_with)).hexdigest()
    shared_sha256 = built_with_sha256

    shared_block = {
        "built_with_sha256": built_with_sha256,
        "sha256": shared_sha256,
    }

    # 7. Lessons calculation
    lessons_out: list[dict[str, Any]] = []

    for n in sorted(lesson_numbers):
        pack_ids_for_lesson = {item for (ln, _step, item) in all_pack_citations if ln == n}
        word_ids_for_lesson = {item for (ln, _step, item) in all_word_citations if ln == n}

        # Check word ids: not retired and present in word store
        for wid in sorted(word_ids_for_lesson):
            if wid in retired_ids:
                raise ValueError(f"{val_codes.UNKNOWN_WORD_ID}: word id {wid!r} is retired in {paths['registry'].name}")
            if wid not in word_record_map:
                raise ValueError(f"{val_codes.UNKNOWN_WORD_ID}: word id {wid!r} not found in {paths['words'].name}")

        # Check pack ids: present in pack
        for pid in sorted(pack_ids_for_lesson):
            if pid not in pack_record_map:
                raise ValueError(f"{val_codes.UNKNOWN_PACK_ID}: evidence id {pid!r} not found in {paths['pack'].name}")

        # Compute record hashes
        records: list[dict[str, str]] = []
        for wid in word_ids_for_lesson:
            r_hash = words.record_hash(word_record_map[wid], wid)
            records.append({"id": wid, "sha256": r_hash})

        for pid in pack_ids_for_lesson:
            r_hash = pack.record_hash(pack_record_map[pid], pid)
            records.append({"id": pid, "sha256": r_hash})

        records_sorted = sorted(records, key=lambda r: r["id"])

        entry_sha256 = hashlib.sha256(
            lock.yaml_bytes({"records": records_sorted, "shared_sha256": shared_sha256})
        ).hexdigest()

        lessons_out.append(
            {
                "entry_sha256": entry_sha256,
                "n": n,
                "records": records_sorted,
            }
        )

    return {
        "lock_schema": 1,
        "module": f"{level}/{slug}",
        "shared": shared_block,
        "lessons": lessons_out,
    }


def write_lesson_lock(
    level: str,
    slug: str,
    *,
    evidence_dir: Path | None = None,
    plans_dir: Path | None = None,
    repo_root: Path = REPO_ROOT,
) -> tuple[Path, str]:
    """Compute and write the lesson lock file and its sidecar."""
    doc = compute_lesson_lock(
        level,
        slug,
        evidence_dir=evidence_dir,
        plans_dir=plans_dir,
        repo_root=repo_root,
    )
    paths = resolve_paths(level, slug, evidence_dir=evidence_dir, plans_dir=plans_dir, repo_root=repo_root)
    lock_path = paths["lock"]
    content_bytes = lock.yaml_bytes(doc)
    digest = lock.write(lock_path, content_bytes)
    return lock_path, digest


def check_lesson_lock(
    level: str,
    slug: str,
    *,
    evidence_dir: Path | None = None,
    plans_dir: Path | None = None,
    repo_root: Path = REPO_ROOT,
) -> tuple[bool, str]:
    """Check that the on-disk lock exists, matches sidecar, and is byte-identical."""
    paths = resolve_paths(level, slug, evidence_dir=evidence_dir, plans_dir=plans_dir, repo_root=repo_root)
    lock_path = paths["lock"]

    if not lock_path.is_file():
        return False, f"error: {lock_path} does not exist; run with --write"

    if not lock.check(lock_path):
        return False, f"error: {codes.LOCK_MISMATCH}: {lock_path} disagrees with sidecar"

    expected_doc = compute_lesson_lock(
        level,
        slug,
        evidence_dir=evidence_dir,
        plans_dir=plans_dir,
        repo_root=repo_root,
    )
    expected_bytes = lock.yaml_bytes(expected_doc)
    actual_bytes = lock_path.read_bytes()

    if actual_bytes == expected_bytes:
        return True, ""

    actual_text = actual_bytes.decode("utf-8", errors="replace")
    expected_text = expected_bytes.decode("utf-8", errors="replace")

    diff_lines = list(
        difflib.unified_diff(
            actual_text.splitlines(keepends=True),
            expected_text.splitlines(keepends=True),
            fromfile=f"committed:{lock_path}",
            tofile=f"fresh:{lock_path}",
        )
    )
    return False, "".join(diff_lines)


def load_baseline_lock(
    level: str,
    slug: str,
    baseline: str,
    *,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any] | None:
    """Load baseline lock from a directory or git ref."""
    baseline_path = Path(baseline)
    if baseline_path.is_dir():
        candidates = [
            baseline_path / f"{slug}/lessons.lock.yaml",
            baseline_path / f"_state/{slug}/lessons.lock.yaml",
            baseline_path / f"{level}/_state/{slug}/lessons.lock.yaml",
            baseline_path / f"evidence/{level}/_state/{slug}/lessons.lock.yaml",
            baseline_path / f"curriculum/l2-uk-en/evidence/{level}/_state/{slug}/lessons.lock.yaml",
        ]
        target = next((c for c in candidates if c.is_file()), None)
        if target is None:
            return None
        if not lock.check(target):
            raise ValueError(f"{codes.LOCK_MISMATCH}: baseline file {target} sidecar invalid or missing")
        return yaml.safe_load(target.read_text(encoding="utf-8"))

    # Git ref
    if not check_git_ref(baseline, cwd=repo_root):
        raise ValueError(f"Baseline '{baseline}' is neither a directory nor a valid git ref")

    git_lock_rel = f"curriculum/l2-uk-en/evidence/{level}/_state/{slug}/lessons.lock.yaml"
    lock_bytes = read_git_file(baseline, git_lock_rel, cwd=repo_root, timeout=10.0)
    if lock_bytes is None:
        return None

    sidecar_bytes = read_git_file(baseline, f"{git_lock_rel}.lock", cwd=repo_root, timeout=10.0)
    if sidecar_bytes is None:
        raise ValueError(f"{codes.LOCK_MISMATCH}: baseline {baseline}:{git_lock_rel}.lock missing")

    actual_digest = hashlib.sha256(lock_bytes).hexdigest()
    sidecar_digest = sidecar_bytes.strip().decode("ascii", errors="replace")
    if actual_digest != sidecar_digest:
        raise ValueError(f"{codes.LOCK_MISMATCH}: baseline {baseline}:{git_lock_rel} hash mismatch with sidecar")

    return yaml.safe_load(lock_bytes.decode("utf-8"))


def diff_module(
    level: str,
    slug: str,
    baseline: str,
    *,
    evidence_dir: Path | None = None,
    plans_dir: Path | None = None,
    repo_root: Path = REPO_ROOT,
) -> list[dict[str, Any]]:
    """Compare current lesson lock of slug against baseline, returning rebuild items."""
    paths = resolve_paths(level, slug, evidence_dir=evidence_dir, plans_dir=plans_dir, repo_root=repo_root)
    lock_path = paths["lock"]

    if not lock_path.is_file():
        raise FileNotFoundError(f"{lock_path} does not exist; run with --write first")
    if not lock.check(lock_path):
        raise ValueError(f"{codes.LOCK_MISMATCH}: {lock_path} sidecar invalid or missing")

    current_lock = compute_lesson_lock(
        level,
        slug,
        evidence_dir=evidence_dir,
        plans_dir=plans_dir,
        repo_root=repo_root,
    )
    baseline_lock = load_baseline_lock(level, slug, baseline, repo_root=repo_root)

    rebuild: list[dict[str, Any]] = []

    if baseline_lock is None:
        for lesson in current_lock.get("lessons", []):
            rebuild.append({"slug": slug, "lesson": lesson["n"], "reasons": ["new_module"]})
        return rebuild

    curr_shared = current_lock.get("shared", {}).get("sha256")
    base_shared = baseline_lock.get("shared", {}).get("sha256")
    shared_changed = curr_shared != base_shared

    base_lessons = {l["n"]: l for l in baseline_lock.get("lessons", [])}

    for lesson in current_lock.get("lessons", []):
        n = lesson["n"]
        reasons: list[str] = []

        if shared_changed:
            reasons.append("shared_changed")

        if n not in base_lessons:
            reasons.append("plan_changed")
        else:
            bl = base_lessons[n]
            curr_recs = {r["id"]: r["sha256"] for r in lesson.get("records", [])}
            base_recs = {r["id"]: r["sha256"] for r in bl.get("records", [])}

            if set(curr_recs.keys()) != set(base_recs.keys()):
                reasons.append("plan_changed")

            for rid, chash in sorted(curr_recs.items()):
                if rid in base_recs and base_recs[rid] != chash:
                    if rid.startswith("W-"):
                        reasons.append(f"word_record_changed {rid}")
                    else:
                        reasons.append(f"record_changed {rid}")

        if reasons:
            rebuild.append({"slug": slug, "lesson": n, "reasons": reasons})

    return rebuild


def find_level_slugs(
    level: str,
    *,
    evidence_dir: Path | None = None,
    plans_dir: Path | None = None,
    repo_root: Path = REPO_ROOT,
) -> list[str]:
    """Find all module slugs for a level."""
    slugs: set[str] = set()

    pl_dir = plans_dir if plans_dir is not None else repo_root / f"curriculum/l2-uk-en/lesson-plans/{level}"
    if pl_dir.is_dir():
        for f in pl_dir.glob("*.yaml"):
            if not f.name.startswith("_") and f.is_file():
                slugs.add(f.stem)

    ev_root = evidence_dir if evidence_dir is not None else repo_root / f"curriculum/l2-uk-en/evidence/{level}"
    state_dir = ev_root / "_state"
    if state_dir.is_dir():
        for sub in state_dir.iterdir():
            if sub.is_dir() and (sub / "lessons.lock.yaml").is_file():
                slugs.add(sub.name)

    return sorted(slugs)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.curriculum.evidence lessons-lock",
        description=(
            "Generate, check, or diff the per-lesson evidence lock (lessons.lock.yaml).\n"
            "Isolates evidence changes so a record fix invalidates only lessons citing it."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Commands:\n"
            "  lessons-lock <level> <slug> --write\n"
            "      Generate the per-lesson lock file and its .lock sidecar.\n\n"
            "  lessons-lock <level> <slug>\n"
            "      Check byte-for-byte against current state; fail with diff if missing/stale.\n\n"
            "  lessons-lock <level> (<slug> | --all) --diff <baseline>\n"
            "      Compare current lock against baseline (git ref or directory).\n"
            "      Prints lessons to rebuild with reason:\n"
            "        record_changed <id>, shared_changed, plan_changed,\n"
            "        word_record_changed <W-id>, new_module\n\n"
            "Exit codes:\n"
            "  0: Success (nothing to rebuild, or lock is byte-identical)\n"
            "  1: Error (file missing, schema violation, lock mismatch, or retired word id)\n"
            "  3: Rebuild needed (one or more lessons must be rebuilt)\n"
        ),
    )
    parser.add_argument("level", help="Target curriculum level slug (e.g. 'a1', 'a2')")
    parser.add_argument("slug", nargs="?", default=None, help="Target module slug (omitted if --all)")
    parser.add_argument("--all", action="store_true", help="Walk every module of the level (diff mode only)")
    parser.add_argument("--write", action="store_true", help="Generate and write lessons.lock.yaml (+ .lock sidecar)")
    parser.add_argument(
        "--diff",
        metavar="BASELINE",
        default=None,
        help="Compare against baseline (git ref like 'origin/main' or directory holding previous _state/ tree)",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON result to stdout")
    parser.add_argument("--evidence-dir", type=Path, default=None, help="Override evidence output directory")
    parser.add_argument("--plans-dir", type=Path, default=None, help="Override lesson plans directory")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT, help="Override repository root path")

    args = parser.parse_args(argv)

    if args.all:
        if args.slug is not None:
            parser.error("Cannot specify both a module slug and --all")
        if args.diff is None:
            parser.error("--all requires --diff <baseline>")
    elif args.slug is None:
        parser.error("Module slug is required unless --all is specified")

    if args.write and args.diff is not None:
        parser.error("Cannot specify both --write and --diff")

    try:
        # Case 1: Diff mode
        if args.diff is not None:
            if args.all:
                slugs = find_level_slugs(
                    args.level,
                    evidence_dir=args.evidence_dir,
                    plans_dir=args.plans_dir,
                    repo_root=args.repo_root,
                )
            else:
                slugs = [args.slug]

            all_rebuild: list[dict[str, Any]] = []
            for s in slugs:
                module_rebuild = diff_module(
                    args.level,
                    s,
                    args.diff,
                    evidence_dir=args.evidence_dir,
                    plans_dir=args.plans_dir,
                    repo_root=args.repo_root,
                )
                all_rebuild.extend(module_rebuild)

            all_rebuild.sort(key=lambda x: (x["slug"], x["lesson"]))

            if args.json:
                out = {
                    "level": args.level,
                    "baseline": args.diff,
                    "rebuild": all_rebuild,
                }
                print(json.dumps(out, indent=2))
            else:
                if not all_rebuild:
                    print("No lessons to rebuild.")
                else:
                    for item in all_rebuild:
                        for reason in item["reasons"]:
                            print(f"{item['slug']} lesson {item['lesson']}: {reason}")

            return 3 if all_rebuild else 0

        # Case 2: Write mode
        if args.write:
            lock_path, digest = write_lesson_lock(
                args.level,
                args.slug,
                evidence_dir=args.evidence_dir,
                plans_dir=args.plans_dir,
                repo_root=args.repo_root,
            )
            if args.json:
                print(
                    json.dumps(
                        {
                            "status": "ok",
                            "level": args.level,
                            "slug": args.slug,
                            "lock_path": str(lock_path),
                            "lock_hash": digest,
                        },
                        indent=2,
                    )
                )
            else:
                print(f"wrote {lock_path} (lock: {digest[:16]}...)")
            return 0

        # Case 3: Check mode (default)
        ok, diff_output = check_lesson_lock(
            args.level,
            args.slug,
            evidence_dir=args.evidence_dir,
            plans_dir=args.plans_dir,
            repo_root=args.repo_root,
        )
        if ok:
            if args.json:
                print(json.dumps({"status": "ok", "level": args.level, "slug": args.slug}, indent=2))
            else:
                paths = resolve_paths(
                    args.level,
                    args.slug,
                    evidence_dir=args.evidence_dir,
                    plans_dir=args.plans_dir,
                    repo_root=args.repo_root,
                )
                print(f"ok: {paths['lock']} is byte-identical to current state")
            return 0
        else:
            if args.json:
                print(
                    json.dumps(
                        {"status": "stale", "level": args.level, "slug": args.slug, "diff": diff_output}, indent=2
                    )
                )
            else:
                print(diff_output, file=sys.stderr)
            return 1

    except Exception as exc:
        if args.json:
            print(json.dumps({"status": "failed", "error": str(exc)}, indent=2))
        else:
            print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
