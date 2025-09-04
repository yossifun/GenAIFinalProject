import os
import subprocess
import sys
import platform

REPO_URL = "https://github.com/yossifun/GenAIFinalProject"

# Clone repo
subprocess.check_call(["git", "clone", REPO_URL])
os.chdir("GenAIFinalProject")

# Create virtual environment
subprocess.check_call([sys.executable, "-m", "venv", ".venv"])

# Activate virtual environment (only for pip install step)
venv_python = ".venv\\Scripts\\python.exe" if platform.system() == "Windows" else ".venv/bin/python"
subprocess.check_call([venv_python, "-m", "pip", "install", "-r", "requirements.txt"])

print("Installation complete. To activate the environment:")
if platform.system() == "Windows":
    print(r"   .venv\Scripts\activate")
else:
    print("   source .venv/bin/activate")
