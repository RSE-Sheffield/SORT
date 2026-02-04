# Release Process

This document describes how to create releases for the SORT project.

## Overview

SORT uses **semantic versioning** (MAJOR.MINOR.PATCH) and **automatic releases** triggered when code is merged to the `main` branch.

- **Version File**: Version is tracked in the `VERSION` file at the repository root
- **Automatic Releases**: Every merge to `main` triggers a release workflow
- **Release Artifacts**: Built frontend assets and source archives are attached to releases

## Versioning Strategy

SORT follows [Semantic Versioning 2.0.0](https://semver.org/):

- **MAJOR** version: Incompatible API changes or major feature overhauls
- **MINOR** version: New features in a backwards-compatible manner
- **PATCH** version: Backwards-compatible bug fixes

## Release Workflow

### Automatic Release (Default)

When you merge a PR to `main`, the release workflow will:

1. Run all tests (Django + JavaScript)
2. Build frontend assets with Vite
3. Auto-increment the **patch** version (e.g., 0.1.0 → 0.1.1)
4. Create a GitHub release with:
   - Built frontend assets (`sort-frontend-{version}.tar.gz`)
   - Complete source archive (`SORT-{version}.tar.gz`)
   - Auto-generated release notes from commits
5. Update VERSION and package.json files

**Example**: Merging PR #123 to `main` automatically creates release v0.1.1

### Manual Version Bump (Major/Minor Releases)

For major or minor version changes, bump the version **before** merging to main:

#### Option 1: Using the bump-version script (Recommended)

```bash
# Bump major version (e.g., 1.0.0 → 2.0.0)
./scripts/bump-version.sh major

# Bump minor version (e.g., 0.1.0 → 0.2.0)
./scripts/bump-version.sh minor

# Bump patch version (e.g., 0.1.0 → 0.1.1)
./scripts/bump-version.sh patch

# Commit the changes
git add VERSION package.json package-lock.json
git commit -m "chore: bump version to $(cat VERSION)"
git push
```

#### Option 2: Manual edit

1. Edit the `VERSION` file directly
2. Update `package.json` version to match
3. Run `npm install` to update `package-lock.json`
4. Commit and push

### Manual Release Trigger

You can also manually trigger a release from the GitHub Actions UI:

1. Go to **Actions** → **Create Release** workflow
2. Click **Run workflow**
3. Optionally specify a version (e.g., `1.0.0`)
4. Click **Run workflow**

This is useful for:
- Creating a hotfix release
- Re-releasing after a failed workflow
- Creating a specific version number

## Release Artifacts

Each release includes:

### 1. Frontend Assets (`sort-frontend-{version}.tar.gz`)
Built Vite/Svelte bundle ready for production deployment. Extract to `static/ui-components/`.

### 2. Source Archive (`SORT-{version}.tar.gz`)
Complete source code with built frontend assets included.

## Release Notes

Release notes are auto-generated from commit messages between releases. For better release notes:

- Use [Conventional Commits](https://www.conventionalcommits.org/) format:
  - `feat: Add user authentication`
  - `fix: Resolve survey response validation bug`
  - `docs: Update installation guide`
  - `chore: Upgrade Django to 5.1.13`

- Write descriptive commit messages that explain **what** and **why**

## Example Release Workflow

### Scenario: Feature Release (Minor Version)

```bash
# On dev branch, implement new feature
git checkout dev
# ... make changes ...
git commit -m "feat: Add evidence file upload functionality"

# Create PR to dev, get it reviewed and merged
# Now ready to release

# Checkout dev, bump minor version
git checkout dev
./scripts/bump-version.sh minor  # 0.1.5 → 0.2.0
git add VERSION package.json package-lock.json
git commit -m "chore: bump version to 0.2.0"
git push origin dev

# Create PR from dev to main
# Once merged to main, release v0.2.0 is automatically created
```

### Scenario: Hotfix Release (Patch Version)

```bash
# On main branch, fix critical bug
git checkout main
git pull
# ... fix bug ...
git commit -m "fix: Correct survey response validation for optional fields"

# No need to bump version manually - patch is auto-incremented
# Push to main triggers release
git push origin main
# → Automatically creates v0.1.6 (assuming current is v0.1.5)
```

## Rollback

If a release has issues:

1. **Revert the problematic commits** on main:
   ```bash
   git revert <commit-hash>
   git push origin main
   ```

2. A new release will be automatically created with the revert

3. Optionally **delete the problematic release** from GitHub UI (Releases page)

## Troubleshooting

### Workflow fails on tests
- Fix the failing tests on a feature branch
- Create PR to dev, then merge to main
- Tests must pass before release is created

### Version conflict
- Ensure VERSION file and package.json versions match
- Pull latest main branch before bumping version

### Release not created
- Check GitHub Actions logs for errors
- Verify workflow permissions (requires `contents: write`)

## Notes

- **Never push directly to main** - always use PRs through dev branch
- **Review release notes** after creation and edit if needed via GitHub UI
- **Tag format**: All releases are tagged as `v{VERSION}` (e.g., v1.0.0)
- The release workflow commits version bumps back to main automatically

## Future Enhancements

Potential improvements to consider:

- [ ] Docker image builds and publication to GitHub Container Registry
- [ ] Changelog generation using [conventional-changelog](https://github.com/conventional-changelog/conventional-changelog)
- [ ] Pre-release/beta releases for testing
- [ ] Deployment automation to staging/production environments
- [ ] Slack/email notifications for new releases
