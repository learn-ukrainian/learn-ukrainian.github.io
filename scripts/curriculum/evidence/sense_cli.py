"""Private selection and reviewed public choices. Diagnostics contain ids only."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import yaml

from scripts.common import github_client
from scripts.common.task_store_paths import tasks_dir

from . import lock, registry, sources
from . import reference_sense_v1 as matcher
from . import sense_bindings as bindings


def validate_formula_record(word: dict, store: dict, evidence: Path, api: sources.Sources) -> None:
    """Keep part W-ids bound to their locked append-only lexical allocations."""
    lock.require(evidence / "_words.yaml")
    bindings.formulas.validate(word, {w["id"]: w for w in store["words"]}, api)
    try:
        registry.check_store(registry.load(evidence / "_words.registry.yaml"), store["words"])
    except ValueError as exc:
        raise ValueError("formula_part_identity_invalid") from exc


def select_store(
    store: dict,
    inventory: list[dict],
    private: dict,
    api: sources.Sources,
    key: bytes | None = None,
    key_id: str | None = None,
) -> tuple[dict[str, dict], list[dict]]:
    """Anna's dictionary chooses the English of each word it prints; formulas take their printed row.

    Diagnostics carry ids and public locators only.
    """
    words = [w for w in store["words"] if w.get("kind") != "formula"]
    rows = api.gloss_rows((w["lemma"], w["pos"]) for w in words).raw
    kaikki = api.kaikki_rows(w["lemma"] for w in words).raw
    context = bindings.Context(store["level"], {}, inventory)
    selected, decisions = {}, []
    for word in words:
        # The private printed label and the public inventory headword must both be the lemma.
        members = [
            m
            for m in context.labelled(word)
            if bindings.printed_headword(private[m["locator"]]["printed_label"]) == word["lemma"]
        ]
        if not members:
            decisions.append({"word": word["id"], "reason": "reference_non_member"})
            continue
        result = bindings.book_choice(
            word,
            rows.get((word["lemma"], word["pos"]), []),
            kaikki.get(word["lemma"]),
            [private[m["locator"]]["meaning"] for m in members],
        )
        if result is None:
            decisions.append({"word": word["id"], "reason": "reference_no_gloss"})
            continue
        choice, index = result
        member = members[index]
        decisions.append({"word": word["id"], "match": choice["match"], "locator": member["locator"]})
        if key is not None and key_id:
            selected[word["id"]] = bindings.book_binding(word, choice, private[member["locator"]], key, key_id)
    records = {w["id"]: w for w in store["words"]}
    for word in store["words"]:
        if word.get("kind") != "formula":
            continue
        bindings.formulas.validate(word, records, api)
        binding, decision = bindings.auto_formula_binding(
            word, api.formula_rows(word).raw, inventory, private, key, key_id
        )
        decisions.append(decision)
        if binding:
            selected[word["id"]] = binding
    return selected, decisions


def _redact_validated_locations(
    content: bytes,
    context: bindings.Context,
    words: dict,
    api: sources.Sources,
    *,
    kind: str,
    public: dict[str, set[str]] | None = None,
) -> bytes:
    """Redact validated scalar nodes only, preserving every other occurrence.

    ``public`` maps a word id to the open-dictionary atoms and spans of that
    record's own lemma. A store gloss equal to one of them, at the location the
    selector validates, is public even when another lemma's private entry shares
    the English.
    """
    if kind not in {"bindings", "words"}:
        return content
    try:
        text = content.decode("utf-8")
        tree = yaml.compose(text)
        # An alias repeats its anchor's value outside the allowed location, so a
        # node reached more than once (directly or inside an aliased subtree) is
        # never exempt. Unrelated aliases elsewhere in the file void nothing.
        reached = Counter()

        def reach(node, ancestors: frozenset[int] = frozenset()) -> None:
            reached[id(node)] += 1
            if id(node) in ancestors:
                return
            inner = ancestors | {id(node)}
            if isinstance(node, yaml.SequenceNode):
                for child in node.value:
                    reach(child, inner)
            elif isinstance(node, yaml.MappingNode):
                for key, value in node.value:
                    reach(key, inner)
                    reach(value, inner)

        reach(tree)

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
            own_public = (public or {}).get(wid, set())
            if not word or not (binding or (kind == "words" and own_public)):
                continue
            row = bindings.rows_for(word, api)
            payload_row = (
                None if word.get("kind") == "formula" else api.kaikki_rows([word["lemma"]]).raw.get(word["lemma"])
            )
            selection = context.select(word, row, payload_row)
            if selection.gloss is None:
                continue
            validated = (
                kind == "words"
                and entry.get("gloss_en") == selection.gloss
                and entry.get("gloss_ref") == selection.ref
                and entry.get("gloss_basis") == selection.basis
            )
            # (scalar node, the only value it may hold)
            allowed = []
            if binding:
                # A dictionary binding shows its atom (``span``); Anna's binding shows its ``gloss``.
                shown_field = "span" if "span" in binding else "gloss"
                if kind == "bindings" and entry == binding:
                    allowed.append((fields[shown_field], binding[shown_field]))
                elif validated and binding[shown_field] == selection.gloss and selection.basis is not None:
                    allowed.append((fields["gloss_en"], binding[shown_field]))
            if not allowed and validated and matcher.normalize(selection.gloss, word["pos"]) in own_public:
                allowed.append((fields["gloss_en"], selection.gloss))
            if allowed and kind == "words" and isinstance(selection.ref, dict) and "span" in selection.ref:
                allowed.append((mapping(fields["gloss_ref"])["span"], allowed[0][1]))
            for scalar, value in allowed:
                if not isinstance(scalar, yaml.ScalarNode) or scalar.value != value or reached[id(scalar)] != 1:
                    return content
                ranges.append((scalar.start_mark.index, scalar.end_mark.index))
        for start, end in sorted(ranges, reverse=True):
            text = text[:start] + " " * (end - start) + text[end:]
        return text.encode()
    except (UnicodeError, ValueError, KeyError, TypeError, AttributeError, yaml.YAMLError):
        return content


def _scan_normalize(text: str) -> str:
    """Literal scan normalization, without changing words or annotations."""
    return " ".join(unicodedata.normalize("NFC", text).casefold().split())


def _scan_pattern(terms: set[str]) -> tuple[re.Pattern, dict[str, list[str]]]:
    """Compile a prefix trie once; retain overlapping shorter literal matches."""
    trie = {}
    prefixes = {}
    for term in sorted(terms):
        node = trie
        for char in term:
            node = node.setdefault(char, {})
        node[""] = {}
        prefixes[term] = [
            term[:i]
            for i in range(1, len(term) + 1)
            if term[:i] in terms and (i == len(term) or (not term[i].isalnum() and term[i] != "_"))
        ]

    def expression(node: dict) -> str:
        branches = [re.escape(char) + expression(child) for char, child in node.items() if char]
        value = "(?:" + "|".join(branches) + ")" if len(branches) > 1 else "".join(branches)
        return "(?:" + value + ")?" if "" in node and branches else value

    # Lookahead allows a second term to start inside a previously matched phrase.
    return re.compile(r"(?<!\w)(?=(" + (expression(trie) if terms else r"(?!)") + r")(?!\w))"), prefixes


def _record_texts(value: object, ancestors: frozenset[int] = frozenset()):
    """Yield individual YAML/JSON mappings, never aggregate sibling records."""
    if id(value) in ancestors:
        return
    ancestors = ancestors | {id(value)}
    if isinstance(value, list):
        for item in value:
            yield from _record_texts(item, ancestors)
    elif isinstance(value, dict):
        parts = []
        for key, child in value.items():
            if isinstance(child, (str, int, float, bool)):
                parts.extend([str(key), str(child)])
            elif isinstance(child, dict):
                # Nested scalar fields (e.g. gloss_ref) belong to this record.
                parts.extend(str(v) for v in child.values() if isinstance(v, (str, int, float, bool)))
            elif isinstance(child, list):
                parts.extend(str(v) for v in child if isinstance(v, (str, int, float, bool)))
                if key == "forms":
                    parts.extend(str(v.get("form", "")) for v in child if isinstance(v, dict))
            yield from _record_texts(child, ancestors)
        if parts:
            yield "\n".join(parts)


def _head_blobs(repo: Path, paths: set[str] | None = None):
    """Read committed blobs through one cat-file stream, including binary files."""
    entries = bindings.git(repo, "ls-tree", "-r", "-z", "HEAD").split(b"\0")
    with subprocess.Popen(
        ["git", "cat-file", "--batch"],
        cwd=repo,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    ) as process:
        try:
            for entry in entries:
                if not entry:
                    continue
                metadata, path = entry.split(b"\t", 1)
                _mode, kind, oid = metadata.split()
                if kind != b"blob" or (paths is not None and path.decode("utf-8") not in paths):
                    continue
                process.stdin.write(oid + b"\n")
                process.stdin.flush()
                header = process.stdout.readline().split()
                if len(header) != 3 or header[1] != b"blob":
                    raise ValueError("tracked_blob_unreadable")
                size = int(header[2])
                content = process.stdout.read(size)
                if len(content) != size or process.stdout.read(1) != b"\n":
                    raise ValueError("tracked_blob_unreadable")
                yield path.decode("utf-8"), content
        finally:
            process.stdin.close()
            process.wait(timeout=30)
        if process.returncode:
            raise ValueError("tracked_blob_unreadable")


def leak_scan(
    repo: Path,
    private: dict,
    context: bindings.Context,
    store: dict,
    api: sources.Sources,
    *,
    base: str = "origin/main",
    pr_text: str | None = None,
    full_tree_report: Path | None = None,
) -> dict:
    """Gate changed blobs and level stores; optionally report the whole tree."""
    if full_tree_report is not None:
        from scripts.ingest.build_ohoiko_a1_reference import require_private_path

        require_private_path(full_tree_report, repo)
    merge_base = bindings.git(repo, "merge-base", base, "HEAD").decode().strip()
    head = bindings.git(repo, "rev-parse", "HEAD").decode().strip()
    changed_paths = {
        p.decode("utf-8")
        for p in bindings.git(
            repo, "diff", "--no-renames", "--name-only", "--diff-filter=AM", "-z", merge_base, head
        ).split(b"\0")
        if p
    }
    prefix = f"curriculum/l2-uk-en/evidence/{context.level}/"
    gate_paths = changed_paths | {prefix + bindings.BINDINGS, prefix + "_words.yaml"}
    scope = {
        "kind": "diff",
        "merge_base": merge_base,
        "head": head,
        "changed_path_count": len(changed_paths),
        "commit_count": int(bindings.git(repo, "rev-list", "--count", f"{merge_base}..{head}")),
    }
    words = {w["id"]: w for w in store["words"]}
    lexical = {wid: w for wid, w in words.items() if w.get("kind") != "formula"}
    entries = {row["locator"]: row for row in context.inventory}
    record_lemmas = {sources.unstressed_headword(w["lemma"]): w["lemma"] for w in lexical.values()}
    lemmas = {sources.unstressed_headword(row["lemma"]) for row in entries.values()}
    open_spans = {}
    positions = {sources.unstressed_headword(row["lemma"]): row.get("pos", "noun") for row in entries.values()}

    # Leak exemptions consider every open row for the lemma, including senses
    # that the learner selector would withhold for POS or annotation reasons.
    for raw in api._db().execute("SELECT * FROM dmklinger_uk_en"):
        row = dict(raw)
        lemma = sources.unstressed_headword(row["word"])
        if lemma not in lemmas and lemma not in record_lemmas:
            continue
        open_spans.setdefault(lemma, []).extend(matcher.row_spans(row))
    kaikki_lemmas = [row["lemma"] for row in entries.values()] + list(record_lemmas.values())
    for lemma, payload in api.kaikki_rows(dict.fromkeys(kaikki_lemmas)).raw.items():
        lemma = sources.unstressed_headword(lemma)
        for whole in (payload or {}).get("glosses", []):
            if isinstance(whole, str):
                for part in sources._sub_senses(whole):
                    open_spans.setdefault(lemma, []).extend((span, whole) for span in sources._sense_spans(part))

    def public(lemma: str, pos: str) -> tuple[set[str], set[str]]:
        """Normalized open-dictionary atoms and spans of one lemma."""
        atoms, spans = set(), set()
        for span, whole in open_spans.get(lemma, ()):
            spans.update((matcher.normalize(span, pos), matcher.normalize(whole, pos)))
            atoms.update(matcher.normalize(a, pos) for a in matcher.source_atoms(sources._gloss_head(span)))
            group = matcher.classify(span)
            if not group.reason:
                atoms.update(matcher.normalize(a, pos) for a in matcher.source_atoms(group.head))
        return atoms, spans

    public_atoms, public_spans = {}, {}
    for lemma in lemmas:
        public_atoms[lemma], public_spans[lemma] = public(lemma, positions[lemma])
    # A store gloss is public when it is an open atom or span of its own record's lemma.
    # A formula's gloss is exempt only through its validated binding.
    record_public = {
        wid: set().union(*public(sources.unstressed_headword(w["lemma"]), w["pos"])) for wid, w in lexical.items()
    }
    forms = {}
    for word in lexical.values():
        forms.setdefault(sources.unstressed_headword(word["lemma"]), set()).update(
            _scan_normalize(variant)
            for v in (word["lemma"], *(f["form"] for f in word.get("forms", []) if f.get("form")))
            for variant in (v, sources.unstressed_headword(v))
        )
    distinctive, mapping_meanings, mapping_forms = {}, {}, {}
    for locator, row in private.items():
        entry = entries[locator]
        lemma = sources.unstressed_headword(entry["lemma"])
        meaning = matcher.normalize(row["meaning"], entry.get("pos", "noun"))
        if meaning in public_atoms.get(lemma, set()):
            continue
        mapping_meanings.setdefault(meaning, set()).add(locator)
        for form in {_scan_normalize(lemma), _scan_normalize(entry.get("stressed", lemma)), *forms.get(lemma, set())}:
            mapping_forms.setdefault(form, set()).add(locator)
        if len(re.findall(r"\b\w+\b", meaning)) >= 3 and meaning not in public_spans.get(lemma, set()):
            distinctive.setdefault(meaning, set()).add(locator)
    wording_pattern, wording_prefixes = _scan_pattern(set(distinctive))
    mapping_pattern, mapping_prefixes = _scan_pattern(set(mapping_meanings) | set(mapping_forms))
    leaks = Counter(committed_files=0, commit_messages=0, pr_text=0)
    signals = Counter(distinctive_wording=0, mapping_copy=0)
    suspects = []
    files, byte_count = 0, 0
    full_counts = Counter(committed_files=0)
    full_signals = Counter(distinctive_wording=0, mapping_copy=0)
    full_suspects = []
    full_files, full_bytes = 0, 0

    def mapping_ids(text: str) -> set[str]:
        meanings, forms = set(), set()
        for match in mapping_pattern.finditer(_scan_normalize(text)):
            for term in mapping_prefixes[match[1]]:
                meanings.update(mapping_meanings.get(term, ()))
                forms.update(mapping_forms.get(term, ()))
        return meanings & forms

    def scan(content: bytes, path: str, category: str, *, gate: bool = True):
        text = content.decode("utf-8", errors="replace")
        wording = Counter()
        for match in wording_pattern.finditer(_scan_normalize(text)):
            for term in wording_prefixes[match[1]]:
                wording.update(distinctive[term])
        pairs = set().union(*(mapping_ids(line) for line in text.splitlines()))
        # Parse only structured files with a possible cross-line pair. Sibling
        # YAML/JSON records cannot lend each other a lemma or a meaning.
        if Path(path).suffix in {".yaml", ".yml", ".json", ".jsonl"} and (
            mapping_ids(text) - pairs or any(escape in text for escape in (r"\u", r"\U", r"\x", r"\N"))
        ):
            try:
                for doc in yaml.load_all(text, Loader=getattr(yaml, "CBaseLoader", yaml.BaseLoader)):
                    for record in _record_texts(doc):
                        pairs.update(mapping_ids(record))
            except yaml.YAMLError:
                # Invalid structured data still receives the literal line scan.
                pass
        for signal, matches in (("distinctive_wording", wording), ("mapping_copy", Counter({p: 1 for p in pairs}))):
            count = sum(matches.values())
            if count:
                suspect = {"path": path, "signal": signal, "locators": sorted(matches), "count": count}
                if gate:
                    leaks[category] += count
                    signals[signal] += count
                    suspects.append(suspect)
                if full_tree_report is not None and category == "committed_files":
                    full_counts[category] += count
                    full_signals[signal] += count
                    full_suspects.append(suspect)

    for path, content in _head_blobs(repo, None if full_tree_report is not None else gate_paths):
        if path in gate_paths:
            files += 1
            byte_count += len(content)
        full_files += 1
        full_bytes += len(content)
        kind = (
            "bindings" if path == prefix + bindings.BINDINGS else "words" if path == prefix + "_words.yaml" else "other"
        )
        scan(
            _redact_validated_locations(content, context, words, api, kind=kind, public=record_public),
            path,
            "committed_files",
            gate=path in gate_paths,
        )
    messages = bindings.git(repo, "log", "--format=%B", f"{merge_base}..{head}")
    scan(messages, "commit_messages", "commit_messages")
    if pr_text is not None:
        scan(pr_text.encode(), "pr_text", "pr_text")
    if full_tree_report is not None:
        full_tree_report.write_text(
            json.dumps(
                {
                    "scope": {"kind": "full_tree", "head": head},
                    "status": "report_only",
                    "counts": dict(full_counts),
                    "signals": dict(full_signals),
                    "suspects": full_suspects,
                    "tracked_files": full_files,
                    "tracked_bytes": full_bytes,
                }
            )
            + "\n"
        )
    return {
        "scope": scope,
        "counts": dict(leaks),
        "signals": dict(signals),
        "suspects": suspects,
        "tracked_files": files,
        "tracked_bytes": byte_count,
        "patterns": {"distinctive_wording": len(distinctive), "mapping_copy": len(mapping_meanings)},
        "pr_text": "unverified" if pr_text is None else "scanned",
        "status": "failed" if sum(leaks.values()) else "checked",
    }


def checked_receipt_payload(
    repo: Path,
    evidence: Path,
    store: dict,
    context: bindings.Context,
    private: dict,
    key: bytes,
    key_id: str,
    api: sources.Sources,
    selected: dict,
    *,
    base: str = "origin/main",
    pr_text: str | None = None,
    full_tree_report: Path | None = None,
) -> tuple[dict, dict]:
    """Reselect the entire binding set and derive the existing receipt's expected payload."""
    for wid, binding in context.entries.items():
        if binding["method"] not in {"reviewed.v1", "formula_row.v1"}:
            continue
        word = next((w for w in store["words"] if w["id"] == wid), None)
        if word is None:
            raise ValueError("word_missing")
        rows = bindings.rows_for(word, api)
        if word.get("kind") == "formula":
            validate_formula_record(word, store, evidence, api)
        if binding["method"] == "formula_row.v1":
            if context.select(word, rows, None).gloss is None:
                raise ValueError("formula_binding_invalid")
            # Keyed formula reference evidence is reselected; coordinate-only
            # bindings keep their explicit public sense choice.
            if "commitment" in binding and selected.get(wid) != binding:
                raise ValueError("formula_binding_reselection_failed")
            selected.pop(wid, None)
            continue
        pool = bindings.candidate_list(word, rows)
        current = bindings.reviewed_binding(
            word,
            pool,
            binding["id"],
            binding["span_index"],
            binding["reviewer"]["task_id"],
            tasks_dir(),
            atom_index=binding["atom_index"],
        )
        if current != binding:
            raise ValueError("review_subject_stale_or_unapproved")
        selected.pop(wid, None)
    expected = {k: v for k, v in context.entries.items() if v["method"] == bindings.BOOK_METHOD}
    if selected != expected:
        raise ValueError("reference_binding_reselection_failed")
    scan = leak_scan(
        repo,
        private,
        context,
        store,
        api,
        base=base,
        pr_text=pr_text,
        full_tree_report=full_tree_report,
    )
    if scan["status"] != "checked":
        raise ValueError("private_text_leak_suspected")
    payload = bindings.receipt_payload(evidence / bindings.BINDINGS, private, key, key_id, repo)
    payload["leak_scan_scope"] = scan["scope"]
    return payload, scan


