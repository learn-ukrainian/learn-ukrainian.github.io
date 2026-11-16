"""Removed machinery copies stay out of the product tree (#13032 slices 3 to 5).

Defect class: a machinery module deleted from ``scripts/`` comes back, and product code
imports that in-tree copy instead of the installed lu-machinery release, so the two drift.
"""

from __future__ import annotations

import importlib.util

import pytest

# Slice 3 to 5 modules the product now takes from the installed release (or that the release retired).
REMOVED_COPIES = (
    "scripts.agent_runtime.acp_health",
    "scripts.agent_runtime.adapters._template",
    "scripts.agent_runtime.attempt_forwarder",
    "scripts.agent_runtime.attempt_proxy",
    "scripts.agent_runtime.bounded_advisory",
    "scripts.agent_runtime.bounded_command",
    "scripts.agent_runtime.codex_accounts",
    "scripts.agent_runtime.mechanical_admission",
    "scripts.agent_runtime.review_mcp",
    "scripts.agent_runtime.tool_config",
    "scripts.ai_llm.agent_runtime_call",
    "scripts.ai_llm.claude_call",
    "scripts.ai_llm.cooldown",
    "scripts.ai_llm.fallback",
    "scripts.bakeoff.run_b1_writer",
    "scripts.bakeoff.score_b1_writer_output",
    "scripts.canary.kimi_oauth_canary",
    "scripts.debug.debug_pymorphy",
    "scripts.debug.debug_stanza",
    "scripts.debug.fetch_debug",
    "scripts.debug.test_regex",
    "scripts.debug.test_regex_cloze",
    "scripts.docs.find",
    "scripts.docs.migrate_to_html",
    "scripts.goal_driver.size_cap",
    "scripts.guardrails.delegate_ownership",
    "scripts.guardrails.primary_write_guard",
    "scripts.hygiene.batch_state_retention",
    "scripts.hygiene.branch_sweep",
    "scripts.hygiene.check_node_modules_integrity",
    "scripts.hygiene.check_primary_integrity",
    "scripts.hygiene.check_self_symlinks",
    "scripts.hygiene.check_tmp_usability",
    "scripts.hygiene.check_venv_integrity",
    "scripts.hygiene.check_worktree_cleanup_integrity",
    "scripts.hygiene.codex_rollout_reconcile",
    "scripts.hygiene.fetch_refspecs",
    "scripts.hygiene.home_session_retention_check",
    "scripts.hygiene.inventory_home_sessions",
    "scripts.hygiene.lane_disk_retention",
    "scripts.hygiene.preserved_retention",
    "scripts.hygiene.primary_dirt_cleanup",
    "scripts.hygiene.retention_engine",
    "scripts.hygiene.tmp_sweep_ledger",
    "scripts.maintenance.batch_state_retention",
    "scripts.maintenance.claude_session_scratch",
    "scripts.maintenance.github_cache",
    "scripts.ops.context_guard",
    "scripts.ops.host_stack_drift",
    "scripts.ops.lane_relaunch",
    "scripts.ops.product_entry",
    "scripts.research.consumption",
    "scripts.research.observability",
    "scripts.research.registry",
    "scripts.research.research_markdown_utils",
    "scripts.research.research_quality",
    "scripts.telemetry.cost_report",
    "scripts.telemetry.emit",
    "scripts.telemetry.legacy_bridge",
    "scripts.tools.agent_watcher",
    "scripts.tools.coverage_report",
    "scripts.utils.claude_version",
    "scripts.work.attention",
    "scripts.work.normalize",
    "scripts.work.relations",
    "scripts.work.sources_public",
)


def _spec(name: str) -> importlib.machinery.ModuleSpec | None:
    try:
        return importlib.util.find_spec(name)
    except ModuleNotFoundError:  # the parent package is gone as well
        return None


@pytest.mark.parametrize("module", REMOVED_COPIES)
def test_removed_machinery_copy_is_not_importable(module: str) -> None:
    assert _spec(module) is None, f"{module} is importable from the product tree again"
