
import sys
import os
import glob
import subprocess
from pathlib import Path

def run_command(command, cwd=None):
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            shell=True,
            capture_output=True,
            text=True
        )
        return result
    except Exception as e:
        return None

def main():
    lit_dir = Path("curriculum/l2-uk-en/lit")
    results = []
    
    print(f"Starting Stage 4 Batch Audit for LIT 01-30...")
    print("-" * 60)
    print(f"{'Module':<30} | {'Status':<10} | {'Notes'}")
    print("-" * 60)
    
    for i in range(1, 31):
        pattern = f"{i:02d}-*.md"
        files = list(lit_dir.glob(pattern))
        
        if not files:
            results.append((f"M{i:02d}", "MISSING", "File not found"))
            print(f"M{i:02d} {'MISSING':<30} | File not found")
            continue
            
        file_path = files[0]
        module_name = file_path.name
        
        # Run audit
        cmd = f".venv/bin/python scripts/audit_module.py {file_path}"
        result = run_command(cmd)
        
        status = "FAIL"
        notes = []
        
        if result and result.returncode == 0:
            status = "PASS"
        else:
            # Analyze failure
            output = result.stdout + result.stderr if result else ""
            if "MISSING LLM SELF-VALIDATION" in output:
                notes.append("Missing Review")
            if "STALE LLM REVIEW" in output:
                notes.append("Stale Review")
            if "Words" in output and "❌" in output:
                notes.append("Word Count")
            if "Richness" in output and "❌" in output:
                notes.append("Richness")
            if "Naturalness" in output and "❌" in output:
                notes.append("Naturalness")
            if "YAML schema violations" in output:
                notes.append("Schema")
            if not notes:
                notes.append("Audit Failed")
                
        note_str = ", ".join(notes)
        print(f"{module_name:<30} | {status:<10} | {note_str}")
        results.append((module_name, status, note_str))

    print("-" * 60)
    
    # Summary
    passed = sum(1 for r in results if r[1] == "PASS")
    failed = sum(1 for r in results if r[1] == "FAIL")
    print(f"\nSummary: {passed} PASSED, {failed} FAILED")

if __name__ == "__main__":
    main()
