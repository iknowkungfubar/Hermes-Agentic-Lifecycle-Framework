#!/usr/bin/env python3
"""Coverage-aware subprocess runner — wraps every Python child process with coverage measurement."""
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
COVERAGERC = HERE / ".coveragerc"

def coverage_run(args, **kwargs):
    """Run a Python command with coverage measurement enabled in the child process."""
    coverage_args = [sys.executable, "-m", "coverage", "run", f"--rcfile={COVERAGERC}", 
                     "--source=src/half", "--parallel-mode"] + args
    env = {**os.environ, "COVERAGE_PROCESS_START": str(COVERAGERC)}
    return subprocess.run(coverage_args, env=env, **kwargs)

def run_half_command(cmd_args, **kwargs):
    """Run a half CLI command with coverage."""
    return coverage_run(["-m", "half.half_sidecar"] + cmd_args, **kwargs)

def run_pytest(path, **kwargs):
    """Run pytest with coverage."""
    return coverage_run(["-m", "pytest", path, "-q", "--tb=no"], **kwargs)

if __name__ == "__main__":
    # Test that the wrapper works
    r = run_half_command(["status"], capture_output=True, text=True, timeout=10)
    print(f"half status: exit={r.returncode}, output={r.stdout[:100]}")
    
    r = run_half_command(["--version"], capture_output=True, text=True, timeout=10)
    print(f"half --version: exit={r.returncode}, output={r.stdout[:100]}")
    
    # Run the full test suite with coverage
    print("\nRunning full test suite with subprocess coverage...")
    r = run_pytest("tests/", timeout=300)
    print(f"pytest: exit={r.returncode}")
    
    # Combine all coverage data
    subprocess.run([sys.executable, "-m", "coverage", "combine"], cwd=HERE)
    subprocess.run([sys.executable, "-m", "coverage", "report", "--include=src/half/*"], cwd=HERE)
