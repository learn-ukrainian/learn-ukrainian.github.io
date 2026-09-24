import os
from unittest.mock import patch

import pytest

from scripts.audit.check_mdx_source_parity import (
    GENERATOR_DEPENDENCIES,
    GENERATOR_PACKAGE,
    MDX_DIR,
    SOURCE_DIR,
    check_parity,
    main,
)

pytestmark = pytest.mark.reads_content


@pytest.fixture
def mock_env():
    with patch.dict(os.environ, clear=True):
        yield

@pytest.fixture
def mock_subprocess():
    with patch("scripts.audit.check_mdx_source_parity.subprocess.check_output") as m:
        yield m

@pytest.fixture
def mock_legacy_levels():
    with patch("scripts.audit.check_mdx_source_parity.get_legacy_levels", return_value={"hist", "bio", "lit"}):
        yield

def test_check_parity_mdx_only(mock_legacy_levels, mock_subprocess):
    # MDX-only diff (should fail)
    mdx_files = [MDX_DIR / "a1" / "01-hello.mdx"]
    changed_files = {MDX_DIR / "a1" / "01-hello.mdx"}
    mock_subprocess.return_value = "1 file changed\n" # Not whitespace-only

    violations = check_parity(mdx_files, changed_files)
    assert len(violations) == 1
    assert "MDX file changed but no source files changed" in violations[0][1]

def test_check_parity_level_landing_page(mock_legacy_levels, mock_subprocess):
    # Level landing pages are generated indexes, not lesson MDX artifacts.
    mdx_files = [MDX_DIR / "b1" / "index.mdx"]
    changed_files = {MDX_DIR / "b1" / "index.mdx"}
    mock_subprocess.return_value = "1 file changed\n" # Not whitespace-only

    violations = check_parity(mdx_files, changed_files)
    assert len(violations) == 0

MODULE_TEXT = '---\ntitle: "x"\narc_kind: module\narc_level: a1\narc_slug: alpha\n---\n'
LANDING_TEXT = '---\ntitle: "A1"\narc_kind: landing\narc_level: a1\n---\n'


@pytest.fixture
def arc_docs(tmp_path, monkeypatch):
    """A temp docs tree whose generator-owned files are ``a1/index.mdx`` and ``a1/alpha/index.mdx``."""
    module = tmp_path / "a1" / "alpha" / "index.mdx"
    landing = tmp_path / "a1" / "index.mdx"
    monkeypatch.setattr("scripts.audit.check_mdx_source_parity.MDX_DIR", tmp_path)
    monkeypatch.setattr(
        "scripts.audit.check_mdx_source_parity._arc_generated_files",
        lambda level: {module: MODULE_TEXT, landing: LANDING_TEXT},
    )
    for path, text in ((module, MODULE_TEXT), (landing, LANDING_TEXT)):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return tmp_path


def test_check_parity_skips_byte_exact_arc_generated_pages(mock_legacy_levels, mock_subprocess, arc_docs):
    mock_subprocess.return_value = "1 file changed\n"
    pages = [arc_docs / "a1" / "alpha" / "index.mdx", arc_docs / "a1" / "index.mdx"]
    assert check_parity(pages, set(pages)) == []


def test_check_parity_rejects_hand_edited_arc_generated_pages(mock_legacy_levels, mock_subprocess, arc_docs):
    mock_subprocess.return_value = "1 file changed\n"
    for page in (arc_docs / "a1" / "alpha" / "index.mdx", arc_docs / "a1" / "index.mdx"):
        page.write_text(page.read_text(encoding="utf-8") + "hand-written body\n", encoding="utf-8")
        violations = check_parity([page], {page})
        assert len(violations) == 1 and "arc_kind" in violations[0][1]


def test_check_parity_rejects_generated_pages_with_arc_kind_removed(mock_legacy_levels, mock_subprocess, arc_docs):
    mock_subprocess.return_value = "1 file changed\n"
    for page in (arc_docs / "a1" / "alpha" / "index.mdx", arc_docs / "a1" / "index.mdx"):
        page.write_text(page.read_text(encoding="utf-8").replace("arc_kind:", "kind:"), encoding="utf-8")
        violations = check_parity([page], {page})
        assert len(violations) == 1 and "arc page" in violations[0][1]


def test_check_parity_staged_bytes_decide_not_the_working_tree(mock_legacy_levels, mock_subprocess, arc_docs, monkeypatch):
    monkeypatch.setattr("scripts.audit.check_mdx_source_parity.PROJECT_ROOT", arc_docs)
    page = arc_docs / "a1" / "alpha" / "index.mdx"  # working-tree copy is the corrected one
    staged = {"a1/alpha/index.mdx": b"---\nhand-edited\n---\n"}

    def fake_git(cmd, **kwargs):
        if cmd[:2] == ["git", "show"]:
            return staged[cmd[2].removeprefix(":")]
        return "1 file changed\n"

    mock_subprocess.side_effect = fake_git
    violations = check_parity([page], {page}, cached=True)
    assert len(violations) == 1 and "arc page" in violations[0][1]
    staged["a1/alpha/index.mdx"] = MODULE_TEXT.encode("utf-8")
    assert check_parity([page], {page}, cached=True) == []


