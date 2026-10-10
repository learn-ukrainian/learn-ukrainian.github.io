"""Prepare and record the one bounded settle attempt for an unsupported finding.

The language seat judges one finding the sources did not settle: a quoted construction
in its sense, or an absence (something the finding says is missing from a scoped unit
of the lesson or the plan). This module checks only identity, receipt provenance and
return shape. The prompt is rendered by ``scripts.review.prompts.render`` from this
task's own manifest, and the outcome is written through ``findings_db.record_settle_outcome``.
"""

from __future__ import annotations

import argparse
import functools
import hashlib
import json
import os
import re
import tempfile
from contextlib import closing
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from scripts.build.fresh.assemble import component_props_from_jsx
from scripts.build.fresh.path_guard import SLUG_RE
from scripts.curriculum.evidence.lock import atomic_write
from scripts.curriculum.validate.loader import read_plan_text
from scripts.review import findings_db as db
from scripts.review.prompts.eligibility import pin_refusals
from scripts.review.prompts.render import render_prompt
from scripts.review.receipts import ledger
from scripts.review.receipts.outcomes import classify_outcome
from scripts.review.validate.validate import _MISSING, _leaf_texts, _plan_unit

REPO_ROOT = Path(__file__).resolve().parents[2]
TREE = "curriculum/l2-uk-en"
TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
_TAB_ITEM = re.compile(r"<TabItem\b([^>]*)>(.*?)</TabItem>", re.DOTALL)
_TAB_LABEL = re.compile(r'\blabel="([^"]*)"')
_ACTIVITY_SPAN = re.compile(r'<span id="([^"]+)"></span>')
_ACTIVITY_HEADING = re.compile(r"(?m)^###[ \t]+([^\n]+?)\s*$")
_DASH = "\u2014"  # the em dash generate_mdx puts between a tab's Ukrainian and English labels
_NO_SCOPE = "finding has no quoted disputed span"
_ABSENT_UNIT = "scope names a unit absent from the document"
_AMBIGUOUS_UNIT = "scope names more than one unit in the document"


def _tab_by_label() -> dict[str, str]:
    """Engine tab labels (``scripts/generate_mdx/core.py``) to the review scope's ASCII key.

    A1 prints the Ukrainian label, an em dash, and the English label. A Ukrainian-only page
    prints the Ukrainian label, and the a2.2 workbook tab uses its own Ukrainian label.
    The ASCII key itself is accepted so a fixture can name the tab without a display label.
    """
    ukrainian = {
        "urok": "\u0423\u0440\u043e\u043a",
        "slovnyk": "\u0421\u043b\u043e\u0432\u043d\u0438\u043a",
        "vpravy": "\u0412\u043f\u0440\u0430\u0432\u0438",
        "resursy": "\u0420\u0435\u0441\u0443\u0440\u0441\u0438",
    }
    english = {"urok": "Lesson", "slovnyk": "Vocabulary", "vpravy": "Activities", "resursy": "Resources"}
    labels = {key: key for key in ukrainian}
    for key, uk in ukrainian.items():
        labels[english[key]] = key
        labels[uk] = key
        labels[f"{uk} {_DASH} {english[key]}"] = key
    workbook = "\u0417\u043e\u0448\u0438\u0442"
    labels[workbook] = "vpravy"
    labels[f"{workbook} {_DASH} Activities"] = "vpravy"
    return labels


_TAB_BY_LABEL = _tab_by_label()

# Distinct authorities, rather than distinct calls, are required for a conflict.
# Ambiguous signal tools have no authority here and cannot establish a conflict.
# slovnyk.me supplies dictionary evidence, ESUM etymology, and Grinchenko
# historical attestation. search_definitions supplies Sovietization context
# only; it must never settle meaning, norm or stress, or establish a conflict.
SOURCES = {
    "verify_word": "vesum",
    "verify_lemma": "vesum",
    "verify_words": "vesum",
    "inspect_word": "vesum",
    "inspect_words": "vesum",
    "verify_stress": "stress",
    "query_sum20": "sum20",
    "search_slovnyk_me": "slovnyk_me",
    "search_esum": "esum",
    "search_grinchenko_1907": "grinchenko",
    "query_ulif": "ulif",
    "query_pravopys": "pravopys",
    "search_style_guide": "style_guide",
    "search_text": "style_guide",
    "query_r2u": "r2u",
    "search_heritage": "heritage",
    "search_ua_gec_errors": "ua_gec",
    "query_grac": "grac",
    "query_cefr_level": "cefr",
}

