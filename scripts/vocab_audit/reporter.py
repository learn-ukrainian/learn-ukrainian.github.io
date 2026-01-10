"""
Vocabulary Reporter

Generates markdown reports for:
1. Duplicates across levels
2. Missing words (in plan but not in modules)
3. Extra words (in modules but not in plan)
4. Comprehensive audit report
"""

from typing import Dict, List, Tuple
from datetime import datetime


class VocabularyReporter:
    """Generate vocabulary audit reports."""

    @staticmethod
    def generate_duplicates_report(duplicates: Dict[str, List[Tuple[str, str]]]) -> str:
        """
        Generate markdown report for duplicate words.

        Args:
            duplicates: Dict mapping word to list of (level, module) locations

        Returns:
            Markdown report string
        """
        if not duplicates:
            return "# Vocabulary Duplicates Report\n\n✅ **No duplicates found across levels.**\n"

        report = []
        report.append("# Vocabulary Duplicates Report\n")
        report.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        report.append(f"**Total duplicates:** {len(duplicates)}\n")
        report.append("---\n")

        # Sort by number of occurrences (most duplicated first)
        sorted_duplicates = sorted(duplicates.items(), key=lambda x: len(x[1]), reverse=True)

        report.append("| Word | Occurrences | Locations |")
        report.append("|------|-------------|-----------|")

        for word, locations in sorted_duplicates:
            locations_str = ', '.join(sorted(locations))
            report.append(f"| {word} | {len(locations)} | {locations_str} |")

        return '\n'.join(report)

    @staticmethod
    def generate_missing_report(level: str, missing: Dict[str, List[str]]) -> str:
        """
        Generate markdown report for missing words.

        Args:
            level: CEFR level (e.g., 'A1')
            missing: Dict mapping module number to list of missing words

        Returns:
            Markdown report string
        """
        if not missing:
            return f"# {level} Missing Vocabulary Report\n\n✅ **All planned words are present in modules.**\n"

        report = []
        report.append(f"# {level} Missing Vocabulary Report\n")
        report.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        total_missing = sum(len(words) for words in missing.values())
        report.append(f"**Total missing:** {total_missing} words across {len(missing)} modules\n")
        report.append("---\n")

        # Sort by module number
        for module_num in sorted(missing.keys()):
            words = missing[module_num]
            report.append(f"## Module {module_num}\n")
            report.append(f"**Missing:** {len(words)} words\n")
            report.append(f"{', '.join(words)}\n")

        return '\n'.join(report)

    @staticmethod
    def generate_extra_report(level: str, extra: Dict[str, List[str]]) -> str:
        """
        Generate markdown report for extra words.

        Args:
            level: CEFR level (e.g., 'A1')
            extra: Dict mapping module number to list of extra words

        Returns:
            Markdown report string
        """
        if not extra:
            return f"# {level} Extra Vocabulary Report\n\n✅ **No extra words found. All words match the plan.**\n"

        report = []
        report.append(f"# {level} Extra Vocabulary Report\n")
        report.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        total_extra = sum(len(words) for words in extra.values())
        report.append(f"**Total extra:** {total_extra} words across {len(extra)} modules\n")
        report.append("---\n")

        # Sort by module number
        for module_num in sorted(extra.keys()):
            words = extra[module_num]
            report.append(f"## Module {module_num}\n")
            report.append(f"**Extra:** {len(words)} words\n")
            report.append(f"{', '.join(words)}\n")

        return '\n'.join(report)

    @staticmethod
    def generate_comprehensive_report(
        stats: Dict[str, Dict[str, int]],
        duplicates: Dict[str, List[Tuple[str, str]]],
        missing_by_level: Dict[str, Dict[str, List[str]]],
        extra_by_level: Dict[str, Dict[str, List[str]]]
    ) -> str:
        """
        Generate comprehensive vocabulary audit report.

        Args:
            stats: Vocabulary statistics by level
            duplicates: Duplicate words across levels
            missing_by_level: Missing words by level
            extra_by_level: Extra words by level

        Returns:
            Markdown report string
        """
        report = []
        report.append("# Vocabulary Audit Report\n")
        report.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        report.append("---\n")

        # 1. Statistics Summary
        report.append("## 📊 Vocabulary Statistics\n")
        report.append("| Level | Total Words | Modules | Avg per Module |")
        report.append("|-------|-------------|---------|----------------|")

        cumulative = 0
        for level, level_stats in stats.items():
            cumulative += level_stats['total_words']
            report.append(
                f"| {level.upper()} | {level_stats['total_words']} | {level_stats['modules']} | {level_stats['avg_per_module']} |"
            )

        report.append(f"\n**Cumulative vocabulary:** {cumulative} words\n")
        report.append("---\n")

        # 2. Duplicates Summary
        report.append("## 🔄 Duplicate Words Across Levels\n")
        if duplicates:
            report.append(f"**Total duplicates:** {len(duplicates)}\n")
            report.append("\nTop 10 most duplicated:\n")
            sorted_dups = sorted(duplicates.items(), key=lambda x: len(x[1]), reverse=True)[:10]
            for word, locations in sorted_dups:
                locs_str = ', '.join(sorted(set(loc.split()[0] for loc in locations)))
                report.append(f"- **{word}** ({len(locations)} occurrences) - {locs_str}")
        else:
            report.append("✅ **No duplicates found.**\n")

        report.append("\n---\n")

        # 3. Missing Words Summary
        report.append("## ⚠️ Missing Words (Planned but Not in Modules)\n")
        total_missing = sum(
            sum(len(words) for words in level_missing.values())
            for level_missing in missing_by_level.values()
        )

        if total_missing > 0:
            report.append(f"**Total missing:** {total_missing} words\n")
            for level, level_missing in missing_by_level.items():
                if level_missing:
                    count = sum(len(words) for words in level_missing.values())
                    report.append(f"- **{level.upper()}:** {count} words across {len(level_missing)} modules")
        else:
            report.append("✅ **All planned words are present.**\n")

        report.append("\n---\n")

        # 4. Extra Words Summary
        report.append("## ➕ Extra Words (In Modules but Not Planned)\n")
        total_extra = sum(
            sum(len(words) for words in level_extra.values())
            for level_extra in extra_by_level.values()
        )

        if total_extra > 0:
            report.append(f"**Total extra:** {total_extra} words\n")
            for level, level_extra in extra_by_level.items():
                if level_extra:
                    count = sum(len(words) for words in level_extra.values())
                    report.append(f"- **{level.upper()}:** {count} words across {len(level_extra)} modules")
        else:
            report.append("✅ **No extra words found.**\n")

        report.append("\n---\n")

        # 5. Recommendations
        report.append("## 💡 Recommendations\n")

        if duplicates:
            report.append("1. **Review duplicates** - Verify intentional re-teaching or remove redundancy\n")

        if total_missing > 0:
            report.append("2. **Add missing words** - Update module vocabulary YAML files with planned words\n")

        if total_extra > 0:
            report.append("3. **Review extra words** - Update curriculum plan or remove from modules\n")

        if not duplicates and total_missing == 0 and total_extra == 0:
            report.append("✅ **Vocabulary is perfectly aligned across plan and modules. No action needed.**\n")

        return '\n'.join(report)
