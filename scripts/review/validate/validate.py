"""Active validator for a review return (#8430 r4).

Rejects a review whose manifest hash, receipts, quotes, taxonomy checks, or
evidence branch do not match the pinned inputs. Prints APPROVE or REVISE from
active and persisting findings. A resolved MAJOR is history and does not block.

A plan review (manifest kind: plan) is validated against the plan pinned by the
manifest: the plan's sha256 must equal inputs.plan.sha256, every manifest input
must still be current (after a promotion, only the plan transition proven by the
promotion receipt may differ), and a located finding's quote must occur inside
the named lesson/step/activity/field of that plan. Against a manifest that is not
a plan manifest no plan document is pinned, so:

Plan-review findings with locations are rejected (location_not_in_lesson)
until a plan document locator is defined.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from scripts.curriculum.resolver.codes import TABS
from scripts.review.receipts.ledger import REVIEW_TOOLS, LedgerError, LedgerHashStaleLastLine, records

from . import codes

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = REPO_ROOT / "schemas" / "review-v1.schema.json"
TAXONOMY_PATH = REPO_ROOT / "schemas" / "review-taxonomy-v1.yaml"
EXERCISE_TAB = "vpravy"
EVIDENCE_KEYS = ("evidence", "unsupported_by_source", "source_conflict")
PREVIOUS_STATUSES = frozenset({"resolved", "persisting"})
BLOCKING_STATUSES = frozenset({"active", "persisting"})
_STRESS = frozenset("\u0301\u0300")
_NO_HITS = ("no result", "no hits", "not found", "0 results")


@dataclass
class Rejection:
    code: str
    message: str


@dataclass
class ValidationResult:
    ok: bool
    verdict: str | None
    rejections: list[Rejection] = field(default_factory=list)
    active_blockers: int = 0
    active_majors: int = 0

    def payload(self) -> dict[str, Any]:
        return {
            "active_blockers": self.active_blockers,
            "active_majors": self.active_majors,
            "ok": self.ok,
            "rejections": [{"code": item.code, "message": item.message} for item in self.rejections],
            "verdict": self.verdict,
        }


def fold_quote(text: str) -> str:
    """NFC, then drop combining acute and grave. Same fold as the word store."""
    nfd = unicodedata.normalize("NFD", text)
    return unicodedata.normalize("NFC", "".join(ch for ch in nfd if ch not in _STRESS))


def _load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_bytes())


def _taxonomy() -> dict[str, Any]:
    loaded = _load_yaml(TAXONOMY_PATH)
    if not isinstance(loaded, dict):
        raise ValueError("review taxonomy is not a mapping")
    return loaded


def _schema_validator() -> Draft202012Validator:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def review_schema_errors(review: Any) -> list[str]:
    """Every way ``review`` departs from ``schemas/review-v1.schema.json`` (empty when it conforms)."""
    return [f"{error.json_path}: {error.message}" for error in _schema_validator().iter_errors(review)]


def _kind_checks(taxonomy: dict[str, Any], kind: str, *, recap: bool) -> dict[str, str]:
    """Map check name to required, optional, or absent."""
    spec = taxonomy["kinds"][kind]["checks"]
    modes: dict[str, str] = {}
    for item in spec:
        name = item["name"]
        if item.get("recap_only"):
            modes[name] = "required" if recap else "absent"
        elif item.get("optional"):
            modes[name] = "optional"
        else:
            modes[name] = "required"
    return modes


def _outcome_shown(outcome: str, record: dict[str, Any]) -> bool:
    """Whether the ledger record shows the reviewer's claimed search outcome.

    Decided from structured outcome_facts captured at record time.
    """
    call_status = record.get("status")
    facts = record.get("outcome_facts")
    if facts is None:
        from scripts.review.receipts.outcomes import classify_outcome

        tool = record.get("tool", "")
        result_text = record.get("result", "")
        facts = classify_outcome(tool, call_status or "ok", result_text)

    if outcome == "error":
        return call_status == "error" or facts.get("status") == "error"
    if call_status != "ok":
        return False
    if outcome == "unavailable":
        return bool(facts.get("unavailable")) or facts.get("status") == "unavailable"
    if facts.get("unavailable"):
        return False
    if outcome == "no_hits":
        return facts.get("hits") == 0
    if outcome == "hits_but_no_support":
        return (facts.get("hits") or 0) > 0
    return False


def _units(document: Any) -> list[dict[str, Any]]:
    if not isinstance(document, dict) or not isinstance(document.get("units"), list):
        raise ValueError("expanded document needs a units list")
    units: list[dict[str, Any]] = []
    for raw in document["units"]:
        if not isinstance(raw, dict) or not isinstance(raw.get("tab"), str) or not isinstance(raw.get("text"), str):
            raise ValueError("a unit needs tab and text")
        units.append(
            {
                "tab": raw["tab"],
                "activity": raw.get("activity"),
                "item": raw.get("item"),
                "text": raw["text"],
            }
        )
    return units


def index_ledger(path: Path) -> dict[str, dict[str, Any]]:
    """Receipts by id, read through the ledger's sidecar verification; a duplicate or id-less record is refused."""
    indexed: dict[str, dict[str, Any]] = {}
    for record in records(path):
        receipt_id = record.get("receipt_id")
        if not isinstance(receipt_id, str) or receipt_id in indexed:
            raise LedgerError(f"duplicate or missing receipt id in {path}")
        indexed[receipt_id] = record
    return indexed


