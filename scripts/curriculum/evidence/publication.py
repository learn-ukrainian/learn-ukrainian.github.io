"""Publication rights from the existing textbook acquisition registry.

Pack provenance and inline ``publish`` claims never grant permission. Grounding
records remain usable without a right; only publication as a quote needs one.
"""

import argparse
import hashlib
import json
import re
import subprocess
import unicodedata
from collections import defaultdict
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from . import codes

REGISTRY_PATH = Path(__file__).resolve().parents[3] / "docs/l2-uk-direct/textbook-selection.yaml"
NAMED_EXCERPTS = frozenset(
    [
        *(f"ulp-{i}-00-lesson-notes" for i in range(1, 7)),
        "owned-oho-a1-workbook",
        "owned-oho-a1-transcripts",
        "owned-ulp-charts",
        "owned-fmu-1-premium",
        "owned-yak-inozemtsi-kozaka-riatuvaly",
    ]
)
REPO_ROOT = Path(__file__).resolve().parents[3]
OWNED_RIGHTS_PATH = Path(__file__).resolve().parents[3] / "registry/sources/owned-rights.yaml"


class _UniqueRightsLoader(yaml.SafeLoader):
    """A duplicate key must never withdraw a protected identity silently."""

    def construct_mapping(self, node, deep=False):
        keys = [self.construct_object(key, deep=deep) for key, _ in node.value]
        if len(set(keys)) != len(keys):
            raise ValueError("duplicate rights key")
        return super().construct_mapping(node, deep=deep)


def load_owned_rights() -> dict[str, dict]:
    """Read the mandatory rights overlay, including on injected-registry calls.

    No cache: withdrawals and malformed revisions are effective on the next
    publication check. Only the eleven #10106 identities may carry the named excerpt exception.
    """
    try:
        document = yaml.load(OWNED_RIGHTS_PATH.read_text(encoding="utf-8"), Loader=_UniqueRightsLoader)
        entries = document.get("sources") if isinstance(document, dict) else None
        if (
            type(document.get("schema")) is not int
            or document["schema"] != 1
            or not isinstance(entries, dict)
            or not entries
        ):
            raise ValueError("invalid rights document")
        for slug, entry in entries.items():
            if (
                not isinstance(slug, str)
                or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug)
                or not isinstance(entry, dict)
                or entry.get("rights") not in {"owned_cite_only", "private_permission"}
                or set(entry) - {"rights", "title", "author", "short_excerpts"}
                or (entry["rights"] == "private_permission" and set(entry) != {"rights"})
                or (
                    "short_excerpts" in entry
                    and (
                        entry["short_excerpts"] is not True
                        or slug not in NAMED_EXCERPTS
                        or entry["rights"] != "owned_cite_only"
                    )
                )
                or ("title" in entry and (not isinstance(entry["title"], str) or not entry["title"].strip()))
                or ("author" in entry and not isinstance(entry["author"], str))
            ):
                raise ValueError("invalid rights entry")
        return entries
    except (OSError, ValueError, TypeError, AttributeError, yaml.YAMLError):
        raise ValueError(f"{codes.OWNED_RIGHTS_UNREADABLE}: cannot validate owned rights") from None


def _owned_entry(record: dict, *, quote: bool = False) -> dict | None:
    """Resolve non-overridable denials before any textbook-selection grant."""
    entry = load_owned_rights().get((record.get("source") or {}).get("file"))
    if entry is not None:
        if quote and not (
            entry.get("short_excerpts") is True and (record.get("source") or {}).get("file") in NAMED_EXCERPTS
        ):
            raise ValueError(f"{codes.OWNED_QUOTE_REFUSED}: owned text is reference only")
        if entry["rights"] == "private_permission":
            raise ValueError(f"{codes.PRIVATE_CITATION_REFUSED}: private reference cannot be cited")
    return entry


@lru_cache(maxsize=8)
def _parse_registry(path: Path, fingerprint: tuple[int, int, int]) -> dict[str, Any]:
    """Parse once per file revision; the stat fingerprint invalidates withdrawals."""
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, yaml.YAMLError):
        raise ValueError(f"{codes.PUBLICATION_REGISTRY_UNREADABLE}: cannot parse source registry") from None
    entries = document.get("sources") if isinstance(document, dict) else None
    if not isinstance(entries, dict) or any(not isinstance(entry, dict) for entry in entries.values()):
        raise ValueError(f"{codes.PUBLICATION_REGISTRY_UNREADABLE}: invalid sources mapping")
    return entries


