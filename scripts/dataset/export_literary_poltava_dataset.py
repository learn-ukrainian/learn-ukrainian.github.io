"""Refuse regeneration of the audited Literary Poltava candidate.

The committed candidate has the collection verdict ``rebuild_required``.  It
must not be regenerated in place because its replacement would lose the frozen
evidence that records why it is not eligible for training or publication.
"""

class LiteraryCandidateSafetyError(RuntimeError):
    """Raised when an executable path targets the failed literary candidate."""


def refuse_rebuild_required_candidate() -> None:
    """Stop before opening the database or creating/replacing any output."""
    raise LiteraryCandidateSafetyError(
        "Refusing to export hramatka_literary_poltava_v1: audit #6058 marks "
        "this candidate rebuild_required. Create a rights-cleared replacement "
        "collection instead of regenerating the committed candidate."
    )


def export_literary_dataset(limit: int = 5000) -> None:
    """Refuse the unsafe export entry point before any side effect occurs."""
    del limit
    refuse_rebuild_required_candidate()


if __name__ == "__main__":
    export_literary_dataset()