class _Check:
    def __init__(self) -> None:
        self.rejections: list[Rejection] = []

    def add(self, code: str, message: str) -> None:
        self.rejections.append(Rejection(code, message))

    @property
    def ok(self) -> bool:
        return not self.rejections


def _matching_units(units: list[dict[str, Any]], location: dict[str, Any]) -> list[dict[str, Any]]:
    matched = []
    for unit in units:
        if unit["tab"] != location.get("tab"):
            continue
        if "activity" in location and unit["activity"] != location["activity"]:
            continue
        if "item" in location and unit["item"] != location["item"]:
            continue
        matched.append(unit)
    return matched


def _peek_kind(review_path: Path) -> str | None:
    """The review's kind, read early because it decides which document the review is checked against."""
    try:
        review = _load_yaml(Path(review_path))
    except (OSError, yaml.YAMLError):
        return None
    return review.get("kind") if isinstance(review, dict) and isinstance(review.get("kind"), str) else None


def _leaf_texts(node: Any) -> list[str]:
    """Every scalar value under node, one string each, in document order (keys are not text)."""
    if isinstance(node, dict):
        return [text for value in node.values() for text in _leaf_texts(value)]
    if isinstance(node, list):
        return [text for value in node for text in _leaf_texts(value)]
    if node is None:
        return []
    return [node if isinstance(node, str) else str(node)]


def _plan_unit(plan: dict[str, Any], location: dict[str, Any]) -> Any:
    """The plan node a location or scope names; _MISSING when the plan has no such unit.

    ``lesson`` selects the lesson whose ``n`` it is (omitted: the module itself);
    ``step`` or ``activity`` selects the entry of that lesson's ``steps`` or
    ``activities`` with that ``id``; ``field`` is a dotted path of mapping keys and
    list indexes inside what was selected.
    """
    node: Any = plan
    if "lesson" in location:
        node = next(
            (
                item
                for item in plan.get("lessons") or []
                if isinstance(item, dict) and item.get("n") == location["lesson"]
            ),
            _MISSING,
        )
        if node is _MISSING:
            return _MISSING
        for key, list_name in (("step", "steps"), ("activity", "activities")):
            if key in location:
                node = next(
                    (
                        item
                        for item in node.get(list_name) or []
                        if isinstance(item, dict) and item.get("id") == location[key]
                    ),
                    _MISSING,
                )
                if node is _MISSING:
                    return _MISSING
    for part in str(location.get("field", "")).split("."):
        if not part:
            continue
        if isinstance(node, dict) and part in node:
            node = node[part]
        elif isinstance(node, list) and part.isdigit() and int(part) < len(node):
            node = node[int(part)]
        else:
            return _MISSING
    return node


_MISSING = object()