def test_check_parity_rejects_arc_kind_on_a_lesson_file(mock_legacy_levels, mock_subprocess, arc_docs):
    lesson = arc_docs / "a1" / "alpha" / "1.mdx"
    lesson.write_text(MODULE_TEXT, encoding="utf-8")
    mock_subprocess.return_value = "1 file changed\n"
    violations = check_parity([lesson], {lesson})
    assert len(violations) == 1 and "arc_kind" in violations[0][1]


def test_check_parity_rejects_arc_kind_outside_arc_levels(mock_legacy_levels, mock_subprocess, arc_docs):
    other = arc_docs / "b1" / "index.mdx"
    other.parent.mkdir()
    other.write_text(LANDING_TEXT, encoding="utf-8")
    mock_subprocess.return_value = "1 file changed\n"
    assert len(check_parity([other], {other})) == 1


def test_real_generated_a1_pages_pass_parity(mock_legacy_levels, mock_subprocess):
    pages = [MDX_DIR / "a1" / "index.mdx", *sorted(MDX_DIR.glob("a1/*/index.mdx"))]
    assert pages and all(page.is_file() for page in pages)
    mock_subprocess.return_value = "1 file changed\n"
    assert check_parity(pages, set(pages)) == []


def test_check_parity_mdx_and_source(mock_legacy_levels, mock_subprocess):
    # MDX + source diff (pass)
    mdx_files = [MDX_DIR / "a1" / "01-hello.mdx"]
    changed_files = {
        MDX_DIR / "a1" / "01-hello.mdx",
        SOURCE_DIR / "a1" / "01-hello" / "01-hello.md"
    }
    mock_subprocess.return_value = "1 file changed\n"

    violations = check_parity(mdx_files, changed_files)
    assert len(violations) == 0

def test_check_parity_mdx_and_meta_source(mock_legacy_levels, mock_subprocess):
    # MDX + module meta diff (pass). Meta frontmatter controls generated MDX.
    mdx_files = [MDX_DIR / "a2" / "aspect-in-past.mdx"]
    changed_files = {
        MDX_DIR / "a2" / "aspect-in-past.mdx",
        SOURCE_DIR / "a2" / "meta" / "aspect-in-past.yaml",
    }
    mock_subprocess.return_value = "1 file changed\n"

    violations = check_parity(mdx_files, changed_files)
    assert len(violations) == 0

def test_check_parity_mdx_and_plan_source(mock_legacy_levels, mock_subprocess):
    # Plan titles/subtitles/objectives can flow into generated MDX.
    mdx_files = [MDX_DIR / "a2" / "aspect-in-past.mdx"]
    changed_files = {
        MDX_DIR / "a2" / "aspect-in-past.mdx",
        SOURCE_DIR / "plans" / "a2" / "aspect-in-past.yaml",
    }
    mock_subprocess.return_value = "1 file changed\n"
    violations = check_parity(mdx_files, changed_files)
    assert len(violations) == 0


def test_check_parity_mdx_and_discovery_source(mock_legacy_levels, mock_subprocess):
    # Discovery resources can flow into generated MDX resource sections.
    mdx_files = [MDX_DIR / "a2" / "aspect-in-past.mdx"]
    changed_files = {
        MDX_DIR / "a2" / "aspect-in-past.mdx",
        SOURCE_DIR / "a2" / "discovery" / "aspect-in-past.yaml",
    }
    mock_subprocess.return_value = "1 file changed\n"
    violations = check_parity(mdx_files, changed_files)
    assert len(violations) == 0


def test_check_parity_adjacent_module_nav_only_change(mock_legacy_levels, mock_subprocess):
    # Adding a later source module can legitimately regenerate prev/next
    # frontmatter for the previous generated MDX page.
    mdx_files = [MDX_DIR / "b1" / "aspect-in-negation.mdx"]
    changed_files = {
        MDX_DIR / "b1" / "aspect-in-negation.mdx",
        SOURCE_DIR / "b1" / "work-and-career" / "module.md",
    }

    def side_effect(cmd, **kwargs):
        if "--shortstat" in cmd:
            return "1 file changed\n"
        return """diff --git a/site/src/content/docs/b1/aspect-in-negation.mdx b/site/src/content/docs/b1/aspect-in-negation.mdx
@@ -8 +8 @@
-next: false
+next: work-and-career
"""

    mock_subprocess.side_effect = side_effect

    violations = check_parity(mdx_files, changed_files, base="origin/main")
    assert len(violations) == 0

def test_check_parity_same_level_source_does_not_allow_body_mdx_only(mock_legacy_levels, mock_subprocess):
    mdx_files = [MDX_DIR / "b1" / "aspect-in-negation.mdx"]
    changed_files = {
        MDX_DIR / "b1" / "aspect-in-negation.mdx",
        SOURCE_DIR / "b1" / "work-and-career" / "module.md",
    }

    def side_effect(cmd, **kwargs):
        if "--shortstat" in cmd:
            return "1 file changed\n"
        return """diff --git a/site/src/content/docs/b1/aspect-in-negation.mdx b/site/src/content/docs/b1/aspect-in-negation.mdx
@@ -20 +20 @@
-Old learner text.
+New learner text.
"""

    mock_subprocess.side_effect = side_effect

    violations = check_parity(mdx_files, changed_files, base="origin/main")
    assert len(violations) == 1
    assert "MDX file changed but no source files changed" in violations[0][1]

