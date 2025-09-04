#!/bin/bash
set -e

# --- Get the directory of this script ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# --- Determine if we're already inside GenAIFinalProject ---
CURRENT_DIR_NAME="$(basename "$SCRIPT_DIR")"

if [ "$CURRENT_DIR_NAME" = "GenAIFinalProject" ]; then
    echo "Running inside GenAIFinalProject directory."
    cd "$SCRIPT_DIR"
elif [ -d "$SCRIPT_DIR/GenAIFinalProject" ]; then
    echo "Found GenAIFinalProject folder next to the script. Entering it..."
    cd "$SCRIPT_DIR/GenAIFinalProject"
else
    echo "GenAIFinalProject not found. Cloning..."
    cd "$SCRIPT_DIR"
    git clone https://github.com/yossifun/GenAIFinalProject
    cd GenAIFinalProject
fi

# --- Prepare secrets directory ---
SECRETS_DIR="secrets"
mkdir -p "$SECRETS_DIR"

# List of secret files and default content
echo "Looking for secret files..."

declare -A SECRET_FILES
SECRET_FILES["openai_api_key.txt"]="Replace this with your Open AI API key (sk-XXXX)"
SECRET_FILES["openai_fine_tune_model.txt"]="Replace this with your Open AI fine tuned model id"

# Track if any defaults were used
MISSING_SECRETS=0

# --- Handle each secret file independently ---
for FILE in "${!SECRET_FILES[@]}"; do
    DEST="$SECRETS_DIR/$FILE"
    if [ -f "$SECRETS_DIR/$FILE" ]; then
        echo "$FILE already exists in $SECRETS_DIR. Skipping."
    elif [ -f "$SCRIPT_DIR/secrets/$FILE" ]; then
        cp "$SCRIPT_DIR/secrets/$FILE" "$DEST"
        echo "Copied $FILE from script's secrets folder."
    elif [ -f "$SCRIPT_DIR/$FILE" ]; then
        cp "$SCRIPT_DIR/$FILE" "$DEST"
        echo "Copied $FILE from script directory."
    else
        echo "${SECRET_FILES[$FILE]}" > "$DEST"
        echo "Created default $FILE."
        MISSING_SECRETS=1
    fi
done


# --- Check if any defaults were created ---
if [ $MISSING_SECRETS -eq 1 ]; then
    echo "WARNING: One or more secret files are missing ; placeholders were created instead."
    echo "Please update the secret files in $SECRETS_DIR before running the project."
    echo "Then run the project with this command: streamlit run streamlit/streamlit_main.py "
    exit 1
fi

# --- Create virtual environment ---
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "Virtual environment created."
else
    echo "Virtual environment already exists. Skipping creation."
fi

# --- Activate environment ---
source .venv/bin/activate
echo "Virtual environment activated."

# --- Install dependencies ---
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
echo "Dependencies installed."
echo "Setup complete. You can now run the project with run.sh"