def _load_plan_document(
    check: _Check, manifest: dict[str, Any], manifest_hash: str, document: Path | None, root: Path
) -> dict[str, Any] | None:
    """The plan a plan-manifest pins, verified against inputs.plan.sha256 before it is used.

    Also fails PLAN_INPUTS_STALE for every other manifest input that changed (the
    freshness rules of scripts/build/fresh/plan_manifest.py). After a promotion
    the live plan differs from the manifest by design; the reviewed copy the
    receipt names is then the pinned document.
    """
    from scripts.build.fresh import plan_manifest as pm

    try:
        pm.validate_manifest_document(manifest)
    except pm.PlanReviewError as exc:
        check.add(codes.PLAN_MANIFEST_INVALID, exc.message)
        return None
    pinned = manifest["inputs"]["plan"]
    freshness = pm.plan_review_freshness(root, manifest, manifest_hash)
    candidates = [Path(document)] if document is not None else [root / pinned["path"]]
    if document is None and freshness.state == "promoted":
        candidates.append(
            pm.state_dir(root, manifest["level"], manifest["slug"]) / f"plan-reviewed.{pinned['sha256']}.yaml"
        )
    content: bytes | None = None
    for candidate in candidates:
        try:
            data = candidate.read_bytes()
        except OSError:
            continue
        if hashlib.sha256(data).hexdigest() == pinned["sha256"]:
            content = data
            break
    plan: dict[str, Any] | None = None
    if content is None:
        readable = [candidate for candidate in candidates if candidate.is_file()]
        if readable:
            check.add(
                codes.PLAN_BYTES_MISMATCH,
                f"{readable[0]} does not hash to the manifest's inputs.plan.sha256 {pinned['sha256']}",
            )
        else:
            check.add(codes.PLAN_UNREADABLE, f"{candidates[0]}: the plan the manifest pins is missing")
    else:
        try:
            loaded = yaml.safe_load(content)
        except yaml.YAMLError as exc:
            check.add(codes.PLAN_UNREADABLE, f"{candidates[0]}: {type(exc).__name__}")
        else:
            if isinstance(loaded, dict) and isinstance(loaded.get("lessons"), list):
                plan = loaded
            else:
                check.add(codes.PLAN_UNREADABLE, f"{candidates[0]} is not a plan mapping with lessons")
    stale = {path: why for path, why in freshness.stale.items() if not (content is None and path == pinned["path"])}
    if stale:
        check.add(
            codes.PLAN_INPUTS_STALE,
            "changed since the manifest: " + "; ".join(f"{path} ({why})" for path, why in sorted(stale.items())),
        )
    return plan


def _check_plan_locations(check: _Check, finding: dict[str, Any], plan: dict[str, Any], locations: list) -> None:
    if not locations:
        scope = finding.get("scope")
        if not isinstance(scope, dict) or "lesson" not in scope:
            check.add(codes.SCOPE_MISSING, f"{finding.get('id')}: absence finding needs scope.lesson")
        elif _plan_unit(plan, scope) is _MISSING:
            check.add(codes.LOCATION_NOT_IN_PLAN, f"{finding.get('id')}: scope {scope} is not in the plan")
        return
    for location in locations:
        if not isinstance(location, dict):
            continue
        quote = location.get("quote")
        folded = fold_quote(quote) if isinstance(quote, str) else ""
        if folded.strip() == "":
            check.add(codes.QUOTE_EMPTY, f"{finding.get('id')}: quote is empty")
            continue
        unit = _plan_unit(plan, location)
        if unit is _MISSING:
            check.add(
                codes.LOCATION_NOT_IN_PLAN, f"{finding.get('id')}: location {_describe(location)} is not in the plan"
            )
            continue
        if folded not in fold_quote("\n".join(_leaf_texts(unit))):
            check.add(codes.QUOTE_NOT_IN_UNIT, f"{finding.get('id')}: quote is not inside {_describe(location)}")


def _describe(location: dict[str, Any]) -> str:
    return ", ".join(f"{key} {location[key]}" for key in ("lesson", "step", "activity", "field") if key in location)