def load_registry(path: Path | None = None) -> dict[str, Any]:
    """Load cached exact keys, preserving typed errors and isolating caller mutations."""
    path = path or REGISTRY_PATH
    try:
        stat = path.stat()
    except OSError:
        raise ValueError(f"{codes.PUBLICATION_REGISTRY_UNREADABLE}: cannot read source registry") from None
    return deepcopy(_parse_registry(path, (stat.st_mtime_ns, stat.st_ctime_ns, stat.st_size)))


def source_attribution(record: dict, registry: dict | None = None) -> str:
    """One strict Ukrainian textbook citation, required for printed quotes.

    Metadata is registry-owned. This formats a citation, never grants quote rights.
    Grade ranges keep two positive integer endpoints rather than a string grade.
    """
    _owned_entry(record)
    entries = load_registry() if registry is None else registry
    source = record.get("source") or {}
    entry = entries.get(source.get("file"))
    try:
        if (
            not isinstance(entry, dict)
            or entry.get("file") != source.get("file")
            or entry.get("kind") != source.get("kind")
        ):
            raise ValueError("unregistered source")
        author, title = entry.get("author"), entry.get("title")
        provenance = entry.get("title_provenance")
        if (
            not isinstance(author, str)
            or not author.strip()
            or not isinstance(title, str)
            or not title.strip()
            or re.search(r"[A-Za-z]", title + author)
            or title == source.get("file")
            or not isinstance(provenance, dict)
            or not (provenance.get("url") or provenance.get("chunk_id"))
        ):
            raise ValueError("unconfirmed bibliography")
        grade, year, page = entry.get("grade"), entry.get("year"), source.get("page")
        if any(type(value) is not int or value < 1 for value in (grade, year, page)):
            raise ValueError("invalid grade, year or page")
        grade_end, part = entry.get("grade_end"), entry.get("part")
        if grade_end is not None and (type(grade_end) is not int or grade_end < grade):
            raise ValueError("invalid grade range")
        if part is not None and (type(part) is not int or part < 1):
            raise ValueError("invalid part")
        grades = f"{grade}–{grade_end}" if grade_end is not None else str(grade)
        part_label = f", ч. {part}" if part is not None else ""
        return f"{author}, «{title}», {grades} клас{part_label}, {year}, с. {page}"
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"{codes.PUBLICATION_ATTRIBUTION}: {record.get('id')} incomplete source attribution") from exc


def resource_citation(record: dict, registry: dict | None = None) -> dict[str, str] | None:
    """Return registry-owned resource metadata without requiring quote permission.

    Sources without citable metadata are omitted; registry read failures still
    propagate. A credit never admits the record's quote or supports text.
    """
    owned = _owned_entry(record)
    entries = load_registry() if registry is None else registry
    source = record.get("source") or {}
    entry = entries.get(source.get("file"))
    if isinstance(entry, dict) and entry.get("file") == source.get("file") and entry.get("kind") == source.get("kind"):
        credit = entry.get("resource_credit")
        if isinstance(credit, dict):
            title, url = credit.get("title"), credit.get("url")
            if isinstance(title, str) and title.strip() and isinstance(url, str) and url.startswith("https://"):
                episode = (
                    record.get("episode_url") or record.get("url") or source.get("episode_url") or source.get("url")
                )
                description = ""
                if (
                    credit.get("episode_links")
                    and isinstance(episode, str)
                    and re.fullmatch(r"https://www\.ukrainianlessons\.com/[^\s<>\[\]()]*", episode)
                ):
                    description = f"<{episode}>"
                return {"title": title, "url": url, "description": description}
        if owned is not None and source.get("file") in NAMED_EXCERPTS and "resource_credit" not in entry:
            try:
                return {"title": owned_attribution(entry), "url": entry["public_link"]["url"], "description": ""}
            except ValueError:
                return None
    if owned is not None and entry is None and source.get("kind") == "textbook":
        # Registry-owned bibliography only; pack text and private locators can
        # never supply a title. Owned books need no school-grade attribution.
        title = owned.get("title", "Owned reference")
        if owned.get("author"):
            title = f"{owned['author']}, «{title}»"
        return {"title": title, "url": "", "description": ""}
    try:
        return {
            "title": source_attribution(record, entries),
            "url": "",
            "description": "",
        }
    except ValueError:
        return None


