#!/bin/bash

set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "Usage git/main.sh <yyyy-mm-dd>" >&2
    exit 1
fi

base_path="$HOME/devel"
author="Jakub Valenta"
date_after=$1
date_before=$(date -d "$date_after +1 day" "+%Y-%m-%d")

echo "Reading Git logs from $date_after to $date_before" >&2

read_repo_log() {
    repo_path=$1
    repo_name=$(basename "$repo_path")
    (
        cd "$repo_path" &&
            (git --no-pager log \
                --author="$author" \
                --after="$date_after" \
                --before="$date_before" \
                --format="%ad,git,\"$repo_name\",\"%s\"" \
                --date=iso8601-strict || echo "")
    )
}

for repo_path in "$base_path"/*; do
    echo "  Reading repository $repo_path" >&2
    read_repo_log "$repo_path"
done
