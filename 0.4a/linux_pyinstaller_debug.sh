#!/bin/bash

# ============================================================
# Edgar AI v0.3a Build Script for Linux
# ============================================================

# Move to the script directory
cd "$(dirname "$0")" || exit

# Paths
PYINSTALLER="/home/aayden/Documents/GitHub/Edgar_Rule_based_AI/.venv/bin/pyinstaller"
PACKAGE_DIR="dist/package"
ICON_DIR="icon"

# ============================================================
# Clean previous builds and create package directory
# ============================================================
echo "Cleaning previous builds..."
rm -rf build "$PACKAGE_DIR" *.spec
mkdir -p "$PACKAGE_DIR"

# ============================================================
# Shared BS4 hidden imports (for all apps using web queries)
# ============================================================
BS4_IMPORTS=(
  --hidden-import beautifulsoup4
  --hidden-import bs4
  --hidden-import bs4.element
  --hidden-import bs4.builder
  --hidden-import bs4.builder._htmlparser
)

# ============================================================
# Function to build a PyInstaller executable
# ============================================================
build_app() {
  local name="$1"
  local entry="$2"
  local icon="$3"
  local console_flag="$4"
  shift 4
  local extra_hidden=("$@")

  echo "Building $name..."
  "$PYINSTALLER" --onefile \
    --distpath "$PACKAGE_DIR" \
    --name "$name" \
    ${icon:+--icon "$ICON_DIR/$icon"} \
    ${console_flag:+--console} \
    --hidden-import configparser \
    --add-data "resources:resources" \
    --add-data "models:models" \
    --add-data "core:core" \
    "${extra_hidden[@]}" \
    "${BS4_IMPORTS[@]}" \
    "$entry"
}

# ============================================================
# Build all executables
# ============================================================

# chat-0.3a (GUI)
build_app "chat-0.3a" "main.py" "chat.ico" "" \
  --hidden-import core.modules.weather \
  --hidden-import core.modules.time \
  --hidden-import core.modules.search \
  --hidden-import fuzzywuzzy \
  --hidden-import fuzzywuzzy.process \
  --hidden-import fuzzywuzzy.fuzz \
  --hidden-import pytz \
  --hidden-import requests \
  --hidden-import Levenshtein \
  --hidden-import Levenshtein.levenshtein_cpp

# tty-0.3a (Terminal)
build_app "tty-0.3a" "tty.py" "tty.ico" "--console" \
  --hidden-import core.modules.weather \
  --hidden-import core.modules.time \
  --hidden-import core.modules.search \
  --hidden-import fuzzywuzzy \
  --hidden-import fuzzywuzzy.process \
  --hidden-import fuzzywuzzy.fuzz \
  --hidden-import pytz \
  --hidden-import requests \
  --hidden-import Levenshtein \
  --hidden-import Levenshtein.levenshtein_cpp

# train-0.3a (GUI)
build_app "train-0.3a" "training/train.py" "train.ico" "" \
  --add-data "training:training" \
  --hidden-import fuzzywuzzy \
  --hidden-import fuzzywuzzy.process \
  --hidden-import fuzzywuzzy.fuzz

# route-trainer-0.3a
build_app "route-trainer-0.3a" "route trainer.py" "route-trainer.ico" "" \
  --hidden-import fuzzywuzzy \
  --hidden-import fuzzywuzzy.process \
  --hidden-import fuzzywuzzy.fuzz

# webui-0.3a (Web interface)
build_app "webui-0.3a" "webui.py" "webui.ico" "" \
  --add-data "webui:webui" \
  --hidden-import fuzzywuzzy \
  --hidden-import fuzzywuzzy.process \
  --hidden-import fuzzywuzzy.fuzz \
  --hidden-import pytz \
  --hidden-import requests \
  --hidden-import Levenshtein \
  --hidden-import Levenshtein.levenshtein_cpp

# ============================================================
# Copy additional resources to package directory
# ============================================================
echo "Copying resource files..."
cp config.cfg "$PACKAGE_DIR/"
cp -r resources "$PACKAGE_DIR/resources"
cp -r models "$PACKAGE_DIR/models"
cp -r "$ICON_DIR" "$PACKAGE_DIR/$ICON_DIR"

# ============================================================
# Create README.txt
# ============================================================
echo "Creating README.txt..."
cat > "$PACKAGE_DIR/README.txt" << EOF
Edgar AI Assistant v0.3a
========================

Distribution Package

Included Files:
- chat-0.3a       - Main Edgar AI application (GUI)
- tty-0.3a        - Terminal/Command Line interface
- train-0.3a      - Training application
- route-trainer-0.3a - Routing configuration tool
- webui-0.3a      - Web interface application
- config.cfg      - Configuration file (shared by all apps)
- resources/      - Routing configuration and resources
- models/         - AI model data
- icon/           - Application icons

Usage:
1. Run chat-0.3a for GUI
2. Run tty-0.3a for terminal
3. Run train-0.3a for training
4. Run route-trainer-0.3a to configure modules
5. Run webui-0.3a for web interface

TTY Interface Features:
- Full terminal interface
- Real-time text streaming
- Commands: stats, context, reset, models, modules, config, help

New Features in v0.3a:
- New search module
- Enhanced module routing
- Improved text streaming
- Better error handling
- Custom icons

System Requirements:
- Linux (tested on Debian/Ubuntu)
- Python 3.12 (included in executables)
- Internet connection for weather and search modules
EOF

# ============================================================
# Clean up build artifacts (keep package directory)
# ============================================================
echo "Cleaning up build artifacts..."
rm -rf build *.spec

# ============================================================
# Finish
# ============================================================
echo
echo "========================================"
echo "BUILD COMPLETED SUCCESSFULLY!"
echo "Executables and resources are in: $PACKAGE_DIR"
echo
xdg-open "$PACKAGE_DIR"