# The categories name the steps of the accepted contract's "The settle step".
# A citation to a call from another category cannot stand in for the required search.
SEARCH_TOOLS = {
    "lemma": frozenset(
        {
            "verify_word",
            "verify_lemma",
            "verify_words",
            "inspect_word",
            "inspect_words",
            "query_sum20",
            "query_ulif",
            "query_r2u",
            "search_slovnyk_me",
            "search_esum",
            "search_grinchenko_1907",
        }
    ),
    "construction": frozenset({"search_text", "search_style_guide", "search_ua_gec_errors", "query_grac"}),
    "style_prose": frozenset({"search_text"}),
    "ua_gec_context": frozenset({"search_ua_gec_errors"}),
    "grac": frozenset({"query_grac"}),
    "pravopys": frozenset({"query_pravopys"}),
    "counterevidence": frozenset(SOURCES),
}


class SettleError(Exception):
    """A settle task or return failed its structural contract."""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _save_exclusive(path: Path, content: bytes) -> None:
    """Publish a complete reply without replacing another settle session's file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            os.fchmod(stream.fileno(), 0o600)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def _safe_path(path: Path, root: Path) -> str:
    resolved = path.resolve()
    if not resolved.is_file() or not resolved.is_relative_to(root.resolve()):
        raise SettleError("document must be an existing file within the repository")
    return resolved.relative_to(root.resolve()).as_posix()


def _item(conn: Any, item_id: int) -> Any:
    row = conn.execute("SELECT * FROM settle_items WHERE item_id = ?", (item_id,)).fetchone()
    if row is None or row["kind"] != "unsupported_by_source":
        raise SettleError(f"item {item_id} is not an unsupported_by_source settle item")
    if row["outcome"] is not None:
        raise db.SettleAlreadyDecided(f"settle item {item_id} is already decided")
    return row


def _original_finding(conn: Any, item: Any) -> dict[str, Any]:
    try:
        review_id, attempt_id, finding_id = item["finding_ref"].split("/", 2)
    except ValueError as exc:
        raise SettleError("item finding_ref is malformed") from exc
    row = conn.execute(
        "SELECT f.finding_json, a.manifest_sha256, a.kind, a.lesson_n FROM findings f"
        " JOIN attempts a ON a.review_id = f.review_id AND a.attempt_id = f.attempt_id"
        " WHERE f.review_id = ? AND f.attempt_id = ? AND f.finding_id = ?",
        (review_id, attempt_id, finding_id),
    ).fetchone()
    if row is None or row["manifest_sha256"] != item["manifest_sha256"]:
        raise SettleError("settle item does not match a recorded finding and manifest")
    finding = json.loads(row["finding_json"])
    if "unsupported_by_source" not in finding:
        raise SettleError("recorded finding has no unsupported_by_source branch")
    return finding


def _quoted_spans(document: str, finding: dict[str, Any]) -> list[dict[str, Any]]:
    spans: list[dict[str, Any]] = []
    locations = finding.get("locations", [])
    if not isinstance(locations, list):
        return spans
    for location in locations:
        quote = location.get("quote") if isinstance(location, dict) else None
        if not isinstance(quote, str) or not quote:
            continue
        positions = [match.start() for match in re.finditer(re.escape(quote), document)]
        if not positions:
            raise SettleError("a disputed quote is absent from the current document")
        for occurrence, position in enumerate(positions, start=1):
            start, end = max(0, position - 160), min(len(document), position + len(quote) + 160)
            spans.append(
                {
                    "quote": quote,
                    "context": document[start:end],
                    "location": json.dumps(location, ensure_ascii=False),
                    "occurrence": occurrence,
                }
            )
    return spans


def _is_lesson_scope(scope: Any) -> bool:
    """A lesson absence scope: a tab, optionally one activity inside that tab."""
    if not isinstance(scope, dict) or "tab" not in scope or set(scope) - {"tab", "activity"}:
        return False
    tab = scope.get("tab")
    if not isinstance(tab, str) or not tab:
        return False
    activity = scope.get("activity")
    return "activity" not in scope or (isinstance(activity, str) and bool(activity))


def _is_plan_scope(scope: Any) -> bool:
    """A plan absence scope: one lesson, optionally one step or one activity of it."""
    if not isinstance(scope, dict) or "lesson" not in scope or set(scope) - {"lesson", "step", "activity"}:
        return False
    if "step" in scope and "activity" in scope:
        return False
    lesson = scope["lesson"]
    if isinstance(lesson, bool) or not isinstance(lesson, int) or lesson < 1:
        return False
    return all(isinstance(scope[key], str) and scope[key] for key in ("step", "activity") if key in scope)


def _require_one(texts: list[str]) -> str:
    if not texts:
        raise SettleError(_ABSENT_UNIT)
    if len(texts) > 1:
        raise SettleError(_AMBIGUOUS_UNIT)
    return texts[0]


def _tab_bodies(document: str) -> dict[str, list[str]]:
    """Each tab key's inner text, in document order, exactly as it stands between the tags."""
    found: dict[str, list[str]] = {}
    for attrs, body in _TAB_ITEM.findall(document):
        label = _TAB_LABEL.search(attrs)
        if label is None:
            continue
        key = _TAB_BY_LABEL.get(label.group(1))
        if key is not None:
            found.setdefault(key, []).append(body)
    return found


