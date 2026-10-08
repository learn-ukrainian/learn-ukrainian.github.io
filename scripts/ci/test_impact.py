import ast
import multiprocessing

from scripts.ci.components import assign_path, load_manifest, python_sources, test_files


def parse_file(item):
    f, b = item
    if not f.endswith(".py"):
        return f, set(), False, False
    try:
        tree = ast.parse(b, f)
    except Exception:
        return f, set(), False, True # parse error

    imports = set()
    dynamic = False

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)
                for alias in node.names:
                    imports.add(f"{node.module}.{alias.name}")
        elif isinstance(node, ast.Call):
            name = ""
            if isinstance(node.func, ast.Name):
                name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                name = node.func.attr
            if name in ('__import__', 'import_module') and (not node.args or not isinstance(node.args[0], ast.Constant) or not isinstance(node.args[0].value, str)):
                dynamic = True

    return f, imports, dynamic, False

def build_graph():
    sources = python_sources()
    with multiprocessing.Pool() as pool:
        results = pool.map(parse_file, sources.items(), chunksize=100)

    file_to_module = {}
    for f in sources:
        if not f.endswith(".py"):
            continue
        mod = f[:-3].replace("/", ".")
        if mod.endswith(".__init__"):
            mod = mod[:-9]
        file_to_module[f] = mod

    module_to_files = {}
    for f, mod in file_to_module.items():
        module_to_files[mod] = f

    dependents = {f: set() for f in file_to_module}
    file_dynamic = set()
    file_parse_error = set()

    for f, imports, dyn, err in results:
        if err:
            file_parse_error.add(f)
            continue
        if dyn:
            file_dynamic.add(f)

        if imports:
            for imp in imports:
                parts = imp.split(".")
                for i in range(1, len(parts) + 1):
                    sub_mod = ".".join(parts[:i])
                    if sub_mod in module_to_files:
                        target_f = module_to_files[sub_mod]
                        if target_f != f:
                            dependents[target_f].add(f)

    return dependents, file_dynamic, file_parse_error

def get_impacted_tests(changed_files):
    dependents, file_dynamic, file_parse_error = build_graph()

    for f in changed_files:
        if f in file_parse_error:
            return {"full_suite": True, "reason": "parse error"}
        if f in file_dynamic:
            return {"full_suite": True, "reason": "dynamic or non-literal imports"}
        if f not in dependents or not dependents[f]:
            return {"full_suite": True, "reason": "no dependents"}

    # transitive closure
    impacted_files = set()
    queue = list(changed_files)
    visited = set(changed_files)

    while queue:
        curr = queue.pop(0)
        if curr in dependents:
            for dep in dependents[curr]:
                if dep not in visited:
                    visited.add(dep)
                    queue.append(dep)
                    impacted_files.add(dep)

    # tests that import the script
    impacted_tests = {f for f in impacted_files if f.startswith("tests/") and f.endswith(".py")}

    # existing safety net
    manifest = load_manifest()
    safety_net_tests = set()
    for f in changed_files:
        owners, _ = assign_path(f, manifest)
        for owner in owners:
            safety_net_tests.update(test_files(owner, manifest))

    impacted_tests.update(safety_net_tests)

    return {"full_suite": False, "tests": sorted(list(impacted_tests))}
