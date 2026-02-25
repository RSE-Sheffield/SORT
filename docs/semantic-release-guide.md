# Semantic Release Guide for SORT

## What Changed?

SORT now uses **semantic-release** for fully automated releases. You no longer need to manually bump versions or run release scripts.

## How It Works

### Before (Manual Process)
1. Make changes
2. **Manually** run `./scripts/bump-version.sh patch`
3. **Manually** commit version changes
4. Merge to main → release created

### After (Fully Automated)
1. Make changes with conventional commit messages
2. Merge to main → **automatic** version bump + release

## Commit Message Format

Use [Conventional Commits](https://www.conventionalcommits.org/) to control releases:

| Commit Type | Version Bump | Example |
|-------------|--------------|---------|
| `feat:` or `feature:` | **Minor** (0.1.0 → 0.2.0) | `feat: Add file upload` |
| `fix:` | **Patch** (0.1.0 → 0.1.1) | `fix: Correct validation` |
| `perf:` | **Patch** | `perf: Optimize queries` |
| `refactor:` | **Patch** | `refactor: Simplify code` |
| `docs:` | **Patch** | `docs: Update README` |
| `chore:` | **No release** | `chore: Update deps` |
| `test:` | **No release** | `test: Add unit tests` |
| `ci:` | **No release** | `ci: Update workflow` |
| `BREAKING CHANGE:` | **Major** (0.1.0 → 1.0.0) | See below |

### Breaking Changes

Add `BREAKING CHANGE:` in the commit footer for major versions:

```bash
git commit -m "feat: Redesign survey API

BREAKING CHANGE: Survey configuration endpoint now requires authentication.
Update your API clients to include Authorization header."
```

## What Gets Automated?

When you merge to `main` with release-worthy commits:

1. ✅ **Version determination** - Analyzes commits to decide version bump
2. ✅ **VERSION file update** - Automatically updated
3. ✅ **package.json update** - Automatically updated
4. ✅ **package-lock.json update** - Automatically updated
5. ✅ **CHANGELOG.md generation** - Created/updated with release notes
6. ✅ **Git tag creation** - Creates `v{version}` tag
7. ✅ **GitHub release** - Created with artifacts and notes
8. ✅ **Commit version changes** - Committed back to main with `[skip ci]`

## Example Workflows

### New Feature (Minor Release)

```bash
git checkout -b feat/upload-improvements
# ... make changes ...
git commit -m "feat: Add drag-and-drop file upload"
git push origin feat/upload-improvements
# Create PR → merge to main
# ✅ Automatically creates v0.2.0 release
```

### Bug Fix (Patch Release)

```bash
git checkout -b fix/validation-error
# ... fix bug ...
git commit -m "fix: Correct survey date validation logic"
git push origin fix/validation-error
# Create PR → merge to main
# ✅ Automatically creates v0.2.1 release
```

### Multiple Changes in One PR

```bash
git checkout -b improvements
git commit -m "feat: Add export to PDF"
git commit -m "fix: Correct timezone handling"
git commit -m "docs: Update API documentation"
git commit -m "chore: Update test fixtures"
# Create PR → merge to main
# ✅ Highest priority wins: "feat" found → v0.3.0 release
# ✅ CHANGELOG includes all 4 commits
```

### No Release Needed

```bash
git checkout -b chore/dependencies
git commit -m "chore: Update Django to 5.1.14"
git commit -m "test: Add missing test coverage"
# Create PR → merge to main
# ✅ No release created (only chore/test commits)
```

## Files Modified by semantic-release

After each release, semantic-release commits these files back to `main`:

- `VERSION` - Updated with new version number
- `package.json` - Version field updated
- `package-lock.json` - Updated after package.json change
- `CHANGELOG.md` - New release section added

**These commits are tagged `[skip ci]`** to prevent infinite loops.

## Configuration

Semantic-release is configured in `.releaserc.json`:

```json
{
  "branches": ["main"],
  "plugins": [
    "@semantic-release/commit-analyzer",     // Analyzes commits
    "@semantic-release/release-notes-generator", // Generates notes
    "@semantic-release/changelog",           // Updates CHANGELOG.md
    "@semantic-release/npm",                 // Updates package.json
    "@semantic-release/exec",                // Updates VERSION file
    "@semantic-release/git",                 // Commits changes
    "@semantic-release/github"               // Creates GitHub release
  ]
}
```

## Checking What Will Be Released

Before merging, you can preview what version would be released:

```bash
# Install semantic-release locally
npm install

# Dry run (doesn't create release, just shows what would happen)
npx semantic-release --dry-run
```

This shows:
- Which commits would be included
- What version would be created
- What would go in the release notes

## Troubleshooting

### "No release published" message

**Cause**: No release-worthy commits since last release (only `chore:`, `test:`, `ci:`, `build:`)

**Solution**: This is expected! Not every merge needs a release. Use `feat:` or `fix:` commits to trigger releases.

### Release workflow fails

**Check**:
1. Commit messages follow conventional format
2. Build succeeds (`npm run build` works locally)
3. GitHub Actions has proper permissions

### VERSION file out of sync

**Should never happen** - semantic-release updates both files atomically.

If it does happen:
```bash
# Sync to last git tag version
git describe --tags --abbrev=0  # e.g., v0.2.3
# Manually edit VERSION and package.json to match
git commit -m "chore: sync version files [skip ci]"
```

## Migration Notes

### Old `scripts/bump-version.sh` script

**No longer needed!** You can delete it or keep it for manual overrides in edge cases.

### Existing PRs with manual version bumps

If you have open PRs with manual version bump commits:
1. **Revert** the version bump commits
2. Keep your feature commits with proper conventional format
3. Merge - semantic-release will handle versioning

### First release with semantic-release

The first release after migration will:
- Read current version from VERSION file (0.1.3)
- Analyze commits since last tag
- Create appropriate next version based on commits

## Best Practices

1. **Write good commit messages** - They become your release notes
2. **Use conventional format strictly** - This determines versions
3. **Group related changes** - One PR for one feature/fix when possible
4. **Review CHANGELOG** - Check generated changelog after release
5. **Don't manually edit VERSION** - Let semantic-release manage it

## Further Reading

- [Conventional Commits Specification](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [semantic-release Documentation](https://semantic-release.gitbook.io/)
- [RELEASING.md](../RELEASING.md) - Full release process documentation
