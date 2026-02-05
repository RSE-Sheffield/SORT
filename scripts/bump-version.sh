#!/bin/bash
# Script to manually bump version before merging to main
# Usage: ./scripts/bump-version.sh [major|minor|patch]

set -e

BUMP_TYPE=${1:-patch}
CURRENT_VERSION=$(cat VERSION)

IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT_VERSION"

case "$BUMP_TYPE" in
  major)
    MAJOR=$((MAJOR + 1))
    MINOR=0
    PATCH=0
    ;;
  minor)
    MINOR=$((MINOR + 1))
    PATCH=0
    ;;
  patch)
    PATCH=$((PATCH + 1))
    ;;
  *)
    echo "Error: Invalid bump type. Use 'major', 'minor', or 'patch'"
    exit 1
    ;;
esac

NEW_VERSION="$MAJOR.$MINOR.$PATCH"

echo "Bumping version from $CURRENT_VERSION to $NEW_VERSION"

# Update VERSION file
echo "$NEW_VERSION" > VERSION

# Update package.json
npm version "$NEW_VERSION" --no-git-tag-version

echo "✓ Version bumped to $NEW_VERSION"
echo ""
echo "Files updated:"
echo "  - VERSION"
echo "  - package.json"
echo "  - package-lock.json"
echo ""
echo "Next steps:"
echo "  1. Review changes: git diff"
echo "  2. Commit changes: git add VERSION package.json package-lock.json"
echo "  3. Commit: git commit -m 'chore: bump version to $NEW_VERSION'"
echo "  4. Merge to main to trigger release"
