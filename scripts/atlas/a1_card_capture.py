"""Freeze actual Sources replies and their admitted witnesses for the fixed A1 batch."""

import hashlib
import json
from contextlib import ExitStack
from pathlib import Path

from scripts.atlas import word_card_foundation as foundation
from scripts.atlas import word_card_meanings as meanings
from scripts.atlas.a1_card_receipts import Refusal, digest, selected_rows
from scripts.common.repo_root import main_checkout_root
from scripts.storage.topology import StoreRefusal, resolve_store, store_data_dir
from scripts.wiki.sum20_mirror import served_rows


def response_text(call):
    return "\n".join(c.get("text", "") for c in call["response"]["content"])


def capture(tool_dir: Path, inventory: dict, root: Path) -> dict:
    """Read saved tool replies and authenticate cached VTS text; never fetch or write stores."""
    words = sorted({r["mapping"]["lemma"] for r in selected_rows(inventory)})
    calls = {p.stem: json.loads(p.read_text()) for p in sorted(tool_dir.glob("*.json"))}
    records = {}

    def add(key, call_key, source, payload, *, locator, url="", fetched="", content="", parser="", role=None):
        call = calls[call_key]
        record = {
            "source_id": source, "snapshot_id": source + "@sha256:" + digest(payload),
            "locator": locator, "source_url": url, "retrieved_at": fetched,
            "content_sha256": content or digest(payload), "parser_version": parser,
            "payload": payload, "tool": call["tool"], "arguments": call["arguments"],
            "response_sha256": digest(call["response"]), "call_key": call_key,
        }
        if role is not None:
            record["source_role"] = role
        records[key] = record

    binding = resolve_store("sources", main_checkout_root(root))
    if isinstance(binding, StoreRefusal):
        raise Refusal("sources_store_unavailable:" + binding.reason)
    with ExitStack() as stack:
        connection = foundation.readonly(stack, binding.path)
        for index, word in enumerate(words):
            ulif_call = calls[f"{index}-ulif"]
            entries = json.loads(response_text(ulif_call))["records"][0]["entries"]
            if len(entries) != 1 or not entries[0]["verified"]:
                raise Refusal("ulif_identity_not_unique")
            entry = entries[0]
            if not entry["identity_from_raw"].get("stored_matches_raw"):
                raise Refusal("ulif_raw_identity_mismatch")
            add(f"ulif:{word}", f"{index}-ulif", "ulif", entry,
                locator=f"ulif:entry:{entry['entry_id']}", url="https://lcorp.ulif.org.ua/dictua",
                fetched=entry["retrieved_at"], content=entry["content_sha256"], parser=entry["parser_version"])
            inspection = json.loads(response_text(calls[f"{index}-vesum"]).split("- Raw payload: ", 1)[1])
            if inspection["pipeline_identity"] != inventory["sources"]["vesum_pipeline_identity"]:
                raise Refusal("vesum_import_drift")
            add(f"vesum:{word}", f"{index}-vesum", "vesum", inspection,
                locator="vesum:lemma:" + word, parser=inventory["sources"]["vesum_pipeline_identity"]["schema_version"])
            rows = [dict(row) for row in connection.execute(
                "SELECT * FROM slovnyk_me_entries WHERE dictionary_slug='vts' AND normalized_word=? ORDER BY id",
                (word,))]
            if len(rows) != 1:
                raise Refusal("admitted_vts_not_unique")
            row = rows[0]
            text, reason = meanings.full_vts(row, store_data_dir(binding.path).parent)
            if reason or text is None:
                raise Refusal(reason or "vts_text_unavailable")
            if hashlib.sha256(text.encode()).hexdigest() != row["content_sha256"]:
                raise Refusal("vts_snapshot_mismatch")
            add(f"vts:{word}", f"{index}-vts", "vts_busel_slovnyk_me", {"row": row, "text": text},
                locator=f"vts:slovnyk_me_entries:{row['id']}", url=row["source_url"],
                fetched=row["fetched_at"], content=row["content_sha256"], parser=row["importer_version"], role="admitted")
            for mirror, relation in served_rows(connection, word):
                if mirror["article_text"] not in response_text(calls[f"{index}-sum20"]):
                    raise Refusal("sum20_tool_snapshot_mismatch")
                add(f"sum20:{word}", f"{index}-sum20", "sum20_slovnyk_mirror", mirror,
                    locator=f"sum20_mirror_articles:{mirror['id']}", url=mirror["source_url"],
                    fetched=mirror["fetched_at"], content=mirror["content_sha256"],
                    parser="sum20-mirror-rule-v1", role=relation)
            for label, source in (("cefr", "puls"), ("frequency", "grac"), ("heritage", "grinchenko")):
                reply = calls[f"{index}-{label}"]["response"]
                add(f"{label}:{word}", f"{index}-{label}", source,
                    reply.get("structuredContent") or {"text": response_text(calls[f"{index}-{label}"])},
                    locator=f"{source}:query:{word}")
        if "school-context" in calls:
            add("textbook:school", "school-context", "textbooks",
                {"text": response_text(calls["school-context"])},
                locator="textbook:1-klas-bukvar-zaharijchuk-2025-1::1-klas-bukvar-zaharijchuk-2025-1_s0002")
        for key, call in calls.items():
            if key.startswith("balla-"):
                add(key, key, "balla", call["response"].get("structuredContent") or {"text": response_text(call)},
                    locator="balla:query:" + call["arguments"]["query"])
    return {"schema_version": "atlas-a1-slice2-sources.v1", "calls": calls, "records": records,
            "inventory_sha256": digest(inventory)}