def _check_locations(
    check: _Check,
    finding: dict[str, Any],
    units: list[dict[str, Any]],
    *,
    kind: str,
    plan: dict[str, Any] | None = None,
    plan_mode: bool = False,
) -> None:
    locations = finding.get("locations")
    if not isinstance(locations, list):
        return
    if kind == "plan" and plan_mode:
        if plan is not None:
            _check_plan_locations(check, finding, plan, locations)
        return
    if kind == "plan" and locations:
        check.add(
            codes.LOCATION_NOT_IN_LESSON,
            f"{finding.get('id')}: plan-review findings with locations are rejected until a plan document locator is defined",
        )
        return
    if not locations:
        scope = finding.get("scope")
        if not isinstance(scope, dict) or not isinstance(scope.get("tab"), str) or not scope["tab"]:
            check.add(codes.SCOPE_MISSING, f"{finding.get('id')}: absence finding needs scope.tab")
            return
        if kind == "lesson" and scope["tab"] not in TABS:
            check.add(
                codes.LOCATION_NOT_IN_LESSON, f"{finding.get('id')}: scope tab {scope['tab']!r} is not in the lesson"
            )
            return
        activity = scope.get("activity")
        if kind == "lesson" and isinstance(activity, str) and not any(unit["activity"] == activity for unit in units):
            check.add(
                codes.LOCATION_NOT_IN_LESSON,
                f"{finding.get('id')}: scope activity {activity!r} is not in the lesson",
            )
        return
    for location in locations:
        if not isinstance(location, dict):
            continue
        quote = location.get("quote")
        folded = fold_quote(quote) if isinstance(quote, str) else ""
        if folded.strip() == "":
            check.add(codes.QUOTE_EMPTY, f"{finding.get('id')}: quote is empty")
            continue
        if location.get("tab") == EXERCISE_TAB and ("activity" not in location or "item" not in location):
            check.add(codes.LOCATION_INCOMPLETE, f"{finding.get('id')}: exercise location needs activity and item")
            continue
        matched = _matching_units(units, location)
        if not matched:
            check.add(codes.LOCATION_NOT_IN_LESSON, f"{finding.get('id')}: location is outside the lesson")
            continue
        haystack = fold_quote("\n".join(unit["text"] for unit in matched))
        if folded not in haystack:
            check.add(codes.QUOTE_NOT_IN_UNIT, f"{finding.get('id')}: quote is not inside the named unit")


def _cited_receipts(finding: dict[str, Any]) -> list[str]:
    if "evidence" in finding and isinstance(finding["evidence"], dict):
        receipt = finding["evidence"].get("receipt")
        return [receipt] if isinstance(receipt, str) else []
    if "source_conflict" in finding and isinstance(finding["source_conflict"], dict):
        found = []
        for side in ("a", "b"):
            ref = finding["source_conflict"].get(side)
            if isinstance(ref, dict) and isinstance(ref.get("receipt"), str):
                found.append(ref["receipt"])
        return found
    if "unsupported_by_source" in finding and isinstance(finding["unsupported_by_source"], dict):
        searches = finding["unsupported_by_source"].get("searches")
        if not isinstance(searches, list):
            return []
        return [item["receipt"] for item in searches if isinstance(item, dict) and isinstance(item.get("receipt"), str)]
    return []


def _accept_record(
    record: dict[str, Any],
    *,
    review_id: str,
    attempt_id: str,
    manifest_sha256: str | None,
) -> bool:
    same_attempt = record.get("review_id") == review_id and record.get("attempt_id") == attempt_id
    same_manifest = manifest_sha256 is None or record.get("manifest_sha256") == manifest_sha256
    return same_attempt and same_manifest


def _resolve(
    check: _Check,
    receipt_id: str,
    *,
    current: dict[str, dict[str, Any]],
    previous: dict[str, dict[str, Any]] | None,
    allow_previous: bool,
    review_id: str,
    attempt_id: str,
    manifest_sha256: str,
    previous_attempt_id: str | None,
) -> dict[str, Any] | None:
    record = current.get(receipt_id)
    if record is not None and _accept_record(
        record, review_id=review_id, attempt_id=attempt_id, manifest_sha256=manifest_sha256
    ):
        return record
    if allow_previous and previous is not None and previous_attempt_id:
        earlier = previous.get(receipt_id)
        if earlier is not None and _accept_record(
            earlier, review_id=review_id, attempt_id=previous_attempt_id, manifest_sha256=None
        ):
            return earlier
    check.add(codes.RECEIPT_NOT_IN_LEDGER, f"receipt {receipt_id} is not in the attempt ledger")
    return None


