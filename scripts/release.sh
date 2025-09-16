#!/bin/bash
# Release helper script for NEDC-BENCH

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}NEDC-BENCH Release Helper${NC}"
echo "========================="

# Check if we're on main branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo -e "${RED}Error: Not on main branch (currently on $CURRENT_BRANCH)${NC}"
    echo "Please switch to main branch: git checkout main"
    exit 1
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo -e "${RED}Error: Uncommitted changes detected${NC}"
    echo "Please commit or stash changes before releasing"
    exit 1
fi

# Get current version from pyproject.toml
CURRENT_VERSION=$(grep '^version = ' pyproject.toml | cut -d'"' -f2)
echo -e "Current version: ${YELLOW}$CURRENT_VERSION${NC}"

# Prompt for new version
read -p "Enter new version (e.g., 0.2.0): " NEW_VERSION

# Validate version format
if ! [[ "$NEW_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.]+)?$ ]]; then
    echo -e "${RED}Error: Invalid version format${NC}"
    echo "Please use semantic versioning: MAJOR.MINOR.PATCH or MAJOR.MINOR.PATCH-PRERELEASE"
    exit 1
fi

echo ""
echo -e "${GREEN}Release Checklist:${NC}"
echo "1. Update version in pyproject.toml to $NEW_VERSION"
echo "2. Update CHANGELOG.md with release date"
echo "3. Run tests (make ci)"
echo "4. Commit changes"
echo "5. Create git tag v$NEW_VERSION"
echo "6. Push to GitHub"
echo ""

read -p "Do you want to proceed? (y/n): " PROCEED
if [ "$PROCEED" != "y" ]; then
    echo "Release cancelled"
    exit 0
fi

# Update version in pyproject.toml
echo -e "${GREEN}Updating pyproject.toml...${NC}"
sed -i "s/^version = \".*\"/version = \"$NEW_VERSION\"/" pyproject.toml

# Remind to update CHANGELOG
echo -e "${YELLOW}Please update CHANGELOG.md:${NC}"
echo "1. Change [Unreleased] to [$NEW_VERSION] - $(date +%Y-%m-%d)"
echo "2. Add new [Unreleased] section at top"
echo ""
read -p "Press enter when CHANGELOG.md is updated..."

# Run tests
echo -e "${GREEN}Running tests...${NC}"
make ci || {
    echo -e "${RED}Tests failed! Aborting release.${NC}"
    git checkout pyproject.toml
    exit 1
}

# Commit changes
echo -e "${GREEN}Committing changes...${NC}"
git add pyproject.toml CHANGELOG.md
git commit -m "Release v$NEW_VERSION"

# Create tag
echo -e "${GREEN}Creating tag...${NC}"
echo "Enter tag message (press Ctrl+D when done):"
TAG_MESSAGE=$(cat)
git tag -a "v$NEW_VERSION" -m "$TAG_MESSAGE"

echo ""
echo -e "${GREEN}Release prepared successfully!${NC}"
echo ""
echo "Next steps:"
echo "1. Push changes: git push origin main"
echo "2. Push tag: git push origin v$NEW_VERSION"
echo "3. Create GitHub release from tag"
echo "4. Update version to next dev version (e.g., ${NEW_VERSION}-dev)"
echo ""
echo "To undo this release (before pushing):"
echo "  git tag -d v$NEW_VERSION"
echo "  git reset --hard HEAD~1"
