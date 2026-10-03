"""Repo-wide read-only enforcement for sources.db / vesum.db (#9609, plan PA2)."""

from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path

import pytest

from scripts.hygiene import lint_source_db_writable_connects as lint

REPO_ROOT = Path(__file__).resolve().parents[1]


def _sparse_excluded(rel_paths: list[str]) -> set[str]:
    """Tracked paths marked skip-worktree (absent by sparse checkout)."""
    if not rel_paths:
        return set()
    listed = subprocess.run(
        ["git", "ls-files", "-t", "--", *rel_paths],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    ).stdout.splitlines()
    return {line[2:] for line in listed if line.startswith("S ")}


@pytest.mark.repo_wide
def test_repo_has_no_unallowlisted_writable_source_db_connect():
    violations, unreadable = lint.find_violations()
    assert violations == [], "\n".join(violations)
    # Only files a sparse checkout left out may go unscanned; CI's full checkout scans all.
    assert set(unreadable) <= _sparse_excluded(unreadable), unreadable


def test_every_allowlist_entry_states_a_reason():
    for site in lint.ALLOWLIST:
        assert site.reason.strip(), site
        assert not site.path.startswith(lint.EXCLUDED_PREFIXES), site


@pytest.mark.parametrize(
    "module",
    [
        "scripts/projects/open_model_data/v5_mine_middle_ukrainian.py",
        "scripts/projects/open_model_data/v4_production_shards_assembly.py",
        "scripts/projects/open_model_data/phase3_decolonization_partition.py",
        "scripts/projects/open_model_data/v5_mine_kyivan_rus_epigraphy.py",
    ],
)
def test_plan_listed_sites_now_open_read_only(module):
    """The writable connects named in plan PA2 are fixed (v6_mine_ulif_phraseology.py was archived by E1)."""
    assert lint.classify_source((REPO_ROOT / module).read_text(encoding="utf-8"), module) == []


def test_archived_plan_listed_module_is_outside_product_code():
    assert not (REPO_ROOT / "scripts/projects/open_model_data/v6_mine_ulif_phraseology.py").exists()
    assert "archive/code/open_model_data/scripts/v6_mine_ulif_phraseology.py".startswith(lint.EXCLUDED_PREFIXES)


