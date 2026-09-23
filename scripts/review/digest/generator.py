"""Module digest generator implementation (#8430 WP 15 Part R2a).

Aggregates recorded decisions across lessons 1...n-1 of a module.
Infers nothing; copies and counts from observed, resolutions, provenance, plan v2, and MDX.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

import yaml

from scripts.curriculum.evidence import lock

from . import codes
from .error import DigestError
from .schema import (
    validate_digest,
    validate_observed_schema,
    validate_plan_schema,
    validate_resolutions_schema,
)

REPO_ROOT = Path(__file__).resolve().parents[3]

GENERATOR_VERSION: str = "1"
DIGEST_SCHEMA: int = 1

ALLOWED_LEVELS: tuple[str, ...] = ("a1", "a2", "b1", "b2", "c1", "c2")
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def validate_level(level: str) -> None:
    """Accept level only from the fixed set offered by the CLI."""
    if not isinstance(level, str) or level not in ALLOWED_LEVELS:
        raise DigestError(
            codes.PATH_FORBIDDEN,
            f"level {level!r} is not an allowed CEFR level ({', '.join(ALLOWED_LEVELS)})",
        )


def validate_slug(slug: str) -> None:
    """Accept slug only if it matches ^[a-z0-9]+(?:-[a-z0-9]+)*$."""
    if not isinstance(slug, str) or not SLUG_PATTERN.fullmatch(slug):
        raise DigestError(
            codes.PATH_FORBIDDEN,
            f"slug {slug!r} must match pattern '^[a-z0-9]+(?:-[a-z0-9]+)*$'",
        )


def is_forbidden_path(path: Path) -> bool:
    """Check if resolved path violates R-11 boundaries (curriculum/l2-uk-en/plans/, *-v1, wiki/)."""
    parts = path.resolve().parts
    for i in range(len(parts) - 2):
        if parts[i : i + 3] == ("curriculum", "l2-uk-en", "plans"):
            return True
    if any(part.endswith("-v1") for part in parts):
        return True
    return any(part == "wiki" for part in parts)


def validate_input_path(path: Path, expected_root: Path) -> Path:
    """Resolve path, ensure it lies under expected_root, and verify it is not forbidden under R-11."""
    resolved_root = expected_root.resolve()
    resolved = path.resolve()
    try:
        if not resolved.is_relative_to(resolved_root):
            raise DigestError(
                codes.PATH_FORBIDDEN,
                f"path {path} resolves outside expected root {resolved_root}: {resolved}",
            )
    except (ValueError, TypeError) as exc:
        raise DigestError(
            codes.PATH_FORBIDDEN,
            f"path {path} is invalid: {exc}",
        ) from exc

    if is_forbidden_path(resolved):
        raise DigestError(
            codes.PATH_FORBIDDEN,
            f"path {resolved} is forbidden under R-11",
        )
    return resolved


def _sort_val(v: Any) -> tuple[int, Any]:
    """Helper to sort nullable integers and strings with null sorting first."""
    if v is None:
        return (0, "")
    if isinstance(v, int):
        return (1, v)
    return (2, str(v))


def _sort_key_locator(item: dict[str, Any]) -> tuple:
    """Sort key matching (locator.tab, step, activity, item, block, offset) with null first."""
    loc = item["locator"]
    return (
        _sort_val(loc.get("tab")),
        _sort_val(loc.get("step")),
        _sort_val(loc.get("activity")),
        _sort_val(loc.get("item")),
        _sort_val(loc.get("block")),
        _sort_val(item.get("offset")),
        _sort_val(item.get("record")),
    )


def classify_address_form(forms: list[str]) -> tuple[str, str | None] | None:
    """Classify address form from VESUM tag strings.

    Precedence: second_person over vocative.
    Returns (kind, number) where kind in ("second_person", "vocative") and number in ("s", "p", None).
    """
    for tag in forms:
        atoms = set(tag.split(":"))
        if {"pron", "pers", "2"}.issubset(atoms):
            if "s" in atoms:
                return ("second_person", "s")
            elif "p" in atoms:
                return ("second_person", "p")
            return ("second_person", None)

    for tag in forms:
        atoms = set(tag.split(":"))
        if "v_kly" in atoms:
            return ("vocative", None)

    return None


def compute_file_sha256(path: Path) -> str:
    """Compute sha256 hex digest of file bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_digest(
    level: str,
    slug: str,
    up_to: int,
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Build deterministic module digest dict for lessons 1...up_to-1."""
    validate_level(level)
    validate_slug(slug)

    if up_to < 1:
        raise DigestError(codes.INVALID_ARGUMENT, f"--up-to must be >= 1, got {up_to}")

    root = (repo_root or REPO_ROOT).resolve()
    expected_plan_root = (root / f"curriculum/l2-uk-en/lesson-plans/{level}").resolve()
    expected_state_root = (root / f"curriculum/l2-uk-en/evidence/{level}/_state/{slug}").resolve()
    expected_mdx_root = (root / f"site/src/content/docs/{level}/{slug}").resolve()

    plan_path = root / f"curriculum/l2-uk-en/lesson-plans/{level}/{slug}.yaml"
    resolved_plan_path = validate_input_path(plan_path, expected_plan_root)

    if not resolved_plan_path.is_file():
        raise DigestError(codes.PLAN_MISSING, f"module plan {resolved_plan_path} not found")

    plan_sha256 = compute_file_sha256(resolved_plan_path)
    try:
        plan_doc = yaml.safe_load(resolved_plan_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise DigestError(codes.PLAN_INVALID, f"module plan {resolved_plan_path} unreadable YAML: {exc}") from exc

    if not isinstance(plan_doc, dict):
        raise DigestError(codes.PLAN_INVALID, f"module plan {resolved_plan_path} is not a YAML mapping")

    validate_plan_schema(plan_doc, resolved_plan_path, repo_root=root)

    plan_lessons_by_n: dict[int, dict[str, Any]] = {
        l["n"]: l for l in plan_doc["lessons"]
    }

    sources: list[dict[str, Any]] = []
    lessons: list[dict[str, Any]] = []

    for k in range(1, up_to):
        if k not in plan_lessons_by_n:
            raise DigestError(codes.LESSON_NOT_IN_PLAN, f"lesson {k} not found in module plan {resolved_plan_path}")

        mdx_path = root / f"site/src/content/docs/{level}/{slug}/{k}.mdx"
        resolved_mdx = validate_input_path(mdx_path, expected_mdx_root)
        if not resolved_mdx.is_file():
            raise DigestError(codes.MDX_MISSING, f"lesson {k} MDX file {resolved_mdx} not found")
        mdx_sha256 = compute_file_sha256(resolved_mdx)

        obs_path = root / f"curriculum/l2-uk-en/evidence/{level}/_state/{slug}/lesson-{k}.observed.yaml"
        resolved_obs = validate_input_path(obs_path, expected_state_root)
        if not resolved_obs.is_file():
            raise DigestError(codes.OBSERVED_MISSING, f"observed state file {resolved_obs} not found")
        try:
            lock.require(resolved_obs)
        except ValueError as exc:
            msg = str(exc)
            if msg.startswith(f"{codes.LOCK_MISMATCH}: "):
                msg = msg[len(codes.LOCK_MISMATCH) + 2:]
            raise DigestError(codes.LOCK_MISMATCH, msg) from exc
        obs_sha256 = compute_file_sha256(resolved_obs)
        try:
            obs_doc = yaml.safe_load(resolved_obs.read_text(encoding="utf-8"))
        except Exception as exc:
            raise DigestError(codes.OBSERVED_INVALID, f"observed file {resolved_obs} unreadable: {exc}") from exc
        if not isinstance(obs_doc, dict):
            raise DigestError(codes.OBSERVED_INVALID, f"observed file {resolved_obs} is not a YAML mapping")
        validate_observed_schema(obs_doc, resolved_obs, repo_root=root)

        res_path = root / f"curriculum/l2-uk-en/evidence/{level}/_state/{slug}/lesson-{k}.resolutions.yaml"
        resolved_res = validate_input_path(res_path, expected_state_root)
        if not resolved_res.is_file():
            raise DigestError(codes.RESOLUTIONS_MISSING, f"resolutions file {resolved_res} not found")
        try:
            lock.require(resolved_res)
        except ValueError as exc:
            msg = str(exc)
            if msg.startswith(f"{codes.LOCK_MISMATCH}: "):
                msg = msg[len(codes.LOCK_MISMATCH) + 2:]
            raise DigestError(codes.LOCK_MISMATCH, msg) from exc
        res_sha256 = compute_file_sha256(resolved_res)
        try:
            res_doc = yaml.safe_load(resolved_res.read_text(encoding="utf-8"))
        except Exception as exc:
            raise DigestError(codes.RESOLUTIONS_INVALID, f"resolutions file {resolved_res} unreadable: {exc}") from exc
        if not isinstance(res_doc, dict):
            raise DigestError(codes.RESOLUTIONS_INVALID, f"resolutions file {resolved_res} is not a YAML mapping")
        validate_resolutions_schema(res_doc, resolved_res, repo_root=root)

        prov_path = root / f"curriculum/l2-uk-en/evidence/{level}/_state/{slug}/lesson-{k}.provenance.yaml"
        resolved_prov = validate_input_path(prov_path, expected_state_root)
        if not resolved_prov.is_file():
            raise DigestError(codes.PROVENANCE_MISSING, f"provenance file {resolved_prov} not found")
        prov_sha256 = compute_file_sha256(resolved_prov)
        try:
            prov_doc = yaml.safe_load(resolved_prov.read_text(encoding="utf-8"))
        except Exception as exc:
            raise DigestError(codes.PROVENANCE_INVALID, f"provenance file {resolved_prov} unreadable: {exc}") from exc
        if not isinstance(prov_doc, dict):
            raise DigestError(codes.PROVENANCE_INVALID, f"provenance file {resolved_prov} is not a YAML mapping")
        if "spans" not in prov_doc or not isinstance(prov_doc["spans"], list):
            raise DigestError(codes.PROVENANCE_INVALID, f"provenance file {resolved_prov} missing 'spans' list")

        sources.append(
            {
                "lesson": k,
                "mdx_sha256": mdx_sha256,
                "observed_sha256": obs_sha256,
                "resolutions_sha256": res_sha256,
                "provenance_sha256": prov_sha256,
            }
        )

        prov_map: dict[tuple[Any, Any, Any, Any, Any], dict[str, Any]] = {}
        for span in prov_doc["spans"]:
            if isinstance(span, dict):
                key = (
                    span.get("tab"),
                    span.get("step"),
                    span.get("activity"),
                    span.get("item"),
                    span.get("block"),
                )
                if key not in prov_map:
                    prov_map[key] = {
                        "source": span.get("source"),
                        "ref": span.get("ref"),
                    }

        observed_roles: dict[str, str] = {
            rec["id"]: rec["role"] for rec in obs_doc["records"]
        }

        occurrences: list[dict[str, Any]] = []
        names: list[dict[str, Any]] = []
        dialogue_address_forms: list[dict[str, Any]] = []

        tokens = res_doc["tokens"]
        for token in tokens:
            selected = token["selected"]
            if not selected:
                continue
            rec_id = selected["record"]
            forms = selected["forms"]
            pos = forms[0].split(":")[0] if forms else ""

            if rec_id not in observed_roles:
                raise DigestError(
                    codes.RECORD_NOT_IN_OBSERVED,
                    f"token record {rec_id} not found in observed index {resolved_obs}",
                )
            role = observed_roles[rec_id]

            prov_str = token["provenance"]
            if prov_str == "deterministic":
                chosen_by = "resolver"
                question_ref = None
            else:
                chosen_by = "question"
                question_ref = prov_str

            unit = token["unit"]
            locator = {
                "tab": unit["tab"],
                "step": unit.get("step"),
                "activity": unit["activity"],
                "item": unit["item"],
                "block": unit["block"],
            }

            tok_key = (
                locator["tab"],
                locator["step"],
                locator["activity"],
                locator["item"],
                locator["block"],
            )
            if tok_key not in prov_map:
                raise DigestError(
                    codes.UNIT_NOT_IN_PROVENANCE,
                    f"token unit {locator} not found in provenance spans of {resolved_prov}",
                )
            span_info = prov_map[tok_key]
            span_source = span_info.get("source")
            span_ref = span_info.get("ref")

            offset = token["offset"]
            length = len(token["token"])

            if role == "name":
                names.append(
                    {
                        "record": rec_id,
                        "pos": pos,
                        "forms": list(forms),
                        "chosen_by": chosen_by,
                        "question_ref": question_ref,
                        "locator": locator,
                        "offset": offset,
                        "length": length,
                        "span_source": span_source,
                        "span_ref": span_ref,
                    }
                )
            else:
                occurrences.append(
                    {
                        "record": rec_id,
                        "pos": pos,
                        "forms": list(forms),
                        "role": role,
                        "chosen_by": chosen_by,
                        "question_ref": question_ref,
                        "locator": locator,
                        "offset": offset,
                        "length": length,
                        "span_source": span_source,
                        "span_ref": span_ref,
                    }
                )

            block = locator["block"]
            if isinstance(block, str) and block.startswith("dialogue_"):
                af_info = classify_address_form(forms)
                if af_info is not None:
                    af_kind, af_number = af_info
                    dialogue_address_forms.append(
                        {
                            "record": rec_id,
                            "forms": list(forms),
                            "kind": af_kind,
                            "number": af_number,
                            "locator": locator,
                            "offset": offset,
                            "length": length,
                        }
                    )

        occurrences.sort(key=_sort_key_locator)
        names.sort(key=_sort_key_locator)
        dialogue_address_forms.sort(key=_sort_key_locator)

        lesson_plan = plan_lessons_by_n[k]
        taught_grammar: list[str] = []
        for step in lesson_plan["steps"]:
            introduces = step.get("introduces")
            if isinstance(introduces, dict):
                for gid in introduces.get("grammar") or []:
                    if isinstance(gid, str):
                        taught_grammar.append(gid)

        untaught = obs_doc["untaught_forms"]
        raw_forms = untaught["forms"]
        encountered_unexplained = [
            {
                "record": item["record"],
                "tags": item["tags"],
                "category": item["category"],
            }
            for item in raw_forms
        ]

        grammar_entry = {
            "taught": taught_grammar,
            "encountered_unexplained": encountered_unexplained,
        }

        plan_dialogue = lesson_plan.get("dialogue")
        if plan_dialogue is not None:
            places = [
                p["name"]
                for p in plan_dialogue.get("places") or []
            ]
            speakers = [
                {
                    "name": s["name"],
                    "role": s["role"],
                    "gender": s["gender"],
                }
                for s in plan_dialogue["speakers"]
            ]
            dialogue_entry: dict[str, Any] | None = {
                "step": plan_dialogue.get("step"),
                "setting": plan_dialogue["setting"],
                "register": plan_dialogue["register"],
                "places": places,
                "speakers": speakers,
                "address_forms": dialogue_address_forms,
            }
        else:
            dialogue_entry = None

        lessons.append(
            {
                "lesson": k,
                "occurrences": occurrences,
                "names": names,
                "grammar": grammar_entry,
                "dialogue": dialogue_entry,
            }
        )

    sources.sort(key=lambda s: s["lesson"])
    lessons.sort(key=lambda l: l["lesson"])

    digest_doc: dict[str, Any] = {
        "digest_schema": DIGEST_SCHEMA,
        "generator_version": GENERATOR_VERSION,
        "level": level,
        "slug": slug,
        "up_to": up_to,
        "plan_sha256": plan_sha256,
        "sources": sources,
        "lessons": lessons,
    }

    validate_digest(digest_doc, repo_root=root)
    return digest_doc


def digest_output_path(
    level: str,
    slug: str,
    up_to: int,
    *,
    repo_root: Path | None = None,
) -> Path:
    """Return path to digest-upto-<n>.yaml."""
    validate_level(level)
    validate_slug(slug)
    root = (repo_root or REPO_ROOT).resolve()
    expected_root = (root / f"curriculum/l2-uk-en/evidence/{level}/_state/{slug}").resolve()
    path = root / f"curriculum/l2-uk-en/evidence/{level}/_state/{slug}/digest-upto-{up_to}.yaml"
    return validate_input_path(path, expected_root)


def write_digest(
    digest_doc: dict[str, Any],
    *,
    repo_root: Path | None = None,
) -> tuple[Path, str]:
    """Write digest and lock sidecar to disk, returning path and sha256."""
    validate_digest(digest_doc, repo_root=repo_root)
    validate_level(digest_doc["level"])
    validate_slug(digest_doc["slug"])
    path = digest_output_path(
        digest_doc["level"],
        digest_doc["slug"],
        digest_doc["up_to"],
        repo_root=repo_root,
    )
    content_bytes = lock.yaml_bytes(digest_doc)
    sha256 = lock.write(path, content_bytes)
    return path, sha256


def check_digest(
    level: str,
    slug: str,
    up_to: int,
    *,
    repo_root: Path | None = None,
) -> tuple[Path, str]:
    """Verify digest on disk against recomputed content without byte drift."""
    validate_level(level)
    validate_slug(slug)
    path = digest_output_path(level, slug, up_to, repo_root=repo_root)
    if not path.is_file():
        raise DigestError(codes.DIGEST_FILE_MISSING, f"digest file {path} not found")
    lock_path = Path(f"{path}.lock")
    if not lock_path.is_file():
        raise DigestError(codes.DIGEST_FILE_MISSING, f"lock file {lock_path} not found")
    if not lock.check(path):
        raise DigestError(codes.LOCK_MISMATCH, f"digest lock check failed for {path}")

    computed_doc = build_digest(level, slug, up_to, repo_root=repo_root)
    expected_bytes = lock.yaml_bytes(computed_doc)
    actual_bytes = path.read_bytes()

    if actual_bytes != expected_bytes:
        raise DigestError(
            codes.BYTE_DRIFT,
            f"digest file on disk disagrees with recomputed bytes: {path}",
        )

    return path, hashlib.sha256(actual_bytes).hexdigest()
