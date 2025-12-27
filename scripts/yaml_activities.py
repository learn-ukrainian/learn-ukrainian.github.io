#!/usr/bin/env python3
"""
Shared YAML Activity Parser

Single source of truth for parsing YAML activity files.
Used by both the MDX generator and the YAML validator.

Usage:
    from yaml_activities import ActivityParser

    parser = ActivityParser()
    activities = parser.parse('module.activities.yaml')
    result = parser.validate(activities, level='b1')
    mdx = parser.to_mdx(activities)
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Union

import yaml

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class QuizOption:
    text: str
    correct: bool


@dataclass
class QuizItem:
    question: str
    options: list[QuizOption]
    explanation: Optional[str] = None


@dataclass
class QuizActivity:
    type: str = "quiz"
    title: str = ""
    items: list[QuizItem] = field(default_factory=list)


@dataclass
class SelectItem:
    question: str
    options: list[QuizOption]
    min_correct: Optional[int] = None
    explanation: Optional[str] = None


@dataclass
class SelectActivity:
    type: str = "select"
    title: str = ""
    items: list[SelectItem] = field(default_factory=list)


@dataclass
class TrueFalseItem:
    statement: str
    correct: bool
    explanation: Optional[str] = None


@dataclass
class TrueFalseActivity:
    type: str = "true-false"
    title: str = ""
    items: list[TrueFalseItem] = field(default_factory=list)


@dataclass
class FillInItem:
    sentence: str
    answer: str
    options: list[str]
    explanation: Optional[str] = None


@dataclass
class FillInActivity:
    type: str = "fill-in"
    title: str = ""
    items: list[FillInItem] = field(default_factory=list)


@dataclass
class ClozeBlank:
    id: int
    answer: str
    options: list[str]


@dataclass
class ClozeActivity:
    type: str = "cloze"
    title: str = ""
    passage: str = ""
    blanks: list[ClozeBlank] = field(default_factory=list)


@dataclass
class MatchPair:
    left: str
    right: str


@dataclass
class MatchUpActivity:
    type: str = "match-up"
    title: str = ""
    pairs: list[MatchPair] = field(default_factory=list)


@dataclass
class GroupSortGroup:
    name: str
    items: list[str]


@dataclass
class GroupSortActivity:
    type: str = "group-sort"
    title: str = ""
    groups: list[GroupSortGroup] = field(default_factory=list)


@dataclass
class UnjumbleItem:
    words: list[str]
    answer: str


@dataclass
class UnjumbleActivity:
    type: str = "unjumble"
    title: str = ""
    items: list[UnjumbleItem] = field(default_factory=list)


@dataclass
class ErrorCorrectionItem:
    sentence: str
    error: str
    answer: str
    options: list[str]
    explanation: str


@dataclass
class ErrorCorrectionActivity:
    type: str = "error-correction"
    title: str = ""
    items: list[ErrorCorrectionItem] = field(default_factory=list)


@dataclass
class MarkTheWordsActivity:
    type: str = "mark-the-words"
    title: str = ""
    instruction: str = ""
    passage: str = ""
    correct_words: list[str] = field(default_factory=list)


@dataclass
class DialogueLine:
    order: int
    text: str
    speaker: Optional[str] = None


@dataclass
class DialogueReorderActivity:
    type: str = "dialogue-reorder"
    title: str = ""
    lines: list[DialogueLine] = field(default_factory=list)


@dataclass
class TranslateOption:
    text: str
    correct: bool


@dataclass
class TranslateItem:
    source: str
    options: list[TranslateOption]
    explanation: Optional[str] = None


@dataclass
class TranslateActivity:
    type: str = "translate"
    title: str = ""
    items: list[TranslateItem] = field(default_factory=list)


@dataclass
class AnagramItem:
    scrambled: str
    answer: str
    hint: Optional[str] = None


@dataclass
class AnagramActivity:
    type: str = "anagram"
    title: str = ""
    items: list[AnagramItem] = field(default_factory=list)


# Type alias for all activity types
Activity = Union[
    QuizActivity, SelectActivity, TrueFalseActivity, FillInActivity,
    ClozeActivity, MatchUpActivity, GroupSortActivity, UnjumbleActivity,
    ErrorCorrectionActivity, MarkTheWordsActivity, DialogueReorderActivity,
    TranslateActivity, AnagramActivity
]


# =============================================================================
# VALIDATION RESULT
# =============================================================================

@dataclass
class ValidationError:
    """A single validation error."""
    path: str  # JSON pointer to error location
    message: str
    activity_type: Optional[str] = None
    activity_title: Optional[str] = None
    severity: str = "error"  # "error" or "warning"


@dataclass
class ValidationResult:
    """Result of validation."""
    ok: bool = True
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[ValidationError] = field(default_factory=list)

    def add_error(self, path: str, message: str, **kwargs):
        self.errors.append(ValidationError(path=path, message=message, severity="error", **kwargs))
        self.ok = False

    def add_warning(self, path: str, message: str, **kwargs):
        self.warnings.append(ValidationError(path=path, message=message, severity="warning", **kwargs))


# =============================================================================
# PARSER
# =============================================================================

class ActivityParser:
    """
    Single source of truth for YAML activity parsing.

    Used by:
    - Generator: to convert YAML to MDX
    - Validator: to check YAML against schema and logic rules
    """

    def __init__(self, schemas_dir: Optional[Path] = None):
        """Initialize parser with optional schemas directory."""
        if schemas_dir is None:
            schemas_dir = Path(__file__).parent.parent / "schemas"
        self.schemas_dir = schemas_dir
        self._schema_cache: dict[str, dict] = {}

    def parse(self, yaml_path: Union[str, Path]) -> list[Activity]:
        """
        Parse YAML activity file into Activity objects.

        Args:
            yaml_path: Path to .activities.yaml file

        Returns:
            List of Activity objects
        """
        yaml_path = Path(yaml_path)

        with open(yaml_path, 'r', encoding='utf-8') as f:
            raw_data = yaml.safe_load(f)

        if raw_data is None:
            return []

        # Support both formats:
        # 1. Direct list: [{ type: quiz, ... }, ...]
        # 2. Wrapped in 'activities' key: { activities: [{ type: quiz, ... }, ...] }
        if isinstance(raw_data, dict) and 'activities' in raw_data:
            raw_data = raw_data['activities']

        if not isinstance(raw_data, list):
            raise ValueError(f"Expected list of activities, got {type(raw_data)}")

        activities = []
        for item in raw_data:
            activity = self._parse_activity(item)
            if activity:
                activities.append(activity)

        return activities

    def parse_yaml_string(self, yaml_content: str) -> list[Activity]:
        """Parse YAML content string into Activity objects."""
        raw_data = yaml.safe_load(yaml_content)

        if raw_data is None:
            return []

        # Support both formats:
        # 1. Direct list: [{ type: quiz, ... }, ...]
        # 2. Wrapped in 'activities' key: { activities: [{ type: quiz, ... }, ...] }
        if isinstance(raw_data, dict) and 'activities' in raw_data:
            raw_data = raw_data['activities']

        if not isinstance(raw_data, list):
            raise ValueError(f"Expected list of activities, got {type(raw_data)}")

        activities = []
        for item in raw_data:
            activity = self._parse_activity(item)
            if activity:
                activities.append(activity)

        return activities

    def _parse_activity(self, data: dict) -> Optional[Activity]:
        """Parse a single activity from dict to dataclass."""
        activity_type = data.get('type')

        parsers = {
            'quiz': self._parse_quiz,
            'select': self._parse_select,
            'true-false': self._parse_true_false,
            'fill-in': self._parse_fill_in,
            'cloze': self._parse_cloze,
            'match-up': self._parse_match_up,
            'group-sort': self._parse_group_sort,
            'unjumble': self._parse_unjumble,
            'error-correction': self._parse_error_correction,
            'mark-the-words': self._parse_mark_the_words,
            'dialogue-reorder': self._parse_dialogue_reorder,
            'translate': self._parse_translate,
            'anagram': self._parse_anagram,
        }

        parser = parsers.get(activity_type)
        if parser:
            return parser(data)

        return None

    def _parse_quiz(self, data: dict) -> QuizActivity:
        items = []
        for item_data in data.get('items', []):
            options = [
                QuizOption(text=opt['text'], correct=opt.get('correct', False))
                for opt in item_data.get('options', [])
            ]
            items.append(QuizItem(
                question=item_data['question'],
                options=options,
                explanation=item_data.get('explanation')
            ))
        return QuizActivity(title=data.get('title', ''), items=items)

    def _parse_select(self, data: dict) -> SelectActivity:
        items = []
        for item_data in data.get('items', []):
            options = [
                QuizOption(text=opt['text'], correct=opt.get('correct', False))
                for opt in item_data.get('options', [])
            ]
            items.append(SelectItem(
                question=item_data['question'],
                options=options,
                min_correct=item_data.get('min_correct'),
                explanation=item_data.get('explanation')
            ))
        return SelectActivity(title=data.get('title', ''), items=items)

    def _parse_true_false(self, data: dict) -> TrueFalseActivity:
        items = []
        for item_data in data.get('items', []):
            items.append(TrueFalseItem(
                statement=item_data['statement'],
                correct=item_data['correct'],
                explanation=item_data.get('explanation')
            ))
        return TrueFalseActivity(title=data.get('title', ''), items=items)

    def _parse_fill_in(self, data: dict) -> FillInActivity:
        items = []
        for item_data in data.get('items', []):
            items.append(FillInItem(
                sentence=item_data['sentence'],
                answer=item_data['answer'],
                options=item_data.get('options', []),
                explanation=item_data.get('explanation')
            ))
        return FillInActivity(title=data.get('title', ''), items=items)

    def _parse_cloze(self, data: dict) -> ClozeActivity:
        blanks = []
        for blank_data in data.get('blanks', []):
            blanks.append(ClozeBlank(
                id=blank_data['id'],
                answer=blank_data['answer'],
                options=blank_data.get('options', [])
            ))
        return ClozeActivity(
            title=data.get('title', ''),
            passage=data.get('passage', ''),
            blanks=blanks
        )

    def _parse_match_up(self, data: dict) -> MatchUpActivity:
        pairs = []
        for pair_data in data.get('pairs', []):
            pairs.append(MatchPair(
                left=pair_data['left'],
                right=pair_data['right']
            ))
        return MatchUpActivity(title=data.get('title', ''), pairs=pairs)

    def _parse_group_sort(self, data: dict) -> GroupSortActivity:
        groups = []
        for group_data in data.get('groups', []):
            groups.append(GroupSortGroup(
                name=group_data['name'],
                items=group_data.get('items', [])
            ))
        return GroupSortActivity(title=data.get('title', ''), groups=groups)

    def _parse_unjumble(self, data: dict) -> UnjumbleActivity:
        items = []
        for item_data in data.get('items', []):
            items.append(UnjumbleItem(
                words=item_data.get('words', []),
                answer=item_data['answer']
            ))
        return UnjumbleActivity(title=data.get('title', ''), items=items)

    def _parse_error_correction(self, data: dict) -> ErrorCorrectionActivity:
        items = []
        for item_data in data.get('items', []):
            items.append(ErrorCorrectionItem(
                sentence=item_data['sentence'],
                error=item_data['error'],
                answer=item_data['answer'],
                options=item_data.get('options', []),
                explanation=item_data.get('explanation', '')
            ))
        return ErrorCorrectionActivity(title=data.get('title', ''), items=items)

    def _parse_mark_the_words(self, data: dict) -> MarkTheWordsActivity:
        return MarkTheWordsActivity(
            title=data.get('title', ''),
            instruction=data.get('instruction', ''),
            passage=data.get('passage', ''),
            correct_words=data.get('correct_words', [])
        )

    def _parse_dialogue_reorder(self, data: dict) -> DialogueReorderActivity:
        lines = []
        for i, line_data in enumerate(data.get('lines', []), start=1):
            lines.append(DialogueLine(
                order=line_data.get('order', i),  # Use implicit order if not specified
                text=line_data['text'],
                speaker=line_data.get('speaker')
            ))
        return DialogueReorderActivity(title=data.get('title', ''), lines=lines)

    def _parse_translate(self, data: dict) -> TranslateActivity:
        items = []
        for item_data in data.get('items', []):
            options = [
                TranslateOption(text=opt['text'], correct=opt.get('correct', False))
                for opt in item_data.get('options', [])
            ]
            items.append(TranslateItem(
                source=item_data['source'],
                options=options,
                explanation=item_data.get('explanation')
            ))
        return TranslateActivity(title=data.get('title', ''), items=items)

    def _parse_anagram(self, data: dict) -> AnagramActivity:
        items = []
        for item_data in data.get('items', []):
            items.append(AnagramItem(
                scrambled=item_data['scrambled'],
                answer=item_data['answer'],
                hint=item_data.get('hint')
            ))
        return AnagramActivity(title=data.get('title', ''), items=items)

    # =========================================================================
    # VALIDATION
    # =========================================================================

    def validate(self, activities: list[Activity], level: str) -> ValidationResult:
        """
        Validate activities against level-specific rules.

        Args:
            activities: List of Activity objects
            level: Level code (a1, a2, b1, b2, c1, c2)

        Returns:
            ValidationResult with errors and warnings
        """
        result = ValidationResult(ok=True)

        # Stage 1: Schema validation (if jsonschema available)
        if HAS_JSONSCHEMA:
            schema_result = self._validate_schema(activities, level)
            result.errors.extend(schema_result.errors)
            result.warnings.extend(schema_result.warnings)
            if not schema_result.ok:
                result.ok = False

        # Stage 2: Logic validation
        logic_result = self._validate_logic(activities, level)
        result.errors.extend(logic_result.errors)
        result.warnings.extend(logic_result.warnings)
        if not logic_result.ok:
            result.ok = False

        return result

    def _get_schema(self, level: str) -> Optional[dict]:
        """Load JSON Schema for level."""
        # Map level to schema file
        if level == 'a1':
            schema_file = 'activities-a1.schema.json'
        elif level == 'a2':
            schema_file = 'activities-a2.schema.json'
        else:  # b1, b2, c1, c2
            schema_file = 'activities-b1.schema.json'

        if schema_file in self._schema_cache:
            return self._schema_cache[schema_file]

        schema_path = self.schemas_dir / schema_file
        if not schema_path.exists():
            return None

        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = json.load(f)

        self._schema_cache[schema_file] = schema
        return schema

    def _validate_schema(self, activities: list[Activity], level: str) -> ValidationResult:
        """Validate against JSON Schema."""
        result = ValidationResult(ok=True)

        schema = self._get_schema(level)
        if schema is None:
            result.add_warning("/", f"No schema found for level {level}")
            return result

        # Convert activities back to dict for schema validation
        activities_dict = self._activities_to_dict(activities)

        try:
            jsonschema.validate(activities_dict, schema)
        except jsonschema.ValidationError as e:
            # Format the error nicely
            path = '/'.join(str(p) for p in e.absolute_path) if e.absolute_path else '/'
            result.add_error(
                path=path,
                message=e.message,
                activity_type=self._get_activity_type_at_path(activities_dict, e.absolute_path),
                activity_title=self._get_activity_title_at_path(activities_dict, e.absolute_path)
            )

        return result

    def _validate_logic(self, activities: list[Activity], level: str) -> ValidationResult:
        """Validate business logic rules."""
        result = ValidationResult(ok=True)

        for i, activity in enumerate(activities):
            prefix = f"/{i}"

            # Check activity type is allowed for level
            allowed = self._get_allowed_activities(level)
            if activity.type not in allowed:
                result.add_error(
                    path=prefix,
                    message=f"Activity type '{activity.type}' not allowed at level {level.upper()}",
                    activity_type=activity.type,
                    activity_title=getattr(activity, 'title', None)
                )
                continue

            # Type-specific logic validation
            if isinstance(activity, QuizActivity):
                self._validate_quiz_logic(activity, prefix, result)
            elif isinstance(activity, SelectActivity):
                self._validate_select_logic(activity, prefix, result)
            elif isinstance(activity, FillInActivity):
                self._validate_fill_in_logic(activity, prefix, result)
            elif isinstance(activity, ClozeActivity):
                self._validate_cloze_logic(activity, prefix, result)
            elif isinstance(activity, ErrorCorrectionActivity):
                self._validate_error_correction_logic(activity, prefix, result)
            elif isinstance(activity, MarkTheWordsActivity):
                self._validate_mark_the_words_logic(activity, prefix, result)
            elif isinstance(activity, DialogueReorderActivity):
                self._validate_dialogue_reorder_logic(activity, prefix, result)
            elif isinstance(activity, TranslateActivity):
                self._validate_translate_logic(activity, prefix, result)

        return result

    def _get_allowed_activities(self, level: str) -> set[str]:
        """Get allowed activity types for level."""
        base = {'quiz', 'match-up', 'fill-in', 'group-sort', 'unjumble', 'true-false'}

        if level == 'a1':
            return base | {'anagram'}
        elif level == 'a2':
            return base | {'cloze', 'error-correction', 'mark-the-words',
                          'dialogue-reorder', 'select', 'translate'}
        else:  # b1+
            return base | {'cloze', 'error-correction', 'mark-the-words',
                          'dialogue-reorder', 'select', 'translate'}

    def _validate_quiz_logic(self, activity: QuizActivity, prefix: str, result: ValidationResult):
        """Validate quiz-specific logic."""
        for i, item in enumerate(activity.items):
            correct_count = sum(1 for opt in item.options if opt.correct)
            if correct_count == 0:
                result.add_error(
                    path=f"{prefix}/items/{i}",
                    message="No correct answer in quiz question",
                    activity_type="quiz",
                    activity_title=activity.title
                )
            elif correct_count > 1:
                result.add_error(
                    path=f"{prefix}/items/{i}",
                    message=f"Quiz question has {correct_count} correct answers (should be 1)",
                    activity_type="quiz",
                    activity_title=activity.title
                )

    def _validate_select_logic(self, activity: SelectActivity, prefix: str, result: ValidationResult):
        """Validate select-specific logic."""
        for i, item in enumerate(activity.items):
            correct_count = sum(1 for opt in item.options if opt.correct)
            if correct_count < 2:
                result.add_error(
                    path=f"{prefix}/items/{i}",
                    message=f"Select question needs at least 2 correct answers (has {correct_count})",
                    activity_type="select",
                    activity_title=activity.title
                )

    def _validate_fill_in_logic(self, activity: FillInActivity, prefix: str, result: ValidationResult):
        """Validate fill-in-specific logic."""
        for i, item in enumerate(activity.items):
            if item.answer not in item.options:
                result.add_error(
                    path=f"{prefix}/items/{i}",
                    message=f"Answer '{item.answer}' not in options list",
                    activity_type="fill-in",
                    activity_title=activity.title
                )
            if '___' not in item.sentence and '[___]' not in item.sentence:
                result.add_warning(
                    path=f"{prefix}/items/{i}",
                    message="Sentence doesn't contain blank marker (___)",
                    activity_type="fill-in",
                    activity_title=activity.title
                )

    def _validate_cloze_logic(self, activity: ClozeActivity, prefix: str, result: ValidationResult):
        """Validate cloze-specific logic."""
        # Check all blanks have answers in options
        for i, blank in enumerate(activity.blanks):
            if blank.answer not in blank.options:
                result.add_error(
                    path=f"{prefix}/blanks/{i}",
                    message=f"Answer '{blank.answer}' not in options list",
                    activity_type="cloze",
                    activity_title=activity.title
                )

        # Check passage has correct number of blank markers
        blank_ids = {b.id for b in activity.blanks}
        for blank_id in blank_ids:
            marker = f"{{{blank_id}}}"
            if marker not in activity.passage:
                result.add_warning(
                    path=f"{prefix}/passage",
                    message=f"Blank marker {marker} not found in passage",
                    activity_type="cloze",
                    activity_title=activity.title
                )

    def _validate_error_correction_logic(self, activity: ErrorCorrectionActivity, prefix: str, result: ValidationResult):
        """Validate error-correction-specific logic."""
        for i, item in enumerate(activity.items):
            # Error word should appear in sentence
            if item.error not in item.sentence:
                result.add_error(
                    path=f"{prefix}/items/{i}",
                    message=f"Error word '{item.error}' not found in sentence",
                    activity_type="error-correction",
                    activity_title=activity.title
                )
            # Answer should be in options
            if item.answer not in item.options:
                result.add_error(
                    path=f"{prefix}/items/{i}",
                    message=f"Answer '{item.answer}' not in options list",
                    activity_type="error-correction",
                    activity_title=activity.title
                )
            # Error should be in options
            if item.error not in item.options:
                result.add_warning(
                    path=f"{prefix}/items/{i}",
                    message=f"Error word '{item.error}' not in options (common pattern)",
                    activity_type="error-correction",
                    activity_title=activity.title
                )

    def _validate_mark_the_words_logic(self, activity: MarkTheWordsActivity, prefix: str, result: ValidationResult):
        """Validate mark-the-words-specific logic."""
        for i, word in enumerate(activity.correct_words):
            if word not in activity.passage:
                result.add_error(
                    path=f"{prefix}/correct_words/{i}",
                    message=f"Word '{word}' not found in passage",
                    activity_type="mark-the-words",
                    activity_title=activity.title
                )

    def _validate_dialogue_reorder_logic(self, activity: DialogueReorderActivity, prefix: str, result: ValidationResult):
        """Validate dialogue-reorder-specific logic."""
        orders = [line.order for line in activity.lines]
        expected = list(range(1, len(activity.lines) + 1))

        if sorted(orders) != expected:
            result.add_error(
                path=f"{prefix}/lines",
                message=f"Order numbers should be 1 to {len(activity.lines)}, got {sorted(orders)}",
                activity_type="dialogue-reorder",
                activity_title=activity.title
            )

    def _validate_translate_logic(self, activity: TranslateActivity, prefix: str, result: ValidationResult):
        """Validate translate-specific logic."""
        for i, item in enumerate(activity.items):
            correct_count = sum(1 for opt in item.options if opt.correct)
            if correct_count == 0:
                result.add_error(
                    path=f"{prefix}/items/{i}",
                    message="No correct translation option",
                    activity_type="translate",
                    activity_title=activity.title
                )

    def _activities_to_dict(self, activities: list[Activity]) -> list[dict]:
        """Convert Activity objects back to dict for schema validation."""
        result = []
        for activity in activities:
            result.append(self._activity_to_dict(activity))
        return result

    def _activity_to_dict(self, activity: Activity) -> dict:
        """Convert single Activity to dict."""
        if isinstance(activity, QuizActivity):
            return {
                'type': 'quiz',
                'title': activity.title,
                'items': [
                    {
                        'question': item.question,
                        'options': [{'text': opt.text, 'correct': opt.correct} for opt in item.options],
                        **(({'explanation': item.explanation} if item.explanation else {}))
                    }
                    for item in activity.items
                ]
            }
        elif isinstance(activity, SelectActivity):
            return {
                'type': 'select',
                'title': activity.title,
                'items': [
                    {
                        'question': item.question,
                        'options': [{'text': opt.text, 'correct': opt.correct} for opt in item.options],
                        **(({'min_correct': item.min_correct} if item.min_correct else {})),
                        **(({'explanation': item.explanation} if item.explanation else {}))
                    }
                    for item in activity.items
                ]
            }
        elif isinstance(activity, TrueFalseActivity):
            return {
                'type': 'true-false',
                'title': activity.title,
                'items': [
                    {
                        'statement': item.statement,
                        'correct': item.correct,
                        **(({'explanation': item.explanation} if item.explanation else {}))
                    }
                    for item in activity.items
                ]
            }
        elif isinstance(activity, FillInActivity):
            return {
                'type': 'fill-in',
                'title': activity.title,
                'items': [
                    {
                        'sentence': item.sentence,
                        'answer': item.answer,
                        'options': item.options,
                        **(({'explanation': item.explanation} if item.explanation else {}))
                    }
                    for item in activity.items
                ]
            }
        elif isinstance(activity, ClozeActivity):
            return {
                'type': 'cloze',
                'title': activity.title,
                'passage': activity.passage,
                'blanks': [
                    {
                        'id': blank.id,
                        'answer': blank.answer,
                        'options': blank.options
                    }
                    for blank in activity.blanks
                ]
            }
        elif isinstance(activity, MatchUpActivity):
            return {
                'type': 'match-up',
                'title': activity.title,
                'pairs': [
                    {'left': pair.left, 'right': pair.right}
                    for pair in activity.pairs
                ]
            }
        elif isinstance(activity, GroupSortActivity):
            return {
                'type': 'group-sort',
                'title': activity.title,
                'groups': [
                    {'name': group.name, 'items': group.items}
                    for group in activity.groups
                ]
            }
        elif isinstance(activity, UnjumbleActivity):
            return {
                'type': 'unjumble',
                'title': activity.title,
                'items': [
                    {'words': item.words, 'answer': item.answer}
                    for item in activity.items
                ]
            }
        elif isinstance(activity, ErrorCorrectionActivity):
            return {
                'type': 'error-correction',
                'title': activity.title,
                'items': [
                    {
                        'sentence': item.sentence,
                        'error': item.error,
                        'answer': item.answer,
                        'options': item.options,
                        'explanation': item.explanation
                    }
                    for item in activity.items
                ]
            }
        elif isinstance(activity, MarkTheWordsActivity):
            return {
                'type': 'mark-the-words',
                'title': activity.title,
                'instruction': activity.instruction,
                'passage': activity.passage,
                'correct_words': activity.correct_words
            }
        elif isinstance(activity, DialogueReorderActivity):
            return {
                'type': 'dialogue-reorder',
                'title': activity.title,
                'lines': [
                    {
                        'order': line.order,
                        'text': line.text,
                        **(({'speaker': line.speaker} if line.speaker else {}))
                    }
                    for line in activity.lines
                ]
            }
        elif isinstance(activity, TranslateActivity):
            return {
                'type': 'translate',
                'title': activity.title,
                'items': [
                    {
                        'source': item.source,
                        'options': [{'text': opt.text, 'correct': opt.correct} for opt in item.options],
                        **(({'explanation': item.explanation} if item.explanation else {}))
                    }
                    for item in activity.items
                ]
            }
        elif isinstance(activity, AnagramActivity):
            return {
                'type': 'anagram',
                'title': activity.title,
                'items': [
                    {
                        'scrambled': item.scrambled,
                        'answer': item.answer,
                        **(({'hint': item.hint} if item.hint else {}))
                    }
                    for item in activity.items
                ]
            }
        return {}

    def _get_activity_type_at_path(self, data: list, path) -> Optional[str]:
        """Get activity type at JSON path."""
        try:
            if len(path) > 0:
                idx = path[0]
                if isinstance(idx, int) and 0 <= idx < len(data):
                    return data[idx].get('type')
        except (IndexError, KeyError, TypeError):
            pass
        return None

    def _get_activity_title_at_path(self, data: list, path) -> Optional[str]:
        """Get activity title at JSON path."""
        try:
            if len(path) > 0:
                idx = path[0]
                if isinstance(idx, int) and 0 <= idx < len(data):
                    return data[idx].get('title')
        except (IndexError, KeyError, TypeError):
            pass
        return None

    # =========================================================================
    # MDX GENERATION
    # =========================================================================

    def to_mdx(self, activities: list[Activity]) -> str:
        """
        Convert activities to MDX component format.

        This generates the same output as the current MD parser,
        ensuring backward compatibility.
        """
        mdx_parts = []

        for activity in activities:
            mdx = self._activity_to_mdx(activity)
            if mdx:
                mdx_parts.append(mdx)

        return '\n\n'.join(mdx_parts)

    def _activity_to_mdx(self, activity: Activity) -> str:
        """Convert single activity to MDX."""
        if isinstance(activity, QuizActivity):
            return self._quiz_to_mdx(activity)
        elif isinstance(activity, SelectActivity):
            return self._select_to_mdx(activity)
        elif isinstance(activity, TrueFalseActivity):
            return self._true_false_to_mdx(activity)
        elif isinstance(activity, FillInActivity):
            return self._fill_in_to_mdx(activity)
        elif isinstance(activity, ClozeActivity):
            return self._cloze_to_mdx(activity)
        elif isinstance(activity, MatchUpActivity):
            return self._match_up_to_mdx(activity)
        elif isinstance(activity, GroupSortActivity):
            return self._group_sort_to_mdx(activity)
        elif isinstance(activity, UnjumbleActivity):
            return self._unjumble_to_mdx(activity)
        elif isinstance(activity, ErrorCorrectionActivity):
            return self._error_correction_to_mdx(activity)
        elif isinstance(activity, MarkTheWordsActivity):
            return self._mark_the_words_to_mdx(activity)
        elif isinstance(activity, DialogueReorderActivity):
            return self._dialogue_reorder_to_mdx(activity)
        elif isinstance(activity, TranslateActivity):
            return self._translate_to_mdx(activity)
        elif isinstance(activity, AnagramActivity):
            return self._anagram_to_mdx(activity)
        return ''

    def _escape_jsx(self, text: str) -> str:
        """Escape text for use in JSX strings."""
        if not text:
            return ''
        text = text.replace('\\', '\\\\')
        text = text.replace('`', '\\`')
        text = text.replace('"', '\\"')
        text = text.replace('${', '\\${')
        return text

    def _quiz_to_mdx(self, activity: QuizActivity) -> str:
        items_json = json.dumps([
            {
                'question': self._escape_jsx(item.question),
                'options': [{'text': self._escape_jsx(opt.text), 'correct': opt.correct} for opt in item.options]
            }
            for item in activity.items
        ], ensure_ascii=False)

        return f'''<Quiz
  title="{self._escape_jsx(activity.title)}"
  questions={{JSON.parse(`{items_json}`)}}
/>'''

    def _select_to_mdx(self, activity: SelectActivity) -> str:
        items_json = json.dumps([
            {
                'question': self._escape_jsx(item.question),
                'options': [{'text': self._escape_jsx(opt.text), 'correct': opt.correct} for opt in item.options]
            }
            for item in activity.items
        ], ensure_ascii=False)

        return f'''<Select
  title="{self._escape_jsx(activity.title)}"
  questions={{JSON.parse(`{items_json}`)}}
/>'''

    def _true_false_to_mdx(self, activity: TrueFalseActivity) -> str:
        items_json = json.dumps([
            {
                'statement': self._escape_jsx(item.statement),
                'isTrue': item.correct,
                'explanation': self._escape_jsx(item.explanation or '')
            }
            for item in activity.items
        ], ensure_ascii=False)

        return f'''<TrueFalse
  title="{self._escape_jsx(activity.title)}"
  statements={{JSON.parse(`{items_json}`)}}
/>'''

    def _fill_in_to_mdx(self, activity: FillInActivity) -> str:
        items_json = json.dumps([
            {
                'sentence': self._escape_jsx(item.sentence),
                'answer': self._escape_jsx(item.answer),
                'options': [self._escape_jsx(opt) for opt in item.options]
            }
            for item in activity.items
        ], ensure_ascii=False)

        return f'''<FillIn
  title="{self._escape_jsx(activity.title)}"
  sentences={{JSON.parse(`{items_json}`)}}
/>'''

    def _cloze_to_mdx(self, activity: ClozeActivity) -> str:
        blanks_json = json.dumps([
            {
                'answer': self._escape_jsx(blank.answer),
                'options': [self._escape_jsx(opt) for opt in blank.options]
            }
            for blank in activity.blanks
        ], ensure_ascii=False)

        return f'''<Cloze
  title="{self._escape_jsx(activity.title)}"
  passage="{self._escape_jsx(activity.passage)}"
  blanks={{JSON.parse(`{blanks_json}`)}}
/>'''

    def _match_up_to_mdx(self, activity: MatchUpActivity) -> str:
        pairs_json = json.dumps([
            {
                'left': self._escape_jsx(pair.left),
                'right': self._escape_jsx(pair.right)
            }
            for pair in activity.pairs
        ], ensure_ascii=False)

        return f'''<MatchUp
  title="{self._escape_jsx(activity.title)}"
  pairs={{JSON.parse(`{pairs_json}`)}}
/>'''

    def _group_sort_to_mdx(self, activity: GroupSortActivity) -> str:
        groups_dict = {
            group.name: [self._escape_jsx(item) for item in group.items]
            for group in activity.groups
        }
        groups_json = json.dumps(groups_dict, ensure_ascii=False)

        return f'''<GroupSort
  title="{self._escape_jsx(activity.title)}"
  groups={{JSON.parse(`{groups_json}`)}}
/>'''

    def _unjumble_to_mdx(self, activity: UnjumbleActivity) -> str:
        items_json = json.dumps([
            {
                'jumbled': ' / '.join(item.words),
                'answer': self._escape_jsx(item.answer)
            }
            for item in activity.items
        ], ensure_ascii=False)

        return f'''<Unjumble
  title="{self._escape_jsx(activity.title)}"
  sentences={{JSON.parse(`{items_json}`)}}
/>'''

    def _error_correction_to_mdx(self, activity: ErrorCorrectionActivity) -> str:
        items_json = json.dumps([
            {
                'sentence': self._escape_jsx(item.sentence),
                'errorWord': self._escape_jsx(item.error),
                'correctForm': self._escape_jsx(item.answer),
                'options': [self._escape_jsx(opt) for opt in item.options],
                'explanation': self._escape_jsx(item.explanation)
            }
            for item in activity.items
        ], ensure_ascii=False)

        return f'''<ErrorCorrection
  title="{self._escape_jsx(activity.title)}"
  sentences={{JSON.parse(`{items_json}`)}}
/>'''

    def _mark_the_words_to_mdx(self, activity: MarkTheWordsActivity) -> str:
        correct_words_json = json.dumps(
            [self._escape_jsx(word) for word in activity.correct_words],
            ensure_ascii=False
        )

        return f'''<MarkTheWords
  title="{self._escape_jsx(activity.title)}"
  instruction="{self._escape_jsx(activity.instruction)}"
  text="{self._escape_jsx(activity.passage)}"
  correctWords={{JSON.parse(`{correct_words_json}`)}}
/>'''

    def _dialogue_reorder_to_mdx(self, activity: DialogueReorderActivity) -> str:
        lines_json = json.dumps([
            {
                'text': self._escape_jsx(line.text),
                'order': line.order
            }
            for line in activity.lines
        ], ensure_ascii=False)

        return f'''<DialogueReorder
  title="{self._escape_jsx(activity.title)}"
  lines={{JSON.parse(`{lines_json}`)}}
/>'''

    def _translate_to_mdx(self, activity: TranslateActivity) -> str:
        items_json = json.dumps([
            {
                'source': self._escape_jsx(item.source),
                'options': [{'text': self._escape_jsx(opt.text), 'correct': opt.correct} for opt in item.options]
            }
            for item in activity.items
        ], ensure_ascii=False)

        return f'''<Translate
  title="{self._escape_jsx(activity.title)}"
  sentences={{JSON.parse(`{items_json}`)}}
/>'''

    def _anagram_to_mdx(self, activity: AnagramActivity) -> str:
        items_json = json.dumps([
            {
                'scrambled': self._escape_jsx(item.scrambled),
                'answer': self._escape_jsx(item.answer),
                'hint': self._escape_jsx(item.hint or '')
            }
            for item in activity.items
        ], ensure_ascii=False)

        return f'''<Anagram
  title="{self._escape_jsx(activity.title)}"
  words={{JSON.parse(`{items_json}`)}}
/>'''


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_activity_source(module_path: Path) -> tuple[str, Path]:
    """
    Determine activity source format for a module.

    Returns:
        ('yaml', yaml_path) if YAML file exists
        ('md', module_path) if only MD file exists
    """
    yaml_path = module_path.with_suffix('.activities.yaml')
    if yaml_path.exists():
        return 'yaml', yaml_path
    return 'md', module_path


def parse_activities(module_path: Path) -> list[Activity]:
    """
    Parse activities from either YAML or MD source.

    Prefers YAML if available, falls back to MD.
    """
    source_type, source_path = get_activity_source(module_path)

    if source_type == 'yaml':
        parser = ActivityParser()
        return parser.parse(source_path)
    else:
        # Fall back to existing MD parsing
        # This would be imported from generate_mdx.py
        raise NotImplementedError("MD parsing should use existing generate_mdx.py functions")


# =============================================================================
# CLI
# =============================================================================

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python yaml_activities.py <yaml_file> [--validate <level>]")
        sys.exit(1)

    yaml_file = sys.argv[1]
    parser = ActivityParser()

    try:
        activities = parser.parse(yaml_file)
        print(f"Parsed {len(activities)} activities from {yaml_file}")

        for i, activity in enumerate(activities):
            print(f"  [{i+1}] {activity.type}: {getattr(activity, 'title', 'untitled')}")

        if '--validate' in sys.argv:
            level_idx = sys.argv.index('--validate') + 1
            level = sys.argv[level_idx] if level_idx < len(sys.argv) else 'b1'

            result = parser.validate(activities, level)

            if result.ok:
                print(f"\n✓ Validation passed for level {level.upper()}")
            else:
                print(f"\n✗ Validation failed for level {level.upper()}")
                for error in result.errors:
                    print(f"  ERROR at {error.path}: {error.message}")

            if result.warnings:
                for warning in result.warnings:
                    print(f"  WARNING at {warning.path}: {warning.message}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