def quote_attribution(record: dict, registry: dict | None = None) -> str:
    """Validate one excerpt and return its required, source-bound attribution.

    limit_chars measures the original excerpt's Unicode characters, before
    normalization or stress annotation. No truncation or pack-provided policy.
    """
    _owned_entry(record, quote=True)
    entries = load_registry() if registry is None else registry
    source = record.get("source") or {}
    entry = entries.get(source.get("file"))
    right = entry.get("publish") if isinstance(entry, dict) else None
    if (
        not isinstance(right, dict)
        or right.get("allowed") is not True
        or entry.get("kind") != source.get("kind")
        or entry.get("file") != source.get("file")
    ):
        raise ValueError(f"{codes.PUBLICATION_RIGHT}: {record.get('id')} source has no publication right")
    limit = right.get("limit_chars")
    quote = record.get("quote")
    if type(limit) is not int or limit < 1 or not isinstance(quote, str) or not quote:
        raise ValueError(f"{codes.PUBLICATION_RIGHT}: {record.get('id')} invalid excerpt or publication limit")
    if source.get("file") in NAMED_EXCERPTS:
        validate_owned_policy(source.get("file"), entry)
        size = nfc_chars(quote)
        if size > 200:
            raise ValueError(f"{codes.PUBLICATION_LIMIT}: owned excerpt exceeds 200 characters")
        return owned_attribution(entry)
    if len(quote) > limit:
        raise ValueError(
            f"{codes.PUBLICATION_LIMIT}: {record.get('id')} excerpt has {len(quote)} characters; limit {limit}"
        )
    if right.get("attribution") != "ukrainian-short":
        raise ValueError(f"{codes.PUBLICATION_ATTRIBUTION}: {record.get('id')} unsupported attribution format")
    return source_attribution(record, entries)


def quoted_records(plan: dict) -> dict[str, str]:
    """Map planned quote refs to step ids; explains-only citations are grounding."""
    refs = {}
    for lesson in plan.get("lessons", [plan]):
        for step in lesson.get("steps", []):
            if "quote" in (step.get("needs") or []):
                citations = [*(step.get("evidence") or []), *(step.get("explains") or [])]
                if step.get("ref"):
                    citations.append(step["ref"])
                refs.update({ref: step.get("id", "") for ref in citations if ref.startswith("T-")})
    return refs


def nfc_chars(text: str) -> int:
    """Original code points, including whitespace, before adding stress."""
    return len(unicodedata.normalize("NFC", text))


