# Release Process

SORT uses **semantic versioning** (MAJOR.MINOR.PATCH) with releases proposed automatically via [release-please](https://github.com/googleapis/release-please), but cut only when you choose to merge the release PR — typically when rolling out a deployment to the VM.

## How it works

1. Every push to `main` updates an open **release PR** with the pending version bump and changelog entries
2. Merging that PR (whenever you're ready to deploy):
   - Creates a git tag (e.g. `v0.3.1`)
   - Publishes a GitHub release with auto-generated notes
3. A follow-up job builds and attaches artifacts:
   - `sort-frontend-{version}.tar.gz` — built Vite/Svelte bundle
   - `SORT-{version}.tar.gz` — full source archive with built assets

The current version lives in `.release-please-manifest.json` and the git tag — nothing is force-pushed or rewritten on `main`.

## Commit message format

Use [Conventional Commits](https://www.conventionalcommits.org/). The commit type determines the version bump proposed in the release PR:

| Type | Version bump |
|---|---|
| `feat:` / `feature:` | Minor (0.1.0 → 0.2.0) |
| `fix:`, `perf:`, `refactor:`, `docs:`, `revert:` | Patch (0.1.0 → 0.1.1) |
| `BREAKING CHANGE:` in commit footer | Major (0.1.0 → 1.0.0) |
| `chore:`, `test:`, `build:`, `ci:` | No version bump |

## Triggering the workflow manually

Go to **Actions → [Create Release](https://github.com/RSE-Sheffield/SORT/actions/workflows/release.yaml) → Run workflow**. Useful for re-running release-please without waiting for the next push to `main`.

## Troubleshooting

**No release PR appears** — check that at least one commit since the last release uses a release-triggering type (`feat:`, `fix:`, etc.).

**Release PR merged but nothing published** — check the Actions log for build errors or `RELEASE_TOKEN` permission issues.

**Release created but nothing archived to ORDA** — `release.yaml` authenticates with `secrets.RELEASE_TOKEN` (a PAT), not `secrets.GITHUB_TOKEN`, specifically because GitHub won't cascade the `release: published` event to other workflows (like `release-to-orda.yml`) when the release was created by the default token. If `RELEASE_TOKEN` is missing or expired, releases still get created but `release-to-orda.yml` silently never runs. See [docs/publish.md](docs/publish.md#one-time-setup-release-token).
