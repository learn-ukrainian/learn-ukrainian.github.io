"""Writer-time Sources coverage (#10107), shared by every check-5 entry.

Full results stay in the ignored task store. Lesson receipts and reports carry
only identities and digests. Coverage is recomputed; saved verdicts have no authority.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, ValidationError

from scripts.build.fresh.regeneration import INPUT_KEYS
from scripts.common.task_store_paths import tasks_dir
from scripts.curriculum.evidence import lock
from scripts.curriculum.resolver.tokenize import lookup_form, tokenize
from scripts.ingest.resource_catalogue_ingest import normalise_url
from scripts.orchestration.task_record_store import locate_task_record

CONTRACT = "fresh-writer-sources.v1"
SCHEMA = Path(__file__).resolve().parents[3] / "schemas/fresh-writer-sources-v1.schema.json"
PREFIX = "mcp__sources__"
EvidenceKey = str | frozenset[str]


def digest(value: Any) -> str:
    """Fingerprint canonical JSON; used identically at harvest and assembly."""
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def inputs_digest(inputs: dict[str, str]) -> str:
    """Full digest of the existing complete INPUT_KEYS snapshot."""
    return digest([inputs[key] for key in INPUT_KEYS])


def _form(value: str) -> str:
    return lookup_form(value).casefold()


def _url_key(value: str) -> str:
    return "url:" + normalise_url(value)


def _payload(result: Any) -> tuple[dict[str, Any] | None, str]:
    if isinstance(result, dict):
        structured = result.get("structured_content", result.get("structuredContent"))
        if isinstance(structured, dict):
            return structured, ""
        if result.get("schema") == "sources.tool-result.v1":
            return result, ""
        result = result.get("content")
    if isinstance(result, str):
        try:
            parsed = json.loads(result)
        except ValueError:
            return None, result
        return _payload(parsed)
    if isinstance(result, list):
        texts = [
            item["text"]
            for item in result
            if isinstance(item, dict) and item.get("type") == "text" and isinstance(item.get("text"), str)
        ]
        for text in texts:
            try:
                parsed = json.loads(text)
            except ValueError:
                continue
            if isinstance(parsed, dict) and parsed.get("schema") == "sources.tool-result.v1":
                return parsed, ""
        return None, "\n".join(texts)
    return None, ""


def _truncated(value: Any) -> bool:
    if isinstance(value, dict):
        return any(str(key).startswith("_truncated") or _truncated(item) for key, item in value.items())
    if isinstance(value, list):
        return any(_truncated(item) for item in value)
    return isinstance(value, str) and "[...truncated]" in value


def credited_keys(call: dict[str, Any]) -> set[str]:
    """Credit only explicit paired non-error results in the expected tool format.

    Query/argument comparisons reject mismatched results; they never supply credit.
    A partial verification batch may contribute its successful per-item analyses.
    """
    name = call.get("name", "")
    args = call.get("arguments")
    result = call.get("result")
    if (
        not name.startswith(PREFIX)
        or call.get("paired") is not True
        or call.get("is_error") is not False
        or call.get("capture_incomplete")
        or not isinstance(args, dict)
        or _truncated(args)
        or _truncated(result)
        or (isinstance(result, dict) and (result.get("isError") or result.get("is_error")))
    ):
        return set()
    tool = name[len(PREFIX) :]
    envelope, text = _payload(result)
    if envelope is not None:
        if envelope.get("tool") != tool or envelope.get("status") != "ok":
            return set()
        query = envelope.get("query")
        if not isinstance(query, dict) or any(query.get(key) != value for key, value in args.items()):
            return set()
        typed = envelope.get("result", {})
        if tool in {"verify_word", "verify_words"}:
            disposition = envelope.get("disposition")
            if not (
                (disposition == "supported" and envelope.get("success") is True)
                or (tool == "verify_words" and disposition == "partial" and envelope.get("success") is False)
            ):
                return set()
            if not isinstance(typed, dict):
                return set()
            if tool == "verify_word":
                word = typed.get("word")
                matches = {word: typed.get("matches")} if isinstance(word, str) and word == args.get("word") else {}
            else:
                if typed.get("words") != args.get("words") or not 0 < len(args.get("words", [])) <= 50:
                    return set()
                matches = typed.get("matches", {})
            if not isinstance(matches, dict):
                return set()
            requested = args.get("words", [args.get("word")])
            return {
                "form:" + _form(word)
                for word, analyses in matches.items()
                if word in requested
                and isinstance(analyses, list)
                and analyses
                and all(isinstance(row, dict) and row.get("lemma") and row.get("pos") for row in analyses)
            }
        if envelope.get("success") is False or envelope.get("disposition") not in (None, "supported"):
            return set()
        hits = envelope.get("hits")
        if not isinstance(hits, list) or not hits:
            return set()
        keys = set()
        for hit in hits:
            if not isinstance(hit, dict):
                continue
            if tool in {"search_text", "search_literary", "get_chunk_context"} and hit.get("chunk_id") is not None:
                if tool == "get_chunk_context" and str(hit["chunk_id"]) != str(args.get("chunk_id")):
                    continue
                if args.get("source_file") and hit.get("source_file") != args["source_file"]:
                    continue
                keys.add("chunk:" + str(hit["chunk_id"]))
            elif tool == "search_style_guide" and hit.get("id") is not None:
                keys.add("style:" + str(hit["id"]))
            elif tool == "search_ua_gec_errors" and hit.get("id") is not None:
                keys.add("error:" + str(hit["id"]))
            elif tool == "search_resources" and hit.get("url"):
                try:
                    keys.add(_url_key(hit["url"]))
                except (ValueError, TypeError, AttributeError):
                    continue
        return keys
    # Current VESUM text starts with analysis counts; older held-out output does not.
    text = re.sub(r"^\d+ analys(?:is|es) \(\d+ distinct lemmas?\)\n\n", "", text)
    # AGY keeps server-rendered text only. Parse exact format, never free prose or hit counts.
    if tool == "verify_words":
        requested = args.get("words")
        if not isinstance(requested, list) or not 0 < len(requested) <= 50:
            return set()
        header = re.match(r"Batch verification: (\d+) words\n+Found: (\d+)/(\d+)\n", text)
        if not header or int(header[1]) != len(requested) or int(header[3]) != len(requested):
            return set()
        rows = re.findall(r"^- \*\*(.+?)\*\* — (.+)$", text, re.M)
        if len(rows) != len(requested) or [word for word, _ in rows] != requested:
            return set()
        found = [
            (word, re.fullmatch(r"FOUND \((\d+) analys(?:is|es)(?: \(\d+ distinct lemmas?\))?\): .+", rest))
            for word, rest in rows
        ]
        if sum(bool(match) for _, match in found) != int(header[2]):
            return set()
        return {"form:" + _form(word) for word, match in found if match and int(match[1]) > 0}
    if tool == "verify_word":
        match = re.match(r"'([^\n]+)' — matches in VESUM:\n", text)
        if (
            match
            and match[1] == args.get("word")
            and re.search(r"^- \*\*lemma\*\*: .+  \|  \*\*pos\*\*: .+", text, re.M)
        ):
            return {"form:" + _form(match[1])}
        return set()
    if tool == "get_chunk_context":
        match = re.match(r"\*\*\[([^]\n]+)]\*\* — .+\n\n.+", text, re.S)
        return {"chunk:" + match[1]} if match and match[1] == str(args.get("chunk_id")) else set()
    headers = {
        "search_text": r'Found \d+ results for: "([^\n]*)"\n',
        "search_literary": r'Found \d+ results for: "([^\n]*)"\n',
        "search_style_guide": r'Found \d+ results in \*\*[^\n]+\*\* for: "([^\n]*)"\n',
        "search_ua_gec_errors": r'Found \d+ human-annotated error pairs for: "([^\n]*)"\n',
        "search_resources": r'Found \d+ catalogue resources for: "([^\n]*)" \(returned ranking order\):\n',
    }
    header = re.match(headers.get(tool, r"(?!)"), text)
    if not header or header[1] != args.get("query", args.get("word")):
        return set()
    # Counts constrain the rendered format; they do not confer identity credit.
    # Extra record headers inside a source body make text-only capture ambiguous.
    count = int(re.match(r"Found (\d+)", text)[1])
    if tool == "search_resources":
        markers = re.findall(r"^(\d+)\. [^\n]+$", text, re.M)
        count = min(count, 5)  # The existing resource renderer prints its first five hits.
    else:
        markers = re.findall(r"^### Result (\d+)(?: \(native author\))?$", text, re.M)
    if markers != [str(i) for i in range(1, count + 1)] or not count:
        return set()
    label, prefix = {
        "search_text": ("Chunk ID", "chunk:"),
        "search_literary": ("Chunk ID", "chunk:"),
        "search_style_guide": ("ID", "style:"),
        "search_ua_gec_errors": ("Row ID", "error:"),
        "search_resources": ("URL", "url:"),
    }[tool]
    # Read identity fields only at their engine-rendered positions. Excerpt bodies
    # may themselves contain Markdown labels; those cannot become record identities.
    if tool in {"search_text", "search_literary"}:
        fields = (
            r"- \*\*Section\*\*: [^\n]*\n- \*\*Source\*\*: [^\n]*\n"
            r"- \*\*Subject\*\*: [^\n]*\n- \*\*Source file\*\*: `([^`\n]*)`\n"
            if tool == "search_text"
            else r"- \*\*Author\*\*: [^\n]*\n- \*\*Source\*\*: ([^\n]*)\n"
        )
        rows = re.findall(
            r"^### Result \d+\n" + fields + r"- \*\*Chunk ID\*\*: `([^`\n]+)`\n- \*\*Text\*\*:\n", text, re.M
        )
        if len(rows) != count:
            return set()
        return {
            prefix + value
            for source_file, value in rows
            if not args.get("source_file") or source_file == args["source_file"]
        }
    if tool == "search_resources":
        pattern = r"^\d+\. [^\n]+\n- \*\*URL\*\*: `([^`\n]+)`$"
    else:
        pattern = r"^### Result \d+(?: \(native author\))?\n- \*\*" + label + r"\*\*: `([^`\n]+)`$"
    values = re.findall(pattern, text, re.M)
    if len(values) != count:
        return set()
    if tool == "search_resources":
        try:
            return {_url_key(value) for value in values}
        except ValueError:
            return set()
    return {prefix + value for value in values}


def summarize_calls(calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Public receipt projection: no raw results, queries or excerpt bodies."""
    return [
        {"tool": call["name"], "credited_keys": sorted(keys), "result_sha256": digest(call.get("result"))}
        for call in calls
        if (keys := credited_keys(call))
    ]


