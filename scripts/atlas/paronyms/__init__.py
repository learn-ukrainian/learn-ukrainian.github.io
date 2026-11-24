"""Source-attested Ukrainian paronym extraction and VESUM verification for Atlas word cards."""

from .extractor import (
    MemberNote,
    RawPairAttestation,
    SourceDocument,
    extract_from_document,
)

__all__ = [
    "MemberNote",
    "RawPairAttestation",
    "SourceDocument",
    "extract_from_document",
]
