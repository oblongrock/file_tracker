import os
import shutil
import json
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox

def select_matlab_dir():
    if os.name == 'nt':  # Windows
        default_dir = r"C:\Program Files\MATLAB\R2024a"
    else:
        default_dir = "/usr/local/MATLAB"

    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo("Select MATLAB Directory", "Please select your MATLAB installation directory.")

    matlab_dir = filedialog.askdirectory(initialdir=default_dir, title="Select MATLAB Directory")
    root.destroy()

    return matlab_dir

def validate_matlab_dir(matlab_dir):
    """Simple validation of MATLAB installation directory."""
    expected_subdirs = ["toolbox", "bin", "extern"]

    for subdir in expected_subdirs:
        if not os.path.isdir(os.path.join(matlab_dir, subdir)):
            return False
    return True

def select_tracked_versions_dir():
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo("Select Tracked Versions Directory", "Please select or create the directory to store tracked figure versions.")

    tracked_versions_dir = filedialog.askdirectory(title="Select Tracked Versions Directory")
    root.destroy()

    return tracked_versions_dir

def install_files(matlab_dir, tracked_versions_dir):
    """Copy necessary files into the MATLAB toolbox directory."""
    file_tracker_toolbox_dir = os.path.join(matlab_dir, "toolbox", "file_tracker")
    os.makedirs(file_tracker_toolbox_dir, exist_ok=True)

    base_dir = os.path.dirname(os.path.abspath(__file__))

    files_to_copy = [
        "print_hook.m",
        "track_figure_metadata_python.m",
        "file_tracker.py",
    ]

    for filename in files_to_copy:
        src = os.path.join(base_dir, filename)
        dst = os.path.join(file_tracker_toolbox_dir, filename)
        print(f"Copying {src} -> {dst}")
        shutil.copy(src, dst)

    # Write tracker_config.json
    config = {
        "tracked_versions_dir": tracked_versions_dir
    }
    config_path = os.path.join(file_tracker_toolbox_dir, "tracker_config.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

    print(f"Configuration written to {config_path}")

    return file_tracker_toolbox_dir

def add_file_tracker_to_matlab_path(file_tracker_toolbox_dir, matlab_dir):
    """Launch MATLAB to add the file_tracker toolbox to path and save."""
    print("Attempting to update MATLAB path...")

    if os.name == 'nt':
        matlab_command = os.path.join(matlab_dir, "bin", "matlab.exe")
    else:
        matlab_command = os.path.join(matlab_dir, "bin", "matlab")

    # Check if the MATLAB executable exists
    if not os.path.isfile(matlab_command):
        print(f"MATLAB executable not found at {matlab_command}")
        messagebox.showerror("MATLAB Not Found", f"Could not find MATLAB executable at:\n{matlab_command}\nPlease update your MATLAB path manually.")
        return

    # Properly format paths (escape backslashes on Windows)
    file_tracker_toolbox_dir_matlab = file_tracker_toolbox_dir.replace("\\", "/")

    # Build the MATLAB command
    matlab_script = f"addpath(genpath('{file_tracker_toolbox_dir_matlab}')); savepath; exit;"

    try:
        subprocess.run(
            [matlab_command, "-batch", matlab_script],
            check=True
        )
        print("MATLAB path updated successfully.")
    except Exception as e:
        print("Error running MATLAB to update path:", str(e))
        messagebox.showerror("MATLAB Path Update Failed", "Failed to automatically update the MATLAB path. You may need to manually add toolbox/file_tracker to your MATLAB path.")

def main():
    matlab_dir = select_matlab_dir()
    if not matlab_dir:
        print("Installation cancelled. No MATLAB directory selected.")
        return

    if not validate_matlab_dir(matlab_dir):
        messagebox.showerror("Invalid MATLAB Directory", "The selected directory does not look like a valid MATLAB installation. Installation cancelled.")
        return

    tracked_versions_dir = select_tracked_versions_dir()
    if not tracked_versions_dir:
        print("Installation cancelled. No tracked versions directory selected.")
        return

    file_tracker_toolbox_dir = install_files(matlab_dir, tracked_versions_dir)

    add_file_tracker_to_matlab_path(file_tracker_toolbox_dir, matlab_dir)

    messagebox.showinfo("Installation Complete", "File Tracker Toolbox installed successfully!\n\nMATLAB path updated!\nYou can now use print_hook immediately.")

if __name__ == "__main__":
    main()
