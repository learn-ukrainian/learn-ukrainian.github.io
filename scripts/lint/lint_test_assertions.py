#!/usr/bin/env python3
"""Lint test files for hard-coded stale-pinned epic/stream assertions (#6968).

Tests asserting on live, derivable workflow state must derive stream IDs from
scripts/config/issue_streams.yaml (or corresponding runtime registries) rather
than hard-coding literal 'epic:<int>' values or bare stream IDs in assertions.

Hard-coding derivable state stales tests across epic succession and turns
unrelated provider or schema transitions into red CI gates.

Designated exceptions:
1. Synthetic/test epic IDs: epic:0, epic:123, epic:1001, epic:1002,
   epic:2001, epic:3001, epic:4220, epic:4700, epic:9999, epic:999999, epic:888001.
2. Negative assertions verifying obsolete/old epics are NOT emitted:
   e.g. `assert "epic:4707" not in text` or `assert out != "epic:4707"`.
3. Explicit line-scoped directives:
   `# noqa: epic-id`, `# noqa: stale-pinned-epic`, `# allow-hardcoded-epic: <reason>`,
   or `# designated-fixture: <reason>`.
"""

from __future__ import annotations

import argparse
import ast
import io
import re
import sys
import tokenize
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from scripts.ci.test_source_cache import parse_test_source, read_test_source

REPO_ROOT = Path(__file__).resolve().parents[2]

# Regex matching epic ID stream literals
_EPIC_ID_RE = re.compile(r"\bepic:\d+\b", re.IGNORECASE)

# Synthetic IDs explicitly reserved for tests/fixtures
_SYNTHETIC_EPIC_IDS: frozenset[str] = frozenset(
    {
        "epic:0",
        "epic:123",
        "epic:1001",
        "epic:1002",
        "epic:2001",
        "epic:3001",
        "epic:4220",
        "epic:4700",
        "epic:9999",
        "epic:999999",
        "epic:888001",
    }
)

