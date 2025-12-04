#!/bin/bash
# Calibre-Web-AI Setup Script (OS Agnostic)
# Works on Windows (Git Bash), Linux, and macOS

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Detect OS
detect_os() {
    case "$(uname -s)" in
        Linux*)     echo "Linux";;
        Darwin*)    echo "macOS";;
        CYGWIN*)    echo "Windows";;
        MINGW*)     echo "Windows";;
        MSYS*)      echo "Windows";;
        *)          echo "Unknown";;
    esac
}

OS=$(detect_os)

echo -e "${CYAN}Calibre-Web-AI Setup${NC}"
echo -e "Detected OS: ${GREEN}$OS${NC}"
echo ""

# Check Python
echo -e "${YELLOW}Checking Python installation...${NC}"
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo -e "${RED}ERROR: Python not found. Please install Python 3.7+ from https://www.python.org/downloads/${NC}"
    exit 1
fi

# Use python3 if available, otherwise python
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python"
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
echo -e "${GREEN}Found: $PYTHON_VERSION${NC}"
echo ""

# Determine virtual environment paths based on OS
if [ "$OS" = "Windows" ]; then
    VENV_ACTIVATE="venv/Scripts/activate"
    VENV_PYTHON="venv/Scripts/python"
else
    VENV_ACTIVATE="venv/bin/activate"
    VENV_PYTHON="venv/bin/python"
fi

# Create virtual environment
echo -e "${YELLOW}Creating virtual environment...${NC}"
if [ -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment already exists. Skipping creation.${NC}"
else
    $PYTHON_CMD -m venv venv
    echo -e "${GREEN}Virtual environment created.${NC}"
fi
echo ""

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
if [ -f "$VENV_ACTIVATE" ]; then
    source "$VENV_ACTIVATE"
    echo -e "${GREEN}Virtual environment activated.${NC}"
else
    echo -e "${RED}ERROR: Virtual environment activation script not found at $VENV_ACTIVATE${NC}"
    exit 1
fi
echo ""

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
$VENV_PYTHON -m pip install --upgrade pip --quiet
echo -e "${GREEN}pip upgraded.${NC}"
echo ""

# Install dependencies
echo -e "${YELLOW}Installing dependencies from requirements.txt...${NC}"
$VENV_PYTHON -m pip install -r requirements.txt
echo -e "${GREEN}Dependencies installed.${NC}"
echo ""

# Install in development mode
echo -e "${YELLOW}Installing calibre-web-ai in development mode...${NC}"
$VENV_PYTHON -m pip install -e . --quiet
echo -e "${GREEN}Development installation complete.${NC}"
echo ""

# Success message
echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo -e "${CYAN}To run calibre-web:${NC}"
if [ "$OS" = "Windows" ]; then
    echo -e "  1. Activate virtual environment: ${YELLOW}source venv/Scripts/activate${NC}"
else
    echo -e "  1. Activate virtual environment: ${YELLOW}source venv/bin/activate${NC}"
fi
echo -e "  2. Run: ${YELLOW}python cps.py${NC}"
echo -e "  3. Open browser: ${YELLOW}http://localhost:8083${NC}"
echo -e "  4. Login: ${YELLOW}admin / admin123${NC}"
echo ""




