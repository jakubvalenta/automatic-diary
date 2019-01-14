#!/bin/bash

set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "Usage git/main.sh <yyyy-mm-dd>" >&2
    exit 1
fi

date_after=$1
date_before=$(date -d "$date_after +1 day" "+%Y-%m-%d")
if [[ -z "$GIT_BASE_PATH" ]]; then
    echo "Please set the environment variable GIT_BASE_PATH." >&2
    echo "Example: GIT_BASE_PATH=\"$HOME/devel\"" >&2
    exit 1
fi

if [[ -z "$GIT_AUTHOR" ]]; then
    echo "Please set the environment variable GIT_AUTHOR." >&2
    echo "Example: GIT_AUTHOR=\"Jakub Valenta\"" >&2
    exit 1
fi

echo "Reading Git logs from $date_after to $date_before" >&2

read_repo_log() {
    repo_path=$1
    repo_name=$(basename "$repo_path")
    (
        cd "$repo_path" &&
            (git --no-pager log \
                --author="$GIT_AUTHOR" \
                --after="$date_after" \
                --before="$date_before" \
                --format="%ad,git,\"$repo_name\",\"%s\"" \
                --date=iso8601-strict || echo "")
    )
}

for repo_path in "$GIT_BASE_PATH"/*; do
    echo "  Reading repository $repo_path" >&2
    read_repo_log "$repo_path"
done