# Inline directive comments that explicitly allow hard-coded literals with line-scoped intent.
# Directives require a non-empty reason after the colon (e.g. 'allow-hardcoded-epic: <reason>'),
# or a standard noqa tag (e.g. 'noqa: epic-id', 'noqa: stale-pinned-epic').
_ALLOW_DIRECTIVE_RE = re.compile(
    r"#\s*(?:"
    r"noqa:\s*(?:epic-id|stale-pinned-epic)\b"
    r"|"
    r"(?:allow-hardcoded-epic|designated-fixture)\s*:\s*\S+"
    r")",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class AssertionViolation:
    """One prohibited hard-coded epic/stream assertion."""

    path: str
    line_number: int
    snippet: str
    epic_id: str
    reason: str


class _Environment:
    """Scoped variable binding environment for AST semantic evaluation."""

    def __init__(self, parent: _Environment | None = None) -> None:
        self.parent = parent
        self.bindings: dict[str, object] = {}

    def get(self, name: str) -> object | None:
        if name in self.bindings:
            return self.bindings[name]
        if self.parent is not None:
            return self.parent.get(name)
        return None

    def set(self, name: str, value: object) -> None:
        self.bindings[name] = value


def _eval_expr(node: ast.AST, env: _Environment) -> object | None:
    """Statically evaluate literal, string-concatenation, alias, and f-string expressions."""
    if isinstance(node, ast.Constant):
        return node.value

    if isinstance(node, ast.Name):
        return env.get(node.id)

    if isinstance(node, ast.NamedExpr):
        val = _eval_expr(node.value, env)
        if isinstance(node.target, ast.Name):
            env.set(node.target.id, val)
        return val

    if isinstance(node, ast.BinOp):
        left = _eval_expr(node.left, env)
        right = _eval_expr(node.right, env)
        if isinstance(node.op, ast.Add):
            if isinstance(left, str) and isinstance(right, str):
                return left + right
            if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                return left + right
        elif isinstance(node.op, ast.Mod):
            if isinstance(left, str):
                try:
                    return left % right
                except Exception:
                    return None

    if isinstance(node, ast.JoinedStr):
        parts: list[str] = []
        for value_node in node.values:
            if isinstance(value_node, ast.Constant):
                parts.append(str(value_node.value))
            elif isinstance(value_node, ast.FormattedValue):
                val = _eval_expr(value_node.value, env)
                if val is not None:
                    parts.append(str(val))
                else:
                    return None
            else:
                return None
        return "".join(parts)

    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "str" and len(node.args) == 1:
        val = _eval_expr(node.args[0], env)
        if val is not None:
            return str(val)

    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return [_eval_expr(el, env) for el in node.elts]

    if isinstance(node, ast.Dict):
        res: dict[object, object] = {}
        for k, v in zip(node.keys, node.values, strict=False):
            if k is not None:
                kval = _eval_expr(k, env)
                vval = _eval_expr(v, env)
                if isinstance(kval, (str, int, float, bool, bytes, type(None))):
                    res[kval] = vval
                else:
                    res[str(kval)] = vval
        return res

    return None


def _extract_epic_ids(val: object) -> set[str]:
    """Extract all non-synthetic epic IDs found in a statically evaluated value."""
    results: set[str] = set()
    if isinstance(val, str):
        for match in _EPIC_ID_RE.finditer(val):
            epic_id = match.group(0).lower()
            if epic_id not in _SYNTHETIC_EPIC_IDS:
                results.add(match.group(0))
    elif isinstance(val, (list, tuple, set, frozenset)):
        for item in val:
            results.update(_extract_epic_ids(item))
    elif isinstance(val, dict):
        for k, v in val.items():
            results.update(_extract_epic_ids(k))
            results.update(_extract_epic_ids(v))
    return results


def _may_evaluate_epic_literal(tree: ast.AST) -> bool:
    """Keep scanning when an assertion can statically evaluate an epic ID."""

    def expression_has_epic(node: ast.AST, env: _Environment) -> bool:
        return any(
            _extract_epic_ids(_eval_expr(sub, env))
            for sub in ast.walk(node)
        )

    def block_has_epic(stmts: Sequence[ast.stmt], env: _Environment) -> bool:
        for stmt in stmts:
            if isinstance(stmt, ast.Assign):
                _bind_targets(stmt.targets, _eval_expr(stmt.value, env), env)
            elif isinstance(stmt, ast.AnnAssign) and stmt.value is not None:
                _bind_targets([stmt.target], _eval_expr(stmt.value, env), env)
            elif isinstance(stmt, ast.AugAssign) and isinstance(stmt.target, ast.Name):
                old_val = env.get(stmt.target.id)
                inc_val = _eval_expr(stmt.value, env)
                if isinstance(stmt.op, ast.Add) and isinstance(old_val, str) and isinstance(inc_val, str):
                    env.set(stmt.target.id, old_val + inc_val)
            elif isinstance(stmt, ast.Assert):
                if expression_has_epic(stmt.test, env):
                    return True
            elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if block_has_epic(stmt.body, _Environment(parent=env)):
                    return True
            elif isinstance(stmt, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.With, ast.AsyncWith)):
                if block_has_epic(stmt.body, env):
                    return True
                if getattr(stmt, "orelse", None) and block_has_epic(stmt.orelse, env):
                    return True
            elif isinstance(stmt, ast.Try):
                if block_has_epic(stmt.body, env):
                    return True
                if any(block_has_epic(handler.body, env) for handler in stmt.handlers):
                    return True
                if stmt.orelse and block_has_epic(stmt.orelse, env):
                    return True
                if stmt.finalbody and block_has_epic(stmt.finalbody, env):
                    return True
        return False

    return block_has_epic(tree.body, _Environment()) if isinstance(tree, ast.Module) else False


def _source_may_contain_split_epic_literal(source_code: str) -> bool:
    """Recognize split/escaped literal pieces before paying for an AST scan."""
    values: list[str] = []
    try:
        tokens = tokenize.generate_tokens(io.StringIO(source_code).readline)
        for token in tokens:
            if token.type == tokenize.STRING:
                try:
                    value = ast.literal_eval(token.string)
                except (SyntaxError, ValueError):
                    value = token.string
                if isinstance(value, str):
                    values.append(value)
            elif token.type == tokenize.NUMBER:
                values.append(token.string)
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return True

    literal_text = "".join(values).lower()
    return bool(
        _EPIC_ID_RE.search(literal_text)
        or (
            all(fragment in literal_text for fragment in ("e", "p", "i", "c", ":"))
            and any(char.isdigit() for char in literal_text)
        )
    )


