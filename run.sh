#!/bin/bash

# --- Get directory of this script ---
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# --- Path to virtual environment activate script ---
VENV_ACTIVATE="$SCRIPT_DIR/.venv/bin/activate"

# --- Check if virtual environment is active ---
if [ -n "$VIRTUAL_ENV" ]; then
    echo "Virtual environment already active: $VIRTUAL_ENV"
else
    if [ -f "$VENV_ACTIVATE" ]; then
        echo "Activating virtual environment..."
        # shellcheck source=/dev/null
        source "$VENV_ACTIVATE"
        echo "Virtual environment activated."
    else
        echo "ERROR: Virtual environment not found at $VENV_ACTIVATE"
        exit 1
    fi
fi

# --- Run the project ---
echo "Launching the Streamlit app..."
streamlit run "$SCRIPT_DIR/streamlit/streamlit_main.py"
