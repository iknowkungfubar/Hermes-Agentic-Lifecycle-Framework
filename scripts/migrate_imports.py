#!/usr/bin/env python3
"""Migrate src/ to half/ namespace: move sub-packages and fix all imports."""

import os
import shutil
import subprocess
from pathlib import Path

REPO = Path("/home/turin/Hermes-Agentic-Lifecycle-Framework")
SRC = REPO / "src"
HALF = SRC / "half"

# Directories to move under half/
DIRS_TO_MOVE = [
    "core",
    "agents",
    "runtime",
    "state",
    "agent_mail",
    "half_voice",
    "half_focalboard",
]

# File to move
FILES_TO_MOVE = ["half_sidecar.py"]

print("=== Moving sub-packages under src/half/ ===")

for d in DIRS_TO_MOVE:
    src_dir = SRC / d
    dst_dir = HALF / d
    if src_dir.exists() and not dst_dir.exists():
        shutil.copytree(src_dir, dst_dir)
        print(f"  Copied {d}/ to half/{d}/")
        # Remove old
        shutil.rmtree(src_dir)
        print(f"  Removed old src/{d}/")

for f in FILES_TO_MOVE:
    src_file = SRC / f
    dst_file = HALF / f
    if src_file.exists() and not dst_file.exists():
        shutil.copy2(src_file, dst_file)
        print(f"  Copied {f} to half/{f}")
        src_file.unlink()
        print(f"  Removed old src/{f}")

print("\n=== Updating all imports from src. to half. ===")

# Find all Python files
python_files = list(HALF.rglob("*.py")) + list((REPO / "tests").rglob("*.py"))
python_files = [
    f for f in python_files if ".venv" not in str(f) and "egg-info" not in str(f)
]

count = 0
for filepath in python_files:
    content = filepath.read_text(encoding="utf-8")
    # Replace from src.xxx → from half.xxx
    new_content = content.replace("from src.", "from half.")
    new_content = new_content.replace("import src.", "import half.")
    if new_content != content:
        filepath.write_text(new_content, encoding="utf-8")
        count += 1
        if count <= 20:
            print(f"  Updated: {filepath.relative_to(REPO)}")

print(f"\nUpdated {count} files")

# Clean up old files in src/
print("\n=== Cleaning up src/ ===")
for item in SRC.iterdir():
    if item.name == "half":
        continue  # Keep half/
    if item.name == "__init__.py" and item.stat().st_size == 0:
        item.unlink()
        print(f"  Removed empty src/{item.name}")
        continue
    if item.name.startswith("hermes_half"):
        continue  # Keep egg-info
    if item.is_file() and item.name != "__init__.py":
        item.unlink()
        print(f"  Removed src/{item.name}")

# Remove empty __init__.py from src since it's no longer a package
src_init = SRC / "__init__.py"
if src_init.exists() and src_init.stat().st_size == 0:
    src_init.unlink()

print("\n=== Update pyproject.toml ===")
pyproject = REPO / "pyproject.toml"
content = pyproject.read_text()
# The packages.find where = ["src"] will automatically find half/ and its sub-packages
# No change needed there since setuptools discovers packages under src/
print("  pyproject.toml: packages.find where=['src'] → auto-discovers half/")

# Remove the sys.path hack from __main__.py since imports are now half.*
main_file = HALF / "__main__.py"
if main_file.exists():
    content = main_file.read_text()
    # Remove the sys.path hack lines
    lines = content.split("\n")
    new_lines = []
    skip_block = False
    for line in lines:
        if "# Ensure src/ is importable" in line:
            skip_block = True
            continue
        if skip_block and "_src_path" in line:
            continue
        if skip_block and "sys.path.insert" in line:
            skip_block = False
            continue
        if not skip_block:
            new_lines.append(line)
    main_file.write_text("\n".join(new_lines), encoding="utf-8")
    print("  Removed sys.path hack from half/__main__.py")

print("\n=== Migration complete ===")
print("Now need to verify: mypy, pytest, all imports")
