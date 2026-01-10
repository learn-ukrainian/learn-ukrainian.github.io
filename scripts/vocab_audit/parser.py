"""
Vocabulary Parser

Parses vocabulary from:
1. Module YAML files (curriculum/l2-uk-en/{level}/vocabulary/*.yaml)
2. Curriculum plan markdown files (docs/l2-uk-en/{LEVEL}-CURRICULUM-PLAN.md)
"""

import re
import yaml
from pathlib import Path
from typing import List, Dict, Tuple


class VocabularyParser:
    """Parse vocabulary from curriculum files."""

    def __init__(self, curriculum_root: Path):
        """
        Initialize parser.

        Args:
            curriculum_root: Path to curriculum root (e.g., curriculum/l2-uk-en)
        """
        self.curriculum_root = Path(curriculum_root)
        self.docs_root = Path('docs/l2-uk-en')

    def parse_module_vocabulary(self, level: str) -> Dict[str, List[str]]:
        """
        Parse vocabulary from module YAML files.

        Args:
            level: CEFR level (a1, a2, b1, b2, c1, c2)

        Returns:
            Dictionary mapping module number to list of vocabulary words
            Example: {'01': ['слово', 'мова', ...], '02': [...]}
        """
        vocab_dir = self.curriculum_root / level / 'vocabulary'
        if not vocab_dir.exists():
            return {}

        module_vocab = {}

        for yaml_file in sorted(vocab_dir.glob('*.yaml')):
            # Extract module number from filename (e.g., '01' from '01-module-name.yaml')
            module_num = yaml_file.stem[:2]

            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)

                words = []
                if data and 'items' in data:
                    for item in data['items']:
                        if 'lemma' in item:
                            words.append(item['lemma'])

                module_vocab[module_num] = words

            except Exception as e:
                print(f"⚠️ Error parsing {yaml_file}: {e}")
                continue

        return module_vocab

    def parse_plan_vocabulary(self, level: str) -> Dict[str, List[str]]:
        """
        Parse vocabulary from curriculum plan markdown files.

        Args:
            level: CEFR level (a1, a2, b1, b2, c1, c2)

        Returns:
            Dictionary mapping module number to list of planned vocabulary words
            Example: {'01': ['слово', 'мова', ...], '02': [...]}
            Returns empty dict for levels without prescribed vocabulary (B1+)
        """
        plan_file = self.docs_root / f'{level.upper()}-CURRICULUM-PLAN.md'

        if not plan_file.exists():
            return {}

        with open(plan_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if this level has prescribed vocabulary
        if re.search(r'vocabulary is not prescribed', content, re.IGNORECASE):
            return {}  # B1+ levels don't have prescribed vocabulary

        module_vocab = {}
        current_module = None

        # Parse module by module
        # Pattern: ### Module XX: Title
        # followed by: **Vocabulary (NN words):**
        # followed by: word1, word2, word3, ...

        lines = content.split('\n')
        for i, line in enumerate(lines):
            # Match module header: #### Module 01: Title
            module_match = re.match(r'####\s+Module\s+(\d+):', line, re.IGNORECASE)
            if module_match:
                current_module = module_match.group(1).zfill(2)  # Zero-pad to 2 digits
                continue

            # Match vocabulary line: **Vocabulary (35 words):**
            vocab_match = re.match(r'\*\*Vocabulary\s+\((\d+)\s+words?\):\*\*', line, re.IGNORECASE)
            if vocab_match and current_module:
                # Next line should contain comma-separated words
                if i + 1 < len(lines):
                    words_line = lines[i + 1].strip()
                    # Split by comma and clean up spaces
                    words = [w.strip() for w in words_line.split(',') if w.strip()]
                    module_vocab[current_module] = words

        return module_vocab

    def get_all_words_by_level(self, level: str) -> Tuple[List[str], List[Tuple[str, str]]]:
        """
        Get all vocabulary words for a level with their module locations.

        Args:
            level: CEFR level (a1, a2, b1, b2, c1, c2)

        Returns:
            Tuple of:
            - List of unique words
            - List of (word, module) tuples for location tracking
        """
        module_vocab = self.parse_module_vocabulary(level)

        all_words = []
        word_locations = []

        for module_num, words in module_vocab.items():
            for word in words:
                word_locations.append((word, f"{level.upper()} M{module_num}"))
                all_words.append(word)

        return list(set(all_words)), word_locations
