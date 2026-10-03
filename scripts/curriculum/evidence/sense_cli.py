"""Private selection and reviewed public choices. Diagnostics contain ids only."""

from __future__ import annotations

import argparse
import json
import unicodedata
from collections import Counter
from pathlib import Path

import yaml

from scripts.common.task_store_paths import tasks_dir

from . import reference_sense_v1 as matcher
from . import sense_bindings as bindings
from . import sources


def select_store(
    store: dict,
    inventory: list[dict],
    private: dict,
    api: sources.Sources,
    key: bytes | None = None,
    key_id: str | None = None,
) -> tuple[dict[str, dict], list[dict]]:
    """Measure without publishing private input, including repeated reference entries."""
    words = store["words"]
    rows = api.gloss_rows((w["lemma"], w["pos"]) for w in words).raw
    kaikki = api.kaikki_rows(w["lemma"] for w in words).raw
    ulif = api.ulif_entries(w["lemma"] for w in words).raw
    context = bindings.Context(store["level"], {}, inventory)
    selected, decisions = {}, []
    for word in words:
        members = context.members(word)
        if not members:
            decisions.append({"word": word["id"], "reason": "reference_non_member"})
            continue
        results = [
            (
                member,
                matcher.select(
                    word,
                    rows.get((word["lemma"], word["pos"]), []),
                    private[member["locator"]]["meaning"],
                    kaikki.get(word["lemma"]),
                    ulif_entries=ulif.get(word["lemma"], []),
                ),
            )
            for member in members
        ]
        successful = [r for _, r in results if r.ref]
        if len(successful) == len(results) and len({r.gloss for r in successful}) == 1:
            member, result = min(
                results, key=lambda pair: (pair[1].ref["id"], pair[1].ref["span_index"], pair[0]["locator"])
            )
            decisions.append({"word": word["id"], "id": result.ref["id"], "span_index": result.ref["span_index"]})
            if key is not None and key_id:
                selected[word["id"]] = bindings.reference_binding(
                    word, result.ref, private[member["locator"]], key, key_id
                )
        else:
            reason = results[0][1].reason if len(results) == 1 else "reference_ambiguous"
            decisions.append({"word": word["id"], "reason": reason or "reference_ambiguous"})
    return selected, decisions


def _redact_validated_locations(
    content: bytes, context: bindings.Context, words: dict, api: sources.Sources, *, kind: str
) -> bytes:
    """Redact validated scalar nodes only, preserving every other occurrence."""
    if kind not in {"bindings", "words"}:
        return content
    try:
        text = content.decode("utf-8")
        # Aliases can point outside the allowed location, and duplicate keys
        # make the parsed value's origin ambiguous. Neither receives exemptions.
        if any(isinstance(event, yaml.AliasEvent) for event in yaml.parse(text)):
            return content
        tree = yaml.compose(text)

        def mapping(node):
            if not isinstance(node, yaml.MappingNode):
                raise ValueError("invalid_mapping")
            fields = {key.value: value for key, value in node.value}
            if len(fields) != len(node.value):
                raise ValueError("duplicate_keys")
            return fields

        nodes = mapping(tree)["bindings" if kind == "bindings" else "words"]
        if not isinstance(nodes, yaml.SequenceNode):
            return content
        payload = yaml.safe_load(text)
        entries = payload.get("bindings" if kind == "bindings" else "words", [])
        ranges = []
        for entry, node in zip(entries, nodes.value, strict=True):
            fields = mapping(node)
            wid = entry.get("word" if kind == "bindings" else "id")
            word = words.get(wid)
            binding = context.entries.get(wid)
            if not word or not binding:
                continue
            row = api.gloss_rows([(word["lemma"], word["pos"])]).raw.get((word["lemma"], word["pos"]), [])
            selection = context.select(word, row, None)
            if selection.gloss is None:
                continue
            allowed = []
            if kind == "bindings" and entry == binding:
                allowed.append(fields["span"])
            elif (
                kind == "words"
                and entry.get("gloss_en") == binding["span"]
                and entry.get("gloss_ref") == selection.ref
                and entry.get("gloss_basis") == context.basis(wid)
            ):
                allowed.extend([fields["gloss_en"], mapping(fields["gloss_ref"])["span"]])
            for scalar in allowed:
                if not isinstance(scalar, yaml.ScalarNode) or scalar.value != binding["span"]:
                    return content
                ranges.append((scalar.start_mark.index, scalar.end_mark.index))
        for start, end in sorted(ranges, reverse=True):
            text = text[:start] + " " * (end - start) + text[end:]
        return text.encode()
    except (UnicodeError, ValueError, KeyError, TypeError, AttributeError, yaml.YAMLError):
        return content