@dataclass(frozen=True)
class LocalReceiptInputs:
    """Explicit host-local runtime inputs; never serialize these paths into evidence."""

    private_input: Path | None = None
    key_file: Path | None = None
    key_id: str | None = None
    receipt: Path | None = None
    base: str = "origin/main"


def add_receipt_arguments(parser: argparse.ArgumentParser) -> None:
    """Expose the existing read-only local receipt contract to verification consumers."""
    parser.add_argument("--private-input", type=Path, help="Private JSONL outside Git (default: no local proof)")
    parser.add_argument(
        "--key-file", type=Path, help="Existing host-local key outside Git, at least 32 bytes (default: none)"
    )
    parser.add_argument("--key-id", help="Existing public receipt key identifier, e.g. build1 (default: none)")
    parser.add_argument("--receipt", type=Path, help="Existing HMAC receipt outside Git; verify only (default: none)")
    parser.add_argument(
        "--receipt-base", default="origin/main", help="Receipt leak-scan merge-base ref (default: origin/main)"
    )


def receipt_inputs(args: argparse.Namespace) -> LocalReceiptInputs | None:
    """Partial explicit configuration must be refused rather than treated as absent."""
    if any((args.private_input, args.key_file, args.key_id, args.receipt)) or args.receipt_base != "origin/main":
        return LocalReceiptInputs(args.private_input, args.key_file, args.key_id, args.receipt, args.receipt_base)
    return None


