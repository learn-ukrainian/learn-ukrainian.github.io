import cProfile
import pstats
import sys
import subprocess
import time

def profile_command(command):
    print(f"Profiling command: {' '.join(command)}")
    start_time = time.time()

    profiler = cProfile.Profile()
    profiler.enable()

    try:
        # We use subprocess to run the command to simulate real-world usage
        # but this won't profile the subprocess itself with cProfile.
        # To profile the code, we should ideally import the main and call it.
        result = subprocess.run(command, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
    finally:
        profiler.disable()
        end_time = time.time()

    stats = pstats.Stats(profiler).sort_stats('cumulative')
    stats.print_stats(20)
    print(f"Total Wall Clock Time: {end_time - start_time:.2f}s")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/utils/profiler.py <command> [args...]")
        sys.exit(1)
    profile_command(sys.argv[1:])
