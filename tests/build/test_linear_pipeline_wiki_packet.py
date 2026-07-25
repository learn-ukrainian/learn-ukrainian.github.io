from __future__ import annotations

import builtins
from typing import Any

from scripts.build import linear_pipeline


def test_build_knowledge_packet_reads_wiki_and_sources(monkeypatch) -> None:
    plan_path = linear_pipeline.plan_path_for("a1", "my-morning")
    plan = linear_pipeline.load_plan(plan_path)

    real_import = builtins.__import__

    def guarded_import(
        name: str,
        globals: dict[str, Any] | None = None,
        locals: dict[str, Any] | None = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> Any:
        blocked = {
            "scripts.rag",
            "scripts.rag.query",
            "scripts.build.research.build_knowledge_packet",
            "build.research.build_knowledge_packet",
        }
        if name in blocked or name.startswith("scripts.rag."):
            raise AssertionError(f"deprecated import attempted: {name}")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)

    packet = linear_pipeline.build_knowledge_packet(
        level="a1",
        slug="my-morning",
        plan=plan,
    )

    # 295d27ea1a ("fix(writer-prompt): ULP S1 baseline...") replaced the verbatim
    # "## Full Wiki Context" dump with compressed targeted excerpts to fit the
    # 130KB writer-prompt ceiling — raw article prose (and its S1=/S9= source-key
    # mapping) is deliberately no longer duplicated in the packet.
    assert "Подача теми «Мій ранок»" not in packet
    assert "Do not duplicate the full article text in the writer prompt" in packet
    assert "зворотних дієслів" in packet
    assert "pedagogy/a1/my-morning.md" in packet
    assert "[S1" in packet
    assert "mcp__sources__verify_lemma" in packet
    assert "mcp__sources__search_style_guide" in packet
    assert "mcp__sources__search_definitions" in packet
    assert "scripts.rag" in packet


def test_build_knowledge_packet_accepts_legacy_plan_path() -> None:
    packet = linear_pipeline.build_knowledge_packet(
        linear_pipeline.plan_path_for("a1", "my-morning")
    )

    assert "# Knowledge Packet: Мій ранок" in packet
    assert "**Retrieval:** compiled wiki + MCP sources, no Qdrant" in packet
