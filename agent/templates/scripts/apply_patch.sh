#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PATCH_FILE="${SCRIPT_DIR}/changes.patch"

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
    echo "Error: not inside a git repository."
    exit 1
}

cd "${REPO_ROOT}"

if git apply --reverse --check "${PATCH_FILE}" >/dev/null 2>&1; then
    echo "Patch is already applied."
    exit 0
fi

echo "Applying patch..."

if git apply --check "${PATCH_FILE}" >/dev/null 2>&1; then
    # Normal apply does not stage changes.
    git apply "${PATCH_FILE}"
else
    echo "Direct apply failed. Trying 3-way merge..."

    # 3-way stages changes.
    git apply --3way "${PATCH_FILE}"

    # Convert them back to normal working-tree changes.
    git reset
fi

echo "Patch applied successfully."