def leak_scan(
    repo: Path,
    private: dict,
    context: bindings.Context,
    store: dict,
    api: sources.Sources,
    *,
    base: str = "origin/main",
    pr_text: str | None = None,
) -> dict:
    """Scan tracked HEAD files and new commit messages; never emit matched text.

    Exemptions are scalar locations, not a global dictionary-text allowlist. A same value
    in a comment, note or unrelated file still counts as a possible leak.
    """
    import re

    words = {w["id"]: w for w in store["words"]}
    meanings = {" ".join(unicodedata.normalize("NFC", row["meaning"]).casefold().split()) for row in private.values()}
    pattern = (
        re.compile(
            r"(?<!\w)(?:" + "|".join(re.escape(m) for m in sorted(meanings, key=lambda m: (-len(m), m))) + r")(?!\w)"
        )
        if meanings
        else None
    )
    leaks = Counter()

    def counts(content: bytes) -> Counter:
        value = " ".join(unicodedata.normalize("NFC", content.decode("utf-8", errors="replace")).casefold().split())
        return Counter(match[0] for match in pattern.finditer(value)) if pattern else Counter()

    paths = bindings.git(repo, "ls-tree", "-r", "--name-only", "-z", "HEAD").split(b"\0")
    for raw_path in paths:
        if not raw_path:
            continue
        path = raw_path.decode()
        content = bindings.git(repo, "show", f"HEAD:{path}")
        prefix = f"curriculum/l2-uk-en/evidence/{context.level}/"
        kind = (
            "bindings" if path == prefix + bindings.BINDINGS else "words" if path == prefix + "_words.yaml" else "other"
        )
        current = counts(_redact_validated_locations(content, context, words, api, kind=kind))
        leaks["committed_files"] += sum(current.values())
    messages = bindings.git(repo, "log", "--format=%B", f"{base}..HEAD")
    leaks["commit_messages"] = sum(counts(messages).values())
    leaks["pr_text"] = sum(counts(pr_text.encode()).values()) if pr_text is not None else 0
    return {
        "counts": dict(leaks),
        "pr_text": "unverified" if pr_text is None else "scanned",
        "status": "failed" if sum(leaks.values()) else "checked",
    }


