import subprocess
import time

from scripts.ci.components import assign_path, import_graph, load_manifest
from scripts.ci.components import test_files as components_test_files
from scripts.ci.test_impact import build_graph, get_impacted_tests


def test_graph_build_under_10_seconds():
    t0 = time.time()
    res = get_impacted_tests(["scripts/ci/test_impact.py"])
    assert time.time() - t0 < 10.0

def test_zero_missed_importers():
    manifest = load_manifest()
    graph = import_graph(manifest)
    file_edges = graph["file_edges"]

    true_dependents = {}
    for edge in file_edges:
        producer = edge[0]
        consumer = edge[1]
        if producer not in true_dependents:
            true_dependents[producer] = set()
        true_dependents[producer].add(consumer)

    _my_dependents, _my_dyn, _my_err = build_graph()

    out = subprocess.check_output(["git", "log", "--merges", "-n", "30", "--pretty=format:%H"], timeout=30)
    commits = out.decode().strip().split()

    for commit in commits:
        files = subprocess.check_output(["git", "diff-tree", "--no-commit-id", "--name-only", "-r", commit], timeout=30).decode().split()
        changed_files = [f for f in files if f.endswith(".py")]
        if not changed_files:
            continue

        my_res = get_impacted_tests(changed_files)
        if my_res["full_suite"]:
            continue
        my_tests = set(my_res["tests"])

        true_impacted = set()
        queue = list(changed_files)
        visited = set(changed_files)
        while queue:
            curr = queue.pop(0)
            if curr in true_dependents:
                for dep in true_dependents[curr]:
                    if dep not in visited:
                        visited.add(dep)
                        queue.append(dep)
                        true_impacted.add(dep)

        true_tests = {f for f in true_impacted if f.startswith("tests/") and f.endswith(".py")}

        safety_net = set()
        for f in changed_files:
            owners, _ = assign_path(f, manifest)
            for o in owners:
                safety_net.update(components_test_files(o, manifest))
        true_tests.update(safety_net)

        missing = true_tests - my_tests
        assert not missing, f"Commit {commit} missed importers: {missing}"
