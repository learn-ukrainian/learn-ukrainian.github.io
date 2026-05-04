import asyncio
import sys
from pathlib import Path

from mcp.types import TextContent

# Add .mcp/servers/sources/ to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / ".mcp" / "servers" / "sources"))
from server import handle_dict_search


def test_search_antonenko_pryimaty_uchast():
    args = {"query": "приймати участь", "limit": 3}
    results = asyncio.run(handle_dict_search(args, "style_guide", "Антоненко-Давидович"))

    assert len(results) == 1
    assert isinstance(results[0], TextContent)
    text = results[0].text

    assert "Found" in text
    assert "брати участь" in text.lower() or "приймати участь" in text.lower()

def test_search_antonenko_virnyi():
    args = {"query": "вірний", "limit": 3}
    results = asyncio.run(handle_dict_search(args, "style_guide", "Антоненко-Давидович"))

    text = results[0].text
    assert "Found" in text
    # actual commentary text assertion
    assert "вірний" in text.lower()
    assert "певний" in text.lower() or "правильний" in text.lower()

def test_search_antonenko_zamisnyk():
    args = {"query": "замісник", "limit": 3}
    results = asyncio.run(handle_dict_search(args, "style_guide", "Антоненко-Давидович"))

    text = results[0].text
    assert "Found" in text
    assert "заступник" in text.lower() or "замісник" in text.lower()

def test_search_antonenko_bolilnyk():
    args = {"query": "болільник", "limit": 3}
    results = asyncio.run(handle_dict_search(args, "style_guide", "Антоненко-Давидович"))

    text = results[0].text
    assert "Found" in text
    assert "вболівальник" in text.lower() or "болільник" in text.lower()

def test_search_antonenko_pidpys():
    args = {"query": "підпис", "limit": 3}
    results = asyncio.run(handle_dict_search(args, "style_guide", "Антоненко-Давидович"))

    text = results[0].text
    assert "Found" in text
    assert "розпис" in text.lower() or "підпис" in text.lower()

def test_search_antonenko_negative():
    args = {"query": "xxxx", "limit": 3}
    results = asyncio.run(handle_dict_search(args, "style_guide", "Антоненко-Давидович"))

    text = results[0].text
    assert "No results in Антоненко-Давидович for: \"xxxx\"" in text