def _check_finding_evidence(
    check: _Check,
    finding: dict[str, Any],
    *,
    current: dict[str, dict[str, Any]],
    previous: dict[str, dict[str, Any]] | None,
    review_id: str,
    attempt_id: str,
    manifest_sha256: str,
    previous_attempt_id: str | None,
) -> None:
    present = [key for key in EVIDENCE_KEYS if key in finding]
    if len(present) != 1:
        check.add(codes.EVIDENCE_BRANCH_COUNT, f"{finding.get('id')}: evidence branch count is {len(present)}")
        return
    status = finding.get("status")
    allow_previous = status in PREVIOUS_STATUSES
    if present[0] == "unsupported_by_source":
        severity = finding.get("severity")
        if severity in {"BLOCKER", "MAJOR"}:
            check.add(
                codes.UNSUPPORTED_SEVERITY_ABOVE_MINOR,
                f"{finding.get('id')}: unsupported_by_source finding severity {severity} is above MINOR",
            )
        searches = (
            finding["unsupported_by_source"].get("searches")
            if isinstance(finding["unsupported_by_source"], dict)
            else None
        )
        if not isinstance(searches, list) or not searches:
            check.add(codes.UNSUPPORTED_WITHOUT_SEARCHES, f"{finding.get('id')}: unsupported_by_source has no searches")
            return
        for search in searches:
            if not isinstance(search, dict):
                continue
            outcome = search.get("outcome")
            receipt_id = search.get("receipt")
            if not isinstance(receipt_id, str):
                continue
            record = _resolve(
                check,
                receipt_id,
                current=current,
                previous=previous,
                allow_previous=allow_previous,
                review_id=review_id,
                attempt_id=attempt_id,
                manifest_sha256=manifest_sha256,
                previous_attempt_id=previous_attempt_id,
            )
            if record is not None and isinstance(outcome, str) and not _outcome_shown(outcome, record):
                check.add(
                    codes.OUTCOME_NOT_IN_LEDGER,
                    f"{finding.get('id')}: outcome {outcome} is not in receipt {receipt_id}",
                )
    elif present[0] == "evidence":
        receipt_id = finding["evidence"].get("receipt") if isinstance(finding["evidence"], dict) else None
        if isinstance(receipt_id, str):
            record = _resolve(
                check,
                receipt_id,
                current=current,
                previous=previous,
                allow_previous=allow_previous,
                review_id=review_id,
                attempt_id=attempt_id,
                manifest_sha256=manifest_sha256,
                previous_attempt_id=previous_attempt_id,
            )
            if record is not None and (record.get("status") != "ok" or record.get("tool") not in REVIEW_TOOLS):
                check.add(
                    codes.EVIDENCE_RECEIPT_INVALID,
                    f"{finding.get('id')}: positive evidence receipt {receipt_id} requires status: ok and review tool",
                )
    else:
        for receipt_id in _cited_receipts(finding):
            record = _resolve(
                check,
                receipt_id,
                current=current,
                previous=previous,
                allow_previous=allow_previous,
                review_id=review_id,
                attempt_id=attempt_id,
                manifest_sha256=manifest_sha256,
                previous_attempt_id=previous_attempt_id,
            )
            if record is not None and (record.get("status") != "ok" or record.get("tool") not in REVIEW_TOOLS):
                check.add(
                    codes.EVIDENCE_RECEIPT_INVALID,
                    f"{finding.get('id')}: source conflict receipt {receipt_id} requires status: ok and review tool",
                )

    expected = finding.get("expected")
    if not isinstance(expected, str):
        return
    stored = []
    for receipt_id in _cited_receipts(finding):
        record = current.get(receipt_id)
        if record is None and previous is not None:
            record = previous.get(receipt_id)
        if isinstance(record, dict) and isinstance(record.get("result"), str):
            stored.append(record["result"])
    if stored and not any(expected in result for result in stored):
        check.add(codes.EXPECTED_NOT_IN_RESULT, f"{finding.get('id')}: expected is not in the stored result")


