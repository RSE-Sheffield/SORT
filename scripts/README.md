# Scripts

These shell scripts can be used to help administer the system.

# Installation

These require the Bash shell and the [jq JSON editor tool](https://jqlang.org/).

```bash
sudo apt install jq
```

# Usage

To run the scripts, navigate to the root directory of this repository and activate the virtual environment.

Example usage:

```bash
bash ./scripts/export.sh > sort-export-$(date -I).json
```