def validate_owned_policy(file: str, entry: dict, api=None) -> dict:
    """Only registry-owned, internally consistent canonical metadata is a denominator."""
    if not isinstance(entry, dict) or not isinstance(entry.get("canonical"), dict):
        raise ValueError(f"{codes.PUBLICATION_SCOPE_INCOMPLETE}: canonical metadata missing")
    right = entry.get("publish") or {}
    metadata = entry.get("canonical") or {}
    units = metadata.get("units") or {}
    if not isinstance(units, dict):
        raise ValueError(f"{codes.PUBLICATION_SCOPE_INCOMPLETE}: invalid canonical units")
    if (
        file not in NAMED_EXCERPTS
        or entry.get("file") != file
        or entry.get("kind") != "textbook"
        or right
        != {
            "allowed": True,
            "limit_chars": 200,
            "attribution": "owned-short",
            "source_lesson_uses": 2,
            "source_lesson_chars": 300,
            "lesson_uses": 3,
            "lesson_chars": 500,
            "course_chars": 2000,
            "course_divisor": 100,
            "unit_chars": 300,
            "unit_divisor": 10,
        }
        or type(metadata.get("canonical_chars")) is not int
        or type(metadata.get("unit_count")) is not int
        or not units
        or metadata["unit_count"] != len(units)
        or any(
            not isinstance(unit, dict)
            or type(unit.get("chars")) is not int
            or unit["chars"] < 1
            or not isinstance(unit.get("number"), str)
            or not isinstance(unit.get("sha256"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", unit["sha256"])
            for unit in units.values()
        )
        or metadata["canonical_chars"] != sum(unit["chars"] for unit in units.values())
        or len({unit["number"] for unit in units.values()}) != len(units)
    ):
        raise ValueError(f"{codes.PUBLICATION_SCOPE_INCOMPLETE}: invalid canonical publication policy")
    if api is not None and api.publication_metadata(file) != metadata:
        raise ValueError(f"{codes.PUBLICATION_DENOMINATOR_DRIFT}: {file} canonical sections changed")
    return metadata


def owned_attribution(entry: dict) -> str:
    """Required bibliography comes only from the registry, never pack prose."""
    author, title, link = entry.get("author"), entry.get("title"), entry.get("public_link")
    if (
        not all(isinstance(item, str) and item.strip() for item in (author, title))
        or not isinstance(link, dict)
        or not isinstance(link.get("url"), str)
        or not re.fullmatch(r"https://www\.ukrainianlessons\.com/[^\s<>\[\]()]*", link["url"])
        or link.get("http_status") != 200
        or not isinstance(link.get("verified_on"), str)
        or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", link["verified_on"])
    ):
        raise ValueError(f"{codes.PUBLICATION_SCOPE_INCOMPLETE}: required excerpt attribution missing")
    return f"{author}, «{title}»"


def excerpt_record(record: dict) -> dict:
    """Examples and quotes use identical rights and character accounting."""
    return {**record, "quote": record.get("quote", record.get("text"))}


def publication_unit(record: dict, entry: dict, api=None) -> str:
    """Exact parent section, or ULP lesson-number fallback; never a window denominator."""
    source = record.get("source") or {}
    file, chunk_id = source.get("file"), source.get("chunk_id")
    if not isinstance(chunk_id, str) or not chunk_id.startswith(str(file) + "_"):
        raise ValueError(f"{codes.PUBLICATION_SCOPE_INCOMPLETE}: chunk belongs to another source")
    metadata = validate_owned_policy(file, entry)
    units = metadata["units"]
    section_id = source.get("parent_section_id")
    if section_id is None:
        section_id = source.get("section_id")
    chunk = None
    if api is not None:
        chunk = api.get_textbook_chunk(chunk_id)
        if chunk is None or chunk.get("source_file") != file:
            raise ValueError(f"{codes.PUBLICATION_SCOPE_INCOMPLETE}: cited source identity unresolved")
        parent = chunk.get("parent_section_id")
        if parent is not None:
            if section_id is not None and str(section_id) != str(parent):
                raise ValueError(f"{codes.PUBLICATION_SCOPE_INCOMPLETE}: cited parent differs")
            section_id = parent
        elif section_id is not None:
            raise ValueError(f"{codes.PUBLICATION_SCOPE_INCOMPLETE}: forged parent section")
    if section_id is None:
        match = re.fullmatch(re.escape(file) + r"_l(\d{4})_w\d+", chunk_id or "")
        candidates = [key for key, unit in units.items() if match and unit["number"] == str(int(match[1]))]
        if len(candidates) != 1:
            raise ValueError(f"{codes.PUBLICATION_SCOPE_INCOMPLETE}: no canonical unit mapping")
        section_id = candidates[0]
    key = str(section_id)
    if key not in units:
        raise ValueError(f"{codes.PUBLICATION_SCOPE_INCOMPLETE}: unit outside exact source")
    quote = excerpt_record(record).get("quote")
    if not isinstance(quote, str) or not quote.strip():
        raise ValueError(f"{codes.PUBLICATION_SCOPE_INCOMPLETE}: empty excerpt")
    if api is not None:
        section = next((row for row in api.publication_sections(file) if str(row["section_id"]) == key), None)

        def normalized(text):
            return " ".join(unicodedata.normalize("NFC", text).split())

        if section is None or normalized(quote) not in normalized(section["full_text"]):
            raise ValueError(f"{codes.QUOTE_MISMATCH}: excerpt absent from canonical section")
        if chunk is None or normalized(quote) not in normalized(chunk["text"]):
            raise ValueError(f"{codes.QUOTE_MISMATCH}: excerpt absent from cited chunk")
    return key


def excerpt_occurrences(plan: dict, pack: dict, *, level="unknown", module="unknown", draft=None) -> list[dict]:
    """Preserve lesson/step/ref uses while deduplicating generated representations."""
    from scripts.curriculum.validate.quote_bytes import quote_host_refs

    records = {row["id"]: row for group in ("texts", "examples") for row in (pack or {}).get(group, [])}
    result = {}
    for index, lesson in enumerate(plan.get("lessons", [plan]), 1):
        lesson_id = lesson.get("n", index)
        steps = draft.get("steps", []) if draft is not None else lesson.get("steps", [])
        for step in steps:
            refs = []
            repeats = defaultdict(int)
            if draft is not None:
                refs += [
                    block.get("ref") for block in step.get("blocks", []) if block.get("kind") in {"quote", "example"}
                ]
            else:
                citations = [*(step.get("evidence") or []), *(step.get("explains") or []), step.get("ref")]
                refs += [
                    ref
                    for ref in citations
                    if isinstance(ref, str)
                    and (
                        ("quote" in (step.get("needs") or []) and ref.startswith("T-"))
                        or ("example" in (step.get("needs") or []) and ref.startswith("EX-"))
                    )
                ]
            for ref in refs:
                if ref not in records:
                    raise ValueError(f"{codes.PUBLICATION_SCOPE_INCOMPLETE}: printed record missing")
                rec = records[ref]
                if (rec.get("source") or {}).get("file") not in NAMED_EXCERPTS:
                    continue
                key = ("l2-uk-en", level, module, lesson_id, step.get("id"), ref)
                if draft is not None:
                    repeats[ref] += 1
                    if repeats[ref] > 1:
                        key += (repeats[ref],)
                if not key[4]:
                    raise ValueError(f"{codes.PUBLICATION_SCOPE_INCOMPLETE}: occurrence step missing")
                result[key] = {"key": key, "record": excerpt_record(rec), "column": "lesson"}
        for activity in lesson.get("activities", []):
            hosts = [
                ref
                for ref in quote_host_refs(activity.get("focus") or "")
                if ref not in records or (records[ref].get("source") or {}).get("file") in NAMED_EXCERPTS
            ]
            host_steps = [
                step.get("id") for step in lesson.get("steps", []) if activity.get("id") in (step.get("practice") or [])
            ]
            if hosts and not host_steps:
                raise ValueError(f"{codes.PUBLICATION_SCOPE_INCOMPLETE}: activity host step missing")
            for step_id in host_steps:
                for ref in hosts:
                    if ref not in records:
                        raise ValueError(f"{codes.PUBLICATION_SCOPE_INCOMPLETE}: activity quote missing")
                    if (records[ref].get("source") or {}).get("file") in NAMED_EXCERPTS:
                        key = ("l2-uk-en", level, module, lesson_id, step_id, ref)
                        result[key] = {"key": key, "record": excerpt_record(records[ref]), "column": "lesson"}
    return list(result.values())


def check_occurrences(occurrences: list[dict], registry: dict | None = None, *, api=None) -> dict:
    """Pure shared lesson/course/unit accounting. Every distinct use consumes its full length."""
    registry = load_registry() if registry is None else registry
    totals = {file: {"lesson": 0, "site_data": 0, "occurrences": 0, "units": {}} for file in NAMED_EXCERPTS}
    lesson_totals, source_lessons, seen, errors = defaultdict(list), defaultdict(list), {}, []
    for occurrence in occurrences:
        key = tuple(occurrence["key"])
        rec = excerpt_record(occurrence["record"])
        if key in seen:
            if seen[key] != rec:
                errors.append(f"{codes.PUBLICATION_SCOPE_INCOMPLETE}: conflicting generated occurrence")
            continue
        seen[key] = rec
        file = (rec.get("source") or {}).get("file")
        if file not in NAMED_EXCERPTS:
            errors.append(f"{codes.PUBLICATION_SCOPE_INCOMPLETE}: unregistered excerpt identity")
            continue
        size = nfc_chars(rec.get("quote") or "")
        totals[file][occurrence.get("column", "lesson")] += size
        totals[file]["occurrences"] += 1
        if occurrence.get("column", "lesson") == "lesson":
            lesson_totals[key[:4]].append(size)
            source_lessons[(key[:4], file)].append(size)
        try:
            quote_attribution(rec, registry)
            unit = publication_unit(rec, registry[file], api)
            totals[file]["units"][unit] = totals[file]["units"].get(unit, 0) + size
        except (ValueError, KeyError) as exc:
            errors.append(
                str(exc)
                if isinstance(exc, ValueError)
                else f"{codes.PUBLICATION_SCOPE_INCOMPLETE}: source metadata missing"
            )
    for sizes in lesson_totals.values():
        if len(sizes) > 3 or sum(sizes) > 500:
            errors.append(f"{codes.PUBLICATION_LESSON_LIMIT}: all named sources exceed lesson allowance")
    for sizes in source_lessons.values():
        if len(sizes) > 2 or sum(sizes) > 300:
            errors.append(f"{codes.PUBLICATION_LESSON_LIMIT}: source exceeds lesson allowance")
    for file, total in totals.items():
        try:
            metadata = validate_owned_policy(file, registry[file], api)
            cap = min(2000, metadata["canonical_chars"] // 100)
            total.update(
                canonical_chars=metadata["canonical_chars"],
                unit_count=metadata["unit_count"],
                effective_cap=cap,
                unit_max=max(min(300, unit["chars"] // 10) for unit in metadata["units"].values()),
            )
            used = total["lesson"] + total["site_data"]
            total["share"] = used / metadata["canonical_chars"]
            total["unit_usage_max"] = max(total["units"].values(), default=0)
            total["unit_caps"] = {key: min(300, unit["chars"] // 10) for key, unit in metadata["units"].items()}
            if used > cap:
                errors.append(f"{codes.PUBLICATION_COURSE_LIMIT}: {file} {used} > {cap}")
            for unit, chars in total["units"].items():
                if chars > min(300, metadata["units"][unit]["chars"] // 10):
                    errors.append(f"{codes.PUBLICATION_UNIT_LIMIT}: {file} canonical unit over allowance")
        except (KeyError, ValueError) as exc:
            errors.append(
                str(exc)
                if isinstance(exc, ValueError)
                else f"{codes.PUBLICATION_SCOPE_INCOMPLETE}: canonical source missing"
            )
    return {
        "sources": dict(sorted(totals.items())),
        "errors": sorted(set(errors)),
        "status": "blocked" if errors else "ok",
    }


def tracked_inputs(root: Path) -> list[str]:
    """Read the actual tracked combined working tree, not a caller's partial file list."""
    try:
        result = subprocess.run(["git", "ls-files", "-z"], cwd=root, check=True, capture_output=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        raise ValueError(f"{codes.PUBLICATION_SCOPE_INCOMPLETE}: tracked course scope unavailable") from None
    return sorted(path for path in result.stdout.decode().split("\0") if path)


def course_report(root: Path | None = None, *, api=None, proposed: list[dict] | None = None) -> dict:
    """Recompute publication and exposure; unknown legacy provenance is never zero."""
    root = root or REPO_ROOT
    registry = load_registry(root / "docs/l2-uk-direct/textbook-selection.yaml")
    paths = tracked_inputs(root)
    occurrences, unknown, errors, fingerprints, repo_exposed = [], [], [], [], defaultdict(int)
    packs, plans = {}, {}
    for path in paths:
        if not (
            path.startswith("curriculum/l2-uk-en/lesson-plans/") or path.startswith("curriculum/l2-uk-en/evidence/")
        ):
            continue
        parts = Path(path).parts
        if len(parts) != 5 or not path.endswith(".yaml") or parts[-1].startswith("_"):
            continue
        try:
            data = (root / path).read_bytes()
            document = yaml.safe_load(data)
            fingerprints.append((path, hashlib.sha256(data).hexdigest()))
            (plans if parts[2] == "lesson-plans" else packs)[(parts[3], Path(path).stem)] = document
        except (OSError, ValueError, yaml.YAMLError):
            errors.append(f"{codes.PUBLICATION_SCOPE_INCOMPLETE}: tracked input unreadable")
    for (level, module), plan in plans.items():
        pack = packs.get((level, module))
        if not isinstance(plan, dict):
            errors.append(f"{codes.PUBLICATION_SCOPE_INCOMPLETE}: tracked plan invalid")
            continue
        if not isinstance(pack, dict):
            # Unbuilt plans contain no published prose, but planned excerpt demands need their packs.
            if quoted_records(plan) or any(
                "example" in (step.get("needs") or [])
                for lesson in plan.get("lessons", [])
                for step in lesson.get("steps", [])
            ):
                errors.append(f"{codes.PUBLICATION_SCOPE_INCOMPLETE}: demanded pack missing")
            continue
        try:
            occurrences += excerpt_occurrences(plan, pack, level=level, module=module)
        except ValueError as exc:
            errors.append(str(exc))
    for pack in packs.values():
        if not isinstance(pack, dict):
            continue
        for group in ("texts", "examples", "exercises"):
            for row in pack.get(group, []):
                file = (row.get("source") or {}).get("file")
                if file in NAMED_EXCERPTS:
                    repo_exposed[file] += nfc_chars(row.get("quote", row.get("text", "")))
    inventory = "site/src/data/lexicon-sentence-inventory.json"
    if inventory not in paths:
        errors.append(f"{codes.PUBLICATION_SCOPE_INCOMPLETE}: site inventory missing")
    else:
        data = (root / inventory).read_bytes()
        fingerprints.append((inventory, hashlib.sha256(data).hexdigest()))
        for index, row in enumerate(json.loads(data)["rows"]):
            locator = (row.get("provenance") or {}).get("locator", "")
            file = next((file for file in NAMED_EXCERPTS if locator.startswith(file + "_")), None)
            if file is not None:
                occurrences.append(
                    {
                        "key": ("l2-uk-en", "site-data", "lexicon", index, "sentence", str(index)),
                        "record": {
                            "id": str(index),
                            "quote": row["sentence"],
                            "source": {"kind": "textbook", "file": file, "chunk_id": locator},
                        },
                        "column": "site_data",
                    }
                )
    # Pages without a verified occurrence set cannot be claimed to contain zero excerpts.
    for path in paths:
        if path.startswith("site/src/content/docs/") and path.endswith(".mdx") and Path(path).stem != "index":
            unknown.append(path)
            data = (root / path).read_bytes()
            fingerprints.append((path, hashlib.sha256(data).hexdigest()))
    if unknown:
        errors.append(f"{codes.PUBLICATION_SCOPE_INCOMPLETE}: {len(unknown)} lesson pages provenance unverified")
    combined = occurrences + (proposed or [])
    result = check_occurrences(combined, registry, api=api)
    result["errors"] = sorted(set(result["errors"] + errors))
    result["status"] = "blocked" if result["errors"] else "ok"
    result["provenance_unknown"] = len(unknown)
    result["scope_sha256"] = hashlib.sha256(json.dumps(fingerprints, sort_keys=True).encode()).hexdigest()
    for file, total in result["sources"].items():
        total["repo_exposed"] = repo_exposed[file]
        total["provenance_unknown"] = len(unknown)
    return result


def enforce_publication(
    plan: dict, pack: dict, *, level="unknown", module="unknown", draft=None, api=None, root=None
) -> list[dict]:
    """Admission requires both local allowances and a complete combined course scope."""
    occurrences = excerpt_occurrences(plan, pack, level=level, module=module, draft=draft)
    if not occurrences:
        return []
    if draft is not None:
        reserved = {tuple(item["key"]) for item in excerpt_occurrences(plan, pack, level=level, module=module)}
        if any(tuple(item["key"]) not in reserved for item in occurrences):
            raise ValueError(f"{codes.PUBLICATION_SCOPE_INCOMPLETE}: actual excerpt exceeds planned reservation")
    local = check_occurrences(occurrences, api=api)
    if local["errors"]:
        raise ValueError(local["errors"][0])
    report = course_report(root, api=api, proposed=occurrences)
    if report["errors"]:
        raise ValueError(report["errors"][0])
    return occurrences


def report_main(argv=None) -> int:
    """Metadata-only command; blocked existing usage is an explicit nonzero outcome."""
    from .sources import Sources

    parser = argparse.ArgumentParser(
        description="Report bounded owned-source publication (#10106).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  .venv/bin/python -m scripts.curriculum.evidence publication-report\n"
        "  .venv/bin/python -m scripts.curriculum.evidence publication-report --sources-db data/sources.db\n"
        "Outputs: metadata JSON only; no files or database writes.\nExit codes: 0 complete; 1 blocked/unverified.\n"
        "Related: #10106; docs/epics/fresh-build-writer-contract.md",
    )
    parser.add_argument("--sources-db", type=Path)
    args = parser.parse_args(argv)
    try:
        with Sources(sources_db=args.sources_db) as api:
            result = course_report(api=api)
    except (ValueError, OSError) as exc:
        result = {"status": "blocked", "errors": [str(exc)]}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if result["status"] == "blocked" else 0