def _check_taxonomy(
    check: _Check,
    review: dict[str, Any],
    taxonomy: dict[str, Any],
    *,
    recap: bool,
) -> None:
    kind = review.get("kind")
    if kind not in taxonomy.get("kinds", {}):
        return
    findings = review.get("findings")
    if not isinstance(findings, list):
        return
    ids = [item.get("id") for item in findings if isinstance(item, dict)]
    seen: set[str] = set()
    for finding_id in ids:
        if not isinstance(finding_id, str):
            continue
        if finding_id in seen:
            check.add(codes.DUPLICATE_FINDING_ID, f"finding id {finding_id} is repeated")
        seen.add(finding_id)
    language_dims = set(taxonomy.get("sub_dimensions", {}).get("language", []))
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        if finding.get("dimension") == "language":
            sub = finding.get("sub_dimension")
            if not isinstance(sub, str):
                check.add(
                    codes.LANGUAGE_SUB_DIMENSION_MISSING, f"{finding.get('id')}: language finding needs sub_dimension"
                )
            elif sub not in language_dims:
                check.add(
                    codes.SUB_DIMENSION_INVALID, f"{finding.get('id')}: sub_dimension {sub!r} is not in the taxonomy"
                )
    modes = _kind_checks(taxonomy, kind, recap=recap)
    checks = review.get("checks")
    if not isinstance(checks, dict):
        return
    listed: dict[str, str] = {}
    for name, mode in modes.items():
        if name not in checks:
            if mode == "required":
                check.add(codes.CHECK_MISSING, f"check {name} is missing")
            continue
        if mode == "absent":
            check.add(codes.CHECK_NOT_APPLICABLE, f"check {name} applies only to a recap")
            continue
        value = checks[name]
        if value == "clean":
            continue
        if not isinstance(value, list) or not value:
            check.add(codes.CHECK_MISSING, f"check {name} is neither clean nor a list of finding ids")
            continue
        for finding_id in value:
            if not isinstance(finding_id, str) or finding_id not in seen:
                check.add(codes.DANGLING_CHECK_REFERENCE, f"check {name} lists unknown finding {finding_id}")
                continue
            if finding_id in listed:
                check.add(codes.FINDING_NOT_REFERENCED, f"finding {finding_id} is listed under more than one check")
            else:
                listed[finding_id] = name
    for finding in findings:
        if not isinstance(finding, dict) or not isinstance(finding.get("id"), str):
            continue
        finding_id = finding["id"]
        if finding_id not in listed:
            check.add(codes.FINDING_NOT_REFERENCED, f"finding {finding_id} is not listed under a check")
            continue
        if kind == "lesson" and finding.get("dimension") in modes and listed[finding_id] != finding.get("dimension"):
            check.add(
                codes.FINDING_NOT_REFERENCED,
                f"finding {finding_id} is listed under {listed[finding_id]}, not {finding.get('dimension')}",
            )
    for name in checks:
        if name not in modes:
            check.add(codes.CHECK_NOT_APPLICABLE, f"check {name} is not in the taxonomy for {kind}")


def _verdict(findings: list[Any]) -> tuple[str, int, int]:
    blockers = 0
    majors = 0
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        if finding.get("status") not in BLOCKING_STATUSES:
            continue
        if finding.get("severity") == "BLOCKER":
            blockers += 1
        elif finding.get("severity") == "MAJOR":
            majors += 1
    verdict = "REVISE" if blockers or majors else "APPROVE"
    return verdict, blockers, majors


