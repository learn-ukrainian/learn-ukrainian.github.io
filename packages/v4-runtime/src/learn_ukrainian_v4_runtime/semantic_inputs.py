"""Immutable, permitted semantic inputs transported by the service parent."""

from __future__ import annotations

import json

from learn_ukrainian_v4_runtime.operation_auth import OperationRefused, canonical_bytes, digest
from learn_ukrainian_v4_runtime.resources import resource_root

CONSTRAINT_KEYS = frozenset({"task_kind", "cefr_level", "required_fields", "allowed_evidence_tools"})
TOOLS = frozenset({"verify_word", "verify_words", "verify_lemma", "verify_stress", "check_modern_form"})


def validate_constraints(value: dict) -> None:
    if not isinstance(value, dict) or set(value) != CONSTRAINT_KEYS:
        raise OperationRefused("admitted_constraints_required")
    if value["cefr_level"] not in ("A1", "A2", "B1", "B2", "C1", "C2"):
        raise OperationRefused("constraint_level")
    if value["task_kind"] not in ("original_row", "correction", "explanation", "exercise"):
        raise OperationRefused("constraint_task")
    fields = value["required_fields"]
    if (
        not isinstance(fields, list)
        or not fields
        or len(fields) != len(set(fields))
        or not set(fields) <= {"row_text", "explanation", "answer", "instruction"}
        or "row_text" not in fields
    ):
        raise OperationRefused("constraint_fields")
    tools = value["allowed_evidence_tools"]
    if not isinstance(tools, list) or not tools or not set(tools) <= TOOLS or len(tools) != len(set(tools)):
        raise OperationRefused("constraint_tools")


def rubric_bytes() -> bytes:
    return (resource_root() / "data/projects/open_model_data/trust/v4_review_rubric_v1.txt").read_bytes()


def prompt_from_snapshot(binding: dict, snapshot: dict) -> str:
    if binding["role"] == "author":
        if set(snapshot) != {"constraints"}:
            raise OperationRefused("author_snapshot")
        validate_constraints(snapshot["constraints"])
        payload = {
            "role": "author",
            "slot_id": binding["slot_id"],
            "packet_sha256": binding["packet_sha256"],
            "constraints": snapshot["constraints"],
        }
        instructions = "Author one original row satisfying every admitted constraint. Emit V4-AUTHOR-ROW: followed by its JSON object."
    elif binding["role"] == "reviewer":
        if set(snapshot) != {"authored_row", "constraints", "rubric_sha256"}:
            raise OperationRefused("reviewer_snapshot")
        validate_constraints(snapshot["constraints"])
        row = snapshot["authored_row"]
        if not isinstance(row, dict) or not isinstance(row.get("row_text"), str) or not row["row_text"]:
            raise OperationRefused("authored_row_required")
        if not set(row) <= {"row_text", "explanation", "answer", "instruction"}:
            raise OperationRefused("authored_row_keys")
        rubric = rubric_bytes()
        if snapshot["rubric_sha256"] != digest(rubric) or binding["rubric_sha256"] != digest(rubric):
            raise OperationRefused("rubric_digest")
        payload = {
            "role": "reviewer",
            "authored_row": row,
            "constraints": snapshot["constraints"],
            "rubric": rubric.decode(),
            "authorship_receipt_sha256": binding["authorship_receipt_sha256"],
        }
        instructions = "Evaluate the actual authored row against every constraint and the fixed rubric. Emit exactly V4-REVIEW-VERDICT: PASS or V4-REVIEW-VERDICT: FAIL."
    else:
        raise OperationRefused("operation_role")
    return (
        f"V4_PROMPT_PROFILE={binding['prompt_profile']}\n{instructions}\nV4-SEMANTIC-INPUT: "
        + json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    )


def freeze_semantic_input(conn, *, request_id: str, snapshot: dict) -> None:
    """Trusted preparation of an already assigned binding, never an API route.

    The existing private preparation adapter resolves the admitted constraints
    and canonical author artifact before calling this operation. Locking binds
    the exact snapshot before any external authorization can be armed.
    """
    with conn.transaction():
        request = conn.execute("SELECT state FROM requests WHERE request_id=%s FOR UPDATE", (request_id,)).fetchone()
        row = conn.execute(
            "SELECT * FROM v4_execution_dispatch_bindings WHERE request_id=%s FOR UPDATE", (request_id,)
        ).fetchone()
        if request is None or request["state"] != "queued" or row is None or row["semantic_input_json"] is not None:
            raise OperationRefused("assignment_not_freezable")
        binding = json.loads(row["record_json"])
        if binding["role"] == "reviewer":
            authorship = conn.execute(
                "SELECT record_json FROM v4_authorship_receipts WHERE receipt_id=%s",
                (binding["authorship_receipt_id"],),
            ).fetchone()
            if authorship is None:
                raise OperationRefused("authorship_unresolved")
            receipt = json.loads(authorship["record_json"])
            if digest(snapshot["authored_row"]["row_text"].encode()) != receipt["row_content_sha256"]:
                raise OperationRefused("authored_row_digest")
        prompt = prompt_from_snapshot(binding, snapshot)
        binding["prompt_sha256"] = digest(prompt.encode())
        body = canonical_bytes(binding)
        conn.execute(
            "UPDATE v4_execution_dispatch_bindings SET record_json=%s,record_sha256=%s,semantic_input_json=%s WHERE request_id=%s",
            (body.decode(), digest(body), canonical_bytes(snapshot).decode(), request_id),
        )