def receipt_semantic_identity(payload: dict) -> dict:
    """Stable selection identity, never an authentication substitute.

    HEAD and scan counts remain mandatory in the live seal, but change when
    generated reports or review metadata are committed. Only selection inputs
    belong in tracked reports. Use an allowlist to exclude runtime diagnostics.
    """
    return {name: payload[name] for name in ("bindings_sha256", "private_input_commitment", "key_id", "matcher")}


def private_proof_required(level: str, evidence: Path) -> bool:
    """Derive proof need from current bindings and stored selection provenance."""
    entries = bindings.load(evidence / bindings.BINDINGS, level)
    store = yaml.safe_load((evidence / "_words.yaml").read_text(encoding="utf-8"))
    if not isinstance(store, dict) or not isinstance(store.get("words"), list):
        raise ValueError("sense_bindings_invalid")
    for word in store["words"]:
        basis = word.get("gloss_basis") or {}
        if bindings.local_proof(basis) == "private_commitment":
            return True
        if basis.get("method") == "formula_row.v1" and word["id"] not in entries:
            raise ValueError("formula_binding_invalid")
    return any(bindings.local_proof(entry) == "private_commitment" for entry in entries.values())


def verify_local_receipt(
    level: str,
    evidence: Path,
    api: sources.Sources,
    inputs: LocalReceiptInputs,
    *,
    repo: Path,
) -> tuple[frozenset[str], dict]:
    """Read-only authenticated replay, with safe reason codes and no receipt issuance."""
    try:
        from scripts.ingest.build_ohoiko_a1_reference import require_private_path

        if inputs.private_input is None or inputs.key_file is None or not inputs.key_id:
            raise ValueError("commitment_key_required")
        if inputs.receipt is None:
            raise ValueError("local_receipt_required")
        for private_path in (inputs.private_input, inputs.key_file, inputs.receipt):
            require_private_path(private_path, repo)
        context = bindings.Context.read(level, evidence)
        if context.invalid:
            raise ValueError("sense_bindings_invalid")
        store = yaml.safe_load((evidence / "_words.yaml").read_text())
        private = bindings.private_entries(inputs.private_input, context.inventory)
        key = inputs.key_file.read_bytes()
        bindings.keyed({}, key)
        selected, _ = select_store(store, context.inventory, private, api, key, inputs.key_id)
        payload, _ = checked_receipt_payload(
            repo,
            evidence,
            store,
            context,
            private,
            key,
            inputs.key_id,
            api,
            selected,
            base=inputs.base,
        )
        if not bindings.verify_receipt(inputs.receipt, payload, key):
            raise ValueError("local_receipt_stale_or_invalid")
        covered = frozenset(
            wid for wid, binding in context.entries.items() if bindings.local_proof(binding) == "private_commitment"
        )
        return covered, {"status": "verified", **receipt_semantic_identity(payload)}
    except Exception as error:
        return frozenset(), {"status": "failed", "reason": safe_error_reason(error)}


