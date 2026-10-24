"""The Sources reader must observe in-place card spelling rewrites (#11084)."""

import importlib.util
import json
import sys
from pathlib import Path

from tests.mcp.sources_probe_fixture import word_card as make_card

MODULE_PATH = Path(__file__).resolve().parents[1] / ".mcp/servers/sources/word_card.py"
_spec = importlib.util.spec_from_file_location("word_card_index_under_test", MODULE_PATH)
word_card = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = word_card
_spec.loader.exec_module(word_card)


def test_in_place_spelling_rewrite_invalidates_reader_index(tmp_path):
    cards = tmp_path / "cards"
    cards.mkdir()
    card = make_card("wc_aaaaaaaaaaaa", "мова")
    path = cards / f"{card['card_id']}.json"
    path.write_text(json.dumps(card, ensure_ascii=False), encoding="utf-8")
    env = {word_card.ENV_WORD_CARDS_DIR: str(tmp_path)}

    def lookup(spelling):
        return word_card.lookup_word_card(spelling, env=env, vesum_lookup=lambda _: [])

    initial = lookup("мова")
    assert initial["result"] == "card_found"
    assert initial["cards"][0]["card_id"] == "wc_aaaaaaaaaaaa"
    directory_mtime = cards.stat().st_mtime_ns
    inode = path.stat().st_ino

    card["key_at_creation"]["spelling"] = "баран"
    path.write_text(json.dumps(card, ensure_ascii=False), encoding="utf-8")
    assert path.stat().st_ino == inode
    assert cards.stat().st_mtime_ns == directory_mtime

    changed = lookup("баран")
    assert changed["result"] == "card_found"
    assert changed["cards"][0]["card_id"] == "wc_aaaaaaaaaaaa"
    assert changed["cards"][0]["identity"]["spelling"] == "баран"
    old = lookup("мова")
    assert old["result"] == "no_card"
    assert old["cards"] == []
