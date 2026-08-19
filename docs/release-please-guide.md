# Release Please Guide for SORT

## How It Works

SORT uses [release-please](https://github.com/googleapis/release-please) to turn Conventional Commits into a release. Instead of releasing on every merge, it maintains an always-up-to-date **release PR** that accumulates pending changes — merging that PR is what actually cuts the release, so you control exactly when a release (and the deployment that follows it) happens.

1. Every push to `main` runs the **Create Release** workflow (`release.yaml`).
2. release-please looks at commits since the last release and opens or updates a PR titled something like `chore(main): release 0.10.0`, containing:
   - A version bump in `.release-please-manifest.json`
   - An updated `CHANGELOG.md`
3. That PR sits open and keeps updating itself as more commits land on `main` — no release happens yet.
4. When you're ready to deploy, **merge the release PR**. That merge:
   - Creates the git tag (e.g. `v0.10.0`)
   - Publishes the GitHub release with auto-generated notes
5. A second job then builds the frontend and attaches release artifacts:
   - `sort-frontend-{version}.tar.gz` — built Vite/Svelte bundle
   - `SORT-{version}.tar.gz` — full source archive with built assets
6. Publishing the GitHub release fires `release: published`, triggering `release-to-orda.yml` (see [docs/publish.md](publish.md)).

## Commit Message Format

Use [Conventional Commits](https://www.conventionalcommits.org/) — the commit type determines the version bump and which section of the changelog it lands in:

| Commit Type | Version Bump | Example |
|-------------|--------------|---------|
| `feat:` or `feature:` | **Minor** (0.1.0 → 0.2.0) | `feat: Add file upload` |
| `fix:` | **Patch** (0.1.0 → 0.1.1) | `fix: Correct validation` |
| `BREAKING CHANGE:` in the footer | **Major** (0.1.0 → 1.0.0) | See below |
| `perf:`, `refactor:`, `docs:`, `revert:`, `chore:`, `test:`, `build:`, `ci:` | No version bump | Still shown in the changelog under their own heading (release-please's default grouping) |

### Breaking Changes

Add `BREAKING CHANGE:` in the commit footer for major versions:

```bash
git commit -m "feat: Redesign survey API

BREAKING CHANGE: Survey configuration endpoint now requires authentication.
Update your API clients to include Authorization header."
```

## What Gets Automated?

On every push to `main`:

1. release-please opens/updates the release PR with the version bump and changelog — no release yet.

When the release PR is merged:

1. ✅ Git tag created (e.g. `v0.10.0`)
2. ✅ GitHub release published with generated notes
3. ✅ Frontend built and archived, source archive created
4. ✅ Both archives attached to the GitHub release
5. ✅ `release-to-orda.yml` triggered by the published release

Nothing is committed back to `main` outside of merging the release PR itself — there's no `[skip ci]` version-bump commit to worry about.

## Example Workflow

```bash
git checkout -b feat/upload-improvements
# ... make changes ...
git commit -m "feat: Add drag-and-drop file upload"
git push origin feat/upload-improvements
# Create PR → merge to main
# release-please updates (or opens) the release PR to include this change
```

Repeat for as many feature/fix PRs as you like — they all accumulate into the same open release PR. When you're ready to deploy:

```text
Merge the "chore(main): release X.Y.Z" PR
# → tag + GitHub release created
# → frontend built and attached
# → release-to-orda.yml runs
```

## Configuration

release-please is configured by two files at the repo root:

- `release-please-config.json` — release type (`simple`, i.e. no `package.json` version bump) and changelog path
- `.release-please-manifest.json` — tracks the current released version per package

The workflow itself lives at `.github/workflows/release.yaml`.

## Triggering the workflow manually

Go to **Actions → Create Release → Run workflow** to re-run release-please without waiting for the next push to `main` — useful for retrying after a failed run.

## Troubleshooting

### No release PR appears

**Cause**: No release-worthy commits since the last release (only `chore:`, `test:`, `ci:`, `build:`, etc.)

**Solution**: This is expected — release-please only proposes a version bump for `feat:`/`fix:`/breaking-change commits, though other types still show up in the changelog once a bump is proposed.

### Release PR merged but no GitHub release / artifacts

**Check**:
1. The `build-artifacts` job in `release.yaml` ran (Actions tab) — it's gated on `release_created` from the release-please step
2. `npm run build` succeeds locally
3. `RELEASE_TOKEN` is set and has `contents: write` — see [docs/publish.md](publish.md#one-time-setup-release-token)

### Release created but nothing archived to ORDA

See [docs/publish.md](publish.md#one-time-setup-release-token) — this requires `RELEASE_TOKEN`, not the default `GITHUB_TOKEN`, for the same anti-recursion reason described there.

## Further Reading

- [Conventional Commits Specification](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [release-please Documentation](https://github.com/googleapis/release-please)
- [RELEASING.md](../RELEASING.md) - Full release process documentation