def safe_error_reason(error: Exception) -> str:
    """Never echo private parse, filesystem, SQLite or ledger diagnostics."""
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
        "formula_coordinates_required",
        "formula_binding_invalid",
        "formula_binding_reselection_failed",
        "formula_gloss_ineligible",
        "formula_part_identity_invalid",
        "formula_vesum_unavailable",
        "formula_tokens_invalid",
        "formula_punctuation_invalid",
        "formula_token_parts_mismatch",
        "formula_part_cycle",
        "formula_part_missing_or_retired",
        "formula_part_non_lexical",
        "formula_part_ambiguous",
        "formula_part_entry_invalid",
        "formula_part_form_invalid",
        "formula_alias_unattested",
        "formula_alias_invalid",
        "formula_definition_invalid",
    }
    reason = str(error) if isinstance(error, ValueError) and str(error) in safe_codes else type(error).__name__
    return reason


def parser(command: str) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog=f"sense-{command}",
        description=(
            "Select private reference meanings, formula atoms, or reviewed lexical spans.\n"
            "Private inputs and receipts stay outside Git; diagnostics expose only ids and reason codes."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n  .venv/bin/python -m scripts.curriculum.evidence sense-select a1 --private-input PRIVATE_JSONL\n"
            "  .venv/bin/python -m scripts.curriculum.evidence sense-select a1 --private-input PRIVATE_JSONL --write --key-file KEY --key-id build1\n"
            "  .venv/bin/python -m scripts.curriculum.evidence sense-bind a1 --word W-001 --candidates\n"
            "  .venv/bin/python -m scripts.curriculum.evidence sense-bind a1 --word W-001 --row-id 1 --span-index 0 --atom-index 0 --review-task REVIEW --author-model gpt-6.1-sol\n"
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
        modes.add_argument(
            "--write", action="store_true", help="Update bindings and lock; report and skip stale formula bindings"
        )
        modes.add_argument("--check", action="store_true", help="Reselect, scan and verify/seal current head")
        p.add_argument("--key-file", type=Path, help="Host-local secret key, at least 32 bytes")
        p.add_argument("--key-id", help="Public non-secret key identifier")
        p.add_argument("--receipt", type=Path, help="Host-local HMAC receipt outside Git")
        p.add_argument("--verify-receipt", action="store_true", help="Refuse stale receipt instead of issuing one")
        p.add_argument(
            "--base",
            default="origin/main",
            help="Ref whose merge-base with HEAD bounds changed blobs and commit messages (default: origin/main)",
        )
        p.add_argument(
            "--full-tree-report",
            type=Path,
            help="Optional full HEAD tree ids/paths/counts JSON outside the repository, e.g. /tmp/tree-report.json; report only, requires --check",
        )
        p.add_argument(
            "--pr", type=int, help="PR number whose title/body/comments are scanned; absent means unverified"
        )
    else:
        p.add_argument("--word", required=True, help="W-id whose candidate list is the subject")
        p.add_argument("--candidates", action="store_true", help="List public dictionary candidates without writing")
        p.add_argument("--row-id", type=int, help="Dictionary row id from candidate list")
        p.add_argument("--span-index", type=int, help="Parser position from candidate list")
        p.add_argument("--atom-index", type=int, default=0, help="Atom position from candidate list (default: 0)")
        p.add_argument("--review-task", help="Terminal Ukrainian review dispatch id")
        p.add_argument(
            "--author-model", help="Lexical review author consistency check; identity is derived from the dispatch"
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
            for private_path in (args.private_input, args.key_file, args.receipt, args.full_tree_report):
                if private_path is not None:
                    require_private_path(private_path, repo)
        if command == "select" and args.verify_receipt and not args.check:
            raise ValueError("receipt_check_required")
        if command == "select" and args.full_tree_report and not args.check:
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
                rows = bindings.rows_for(word, api)
                if word.get("kind") == "formula":
                    validate_formula_record(word, store, evidence, api)
                pool = bindings.candidate_list(word, rows)
                if args.candidates:
                    print(
                        json.dumps(
                            {
                                "word": args.word,
                                "candidates_sha256": bindings.digest(pool),
                                "candidates": pool,
                                **(
                                    {
                                        **bindings.formulas.definition(word),
                                        "definition_sha256": word["definition_sha256"],
                                    }
                                    if word.get("kind") == "formula"
                                    else {}
                                ),
                            },
                            ensure_ascii=False,
                        )
                    )
                    return 0
                if word.get("kind") == "formula":
                    if None in (args.row_id, args.span_index):
                        raise ValueError("formula_coordinates_required")
                    chosen = next(
                        (
                            c
                            for c in pool
                            if c["id"] == args.row_id
                            and c["span_index"] == args.span_index
                            and c["atom_index"] == args.atom_index
                        ),
                        None,
                    )
                    context.entries[args.word] = bindings.formula_binding(word, pool, chosen)
                else:
                    if None in (args.row_id, args.span_index, args.review_task):
                        raise ValueError("review_arguments_required")
                    context.entries[args.word] = bindings.reviewed_binding(
                        word,
                        pool,
                        args.row_id,
                        args.span_index,
                        args.review_task,
                        tasks_dir(),
                        args.author_model,
                        atom_index=args.atom_index,
                    )
                bindings.write(path, args.level, context.entries)
                print(
                    json.dumps(
                        {
                            "word": args.word,
                            "id": args.row_id,
                            "span_index": args.span_index,
                            "atom_index": args.atom_index,
                            "status": "bound",
                        }
                    )
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
                by_id = {w["id"]: w for w in store["words"]}
                for wid, binding in context.entries.items():
                    if binding["method"] == "reviewed.v1":
                        selected[wid] = binding
                    elif binding["method"] == "formula_row.v1":
                        word = by_id.get(wid)
                        valid = word is not None and word.get("kind") == "formula"
                        if valid:
                            validate_formula_record(word, store, evidence, api)
                            valid = context.select(word, bindings.rows_for(word, api), None).gloss is not None
                        if not valid:
                            selected.pop(wid, None)
                            decisions = [d for d in decisions if d["word"] != wid]
                            decisions.append({"word": wid, "reason": "formula_binding_invalid"})
                            continue
                        selected[wid] = binding
                bindings.write(path, args.level, selected)
            if args.check:
                pr_text = None
                if args.pr:
                    import subprocess

                    try:
                        pr = github_client.run(
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
                payload, scan = checked_receipt_payload(
                    repo,
                    evidence,
                    store,
                    context,
                    private,
                    key,
                    args.key_id,
                    api,
                    selected,
                    base=args.base,
                    pr_text=pr_text,
                    full_tree_report=args.full_tree_report,
                )
                print(json.dumps({"leak_scan": scan}))
                if not args.receipt:
                    raise ValueError("local_receipt_required")
                if args.verify_receipt:
                    if not bindings.verify_receipt(args.receipt, payload, key):
                        raise ValueError("local_receipt_stale_or_invalid")
                else:
                    bindings.write_receipt(args.receipt, payload, key)
            print(
                json.dumps(
                    {
                        "decisions": decisions,
                        # A lexical choice names its match; a formula choice names its row coordinates.
                        "resolved": sum("match" in d or "id" in d for d in decisions),
                        "book_glosses": sum(d.get("match") == "book" for d in decisions),
                        "total": len(decisions),
                    },
                    ensure_ascii=False,
                )
            )
        return 0
    except Exception as error:
        # Parse/SQLite/ledger errors can contain private input. Only controlled
        # reason codes are safe to report; never print an arbitrary exception.
        reason = safe_error_reason(error)
        print(json.dumps({"status": "failed", "reason": reason}))
        return 1
