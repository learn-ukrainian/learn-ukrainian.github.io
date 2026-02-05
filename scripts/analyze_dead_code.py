#!/usr/bin/env python3
"""
Dead Code Analyzer - Identifies safe-to-remove scripts

Analyzes:
1. Import dependencies (who imports this script?)
2. External references (mentioned in docs, package.json, etc.)
3. Last modification date
4. Naming patterns (test_, debug_, fix_, etc.)

Output: JSON report with removal candidates categorized by risk level
"""

import subprocess
import json
from pathlib import Path
from datetime import datetime
import re
import ast
import sys

class DeadCodeAnalyzer:
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.scripts_dir = self.project_root / 'scripts'
        self.results = {}

    def get_all_python_scripts(self):
        """Get all .py files in scripts/ directory"""
        scripts = []
        for script in self.scripts_dir.rglob('*.py'):
            if '__pycache__' not in str(script):
                scripts.append(script)
        return sorted(scripts)

    def get_last_modified(self, script_path):
        """Get last git modification date"""
        try:
            result = subprocess.run(
                ['git', 'log', '-1', '--format=%ci', '--', str(script_path)],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            if result.stdout.strip():
                date_str = result.stdout.strip().split()[0]
                return datetime.strptime(date_str, '%Y-%m-%d')
            return None
        except Exception as e:
            return None

    def count_external_references(self, script_name):
        """Count references in docs, configs, and other non-script files"""
        name_no_ext = script_name.replace('.py', '')

        try:
            # Search in markdown, JSON, YAML, shell scripts
            result = subprocess.run(
                ['rg', '-l', name_no_ext,
                 '--type', 'md', '--type', 'json', '--type', 'yaml', '--type', 'sh',
                 '--glob', '!scripts/**'],  # Exclude scripts directory
                capture_output=True,
                text=True,
                cwd=self.project_root
            )

            files = [f for f in result.stdout.strip().split('\n') if f]
            return len(files), files
        except Exception as e:
            return 0, []

    def find_python_imports(self, script_name):
        """Find which Python files import this script"""
        name_no_ext = script_name.replace('.py', '')

        try:
            # Search for import statements
            result = subprocess.run(
                ['rg', '-l', f'(from|import).*{name_no_ext}',
                 '--type', 'py',
                 '--glob', '!scripts/{}'.format(script_name)],  # Exclude the script itself
                capture_output=True,
                text=True,
                cwd=self.project_root
            )

            files = [f for f in result.stdout.strip().split('\n') if f]
            return len(files), files
        except Exception as e:
            return 0, []

    def categorize_by_pattern(self, script_name):
        """Categorize script by naming pattern"""
        patterns = {
            'test': r'^test_',
            'debug': r'^debug_',
            'temp': r'^(temp_|tmp_)',
            'one_time_fix': r'^fix_',
            'one_time_add': r'^add_',
            'one_time_clean': r'^clean_',
            'one_time_convert': r'^convert_',
            'one_time_migrate': r'^migrate_',
            'batch': r'^batch_',
            'apply': r'^apply_',
            'utility': r'.*',  # Default catch-all
        }

        for category, pattern in patterns.items():
            if re.match(pattern, script_name):
                return category
        return 'utility'

    def assess_risk_level(self, analysis):
        """Assess risk level for removing this script"""
        # HIGH RISK: Has external references or imports
        if analysis['external_refs_count'] > 0 or analysis['import_count'] > 0:
            return 'HIGH'

        # LOW RISK: Test/debug/temp scripts with no refs
        if analysis['category'] in ['test', 'debug', 'temp']:
            return 'LOW'

        # LOW RISK: One-time scripts for completed work, not modified recently
        if analysis['category'].startswith('one_time_'):
            days_since_modified = analysis['days_since_modified'] if analysis['days_since_modified'] is not None else 999
            if days_since_modified > 60:  # Not modified in 2 months
                return 'LOW'
            return 'MEDIUM'

        # MEDIUM RISK: Batch scripts (might be used occasionally)
        if analysis['category'] in ['batch', 'apply']:
            return 'MEDIUM'

        # MEDIUM RISK: Utilities with no references
        return 'MEDIUM'

    def analyze_script(self, script_path):
        """Analyze a single script"""
        script_name = script_path.name
        relative_path = script_path.relative_to(self.project_root)

        # Gather data
        last_modified = self.get_last_modified(script_path)
        external_refs_count, external_refs = self.count_external_references(script_name)
        import_count, importers = self.find_python_imports(script_name)
        category = self.categorize_by_pattern(script_name)

        days_since_modified = (datetime.now() - last_modified).days if last_modified else None

        analysis = {
            'name': script_name,
            'path': str(relative_path),
            'last_modified': last_modified.isoformat() if last_modified else None,
            'days_since_modified': days_since_modified,
            'external_refs_count': external_refs_count,
            'external_refs': external_refs,
            'import_count': import_count,
            'importers': importers,
            'category': category,
            '_last_modified_obj': last_modified,  # Keep for assessment
        }

        analysis['risk_level'] = self.assess_risk_level(analysis)

        return analysis

    def analyze_all(self):
        """Analyze all scripts"""
        scripts = self.get_all_python_scripts()

        print(f"Analyzing {len(scripts)} Python scripts...")
        print("=" * 70)

        for i, script in enumerate(scripts, 1):
            if i % 20 == 0:
                print(f"Progress: {i}/{len(scripts)}...")

            analysis = self.analyze_script(script)
            self.results[script.name] = analysis

        return self.results

    def generate_report(self):
        """Generate removal candidates report"""
        low_risk = []
        medium_risk = []
        high_risk = []

        for name, analysis in self.results.items():
            # Remove non-serializable fields
            if '_last_modified_obj' in analysis:
                del analysis['_last_modified_obj']

            if analysis['risk_level'] == 'LOW':
                low_risk.append(analysis)
            elif analysis['risk_level'] == 'MEDIUM':
                medium_risk.append(analysis)
            else:
                high_risk.append(analysis)

        report = {
            'summary': {
                'total_scripts': len(self.results),
                'low_risk': len(low_risk),
                'medium_risk': len(medium_risk),
                'high_risk': len(high_risk),
                'generated_at': datetime.now().isoformat()
            },
            'low_risk_candidates': sorted(low_risk, key=lambda x: x['days_since_modified'] or 0, reverse=True),
            'medium_risk_candidates': sorted(medium_risk, key=lambda x: x['days_since_modified'] or 0, reverse=True),
            'high_risk_keep': sorted(high_risk, key=lambda x: x['external_refs_count'], reverse=True)
        }

        return report

    def print_summary(self, report):
        """Print human-readable summary"""
        print("\n" + "=" * 70)
        print("DEAD CODE ANALYSIS REPORT")
        print("=" * 70)
        print(f"\nTotal scripts analyzed: {report['summary']['total_scripts']}")
        print(f"Low risk (safe to remove): {report['summary']['low_risk']}")
        print(f"Medium risk (review needed): {report['summary']['medium_risk']}")
        print(f"High risk (keep): {report['summary']['high_risk']}")

        print("\n" + "=" * 70)
        print("LOW RISK CANDIDATES (Safe to Remove)")
        print("=" * 70)

        for script in report['low_risk_candidates'][:20]:  # Top 20
            days = script['days_since_modified'] or 0
            print(f"\n{script['name']}")
            print(f"  Category: {script['category']}")
            print(f"  Last modified: {days} days ago")
            print(f"  References: {script['external_refs_count']} external, {script['import_count']} imports")

        if len(report['low_risk_candidates']) > 20:
            print(f"\n... and {len(report['low_risk_candidates']) - 20} more")

        print("\n" + "=" * 70)
        print("MEDIUM RISK (Review Before Removing)")
        print("=" * 70)

        for script in report['medium_risk_candidates'][:10]:  # Top 10
            days = script['days_since_modified'] or 0
            print(f"\n{script['name']}")
            print(f"  Category: {script['category']}")
            print(f"  Last modified: {days} days ago")

        print("\n" + "=" * 70)
        print("Report saved to: /tmp/dead_code_report.json")
        print("=" * 70)

def main():
    project_root = Path(__file__).parent.parent

    analyzer = DeadCodeAnalyzer(project_root)
    analyzer.analyze_all()
    report = analyzer.generate_report()

    # Save full report
    output_path = '/tmp/dead_code_report.json'
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    # Print summary
    analyzer.print_summary(report)

    print(f"\nTo remove low-risk scripts, run:")
    print(f"  python3 scripts/remove_dead_code.py --low-risk")

if __name__ == '__main__':
    main()
