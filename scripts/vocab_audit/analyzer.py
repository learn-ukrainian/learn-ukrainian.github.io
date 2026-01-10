"""
Vocabulary Analyzer

Analyzes vocabulary for:
1. Duplicates across levels
2. Missing words (in plan but not in modules)
3. Extra words (in modules but not in plan)
"""

from typing import Dict, List, Tuple, Set
from collections import defaultdict


class VocabularyAnalyzer:
    """Analyze vocabulary for duplicates, missing, and extra words."""

    def __init__(self):
        """Initialize analyzer."""
        self.duplicate_index = defaultdict(list)  # word -> [(level, module), ...]

    def find_duplicates(self, levels: List[str], word_locations: Dict[str, List[Tuple[str, str]]]) -> Dict[str, List[Tuple[str, str]]]:
        """
        Find words that appear in multiple levels.

        Args:
            levels: List of levels to check (e.g., ['a1', 'a2', 'b1'])
            word_locations: Dict mapping word to list of (level, module) locations

        Returns:
            Dictionary mapping duplicate word to list of locations
            Only includes words appearing in 2+ levels
        """
        duplicates = {}

        for word, locations in word_locations.items():
            # Extract unique levels from locations
            levels_with_word = set(loc.split()[0] for loc in locations)

            if len(levels_with_word) > 1:
                duplicates[word] = locations

        return duplicates

    def find_missing_words(self, plan_vocab: Dict[str, List[str]], module_vocab: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """
        Find words in curriculum plan but not in module YAML files.

        Args:
            plan_vocab: Dict mapping module number to list of planned words
            module_vocab: Dict mapping module number to list of actual module words

        Returns:
            Dictionary mapping module number to list of missing words
        """
        missing = {}

        for module_num, planned_words in plan_vocab.items():
            actual_words = set(module_vocab.get(module_num, []))
            missing_words = [w for w in planned_words if w not in actual_words]

            if missing_words:
                missing[module_num] = missing_words

        return missing

    def find_extra_words(self, plan_vocab: Dict[str, List[str]], module_vocab: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """
        Find words in module YAML files but not in curriculum plan.

        Args:
            plan_vocab: Dict mapping module number to list of planned words
            module_vocab: Dict mapping module number to list of actual module words

        Returns:
            Dictionary mapping module number to list of extra words
        """
        extra = {}

        for module_num, actual_words in module_vocab.items():
            planned_words = set(plan_vocab.get(module_num, []))
            extra_words = [w for w in actual_words if w not in planned_words]

            if extra_words:
                extra[module_num] = extra_words

        return extra

    def build_word_index(self, levels: List[str], parser) -> Dict[str, List[Tuple[str, str]]]:
        """
        Build a comprehensive word index across all levels.

        Args:
            levels: List of levels to index (e.g., ['a1', 'a2', 'b1', 'b2'])
            parser: VocabularyParser instance

        Returns:
            Dictionary mapping word to list of (level, module) locations
        """
        word_index = defaultdict(list)

        for level in levels:
            _, word_locations = parser.get_all_words_by_level(level)

            for word, location in word_locations:
                word_index[word].append(location)

        return dict(word_index)

    def get_vocabulary_stats(self, levels: List[str], parser) -> Dict[str, Dict[str, int]]:
        """
        Get vocabulary statistics for each level.

        Args:
            levels: List of levels to analyze
            parser: VocabularyParser instance

        Returns:
            Dictionary mapping level to stats dict with keys:
            - total_words: Total unique words
            - modules: Number of modules
            - avg_per_module: Average words per module
        """
        stats = {}

        for level in levels:
            unique_words, word_locations = parser.get_all_words_by_level(level)
            module_vocab = parser.parse_module_vocabulary(level)

            total_modules = len(module_vocab)
            total_words = len(unique_words)
            avg_per_module = total_words / total_modules if total_modules > 0 else 0

            stats[level] = {
                'total_words': total_words,
                'modules': total_modules,
                'avg_per_module': round(avg_per_module, 1)
            }

        return stats
