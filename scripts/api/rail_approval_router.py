"""Read-only Monitor API projection for human-issued rail approvals."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from scripts.orchestration.rail_approval import (
    RailApprovalReceiptRegistry,
    RailApprovalStoreError,
)
from scripts.orchestration.rail_path_guard import RAIL_APPROVAL_RECEIPT_ID

router = APIRouter(tags=["rail-approvals"])


def get_rail_approval_registry() -> RailApprovalReceiptRegistry:
    """Build the local registry only inside the provisioned Monitor process."""
    return RailApprovalReceiptRegistry()


@router.get("/{receipt_id}")
def get_rail_approval_receipt(receipt_id: str) -> dict:
    """Return one immutable receipt for an enforcement-layer re-fetch."""
    if RAIL_APPROVAL_RECEIPT_ID.fullmatch(receipt_id) is None:
        # Client error, not store unavailability: a malformed id can never
        # resolve, so it must not read as a retryable 503.
        raise HTTPException(status_code=422, detail="malformed rail approval receipt id")
    try:
        return get_rail_approval_registry().fetch(receipt_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="rail approval receipt not found") from exc
    except RailApprovalStoreError as exc:
        raise HTTPException(status_code=503, detail="rail approval store unavailable") from exc