def parser(command: str) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog=f"sense-{command}",
        description=(
            "Select exact private reference meanings or bind a recorded reviewed dictionary span.\n"
            "Private inputs and receipts stay outside Git; diagnostics expose only ids and reason codes."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n  .venv/bin/python -m scripts.curriculum.evidence sense-select a1 --private-input PRIVATE_JSONL\n"
            "  .venv/bin/python -m scripts.curriculum.evidence sense-select a1 --private-input PRIVATE_JSONL --write --key-file KEY --key-id build1\n"
            "  .venv/bin/python -m scripts.curriculum.evidence sense-bind a1 --word W-001 --candidates\n"
            "  .venv/bin/python -m scripts.curriculum.evidence sense-bind a1 --word W-001 --row-id 1 --span-index 0 --review-task REVIEW --author-model gpt-6.1-sol\n"
            "Outputs: public JSON decisions/candidates; --write updates bindings + lock; --check verifies and seals a clean head.\n"
            "Exit codes: 0 success; 1 invalid/stale evidence or suspected leak; 2 usage.\n"
            "Related: build-words, words-verify, pack-verify; docs/runbooks/reference-sense-bindings.md"
        ),
    )
    p.add_argument("level", help="Evidence level, e.g. a1")
    p.add_argument("--evidence-dir", type=Path, help="Evidence directory (default: level directory)")
    if command == "select":
        p.add_argument("--private-input", required=True, type=Path, help="Private JSONL extraction outside Git")
        modes = p.add_mutually_exclusive_group()
        modes.add_argument("--write", action="store_true", help="Update reference bindings and lock")
        modes.add_argument("--check", action="store_true", help="Reselect, scan and verify/seal current head")
        p.add_argument("--key-file", type=Path, help="Host-local secret key, at least 32 bytes")
        p.add_argument("--key-id", help="Public non-secret key identifier")
        p.add_argument("--receipt", type=Path, help="Host-local HMAC receipt outside Git")
        p.add_argument("--verify-receipt", action="store_true", help="Refuse stale receipt instead of issuing one")
        p.add_argument(
            "--base", default="origin/main", help="Base ref for commit message scan (all HEAD files are scanned)"
        )
        p.add_argument(
            "--pr", type=int, help="PR number whose title/body/comments are scanned; absent means unverified"
        )
    else:
        p.add_argument("--word", required=True, help="W-id whose candidate list is the subject")
        p.add_argument("--candidates", action="store_true", help="List public dictionary candidates without writing")
        p.add_argument("--row-id", type=int, help="Dictionary row id from candidate list")
        p.add_argument("--span-index", type=int, help="Parser position from candidate list")
        p.add_argument("--review-task", help="Terminal Ukrainian review dispatch id")
        p.add_argument(
            "--author-model", help="Optional author consistency check; identity is derived from the dispatch"
        )
    return p


