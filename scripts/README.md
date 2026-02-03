# Scripts

These shell scripts can be used to help administer the system.

# Installation

These require the Bash shell and the [jq JSON editor tool](https://jqlang.org/).

```bash
sudo apt install jq
```

# Usage

To run the scripts, navigate to the root directory of this repository and activate the virtual environment.

## Version Management

### bump-version.sh

Bump the semantic version before creating a release.

```bash
# Bump patch version (0.1.0 → 0.1.1)
./scripts/bump-version.sh patch

# Bump minor version (0.1.5 → 0.2.0)
./scripts/bump-version.sh minor

# Bump major version (1.2.3 → 2.0.0)
./scripts/bump-version.sh major
```

This script updates both `VERSION` file and `package.json`. After bumping, commit the changes and merge to `main` to trigger an automatic release.

See [../.github/RELEASE.md](../.github/RELEASE.md) for complete release documentation.

## Data Management

### export.sh

Export SORT data to JSON format.

```bash
bash ./scripts/export.sh > sort-export-$(date -I).json
```