def _find_positive_epic_violations(test_node: ast.AST, env: _Environment, polarity: bool = True) -> set[str]:
    """Inspect an assertion AST node for epic IDs in positive assertion contexts."""
    if isinstance(test_node, ast.UnaryOp) and isinstance(test_node.op, ast.Not):
        return _find_positive_epic_violations(test_node.operand, env, not polarity)

    if isinstance(test_node, ast.BoolOp):
        found: set[str] = set()
        for val in test_node.values:
            found.update(_find_positive_epic_violations(val, env, polarity))
        return found

    if isinstance(test_node, ast.Compare):
        found = set()
        current_left = test_node.left
        for op, comp in zip(test_node.ops, test_node.comparators, strict=False):
            is_negative_op = isinstance(op, (ast.NotIn, ast.IsNot, ast.NotEq))
            cmp_polarity = (not polarity) if is_negative_op else polarity
            if cmp_polarity:
                for target_node in (current_left, comp):
                    for sub in ast.walk(target_node):
                        val = _eval_expr(sub, env)
                        found.update(_extract_epic_ids(val))
            current_left = comp
        return found

    if polarity:
        found = set()
        for sub in ast.walk(test_node):
            val = _eval_expr(sub, env)
            found.update(_extract_epic_ids(val))
        return found
    return set()


def _extract_suppressed_comment_lines(source_code: str) -> set[int]:
    """Parse comments via Python tokenize module and extract line numbers with valid allow directives."""
    suppressed_lines: set[int] = set()
    try:
        tokens = tokenize.generate_tokens(io.StringIO(source_code).readline)
        for tok in tokens:
            if tok.type == tokenize.COMMENT and _ALLOW_DIRECTIVE_RE.search(tok.string):
                suppressed_lines.add(tok.start[0])
    except (tokenize.TokenError, IndentationError, SyntaxError):
        pass
    return suppressed_lines


def _has_allow_directive(
    suppressed_lines: set[int],
    lines: list[str],
    start_line: int,
    end_line: int,
) -> bool:
    """Check if any line from start_line to end_line or preceding standalone comment line contains an allow directive."""
    # Check lines of the assert statement itself (start_line to end_line)
    for lineno in range(start_line, end_line + 1):
        if lineno in suppressed_lines:
            return True
    # Check immediate preceding line ONLY IF it is a standalone comment line
    if start_line >= 2 and (start_line - 1) in suppressed_lines:
        prev_line = lines[start_line - 2].strip()
        if prev_line.startswith("#"):
            return True
    return False


def _bind_targets(targets: Sequence[ast.AST], value: object | None, env: _Environment) -> None:
    for target in targets:
        if isinstance(target, ast.Name):
            env.set(target.id, value)
        elif (
            isinstance(target, (ast.Tuple, ast.List))
            and isinstance(value, (list, tuple))
            and len(target.elts) == len(value)
        ):
            for sub_t, sub_v in zip(target.elts, value, strict=True):
                if isinstance(sub_t, ast.Name):
                    env.set(sub_t.id, sub_v)


