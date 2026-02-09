#!/usr/bin/env python3
"""
Batch Manager CLI - Unified interface for batch operations

Usage:
    # Fix + Review batches
    .venv/bin/python scripts/batch_manager.py fix-review a1 1 44
    .venv/bin/python scripts/batch_manager.py fix-review b2-hist 1 20 --model gemini-3-pro-preview

    # Research batches
    .venv/bin/python scripts/batch_manager.py research b1 1 92
    .venv/bin/python scripts/batch_manager.py research c1-bio 1 128

    # Orchestrated rebuilds
    .venv/bin/python scripts/batch_manager.py orchestrate a1 1 10

    # List active tasks
    .venv/bin/python scripts/batch_manager.py list

    # View task details
    .venv/bin/python scripts/batch_manager.py show <task-id>

    # Stop running task
    .venv/bin/python scripts/batch_manager.py stop <task-id>
"""

import sys
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
import json

# Add project root to sys.path for internal imports
sys.path.append(str(Path(__file__).parent.parent))

from scripts.utils.logging_utils import setup_logging
from scripts.utils.monitoring import MetricsManager

# Initialize logging and monitoring
logger = setup_logging("batch_manager")
metrics = MetricsManager()

REPO = Path(__file__).parent.parent

# Task tracking directory
TASKS_DIR = REPO / "tasks"
TASKS_DIR.mkdir(exist_ok=True)

# Available tracks
TRACKS = {
    'core': ['a1', 'a2', 'b1', 'b2', 'c1', 'c2', 'b2-pro', 'c1-pro'],
    'seminar': ['b2-hist', 'c1-bio', 'c1-hist', 'lit', 'oes', 'ruth']
}

# Module counts
MODULE_COUNTS = {
    'a1': 44, 'a2': 70, 'b1': 92, 'b2': 94, 'c1': 106, 'c2': 100,
    'b2-hist': 140, 'c1-bio': 128, 'c1-hist': 60, 'lit': 30,
    'b2-pro': 30, 'c1-pro': 30, 'oes': 40, 'ruth': 40
}


def validate_track(track: str) -> bool:
    """Validate track name."""
    all_tracks = TRACKS['core'] + TRACKS['seminar']
    if track not in all_tracks:
        print(f"❌ Invalid track: {track}")
        print(f"   Available: {', '.join(all_tracks)}")
        return False
    return True


def validate_range(track: str, start: int, end: int) -> bool:
    """Validate module range for track."""
    max_count = MODULE_COUNTS.get(track, 100)
    if start < 1 or end < start or end > max_count:
        print(f"❌ Invalid range: M{start}-M{end} for {track} (max: {max_count})")
        return False
    return True


