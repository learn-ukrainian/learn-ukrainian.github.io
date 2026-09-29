"""Deliberate broken test module for issue #9183 proof."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.needs_artifact("group", "rel")

raise RuntimeError("DELIBERATE_COLLECTION_ERROR_PROOF_9183")