def harvest_receipt(
    state_dir: Path,
    n: int,
    *,
    level: str,
    slug: str,
    inputs: dict[str, str],
    meta: dict[str, Any],
    task: dict[str, Any],
    draft_file: Path,
) -> None:
    """Bind the engine's metadata-only receipt to the actual persisted task evidence."""
    sidecar = task.get("tool_calls_file")
    sidecar_hash = task.get("tool_calls_sha256")
    # Old done records remain untrusted; the shared assembly gate reports missing.
    if not sidecar or not sidecar_hash:
        return
    raw = Path(sidecar).read_bytes()
    if hashlib.sha256(raw).hexdigest() != sidecar_hash:
        raise ValueError("writer_sources_binding_mismatch")
    payload = json.loads(raw)
    calls = payload.get("tool_calls") if isinstance(payload, dict) else None
    if not isinstance(calls, list) or not all(isinstance(call, dict) for call in calls):
        raise ValueError("writer_sources_capture_incomplete")
    receipt = {
        "contract_version": CONTRACT,
        "lesson": {"module": f"{level}/{slug}", "n": n},
        **{key: meta[key] for key in ("task_id", "attempt", "writer", "model", "effort", "prompt_sha256")},
        "inputs_sha256": inputs_digest(inputs),
        "draft_sha256": hashlib.sha256(draft_file.read_bytes()).hexdigest(),
        "sidecar_sha256": sidecar_hash,
        "credited_calls": summarize_calls(calls),
    }
    try:
        Draft202012Validator(json.loads(SCHEMA.read_text())).validate(receipt)
    except ValidationError as err:
        raise ValueError("writer_sources_binding_mismatch") from err
    lock.atomic_write(
        state_dir / f"lesson-{n}.writer_tool_calls.json",
        (json.dumps(receipt, ensure_ascii=False, indent=2) + "\n").encode(),
    )


