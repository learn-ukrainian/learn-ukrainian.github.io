"""Regression tests for duplicate agent names in runtime agent listings.

Issue #7082: ``/api/runtime/agents`` (and ``/api/orient`` ``runtime.agents``,
which shares the same source list) surfaced ``deepseek`` twice because the
alternate-harness ``hermes_deepseek`` adapter re-exports the fleet name
``deepseek``. Alternate-harness adapters (``hermes_*``) are ask-hermes-only
and must not appear as separate fleet agents.
"""

from __future__ import annotations

from scripts.api.monitor_context import production_context
from scripts.api.runtime_router import list_runtime_agents


def test_list_runtime_agents_names_are_unique():
    agents = list_runtime_agents(production_context())

    names = [agent["name"] for agent in agents]
    assert len(names) == len(set(names)), f"duplicate agent names: {sorted(names)}"