def test_check_parity_generator_change_allows_existing_source_dir(mock_legacy_levels, mock_subprocess, tmp_path):
    # Generator changes may legitimately update generated MDX without touching
    # every module source, but only for pages that still have real source dirs.
    with patch("scripts.audit.check_mdx_source_parity.SOURCE_DIR", tmp_path):
        (tmp_path / "a1" / "01-hello").mkdir(parents=True)
        mdx_files = [MDX_DIR / "a1" / "01-hello.mdx"]
        changed_files = {
            MDX_DIR / "a1" / "01-hello.mdx",
            GENERATOR_PACKAGE / "core.py",
        }
        mock_subprocess.return_value = "1 file changed\n"

        violations = check_parity(mdx_files, changed_files)

    assert len(violations) == 0

def test_check_parity_generator_dependency_allows_existing_source_dir(mock_legacy_levels, mock_subprocess, tmp_path):
    # Shared parser code feeds the generator even though it lives outside
    # scripts/generate_mdx/.
    with patch("scripts.audit.check_mdx_source_parity.SOURCE_DIR", tmp_path):
        (tmp_path / "a1" / "01-hello").mkdir(parents=True)
        mdx_files = [MDX_DIR / "a1" / "01-hello.mdx"]
        changed_files = {
            MDX_DIR / "a1" / "01-hello.mdx",
            next(iter(GENERATOR_DEPENDENCIES)),
        }
        mock_subprocess.return_value = "1 file changed\n"

        violations = check_parity(mdx_files, changed_files)

    assert len(violations) == 0

def test_check_parity_generator_change_rejects_orphan_mdx(mock_legacy_levels, mock_subprocess, tmp_path):
    with patch("scripts.audit.check_mdx_source_parity.SOURCE_DIR", tmp_path):
        mdx_files = [MDX_DIR / "a1" / "orphan.mdx"]
        changed_files = {
            MDX_DIR / "a1" / "orphan.mdx",
            GENERATOR_PACKAGE / "core.py",
        }
        mock_subprocess.return_value = "1 file changed\n"

        violations = check_parity(mdx_files, changed_files)

    assert len(violations) == 1
    assert "MDX file changed but no source files changed" in violations[0][1]

def test_check_parity_source_only(mock_legacy_levels, mock_subprocess):
    # source-only diff (pass)
    mdx_files = []
    changed_files = {
        SOURCE_DIR / "a1" / "01-hello" / "01-hello.md"
    }

    violations = check_parity(mdx_files, changed_files)
    assert len(violations) == 0

def test_check_parity_legacy_level(mock_legacy_levels, mock_subprocess):
    # legacy-level MDX-only (pass via allowlist)
    mdx_files = [MDX_DIR / "hist" / "01-history.mdx"]
    changed_files = {MDX_DIR / "hist" / "01-history.mdx"}
    mock_subprocess.return_value = "1 file changed\n"

    violations = check_parity(mdx_files, changed_files)
    assert len(violations) == 0

def test_check_parity_whitespace_only(mock_legacy_levels, mock_subprocess):
    # whitespace-only MDX diff (pass per the exemption)
    mdx_files = [MDX_DIR / "a1" / "01-hello.mdx"]
    changed_files = {MDX_DIR / "a1" / "01-hello.mdx"}

    # Mock is_whitespace_only returning empty string
    mock_subprocess.return_value = ""

    violations = check_parity(mdx_files, changed_files)
    assert len(violations) == 0

def test_main_bulk_regen_env_var(mock_env, mock_subprocess, mock_legacy_levels):
    # bulk-regen MDX-only with env var (pass)
    os.environ["MDX_PARITY_BULK_REGEN"] = "1"

    mdx_paths = [f"site/src/content/docs/a1/{i}.mdx" for i in range(51)]
    mock_subprocess.return_value = "\n".join(mdx_paths)

    # We pass --changed-vs-base origin/main
    exit_code = main(["--changed-vs-base", "origin/main"])
    assert exit_code == 0

def test_main_single_file_regen_env_var(mock_env, mock_subprocess, mock_legacy_levels):
    # single-file regen without env var (fail) or with env var but only 1 file (fail)
    os.environ["MDX_PARITY_BULK_REGEN"] = "1"

    mdx_paths = ["site/src/content/docs/a1/01-hello.mdx"]

    def side_effect(cmd, **kwargs):
        if "merge-base" in cmd:
            return "mergebase"
        elif "--shortstat" in cmd:
            return "1 file changed\n" # Not whitespace-only
        else:
            return "\n".join(mdx_paths)

    mock_subprocess.side_effect = side_effect

    exit_code = main(["--changed-vs-base", "origin/main"])
    assert exit_code == 1