def validate_review(
    review_path: Path,
    *,
    manifest_path: Path,
    lesson_path: Path | None = None,
    ledger_path: Path,
    previous_ledger_path: Path | None = None,
    document_path: Path | None = None,
    repo_root: Path | None = None,
) -> ValidationResult:
    """Validate one review file against its manifest, document, and receipt ledger.

    The document is the expanded lesson for a lesson review (``lesson_path`` and
    ``document_path`` are aliases). For a plan review whose manifest is a plan
    manifest it is the plan the manifest pins: ``document_path`` if given, else
    the plan at the manifest's ``inputs.plan.path`` under ``repo_root``.
    """
    check = _Check()
    review_path = Path(review_path)
    manifest_path = Path(manifest_path)
    document = document_path if document_path is not None else lesson_path
    ledger_path = Path(ledger_path)
    root = Path(repo_root) if repo_root is not None else REPO_ROOT

    manifest_hash = ""
    recap = False
    manifest: Any = None
    try:
        manifest_bytes = manifest_path.read_bytes()
        manifest_hash = hashlib.sha256(manifest_bytes).hexdigest()
        manifest = yaml.safe_load(manifest_bytes)
        if not isinstance(manifest, dict):
            check.add(codes.MANIFEST_UNREADABLE, f"{manifest_path} is not a YAML mapping")
        else:
            recap = manifest.get("recap") is True
    except (OSError, yaml.YAMLError) as exc:
        check.add(codes.MANIFEST_UNREADABLE, f"{manifest_path}: {type(exc).__name__}")

    plan_mode = _peek_kind(review_path) == "plan" and isinstance(manifest, dict) and manifest.get("kind") == "plan"
    units: list[dict[str, Any]] = []
    plan: dict[str, Any] | None = None
    if plan_mode:
        plan = _load_plan_document(check, manifest, manifest_hash, document, root)
    else:
        try:
            if document is None:
                raise ValueError("no expanded lesson was given")
            units = _units(_load_yaml(Path(document)))
        except (OSError, yaml.YAMLError, ValueError) as exc:
            check.add(codes.LESSON_UNREADABLE, f"{document}: {exc}")

    try:
        review = _load_yaml(review_path)
    except (OSError, yaml.YAMLError) as exc:
        check.add(codes.REVIEW_UNREADABLE, f"{review_path}: {type(exc).__name__}")
        return ValidationResult(False, None, check.rejections)
    if not isinstance(review, dict):
        check.add(codes.REVIEW_UNREADABLE, f"{review_path} is not a YAML mapping")
        return ValidationResult(False, None, check.rejections)

    for error in review_schema_errors(review):
        check.add(codes.SCHEMA_INVALID, error)

    if isinstance(manifest, dict) and "kind" in manifest and manifest["kind"] != review.get("kind"):
        check.add(
            codes.MANIFEST_KIND_MISMATCH,
            f"the review is kind {review.get('kind')!r} but its manifest is kind {manifest['kind']!r}",
        )

    attempt = review.get("attempt") if isinstance(review.get("attempt"), dict) else {}
    echoed = attempt.get("manifest_sha256")
    if manifest_hash and echoed != manifest_hash:
        check.add(codes.MANIFEST_HASH_MISMATCH, f"echoed {echoed} != manifest file {manifest_hash}")

    current: dict[str, dict[str, Any]] = {}
    try:
        current = index_ledger(ledger_path)
    except LedgerHashStaleLastLine as exc:
        check.add(codes.LEDGER_HASH_STALE_LAST_LINE, f"{ledger_path}: {exc}")
    except (LedgerError, json.JSONDecodeError, OSError) as exc:
        check.add(codes.LEDGER_UNREADABLE, f"{ledger_path}: {exc}")

    previous_attempt_id = attempt.get("previous_attempt_id")
    if not isinstance(previous_attempt_id, str):
        previous_attempt_id = None
    previous_path = previous_ledger_path
    if previous_path is None and previous_attempt_id:
        previous_path = ledger_path.parent / f"{previous_attempt_id}.jsonl"
    previous: dict[str, dict[str, Any]] | None = None
    if previous_attempt_id and previous_path is not None and Path(previous_path).exists():
        try:
            previous = index_ledger(Path(previous_path))
        except LedgerHashStaleLastLine as exc:
            check.add(codes.LEDGER_HASH_STALE_LAST_LINE, f"{previous_path}: {exc}")
        except (LedgerError, json.JSONDecodeError, OSError) as exc:
            check.add(codes.LEDGER_UNREADABLE, f"{previous_path}: {exc}")

    review_id = attempt.get("review_id") if isinstance(attempt.get("review_id"), str) else ""
    attempt_id = attempt.get("attempt_id") if isinstance(attempt.get("attempt_id"), str) else ""
    try:
        taxonomy = _taxonomy()
    except (OSError, yaml.YAMLError, ValueError) as exc:
        check.add(codes.SCHEMA_INVALID, f"taxonomy: {exc}")
        taxonomy = {}
    if taxonomy:
        _check_taxonomy(check, review, taxonomy, recap=recap)

    findings = review.get("findings") if isinstance(review.get("findings"), list) else []
    kind = review.get("kind") if isinstance(review.get("kind"), str) else ""
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        _check_locations(check, finding, units, kind=kind, plan=plan, plan_mode=plan_mode)
        _check_finding_evidence(
            check,
            finding,
            current=current,
            previous=previous,
            review_id=review_id,
            attempt_id=attempt_id,
            manifest_sha256=manifest_hash,
            previous_attempt_id=previous_attempt_id,
        )

    if not check.ok:
        return ValidationResult(False, None, check.rejections)
    verdict, blockers, majors = _verdict(findings)
    return ValidationResult(True, verdict, [], blockers, majors)


