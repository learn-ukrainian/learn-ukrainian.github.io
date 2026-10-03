"""Keep Unicode line separators inside structured records (#9556).

Intraprocedural data flow follows assignments, loop/comprehension variables,
container mutations, and local parser wrappers. A split is only reported when
its output reaches a JSON parser; merely sharing a function is not sufficient.
The exceptions identify reviewed byte readers, non-record diagnostic text,
and frozen sources whose release receipts prohibit byte changes.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
# (repository-relative path, qualified function): reviewed disposition and exact call(s).
ALLOWLIST: dict[tuple[str, str], tuple[str, str | tuple[str, ...]]] = {
    ("scripts/agent_runtime/adapters/agy.py", "_read_transcript_events"): (
        "Bytes are split before UTF-8 decoding; bytes.splitlines preserves NEL, LS and PS.",
        "safe_read_attempt_file(transcript_path, offset=offset, trusted_root=trusted_root).splitlines()",
    ),
    ("scripts/projects/open_model_data/correction_protection_consumer.py", "public_bundle"): (
        "Bytes are split before UTF-8 decoding; bytes.splitlines preserves NEL, LS and PS.",
        "raw.splitlines()",
    ),
    ("scripts/projects/open_model_data/correction_protection_consumer.py", "verify_release"): (
        "Bytes are split before UTF-8 decoding; bytes.splitlines preserves NEL, LS and PS.",
        "raw.splitlines()",
    ),
    ("scripts/projects/open_model_data/phase3_evaluation_context_manifest.py", "_parse_jsonl_bytes"): (
        "Bytes are split before UTF-8 decoding; bytes.splitlines preserves NEL, LS and PS.",
        "raw.splitlines(keepends=True)",
    ),
    ("scripts/projects/open_model_data/phase3_evaluation_freeze.py", "_private_partition_rows"): (
        "Bytes are split before UTF-8 decoding; bytes.splitlines preserves NEL, LS and PS.",
        "path.read_bytes().splitlines()",
    ),
    ("scripts/projects/open_model_data/phase3_fixed_release.py", "_read_jsonl"): (
        "Bytes are split before UTF-8 decoding; bytes.splitlines preserves NEL, LS and PS.",
        "path.read_bytes().splitlines()",
    ),
    ("scripts/projects/open_model_data/phase3_heldout_label_transport.py", "_materialization"): (
        "Bytes are split before UTF-8 decoding; bytes.splitlines preserves NEL, LS and PS.",
        "raw.splitlines()",
    ),
    ("scripts/projects/open_model_data/phase3_heldout_label_transport.py", "_partition"): (
        "Bytes are split before UTF-8 decoding; bytes.splitlines preserves NEL, LS and PS.",
        "raw.splitlines()",
    ),
    ("scripts/projects/open_model_data/phase3_heldout_label_transport.py", "_jsonl"): (
        "Bytes are split before UTF-8 decoding; bytes.splitlines preserves NEL, LS and PS.",
        "path.read_bytes().splitlines()",
    ),
    ("scripts/projects/open_model_data/phase3_middle_ukrainian_page_sample.py", "_load_source_rows"): (
        "Bytes are split before UTF-8 decoding; bytes.splitlines preserves NEL, LS and PS.",
        "source_jsonl.read_bytes().splitlines(keepends=True)",
    ),
    ("scripts/projects/open_model_data/phase3_pravopys_evaluation_context.py", "_parse_jsonl_bytes"): (
        "Bytes are split before UTF-8 decoding; bytes.splitlines preserves NEL, LS and PS.",
        "raw.splitlines(keepends=True)",
    ),
    (
        "scripts/projects/open_model_data/phase3_school_context_negative_recovery.py",
        "_assert_public_ledger_lacks_parent_boundaries",
    ): (
        "Bytes are split before UTF-8 decoding; bytes.splitlines preserves NEL, LS and PS.",
        "_school_ledger_bytes().splitlines()",
    ),
    ("scripts/review/receipts/ledger.py", "records"): (
        "Bytes are split before UTF-8 decoding; bytes.splitlines preserves NEL, LS and PS.",
        "content.splitlines()",
    ),
    ("scripts/agent_runtime/adapters/agy.py", "_parse_stdout_marker_tool_calls"): (
        "Human CLI marker telemetry with optional inline argument coercion, not JSONL record parsing.",
        "text.splitlines()",
    ),
    ("scripts/agent_runtime/failure_codes.py", "provider_stderr_error"): (
        "Diagnostic lines locate an API Error wrapper; raw_decode receives a slice of the original stderr, not split lines.",
        "stderr.splitlines(keepends=True)",
    ),
    # Frozen receipt bindings: UA v0.1.0/v0.1.1 manifests, Gemma paths.py,
    # and phase3_v2_compatibility.MIGRATED_ENGINE_SOURCE_SHA256.
    ("scripts/projects/open_model_data/gemma_hardware_probe.py", "collect_job"): (
        "hash-pinned frozen source; changing bytes breaks its release receipt",
        "logs_result.stdout.splitlines()",
    ),
    ("scripts/projects/open_model_data/phase3_disposition_audit.py", "_source_receipt"): (
        "hash-pinned frozen source; changing bytes breaks its release receipt",
        "ledger_path.read_text(encoding='utf-8').splitlines()",
    ),
    ("scripts/projects/open_model_data/phase3_heldout_partition.py", "_load_freeze_ua_gec_units"): (
        "hash-pinned frozen source; changing bytes breaks its release receipt",
        ("snapshot.artifacts[member].decode('utf-8').splitlines()", "path.read_text(encoding='utf-8').splitlines()"),
    ),
    ("scripts/projects/open_model_data/phase3_pravopys_delta.py", "_read_jsonl"): (
        "hash-pinned frozen source; changing bytes breaks its release receipt",
        "path.read_text(encoding='utf-8').splitlines()",
    ),
    ("scripts/projects/open_model_data/phase3_source_dispositions.py", "_ledger_records"): (
        "hash-pinned frozen source; changing bytes breaks its release receipt",
        "path.read_text(encoding='utf-8').splitlines()",
    ),
    ("scripts/projects/open_model_data/phase3_source_production_transport.py", "_strict_response"): (
        "hash-pinned frozen source; changing bytes breaks its release receipt",
        "text.splitlines()",
    ),
    ("scripts/projects/open_model_data/phase3_source_unit_materialization.py", "_read_ledger"): (
        "hash-pinned frozen source; changing bytes breaks its release receipt",
        "path.read_text(encoding='utf-8').splitlines()",
    ),
    ("scripts/projects/ua_eval_harness/evaluate_model.py", "_read_jsonl"): (
        "hash-pinned frozen source; changing bytes breaks its release receipt",
        "path.read_text(encoding='utf-8').splitlines()",
    ),
    ("scripts/projects/ua_eval_harness/run_model_batch.py", "_read_jsonl"): (
        "hash-pinned frozen source; changing bytes breaks its release receipt",
        "path.read_text(encoding='utf-8').splitlines()",
    ),
    ("scripts/projects/ua_eval_harness/run_model_batch.py", "_ndjson_assistant_text"): (
        "hash-pinned frozen source; changing bytes breaks its release receipt",
        "raw_text.splitlines()",
    ),
}


def _call_name(node: ast.AST) -> str:
    return ast.unparse(node)


def _direct_parser(node: ast.Call, json_names: set[str], load_names: set[str]) -> bool:
    name = _call_name(node.func)
    return name in load_names or name in {f"{module}.loads" for module in json_names} or name.endswith(".raw_decode")


class _Flow:
    def __init__(self, parsers, json_names, load_names):
        self.parsers = parsers
        self.json_names = json_names
        self.load_names = load_names
        self.consumed: set[int] = set()
        self.splits: set[int] = set()

    def bind(self, target, value, env):
        if isinstance(target, ast.Name):
            env[target.id] = set(value)
        elif isinstance(target, (ast.Tuple, ast.List)):
            for item in target.elts:
                self.bind(item, value, env)
        elif isinstance(target, (ast.Subscript, ast.Attribute)):
            root = target
            while isinstance(root, (ast.Subscript, ast.Attribute)):
                root = root.value
            if isinstance(root, ast.Name):
                env.setdefault(root.id, set()).update(value)

    def expr(self, node, env):
        if node is None:
            return set()
        if isinstance(node, ast.Name):
            return env.get(node.id, set()).copy()
        if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            local = {key: value.copy() for key, value in env.items()}
            for gen in node.generators:
                self.bind(gen.target, self.expr(gen.iter, local), local)
                for condition in gen.ifs:
                    self.expr(condition, local)
            if isinstance(node, ast.DictComp):
                return self.expr(node.key, local) | self.expr(node.value, local)
            return self.expr(node.elt, local)
        if isinstance(node, ast.NamedExpr):
            value = self.expr(node.value, env)
            self.bind(node.target, value, env)
            return value
        if isinstance(node, ast.Call):
            values = [self.expr(arg, env) for arg in node.args]
            keywords = {kw.arg: self.expr(kw.value, env) for kw in node.keywords}
            receiver = self.expr(node.func.value, env) if isinstance(node.func, ast.Attribute) else set()
            if isinstance(node.func, ast.Attribute) and node.func.attr == "splitlines":
                self.splits.add(node.lineno)
                return {node.lineno}
            if isinstance(node.func, ast.Attribute) and node.func.attr in {
                "read_text",
                "read_bytes",
                "readline",
                "parse_args",
            }:
                return set()  # New input bytes, not bytes of the path/CLI description.
            if _call_name(node.func) == "_git":
                return set()  # Git output is not the bytes of its argv paths/SHAs.
            if _direct_parser(node, self.json_names, self.load_names):
                self.consumed.update(values[0] if values else keywords.get("s", set()))
                return set()
            sensitive = self.parsers.get(_call_name(node.func), {})
            for index, parameter in sensitive.items():
                self.consumed.update(values[index] if index < len(values) else keywords.get(parameter, set()))
            value = receiver | set().union(set(), *values, *keywords.values())
            if isinstance(node.func, ast.Attribute) and node.func.attr in {"append", "extend", "add", "update"}:
                self.bind(node.func.value, value, env)
            return value
        return set().union(set(), *(self.expr(child, env) for child in ast.iter_child_nodes(node)))

    def statements(self, nodes, env):
        for node in nodes:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue  # Each lexical scope is analyzed separately.
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                value = self.expr(node.value, env)
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for target in targets:
                    self.bind(target, value, env)
            elif isinstance(node, ast.AugAssign):
                self.bind(node.target, self.expr(node.target, env) | self.expr(node.value, env), env)
            elif isinstance(node, (ast.For, ast.AsyncFor)):
                self.bind(node.target, self.expr(node.iter, env), env)
                self.statements(node.body, env)
                self.statements(node.orelse, env)
            elif isinstance(node, (ast.If, ast.While)):
                self.expr(node.test, env)
                branches = []
                for body in (node.body, node.orelse):
                    branch = {key: value.copy() for key, value in env.items()}
                    self.statements(body, branch)
                    branches.append(branch)
                for key in set().union(*(set(branch) for branch in branches)):
                    env[key] = set().union(*(branch.get(key, set()) for branch in branches))
            elif isinstance(node, (ast.Try, ast.TryStar)):
                self.statements(node.body, env)
                for handler in node.handlers:
                    self.statements(handler.body, env)
                self.statements(node.orelse, env)
                self.statements(node.finalbody, env)
            elif isinstance(node, (ast.With, ast.AsyncWith)):
                for item in node.items:
                    value = self.expr(item.context_expr, env)
                    if item.optional_vars:
                        self.bind(item.optional_vars, value, env)
                self.statements(node.body, env)
            else:
                self.expr(node, env)


def _scopes(tree, prefix=""):
    yield prefix or "<module>", tree
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            name = f"{prefix}.{node.name}" if prefix else node.name
            yield from _scopes(node, name)


def analyze(source: str) -> tuple[dict[str, set[int]], dict[str, set[int]]]:
    """Return parser-consuming splits and every executable split, by scope."""
    tree = ast.parse(source)
    json_names = {"json"}
    load_names = {"_strict_json_loads"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            json_names.update(alias.asname or "json" for alias in node.names if alias.name == "json")
        if isinstance(node, ast.ImportFrom) and node.module == "json":
            load_names.update(alias.asname or alias.name for alias in node.names if alias.name == "loads")
    scopes = list(_scopes(tree))
    parsers = {}
    # Derive argument summaries for local parser wrappers, including multi-hop
    # wrappers, rather than guessing that every function named parse is JSON.
    for _ in range(len(scopes) + 1):
        before = repr(parsers)
        for name, scope in scopes:
            if not isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            args = scope.args.posonlyargs + scope.args.args
            flow = _Flow(parsers, json_names, load_names)
            flow.statements(scope.body, {arg.arg: {-(i + 1)} for i, arg in enumerate(args)})
            summary = {i: arg.arg for i, arg in enumerate(args) if -(i + 1) in flow.consumed}
            if summary:
                parsers[name] = summary
                parsers[scope.name] = summary
        if repr(parsers) == before:
            break
    findings, inventory = {}, {}
    for name, scope in scopes:
        flow = _Flow(parsers, json_names, load_names)
        flow.statements(scope.body, {})
        if flow.splits:
            inventory[name] = flow.splits
        bad = flow.splits & flow.consumed
        if bad:
            findings[name] = bad
    return findings, inventory


def violations(path: str, source: str) -> list[str]:
    findings, _ = analyze(source)
    tree = ast.parse(source)
    calls = {
        node.lineno: ast.unparse(node)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "splitlines"
    }
    result = []
    for function, lines in findings.items():
        exception = ALLOWLIST.get((path, function))
        for line in sorted(lines):
            if exception is None or calls[line] not in (
                (exception[1],) if isinstance(exception[1], str) else exception[1]
            ):
                result.append(f"{path}:{line} ({function})")
    return result


@pytest.mark.repo_wide
def test_scripts_structured_readers_do_not_use_str_splitlines():
    failures = []
    for path in sorted((ROOT / "scripts").rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        if "splitlines" in source:
            failures.extend(violations(path.relative_to(ROOT).as_posix(), source))
    assert not failures, "JSON parser consumes splitlines output:\n" + "\n".join(failures)


@pytest.mark.parametrize(
    "body",
    [
        "return json.loads(text.splitlines()[-1])",
        "lines = text.splitlines()\nfor line in lines:\n    json.loads(line.strip())",
        "return [json.loads(line) for line in text.splitlines()]",
        "lines = text.splitlines()\nselected = [line[5:] for line in lines]\nreturn json.loads('\\n'.join(selected))",
        "for line in text.splitlines():\n    _strict_json_loads(line)",
        "for line in text.splitlines():\n    parse(line)\ndef parse(value):\n    return json.loads(value)",
        "lines = text.splitlines()\nfor number, line in enumerate(lines):\n    json.loads(line)",
        "lines = text.splitlines()\nrows = []\nfor line in lines:\n    rows.append(line)\njson.loads(rows[0])",
        "for line in text.splitlines():\n    loads(line)",
    ],
)
def test_guard_detects_parser_data_flow(body):
    source = "import json\nfrom json import loads\ndef read(text):\n" + "\n".join(
        "    " + line for line in body.split("\n")
    )
    assert violations("example.py", source)


@pytest.mark.parametrize(
    "body",
    [
        "for line in text.splitlines():\n    print(line)\nreturn json.loads(other)",
        "lines = text.splitlines()\nlines = other\nreturn json.loads(lines)",
        "for line in text.splitlines():\n    print(line)\nreturn [json.loads(line) for line in other]",
        "return [json.loads(line) for line in split_jsonl_lines(text)]",
    ],
)
def test_guard_does_not_confuse_human_text_with_json_input(body):
    source = "import json\ndef read(text, other):\n" + "\n".join("    " + line for line in body.split("\n"))
    assert not violations("example.py", source)


def test_allowlist_reasons_and_exact_call_shapes_are_current():
    for (path, function), (reason, expression) in ALLOWLIST.items():
        assert reason
        tree = ast.parse((ROOT / path).read_text())
        scope = dict(_scopes(tree))[function]
        expressions = (expression,) if isinstance(expression, str) else expression
        assert set(expressions) <= {ast.unparse(node) for node in ast.walk(scope) if isinstance(node, ast.Call)}


def test_byte_exception_does_not_allow_decode_before_splitting():
    path = "scripts/projects/open_model_data/phase3_fixed_release.py"
    assert violations(
        path,
        "import json\ndef _read_jsonl(path):\n    return [json.loads(row) for row in path.read_bytes().decode('utf-8').splitlines()]",
    )


@pytest.mark.parametrize(
    "path, function",
    [key for key, (reason, _) in ALLOWLIST.items() if reason.startswith("hash-pinned frozen source;")],
)
def test_frozen_exception_does_not_admit_unreviewed_split(path, function):
    assert ALLOWLIST[path, function][0] == "hash-pinned frozen source; changing bytes breaks its release receipt"
    source = f"import json\ndef {function}(unreviewed_text):\n    return json.loads(unreviewed_text.splitlines()[-1])"
    assert violations(path, source)
