#!/bin/bash
# Quick update script for WineTranslator

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}WineTranslator Update Script${NC}"
echo ""

# Check if we're in a git repo
if [ ! -d .git ]; then
    echo -e "${YELLOW}Error: Not a git repository${NC}"
    echo "This script only works if WineTranslator was installed from git."
    exit 1
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo -e "${YELLOW}Warning: You have uncommitted changes${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Fetch updates
echo "Fetching updates from GitHub..."
git fetch origin

# Check if updates are available
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" = "$REMOTE" ]; then
    echo -e "${GREEN}Already up to date!${NC}"
    exit 0
fi

# Show what will be updated
echo ""
echo "New commits:"
git log --oneline $LOCAL..$REMOTE
echo ""

# Pull updates
echo "Pulling updates..."
git pull origin main

# Reinstall package
echo "Reinstalling package..."
pip3 install --user -e .

echo ""
echo -e "${GREEN}Update complete!${NC}"
echo "Restart WineTranslator to use the new version."
