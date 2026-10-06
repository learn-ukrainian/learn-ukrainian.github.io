"""Pages policy is independent of component ownership and keeps its denominator."""

from __future__ import annotations

import pytest

from scripts.ci import components
from scripts.deploy import auto_deploy_eligibility as pages


@pytest.mark.parametrize(("path", "deploy", "reason"), [
    ("site/src/pages/index.astro", True, "site_code_only"),
    ("packages/activity-kit/src/index.ts", True, "site_code_only"),
    ("site/src/data/lexicon-manifest.pointer.json", True, "site_code_only"),
    ("site/src/data/lexicon-practice-deck.pointer.json", True, "site_code_only"),
    ("site/src/data/new-pointer.json", False, "content_drift"),
    ("site/src/lib/lexicon/curated-heteronyms.ts", False, "content_drift"),
    ("site/src/content/lesson.mdx", False, "content_drift"),
    ("curriculum/l2-uk-en/curriculum.yaml", False, "content_drift"),
    ("registry/practice/allowlist.yaml", False, "content_drift"),
    ("data/new.json", False, "content_drift"),
    ("scripts/atlas/atlas_db.py", False, "unknown_path"),
    ("new-root/new.ts", False, "unknown_path"),
])
def test_pages_decision_and_frontend_closure(path, deploy, reason):
    decision = pages.decide_auto_deploy([path])
    assert (decision.deploy, decision.reason) == (deploy, reason)
    manifest = components.load_manifest()
    if deploy:
        assert set(manifest["selector_contracts"]["frontend_components"]) <= set(components.affected([path], manifest)["components"])


def test_every_tracked_pages_eligible_path_covers_all_frontend_consumers():
    manifest = components.load_manifest()
    graph = components.import_graph(manifest)
    paths = components.tracked_paths()
    eligible = [path for path in paths if pages.decide_auto_deploy([path]).deploy]
    assert eligible
    fronts = set(manifest["selector_contracts"]["frontend_components"])
    assert all(fronts <= set(components.affected([path], manifest, graph)["components"]) for path in eligible)


def test_empty_and_mixed_pages_changes_keep_fail_closed_semantics():
    assert pages.decide_auto_deploy([]).reason == "no_changed_paths"
    assert pages.decide_auto_deploy(["site/src/pages/index.astro", "docs/a.md"]).reason == "unknown_path"
    assert pages.decide_auto_deploy(["site/src/pages/index.astro", "curriculum/a.yaml"]).reason == "content_drift"