def obligations(
    draft: dict, plan: dict, pack: dict, words: dict, level: str, slug: str, n: int, *, provenance: dict | None = None
) -> tuple[set[str], dict[str, EvidenceKey], dict[str, dict[str, str]], set[str]]:
    """Use existing assembly provenance and validated exceptions, without publishing.

    Engine record expansions retain check 7. Writer options are included even
    though the resolver skips them; only its existing phonetics/error exceptions apply.
    """
    from scripts.build.fresh.assemble import assemble_expanded_document
    from scripts.build.fresh.prompt import extract_plan_citations
    from scripts.curriculum.evidence.sources import Sources

    if provenance is None:
        _, provenance = assemble_expanded_document(draft, plan, pack, words, level, slug, n)
    forms = {
        _form(token.lookup)
        for span in provenance["spans"]
        if span["source"] == "writer_prose" and span["role"] != "phonetics"
        for token in tokenize(span["text"])
        if token.kind in {"cyrillic", "mixed"}
    }
    lesson = next(row for row in plan["lessons"] if row["n"] == n)
    records = {
        row["id"]: row
        for rows in pack.values()
        if isinstance(rows, list)
        for row in rows
        if isinstance(row, dict) and "id" in row
    }
    records.update({row["id"]: row for row in words.get("words", [])})
    evidence, pinned, report_only = {}, {}, set()
    for rid in sorted(extract_plan_citations(lesson)):
        row = records.get(rid)
        if rid.startswith("U-"):
            report_only.add(rid)
        elif rid.startswith("S-") and row:
            start, end = map(int, row["lines"].split("-"))
            # Existing fixed Standard reader validates range, digest and bytes; no MCP lookup.
            try:
                text, file_hash = Sources().get_standard_lines(start, end)
                if text != row["text"] or file_hash != row["file_sha256"]:
                    raise ValueError("pin mismatch")
                pin = {"file_sha256": file_hash, "lines": row["lines"]}
                pinned[rid] = {**pin, "fingerprint": digest(pin)}
            except (OSError, ValueError):
                evidence[rid] = "engine_pin_missing:" + rid
        elif row:
            source = row.get("source", {})
            if rid.startswith("W-"):
                evidence[rid] = (
                    frozenset("form:" + _form(part["form"]) for part in row["parts"])
                    if row.get("kind") == "formula"
                    else "form:" + _form(row["lemma"])
                )
            elif source.get("chunk_id") is not None:
                evidence[rid] = "chunk:" + str(source["chunk_id"])
            elif source.get("table") in {"ua_gec_errors", "style_guide"}:
                prefix = "error:" if source["table"] == "ua_gec_errors" else "style:"
                evidence[rid] = prefix + str(source["id"])
            elif row.get("url"):
                try:
                    evidence[rid] = _url_key(row["url"])
                except (ValueError, TypeError, AttributeError):
                    evidence[rid] = "unretrievable:" + rid
            else:
                evidence[rid] = "unretrievable:" + rid
        elif not rid.startswith(("P-", "G-")):
            evidence[rid] = "unretrievable:" + rid
    return forms, evidence, pinned, report_only