def _emit(result: ValidationResult, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(result.payload(), indent=2, sort_keys=True))
        return
    if result.ok:
        print(f"verdict: {result.verdict}")
        return
    print("rejected:")
    for item in result.rejections:
        print(f"  {item.code}: {item.message}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.review.validate",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Validate a review-v1 return against its attempt manifest, document,\n"
            "and receipt ledger, then print APPROVE or REVISE from active findings.\n"
            "The document is the expanded lesson for a lesson review, and the plan the\n"
            "manifest pins for a plan review. Use after a review seat returns review.yaml.\n"
            "Do NOT use to judge whether the evidence supports the claim or whether the\n"
            "severity is right, and do NOT use for v1 content-review output.\n\n"
            "Plan mode (review kind plan, manifest kind plan): the plan must hash to the\n"
            "manifest's inputs.plan.sha256; every manifest input must still be current (after\n"
            "plan-promote only the plan transition its receipt proves may differ); a location\n"
            "is {lesson, step or activity, field, quote} and the quote must occur inside that\n"
            "unit's text (its scalar values, one per line); an absence finding uses the scope\n"
            "{lesson, step or activity}. A review whose manifest is not a plan manifest has no\n"
            "pinned plan, so:\n"
            "Plan-review findings with locations are rejected (location_not_in_lesson)\n"
            "until a plan document locator is defined."
        ),
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.review.validate review.yaml \\\n"
            "    --manifest manifest.yaml --lesson lesson.expanded.yaml \\\n"
            "    --ledger batch_state/review-receipts/<review_id>/<attempt_id>.jsonl\n"
            "  .venv/bin/python -m scripts.review.validate review.yaml \\\n"
            "    --manifest plan-review.manifest.yaml --ledger attempt.jsonl   # a plan review\n"
            "  .venv/bin/python -m scripts.review.validate review.yaml \\\n"
            "    --manifest manifest.yaml --lesson lesson.expanded.yaml \\\n"
            "    --ledger attempt.jsonl --previous-ledger previous.jsonl --json\n"
            "\n"
            "Outputs: stdout only. --json prints verdict, ok, rejections, and the\n"
            "active BLOCKER and MAJOR counts. No files are written.\n"
            "Exit codes: 0 = the review is valid (verdict APPROVE or REVISE);\n"
            "1 = rejected; 2 = usage error.\n"
            "Related: schemas/review-v1.schema.json, schemas/review-taxonomy-v1.yaml,\n"
            "docs/epics/fresh-build-review-contracts.md, issues #8430 #8431.\n"
            "Outcome codes:\n" + codes.help_text()
        ),
    )
    parser.add_argument("review", type=Path, help="path to the reviewer's review.yaml (review_schema: 1)")
    parser.add_argument(
        "--manifest",
        type=Path,
        required=True,
        help="attempt manifest YAML; its file sha256 must equal attempt.manifest_sha256",
    )
    parser.add_argument(
        "--document",
        "--lesson",
        dest="document",
        type=Path,
        default=None,
        help="the document quotes are checked in: the expanded lesson YAML (units with tab, activity, item, "
        "text; required for a lesson review), or for a plan review the plan (default: the manifest's "
        "inputs.plan.path under --repo-root; its sha256 must equal inputs.plan.sha256). --lesson is an alias",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="repository root the plan manifest's paths are relative to (plan reviews only; default: this repository)",
    )
    parser.add_argument(
        "--ledger",
        type=Path,
        required=True,
        help="this attempt's receipt ledger JSONL (batch_state/review-receipts/<review_id>/<attempt_id>.jsonl)",
    )
    parser.add_argument(
        "--previous-ledger",
        type=Path,
        default=None,
        help="previous attempt ledger; default is the sibling <previous_attempt_id>.jsonl next to --ledger",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print the verdict and rejections as one JSON object (default: human text)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.document is None and _peek_kind(args.review) != "plan":
        parser.error("--document (alias --lesson) is required unless the review is a plan review")
    result = validate_review(
        args.review,
        manifest_path=args.manifest,
        document_path=args.document,
        ledger_path=args.ledger,
        previous_ledger_path=args.previous_ledger,
        repo_root=args.repo_root,
    )
    _emit(result, as_json=args.json)
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
