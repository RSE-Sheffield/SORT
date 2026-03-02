# Release Process

SORT uses **semantic versioning** (MAJOR.MINOR.PATCH) with fully automated releases via [semantic-release](https://semantic-release.gitbook.io/). Merging to `main` triggers the release pipeline automatically.

## How it works

1. Commits are analysed since the last release to determine the version bump
2. Frontend assets are built with Vite
3. A git tag is created (e.g. `v0.3.1`)
4. A GitHub release is published with auto-generated notes and artifacts:
   - `sort-frontend-{version}.tar.gz` — built Vite/Svelte bundle
   - `SORT-{version}.tar.gz` — full source archive with built assets

No files are committed back to the repo — the version lives in the git tag.

## Commit message format

Use [Conventional Commits](https://www.conventionalcommits.org/). The commit type determines the version bump:

| Type | Version bump |
|---|---|
| `feat:` / `feature:` | Minor (0.1.0 → 0.2.0) |
| `fix:`, `perf:`, `refactor:`, `docs:`, `revert:` | Patch (0.1.0 → 0.1.1) |
| `BREAKING CHANGE:` in commit footer | Major (0.1.0 → 1.0.0) |
| `chore:`, `test:`, `build:`, `ci:` | No release |

When a PR contains multiple commits, the highest-priority type wins.

## Triggering a release manually

Go to **Actions → Create Release → Run workflow**. Useful for re-running a failed release.

## Troubleshooting

**No release created** — check that at least one commit since the last tag uses a release-triggering type (`feat:`, `fix:`, etc.).

**semantic-release fails** — check the Actions log for build errors or `GITHUB_TOKEN` permission issues.
