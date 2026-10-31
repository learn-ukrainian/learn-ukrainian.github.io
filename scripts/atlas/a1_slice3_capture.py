"""Freeze saved Sources replies and authenticated dictionary witnesses for slice 3.

This library reads existing stores only; it never harvests, allocates or writes a source store.
"""

import hashlib
import json
from contextlib import ExitStack

from scripts.atlas import word_card_foundation as foundation
from scripts.atlas import word_card_meanings as meanings
from scripts.atlas.a1_card_receipts import Refusal, digest
from scripts.common.repo_root import main_checkout_root
from scripts.storage.topology import StoreRefusal, resolve_store, store_data_dir


def response_text(call):
    return "\n".join(c["text"] for c in call["response"]["content"] if c["type"] == "text")


def capture(tool_dir, inventory, targets, ulif_ids, root):
    """Retain actual calls and rederive every consumed payload from its source response/witness."""
    calls = {p.stem: json.loads(p.read_text()) for p in sorted(tool_dir.glob("*.json"))}
    records, held = {}, []

    def add(record_key, call_key, source, payload, locator, *, url="", fetched="", content="", parser=""):
        if record_key in records:
            raise Refusal("duplicate_source_record_key")
        call = calls[call_key]
        records[record_key] = {"source_id": source, "snapshot_id": source + "@sha256:" + digest(payload),
            "locator": locator, "source_url": url, "retrieved_at": fetched,
            "content_sha256": content or digest(payload), "parser_version": parser,
            "payload": payload, "tool": call["tool"], "arguments": call["arguments"],
            "response_sha256": digest(call["response"]), "call_key": call_key}

    binding = resolve_store("sources", main_checkout_root(root))
    if isinstance(binding, StoreRefusal):
        raise Refusal("sources_store_unavailable:" + binding.reason)
    with ExitStack() as stack:
        conn = foundation.readonly(stack, binding.path)
        for index, target in enumerate(targets):
            word = target["lemma"]
            for suffix in ("ulif", "vesum", "vts", "sum20", "cefr", "frequency", "heritage"):
                call = calls[f"{index}-{suffix}"]
                argument = "words" if suffix == "ulif" else "lemma" if suffix == "vesum" else \
                    "word" if suffix in {"vts", "sum20"} else "query"
                if call["arguments"][argument] != ([word] if suffix == "ulif" else word):
                    raise Refusal("capture_query_mismatch")
                if call["response"].get("isError"):
                    raise Refusal("capture_tool_error")
            inspection = json.loads(response_text(calls[f"{index}-vesum"]).split("- Raw payload: ", 1)[1])
            if inspection["pipeline_identity"] != inventory["sources"]["vesum_pipeline_identity"]:
                raise Refusal("vesum_import_drift")
            add("vesum:" + word, f"{index}-vesum", "vesum", inspection, "vesum:lemma:" + word,
                parser=inspection["pipeline_identity"]["schema_version"])
            ulif = json.loads(response_text(calls[f"{index}-ulif"]))["records"][0]
            chosen = [e for e in ulif["entries"] if e["entry_id"] == ulif_ids.get(word)]
            for entry in ulif["entries"]:
                if entry not in chosen:
                    held.append({"lemma": word, "source": "ulif", "entry_id": entry["entry_id"],
                                 "reason": "other_homonym_or_unresolved_correspondence"})
            if chosen:
                entry = chosen[0]
                if not entry["verified"] or not entry["identity_from_raw"]["stored_matches_raw"]:
                    raise Refusal("ulif_raw_identity_mismatch")
                add("ulif:" + word, f"{index}-ulif", "ulif", entry, f"ulif:entry:{entry['entry_id']}",
                    url="https://lcorp.ulif.org.ua/dictua", fetched=entry["retrieved_at"],
                    content=entry["content_sha256"], parser=entry["parser_version"])
            rows = conn.execute("SELECT * FROM slovnyk_me_entries WHERE dictionary_slug='vts' AND normalized_word=?",
                                (word.casefold(),)).fetchall()
            if len(rows) == 1:
                row = dict(rows[0])
                text, reason = meanings.full_vts(row, store_data_dir(binding.path).parent)
                if reason or text is None:
                    held.append({"lemma": word, "source": "vts", "reason": reason or "no_admitted_witness"})
                else:
                    if hashlib.sha256(text.encode()).hexdigest() != row["content_sha256"]:
                        raise Refusal("vts_tool_witness_mismatch:" + word)
                    call_key = f"{index}-vts"
                    witness = response_text(calls[call_key])
                    if row["source_url"] not in witness:
                        held.append({"lemma": word, "source": "vts", "reason": "tool_admitted_locator_disagreement"})
                    else:
                        add("vts:" + word, call_key, "vts_busel_slovnyk_me", {"row": row, "text": text},
                            f"vts:slovnyk_me_entries:{row['id']}", url=row["source_url"],
                            fetched=row["fetched_at"], content=row["content_sha256"], parser=row["importer_version"])
                        if text not in witness:
                            held.append({"lemma": word, "source": "vts", "reason": "only_tool_quoted_spans_admissible"})
            else:
                held.append({"lemma": word, "source": "vts", "reason": "no_unique_admitted_witness"})
            for suffix, source in (("cefr", "puls"), ("frequency", "grac"), ("heritage", "grinchenko"),
                                   ("balla", "balla")):
                call = calls[f"{index}-{suffix}"]
                payload = call["response"].get("structuredContent") or {"text": response_text(call)}
                add(suffix + ":" + word, f"{index}-{suffix}", source, payload, source + ":query:" + word)
            held.append({"lemma": word, "source": "sum20", "reason": "mirror_not_admitted_for_slice3",
                         "call_key": f"{index}-sum20"})
        for call_key, call in calls.items():
            if call_key.startswith("context-"):
                add("textbook:" + call_key, call_key, "textbooks", {"text": response_text(call)},
                    "textbook:" + call["arguments"]["chunk_id"])
    return {"schema_version": "atlas-a1-slice3-sources.v1", "inventory_sha256": digest(inventory),
            "calls": calls, "records": records, "held_units": held}