WRITABLE_CASES = {
    "literal_path": 'import sqlite3\nconn = sqlite3.connect("data/sources.db")\n',
    "module_constant": textwrap.dedent(
        """
        import sqlite3
        from pathlib import Path
        SOURCES_DB = Path(__file__).parent / "data" / "sources.db"
        def load():
            return sqlite3.connect(str(SOURCES_DB))
        """
    ),
    "parameter_from_caller": textwrap.dedent(
        """
        import sqlite3
        from scripts.rag.config import VESUM_DB_PATH
        def load(db):
            return sqlite3.connect(db)
        def main():
            return load(VESUM_DB_PATH)
        """
    ),
    "argparse_default": textwrap.dedent(
        """
        import argparse, sqlite3
        def main():
            parser = argparse.ArgumentParser()
            parser.add_argument("--db", default=DEFAULT_DB, help="path to sources.db")
            args = parser.parse_args()
            return sqlite3.connect(args.db)
        """
    ),
    "self_attribute": textwrap.dedent(
        """
        import sqlite3
        class Reader:
            def __init__(self, vesum_db):
                self.path = vesum_db
            def open(self):
                return sqlite3.connect(self.path)
        """
    ),
    "aliased_import": 'from sqlite3 import connect as c\nconn = c("vesum.db")\n',
    "mode_rw": 'import sqlite3\nconn = sqlite3.connect(SOURCES_DB.as_uri() + "?mode=rw", uri=True)\n',
    "mode_ro_without_uri_flag": 'import sqlite3\nconn = sqlite3.connect(f"file:{SOURCES_DB}?mode=ro")\n',
    "explicit_argument_overrides_default": textwrap.dedent(
        """
        import sqlite3
        def read(path="cache.db"):
            return sqlite3.connect(path)
        def main():
            return read("data/sources.db")
        """
    ),
    "keyword_argument_overrides_default": textwrap.dedent(
        """
        import sqlite3
        def read(*, path="cache.db"):
            return sqlite3.connect(path)
        def main():
            return read(path="data/vesum.db")
        """
    ),
    "override_through_a_second_call_level": textwrap.dedent(
        """
        import sqlite3
        def read(path="cache.db"):
            return sqlite3.connect(path)
        def middle(target="other.db"):
            return read(target)
        def main():
            return middle(target="data/sources.db")
        """
    ),
    "writable_argument_overrides_read_only_default": textwrap.dedent(
        """
        import sqlite3
        def read(uri="file:data/sources.db?mode=ro"):
            return sqlite3.connect(uri, uri=True)
        def main():
            return read("file:data/sources.db?mode=rw")
        """
    ),
    "unbound_method_call_through_the_class": textwrap.dedent(
        """
        import sqlite3
        class Reader:
            def read(self, path="cache.db"):
                return sqlite3.connect(path)
        def main():
            return Reader.read(Reader(), "sources.db")
        """
    ),
    "bound_method_call": textwrap.dedent(
        """
        import sqlite3
        class Reader:
            def read(self, path="cache.db"):
                return sqlite3.connect(path)
        def main():
            return Reader().read("sources.db")
        """
    ),
    "staticmethod_call": textwrap.dedent(
        """
        import sqlite3
        class Reader:
            @staticmethod
            def read(path="cache.db"):
                return sqlite3.connect(path)
        def main():
            return Reader.read("sources.db")
        """
    ),
    "classmethod_call": textwrap.dedent(
        """
        import sqlite3
        class Reader:
            @classmethod
            def read(cls, path="cache.db"):
                return sqlite3.connect(path)
        def main():
            return Reader.read("sources.db")
        """
    ),
    "classmethod_call_through_an_instance": textwrap.dedent(
        """
        import sqlite3
        class Reader:
            @classmethod
            def read(cls, path="cache.db"):
                return sqlite3.connect(path)
        def main():
            return Reader().read("sources.db")
        """
    ),
    "unbound_init_call": textwrap.dedent(
        """
        import sqlite3
        class Reader:
            def __init__(self, path="cache.db"):
                self.conn = sqlite3.connect(path)
        class Sub(Reader):
            def __init__(self):
                Reader.__init__(self, "sources.db")
        """
    ),
    "nested_class_unbound_call": textwrap.dedent(
        """
        import sqlite3
        class Outer:
            class Reader:
                def read(self, path="cache.db"):
                    return sqlite3.connect(path)
        def main():
            return Outer.Reader.read(Outer.Reader(), "sources.db")
        """
    ),
    "nested_class_bound_call": textwrap.dedent(
        """
        import sqlite3
        class Outer:
            class Reader:
                def read(self, path="cache.db"):
                    return sqlite3.connect(path)
        def main():
            return Outer.Reader().read("sources.db")
        """
    ),
    "two_level_nested_class_unbound_call": textwrap.dedent(
        """
        import sqlite3
        class A:
            class B:
                class C:
                    def read(self, path="cache.db"):
                        return sqlite3.connect(path)
        def main():
            return A.B.C.read(A.B.C(), "sources.db")
        """
    ),
    "unresolved_receiver_chain_unbound": textwrap.dedent(
        """
        import sqlite3
        class Reader:
            def read(self, path="cache.db"):
                return sqlite3.connect(path)
        def main(holder):
            return holder.klass.read(holder.obj, "sources.db")
        """
    ),
    "unresolved_receiver_chain_bound": textwrap.dedent(
        """
        import sqlite3
        class Reader:
            def read(self, path="cache.db"):
                return sqlite3.connect(path)
        def main(holder):
            return holder.obj.read("sources.db")
        """
    ),
    "aliased_class_unbound": textwrap.dedent(
        """
        import sqlite3
        class Reader:
            def read(self, path="cache.db"):
                return sqlite3.connect(path)
        def main():
            alias = Reader
            return alias.read(alias(), "sources.db")
        """
    ),
    "shadowed_class_name_unbound": textwrap.dedent(
        """
        import sqlite3
        class Reader:
            def read(self, path="cache.db"):
                return sqlite3.connect(path)
        def main(Reader):
            return Reader.read(Reader(), "sources.db")
        """
    ),
    "self_call_binds_self": textwrap.dedent(
        """
        import sqlite3
        class Reader:
            def read(self, path="cache.db"):
                return sqlite3.connect(path)
            def run(self):
                return self.read("sources.db")
        """
    ),
    "public_helper_in_source_module": textwrap.dedent(
        """
        import sqlite3
        DEFAULT = "sources.db"
        def open_db(path):
            return sqlite3.connect(path)
        """
    ),
}


@pytest.mark.parametrize("case", sorted(WRITABLE_CASES))
def test_injected_writable_connect_is_reported(case, tmp_path):
    module = tmp_path / "scripts" / "injected.py"
    module.parent.mkdir(parents=True)
    module.write_text(WRITABLE_CASES[case], encoding="utf-8")
    violations, unreadable = lint.find_violations(tmp_path, allowlist=())
    assert unreadable == []
    assert len(violations) == 1 and "scripts/injected.py" in violations[0], violations