def _scan_block(
    stmts: Sequence[ast.stmt],
    env: _Environment,
    suppressed_lines: set[int],
    lines: list[str],
    content: str,
    rel_path: str,
    violations: list[AssertionViolation],
) -> None:
    for stmt in stmts:
        if isinstance(stmt, ast.Assign):
            val = _eval_expr(stmt.value, env)
            _bind_targets(stmt.targets, val, env)
        elif isinstance(stmt, ast.AnnAssign):
            if stmt.value is not None:
                val = _eval_expr(stmt.value, env)
                _bind_targets([stmt.target], val, env)
        elif isinstance(stmt, ast.AugAssign):
            if isinstance(stmt.target, ast.Name):
                old_val = env.get(stmt.target.id)
                inc_val = _eval_expr(stmt.value, env)
                if isinstance(stmt.op, ast.Add) and isinstance(old_val, str) and isinstance(inc_val, str):
                    env.set(stmt.target.id, old_val + inc_val)
        elif isinstance(stmt, ast.Assert):
            lineno = stmt.lineno
            end_lineno = getattr(stmt, "end_lineno", lineno) or lineno
            if not _has_allow_directive(suppressed_lines, lines, lineno, end_lineno):
                epics = _find_positive_epic_violations(stmt.test, env, polarity=True)
                if epics:
                    snippet = (ast.get_source_segment(content, stmt) or "").strip()
                    for epic in sorted(epics):
                        violations.append(
                            AssertionViolation(
                                path=rel_path,
                                line_number=lineno,
                                snippet=snippet,
                                epic_id=epic,
                                reason=(
                                    f"hard-coded stream literal '{epic}' in assertion; "
                                    "derive from issue_streams.yaml or use a designated fixture pattern "
                                    "(e.g. # noqa: epic-id, # allow-hardcoded-epic: <reason>, or synthetic epic ID)"
                                ),
                            )
                        )
        elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_env = _Environment(parent=env)
            _scan_block(stmt.body, func_env, suppressed_lines, lines, content, rel_path, violations)
        elif isinstance(stmt, ast.ClassDef):
            class_env = _Environment(parent=env)
            _scan_block(stmt.body, class_env, suppressed_lines, lines, content, rel_path, violations)
        elif isinstance(stmt, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.With, ast.AsyncWith)):
            _scan_block(stmt.body, env, suppressed_lines, lines, content, rel_path, violations)
            if hasattr(stmt, "orelse") and stmt.orelse:
                _scan_block(stmt.orelse, env, suppressed_lines, lines, content, rel_path, violations)
        elif isinstance(stmt, ast.Try):
            _scan_block(stmt.body, env, suppressed_lines, lines, content, rel_path, violations)
            for handler in stmt.handlers:
                _scan_block(handler.body, env, suppressed_lines, lines, content, rel_path, violations)
            if stmt.orelse:
                _scan_block(stmt.orelse, env, suppressed_lines, lines, content, rel_path, violations)
            if stmt.finalbody:
                _scan_block(stmt.finalbody, env, suppressed_lines, lines, content, rel_path, violations)


def scan_file(file_path: Path, repo_root: Path | None = None) -> list[AssertionViolation]:
    """Scan a single Python test file for forbidden hard-coded epic assertions."""
    root = (repo_root or REPO_ROOT).resolve()
    rel_path = file_path.resolve().relative_to(root).as_posix()

    try:
        content = read_test_source(file_path)
        tree = parse_test_source(file_path)
    except (OSError, UnicodeDecodeError, SyntaxError):
        return []
    if not _may_evaluate_epic_literal(tree):
        return []

    lines = content.splitlines()
    suppressed_lines = _extract_suppressed_comment_lines(content)
    violations: list[AssertionViolation] = []
    module_env = _Environment()
    _scan_block(tree.body, module_env, suppressed_lines, lines, content, rel_path, violations)

    return violations


def find_stale_pinned_assertions(
    repo_root: Path | None = None,
    paths: Sequence[Path] | None = None,
) -> list[AssertionViolation]:
    """Scan test files under repo_root or explicit paths for stale pinned assertions."""
    root = (repo_root or REPO_ROOT).resolve()
    if paths:
        target_files = [p.resolve() for p in paths if p.is_file() and p.suffix == ".py"]
    else:
        tests_dir = root / "tests"
        if not tests_dir.is_dir():
            return []
        target_files = sorted(tests_dir.rglob("*.py"))

    findings: list[AssertionViolation] = []
    for file_path in target_files:
        try:
            source = read_test_source(file_path)
            if "epic" not in source.lower() and not _source_may_contain_split_epic_literal(source):
                tree = parse_test_source(file_path)
                if not _may_evaluate_epic_literal(tree):
                    continue
        except (OSError, UnicodeDecodeError, SyntaxError):
            continue
        findings.extend(scan_file(file_path, repo_root=root))

    return findings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="Optional specific test files or directories to check",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root directory",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    paths: list[Path] | None = None
    if args.paths:
        paths = []
        for p in args.paths:
            if p.is_dir():
                paths.extend(sorted(p.rglob("*.py")))
            elif p.is_file():
                paths.append(p)

    findings = find_stale_pinned_assertions(repo_root=args.root, paths=paths)

    if not findings:
        print("OK: no forbidden hard-coded epic/stream assertions found in tests")
        return 0

    print("Forbidden hard-coded epic assertions found in tests:", file=sys.stderr)
    for v in findings:
        print(f"  {v.path}:{v.line_number}: [{v.epic_id}] {v.snippet}", file=sys.stderr)
        print(f"    ↳ {v.reason}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