def _evidence_covered(identity: EvidenceKey, keys: set[str]) -> bool:
    """A formula's existing component forms must all have result-backed credit."""
    return identity in keys if isinstance(identity, str) else bool(identity) and identity <= keys


def coverage_summary(
    forms: set[str],
    evidence: dict[str, EvidenceKey],
    keys: set[str],
    *,
    code: str | None,
    noncredited: int = 0,
    pinned: dict[str, dict[str, str]] | None = None,
    report_only: set[str] | None = None,
) -> dict[str, Any]:
    """Counts and fingerprints, safe even for lessons stopped before check 5."""
    covered_forms = {form for form in forms if "form:" + form in keys}
    covered_evidence = {rid for rid, key in evidence.items() if _evidence_covered(key, keys)}
    groups = {"forms": (forms, covered_forms), "evidence": (set(evidence), covered_evidence)}
    return {
        "contract_version": CONTRACT,
        "code": code,
        "noncredited_calls": noncredited,
        "engine_pinned": pinned or {},
        "report_only": sorted(report_only or set()),
        **{
            label: {
                "required": len(required),
                "covered": len(covered),
                "missing": len(required - covered),
                "required_sha256": digest(sorted(required)),
                "covered_sha256": digest(sorted(covered)),
                "missing_sha256": digest(sorted(required - covered)),
            }
            for label, (required, covered) in groups.items()
        },
    }