def generate_task_id(operation: str, track: str, start: int, end: int) -> str:
    """Generate unique task ID."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{operation}-{track}-{start}-{end}-{timestamp}"


def save_task_metadata(task_id: str, metadata: dict):
    """Save task metadata to JSON."""
    task_file = TASKS_DIR / f"{task_id}.json"
    task_file.write_text(json.dumps(metadata, indent=2))
    print(f"📝 Task metadata saved: {task_file}")


def cmd_fix_review(args):
    """Launch fix + review batch."""
    if not validate_track(args.track):
        return 1
    if not validate_range(args.track, args.start, args.end):
        return 1

    task_id = generate_task_id('fix-review', args.track, args.start, args.end)
    output_file = TASKS_DIR / f"{task_id}.output"

    metadata = {
        'task_id': task_id,
        'operation': 'fix-review',
        'track': args.track,
        'start': args.start,
        'end': args.end,
        'model': args.model,
        'created_at': datetime.now().isoformat(),
        'status': 'running',
        'output_file': str(output_file)
    }
    save_task_metadata(task_id, metadata)

    print(f"🚀 Launching fix-review batch: {args.track} M{args.start}-M{args.end}")
    print(f"   Model: {args.model}")
    print(f"   Task ID: {task_id}")
    print(f"   Output: {output_file}")

    cmd = [
        sys.executable,
        str(REPO / "scripts/batch_fix_review.py"),
        args.track,
        str(args.start),
        str(args.end),
        "--model", args.model
    ]

    if args.background:
        print(f"   Running in background...")
        with open(output_file, 'w') as f:
            proc = subprocess.Popen(
                cmd,
                stdout=f,
                stderr=subprocess.STDOUT,
                cwd=str(REPO)
            )
        print(f"   PID: {proc.pid}")
        print(f"\n   Monitor progress: tail -f {output_file}")
        print(f"   View results: .venv/bin/python scripts/batch_manager.py show {task_id}")
    else:
        # Run in foreground
        result = subprocess.run(cmd, cwd=str(REPO))
        return result.returncode

    return 0


def cmd_research(args):
    """Launch research batch."""
    if not validate_track(args.track):
        return 1
    if not validate_range(args.track, args.start, args.end):
        return 1

    # Research only valid for certain tracks
    if args.track in TRACKS['core'] and args.track not in ['b1', 'b2', 'c1', 'c2']:
        print(f"⚠️  Warning: Research for {args.track} uses lightweight template")

    task_id = generate_task_id('research', args.track, args.start, args.end)
    output_file = TASKS_DIR / f"{task_id}.output"

    metadata = {
        'task_id': task_id,
        'operation': 'research',
        'track': args.track,
        'start': args.start,
        'end': args.end,
        'created_at': datetime.now().isoformat(),
        'status': 'running',
        'output_file': str(output_file)
    }
    save_task_metadata(task_id, metadata)

    print(f"🚀 Launching research batch: {args.track} M{args.start}-M{args.end}")
    print(f"   Task ID: {task_id}")
    print(f"   Output: {output_file}")

    cmd = [
        sys.executable,
        str(REPO / "scripts/batch_research.py"),
        args.track,
        str(args.start),
        str(args.end)
    ]

    if args.background:
        print(f"   Running in background...")
        with open(output_file, 'w') as f:
            proc = subprocess.Popen(
                cmd,
                stdout=f,
                stderr=subprocess.STDOUT,
                cwd=str(REPO)
            )
        print(f"   PID: {proc.pid}")
        print(f"\n   Monitor progress: tail -f {output_file}")
    else:
        result = subprocess.run(cmd, cwd=str(REPO))
        return result.returncode

    return 0


def cmd_orchestrate(args):
    """Launch orchestrated rebuild (sequential, not batch)."""
    if not validate_track(args.track):
        return 1
    if not validate_range(args.track, args.start, args.end):
        return 1

    print(f"📋 Orchestrated rebuild: {args.track} M{args.start}-M{args.end}")
    print(f"   This will run /orchestrate-rebuild for each module sequentially")
    print(f"   For parallel execution, use multiple terminal sessions")
    print()

    for num in range(args.start, args.end + 1):
        print(f"\n{'='*60}")
        print(f"Module {num}/{args.end}")
        print(f"{'='*60}")

        # This would invoke the orchestrate-rebuild skill
        # For now, just print the command
        print(f"Command: /orchestrate-rebuild {args.track} {num}")
        print(f"\nTo run this, open Claude Code and execute:")
        print(f"  /orchestrate-rebuild {args.track} {num}")
        print()

        response = input("Continue to next module? [Y/n] ")
        if response.lower() == 'n':
            break

    return 0


def cmd_list(args):
    """List active tasks."""
    task_files = sorted(TASKS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)

    if not task_files:
        print("No tasks found.")
        return 0

    print(f"\n{'='*80}")
    print(f"Active Tasks ({len(task_files)} total)")
    print(f"{'='*80}\n")

    for task_file in task_files[:20]:  # Show last 20
        try:
            metadata = json.loads(task_file.read_text())
            task_id = metadata['task_id']
            operation = metadata['operation']
            track = metadata['track']
            start = metadata['start']
            end = metadata['end']
            status = metadata.get('status', 'unknown')
            created = metadata.get('created_at', 'N/A')

            print(f"📌 {task_id}")
            print(f"   {operation} · {track} M{start}-M{end} · {status}")
            print(f"   Created: {created}")
            print()
        except Exception as e:
            print(f"⚠️  Failed to read {task_file.name}: {e}")

    return 0


def cmd_show(args):
    """Show task details."""
    task_file = TASKS_DIR / f"{args.task_id}.json"
    output_file = TASKS_DIR / f"{args.task_id}.output"

    if not task_file.exists():
        print(f"❌ Task not found: {args.task_id}")
        return 1

    metadata = json.loads(task_file.read_text())

    print(f"\n{'='*80}")
    print(f"Task: {metadata['task_id']}")
    print(f"{'='*80}\n")
    print(f"Operation:  {metadata['operation']}")
    print(f"Track:      {metadata['track']}")
    print(f"Range:      M{metadata['start']}-M{metadata['end']}")
    print(f"Status:     {metadata.get('status', 'unknown')}")
    print(f"Created:    {metadata.get('created_at', 'N/A')}")

    if 'model' in metadata:
        print(f"Model:      {metadata['model']}")

    if output_file.exists():
        print(f"\nOutput file: {output_file}")
        print(f"Size: {output_file.stat().st_size} bytes")

        print("\nLast 30 lines:")
        print("-" * 80)
        result = subprocess.run(['tail', '-30', str(output_file)], capture_output=True, text=True)
        print(result.stdout)
    else:
        print(f"\n⚠️  Output file not found: {output_file}")

    return 0


def cmd_stop(args):
    """Stop running task."""
    task_file = TASKS_DIR / f"{args.task_id}.json"

    if not task_file.exists():
        print(f"❌ Task not found: {args.task_id}")
        return 1

    metadata = json.loads(task_file.read_text())

    # Update status
    metadata['status'] = 'stopped'
    metadata['stopped_at'] = datetime.now().isoformat()
    task_file.write_text(json.dumps(metadata, indent=2))

    print(f"✋ Task marked as stopped: {args.task_id}")
    print(f"   Note: Background process may still be running")
    print(f"   Use 'ps aux | grep batch' to find PIDs and 'kill <pid>' to terminate")

    return 0


def main():
    # Setup logging again at main entry
    global logger
    logger = setup_logging("batch_manager")

    parser = argparse.ArgumentParser(
        description="Batch Manager - Unified CLI for batch operations",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--json-log", action="store_true", help="Enable structured JSON logging")

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # fix-review command
    fix_parser = subparsers.add_parser('fix-review', help='Launch fix + review batch')
    fix_parser.add_argument('track', help='Track name (a1, b2-hist, etc.)')
    fix_parser.add_argument('start', type=int, help='Start module number')
    fix_parser.add_argument('end', type=int, help='End module number')
    fix_parser.add_argument('--model', default='gemini-3-pro-preview',
                           choices=['gemini-3-pro-preview', 'gemini-3-flash-preview'],
                           help='Model for review (default: gemini-3-pro-preview)')
    fix_parser.add_argument('-b', '--background', action='store_true',
                           help='Run in background')

    # research command
    research_parser = subparsers.add_parser('research', help='Launch research batch')
    research_parser.add_argument('track', help='Track name (a1, b2-hist, etc.)')
    research_parser.add_argument('start', type=int, help='Start module number')
    research_parser.add_argument('end', type=int, help='End module number')
    research_parser.add_argument('-b', '--background', action='store_true',
                                help='Run in background')

    # orchestrate command
    orch_parser = subparsers.add_parser('orchestrate', help='Launch orchestrated rebuilds')
    orch_parser.add_argument('track', help='Track name (a1, b2-hist, etc.)')
    orch_parser.add_argument('start', type=int, help='Start module number')
    orch_parser.add_argument('end', type=int, help='End module number')

    # list command
    subparsers.add_parser('list', help='List active tasks')

    # show command
    show_parser = subparsers.add_parser('show', help='Show task details')
    show_parser.add_argument('task_id', help='Task ID')

    # stop command
    stop_parser = subparsers.add_parser('stop', help='Stop running task')
    stop_parser.add_argument('task_id', help='Task ID')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Route to command handler
    handlers = {
        'fix-review': cmd_fix_review,
        'research': cmd_research,
        'orchestrate': cmd_orchestrate,
        'list': cmd_list,
        'show': cmd_show,
        'stop': cmd_stop
    }

    handler = handlers.get(args.command)
    if handler:
        return handler(args)
    else:
        print(f"❌ Unknown command: {args.command}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
