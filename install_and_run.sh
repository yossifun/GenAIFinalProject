#!/bin/bash

# Run install.sh first
./install.sh
INSTALL_EXIT_CODE=$?

if [ $INSTALL_EXIT_CODE -ne 0 ]; then
    echo "Installation failed with exit code $INSTALL_EXIT_CODE."
    read -p "Press Enter to exit..."
    exit $INSTALL_EXIT_CODE
fi

# Installation successful
echo "Installation successful."
if [ $# -eq 0 ]; then
    echo "Launching run.sh in a new terminal with no arguments..."
else
    echo "Launching run.sh in a new terminal with arguments: $*"
fi
echo "Closing this terminal in 3 seconds..."
sleep 3

# Detect platform
OS_TYPE=$(uname)

if [ "$OS_TYPE" = "Darwin" ]; then
    # macOS
    osascript <<EOF
tell application "Terminal"
    activate
    do script "cd \"$(pwd)\"; ./run.sh $*"
end tell
EOF
elif [ "$OS_TYPE" = "Linux" ]; then
    # Linux: detect terminal emulator
    if command -v gnome-terminal >/dev/null 2>&1; then
        TERMINAL="gnome-terminal"
        TERMINAL_CMD="-- bash -c './run.sh $*; exec bash'"
    elif command -v konsole >/dev/null 2>&1; then
        TERMINAL="konsole"
        TERMINAL_CMD="-e bash -c './run.sh $*; exec bash'"
    elif command -v xfce4-terminal >/dev/null 2>&1; then
        TERMINAL="xfce4-terminal"
        TERMINAL_CMD="-e bash -c './run.sh $*; exec bash'"
    elif command -v xterm >/dev/null 2>&1; then
        TERMINAL="xterm"
        TERMINAL_CMD="-hold -e ./run.sh $*"
    else
        echo "No known terminal emulator found. Run ./run.sh manually."
        exit 1
    fi

    $TERMINAL $TERMINAL_CMD
else
    echo "Unsupported OS: $OS_TYPE"
    exit 1
fi

exit 0