def _activity_blocks(body: str) -> list[tuple[str | None, str | None, str]]:
    """Activity blocks in one tab: ``(span id, heading, exact slice)``.

    A block starts at an anchor ``<span id="..."></span>`` or, when that anchor does not
    own it, at a ``###`` heading. The anchor owns the heading that follows it with only
    whitespace between, which is how the page renderer writes an anchored activity.
    The slice runs up to the next block and no further.
    """
    spans = list(_ACTIVITY_SPAN.finditer(body))
    headings = list(_ACTIVITY_HEADING.finditer(body))
    owned: dict[int, re.Match[str]] = {}
    taken: set[int] = set()
    for index, span in enumerate(spans):
        following = spans[index + 1].start() if index + 1 < len(spans) else len(body)
        for heading in headings:
            if span.end() <= heading.start() < following and not body[span.end() : heading.start()].strip():
                owned[span.start()] = heading
                taken.add(heading.start())
                break
    starts: list[tuple[int, str | None, str | None]] = []
    for span in spans:
        heading = owned.get(span.start())
        starts.append((span.start(), span.group(1), heading.group(1).strip() if heading else None))
    starts.extend(
        (heading.start(), None, heading.group(1).strip()) for heading in headings if heading.start() not in taken
    )
    starts.sort(key=lambda item: item[0])
    blocks: list[tuple[str | None, str | None, str]] = []
    for index, (start, span_id, heading) in enumerate(starts):
        end = starts[index + 1][0] if index + 1 < len(starts) else len(body)
        blocks.append((span_id, heading, body[start:end]))
    return blocks


def _string_values(node: Any) -> set[str]:
    """Every string the page's component props hold, after the JSX escapes are decoded."""
    if isinstance(node, str):
        return {node}
    if isinstance(node, dict):
        return {text for value in node.values() for text in _string_values(value)}
    if isinstance(node, list):
        return {text for value in node for text in _string_values(value)}
    return set()


def _block_contains_units(block: str, units: list[str]) -> bool:
    """Whether this rendered activity block carries every provenance unit of the activity.

    A unit's text is the field the page component receives (check 9). It is compared with
    the decoded props, and with the block source for prose the component does not wrap.
    The heading is only the block boundary; it is never matched against the activity id.
    """
    decoded = _string_values(component_props_from_jsx(block))
    for unit in units:
        if unit in decoded or unit in block:
            continue
        escaped = json.dumps(unit, ensure_ascii=False)[1:-1]
        if escaped != unit and escaped in block:
            continue
        return False
    return True


def _activity_unit_texts(provenance: dict[str, Any], tab: str, activity: str) -> list[str]:
    """Rendered text of each provenance unit of this activity, spans concatenated in order.

    One activity id on more than one step is two units. That is the ambiguous-unit refusal,
    raised before any block is chosen.
    """
    spans = provenance.get("spans")
    if not isinstance(spans, list):
        raise SettleError("provenance file is not usable")
    owned = [
        span for span in spans if isinstance(span, dict) and span.get("tab") == tab and span.get("activity") == activity
    ]
    if not owned:
        raise SettleError(_ABSENT_UNIT)
    if len({span.get("step") for span in owned}) > 1:
        raise SettleError(_AMBIGUOUS_UNIT)
    groups: dict[tuple[Any, Any], list[dict[str, Any]]] = {}
    for span in owned:
        groups.setdefault((span.get("item"), span.get("block")), []).append(span)
    texts: list[str] = []
    for group in groups.values():
        group.sort(key=lambda span: span.get("span") if isinstance(span.get("span"), int) else 0)
        piece = "".join(str(span.get("text") or "") for span in group)
        if piece:
            texts.append(piece)
    if not texts:
        raise SettleError(_ABSENT_UNIT)
    return texts


