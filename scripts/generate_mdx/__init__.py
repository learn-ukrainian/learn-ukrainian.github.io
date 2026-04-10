"""MDX Generator package for Starlight.

Converts curriculum markdown modules to MDX format with React components.
This package replaces the monolithic generate_mdx.py with a modular structure.

Re-exports all public symbols for backward compatibility with existing imports
like ``from generate_mdx import generate_mdx, escape_jsx``.
"""

# Dataclasses
# Converters
from .converters import (
    CALLOUT_MAP,
    comparative_study_to_jsx,
    convert_callouts,
    essay_response_to_jsx,
    highlight_morphemes_to_jsx,
    normalize_mdx,
    process_dialogues,
    process_story_sections,
    resolve_slug_links,
    yaml_activities_to_jsx,
)

# Core
from .core import (
    detect_pipeline_info,
    generate_mdx,
    get_modules_from_manifest,
    main,
    parse_frontmatter,
)
from .dataclasses_ import (
    AnagramItem,
    ClozeData,
    ComparativeStudyData,
    ErrorCorrectionItem,
    EssayResponseData,
    FillInItem,
    GroupSortData,
    HighlightMorphemesItem,
    MarkTheWordsItem,
    MatchPair,
    MorphemeItem,
    QuizQuestion,
    SelectQuestion,
    TranslateQuestion,
    TrueFalseItem,
    UnjumbleItem,
)

# Parsers
from .parsers import (
    has_morpheme_patterns,
    parse_anagram,
    parse_cloze,
    parse_comparative_study,
    parse_error_correction,
    parse_essay_response,
    parse_fill_in,
    parse_group_sort,
    parse_highlight_morphemes,
    parse_mark_the_words,
    parse_match_up,
    parse_quiz,
    parse_select,
    parse_translate,
    parse_true_false,
    parse_unjumble,
)
from .resources import (
    b1_vocab_items_to_markdown as _b1_vocab_items_to_markdown,
)

# Resources (re-export with original underscore-prefixed names for backward compat)
from .resources import (
    embed_youtube_video_links as _embed_youtube_video_links,
)
from .resources import (
    format_resources_for_mdx,
    validate_and_clean_url,
)
from .resources import (
    load_discovery_resources as _load_discovery_resources,
)
from .resources import (
    merge_resources as _merge_resources,
)
from .resources import (
    vocab_items_to_markdown as _vocab_items_to_markdown,
)

# Utilities
from .utils import dump_json_for_jsx, escape_jsx, fix_html_for_jsx

__all__ = [  # noqa: RUF022 — intentionally grouped by category (Dataclasses, Utilities, Parsers, ...), not alphabetical
    # Dataclasses
    "AnagramItem",
    "ClozeData",
    "ComparativeStudyData",
    "ErrorCorrectionItem",
    "EssayResponseData",
    "FillInItem",
    "GroupSortData",
    "HighlightMorphemesItem",
    "MarkTheWordsItem",
    "MatchPair",
    "MorphemeItem",
    "QuizQuestion",
    "SelectQuestion",
    "TranslateQuestion",
    "TrueFalseItem",
    "UnjumbleItem",
    # Utilities
    "dump_json_for_jsx",
    "escape_jsx",
    "fix_html_for_jsx",
    # Parsers
    "has_morpheme_patterns",
    "parse_anagram",
    "parse_cloze",
    "parse_comparative_study",
    "parse_error_correction",
    "parse_essay_response",
    "parse_fill_in",
    "parse_group_sort",
    "parse_highlight_morphemes",
    "parse_mark_the_words",
    "parse_match_up",
    "parse_quiz",
    "parse_select",
    "parse_translate",
    "parse_true_false",
    "parse_unjumble",
    # Converters
    "CALLOUT_MAP",
    "comparative_study_to_jsx",
    "convert_callouts",
    "essay_response_to_jsx",
    "highlight_morphemes_to_jsx",
    "normalize_mdx",
    "process_dialogues",
    "process_story_sections",
    "resolve_slug_links",
    "yaml_activities_to_jsx",
    # Resources
    "_embed_youtube_video_links",
    "format_resources_for_mdx",
    "_load_discovery_resources",
    "_merge_resources",
    "validate_and_clean_url",
    "_vocab_items_to_markdown",
    "_b1_vocab_items_to_markdown",
    # Core
    "detect_pipeline_info",
    "generate_mdx",
    "get_modules_from_manifest",
    "main",
    "parse_frontmatter",
]
