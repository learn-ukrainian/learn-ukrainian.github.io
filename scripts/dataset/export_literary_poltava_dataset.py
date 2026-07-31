"""Refuse regeneration of the audited Literary Poltava candidate.

The committed candidate has the collection verdict ``rebuild_required``.  It
must not be regenerated in place because its replacement would lose the frozen
evidence that records why it is not eligible for training or publication.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATASET_DIR = REPO_ROOT / "data" / "datasets" / "hramatka_literary_poltava_v1"
CANDIDATE_JSONL = DATASET_DIR / "hramatka_literary_poltava_v1.jsonl"


class LiteraryCandidateSafetyError(RuntimeError):
    """Raised when an executable path targets the failed literary candidate."""


def refuse_rebuild_required_candidate() -> None:
    """Stop before opening the database or creating/replacing any output."""
    raise LiteraryCandidateSafetyError(
        "Refusing to export hramatka_literary_poltava_v1: audit #6058 marks "
        "this candidate rebuild_required. Create a rights-cleared replacement "
        "collection instead of regenerating the committed candidate."
    )


def export_literary_dataset(limit: int = 5000) -> dict[str, object]:
    """Refuse the unsafe export entry point before any side effect occurs."""
    del limit
    refuse_rebuild_required_candidate()


if __name__ == "__main__":
    export_literary_dataset()
