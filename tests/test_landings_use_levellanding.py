import re
from pathlib import Path

import pytest
import yaml

from scripts import generate_landing_pages

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = PROJECT_ROOT / "site" / "src" / "content" / "docs"
CONTENT_CONFIG_PATH = PROJECT_ROOT / "site" / "src" / "content.config.ts"
ROUTER_PATH = PROJECT_ROOT / "site" / "src" / "pages" / "[...slug].astro"

REQUIRED_PROPS = (
    "level",
    "title",
    "subtitle",
    "moduleCount",
    "wordTarget",
    "color",
    "progressTitle",
    "progressDescription",
    "modules",
)

LEGACY_PROPS = (
    "levelName",
    "introduction",
    "totalPlanned",
)


def _track_landings() -> list[Path]:
    return sorted(path for path in DOCS_ROOT.glob("*/index.mdx") if path.parent != DOCS_ROOT)


def _has_prop(text: str, prop: str) -> bool:
    return re.search(rf"\b{re.escape(prop)}\s*=", text) is not None


@pytest.mark.parametrize("path", _track_landings(), ids=lambda path: path.parent.name)
def test_track_landing_uses_levellanding_contract(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    track = path.parent.name

    assert "import LevelLanding from '@site/src/components/LevelLanding';" in text
    assert re.search(r"<LevelLanding\b", text), f"{path} must render LevelLanding"
    assert "client:load" in text

    missing = [prop for prop in REQUIRED_PROPS if not _has_prop(text, prop)]
    assert not missing, f"{path} missing LevelLanding props: {', '.join(missing)}"

    legacy = [prop for prop in LEGACY_PROPS if _has_prop(text, prop)]
    assert not legacy, f"{path} still uses legacy LevelLanding props: {', '.join(legacy)}"

    forbidden = ["CourseLayout", "CORE LADDER"]
    matches = [marker for marker in forbidden if marker in text]
    assert not matches, f"{path} still contains old landing markup: {', '.join(matches)}"

    level_match = re.search(r'\blevel="([^"]+)"', text)
    assert level_match is not None
    assert level_match.group(1).lower() == track

    color_match = re.search(r'\bcolor="([^"]+)"', text)
    assert color_match is not None
    assert color_match.group(1) == f"var(--lu-id-{track})"

    module_count = re.search(r"\bmoduleCount=\{(\d+)\}", text)
    word_target = re.search(r"\bwordTarget=\{(\d+)\}", text)
    assert module_count is not None and int(module_count.group(1)) > 0
    assert word_target is not None and int(word_target.group(1)) > 0


def test_dynamic_route_uses_every_track_index_mdx_as_landing_doc() -> None:
    text = ROUTER_PATH.read_text(encoding="utf-8")

    assert "LANDING_DOC_TRACKS" not in text
    assert "track-overview" not in text
    assert "id !== 'index' && id === track" in text
    assert "landingDocsByPathTrack.set(track, entry)" in text
    assert "...landingDocsByPathTrack.keys()" in text
    assert "<LevelLanding" in text
    assert "showHero={props.kind !== 'landingDoc' && props.kind !== 'track'}" in text


def test_content_collection_loads_track_index_mdx_files() -> None:
    text = CONTENT_CONFIG_PATH.read_text(encoding="utf-8")
    tracks = {path.parent.name for path in _track_landings()}

    missing = sorted(track for track in tracks if track not in text)
    assert not missing, f"content loader does not include track indexes: {', '.join(missing)}"


def test_b2_landing_matches_generated_curriculum_state() -> None:
    curriculum = yaml.safe_load((PROJECT_ROOT / "curriculum" / "l2-uk-en" / "curriculum.yaml").read_text("utf-8"))
    expected = generate_landing_pages.generate_landing_page("b2", curriculum)
    actual = (DOCS_ROOT / "b2" / "index.mdx").read_text(encoding="utf-8")

    assert actual == expected, "Run `.venv/bin/python scripts/generate_landing_pages.py --track b2`."
