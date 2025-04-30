import sys
import os
import json
import shutil
import inspect
import hashlib
import uuid
import re
from datetime import datetime
import argparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "tracker_config.json")
DEFAULT_TRACKED_VERSIONS_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "tracked_versions"))

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            return config.get("tracked_versions_dir", DEFAULT_TRACKED_VERSIONS_DIR)
    else:
        return DEFAULT_TRACKED_VERSIONS_DIR

TRACKED_VERSIONS_DIR = load_config()

def python_get_script_dependencies(script_path):
    """Extracts local script dependencies from import statements (Python)."""
    dependencies = set()
    file_ext = os.path.splitext(script_path)[1]

    with open(script_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if line.startswith("import ") or line.startswith("from "):
            parts = line.split()
            module_name = parts[1].split('.')[0]  # Get the base module
            module_file = f"{module_name}.py"
            if os.path.exists(module_file):
                dependencies.add(module_file)

    return list(dependencies)

def get_input_files(script_path):
    """Extracts input file paths from common file-reading patterns in Python and MATLAB scripts."""
    input_files = set()
    file_ext = os.path.splitext(script_path)[1]

    python_patterns = [
        r'pd\.read_csv\(["\']([^"\']+)["\']',  # Pandas read_csv
        r'open\(["\']([^"\']+)["\']',         # open("file.csv")
        r'load\(["\']([^"\']+)["\']',         # load("data.pkl"), common for pickle
    ]

    matlab_patterns = [
        r'load\(["\']([^"\']+)["\']',         # load('data.mat')
        r'xlsread\(["\']([^"\']+)["\']',      # xlsread('file.xlsx')
        r'readmatrix\(["\']([^"\']+)["\']',   # readmatrix('file.csv')
    ]

    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()

    patterns = python_patterns if file_ext == ".py" else matlab_patterns
    for pattern in patterns:
        print(f"Searching for pattern: {pattern}")
        matches = re.findall(pattern, content)
        for match in matches:
            print(f"Match found: {match}")
            if os.path.exists(match):
                print("Path exists")
                input_files.add(match)

    return list(input_files)

def hash_file(file_path):
    """Returns a SHA256 hash of a file to track versions."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(4096):
            hasher.update(chunk)
    return hasher.hexdigest()

def generate_version_id():
    """Generates a unique version ID based on the current timestamp and a random UUID."""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    unique_id = str(uuid.uuid4())[:8]  # Take first 8 chars of UUID
    return f"{timestamp}_{unique_id}"

def track_figure_metadata(fig_path, script_path = None, matlabdeps = None):
    """Logs metadata, tracks dependencies and input files, and copies necessary files (supports Python & MATLAB)."""
    if not script_path:
        frame = inspect.stack()[1]  # Caller of this function
        script_path = frame.filename
    script_name = os.path.basename(script_path)

    print("--- file_tracker DEBUG INFO: ---")
    print(f"fig_path: {fig_path}")
    print(f"script_path: {script_path}")
    print(f"matlabdeps: {matlabdeps}")
    print("--- END ---")

    # Generate unique version ID and timestamp
    version_id = generate_version_id()

    # Get dependencies and input files
    if not matlabdeps:
        [dependencies, input_files] = python_get_all_dependencies(script_path)
        dependencies = list(dependencies)
        input_files = list(input_files)
    elif matlabdeps:
        dependencies = matlabdeps.split(os.pathsep)
        input_files = []

    # Metadata structure
    metadata = {
        "output_file": fig_path,
        "author": os.getenv("USER") or os.getenv("USERNAME"),
        "created_at": datetime.utcnow().isoformat(),
        "main_script": script_name,
        "dependencies": {dep: hash_file(dep) for dep in dependencies},
        "input_files": {inp: hash_file(inp) for inp in input_files},
        "script_hash": hash_file(script_path),
        "version_id": version_id
    }

    # Create versioned folder with version ID
    version_folder = os.path.join(TRACKED_VERSIONS_DIR, version_id)
    os.makedirs(version_folder, exist_ok=True)

    # Save metadata JSON inside the version folder
    meta_filename = f"{version_folder}/{os.path.basename(fig_path)}_{version_id}.metadata.json"
    with open(meta_filename, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4)

    # Copy script, dependencies, and input files to versioned folder
    shutil.copy(script_path, os.path.join(version_folder, script_name))
    for dep in dependencies:
        shutil.copy(dep, os.path.join(version_folder, os.path.basename(dep)))
    for inp in input_files:
        shutil.copy(inp, os.path.join(version_folder, os.path.basename(inp)))

    # Backup the figure with version ID and timestamp
    figure_backup = f"{version_folder}/{os.path.basename(fig_path)}"
    shutil.copy(fig_path, figure_backup)

    print(f"Metadata saved: {meta_filename}")
    print(f"Scripts, input files, and figure copied to: {version_folder}")

def python_get_all_dependencies(script_path, visited=None):
    if visited is None:
        visited = set()

    if script_path in visited:
        return set(), set()

    visited.add(script_path)
    dependencies = set(python_get_script_dependencies(script_path))
    input_files = set(get_input_files(script_path))

    for dep in list(dependencies):  # Convert to list to avoid modifying set during iteration
        if dep not in visited:
            dep_deps, dep_inputs = python_get_all_dependencies(dep, visited)
            dependencies.update(dep_deps)
            input_files.update(dep_inputs)

    return dependencies, input_files

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python track_figure_metadata.py <figure_path> <script_path> --matlabdeps <list_of_deps>")
        sys.exit(1)

    log_file = open("file_tracker_output.log", "w")
    sys.stdout = log_file

    parser = argparse.ArgumentParser()

    parser.add_argument('fig_path', type=str)
    parser.add_argument('script_path', type=str)

    parser.add_argument('--matlabdeps', type=str)

    args = parser.parse_args()
    print(args.matlabdeps)

    track_figure_metadata(args.fig_path, args.script_path, args.matlabdeps)

    sys.stdout = sys.__stdout__
    log_file.close()