def test_conditional_mode_is_reported_as_conditional():
    source = textwrap.dedent(
        """
        import sqlite3
        def open_db(sources_db, read_only):
            uri = f"file:{sources_db}?mode=ro" if read_only else str(sources_db)
            return sqlite3.connect(uri, uri=True)
        """
    )
    [finding] = lint.classify_source(source, "scripts/x.py")
    assert finding.kind == "conditional"


READ_ONLY_OR_UNRELATED = {
    "fstring_uri": 'import sqlite3\nconn = sqlite3.connect(f"{SOURCES_DB.resolve().as_uri()}?mode=ro", uri=True)\n',
    "concatenated_uri": 'import sqlite3\nconn = sqlite3.connect("file:" + str(VESUM_DB) + "?immutable=1", uri=True)\n',
    "uri_through_name": textwrap.dedent(
        """
        import sqlite3
        def open_db(sources_db):
            uri = f"file:{sources_db}?mode=ro"
            return sqlite3.connect(uri, uri=True)
        """
    ),
    "unbound_call_reads_the_path_argument_not_self": textwrap.dedent(
        """
        import sqlite3
        class Reader:
            def read(self, path="cache.db"):
                return sqlite3.connect(path)
        def main(sources_db_holder):
            return Reader.read(sources_db_holder, "other.db")
        """
    ),
    "default_and_every_caller_are_other_databases": textwrap.dedent(
        """
        import sqlite3
        SOURCES_DB = "sources.db"
        def read(path="cache.db"):
            return sqlite3.connect(path)
        def main():
            return read("index.sqlite"), read(path="other.db")
        """
    ),
    "read_only_default_and_read_only_callers": textwrap.dedent(
        """
        import sqlite3
        def read(uri="file:data/sources.db?mode=ro"):
            return sqlite3.connect(uri, uri=True)
        def main():
            return read("file:data/vesum.db?mode=ro"), read(uri="file:data/sources.db?immutable=1")
        """
    ),
    "nested_class_unbound_call_with_other_database": textwrap.dedent(
        """
        import sqlite3
        class Outer:
            class Reader:
                def read(self, path="cache.db"):
                    return sqlite3.connect(path)
        def main():
            return Outer.Reader.read(Outer.Reader(), "other.db")
        """
    ),
    "unresolved_receiver_every_binding_passes_other_database": textwrap.dedent(
        """
        import sqlite3
        class Reader:
            def read(self, path="cache.db"):
                return sqlite3.connect(path)
        def main(holder):
            return holder.klass.read(holder.obj, "other.db")
        """
    ),
    "other_database": 'import sqlite3\nconn = sqlite3.connect("data/atlas.db")\n',
    "resources_db_is_not_sources_db": "import sqlite3\nconn = sqlite3.connect(resources_db)\n",
    "caller_passes_other_db": textwrap.dedent(
        """
        import sqlite3
        SOURCES_DB = "sources.db"
        def write_index(out):
            return sqlite3.connect(out)
        def main():
            return write_index("index.sqlite")
        """
    ),
}


@pytest.mark.parametrize("case", sorted(READ_ONLY_OR_UNRELATED))
def test_read_only_or_unrelated_opens_pass(case):
    assert lint.classify_source(READ_ONLY_OR_UNRELATED[case], "scripts/x.py") == []


@pytest.mark.parametrize("prefix", ["scripts/ingest", "tests", "archive/code"])
def test_ingest_tests_and_archive_are_excluded(prefix, tmp_path):
    module = tmp_path / prefix / "writer.py"
    module.parent.mkdir(parents=True)
    module.write_text(WRITABLE_CASES["literal_path"], encoding="utf-8")
    assert lint.find_violations(tmp_path, allowlist=()) == ([], [])


def test_allowlist_matches_by_snippet_and_count_and_reports_stale_entries(tmp_path):
    module = tmp_path / "scripts" / "writer.py"
    module.parent.mkdir(parents=True)
    module.write_text(WRITABLE_CASES["literal_path"], encoding="utf-8")
    site = lint.AllowedSite("scripts/writer.py", 'conn = sqlite3.connect("data/sources.db")', 1, "test writer")
    assert lint.find_violations(tmp_path, allowlist=(site,)) == ([], [])
    stale = lint.AllowedSite("scripts/gone.py", "conn = sqlite3.connect(x)", 1, "removed")
    violations, _ = lint.find_violations(tmp_path, allowlist=(site, stale))
    assert len(violations) == 1 and "stale allowlist entry" in violations[0]


def test_cli_fails_on_violation(monkeypatch, capsys):
    monkeypatch.setattr(lint, "find_violations", lambda: (["scripts/x.py:1: writable open: x"], []))
    assert lint.main([]) == 1
    assert "scripts/x.py:1" in capsys.readouterr().err
