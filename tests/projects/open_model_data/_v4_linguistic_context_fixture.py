"""Synthetic abstract grammatical metadata; no Ukrainian example is normative gold.

Only these tests write prepared target artifacts. Production source qualification
belongs to the existing trusted preparation owner and is not supplied here.
"""

from copy import deepcopy

from learn_ukrainian_v4_runtime import semantic_inputs as semantic
from learn_ukrainian_v4_runtime.operation_auth import canonical_bytes, digest
from learn_ukrainian_v4_runtime.resources import resource_root


def constraints():
    return {
        "task_kind": "original_row", "cefr_level": "A1",
        "required_fields": ["row_text", "answer"], "allowed_evidence_tools": ["verify_word"],
        "language": "uk", "stratum": "standard_correct",
        "target": {
            "claim_type": "prescriptive_rule", "mechanism": "syntax",
            "scope": {"register": "fixture_register", "period": "fixture_period", "genre": "fixture_genre"},
            "matcher": {
                "kind": "syntax",
                "tokens": [{"pos": "NOUN", "features": {"Number": "Sing"}},
                           {"pos": "ADJ", "features": {"Number": "Sing"}}],
                "dependency_constraints": [{"head": 0, "dependent": 1, "relation": "amod"}],
            },
            "protections": [],
        },
    }


def preparation(binding, value=None):
    value = deepcopy(value if value is not None else constraints())
    return {
        "schema": "v4-admitted-linguistic-context.v1",
        "slot_id": binding["slot_id"], "packet_sha256": binding["packet_sha256"],
        "constraints": value,
        "evidence": {
            "target_sha256": digest(canonical_bytes(value["target"])),
            "a4_receipt_sha256": digest((resource_root() / semantic.A4_RELATIVE).read_bytes()),
            "a5_receipt_sha256": digest((resource_root() / semantic.A5_RELATIVE).read_bytes()),
            "source_role": "explicit_rule", "claim_type": value["target"]["claim_type"],
            "support_decision": "source_supported", "locator_decision": "exact_sufficient",
            "evidence_locator_sha256s": [digest(("synthetic locator; no normative claim " + binding["request_id"]).encode())],
        },
    }


def store_artifact(conn, value):
    raw = canonical_bytes(value)
    sha = digest(raw)
    conn.execute(
        """INSERT INTO fleet_comms_artifact_blobs(sha256,artifact_id,bytes,mime_type,
        logical_filename,producer,retention_class,created_at,payload)
        VALUES(%s,%s,%s,'application/json','synthetic-preparation','test-fixture',
        'test-fixture',clock_timestamp()::text,%s) ON CONFLICT(sha256) DO NOTHING""",
        (sha, "fixture-preparation-" + sha, len(raw), raw),
    )
    return {"preparation_sha256": sha}


def stored_preparation(conn, request_id, value=None):
    import json

    row = conn.execute(
        "SELECT record_json FROM v4_execution_dispatch_bindings WHERE request_id=%s", (request_id,),
    ).fetchone()
    return store_artifact(conn, preparation(json.loads(row["record_json"]), value))
