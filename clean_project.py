"""
clean_project.py

Fully cleans a Python/Streamlit project:
- Removes Python bytecode files
- Clears Streamlit caches
- Clears session state
- Deletes logs and temporary files
"""

import os
import shutil
import streamlit as st

# ---------------- Settings ----------------
LOG_DIRS = ["logs"]       # add any other log directories
TMP_EXTENSIONS = [".tmp", ".swp"]

# ---------------- Clear Python bytecode ----------------
def clear_python_cache(base_dir="."):
    print("Clearing __pycache__ directories and .pyc files...")
    for root, dirs, files in os.walk(base_dir):
        for dir_name in dirs:
            if dir_name == "__pycache__":
                dir_path = os.path.join(root, dir_name)
                shutil.rmtree(dir_path)
                print(f"Removed {dir_path}")
        for file_name in files:
            if file_name.endswith(".pyc") or file_name.endswith(".pyo"):
                file_path = os.path.join(root, file_name)
                os.remove(file_path)
                print(f"Removed {file_path}")

# ---------------- Clear Streamlit cache ----------------
def clear_streamlit_cache():
    try:
        st.cache_data.clear()
        st.cache_resource.clear()
        if hasattr(st, "session_state"):
            st.session_state.clear()
        print("Cleared Streamlit cache and session state")
    except Exception as e:
        print(f"Streamlit cache clear skipped: {e}")

# ---------------- Clear log files ----------------
def clear_logs():
    for log_dir in LOG_DIRS:
        if os.path.exists(log_dir):
            for file_name in os.listdir(log_dir):
                file_path = os.path.join(log_dir, file_name)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    print(f"Removed log file {file_path}")

# ---------------- Clear temporary files ----------------
def clear_temp_files(base_dir="."):
    for root, dirs, files in os.walk(base_dir):
        for file_name in files:
            if any(file_name.endswith(ext) for ext in TMP_EXTENSIONS):
                file_path = os.path.join(root, file_name)
                os.remove(file_path)
                print(f"Removed temp file {file_path}")

# ---------------- Main ----------------
def main():
    print("Cleaning project...")
    clear_python_cache()
    clear_streamlit_cache()
    clear_logs()
    clear_temp_files()
    print("Project cleaned successfully!")

if __name__ == "__main__":
    main()