def _lesson_unit(document: str, scope: dict[str, Any], provenance: dict[str, Any] | None) -> str:
    """One tab, or the one activity block inside it.

    An activity is the block whose rendered text carries that activity's provenance units.
    A ``<span id>`` equal to the activity id is the same block when the page has one; a
    heading whose text happens to equal the id is not an activity. Duplicate span ids,
    duplicate provenance steps, or two blocks that both carry the units are ambiguous.
    """
    body = _require_one(_tab_bodies(document).get(scope["tab"], []))
    activity = scope.get("activity")
    if not isinstance(activity, str):
        return body
    blocks = [text for span_id, _heading, text in _activity_blocks(body) if span_id == activity]
    if len(blocks) > 1:
        raise SettleError(_AMBIGUOUS_UNIT)
    if provenance is None:
        return _require_one(blocks)
    units = _activity_unit_texts(provenance, scope["tab"], activity)
    located = [text for _span_id, _heading, text in _activity_blocks(body) if _block_contains_units(text, units)]
    if len(located) > 1 or (len(located) == 1 and blocks and blocks[0] != located[0]):
        raise SettleError(_AMBIGUOUS_UNIT)
    if len(located) == 1:
        return located[0]
    raise SettleError(_ABSENT_UNIT)


def _plan_matches(items: Any, key: str, value: Any) -> list[Any]:
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict) and item.get(key) == value]


def _refuse_duplicate_plan_ids(plan: dict[str, Any], scope: dict[str, Any]) -> None:
    """Duplicate lesson, step or activity ids are ambiguous before the first match is used."""
    lessons = _plan_matches(plan.get("lessons"), "n", scope["lesson"])
    if len(lessons) > 1:
        raise SettleError(_AMBIGUOUS_UNIT)
    if len(lessons) != 1:
        return
    lesson = lessons[0]
    if "step" in scope and len(_plan_matches(lesson.get("steps"), "id", scope["step"])) > 1:
        raise SettleError(_AMBIGUOUS_UNIT)
    if "activity" in scope and len(_plan_matches(lesson.get("activities"), "id", scope["activity"])) > 1:
        raise SettleError(_AMBIGUOUS_UNIT)


def _plan_unit_text(document: str, scope: dict[str, Any]) -> str:
    """The plan unit's scalar values, one per line, the same text the review validator checks."""
    try:
        plan = yaml.safe_load(document)
    except yaml.YAMLError as exc:
        raise SettleError(_ABSENT_UNIT) from exc
    if not isinstance(plan, dict):
        raise SettleError(_ABSENT_UNIT)
    _refuse_duplicate_plan_ids(plan, scope)
    unit = _plan_unit(plan, scope)
    if unit is _MISSING:
        raise SettleError(_ABSENT_UNIT)
    return "\n".join(_leaf_texts(unit))


