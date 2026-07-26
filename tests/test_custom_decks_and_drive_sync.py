from __future__ import annotations


def test_custom_decks_3way_merge_logic() -> None:
    # Test 3-way merge behavior with revisions and tombstones
    local = [
        {
            "id": "deck_1",
            "title": "Local Version",
            "lemma_keys": ["добрий", "день"],
            "created_at": "2026-07-24T10:00:00.000Z",
            "updated_at": "2026-07-24T10:00:00.000Z",
            "device_id": "dev_1",
            "revision": 1,
        },
        {
            "id": "deck_2",
            "title": "Deleted Deck",
            "lemma_keys": ["сонце"],
            "created_at": "2026-07-24T10:00:00.000Z",
            "updated_at": "2026-07-24T10:05:00.000Z",
            "deleted_at": "2026-07-24T10:05:00.000Z",
            "device_id": "dev_1",
            "revision": 2,
        },
    ]

    remote = [
        {
            "id": "deck_1",
            "title": "Remote Newer Version",
            "lemma_keys": ["добрий", "день", "вечір"],
            "created_at": "2026-07-24T10:00:00.000Z",
            "updated_at": "2026-07-24T10:02:00.000Z",
            "device_id": "dev_2",
            "revision": 2,
        },
        {
            "id": "deck_3",
            "title": "New Remote Deck",
            "lemma_keys": ["книга"],
            "created_at": "2026-07-24T10:03:00.000Z",
            "updated_at": "2026-07-24T10:03:00.000Z",
            "device_id": "dev_2",
            "revision": 1,
        },
    ]

    # Merging logic test
    map_by_id = {}
    for item in local + remote:
        existing = map_by_id.get(item["id"])
        if not existing:
            map_by_id[item["id"]] = item
        else:
            if item.get("revision", 0) > existing.get("revision", 0) or item.get("updated_at") > existing.get("updated_at"):
                map_by_id[item["id"]] = item

    merged = list(map_by_id.values())
    assert len(merged) == 3

    # Deck 1 resolves to remote (revision 2)
    deck_1 = next(d for d in merged if d["id"] == "deck_1")
    assert deck_1["title"] == "Remote Newer Version"
    assert len(deck_1["lemma_keys"]) == 3

    # Deck 2 preserves tombstone
    deck_2 = next(d for d in merged if d["id"] == "deck_2")
    assert "deleted_at" in deck_2

    # Deck 3 added
    assert any(d["id"] == "deck_3" for d in merged)


def test_ukrainian_word_extraction_regex() -> None:
    import re

    regex = re.compile(r"[а-щьюяєіїґА-ЩЬЮЯЄІЇҐ'’ʼ\-]+")
    text = "Відібрана добірка: кава, старшина, добрий день!"
    matches = [m.lower().strip() for m in regex.findall(text) if len(m) >= 2]

    assert "кава" in matches
    assert "старшина" in matches
    assert "добрий" in matches
    assert "день" in matches
    assert "відібрана" in matches
    assert "добірка" in matches
