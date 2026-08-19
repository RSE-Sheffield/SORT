#!/usr/bin/env bash
#
# Run svelte-check and fail if the number of type errors has gone up.
#
# The codebase has a backlog of pre-existing type errors, so `npm run check` cannot be a
# hard gate yet. This ratchet blocks new ones while the backlog is burnt down: whenever
# the count drops, lower the number in .svelte-check-baseline in the same commit.
#
# Usage: scripts/svelte_check_ratchet.sh
set -euo pipefail

repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
baseline_file="$repository_root/.svelte-check-baseline"

if [[ ! -f "$baseline_file" ]]
then
    echo "Baseline file not found: $baseline_file" >&2
    exit 2
fi

baseline="$(tr -d '[:space:]' < "$baseline_file")"
if ! [[ "$baseline" =~ ^[0-9]+$ ]]
then
    echo "Baseline file must contain a single number, got: '$baseline'" >&2
    exit 2
fi

# svelte-check exits non-zero when it finds errors, which is what we are measuring.
# NO_COLOR disables chalk's ANSI colour codes, which otherwise break the summary-line match below.
output="$(cd "$repository_root" && NO_COLOR=1 npm run --silent check 2>&1 || true)"
echo "$output"

# The summary line reads: "svelte-check found N errors and M warnings in K files".
# Strip ANSI escape codes defensively in case colour output slips through despite NO_COLOR.
errors="$(echo "$output" | sed -E 's/\x1b\[[0-9;]*m//g' | sed -n 's/^svelte-check found \([0-9]\+\) error.*/\1/p' | tail -n 1)"
if [[ -z "$errors" ]]
then
    echo "Could not read the error count from the svelte-check output" >&2
    exit 2
fi

if (( errors > baseline ))
then
    cat >&2 <<MESSAGE

svelte-check reports $errors errors, up from the baseline of $baseline.
Fix the new type errors, or explain why the baseline should rise.
MESSAGE
    exit 1
fi

if (( errors < baseline ))
then
    cat >&2 <<MESSAGE

svelte-check reports $errors errors, below the baseline of $baseline.
Lower the number in .svelte-check-baseline to lock the improvement in.
MESSAGE
    exit 1
fi

echo "svelte-check errors: $errors (baseline $baseline)"
