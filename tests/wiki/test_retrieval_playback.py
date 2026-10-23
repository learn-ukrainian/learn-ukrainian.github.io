import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from wiki.diagnostics import retrieval_playback


def _chunk(chunk_id: str, text: str, grade: str = "2") -> dict[str, str]:
    return {
        "chunk_id": chunk_id,
        "text": text,
        "grade": grade,
        "title": f"Chunk {chunk_id}",
        "author": "test",
    }


def test_match_returned_concepts_normalizes_apostrophes():
    chunks = [
        _chunk(
            "apostrophe",
            "Після приголосних букви я, ю, є позначають один звук і пом’якшують попередній приголосний.",
        )
    ]

    results = retrieval_playback.match_returned_concepts(chunks)

    assert results["ya_yu_ye_dual"]["present_in_returned_41"] is True
    assert results["ya_yu_ye_dual"]["chunks_containing"] == ["apostrophe"]
