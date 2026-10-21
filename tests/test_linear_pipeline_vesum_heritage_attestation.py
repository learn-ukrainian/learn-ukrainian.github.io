from __future__ import annotations

from scripts.build.linear_pipeline import _vesum_heritage_attestation_enabled


def test_vesum_heritage_attestation_enabled_for_folk_and_seminar_levels() -> None:
    assert _vesum_heritage_attestation_enabled("folk") is True
    assert _vesum_heritage_attestation_enabled("hist") is True
