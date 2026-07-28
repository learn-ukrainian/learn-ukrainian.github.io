"""Read-only Monitor API projection for human-issued rail approvals."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from scripts.orchestration.rail_approval import (
    RailApprovalReceiptRegistry,
    RailApprovalStoreError,
)

router = APIRouter(tags=["rail-approvals"])


def get_rail_approval_registry() -> RailApprovalReceiptRegistry:
    """Build the local registry only inside the provisioned Monitor process."""
    return RailApprovalReceiptRegistry()


@router.get("/{receipt_id}")
def get_rail_approval_receipt(receipt_id: str) -> dict:
    """Return one immutable receipt for an enforcement-layer re-fetch."""
    try:
        return get_rail_approval_registry().fetch(receipt_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="rail approval receipt not found") from exc
    except RailApprovalStoreError as exc:
        raise HTTPException(status_code=503, detail="rail approval store unavailable") from exc
