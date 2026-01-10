#!/usr/bin/env python3
"""
Vocabulary Deduplication Audit CLI

Audits curriculum vocabulary for duplicates, missing words, and extra words.

Usage:
    python scripts/vocab_audit/main.py --level a1 --report missing
    python scripts/vocab_audit/main.py --level a1 --report extra
    python scripts/vocab_audit/main.py --all --report duplicates
    python scripts/vocab_audit/main.py --all --output reports/vocab_audit.md
"""

import argparse
from pathlib import Path
from typing import List

from .parser import VocabularyParser
from .analyzer import VocabularyAnalyzer
from .reporter import VocabularyReporter


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Audit curriculum vocabulary for duplicates, missing, and extra words'
    )

    parser.add_argument(
        '--level',
        type=str,
        choices=['a1', 'a2', 'b1', 'b2', 'c1', 'c2'],
        help='CEFR level to audit'
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Audit all levels (a1, a2, b1, b2, c1, c2)'
    )

    parser.add_argument(
        '--report',
        type=str,
        choices=['duplicates', 'missing', 'extra', 'comprehensive'],
        default='comprehensive',
        help='Type of report to generate (default: comprehensive)'
    )

    parser.add_argument(
        '--output',
        type=str,
        help='Output file path (default: print to stdout)'
    )

    parser.add_argument(
        '--curriculum-root',
        type=str,
        default='curriculum/l2-uk-en',
        help='Path to curriculum root directory'
    )

    args = parser.parse_args()

    # Determine which levels to audit
    if args.all:
        levels = ['a1', 'a2', 'b1', 'b2', 'c1', 'c2']
    elif args.level:
        levels = [args.level]
    else:
        parser.error('Must specify either --level or --all')

    # Initialize components
    vocab_parser = VocabularyParser(Path(args.curriculum_root))
    analyzer = VocabularyAnalyzer()
    reporter = VocabularyReporter()

    # Generate reports
    if args.report == 'duplicates':
        report = generate_duplicates_report(levels, vocab_parser, analyzer, reporter)

    elif args.report == 'missing':
        if not args.level:
            parser.error('--report missing requires --level (cannot use --all)')
        report = generate_missing_report(args.level, vocab_parser, analyzer, reporter)

    elif args.report == 'extra':
        if not args.level:
            parser.error('--report extra requires --level (cannot use --all)')
        report = generate_extra_report(args.level, vocab_parser, analyzer, reporter)

    elif args.report == 'comprehensive':
        report = generate_comprehensive_report(levels, vocab_parser, analyzer, reporter)

    # Output report
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"✅ Report written to {output_path}")
    else:
        print(report)


def generate_duplicates_report(levels: List[str], vocab_parser, analyzer, reporter) -> str:
    """Generate duplicates report."""
    word_index = analyzer.build_word_index(levels, vocab_parser)
    duplicates = analyzer.find_duplicates(levels, word_index)
    return reporter.generate_duplicates_report(duplicates)


def generate_missing_report(level: str, vocab_parser, analyzer, reporter) -> str:
    """Generate missing words report for a single level."""
    plan_vocab = vocab_parser.parse_plan_vocabulary(level)

    if not plan_vocab:
        return f"# {level.upper()} Missing Vocabulary Report\n\nℹ️ **Level {level.upper()} has no prescribed vocabulary plan (content-driven approach).**\n"

    module_vocab = vocab_parser.parse_module_vocabulary(level)
    missing = analyzer.find_missing_words(plan_vocab, module_vocab)
    return reporter.generate_missing_report(level.upper(), missing)


def generate_extra_report(level: str, vocab_parser, analyzer, reporter) -> str:
    """Generate extra words report for a single level."""
    plan_vocab = vocab_parser.parse_plan_vocabulary(level)

    if not plan_vocab:
        return f"# {level.upper()} Extra Vocabulary Report\n\nℹ️ **Level {level.upper()} has no prescribed vocabulary plan (content-driven approach).**\n"

    module_vocab = vocab_parser.parse_module_vocabulary(level)
    extra = analyzer.find_extra_words(plan_vocab, module_vocab)
    return reporter.generate_extra_report(level.upper(), extra)


def generate_comprehensive_report(levels: List[str], vocab_parser, analyzer, reporter) -> str:
    """Generate comprehensive audit report."""
    # Get statistics
    stats = analyzer.get_vocabulary_stats(levels, vocab_parser)

    # Find duplicates
    word_index = analyzer.build_word_index(levels, vocab_parser)
    duplicates = analyzer.find_duplicates(levels, word_index)

    # Find missing and extra words for levels with prescribed vocabulary
    missing_by_level = {}
    extra_by_level = {}

    for level in levels:
        plan_vocab = vocab_parser.parse_plan_vocabulary(level)

        if plan_vocab:  # Only for levels with prescribed vocabulary
            module_vocab = vocab_parser.parse_module_vocabulary(level)
            missing = analyzer.find_missing_words(plan_vocab, module_vocab)
            extra = analyzer.find_extra_words(plan_vocab, module_vocab)

            if missing:
                missing_by_level[level] = missing
            if extra:
                extra_by_level[level] = extra

    return reporter.generate_comprehensive_report(stats, duplicates, missing_by_level, extra_by_level)


if __name__ == '__main__':
    main()