def main(argv: list[str] | None = None, *, command: str = "select") -> int:
    args = parser(command).parse_args(argv)
    repo = Path.cwd()
    evidence = args.evidence_dir or bindings.ROOT / "curriculum/l2-uk-en/evidence" / args.level
    path = evidence / bindings.BINDINGS
    try:
        from scripts.ingest.build_ohoiko_a1_reference import require_private_path

        if command == "select":
            for private_path in (args.private_input, args.key_file, args.receipt):
                if private_path is not None:
                    require_private_path(private_path, repo)
        if command == "select" and args.verify_receipt and not args.check:
            raise ValueError("receipt_check_required")
        store = yaml.safe_load((evidence / "_words.yaml").read_text())
        context = bindings.Context.read(args.level, evidence)
        if context.invalid:
            raise ValueError("sense_bindings_invalid")
        with sources.Sources() as api:
            if command == "bind":
                word = next((w for w in store["words"] if w["id"] == args.word), None)
                if word is None:
                    raise ValueError("word_missing")
                rows = api.gloss_rows([(word["lemma"], word["pos"])]).raw[(word["lemma"], word["pos"])]
                pool = bindings.candidate_list(word, rows)
                if args.candidates:
                    print(
                        json.dumps(
                            {"word": args.word, "candidates_sha256": bindings.digest(pool), "candidates": pool},
                            ensure_ascii=False,
                        )
                    )
                    return 0
                if None in (args.row_id, args.span_index, args.review_task):
                    raise ValueError("review_arguments_required")
                context.entries[args.word] = bindings.reviewed_binding(
                    word, pool, args.row_id, args.span_index, args.review_task, tasks_dir(), args.author_model
                )
                bindings.write(path, args.level, context.entries)
                print(
                    json.dumps({"word": args.word, "id": args.row_id, "span_index": args.span_index, "status": "bound"})
                )
                return 0
            private = bindings.private_entries(args.private_input, context.inventory)
            key = args.key_file.read_bytes() if args.key_file else None
            if args.write or args.check:
                if key is None or not args.key_id:
                    raise ValueError("commitment_key_required")
                bindings.keyed({}, key)
            selected, decisions = select_store(store, context.inventory, private, api, key, args.key_id)
            if args.write:
                selected.update({k: v for k, v in context.entries.items() if v["method"] == "reviewed.v1"})
                bindings.write(path, args.level, selected)
            if args.check:
                for wid, binding in context.entries.items():
                    if binding["method"] != "reviewed.v1":
                        continue
                    word = next((w for w in store["words"] if w["id"] == wid), None)
                    if word is None:
                        raise ValueError("word_missing")
                    rows = api.gloss_rows([(word["lemma"], word["pos"])]).raw.get((word["lemma"], word["pos"]), [])
                    pool = bindings.candidate_list(word, rows)
                    current = bindings.reviewed_binding(
                        word, pool, binding["id"], binding["span_index"], binding["reviewer"]["task_id"], tasks_dir()
                    )
                    if current != binding:
                        raise ValueError("review_subject_stale_or_unapproved")
                    selected.pop(wid, None)
                expected = {k: v for k, v in context.entries.items() if v["method"] == matcher.METHOD}
                if selected != expected:
                    raise ValueError("reference_binding_reselection_failed")
                pr_text = None
                if args.pr:
                    import subprocess

                    try:
                        pr = subprocess.run(
                            ["gh", "pr", "view", str(args.pr), "--json", "title,body,comments"],
                            cwd=repo,
                            capture_output=True,
                            text=True,
                            timeout=60,
                        )
                    except (OSError, subprocess.TimeoutExpired):
                        pr = None
                    if pr is not None and pr.returncode == 0:
                        try:
                            data = json.loads(pr.stdout)
                            pr_text = " ".join([data["title"], data["body"], *(c["body"] for c in data["comments"])])
                        except (ValueError, KeyError, TypeError):
                            pr_text = None
                scan = leak_scan(repo, private, context, store, api, base=args.base, pr_text=pr_text)
                print(json.dumps({"leak_scan": scan}))
                if scan["status"] != "checked":
                    raise ValueError("private_text_leak_suspected")
                if not args.receipt:
                    raise ValueError("local_receipt_required")
                payload = bindings.receipt_payload(path, private, key, args.key_id, repo)
                if args.verify_receipt:
                    if not bindings.verify_receipt(args.receipt, payload, key):
                        raise ValueError("local_receipt_stale_or_invalid")
                else:
                    bindings.write_receipt(args.receipt, payload, key)
            print(
                json.dumps(
                    {"decisions": decisions, "resolved": sum("id" in d for d in decisions), "total": len(decisions)},
                    ensure_ascii=False,
                )
            )
        return 0
    except Exception as error:
        # Parse/SQLite/ledger errors can contain private input. Only controlled
        # reason codes are safe to report; never print an arbitrary exception.
        safe_codes = {
            "sense_bindings_invalid",
            "word_missing",
            "review_arguments_required",
            "commitment_key_required",
            "commitment_key_invalid",
            "reference_binding_reselection_failed",
            "private_text_leak_suspected",
            "local_receipt_required",
            "local_receipt_stale_or_invalid",
            "receipt_requires_clean_head",
            "private_inventory_coverage_invalid",
            "private_entry_invalid",
            "review_task_invalid",
            "review_author_identity_invalid",
            "review_effort_invalid",
            "review_harness_invalid",
            "receipt_check_required",
            "review_not_done_or_unrelated",
            "review_identity_unknown",
            "review_family_invalid",
            "review_result_changed",
            "review_subject_stale_or_unapproved",
            "review_sources_unproven",
            "review_date_invalid",
            "private_output_inside_repository",
        }
        reason = str(error) if isinstance(error, ValueError) and str(error) in safe_codes else type(error).__name__
        print(json.dumps({"status": "failed", "reason": reason}))
        return 1