def check_coverage(
    draft: dict,
    plan: dict,
    pack: dict,
    words: dict,
    level: str,
    slug: str,
    n: int,
    *,
    state_dir: Path | None,
    expected_inputs: dict[str, str] | None = None,
    provenance: dict | None = None,
) -> dict[str, Any]:
    """Fail closed on missing or stale receipts at the entry to shared check 5."""
    forms, evidence, pinned, report_only = obligations(draft, plan, pack, words, level, slug, n, provenance=provenance)
    keys: set[str] = set()
    noncredited = 0
    code = "writer_sources_missing"
    try:
        if state_dir is None:
            return coverage_summary(forms, evidence, keys, code=code, pinned=pinned, report_only=report_only)
        receipt_path = state_dir / f"lesson-{n}.writer_tool_calls.json"
        if not receipt_path.is_file():
            return coverage_summary(forms, evidence, keys, code=code, pinned=pinned, report_only=report_only)
        code = "writer_sources_binding_mismatch"
        receipt = json.loads(receipt_path.read_text())
        Draft202012Validator(json.loads(SCHEMA.read_text())).validate(receipt)
        meta = yaml.safe_load((state_dir / f"lesson-{n}.writer.yaml").read_text())
        draft_path = state_dir / f"lesson-{n}.draft.yaml"
        expected = expected_inputs or {}
        inputs = {
            "plan_sha256": expected.get("plan_sha256", hashlib.sha256(lock.yaml_bytes(plan)).hexdigest()),
            "pack_lock": expected.get("pack_lock", hashlib.sha256(lock.yaml_bytes(pack)).hexdigest()),
            "words_lock": expected.get("words_lock", hashlib.sha256(lock.yaml_bytes(words)).hexdigest()),
            "card_sha256": expected.get("style_card_sha256", draft["inputs"].get("style_card_sha256")),
            "prompt_sha256": expected.get("prompt_sha256", meta.get("base_prompt_sha256", meta["prompt_sha256"])),
        }
        prompt_path = state_dir / (
            f"lesson-{n}.attempt-{meta['attempt']}.prompt.md"
            if meta.get("base_prompt_sha256")
            else f"lesson-{n}.prompt.md"
        )
        task_path = locate_task_record(tasks_dir(), receipt["task_id"])
        task = json.loads(task_path.read_text()) if task_path else {}
        if (
            receipt["lesson"] != {"module": f"{level}/{slug}", "n": n}
            or receipt["inputs_sha256"] != inputs_digest(inputs)
            or any(draft["inputs"].get(key) != inputs[key] for key in ("plan_sha256", "pack_lock", "words_lock"))
            or draft["inputs"].get("style_card_sha256") != inputs["card_sha256"]
            or yaml.safe_load(draft_path.read_text()) != draft
            or receipt["draft_sha256"] != hashlib.sha256(draft_path.read_bytes()).hexdigest()
            or receipt["prompt_sha256"] != hashlib.sha256(prompt_path.read_bytes()).hexdigest()
            or inputs["prompt_sha256"] != hashlib.sha256((state_dir / f"lesson-{n}.prompt.md").read_bytes()).hexdigest()
            or task.get("status") != "done"
            or task.get("prompt_sha256") != receipt["prompt_sha256"]
            or task.get("agent") != receipt["writer"]
            or (task.get("resolved_model") or task.get("model")) != receipt["model"]
            or (task.get("resolved_effort") or task.get("effort") or "unknown") != receipt["effort"]
            or any(
                receipt[key] != meta[key]
                for key in ("task_id", "attempt", "writer", "model", "effort", "prompt_sha256")
            )
            or receipt["sidecar_sha256"] != task.get("tool_calls_sha256")
        ):
            raise ValueError(code)
        raw = Path(task["tool_calls_file"]).read_bytes()
        if hashlib.sha256(raw).hexdigest() != receipt["sidecar_sha256"]:
            raise ValueError(code)
        payload = json.loads(raw)
        calls = payload.get("tool_calls") if isinstance(payload, dict) else None
        if summarize_calls(calls) != receipt["credited_calls"]:
            raise ValueError(code)
        code = "writer_sources_capture_incomplete"
        if not isinstance(calls, list) or not calls or any(call.get("capture_incomplete") for call in calls):
            raise ValueError(code)
        for call in calls:
            credited = credited_keys(call)
            keys.update(credited)
            noncredited += not bool(credited)
        code = (
            "writer_sources_forms_uncovered"
            if any("form:" + form not in keys for form in forms)
            else (
                "writer_sources_evidence_uncovered"
                if any(not _evidence_covered(key, keys) for key in evidence.values())
                else (None if keys else "writer_sources_capture_incomplete")
            )
        )
    except (OSError, ValueError, KeyError, TypeError, AttributeError, ValidationError):
        pass
    # jsonschema errors are value-independent; keep the public failure metadata body-free.
    return coverage_summary(
        forms, evidence, keys, code=code, noncredited=noncredited, pinned=pinned, report_only=report_only
    )