def _context(document: str, finding: dict[str, Any], provenance: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Quoted windows, or one absence context for a scope the document actually contains.

    A quoted location keeps the window around each occurrence. An absence finding has no
    quote: a lesson scope is one tab (or one activity block inside it), and a plan scope
    is one lesson, step or activity of the plan. Anything else fails closed. ``provenance``
    is the lesson's provenance document when the scope names an activity; plan scopes ignore it.
    """
    quoted = _quoted_spans(document, finding)
    if quoted:
        return quoted
    scope = finding.get("scope")
    if _is_lesson_scope(scope):
        text = _lesson_unit(document, scope, provenance)
    elif _is_plan_scope(scope):
        text = _plan_unit_text(document, scope)
    else:
        raise SettleError(_NO_SCOPE)
    return [{"absence": True, "locator": dict(scope), "context": text}]


@functools.cache
def _provenance_validator() -> Draft202012Validator:
    schema = json.loads((REPO_ROOT / "schemas" / "lesson-provenance-v1.schema.json").read_text(encoding="utf-8"))
    return Draft202012Validator(schema)


def _parse_provenance(data: bytes) -> dict[str, Any]:
    try:
        document = yaml.safe_load(data)
    except yaml.YAMLError as exc:
        raise SettleError("provenance file is not usable") from exc
    if not isinstance(document, dict):
        raise SettleError("provenance file is not usable")
    if any(_provenance_validator().iter_errors(document)):
        raise SettleError("provenance file does not conform to lesson-provenance-v1")
    return document


def _pin_file(root: Path, pin: dict[str, Any]) -> bytes:
    """Bytes of one manifest pin, refused unless the path stays in the repository and the sha256 matches."""
    path_text, recorded = pin.get("path"), pin.get("sha256")
    if not isinstance(path_text, str) or not isinstance(recorded, str):
        raise SettleError("lesson manifest pin is malformed")
    relative = Path(path_text)
    if relative.is_absolute() or ".." in relative.parts:
        raise SettleError("lesson manifest pin escapes the repository")
    full = (root / relative).resolve()
    if not full.is_file() or not full.is_relative_to(root.resolve()):
        raise SettleError("lesson manifest pin is not a file in the repository")
    data = full.read_bytes()
    if _sha(data) != recorded:
        raise SettleError("lesson manifest pin does not match the file")
    return data


def _lesson_manifest_bytes(root: Path, level: str, slug: str, lesson_n: int, digest: str) -> bytes | None:
    """The original lesson manifest, found by the hash the settle item recorded, or None when it is not on disk."""
    if not isinstance(digest, str) or not SLUG_RE.fullmatch(level) or not SLUG_RE.fullmatch(slug):
        return None
    state = root / TREE / "evidence" / level / "_state" / slug
    candidates = (
        state / "manifests" / f"lesson-{lesson_n}" / f"{digest}.yaml",
        state / f"lesson-{lesson_n}.manifest.yaml",
    )
    for path in candidates:
        try:
            data = path.read_bytes()
        except OSError:
            continue
        if _sha(data) == digest:
            return data
    return None


def _provenance_document(root: Path, level: str, slug: str, lesson_n: int, manifest_sha: str) -> dict[str, Any]:
    """Read this lesson's provenance only through its original manifest's exact pin."""
    raw = _lesson_manifest_bytes(root, level, slug, lesson_n, manifest_sha)
    if raw is None:
        raise SettleError("lesson_manifest_unavailable_for_activity_provenance")
    try:
        manifest = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise SettleError("lesson manifest is not usable") from exc
    if not isinstance(manifest, dict):
        raise SettleError("lesson manifest is not usable")
    inputs = manifest.get("inputs")
    pin = inputs.get("provenance") if isinstance(inputs, dict) else None
    if not isinstance(pin, dict):
        raise SettleError("lesson_manifest_missing_provenance_pin")
    expected = f"{TREE}/evidence/{level}/_state/{slug}/lesson-{lesson_n}.provenance.yaml"
    if pin.get("path") != expected:
        raise SettleError("lesson_manifest_provenance_path_mismatch")
    try:
        data = _pin_file(root, pin)
    except SettleError as exc:
        raise SettleError(f"lesson_manifest_provenance_pin_invalid: {exc}") from exc
    parsed = _parse_provenance(data)
    return _provenance_for_lesson(parsed, level, slug, lesson_n)


def _provenance_for_lesson(document: dict[str, Any], level: str, slug: str, lesson_n: int) -> dict[str, Any]:
    described = document.get("lesson")
    if (
        not isinstance(described, dict)
        or described.get("level") != level
        or described.get("slug") != slug
        or described.get("n") != lesson_n
    ):
        raise SettleError("provenance file is not this lesson's")
    return document


def _prior_searches(
    finding: dict[str, Any], prior_ledger: Path, review_id: str, attempt_id: str, manifest: str
) -> list[dict[str, Any]]:
    indexed = {entry["receipt_id"]: entry for entry in ledger.records(prior_ledger)}
    searches: list[dict[str, Any]] = []
    for search in finding["unsupported_by_source"]["searches"]:
        receipt = search["receipt"]
        entry = indexed.get(receipt)
        if entry is None or (entry.get("review_id"), entry.get("attempt_id"), entry.get("manifest_sha256")) != (
            review_id,
            attempt_id,
            manifest,
        ):
            raise SettleError(f"original search receipt {receipt} is not in the review attempt ledger")
        searches.append(
            {
                "receipt": receipt,
                "tool": entry["tool"],
                "arguments": entry["arguments"],
                "outcome": search["outcome"],
                "result": entry["result"],
            }
        )
    if not searches:
        raise SettleError("original finding has no recorded searches")
    return searches


def prepare(
    item_id: int,
    *,
    db_path: Path,
    document_path: Path,
    prior_ledger: Path,
    review_id: str,
    attempt_id: str,
    manifest_path: Path,
    prompt_path: Path,
    repo_root: Path = REPO_ROOT,
    parameters_path: Path | None = None,
) -> str:
    """Write the settle manifest and exact rendered prompt; return the prompt sha256."""
    if not TOKEN.fullmatch(review_id) or not TOKEN.fullmatch(attempt_id):
        raise SettleError("review_id and attempt_id must be ledger tokens")
    root = repo_root.resolve()
    with closing(db.connect(db_path)) as conn:
        item = _item(conn, item_id)
        expected = (
            f"{TREE}/lesson-plans/{item['level']}/{item['slug']}.yaml"
            if item["lesson_n"] is None
            else f"site/src/content/docs/{item['level']}/{item['slug']}/{item['lesson_n']}.mdx"
        )
        actual = _safe_path(document_path, root)
        if actual != expected:
            raise SettleError(f"document path is {actual}; expected {expected}")
        document_bytes = (
            read_plan_text(document_path).encode("utf-8")
            if item["lesson_n"] is None
            else document_path.read_bytes()
        )
        finding = _original_finding(conn, item)
        scope = finding.get("scope")
        provenance = None
        if item["lesson_n"] is not None and _is_lesson_scope(scope) and isinstance(scope.get("activity"), str):
            provenance = _provenance_document(
                root, item["level"], item["slug"], item["lesson_n"], item["manifest_sha256"]
            )
        spans = _context(document_bytes.decode("utf-8"), finding, provenance)
        source_review, source_attempt, _ = item["finding_ref"].split("/", 2)
        searches = _prior_searches(finding, prior_ledger, source_review, source_attempt, item["manifest_sha256"])
        manifest = {
            "kind": "settle",
            "settle_schema": 1,
            "item_id": item_id,
            "level": item["level"],
            "slug": item["slug"],
            "lesson": item["lesson_n"],
            "finding_ref": item["finding_ref"],
            "source_manifest_sha256": item["manifest_sha256"],
            "review_id": review_id,
            "attempt_id": attempt_id,
            "call_budget": db.load_parameters(parameters_path)["settle_call_budget"],
            "finding_text": yaml.safe_dump(finding, allow_unicode=True, sort_keys=False),
            "disputed_spans_text": yaml.safe_dump(spans, allow_unicode=True, sort_keys=False),
            "reviewer_searches_text": yaml.safe_dump(searches, allow_unicode=True, sort_keys=False),
            "inputs": {"document": {"path": actual, "sha256": _sha(document_bytes)}},
        }
    refusals = pin_refusals(manifest, root)
    if refusals:
        raise SettleError("; ".join(str(refusal) for refusal in refusals))
    data = yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False).encode("utf-8")
    atomic_write(manifest_path, data)
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".settle-prompt-", dir=prompt_path.parent) as temp_dir:
        temporary_prompt = Path(temp_dir) / prompt_path.name
        _, prompt_sha, _ = render_prompt(manifest_path, repo_root=root, output_path=temporary_prompt)
        for suffix in ("", ".sha256", ".files_read.json"):
            os.replace(Path(f"{temporary_prompt}{suffix}"), Path(f"{prompt_path}{suffix}"))
    return prompt_sha


class _UniqueLoader(yaml.SafeLoader):
    """Do not let a repeated YAML key silently replace an earlier outcome."""


def _unique_mapping(loader: _UniqueLoader, node: yaml.MappingNode) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if key in result:
            raise SettleError(f"duplicate reply key {key!r}")
        result[key] = loader.construct_object(value_node)
    return result


_UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _unique_mapping)


def _source(entry: dict[str, Any]) -> str | None:
    """The authority a hit receipt counts as, or None when the call names none.

    ``search_text`` stays ``style_guide`` in ``SOURCES`` (the authority table). Its label
    names the tool and the ``source_file`` argument, because that call searches textbooks
    and the style-guide prose through the same tool.
    """
    authority = SOURCES.get(entry.get("tool"))
    if authority == "style_guide" and entry.get("tool") == "search_text":
        source_file = entry.get("arguments", {}).get("source_file")
        return f"search_text:{source_file}" if isinstance(source_file, str) and source_file else None
    return authority


def validate_reply(reply_bytes: bytes, manifest_bytes: bytes, ledger_path: Path) -> tuple[str, list[str]]:
    """Validate structure only; never decide whether quoted evidence supports a claim."""
    manifest = yaml.safe_load(manifest_bytes)
    if manifest.get("kind") != "settle" or manifest.get("settle_schema") != 1:
        raise SettleError("not a settle manifest")
    try:
        reply = yaml.load(reply_bytes, Loader=_UniqueLoader)
    except yaml.YAMLError as exc:
        raise SettleError(f"invalid reply YAML: {exc}") from exc
    required = {
        "settle_schema",
        "item_id",
        "review_id",
        "attempt_id",
        "manifest_sha256",
        "outcome",
        "reason",
        "evidence",
        "broadened_searches",
    }
    if not isinstance(reply, dict) or set(reply) != required or reply.get("settle_schema") != 1:
        raise SettleError("reply must carry exactly the settle return fields and one outcome")
    if reply["outcome"] not in db.SEAT_OUTCOMES or not isinstance(reply["outcome"], str):
        raise SettleError("reply must name exactly one of the four settle outcomes")
    if (reply["item_id"], reply["review_id"], reply["attempt_id"], reply["manifest_sha256"]) != (
        manifest["item_id"],
        manifest["review_id"],
        manifest["attempt_id"],
        _sha(manifest_bytes),
    ):
        raise SettleError("reply identity does not match this settle attempt manifest")
    if not isinstance(reply["reason"], str) or not reply["reason"].strip():
        raise SettleError("settle seat must state its judgment")
    records = ledger.records(ledger_path)
    if len(records) > manifest["call_budget"]:
        raise SettleError(f"settle call budget exceeded: {len(records)} > {manifest['call_budget']}")
    indexed: dict[str, dict[str, Any]] = {}
    for record in records:
        if (record.get("review_id"), record.get("attempt_id"), record.get("manifest_sha256")) != (
            manifest["review_id"],
            manifest["attempt_id"],
            _sha(manifest_bytes),
        ):
            raise SettleError("ledger contains a call from another settle attempt")
        indexed[record["receipt_id"]] = record

    def citation(value: Any) -> tuple[str, dict[str, Any]]:
        if not isinstance(value, dict) or set(value) != {"receipt", "quote"}:
            raise SettleError("each citation needs a receipt and quoted receipt text")
        receipt, quote = value["receipt"], value["quote"]
        if not isinstance(receipt, str) or receipt not in indexed:
            raise SettleError(f"receipt {receipt!r} is outside this settle attempt ledger")
        record = indexed[receipt]
        if not isinstance(quote, str) or not quote.strip() or quote not in record["result"]:
            raise SettleError("cited quote is not in the stored receipt result")
        return receipt, record

    if not isinstance(reply["evidence"], list) or not isinstance(reply["broadened_searches"], list):
        raise SettleError("evidence and broadened_searches must be lists")
    evidence = [citation(value) for value in reply["evidence"]]
    searches: dict[str, str] = {}
    for value in reply["broadened_searches"]:
        if not isinstance(value, dict) or set(value) != {"category", "receipt", "quote"}:
            raise SettleError("each broadened search needs category, receipt and quote")
        category = value["category"]
        if category not in SEARCH_TOOLS or category in searches:
            raise SettleError("unknown or repeated broadened search category")
        receipt, record = citation({"receipt": value["receipt"], "quote": value["quote"]})
        if receipt in searches.values() or record["tool"] not in SEARCH_TOOLS[category]:
            raise SettleError("broadened search receipt is duplicated or uses the wrong tool")
        if category == "style_prose" and record.get("arguments", {}).get("source_file") != (
            "antonenko-davydovych-yak-my-hovorymo"
        ):
            raise SettleError("style prose search must name the contract's source_file")
        facts = classify_outcome(record["tool"], record["status"], record["result"])
        if facts["status"] not in {"no_hits", "hits_found"}:
            raise SettleError(f"broadened_search_call_unsuccessful: {category}: {facts['status']}")
        searches[category] = receipt
    outcome = reply["outcome"]
    if outcome in {"supported_defect", "refuted"} and not any(
        record.get("status") == "ok"
        and record.get("tool") != "search_definitions"
        and record.get("outcome_facts", {}).get("hits", 0) > 0
        for _, record in evidence
    ):
        raise SettleError(f"{outcome} needs a cited receipt with hits")
    if outcome == "source_conflict":
        sources = {
            _source(record)
            for _, record in evidence
            if record.get("status") == "ok" and record.get("outcome_facts", {}).get("hits", 0) > 0
        }
        sources.discard(None)
        if len(sources) < 2:
            raise SettleError("source_conflict needs hit receipts from two different sources")
    if outcome == "unresolved" and set(searches) != set(SEARCH_TOOLS):
        raise SettleError("unresolved must cite every required broadened search and counterevidence")
    return outcome, list(dict.fromkeys([*(receipt for receipt, _ in evidence), *searches.values()]))


def record(
    reply_path: Path,
    *,
    manifest_path: Path,
    ledger_path: Path,
    db_path: Path,
    decided_by: str,
    repo_root: Path = REPO_ROOT,
) -> str:
    """Record a validated reply once and preserve its exact bytes beside the module state."""
    if not TOKEN.fullmatch(decided_by):
        raise SettleError("decided_by must be a dispatch seat token")
    manifest_bytes = manifest_path.read_bytes()
    manifest = yaml.safe_load(manifest_bytes)
    with closing(db.connect(db_path)) as conn:
        item = _item(conn, manifest["item_id"])
        if (item["level"], item["slug"], item["lesson_n"], item["finding_ref"], item["manifest_sha256"]) != (
            manifest["level"],
            manifest["slug"],
            manifest["lesson"],
            manifest["finding_ref"],
            manifest["source_manifest_sha256"],
        ):
            raise SettleError("manifest does not match the open settle item")
        refusals = pin_refusals(manifest, repo_root)
        if refusals:
            raise SettleError("; ".join(str(refusal) for refusal in refusals))
        pin = manifest["inputs"]["document"]
        if _sha((repo_root / pin["path"]).read_bytes()) != pin["sha256"]:
            raise SettleError("disputed document changed since settle manifest")
        reply_bytes = reply_path.read_bytes()
        outcome, receipts = validate_reply(reply_bytes, manifest_bytes, ledger_path)
        state = repo_root / TREE / "evidence" / item["level"] / "_state" / item["slug"]
        saved = state / f"settle-{item['item_id']}.reply.yaml"
        created = True
        try:
            _save_exclusive(saved, reply_bytes)
        except FileExistsError as exc:
            # A prior run, or a competing recorder racing this one, may have saved this exact reply
            # already (the item's outcome is still NULL, per the ``_item`` check above): that retry is
            # the same reply arriving again, not a second attempt, and must be let through to record().
            created = False
            if saved.read_bytes() != reply_bytes:
                raise SettleError(
                    f"settle item {item['item_id']}: a different reply is already saved; no second attempt"
                ) from exc
        try:
            db.record_settle_outcome(conn, item["item_id"], outcome, receipts, decided_by)
        except db.SettleAlreadyDecided:
            # Another recorder decided this item before this call's own write reached the
            # database — whether that recorder created ``saved`` or found it already there with
            # identical bytes, the file is the reply of record (or byte-identical to it) either
            # way. Never unlink it here, regardless of whether this call is the one that created
            # it: doing so on ``created`` alone deletes the winner's saved reply out from under it
            # when this call happened to be the one that raced ahead of the winner to the
            # filesystem but lost the database race (#8774 r7).
            raise
        except BaseException:
            # A genuine failure with no outcome recorded for this item at all: only the call that
            # created ``saved`` cleans it up.
            if created:
                saved.unlink()
            raise
        return outcome


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Prepare one sourced settle task or record its validated reply.\nUse after record opens an unsupported_by_source item; never retry a decided item.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  /home/ops/learn-ukrainian/.venv/bin/python -m scripts.review.settle prepare 1 --db batch_state/review-findings/a1.sqlite --document site/src/content/docs/a1/module/2.mdx --prior-ledger batch_state/review-receipts/R/A.jsonl --review-id settle-R --attempt-id A1 --manifest settle.manifest.yaml --prompt settle.prompt.md\n"
            "  /home/ops/learn-ukrainian/.venv/bin/python -m scripts.review.settle record reply.yaml --db batch_state/review-findings/a1.sqlite --manifest settle.manifest.yaml --ledger settle.jsonl --decided-by language-seat\n"
            "Outputs: prepare writes a manifest, prompt and render sidecars; record writes a saved reply and updates settle_items.\n"
            "Exit codes: 0 accepted; 1 malformed task, reply or filesystem error.\n"
            "Related: scripts/review/prompts/settle.md.j2; docs/epics/fresh-build-review-contracts.md The settle step."
        ),
    )
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT, help="Repository root (default: this checkout)")
    sub = parser.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare", help="Write one settle manifest and rendered prompt")
    prep.add_argument("item_id", type=int, help="Open settle_items.item_id")
    prep.add_argument("--db", type=Path, required=True, help="Findings SQLite database for the item's level")
    prep.add_argument("--document", type=Path, required=True, help="Current plan YAML or lesson MDX in this module")
    prep.add_argument("--prior-ledger", type=Path, required=True, help="Original review attempt's receipt JSONL")
    prep.add_argument("--review-id", required=True, help="New settle review id (ledger token)")
    prep.add_argument("--attempt-id", required=True, help="New settle attempt id (ledger token)")
    prep.add_argument("--manifest", type=Path, required=True, help="Output settle manifest YAML")
    prep.add_argument("--prompt", type=Path, required=True, help="Output rendered settle prompt Markdown")
    rec = sub.add_parser("record", help="Validate and record the sole settle outcome")
    rec.add_argument("reply", type=Path, help="Seat's YAML reply")
    rec.add_argument("--db", type=Path, required=True, help="Findings SQLite database for the item's level")
    rec.add_argument("--manifest", type=Path, required=True, help="Exact settle manifest YAML")
    rec.add_argument("--ledger", type=Path, required=True, help="This settle attempt's receipt JSONL")
    rec.add_argument("--decided-by", required=True, help="Trusted dispatch seat identifier")
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            digest = prepare(
                args.item_id,
                db_path=args.db,
                document_path=args.document,
                prior_ledger=args.prior_ledger,
                review_id=args.review_id,
                attempt_id=args.attempt_id,
                manifest_path=args.manifest,
                prompt_path=args.prompt,
                repo_root=args.repo_root,
            )
            print(f"prompt_sha256: {digest}")
        else:
            outcome = record(
                args.reply,
                manifest_path=args.manifest,
                ledger_path=args.ledger,
                db_path=args.db,
                decided_by=args.decided_by,
                repo_root=args.repo_root,
            )
            print(f"outcome: {outcome}")
        return 0
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        yaml.YAMLError,
        db.FindingsDbError,
        ledger.LedgerError,
        SettleError,
    ) as exc:
        parser.exit(1, f"settle: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
